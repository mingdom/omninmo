"""
Test utilities for stock data testing
"""

import logging
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_stock_data(ticker, period="5y", interval="1d"):
    """
    Generate sample stock data for testing

    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period ('1y', '5y', etc.)
        interval (str): Data interval ('1d', '1wk', etc.)

    Returns:
        pandas.DataFrame: DataFrame with sample stock data
    """
    # Determine date range based on period
    end_date = datetime.now()

    if period.endswith("y"):
        years = int(period[:-1])
        start_date = end_date - timedelta(days=365 * years)
    elif period.endswith("m"):
        months = int(period[:-1])
        start_date = end_date - timedelta(days=30 * months)
    else:
        # Default to 1 year
        start_date = end_date - timedelta(days=365)

    # Generate date range
    if interval == "1d":
        # Business days only
        date_range = pd.date_range(start=start_date, end=end_date, freq="B")
    else:
        # Weekly
        date_range = pd.date_range(start=start_date, end=end_date, freq="W")

    # Generate random price data
    n = len(date_range)

    # Start with a random price between 10 and 100
    start_price = random.uniform(10, 100)

    # Generate random daily returns with a slight upward bias
    daily_returns = np.random.normal(0.0005, 0.015, n)

    # Calculate cumulative returns
    cumulative_returns = np.cumprod(1 + daily_returns)

    # Calculate prices
    prices = start_price * cumulative_returns

    # Generate OHLC data
    data = {
        "Open": prices * np.random.uniform(0.99, 1.01, n),
        "High": prices * np.random.uniform(1.01, 1.03, n),
        "Low": prices * np.random.uniform(0.97, 0.99, n),
        "Close": prices,
        "Volume": np.random.randint(100000, 10000000, n),
    }

    # Create DataFrame
    df = pd.DataFrame(data, index=date_range)

    # If this is a market index, make it less volatile
    if ticker in ["SPY", "^GSPC", "^DJI", "^IXIC"]:
        df["Open"] = start_price * np.cumprod(1 + np.random.normal(0.0003, 0.008, n))
        df["Close"] = start_price * np.cumprod(1 + np.random.normal(0.0003, 0.008, n))
        df["High"] = df["Close"] * np.random.uniform(1.005, 1.01, n)
        df["Low"] = df["Close"] * np.random.uniform(0.99, 0.995, n)

    return df
