"""
Script to train the stock rating prediction model.
"""

import os
import sys
import time
from src.utils.trainer import train_on_default_tickers


def main():
    """
    Train the stock rating prediction model.
    """
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the model path
    model_path = os.path.join(script_dir, "models", "stock_rating_model.joblib")

    # Create models directory if it doesn't exist
    models_dir = os.path.join(script_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    # Check if model already exists
    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
        overwrite = input("Do you want to overwrite it? (y/n): ").lower()
        if overwrite != "y":
            print("Training cancelled.")
            sys.exit(0)

    # Start training
    print("Starting model training...")
    print(
        "This may take several minutes depending on your internet connection and the number of tickers."
    )
    print("The model will be trained on 100+ major stocks from different sectors.")

    start_time = time.time()

    try:
        # Train the model
        train_on_default_tickers(model_path=model_path)

        # Calculate training time
        training_time = time.time() - start_time
        minutes = int(training_time // 60)
        seconds = int(training_time % 60)

        print(f"Model training completed in {minutes} minutes and {seconds} seconds.")
        print(f"Model saved to {model_path}")
        print("You can now run the app with: python run_app.py")

    except Exception as e:
        print(f"Error during model training: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
