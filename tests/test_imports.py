"""
Test that all imports work correctly.
"""

import unittest
import os
import sys

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestImports(unittest.TestCase):
    """Test that all imports work correctly."""
    
    def test_data_imports(self):
        """Test that data module imports work."""
        try:
            from src.data.stock_data_fetcher import StockDataFetcher
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import StockDataFetcher: {e}")
    
    def test_models_imports(self):
        """Test that models module imports work."""
        try:
            from src.models.stock_rating_predictor import StockRatingPredictor
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import StockRatingPredictor: {e}")
    
    def test_utils_imports(self):
        """Test that utils module imports work."""
        try:
            from src.utils.feature_engineer import FeatureEngineer
            from src.utils.trainer import train_on_default_tickers, load_model
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import utils modules: {e}")
    
    def test_app_imports(self):
        """Test that app module imports work."""
        try:
            import src.app.streamlit_app
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import streamlit_app: {e}")

if __name__ == '__main__':
    unittest.main() 