#!/usr/bin/env python3
"""
Script to test the train_on_default_tickers function.
"""

import os
import sys
import logging
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the train_on_default_tickers function."""
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Add the project root to the Python path
    sys.path.insert(0, project_root)
    
    # Import the trainer module
    try:
        from src.utils.trainer import train_on_default_tickers
        logger.info("Successfully imported train_on_default_tickers function")
    except ImportError as e:
        logger.error(f"Failed to import train_on_default_tickers: {e}")
        sys.exit(1)
    
    # Create a temporary file for the model
    with tempfile.NamedTemporaryFile(suffix='.pkl') as temp_file:
        model_path = temp_file.name
        
        # Test with a small subset of tickers and a longer period to ensure enough data
        # Using 2y instead of 1mo to ensure we have enough data points
        test_tickers = ['AAPL', 'MSFT']
        test_period = '2y'
        
        logger.info(f"Testing train_on_default_tickers with tickers={test_tickers}, period={test_period}")
        
        try:
            # Call the function with test parameters
            model = train_on_default_tickers(
                model_path=model_path,
                period=test_period,
                tickers=test_tickers
            )
            
            # Check if the model was created successfully
            if model is not None:
                logger.info("Successfully trained the model")
                
                # Check if the model file was created
                if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
                    logger.info(f"Model file created at {model_path}")
                else:
                    logger.error(f"Model file not created or empty at {model_path}")
                    return 1
                
                return 0
            else:
                logger.error("Failed to train the model")
                return 1
                
        except Exception as e:
            logger.error(f"Error testing train_on_default_tickers: {e}")
            return 1

if __name__ == '__main__':
    sys.exit(main()) 