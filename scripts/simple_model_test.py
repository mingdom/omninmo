#!/usr/bin/env python3
"""
Simple Model Test Script

This script tests the XGBoost model with a simple synthetic dataset.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.xgboost_predictor import XGBoostRatingPredictor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_data(n_samples=1000, n_features=20):
    """
    Generate synthetic data for testing.
    
    Args:
        n_samples (int): Number of samples to generate
        n_features (int): Number of features to generate
        
    Returns:
        tuple: (X, y) where X is a DataFrame of features and y is a Series of labels
    """
    logger.info(f"Generating synthetic dataset with {n_samples} samples and {n_features} features")
    
    # Generate random features
    X = pd.DataFrame(np.random.randn(n_samples, n_features))
    X.columns = [f'feature_{i}' for i in range(n_features)]
    
    # Generate target variable (5 classes)
    # We'll make it somewhat predictable based on the first few features
    y_score = 0.2 * X['feature_0'] + 0.3 * X['feature_1'] - 0.1 * X['feature_2'] + 0.4 * np.random.randn(n_samples)
    
    # Convert to rating categories
    def get_rating(score):
        if score > 0.8:
            return 'Strong Buy'
        elif score > 0.2:
            return 'Buy'
        elif score > -0.2:
            return 'Hold'
        elif score > -0.8:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    y = pd.Series([get_rating(score) for score in y_score])
    
    # Print class distribution
    logger.info(f"Class distribution:\n{y.value_counts()}")
    
    return X, y

def main():
    """Main function to test the XGBoost model."""
    print("Starting simple model test")
    
    # Generate synthetic data
    X, y = generate_synthetic_data()
    
    # Print more information about the data
    print(f"Data shape: {X.shape}")
    print(f"Feature names: {X.columns.tolist()[:5]}...")  # Show first 5 features
    print(f"Sample data:\n{X.head(3)}")  # Show first 3 rows
    print(f"Class distribution:\n{y.value_counts()}")
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"Training set shape: {X_train.shape}")
    print(f"Test set shape: {X_test.shape}")
    
    # Train XGBoost model
    print("\nTraining XGBoost model")
    xgb_model = XGBoostRatingPredictor()
    results = xgb_model.train(X_train, y_train)
    
    if results:
        print(f"Training accuracy: {results['accuracy']:.4f}")
        
        # Get top features
        top_features = xgb_model.get_feature_importance(top_n=10)
        print(f"\nTop 10 features:\n{top_features}")
        
        # Evaluate on test set
        test_results = xgb_model.evaluate(X_test, y_test)
        print(f"\nTest accuracy: {test_results['accuracy']:.4f}")
        
        # Print detailed classification report
        y_pred = xgb_model.model.predict(X_test)
        print(f"\nClassification report:\n{classification_report(y_test, y_pred)}")
        
        # Make a sample prediction
        sample_idx = np.random.randint(0, len(X_test))
        sample_features = X_test.iloc[[sample_idx]]
        true_label = y_test.iloc[sample_idx]
        
        prediction, confidence = xgb_model.predict(sample_features)
        print(f"\nSample prediction:")
        print(f"  True label: {true_label}")
        print(f"  Predicted label: {prediction}")
        print(f"  Confidence: {confidence:.4f}")
    else:
        print("Model training failed")
    
    print("\nSimple model test completed")

if __name__ == "__main__":
    main() 