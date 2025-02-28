"""
Feature engineering module for calculating technical indicators.
"""

import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Class for calculating technical indicators and preparing features for the prediction model.
    """
    
    def __init__(self):
        """Initialize the FeatureEngineer."""
        pass
    
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
            # Create a copy to avoid modifying the original data
            df = data.copy()
            
            # Check if required columns exist
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return None
            
            # Simple Moving Averages
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            
            # Only calculate longer-term MAs if we have enough data
            if len(df) >= 50:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
            else:
                df['SMA_50'] = np.nan
                
            if len(df) >= 200:
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
            else:
                df['SMA_200'] = np.nan
            
            # Exponential Moving Averages
            df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            
            if len(df) >= 50:
                df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            else:
                df['EMA_50'] = np.nan
                
            if len(df) >= 200:
                df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
            else:
                df['EMA_200'] = np.nan
            
            # Moving Average Convergence Divergence (MACD)
            df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            
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
            
            # Average True Range (ATR)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['ATR'] = true_range.rolling(14).mean()
            
            # Volume indicators
            df['Volume_SMA_5'] = df['Volume'].rolling(window=5).mean()
            df['Volume_SMA_10'] = df['Volume'].rolling(window=10).mean()
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_5']
            
            # Replace infinity and NaN with NaN
            df['Volume_Ratio'] = df['Volume_Ratio'].replace([np.inf, -np.inf], np.nan)
            
            # Price momentum
            df['ROC_5'] = df['Close'].pct_change(periods=5) * 100
            df['ROC_10'] = df['Close'].pct_change(periods=10) * 100
            df['ROC_20'] = df['Close'].pct_change(periods=20) * 100
            
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
            
            # Golden/Death Cross
            if not df['SMA_50'].isna().all() and not df['SMA_200'].isna().all():
                with np.errstate(divide='ignore', invalid='ignore'):
                    df['SMA_50_200_Ratio'] = df['SMA_50'] / df['SMA_200']
                df['SMA_50_200_Ratio'] = df['SMA_50_200_Ratio'].replace([np.inf, -np.inf], np.nan)
            else:
                df['SMA_50_200_Ratio'] = np.nan
            
            # Drop the original OHLCV columns as they're not used as features
            features = df.drop(['Open', 'High', 'Low', 'Close', 'Volume'], axis=1, errors='ignore')
            
            # Drop rows with all NaN values
            features = features.dropna(how='all')
            
            logger.info(f"Calculated {features.shape[1]} technical indicators")
            return features
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
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
            return None
        
        try:
            # Calculate mean and standard deviation
            mean = features.mean()
            std = features.std()
            
            # Avoid division by zero
            std = std.replace(0, 1)
            
            # Normalize features
            normalized = (features - mean) / std
            
            # Replace infinite values with NaN and then drop rows with NaN
            normalized = normalized.replace([np.inf, -np.inf], np.nan)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing features: {e}")
            return None 