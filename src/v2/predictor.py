"""
XGBoost model for stock prediction
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import accuracy_score, classification_report
import math

from src.v2.config import config

logger = logging.getLogger(__name__)

class Predictor:
    """Stock prediction model using XGBoost"""
    
    def __init__(self, mode='regression'):
        """
        Initialize the predictor
        
        Args:
            mode (str): 'regression' or 'classification'
        """
        self.mode = mode
        
        # Load XGBoost parameters from config
        params = config.get('model.xgboost', {})
        self.learning_rate = params.get('learning_rate', 0.1)
        self.max_depth = params.get('max_depth', 6)
        self.n_estimators = params.get('n_estimators', 100)
        self.random_state = params.get('random_state', 42)
        
        # Initialize model
        if mode == 'classification':
            self.model = xgb.XGBClassifier(
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
            self.classes = None
        else:  # regression mode
            self.model = xgb.XGBRegressor(
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                objective='reg:squarederror'
            )
            self.classes = None  # Initialize for both modes
        
        # Store feature importance and feature names
        self.feature_importance = None
        self.feature_names = None
    
    def train(self, X, y, test_size=0.2):
        """
        Train the model
        
        Args:
            X (pandas.DataFrame): Features
            y (pandas.Series): Target values
            test_size (float): Proportion of data for testing
            
        Returns:
            dict: Training results
        """
        logger.info(f"Training {self.mode} model with {len(X)} samples")
        
        # Store feature names for prediction
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Calculate feature importance
        self.feature_importance = pd.Series(
            self.model.feature_importances_,
            index=X.columns
        ).sort_values(ascending=False)
        
        # Log top features
        logger.info("Top 10 important features:")
        top_features = self.feature_importance.head(10)
        for feature, importance in top_features.items():
            logger.info(f"  {feature}: {importance:.4f}")
        
        # Evaluate model
        if self.mode == 'classification':
            # For classification
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            logger.info(f"Accuracy: {accuracy:.4f}")
            
            # Store classes
            self.classes = self.model.classes_
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'feature_importance': top_features.to_dict()
            }
        
        else:  # regression mode
            # For regression
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            rmse = math.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
            
            return {
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'feature_importance': top_features.to_dict()
            }
    
    def predict(self, features):
        """
        Make prediction for new data
        
        Args:
            features (pandas.DataFrame): Features for prediction
            
        Returns:
            tuple: Prediction results based on mode
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None
        
        try:
            # Make a copy of features to avoid modifying the original
            features = features.copy()
            
            # Remove label column if it exists (not needed for prediction)
            if 'label' in features.columns:
                features = features.drop('label', axis=1)
            
            # Ensure all features are numeric
            for col in features.columns:
                if features[col].dtype == 'object':
                    logger.warning(f"Converting non-numeric column {col} to numeric")
                    features.loc[:, col] = pd.to_numeric(features[col], errors='coerce')
            
            # Fill any NaN values that might have been introduced
            features = features.fillna(0)
            
            # Check if we have the expected feature names
            if self.feature_names is not None:
                # Get the intersection of available features
                common_features = list(set(features.columns) & set(self.feature_names))
                
                if len(common_features) < len(self.feature_names):
                    missing_features = set(self.feature_names) - set(common_features)
                    logger.warning(f"Missing features: {missing_features}")
                    
                    # Add missing features with zeros
                    for feature in missing_features:
                        features[feature] = 0
                
                # Remove extra features not used in training
                extra_features = set(features.columns) - set(self.feature_names)
                if extra_features:
                    logger.warning(f"Removing extra features not used in training: {extra_features}")
                    features = features[self.feature_names]
                
                # Ensure features are in the same order as during training
                features = features[self.feature_names]
            
            if self.mode == 'classification':
                # Make class prediction
                prediction = self.model.predict(features)[0]
                
                # Get prediction probabilities
                probabilities = self.model.predict_proba(features)[0]
                
                # Get the index of the predicted class
                if hasattr(prediction, 'item'):
                    pred_idx = self.model.classes_.tolist().index(prediction)
                else:
                    pred_idx = np.where(self.model.classes_ == prediction)[0][0]
                
                # Get confidence
                confidence = probabilities[pred_idx]
                
                return prediction, confidence
                
            else:  # regression mode
                # Make prediction
                predicted_return = self.model.predict(features)[0]
                
                # Calculate normalized score (0-1)
                score = self.normalize_return(predicted_return)
                
                # Get rating based on thresholds
                rating = self.get_rating(predicted_return)
                
                # Simple confidence calculation
                confidence = 0.7  # Default confidence
                
                return predicted_return, score, rating, confidence
                
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def normalize_return(self, return_value):
        """
        Normalize return to 0-1 score
        
        Args:
            return_value (float): Predicted return
            
        Returns:
            float: Score between 0 and 1
        """
        # Get normalization parameters from config
        params = config.get('model.normalization', {})
        method = params.get('method', 'sigmoid')
        
        if method == 'sigmoid':
            # Apply sigmoid normalization
            k = params.get('sigmoid_k', 10)
            return 1 / (1 + np.exp(-k * return_value))
            
        elif method == 'linear':
            # Apply linear normalization
            min_val = params.get('linear_min', -0.1)
            max_val = params.get('linear_max', 0.1)
            
            # Clip return value to range
            clipped = max(min(return_value, max_val), min_val)
            
            # Normalize to 0-1
            return (clipped - min_val) / (max_val - min_val)
            
        else:
            # Default to simple normalization
            # Assume returns within -10% to +10%
            return (return_value + 0.1) / 0.2
    
    def get_rating(self, return_value):
        """
        Convert return to rating category
        
        Args:
            return_value (float): Predicted return
            
        Returns:
            str: Rating category
        """
        # Get thresholds from config
        thresholds = config.get('model.training.rating_thresholds', {})
        
        strong_buy = thresholds.get('strong_buy', 0.06)
        buy = thresholds.get('buy', 0.03)
        hold = thresholds.get('hold', -0.03)
        sell = thresholds.get('sell', -0.06)
        
        if return_value > strong_buy:
            return 'Strong Buy'
        elif return_value > buy:
            return 'Buy'
        elif return_value > hold:
            return 'Hold'
        elif return_value > sell:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def analyze_feature_importance(self):
        """
        Analyze and return feature importance in a detailed format.
        
        Returns:
            pandas.DataFrame: DataFrame containing feature importance analysis with columns:
                - feature: Feature name
                - importance: Importance score
                - importance_pct: Importance as percentage
                - cumulative_pct: Cumulative importance percentage
        """
        if self.model is None or self.feature_names is None:
            logger.error("Model not trained or feature names not available")
            return None
            
        try:
            # Create DataFrame with feature importance
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            })
            
            # Sort by importance
            importance_df = importance_df.sort_values('importance', ascending=False)
            
            # Calculate percentage and cumulative percentage
            total_importance = importance_df['importance'].sum()
            importance_df['importance_pct'] = importance_df['importance'] / total_importance * 100
            importance_df['cumulative_pct'] = importance_df['importance_pct'].cumsum()
            
            # Round numeric columns for readability
            importance_df['importance'] = importance_df['importance'].round(4)
            importance_df['importance_pct'] = importance_df['importance_pct'].round(2)
            importance_df['cumulative_pct'] = importance_df['cumulative_pct'].round(2)
            
            # Log top features
            logger.info("\nTop 10 Most Important Features:")
            for _, row in importance_df.head(10).iterrows():
                logger.info(f"{row['feature']}: {row['importance_pct']:.2f}% (cumulative: {row['cumulative_pct']:.2f}%)")
            
            return importance_df
            
        except Exception as e:
            logger.error(f"Error analyzing feature importance: {e}")
            return None
    
    def save(self, filepath):
        """
        Save model to file
        
        Args:
            filepath (str): Path to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        # Save model and metadata
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'mode': self.mode,
                'feature_importance': self.feature_importance,
                'feature_names': self.feature_names,
                'classes': self.classes
            }, f)
        
        logger.info(f"Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath):
        """
        Load model from file
        
        Args:
            filepath (str): Path to the model file
            
        Returns:
            Predictor: Loaded model
        """
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # Create new instance
            instance = cls(mode=data['mode'])
            
            # Set attributes
            instance.model = data['model']
            instance.feature_importance = data['feature_importance']
            instance.feature_names = data.get('feature_names')
            instance.classes = data.get('classes')  # Use get to handle missing key
            
            logger.info(f"Model loaded from {filepath}")
            return instance
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None

if __name__ == "__main__":
    # Simple test
    from src.v2.data_fetcher import DataFetcher
    from src.v2.features import Features
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test model creation
    model = Predictor(mode='regression')
    print(f"Created {model.mode} model")
    
    # Test loading
    if os.path.exists('models/test_model.pkl'):
        loaded = Predictor.load('models/test_model.pkl')
        if loaded:
            print("Successfully loaded existing model") 