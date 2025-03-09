"""
Pytest configuration and fixtures.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.fmp_data_fetcher import FMPDataFetcher
from src.models.xgboost_predictor import XGBoostRatingPredictor

@pytest.fixture
def test_data_dir():
    """Create and return a temporary test data directory."""
    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(test_dir, exist_ok=True)
    return test_dir

@pytest.fixture
def cache_dir(test_data_dir):
    """Create and return a temporary cache directory."""
    cache_dir = os.path.join(test_data_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

@pytest.fixture
def sample_stock_data():
    """Generate sample stock data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, 100),
        'High': np.random.uniform(150, 250, 100),
        'Low': np.random.uniform(50, 150, 100),
        'Close': np.random.uniform(100, 200, 100),
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    return data

@pytest.fixture
def fmp_data_fetcher(cache_dir):
    """Create an FMPDataFetcher instance for testing."""
    return FMPDataFetcher(cache_dir=cache_dir)

@pytest.fixture
def xgboost_model():
    """Create an XGBoostRatingPredictor instance for testing."""
    return XGBoostRatingPredictor() 