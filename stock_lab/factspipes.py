import pandas as pd

from edgar.xbrl.xbrl import XBRL

# example: revenue pipeline
# first_tag > check_duration > max_end_date > max_start_date > max_value > 

class InvalidDate(Exception):
    """Thrown when something invalid related to a date is encountered."""
    pass

class MissingDate(Exception):
    """Thrown when expected date is missing."""
    pass

def match_first_in_column(df, column, candidates):
    """
    Return all rows where the given column matches the first value found in `candidates`.
    Subsequent values are ignored once a match is found.
    """
    # Create an empty DataFrame with the same columns and types
    results = pd.DataFrame(columns=df.columns)
    for cand in candidates:
        results = df[df[column] == cand]
        if not results.empty:
            return results
    return results

def get_date_durations(period_list, end_date, period_type):
    """
    From a list of periods, find the period that corresponds to end_date and 
    period_type ('Annual', 'Quarterly') and return matching dictionary. 
    If more than one dictionary is found, order by the most context ids.
    """
    results = []
    for period in period_list:
        if period['type'] == 'duration':
            if period['period_type'] == period_type:
                if period['end_date'] == end_date:
                    results.append(period)
    if not results:
        raise MissingDate(f"Could not find '{period_type}' duration for {end_date}")
    return sorted(results, key=lambda d: len(d['context_ids']), reverse=True)

def get_date_instant(period_list, instant_date):
    """
    From a list of periods, find the instant date that corresponds to 
    instant_date and return matching dictionary. If more than one dictionary is
    found, raise an InvalidDate error.
    """
    results = []
    for period in period_list:
        if period['type'] == 'instant':
            if period['date'] == instant_date:
                results.append(period)
    if not results:
        raise MissingDate(f"Could not find instant date for {instant_date}")
    if len(results) > 1:
        raise InvalidDate(f"Found more than one instant date for {instant_date}")
    return results[0]

class FactsPipe():
    """
    Data ingestion pipeline for getting key facts from XBRL filing object.
    """
    def __init__(self, filing):
        self.filing = filing
        self.xbrl = XBRL.from_filing(filing)
        self.get_keys()
        
    def get_keys(self):
        """
        Get general filing metadata for accessing information.
        """
        self.accession_number = self.filing.accession_no
        self.ticker = self.xbrl.entity_info['ticker']
        self.document_type = self.xbrl.entity_info['document_type']
        self.report_end = self.xbrl.period_of_report

        if self.document_type == '10-K':
            self.annual_duration = get_date_durations(
                self.xbrl.reporting_periods, self.report_end, 'Annual')
            try:
                self.quarter_duration = get_date_durations(
                self.xbrl.reporting_periods, self.report_end, 'Quarterly')
            except MissingDate:
                self.quarter_duration = None
        else:
            self.quarter_duration = get_date_durations(
            self.xbrl.reporting_periods, self.report_end, 'Quarterly')
        self.current_instant = get_date_instant(
            self.xbrl.reporting_periods, self.report_end)
