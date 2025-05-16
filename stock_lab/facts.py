import pandas as pd

from edgar.xbrl.xbrl import XBRL

class MissingFact(Exception):
    """Thrown when expected data is not present."""
    pass

class InvalidFact(Exception):
    """Thrown when a row's data does not conform to expectations."""
    pass

class FilingFacts():
    """
    Raw, uncalculated, data pulled from a single filing's XBRL.
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
        ),
        "gross_profit": (
            "us-gaap:GrossProfit",
        ),
        "cash_equivalents": (
            "us-gaap:CashAndCashEquivalentsAtCarryingValue",
            "us-gaap:CashCashEquivalentsAndShortTermInvestments",
        )
    }

    def __init__(self, filing):
        self.filing = filing
        self.facts_df = XBRL.from_filing(self.filing).facts.to_dataframe()
        self.rows = self.get_rows()
        self.validate()

    def get_rows(self):
        """
        For each fact type, pull rows from the facts dataframe.
        If no matches are found after gaap_tags are exhausted,
        raise a MissingFact exception.
        """
        all_rows = []
        for fact_type, tags in self.gaap_tags.items():
            type_rows = None
            type_rows = self._seek_tags_until_found(tags)
            if self.data_missing(type_rows):
                raise MissingFact(f"""Could not find a row for {fact_type}.
                                  Nothing matched for: {tags.split(', ')}""")
            
            type_rows["fact_type"] = fact_type
            all_rows.append(type_rows)
        return all_rows
    
    @staticmethod
    def data_missing(rows):
        return rows is None or rows["value"].replace("", pd.NA).isna().all()

    def _seek_tags_until_found(self, gaap_tags):
        """
        Search in order of gaap_tags until at least one is found,
        short circuiting other tags when a tag finds a match.
        Returns dataframe for ALL rows for that tag with the latest end date.
        """
        rows = []
        for tag in gaap_tags:
            rows = self._get_for_latest_end_dates(tag)
            if rows:
                break
        return rows

    def _get_for_latest_end_dates(self, tag):
        """
        For provided tag (aka "concept"), 
        find the most recent end dates in the filing.
        Returns a dataframe with each row found.
        """
        pass

    def validate(self):
        # End dates should all be the same.
        # Revenue >= 0
        pass