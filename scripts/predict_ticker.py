#!/usr/bin/env python3
"""
Script for quick command-line stock predictions.
"""

import os
import sys
import argparse
import logging
import pandas as pd

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

def predict_ticker(ticker, model_path='models/stock_predictor.pkl', period='1y'):
    """
    Predict the rating for a given ticker.
    
    Args:
        ticker (str): Stock ticker symbol
        model_path (str): Path to the trained model
        period (str): Time period for historical data
    
    Returns:
        tuple: (rating, confidence, indicators)
    """
    # Load the model
    model = load_model(model_path)
    if model is None:
        logger.error(f"Failed to load model from {model_path}")
        return None, 0, None
    
    # Initialize components
    data_fetcher = StockDataFetcher()
    feature_engineer = FeatureEngineer()
    
    try:
        # Fetch historical data
        stock_data = data_fetcher.fetch_data(ticker, period=period)
        
        if stock_data is None or stock_data.empty:
            logger.error(f"No data available for {ticker}")
            return None, 0, None
            
        # Engineer features
        features = feature_engineer.calculate_indicators(stock_data)
        
        if features is None or features.empty:
            logger.error(f"Failed to calculate features for {ticker}")
            return None, 0, None
        
        # Get the most recent features for prediction
        recent_features = features.iloc[[-1]]
        
        # Make prediction
        rating, confidence = model.predict(recent_features)
        
        # Extract key indicators
        indicators = {
            "RSI": features.iloc[-1]['RSI'],
            "MACD": features.iloc[-1]['MACD'],
            "Price to 50-day MA": features.iloc[-1]['Price_to_SMA_50'],
            "Price to 200-day MA": features.iloc[-1]['Price_to_SMA_200'],
            "Bollinger Band Width": features.iloc[-1]['BB_Width']
        }
        
        return rating, confidence, indicators
        
    except Exception as e:
        logger.error(f"Error predicting {ticker}: {e}")
        return None, 0, None

def main():
    """Main function to parse arguments and make predictions."""
    parser = argparse.ArgumentParser(description='Predict stock rating for a ticker.')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--model-path', type=str, default='models/stock_predictor.pkl',
                        help='Path to the trained model')
    parser.add_argument('--period', type=str, default='1y',
                        help='Time period for historical data (e.g., 1y, 2y)')
    
    args = parser.parse_args()
    
    print(f"Analyzing {args.ticker}...")
    
    # Make prediction
    rating, confidence, indicators = predict_ticker(
        args.ticker,
        model_path=args.model_path,
        period=args.period
    )
    
    if rating is None:
        print(f"Failed to predict rating for {args.ticker}")
        sys.exit(1)
    
    # Print results
    print(f"\nomninmo Rating: {rating} (Confidence: {confidence:.2%})")
    
    if indicators:
        print("\nKey Indicators:")
        for name, value in indicators.items():
            print(f"- {name}: {value:.2f}")
    
    # Add interpretation
    print("\nInterpretation:")
    if rating == "Strong Buy":
        print("- Technical indicators suggest strong positive momentum")
    elif rating == "Buy":
        print("- Technical indicators suggest positive momentum")
    elif rating == "Hold":
        print("- Technical indicators suggest neutral momentum")
    elif rating == "Sell":
        print("- Technical indicators suggest negative momentum")
    elif rating == "Strong Sell":
        print("- Technical indicators suggest strong negative momentum")

if __name__ == '__main__':
    main() 