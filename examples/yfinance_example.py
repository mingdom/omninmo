"""
Example script demonstrating the use of YFinanceDataFetcher.

This script shows how to use the YFinanceDataFetcher to fetch stock data
and calculate beta values.
"""

import os
import sys

import matplotlib.pyplot as plt

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.yfinance import YFinanceDataFetcher


def main():
    """Run the example."""
    print("YFinance Data Fetcher Example")
    print("============================")

    # Create a data fetcher
    fetcher = YFinanceDataFetcher(cache_dir="cache")

    # Fetch data for a few tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    print("\nFetching data for multiple tickers...")
    data = {}
    for ticker in tickers:
        print(f"Fetching data for {ticker}...")
        data[ticker] = fetcher.fetch_data(ticker, period="1y")
        print(f"  Got {len(data[ticker])} rows of data")

    # Fetch market data
    print("\nFetching market data (SPY)...")
    market_data = fetcher.fetch_market_data(period="1y")
    print(f"  Got {len(market_data)} rows of data")

    # Calculate beta values
    print("\nCalculating beta values...")
    betas = {}
    for ticker in tickers:
        beta = calculate_beta(data[ticker], market_data)
        betas[ticker] = beta
        print(f"  {ticker} beta: {beta:.2f}")

    # Plot the data
    print("\nPlotting data...")
    plot_data(data, "Stock Prices (Last Year)")

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


def plot_data(data, title):
    """
    Plot stock data.

    Args:
        data (dict): Dictionary of DataFrames with stock data
        title (str): Plot title
    """
    plt.figure(figsize=(12, 6))

    for ticker, df in data.items():
        # Normalize to starting price
        normalized = df["Close"] / df["Close"].iloc[0] * 100
        plt.plot(normalized, label=ticker)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Normalized Price (%)")
    plt.legend()
    plt.grid(True)

    # Save the plot to .tmp directory
    os.makedirs(".tmp", exist_ok=True)
    plt.savefig(".tmp/stock_prices.png")
    print("  Plot saved to .tmp/stock_prices.png")


if __name__ == "__main__":
    main()
