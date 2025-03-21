Date: March 21, 2025

# Development Plan: Market Cycle Detection and Volatility-Adjusted Momentum Indicators

## Overview

This development plan outlines the implementation approach for two advanced feature engineering techniques identified in our future experiments document:

1. **Cycle detection algorithms for market regime identification**
2. **Custom momentum indicators with volatility adjustment**

These features aim to enhance our prediction model's ability to adapt to changing market conditions and improve performance across different volatility regimes.

## 1. Cycle Detection Algorithms

### Concept

Market cycles represent recurring patterns in price movements, often categorized into four main phases:
- Accumulation (bottoming)
- Markup (bullish trend)
- Distribution (topping)
- Markdown (bearish trend)

Detecting the current market cycle/regime can provide valuable context for other technical indicators and potentially improve prediction accuracy by allowing the model to learn regime-specific patterns.

### Implementation Approach

#### 1.1 Hilbert Transform Cycle Indicators

The Hilbert Transform can decompose price series into cyclical components:

```python
def add_hilbert_cycle_indicators(df):
    """Add Hilbert Transform cycle indicators"""
    # Import required libraries
    from scipy import signal
    
    # Calculate analytic signal using Hilbert transform
    analytic_signal = signal.hilbert(df['close'].values)
    
    # Extract amplitude envelope (instantaneous amplitude)
    df['amplitude_envelope'] = np.abs(analytic_signal)
    
    # Extract instantaneous phase
    df['instantaneous_phase'] = np.unwrap(np.angle(analytic_signal))
    
    # Calculate instantaneous frequency
    df['instantaneous_frequency'] = np.diff(df['instantaneous_phase'], 
                                          prepend=df['instantaneous_phase'][0]) / (2.0*np.pi)
    
    # Calculate dominant cycle period (in days)
    window = 20  # lookback window for dominant cycle estimation
    df['dominant_cycle'] = df['instantaneous_frequency'].rolling(window).mean().apply(
        lambda x: 1/x if x != 0 else 0)
    
    return df
```

#### 1.2 Fourier Transform for Cycle Detection

Implement spectral analysis using the Fast Fourier Transform (FFT) to identify dominant cycles:

```python
def add_fft_cycle_features(df, periods=[10, 20, 40, 60]):
    """Add cycle detection features using FFT"""
    from scipy.fftpack import fft
    
    # Detrend the price series
    detrended = signal.detrend(df['close'].values)
    
    # Compute FFT
    fft_values = fft(detrended)
    fft_mag = np.abs(fft_values[:len(detrended)//2])
    
    # Find dominant frequencies
    dominant_periods = []
    for i in range(3):  # Get top 3 dominant periods
        if len(fft_mag) > i:
            idx = np.argsort(fft_mag)[-i-1] if i < len(fft_mag) else 0
            period = len(detrended) / (idx + 1) if idx > 0 else 0
            dominant_periods.append(period)
    
    # Calculate cycle phase features for specified periods
    for period in periods:
        if period > 0:
            df[f'cycle_{period}_phase'] = np.sin(2 * np.pi * np.arange(len(df)) / period)
            df[f'cycle_{period}_amplitude'] = np.abs(
                df['close'].rolling(period).apply(
                    lambda x: np.corrcoef(x, np.sin(2 * np.pi * np.arange(len(x)) / period))[0, 1]
                    if len(x) == period else np.nan)
            )
    
    # Add dominant cycle information
    df['dominant_cycle_1'] = dominant_periods[0] if dominant_periods else 0
    df['dominant_cycle_2'] = dominant_periods[1] if len(dominant_periods) > 1 else 0
    
    return df
```

#### 1.3 Hidden Markov Models for Regime Detection

Implement a Hidden Markov Model to identify latent market regimes:

```python
def add_hmm_regime_features(df, n_regimes=3, lookback=252):
    """Add Hidden Markov Model regime detection features"""
    from hmmlearn import hmm
    
    # Function to fit HMM and predict regimes
    def fit_hmm_predict(data, n_components):
        model = hmm.GaussianHMM(n_components=n_components, 
                               covariance_type="full", 
                               n_iter=1000)
        model.fit(data)
        states = model.predict(data)
        return states
    
    # Prepare features for HMM (returns and volatility)
    features = np.column_stack([
        df['return_1d'].fillna(0).values,
        df['volatility_20d'].fillna(df['volatility_20d'].mean()).values
    ])
    
    # Initialize regime column
    df['market_regime'] = np.nan
    
    # Rolling window approach for HMM (to avoid lookahead bias)
    for i in range(lookback, len(df)):
        window_data = features[i-lookback:i]
        if len(window_data) >= lookback:  # Ensure we have enough data
            regimes = fit_hmm_predict(window_data, n_regimes)
            df.loc[df.index[i], 'market_regime'] = regimes[-1]
    
    # Convert regime to one-hot encoding for the model
    for i in range(n_regimes):
        df[f'regime_{i}'] = (df['market_regime'] == i).astype(float)
    
    return df
```

### Integration with Features Module

Add these functions to the `features.py` module and update the `generate()` method:

```python
def _add_cycle_detection(self, df):
    """Add market cycle detection features"""
    logger.debug("Generating cycle detection features")
    
    # Skip if not enough data
    if len(df) < MIN_DATA_DAYS:
        logger.warning("Not enough data for cycle detection")
        return df
    
    # Add Hilbert transform cycle indicators
    df = self.add_hilbert_cycle_indicators(df)
    
    # Add FFT-based cycle features for specific periods
    periods = [5, 10, 20, 40, 60]  # Common market cycles in trading days
    df = self.add_fft_cycle_features(df, periods)
    
    # Only add HMM features if sufficient data
    if len(df) >= 252:  # One year of data
        df = self.add_hmm_regime_features(df)
    
    return df
```

## 2. Custom Momentum Indicators with Volatility Adjustment

### Concept

Traditional momentum indicators can generate false signals during high volatility periods. Volatility-adjusted momentum indicators dynamically adjust their sensitivity based on recent market volatility, potentially improving signal quality across different market conditions.

### Implementation Approach

#### 2.1 Volatility-Adjusted RSI

Modify the standard RSI to incorporate volatility:

```python
def add_volatility_adjusted_rsi(df, period=14, vol_period=20):
    """Calculate volatility-adjusted RSI"""
    # Calculate standard RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Calculate volatility
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=vol_period).std() * np.sqrt(252)  # Annualized
    
    # Normalize volatility to a scale factor (higher volatility = less sensitivity)
    vol_median = volatility.median()
    vol_ratio = vol_median / volatility
    vol_ratio = vol_ratio.clip(0.5, 2.0)  # Limit adjustment range
    
    # Adjust RSI based on volatility
    df['vol_adj_rsi'] = 50 + (rsi - 50) * vol_ratio
    
    # Additional RSI-volatility derived signals
    df['rsi_vol_ratio'] = rsi / (volatility * 100)  # Momentum per unit of risk
    
    return df
```

#### 2.2 Volatility-Adjusted Momentum

Create a momentum indicator that normalizes by recent volatility:

```python
def add_volatility_adjusted_momentum(df, momentum_periods=[10, 20, 60], vol_period=20):
    """Add volatility-adjusted momentum indicators"""
    # Calculate volatility
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=vol_period).std() * np.sqrt(252)
    
    for period in momentum_periods:
        # Standard momentum (price change over period)
        momentum = df['close'] / df['close'].shift(period) - 1
        
        # Volatility-adjusted momentum (excess returns per unit of risk)
        df[f'vol_adj_momentum_{period}d'] = momentum / volatility
        
        # Z-score of momentum relative to its own history
        rolling_mean = momentum.rolling(window=252).mean()
        rolling_std = momentum.rolling(window=252).std()
        df[f'momentum_{period}d_zscore'] = (momentum - rolling_mean) / rolling_std
    
    return df
```

#### 2.3 Adaptive Trend Strength Indicator

Create an indicator that measures trend strength with volatility adaptation:

```python
def add_adaptive_trend_strength(df, short_period=20, long_period=50, vol_period=20):
    """Add adaptive trend strength indicator"""
    # Calculate short and long moving averages
    short_ma = df['close'].rolling(window=short_period).mean()
    long_ma = df['close'].rolling(window=long_period).mean()
    
    # Calculate trend direction and strength
    trend_direction = np.sign(short_ma - long_ma)
    trend_magnitude = (short_ma / long_ma - 1) * 100  # Percentage difference
    
    # Calculate volatility
    returns = df['close'].pct_change()
    volatility = returns.rolling(window=vol_period).std() * np.sqrt(252)
    
    # Normalize trend magnitude by volatility
    df['adaptive_trend_strength'] = trend_direction * trend_magnitude / volatility
    
    # Create regime based on adaptive trend strength
    df['trend_regime'] = 0  # Neutral/ranging
    df.loc[df['adaptive_trend_strength'] > 0.5, 'trend_regime'] = 1  # Strong uptrend
    df.loc[df['adaptive_trend_strength'] < -0.5, 'trend_regime'] = -1  # Strong downtrend
    
    return df
```

### Integration with Features Module

Add these functions to the `features.py` module and update the `generate()` method:

```python
def _add_volatility_adjusted_momentum(self, df):
    """Add volatility-adjusted momentum indicators"""
    logger.debug("Generating volatility-adjusted momentum indicators")
    
    # Skip if not enough data
    if len(df) < MIN_DATA_DAYS:
        logger.warning("Not enough data for volatility-adjusted momentum")
        return df
    
    # Add volatility-adjusted RSI
    df = self.add_volatility_adjusted_rsi(df)
    
    # Add volatility-adjusted momentum for multiple timeframes
    momentum_periods = [5, 10, 20, 60]
    df = self.add_volatility_adjusted_momentum(df, momentum_periods)
    
    # Add adaptive trend strength indicator
    df = self.add_adaptive_trend_strength(df)
    
    return df
```

## Implementation Plan

### Phase 1: Development and Integration (2 weeks)

1. **Week 1: Core Implementation**
   - Develop and test cycle detection algorithms
   - Implement volatility-adjusted momentum indicators
   - Write comprehensive unit tests for each function

2. **Week 2: Integration and Optimization**
   - Integrate new functions into the features module
   - Update the `generate()` method to include new features
   - Optimize performance for large datasets
   - Add configuration parameters to control feature generation

### Phase 2: Testing and Evaluation (2 weeks)

1. **Week 3: Validation**
   - Generate features for historical data
   - Analyze feature distributions and correlations
   - Verify absence of look-ahead bias
   - Test with different market regimes (bull, bear, sideways)

2. **Week 4: Model Performance Testing**
   - Train models with and without new features
   - Compare performance metrics (RMSE, MAE, R²)
   - Analyze feature importance to assess new features' value
   - Test in different market conditions

### Phase 3: Documentation and Deployment (1 week)

1. **Documentation**
   - Update feature documentation
   - Add examples to developer guide
   - Create visualization tools for new features

2. **Deployment**
   - Create configuration parameters for production
   - Deploy to staging environment
   - Monitor performance and resource usage

## Expected Outcomes

After implementing these features, we expect:

1. **Improved Model Performance**
   - Better prediction accuracy during market transitions
   - Reduced false signals during high volatility periods
   - More adaptive response to changing market conditions

2. **Enhanced Feature Importance**
   - New cycle and regime features should appear in top feature importance
   - Volatility-adjusted momentum indicators should outperform standard versions

3. **Better Risk-Adjusted Returns**
   - Recommendations should have better risk-adjusted performance
   - Lower drawdowns during regime transitions

## Resource Requirements

- **Development**: 1 backend developer (full-time, 3 weeks)
- **Data Science**: 1 data scientist (part-time, 2 weeks for evaluation)
- **Computing**: Additional processing power for feature generation
- **Dependencies**: 
  - scipy (for signal processing functions)
  - hmmlearn (for Hidden Markov Models)
  - statsmodels (for additional statistical tests)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Increased computational load | Slower feature generation | Optimize critical functions, make features optional |
| Look-ahead bias | Unrealistic performance | Careful implementation of rolling calculations, thorough testing |
| Increased model complexity | Potential overfitting | Regularization, feature selection, cross-validation |
| Noisy regime detection | Unreliable signals | Ensemble multiple detection methods, add smoothing |

## Conclusion

Implementing cycle detection algorithms and volatility-adjusted momentum indicators represents a significant enhancement to our feature engineering capabilities. These features should help our model better adapt to changing market conditions and improve performance across different volatility regimes.

By following this development plan, we can systematically implement, test, and deploy these enhancements while minimizing risks and ensuring measurable improvements to our prediction model. 