import pytest

import stock_lab.utils
import stock_lab.facts

@pytest.fixture
def nvda_quarters():
    nvda_pkls = stock_lab.utils.REPO_ROOT/"tests/data/nvda"
    return stock_lab.utils.load_filings_from_dir(nvda_pkls)

@pytest.fixture
def nvda_ten_k():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-25-000023.pkl"
    )

def nvda_ten_q():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-24-000316.pkl"
    )

def test_filings_facts(nvda_ten_k):
    stock_lab.facts.FilingFacts(nvda_ten_k)

def test_muliple_quarters(nvda_quarters):
    # Finish later...
    for q in nvda_quarters:
        stock_lab.utils.filings_facts_to_csv(q)