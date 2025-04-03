"""
Regression tests for portfolio loading and calculation.

This test ensures that the sample portfolio consistently produces the same
summary metrics after processing, which helps catch any regressions in the
portfolio loading or sanitization code.
"""

from pathlib import Path

import pandas as pd
import pytest

import src.folio.utils
from src.folio.data_model import ExposureBreakdown, PortfolioSummary
from src.folio.utils import process_portfolio_data


@pytest.fixture(autouse=True)
def mock_beta_calculation(monkeypatch):
    """
    Mock the beta calculation to ensure consistent test results.

    This prevents the test from making actual API calls and ensures
    the same beta values are used each time.
    """
    # Define a dictionary of known beta values for tickers in the sample portfolio
    beta_values = {
        "SPAXX": 0.0,  # Money market
        "AAPL": 1.2,
        "AMZN": 1.3,
        "BKNG": 1.1,
        "CRM": 1.25,
        "FFRHX": 0.05,  # Low beta fund
        "GOOGL": 1.15,
        "META": 1.4,
        "MSFT": 1.1,
        "NVDA": 1.8,
        "SMH": 1.5,
        "TCEHY": 0.9,
        "TLT": 0.1,  # Bond ETF
        "UBER": 1.6,
        "UPRO": 3.0,  # Leveraged ETF
        # Add more tickers as needed
    }

    def mock_get_beta(ticker, description=""):
        # Strip any option-related prefixes
        base_ticker = ticker.lstrip('-')

        # Extract the underlying ticker from option symbols
        if base_ticker.endswith(('C', 'P')) and any(char.isdigit() for char in base_ticker):
            # This is likely an option symbol, extract the base ticker
            for known_ticker in beta_values.keys():
                if base_ticker.startswith(known_ticker):
                    base_ticker = known_ticker
                    break

        # Return the mocked beta value or a default
        # Note: description parameter is unused but required for the mock
        return beta_values.get(base_ticker, 1.0)

    # Mock the is_cash_or_short_term function to use our beta values
    def mock_is_cash_or_short_term(ticker, beta=None, description=""):
        if ticker in ["CASH", "USD", "SPAXX"]:
            return True
        if "MONEY MARKET" in str(description).upper():
            return True
        if beta is not None:
            return abs(beta) < 0.1
        beta = mock_get_beta(ticker, description)
        return abs(beta) < 0.1

    monkeypatch.setattr(src.folio.utils, "get_beta", mock_get_beta)
    monkeypatch.setattr(src.folio.utils, "is_cash_or_short_term", mock_is_cash_or_short_term)


@pytest.fixture
def sample_portfolio_path():
    """Get the path to the sample portfolio CSV file"""
    # Find the sample portfolio in the src/folio/assets directory
    repo_root = Path(__file__).parent.parent
    sample_path = repo_root / "src" / "folio" / "assets" / "sample-portfolio.csv"

    # Ensure the file exists
    assert sample_path.exists(), f"Sample portfolio not found at {sample_path}"
    return sample_path


def test_sample_portfolio_regression(sample_portfolio_path):
    """
    Test that the sample portfolio consistently produces the same metrics.

    This regression test ensures that changes to the code don't unexpectedly
    alter the calculated metrics for the sample portfolio.
    """
    # Load the sample portfolio
    df = pd.read_csv(sample_portfolio_path)

    # Process the portfolio data
    groups, summary, cash_like_positions = process_portfolio_data(df)

    # Verify the number of groups and cash-like positions
    assert len(groups) > 0, "No portfolio groups were created"
    assert len(cash_like_positions) > 0, "No cash-like positions were identified"

    # Verify key portfolio metrics
    assert isinstance(summary, PortfolioSummary), "Summary is not a PortfolioSummary object"

    # Test total values
    assert summary.total_value_net > 0, "Total net value should be positive"
    assert summary.total_value_abs > 0, "Total absolute value should be positive"
    assert summary.total_value_abs >= summary.total_value_net, "Absolute value should be >= net value"

    # Test portfolio beta
    assert 0 <= summary.portfolio_beta <= 3.0, "Portfolio beta should be in a reasonable range"

    # Test exposure breakdowns
    assert isinstance(summary.long_exposure, ExposureBreakdown), "Long exposure is not an ExposureBreakdown object"
    assert isinstance(summary.short_exposure, ExposureBreakdown), "Short exposure is not an ExposureBreakdown object"
    assert isinstance(summary.options_exposure, ExposureBreakdown), "Options exposure is not an ExposureBreakdown object"

    # Test exposure values
    assert summary.long_exposure.total_value > 0, "Long exposure value should be positive"
    assert summary.short_exposure.total_value >= 0, "Short exposure value should be non-negative"

    # Test cash-like positions
    assert summary.cash_like_count > 0, "Should have at least one cash-like position"
    assert summary.cash_like_value > 0, "Cash-like value should be positive"

    # Test percentage metrics
    assert 0 <= summary.short_percentage <= 100, "Short percentage should be between 0 and 100"
    assert 0 <= summary.exposure_reduction_percentage <= 100, "Exposure reduction should be between 0 and 100"

    # Expected values for regression testing
    # These values should be updated if the sample portfolio or calculation logic intentionally changes
    expected_values = {
        "total_groups": 12,  # Expected number of portfolio groups
        "cash_like_count": 2,  # Expected number of cash-like positions
        "total_value_net": 24624556,  # Expected net portfolio value (approximate)
        "portfolio_beta": 0.98,  # Expected portfolio beta (approximate)
        "long_exposure_value": 16411168,  # Expected long exposure value (approximate)
        "short_exposure_value": 5972282,  # Expected short exposure value (approximate)
        "options_exposure_value": 3876199,  # Expected options exposure value (approximate)
        "cash_like_value": 14185670,  # Expected cash-like value (approximate)
    }

    # Test against expected values with reasonable tolerances
    assert abs(len(groups) - expected_values["total_groups"]) <= 2, \
        f"Expected approximately {expected_values['total_groups']} groups, got {len(groups)}"

    assert abs(summary.cash_like_count - expected_values["cash_like_count"]) <= 1, \
        f"Expected approximately {expected_values['cash_like_count']} cash-like positions, got {summary.cash_like_count}"

    assert abs(summary.total_value_net - expected_values["total_value_net"]) / expected_values["total_value_net"] <= 0.1, \
        f"Total net value {summary.total_value_net} differs significantly from expected {expected_values['total_value_net']}"

    assert abs(summary.portfolio_beta - expected_values["portfolio_beta"]) <= 0.3, \
        f"Portfolio beta {summary.portfolio_beta} differs significantly from expected {expected_values['portfolio_beta']}"

    assert abs(summary.long_exposure.total_value - expected_values["long_exposure_value"]) / expected_values["long_exposure_value"] <= 0.1, \
        f"Long exposure value {summary.long_exposure.total_value} differs significantly from expected {expected_values['long_exposure_value']}"

    assert abs(summary.short_exposure.total_value - expected_values["short_exposure_value"]) / expected_values["short_exposure_value"] <= 0.1, \
        f"Short exposure value {summary.short_exposure.total_value} differs significantly from expected {expected_values['short_exposure_value']}"

    assert abs(summary.options_exposure.total_value - expected_values["options_exposure_value"]) / expected_values["options_exposure_value"] <= 0.1, \
        f"Options exposure value {summary.options_exposure.total_value} differs significantly from expected {expected_values['options_exposure_value']}"

    assert abs(summary.cash_like_value - expected_values["cash_like_value"]) / expected_values["cash_like_value"] <= 0.1, \
        f"Cash-like value {summary.cash_like_value} differs significantly from expected {expected_values['cash_like_value']}"

    # Print summary for debugging
    print(f"\nPortfolio Summary:")
    print(f"  Total Groups: {len(groups)}")
    print(f"  Total Net Value: ${summary.total_value_net:,.2f}")
    print(f"  Total Absolute Value: ${summary.total_value_abs:,.2f}")
    print(f"  Portfolio Beta: {summary.portfolio_beta:.2f}")
    print(f"  Long Exposure: ${summary.long_exposure.total_value:,.2f}")
    print(f"  Short Exposure: ${summary.short_exposure.total_value:,.2f}")
    print(f"  Options Exposure: ${summary.options_exposure.total_value:,.2f}")
    print(f"  Cash-like Positions: {summary.cash_like_count}")
    print(f"  Cash-like Value: ${summary.cash_like_value:,.2f}")
    print(f"  Short Percentage: {summary.short_percentage:.2f}%")
    print(f"  Exposure Reduction: {summary.exposure_reduction_percentage:.2f}%")


def test_sample_portfolio_serialization(sample_portfolio_path):
    """
    Test that the portfolio summary and groups can be serialized to dictionaries.

    This ensures that the data structures can be properly converted to JSON for
    the Dash frontend.
    """
    # Load and process the sample portfolio
    df = pd.read_csv(sample_portfolio_path)
    groups, summary, _ = process_portfolio_data(df)  # We don't need cash_like_positions for this test

    # Test serialization of summary
    summary_dict = summary.to_dict()
    assert isinstance(summary_dict, dict), "Summary should serialize to a dictionary"
    assert "total_value_net" in summary_dict, "Serialized summary missing total_value_net"
    assert "portfolio_beta" in summary_dict, "Serialized summary missing portfolio_beta"
    assert "long_exposure" in summary_dict, "Serialized summary missing long_exposure"
    assert "short_exposure" in summary_dict, "Serialized summary missing short_exposure"

    # Test serialization of groups
    for i, group in enumerate(groups):
        group_dict = group.to_dict()
        assert isinstance(group_dict, dict), f"Group {i} should serialize to a dictionary"
        assert "ticker" in group_dict, f"Group {i} missing ticker"
        assert "total_value" in group_dict, f"Group {i} missing total_value"

        # Test stock position serialization if present
        if group.stock_position:
            stock_dict = group.stock_position.to_dict()
            assert isinstance(stock_dict, dict), f"Stock position in group {i} should serialize to a dictionary"
            assert "ticker" in stock_dict, f"Stock position in group {i} missing ticker"
            assert "market_value" in stock_dict, f"Stock position in group {i} missing market_value"

        # Test option positions serialization if present
        for j, option in enumerate(group.option_positions):
            option_dict = option.to_dict()
            assert isinstance(option_dict, dict), f"Option {j} in group {i} should serialize to a dictionary"
            assert "ticker" in option_dict, f"Option {j} in group {i} missing ticker"
            assert "strike" in option_dict, f"Option {j} in group {i} missing strike"
            assert "option_type" in option_dict, f"Option {j} in group {i} missing option_type"
