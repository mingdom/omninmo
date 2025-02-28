#!/usr/bin/env python3
"""
Script to test the stock rating prediction model.
"""

import os
import sys
import argparse
import logging
import pandas as pd
from sklearn.metrics import classification_report

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
try:
    from src.data.stock_data_fetcher import StockDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.utils.trainer import load_model
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def test_model(model_path='models/stock_predictor.pkl', test_tickers=None, period='1y'):
    """
    Test the stock rating prediction model on the provided tickers.
    
    Args:
        model_path (str): Path to the trained model
        test_tickers (list): List of ticker symbols to test on
        period (str): Time period for historical data
    
    Returns:
        dict: Dictionary containing test results
    """
    # Default test tickers if none provided
    if test_tickers is None:
        test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    # Load the model
    model = load_model(model_path)
    if model is None:
        logger.error(f"Failed to load model from {model_path}")
        return None
    
    # Initialize components
    data_fetcher = StockDataFetcher()
    feature_engineer = FeatureEngineer()
    
    # Collect test data
    all_features = []
    all_labels = []
    
    logger.info(f"Testing model on {len(test_tickers)} tickers")
    
    for ticker in test_tickers:
        try:
            # Fetch historical data
            stock_data = data_fetcher.fetch_data(ticker, period=period)
            
            if stock_data is None or stock_data.empty:
                logger.warning(f"No data available for {ticker}, skipping")
                continue
                
            # Engineer features
            features = feature_engineer.calculate_indicators(stock_data)
            
            if features is None or features.empty:
                logger.warning(f"Failed to calculate features for {ticker}, skipping")
                continue
            
            # Generate labels (this is simplified - in a real scenario, you'd have actual labels)
            # For demonstration, we'll use a simple rule-based approach
            returns = stock_data['Close'].pct_change(20)  # 20-day returns
            labels = pd.cut(returns, 
                           bins=[-float('inf'), -0.1, -0.03, 0.03, 0.1, float('inf')],
                           labels=['Strong Sell', 'Sell', 'Hold', 'Buy', 'Strong Buy'])
            
            # Remove NaN values
            valid_idx = ~(features.isna().any(axis=1) | labels.isna())
            filtered_features = features[valid_idx]
            filtered_labels = labels[valid_idx]
            
            all_features.append(filtered_features)
            all_labels.append(filtered_labels)
            
            logger.info(f"Successfully processed {ticker}: {len(filtered_features)} valid samples")
            
            # Test on the most recent data point
            if not filtered_features.empty:
                recent_features = filtered_features.iloc[[-1]]
                rating, confidence = model.predict(recent_features)
                logger.info(f"{ticker} prediction: {rating} (Confidence: {confidence:.2%})")
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
    
    if not all_features or not all_labels:
        logger.error("No valid test data collected")
        return None
    
    # Combine all data
    X = pd.concat(all_features, axis=0)
    y = pd.concat(all_labels, axis=0)
    
    # Evaluate the model
    results = model.evaluate(X, y)
    
    if results:
        logger.info(f"Test accuracy: {results['accuracy']:.4f}")
        logger.info("Classification Report:")
        for label, metrics in results['classification_report'].items():
            if isinstance(metrics, dict):
                logger.info(f"{label}: precision={metrics['precision']:.2f}, recall={metrics['recall']:.2f}, f1-score={metrics['f1-score']:.2f}")
    
    return results

def main():
    """Main function to parse arguments and test the model."""
    parser = argparse.ArgumentParser(description='Test the stock rating prediction model.')
    parser.add_argument('--model-path', type=str, default='models/stock_predictor.pkl',
                        help='Path to the trained model')
    parser.add_argument('--tickers', type=str, nargs='+',
                        help='List of ticker symbols to test on')
    parser.add_argument('--period', type=str, default='1y',
                        help='Time period for historical data (e.g., 1y, 2y)')
    
    args = parser.parse_args()
    
    # Test the model
    results = test_model(
        model_path=args.model_path,
        test_tickers=args.tickers,
        period=args.period
    )
    
    if results is None:
        logger.error("Model testing failed")
        sys.exit(1)

if __name__ == '__main__':
    main() 