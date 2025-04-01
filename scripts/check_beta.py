"""
Beta Calculation Validation Script

This script fetches historical data and calculates beta values for a predefined list of symbols
to validate how the beta calculation works in practice. It uses raw beta calculation without
any of the special case handling found in the portfolio processing code.

Beta measures the volatility of a security in relation to the market (using SPY as proxy).
- Beta > 1: More volatile than the market
- Beta = 1: Same volatility as the market
- Beta < 1: Less volatile than the market
- Beta < 0: Moves in the opposite direction as the market

Latest Beta Values (as of 2025-04-01):
   SPAXX**: Not available (money market fund, no market data)
     FMPXX: Not available (money market fund, no market data)
     FFRHX: 0.0553 (money market fund)
       TLT: -0.0145 (long-term treasury ETF, negative correlation)
       SHY: 0.0107 (short-term treasury ETF)
       BIL: 0.0005 (1-3 month T-bill ETF, extremely low beta)
      MCHI: 0.7130 (China ETF, significant market exposure)
      IEFA: 0.7862 (International ETF, significant market exposure)
       SPY: 1.0000 (S&P 500 ETF, market benchmark)
      AAPL: 1.2029 (Tech stock, higher volatility than market)
     GOOGL: 1.2695 (Tech stock, higher volatility than market)
   INVALID: Not available (invalid symbol for testing error handling)

Usage:
    python scripts/check_beta.py

Note: This script calculates raw beta values without the additional logic that might be
applied in the main application, such as fallbacks for cash-like positions or special
handling of missing data.
"""

import os
import sys

import pandas as pd

# Adjust path to import from src
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)

from src.folio.logger import logger  # Use the same logger if desired
from src.folio.utils import is_cash_or_short_term
from src.v2.data_fetcher import DataFetcher


def calculate_raw_beta(
    ticker: str, fetcher: DataFetcher, market_data: pd.DataFrame | None
) -> float | str:
    """Fetches data and calculates raw beta without special handling."""
    if market_data is None:
        return "Error: Market data not available"

    try:
        logger.info(f"Fetching data for {ticker}...")
        stock_data = fetcher.fetch_data(ticker)

        if stock_data is None or stock_data.empty:
            return f"Error: No data fetched for {ticker}"
        if len(stock_data) < 2:
            return f"Error: Not enough data points for {ticker} (need >= 2)"

        logger.info(f"Calculating returns for {ticker}...")
        stock_returns = stock_data["Close"].pct_change().dropna()
        market_returns = market_data["Close"].pct_change().dropna()

        # Align data by index
        aligned_stock, aligned_market = stock_returns.align(
            market_returns, join="inner"
        )

        if aligned_stock.empty or len(aligned_stock) < 2:
            return f"Error: Not enough overlapping data points after alignment for {ticker} (need >= 2)"

        logger.info(f"Calculating variance/covariance for {ticker}...")
        market_variance = aligned_market.var()
        covariance = aligned_stock.cov(aligned_market)

        if pd.isna(market_variance) or abs(market_variance) < 1e-12:
            return f"Error: Market variance is zero or near-zero ({market_variance})"
        if pd.isna(covariance):
            return "Error: Covariance calculation resulted in NaN"

        beta = covariance / market_variance
        return beta

    except Exception as e:
        return f"Error calculating beta for {ticker}: {e}"


if __name__ == "__main__":
    symbols_to_check = [
        "SPAXX**",
        "FMPXX",
        "FFRHX",
        "TLT",  # 20+ Year Treasury Bond ETF
        "SHY",  # 1-3 Year Treasury Bond ETF
        "BIL",  # 1-3 Month T-Bill ETF
        "MCHI",  # iShares MSCI China ETF
        "IEFA",  # iShares Core MSCI EAFE ETF
        "SPY",  # S&P 500 ETF
        "AAPL",  # Apple Stock
        "GOOGL",  # Google Stock
        "INVALID",  # Test an invalid ticker
    ]

    print("Initializing DataFetcher...")
    try:
        fetcher = DataFetcher()
        if fetcher is None:
            raise RuntimeError("Fetcher initialization failed")
        print("Fetching market data (SPY as proxy)...")
        # Fetch market data once
        market_data = (
            fetcher.fetch_market_data()
        )  # Assumes this fetches S&P500 or similar
        if market_data is None or market_data.empty:
            print("Fatal: Could not fetch market data. Aborting.")
            sys.exit(1)
        print(f"Market data fetched: {len(market_data)} rows.")

    except Exception as e:
        print(f"Fatal: Failed to initialize DataFetcher or fetch market data: {e}")
        sys.exit(1)

    print("\n--- Checking Raw Beta Calculations ---")
    results = {}
    for symbol in symbols_to_check:
        print(f"\nProcessing: {symbol}")
        beta_result = calculate_raw_beta(symbol, fetcher, market_data)
        results[symbol] = beta_result
        if isinstance(beta_result, float):
            print(f"Result for {symbol}: Beta = {beta_result:.4f}")
        else:
            print(f"Result for {symbol}: {beta_result}")

    print("\n--- Summary --- ")
    for symbol, result in results.items():
        if isinstance(result, float):
            print(f"{symbol:>10}: {result:.4f}")
        else:
            print(f"{symbol:>10}: {result}")

    # Check cash-like classification
    print("\n--- Cash-Like Classification ---")
    for symbol, result in results.items():
        if isinstance(result, float):
            is_cash = is_cash_or_short_term(symbol, beta=result)
            classification = "CASH-LIKE" if is_cash else "MARKET-CORRELATED"
            print(f"{symbol:>10}: Beta = {result:.4f} -> {classification}")

    print("\nScript finished.")
