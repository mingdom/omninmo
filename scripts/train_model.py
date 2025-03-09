"""
Script to train the XGBoost stock rating prediction model.
"""

#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary modules
from src.models.xgboost_predictor import XGBoostRatingPredictor
from src.utils.trainer import Trainer, DEFAULT_TICKERS
from src.utils.env_utils import load_env

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

def configure_logging(log_level):
    """Configure logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/training.log', mode='a')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging level set to {log_level}")
    return logger

def main():
    """
    Train the XGBoost stock rating prediction model.
    """
    parser = argparse.ArgumentParser(description='Train an XGBoost stock rating model.')
    parser.add_argument('-f', '--model-file', type=str, default='models/xgboost_model.pkl',
                        help='Path to save the trained model')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Automatically overwrite the model file if it exists')
    parser.add_argument('-s', '--sample', action='store_true',
                        help='Use sample data for training (faster for testing)')
    parser.add_argument('-l', '--log-level', type=str, default='DEBUG',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Set the logging level')
    args = parser.parse_args()
    
    # Configure logging
    logger = configure_logging(args.log_level)
    
    # Load environment variables
    if not load_env():
        logger.error("Failed to load environment variables, aborting")
        sys.exit(1)

    # Get the full path to the model file
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', args.model_file))
    
    # Check if the model file exists
    if os.path.exists(model_path):
        logger.info(f"Model exists at {model_path}")
        if not args.yes:
            response = input(f"Model file {model_path} already exists. Overwrite? (y/n): ")
            if response.lower() != 'y':
                logger.info("Training canceled by user")
                return
        logger.info(f"Model will be overwritten")
    
    # Create the model directory if it doesn't exist
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # Create an instance of the Trainer class
    trainer = Trainer(use_sample_data=args.sample)
    
    # Start and end dates for training data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5)  # 5 years of data
    
    # Train the model
    logger.info(f"Training XGBoost model using data from {len(DEFAULT_TICKERS)} major stocks across various sectors")
    
    try:
        # Prepare the training data
        features, target = trainer.prepare_training_data(DEFAULT_TICKERS, start_date, end_date)
        
        if features.empty or target.empty:
            logger.error("Empty features or target data, cannot train model")
            sys.exit(1)
            
        logger.info(f"Data preparation complete. Features shape: {features.shape}, Target shape: {target.shape}")
        
        # Initialize and train the model
        model = XGBoostRatingPredictor()
        
        # Train the model
        start_time = datetime.now()
        accuracy = model.train(features, target)
        end_time = datetime.now()
        
        logger.info(f"Model trained with accuracy: {accuracy:.4f}")
        logger.info(f"Training completed in {(end_time - start_time).total_seconds()} seconds")
        
        # Save the model
        if not model.save(model_path):
            logger.error(f"Failed to save model to {model_path}")
            sys.exit(1)
            
        logger.info(f"Model saved to {model_path}")
        logger.info("To run the application, use: python run_app.py")
        
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
