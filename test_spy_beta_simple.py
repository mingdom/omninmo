"""Simple script to test SPY's beta calculation."""

from src.folio.utils import get_beta
from src.stockdata import create_data_fetcher


def main():
    """Calculate and print SPY's beta."""
    data_fetcher = create_data_fetcher()

    get_beta("SPY")

    # Get the actual data used in the calculation
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
    import numpy as np
    is_identical = np.allclose(aligned_stock.values, aligned_market.values, rtol=1e-5)

    if not is_identical:
        # Print the first few differences
        diff = aligned_stock - aligned_market
        non_zero_diff = diff[abs(diff) > 1e-5]
        if not non_zero_diff.empty:
            pass

if __name__ == "__main__":
    main()
