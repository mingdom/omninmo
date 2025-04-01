from unittest.mock import patch

import pytest

from src.folio.utils import is_cash_or_short_term


@pytest.fixture
def mock_get_beta():
    """Mock get_beta function to return controlled values for testing."""
    with patch("src.folio.utils.get_beta") as mock:
        yield mock


def test_low_beta_instruments(mock_get_beta):
    """Test that instruments with low beta are identified as cash-like."""
    # Test with pre-calculated beta
    assert is_cash_or_short_term("SPAXX", beta=0.01)  # Money market fund
    assert is_cash_or_short_term("BIL", beta=0.001)  # Treasury bill ETF
    assert not is_cash_or_short_term(
        "TLT", beta=0.15
    )  # Long-term treasury (higher beta)

    # Test with calculated beta
    mock_get_beta.return_value = 0.05
    assert is_cash_or_short_term("SHY")  # Short-term treasury ETF

    mock_get_beta.return_value = 0.2
    assert not is_cash_or_short_term("AAPL")  # Regular stock


def test_regular_stocks(mock_get_beta):
    """Test that regular stocks are not identified as cash-like."""
    mock_get_beta.return_value = 1.2
    assert not is_cash_or_short_term("AAPL")
    assert not is_cash_or_short_term("GOOGL")


def test_beta_calculation_error(mock_get_beta):
    """Test that beta calculation errors are propagated."""
    mock_get_beta.side_effect = RuntimeError("Failed to fetch data")
    with pytest.raises(RuntimeError, match="Failed to fetch data"):
        is_cash_or_short_term("INVALID")

    mock_get_beta.side_effect = ValueError("Invalid beta calculation")
    with pytest.raises(ValueError, match="Invalid beta calculation"):
        is_cash_or_short_term("INVALID")

    mock_get_beta.side_effect = KeyError("Missing required data")
    with pytest.raises(KeyError, match="Missing required data"):
        is_cash_or_short_term("INVALID")


def test_beta_threshold_edge_cases():
    """Test edge cases around the beta threshold."""
    assert is_cash_or_short_term("TEST1", beta=0.099)  # Just under threshold
    assert not is_cash_or_short_term("TEST2", beta=0.1)  # At threshold
    assert not is_cash_or_short_term("TEST3", beta=0.101)  # Just over threshold
    assert is_cash_or_short_term("TEST4", beta=-0.099)  # Negative but under threshold
    assert not is_cash_or_short_term(
        "TEST5", beta=-0.101
    )  # Negative and over threshold
