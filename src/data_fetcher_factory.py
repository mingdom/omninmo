"""
Factory for data fetcher creation.

This module provides a factory function for creating data fetchers,
allowing for runtime selection between different data sources.
"""

import logging

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
    # Set default cache directories based on data source
    if cache_dir is None:
        cache_dir = ".cache_yf" if source == "yfinance" else ".cache_fmp"
    
    if source == "yfinance":
        from src.yfinance import YFinanceDataFetcher
        logger.info(f"Creating YFinance data fetcher with cache dir: {cache_dir}")
        return YFinanceDataFetcher(cache_dir=cache_dir)
    elif source == "fmp":
        from src.v2.data_fetcher import DataFetcher
        logger.info(f"Creating FMP data fetcher with cache dir: {cache_dir}")
        return DataFetcher(cache_dir=cache_dir)
    else:
        raise ValueError(f"Unknown data source: {source}")
