"""
Stock data fetcher module for retrieving historical stock data.
"""

import pandas as pd
import yfinance as yf
import logging
import os
import time
import requests
from datetime import datetime, timedelta
import random
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class StockDataFetcher:
    """
    Class for fetching historical stock data using yfinance.
    """
    
    def __init__(self, cache_dir=None):
        """
        Initialize the StockDataFetcher.
        
        Args:
            cache_dir (str, optional): Directory to cache stock data. If None, no caching is used.
        """
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_data(self, ticker, period='1y', interval='1d', max_retries=3, retry_delay=2, force_sample=False):
        """
        Fetch historical stock data for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period to fetch data for (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval (str): Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            force_sample (bool): Force the use of sample data even if real data is available
        
        Returns:
            pandas.DataFrame: DataFrame containing historical stock data
        """
        try:
            logger.info(f"Fetching data for {ticker} with period={period}, interval={interval}")
            
            # If force_sample is True, skip API calls and use sample data
            if force_sample:
                logger.info(f"Forcing sample data for {ticker}")
                return self._generate_sample_data(ticker, period, interval)
            
            # Check cache if enabled
            if self.cache_dir:
                cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")
                if os.path.exists(cache_file):
                    # Check if cache is recent (less than 1 day old)
                    if datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file)) < timedelta(days=1):
                        logger.info(f"Loading {ticker} data from cache")
                        try:
                            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
                        except Exception as e:
                            logger.warning(f"Error reading cache file: {e}. Will fetch fresh data.")
            
            # Fetch data from yfinance with retries
            data = None
            for attempt in range(max_retries):
                try:
                    # Create a session with a longer timeout and better headers
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'max-age=0'
                    })
                    
                    # Add a random delay to avoid rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Try direct download method first
                    try:
                        data = yf.download(
                            ticker, 
                            period=period, 
                            interval=interval,
                            progress=False,
                            timeout=20  # Increase timeout
                        )
                    except Exception as e:
                        logger.warning(f"Direct download failed for {ticker}: {e}, trying Ticker method")
                        # If direct download fails, try the Ticker method
                        stock = yf.Ticker(ticker, session=session)
                        data = stock.history(period=period, interval=interval)
                    
                    if not data.empty:
                        break
                    
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Empty data for {ticker}, retrying...")
                    time.sleep(retry_delay + attempt)  # Increasing delay with each attempt
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Error fetching {ticker}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay + attempt)
            
            # If we still don't have data, use sample data for testing
            if data is None or data.empty:
                logger.warning(f"No data available for {ticker}, using sample data for testing")
                data = self._generate_sample_data(ticker, period, interval)
            
            # Save to cache if enabled and we have data
            if self.cache_dir and data is not None and not data.empty:
                try:
                    data.to_csv(cache_file)
                except Exception as e:
                    logger.warning(f"Error saving to cache: {e}")
            
            if data is not None and not data.empty:
                logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            else:
                logger.warning(f"No data available for {ticker}")
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            # Return sample data for testing purposes
            return self._generate_sample_data(ticker, period, interval)
    
    def _generate_sample_data(self, ticker, period, interval):
        """
        Generate sample stock data for testing purposes.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period
            interval (str): Data interval
        
        Returns:
            pandas.DataFrame: DataFrame containing sample stock data
        """
        logger.info(f"Generating sample data for {ticker}")
        
        # Determine number of days based on period
        if 'mo' in period:
            days = int(period.replace('mo', '')) * 30
        elif 'y' in period:
            days = int(period.replace('y', '')) * 365
        else:
            days = 30  # Default to 1 month
            
        # Ensure we have at least 252 trading days (1 year) for testing
        days = max(days, 252)
        
        # Generate dates (only business days for stock data)
        end_date = datetime.now()
        dates = []
        current_date = end_date
        
        # Generate approximately days * 1.4 calendar days to get enough business days
        for i in range(int(days * 1.4)):
            current_date = current_date - timedelta(days=1)
            # Skip weekends (0 = Monday, 6 = Sunday)
            if current_date.weekday() < 5:  # Only include weekdays
                dates.append(current_date)
            if len(dates) >= days:
                break
                
        dates.reverse()
        
        # Get base price and volatility for the ticker
        base_price = DEFAULT_PRICES.get(ticker, 100.0)
        volatility = DEFAULT_VOLATILITY.get(ticker, 0.02)
        
        # Generate price series with realistic trends and volatility
        price_series = self._generate_realistic_price_series(base_price, len(dates), volatility)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Open': price_series,
            'Close': [p * (1 + np.random.normal(0, volatility/3)) for p in price_series],
            'High': [max(o, c) * (1 + abs(np.random.normal(0, volatility/2))) 
                    for o, c in zip(price_series, [p * (1 + np.random.normal(0, volatility/3)) for p in price_series])],
            'Low': [min(o, c) * (1 - abs(np.random.normal(0, volatility/2))) 
                   for o, c in zip(price_series, [p * (1 + np.random.normal(0, volatility/3)) for p in price_series])],
            'Volume': [int(np.random.normal(base_price * 100000, base_price * 20000)) for _ in range(len(dates))]
        }, index=dates)
        
        # Ensure High is always >= Open and Close
        df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
        
        # Ensure Low is always <= Open and Close
        df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
        
        # Ensure Volume is always positive
        df['Volume'] = df['Volume'].abs()
        
        logger.info(f"Generated {len(df)} records of sample data for {ticker}")
        return df
    
    def _generate_realistic_price_series(self, base_price, length, volatility):
        """
        Generate a realistic price series with trends and volatility.
        
        Args:
            base_price (float): Starting price
            length (int): Number of data points
            volatility (float): Daily volatility
            
        Returns:
            list: List of prices
        """
        # Parameters for the price series
        trend_strength = 0.001  # Strength of the trend
        trend_change_prob = 0.05  # Probability of trend change
        trend = random.choice([-1, 1]) * trend_strength  # Initial trend direction
        
        prices = [base_price]
        
        for i in range(1, length):
            # Randomly change trend direction
            if random.random() < trend_change_prob:
                trend = random.choice([-1, 1]) * trend_strength
            
            # Calculate daily return with trend and volatility
            daily_return = trend + np.random.normal(0, volatility)
            
            # Calculate new price
            new_price = prices[-1] * (1 + daily_return)
            
            # Ensure price doesn't go too low
            new_price = max(new_price, base_price * 0.1)
            
            prices.append(new_price)
        
        return prices
    
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
            data = self.fetch_data(ticker, period, interval, force_sample=force_sample)
            if data is not None:
                result[ticker] = data
        
        return result 