"""
Model training utilities for omninmo.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
import joblib
import pickle
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default tickers for training
DEFAULT_TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 
    'TSLA', 'NVDA', 'JPM', 'V', 'JNJ',
    'WMT', 'PG', 'DIS', 'NFLX', 'INTC'
]

# Import necessary modules
try:
    from src.data.stock_data_fetcher import StockDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.models.stock_rating_predictor import StockRatingPredictor
except ImportError:
    logger.warning("Attempting relative imports...")
    try:
        # Try relative imports if absolute imports fail
        from ..data.stock_data_fetcher import StockDataFetcher
        from ..utils.feature_engineer import FeatureEngineer
        from ..models.stock_rating_predictor import StockRatingPredictor
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        raise

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
        StockRatingPredictor: Trained model
    """
    # Initialize components
    fetcher = StockDataFetcher(cache_dir="cache")
    feature_engineer = FeatureEngineer()
    predictor = StockRatingPredictor()

    # Collect data and features for all tickers
    all_features = []
    all_targets = []

    print(f"Training model on {len(tickers)} tickers...")
    for ticker in tqdm(tickers):
        try:
            # Fetch historical data
            df = fetcher.fetch_data(ticker, period=period, interval=interval, force_sample=force_sample)

            if df is None or len(df) < 252:  # Require at least 1 year of data
                print(f"Skipping {ticker}: Insufficient data")
                continue

            # Add technical indicators
            df_with_indicators = feature_engineer.calculate_indicators(df)

            if df_with_indicators is None or len(df_with_indicators) < 100:
                print(f"Skipping {ticker}: Insufficient data after adding indicators")
                continue

            # Prepare target variable
            # For demonstration, we'll use a simple rule-based approach
            returns = df['Close'].pct_change(forward_days)
            target = pd.cut(returns, 
                           bins=[-float('inf'), -0.1, -0.03, 0.03, 0.1, float('inf')],
                           labels=['Strong Sell', 'Sell', 'Hold', 'Buy', 'Strong Buy'])

            # Remove NaN values
            valid_idx = ~(df_with_indicators.isna().any(axis=1) | target.isna())
            
            if valid_idx.sum() == 0:
                print(f"Skipping {ticker}: No valid data points after removing NaNs")
                continue
                
            filtered_features = df_with_indicators[valid_idx]
            filtered_target = target[valid_idx]

            # Append to collection
            all_features.append(filtered_features)
            all_targets.append(filtered_target)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    if not all_features or not all_targets:
        raise ValueError("No valid data collected for training")

    # Combine data from all tickers
    X_combined = pd.concat(all_features, axis=0)
    y_combined = pd.concat(all_targets, axis=0)
    
    # Train the model
    predictor.train(X_combined, y_combined)
    
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
        StockRatingPredictor: Trained model instance
    """
    logger.info("Starting model training on default tickers")
    
    # Use default tickers if none provided
    if tickers is None:
        tickers = DEFAULT_TICKERS
    
    # Create directory for model if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
    
    try:
        # Call the main training function
        model = train_model(tickers, model_path, period=period, force_sample=force_sample)
        logger.info(f"Model trained and saved to {model_path}")
        return model
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        return None

def load_model(model_path='models/stock_predictor.pkl'):
    """
    Load a trained model from disk.
    
    Args:
        model_path (str): Path to the saved model
    
    Returns:
        StockRatingPredictor: Loaded model instance
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
        logger.error(f"Error loading model: {e}")
        return None

def evaluate_model(model, test_tickers, period="1y", interval="1d"):
    """
    Evaluate a trained model on a set of test tickers.

    Args:
        model (StockRatingPredictor): Trained model
        test_tickers (list): List of ticker symbols for testing
        period (str): Period to fetch data for (default: '1y')
        interval (str): Data interval (default: '1d')

    Returns:
        pd.DataFrame: DataFrame with evaluation results
    """
    # Initialize components
    fetcher = StockDataFetcher()
    feature_engineer = FeatureEngineer()

    # Collect evaluation results
    results = []

    print(f"Evaluating model on {len(test_tickers)} tickers...")
    for ticker in tqdm(test_tickers):
        try:
            # Fetch historical data
            df = fetcher.fetch_stock_data(ticker, period=period, interval=interval)

            if df is None or len(df) < 60:  # Require at least 60 days of data
                print(f"Skipping {ticker}: Insufficient data")
                continue

            # Add technical indicators
            df_with_indicators = feature_engineer.add_technical_indicators(df)

            if df_with_indicators is None or len(df_with_indicators) < 30:
                print(f"Skipping {ticker}: Insufficient data after adding indicators")
                continue

            # Prepare features
            X, _ = feature_engineer.prepare_features(df_with_indicators)

            if X is None or len(X) == 0:
                print(f"Skipping {ticker}: No features generated")
                continue

            # Make predictions
            ratings = model.predict(X)

            # Get the most recent rating
            latest_rating = ratings[-1] if ratings else "Unknown"

            # Calculate future returns (if available)
            future_return_20d = None
            if len(df) > 20:
                future_return_20d = df["Close"].iloc[-1] / df["Close"].iloc[-21] - 1

            # Add to results
            results.append(
                {
                    "ticker": ticker,
                    "rating": latest_rating,
                    "current_price": df["Close"].iloc[-1],
                    "future_return_20d": future_return_20d,
                    "prediction_date": df.index[-1],
                }
            )

        except Exception as e:
            print(f"Error evaluating {ticker}: {e}")

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Calculate accuracy metrics if future returns are available
    if (
        "future_return_20d" in results_df.columns
        and not results_df["future_return_20d"].isna().all()
    ):
        # Define expected returns for each rating
        expected_returns = {
            "Strong Buy": 0.05,
            "Buy": 0.02,
            "Hold": 0.0,
            "Sell": -0.02,
            "Strong Sell": -0.05,
        }

        # Calculate if prediction was correct
        def check_prediction(row):
            if pd.isna(row["future_return_20d"]):
                return None

            rating = row["rating"]
            actual_return = row["future_return_20d"]

            if rating in expected_returns:
                expected_return = expected_returns[rating]

                # For Buy ratings, correct if return is positive
                if rating in ["Strong Buy", "Buy"] and actual_return > 0:
                    return True
                # For Sell ratings, correct if return is negative
                elif rating in ["Strong Sell", "Sell"] and actual_return < 0:
                    return True
                # For Hold ratings, correct if return is close to zero
                elif rating == "Hold" and abs(actual_return) < 0.02:
                    return True
                else:
                    return False
            else:
                return None

        results_df["prediction_correct"] = results_df.apply(check_prediction, axis=1)

        # Calculate accuracy
        accuracy = results_df["prediction_correct"].mean()
        print(f"Model accuracy: {accuracy:.2%}")

    return results_df
