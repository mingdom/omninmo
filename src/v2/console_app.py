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
from src.v2.features import Features
from src.v2.predictor import Predictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
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
        """
        if model_path is None:
            # Find the latest model file
            model_dir = "models"
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
                logger.warning(f"Created models directory: {model_dir}")
                return False

            model_files = [
                f
                for f in os.listdir(model_dir)
                if f.startswith("st_predictor_") and f.endswith(".pkl")
            ]

            if not model_files:
                logger.error("No model files found in the models directory")
                return False

            # Sort by modification time (newest first)
            model_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(model_dir, x)), reverse=True
            )
            model_path = os.path.join(model_dir, model_files[0])

        # Load the model
        self.model_path = model_path
        self.predictor = Predictor.load(model_path)

        if self.predictor is None:
            logger.error(f"Failed to load model from {model_path}")
            return False

        logger.info(f"Loaded model from {model_path}")
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
        """
        if self.predictor is None:
            logger.error("No model loaded. Call load_model() first")
            return None

        # Use watchlist if no tickers provided
        if tickers is None:
            tickers = config.get("app.watchlist.default")

        if not tickers:
            logger.error("No tickers specified and no watchlist found in config")
            return None

        # Ensure tickers are unique and sorted alphabetically
        tickers = sorted(
            set(tickers)
        )  # Convert to set for uniqueness and sort alphabetically

        logger.info(f"Running predictions for {len(tickers)} unique tickers")

        # Prepare results table
        results = []

        # Process each ticker
        for ticker in tickers:
            try:
                # Fetch data
                df = self.fetcher.fetch_data(ticker, force_sample=use_sample_data)

                if df is None or len(df) < MIN_DATA_DAYS:
                    logger.warning(f"Insufficient data for {ticker}")
                    continue

                # Generate features
                df_features = self.features.generate(df)

                if df_features is None:
                    logger.warning(f"Failed to generate features for {ticker}")
                    continue

                # Get latest price
                latest_price = df["Close"].iloc[-1]
                latest_date = df.index[-1].strftime("%Y-%m-%d")

                # Make prediction with the latest data
                latest_features = df_features.iloc[[-1]]
                prediction = self.predictor.predict(latest_features)

                if prediction is None:
                    logger.warning(f"Failed to make prediction for {ticker}")
                    continue

                predicted_return, score, rating = prediction

                # Add to results
                results.append(
                    {
                        "Ticker": ticker,
                        "Price": latest_price,
                        "Date": latest_date,
                        "Predicted Return": f"{predicted_return:.2%}",
                        "Score": f"{score:.2f}",
                        "Rating": rating,
                    }
                )

            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")

        if not results:
            logger.error("No prediction results generated")
            return None

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Sort by score
        results_df.sort_values("Score", ascending=False, inplace=True)

        # Output results based on format
        if output_format == "table":
            print("\n" + tabulate(results_df, headers="keys", tablefmt="fancy_grid"))
        elif output_format == "csv":
            print(results_df.to_csv(index=False))
        elif output_format == "json":
            print(results_df.to_json(orient="records", indent=2))

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
        "--tickers", type=str, nargs="+", help="List of tickers to predict"
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
        logger.info("No model available. Training a sample model...")
        from src.v2.train import train_model

        model = train_model(force_sample=True)
        if model is None:
            logger.error("Failed to train a sample model")
            sys.exit(1)
        app.predictor = model

    # Run predictions
    app.run_predictions(args.tickers, args.sample, args.format)


if __name__ == "__main__":
    main()
