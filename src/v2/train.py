"""
Script for training the stock prediction model
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import pandas as pd

from src.v2.config import config
from src.v2.data_fetcher import DataFetcher
from src.v2.features import Features
from src.v2.predictor import Predictor
from src.v2.training_summary import (
    generate_training_summary,
    log_mlflow_metrics,
    save_training_summary,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/train.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constants from config
MIN_DATA_DAYS = config.get(
    "model.training.min_data_days", 60
)  # Minimum days for reliable training
MIN_FEATURE_DAYS = config.get(
    "model.training.min_feature_days", 30
)  # Minimum days after feature generation


def train_model(
    tickers=None,
    model_path=None,
    period=None,
    interval=None,
    forward_days=None,
    force_sample=False,
    overwrite=False,
    use_enhanced_features=True,
    use_risk_adjusted_target=True,
):
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
        use_enhanced_features (bool): Use enhanced features with risk metrics
        use_risk_adjusted_target (bool): Use risk-adjusted target (Sharpe ratio)

    Returns:
        tuple: (Predictor, dict) - Trained model and results including:
            - Cross-validation metrics
            - Feature importance stability
            - Final model performance
    """
    # Load configuration with defaults
    if tickers is None:
        tickers = config.get("model.training.default_tickers")

    if period is None:
        period = config.get("model.training.period", "5y")

    if interval is None:
        interval = config.get("model.training.interval", "1d")

    if forward_days is None:
        forward_days = config.get("model.training.forward_days", 90)

    if model_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/st_predictor_{timestamp}.pkl"

    # Create model path directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)

    # Check if model already exists
    if os.path.exists(model_path) and not overwrite:
        response = input(f"Model file {model_path} already exists. Overwrite? (y/n): ")
        if response.lower() != "y":
            logger.info("Training cancelled by user")
            return None, None

    # Initialize components
    fetcher = DataFetcher(cache_dir="cache")
    features = Features()

    if use_enhanced_features:
        logger.info("Using enhanced features with risk metrics")
    else:
        logger.info("Using standard features")

    predictor = Predictor()

    # Fetch market data for beta calculations if using enhanced features
    market_data = None
    if use_enhanced_features:
        try:
            logger.info("Fetching market data (S&P 500) for beta calculations")
            market_data = fetcher.fetch_market_data(
                "SPY", period=period, interval=interval, force_sample=force_sample
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch market data: {e}. Beta features will not be available."
            )

    # Process tickers
    all_features = []
    all_targets = []
    processed_tickers = []
    skipped_tickers = []
    error_tickers = []

    logger.info(f"Training model on {len(tickers)} tickers")
    logger.info(f"Looking ahead {forward_days} days for returns")

    for ticker in tickers:
        try:
            logger.info(f"Processing {ticker}...")

            # Fetch data
            df = fetcher.fetch_data(
                ticker, period=period, interval=interval, force_sample=force_sample
            )

            if df is None or len(df) < MIN_DATA_DAYS:
                logger.warning(f"Not enough data for {ticker}, skipping")
                skipped_tickers.append(ticker)
                continue

            # Calculate future returns for target
            future_return_col = f"future_return_{forward_days}d"
            df[future_return_col] = (
                df["Close"].pct_change(forward_days).shift(-forward_days)
            )

            # Generate features
            feature_df = features.generate(
                df, market_data, use_enhanced_features=use_enhanced_features
            )

            if feature_df is None:
                logger.warning(f"Failed to generate features for {ticker}, skipping")
                skipped_tickers.append(ticker)
                continue

            # Add future return column to feature_df
            feature_df[future_return_col] = df[future_return_col]

            # Drop rows with NaN values in features or target
            feature_df = feature_df.dropna(subset=[future_return_col])
            feature_df = feature_df.dropna()

            if len(feature_df) < MIN_FEATURE_DAYS:
                logger.warning(
                    f"Not enough data after feature generation for {ticker}, skipping"
                )
                skipped_tickers.append(ticker)
                continue

            # Prepare target variable
            if (
                use_risk_adjusted_target
                and use_enhanced_features
                and "target_sharpe_ratio" in feature_df.columns
            ):
                target_col = "target_sharpe_ratio"
                logger.info(f"Using risk-adjusted target (Sharpe ratio) for {ticker}")
            else:
                target_col = future_return_col
                logger.info(f"Using raw return as target for {ticker}")

            target = feature_df[target_col]

            # Drop target columns from features
            feature_df = feature_df.drop(
                columns=[
                    col
                    for col in feature_df.columns
                    if "future_" in col or col == "target_sharpe_ratio"
                ],
                errors="ignore",
            )

            # Add to training data
            all_features.append(feature_df)
            all_targets.append(target)
            processed_tickers.append(ticker)

            logger.info(f"Successfully processed {ticker} with {len(feature_df)} rows")

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            error_tickers.append(ticker)

    if not all_features:
        logger.error("No valid data to train on")
        return None, None

    # Combine all data
    X = pd.concat(all_features)
    y = pd.concat(all_targets)

    logger.info(
        f"Combined dataset: {len(X)} rows from {len(processed_tickers)} tickers"
    )

    # Perform cross-validation
    cv_results = predictor.cross_validate(X, y)

    # Train final model on all data
    train_results = predictor.train(X, y)

    # Save model
    predictor.save(model_path)
    logger.info(f"Model saved to {model_path}")

    # Generate training summary
    summary = generate_training_summary(
        predictor=predictor,
        cv_results=cv_results,
        training_results=train_results,
        processed_tickers=processed_tickers,
        skipped_tickers=skipped_tickers,
        error_tickers=error_tickers,
    )

    # Save summary
    summary_path = model_path.replace(".pkl", "_summary.md")
    save_training_summary(summary, summary_path)

    # Log metrics to MLflow
    log_mlflow_metrics(
        predictor=predictor,
        cv_results=cv_results,
        training_results=train_results,
        X_data=X,
        processed_tickers=processed_tickers,
        skipped_tickers=skipped_tickers,
        error_tickers=error_tickers,
        model_path=model_path,
    )

    return predictor, summary


def main():
    """Main function for command-line execution"""
    parser = argparse.ArgumentParser(description="Train stock prediction model")
    parser.add_argument("--tickers", type=str, help="Comma-separated list of tickers")
    parser.add_argument("--model-path", type=str, help="Path to save model")
    parser.add_argument("--period", type=str, help="Historical data period (e.g., 5y)")
    parser.add_argument("--interval", type=str, help="Data interval (e.g., 1d)")
    parser.add_argument(
        "--forward-days", type=int, help="Days to look ahead for returns"
    )
    parser.add_argument("--force-sample", action="store_true", help="Use sample data")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing model"
    )
    parser.add_argument(
        "--enhanced-features",
        action="store_true",
        help="Use enhanced features with risk metrics",
    )
    parser.add_argument(
        "--risk-adjusted-target",
        action="store_true",
        help="Use risk-adjusted target (Sharpe ratio)",
    )

    args = parser.parse_args()

    # Process tickers
    tickers = None
    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",")]

    # Train model
    predictor, summary = train_model(
        tickers=tickers,
        model_path=args.model_path,
        period=args.period,
        interval=args.interval,
        forward_days=args.forward_days,
        force_sample=args.force_sample,
        overwrite=args.overwrite,
        use_enhanced_features=args.enhanced_features,
        use_risk_adjusted_target=args.risk_adjusted_target,
    )

    if predictor is None:
        sys.exit(1)

    print("\nTraining complete!")
    print(f"Model saved to: {args.model_path or 'default path'}")

    # Print feature importance
    if predictor.feature_importance is not None:
        print("\nTop 10 Feature Importance:")
        for feature, importance in predictor.feature_importance[:10]:
            print(f"{feature}: {importance:.4f}")


if __name__ == "__main__":
    main()
