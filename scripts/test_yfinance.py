#!/usr/bin/env python3
"""
Script to test the yfinance API directly.
"""

import os
import sys
import logging
import yfinance as yf
import pandas as pd
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ticker(ticker, period='1mo'):
    """Test fetching data for a single ticker."""
    logger.info(f"Testing ticker: {ticker} with period {period}")
    
    # Try direct download method
    try:
        logger.info(f"Trying yf.download for {ticker}...")
        data = yf.download(
            ticker, 
            period=period, 
            progress=False,
            timeout=30
        )
        
        if not data.empty:
            logger.info(f"Successfully fetched {len(data)} records for {ticker} using yf.download")
            return data
        else:
            logger.warning(f"Empty data returned for {ticker} using yf.download")
    except Exception as e:
        logger.error(f"Error using yf.download for {ticker}: {e}")
    
    # Try Ticker method
    try:
        logger.info(f"Trying yf.Ticker for {ticker}...")
        time.sleep(random.uniform(1, 3))  # Add random delay
        
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if not data.empty:
            logger.info(f"Successfully fetched {len(data)} records for {ticker} using yf.Ticker")
            return data
        else:
            logger.warning(f"Empty data returned for {ticker} using yf.Ticker")
    except Exception as e:
        logger.error(f"Error using yf.Ticker for {ticker}: {e}")
    
    logger.error(f"Failed to fetch data for {ticker} using both methods")
    return None

def main():
    """Main function to test yfinance API."""
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']
    
    results = {}
    for ticker in test_tickers:
        data = test_ticker(ticker)
        results[ticker] = data is not None and not data.empty
        time.sleep(random.uniform(2, 4))  # Add delay between requests
    
    # Print summary
    logger.info("=== Test Results ===")
    for ticker, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{ticker}: {status}")
    
    # Overall result
    success_count = sum(1 for success in results.values() if success)
    logger.info(f"Successfully fetched data for {success_count}/{len(test_tickers)} tickers")
    
    return 0 if success_count == len(test_tickers) else 1

if __name__ == '__main__':
    sys.exit(main()) 