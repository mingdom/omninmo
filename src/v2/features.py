"""
Feature engineering for stock data
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Features:
    """Class for generating features from stock data"""
    
    def __init__(self):
        """Initialize the feature generator"""
        pass
    
    def generate(self, df):
        """
        Generate features from stock price data
        
        Args:
            df (pandas.DataFrame): DataFrame with OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with additional features
        """
        if df is None or len(df) < 30:
            logger.warning("Not enough data for feature generation")
            return None
        
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        try:
            # Price-based features
            self._add_returns(result)
            self._add_moving_averages(result)
            self._add_volatility(result)
            
            # Technical indicators
            self._add_rsi(result)
            self._add_macd(result)
            self._add_bollinger_bands(result)
            
            # Fill NaN values that might have been introduced
            # Use ffill and bfill instead of method parameter (which is deprecated)
            result = result.ffill().bfill()
            
            # Select only the columns we want to use for training
            keep_columns = [
                # Price data
                'Open', 'High', 'Low', 'Close', 'Volume',
                # Returns
                'return_1d', 'return_5d', 'return_10d', 'return_20d', 'return_60d',
                'log_return_1d',
                # Moving averages
                'sma_5', 'close_to_sma_5',
                'sma_10', 'close_to_sma_10',
                'sma_20', 'close_to_sma_20',
                'sma_50', 'close_to_sma_50',
                'sma_200', 'close_to_sma_200',
                'ema_5', 'close_to_ema_5',
                'ema_10', 'close_to_ema_10',
                'ema_20', 'close_to_ema_20',
                'ema_50', 'close_to_ema_50',
                # Crossovers
                'sma_10_50_cross', 'ema_10_20_cross',
                # Volatility
                'volatility_10d', 'volatility_20d', 'volatility_60d',
                'day_range', 'avg_range_10d',
                # Technical indicators
                'rsi', 'macd', 'macd_signal', 'macd_hist',
                'bb_middle', 'bb_std', 'bb_upper', 'bb_lower',
                'bb_width', 'bb_pct_b'
            ]
            
            result = result[keep_columns]
            
            logger.info(f"Generated {len(keep_columns)} features")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating features: {e}")
            return None
    
    def _add_returns(self, df):
        """Add return-based features"""
        # Daily returns
        df['return_1d'] = df['Close'].pct_change(1)
        
        # N-day returns
        for n in [5, 10, 20, 60]:
            df[f'return_{n}d'] = df['Close'].pct_change(n)
        
        # Log returns (reduces skewness)
        df['log_return_1d'] = np.log(df['Close'] / df['Close'].shift(1))
    
    def _add_moving_averages(self, df):
        """Add moving average features"""
        # Simple moving averages
        for window in [5, 10, 20, 50, 200]:
            df[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
            
            # Relative position to moving average (%)
            df[f'close_to_sma_{window}'] = (df['Close'] / df[f'sma_{window}'] - 1) * 100
        
        # Exponential moving averages
        for window in [5, 10, 20, 50]:
            df[f'ema_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
            
            # Relative position to EMA (%)
            df[f'close_to_ema_{window}'] = (df['Close'] / df[f'ema_{window}'] - 1) * 100
        
        # Moving average crossovers
        df['sma_10_50_cross'] = (df['sma_10'] > df['sma_50']).astype(int)
        df['ema_10_20_cross'] = (df['ema_10'] > df['ema_20']).astype(int)
    
    def _add_volatility(self, df):
        """Add volatility-based features"""
        # Historical volatility (standard deviation of returns)
        for window in [10, 20, 60]:
            df[f'volatility_{window}d'] = df['return_1d'].rolling(window=window).std()
        
        # High-Low range as percentage of Close
        df['day_range'] = (df['High'] - df['Low']) / df['Close'] * 100
        
        # Average day range over time
        df['avg_range_10d'] = df['day_range'].rolling(window=10).mean()
    
    def _add_rsi(self, df, window=14):
        """Add Relative Strength Index (RSI)"""
        delta = df['Close'].diff()
        
        # Get gains and losses
        gains = delta.copy()
        losses = delta.copy()
        
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate averages
        avg_gain = gains.rolling(window=window).mean()
        avg_loss = losses.rolling(window=window).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
    
    def _add_macd(self, df, fast=12, slow=26, signal=9):
        """Add Moving Average Convergence Divergence (MACD)"""
        # Calculate MACD components
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        # MACD line
        df['macd'] = ema_fast - ema_slow
        
        # Signal line
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        
        # Histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
    
    def _add_bollinger_bands(self, df, window=20, num_std=2):
        """Add Bollinger Bands"""
        # Calculate middle band (SMA)
        df['bb_middle'] = df['Close'].rolling(window=window).mean()
        
        # Calculate the standard deviation
        df['bb_std'] = df['Close'].rolling(window=window).std()
        
        # Calculate upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * num_std)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * num_std)
        
        # Calculate bandwidth and %B
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_pct_b'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

if __name__ == "__main__":
    # Simple test
    from src.v2.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    data = fetcher.fetch_data('AAPL', period='1y', force_sample=True)
    
    features = Features()
    result = features.generate(data)
    
    print(f"Original columns: {list(data.columns)}")
    print(f"Feature columns: {list(result.columns)}")
    print(f"Total features: {len(result.columns)}") 