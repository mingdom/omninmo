#!/usr/bin/env python3
"""
Script to train the XGBoost stock rating prediction model on default tickers.
"""

import os
import sys
import argparse
import logging
import pickle

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
try:
    from src.data.fmp_data_fetcher import FMPDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.models.xgboost_predictor import XGBoostRatingPredictor
    from src.utils.trainer import DEFAULT_TICKERS
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def train_xgboost_model(tickers, model_path, period="5y", interval="1d", forward_days=20, force_sample=False):
    """
    Train an XGBoost model on historical data for a set of tickers.

    Args:
        tickers (list): List of ticker symbols
        model_path (str): Path to save the trained model
        period (str): Period to fetch data for (default: '5y')
        interval (str): Data interval (default: '1d')
        forward_days (int): Number of days to look ahead for returns
        force_sample (bool): Force the use of sample data instead of fetching from API

    Returns:
        XGBoostRatingPredictor: Trained model
    """
    # Initialize components
    fetcher = FMPDataFetcher(cache_dir="cache")
    feature_engineer = FeatureEngineer()
    predictor = XGBoostRatingPredictor()

    # Collect data and features for all tickers
    all_features = []
    all_targets = []

    print(f"Training XGBoost model on {len(tickers)} tickers...")
    
    for ticker in tickers:
        try:
            # Fetch historical data
            print(f"Fetching data for {ticker}...")
            data = fetcher.fetch_data(ticker, period=period, interval=interval, force_sample=force_sample)
            
            if data is None or data.empty:
                logger.warning(f"No data available for {ticker}, skipping")
                continue
                
            # Calculate technical indicators
            print(f"Calculating indicators for {ticker}...")
            features = feature_engineer.calculate_indicators(data)
            
            if features is None or features.empty:
                logger.warning(f"Failed to calculate indicators for {ticker}, skipping")
                continue
                
            # Prepare target variable (future returns)
            # Make sure we're using the price column from the original data
            if 'Close' not in data.columns:
                logger.warning(f"No 'Close' column in data for {ticker}, skipping")
                continue
                
            future_returns = data['Close'].shift(-forward_days) / data['Close'] - 1
            
            # Remove rows with NaN values
            valid_indices = ~(features.isna().any(axis=1) | future_returns.isna())
            valid_features = features[valid_indices]
            valid_returns = future_returns[valid_indices]
            
            if len(valid_features) == 0:
                logger.warning(f"No valid data after preprocessing for {ticker}, skipping")
                continue
                
            # Convert returns to rating categories
            def get_rating(return_value):
                if return_value > 0.05:
                    return 'Strong Buy'
                elif return_value > 0.02:
                    return 'Buy'
                elif return_value > -0.02:
                    return 'Hold'
                elif return_value > -0.05:
                    return 'Sell'
                else:
                    return 'Strong Sell'
            
            ratings = valid_returns.apply(get_rating)
            
            # Add to collection
            all_features.append(valid_features)
            all_targets.append(ratings)
            
            print(f"Processed {ticker}: {len(valid_features)} samples")
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            continue
    
    if not all_features or not all_targets:
        logger.error("No valid data collected for any ticker")
        return None
        
    # Combine data from all tickers
    X = pd.concat(all_features, axis=0)
    y = pd.concat(all_targets, axis=0)
    
    print(f"Combined dataset: {X.shape[0]} samples, {X.shape[1]} features")
    
    # Train the model
    print("Training XGBoost model...")
    training_results = predictor.train(X, y)
    
    if training_results:
        print(f"Training accuracy: {training_results['accuracy']:.4f}")
        
        # Get top features by importance
        top_features = predictor.get_feature_importance(top_n=10)
        print("Top 10 features by importance:")
        for feature, importance in top_features.items():
            print(f"  {feature}: {importance:.4f}")
    
    # Save the model
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(predictor, f)
    
    print(f"Model saved to {model_path}")
    return predictor

def train_on_default_tickers(model_path='models/xgboost_predictor.pkl', period='2y', tickers=None, force_sample=False):
    """
    Train the XGBoost stock rating predictor model on default tickers.
    
    Args:
        model_path (str): Path to save the trained model
        period (str): Time period for historical data (e.g., '1y', '2y')
        tickers (list): List of ticker symbols to use for training. If None, uses DEFAULT_TICKERS
        force_sample (bool): Force the use of sample data instead of fetching from API
    
    Returns:
        XGBoostRatingPredictor: Trained model instance
    """
    logger.info("Starting XGBoost model training on default tickers")
    
    # Use default tickers if none provided
    if tickers is None:
        tickers = DEFAULT_TICKERS
    
    # Create directory for model if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    
    try:
        # Call the main training function
        model = train_xgboost_model(tickers, model_path, period=period, force_sample=force_sample)
        logger.info(f"XGBoost model trained and saved to {model_path}")
        return model
    except Exception as e:
        logger.error(f"Error during XGBoost model training: {e}")
        return None

def main():
    """Main function to parse arguments and train the model."""
    parser = argparse.ArgumentParser(description='Train the XGBoost stock rating prediction model.')
    parser.add_argument('--model-path', type=str, default='models/stock_predictor.pkl',
                        help='Path to save the trained model')
    parser.add_argument('--period', type=str, default='2y',
                        help='Time period for historical data (e.g., 1y, 2y)')
    parser.add_argument('--tickers', type=str, nargs='+',
                        help='List of ticker symbols to use for training')
    parser.add_argument('--force-sample', action='store_true',
                        help='Force the use of sample data instead of fetching from API')
    
    args = parser.parse_args()
    
    # Use provided tickers or default ones
    tickers = args.tickers if args.tickers else DEFAULT_TICKERS
    
    logger.info(f"Starting XGBoost model training with {len(tickers)} tickers for period {args.period}")
    
    # Train the model
    model = train_on_default_tickers(
        model_path=args.model_path,
        period=args.period,
        tickers=tickers,
        force_sample=args.force_sample
    )
    
    if model is not None:
        logger.info("XGBoost model training completed successfully")
        sys.exit(0)
    else:
        logger.error("XGBoost model training failed")
        sys.exit(1)

if __name__ == '__main__':
    # Import pandas here to avoid circular imports
    import pandas as pd
    main() 