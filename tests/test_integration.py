import pytest
from datetime import date

from edgar import Company, get_by_accession_number
from edgar.xbrl.xbrl import XBRL

from common.edgar import QuarterlyData

# @pytest.mark.integration
# def test_get_eps():
#     nvda_cik = 1045810
#     nvda_co = Company(nvda_cik)
#     ten_k = nvda_co.get_filings(form="10-K").latest()
#     xlbr = XBRL.from_filing(ten_k)
#     facts = xlbr.facts.to_dataframe()
#     fact_keys = [
#         'us-gaap_EarningsPerShareDiluted_c-1',
#         'us-gaap_EarningsPerShareDiluted_c-11',
#         'us-gaap_EarningsPerShareDiluted_c-12'
#     ]
#     eps_df = facts[facts['fact_key'].isin(fact_keys)]
#     print("break")

@pytest.fixture
def quarterly_instance():
    nvda_2024_Q3 = "0001045810-24-000316"
    nvda_2024_Q3_filing = get_by_accession_number(nvda_2024_Q3)
    return QuarterlyData(nvda_2024_Q3_filing)

@pytest.mark.integration
def test_get_revenue(quarterly_instance):
    quarterly_instance.get_revenue()
    assert quarterly_instance.revenue == 35082000000
