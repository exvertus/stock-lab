import pytest

import pandas as pd

import stock_lab.utils
from stock_lab.facts import FilingFacts

# ---------------- Unit tests ----------------

def test_data_missing_empty():
    df_empty = pd.DataFrame()
    df_none = None
    assert FilingFacts.data_missing(df_empty)
    assert FilingFacts.data_missing(df_none)

def test_data_missing_no_rows():
    df = pd.DataFrame(columns=["period_end", "value"])
    assert FilingFacts.data_missing(df)

def test_data_missing_nil_value():
    df_none = pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": [None, None]
    })
    df_nil = pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["", ""]
    })
    assert FilingFacts.data_missing(df_none)
    assert FilingFacts.data_missing(df_nil)

def test_data_missing_one_missing():
    df = pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["234561", ""]
    })
    assert not FilingFacts.data_missing(df)

def test_data_missing_returns_false():
    df = pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["3400521", "42145"]
    })
    assert not FilingFacts.data_missing(df)

# ------------- Integration tests -------------

@pytest.fixture
def nvda_quarters():
    nvda_pkls = stock_lab.utils.REPO_ROOT/"tests/data/nvda"
    return stock_lab.utils.load_filings_from_dir(nvda_pkls)

@pytest.fixture
def nvda_ten_k():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-25-000023.pkl"
    )

@pytest.fixture
def nvda_ten_q():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-24-000316.pkl"
    )

@pytest.mark.integration
def test_filings_facts_ten_q(nvda_ten_q):
    FilingFacts(nvda_ten_q)

@pytest.mark.integration
def test_filings_facts_ten_k(nvda_ten_k):
    FilingFacts(nvda_ten_k)

def test_muliple_quarters(nvda_quarters):
    # Finish later...
    pass
