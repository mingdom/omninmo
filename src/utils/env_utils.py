"""
Environment utilities for loading and managing environment variables.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set default level to DEBUG

def load_env():
    """
    Load environment variables from .env file.
    
    Returns:
        bool: True if environment variables were loaded successfully, False otherwise
    """
    try:
        # Find the .env file in the project root
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        
        if os.path.exists(dotenv_path):
            # Load environment variables from .env file
            load_dotenv(dotenv_path)
            logger.info(f"Environment variables loaded from {dotenv_path}")
            return True
        else:
            logger.warning(f"No .env file found at {dotenv_path}")
            return False
    except Exception as e:
        logger.error(f"Error loading environment variables: {str(e)}", exc_info=True)
        return False 