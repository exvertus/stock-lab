import pytest
import pandas as pd

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.factspipes import (
    FactsPipe, MissingDate, InvalidDate,
    get_rows_matching_first_found_value, get_matching_period_data,
    get_matching_instant_data
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
def test_get_rows_matching_first_found_value(df, candidates, expected):
    actual = get_rows_matching_first_found_value(df, "concept", candidates)
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True),
        expected.reset_index(drop=True)
    )

class TestGetMatchingPeriodData:
    
    @pytest.mark.parametrize("period_data_list,target_end_date,reporting_period_type,expected_result", [
        # Single match
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2']},
                {'type': 'duration', 'end_date': '2023-09-30', 'period_type': 'Quarterly', 'context_ids': ['ctx3']},
            ],
            '2023-12-31',
            'Annual',
            [{'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2']}]
        ),
        # Multiple matches, sorted by context_ids count (descending)
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2', 'ctx3']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2']},
            ],
            '2023-12-31',
            'Annual',
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2', 'ctx3']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
            ]
        ),
        # Quarterly period match
        (
            [
                {'type': 'duration', 'end_date': '2023-09-30', 'period_type': 'Quarterly', 'context_ids': ['ctx1']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx2']},
            ],
            '2023-09-30',
            'Quarterly',
            [{'type': 'duration', 'end_date': '2023-09-30', 'period_type': 'Quarterly', 'context_ids': ['ctx1']}]
        ),
        # Mixed types - only duration types should match
        (
            [
                {'type': 'instant', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx2']},
                {'type': 'other', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx3']},
            ],
            '2023-12-31',
            'Annual',
            [{'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx2']}]
        ),
        # Empty context_ids list
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': []},
            ],
            '2023-12-31',
            'Annual',
            [{'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': []}]
        ),
    ],
    ids=[
            "Single match",
            "Multiple matches, sorted by context_ids count (descending)",
            "Quarterly period match",
            "Mixed types - only duration types should match",
            "Empty context_ids list"
        ])
    def test_successful_matches(self, period_data_list, target_end_date, reporting_period_type, expected_result):
        """Test cases where matches are found and returned correctly."""
        result = get_matching_period_data(period_data_list, target_end_date, reporting_period_type)
        assert result == expected_result

    @pytest.mark.parametrize("period_data_list,target_end_date,reporting_period_type", [
        # No matching end_date
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
            ],
            '2024-12-31',
            'Annual'
        ),
        # No matching period_type
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
            ],
            '2023-12-31',
            'Quarterly'
        ),
        # No matching type (all non-duration)
        (
            [
                {'type': 'instant', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']},
                {'type': 'other', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx2']},
            ],
            '2023-12-31',
            'Annual'
        ),
        # Empty list
        (
            [],
            '2023-12-31',
            'Annual'
        ),
        # No matches for any criteria
        (
            [
                {'type': 'duration', 'end_date': '2022-12-31', 'period_type': 'Quarterly', 'context_ids': ['ctx1']},
            ],
            '2023-12-31',
            'Annual'
        ),
        # Case sensitivity test for period_type
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'annual', 'context_ids': ['ctx1']},
            ],
            '2023-12-31',
            'Annual'
        ),
    ],
    ids=[
        "No matching end_date",
        "No matching period_type",
        "No matching type (all non-duration)",
        "Empty list",
        "No matches for any criteria",
        "Case sensitivity test for period_type",
    ]
    )
    def test_missing_date_exception(self, period_data_list, target_end_date, reporting_period_type):
        """Test cases where MissingDate exception should be raised."""
        with pytest.raises(MissingDate):
            get_matching_period_data(period_data_list, target_end_date, reporting_period_type)

    @pytest.mark.parametrize("period_data_list,target_end_date,reporting_period_type", [
        # Test multiple matches with same context_ids count - order should be stable
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1', 'ctx2'], 'id': 'first'},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx3', 'ctx4'], 'id': 'second'},
            ],
            '2023-12-31',
            'Annual'
        ),
    ],
    ids=["Test multiple matches with same context_ids count - order should be stable"])
    def test_sorting_behavior_detailed(self, period_data_list, target_end_date, reporting_period_type):
        """Test detailed sorting behavior when context_ids counts are equal."""
        result = get_matching_period_data(period_data_list, target_end_date, reporting_period_type)
        
        # Should return both items
        assert len(result) == 2
        
        # Both should have same number of context_ids
        assert len(result[0]['context_ids']) == len(result[1]['context_ids'])
        
        # Order should be preserved from original list when counts are equal
        assert result[0]['id'] == 'first'
        assert result[1]['id'] == 'second'

    def test_context_ids_sorting_edge_cases(self):
        """Test edge cases for context_ids sorting."""
        period_data_list = [
            {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['a']},
            {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['a', 'b', 'c', 'd', 'e']},
            {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': []},
            {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['a', 'b', 'c']},
        ]
        
        result = get_matching_period_data(period_data_list, '2023-12-31', 'Annual')
        
        # Should be sorted by context_ids count: 5, 3, 1, 0
        context_counts = [len(item['context_ids']) for item in result]
        assert context_counts == [5, 3, 1, 0]

    @pytest.mark.parametrize("invalid_data", [
        # Missing required keys
        [{'end_date': '2023-12-31', 'period_type': 'Annual', 'context_ids': ['ctx1']}],  # Missing 'type'
        [{'type': 'duration', 'period_type': 'Annual', 'context_ids': ['ctx1']}],        # Missing 'end_date'
        [{'type': 'duration', 'end_date': '2023-12-31', 'context_ids': ['ctx1']}],       # Missing 'period_type'
        [{'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual'}],       # Missing 'context_ids'
    ])
    def test_invalid_data_structure(self, invalid_data):
        """Test behavior with invalid data structures (missing required keys)."""
        # This test assumes the function will handle missing keys gracefully
        # You may need to adjust based on actual implementation behavior
        with pytest.raises((KeyError, AttributeError)):
            get_matching_period_data(invalid_data, '2023-12-31', 'Annual')

class TestGetMatchingInstantData:
    
    @pytest.mark.parametrize("period_data_list,target_instant_date,expected_result", [
        # Single instant match
        (
            [
                {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['ctx1']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual'},
            ],
            '2023-12-31',
            {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['ctx1']}
        ),
        # Multiple non-instant types ignored
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31'},
                {'type': 'instant', 'date': '2023-09-30', 'context_ids': ['c-188']},
                {'type': 'other', 'some_date': '2023-12-31'},
            ],
            '2023-09-30',
            {'type': 'instant', 'date': '2023-09-30', 'context_ids': ['c-188']}
        ),
        # Instant with minimal data
        (
            [
                {'type': 'instant', 'date': '2023-06-30'},
            ],
            '2023-06-30',
            {'type': 'instant', 'date': '2023-06-30'}
        ),
        # Mixed instant and duration with same dates
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual'},
                {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['c-100']},
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Quarterly'},
            ],
            '2023-12-31',
            {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['c-100']}
        ),
        # Instant with additional fields
        (
            [
                {'type': 'instant', 'date': '2025-02-05', 'label': 'February 05, 2025', 'context_ids': ['c-188'], 'key': 'instant_2025-02-05'},
            ],
            '2025-02-05',
            {'type': 'instant', 'date': '2025-02-05', 'label': 'February 05, 2025', 'context_ids': ['c-188'], 'key': 'instant_2025-02-05'}
        ),
    ], ids=[
        "single_instant_match",
        "multiple_non_instant_types_ignored", 
        "instant_with_minimal_data",
        "mixed_instant_and_duration_same_dates",
        "instant_with_additional_fields"
    ])
    def test_successful_matches(self, period_data_list, target_instant_date, expected_result):
        """Test cases where a single instant match is found and returned correctly."""
        result = get_matching_instant_data(period_data_list, target_instant_date)
        assert result == expected_result

    @pytest.mark.parametrize("period_data_list,target_instant_date", [
        # No matching date
        (
            [
                {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['ctx1']},
            ],
            '2024-12-31'
        ),
        # No instant type dictionaries
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual'},
                {'type': 'other', 'some_date': '2023-12-31'},
            ],
            '2023-12-31'
        ),
        # Empty list
        (
            [],
            '2023-12-31'
        ),
        # Multiple types but no instant matches
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31'},
                {'type': 'instant', 'date': '2022-12-31'},
                {'type': 'other', 'date': '2023-12-31'},
            ],
            '2023-12-31'
        ),
        # None values
        (
            [
                {'type': None, 'date': '2023-12-31'}
            ],
            '2023-12-31'),
        # Empty type
        (
            [{'type': '', 'date': '2023-12-31'}],
            '2023-12-31'
        )
    ], ids=[
        "no_matching_date",
        "no_instant_type_dictionaries",
        "empty_list",
        "multiple_types_no_instant_matches",
        "none_type_value", 
        "empty_type_value"
    ])
    def test_missing_date_exception(self, period_data_list, target_instant_date):
        """Test cases where MissingDate exception should be raised."""
        with pytest.raises(MissingDate):
            get_matching_instant_data(period_data_list, target_instant_date)

    @pytest.mark.parametrize("period_data_list,target_instant_date", [
        # Two instant matches for same date
        (
            [
                {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['ctx1']},
                {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['ctx2']},
            ],
            '2023-12-31'
        ),
        # Multiple instant matches with different additional data
        (
            [
                {'type': 'instant', 'date': '2023-09-30', 'context_ids': ['c-100']},
                {'type': 'instant', 'date': '2023-09-30', 'context_ids': ['c-200']},
                {'type': 'instant', 'date': '2023-09-30', 'context_ids': ['c-300']},
            ],
            '2023-09-30'
        ),
        # Multiple instant matches mixed with other types
        (
            [
                {'type': 'duration', 'end_date': '2023-12-31'},
                {'type': 'instant', 'date': '2023-12-31', 'key': 'instant_first'},
                {'type': 'instant', 'date': '2023-12-31', 'key': 'instant_second'},
                {'type': 'other', 'date': '2023-12-31'},
            ],
            '2023-12-31'
        ),
    ], ids=[
        "two_instant_matches_same_date",
        "multiple_instant_matches_different_contexts",
        "multiple_instant_matches_mixed_types"
    ])
    def test_invalid_date_exception(self, period_data_list, target_instant_date):
        """Test cases where InvalidDate exception should be raised due to multiple matches."""
        with pytest.raises(InvalidDate):
            get_matching_instant_data(period_data_list, target_instant_date)

    @pytest.mark.parametrize("invalid_data", [
        # Missing 'type' key
        [{'date': '2023-12-31', 'context_ids': ['ctx1']}],
        # Instant type but no date key
        [{'type': 'instant', 'other_date': '2023-12-31'}],
    ], ids=[
        "missing_type_key",
        "instant_type_missing_date_key",
    ])
    def test_invalid_data_structure(self, invalid_data):
        """Test behavior with invalid data structures."""
        # Behavior may vary based on implementation - adjust as needed
        with pytest.raises((KeyError, AttributeError, TypeError)):
            get_matching_instant_data(invalid_data, '2023-12-31')

    def test_non_instant_without_date_key(self):
        """Test that non-instant dictionaries can safely lack date key."""
        period_data_list = [
            {'type': 'duration', 'end_date': '2023-12-31', 'period_type': 'Annual'},  # No date key
            {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['c-100']},
            {'type': 'other', 'some_field': 'value'},  # No date key
        ]
        
        result = get_matching_instant_data(period_data_list, '2023-12-31')
        assert result == {'type': 'instant', 'date': '2023-12-31', 'context_ids': ['c-100']}

    def test_case_sensitivity(self):
        """Test that type matching is case sensitive."""
        period_data_list = [
            {'type': 'Instant', 'date': '2023-12-31'},  # Wrong case
            {'type': 'INSTANT', 'date': '2023-12-31'},  # Wrong case
        ]
        
        with pytest.raises(MissingDate):
            get_matching_instant_data(period_data_list, '2023-12-31')

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
                    bdl_quarters,
                    nflx_quarters, 
                    nvda_quarters,
                    x_quarters):
        for quarter in company:
            FactsPipe(quarter)
