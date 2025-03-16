# Risk-Adjusted Model Enhancement Plan

## Problem Statement

Our current stock prediction model exhibits a critical flaw: it consistently assigns "Strong Buy" ratings with high predicted returns to high-beta, volatile "meme stocks" like PLTR, IONQ, and AI. These stocks are particularly vulnerable in bear markets, creating significant downside risk for users following our recommendations.

Despite implementing risk metrics like maximum drawdown (which is our most important feature at 0.1187 importance), the model continues to favor these high-volatility stocks. This suggests our current approach to risk-adjustment is insufficient.

## Root Cause Analysis

After careful analysis, we've identified several key issues:

1. **Missing Beta/Market Sensitivity Metrics**: The model lacks features that explicitly measure a stock's sensitivity to market movements.

2. **Raw Return Prediction**: By predicting raw returns rather than risk-adjusted returns, high-volatility stocks naturally show higher potential returns.

3. **Insufficient Risk Quantification**: Our current risk metrics don't adequately capture the asymmetric nature of risk in volatile stocks.

4. **Market Regime Blindness**: The model doesn't have explicit knowledge of the current market regime (bull vs. bear) or how stocks perform in different regimes.

5. **Single-Model Approach**: Using a single model to predict returns may not adequately balance risk and return considerations.

## Enhanced Approach

We propose a comprehensive three-phase approach to address these issues:

### Phase 1: Risk-Adjusted Target Transformation

#### 1.1 Beta and Market Sensitivity
- **Rolling Beta Calculation**: Add 60-day and 120-day beta against major indices (S&P 500, NASDAQ)
- **Correlation Features**: Add correlation with market indices over multiple timeframes
- **Sector-Relative Performance**: Add metrics comparing stock performance to sector averages

```python
def add_beta_features(df, market_data, window=60):
    """
    Calculate beta and correlation with market indices
    """
    # Calculate returns for the stock
    stock_returns = df['Close'].pct_change()
    
    # Calculate returns for market indices
    market_returns = market_data['Close'].pct_change()
    
    # Calculate rolling beta (slope of regression line)
    df[f'beta_{window}d'] = stock_returns.rolling(window).cov(market_returns) / market_returns.rolling(window).var()
    
    # Calculate rolling correlation
    df[f'market_corr_{window}d'] = stock_returns.rolling(window).corr(market_returns)
    
    # Calculate relative strength vs market
    df[f'rel_strength_{window}d'] = (1 + stock_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1) / \
                                   (1 + market_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1)
    
    return df
```

#### 1.2 Volatility and Downside Risk
- **Historical Volatility**: Add rolling volatility over multiple timeframes
- **Downside Deviation**: Add metrics focusing specifically on negative returns
- **Volatility Ratio**: Compare recent volatility to historical volatility

```python
def add_volatility_features(df, windows=[30, 60, 90]):
    """
    Add volatility and downside risk metrics
    """
    returns = df['Close'].pct_change()
    
    for window in windows:
        # Historical volatility (annualized)
        df[f'volatility_{window}d'] = returns.rolling(window).std() * np.sqrt(252)
        
        # Downside deviation (focuses only on negative returns)
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        df[f'downside_dev_{window}d'] = downside_returns.rolling(window).std() * np.sqrt(252)
        
        # Volatility ratio (recent vs longer-term)
        if window > 30:
            df[f'vol_ratio_30_{window}d'] = df[f'volatility_30d'] / df[f'volatility_{window}d']
    
    return df
```

#### 1.3 Risk-Adjusted Target Variable
Instead of predicting raw returns, modify our target variable to predict risk-adjusted returns:

```python
# Calculate Sharpe ratio as target
target_returns = df['future_return_90d']
target_volatility = df['volatility_90d']
risk_free_rate = 0.05/4  # Quarterly risk-free rate (assuming 5% annual)

df['target_sharpe_ratio'] = (target_returns - risk_free_rate) / target_volatility
```

#### 1.4 Success Metrics for Phase 1
- Reduction in high-beta stocks receiving "Strong Buy" ratings
- Improved risk-adjusted performance of recommended stocks
- Maintain prediction accuracy (R² > 0.65) while improving risk adjustment

### Phase 2: Market Regime Awareness

#### 2.1 Market Regime Classification
Add features that identify the current market regime:

```python
def add_market_regime_features(df, market_data):
    """
    Add market regime classification features
    """
    # Simple trend-based regime classification
    sma_50 = market_data['Close'].rolling(50).mean()
    sma_200 = market_data['Close'].rolling(200).mean()
    
    # Bull market: 50-day SMA > 200-day SMA
    bull_market = (sma_50 > sma_200).astype(int)
    
    # Add market regime to stock data (aligned by date)
    df['market_regime_bull'] = bull_market
    
    # Add VIX (volatility index) as a feature if available
    if 'VIX' in market_data.columns:
        df['vix'] = market_data['VIX']
        
        # High volatility regime
        df['high_vol_regime'] = (market_data['VIX'] > market_data['VIX'].rolling(90).mean()).astype(int)
    
    return df
```

#### 2.2 Conditional Performance Metrics
Add features that measure performance in different market conditions:

```python
def add_conditional_performance(df, market_data, window=90):
    """
    Add performance metrics conditional on market regime
    """
    # Get market regime
    bull_market = (market_data['Close'] > market_data['Close'].rolling(200).mean()).astype(int)
    
    # Calculate stock returns
    returns = df['Close'].pct_change()
    
    # Align dates
    aligned_bull = bull_market.reindex(returns.index, method='ffill')
    
    # Calculate conditional returns
    bull_returns = returns.copy()
    bull_returns[aligned_bull == 0] = np.nan
    
    bear_returns = returns.copy()
    bear_returns[aligned_bull == 1] = np.nan
    
    # Calculate performance metrics in bull markets
    df[f'bull_return_{window}d'] = bull_returns.rolling(window, min_periods=window//4).mean()
    df[f'bull_volatility_{window}d'] = bull_returns.rolling(window, min_periods=window//4).std()
    
    # Calculate performance metrics in bear markets
    df[f'bear_return_{window}d'] = bear_returns.rolling(window, min_periods=window//4).mean()
    df[f'bear_volatility_{window}d'] = bear_returns.rolling(window, min_periods=window//4).std()
    
    # Calculate relative performance in different regimes
    df[f'bull_bear_return_ratio'] = df[f'bull_return_{window}d'] / df[f'bear_return_{window}d'].abs()
    
    return df
```

#### 2.3 Conditional Feature Importance Analysis
- Analyze feature importance in different market regimes
- Identify which features are most predictive in bull vs. bear markets
- Use this information to improve model robustness

#### 2.4 Success Metrics for Phase 2
- More consistent performance across different market regimes
- Better downside protection during market corrections
- Improved feature stability score (target > 0.8)

### Phase 3: Advanced Risk Modeling

#### 3.1 Return Distribution Characteristics
- **Skewness**: Add metrics capturing the asymmetry of returns
- **Kurtosis**: Add metrics capturing the "tailedness" of returns
- **Maximum Drawdown Ratio**: Compare drawdown to volatility

```python
def add_distribution_features(df, window=90):
    """
    Add return distribution characteristics
    """
    returns = df['Close'].pct_change()
    
    # Calculate rolling skewness
    df[f'returns_skew_{window}d'] = returns.rolling(window).skew()
    
    # Calculate rolling kurtosis
    df[f'returns_kurt_{window}d'] = returns.rolling(window).kurt()
    
    # Calculate drawdown to volatility ratio
    if f'max_drawdown_{window}d' in df.columns and f'volatility_{window}d' in df.columns:
        df[f'drawdown_vol_ratio_{window}d'] = df[f'max_drawdown_{window}d'].abs() / df[f'volatility_{window}d']
    
    return df
```

#### 3.2 Tail Risk Metrics
- Implement Value at Risk (VaR) calculations
- Add Conditional Value at Risk (CVaR) metrics
- Develop custom tail risk indicators

#### 3.3 Ensemble Approaches for Different Market Conditions
- Explore specialized models for different market regimes
- Implement model blending based on market conditions
- Develop a meta-model approach for combining predictions

#### 3.4 Success Metrics for Phase 3
- Further reduction in maximum drawdown during extreme market conditions
- Improved performance in tail risk scenarios
- Enhanced model robustness across all market conditions

## Implementation Plan

Each phase in our approach is designed to be independently valuable and testable, allowing us to evaluate results before proceeding to the next phase.

### Phase 1: Risk-Adjusted Target Transformation (1-4 weeks)
1. **Week 1-2**: Implement beta and volatility features
   - Add rolling beta calculation
   - Add historical volatility metrics
   - Add downside deviation features

2. **Week 3-4**: Implement risk-adjusted target variable
   - Modify target variable to predict Sharpe ratio
   - Update evaluation framework to measure risk-adjusted performance
   - Train and evaluate model with new target and features

### Phase 2: Market Regime Awareness (2-4 weeks)
1. **Week 1-2**: Implement market regime features
   - Add market regime classification
   - Add conditional performance metrics
   - Evaluate feature importance in different regimes

2. **Week 3-4**: Enhance evaluation framework
   - Implement regime-specific performance metrics
   - Develop stress testing for different market conditions
   - Evaluate model performance across different regimes

### Phase 3: Advanced Risk Modeling (3-6 weeks)
1. **Week 1-2**: Implement tail risk features
   - Add skewness and kurtosis metrics
   - Implement VaR and CVaR calculations
   - Add sentiment and volatility regime features

2. **Week 3-4**: Explore ensemble approaches
   - Develop specialized models for different market conditions
   - Implement model blending techniques
   - Evaluate ensemble performance

3. **Week 5-6**: Fine-tune and optimize
   - Optimize feature selection
   - Fine-tune model parameters
   - Conduct comprehensive evaluation

## Success Metrics

1. **Primary Metrics**
   - **Meme Stock Ranking**: Reduction in high-beta stocks receiving "Strong Buy" ratings
   - **Risk-Adjusted Returns**: Improve Sharpe ratio of recommended stocks by at least 15%
   - **Prediction Accuracy**: Maintain R² > 0.65 while improving risk adjustment

2. **Secondary Metrics**
   - **Feature Stability**: Maintain or improve feature stability score (target > 0.8)
   - **Market Regime Performance**: Consistent performance across bull and bear markets
   - **Tail Risk Protection**: Reduced impact during extreme market events

## Revised Roadmap Impact

This plan represents a significant shift in our feature engineering roadmap:

1. **Deprioritize**: Linear Regression Slope and MA Acceleration features
2. **Prioritize**: Beta, volatility, and risk-adjusted return features
3. **Add**: Two-stage modeling approach and risk-adjusted target variables
4. **Accelerate**: Market regime detection features

## Conclusion

The proposed risk-adjusted model enhancement plan directly addresses the critical issue of meme stocks receiving inappropriately high ratings. By implementing enhanced risk metrics, risk-adjusted targets, and model architecture improvements, we can create a more balanced recommendation system that properly accounts for the downside risk of high-volatility stocks.

This approach maintains our focus on feature stability and predictive performance while adding a crucial dimension of risk awareness that was previously insufficient. The result will be a more robust model that performs well across different market regimes and provides more reliable recommendations for all types of stocks. 