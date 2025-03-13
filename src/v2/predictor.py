"""
XGBoost model for stock prediction
"""

import os
import pickle
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, KFold
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
    
    def train(self, X, y):
        """
        Train the model on the full dataset after cross-validation.
        This ensures we have a final model trained on all available data
        while maintaining confidence in its performance through prior CV.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target values
            
        Returns:
            dict: Training results including metrics and feature importance
        """
        logger.info("Training final model on full dataset...")
        
        # Ensure data types are correct
        X = X.astype(np.float32)
        if self.mode == 'classification':
            y = y.astype(int)
        else:
            y = y.astype(np.float32)
        
        # Train the model
        self.model.fit(X, y)
        
        # Get predictions
        y_pred = self.model.predict(X)
        
        # Calculate metrics
        results = {}
        if self.mode == 'classification':
            results['accuracy'] = accuracy_score(y, y_pred)
            results['classification_report'] = classification_report(y, y_pred)
        else:
            results['rmse'] = np.sqrt(mean_squared_error(y, y_pred))
            results['mae'] = mean_absolute_error(y, y_pred)
            results['r2'] = r2_score(y, y_pred)
        
        # Get feature importance
        if hasattr(self.model, 'feature_importances_'):
            results['feature_importance'] = dict(zip(X.columns, self.model.feature_importances_))
        elif hasattr(self.model, 'coef_'):
            results['feature_importance'] = dict(zip(X.columns, np.abs(self.model.coef_)))
        
        return results
    
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

    def cross_validate(self, X, y, n_splits=5):
        """
        Perform k-fold cross-validation with feature importance stability analysis.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target values
            n_splits (int): Number of folds for cross validation
            
        Returns:
            dict: Cross-validation results including:
                - Mean and std of performance metrics
                - Feature importance stability score
                - Individual fold results
        """
        logger.info(f"Performing {n_splits}-fold cross validation")
        
        # Data validation
        if len(X) < n_splits * 2:  # Ensure at least 2 samples per fold
            raise ValueError(f"Insufficient data for {n_splits} folds. Need at least {n_splits * 2} samples, got {len(X)}")
        
        if X.isna().any().any():
            raise ValueError("Features contain NaN values. Please handle missing data before cross-validation.")
            
        if y.isna().any():
            raise ValueError("Target contains NaN values. Please handle missing data before cross-validation.")
            
        # Validate target variable for classification mode
        if self.mode == 'classification':
            unique_classes = y.nunique()
            if unique_classes < 2:
                raise ValueError(f"Classification requires at least 2 classes, got {unique_classes}")
            
            # Check if we have enough samples per class
            class_counts = y.value_counts()
            min_class_count = class_counts.min()
            if min_class_count < n_splits:
                logger.warning(f"Some classes have fewer samples than folds. Smallest class has {min_class_count} samples.")
        
        # Store feature names for prediction
        self.feature_names = X.columns.tolist()
        
        # Initialize k-fold cross validation
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=self.random_state)
        
        # Lists to store metrics for each fold
        fold_metrics = []
        feature_importance_list = []
        feature_ranks_list = []  # For stability calculation
        
        # Memory optimization: Pre-allocate arrays
        X_values = X.values
        y_values = y.values
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X_values), 1):
            logger.info(f"\nFold {fold}/{n_splits}")
            
            # Split data using numpy arrays for memory efficiency
            X_train, X_val = X_values[train_idx], X_values[val_idx]
            y_train, y_val = y_values[train_idx], y_values[val_idx]
            
            # Convert back to pandas for XGBoost (required for feature names)
            X_train_df = pd.DataFrame(X_train, columns=self.feature_names)
            X_val_df = pd.DataFrame(X_val, columns=self.feature_names)
            
            # Train model on this fold
            self.model.fit(X_train_df, y_train)
            
            # Store feature importance for this fold
            fold_importance = pd.Series(
                self.model.feature_importances_,
                index=self.feature_names
            ).sort_values(ascending=False)
            feature_importance_list.append(fold_importance)
            
            # Store feature ranks for stability calculation
            feature_ranks = pd.Series(
                range(len(self.feature_names)),
                index=fold_importance.index
            )
            feature_ranks_list.append(feature_ranks)
            
            # Free memory
            del X_train_df
            
            # Evaluate on validation set
            y_pred = self.model.predict(X_val_df)
            
            # Free more memory
            del X_val_df
            
            if self.mode == 'classification':
                # Classification metrics
                accuracy = accuracy_score(y_val, y_pred)
                report = classification_report(y_val, y_pred, output_dict=True)
                
                fold_metrics.append({
                    'fold': fold,
                    'accuracy': accuracy,
                    'classification_report': report
                })
                
                logger.info(f"Fold {fold} Accuracy: {accuracy:.4f}")
                
            else:  # regression mode
                # Regression metrics
                mse = mean_squared_error(y_val, y_pred)
                rmse = math.sqrt(mse)
                mae = mean_absolute_error(y_val, y_pred)
                r2 = r2_score(y_val, y_pred)
                
                fold_metrics.append({
                    'fold': fold,
                    'rmse': rmse,
                    'mae': mae,
                    'r2': r2
                })
                
                logger.info(f"Fold {fold} - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
        
        # Calculate average feature importance across folds
        self.feature_importance = pd.concat(feature_importance_list, axis=1).mean(axis=1).sort_values(ascending=False)
        
        # Calculate feature importance stability using Spearman correlation
        n_features = len(self.feature_names)
        stability_matrix = np.zeros((n_splits, n_splits))
        for i in range(n_splits):
            for j in range(i + 1, n_splits):
                corr = feature_ranks_list[i].corr(feature_ranks_list[j], method='spearman')
                stability_matrix[i, j] = corr
                stability_matrix[j, i] = corr
        
        # Average stability score (mean of upper triangle)
        stability_score = np.mean(stability_matrix[np.triu_indices(n_splits, k=1)])
        
        # Log feature importance stability
        logger.info(f"\nFeature Importance Stability Score: {stability_score:.4f}")
        if stability_score < 0.8:
            logger.warning("Feature importance stability is below target threshold (0.8)")
        
        # Log top features
        logger.info("\nTop 10 important features (averaged across folds):")
        top_features = self.feature_importance.head(10)
        for feature, importance in top_features.items():
            logger.info(f"  {feature}: {importance:.4f}")
        
        # Calculate aggregate metrics
        if self.mode == 'classification':
            accuracies = [m['accuracy'] for m in fold_metrics]
            mean_accuracy = np.mean(accuracies)
            std_accuracy = np.std(accuracies)
            
            logger.info(f"\nCross Validation Results:")
            logger.info(f"Mean Accuracy: {mean_accuracy:.4f} ± {std_accuracy:.4f}")
            
            # Check variance threshold
            if std_accuracy > 0.2 * mean_accuracy:  # > 20% of mean
                logger.warning("High variance between folds detected (> 20% of mean accuracy)")
            
            return {
                'fold_metrics': fold_metrics,
                'mean_accuracy': mean_accuracy,
                'std_accuracy': std_accuracy,
                'feature_importance': top_features.to_dict(),
                'feature_stability': stability_score
            }
            
        else:  # regression mode
            rmse_scores = [m['rmse'] for m in fold_metrics]
            mae_scores = [m['mae'] for m in fold_metrics]
            r2_scores = [m['r2'] for m in fold_metrics]
            
            mean_rmse = np.mean(rmse_scores)
            mean_mae = np.mean(mae_scores)
            mean_r2 = np.mean(r2_scores)
            
            std_rmse = np.std(rmse_scores)
            std_mae = np.std(mae_scores)
            std_r2 = np.std(r2_scores)
            
            logger.info(f"\nCross Validation Results:")
            logger.info(f"Mean RMSE: {mean_rmse:.4f} ± {std_rmse:.4f}")
            logger.info(f"Mean MAE: {mean_mae:.4f} ± {std_mae:.4f}")
            logger.info(f"Mean R²: {mean_r2:.4f} ± {std_r2:.4f}")
            
            # Check variance threshold
            if std_rmse > 0.2 * mean_rmse:  # > 20% of mean
                logger.warning("High RMSE variance between folds detected (> 20% of mean)")
            
            return {
                'fold_metrics': fold_metrics,
                'mean_rmse': mean_rmse,
                'mean_mae': mean_mae,
                'mean_r2': mean_r2,
                'std_rmse': std_rmse,
                'std_mae': std_mae,
                'std_r2': std_r2,
                'feature_importance': top_features.to_dict(),
                'feature_stability': stability_score
            }

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