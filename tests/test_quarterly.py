import pytest

from pathlib import Path
from edgar import get_by_accession_number, Filing

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
def data_directory():
    here = Path(__file__).parent
    return here / "data"

@pytest.fixture
def local_nvda_ten_q(data_directory):
    local_path = data_directory / "nvda_ten_q0001045810-24-000316.pkl"
    return Filing.load(local_path)

@pytest.mark.integration
def test_get_revenue(quarterly_instance):
    quarterly_instance.get_revenue()
    assert quarterly_instance.revenue == 35082000000

@pytest.mark.integration
def test_get_eps(quarterly_instance):
    quarterly_instance.get_eps()
    assert quarterly_instance.eps == 0.78

def test_shares_outstanding(quarterly_instance):
    quarterly_instance.get_shares_outstanding()
    assert quarterly_instance.shares == 24774000000

@pytest.fixture
def quarterly_instance():
    nvda_2024_Q3 = "0001045810-24-000316"
    nvda_2024_Q3_filing = get_by_accession_number(nvda_2024_Q3)
    return QuarterlyData(nvda_2024_Q3_filing)
