"""
Tests for the FMP API data fetcher.
"""

import os
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.data.fmp_data_fetcher import FMPDataFetcher

def test_fmp_data_fetcher_initialization(cache_dir):
    """Test FMPDataFetcher initialization."""
    fetcher = FMPDataFetcher(cache_dir=cache_dir)
    assert fetcher.cache_dir == cache_dir
    assert fetcher.api_key is not None

def test_fetch_single_ticker_data(fmp_data_fetcher):
    """Test fetching data for a single ticker."""
    ticker = "AAPL"
    period = "1mo"
    data = fmp_data_fetcher.fetch_data(ticker, period=period)
    
    assert data is not None
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    assert data.index.name == 'Date'

def test_fetch_data_with_invalid_ticker(fmp_data_fetcher):
    """Test fetching data with an invalid ticker symbol."""
    ticker = "INVALID_TICKER"
    period = "1mo"
    data = fmp_data_fetcher.fetch_data(ticker, period=period)
    
    # Should return sample data for invalid ticker
    assert data is not None
    assert isinstance(data, pd.DataFrame)
    assert not data.empty

def test_fetch_multiple_tickers(fmp_data_fetcher):
    """Test fetching data for multiple tickers."""
    tickers = ["AAPL", "MSFT", "GOOGL"]
    period = "1mo"
    data_dict = fmp_data_fetcher.fetch_multiple(tickers, period=period)
    
    assert isinstance(data_dict, dict)
    assert len(data_dict) == len(tickers)
    for ticker in tickers:
        assert ticker in data_dict
        assert isinstance(data_dict[ticker], pd.DataFrame)
        assert not data_dict[ticker].empty

def test_cache_mechanism(cache_dir):
    """Test the cache mechanism."""
    fetcher = FMPDataFetcher(cache_dir=cache_dir)
    ticker = "AAPL"
    period = "1mo"
    
    # First fetch (should create cache)
    data1 = fetcher.fetch_data(ticker, period=period)
    assert data1 is not None
    
    # Second fetch (should use cache)
    with patch('requests.get') as mock_get:
        data2 = fetcher.fetch_data(ticker, period=period)
        assert not mock_get.called  # Should not make API call
        pd.testing.assert_frame_equal(data1, data2)

def test_sample_data_generation(fmp_data_fetcher):
    """Test sample data generation."""
    ticker = "AAPL"
    period = "1mo"
    data = fmp_data_fetcher._generate_sample_data(ticker, period)
    
    assert isinstance(data, pd.DataFrame)
    assert not data.empty
    assert all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    assert data.index.name == 'Date'
    
    # Test price consistency
    assert all(data['High'] >= data['Open'])
    assert all(data['High'] >= data['Close'])
    assert all(data['Low'] <= data['Open'])
    assert all(data['Low'] <= data['Close'])

@pytest.mark.parametrize("period,expected_days", [
    ("1d", 1),
    ("5d", 5),
    ("1mo", 30),
    ("3mo", 90),
    ("1y", 365),
])
def test_period_conversion(fmp_data_fetcher, period, expected_days):
    """Test period to date conversion."""
    from_date, to_date = fmp_data_fetcher._convert_period_to_dates(period)
    
    from_date = datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.strptime(to_date, '%Y-%m-%d')
    
    delta = to_date - from_date
    assert abs(delta.days - expected_days) <= 1  # Allow 1 day difference due to month lengths

def test_error_handling(fmp_data_fetcher):
    """Test error handling in data fetching."""
    with patch('requests.get') as mock_get:
        # Simulate network error
        mock_get.side_effect = Exception("Network error")
        data = fmp_data_fetcher.fetch_data("AAPL", period="1mo")
        
        # Should return sample data on error
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert not data.empty

def test_api_rate_limiting(fmp_data_fetcher):
    """Test API rate limiting handling."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    period = "1mo"
    
    # Fetch multiple tickers in quick succession
    data_dict = fmp_data_fetcher.fetch_multiple(tickers, period=period)
    
    assert isinstance(data_dict, dict)
    assert len(data_dict) == len(tickers)
    for ticker in tickers:
        assert ticker in data_dict
        assert isinstance(data_dict[ticker], pd.DataFrame)
        assert not data_dict[ticker].empty 