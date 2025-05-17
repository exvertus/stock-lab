import pytest
import pandas as pd

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.facts import FilingFacts, MissingFact

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
    (
        "us-gaap:Revenues",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues", "us-gaap:CostOfRevenue"],
            "value": ["2000", "3000", "1000"],
            "period_end": ["2024-01-29", "2024-10-27", "2024-11-27"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["3000"],
            "period_end": ["2024-10-27"]
        })
    ),

    # No matching concept
    (
        "us-gaap:NetIncomeLoss",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:CostOfRevenue"],
            "value": ["3000", "1000"],
            "period_end": ["2024-10-27", "2024-11-27"]
        }),
        pd.DataFrame(columns=["concept", "value", "period_end"])
    ),

    # Latest date "tie"
    (
        "us-gaap:Revenues",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", "2024-10-27"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", "2024-10-27"]
        })
    ),

    # Ignore missing period_end
    (
        "us-gaap:Revenues",
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:Revenues"],
            "value": ["3000", "4000"],
            "period_end": ["2024-10-27", None]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["3000"],
            "period_end": ["2024-10-27"]
        })
    ),

])
def test_get_for_latest_end_dates(concept, df_in, df_expected):
    ff = FilingFacts(df_in)
    actual_df = ff.get_for_latest_end_dates(concept)
    pd.testing.assert_frame_equal(
        actual_df.reset_index(drop=True), df_expected.reset_index(drop=True))

@pytest.mark.parametrize("gaap_tags, df_in, df_expected", [
    # Ideal case: first tag matches
    (
        ("us-gaap:Revenues", "us-gaap:SalesRevenueNet",),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues", "us-gaap:SalesRevenueNet"],
            "value": ["111", "222"],
            "period_end": ["2024-10-27", "2024-01-01"]
        }),
        pd.DataFrame({
            "concept": ["us-gaap:Revenues"],
            "value": ["111"],
            "period_end": ["2024-10-27"]
        })
    ),

    # Fallback case: first tag not found
    (
        ["tag1", "tag2"],
        pd.DataFrame({
            "concept": ["tag2"],
            "value": ["222"],
            "period_end": ["2024-01-01"]
        }),
        pd.DataFrame({
            "concept": ["tag2"],
            "value": ["222"],
            "period_end": ["2024-01-01"]
        })
    ),

    # No tags match
    (
        ["tag1", "tag2"],
        pd.DataFrame({
            "concept": ["tag3"],
            "value": ["333"],
            "period_end": ["2024-01-01"]
        }),
        pd.DataFrame(columns=["concept", "value", "period_end"])
    ),

    # Multiple first-matches
    (
        ["tag1"],
        pd.DataFrame({
            "concept": ["tag1", "tag1", "tag1"],
            "value": ["100", "200", "300"],
            "period_end": ["2024-10-27", "2024-10-27", "2023-12-31"]
        }),
        pd.DataFrame({
            "concept": ["tag1", "tag1"],
            "value": ["100", "200"],
            "period_end": ["2024-10-27", "2024-10-27"]
        })
    ),

    # Missing period_end
    (
        ["tag1"],
        pd.DataFrame({
            "concept": ["tag1", "tag1"],
            "value": ["111", "222"],
            "period_end": ["2024-10-27", None]
        }),
        pd.DataFrame({
            "concept": ["tag1"],
            "value": ["111"],
            "period_end": ["2024-10-27"]
        })
    ),
])
def test_seek_tags_until_found(gaap_tags, df_in, df_expected):
    ff = FilingFacts(df_in)
    actual = ff.seek_tags_until_found(gaap_tags)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        df_expected.reset_index(drop=True)
    )

first_concepts = [val[0] for val in FilingFacts.gaap_tags.values()]
last_concepts = [val[-1] for val in FilingFacts.gaap_tags.values()]
@pytest.mark.parametrize("filing_df, expected_df", [
    # Ideal case: single first-matches for each tag
    (
        pd.DataFrame({
            "concept": first_concepts,
            "value": [str(i) for i in range(len(first_concepts))],
            "period_end": ["2020-10-01"] * len(first_concepts)
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": first_concepts,
            "value": [str(i) for i in range(len(first_concepts))],
            "period_end": ["2020-10-01"] * len(first_concepts)
        })
    ),

    # Acceptable case: last concept matches
    (
        pd.DataFrame({
            "concept": last_concepts,
            "value": [str(i) for i in range(len(last_concepts))],
            "period_end": ["2020-10-01"] * len(last_concepts)
        }),
        pd.DataFrame({
            "fact_type": list(FilingFacts.gaap_tags.keys()),
            "concept": last_concepts,
            "value": [str(i) for i in range(len(last_concepts))],
            "period_end": ["2020-10-01"] * len(last_concepts)
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
        "period_end": ["2020-10-01"] * (len(first_concepts) - 1)
    }),

    # Empty input dataframe raises exception
    pd.DataFrame(),

    # Rows found but value is empty
    pd.DataFrame({
        "concept": first_concepts,
        "value": [""] * len(first_concepts),
        "period_end": ["2020-10-01"] * len(first_concepts)
    }),
])
def test_get_rows_raises(filing_df):
    ff = FilingFacts(filing_df)
    with pytest.raises(MissingFact):
        ff.get_rows()

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
    FilingFacts(ten_q_df).parse()

@pytest.mark.integration
def test_filings_facts_ten_k(nvda_ten_k):
    ten_k_df = XBRL.from_filing(nvda_ten_k).facts.to_dataframe()
    FilingFacts(ten_k_df).parse()
