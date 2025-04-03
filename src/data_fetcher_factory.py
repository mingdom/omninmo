"""
Factory for data fetcher creation.

This module provides a factory function for creating data fetchers,
allowing for runtime selection between different data sources.
"""

import logging
import os

logger = logging.getLogger(__name__)


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
