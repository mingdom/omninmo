#!/usr/bin/env python3
"""
Model maintenance script for omninmo.

This script handles automated model maintenance tasks:
- Daily incremental updates
- Weekly full retraining
- Monthly evaluation

Usage:
    python maintain_model.py --mode [daily|weekly|monthly]
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import shutil

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'logs', 'model_maintenance.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
try:
    from src.utils.trainer import train_on_default_tickers, load_model, evaluate_model
    from src.data.stock_data_fetcher import StockDataFetcher
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs(os.path.join(project_root, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'models', 'archive'), exist_ok=True)

def archive_current_model():
    """Archive the current model with a timestamp."""
    current_model_path = os.path.join(project_root, 'models', 'stock_predictor.pkl')
    if not os.path.exists(current_model_path):
        logger.warning("No existing model found to archive")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_path = os.path.join(project_root, 'models', 'archive', f'stock_predictor_{timestamp}.pkl')
    
    try:
        shutil.copy2(current_model_path, archive_path)
        logger.info(f"Archived current model to {archive_path}")
    except Exception as e:
        logger.error(f"Failed to archive model: {e}")

def daily_update():
    """Perform daily incremental model update."""
    logger.info("Starting daily model update")
    
    # Archive current model
    archive_current_model()
    
    # Train on recent data (30 days)
    try:
        model = train_on_default_tickers(period='30d')
        if model:
            logger.info("Daily model update completed successfully")
        else:
            logger.error("Daily model update failed")
    except Exception as e:
        logger.error(f"Error during daily update: {e}")

def weekly_update():
    """Perform weekly full model retraining."""
    logger.info("Starting weekly full model retraining")
    
    # Archive current model
    archive_current_model()
    
    # Clear cache to ensure fresh data
    cache_dir = os.path.join(project_root, 'cache')
    if os.path.exists(cache_dir):
        logger.info("Clearing data cache for fresh training")
        try:
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    # Train on longer period (1 year)
    try:
        model = train_on_default_tickers(period='1y')
        if model:
            logger.info("Weekly model retraining completed successfully")
        else:
            logger.error("Weekly model retraining failed")
    except Exception as e:
        logger.error(f"Error during weekly retraining: {e}")

def monthly_evaluation():
    """Perform monthly model evaluation."""
    logger.info("Starting monthly model evaluation")
    
    # Load current model
    model_path = os.path.join(project_root, 'models', 'stock_predictor.pkl')
    model = load_model(model_path)
    
    if not model:
        logger.error("Failed to load model for evaluation")
        return
    
    # Define test tickers (different from training set)
    test_tickers = [
        'ADBE', 'CRM', 'CSCO', 'HD', 'KO', 
        'MCD', 'NKE', 'PEP', 'UNH', 'VZ'
    ]
    
    # Fetch test data
    fetcher = StockDataFetcher(cache_dir=os.path.join(project_root, 'cache'))
    feature_engineer = None  # Will be imported in evaluate_model
    
    try:
        # Evaluate model on test tickers
        results = evaluate_model(model, test_tickers, period="3mo")
        
        if results is not None:
            # Log evaluation metrics
            logger.info(f"Model evaluation results:")
            if 'accuracy' in results:
                logger.info(f"Accuracy: {results['accuracy']:.4f}")
            
            # Save evaluation results
            results_path = os.path.join(
                project_root, 'logs', 
                f'evaluation_{datetime.now().strftime("%Y%m%d")}.csv'
            )
            results.to_csv(results_path)
            logger.info(f"Evaluation results saved to {results_path}")
        else:
            logger.error("Model evaluation failed to produce results")
    except Exception as e:
        logger.error(f"Error during monthly evaluation: {e}")

def main():
    """Main function to handle model maintenance."""
    parser = argparse.ArgumentParser(description='Maintain the stock prediction model')
    parser.add_argument(
        '--mode', 
        choices=['daily', 'weekly', 'monthly'], 
        default='daily', 
        help='Maintenance mode'
    )
    args = parser.parse_args()
    
    # Ensure required directories exist
    ensure_directories()
    
    start_time = datetime.now()
    logger.info(f"Starting model maintenance in {args.mode} mode")
    
    try:
        if args.mode == 'daily':
            daily_update()
        elif args.mode == 'weekly':
            weekly_update()
        elif args.mode == 'monthly':
            monthly_evaluation()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Model maintenance ({args.mode}) completed in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"Unhandled exception during {args.mode} maintenance: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 