from datetime import date

from edgar import get_by_accession_number
from edgar.xbrl.xbrl import XBRL

from common.shared import inspect_dir

class Quarterly():
    def __init__(self, accession_number):
        self.accession_number = accession_number
        self.filing = get_by_accession_number(accession_number)
        self.ten_q_df = XBRL.from_filing(self.filing).facts.to_dataframe()
        self.end_date = date.fromisoformat('1000-01-01')
        self.revenue = 0
        self.eps = 0
        self.profit_margin = 0.0
        self.free_cash_flow = 0

    def export_facts(self):
        self.ten_q_df.to_csv(inspect_dir / f"{self.accession_number}.csv")

    def get_end_date(self):
        print("break")

    def get_revenue(self):
        pass

    def get_eps(self):
        pass

    def get_profit_margin(self):
        pass

    def get_free_cash_flow(self):
        pass
    