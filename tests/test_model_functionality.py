"""
Model functionality tests for the omninmo application.
This file contains tests for the model training and prediction components.
"""

import unittest
import os
import sys
import pandas as pd
import logging
import tempfile

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestModelFunctionality(unittest.TestCase):
    """Test model functionality of the application."""
    
    def setUp(self):
        """Set up test fixtures."""
        from src.data.stock_data_fetcher import StockDataFetcher
        from src.utils.feature_engineer import FeatureEngineer
        
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_fetcher = StockDataFetcher(cache_dir=os.path.join(self.project_root, "cache"))
        self.feature_engineer = FeatureEngineer()
        
        # Test with a single ticker and short period to keep tests fast
        self.test_tickers = ["AAPL"]
        self.period = "1mo"
        self.use_sample_data = True  # Always use sample data for testing
    
    def test_model_training(self):
        """Test that a model can be trained."""
        from src.utils.trainer import train_model
        from src.models.xgboost_predictor import XGBoostRatingPredictor
        
        # Create a temporary file for the model
        with tempfile.NamedTemporaryFile(suffix='.pkl') as temp_model_file:
            model_path = temp_model_file.name
            
            # Train the model
            result = train_model(
                self.test_tickers,
                model_path,
                period="1mo",
                force_sample=self.use_sample_data
            )
            
            # Check that the result is either a float (accuracy) or a model object
            self.assertTrue(
                isinstance(result, float) or isinstance(result, XGBoostRatingPredictor),
                "Result should be either a float (accuracy) or a model object"
            )
            
            if isinstance(result, float):
                # If it's a float, it's the accuracy
                accuracy = result
                self.assertGreaterEqual(accuracy, 0, "Accuracy should be >= 0")
                self.assertLessEqual(accuracy, 1, "Accuracy should be <= 1")
                logger.info(f"Successfully trained model with accuracy: {accuracy:.4f}")
            else:
                # If it's a model object, log that we got a model back
                logger.info("Successfully trained model and got model object back")
            
            # Check that the model file exists
            self.assertTrue(os.path.exists(model_path), f"Model file should exist at {model_path}")
    
    def test_model_loading(self):
        """Test that a model can be loaded."""
        from src.utils.trainer import train_model, load_model
        
        # Create a temporary file for the model
        with tempfile.NamedTemporaryFile(suffix='.pkl') as temp_model_file:
            model_path = temp_model_file.name
            
            # Train the model
            train_model(
                self.test_tickers,
                model_path,
                period="1mo",
                force_sample=self.use_sample_data
            )
            
            # Load the model
            model = load_model(model_path)
            
            # Check that the model is not None
            self.assertIsNotNone(model, "Model should not be None")
            
            logger.info("Successfully loaded model")
    
    def test_model_prediction(self):
        """Test that a model can make predictions."""
        from src.utils.trainer import train_model, load_model
        
        # Create a temporary file for the model
        with tempfile.NamedTemporaryFile(suffix='.pkl') as temp_model_file:
            model_path = temp_model_file.name
            
            # Train the model
            train_model(
                self.test_tickers,
                model_path,
                period="1mo",
                force_sample=self.use_sample_data
            )
            
            # Load the model
            model = load_model(model_path)
            
            # Get data and features for prediction
            data = self.data_fetcher.fetch_data(
                self.test_tickers[0],
                period=self.period,
                force_sample=self.use_sample_data
            )
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
            
            logger.info(f"Prediction for {self.test_tickers[0]}: {rating} (Confidence: {confidence:.2%})")

if __name__ == '__main__':
    unittest.main() 