import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import datetime

from edgar.xbrl.xbrl import XBRL

import stock_lab.utils
from stock_lab.facts_normalizer import (
    XBRLFactsNormalizer, MissingDate, InvalidDate, FilingDataError,
    get_rows_matching_first_found_value, get_matching_period_data,
    get_matching_instant_data
)

# # -----------------------------------------------------------------------------
# #                                 Unit tests
# # -----------------------------------------------------------------------------

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

@pytest.fixture
def valid_periods():
    """Valid period data for period testing."""
    return [
        {
            'type': 'instant', 
            'date': '2024-12-31', 
            'context_ids': ['c-1'], 
            'key': 'instant_2024-12-31'
        },
        {
            'type': 'duration',
            'start_date': '2024-10-02',
            'end_date': '2024-12-31', 
            'days': 90, 
            'period_type': 'Quarterly',
            'context_ids': ['c-2', 'c-3', 'c-4'], 
            'key': 'duration_2024-07-29_2024-12-31'
        },
        {
            'type': 'duration',
            'start_date': '2024-10-03',
            'end_date': '2024-12-31', 
            'days': 90, 
            'period_type': 'Quarterly',
            'context_ids': ['c-8', 'c-9', 'c-10'], 
            'key': 'duration_2024-07-29_2024-12-31'
        },
        {
            'type': 'duration', 
            'start_date': '2023-12-31',
            'end_date': '2024-12-31', 
            'days': 365, 
            'period_type': 'Annual',
            'context_ids': ['c-5', 'c-6'], 
            'key': 'duration_2024-01-01_2024-12-31'
        }
    ]

@pytest.fixture
def invalid_periods():
    """Unexpected double instant on same date."""
    return [
        {
            'type': 'instant', 
            'date': '2024-12-31', 
            'context_ids': ['c-1'], 
            'key': 'instant_2024-12-31'
        },
        {
            'type': 'instant', 
            'date': '2024-12-31', 
            'context_ids': ['c-8'], 
            'key': 'instant_2024-12-31'
        },
        {
            'type': 'duration',
            'start_date': '2024-10-02',
            'end_date': '2024-12-31', 
            'days': 90, 
            'period_type': 'Quarterly',
            'context_ids': ['c-2', 'c-3', 'c-4'], 
            'key': 'duration_2024-07-29_2024-12-31'
        },
        {
            'type': 'duration', 
            'start_date': '2023-12-31',
            'end_date': '2024-12-31', 
            'days': 365, 
            'period_type': 'Annual',
            'context_ids': ['c-5', 'c-6'], 
            'key': 'duration_2024-01-01_2024-12-31'
        }
    ]

@pytest.fixture
def missing_periods():
    """Missing duration period data."""
    return [
        {
            'type': 'instant', 
            'date': '2024-12-31', 
            'context_ids': ['c-1'], 
            'key': 'instant_2024-12-31'
        }
    ]

@pytest.fixture
def missing_context_ids():
    """Valid period data for period testing."""
    return [
        {
            'type': 'instant', 
            'date': '2024-12-31', 
            'context_ids': ['c-1'], 
            'key': 'instant_2024-12-31'
        },
        {
            'type': 'duration',
            'start_date': '2024-10-02',
            'end_date': '2024-12-31', 
            'days': 90, 
            'period_type': 'Quarterly',
            'context_ids': [], 
            'key': 'duration_2024-07-29_2024-12-31'
        },
        {
            'type': 'duration',
            'start_date': '2024-10-03',
            'end_date': '2024-12-31', 
            'days': 90, 
            'period_type': 'Quarterly',
            'context_ids': [], 
            'key': 'duration_2024-07-29_2024-12-31'
        },
        {
            'type': 'duration', 
            'start_date': '2023-12-31',
            'end_date': '2024-12-31', 
            'days': 365, 
            'period_type': 'Annual',
            'context_ids': [], 
            'key': 'duration_2024-01-01_2024-12-31'
        }
    ]

@pytest.fixture
def mock_xbrl(valid_periods):
    """Mock XBRL object with valid entity info."""
    xbrl = Mock()
    xbrl.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-Q'
    }
    xbrl.period_of_report = '2024-12-31'
    xbrl.reporting_periods = valid_periods
    return xbrl

@pytest.fixture
def mock_xbrl_10_k(valid_periods):
    """Mock XBRL object with valid 10-K entity info."""
    xbrl = Mock()
    xbrl.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-K'
    }
    xbrl.period_of_report = '2024-12-31'
    xbrl.reporting_periods = valid_periods
    return xbrl

@pytest.fixture
def mock_xbrl_ten_q_missing_durations(missing_periods):
    """Mock XBRL object with missing duration periods."""
    xbrl = Mock()
    xbrl.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-Q'
    }
    xbrl.period_of_report = '2024-12-31'
    xbrl.reporting_periods = missing_periods
    return xbrl

@pytest.fixture
def mock_xbrl_no_context(missing_context_ids):
    """Mock XBRL object with missing context ids."""
    xbrl = Mock()
    xbrl.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-Q'
    }
    xbrl.period_of_report = '2024-12-31'
    xbrl.reporting_periods = missing_context_ids
    return xbrl

@pytest.fixture
def mock_xbrl_invalid(invalid_periods):
    """Mock XBRL object with invalid period data."""
    xbrl = Mock()
    xbrl.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-Q'
    }
    xbrl.period_of_report = '2024-12-31'
    xbrl.reporting_periods = invalid_periods
    return xbrl

@pytest.fixture
def mock_filing():
    """Mock filing object with all required data."""
    filing = Mock()
    filing.accession_no = '0000320193-24-000456'
    return filing

@pytest.fixture
def mock_xbrl_from_filing(mock_xbrl):
    """Mock the XBRL.from_filing class method."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl) as mock:
        yield mock

@pytest.fixture
def mock_xbrl_10_k_from_filing(mock_xbrl_10_k):
    """Mock the XBRL.from_filing class method."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_10_k) as mock:
        yield mock

@pytest.fixture
def mock_xbrl_10_q_missing(mock_xbrl_ten_q_missing_durations):
    """Mock the XBRL.from_filing class method."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_ten_q_missing_durations) as mock:
        yield mock

@pytest.fixture
def mock_xbrl_10_q_no_context(mock_xbrl_no_context):
    """Mock the XBRL.from_filing class method."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_no_context) as mock:
        yield mock

@pytest.fixture
def mock_xbrl_ten_q_invalid(mock_xbrl_invalid):
    """Mock the XBRL.from_filing class method."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_invalid) as mock:
        yield mock

@pytest.fixture
def mock_filing_no_ticker(mock_filing):
    """Mock filing where XBRL has missing ticker."""
    mock_xbrl_no_ticker = Mock()
    mock_xbrl_no_ticker.entity_info = {'document_type': '10-Q'}  # Missing ticker
    mock_xbrl_no_ticker.period_of_report = '2024-12-31'
    
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_no_ticker):
        yield mock_filing

@pytest.fixture
def mock_filing_invalid_doc_type(mock_filing):
    """Mock filing with invalid document type."""
    mock_xbrl_bad_doc = Mock()
    mock_xbrl_bad_doc.entity_info = {
        'ticker': 'AAPL',
        'document_type': '8-K'  # Invalid type
    }
    mock_xbrl_bad_doc.period_of_report = '2024-12-31'
    
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_xbrl_bad_doc):
        yield mock_filing

@pytest.fixture
def mock_filing_xbrl_failure(mock_filing):
    """Mock filing where XBRL.from_filing() raises an exception."""
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', side_effect=Exception("XBRL parsing failed")):
        yield mock_filing

@pytest.fixture
def mock_filing_no_accession():
    """Mock filing with neither accession attribute."""
    filing = Mock()
    # Remove both attributes
    del filing.accession_no
    del filing.accession_number
    return filing

@pytest.fixture
def mock_filing_no_report_end(mock_filing):
    """Mock filing lacking report end."""
    mock_no_report = Mock()
    mock_no_report.entity_info = {
        'ticker': 'AAPL',
        'document_type': '10-K'
    }
    mock_no_report.period_of_report = ''
    
    with patch('stock_lab.facts_normalizer.XBRL.from_filing', return_value=mock_no_report):
        yield mock_filing

def test_successful_metadata_extraction(mock_filing, mock_xbrl_from_filing):
    """Test happy path with all required data present."""
    normalizer = XBRLFactsNormalizer(mock_filing)
    
    assert normalizer.accession_number == '0000320193-24-000456'
    assert normalizer.ticker == 'AAPL'
    assert normalizer.document_type == '10-Q'
    assert normalizer.report_end == '2024-12-31'

def test_missing_ticker_raises_exception(mock_filing_no_ticker):
    """Test that missing ticker raises descriptive exception."""
    with pytest.raises(FilingDataError, match="Ticker not found"):
        XBRLFactsNormalizer(mock_filing_no_ticker)

def test_invalid_document_type_raises_exception(mock_filing_invalid_doc_type):
    """Test that invalid document type raises exception."""
    with pytest.raises(FilingDataError, match="Document type must be 10-K or 10-Q"):
        XBRLFactsNormalizer(mock_filing_invalid_doc_type)

def test_xbrl_creation_failure_raises_exception(mock_filing_xbrl_failure):
    """Test that XBRL.from_filing() failure is handled."""
    with pytest.raises(FilingDataError, match="Failed to create XBRL"):
        XBRLFactsNormalizer(mock_filing_xbrl_failure)

def test_missing_accession_raises_exception(mock_filing_no_accession, mock_xbrl_from_filing):
    """Test that missing both accession attributes raises descriptive exception."""
    with pytest.raises(FilingDataError, match="Accession number not found"):
        XBRLFactsNormalizer(mock_filing_no_accession)

def test_missing_report_end_raises_exception(mock_filing_no_report_end):
    with pytest.raises(FilingDataError, match="Report date not found"):
        XBRLFactsNormalizer(mock_filing_no_report_end)

def test_get_period_keys_ten_q(mock_filing, mock_xbrl_from_filing):
    """Test happy path for a 10-Q"""
    normalizer_10q = XBRLFactsNormalizer(mock_filing)

    assert normalizer_10q.instant_dict['date'] == '2024-12-31'
    assert len(normalizer_10q.quarter_durations) >= 1
    assert normalizer_10q.quarter_durations[0]['days'] == 90

def test_get_period_keys_ten_k(mock_filing, mock_xbrl_10_k_from_filing):
    """Test happy path for a 10-K"""
    normalizer_10k = XBRLFactsNormalizer(mock_filing)

    assert normalizer_10k.annual_durations[0]['days'] == 365

# TODO: Finish these
def test_get_period_keys_missing_data(mock_filing, mock_xbrl_10_q_missing):
    """Test that missing data raises MissingData exception."""
    with pytest.raises(MissingDate):
        normalizer_ten_q = XBRLFactsNormalizer(mock_filing)

def test_get_period_keys_missing_context(mock_filing, mock_xbrl_10_q_no_context):
    """"""
    with pytest.raises(FilingDataError):
        normalizer = XBRLFactsNormalizer(mock_filing)

def test_get_period_keys_invalid_data(mock_filing, mock_xbrl_ten_q_invalid):
    with pytest.raises(InvalidDate):
        normalizer = XBRLFactsNormalizer(mock_filing)

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

# TODO: update
@pytest.mark.integration
def test_facts_pipe_ten_q(nvda_ten_q):
    rows = XBRLFactsNormalizer(nvda_ten_q)
    #TODO: Create expected values from spreadsheet and assert against

# TODO: update
@pytest.mark.integration
def test_facts_pipe_ten_k(nvda_ten_k):
    rows = XBRLFactsNormalizer(nvda_ten_k)
    #TODO: Create expected values from spreadsheet and assert against

@pytest.mark.integration
def test_facts_normalizer_small_cap(bdl_quarters):
    for quarter in bdl_quarters:
        normalizer = XBRLFactsNormalizer(bdl_quarters)

# TODO: update
@pytest.mark.integration
def test_facts_pipe_multiple(appl_quarters,
                             nflx_quarters,
                             nvda_quarters,
                             x_quarters):
    for company in (appl_quarters, 
                    nflx_quarters, 
                    nvda_quarters,
                    x_quarters):
        for quarter in company:
            XBRLFactsNormalizer(quarter)
