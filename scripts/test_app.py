#!/usr/bin/env python3
"""
Script to test the omninmo application components.
"""

import os
import sys
import logging
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the application components."""
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Add the project root to the Python path
    sys.path.insert(0, project_root)
    
    # Import project modules
    try:
        from src.data.stock_data_fetcher import StockDataFetcher
        from src.utils.feature_engineer import FeatureEngineer
        from src.utils.trainer import load_model
        logger.info("Successfully imported project modules")
    except ImportError as e:
        logger.error(f"Failed to import project modules: {e}")
        sys.exit(1)
    
    # Test data fetching
    logger.info("Testing data fetching...")
    data_fetcher = StockDataFetcher(cache_dir=os.path.join(project_root, "cache"))
    
    ticker = "AAPL"
    period = "1mo"
    
    try:
        data = data_fetcher.fetch_data(ticker, period=period)
        if data is None or data.empty:
            logger.error(f"Failed to fetch data for {ticker}")
            return 1
        logger.info(f"Successfully fetched {len(data)} records for {ticker}")
        
        # Print the first few rows
        print("\nSample data:")
        print(data.head())
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return 1
    
    # Test feature engineering
    logger.info("\nTesting feature engineering...")
    feature_engineer = FeatureEngineer()
    
    try:
        features = feature_engineer.calculate_indicators(data)
        if features is None or features.empty:
            logger.error("Failed to calculate features")
            return 1
        logger.info(f"Successfully calculated {features.shape[1]} features")
        
        # Print the first few rows of features
        print("\nSample features:")
        print(features.head())
        
    except Exception as e:
        logger.error(f"Error calculating features: {e}")
        return 1
    
    # Test model loading
    logger.info("\nTesting model loading...")
    model_path = os.path.join(project_root, "models", "stock_predictor.pkl")
    
    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}. Skipping model testing.")
        print("\nNOTE: To complete all tests, train the model first with:")
        print("    make train")
        return 0
    
    try:
        model = load_model(model_path)
        if model is None:
            logger.error("Failed to load model")
            return 1
        logger.info("Successfully loaded model")
        
        # Test prediction
        logger.info("\nTesting prediction...")
        recent_features = features.iloc[[-1]]
        
        rating, confidence = model.predict(recent_features)
        logger.info(f"Prediction for {ticker}: {rating} (Confidence: {confidence:.2%})")
        
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        return 1
    
    logger.info("\nAll tests passed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 