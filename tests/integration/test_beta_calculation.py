"""Integration tests for beta calculation.

These tests verify that beta calculations work correctly with real data from the API.
"""


import numpy as np
import pytest

from src.folio.utils import get_beta
from src.stockdata import create_data_fetcher


class TestBetaCalculation:
    """Integration tests for beta calculation with real data."""

    @pytest.fixture
    def data_fetcher(self):
        """Create a real data fetcher for testing."""
        return create_data_fetcher()

    def test_spy_beta_with_real_data(self, data_fetcher):
        """Test that SPY's beta is very close to 1.0 with real data."""
        # Calculate SPY's beta using the real data fetcher
        beta = get_beta("SPY")

        # SPY's beta should be very close to 1.0 since it's the benchmark
        assert 0.99 <= beta <= 1.01, f"SPY beta should be very close to 1.0, got {beta}"

        # Print detailed information for debugging

        # Get the actual data used in the calculation to understand any discrepancies
        stock_data = data_fetcher.fetch_data("SPY")
        market_data = data_fetcher.fetch_market_data()

        # Calculate returns
        stock_returns = stock_data["Close"].pct_change().dropna()
        market_returns = market_data["Close"].pct_change().dropna()

        # Align data
        aligned_stock, aligned_market = stock_returns.align(market_returns, join="inner")

        # Calculate beta components
        market_variance = aligned_market.var()
        covariance = aligned_stock.cov(aligned_market)
        covariance / market_variance

        # Print detailed information

        # Check if the data is identical
        is_identical = np.allclose(aligned_stock.values, aligned_market.values, rtol=1e-5)

        if not is_identical:
            # Print the first few differences
            diff = aligned_stock - aligned_market
            non_zero_diff = diff[abs(diff) > 1e-5]
            if not non_zero_diff.empty:
                pass

    def test_other_securities_beta(self):
        """Test beta calculation for other securities."""
        # Test a high beta stock (technology)
        aapl_beta = get_beta("AAPL")
        assert aapl_beta > 0.8, f"AAPL beta should be significant, got {aapl_beta}"

        # Test a low beta stock (utility)
        so_beta = get_beta("SO")  # Southern Company, a utility
        assert so_beta < 1.0, f"SO beta should be less than 1.0, got {so_beta}"

        # Test a market ETF that should have beta close to 1
        ivv_beta = get_beta("IVV")  # iShares Core S&P 500 ETF
        assert 0.95 <= ivv_beta <= 1.05, f"IVV beta should be close to 1.0, got {ivv_beta}"

        # Test a bond ETF that should have low beta
        tlt_beta = get_beta("TLT")  # iShares 20+ Year Treasury Bond ETF
        assert abs(tlt_beta) < 0.5, f"TLT beta should be low, got {tlt_beta}"


if __name__ == "__main__":
    pytest.main(["-v", "tests/integration/test_beta_calculation.py"])
