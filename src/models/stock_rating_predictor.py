"""
Stock rating predictor module for predicting stock ratings.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockRatingPredictor:
    """
    Class for predicting stock ratings using a RandomForest classifier.
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        """
        Initialize the StockRatingPredictor.
        
        Args:
            n_estimators (int): Number of trees in the random forest
            random_state (int): Random seed for reproducibility
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1  # Use all available cores
        )
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