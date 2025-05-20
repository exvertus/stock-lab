import pytest
import pandas as pd
import numpy as np

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.facts import ( 
    FilingFacts, MissingFact, InvalidFact, values_to_num, values_not_negative,
    duration_to_date, instant_to_date, err_if_none_in_column
)

# ---------------- Unit tests ----------------

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
            "value": [80000000, 17, 8.41, 4.17]
        }),
        pd.DataFrame({
            "value": [80000000, 17, 8.41, 4.17]
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
    # TODO: Raise exception from new class var
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

first_concepts = [val["tags"][0] for val in FilingFacts.gaap_tags.values()]
last_concepts = [val["tags"][-1] for val in FilingFacts.gaap_tags.values()]
period_ends = ["2020-10-01" if val['period_type'] == "duration" else "" 
               for val in FilingFacts.gaap_tags.values()]
period_instants = ["2020-10-01" if val['period_type'] == "instant" else "" 
                   for val in FilingFacts.gaap_tags.values()]
period_types = [val["period_type"] for val in FilingFacts.gaap_tags.values()]

@pytest.mark.parametrize("filing_df, expected_df", [
    # Ideal case: single first-matches for each tag
    (
        pd.DataFrame({
            "concept": first_concepts,
            "value": [str(i) for i in range(len(first_concepts))],
            "period_end": period_ends,
            "period_instant": period_instants,
            "period_type": period_types
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": first_concepts,
            "value": [str(i) for i in range(len(first_concepts))],
            "period_end": period_ends,
            "period_instant": period_instants,
            "period_type": period_types
        })
    ),

    # Acceptable case: last concept matches
    (
        pd.DataFrame({
            "concept": last_concepts,
            "value": [str(i) for i in range(len(last_concepts))],
            "period_end": ["2020-10-01"] * len(last_concepts),
            "period_instant": period_instants,
            "period_type": period_types
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": last_concepts,
            "value": [str(i) for i in range(len(last_concepts))],
            "period_end": ["2020-10-01"] * len(last_concepts),
            "period_instant": period_instants,
            "period_type": period_types
        })
    ),
])
def test_get_rows(filing_df, expected_df):
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
        "value": [str(i) for i in range(len(first_concepts) - 1)],
        "period_end": ["2020-10-01"] * (len(first_concepts) - 1),
        "period_instant": period_instants[1:],
        "period_type": period_types[1:]
    }),

    # Empty input dataframe raises exception
    pd.DataFrame(),

    # Rows found but value is empty
    pd.DataFrame({
        "concept": first_concepts,
        "value": [""] * len(first_concepts),
        "period_end": ["2020-10-01"] * len(first_concepts),
        "period_instant": period_instants,
        "period_type": period_types
    }),
])
def test_get_rows_raises_mf(filing_df):
    ff = FilingFacts(filing_df)
    with pytest.raises(MissingFact):
        ff.get_rows()

@pytest.mark.parametrize("filing_df", [
    # Filing with acceptable values should not raise an error
    (
        pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "1000000", # revenue
                "1.23",    # eps
                "400000",  # diluted_shares
                "400",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "3000",    # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_instant": period_instants,
            "period_type": period_types
        })
    )
])
def test_get_rows_validation_clean(filing_df):
    ff = FilingFacts(filing_df)
    ff.get_rows()

# @pytest.mark.parametrize("filing_df", [
#     # Revenue must be >= 0
#     (
#         pd.DataFrame({
#             "concept": first_concepts,
#             "value": [
#                 "-100000", # revenue
#                 "1.23",    # eps
#                 "400000",  # diluted_shares
#                 "400",     # net_income
#                 "500",     # operating_income
#                 "234",     # operating_cash_flow
#                 "3000",    # cap_ex
#                 "240",     # gross_profit
#                 "30000"    # cash_equivalents
#             ],
#             "period_end": period_ends,
#             "period_instant": period_instants,
#             "period_type": period_types
#         })
#     ),

#     # EPS must be numeric
#     # Diluted shares > 0
#     # Net income must be numeric
#     # Operating income must be numeric
#     # Operating cash flow must be numeric
#     # Gross profit must be numeric
#     # Cash equivalents must be >= 0
# ])
# def test_get_rows_validation_raises(filing_df):
#     ff = FilingFacts(filing_df)
#     with pytest.raises(InvalidFact):
#         ff.get_rows()

# ------------- Integration tests -------------

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
    FilingFacts(ten_q_df).parse()

@pytest.mark.integration
def test_filings_facts_ten_k(nvda_ten_k):
    ten_k_df = XBRL.from_filing(nvda_ten_k).facts.to_dataframe()
    FilingFacts(ten_k_df).parse()
