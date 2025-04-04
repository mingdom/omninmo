"""
Console application for stock predictions
"""

import argparse
import json
import logging
import os
import sys

import pandas as pd

from src.fmp import DataFetcher
from src.v2.config import config
from src.v2.exceptions import (
    ConfigurationError,
    FeatureGenerationError,
    InsufficientDataError,
)
from src.v2.features import Features
from src.v2.predictor import Predictor

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
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

    def run_predictions(self, tickers=None, output_format="table"):
        """
        Run predictions for given tickers

        Args:
            tickers (list): List of tickers to predict (uses default if None)
            output_format (str): Output format ('table', 'csv', or 'json')

        Returns:
            str: Formatted prediction results
        """
        # Load default tickers if none provided
        if tickers is None:
            logger.debug("No tickers provided, attempting to load defaults")
            default_tickers = config.get("app.watchlist.default")
            logger.debug(f"Loaded default tickers: {default_tickers}")
            tickers = default_tickers

        # Validate tickers
        if not tickers:
            raise ValueError("No tickers provided and no defaults configured")

        # Clean and validate tickers
        tickers = [t.strip().upper() for t in tickers if t.strip()]
        if not tickers:
            raise ValueError("No valid tickers provided")

        # Initialize results list
        results = []

        # Process each ticker
        for ticker in tickers:
            try:
                logger.debug(f"Processing {ticker}")

                # Fetch data
                df = self.fetcher.fetch_data(ticker)

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

            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                results.append(
                    {
                        "Ticker": ticker,
                        "Price": None,
                        "Date": None,
                        "Return": None,
                        "Predicted Return": "Error",
                        "Score": "N/A",
                    }
                )

        # Sort results by predicted return (descending)
        results = sorted(
            results,
            key=lambda x: (
                x["Return"] is None,
                -x["Return"] if x["Return"] is not None else 0,
            ),
        )

        # Format output
        if output_format == "json":
            return json.dumps(results, indent=2)
        elif output_format == "csv":
            return self._format_csv(results)
        else:  # table
            return self._format_table(results)

    def _format_table(self, results):
        """Format results as a table"""
        if not results:
            return "No results to display"

        # Define headers and widths
        headers = ["Ticker", "Price", "Date", "Predicted Return", "Score"]
        widths = [10, 12, 12, 16, 8]

        # Create header row
        header = "  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=False))
        separator = "-" * len(header)

        # Create rows
        rows = []
        for r in results:
            row = [
                r["Ticker"].ljust(widths[0]),
                f"{r['Price']:.2f}".ljust(widths[1])
                if r["Price"]
                else "N/A".ljust(widths[1]),
                (r["Date"] or "N/A").ljust(widths[2]),
                r["Predicted Return"].ljust(widths[3]),
                r["Score"].ljust(widths[4]),
            ]
            rows.append("  ".join(row))

        # Combine all parts
        return f"\n{header}\n{separator}\n" + "\n".join(rows)

    def _format_csv(self, results):
        """Format results as CSV"""
        if not results:
            return "No results to display"

        # Define headers
        headers = ["Ticker", "Price", "Date", "Predicted Return", "Score"]

        # Create CSV string
        output = []
        output.append(",".join(headers))

        for r in results:
            row = [
                r["Ticker"],
                f"{r['Price']:.2f}" if r["Price"] else "",
                r["Date"] or "",
                r["Predicted Return"],
                r["Score"],
            ]
            output.append(",".join(row))

        return "\n".join(output)

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
        sys.exit(1)

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
    try:
        output = app.run_predictions(tickers, args.format)
        print("\nPrediction Results:")
        print(output)
    except Exception as e:
        logger.error(f"Error running predictions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
