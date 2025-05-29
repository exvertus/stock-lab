import pandas as pd

from edgar.xbrl.xbrl import XBRL

class FilingDataError(Exception):
    """Raised when required filing data is missing or invalid."""
    pass

class InvalidDate(Exception):
    """Raised when something invalid related to a date is encountered."""
    pass

class MissingDate(Exception):
    """Raised when expected date is missing."""
    pass

def get_rows_matching_first_found_value(dataframe, target_column, candidate_values):
    """
    Filter DataFrame rows based on the first candidate value that exists in the target column.
    
    Args:
        dataframe (pd.DataFrame): The DataFrame to filter.
        target_column (str): Name of the column to search within. Must exist in the DataFrame.
        candidate_values (list): Ordered list of values to search for. The function will use
                               the first value from this list that is found anywhere in the
                               target_column. Order matters - earlier values take precedence.
    
    Returns:
        pd.DataFrame: All rows where the target_column matches the first found candidate value.
                     Returns empty DataFrame if none of the candidate values are found in
                     the target_column. Preserves original DataFrame structure and dtypes.
    
    Behavior:
        - Searches through candidate_values in order until finding one that exists in target_column
        - Once a match is found, stops searching and returns ALL rows with that value
        - Ignores remaining candidate_values after first match is found
        - Case-sensitive matching (unless column data is already case-insensitive)
    
    Example:
        If target_column contains ['A', 'B', 'C', 'A'] and candidate_values is ['X', 'B', 'A'],
        the function will return all rows where target_column == 'B' (since 'B' is found first
        in the candidates list, even though 'A' also exists in the column).
    """
    results = pd.DataFrame(columns=dataframe.columns)
    for cand in candidate_values:
        results = dataframe[dataframe[target_column] == cand]
        if not results.empty:
            return results
    return results

def get_matching_period_data(period_data_list, target_end_date, reporting_period_type):
    """
    Filter and sort period data dictionaries based on type, end date, and period type.
    
    Args:
        period_data_list (list): List of dictionaries, each representing a reporting period.
                                Each dictionary must contain 'type', 'end_date', and 'period_type' keys.
        target_end_date (str/date): The end date to match against. Format should match the 
                                   'end_date' values in the period dictionaries.
        reporting_period_type (str): The period type to filter by. Expected values are 
                                   'Annual' or 'Quarterly' (case-sensitive).
    
    Returns:
        list: Filtered list of period dictionaries that match all criteria:
              - type == 'duration'
              - end_date == target_end_date  
              - period_type == reporting_period_type
              If multiple matches exist, they are sorted by the number of context IDs 
              in descending order (most context IDs first).
    
    Raises:
        MissingDate: If no period dictionaries match all three criteria (type='duration',
                    target_end_date, and reporting_period_type).
    
    Notes:
        - Dictionaries without type='duration' are ignored during filtering.
        - Each period dictionary is expected to have a 'context_ids' key (list or countable)
          used for sorting when multiple matches exist.
        - Exact matching is performed on all filter criteria.
    """
    results = []
    for period in period_data_list:
        if period['type'] == 'duration':
            if period['period_type'] == reporting_period_type:
                if period['end_date'] == target_end_date:
                    results.append(period)
    if not results:
        raise MissingDate(f"Could not find '{reporting_period_type}' duration for {target_end_date}")
    return sorted(results, key=lambda d: len(d['context_ids']), reverse=True)

def get_matching_instant_data(period_data_list, target_instant_date):
    """
    Find a single instant-type period dictionary that matches the target instant date.
    
    Args:
        period_data_list (list): List of dictionaries, each representing a reporting period.
                                Each dictionary must contain a 'type' key. Only dictionaries
                                with type='instant' are expected to have an 'instant_date' key.
        target_instant_date (str/date): The instant date to match against. Format should match
                                       the 'instant_date' values in the instant-type dictionaries.
    
    Returns:
        dict: Single period dictionary that matches both criteria:
              - type == 'instant'
              - instant_date == target_instant_date
    
    Raises:
        MissingDate: If no period dictionaries match both the type='instant' and 
                    target_instant_date criteria.
        InvalidDate: If more than one period dictionary matches the criteria.
                    Only one instant match is expected per target date.
    
    Notes:
        - Dictionaries without type='instant' are ignored during filtering.
        - Non-instant dictionaries may not contain an 'instant_date' key.
        - Exact matching is performed on the instant_date field.
        - This function enforces uniqueness - multiple matches indicate data inconsistency.
    """
    results = []
    for period in period_data_list:
        if period['type'] == 'instant':
            if period['date'] == target_instant_date:
                results.append(period)
    if not results:
        raise MissingDate(f"Could not find instant date for {target_instant_date}")
    if len(results) > 1:
        raise InvalidDate(f"Found more than one instant date for {target_instant_date}")
    return results[0]

class XBRLFactsNormalizer:
    """
    Normalizes and extracts key financial metrics from XBRL filing data.
    
    Takes structured XBRL data (via edgartools) and normalizes varying GAAP tags
    and date ranges into standardized financial concepts. Handles the complexity
    of multiple tags representing the same concept, date range variations, and
    segment breakdowns to extract the most appropriate values.
    
    Extracts core metrics including revenue, EPS, diluted shares, net income,
    operating income, operating cash flow, capex, gross profit, and cash equivalents
    from 10-K and 10-Q filings.
    
    The class applies modular processing steps: tag identification, date range
    filtering, value selection (preferring totals over breakdowns), and basic
    validation/transformation.
    
    Args:
        filing: Edgartools filing object
        
    Returns:
        DataFrame with normalized financial facts, with individual metrics
        accessible via attributes. Includes metadata for downstream processing
        when exact date ranges aren't available.
        
    Example:
        >>> normalizer = XBRLFactsNormalizer(filing)
        >>> facts_df = normalizer.extract()
        >>> quarterly_revenue = normalizer.revenue
    """
    def __init__(self, filing):
        self.filing = filing
        self.get_metadata()

    def get_metadata(self):
        """
        Pull metadata from filing.
        """
        try:
            self.xbrl = XBRL.from_filing(self.filing)
        except(Exception) as e:
            raise FilingDataError(f"Failed to create XBRL: {e}")

        try:
            self.accession_number = self.filing.accession_no
        except(AttributeError):
            try:
                self.accession_number = self.filing.accession_number
            except(AttributeError):
                raise FilingDataError("Accession number not found")

        try:
            self.ticker = self.xbrl.entity_info['ticker']
        except(KeyError):
            raise FilingDataError("Ticker not found")

        try:
            self.document_type = self.xbrl.entity_info['document_type']
        except(KeyError):
            raise FilingDataError("Document type not found")
        
        if self.document_type not in ('10-K', '10-Q'):
            raise FilingDataError(f"Document type must be 10-K or 10-Q: got {self.document_type}")
        self.report_end = self.xbrl.period_of_report

    def extract(self):
        pass
        
    def get_timeframes(self):
        """
        
        """
        self.current_instant = get_matching_instant_data(
            self.xbrl.reporting_periods, self.report_end)
        # TODO: Handle 10-K in an inherited class instead?
        if self.document_type == '10-K':
            self.annual_duration = get_matching_period_data(
                self.xbrl.reporting_periods, self.report_end, 'Annual')
            try:
                self.quarter_duration = get_matching_period_data(
                self.xbrl.reporting_periods, self.report_end, 'Quarterly')
            except MissingDate:
                self.quarter_duration = None
        else:
            self.quarter_duration = get_matching_period_data(
            self.xbrl.reporting_periods, self.report_end, 'Quarterly')

        # TODO: Will probably need to add some kind of YTD range as
        # some data can be listed as a YTD duration only
        
    def get_revenue(self):
        """
        Get revenue data for a given 
        """
        # first_tag > check_duration > max_end_date > max_start_date > max_value > 
        pass