import pandas as pd

class MissingFact(Exception):
    """Thrown when expected data is not present."""
    pass

class InvalidFact(Exception):
    """Thrown when a row's data does not conform to expectations."""
    pass

class FilingFacts():
    """
    Raw, uncalculated, data pulled from a single quarterly filing (10-Q, 10-K).
    Filing validation is performed after data is pulled.
    filing_df: a dataframe from a quarterly filing.
    """
    gaap_tags = {
        "revenue": (
            "us-gaap:Revenues",
            "us-gaap:SalesRevenueNet",
            "us-gaap:SalesRevenueServicesNet",
        ),
        "eps": (
            "us-gaap:EarningsPerShareDiluted",
            "us-gaap:EarningsPerShareBasicAndDiluted",
        ),
        "diluted_shares": (
            "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
            "us-gaap:WeightedAverageNumberOfSharesOutstandingDiluted",
        ),
        "net_income": (
            "us-gaap:NetIncomeLoss",
            "us-gaap:ProfitLoss",
        ),
        "operating_income": (
            "us-gaap:OperatingIncomeLoss",
        ),
        "operating_cash_flow": (
            "us-gaap:NetCashProvidedByUsedInOperatingActivities",
            "us-gaap:NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ),
        "cap_ex": (
            "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
            "us-gaap:CapitalExpenditures",
            "us-gaap:PaymentsForCapitalExpenditures",
            "us-gaap:NetCashUsedForInvestingActivities",
            "us-gaap:PaymentsToAcquireProductiveAssets",
        ),
        "gross_profit": (
            "us-gaap:GrossProfit",
        ),
        "cash_equivalents": (
            "us-gaap:CashAndCashEquivalentsAtCarryingValue",
            "us-gaap:CashCashEquivalentsAndShortTermInvestments",
        )
    }

    def __init__(self, filing_df):
        self.facts_df = filing_df

    def parse(self):
        self.rows = self.get_rows()
        self.validate()

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
        for fact_type, concepts in self.gaap_tags.items():
            rows_df = self.seek_tags_until_found(concepts)
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

    def seek_tags_until_found(self, gaap_tags):
        """
        Search in order of gaap_tags until at least one is found,
        short circuiting other tags when a tag finds a match.
        Returns dataframe for ALL rows for that tag with the latest end date.
        """
        rows = None
        for tag in gaap_tags:
            rows = self.get_for_latest_end_dates(tag)
            if not rows.empty:
                return rows
        return rows

    def get_for_latest_end_dates(self, tag):
        """
        For provided tag (aka "concept"), 
        find the most recent end dates in the filing.
        Returns a dataframe with each row found.
        """
        concept_rows = self.facts_df.loc[
            self.facts_df["concept"] == tag
        ].copy()

        concept_rows = concept_rows.dropna(subset=["period_end"])
        if concept_rows.empty:
            return concept_rows
        
        latest_end_date = concept_rows["period_end"].max()
        result_rows = concept_rows.loc[
            concept_rows["period_end"] == latest_end_date
        ]
        return result_rows

    def validate(self):
        # End dates should all be the same.
        pass