#!/usr/bin/env python3
"""
Script to train the stock rating prediction model on default tickers.
"""

import os
import sys
import argparse
import logging

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the training function
try:
    from src.utils.trainer import train_on_default_tickers, DEFAULT_TICKERS
except ImportError as e:
    logger.error(f"Failed to import training function: {e}")
    sys.exit(1)

def main():
    """Main function to parse arguments and train the model."""
    parser = argparse.ArgumentParser(description='Train the stock rating prediction model.')
    parser.add_argument('--model-path', type=str, default='models/stock_predictor.pkl',
                        help='Path to save the trained model')
    parser.add_argument('--period', type=str, default='2y',
                        help='Time period for historical data (e.g., 1y, 2y)')
    parser.add_argument('--tickers', type=str, nargs='+',
                        help='List of ticker symbols to use for training')
    parser.add_argument('--force-sample', action='store_true',
                        help='Force the use of sample data instead of fetching from API')
    
    args = parser.parse_args()
    
    # Use provided tickers or default ones
    tickers = args.tickers if args.tickers else DEFAULT_TICKERS
    
    logger.info(f"Starting model training with {len(tickers)} tickers for period {args.period}")
    
    # Train the model
    model = train_on_default_tickers(
        model_path=args.model_path,
        period=args.period,
        tickers=tickers,
        force_sample=args.force_sample
    )
    
    if model is not None:
        logger.info("Model training completed successfully")
    else:
        logger.error("Model training failed")
        sys.exit(1)

if __name__ == '__main__':
    main() 