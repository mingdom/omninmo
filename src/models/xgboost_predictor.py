"""
XGBoost-based stock rating predictor module.

This module implements the XGBoost prediction model for stock ratings.
"""

import numpy as np
import pandas as pd
import logging
import logging.handlers
from pathlib import Path
import pickle
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

# Setup logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set default level to DEBUG

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Setup file handler
file_handler = logging.handlers.RotatingFileHandler(
    'logs/xgboost_predictor.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

class XGBoostRatingPredictor:
    """
    Class for predicting stock ratings using XGBoost classifier.
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
        logger.debug(f"Initializing XGBoostRatingPredictor with learning_rate={learning_rate}, "
                   f"max_depth={max_depth}, n_estimators={n_estimators}, random_state={random_state}")
                   
        self.model = xgb.XGBClassifier(
            learning_rate=learning_rate,
            max_depth=max_depth,
            n_estimators=n_estimators,
            random_state=random_state,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        logger.info("XGBoost classifier initialized")
        self.classes = None
        self.feature_importance = None
        self.label_encoder = LabelEncoder()
    
    def train(self, X, y, test_size=0.2):
        """
        Train the model on the provided data.
        
        Args:
            X (pandas.DataFrame): Features for training
            y (pandas.Series): Target labels (string labels)
            test_size (float): Proportion of data to use for testing
        
        Returns:
            dict: Dictionary containing training results including accuracy and classification report
        """
        try:
            logger.info(f"Training model with {X.shape[0]} samples and {X.shape[1]} features")
            logger.debug(f"Target distribution: {y.value_counts().to_dict()}")
            logger.debug(f"Feature columns: {list(X.columns)}")
            
            # Store the unique class values and fit the label encoder
            self.classes = np.unique(y)
            y_encoded = self.label_encoder.fit_transform(y)
            logger.debug(f"Unique classes: {self.classes}")
            logger.debug(f"Encoded classes: {np.unique(y_encoded)}")
            
            # Check if we have enough samples per class for stratification
            min_samples_per_class = y.value_counts().min()
            use_stratify = min_samples_per_class >= 2
            logger.debug(f"Using stratification: {use_stratify} (min samples per class: {min_samples_per_class})")
            
            # Split the data into training and testing sets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded if use_stratify else None
            )
            
            logger.debug(f"Training set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")
            
            # Train the model
            logger.debug("Starting model fitting")
            self.model.fit(X_train, y_train)
            logger.debug("Model fitting completed")
            
            # Calculate feature importance
            self.feature_importance = pd.Series(
                self.model.feature_importances_,
                index=X.columns
            ).sort_values(ascending=False)
            
            top_features = self.feature_importance.head(10)
            logger.debug(f"Top 10 features: {top_features.to_dict()}")
            
            # Evaluate the model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Convert numeric predictions back to string labels for the report
            y_test_decoded = self.label_encoder.inverse_transform(y_test)
            y_pred_decoded = self.label_encoder.inverse_transform(y_pred)
            report = classification_report(y_test_decoded, y_pred_decoded, output_dict=True)
            
            logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            logger.debug(f"Classification report: {report}")
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'feature_importance': top_features.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}", exc_info=True)
            raise
    
    def predict(self, features):
        """
        Predict the stock rating for the given features.
        
        Args:
            features (pandas.DataFrame): Features for prediction
        
        Returns:
            tuple: (predicted_rating, confidence) where predicted_rating is a string label
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None, 0
        
        try:
            logger.debug(f"Making prediction with features shape: {features.shape}")
            
            # Make prediction
            prediction = self.model.predict(features)
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(features)
            
            # Convert numeric prediction back to string label
            prediction_decoded = self.label_encoder.inverse_transform(prediction)
            
            # Get the index of the predicted class in the probability array
            pred_class_idx = prediction[0]
            
            # Get the confidence (probability) of the prediction
            confidence = probabilities[0][pred_class_idx]
            
            logger.info(f"Predicted rating: {prediction_decoded[0]} with confidence: {confidence:.4f}")
            logger.debug(f"All class probabilities: {probabilities[0]}")
            
            return prediction_decoded[0], confidence
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}", exc_info=True)
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
        
        logger.debug(f"Getting top {top_n} features by importance")
        return self.feature_importance.head(top_n)
    
    def evaluate(self, X, y):
        """
        Evaluate the model on the provided data.
        
        Args:
            X (pandas.DataFrame): Features for evaluation
            y (pandas.Series): True labels (string labels)
        
        Returns:
            dict: Dictionary containing evaluation metrics
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None
        
        try:
            logger.debug(f"Evaluating model on {X.shape[0]} samples")
            
            # Encode the labels
            y_encoded = self.label_encoder.transform(y)
            
            # Make predictions
            y_pred = self.model.predict(X)
            
            # Calculate metrics
            accuracy = accuracy_score(y_encoded, y_pred)
            
            # Convert predictions back to string labels for the report
            y_pred_decoded = self.label_encoder.inverse_transform(y_pred)
            report = classification_report(y, y_pred_decoded, output_dict=True)
            
            logger.info(f"Model evaluation accuracy: {accuracy:.4f}")
            logger.debug(f"Evaluation classification report: {report}")
            
            return {
                'accuracy': accuracy,
                'classification_report': report
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}", exc_info=True)
            return None
            
    def save(self, filepath):
        """
        Save the trained model to a file.
        
        Args:
            filepath (str): Path to save the model file
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.model is None:
            logger.error("Cannot save: model not trained yet")
            return False
            
        try:
            logger.info(f"Saving model to {filepath}")
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            logger.info("Model saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def load(cls, filepath):
        """
        Load a trained model from a file.
        
        Args:
            filepath (str): Path to the model file
        
        Returns:
            XGBoostRatingPredictor: Loaded model instance
        """
        try:
            logger.info(f"Loading model from {filepath}")
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}", exc_info=True)
            return None 