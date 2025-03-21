"""
XGBoost model for stock prediction
"""

import gc
import logging
import os
import pickle
import random

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold

from src.v2.config import config

logger = logging.getLogger(__name__)


class Predictor:
    """Stock prediction model using XGBoost"""

    def __init__(self):
        """
        Initialize the predictor
        """
        # Load XGBoost parameters from config
        params = config.get("model.xgboost", {})
        self.learning_rate = params.get("learning_rate", 0.1)
        self.max_depth = params.get("max_depth", 6)
        self.n_estimators = params.get("n_estimators", 100)

        # Use truly random seed
        self.random_state = params.get("random_state", random.randint(1, 1000000))

        # Initialize model
        self.model = xgb.XGBRegressor(
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            objective="reg:squarederror",
        )

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
        y = y.astype(np.float32)

        # Create new model instance with truly random state
        self.model = xgb.XGBRegressor(
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            n_estimators=self.n_estimators,
            random_state=random.randint(1, 1000000),
            objective="reg:squarederror",
        )

        # Train the model
        self.model.fit(X, y)

        # Get predictions
        y_pred = self.model.predict(X)

        # Calculate metrics
        results = {}
        results["rmse"] = np.sqrt(mean_squared_error(y, y_pred))
        results["mae"] = mean_absolute_error(y, y_pred)
        results["r2"] = r2_score(y, y_pred)

        # Get feature importance
        if hasattr(self.model, "feature_importances_"):
            results["feature_importance"] = dict(
                zip(X.columns, self.model.feature_importances_)
            )
        elif hasattr(self.model, "coef_"):
            results["feature_importance"] = dict(
                zip(X.columns, np.abs(self.model.coef_))
            )

        return results

    def predict(self, features):
        """
        Make prediction for new data

        Args:
            features (pandas.DataFrame): Features for prediction

        Returns:
            tuple: (predicted_return, score, rating)
                - predicted_return (float): Predicted return value
                - score (float): Normalized score between 0 and 1
                - rating (str): Rating category (Strong Buy, Buy, Hold, Sell, Strong Sell)
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None

        try:
            # Make a copy of features to avoid modifying the original
            features = features.copy()

            # Remove label column if it exists (not needed for prediction)
            if "label" in features.columns:
                features = features.drop("label", axis=1)

            # Ensure all features are numeric
            for col in features.columns:
                if features[col].dtype == "object":
                    logger.warning(f"Converting non-numeric column {col} to numeric")
                    features.loc[:, col] = pd.to_numeric(features[col], errors="coerce")

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
                    logger.warning(
                        f"Removing extra features not used in training: {extra_features}"
                    )
                    features = features[self.feature_names]

                # Ensure features are in the same order as during training
                features = features[self.feature_names]

            # Make prediction
            predicted_return = self.model.predict(features)[0]

            # Calculate normalized score (0-1)
            score = self.normalize_return(predicted_return)

            # Get rating based on thresholds
            rating = self.get_rating(predicted_return)

            return predicted_return, score, rating

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
        params = config.get("model.normalization", {})
        method = params.get("method", "sigmoid")

        if method == "sigmoid":
            # Apply sigmoid normalization
            k = params.get("sigmoid_k", 10)
            return 1 / (1 + np.exp(-k * return_value))

        elif method == "tanh":
            # Apply tanh normalization and rescale from (-1,1) to (0,1)
            k = params.get("tanh_k", 10)  # Use same default as sigmoid for consistency
            return (np.tanh(k * return_value) + 1) / 2

        elif method == "linear":
            # Apply linear normalization
            min_val = params.get("linear_min", -0.1)
            max_val = params.get("linear_max", 0.1)

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
        thresholds = config.get("model.training.rating_thresholds", {})

        strong_buy = thresholds.get("strong_buy", 0.10)  # Default to 10%
        buy = thresholds.get("buy", 0.05)  # Default to 5%
        hold = thresholds.get("hold", -0.05)  # Default to -5%
        sell = thresholds.get("sell", -0.10)  # Default to -10%
        strong_sell = thresholds.get("strong_sell", -0.20)  # Default to -20%

        if return_value > strong_buy:
            return "Strong Buy"
        elif return_value > buy:
            return "Buy"
        elif return_value > hold:
            return "Hold"
        elif return_value > sell:
            return "Sell"
        else:
            return "Strong Sell"

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
            importance_df = pd.DataFrame(
                {
                    "feature": self.feature_names,
                    "importance": self.model.feature_importances_,
                }
            )

            # Sort by importance
            importance_df = importance_df.sort_values("importance", ascending=False)

            # Calculate percentage and cumulative percentage
            total_importance = importance_df["importance"].sum()
            importance_df["importance_pct"] = (
                importance_df["importance"] / total_importance * 100
            )
            importance_df["cumulative_pct"] = importance_df["importance_pct"].cumsum()

            # Round numeric columns for readability
            importance_df["importance"] = importance_df["importance"].round(4)
            importance_df["importance_pct"] = importance_df["importance_pct"].round(2)
            importance_df["cumulative_pct"] = importance_df["cumulative_pct"].round(2)

            # Log top features
            logger.info("\nTop 10 Most Important Features:")
            for _, row in importance_df.head(10).iterrows():
                logger.info(
                    f"{row['feature']}: {row['importance_pct']:.2f}% (cumulative: {row['cumulative_pct']:.2f}%)"
                )

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
        with open(filepath, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "feature_importance": self.feature_importance,
                    "feature_names": self.feature_names,
                },
                f,
            )

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
            with open(filepath, "rb") as f:
                data = pickle.load(f)

            # Create new instance
            instance = cls()

            # Set attributes
            instance.model = data["model"]
            instance.feature_importance = data["feature_importance"]
            instance.feature_names = data.get("feature_names")

            logger.info(f"Model loaded from {filepath}")
            return instance

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None

    def cross_validate(self, X, y, n_splits=5, shuffle=True, random_state=None):
        """
        Perform k-fold cross-validation

        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target values
            n_splits (int): Number of folds
            shuffle (bool): Whether to shuffle data before splitting
            random_state (int): Random seed for reproducibility

        Returns:
            dict: Cross-validation results
        """
        logger.info(f"Performing {n_splits}-fold cross-validation...")

        # Validate inputs
        if len(X) != len(y):
            raise ValueError(
                f"X and y must have same length. Got X: {len(X)}, y: {len(y)}"
            )

        if X.isna().any().any():
            raise ValueError(
                "Features contain NaN values. Please handle missing data before cross-validation."
            )

        if y.isna().any():
            raise ValueError(
                "Target contains NaN values. Please handle missing data before cross-validation."
            )

        # Store feature names for later use
        self.feature_names = X.columns.tolist()

        # Create KFold object
        kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)

        # Initialize metrics storage
        fold_metrics = []
        feature_importances = []

        # Perform cross-validation
        for fold, (train_idx, test_idx) in enumerate(kf.split(X)):
            logger.info(f"Training fold {fold + 1}/{n_splits}...")

            # Split data
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Create and train model
            model = xgb.XGBRegressor(
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                objective="reg:squarederror",
            )

            # Train model
            model.fit(X_train, y_train)

            # Make predictions
            y_pred = model.predict(X_test)

            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Store metrics
            fold_metrics.append({"fold": fold + 1, "rmse": rmse, "mae": mae, "r2": r2})

            # Store feature importance
            if hasattr(model, "feature_importances_"):
                fold_importance = pd.DataFrame(
                    {"feature": X.columns, "importance": model.feature_importances_}
                )
                feature_importances.append(fold_importance)

            # Log metrics
            logger.info(
                f"Fold {fold + 1} metrics: RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}"
            )

            # Clean up to free memory
            del model, X_train, X_test, y_train, y_test, y_pred
            gc.collect()

        # Calculate feature importance stability
        if feature_importances:
            # Combine all fold importances
            all_importances = pd.concat(feature_importances)

            # Calculate mean importance by feature
            mean_importance = (
                all_importances.groupby("feature")["importance"].mean().reset_index()
            )
            mean_importance = mean_importance.sort_values("importance", ascending=False)

            # Calculate stability score (coefficient of variation)
            importance_stats = (
                all_importances.groupby("feature")["importance"]
                .agg(["mean", "std"])
                .reset_index()
            )
            importance_stats["cv"] = importance_stats["std"] / importance_stats["mean"]
            mean_cv = importance_stats["cv"].mean()
            stability_score = 1 - min(
                mean_cv, 1
            )  # Higher is better (1 = perfect stability)

            # Store top features
            top_features = mean_importance.head(20)
            self.feature_importance = list(
                zip(top_features["feature"], top_features["importance"])
            )
        else:
            stability_score = 0
            top_features = pd.DataFrame()

        # Calculate aggregate metrics
        rmses = [m["rmse"] for m in fold_metrics]
        maes = [m["mae"] for m in fold_metrics]
        r2s = [m["r2"] for m in fold_metrics]

        mean_rmse = np.mean(rmses)
        mean_mae = np.mean(maes)
        mean_r2 = np.mean(r2s)

        std_rmse = np.std(rmses)
        std_mae = np.std(maes)
        std_r2 = np.std(r2s)

        logger.info("\nCross Validation Results:")
        logger.info(f"Mean RMSE: {mean_rmse:.4f} ± {std_rmse:.4f}")
        logger.info(f"Mean MAE: {mean_mae:.4f} ± {std_mae:.4f}")
        logger.info(f"Mean R²: {mean_r2:.4f} ± {std_r2:.4f}")

        # Check variance threshold
        if std_rmse > 0.2 * mean_rmse:  # > 20% of mean
            logger.warning("High variance between folds detected (> 20% of mean RMSE)")

        return {
            "fold_metrics": fold_metrics,
            "mean_rmse": mean_rmse,
            "mean_mae": mean_mae,
            "mean_r2": mean_r2,
            "std_rmse": std_rmse,
            "std_mae": std_mae,
            "std_r2": std_r2,
            "feature_importance": top_features.to_dict(),
            "feature_stability": stability_score,
        }


if __name__ == "__main__":
    # Simple test

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Test model creation
    model = Predictor()
    print("Created model")

    # Test loading
    if os.path.exists("models/test_model.pkl"):
        loaded = Predictor.load("models/test_model.pkl")
        if loaded:
            print("Successfully loaded existing model")
