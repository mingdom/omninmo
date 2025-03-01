"""
XGBoost-based stock rating predictor module.

This module implements an alternative prediction model using XGBoost
as an example of the model improvement strategies.
"""

import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Try to import XGBoost, but fall back to sklearn's GradientBoostingClassifier if not available
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available. Using sklearn's GradientBoostingClassifier instead.")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XGBoostRatingPredictor:
    """
    Class for predicting stock ratings using XGBoost classifier.
    
    This is an example implementation of an alternative model
    as suggested in the model improvement strategies.
    
    If XGBoost is not available, it falls back to sklearn's GradientBoostingClassifier.
    """
    
    def __init__(self, learning_rate=0.1, max_depth=6, n_estimators=100, random_state=42):
        """
        Initialize the XGBoostRatingPredictor.
        
        Args:
            learning_rate (float): Learning rate for XGBoost
            max_depth (int): Maximum tree depth
            n_estimators (int): Number of boosting rounds
            random_state (int): Random seed for reproducibility
        """
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                learning_rate=learning_rate,
                max_depth=max_depth,
                n_estimators=n_estimators,
                random_state=random_state,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
            logger.info("Using XGBoost classifier")
        else:
            self.model = GradientBoostingClassifier(
                learning_rate=learning_rate,
                max_depth=max_depth,
                n_estimators=n_estimators,
                random_state=random_state
            )
            logger.info("Using sklearn's GradientBoostingClassifier as fallback")
            
        self.classes = None
        self.feature_importance = None
    
    def train(self, X, y, test_size=0.2):
        """
        Train the model on the provided data.
        
        Args:
            X (pandas.DataFrame): Features for training
            y (pandas.Series): Target labels
            test_size (float): Proportion of data to use for testing
        
        Returns:
            dict: Dictionary containing training metrics
        """
        try:
            logger.info(f"Training model with {X.shape[0]} samples and {X.shape[1]} features")
            
            # Store the class labels
            self.classes = np.unique(y)
            
            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
            
            # Train the model
            self.model.fit(X_train, y_train)
            
            # Calculate feature importance
            self.feature_importance = pd.Series(
                self.model.feature_importances_,
                index=X.columns
            ).sort_values(ascending=False)
            
            # Evaluate the model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'feature_importance': self.feature_importance
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    def predict(self, features):
        """
        Predict the stock rating for the given features.
        
        Args:
            features (pandas.DataFrame): Features for prediction
        
        Returns:
            tuple: (predicted_rating, confidence)
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None, 0
        
        try:
            # Make prediction
            prediction = self.model.predict(features)
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(features)
            
            # Get the index of the predicted class
            pred_idx = np.where(self.classes == prediction[0])[0][0]
            
            # Get the confidence (probability) of the prediction
            confidence = probabilities[0][pred_idx]
            
            logger.info(f"Predicted rating: {prediction[0]} with confidence: {confidence:.4f}")
            
            return prediction[0], confidence
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None, 0
    
    def get_feature_importance(self, top_n=10):
        """
        Get the top N most important features.
        
        Args:
            top_n (int): Number of top features to return
        
        Returns:
            pandas.Series: Series containing feature importance scores
        """
        if self.feature_importance is None:
            logger.warning("Feature importance not available (model not trained)")
            return None
        
        return self.feature_importance.head(top_n)
    
    def evaluate(self, X, y):
        """
        Evaluate the model on the provided data.
        
        Args:
            X (pandas.DataFrame): Features for evaluation
            y (pandas.Series): True labels
        
        Returns:
            dict: Dictionary containing evaluation metrics
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None
        
        try:
            # Make predictions
            y_pred = self.model.predict(X)
            
            # Calculate metrics
            accuracy = accuracy_score(y, y_pred)
            report = classification_report(y, y_pred, output_dict=True)
            
            logger.info(f"Model evaluation accuracy: {accuracy:.4f}")
            
            return {
                'accuracy': accuracy,
                'classification_report': report
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return None 