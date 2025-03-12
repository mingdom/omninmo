"""
Data fetcher for stock data
"""

import os
import json
import random
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

from src.v2.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    """Class to fetch stock data from API or use sample data"""
    
    def __init__(self, cache_dir="cache"):
        """Initialize with cache directory"""
        self.cache_dir = cache_dir
        self.api_key = os.environ.get('FMP_API_KEY') or config.get('data.fmp.api_key')
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_data(self, ticker, period='5y', interval='1d', force_sample=False):
        """
        Fetch stock data for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)
            force_sample (bool): Force using sample data instead of API
            
        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")
        
        if os.path.exists(cache_file):
            logger.info(f"Loading cached data for {ticker}")
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        
        # If forcing sample data or no API key, use sample data
        if force_sample or not self.api_key:
            logger.info(f"Using sample data for {ticker}")
            return self._generate_sample_data(ticker, period, interval)
        
        # If we have an API key, try to fetch from API
        try:
            logger.info(f"Fetching data for {ticker} from API")
            df = self._fetch_from_api(ticker, period)
            
            if df is not None and not df.empty:
                # Save to cache
                df.to_csv(cache_file)
                return df
            else:
                logger.warning(f"No data returned from API for {ticker}, using sample data")
                return self._generate_sample_data(ticker, period, interval)
                
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            logger.info(f"Falling back to sample data for {ticker}")
            return self._generate_sample_data(ticker, period, interval)
    
    def _fetch_from_api(self, ticker, period='5y'):
        """Fetch data from Financial Modeling Prep API"""
        # Determine date range based on period
        end_date = datetime.now()
        
        if period.endswith('y'):
            years = int(period[:-1])
            start_date = end_date - timedelta(days=365 * years)
        elif period.endswith('m'):
            months = int(period[:-1])
            start_date = end_date - timedelta(days=30 * months)
        else:
            # Default to 1 year
            start_date = end_date - timedelta(days=365)
        
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # FMP API endpoint
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
        params = {
            'from': start_str,
            'to': end_str,
            'apikey': self.api_key
        }
        
        # Make request
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"API returned status code {response.status_code}")
            return None
        
        # Parse response
        data = response.json()
        
        if 'historical' not in data:
            logger.error(f"No historical data found for {ticker}")
            return None
        
        # Convert to DataFrame
        historical = data['historical']
        df = pd.DataFrame(historical)
        
        # Format DataFrame
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)  # Ascending date order
        
        # Rename columns to match expected format
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        return df
    
    def _generate_sample_data(self, ticker, period='5y', interval='1d'):
        """Generate sample stock data when API is unavailable"""
        # Get default price and volatility from config
        default_price = config.get(f'data.sample_data.default_prices.{ticker}', 100.0)
        default_volatility = config.get(f'data.sample_data.default_volatility.{ticker}', 0.02)
        
        # Determine number of days based on period
        if period.endswith('y'):
            days = int(period[:-1]) * 252  # Trading days in a year
        elif period.endswith('m'):
            days = int(period[:-1]) * 21   # Trading days in a month
        else:
            days = 252  # Default to 1 year
        
        # Generate dates
        end_date = datetime.now()
        dates = [end_date - timedelta(days=i) for i in range(days)]
        dates.reverse()  # Put in ascending order
        
        # Generate price data with random walk
        price = default_price
        prices = []
        
        for _ in dates:
            # Random daily return with slight upward bias
            daily_return = random.normalvariate(0.0002, default_volatility)
            price *= (1 + daily_return)
            prices.append(price)
        
        # Create DataFrame
        df = pd.DataFrame(index=dates)
        df.index = pd.DatetimeIndex(df.index)
        df['Close'] = prices
        
        # Generate other price columns based on Close
        df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.005, len(df)))
        df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + abs(np.random.normal(0, 0.005, len(df))))
        df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - abs(np.random.normal(0, 0.005, len(df))))
        df['Volume'] = np.random.normal(1000000, 200000, len(df))
        df['Volume'] = df['Volume'].clip(10000)  # Ensure volume is positive
        
        return df

if __name__ == "__main__":
    # Simple test
    fetcher = DataFetcher()
    data = fetcher.fetch_data('AAPL', period='1y', force_sample=True)
    print(data.head())
    print(f"Got {len(data)} rows of data for AAPL") 