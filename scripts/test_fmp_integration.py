#!/usr/bin/env python3
"""
Test script to verify that our app works with the FMP data fetcher.
"""

import os
import sys
import logging
import pandas as pd
import unittest
from unittest.mock import patch, MagicMock

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

# Import project modules
from src.data.fmp_data_fetcher import FMPDataFetcher
from src.utils.feature_engineer import FeatureEngineer
from src.utils.trainer import load_model
from src.app.streamlit_app import analyze_single_ticker_for_watchlist, analyze_watchlist

class TestFMPIntegration(unittest.TestCase):
    """Test case for FMP data fetcher integration with the app."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache_dir = os.path.join(project_root, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.data_fetcher = FMPDataFetcher(cache_dir=self.cache_dir)
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(project_root, "models", "stock_predictor.pkl")
        self.model = load_model(self.model_path)
        
        # Test tickers
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]
        self.period = "1mo"
        self.use_sample_data = False  # Use real data for testing
    
    def test_analyze_single_ticker(self):
        """Test analyzing a single ticker with FMP data."""
        logger.info("Testing analyze_single_ticker_for_watchlist with FMP data...")
        
        for ticker in self.test_tickers:
            result = analyze_single_ticker_for_watchlist(
                ticker, 
                self.period, 
                self.data_fetcher, 
                self.feature_engineer, 
                self.model, 
                self.use_sample_data
            )
            
            # Check if result is not None
            self.assertIsNotNone(result, f"Result for {ticker} should not be None")
            
            # Check if result contains expected keys
            expected_keys = [
                'ticker', 'data', 'features', 'rating', 'confidence', 
                'latest_price', 'price_change', 'price_change_pct', 
                'indicators', 'last_updated'
            ]
            for key in expected_keys:
                self.assertIn(key, result, f"Result for {ticker} should contain key '{key}'")
            
            # Check if data and features are pandas DataFrames
            self.assertIsInstance(result['data'], pd.DataFrame, f"Data for {ticker} should be a DataFrame")
            self.assertIsInstance(result['features'], pd.DataFrame, f"Features for {ticker} should be a DataFrame")
            
            # Check if rating is one of the expected values or 'Error'
            expected_ratings = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell', 'Error']
            self.assertIn(result['rating'], expected_ratings, f"Rating for {ticker} should be one of {expected_ratings}")
            
            # If not an error, check confidence
            if result['rating'] != 'Error':
                # Check if confidence is a float between 0 and 1
                self.assertIsInstance(result['confidence'], float, f"Confidence for {ticker} should be a float")
                self.assertGreaterEqual(result['confidence'], 0, f"Confidence for {ticker} should be >= 0")
                self.assertLessEqual(result['confidence'], 1, f"Confidence for {ticker} should be <= 1")
            
            # Check if indicators is a dictionary
            self.assertIsInstance(result['indicators'], dict, f"Indicators for {ticker} should be a dictionary")
            
            logger.info(f"Successfully tested analyze_single_ticker_for_watchlist with FMP data for {ticker}")
    
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    def test_analyze_watchlist(self, mock_empty, mock_progress):
        """Test analyzing multiple tickers in the watch list with FMP data."""
        logger.info("Testing analyze_watchlist with FMP data...")
        
        # Mock streamlit components
        mock_progress.return_value.progress = MagicMock()
        mock_progress.return_value.empty = MagicMock()
        mock_empty.return_value.text = MagicMock()
        
        # Test analyze_watchlist function
        results = analyze_watchlist(
            self.test_tickers,
            self.period,
            self.data_fetcher,
            self.feature_engineer,
            self.model,
            self.use_sample_data,
            max_workers=3
        )
        
        # Check if results is a dictionary
        self.assertIsInstance(results, dict, "Results should be a dictionary")
        
        # Check if all test tickers are in the results
        for ticker in self.test_tickers:
            self.assertIn(ticker, results, f"Results should contain {ticker}")
            
            # Check if result for ticker is not None
            self.assertIsNotNone(results[ticker], f"Result for {ticker} should not be None")
        
        logger.info(f"Successfully tested analyze_watchlist with FMP data for {len(self.test_tickers)} tickers")

def main():
    """Run the tests."""
    unittest.main()

if __name__ == "__main__":
    main() 