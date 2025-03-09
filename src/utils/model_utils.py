"""
Model utility functions for managing model versioning and symlinks.
"""

import os
from datetime import datetime
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

def generate_model_filename(base_name='stock_predictor', ext='.pkl'):
    """
    Generate a timestamped model filename.
    
    Args:
        base_name (str): Base name for the model file
        ext (str): File extension
        
    Returns:
        str: Timestamped filename
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}{ext}"

def update_latest_symlink(model_path, symlink_path):
    """
    Update the symlink to point to the latest model.
    
    Args:
        model_path (str): Path to the actual model file
        symlink_path (str): Path where the symlink should be created/updated
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the symlink path's directory exists
        os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
        
        # Remove existing symlink if it exists
        if os.path.exists(symlink_path):
            if os.path.islink(symlink_path):
                os.unlink(symlink_path)
            else:
                logger.error(f"'{symlink_path}' exists but is not a symlink")
                return False
        
        # Create new symlink
        os.symlink(os.path.abspath(model_path), symlink_path)
        logger.info(f"Updated symlink {symlink_path} -> {model_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating symlink: {str(e)}")
        return False

def get_latest_model_path(models_dir='models', symlink_name='latest_model.pkl'):
    """
    Get the path to the latest model via symlink.
    
    Args:
        models_dir (str): Directory containing model files
        symlink_name (str): Name of the symlink file
        
    Returns:
        str: Path to the latest model
    """
    return os.path.join(models_dir, symlink_name)

def save_model_versioned(model, models_dir='models', base_name='stock_predictor', symlink_name='latest_model.pkl'):
    """
    Save a model with versioning and update the latest symlink.
    
    Args:
        model: The model object to save
        models_dir (str): Directory to save models in
        base_name (str): Base name for the model file
        symlink_name (str): Name of the symlink file
        
    Returns:
        tuple: (bool, str) indicating success and the path to the saved model
    """
    try:
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # Generate versioned filename
        filename = generate_model_filename(base_name)
        model_path = os.path.join(models_dir, filename)
        
        # Save the model
        model.save(model_path)
        
        # Update symlink
        symlink_path = os.path.join(models_dir, symlink_name)
        if update_latest_symlink(model_path, symlink_path):
            logger.info(f"Model saved to {model_path} with symlink {symlink_path}")
            return True, model_path
        else:
            logger.error("Failed to update symlink")
            return False, model_path
            
    except Exception as e:
        logger.error(f"Error saving versioned model: {str(e)}")
        return False, None 