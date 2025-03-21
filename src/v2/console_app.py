"""
Console application for stock predictions
"""

import argparse
import logging
import os
import sys

import pandas as pd
from tabulate import tabulate

from src.v2.config import config
from src.v2.data_fetcher import DataFetcher
from src.v2.exceptions import (
    ConfigurationError,
    FeatureGenerationError,
    InsufficientDataError,
    ModelNotLoadedError,
)
from src.v2.features import Features
from src.v2.predictor import Predictor

# Setup logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/console_app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constants with defaults from config
RECENT_DAYS_THRESHOLD = config.get("data.max_age_days", 30)
MIN_DATA_DAYS = config.get("model.training.min_data_days", 30)


class ConsoleApp:
    """Console application for stock predictions"""

    def __init__(self):
        """Initialize the console app"""
        self.fetcher = DataFetcher()
        self.features = Features()
        self.predictor = None
        self.model_path = None

    def load_model(self, model_path=None):
        """
        Load the prediction model

        Args:
            model_path (str): Path to the model file, or None to use latest

        Returns:
            bool: True if model loaded successfully

        Raises:
            ConfigurationError: If no model file is found
        """
        if model_path is None:
            # Find the latest model file
            model_dir = "models"
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
                logger.debug(f"Created models directory: {model_dir}")
                raise ConfigurationError(
                    "No models directory found. Created empty directory."
                )

            model_files = [
                f
                for f in os.listdir(model_dir)
                if f.startswith("st_predictor_") and f.endswith(".pkl")
            ]

            if not model_files:
                raise ConfigurationError("No model files found in the models directory")

            # Sort by modification time (newest first)
            model_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(model_dir, x)), reverse=True
            )
            model_path = os.path.join(model_dir, model_files[0])

        # Load the model
        self.model_path = model_path
        self.predictor = Predictor.load(model_path)

        if self.predictor is None:
            raise ConfigurationError(f"Failed to load model from {model_path}")

        logger.debug(f"Model loaded successfully from {model_path}")
        return True

    def run_predictions(
        self, tickers=None, use_sample_data=False, output_format="table"
    ):
        """
        Run predictions for a list of tickers

        Args:
            tickers (list): List of ticker symbols, or None to use watchlist
            use_sample_data (bool): Whether to use sample data instead of API
            output_format (str): Output format ('table', 'csv', or 'json')

        Returns:
            pandas.DataFrame: Prediction results

        Raises:
            ModelNotLoadedError: If model is not loaded
            ConfigurationError: If no tickers specified
            InsufficientDataError: If not enough data for prediction
            FeatureGenerationError: If feature generation fails
        """
        if self.predictor is None:
            raise ModelNotLoadedError("No model loaded. Call load_model() first")

        # Use watchlist if no tickers provided
        if tickers is None:
            tickers = config.get("app.watchlist.default")

        if not tickers:
            raise ConfigurationError(
                "No tickers specified and no watchlist found in config"
            )

        # Ensure tickers are unique and sorted alphabetically
        tickers = sorted(set(tickers))

        # Display model configuration
        forward_days = config.get("model.training.forward_days", 30)
        norm_method = config.get("model.normalization.method", "tanh")
        norm_k = config.get(f"model.normalization.{norm_method}_k", 10)

        print("\nModel Configuration:")
        print(f"- Prediction horizon: {forward_days} days")
        print(f"- Normalization: {norm_method} (k={norm_k})")
        print("- Score interpretation:")
        print("  • > 0.5: Positive outlook")
        print("  • = 0.5: Neutral")
        print("  • < 0.5: Negative outlook")
        print()

        logger.debug(f"Running predictions for {len(tickers)} tickers")

        # Prepare results table
        results = []
        errors = []

        # Process each ticker
        for ticker in tickers:
            try:
                logger.debug(f"Processing {ticker}")

                # Fetch data
                df = self.fetcher.fetch_data(ticker, force_sample=use_sample_data)

                # Check data sufficiency
                if df is None or len(df) < MIN_DATA_DAYS:
                    raise InsufficientDataError(
                        f"Insufficient data for {ticker}. "
                        f"Required: {MIN_DATA_DAYS} days, "
                        f"Got: {len(df) if df is not None else 0} days"
                    )

                # Generate features
                df_features = self.features.generate(df)

                if df_features is None:
                    raise FeatureGenerationError(
                        f"Failed to generate features for {ticker}"
                    )

                # Get latest price
                latest_price = df["Close"].iloc[-1]
                latest_date = df.index[-1].strftime("%Y-%m-%d")

                # Make prediction with the latest data
                latest_features = df_features.iloc[[-1]]
                prediction = self.predictor.predict(latest_features)

                if prediction is None:
                    raise FeatureGenerationError(
                        f"Failed to make prediction for {ticker}"
                    )

                predicted_return, score = prediction

                # Add to results
                results.append(
                    {
                        "Ticker": ticker,
                        "Price": latest_price,
                        "Date": latest_date,
                        "Return": predicted_return,  # Store raw value for sorting
                        "Predicted Return": f"{predicted_return:.2%}",  # Formatted for display
                        "Score": f"{score:.2f}",
                    }
                )

            except (InsufficientDataError, FeatureGenerationError) as e:
                logger.warning(f"Skipping {ticker}: {e!s}")
                errors.append({"ticker": ticker, "error": str(e)})
            except Exception as e:
                logger.error(f"Unexpected error processing {ticker}: {e!s}")
                errors.append({"ticker": ticker, "error": str(e)})

        if not results:
            raise ConfigurationError(
                "No valid predictions generated. "
                f"Errors occurred for {len(errors)} tickers."
            )

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Sort by predicted return (descending)
        results_df.sort_values("Return", ascending=False, inplace=True)

        # Drop the raw return column used for sorting
        results_df = results_df.drop("Return", axis=1)

        # Output results based on format
        if output_format == "table":
            print("\n" + tabulate(results_df, headers="keys", tablefmt="fancy_grid"))

            # Print errors if any
            if errors:
                print("\nErrors occurred:")
                for error in errors:
                    print(f"- {error['ticker']}: {error['error']}")
        elif output_format == "csv":
            print(results_df.to_csv(index=False))
        elif output_format == "json":
            print(results_df.to_json(orient="records", indent=2))

        # Log summary
        logger.debug(
            f"Generated predictions for {len(results)} tickers "
            f"(skipped {len(errors)} with errors)"
        )

        return results_df

    def _check_recent_data(self, ticker):
        """Check if we have recent data for this ticker."""
        try:
            data = self.fetcher.get_data(ticker)
            if data is None or len(data) == 0:
                return False

            last_date = pd.to_datetime(data.index[-1])
            days_old = (pd.Timestamp.now() - last_date).days

            if days_old > RECENT_DAYS_THRESHOLD:
                logger.warning(f"Data for {ticker} is {days_old} days old")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking data for {ticker}: {e}")
            return False


def main():
    """Main function for console app"""
    parser = argparse.ArgumentParser(description="Stock Prediction Console App")
    parser.add_argument(
        "--tickers",
        type=str,
        nargs="+",
        help="List of tickers to predict (space or comma-separated)",
    )
    parser.add_argument(
        "--model", type=str, help="Path to model file (uses latest if not specified)"
    )
    parser.add_argument(
        "--sample", action="store_true", help="Use sample data instead of API"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (table, csv, or json)",
    )

    args = parser.parse_args()

    app = ConsoleApp()

    # Load model
    if not app.load_model(args.model):
        # If no model is available, train a sample model
        logger.debug("No model available. Training a sample model...")
        from src.v2.train import train_model

        model = train_model(force_sample=True)
        if model is None:
            logger.error("Failed to train a sample model")
            sys.exit(1)
        app.predictor = model

    # Handle comma-separated tickers if provided
    if args.tickers:
        # Split any comma-separated tickers and flatten the list
        tickers = []
        for ticker_arg in args.tickers:
            tickers.extend(ticker_arg.split(","))
        # Remove any empty strings and strip whitespace
        tickers = [t.strip() for t in tickers if t.strip()]
    else:
        tickers = None

    # Run predictions
    app.run_predictions(tickers, args.sample, args.format)


if __name__ == "__main__":
    main()
