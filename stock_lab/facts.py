import pandas as pd

# TODO: Add decorator to wrap error messages for validator pipeline funcs.

class MissingFact(Exception):
    """Thrown when expected data is not present."""
    pass

class InvalidFact(Exception):
    """Thrown when a row's data does not conform to expectations."""
    pass

def err_if_none_in_column(column_name, df):
    """
    Raise a MissingFact exception if any value in the column is 'none-like':
    - None
    - np.nan / pd.NA
    - Empty string
    - Whitespace-only string
    """
    col = df[column_name]
    mask = col.isna() | col.astype(str).str.strip().eq("")
    if mask.any():
        raise MissingFact(
            f"Found none-like value(s) in column '{column_name}':\n{df.loc[mask]}"
        )

def values_to_num(df):
    """
    Convert all cells in the values column to numerics.
    If any cannot be converted raise InvalidFact exception.
    """
    try:
        df["value"] = pd.to_numeric(df["value"], errors='raise')
    except ValueError as e:
        raise InvalidFact(f"Failed to convert value to numeric: {e}")
    return df
    
def values_not_negative(df):
    """
    Raise an InvalidFact expection if anything in the values column is < 0.
    """
    if (df["value"] < 0).any():
        raise InvalidFact(f"Value should not be < 0")
    return df
    
def duration_to_date(df):
    """
    Convert all in the period_start and period_end columns to date types.
    """
    err_if_none_in_column("period_start", df)
    err_if_none_in_column("period_end", df)
    try:
        df["period_start"] = pd.to_datetime(df["period_start"], errors='raise')
        df["period_end"] = pd.to_datetime(df["period_end"], errors='raise')
    except ValueError as e:
        raise InvalidFact(f"Failed to convert to date: {e}")
    return df

def instant_to_date(df):
    """
    Convert all in the period_instant column to date types.
    """
    err_if_none_in_column("period_instant", df)
    try:
        df["period_instant"] = pd.to_datetime(df["period_instant"], errors='raise')
    except ValueError as e:
        raise InvalidFact(f"Failed to convert to date: {e}")
    return df

class FilingFacts():
    """
    Raw data pulled from a single quarterly filing (10-Q, 10-K).
    Type conversion and filing validation is performed after data is pulled.
    filing_df: a dataframe from a quarterly filing.
    """

    period_type_bi_dict = {
        "period_end": "duration",
        "duration": "period_end",
        "period_instant": "instant",
        "instant": "period_instant",
    }
    gaap_tags = {
        "revenue": {
            "period_type": "duration",
            "tags": (
                "us-gaap:Revenues",
                "us-gaap:SalesRevenueNet",
                "us-gaap:SalesRevenueServicesNet",
                )
        },
        "eps": {
            "period_type": "duration",
            "tags": (
                "us-gaap:EarningsPerShareDiluted",
                "us-gaap:EarningsPerShareBasicAndDiluted",
            )
        },
        "diluted_shares": {
            "period_type": "duration",
            "tags": (
                "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
                "us-gaap:WeightedAverageNumberOfSharesOutstandingDiluted",
            ),
        },
        "net_income": {
            "period_type": "duration",
            "tags": (
                "us-gaap:NetIncomeLoss",
                "us-gaap:ProfitLoss",
            )
        },
        "operating_income": {
            "period_type": "duration",
            "tags": (
                "us-gaap:OperatingIncomeLoss",
            ),
        },
        "operating_cash_flow": {
            "period_type": "duration",
            "tags": (
                "us-gaap:NetCashProvidedByUsedInOperatingActivities",
                "us-gaap:NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
            ),
        },
        "cap_ex": {
            "period_type": "duration",
            "tags": (
                "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
                "us-gaap:CapitalExpenditures",
                "us-gaap:PaymentsForCapitalExpenditures",
                "us-gaap:NetCashUsedForInvestingActivities",
                "us-gaap:PaymentsToAcquireProductiveAssets",
            ),
        },
        "gross_profit": {
            "period_type": "duration",
            "tags": (
                "us-gaap:GrossProfit",
            ),
        },
        "cash_equivalents": {
            "period_type": "instant",
            "tags": (
                "us-gaap:CashAndCashEquivalentsAtCarryingValue",
                "us-gaap:CashCashEquivalentsAndShortTermInvestments",
            ),
        },
    }

    def __init__(self, filing_df):
        self.facts_df = filing_df

    def parse(self):
        self.rows = self.get_rows()
        self.post_checks()

    def get_rows(self):
        """
        For each fact type, pull row(s) from the facts dataframe.
        If no matches are found after gaap_tags values are exhausted,
        raise a MissingFact exception.
        Returns dataframe of found facts for latest period_end.
        """
        if self.facts_df.empty:
            raise MissingFact(f"Input dataframe is empty.")
        results_df = pd.DataFrame()
        for fact_type, gaap_dict in self.gaap_tags.items():
            rows_df = self.seek_tags_until_found(gaap_dict)
            # Validate here?
            if FilingFacts.data_missing(rows_df):
                raise MissingFact(f"Could not find a matching row for {fact_type}")
            rows_df.insert(0, "fact_type", fact_type)
            if results_df.empty:  
                results_df = rows_df
            else:
                results_df = pd.concat([results_df, rows_df], ignore_index=True)
        return results_df
    
    @staticmethod
    def data_missing(df):
        """True if df is empty or values column contains all nil values."""
        if df is None or df.empty:
            return True
        if "value" not in df.columns:
            return True
        return df["value"].replace("", pd.NA).isna().all()
    
    @staticmethod
    def normalize_duration(df):
        """
        Convert period_start, period_end columns to date types
        and value column to numerics."""
        pass

    def seek_tags_until_found(self, gaap_dict):
        """
        Search in order of gaap_data until at least one is found,
        short circuiting other tags when a tag finds a match.
        Returns dataframe for ALL rows for that tag with the latest end date.
        """
        rows = None
        target_date = FilingFacts.period_type_bi_dict[gaap_dict["period_type"]]
        for tag in gaap_dict["tags"]:
            rows = self.get_for_latest_date(tag, target_date)
            if not rows.empty:
                return rows
        return rows

    def get_for_latest_date(self, tag, target_date):
        """
        For provided tag (aka "concept"), 
        find the most recent dates in the filing.
        Returns a dataframe with each row found.
        """
        concept_rows = self.facts_df.loc[
            self.facts_df["concept"] == tag
        ].copy()

        concept_rows = concept_rows.dropna(subset=[target_date])
        if concept_rows.empty:
            return concept_rows
        
        latest_date = concept_rows[target_date].max()
        result_rows = concept_rows.loc[
            concept_rows[target_date] == latest_date
        ]

        expected_date_type = FilingFacts.period_type_bi_dict[target_date]
        if not (result_rows["period_type"] == expected_date_type).all():
            raise InvalidFact(f"Expected all {expected_date_type} but got {result_rows["period_type"]}.")
        return result_rows

    def post_checks(self):
        # End and instant dates should all be the same.
        pass
