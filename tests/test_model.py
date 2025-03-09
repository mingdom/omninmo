"""
Tests for the XGBoost model and training pipeline.
"""

import os
import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.models.xgboost_predictor import XGBoostRatingPredictor
from src.utils.feature_engineer import FeatureEngineer

def test_model_initialization(xgboost_model):
    """Test model initialization."""
    assert xgboost_model.model is not None
    assert xgboost_model.classes is None  # Should be None before training
    assert xgboost_model.feature_importance is None  # Should be None before training

def test_model_training(xgboost_model, sample_stock_data):
    """Test model training with sample data."""
    # Prepare features
    feature_engineer = FeatureEngineer()
    features = feature_engineer.calculate_indicators(sample_stock_data)
    
    # Prepare target (dummy classifications)
    y = pd.Series(np.random.randint(0, 5, size=len(features)), index=features.index)
    
    # Train model
    accuracy = xgboost_model.train(features, y)
    
    assert accuracy > 0  # Should have some accuracy
    assert xgboost_model.classes is not None
    assert xgboost_model.feature_importance is not None
    assert len(xgboost_model.feature_importance) == features.shape[1]

def test_model_prediction(xgboost_model, sample_stock_data):
    """Test model prediction."""
    # Prepare data
    feature_engineer = FeatureEngineer()
    features = feature_engineer.calculate_indicators(sample_stock_data)
    y = pd.Series(np.random.randint(0, 5, size=len(features)), index=features.index)
    
    # Train model
    xgboost_model.train(features, y)
    
    # Make prediction
    test_features = features.iloc[[0]]  # Use first row for prediction
    prediction, confidence = xgboost_model.predict(test_features)
    
    assert prediction in range(5)  # Should be 0-4
    assert 0 <= confidence <= 1  # Confidence should be between 0 and 1

def test_feature_importance(xgboost_model, sample_stock_data):
    """Test feature importance calculation."""
    # Prepare data
    feature_engineer = FeatureEngineer()
    features = feature_engineer.calculate_indicators(sample_stock_data)
    y = pd.Series(np.random.randint(0, 5, size=len(features)), index=features.index)
    
    # Train model
    xgboost_model.train(features, y)
    
    # Get feature importance
    importance = xgboost_model.get_feature_importance(top_n=5)
    
    assert importance is not None
    assert len(importance) == 5
    assert all(importance.index.isin(features.columns))
    assert (importance >= 0).all()  # Importance scores should be non-negative

def test_model_evaluation(xgboost_model, sample_stock_data):
    """Test model evaluation."""
    # Prepare data
    feature_engineer = FeatureEngineer()
    features = feature_engineer.calculate_indicators(sample_stock_data)
    y = pd.Series(np.random.randint(0, 5, size=len(features)), index=features.index)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)
    
    # Train model
    xgboost_model.train(X_train, y_train)
    
    # Evaluate model
    eval_results = xgboost_model.evaluate(X_test, y_test)
    
    assert eval_results is not None
    assert 'accuracy' in eval_results
    assert 'classification_report' in eval_results
    assert 0 <= eval_results['accuracy'] <= 1

def test_model_persistence(xgboost_model, sample_stock_data, test_data_dir):
    """Test model saving and loading."""
    # Prepare data
    feature_engineer = FeatureEngineer()
    features = feature_engineer.calculate_indicators(sample_stock_data)
    y = pd.Series(np.random.randint(0, 5, size=len(features)), index=features.index)
    
    # Train model
    xgboost_model.train(features, y)
    
    # Save model
    model_path = os.path.join(test_data_dir, 'test_model.pkl')
    save_success = xgboost_model.save(model_path)
    assert save_success
    
    # Load model
    loaded_model = XGBoostRatingPredictor.load(model_path)
    assert loaded_model is not None
    
    # Compare predictions
    test_features = features.iloc[[0]]
    pred1, conf1 = xgboost_model.predict(test_features)
    pred2, conf2 = loaded_model.predict(test_features)
    
    assert pred1 == pred2
    assert conf1 == conf2

def test_model_with_missing_data(xgboost_model):
    """Test model handling of missing data."""
    # Create data with missing values
    data = pd.DataFrame({
        'feature1': [1, 2, np.nan, 4, 5],
        'feature2': [10, np.nan, 30, 40, 50],
        'feature3': [100, 200, 300, 400, 500]
    })
    y = pd.Series([0, 1, 2, 3, 4])
    
    # Training should fail with missing data
    with pytest.raises(Exception):
        xgboost_model.train(data, y)

def test_model_with_invalid_features(xgboost_model):
    """Test model handling of invalid features."""
    # Create invalid data (non-numeric)
    data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': ['a', 'b', 'c', 'd', 'e'],  # Non-numeric feature
        'feature3': [100, 200, 300, 400, 500]
    })
    y = pd.Series([0, 1, 2, 3, 4])
    
    # Training should fail with non-numeric data
    with pytest.raises(Exception):
        xgboost_model.train(data, y) 