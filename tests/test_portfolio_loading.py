import pandas as pd
import pytest

import src.folio.utils
from src.folio.portfolio import process_portfolio_data


@pytest.fixture(autouse=True)
def mock_get_beta(monkeypatch):
    """Mock get_beta to return 1.25 for TSM"""

    def mock_beta(ticker: str, description: str = "") -> float:
        if ticker == "TSM":
            return 1.25
        return 1.0

    monkeypatch.setattr(src.folio.utils, "get_beta", mock_beta)


@pytest.fixture
def sample_portfolio_csv():
    """Create a sample portfolio DataFrame for testing"""
    return pd.DataFrame(
        {
            "Symbol": ["TSM", "-TSM250417C190", "-TSM250620P170"],
            "Description": [
                "TAIWAN SEMICONDUCTOR MANUFACTURING SPON ADS EACH REP 5 ORD TWD10",
                "TSM APR 17 2025 $190 CALL",
                "TSM JUN 20 2025 $170 PUT",
            ],
            "Quantity": [400, -4, -3],
            "Last Price": ["165.25", "0.87", "14.15"],
            "Current Value": ["66100.00", "-348.00", "-4245.00"],
            "Percent Of Account": ["2.40%", "-0.01%", "-0.15%"],
            "Type": ["Margin", "Margin", "Margin"],
        }
    )


def test_process_portfolio_data(sample_portfolio_csv):
    """Test that portfolio data can be loaded without errors"""
    groups, summary, cash_like_positions = process_portfolio_data(sample_portfolio_csv)
    assert len(groups) == 1, "Should create one group for TSM"


def test_portfolio_group_serialization(sample_portfolio_csv):
    """Test that portfolio groups can be serialized without errors"""
    groups, _, _ = process_portfolio_data(sample_portfolio_csv)
    assert len(groups) == 1
    group_dict = groups[0].to_dict()
    assert group_dict["ticker"] == "TSM"


def test_invalid_portfolio_data():
    """Test that invalid portfolio data is handled correctly"""
    # Test missing required columns
    df = pd.DataFrame(
        {
            "Symbol": ["TSM"],
            "Description": ["Test"],
            # Missing other required columns
        }
    )
    with pytest.raises(ValueError, match="Missing required columns"):
        process_portfolio_data(df)

    # Test empty DataFrame - now returns empty results instead of raising an error
    df = pd.DataFrame()
    groups, summary, cash_like_positions = process_portfolio_data(df)
    assert len(groups) == 0
    assert summary.total_exposure == 0
    assert len(cash_like_positions) == 0

    # Test None DataFrame - now returns empty results instead of raising an error
    groups, summary, cash_like_positions = process_portfolio_data(None)
    assert len(groups) == 0
    assert summary.total_exposure == 0
    assert len(cash_like_positions) == 0
