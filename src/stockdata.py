"""
Stock data interface and factory.

This module provides:
1. A common interface for data fetchers (DataFetcherInterface)
2. A factory function to create data fetchers (create_data_fetcher)

This allows for interchangeable use of different data sources (FMP API, Yahoo Finance, etc.)
with runtime selection between them.
"""

import logging
import os
from abc import ABC, abstractmethod

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
    is_huggingface = os.environ.get('HF_SPACE') == '1' or os.environ.get('SPACE_ID') is not None

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
