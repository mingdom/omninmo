"""
Stock data fetcher module for retrieving historical stock data using Financial Modeling Prep (FMP) API.
"""

import pandas as pd
import requests
import logging
import os
import time
import random
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, using environment variables as is")

# Get API key from environment variables
FMP_API_KEY = os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    logger.warning("FMP_API_KEY not found in environment variables. API calls will fail.")

class FMPDataFetcher:
    """
    Class for fetching historical stock data using Financial Modeling Prep API.
    """
    
    def __init__(self, api_key=None, cache_dir=None):
        """
        Initialize the FMPDataFetcher.
        
        Args:
            api_key (str, optional): FMP API key. If None, uses the one from environment variables.
            cache_dir (str, optional): Directory to cache stock data. If None, no caching is used.
        """
        self.api_key = api_key or FMP_API_KEY
        self.cache_dir = cache_dir
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_data(self, ticker, period='1y', interval='1d', max_retries=3, retry_delay=2, force_sample=False):
        """
        Fetch historical stock data for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period to fetch data for (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval (str): Data interval (e.g., '1d', '1wk', '1mo')
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            force_sample (bool): Force the use of sample data even if real data is available
        
        Returns:
            pandas.DataFrame: DataFrame containing historical stock data
        """
        # If force_sample is True, skip API calls and use sample data
        if force_sample:
            logger.info(f"Forcing sample data for {ticker}")
            from src.data.stock_data_fetcher import StockDataFetcher
            sample_generator = StockDataFetcher()
            return sample_generator._generate_sample_data(ticker, period, interval)
        
        try:
            logger.info(f"Fetching data for {ticker} with period={period}, interval={interval}")
            
            # Check cache if enabled
            if self.cache_dir:
                cache_file = os.path.join(self.cache_dir, f"fmp_{ticker}_{period}_{interval}.csv")
                if os.path.exists(cache_file):
                    # Check if cache is recent (less than 1 day old)
                    if datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file)) < timedelta(days=1):
                        logger.info(f"Loading {ticker} data from cache")
                        try:
                            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
                        except Exception as e:
                            logger.warning(f"Error reading cache file: {e}. Will fetch fresh data.")
            
            # Convert period to FMP API parameters
            from_date, to_date = self._convert_period_to_dates(period)
            
            # Fetch data from FMP API with retries
            data = None
            for attempt in range(max_retries):
                try:
                    # Add a random delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Determine which endpoint to use based on interval
                    if interval == '1d':
                        endpoint = f"/historical-price-full/{ticker}"
                        params = {
                            'from': from_date,
                            'to': to_date,
                            'apikey': self.api_key
                        }
                    elif interval == '1wk':
                        endpoint = f"/historical-price-full/{ticker}"
                        params = {
                            'from': from_date,
                            'to': to_date,
                            'timeseries': 7,  # Weekly data
                            'apikey': self.api_key
                        }
                    elif interval == '1mo':
                        endpoint = f"/historical-price-full/{ticker}"
                        params = {
                            'from': from_date,
                            'to': to_date,
                            'timeseries': 30,  # Monthly data
                            'apikey': self.api_key
                        }
                    else:
                        # Default to daily data
                        endpoint = f"/historical-price-full/{ticker}"
                        params = {
                            'from': from_date,
                            'to': to_date,
                            'apikey': self.api_key
                        }
                    
                    # Make the request
                    url = f"{self.base_url}{endpoint}"
                    logger.info(f"Making request to {url} with params: {params}")
                    
                    response = requests.get(url, params=params, timeout=20)
                    
                    # Check if response is successful
                    if response.status_code != 200:
                        logger.warning(f"Attempt {attempt+1}/{max_retries}: HTTP error {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay + attempt)
                        continue
                    
                    # Parse response
                    response_data = response.json()
                    
                    # Check if response contains historical data
                    if 'historical' not in response_data or not response_data['historical']:
                        logger.warning(f"Attempt {attempt+1}/{max_retries}: No historical data found for {ticker}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay + attempt)
                        continue
                    
                    # Convert to DataFrame
                    historical_data = response_data['historical']
                    df = pd.DataFrame(historical_data)
                    
                    # Rename columns to match yfinance format
                    df = df.rename(columns={
                        'date': 'Date',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                    
                    # Set date as index
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                    
                    # Sort by date (newest first to match yfinance)
                    df = df.sort_index(ascending=False)
                    
                    # Select only the columns we need
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                    
                    if not df.empty:
                        data = df
                        break
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Error fetching {ticker}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay + attempt)
            
            # If we still don't have data, use sample data
            if data is None or data.empty:
                logger.warning(f"No data available for {ticker} after {max_retries} attempts, using sample data")
                from src.data.stock_data_fetcher import StockDataFetcher
                sample_generator = StockDataFetcher()
                return sample_generator._generate_sample_data(ticker, period, interval)
            
            # Save to cache if enabled and we have data
            if self.cache_dir and data is not None and not data.empty:
                try:
                    data.to_csv(os.path.join(self.cache_dir, f"fmp_{ticker}_{period}_{interval}.csv"))
                except Exception as e:
                    logger.warning(f"Error saving to cache: {e}")
            
            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            # Return sample data when any error occurs
            logger.info(f"Using sample data for {ticker} due to error")
            from src.data.stock_data_fetcher import StockDataFetcher
            sample_generator = StockDataFetcher()
            return sample_generator._generate_sample_data(ticker, period, interval)
    
    def _convert_period_to_dates(self, period):
        """
        Convert period string to from_date and to_date for FMP API.
        
        Args:
            period (str): Period string (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', '5y')
            
        Returns:
            tuple: (from_date, to_date) in YYYY-MM-DD format
        """
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        if period == '1d':
            from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif period == '5d':
            from_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        elif period == '1mo':
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif period == '3mo':
            from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        elif period == '6mo':
            from_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        elif period == '1y':
            from_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        elif period == '2y':
            from_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        elif period == '5y':
            from_date = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        elif period == '10y':
            from_date = (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d')
        elif period == 'ytd':
            from_date = datetime(datetime.now().year, 1, 1).strftime('%Y-%m-%d')
        elif period == 'max':
            from_date = '1970-01-01'
        else:
            # Default to 1 year
            from_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        return from_date, to_date
    
    def fetch_multiple(self, tickers, period='1y', interval='1d', force_sample=False):
        """
        Fetch historical data for multiple tickers.
        
        Args:
            tickers (list): List of ticker symbols
            period (str): Time period to fetch data for
            interval (str): Data interval
            force_sample (bool): Force the use of sample data
        
        Returns:
            dict: Dictionary mapping ticker symbols to DataFrames
        """
        result = {}
        for ticker in tickers:
            try:
                data = self.fetch_data(ticker, period, interval, force_sample=force_sample)
                if data is not None:
                    result[ticker] = data
            except Exception as e:
                logger.error(f"Error in fetch_multiple for {ticker}: {e}")
                # Generate sample data for this ticker
                from src.data.stock_data_fetcher import StockDataFetcher
                sample_generator = StockDataFetcher()
                result[ticker] = sample_generator._generate_sample_data(ticker, period, interval)
        
        return result 