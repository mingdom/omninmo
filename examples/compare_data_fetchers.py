"""
Script to compare YFinanceDataFetcher and DataFetcher.

This script fetches data for the same tickers using both data fetchers
and compares the results to ensure compatibility.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fmp import DataFetcher
from src.yfinance import YFinanceDataFetcher


def main():
    """Run the comparison."""
    print("Data Fetcher Comparison")
    print("======================")

    # Create data fetchers
    fmp_fetcher = DataFetcher(cache_dir=".cache_fmp")
    yf_fetcher = YFinanceDataFetcher(cache_dir=".cache_yf")

    # Tickers to compare
    tickers = ["AAPL", "MSFT", "GOOGL", "SPY"]
    period = "1y"

    # Fetch data and compare
    for ticker in tickers:
        print(f"\nComparing data for {ticker}...")

        try:
            # Fetch data from both sources
            fmp_data = fmp_fetcher.fetch_data(ticker, period=period)
            yf_data = yf_fetcher.fetch_data(ticker, period=period)

            # Print basic info
            print(f"  FMP data: {len(fmp_data)} rows, columns: {list(fmp_data.columns)}")
            print(f"  YF data:  {len(yf_data)} rows, columns: {list(yf_data.columns)}")

            # Compare date ranges
            print(f"  FMP date range: {fmp_data.index.min()} to {fmp_data.index.max()}")
            print(f"  YF date range:  {yf_data.index.min()} to {yf_data.index.max()}")

            # Compare common dates
            common_dates = fmp_data.index.intersection(yf_data.index)
            print(f"  Common dates: {len(common_dates)}")

            if len(common_dates) > 0:
                # Compare prices on common dates
                fmp_subset = fmp_data.loc[common_dates]
                yf_subset = yf_data.loc[common_dates]

                # Calculate price differences
                close_diff_pct = abs((fmp_subset["Close"] - yf_subset["Close"]) / fmp_subset["Close"] * 100)

                print(f"  Average close price difference: {close_diff_pct.mean():.2f}%")
                print(f"  Max close price difference: {close_diff_pct.max():.2f}%")

                # Plot comparison
                plot_comparison(ticker, fmp_subset, yf_subset)

                # Calculate beta using both data sources
                if ticker != "SPY":
                    fmp_market = fmp_fetcher.fetch_market_data(period=period)
                    yf_market = yf_fetcher.fetch_market_data(period=period)

                    fmp_beta = calculate_beta(fmp_data, fmp_market)
                    yf_beta = calculate_beta(yf_data, yf_market)

                    print(f"  FMP beta: {fmp_beta:.2f}")
                    print(f"  YF beta:  {yf_beta:.2f}")
                    print(f"  Beta difference: {abs(fmp_beta - yf_beta):.2f}")

        except Exception as e:
            print(f"  Error comparing {ticker}: {e}")

    print("\nDone!")


def calculate_beta(stock_data, market_data):
    """
    Calculate beta for a stock against the market.

    Args:
        stock_data (pandas.DataFrame): Stock data
        market_data (pandas.DataFrame): Market data

    Returns:
        float: Beta value
    """
    # Calculate returns
    stock_returns = stock_data["Close"].pct_change().dropna()
    market_returns = market_data["Close"].pct_change().dropna()

    # Align data
    common_dates = stock_returns.index.intersection(market_returns.index)
    stock_returns = stock_returns.loc[common_dates]
    market_returns = market_returns.loc[common_dates]

    # Calculate beta
    covariance = stock_returns.cov(market_returns)
    market_variance = market_returns.var()

    return covariance / market_variance


def plot_comparison(ticker, fmp_data, yf_data):
    """
    Plot comparison of FMP and YF data.

    Args:
        ticker (str): Ticker symbol
        fmp_data (pandas.DataFrame): FMP data
        yf_data (pandas.DataFrame): YF data
    """
    plt.figure(figsize=(12, 8))

    # Plot close prices
    plt.subplot(2, 1, 1)
    plt.plot(fmp_data.index, fmp_data["Close"], label="FMP Close")
    plt.plot(yf_data.index, yf_data["Close"], label="YF Close", linestyle="--")
    plt.title(f"{ticker} Close Price Comparison")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)

    # Plot percentage difference
    plt.subplot(2, 1, 2)
    diff_pct = (fmp_data["Close"] - yf_data["Close"]) / fmp_data["Close"] * 100
    plt.plot(diff_pct.index, diff_pct)
    plt.title(f"{ticker} Price Difference (FMP - YF)")
    plt.xlabel("Date")
    plt.ylabel("Difference (%)")
    plt.axhline(y=0, color="r", linestyle="-")
    plt.grid(True)

    plt.tight_layout()

    # Save the plot to .tmp directory
    os.makedirs(".tmp", exist_ok=True)
    plt.savefig(f".tmp/{ticker}_comparison.png")
    print(f"  Plot saved to .tmp/{ticker}_comparison.png")


if __name__ == "__main__":
    main()
