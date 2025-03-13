"""
Script for training the stock prediction model
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import pandas as pd
import numpy as np

from src.v2.config import config
from src.v2.data_fetcher import DataFetcher
from src.v2.features import Features
from src.v2.predictor import Predictor
from src.v2.training_summary import generate_training_summary, save_training_summary, log_mlflow_metrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/train.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def train_model(tickers=None, model_path=None, period=None, interval=None, 
               forward_days=None, force_sample=False, overwrite=False, mode=None):
    """
    Train a stock prediction model using k-fold cross-validation
    
    Args:
        tickers (list): List of ticker symbols to train on
        model_path (str): Path to save the model
        period (str): Historical data period
        interval (str): Data interval
        forward_days (int): Days to look ahead for returns
        force_sample (bool): Use sample data instead of API
        overwrite (bool): Overwrite existing model without asking
        mode (str): 'regression' or 'classification'
        
    Returns:
        tuple: (Predictor, dict) - Trained model and results including:
            - Cross-validation metrics
            - Feature importance stability
            - Final model performance
    """
    # Load configuration with defaults
    if tickers is None:
        tickers = config.get('model.training.default_tickers')
    
    if period is None:
        period = config.get('model.training.period', '5y')
    
    if interval is None:
        interval = config.get('model.training.interval', '1d')
    
    if forward_days is None:
        forward_days = config.get('model.training.forward_days', 30)
    
    if mode is None:
        mode = config.get('model.prediction.mode', 'regression')
    
    if model_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/st_predictor_{mode}_{timestamp}.pkl"
    
    # Create model path directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    
    # Check if model already exists
    if os.path.exists(model_path) and not overwrite:
        response = input(f"Model file {model_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            logger.info("Training cancelled by user")
            return None, None
    
    # Initialize components
    fetcher = DataFetcher(cache_dir="cache")
    features = Features()
    predictor = Predictor(mode=mode)
    
    # Process tickers
    all_features = []
    all_targets = []
    processed_tickers = []
    skipped_tickers = []
    error_tickers = []
    
    logger.info(f"Training model on {len(tickers)} tickers with {mode} mode")
    logger.info(f"Looking ahead {forward_days} days for returns")
    
    for ticker in tickers:
        try:
            logger.info(f"Processing {ticker}...")
            
            # Fetch data
            df = fetcher.fetch_data(ticker, period=period, interval=interval, force_sample=force_sample)
            
            if df is None or len(df) < 60:
                logger.warning(f"Skipping {ticker}: Insufficient data")
                skipped_tickers.append(ticker)
                continue
            
            # Keep copy of close prices for return calculation
            close_prices = df['Close'].copy()
            
            # Generate features
            df_features = features.generate(df)
            
            if df_features is None or len(df_features) < 30:
                logger.warning(f"Skipping {ticker}: Failed to generate features")
                skipped_tickers.append(ticker)
                continue
            
            # Calculate future returns
            future_returns = close_prices.shift(-forward_days) / close_prices - 1
            df_features['future_return'] = future_returns
            
            # Remove rows with NaN future returns
            df_features = df_features.dropna(subset=['future_return'])
            
            if len(df_features) == 0:
                logger.warning(f"Skipping {ticker}: No valid data after calculating future returns")
                skipped_tickers.append(ticker)
                continue
            
            # Prepare features and target
            X = df_features.drop(['future_return'], axis=1, errors='ignore')
            
            # For classification, convert returns to ratings
            if mode == 'classification':
                # Get rating thresholds
                thresholds = config.get('model.training.rating_thresholds', {})
                strong_buy = thresholds.get('strong_buy', 0.06)
                buy = thresholds.get('buy', 0.03)
                hold = thresholds.get('hold', -0.03)
                sell = thresholds.get('sell', -0.06)
                
                def get_rating(return_value):
                    if return_value > strong_buy:
                        return 'Strong Buy'
                    elif return_value > buy:
                        return 'Buy'
                    elif return_value > hold:
                        return 'Hold'
                    elif return_value > sell:
                        return 'Sell'
                    else:
                        return 'Strong Sell'
                
                y = df_features['future_return'].apply(get_rating)
            else:
                y = df_features['future_return']
            
            # Remove any remaining NaN values
            valid_indices = X.dropna().index
            X_valid = X.loc[valid_indices]
            y_valid = y.loc[valid_indices]
            
            if len(X_valid) == 0:
                logger.warning(f"Skipping {ticker}: No valid data after cleaning")
                skipped_tickers.append(ticker)
                continue
            
            # Add to collection
            all_features.append(X_valid)
            all_targets.append(y_valid)
            processed_tickers.append(ticker)
            
            logger.info(f"Successfully processed {ticker}: {len(X_valid)} samples")
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            error_tickers.append(ticker)
    
    # Log processing summary
    logger.info("\nProcessing Summary:")
    logger.info(f"Successfully processed ({len(processed_tickers)}): {', '.join(processed_tickers)}")
    logger.info(f"Skipped ({len(skipped_tickers)}): {', '.join(skipped_tickers)}")
    logger.info(f"Errors ({len(error_tickers)}): {', '.join(error_tickers)}")
    
    if not all_features or not all_targets:
        logger.error("No valid data collected for training")
        return None, None
    
    # Combine data from all tickers
    X_combined = pd.concat(all_features, axis=0)
    y_combined = pd.concat(all_targets, axis=0)
    
    logger.info(f"Combined dataset: {X_combined.shape[0]} samples, {X_combined.shape[1]} features")
    
    # Shuffle the combined data to ensure random splits
    # Use the index to keep X and y aligned
    shuffle_idx = np.random.permutation(len(X_combined))
    X_combined = X_combined.iloc[shuffle_idx].reset_index(drop=True)
    y_combined = y_combined.iloc[shuffle_idx].reset_index(drop=True)
    
    # Log data types of all columns
    logger.info("\nFeature data types:")
    for col in X_combined.columns:
        logger.info(f"  {col}: {X_combined[col].dtype}")
        if X_combined[col].dtype == 'object':
            sample_values = X_combined[col].head()
            logger.info(f"    Sample values for {col}:")
            for val in sample_values:
                logger.info(f"      Value: {val}, Type: {type(val)}")
    
    # Perform cross-validation
    logger.info("\nPerforming cross-validation...")
    cv_results = predictor.cross_validate(X_combined, y_combined)
    
    # Train final model on full dataset
    logger.info("\nTraining final model on full dataset...")
    training_results = predictor.train(X_combined, y_combined)
    
    # Generate and save training summary
    summary = generate_training_summary(
        predictor=predictor,
        cv_results=cv_results,
        training_results=training_results,
        processed_tickers=processed_tickers,
        skipped_tickers=skipped_tickers,
        error_tickers=error_tickers
    )
    save_training_summary(summary)
    
    # Save the model
    predictor.save(model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Log metrics to MLflow
    run_id = log_mlflow_metrics(
        predictor=predictor,
        cv_results=cv_results,
        training_results=training_results,
        X_data=X_combined,
        processed_tickers=processed_tickers,
        skipped_tickers=skipped_tickers,
        error_tickers=error_tickers,
        model_path=model_path
    )
    
    logger.info(f"MLflow run ID: {run_id}")
    
    return predictor, cv_results

def main():
    """Main function to parse arguments and train model"""
    parser = argparse.ArgumentParser(description='Train stock prediction model using cross-validation')
    parser.add_argument('--tickers', type=str, nargs='+', help='List of ticker symbols')
    parser.add_argument('--model-path', type=str, help='Path to save the model')
    parser.add_argument('--period', type=str, help='Period to fetch data (e.g., 5y)')
    parser.add_argument('--interval', type=str, help='Data interval (e.g., 1d)')
    parser.add_argument('--forward-days', type=int, help='Days to look ahead for returns')
    parser.add_argument('--force-sample', action='store_true', help='Use sample data')
    parser.add_argument('--mode', type=str, choices=['regression', 'classification'], 
                        help='Prediction mode')
    parser.add_argument('-y', '--yes', action='store_true', help='Overwrite without asking')
    
    args = parser.parse_args()
    
    train_model(
        tickers=args.tickers,
        model_path=args.model_path,
        period=args.period,
        interval=args.interval,
        forward_days=args.forward_days,
        force_sample=args.force_sample,
        overwrite=args.yes,
        mode=args.mode
    )

if __name__ == '__main__':
    main() 