"""
Script to predict the rating for a single stock ticker.
"""

import os
import sys
import argparse
from datetime import datetime
import pandas as pd

from src.data.fmp_data_fetcher import FMPDataFetcher
from src.data.features import FeatureEngineer
from src.models.predictor import StockRatingPredictor
from src.utils.analysis import generate_summary


def predict_ticker(ticker, period="1y", interval="1d", model_path=None):
    """
    Predict the rating for a single stock ticker.

    Args:
        ticker (str): Stock ticker symbol
        period (str): Period to fetch data for
        interval (str): Data interval
        model_path (str, optional): Path to the model file

    Returns:
        tuple: (rating, summary, df) where rating is the predicted rating,
               summary is a dictionary with summary information,
               and df is the DataFrame with stock data
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set default model path if not provided
    if model_path is None:
        model_path = os.path.join(script_dir, "models", "stock_rating_model.joblib")

    # Check if model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. Please train the model first."
        )

    # Initialize components
    fetcher = FMPDataFetcher()
    feature_engineer = FeatureEngineer()
    predictor = StockRatingPredictor(model_path=model_path)

    # Fetch data
    print(f"Fetching data for {ticker}...")
    df = fetcher.fetch_stock_data(ticker, period=period, interval=interval)

    if df is None or df.empty:
        raise ValueError(f"No data found for {ticker}")

    # Add technical indicators
    print("Calculating technical indicators...")
    df_with_indicators = feature_engineer.add_technical_indicators(df)

    if df_with_indicators is None or df_with_indicators.empty:
        raise ValueError(f"Could not calculate technical indicators for {ticker}")

    # Prepare features
    X, _ = feature_engineer.prepare_features(df_with_indicators)

    if X is None or len(X) == 0:
        raise ValueError(f"Could not generate features for {ticker}")

    # Make prediction
    print("Predicting rating...")
    ratings = predictor.predict(X)

    # Get the most recent rating
    latest_rating = ratings[-1] if ratings else None

    if latest_rating is None:
        raise ValueError(f"Could not predict rating for {ticker}")

    # Generate summary
    summary = generate_summary(df, ticker, latest_rating)

    return latest_rating, summary, df


def main():
    """
    Main function for the script.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Predict the rating for a stock ticker."
    )
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., NVDA, AAPL)")
    parser.add_argument(
        "--period", "-p", default="1y", help="Period to fetch data for (default: 1y)"
    )
    parser.add_argument(
        "--interval", "-i", default="1d", help="Data interval (default: 1d)"
    )
    parser.add_argument("--model", "-m", help="Path to the model file")

    args = parser.parse_args()

    # Convert ticker to uppercase
    ticker = args.ticker.upper()

    try:
        # Predict rating
        rating, summary, df = predict_ticker(
            ticker=ticker,
            period=args.period,
            interval=args.interval,
            model_path=args.model,
        )

        # Display results
        print("\n" + "=" * 50)
        print(
            f"Prediction for {ticker} as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 50)

        # Rating
        print(f"\nomninmo Rating: {rating}")

        # Current price and change
        print(f"\nPrice Information:")
        print(f"Current Price: ${summary['current_price']:.2f}")
        if summary["change_1d"] is not None:
            change_sign = "+" if summary["change_1d"] >= 0 else ""
            print(f"1-Day Change: {change_sign}{summary['change_1d']*100:.2f}%")

        # Returns
        print(f"\nReturns:")
        for period in ["1d", "5d", "20d", "60d", "120d", "252d"]:
            if period in summary and summary[period] is not None:
                change_sign = "+" if summary[period] >= 0 else ""
                print(f"{period}: {change_sign}{summary[period]:.2f}%")

        # Risk metrics
        print(f"\nRisk Metrics:")
        if summary["volatility"] is not None:
            print(f"Volatility (Ann.): {summary['volatility']*100:.2f}%")
        if summary["sharpe_ratio"] is not None:
            print(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        if summary["max_drawdown"] is not None:
            print(f"Max Drawdown: {summary['max_drawdown']:.2f}%")

        print("\nFor more detailed analysis, run the Streamlit app: python run_app.py")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
