"""
Feature engineering module for calculating technical indicators.
"""

import pandas as pd
import numpy as np
import logging
import logging.handlers
from pathlib import Path

# Setup logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set default level to DEBUG

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Setup file handler
file_handler = logging.handlers.RotatingFileHandler(
    'logs/feature_engineer.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

class FeatureEngineer:
    """
    Class for calculating technical indicators and preparing features for the prediction model.
    """
    
    def __init__(self):
        """Initialize the FeatureEngineer."""
        logger.debug("Initializing FeatureEngineer")
    
    def add_indicators(self, data):
        """
        Add technical indicators to the DataFrame.
        
        Args:
            data (pandas.DataFrame): DataFrame with OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with added technical indicators
        """
        if data is None or data.empty:
            logger.warning("No data provided for adding indicators")
            return None
            
        logger.debug(f"Adding indicators to data with shape {data.shape}")
        return self.calculate_indicators(data)
    
    def add_return_features(self, data):
        """
        Add future return calculations to the DataFrame.
        
        Args:
            data (pandas.DataFrame): DataFrame with price data
            
        Returns:
            pandas.DataFrame: DataFrame with future return features
        """
        if data is None or data.empty:
            logger.warning("No data provided for adding return features")
            return None
        
        try:
            logger.debug(f"Adding return features to data with shape {data.shape}")
            
            # Make a copy to avoid modifying the original
            df = data.copy()
            
            # Check if we need to get the Close price from the original data
            # This happens when we've already calculated indicators and dropped OHLCV columns
            if 'Close' not in df.columns:
                logger.debug("Close column not found, cannot calculate future returns")
                logger.debug(f"Available columns: {df.columns.tolist()}")
                return df
            
            # Calculate future return (20 days ahead)
            df['future_return'] = df['Close'].pct_change(periods=-20)
            
            # Drop the last 20 rows since they don't have future returns
            df = df.iloc[:-20]
            
            logger.debug(f"Added future return feature, new shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error adding return features: {str(e)}", exc_info=True)
            return None
    
    def calculate_indicators(self, data):
        """
        Calculate technical indicators for stock data.
        
        Args:
            data (pandas.DataFrame): DataFrame containing stock data with OHLCV columns
        
        Returns:
            pandas.DataFrame: DataFrame containing calculated technical indicators
        """
        if data is None or data.empty:
            logger.warning("No data provided for calculating indicators")
            return None
        
        try:
            logger.debug(f"Calculating indicators for data with shape {data.shape}")
            
            # Make a copy to avoid modifying the original dataframe
            df = data.copy()
            
            # Moving Averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            logger.debug("Calculated SMA indicators")
            
            # Exponential Moving Averages
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            
            # MACD (Moving Average Convergence Divergence)
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            
            logger.debug("Calculated MACD indicators")
            
            # Relative Strength Index (RSI)
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))
            
            # Replace infinity and NaN with NaN
            df['RSI'] = df['RSI'].replace([np.inf, -np.inf], np.nan)
            
            logger.debug("Calculated RSI indicator")
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + 2 * df['BB_Std']
            df['BB_Lower'] = df['BB_Middle'] - 2 * df['BB_Std']
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
            
            # Replace infinity and NaN with NaN
            df['BB_Width'] = df['BB_Width'].replace([np.inf, -np.inf], np.nan)
            
            logger.debug("Calculated Bollinger Bands indicators")
            
            # Average True Range (ATR)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            logger.debug("Calculated ATR indicator")
            
            # Volume indicators
            df['Volume_SMA_5'] = df['Volume'].rolling(window=5).mean()
            df['Volume_SMA_10'] = df['Volume'].rolling(window=10).mean()
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_5']
            
            # Replace infinity and NaN with NaN
            df['Volume_Ratio'] = df['Volume_Ratio'].replace([np.inf, -np.inf], np.nan)
            
            logger.debug("Calculated volume indicators")
            
            # Price momentum
            df['ROC_5'] = df['Close'].pct_change(periods=5) * 100
            df['ROC_10'] = df['Close'].pct_change(periods=10) * 100
            df['ROC_20'] = df['Close'].pct_change(periods=20) * 100
            
            logger.debug("Calculated price momentum indicators")
            
            # Price relative to moving averages
            # Only calculate if we have the moving averages
            if not df['SMA_50'].isna().all():
                with np.errstate(divide='ignore', invalid='ignore'):
                    df['Price_to_SMA_50'] = df['Close'] / df['SMA_50']
                df['Price_to_SMA_50'] = df['Price_to_SMA_50'].replace([np.inf, -np.inf], np.nan)
            else:
                df['Price_to_SMA_50'] = np.nan
                
            if not df['SMA_200'].isna().all():
                with np.errstate(divide='ignore', invalid='ignore'):
                    df['Price_to_SMA_200'] = df['Close'] / df['SMA_200']
                df['Price_to_SMA_200'] = df['Price_to_SMA_200'].replace([np.inf, -np.inf], np.nan)
            else:
                df['Price_to_SMA_200'] = np.nan
            
            logger.debug("Calculated price relative to moving averages")
            
            # Golden/Death Cross
            if not df['SMA_50'].isna().all() and not df['SMA_200'].isna().all():
                with np.errstate(divide='ignore', invalid='ignore'):
                    df['SMA_50_200_Ratio'] = df['SMA_50'] / df['SMA_200']
                df['SMA_50_200_Ratio'] = df['SMA_50_200_Ratio'].replace([np.inf, -np.inf], np.nan)
            else:
                df['SMA_50_200_Ratio'] = np.nan
            
            logger.debug("Calculated Golden/Death Cross indicator")
            
            # Drop the original OHLCV columns as they're not used as features
            features = df.drop(['Open', 'High', 'Low', 'Close', 'Volume'], axis=1, errors='ignore')
            
            # Fill NaN values with appropriate values
            # For moving averages and other indicators, forward fill then backward fill
            features = features.ffill().bfill()
            
            # If there are still NaN values (e.g., at the beginning of the series), fill with zeros
            features = features.fillna(0)
            
            # Drop rows with all NaN values
            features = features.dropna(how='all')
            
            logger.info(f"Calculated {features.shape[1]} technical indicators, data shape: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}", exc_info=True)
            return None
    
    def normalize_features(self, features):
        """
        Normalize features to have zero mean and unit variance.
        
        Args:
            features (pandas.DataFrame): DataFrame containing technical indicators
        
        Returns:
            pandas.DataFrame: DataFrame containing normalized features
        """
        if features is None or features.empty:
            logger.warning("No features provided for normalization")
            return None
        
        try:
            logger.debug(f"Normalizing features with shape {features.shape}")
            
            # Fill NaN values before normalization
            features_filled = features.ffill().bfill().fillna(0)
            
            # Calculate mean and standard deviation
            mean = features_filled.mean()
            std = features_filled.std()
            
            # Avoid division by zero
            std = std.replace(0, 1)
            
            # Normalize features
            normalized = (features_filled - mean) / std
            
            # Replace infinite values with 0
            normalized = normalized.replace([np.inf, -np.inf], 0)
            
            logger.debug(f"Normalized features, shape: {normalized.shape}")
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing features: {str(e)}", exc_info=True)
            return None 