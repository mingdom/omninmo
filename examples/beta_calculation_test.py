"""
Script to test beta calculation using both data fetchers.

This script calculates beta values for a set of tickers using both
the FMP DataFetcher and the YFinance DataFetcher, and compares the results.
"""

import os
import sys

# import numpy as np  # Not used
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fmp import DataFetcher
from src.yfinance import YFinanceDataFetcher


def calculate_beta(ticker, data_fetcher, period="6m"):
    """
    Calculate beta for a ticker using the provided data fetcher.

    Args:
        ticker (str): Ticker symbol
        data_fetcher: Data fetcher instance
        period (str): Time period for beta calculation (default: '6m')

    Returns:
        float: Beta value
    """
    # Fetch required data
    stock_data = data_fetcher.fetch_data(ticker, period=period)
    market_data = data_fetcher.fetch_market_data(period=period)

    # Calculate returns
    stock_returns = stock_data["Close"].pct_change(fill_method=None).dropna()
    market_returns = market_data["Close"].pct_change(fill_method=None).dropna()

    # Align data by index
    aligned_stock, aligned_market = stock_returns.align(
        market_returns, join="inner"
    )

    if aligned_stock.empty or len(aligned_stock) < 2:
        print(f"Insufficient overlapping data points for {ticker}, cannot calculate meaningful beta")
        return 0.0

    # Calculate beta components
    market_variance = aligned_market.var()
    covariance = aligned_stock.cov(aligned_market)

    if pd.isna(market_variance) or abs(market_variance) < 1e-12:
        print(f"Market variance is near-zero for {ticker}, cannot calculate meaningful beta")
        return 0.0
    if pd.isna(covariance):
        print(f"Covariance calculation resulted in NaN for {ticker}")
        return 0.0

    beta = covariance / market_variance
    if pd.isna(beta):
        print(f"Beta calculation resulted in NaN for {ticker}")
        return 0.0

    return beta


def main():
    """Run the beta calculation test."""
    print("Beta Calculation Test")
    print("====================")

    # Create data fetchers
    fmp_fetcher = DataFetcher(cache_dir=".cache_fmp")
    yf_fetcher = YFinanceDataFetcher(cache_dir=".cache_yf")

    # Tickers to test
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "PG"]

    # Test periods
    periods = ["1y", "6m"]

    for period in periods:
        print(f"\nCalculating beta values using {period} period...")
        print(f"{'Ticker':<6} {'FMP Beta':>10} {'YF Beta':>10} {'Diff':>10} {'% Diff':>10}")
        print("-" * 50)

        for ticker in tickers:
            try:
                # Calculate beta using FMP data
                fmp_beta = calculate_beta(ticker, fmp_fetcher, period=period)

                # Calculate beta using YF data
                yf_beta = calculate_beta(ticker, yf_fetcher, period=period)

                # Calculate difference
                diff = abs(fmp_beta - yf_beta)
                pct_diff = diff / abs(fmp_beta) * 100 if fmp_beta != 0 else 0

                # Print results
                print(f"{ticker:<6} {fmp_beta:>10.2f} {yf_beta:>10.2f} {diff:>10.2f} {pct_diff:>10.2f}%")

            except Exception as e:
                print(f"{ticker:<6} Error: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
