"""
Core functionality tests for the omninmo application.
This file contains tests for the essential components of the application.
"""

import unittest
import os
import sys
import pandas as pd
import logging
from unittest.mock import patch, MagicMock

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCore(unittest.TestCase):
    """Test core functionality of the application."""
    
    def setUp(self):
        """Set up test fixtures."""
        from src.data.stock_data_fetcher import StockDataFetcher
        from src.utils.feature_engineer import FeatureEngineer
        from src.utils.trainer import load_model
        
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_fetcher = StockDataFetcher(cache_dir=os.path.join(self.project_root, "cache"))
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(self.project_root, "models", "stock_predictor.pkl")
        
        # Test with a single ticker and short period to keep tests fast
        self.test_ticker = "AAPL"
        self.period = "1mo"
        self.use_sample_data = True  # Always use sample data for testing
    
    def test_data_fetching(self):
        """Test that data can be fetched for a ticker."""
        data = self.data_fetcher.fetch_data(self.test_ticker, period=self.period, force_sample=self.use_sample_data)
        
        # Check that data is not None or empty
        self.assertIsNotNone(data, f"Data for {self.test_ticker} should not be None")
        self.assertFalse(data.empty, f"Data for {self.test_ticker} should not be empty")
        
        # Check that data has the expected columns
        expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in expected_columns:
            self.assertIn(col, data.columns, f"Data should contain column '{col}'")
        
        logger.info(f"Successfully fetched {len(data)} records for {self.test_ticker}")
    
    def test_feature_engineering(self):
        """Test that features can be calculated from ticker data."""
        # Get data first
        data = self.data_fetcher.fetch_data(self.test_ticker, period=self.period, force_sample=self.use_sample_data)
        
        # Calculate features
        features = self.feature_engineer.calculate_indicators(data)
        
        # Check that features is not None or empty
        self.assertIsNotNone(features, "Features should not be None")
        self.assertFalse(features.empty, "Features should not be empty")
        
        # Check that we have a reasonable number of features
        self.assertGreater(features.shape[1], 10, "Should have calculated at least 10 features")
        
        logger.info(f"Successfully calculated {features.shape[1]} features")
    
    def test_model_prediction(self):
        """Test that the model can make predictions."""
        # Skip if model doesn't exist
        if not os.path.exists(self.model_path):
            self.skipTest(f"Model not found at {self.model_path}")
        
        # Load the model
        from src.utils.trainer import load_model
        model = load_model(self.model_path)
        self.assertIsNotNone(model, "Model should not be None")
        
        # Get data and features
        data = self.data_fetcher.fetch_data(self.test_ticker, period=self.period, force_sample=self.use_sample_data)
        features = self.feature_engineer.calculate_indicators(data)
        
        # Make a prediction
        recent_features = features.iloc[[-1]]
        rating, confidence = model.predict(recent_features)
        
        # Check that rating is one of the expected values
        expected_ratings = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
        self.assertIn(rating, expected_ratings, f"Rating should be one of {expected_ratings}")
        
        # Check that confidence is a float between 0 and 1
        self.assertIsInstance(confidence, float, "Confidence should be a float")
        self.assertGreaterEqual(confidence, 0, "Confidence should be >= 0")
        self.assertLessEqual(confidence, 1, "Confidence should be <= 1")
        
        logger.info(f"Prediction for {self.test_ticker}: {rating} (Confidence: {confidence:.2%})")
    
    @patch('src.app.streamlit_app.analyze_single_ticker_for_watchlist')
    def test_watchlist_analysis(self, mock_analyze):
        """Test that the watchlist analysis function works."""
        from src.app.streamlit_app import analyze_watchlist
        
        # Mock the analyze_single_ticker_for_watchlist function
        mock_result = {
            'ticker': self.test_ticker,
            'data': pd.DataFrame(),
            'features': pd.DataFrame(),
            'rating': 'Buy',
            'confidence': 0.75,
            'latest_price': 150.0,
            'price_change': 5.0,
            'price_change_pct': 0.0345,
            'indicators': {},
            'last_updated': '2023-01-01'
        }
        mock_analyze.return_value = mock_result
        
        # Mock streamlit components
        with patch('streamlit.progress') as mock_progress, patch('streamlit.empty') as mock_empty:
            mock_progress.return_value.progress = MagicMock()
            mock_empty.return_value.text = MagicMock()
            
            # Test with a single ticker to keep it simple
            results = analyze_watchlist(
                [self.test_ticker],
                self.period,
                self.data_fetcher,
                self.feature_engineer,
                None,  # Model not needed due to mock
                self.use_sample_data
            )
            
            # Check that results is a dictionary with the ticker
            self.assertIsInstance(results, dict, "Results should be a dictionary")
            self.assertIn(self.test_ticker, results, f"Results should contain {self.test_ticker}")
            
            # Check that the mock was called
            mock_analyze.assert_called_once()
            
            logger.info(f"Successfully tested watchlist analysis for {self.test_ticker}")

if __name__ == '__main__':
    unittest.main() 