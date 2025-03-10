"""
Model training utilities for omninmo.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import datetime
import logging
import pickle
import sys
import logging.handlers
from pathlib import Path
from tqdm import tqdm
import joblib
import yaml

# Setup logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set default level to DEBUG

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Setup file handler
file_handler = logging.handlers.RotatingFileHandler(
    'logs/trainer.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.fmp_data_fetcher import FMPDataFetcher
from src.utils.feature_engineer import FeatureEngineer
from src.models.xgboost_predictor import XGBoostRatingPredictor

# Load tickers from config file
def load_default_tickers():
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            return config['model']['training']['default_tickers']
    except Exception as e:
        logger.error(f"Error loading tickers from config: {e}")
        # Fallback to a minimal set if config loading fails
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

# Default tickers for training
DEFAULT_TICKERS = load_default_tickers()

# Rating map (0-4 instead of -2 to 2)
RATING_MAP = {
    0: "Strong Sell",
    1: "Sell",
    2: "Hold",
    3: "Buy",
    4: "Strong Buy"
}

REVERSE_RATING_MAP = {v: k for k, v in RATING_MAP.items()}

class Trainer:
    def __init__(self, use_sample_data=False):
        """
        Initialize the Trainer class.
        
        Args:
            use_sample_data (bool): Whether to use sample data or not.
        """
        self.use_sample_data = use_sample_data
        self.data_fetcher = FMPDataFetcher()
        self.feature_engineer = FeatureEngineer()
        
    def _create_target_variable(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create the target variable based on future returns.
        
        Args:
            data (pd.DataFrame): The input data with future returns.
            
        Returns:
            pd.DataFrame: The data with the target variable.
        """
        # Calculate return thresholds for classification
        data_with_returns = data.copy()
        
        # Using 0-4 rating scale (instead of -2 to 2)
        # 0: Strong Sell, 1: Sell, 2: Hold, 3: Buy, 4: Strong Buy
        data_with_returns['target'] = 2  # Default to Hold (2)
        
        # Strong Sell: < -5%
        data_with_returns.loc[data_with_returns['future_return'] < -0.05, 'target'] = 0
        
        # Sell: -5% to -1%
        data_with_returns.loc[(data_with_returns['future_return'] >= -0.05) & 
                             (data_with_returns['future_return'] < -0.01), 'target'] = 1
        
        # Buy: 1% to 5%
        data_with_returns.loc[(data_with_returns['future_return'] > 0.01) & 
                             (data_with_returns['future_return'] <= 0.05), 'target'] = 3
        
        # Strong Buy: > 5%
        data_with_returns.loc[data_with_returns['future_return'] > 0.05, 'target'] = 4
        
        logger.debug(f"Target value counts: {data_with_returns['target'].value_counts()}")
        
        return data_with_returns
    
    def prepare_training_data(self, tickers: List[str], 
                             start_date: datetime.datetime, 
                             end_date: datetime.datetime) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare the training data for the model.
        
        Args:
            tickers (List[str]): List of tickers to fetch data for.
            start_date (datetime.datetime): Start date for the data.
            end_date (datetime.datetime): End date for the data.
            
        Returns:
            Tuple[pd.DataFrame, pd.Series]: The features and target variable.
        """
        all_features = []
        all_targets = []
        
        logger.info(f"Preparing training data for {len(tickers)} tickers")
        
        for ticker in tickers:
            logger.debug(f"Fetching data for {ticker}")
            
            # Fetch data for the ticker
            if self.use_sample_data:
                data = self.data_fetcher.get_sample_data(ticker)
            else:
                data = self.data_fetcher.get_data(ticker, start_date, end_date)
            
            if data is None or data.empty:
                # Fail fast - if we can't get data for a ticker, something is wrong
                error_msg = f"No data fetched for {ticker}, aborting training"
                logger.error(error_msg)
                raise ValueError(error_msg)
                    
            logger.debug(f"Fetched {len(data)} rows for {ticker}")
            logger.debug(f"NaN count in data: {data.isna().sum().sum()}")
            logger.debug(f"Data columns: {data.columns.tolist()}")
            
            # First add return features (needs Close price)
            data_with_returns = self.feature_engineer.add_return_features(data)
            if data_with_returns is None:
                # Fail fast - if we can't add return features, something is wrong
                error_msg = f"Failed to add return features for {ticker}, aborting training"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.debug(f"Added return features, shape: {data_with_returns.shape}")
            
            # Then add technical indicators
            data_with_indicators = self.feature_engineer.add_indicators(data_with_returns)
            if data_with_indicators is None:
                # Fail fast - if we can't add indicators, something is wrong
                error_msg = f"Failed to add indicators for {ticker}, aborting training"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.debug(f"Added indicators, shape: {data_with_indicators.shape}")
            
            # Create target variable
            data_with_target = self._create_target_variable(data_with_returns)
            
            # Check for NaN values
            if data_with_target.isna().any().any():
                logger.debug(f"NaN values found in {ticker} data: {data_with_target.isna().sum().sum()}")
                # Drop rows with NaN values
                valid_rows = data_with_target.dropna()
                logger.debug(f"Rows after NaN check: {len(valid_rows)}")
                
                if len(valid_rows) == 0:
                    # Fail fast - if we have no valid rows after dropping NaNs, something is wrong
                    error_msg = f"No valid rows for {ticker} after dropping NaN values, aborting training"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                valid_rows = data_with_target
            
            # Combine the indicators with the target data
            combined_data = pd.concat([data_with_indicators, valid_rows[['target']]], axis=1)
            logger.debug(f"Combined data shape: {combined_data.shape}")
            
            # Drop any rows with NaN values after combining
            combined_data = combined_data.dropna()
            if len(combined_data) == 0:
                error_msg = f"No valid rows for {ticker} after combining indicators and target, aborting training"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Select features (all columns except 'target')
            features = combined_data.drop(['target'], axis=1)
            
            # Get target
            target = combined_data['target']
            
            logger.debug(f"Features shape: {features.shape}, Target shape: {target.shape}")
            logger.debug(f"Feature columns: {features.columns.tolist()}")
            
            all_features.append(features)
            all_targets.append(target)
            
            logger.debug(f"Successfully processed {ticker}: {len(features)} samples")
                
        if len(all_features) > 0 and len(all_targets) > 0:
            # Concatenate all features and targets
            combined_features = pd.concat(all_features, ignore_index=True)
            combined_target = pd.concat(all_targets, ignore_index=True)
            
            # Reset index to ensure alignment
            combined_features = combined_features.reset_index(drop=True)
            combined_target = combined_target.reset_index(drop=True)
            
            logger.info(f"Final dataset: {len(combined_features)} samples, {len(combined_features.columns)} features")
            logger.info(f"Target distribution: {combined_target.value_counts().to_dict()}")
            
            return combined_features, combined_target
        else:
            error_msg = "No valid data to train on"
            logger.error(error_msg)
            raise ValueError(error_msg)

def train_model(tickers, model_path, period="5y", interval="1d", forward_days=20, force_sample=False):
    """
    Train a model on historical data for a set of tickers.

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
    logger.info("Using XGBoost model for training")

    # Collect data and features for all tickers
    all_features = []
    all_targets = []

    logger.info(f"Training model on {len(tickers)} tickers...")
    for ticker in tqdm(tickers):
        try:
            # Fetch historical data
            df = fetcher.fetch_data(ticker, period=period, interval=interval, force_sample=force_sample)

            if df is None or len(df) < 252:  # Require at least 1 year of data
                logger.warning(f"Skipping {ticker}: Insufficient data")
                continue

            # Log information about the fetched data
            logger.debug(f"Fetched data for {ticker}: {len(df)} rows, index type: {type(df.index)}")
            logger.debug(f"Index sample: {list(df.index[:5])}")

            # Add technical indicators
            df_with_indicators = feature_engineer.add_technical_indicators(df)

            if df_with_indicators is None or len(df_with_indicators) < 100:
                logger.warning(f"Skipping {ticker}: Insufficient data after adding indicators")
                continue
                
            # Log information about the data after adding indicators
            logger.debug(f"Data with indicators for {ticker}: {len(df_with_indicators)} rows")

            # Create a separate DataFrame from the original to calculate returns
            df_returns = df.copy()
            returns = df_returns['Close'].pct_change(forward_days)
            
            # Log information about returns
            logger.debug(f"Returns for {ticker}: {len(returns)} rows, NaN count: {returns.isna().sum()}")
            
            # Create target variable with values 0-4 (instead of -2 to 2)
            target = pd.Series(index=returns.index, dtype='int')
            target[returns <= -0.1] = 0  # Strong Sell (was -2)
            target[(returns > -0.1) & (returns <= -0.03)] = 1  # Sell (was -1)
            target[(returns > -0.03) & (returns < 0.03)] = 2  # Hold (was 0)
            target[(returns >= 0.03) & (returns < 0.1)] = 3  # Buy (was 1)
            target[returns >= 0.1] = 4  # Strong Buy (was 2)
            
            # Log information about the target
            logger.debug(f"Target for {ticker}: {len(target)} rows, NaN count: {target.isna().sum()}")
            logger.debug(f"Target value counts: {target.value_counts().to_dict()}")

            # Log index information
            logger.debug(f"DataFrame index: {df_with_indicators.index.name}, Target index: {target.index.name}")
            
            # Find common indices between features and target
            common_indices = df_with_indicators.index.intersection(target.index)
            logger.debug(f"Common indices: {len(common_indices)}")
            
            # Use only common indices
            df_with_indicators = df_with_indicators.loc[common_indices]
            target = target.loc[common_indices]
            
            # Remove rows with any NaN values
            valid_mask = ~(df_with_indicators.isna().any(axis=1) | target.isna())
            logger.debug(f"Valid rows after NaN check: {valid_mask.sum()}")
            
            if valid_mask.sum() == 0:
                logger.warning(f"Skipping {ticker}: No valid data points after removing NaNs")
                continue
                
            # Select only rows that have both valid features and target
            filtered_features = df_with_indicators.loc[valid_mask].copy()
            filtered_target = target.loc[valid_mask].copy()
            
            logger.debug(f"Final filtered data for {ticker}: features={len(filtered_features)}, target={len(filtered_target)}")
            
            # Reset indices to ensure alignment
            filtered_features.reset_index(drop=True, inplace=True)
            filtered_target.reset_index(drop=True, inplace=True)

            # Append to collection
            all_features.append(filtered_features)
            all_targets.append(filtered_target)
            logger.debug(f"Successfully processed {ticker}")

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}", exc_info=True)

    if not all_features or not all_targets:
        error_msg = "No valid data collected for training"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Combine data from all tickers
    X_combined = pd.concat(all_features, axis=0, ignore_index=True)
    y_combined = pd.concat(all_targets, axis=0, ignore_index=True)
    
    # Double-check that lengths match
    if len(X_combined) != len(y_combined):
        error_msg = f"Feature and target lengths don't match: {len(X_combined)} vs {len(y_combined)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Final dataset: {len(X_combined)} samples, {X_combined.shape[1]} features")
    logger.info(f"Target distribution: {y_combined.value_counts().to_dict()}")
    
    # Train the model
    training_results = predictor.train(X_combined, y_combined)
    if training_results:
        logger.info(f"Training accuracy: {training_results['accuracy']:.4f}")
    
    # Save the model
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(predictor, f)
    
    return predictor

def train_on_default_tickers(model_path='models/stock_predictor.pkl', period='2y', tickers=None, force_sample=False):
    """
    Train the stock rating predictor model on default tickers.
    
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
        model = train_model(tickers, model_path, period=period, force_sample=force_sample)
        logger.info(f"XGBoost model trained and saved to {model_path}")
        return model
    except Exception as e:
        logger.error(f"Error during XGBoost model training: {e}", exc_info=True)
        return None

def load_model(model_path='models/stock_predictor.pkl'):
    """
    Load a trained model from disk.
    
    Args:
        model_path (str): Path to the saved model
    
    Returns:
        XGBoostRatingPredictor: Loaded model instance
    """
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")
        return model
    except FileNotFoundError:
        logger.error(f"Model file not found at {model_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        return None

def evaluate_model(model, test_tickers, period="1y", interval="1d"):
    """
    Evaluate a trained model on a set of test tickers.

    Args:
        model (XGBoostRatingPredictor): Trained model
        test_tickers (list): List of ticker symbols for testing
        period (str): Period to fetch data for (default: '1y')
        interval (str): Data interval (default: '1d')

    Returns:
        pd.DataFrame: DataFrame with evaluation results
    """
    # Initialize components
    fetcher = FMPDataFetcher(cache_dir="cache")
    feature_engineer = FeatureEngineer()

    # Collect evaluation results
    results = []

    logger.info(f"Evaluating model on {len(test_tickers)} tickers...")
    for ticker in tqdm(test_tickers):
        try:
            # Fetch historical data
            df = fetcher.fetch_data(ticker, period=period, interval=interval)

            if df is None or len(df) < 60:  # Require at least 60 days of data
                logger.warning(f"Skipping {ticker}: Insufficient data")
                continue

            # Add technical indicators
            df_with_indicators = feature_engineer.add_technical_indicators(df)

            if df_with_indicators is None or len(df_with_indicators) < 30:
                logger.warning(f"Skipping {ticker}: Insufficient data after adding indicators")
                continue

            # Remove NaN values
            df_with_indicators = df_with_indicators.dropna()
            
            if len(df_with_indicators) == 0:
                logger.warning(f"Skipping {ticker}: No valid data after removing NaNs")
                continue

            # Get the most recent data point for prediction
            latest_features = df_with_indicators.iloc[-1:].copy()
            
            # Make prediction
            rating_numeric, confidence = model.predict(latest_features)
            
            # Convert numeric rating to string label
            rating = RATING_MAP.get(rating_numeric, 'Unknown')
            logger.debug(f"{ticker} prediction: {rating} (numeric: {rating_numeric}, confidence: {confidence:.4f})")

            # Calculate future returns (if available)
            future_return_20d = None
            if len(df) > 20:
                future_return_20d = df["Close"].iloc[-1] / df["Close"].iloc[-21] - 1 if len(df) >= 21 else None
                logger.debug(f"{ticker} future return (20d): {future_return_20d:.4f}" if future_return_20d is not None else f"{ticker} future return: None")

            # Add to results
            results.append({
                "ticker": ticker,
                "rating": rating,
                "rating_numeric": rating_numeric,
                "confidence": confidence,
                "future_return_20d": future_return_20d,
                "current_price": df["Close"].iloc[-1] if not df.empty else None,
                "date": df.index[-1] if not df.empty else None
            })

        except Exception as e:
            logger.error(f"Error evaluating {ticker}: {e}", exc_info=True)

    # Convert to DataFrame
    if results:
        results_df = pd.DataFrame(results)
        
        # Add accuracy metrics if future returns are available
        if 'future_return_20d' in results_df.columns and not results_df['future_return_20d'].isna().all():
            
            def check_prediction(row):
                if row['future_return_20d'] is None:
                    return None
                
                rating_num = row['rating_numeric']
                future_return = row['future_return_20d']
                
                if rating_num == 4 and future_return > 0.1:  # Strong Buy (was 2)
                    return True
                elif rating_num == 3 and future_return > 0.03:  # Buy (was 1)
                    return True
                elif rating_num == 2 and abs(future_return) <= 0.03:  # Hold (was 0)
                    return True
                elif rating_num == 1 and future_return < -0.03:  # Sell (was -1)
                    return True
                elif rating_num == 0 and future_return < -0.1:  # Strong Sell (was -2)
                    return True
                else:
                    return False
            
            results_df['prediction_correct'] = results_df.apply(check_prediction, axis=1)
            accuracy = results_df['prediction_correct'].mean()
            logger.info(f"Model accuracy on test set: {accuracy:.4f}")
        
        return results_df
    else:
        logger.warning("No evaluation results generated")
        return pd.DataFrame()
