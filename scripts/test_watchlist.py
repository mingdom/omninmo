#!/usr/bin/env python3
"""
Script to test the watch list functionality in the omninmo Streamlit app.
"""

import os
import sys
import logging
import pandas as pd
import unittest
from unittest.mock import patch, MagicMock
import concurrent.futures

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Import project modules
try:
    from src.data.stock_data_fetcher import StockDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.utils.trainer import load_model
    from src.app.streamlit_app import analyze_single_ticker_for_watchlist, analyze_watchlist
    logger.info("Successfully imported project modules")
except ImportError as e:
    logger.error(f"Failed to import project modules: {e}")
    sys.exit(1)

class TestWatchList(unittest.TestCase):
    """Test cases for the watch list functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_fetcher = StockDataFetcher(cache_dir=os.path.join(project_root, "cache"))
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(project_root, "models", "stock_predictor.pkl")
        self.model = load_model(self.model_path)
        
        # Test tickers
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]
        self.period = "1mo"
        self.use_sample_data = True  # Use sample data for testing
    
    def test_analyze_single_ticker(self):
        """Test analyzing a single ticker for the watch list."""
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
            
            # Check if rating is one of the expected values
            expected_ratings = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
            self.assertIn(result['rating'], expected_ratings, f"Rating for {ticker} should be one of {expected_ratings}")
            
            # Check if confidence is a float between 0 and 1
            self.assertIsInstance(result['confidence'], float, f"Confidence for {ticker} should be a float")
            self.assertGreaterEqual(result['confidence'], 0, f"Confidence for {ticker} should be >= 0")
            self.assertLessEqual(result['confidence'], 1, f"Confidence for {ticker} should be <= 1")
            
            # Check if indicators is a dictionary
            self.assertIsInstance(result['indicators'], dict, f"Indicators for {ticker} should be a dictionary")
            
            logger.info(f"Successfully tested analyze_single_ticker_for_watchlist for {ticker}")
    
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    def test_analyze_watchlist(self, mock_empty, mock_progress):
        """Test analyzing multiple tickers in the watch list."""
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
        
        logger.info(f"Successfully tested analyze_watchlist for {len(self.test_tickers)} tickers")
    
    @patch('src.app.streamlit_app.ThreadPoolExecutor')
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    def test_analyze_watchlist_error_handling(self, mock_empty, mock_progress, mock_executor):
        """Test error handling in analyze_watchlist."""
        # Mock streamlit components
        mock_progress.return_value.progress = MagicMock()
        mock_progress.return_value.empty = MagicMock()
        mock_empty.return_value.text = MagicMock()
        
        # Mock ThreadPoolExecutor to simulate errors
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Test exception")
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        # Test analyze_watchlist function with error
        results = analyze_watchlist(
            self.test_tickers,
            self.period,
            self.data_fetcher,
            self.feature_engineer,
            self.model,
            self.use_sample_data
        )
        
        # Check if results is an empty dictionary
        self.assertIsInstance(results, dict, "Results should be a dictionary")
        self.assertEqual(len(results), 0, "Results should be empty due to simulated errors")
        
        logger.info("Successfully tested error handling in analyze_watchlist")

def main():
    """Run the tests."""
    unittest.main()

if __name__ == '__main__':
    main() 