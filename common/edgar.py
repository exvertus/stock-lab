from datetime import date

from edgar.entity.filings import EntityFiling
from edgar.xbrl.xbrl import XBRL

from common.shared import inspect_dir

class QuarterlyData():
    def __init__(self, filing):
        self.filing = filing
        self.period_end_date = date.fromisoformat(self.filing.period_of_report)
        self.facts_df = XBRL.from_filing(self.filing).facts.to_dataframe()

        self.start_date = date.fromisoformat('1000-01-01')
        self.end_date = date.fromisoformat('1000-01-01')
        self.revenue = 0
        self.eps = 0
        self.profit_margin = 0.0
        self.free_cash_flow = 0

    def export_facts(self):
        # TODO: Add url to head of csv
        self.facts_df.to_csv(inspect_dir / f"{self.accession_number}.csv")

    def get_revenue(self):
        print("break")
        pass

    def get_eps(self):
        pass

    def get_profit_margin(self):
        pass

    def get_free_cash_flow(self):
        pass
    
class TenQData(QuarterlyData):
    pass

class TenKData(QuarterlyData):
    pass
