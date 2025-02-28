"""
Stock rating predictor module for omninmo.
Trains a machine learning model and makes predictions.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os


class StockRatingPredictor:
    """Class for predicting stock ratings."""

    def __init__(self, model_path=None):
        """
        Initialize the StockRatingPredictor.

        Args:
            model_path (str, optional): Path to a saved model file. If provided, the model will be loaded from this file.
        """
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.rating_thresholds = {
            "Strong Buy": 0.8,
            "Buy": 0.6,
            "Hold": 0.4,
            "Sell": 0.2,
            "Strong Sell": 0.0,
        }

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def prepare_target(self, df, forward_days=20):
        """
        Prepare target variable for training.
        The target is the future return after forward_days.

        Args:
            df (pd.DataFrame): DataFrame with stock data
            forward_days (int): Number of days to look ahead for returns

        Returns:
            pd.Series: Target variable (future returns)
        """
        # Calculate future returns
        df["future_return"] = df["Close"].shift(-forward_days) / df["Close"] - 1

        # Remove rows with NaN future returns
        df = df.dropna(subset=["future_return"])

        return df["future_return"]

    def train(self, X, y, feature_names=None):
        """
        Train the model.

        Args:
            X (np.ndarray): Feature matrix
            y (np.ndarray): Target variable
            feature_names (list, optional): List of feature names

        Returns:
            self: The trained model
        """
        if X is None or y is None or len(X) == 0 or len(y) == 0:
            raise ValueError("Cannot train model with empty data")

        # Store feature names
        self.feature_names = feature_names

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train a Random Forest classifier
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )

        # Convert continuous returns to discrete classes for classification
        y_classes = self._returns_to_classes(y)

        # Train the model
        self.model.fit(X_scaled, y_classes)

        return self

    def predict(self, X):
        """
        Make predictions.

        Args:
            X (np.ndarray): Feature matrix

        Returns:
            list: Predicted ratings
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        if X is None or len(X) == 0:
            raise ValueError("Cannot predict with empty data")

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Get probability predictions
        probas = self.model.predict_proba(X_scaled)

        # Convert probabilities to ratings
        ratings = self._probas_to_ratings(probas)

        return ratings

    def get_feature_importance(self):
        """
        Get feature importance.

        Returns:
            pd.DataFrame: DataFrame with feature importance
        """
        if self.model is None or self.feature_names is None:
            raise ValueError("Model not trained or feature names not available")

        # Get feature importance from the model
        importance = self.model.feature_importances_

        # Create a DataFrame with feature names and importance
        importance_df = pd.DataFrame(
            {"feature": self.feature_names, "importance": importance}
        )

        # Sort by importance
        importance_df = importance_df.sort_values("importance", ascending=False)

        return importance_df

    def save_model(self, model_path):
        """
        Save the model to a file.

        Args:
            model_path (str): Path to save the model
        """
        if self.model is None:
            raise ValueError("Model not trained")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save model, scaler, and feature names
        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
            },
            model_path,
        )

    def load_model(self, model_path):
        """
        Load the model from a file.

        Args:
            model_path (str): Path to the saved model
        """
        if not os.path.exists(model_path):
            raise ValueError(f"Model file not found: {model_path}")

        # Load model, scaler, and feature names
        model_data = joblib.load(model_path)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]

    def _returns_to_classes(self, returns):
        """
        Convert continuous returns to discrete classes.

        Args:
            returns (np.ndarray): Array of returns

        Returns:
            np.ndarray: Array of classes
        """
        # Define thresholds for classification
        thresholds = [-0.1, -0.05, 0.05, 0.1]

        # Initialize classes
        classes = np.zeros(len(returns), dtype=int)

        # Assign classes based on thresholds
        for i in range(len(thresholds)):
            if i == 0:
                classes[returns <= thresholds[i]] = 0  # Strong Sell
            elif i == len(thresholds) - 1:
                classes[returns > thresholds[i]] = 4  # Strong Buy
            else:
                classes[(returns > thresholds[i - 1]) & (returns <= thresholds[i])] = i

        return classes

    def _probas_to_ratings(self, probas):
        """
        Convert class probabilities to ratings.

        Args:
            probas (np.ndarray): Array of class probabilities

        Returns:
            list: List of ratings
        """
        # Get the weighted average probability
        weighted_probas = np.sum(probas * np.array([0, 0.25, 0.5, 0.75, 1]), axis=1)

        # Convert to ratings
        ratings = []
        for p in weighted_probas:
            for rating, threshold in self.rating_thresholds.items():
                if p >= threshold:
                    ratings.append(rating)
                    break

        return ratings
