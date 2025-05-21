import pytest
import pandas as pd

from stock_lab.factspipes import (
    match_first_in_column
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
