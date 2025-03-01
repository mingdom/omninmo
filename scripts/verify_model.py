#!/usr/bin/env python
"""
Script to verify the model type being used in the application.
"""

import os
import sys
import pickle
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def verify_model():
    """Verify the model type being used in the application."""
    model_path = os.path.join(project_root, "models", "stock_predictor.pkl")
    
    try:
        # Load the model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Get model type
        model_type = type(model).__name__
        logger.info(f"Model type: {model_type}")
        
        # Check if it's the XGBoost model
        if model_type == "XGBoostRatingPredictor":
            logger.info("✅ XGBoost model is being used as expected")
            
            # Check if actual XGBoost is available or using fallback
            if hasattr(model, 'model'):
                model_impl = type(model.model).__name__
                logger.info(f"Model implementation: {model_impl}")
                
                if "XGB" in model_impl:
                    logger.info("✅ Using actual XGBoost implementation")
                else:
                    logger.info("⚠️ Using fallback GradientBoostingClassifier from sklearn")
            
            # Print feature importance if available
            if hasattr(model, 'feature_importance') and model.feature_importance is not None:
                logger.info("Top 10 features by importance:")
                for feature, importance in model.feature_importance.head(10).items():
                    logger.info(f"  {feature}: {importance:.4f}")
            
            return True
        else:
            logger.warning(f"❌ Expected XGBoostRatingPredictor but found {model_type}")
            return False
    
    except FileNotFoundError:
        logger.error(f"❌ Model file not found at {model_path}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verifying model: {e}")
        return False

if __name__ == "__main__":
    verify_model() 