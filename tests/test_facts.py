import pytest
import pandas as pd
import numpy as np

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.facts import ( 
    FilingFacts, MissingFact, InvalidFact, values_to_num, values_not_negative,
    duration_to_date, instant_to_date, err_if_none_in_column, values_positive,
    values_non_positive
)

from tests.test_data import (
    first_concepts, last_concepts, period_ends, period_instants, period_types,
    period_starts, negative_revenue, eps_non_number, zero_shares, 
    income_non_numeric, op_income_non_numeric, op_cash_non_numeric,
    cap_ex_positive, gross_profit_non_numeric, negative_cash_eq,
    acceptable_values, acceptable_results, period_starts_results,
    period_ends_results, period_instants_results
)

# -----------------------------------------------------------------------------
#                                   Unit Tests
# -----------------------------------------------------------------------------


# ------------- Single-field validators -------------

@pytest.mark.parametrize("column_name, df", [
    # If all elements in a column are not none-like, do not raise exception.
    (
        "value",
        pd.DataFrame({
                "value": ["14", 12, "something", "not nothing"]
            })
    ),

    # Other columns may contain blank values without raising exception.
    (
        "column_with_values",
        pd.DataFrame({
                "column_with_values": ["14", 12, "something", "not nothing"],
                "column_without": [None, "", "   ", pd.NA]
            })
    )
])
def test_err_if_none_in_column(column_name, df):
    err_if_none_in_column(column_name, df)

@pytest.mark.parametrize("column_name, df", [
    # None should raise MissingFact
    (
        "value",
        pd.DataFrame({
                "value": ["14", 12, "something", None]
            })
    ),

    # Numpy nan should raise MissingFact
    (
        "value",
        pd.DataFrame({
                "value": ["14", np.nan, "something", "everything"]
            })
    ),

    # Nan float type should raise MissingFact
    (
        "value",
        pd.DataFrame({
                "value": [float('nan'), "whatever", "something", "everything"]
            })
    ),

    # Empty string should raise MissingFact
    (
        "value",
        pd.DataFrame({
                "value": ["14", 6635, "", "exists"]
            })
    ),

    # All-whitespace string should raise MissingFact
    (
        "column_name",
        pd.DataFrame({
                "column_name": ["\t", 6635, "this", "exists"]
            })
    ),
])
def test_err_if_none_in_column_raises(column_name, df):
    with pytest.raises(MissingFact):
        err_if_none_in_column(column_name, df)

@pytest.mark.parametrize("df, expected", [
    # Numeric values should be converted
    (
        pd.DataFrame({
            "value": ["17", "8.41", "-4.17"]
        }),
        pd.DataFrame({
            "value": [17, 8.41, -4.17]
        })
    ),
])
def test_values_to_num(df, expected):
    actual_df = values_to_num(df)
    pd.testing.assert_frame_equal(
        actual_df.reset_index(drop=True), expected.reset_index(drop=True))

@pytest.mark.parametrize("df", [
    pd.DataFrame({
            "value": ["17", "8.41", "not a numeric"]
        }),
])
def test_values_to_num_raises(df):
    with pytest.raises(InvalidFact):
        values_to_num(df)

@pytest.mark.parametrize("df, expected", [
    # Non-negative input should no-op
    (
        pd.DataFrame({
            "value": [80000000, 0, 8.41, 4.17]
        }),
        pd.DataFrame({
            "value": [80000000, 0, 8.41, 4.17]
        })
    ),
])
def test_values_not_negative(df, expected):
    pd.testing.assert_frame_equal(
        values_not_negative(df).reset_index(drop=True),
        expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("df", [
    # Negative numbers should raise InvalidFact
    (
        pd.DataFrame({
            "value": [80000000, 17, 8.41, 4.17, -7000]
        })
    ),
])
def test_values_not_negative_raises(df):
    with pytest.raises(InvalidFact):
        values_not_negative(df)

@pytest.mark.parametrize("df, expected", [
    # Positive input should no-op
    (
        pd.DataFrame({
            "value": [80000000, 17, 0.01, 4.17]
        }),
        pd.DataFrame({
            "value": [80000000, 17, 0.01, 4.17]
        })
    ),
])
def test_values_positive(df, expected):
    pd.testing.assert_frame_equal(
        values_positive(df).reset_index(drop=True),
        expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("df", [
    # Zero should raise InvalidFact
    pd.DataFrame({
        "value": [80000000, 17, 0.00, 4.17]
    }),

    # Negative should raise InvalidFact
    pd.DataFrame({
        "value": [80000000, -17, 0.01, 4.17]
    }),
])
def test_values_positive_raises(df):
    with pytest.raises(InvalidFact):
        values_positive(df)

@pytest.mark.parametrize("df, expected", [
    # Non-positive input should no-op
    (
        pd.DataFrame({
            "value": [-80000000, -17, 0.00, -4.17]
        }),
        pd.DataFrame({
            "value": [-80000000, -17, 0.00, -4.17]
        })
    ),
])
def test_values_non_positive(df, expected):
    pd.testing.assert_frame_equal(
        values_non_positive(df).reset_index(drop=True),
        expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("df", [
    # Positive should raise InvalidFact
    pd.DataFrame({
        "value": [-80000000, -17, 0.00, 4.17]
    }),
])
def test_values_positive_raises(df):
    with pytest.raises(InvalidFact):
        values_non_positive(df)

@pytest.mark.parametrize("df, expected", [
    (
        pd.DataFrame({
            "period_start": ["2024-01-01", "2023-04-01"],
            "period_end": ["2024-03-31", "2024-03-31"]
        }),
        pd.DataFrame({
            "period_start": [
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2023-04-01")
            ],
            "period_end": [
                pd.Timestamp("2024-03-31"),
                pd.Timestamp("2024-03-31")
            ]
        }),
    ),
])
def test_duration_to_date(df, expected):
    actual = duration_to_date(df)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("df", [
    # An invalid date in period_end should raise InvalidFact
    pd.DataFrame({
        "period_start": ["2024-01-01", "2023-04-01"],
        "period_end": ["2024-03-31", "applesauce"]
    }),

    # An invalid date in period_start should raise InvalidFact
    pd.DataFrame({
        "period_start": ["2024-01-01", "November 2020"],
        "period_end": ["2024-03-31", "2023-04-01"]
    }),
])
def test_duration_to_date_raises_invalid(df):
    with pytest.raises(InvalidFact):
        duration_to_date(df)

@pytest.mark.parametrize("df", [
    # A nil value for a date should raise InvalidFact
    pd.DataFrame({
        "period_start": ["2024-01-01", "2023-04-01"],
        "period_end": ["2024-03-31", ""]
    }),

    # A nan value for a date should raise InvalidFact
    pd.DataFrame({
        "period_start": ["2024-01-01", float('nan')],
        "period_end": ["2024-03-31", "2023-04-01"]
    }),
])
def test_duration_to_date_raises_missing(df):
    with pytest.raises(MissingFact):
        duration_to_date(df)

@pytest.mark.parametrize("df, expected", [
    # Valid dates should return converted dates
    (
        pd.DataFrame({
            "period_instant": ["2024-01-01", "2023-04-01"]
        }),
        pd.DataFrame({
            "period_instant": [
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2023-04-01")
            ]
        }),
    ),
])
def test_instant_to_date(df, expected):
    actual = instant_to_date(df)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("df", [
    # An invalid date in period_end should raise InvalidFact
    pd.DataFrame({
        "period_instant": ["2024-01-01", "today-3"]
    }),

    # An invalid date in period_start should raise InvalidFact
    pd.DataFrame({
        "period_instant": ["2024-01-01", "November 2020"]
    }),
])
def test_instant_to_date_raises_invalid(df):
    with pytest.raises(InvalidFact):
        instant_to_date(df)

@pytest.mark.parametrize("df", [
    # Only whitespace for a date should raise InvalidFact
    pd.DataFrame({
        "period_instant": ["2024-01-01", " "]
    }),

    # A nan value for a date should raise InvalidFact
    pd.DataFrame({
        "period_instant": ["2024-01-01", float('nan')]
    }),
])
def test_instant_to_date_raises_missing(df):
    with pytest.raises(MissingFact):
        instant_to_date(df)

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

# ------------- Getter methods -------------

@pytest.mark.parametrize("concept, target_date, df_in, df_expected",[
    # Ideal case: multiple rows but only one latest end_date
    (
        "us-gaap:Revenues",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues", "us-gaap:CostOfRevenue"],
            "value": ["2000", "3000", "1000"],
            "period_end": ["2024-01-29", "2024-10-27", "2024-11-27"],
            "period_type": ["duration", "duration", "duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["3000"],
            "period_end": ["2024-10-27"],
            "period_type": ["duration"]
        })
    ),

    # No matching concept
    (
        "us-gaap:NetIncomeLoss",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:CostOfRevenue"],
            "value": ["3000", "1000"],
            "period_end": ["2024-10-27", "2024-11-27"],
            "period_type": ["duration", "duration"]
        }),
        pd.DataFrame(columns=["concept", "value", "period_end", "period_type"])
    ),

    # Latest date "tie"
    (
        "us-gaap:Revenues",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", "2024-10-27"],
            "period_type": ["duration", "duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", "2024-10-27"],
            "period_type": ["duration", "duration"]
        })
    ),

    # Ignore missing period_end
    (
        "us-gaap:Revenues",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", None],
            "period_type": ["duration", "duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["3000"],
            "period_end": ["2024-10-27"],
            "period_type": ["duration"]
        })
    ),

    # Instant date type
    (
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "period_instant",
        pd.DataFrame({
            "concept": ["us-gaap:CashAndCashEquivalentsAtCarryingValue", 
                        "us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "value": ["3000", "4000"],
            "period_instant": ["2024-10-27", "2023-10-27"],
            "period_type": ["instant", "instant"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "value": ["3000"],
            "period_instant": ["2024-10-27"],
            "period_type": ["instant"]
        })
    ),

])
def test_get_for_latest_date(concept, target_date, df_in, df_expected):
    ff = FilingFacts(df_in)
    actual_df = ff.get_for_latest_date(concept, target_date)
    pd.testing.assert_frame_equal(
        actual_df.reset_index(drop=True), df_expected.reset_index(drop=True))

@pytest.mark.parametrize("concept, target_date, mismatched_df", [
    # Revenues should be a duration
    (
        "us-gaap:Revenues",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["2000"],
            "period_end": ["2024-01-29"],
            "period_type": ["instant"]
        }),
    ),

    # Cash should be an instant
    (
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "period_instant",
        pd.DataFrame({
            "concept": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "value": ["3000"],
            "period_instant": ["2024-10-27"],
            "period_type": ["duration"]
        }),
    ),

    # Mixed types under the same target_date should raise error
    (
        "us-gaap:Revenues",
        "period_end",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["2000", "1000"],
            "period_end": ["2024-01-29", "2024-01-29"],
            "period_type": ["instant", "duration"]
        }),
    ),
])
def test_get_for_latest_date_raises(concept, target_date, mismatched_df):
    ff = FilingFacts(mismatched_df)
    with pytest.raises(InvalidFact):
        ff.get_for_latest_date(concept, target_date)

@pytest.mark.parametrize("gaap_dict, df_in, df_expected", [
    # Ideal case: first tag matches
    (
        {"period_type": "duration",
         "tags": ("us-gaap:Revenues", "us-gaap:SalesRevenueNet",)},
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:SalesRevenueNet"],
            "value": ["111", "222"],
            "period_end": ["2024-10-27", "2024-01-01"],
            "period_type": ["duration", "duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["111"],
            "period_end": ["2024-10-27"],
            "period_type": ["duration"]
        })
    ),

    # Fallback case: first tag not found
    (
        {"period_type": "duration",
         "tags": ("us-gaap:Revenues", "us-gaap:SalesRevenueNet",)},
        pd.DataFrame({
            "concept": ["us-gaap:SalesRevenueNet"],
            "value": ["222"],
            "period_end": ["2024-01-01"],
            "period_type": ["duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:SalesRevenueNet"],
            "value": ["222"],
            "period_end": ["2024-01-01"],
            "period_type": ["duration"]
        })
    ),

    # No tags match
    (
        {"period_type": "duration",
         "tags": ("us-gaap:EarningsPerShareDiluted", "us-gaap:EarningsPerShareBasicAndDiluted")},
        pd.DataFrame({
            "concept": ["us-gaap:EarningsPerShareBasic"],
            "value": ["333"],
            "period_end": ["2024-01-01"],
            "period_type": ["duration"]
        }),
        pd.DataFrame(columns=["concept", "value", "period_end", "period_type"])
    ),

    # Multiple first-tag matches should take latest date
    (
        {"period_type": "duration",
         "tags": ("us-gaap:NetIncomeLoss",)},
        pd.DataFrame({
            "concept": ["us-gaap:NetIncomeLoss", "us-gaap:NetIncomeLoss", "us-gaap:NetIncomeLoss"],
            "value": ["100", "200", "300"],
            "period_end": ["2024-10-27", "2024-10-27", "2023-12-31"],
            "period_type": ["duration", "duration", "duration"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:NetIncomeLoss", "us-gaap:NetIncomeLoss"],
            "value": ["100", "200"],
            "period_end": ["2024-10-27", "2024-10-27"],
            "period_type": ["duration", "duration"],
        })
    ),

    # Missing period_end should be ignored"us-gaap:OperatingIncomeLoss"
    (
        {"period_type": "instant",
         "tags": ("us-gaap:CashAndCashEquivalentsAtCarryingValue",)},
        pd.DataFrame({
            "concept": ["us-gaap:CashAndCashEquivalentsAtCarryingValue", "us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "value": ["111", "222"],
            "period_instant": ["2024-10-27", None],
            "period_type": ["instant", "instant"],
        }),
        pd.DataFrame({
            "concept": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
            "value": ["111"],
            "period_instant": ["2024-10-27"],
            "period_type": ["instant"]
        })
    ),
])
def test_seek_tags_until_found(gaap_dict, df_in, df_expected):
    ff = FilingFacts(df_in)
    actual = ff.seek_tags_until_found(gaap_dict)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        df_expected.reset_index(drop=True)
    )

@pytest.mark.parametrize("filing_df, expected_df", [
    # Ideal case: single first-matches for each tag
    (
        pd.DataFrame({
            "concept": first_concepts,
            "value": acceptable_values,
            "period_start": period_starts,
            "period_end": period_ends,
            "period_instant": period_instants,
            "period_type": period_types
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": first_concepts,
            "value": acceptable_results,
            "period_start": period_starts_results,
            "period_end": period_ends_results,
            "period_instant": period_instants_results,
            "period_type": period_types
        })
    ),

    # Acceptable case: last concept matches
    (
        pd.DataFrame({
            "concept": last_concepts,
            "value": acceptable_values,
            "period_start": period_starts,
            "period_end": period_ends,
            "period_instant": period_instants,
            "period_type": period_types
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": last_concepts,
            "value": acceptable_results,
            "period_start": period_starts_results,
            "period_end": period_ends_results,
            "period_instant": period_instants_results,
            "period_type": period_types
        })
    ),
])
def test_get_rows_single(filing_df, expected_df):
    ff = FilingFacts(filing_df)
    actual = ff.get_rows()
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected_df.reset_index(drop=True)
    )

@pytest.mark.parametrize("filing_df", [
    # Single missing row for all concepts under one gaap_tags key
    # raises exception
    pd.DataFrame({
        "concept": first_concepts[1:],
        "value": acceptable_values[1:],
        "period_start": period_starts[1:],
        "period_end": period_ends[1:],
        "period_instant": period_instants[1:],
        "period_type": period_types[1:]
    }),

    # Empty input dataframe raises exception
    pd.DataFrame(),

    # Rows all present but value is empty
    pd.DataFrame({
        "concept": first_concepts,
        "value": [float('nan')] * len(first_concepts),
        "period_start": period_starts,
        "period_end": period_ends,
        "period_instant": period_instants,
        "period_type": period_types
    }),
])
def test_get_rows_raises_mf(filing_df):
    ff = FilingFacts(filing_df)
    with pytest.raises(MissingFact):
        ff.get_rows()

@pytest.mark.parametrize("filing_df", [
    # Revenue must be >= 0
    (negative_revenue),

    # EPS must be numeric
    (eps_non_number),

    # Diluted shares must be > 0
    (zero_shares),

    # Net income must be numeric
    (income_non_numeric),

    # Operating income must be numeric
    (op_income_non_numeric),

    # Operating cash flow must be numeric
    (op_cash_non_numeric),

    # Cap_ex must be not be positive
    (cap_ex_positive),

    # Gross profit must be numeric
    (gross_profit_non_numeric),

    # Cash equivalents must be >= 0
    (negative_cash_eq),
])
def test_get_rows_invalid(filing_df):
    ff = FilingFacts(filing_df)
    with pytest.raises(InvalidFact):
        ff.get_rows()

# -----------------------------------------------------------------------------
#                               Integration tests
# -----------------------------------------------------------------------------

@pytest.fixture
def nvda_quarters():
    nvda_pkls = stock_lab.utils.REPO_ROOT/"tests/data/nvda"
    return stock_lab.utils.load_filings_from_dir(nvda_pkls)

@pytest.fixture
def nvda_ten_q():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-24-000316.pkl"
    )

@pytest.fixture
def nvda_ten_k():
    return stock_lab.utils.load_filing_from_file(
        stock_lab.utils.REPO_ROOT/"tests/data/nvda/0001045810-25-000023.pkl"
    )

@pytest.mark.integration
def test_filings_facts_ten_q(nvda_ten_q):
    ten_q_df = XBRL.from_filing(nvda_ten_q).facts.to_dataframe()
    rows = FilingFacts(ten_q_df).get_rows()
    #TODO: Create expected values from spreadsheet and assert against

@pytest.mark.integration
def test_filings_facts_ten_k(nvda_ten_k):
    ten_k_df = XBRL.from_filing(nvda_ten_k).facts.to_dataframe()
    rows = FilingFacts(ten_k_df).get_rows()
    #TODO: Create expected values from spreadsheet and assert against
