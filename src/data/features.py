"""
Feature engineering module for omninmo.
Calculates technical indicators and prepares features for the model.
"""

import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator


class FeatureEngineer:
    """Class for feature engineering."""

    def __init__(self):
        """Initialize the FeatureEngineer."""
        pass

    def add_technical_indicators(self, df):
        """
        Add technical indicators to the dataframe.

        Args:
            df (pd.DataFrame): DataFrame containing stock data with OHLCV columns

        Returns:
            pd.DataFrame: DataFrame with added technical indicators
        """
        if df is None or df.empty:
            return None

        # Make a copy to avoid modifying the original dataframe
        df = df.copy()

        # Ensure we have the required columns
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Add trend indicators
        # SMA - Simple Moving Average
        df["sma_20"] = SMAIndicator(close=df["Close"], window=20).sma_indicator()
        df["sma_50"] = SMAIndicator(close=df["Close"], window=50).sma_indicator()
        df["sma_200"] = SMAIndicator(close=df["Close"], window=200).sma_indicator()

        # EMA - Exponential Moving Average
        df["ema_12"] = EMAIndicator(close=df["Close"], window=12).ema_indicator()
        df["ema_26"] = EMAIndicator(close=df["Close"], window=26).ema_indicator()

        # MACD - Moving Average Convergence Divergence
        macd = MACD(close=df["Close"], window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_diff"] = macd.macd_diff()

        # Add momentum indicators
        # RSI - Relative Strength Index
        df["rsi_14"] = RSIIndicator(close=df["Close"], window=14).rsi()

        # Stochastic Oscillator
        stoch = StochasticOscillator(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            window=14,
            smooth_window=3,
        )
        df["stoch_k"] = stoch.stoch()
        df["stoch_d"] = stoch.stoch_signal()

        # Add volatility indicators
        # Bollinger Bands
        bollinger = BollingerBands(close=df["Close"], window=20, window_dev=2)
        df["bb_high"] = bollinger.bollinger_hband()
        df["bb_mid"] = bollinger.bollinger_mavg()
        df["bb_low"] = bollinger.bollinger_lband()
        df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["bb_mid"]

        # Add volume indicators
        # OBV - On Balance Volume
        df["obv"] = OnBalanceVolumeIndicator(
            close=df["Close"], volume=df["Volume"]
        ).on_balance_volume()

        # Add price-based features
        # Price change percentage
        df["price_change_1d"] = df["Close"].pct_change(1)
        df["price_change_5d"] = df["Close"].pct_change(5)
        df["price_change_20d"] = df["Close"].pct_change(20)

        # Volatility (standard deviation of returns)
        df["volatility_20d"] = df["price_change_1d"].rolling(window=20).std()

        # Distance from moving averages (%)
        df["dist_sma_20"] = (df["Close"] - df["sma_20"]) / df["sma_20"] * 100
        df["dist_sma_50"] = (df["Close"] - df["sma_50"]) / df["sma_50"] * 100
        df["dist_sma_200"] = (df["Close"] - df["sma_200"]) / df["sma_200"] * 100

        # Drop rows with NaN values (due to rolling windows)
        df = df.dropna()

        return df

    def prepare_features(self, df):
        """
        Prepare features for the model.

        Args:
            df (pd.DataFrame): DataFrame with technical indicators

        Returns:
            tuple: (X, feature_names) where X is a numpy array of features and feature_names is a list of feature names
        """
        if df is None or df.empty:
            return None, None

        # Select features for the model
        feature_columns = [
            # Trend indicators
            "sma_20",
            "sma_50",
            "sma_200",
            "ema_12",
            "ema_26",
            "macd",
            "macd_signal",
            "macd_diff",
            # Momentum indicators
            "rsi_14",
            "stoch_k",
            "stoch_d",
            # Volatility indicators
            "bb_width",
            "volatility_20d",
            # Volume indicators
            "obv",
            # Price-based features
            "price_change_1d",
            "price_change_5d",
            "price_change_20d",
            "dist_sma_20",
            "dist_sma_50",
            "dist_sma_200",
        ]

        # Check if all feature columns exist in the dataframe
        missing_columns = [col for col in feature_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in dataframe: {missing_columns}")

        # Extract features
        X = df[feature_columns].values

        return X, feature_columns
