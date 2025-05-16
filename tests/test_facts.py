import pytest
import pandas as pd

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.facts import FilingFacts

# ---------------- Unit tests ----------------

@pytest.mark.parametrize("df, expected", [
    # Empty datafrom
    (pd.DataFrame(), True),
    # None object
    (None, True),
    # Column labels but no rows
    (pd.DataFrame(columns=["period_end", "value"]), True),
    # All cells in value column are None
    (pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": [None, None]
    }), True),
    # All cells in value column are empty strings
    (pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["", ""]
    }), True),
    # All cells in value column are pd.NA
    (pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": [pd.NA, pd.NA]
    }), True),
    # Empty strings are okay as long as a value is found
    (pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["234561", ""]
    }), False),
    # The ideal scenario---legit values found in all rows
    (pd.DataFrame({
        "period_end": ["2025-05-16", "2020-05-16"],
        "value": ["3400521", "42145"]
    }), False),
])
def test_data_missing(df, expected):
    assert FilingFacts.data_missing(df) == expected

@pytest.mark.parametrize("concept, df_in, df_expected",[
    # Ideal case: multiple rows but only one latest end_date
    ("us-gaap:Revenues",
     pd.DataFrame({
        "concept": ["us-gaap:Revenues", "us-gaap:Revenues", "us-gaap:CostOfRevenue"],
        "value": ["3000", "2000", "1000"],
        "period_end": ["2024-10-27", "2024-01-29", "2024-11-27"]
     }),
     pd.DataFrame({
        "concept": ["us-gaap:Revenues"],
        "value": ["3000"],
        "period_end": ["2024-10-27"]
     })
    )
])
def test_get_for_latest_end_dates(concept, df_in, df_expected):
    ff = FilingFacts(df_in)
    actual_df = ff.get_for_latest_end_dates(concept)
    pd.testing.assert_frame_equal(
        actual_df.reset_index(drop=True), df_expected.reset_index(drop=True))

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
    ten_q_df = XBRL.from_filing(nvda_ten_q).facts.to_dataframe()
    FilingFacts(ten_q_df)

@pytest.mark.integration
def test_filings_facts_ten_k(nvda_ten_k):
    ten_k_df = XBRL.from_filing(nvda_ten_k).facts.to_dataframe()
    FilingFacts(ten_k_df)
