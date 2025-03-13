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
            self._add_risk_metrics(result)
            
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
                'ema_8', 'close_to_ema_8',
                'ema_21', 'close_to_ema_21',
                'sma_50', 'close_to_sma_50',
                'sma_200', 'close_to_sma_200',
                # Crossovers
                'ema_8_21_cross', 'sma_50_200_cross',
                'macd_cross',
                # Risk metrics
                'max_drawdown_90d', 'max_drawdown_180d',
                'sharpe_ratio_90d',
                'risk_adjusted_momentum',
                'price_stability',
                # Technical indicators
                'rsi', 'rsi_ma_context',
                'macd', 'macd_signal', 'macd_hist',
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
        for window in [50, 200]:  # Updated for medium-term focus
            df[f'sma_{window}'] = df['Close'].rolling(window=window).mean()
            
            # Relative position to moving average (%)
            df[f'close_to_sma_{window}'] = (df['Close'] / df[f'sma_{window}'] - 1) * 100
        
        # Exponential moving averages
        for window in [8, 21]:  # Updated for medium-term focus
            df[f'ema_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
            
            # Relative position to EMA (%)
            df[f'close_to_ema_{window}'] = (df['Close'] / df[f'ema_{window}'] - 1) * 100
        
        # Moving average crossovers (key combinations for medium-term)
        df['ema_8_21_cross'] = (df['ema_8'] > df['ema_21']).astype(int)
        df['sma_50_200_cross'] = (df['sma_50'] > df['sma_200']).astype(int)
    
    def _add_risk_metrics(self, df):
        """Add risk management features"""
        # Calculate rolling maximum drawdown for different windows
        for window in [90, 180]:
            rolling_max = df['Close'].rolling(window=window, min_periods=1).max()
            drawdown = (df['Close'] - rolling_max) / rolling_max * 100
            df[f'max_drawdown_{window}d'] = drawdown
        
        # Calculate rolling Sharpe ratio (90-day)
        returns = df['Close'].pct_change()
        excess_returns = returns - 0.05/252  # Assuming 5% annual risk-free rate
        rolling_std = returns.rolling(window=90, min_periods=30).std() * np.sqrt(252)  # Annualized
        df['sharpe_ratio_90d'] = (excess_returns.rolling(window=90, min_periods=30).mean() * 252) / rolling_std
        
        # Calculate risk-adjusted momentum
        momentum_90d = df['Close'].pct_change(90)
        abs_drawdown_90d = abs(df['max_drawdown_90d'])
        df['risk_adjusted_momentum'] = momentum_90d / (abs_drawdown_90d + 1e-6)  # Add small constant to avoid division by zero
        
        # Calculate price stability (percentage of time above major MAs)
        ma_list = ['sma_50', 'sma_200']
        above_ma_count = pd.DataFrame()
        
        for ma in ma_list:
            if ma in df.columns:
                above_ma_count[ma] = (df['Close'] > df[ma]).astype(int)
        
        if not above_ma_count.empty:
            df['price_stability'] = above_ma_count.mean(axis=1) * 100
    
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
        
        # Add RSI extremes with MA context
        df['rsi_ma_context'] = ((df['rsi'] < 30) & (df['Close'] > df['sma_50'])).astype(int) | \
                              ((df['rsi'] > 70) & (df['Close'] < df['sma_50'])).astype(int)
    
    def _add_macd(self, df, fast=50, slow=100, signal=20):
        """Add Moving Average Convergence Divergence (MACD) with medium-term parameters"""
        # Calculate MACD components
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        # MACD line
        df['macd'] = ema_fast - ema_slow
        
        # Signal line
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        
        # Histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Add MACD crossover signal
        df['macd_cross'] = (df['macd'] > df['macd_signal']).astype(int)
    
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