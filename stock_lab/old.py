from datetime import date, timedelta
import pandas as pd

from edgar.xbrl.xbrl import XBRL

from stock_lab.shared import inspect_dir

class QuarterlyData():
    def __init__(self, filing):
        self.filing = filing
        self.period_end_date = date.fromisoformat(self.filing.period_of_report)
        self.facts_df = XBRL.from_filing(self.filing).facts.to_dataframe()

        self.period_start_cutoff = self.period_end_date - timedelta(98)

        # Raw values
        self.revenue = None
        self.eps = None
        self.shares = None
        self.operating_cash_flow = None
        self.cap_ex = None

        # Calculated
        self.free_cash_flow = None
        self.profit_margin = None

    def _get_concept_within_dates(self, concept):
        concept_rows = self.facts_df.loc[
            (self.facts_df["concept"] == concept) & 
            (self.facts_df["period_start"] > str(self.period_start_cutoff)) &
            (self.facts_df["period_end"] == str(self.period_end_date)), 
            ["fact_key", "value", "unit_ref", "period_start", "period_end", "label"]
        ]
        return pd.to_numeric(concept_rows["value"]).max()

    def get_revenue(self):
        # TODO: Revenue per share instead?
        self.revenue = self._get_concept_within_dates("us-gaap:Revenues")

    def get_eps(self):
        self.eps = self._get_concept_within_dates("us-gaap:EarningsPerShareDiluted")

    def get_shares_outstanding(self):
        self.shares = self._get_concept_within_dates("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding")

    def get_operating_cash_flow(self):
        pass
    
    def get_free_cash_flow(self):
        pass

    def get_profit_margin(self):
        pass

    def export_facts(self):
        # TODO: Add url to head of csv
        self.facts_df.to_csv(inspect_dir / f"{self.accession_number}.csv")
    
class TenQData(QuarterlyData):
    pass

class TenKData(QuarterlyData):
    pass
