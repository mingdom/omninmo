"""
Feature engineering for stock data
"""

import logging

import numpy as np
import pandas as pd

from src.v2.config import config

logger = logging.getLogger(__name__)

# Constants with defaults from config
RSI_THRESHOLD = config.get("features.thresholds.rsi", 30)
STOCH_THRESHOLD_LOW = config.get("features.thresholds.stochastic.low", 30)
STOCH_THRESHOLD_HIGH = config.get("features.thresholds.stochastic.high", 70)
VOLUME_THRESHOLD = config.get("features.thresholds.volume_increase", 25)
MIN_DATA_DAYS = config.get(
    "model.training.min_data_days", 30
)  # Minimum days for feature calculation
TREND_STRENGTH_THRESHOLD = config.get(
    "features.thresholds.trend_strength", 25
)  # ADX trend strength threshold
MIN_ROLLING_PERIODS = config.get(
    "features.min_rolling_periods", 30
)  # Minimum periods for rolling calculations
VOLATILITY_BASE_WINDOW = config.get(
    "features.volatility.base_window", 30
)  # Base window for volatility comparisons


class Features:
    """Class for generating features from stock data"""

    def __init__(self):
        """Initialize the feature generator"""
        pass

    def generate(self, df, market_data=None, use_enhanced_features=False):
        """
        Generate features from stock price data

        Args:
            df (pandas.DataFrame): DataFrame with OHLCV data
            market_data (pandas.DataFrame): DataFrame with market index data (e.g., S&P 500)
            use_enhanced_features (bool): Whether to generate enhanced risk-adjusted features

        Returns:
            pandas.DataFrame: DataFrame with additional features
        """
        if df is None or len(df) < MIN_DATA_DAYS:
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
            self._add_adx(result)  # Add ADX feature

            # Add enhanced risk-adjusted features if requested
            if use_enhanced_features:
                logger.info("Generating enhanced risk-adjusted features")

                # Add enhanced risk metrics if market data is available
                if market_data is not None:
                    # Ensure market_data has the same index as result
                    market_data = market_data.reindex(result.index, method="ffill")

                    # Add beta and market sensitivity features
                    self._add_beta_features(result, market_data)

                    # Add conditional performance metrics
                    self._add_conditional_performance(result, market_data)

                # Add volatility and downside risk metrics
                self._add_volatility_features(result)

                # Add return distribution characteristics
                self._add_distribution_features(result)

                # Calculate risk-adjusted target
                self._add_risk_adjusted_target(result)

            # Fill NaN values that might have been introduced
            # Use ffill and bfill instead of method parameter (which is deprecated)
            result = result.ffill().bfill()

            # Select only the columns we want to use for training
            keep_columns = [
                # Price data
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                # Returns (removed 5d and 10d returns)
                "return_1d",
                "return_20d",
                "return_60d",
                "log_return_1d",
                # Moving averages (removed close_to_ema_8)
                "ema_21",
                "close_to_ema_21",
                "sma_50",
                "close_to_sma_50",
                "sma_200",
                "close_to_sma_200",
                # Crossovers
                "ema_8_21_cross",
                "sma_50_200_cross",
                "macd_cross",
                # Risk metrics
                "max_drawdown_90d",
                "max_drawdown_180d",
                "sharpe_ratio_90d",
                "risk_adjusted_momentum",
                "price_stability",
                # Technical indicators
                "rsi",
                "rsi_ma_context",
                "macd",
                "macd_signal",
                "macd_hist",
                # Bollinger Bands (removed redundant bands)
                "bb_std",
                "bb_width",
                "bb_pct_b",
                # ADX indicators
                "adx",
                "adx_trend_strength",
            ]

            # Add enhanced feature columns if they exist
            if use_enhanced_features:
                enhanced_columns = [
                    # Beta features
                    "beta_60d",
                    "beta_120d",
                    "market_corr_60d",
                    "market_corr_120d",
                    "rel_strength_60d",
                    "rel_strength_120d",
                    # Volatility features
                    "volatility_30d",
                    "volatility_60d",
                    "volatility_90d",
                    "downside_dev_30d",
                    "downside_dev_60d",
                    "downside_dev_90d",
                    "vol_ratio_30_60d",
                    "vol_ratio_30_90d",
                    # Distribution features
                    "returns_skew_90d",
                    "returns_kurt_90d",
                    "drawdown_vol_ratio_90d",
                    # Conditional performance
                    "bull_return_90d",
                    "bull_volatility_90d",
                    "bear_return_90d",
                    "bear_volatility_90d",
                    "bull_bear_return_ratio",
                    # Risk-adjusted target
                    "target_sharpe_ratio",
                ]

                # Filter out enhanced columns that don't exist in the result
                enhanced_columns = [
                    col for col in enhanced_columns if col in result.columns
                ]

                # Add enhanced columns to keep_columns
                keep_columns.extend(enhanced_columns)

            # Filter out columns that don't exist in the result
            keep_columns = [col for col in keep_columns if col in result.columns]

            result = result[keep_columns]

            logger.info(f"Generated {len(keep_columns)} features")

            return result

        except Exception as e:
            logger.error(f"Error generating features: {e}")
            return None

    def _add_returns(self, df):
        """Add return-based features"""
        # Daily returns
        df["return_1d"] = df["Close"].pct_change(1)

        # N-day returns (removed 5d and 10d)
        for n in [20, 60]:
            df[f"return_{n}d"] = df["Close"].pct_change(n)

        # Log returns (reduces skewness)
        df["log_return_1d"] = np.log(df["Close"] / df["Close"].shift(1))

    def _add_moving_averages(self, df):
        """Add moving average features"""
        # Simple moving averages
        for window in [50, 200]:  # Updated for medium-term focus
            df[f"sma_{window}"] = df["Close"].rolling(window=window).mean()

            # Relative position to moving average (%)
            df[f"close_to_sma_{window}"] = (df["Close"] / df[f"sma_{window}"] - 1) * 100

        # Exponential moving averages (removed close_to_ema_8)
        df["ema_8"] = df["Close"].ewm(span=8, adjust=False).mean()  # Keep for crossover
        for window in [21]:  # Removed ema_8 relative position
            df[f"ema_{window}"] = df["Close"].ewm(span=window, adjust=False).mean()

            # Relative position to EMA (%)
            df[f"close_to_ema_{window}"] = (df["Close"] / df[f"ema_{window}"] - 1) * 100

        # Moving average crossovers (key combinations for medium-term)
        df["ema_8_21_cross"] = (df["ema_8"] > df["ema_21"]).astype(int)
        df["sma_50_200_cross"] = (df["sma_50"] > df["sma_200"]).astype(int)

    def _add_risk_metrics(self, df):
        """Add risk management features"""
        # Calculate rolling maximum drawdown for different windows
        for window in [90, 180]:
            rolling_max = df["Close"].rolling(window=window, min_periods=1).max()
            drawdown = (df["Close"] - rolling_max) / rolling_max * 100
            df[f"max_drawdown_{window}d"] = drawdown

        # Calculate rolling Sharpe ratio (90-day)
        returns = df["Close"].pct_change()
        excess_returns = returns - 0.05 / 252  # Assuming 5% annual risk-free rate
        rolling_std = returns.rolling(
            window=90, min_periods=MIN_ROLLING_PERIODS
        ).std() * np.sqrt(252)  # Annualized
        df["sharpe_ratio_90d"] = (
            excess_returns.rolling(window=90, min_periods=MIN_ROLLING_PERIODS).mean()
            * 252
        ) / rolling_std

        # Calculate risk-adjusted momentum
        momentum_90d = df["Close"].pct_change(90)
        abs_drawdown_90d = abs(df["max_drawdown_90d"])
        df["risk_adjusted_momentum"] = momentum_90d / (
            abs_drawdown_90d + 1e-6
        )  # Add small constant to avoid division by zero

        # Calculate price stability (percentage of time above major MAs)
        ma_list = ["sma_50", "sma_200"]
        above_ma_count = pd.DataFrame()

        for ma in ma_list:
            if ma in df.columns:
                above_ma_count[ma] = (df["Close"] > df[ma]).astype(int)

        if not above_ma_count.empty:
            df["price_stability"] = above_ma_count.mean(axis=1) * 100

    def _add_rsi(self, df, window=14):
        """Add Relative Strength Index (RSI)"""
        delta = df["Close"].diff()

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
        df["rsi"] = 100 - (100 / (1 + rs))

        # Add RSI extremes with MA context
        df["rsi_ma_context"] = (
            (df["rsi"] < RSI_THRESHOLD) & (df["Close"] > df["sma_50"])
        ).astype(int) | (
            (df["rsi"] > (100 - RSI_THRESHOLD)) & (df["Close"] < df["sma_50"])
        ).astype(int)

    def _add_macd(self, df, fast=50, slow=100, signal=20):
        """Add Moving Average Convergence Divergence (MACD) with medium-term parameters"""
        # Calculate MACD components
        ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()

        # MACD line
        df["macd"] = ema_fast - ema_slow

        # Signal line
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()

        # Histogram
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # Add MACD crossover signal
        df["macd_cross"] = (df["macd"] > df["macd_signal"]).astype(int)

    def _add_bollinger_bands(self, df, window=20, num_std=2):
        """Add Bollinger Bands"""
        # Calculate middle band (SMA) - removed as redundant
        sma = df["Close"].rolling(window=window).mean()

        # Calculate the standard deviation
        df["bb_std"] = df["Close"].rolling(window=window).std()

        # Calculate upper and lower bands - removed as redundant
        upper = sma + (df["bb_std"] * num_std)
        lower = sma - (df["bb_std"] * num_std)

        # Calculate bandwidth and %B
        df["bb_width"] = (upper - lower) / sma
        df["bb_pct_b"] = (df["Close"] - lower) / (upper - lower)

    def _add_adx(self, df, period=14):
        """
        Add Average Directional Index (ADX) to measure trend strength

        ADX measures trend strength regardless of direction
        Values > 25 indicate strong trend
        """
        # Calculate +DI and -DI
        high_diff = df["High"].diff()
        low_diff = df["Low"].diff().multiply(-1)

        plus_dm = (high_diff > low_diff) & (high_diff > 0)
        plus_dm = high_diff.where(plus_dm, 0)

        minus_dm = (low_diff > high_diff) & (low_diff > 0)
        minus_dm = low_diff.where(minus_dm, 0)

        # Calculate ATR
        tr1 = df["High"] - df["Low"]
        tr2 = (df["High"] - df["Close"].shift(1)).abs()
        tr3 = (df["Low"] - df["Close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        # Calculate +DI and -DI
        plus_di = 100 * plus_dm.rolling(period).mean() / atr
        minus_di = 100 * minus_dm.rolling(period).mean() / atr

        # Calculate DX and ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        df["adx"] = dx.rolling(period).mean()
        df["adx_trend_strength"] = (df["adx"] > TREND_STRENGTH_THRESHOLD).astype(int)

        return df

    # Enhanced risk-adjusted features

    def _add_beta_features(self, df, market_data, windows=[60, 120]):
        """
        Calculate beta and correlation with market indices

        Args:
            df (pandas.DataFrame): DataFrame with stock data
            market_data (pandas.DataFrame): DataFrame with market index data
            windows (list): List of window sizes for rolling calculations
        """
        # Calculate returns for the stock
        stock_returns = df["Close"].pct_change()

        # Calculate returns for market indices
        market_returns = market_data["Close"].pct_change()

        for window in windows:
            # Calculate rolling beta (slope of regression line)
            df[f"beta_{window}d"] = (
                stock_returns.rolling(window).cov(market_returns)
                / market_returns.rolling(window).var()
            )

            # Calculate rolling correlation
            df[f"market_corr_{window}d"] = stock_returns.rolling(window).corr(
                market_returns
            )

            # Calculate relative strength vs market
            stock_cum_return = (
                (1 + stock_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1)
            )
            market_cum_return = (
                (1 + market_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1)
            )
            df[f"rel_strength_{window}d"] = (
                stock_cum_return / market_cum_return.replace(0, np.nan)
            )

    def _add_volatility_features(self, df, windows=[30, 60, 90]):
        """
        Add volatility and downside risk metrics

        Args:
            df (pandas.DataFrame): DataFrame with stock data
            windows (list): List of window sizes for rolling calculations
        """
        returns = df["Close"].pct_change()

        for window in windows:
            # Historical volatility (annualized)
            df[f"volatility_{window}d"] = returns.rolling(window).std() * np.sqrt(252)

            # Downside deviation (focuses only on negative returns)
            downside_returns = returns.copy()
            downside_returns[downside_returns > 0] = 0
            df[f"downside_dev_{window}d"] = downside_returns.rolling(
                window
            ).std() * np.sqrt(252)

            # Volatility ratio (recent vs longer-term)
            if window > VOLATILITY_BASE_WINDOW:
                df[f"vol_ratio_{VOLATILITY_BASE_WINDOW}_{window}d"] = (
                    df[f"volatility_{VOLATILITY_BASE_WINDOW}d"]
                    / df[f"volatility_{window}d"]
                )

    def _add_distribution_features(self, df, window=90):
        """
        Add return distribution characteristics

        Args:
            df (pandas.DataFrame): DataFrame with stock data
            window (int): Window size for rolling calculations
        """
        returns = df["Close"].pct_change()

        # Calculate rolling skewness
        df[f"returns_skew_{window}d"] = returns.rolling(window).skew()

        # Calculate rolling kurtosis
        df[f"returns_kurt_{window}d"] = returns.rolling(window).kurt()

        # Calculate drawdown to volatility ratio
        if (
            f"max_drawdown_{window}d" in df.columns
            and f"volatility_{window}d" in df.columns
        ):
            df[f"drawdown_vol_ratio_{window}d"] = (
                df[f"max_drawdown_{window}d"].abs() / df[f"volatility_{window}d"]
            )

    def _add_conditional_performance(self, df, market_data, window=90):
        """
        Add performance metrics conditional on market regime

        Args:
            df (pandas.DataFrame): DataFrame with stock data
            market_data (pandas.DataFrame): DataFrame with market index data
            window (int): Window size for rolling calculations
        """
        # Get market regime (bull market when price > 200-day MA)
        if "sma_200" not in market_data.columns:
            market_data["sma_200"] = market_data["Close"].rolling(200).mean()

        bull_market = (market_data["Close"] > market_data["sma_200"]).astype(int)

        # Calculate stock returns
        returns = df["Close"].pct_change()

        # Align dates
        aligned_bull = bull_market.reindex(returns.index, method="ffill")

        # Calculate conditional returns
        bull_returns = returns.copy()
        bull_returns[aligned_bull == 0] = np.nan

        bear_returns = returns.copy()
        bear_returns[aligned_bull == 1] = np.nan

        # Calculate performance metrics in bull markets
        df[f"bull_return_{window}d"] = bull_returns.rolling(
            window, min_periods=window // 4
        ).mean()
        df[f"bull_volatility_{window}d"] = bull_returns.rolling(
            window, min_periods=window // 4
        ).std()

        # Calculate performance metrics in bear markets
        df[f"bear_return_{window}d"] = bear_returns.rolling(
            window, min_periods=window // 4
        ).mean()
        df[f"bear_volatility_{window}d"] = bear_returns.rolling(
            window, min_periods=window // 4
        ).std()

        # Calculate relative performance in different regimes
        df["bull_bear_return_ratio"] = (
            df[f"bull_return_{window}d"] / df[f"bear_return_{window}d"].abs()
        )

    def _add_risk_adjusted_target(self, df, window=90, risk_free_rate=0.05):
        """
        Calculate Sharpe ratio as target

        Args:
            df (pandas.DataFrame): DataFrame with stock data
            window (int): Window size for rolling calculations
            risk_free_rate (float): Annual risk-free rate
        """
        # Check if future return column exists (it should be added during training)
        if "future_return_90d" in df.columns and "volatility_90d" in df.columns:
            # Calculate quarterly risk-free rate
            quarterly_rfr = risk_free_rate / 4

            # Calculate Sharpe ratio
            df["target_sharpe_ratio"] = (df["future_return_90d"] - quarterly_rfr) / df[
                "volatility_90d"
            ]


def calculate_rsi(data, period=14):
    """Calculate RSI using configurable threshold"""
    if len(data) < MIN_DATA_DAYS:
        return None

    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi < RSI_THRESHOLD


def calculate_stochastic(data, period=14):
    if len(data) < period:
        return None

    low_min = data["Low"].rolling(window=period).min()
    high_max = data["High"].rolling(window=period).max()

    k = 100 * ((data["Close"] - low_min) / (high_max - low_min))
    k.rolling(window=3).mean()

    # Use constants instead of magic numbers
    return (k < STOCH_THRESHOLD_LOW) | (k > STOCH_THRESHOLD_HIGH)


def analyze_volume_trend(data):
    """Analyze volume trend using configurable threshold"""
    if len(data) < MIN_DATA_DAYS:
        return None

    avg_volume = data["Volume"].mean()
    current_volume = data["Volume"].iloc[-1]

    return current_volume > (avg_volume * (1 + VOLUME_THRESHOLD / 100))


if __name__ == "__main__":
    # Simple test
    from src.v2.data_fetcher import DataFetcher

    fetcher = DataFetcher()
    data = fetcher.fetch_data("AAPL", period="1y", force_sample=True)

    features = Features()
    feature_df = features.generate(data, use_enhanced_features=True)

    if feature_df is not None:
        print(f"Generated {len(feature_df.columns)} features")
        print(feature_df.columns.tolist())
