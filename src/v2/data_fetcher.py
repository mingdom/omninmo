"""
Data fetcher for stock data
"""

import logging
import os
import random
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests

from src.v2.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Class to fetch stock data from API or use sample data"""

    def __init__(self, cache_dir="cache"):
        """Initialize with cache directory"""
        self.cache_dir = cache_dir
        self.api_key = os.environ.get("FMP_API_KEY") or config.get("data.fmp.api_key")
        self.cache_ttl = config.get(
            "app.cache.ttl", 86400
        )  # Default to 1 day if not specified

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_data(self, ticker, period="5y", interval="1d", force_sample=False):
        """
        Fetch stock data for a ticker

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)
            force_sample (bool): Force using sample data instead of API

        Returns:
            pandas.DataFrame: DataFrame with stock data

        Raises:
            ValueError: If no API key is set and force_sample is False
        """
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")

        # Check if cache exists and is still valid
        if os.path.exists(cache_file):
            # Get file modification time
            file_mtime = os.path.getmtime(cache_file)
            cache_age = time.time() - file_mtime

            # If cache is still valid, use it
            if cache_age < self.cache_ttl:
                logger.info(f"Loading cached data for {ticker} (age: {cache_age:.0f}s)")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            else:
                logger.info(
                    f"Cache expired for {ticker} (age: {cache_age:.0f}s > TTL: {self.cache_ttl}s)"
                )

        # If forcing sample data, use sample data
        if force_sample:
            logger.info(f"Using sample data for {ticker} (forced)")
            return self._generate_sample_data(ticker, period, interval)

        # Check for API key
        if not self.api_key:
            raise ValueError(
                "No API key found. Please set the FMP_API_KEY environment variable or "
                "configure it in the config file. If you want to use sample data instead, "
                "explicitly set force_sample=True"
            )

        # If we have an API key, try to fetch from API
        try:
            logger.info(f"Fetching data for {ticker} from API")
            df = self._fetch_from_api(ticker, period)

            if df is not None and not df.empty:
                # Save to cache
                df.to_csv(cache_file)
                return df
            else:
                raise ValueError(f"No data returned from API for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")

            # If cache exists but is expired, use it as fallback
            if os.path.exists(cache_file):
                logger.warning(f"Using expired cache as fallback for {ticker}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)

            raise

    def fetch_market_data(
        self, market_index="SPY", period="5y", interval="1d", force_sample=False
    ):
        """
        Fetch market index data for beta calculations

        Args:
            market_index (str): Market index ticker symbol (default: 'SPY' for S&P 500 ETF)
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)
            force_sample (bool): Force using sample data instead of API

        Returns:
            pandas.DataFrame: DataFrame with market index data
        """
        logger.info(f"Fetching market data for {market_index}")
        return self.fetch_data(market_index, period, interval, force_sample)

    def _fetch_from_api(self, ticker, period="5y"):
        """Fetch data from Financial Modeling Prep API"""
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

        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Construct API URL
        base_url = "https://financialmodelingprep.com/api/v3/historical-price-full"
        url = f"{base_url}/{ticker}?from={start_str}&to={end_str}&apikey={self.api_key}"

        # Make request
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(
                f"API request failed with status code {response.status_code}: {response.text}"
            )

        # Parse response
        data = response.json()

        if "historical" not in data:
            raise ValueError(f"No historical data found for {ticker}")

        # Convert to DataFrame
        df = pd.DataFrame(data["historical"])

        # Convert date to datetime and set as index
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # Sort by date (ascending)
        df = df.sort_index()

        # Rename columns to match expected format
        df = df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )

        return df

    def _generate_sample_data(self, ticker, period="5y", interval="1d"):
        """Generate sample data for testing"""
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
            df["Open"] = start_price * np.cumprod(
                1 + np.random.normal(0.0003, 0.008, n)
            )
            df["Close"] = start_price * np.cumprod(
                1 + np.random.normal(0.0003, 0.008, n)
            )
            df["High"] = df["Close"] * np.random.uniform(1.005, 1.01, n)
            df["Low"] = df["Close"] * np.random.uniform(0.99, 0.995, n)

        return df


if __name__ == "__main__":
    # Simple test
    fetcher = DataFetcher()
    data = fetcher.fetch_data("AAPL", period="1y", force_sample=True)
    print(data.head())
    print(f"Got {len(data)} rows of data for AAPL")
