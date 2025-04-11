"""
Stock data interface and factory.

This module provides:
1. A common interface for data fetchers (DataFetcherInterface)
2. A factory function to create data fetchers (create_data_fetcher)
3. Utility functions for cache management and market hours

This allows for interchangeable use of different data sources (FMP API, Yahoo Finance, etc.)
with runtime selection between them.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime

import pytz

logger = logging.getLogger(__name__)


class DataFetcherInterface(ABC):
    """Interface for stock data fetchers"""

    # Default period for beta calculations
    beta_period = "6m"

    @abstractmethod
    def fetch_data(self, ticker, period="1y", interval="1d"):
        """
        Fetch stock data for a ticker.

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        pass

    @abstractmethod
    def fetch_market_data(self, market_index="SPY", period=None, interval="1d"):
        """
        Fetch market index data for beta calculations.

        Args:
            market_index (str): Market index ticker symbol (default: 'SPY')
            period (str, optional): Time period. If None, uses beta_period.
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with market index data
        """
        pass


def create_data_fetcher(source="yfinance", cache_dir=None):
    """
    Factory function to create the appropriate data fetcher.

    Args:
        source (str): Data source to use ('yfinance' or 'fmp')
        cache_dir (str, optional): Cache directory. If None, uses default.

    Returns:
        DataFetcherInterface: An instance of the appropriate data fetcher

    Raises:
        ValueError: If the specified source is not supported
    """
    # Set default cache directories based on data source and environment
    # In Hugging Face Spaces, use /tmp for cache
    is_huggingface = (
        os.environ.get("HF_SPACE") == "1" or os.environ.get("SPACE_ID") is not None
    )

    if cache_dir is None:
        if is_huggingface:
            # Use /tmp directory for Hugging Face
            cache_dir = "/tmp/cache_yf" if source == "yfinance" else "/tmp/cache_fmp"
        else:
            # Use local directory for other environments
            cache_dir = ".cache_yf" if source == "yfinance" else ".cache_fmp"

    if source == "yfinance":
        from src.yfinance import YFinanceDataFetcher

        logger.info(f"Creating YFinance data fetcher with cache dir: {cache_dir}")
        return YFinanceDataFetcher(cache_dir=cache_dir)
    elif source == "fmp":
        from src.fmp import DataFetcher

        logger.info(f"Creating FMP data fetcher with cache dir: {cache_dir}")
        return DataFetcher(cache_dir=cache_dir)
    else:
        raise ValueError(f"Unknown data source: {source}")


# Cache management functions


def is_cache_expired(cache_timestamp):
    """
    Determine if cache should be considered expired based on market hours.
    Cache expires daily at 2PM Pacific time to ensure we use EOD pricing.

    Args:
        cache_timestamp (float): The timestamp of when the cache was created/modified

    Returns:
        bool: True if cache should be considered expired, False otherwise
    """
    # Convert cache timestamp to datetime
    cache_time = datetime.fromtimestamp(cache_timestamp)

    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone("US/Pacific")
    now = datetime.now(pacific_tz)

    # Convert cache time to Pacific timezone (assuming it's in local time)
    cache_time_pacific = pacific_tz.localize(cache_time)

    # Check if cache is from a previous day
    if cache_time_pacific.date() < now.date():
        # If it's after 2PM Pacific, cache from previous days is expired
        if now.hour >= 14:  # 2PM = 14:00 in 24-hour format
            return True
        # If it's before 2PM, cache is still valid
        return False

    # If cache is from today and it's after 2PM, check if cache was created before 2PM
    if now.hour >= 14 and cache_time_pacific.hour < 14:
        return True

    # In all other cases, cache is still valid
    return False


def should_use_cache(cache_path, cache_ttl):
    """
    Determine if cache should be used based on both TTL and market hours.

    This function centralizes cache validation logic for all data fetchers.
    Cache is considered valid if it's within TTL AND not expired based on market hours.

    Args:
        cache_path (str): Path to the cache file
        cache_ttl (int): Cache time-to-live in seconds

    Returns:
        tuple: (should_use, reason)
            - should_use (bool): True if cache should be used, False otherwise
            - reason (str): Reason for the decision (for logging)
    """
    if not os.path.exists(cache_path):
        return False, "Cache file does not exist"

    # Get cache modification time
    cache_mtime = os.path.getmtime(cache_path)

    # Check TTL
    cache_age = time.time() - cache_mtime
    if cache_age >= cache_ttl:
        return False, f"Cache TTL expired (age: {cache_age:.0f}s > TTL: {cache_ttl}s)"

    # Check market hours
    if is_cache_expired(cache_mtime):
        return False, "Cache expired due to market hours (2PM Pacific cutoff)"

    # Cache is valid
    return True, f"Cache is valid (age: {cache_age:.0f}s)"
