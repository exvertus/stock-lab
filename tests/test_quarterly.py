import pytest

from pathlib import Path
from edgar import get_by_accession_number, Filing

from stock_lab.old import QuarterlyData

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
def local_quarterly(data_directory):
    local_path = data_directory / "nvda_ten_q0001045810-24-000316.pkl"
    nvda_2024_Q3_filing = Filing.load(local_path)
    return QuarterlyData(nvda_2024_Q3_filing)

@pytest.fixture
def remote_quarterly():
    nvda_2024_Q3 = "0001045810-24-000316"
    nvda_2024_Q3_filing = get_by_accession_number(nvda_2024_Q3)
    return QuarterlyData(nvda_2024_Q3_filing)

def test_get_revenue(local_quarterly):
    local_quarterly.get_revenue()
    assert local_quarterly.revenue == 35082000000

def test_get_eps(local_quarterly):
    local_quarterly.get_eps()
    assert local_quarterly.eps == 0.78

def test_shares_outstanding(local_quarterly):
    local_quarterly.get_shares_outstanding()
    assert local_quarterly.shares == 24774000000


