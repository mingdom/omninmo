"""
Script to perform a detailed comparison of beta calculations between data fetchers.

This script analyzes the differences in beta calculations between the FMP DataFetcher
and the YFinance DataFetcher by examining the underlying data.
"""

import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fmp import DataFetcher
from src.yfinance import YFinanceDataFetcher


def analyze_beta_differences(ticker, fmp_fetcher, yf_fetcher):
    """
    Analyze differences in beta calculations between data fetchers.

    Args:
        ticker (str): Ticker symbol
        fmp_fetcher: FMP data fetcher instance
        yf_fetcher: YFinance data fetcher instance
    """
    print(f"\nDetailed Beta Analysis for {ticker}")
    print("=" * 40)

    # Fetch data
    fmp_stock = fmp_fetcher.fetch_data(ticker)
    fmp_market = fmp_fetcher.fetch_market_data()
    yf_stock = yf_fetcher.fetch_data(ticker)
    yf_market = yf_fetcher.fetch_market_data()

    # Print basic info
    print(f"FMP stock data: {len(fmp_stock)} rows, {fmp_stock.index.min()} to {fmp_stock.index.max()}")
    print(f"YF stock data:  {len(yf_stock)} rows, {yf_stock.index.min()} to {yf_stock.index.max()}")
    print(f"FMP market data: {len(fmp_market)} rows, {fmp_market.index.min()} to {fmp_market.index.max()}")
    print(f"YF market data:  {len(yf_market)} rows, {yf_market.index.min()} to {yf_market.index.max()}")

    # Calculate returns
    fmp_stock_returns = fmp_stock["Close"].pct_change().dropna()
    fmp_market_returns = fmp_market["Close"].pct_change().dropna()
    yf_stock_returns = yf_stock["Close"].pct_change().dropna()
    yf_market_returns = yf_market["Close"].pct_change().dropna()

    # Align data for FMP
    fmp_aligned_stock, fmp_aligned_market = fmp_stock_returns.align(
        fmp_market_returns, join="inner"
    )

    # Align data for YF
    yf_aligned_stock, yf_aligned_market = yf_stock_returns.align(
        yf_market_returns, join="inner"
    )

    # Print alignment info
    print(f"FMP aligned data: {len(fmp_aligned_stock)} rows")
    print(f"YF aligned data:  {len(yf_aligned_stock)} rows")

    # Calculate beta components
    fmp_market_variance = fmp_aligned_market.var()
    fmp_covariance = fmp_aligned_stock.cov(fmp_aligned_market)
    yf_market_variance = yf_aligned_market.var()
    yf_covariance = yf_aligned_stock.cov(yf_aligned_market)

    # Calculate beta
    fmp_beta = fmp_covariance / fmp_market_variance
    yf_beta = yf_covariance / yf_market_variance

    # Print beta components
    print(f"FMP market variance: {fmp_market_variance:.6f}")
    print(f"YF market variance:  {yf_market_variance:.6f}")
    print(f"FMP covariance: {fmp_covariance:.6f}")
    print(f"YF covariance:  {yf_covariance:.6f}")
    print(f"FMP beta: {fmp_beta:.2f}")
    print(f"YF beta:  {yf_beta:.2f}")

    # Find common dates
    common_dates = fmp_stock.index.intersection(yf_stock.index)
    print(f"Common dates: {len(common_dates)} rows")

    if len(common_dates) > 0:
        # Compare prices on common dates
        fmp_subset = fmp_stock.loc[common_dates]["Close"]
        yf_subset = yf_stock.loc[common_dates]["Close"]

        # Calculate price differences
        close_diff_pct = abs((fmp_subset - yf_subset) / fmp_subset * 100)

        print(f"Average close price difference: {close_diff_pct.mean():.2f}%")
        print(f"Max close price difference: {close_diff_pct.max():.2f}%")

        # Plot comparison
        plt.figure(figsize=(12, 8))

        # Plot close prices
        plt.subplot(2, 1, 1)
        plt.plot(fmp_subset.index, fmp_subset, label="FMP Close")
        plt.plot(yf_subset.index, yf_subset, label="YF Close", linestyle="--")
        plt.title(f"{ticker} Close Price Comparison")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.grid(True)

        # Plot percentage difference
        plt.subplot(2, 1, 2)
        plt.plot(close_diff_pct.index, close_diff_pct)
        plt.title(f"{ticker} Price Difference (FMP vs YF)")
        plt.xlabel("Date")
        plt.ylabel("Difference (%)")
        plt.grid(True)

        plt.tight_layout()
        # Save the plot to .tmp directory
        os.makedirs(".tmp", exist_ok=True)
        plt.savefig(f".tmp/{ticker}_detailed_comparison.png")
        print(f"Plot saved to .tmp/{ticker}_detailed_comparison.png")

        # Calculate beta using common dates only
        fmp_common_returns = fmp_stock.loc[common_dates]["Close"].pct_change().dropna()
        yf_common_returns = yf_stock.loc[common_dates]["Close"].pct_change().dropna()
        fmp_market_common = fmp_market.loc[common_dates]["Close"].pct_change().dropna()
        yf_market_common = yf_market.loc[common_dates]["Close"].pct_change().dropna()

        # Align data
        common_dates_returns = fmp_common_returns.index.intersection(fmp_market_common.index)
        if len(common_dates_returns) > 30:  # Require at least 30 data points
            fmp_common_aligned = fmp_common_returns.loc[common_dates_returns]
            fmp_market_common_aligned = fmp_market_common.loc[common_dates_returns]
            yf_common_aligned = yf_common_returns.loc[common_dates_returns]
            yf_market_common_aligned = yf_market_common.loc[common_dates_returns]

            # Calculate beta
            fmp_common_beta = fmp_common_aligned.cov(fmp_market_common_aligned) / fmp_market_common_aligned.var()
            yf_common_beta = yf_common_aligned.cov(yf_market_common_aligned) / yf_market_common_aligned.var()

            print(f"Beta using common dates only:")
            print(f"  FMP: {fmp_common_beta:.2f}")
            print(f"  YF:  {yf_common_beta:.2f}")
            print(f"  Diff: {abs(fmp_common_beta - yf_common_beta):.2f}")
            print(f"  % Diff: {abs(fmp_common_beta - yf_common_beta) / abs(fmp_common_beta) * 100:.2f}%")


def main():
    """Run the detailed beta comparison."""
    print("Detailed Beta Comparison")
    print("=======================")

    # Create data fetchers
    fmp_fetcher = DataFetcher(cache_dir=".cache_fmp")
    yf_fetcher = YFinanceDataFetcher(cache_dir=".cache_yf")

    # Tickers to analyze in detail
    tickers = ["AAPL", "TSLA", "PG"]  # Selected tickers with varying differences

    for ticker in tickers:
        try:
            analyze_beta_differences(ticker, fmp_fetcher, yf_fetcher)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
