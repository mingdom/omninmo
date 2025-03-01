"""
Script to test the stock rating prediction model on a set of tickers.
"""

import os
import sys
import pandas as pd
from src.models.predictor import StockRatingPredictor
from src.utils.trainer import evaluate_model


def main():
    """
    Test the stock rating prediction model on a set of tickers.
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the model path
    model_path = os.path.join(script_dir, "models", "stock_rating_model.joblib")

    # Check if model exists
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}")
        print("Please train the model first using: python train_model.py")
        sys.exit(1)

    # Load the model
    print(f"Loading model from {model_path}...")
    try:
        model = StockRatingPredictor(model_path=model_path)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    # Define test tickers
    # You can modify this list to test on different tickers
    test_tickers = [
        # Technology
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "META",
        # Finance
        "JPM",
        "BAC",
        "GS",
        # Healthcare
        "JNJ",
        "PFE",
        "MRK",
        # Consumer
        "PG",
        "KO",
        "WMT",
        # Industrial
        "GE",
        "BA",
        "CAT",
        # Energy
        "XOM",
        "CVX",
        "COP",
        # ETFs
        "SPY",
        "QQQ",
        "DIA",
    ]

    # Ask user if they want to use custom tickers
    use_custom = input("Do you want to use custom tickers? (y/n): ").lower()
    if use_custom == "y":
        custom_input = input(
            "Enter tickers separated by commas (e.g., AAPL,MSFT,GOOGL): "
        )
        if custom_input.strip():
            test_tickers = [
                ticker.strip().upper() for ticker in custom_input.split(",")
            ]

    print(f"Testing model on {len(test_tickers)} tickers: {', '.join(test_tickers)}")

    # Evaluate the model
    try:
        results = evaluate_model(model, test_tickers, period="1y", interval="1d")

        # Display results
        if results is not None and not results.empty:
            # Sort by ticker
            results = results.sort_values("ticker")

            # Display results
            pd.set_option("display.max_rows", None)
            pd.set_option("display.width", 120)

            print("\nPrediction Results:")
            print("===================")

            # Format the results for display
            display_df = results[["ticker", "rating", "current_price"]].copy()

            # Add future return if available
            if "future_return_20d" in results.columns:
                display_df["future_return_20d"] = results["future_return_20d"].apply(
                    lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A"
                )

            # Add prediction correctness if available
            if "prediction_correct" in results.columns:
                display_df["prediction_correct"] = results["prediction_correct"].apply(
                    lambda x: "✓" if x == True else "✗" if x == False else "N/A"
                )

            print(display_df.to_string(index=False))

            # Calculate statistics
            if "prediction_correct" in results.columns:
                correct = results["prediction_correct"].sum()
                total = results["prediction_correct"].count()
                accuracy = correct / total if total > 0 else 0

                print(f"\nAccuracy: {correct}/{total} ({accuracy:.2%})")

            # Save results to CSV
            csv_path = os.path.join(script_dir, "model_test_results.csv")
            results.to_csv(csv_path, index=False)
            print(f"\nDetailed results saved to {csv_path}")
        else:
            print("No results returned from evaluation.")

    except Exception as e:
        print(f"Error during model evaluation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
