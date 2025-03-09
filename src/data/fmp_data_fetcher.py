"""
Stock data fetcher module for retrieving historical stock data using Financial Modeling Prep (FMP) API.
"""

import pandas as pd
import requests
import logging
import logging.handlers
import os
import time
import random
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

# Setup logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set default level to DEBUG

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Setup file handler
file_handler = logging.handlers.RotatingFileHandler(
    'logs/fmp_data_fetcher.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

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

# Default starting prices for sample data
DEFAULT_PRICES = {
    'AAPL': 175.0,
    'MSFT': 380.0,
    'AMZN': 180.0,
    'GOOGL': 150.0,
    'META': 480.0,
    'TSLA': 180.0,
    'NVDA': 800.0,
    'JPM': 190.0,
    'V': 280.0,
    'JNJ': 150.0,
    'WMT': 60.0,
    'PG': 160.0,
    'DIS': 110.0,
    'NFLX': 600.0,
    'INTC': 40.0
}

# Default volatility for sample data
DEFAULT_VOLATILITY = {
    'AAPL': 0.015,
    'MSFT': 0.018,
    'AMZN': 0.022,
    'GOOGL': 0.020,
    'META': 0.025,
    'TSLA': 0.035,
    'NVDA': 0.030,
    'JPM': 0.015,
    'V': 0.012,
    'JNJ': 0.010,
    'WMT': 0.008,
    'PG': 0.007,
    'DIS': 0.018,
    'NFLX': 0.028,
    'INTC': 0.020
}

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
            
        logger.debug(f"FMPDataFetcher initialized with API key: {'set' if self.api_key else 'not set'}")
    
    def get_data(self, ticker, start_date, end_date):
        """
        Get historical stock data for a given ticker and date range.
        
        Args:
            ticker (str): Stock ticker symbol
            start_date (datetime): Start date for the data
            end_date (datetime): End date for the data
            
        Returns:
            pandas.DataFrame: DataFrame containing historical stock data
        """
        logger.debug(f"Getting data for {ticker} from {start_date} to {end_date}")
        
        # Convert dates to string format for API
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        # Calculate period based on date range
        days_diff = (end_date - start_date).days
        if days_diff <= 30:
            period = '1mo'
        elif days_diff <= 90:
            period = '3mo'
        elif days_diff <= 365:
            period = '1y'
        elif days_diff <= 730:
            period = '2y'
        elif days_diff <= 1825:
            period = '5y'
        else:
            period = '10y'
            
        logger.debug(f"Calculated period: {period} for {days_diff} days")
        
        # Fetch data using the fetch_data method
        return self.fetch_data(ticker, period=period)
    
    def get_sample_data(self, ticker):
        """
        Get sample data for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            pandas.DataFrame: DataFrame containing sample stock data
        """
        logger.debug(f"Getting sample data for {ticker}")
        return self._generate_sample_data(ticker, period='5y', interval='1d')
    
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
            return self._generate_sample_data(ticker, period, interval)
        
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
                    logger.debug(f"Making request to {url} with params: {params}")
                    
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
                    
                    # Rename columns to match standard format
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
                    
                    # Sort by date (newest first)
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
                return self._generate_sample_data(ticker, period, interval)
            
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
            return self._generate_sample_data(ticker, period, interval)
    
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
                result[ticker] = self._generate_sample_data(ticker, period, interval)
        
        return result
    
    def _generate_sample_data(self, ticker, period='1y', interval='1d'):
        """
        Generate sample stock data for testing purposes.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period to generate data for
            interval (str): Data interval
        
        Returns:
            pandas.DataFrame: DataFrame containing sample stock data
        """
        logger.info(f"Generating sample data for {ticker} with period={period}, interval={interval}")
        
        # Determine number of days based on period
        if period == '1d':
            days = 1
        elif period == '5d':
            days = 5
        elif period == '1mo':
            days = 30
        elif period == '3mo':
            days = 90
        elif period == '6mo':
            days = 180
        elif period == '1y':
            days = 365
        elif period == '2y':
            days = 730
        elif period == '5y':
            days = 1825
        elif period == '10y':
            days = 3650
        elif period == 'ytd':
            days = (datetime.now() - datetime(datetime.now().year, 1, 1)).days
        elif period == 'max':
            days = 3650  # Default to 10 years for 'max'
        else:
            days = 365  # Default to 1 year
        
        # Determine interval in days
        if interval == '1d':
            interval_days = 1
        elif interval == '1wk':
            interval_days = 7
        elif interval == '1mo':
            interval_days = 30
        else:
            interval_days = 1  # Default to daily
        
        # Calculate number of data points
        num_points = days // interval_days
        
        # Get base price and volatility for the ticker
        base_price = DEFAULT_PRICES.get(ticker, 100.0)  # Default to 100 if ticker not in defaults
        volatility = DEFAULT_VOLATILITY.get(ticker, 0.02)  # Default to 0.02 if ticker not in defaults
        
        # Generate dates
        end_date = datetime.now()
        dates = [end_date - timedelta(days=i*interval_days) for i in range(num_points)]
        dates.reverse()  # Oldest first
        
        # Generate price data with random walk
        np.random.seed(hash(ticker) % 2**32)  # Use ticker as seed for reproducibility
        
        # Start with base price
        close_prices = [base_price]
        
        # Generate subsequent prices with random walk
        for i in range(1, num_points):
            # Random daily return with drift
            daily_return = np.random.normal(0.0002, volatility)  # Small positive drift
            new_price = close_prices[-1] * (1 + daily_return)
            close_prices.append(new_price)
        
        # Generate other price data
        high_prices = [price * (1 + np.random.uniform(0, volatility)) for price in close_prices]
        low_prices = [price * (1 - np.random.uniform(0, volatility)) for price in close_prices]
        open_prices = [low + np.random.uniform(0, high - low) for low, high in zip(low_prices, high_prices)]
        
        # Generate volume data
        base_volume = 1000000  # Base volume
        volumes = [int(base_volume * (1 + np.random.uniform(-0.5, 1.0))) for _ in range(num_points)]
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volumes
        }, index=dates)
        
        # Set index name
        df.index.name = 'Date'
        
        # Sort by date (newest first)
        df = df.sort_index(ascending=False)
        
        logger.info(f"Generated {len(df)} sample records for {ticker}")
        return df 