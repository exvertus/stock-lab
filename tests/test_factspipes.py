import pytest
import pandas as pd

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.factspipes import (
    match_first_in_column, FactsPipe, InvalidDate
)

@pytest.mark.parametrize("df, candidates, expected", [
    (
        pd.DataFrame({"concept": ["a", "b", "c", "b"],
                      "value": [1, 2, 3, 4]}),
        ["b", "c"],
        pd.DataFrame({"concept": ["b", "b"],
                      "value": [2, 4]})
    ),
    (
        pd.DataFrame({"concept": ["x", "y", "z", "y", "z"],
                      "value": [0, 1, 2, 3, 4]}),
        ["z", "y"],
        pd.DataFrame({"concept": ["z", "z"], 
                      "value": [2, 4]})
    ),
    (
        pd.DataFrame({"concept": ["x", "y", "z"], 
                      "value": [1, 2, 3]}),
        ["a", "x", "z"],
        pd.DataFrame({"concept": ["x"], 
                      "value": [1]})
    ),
    (
        pd.DataFrame({"concept": ["a", "b", "c"],
                      "value": [1, 2, 3]}),
        ["x", "y"],
        pd.DataFrame({"concept": pd.Series(dtype="object"),
                      "value": pd.Series(dtype="int64")})
    ),
    (
        pd.DataFrame(columns=["concept", "value"]),
        ["a"],
        pd.DataFrame(columns=["concept", "value"])
    ),
    (
        pd.DataFrame({"concept": ["a", "b", "c"], 
                      "value": [1, 2, 3]}),
        [],
        pd.DataFrame(columns=["concept", "value"])
    ),
    (
        pd.DataFrame({"concept": ["a", "b", "c", "b"], 
                      "value": [1, 2, 3, 4]}),
        ["b", "b", "c"],
        pd.DataFrame({"concept": ["b", "b"], "value": [2, 4]})
    ),
    (
        pd.DataFrame({"concept": ["1", 2, "3", 2], 
                      "value": [10, 20, 30, 40]}),
        [2, "3"],
        pd.DataFrame({"concept": pd.Series([2, 2], dtype=object), 
                      "value": [20, 40]})
    ),
], ids=[
    "basic match",
    "only first match is used",
    "first match is later in list",
    "no matches found",
    "empty input dataframe",
    "empty candidate list",
    "duplicate candidates",
    "mixed types in column and candidates"
])
def test_match_first_in_column(df, candidates, expected):
    actual = match_first_in_column(df, "concept", candidates)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected.reset_index(drop=True)
    )

# # -----------------------------------------------------------------------------
# #                               Integration tests
# # -----------------------------------------------------------------------------

@pytest.fixture
def appl_quarters():
    appl_pkls = stock_lab.utils.TEST_DATA_DIR/"aapl"
    return stock_lab.utils.load_filings_from_dir(appl_pkls)

@pytest.fixture
def bdl_quarters():
    bdl_pkls = stock_lab.utils.TEST_DATA_DIR/"bdl"
    return stock_lab.utils.load_filings_from_dir(bdl_pkls)

@pytest.fixture
def nflx_quarters():
    nflx_pkls = stock_lab.utils.TEST_DATA_DIR/"nflx"
    return stock_lab.utils.load_filings_from_dir(nflx_pkls)

@pytest.fixture
def nvda_quarters():
    nvda_pkls = stock_lab.utils.TEST_DATA_DIR/"nvda"
    return stock_lab.utils.load_filings_from_dir(nvda_pkls)

@pytest.fixture
def x_quarters():
    x_pkls = stock_lab.utils.TEST_DATA_DIR/"x"
    return stock_lab.utils.load_filings_from_dir(x_pkls)

@pytest.fixture
def nvda_ten_q():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.TEST_DATA_DIR/"nvda/0001045810-24-000316.pkl"
    )

@pytest.fixture
def nvda_ten_k():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.TEST_DATA_DIR/"nvda/0001045810-25-000023.pkl"
    )

@pytest.mark.integration
def test_facts_pipe_ten_q(nvda_ten_q):
    rows = FactsPipe(nvda_ten_q)
    #TODO: Create expected values from spreadsheet and assert against

@pytest.mark.integration
def test_facts_pipe_ten_k(nvda_ten_k):
    rows = FactsPipe(nvda_ten_k)
    #TODO: Create expected values from spreadsheet and assert against

def test_facts_pipe_multiple(appl_quarters,
                             bdl_quarters,
                             nflx_quarters,
                             nvda_quarters,
                             x_quarters):
    for company in (appl_quarters, 
                    nflx_quarters, 
                    nvda_quarters,
                    x_quarters):
        for quarter in company:
            FactsPipe(quarter)
