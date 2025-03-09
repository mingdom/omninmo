"""
Integration tests for the complete pipeline.
"""

import os
import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.data.fmp_data_fetcher import FMPDataFetcher
from src.utils.feature_engineer import FeatureEngineer
from src.models.xgboost_predictor import XGBoostRatingPredictor

def test_complete_pipeline(test_data_dir, cache_dir):
    """Test the complete pipeline from data fetching to prediction."""
    # Initialize components
    data_fetcher = FMPDataFetcher(cache_dir=cache_dir)
    feature_engineer = FeatureEngineer()
    model = XGBoostRatingPredictor()
    
    # 1. Fetch training data
    tickers = ["AAPL", "MSFT", "GOOGL"]
    period = "1y"
    ticker_data = {}
    
    for ticker in tickers:
        data = data_fetcher.fetch_data(ticker, period=period)
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        ticker_data[ticker] = data
    
    # 2. Prepare features and targets
    all_features = []
    all_targets = []
    
    for ticker, data in ticker_data.items():
        # Calculate features
        features = feature_engineer.calculate_indicators(data)
        assert features is not None
        assert not features.empty
        
        # Create dummy targets
        targets = pd.Series(data['Close'].pct_change().apply(
            lambda x: 2 if x > 0.05 else (1 if x > 0.02 else (0 if x > -0.02 else (0 if x > -0.05 else 0)))
        ))
        targets = targets.dropna()
        
        # Align features and targets
        valid_idx = features.index.intersection(targets.index)
        all_features.append(features.loc[valid_idx])
        all_targets.append(targets.loc[valid_idx])
    
    # Combine all data
    X = pd.concat(all_features, axis=0)
    y = pd.concat(all_targets, axis=0)
    
    # 3. Train model
    accuracy = model.train(X, y)
    assert accuracy > 0
    
    # 4. Save and load model
    model_path = os.path.join(test_data_dir, 'integration_test_model.pkl')
    save_success = model.save(model_path)
    assert save_success
    
    loaded_model = XGBoostRatingPredictor.load(model_path)
    assert loaded_model is not None
    
    # 5. Make predictions on new data
    test_ticker = "AAPL"
    test_period = "1mo"
    
    # Fetch new data
    new_data = data_fetcher.fetch_data(test_ticker, period=test_period)
    assert new_data is not None
    
    # Calculate features
    new_features = feature_engineer.calculate_indicators(new_data)
    assert new_features is not None
    
    # Make prediction
    latest_features = new_features.iloc[[-1]]
    prediction, confidence = model.predict(latest_features)
    
    # Verify prediction
    assert prediction in range(5)  # Should be 0-4
    assert 0 <= confidence <= 1

def test_pipeline_with_sample_data(test_data_dir):
    """Test the pipeline using sample data."""
    # Initialize components
    data_fetcher = FMPDataFetcher(cache_dir=None)  # No cache to force sample data
    feature_engineer = FeatureEngineer()
    model = XGBoostRatingPredictor()
    
    # Generate sample data
    ticker = "SAMPLE"
    period = "1y"
    data = data_fetcher._generate_sample_data(ticker, period)
    
    # Calculate features
    features = feature_engineer.calculate_indicators(data)
    
    # Create dummy targets
    targets = pd.Series(data['Close'].pct_change().apply(
        lambda x: 2 if x > 0.05 else (1 if x > 0.02 else (0 if x > -0.02 else (0 if x > -0.05 else 0)))
    ))
    targets = targets.dropna()
    
    # Align features and targets
    valid_idx = features.index.intersection(targets.index)
    features = features.loc[valid_idx]
    targets = targets.loc[valid_idx]
    
    # Train model
    accuracy = model.train(features, targets)
    assert accuracy > 0
    
    # Make prediction
    latest_features = features.iloc[[-1]]
    prediction, confidence = model.predict(latest_features)
    
    assert prediction in range(5)
    assert 0 <= confidence <= 1

def test_pipeline_error_recovery(test_data_dir, cache_dir):
    """Test pipeline recovery from errors."""
    # Initialize components with invalid cache directory
    invalid_cache_dir = os.path.join(test_data_dir, "nonexistent_dir", "another_nonexistent_dir")
    data_fetcher = FMPDataFetcher(cache_dir=invalid_cache_dir)
    feature_engineer = FeatureEngineer()
    model = XGBoostRatingPredictor()
    
    # Attempt to fetch data (should fall back to sample data)
    data = data_fetcher.fetch_data("AAPL", period="1mo")
    assert data is not None  # Should get sample data
    
    # Calculate features
    features = feature_engineer.calculate_indicators(data)
    assert features is not None
    
    # Create dummy targets
    targets = pd.Series(data['Close'].pct_change().apply(
        lambda x: 2 if x > 0.05 else (1 if x > 0.02 else (0 if x > -0.02 else (0 if x > -0.05 else 0)))
    ))
    targets = targets.dropna()
    
    # Train model
    accuracy = model.train(features.loc[targets.index], targets)
    assert accuracy > 0 