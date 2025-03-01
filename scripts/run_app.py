#!/usr/bin/env python3
"""
Script to run the omninmo Streamlit application.
"""

import os
import sys
import subprocess
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the Streamlit application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the omninmo Streamlit application.')
    parser.add_argument('--sample-data', action='store_true', 
                       help='Use generated sample data instead of fetching from Yahoo Finance API (useful when API has issues)')
    args = parser.parse_args()
    
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Path to the Streamlit app
    app_path = os.path.join(project_root, 'src', 'app', 'streamlit_app.py')
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        logger.error(f"Streamlit app not found at {app_path}")
        sys.exit(1)
    
    logger.info(f"Starting Streamlit app from {app_path}")
    
    # Run the Streamlit app
    try:
        # Create the models directory if it doesn't exist
        models_dir = os.path.join(project_root, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        # Create the cache directory if it doesn't exist
        cache_dir = os.path.join(project_root, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Check if the model exists
        model_path = os.path.join(models_dir, 'stock_predictor.pkl')
        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}. You may need to train the model first.")
            print("=" * 80)
            print(f"WARNING: Model not found at {model_path}")
            print("You may need to train the model first by running:")
            print("    make train")
            print("=" * 80)
        
        # Run the Streamlit app
        cmd = ['streamlit', 'run', app_path]
        
        # Add environment variables for sample data if requested
        env = os.environ.copy()
        if args.sample_data:
            logger.info("Using sample data mode")
            env['OMNINMO_USE_SAMPLE_DATA'] = 'true'
            print("=" * 80)
            print("RUNNING WITH SAMPLE DATA MODE")
            print("The app will use generated sample data instead of fetching from Yahoo Finance API")
            print("=" * 80)
        
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Streamlit app: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Streamlit not found. Please install it with 'pip3 install streamlit'")
        print("=" * 80)
        print("ERROR: Streamlit not found.")
        print("Please install it with:")
        print("    pip3 install streamlit")
        print("=" * 80)
        sys.exit(1)

if __name__ == '__main__':
    main() 