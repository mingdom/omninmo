#!/usr/bin/env python3
"""
Test script for the FMP data fetcher.
"""

import os
import sys
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, using environment variables as is")

# Import the FMPDataFetcher
from src.data.fmp_data_fetcher import FMPDataFetcher

def test_fmp_data_fetcher():
    """Test the FMPDataFetcher class."""
    logger.info("Testing FMPDataFetcher...")
    
    # Create a cache directory
    cache_dir = os.path.join(project_root, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Initialize the data fetcher
    data_fetcher = FMPDataFetcher(cache_dir=cache_dir)
    
    # Test fetching data for a single ticker
    ticker = "AAPL"
    period = "1mo"
    interval = "1d"
    
    logger.info(f"Fetching data for {ticker} with period={period}, interval={interval}")
    data = data_fetcher.fetch_data(ticker, period, interval)
    
    if data is not None and not data.empty:
        logger.info(f"Successfully fetched {len(data)} records for {ticker}")
        logger.info(f"Sample data:\n{data.head()}")
    else:
        logger.error(f"Failed to fetch data for {ticker}")
    
    # Test fetching data for multiple tickers
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    logger.info(f"Fetching data for multiple tickers: {tickers}")
    data_dict = data_fetcher.fetch_multiple(tickers, period, interval)
    
    for ticker, data in data_dict.items():
        if data is not None and not data.empty:
            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
        else:
            logger.error(f"Failed to fetch data for {ticker}")
    
    logger.info("FMPDataFetcher test completed")

if __name__ == "__main__":
    test_fmp_data_fetcher() 