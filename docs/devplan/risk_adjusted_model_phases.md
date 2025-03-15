# Risk-Adjusted Model Enhancement: Phased Implementation Plan

## Overview

This document outlines a phased approach to implementing the risk-adjusted model enhancement plan. Each phase is designed to be:

1. **Independently valuable** - Delivers measurable improvements on its own
2. **Self-contained** - Can be evaluated without depending on future phases
3. **Decision-enabling** - Provides clear metrics to decide whether to proceed to the next phase
4. **Risk-managed** - Limits complexity and potential for regression

The goal is to address the critical issue of high-beta "meme stocks" receiving inappropriately high ratings while maintaining model stability and performance.

## Phase 1: Beta and Volatility Features

### Objective
Add explicit risk metrics that directly address the high-beta stock issue while maintaining the current model architecture.

### Why This Approach
The core issue is that our model doesn't have explicit features measuring a stock's sensitivity to market movements (beta) or its volatility characteristics. By adding these features while keeping the same model architecture and target variable, we can:

1. Directly address the root cause (missing beta/volatility metrics)
2. Minimize implementation complexity and risk
3. Evaluate whether these features alone can reduce the meme stock bias
4. Establish a foundation for more sophisticated changes if needed

### Implementation Details

#### 1. Beta Calculation
```python
def add_beta_features(df, market_data, windows=[60, 120]):
    """
    Calculate beta against market indices
    """
    # Get market returns (S&P 500)
    market_returns = market_data['Close'].pct_change()
    
    # Calculate stock returns
    stock_returns = df['Close'].pct_change()
    
    for window in windows:
        # Calculate rolling beta
        cov = stock_returns.rolling(window).cov(market_returns)
        var = market_returns.rolling(window).var()
        df[f'beta_{window}d'] = cov / var
        
        # Calculate correlation with market
        df[f'market_corr_{window}d'] = stock_returns.rolling(window).corr(market_returns)
    
    return df
```

**Why**: Beta directly measures a stock's sensitivity to market movements. High-beta stocks like PLTR, IONQ, and AI typically have beta values >1.5, making them much more volatile than the market. By explicitly including beta, we give the model a direct measure of market sensitivity.

**Expected Impact**: The model will recognize that high-beta stocks carry significantly more market risk, potentially reducing their predicted returns or ratings.

#### 2. Volatility Metrics
```python
def add_volatility_features(df, windows=[30, 60, 90]):
    """
    Add historical volatility and downside risk metrics
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
    df['vol_ratio_30_90d'] = df['volatility_30d'] / df['volatility_90d']
    
    return df
```

**Why**: Volatility captures the magnitude of price swings, while downside deviation specifically focuses on downside risk. Meme stocks typically have much higher volatility and downside deviation than more stable stocks. The volatility ratio helps identify stocks with increasing volatility, which often precedes major price movements.

**Expected Impact**: The model will have explicit measures of both overall volatility and downside risk, helping it distinguish between stocks with similar return potential but different risk profiles.

#### 3. Return Distribution Characteristics
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

**Why**: Skewness and kurtosis capture the shape of the return distribution. Negative skewness indicates more frequent small gains but occasional large losses, while high kurtosis indicates fat tails (more extreme events than a normal distribution). The drawdown-to-volatility ratio normalizes drawdown by volatility, providing a measure of how severe drawdowns are relative to overall volatility.

**Expected Impact**: The model will be able to identify stocks with asymmetric risk profiles (larger drawdowns than their volatility would suggest) and those with particularly dangerous return distributions.

### Evaluation Framework

#### 1. Individual Stock Metrics
- Track changes in ratings for known high-beta stocks (PLTR, IONQ, AI, etc.)
- Compare feature importance of new risk metrics vs. existing features
- Evaluate prediction accuracy across different volatility quintiles

#### 2. Portfolio-Based Evaluation
```python
def evaluate_portfolio_performance(model, test_data, market_data, top_n=10):
    """
    Evaluate performance of a portfolio based on model recommendations
    """
    # Get model predictions
    predictions = model.predict(test_data)
    
    # Select top N stocks based on predictions
    top_stocks = predictions.sort_values(by='predicted_return', ascending=False).head(top_n)
    
    # Create equal-weighted portfolio
    portfolio_returns = []
    for date in test_period:
        daily_return = 0
        for stock in top_stocks:
            daily_return += stock_returns.loc[date, stock] / top_n
        portfolio_returns.append(daily_return)
    
    # Calculate portfolio metrics
    portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
    portfolio_sharpe = (np.mean(portfolio_returns) * 252 - risk_free_rate) / portfolio_volatility
    portfolio_max_drawdown = calculate_max_drawdown(portfolio_returns)
    
    # Compare to benchmark (S&P 500)
    benchmark_returns = market_data['Close'].pct_change()
    benchmark_volatility = np.std(benchmark_returns) * np.sqrt(252)
    benchmark_sharpe = (np.mean(benchmark_returns) * 252 - risk_free_rate) / benchmark_volatility
    benchmark_max_drawdown = calculate_max_drawdown(benchmark_returns)
    
    return {
        'portfolio_return': np.mean(portfolio_returns) * 252,
        'portfolio_volatility': portfolio_volatility,
        'portfolio_sharpe': portfolio_sharpe,
        'portfolio_max_drawdown': portfolio_max_drawdown,
        'benchmark_return': np.mean(benchmark_returns) * 252,
        'benchmark_volatility': benchmark_volatility,
        'benchmark_sharpe': benchmark_sharpe,
        'benchmark_max_drawdown': benchmark_max_drawdown
    }
```

**Why Portfolio-Based Evaluation**: This approach evaluates how the model's recommendations would perform in practice, not just how accurate individual predictions are. It aligns with how users would actually apply the model's recommendations - by constructing a portfolio of top-rated stocks.

**Expected Impact**: We should see reduced drawdowns and improved risk-adjusted returns (Sharpe ratio) compared to the current model, particularly during market corrections.

### Success Metrics for Phase 1

1. **Meme Stock Ranking**: Reduction in high-beta stocks receiving "Strong Buy" ratings
   - Target: No more than 1 high-beta stock (beta > 1.5) in top 5 recommendations

2. **Portfolio Risk-Adjusted Performance**:
   - Target: 15% improvement in portfolio Sharpe ratio
   - Target: 20% reduction in maximum drawdown during recent corrections

3. **Feature Importance**:
   - Target: At least 2 new risk metrics in top 10 important features
   - Target: Maintain or improve feature stability score (currently 0.7727)

4. **Prediction Accuracy**:
   - Target: Maintain R² > 0.65 while improving risk adjustment
   - Target: Improved prediction accuracy for high-volatility stocks

### Go/No-Go Decision Criteria
- If 3+ success metrics are met: Proceed to Phase 2
- If 1-2 success metrics are met: Refine Phase 1 implementation before proceeding
- If 0 success metrics are met: Reconsider approach before proceeding

## Phase 2: Risk-Adjusted Target Variable

### Objective
Modify the target variable to predict risk-adjusted returns (Sharpe ratio) instead of raw returns.

### Why This Approach
If Phase 1 doesn't sufficiently address the meme stock issue, changing what we're asking the model to predict represents a more fundamental solution. By predicting Sharpe ratio instead of raw returns, we explicitly incorporate risk into the target variable itself.

### Key Implementation Components
1. Calculate historical Sharpe ratio for each stock
2. Modify target variable to predict future Sharpe ratio
3. Adjust evaluation metrics to focus on risk-adjusted performance
4. Keep the same features and model architecture from Phase 1

### Success Metrics
1. Further reduction in high-beta stocks receiving high ratings
2. Improved portfolio performance during market corrections
3. More balanced distribution of ratings across different volatility quintiles
4. Maintained or improved feature stability score

## Phase 3: Market Regime Awareness

### Objective
Add features that identify the current market regime and how stocks perform in different regimes.

### Why This Approach
High-beta stocks tend to outperform in bull markets and underperform in bear markets. By adding market regime awareness, we can help the model understand this context and make more nuanced predictions.

### Key Implementation Components
1. Add market regime classification features
2. Add conditional performance metrics (performance in bull vs. bear markets)
3. Keep the risk-adjusted target from Phase 2
4. Keep the same model architecture

### Success Metrics
1. Improved performance across different market regimes
2. Reduced drawdowns during market corrections
3. More consistent performance over time
4. Maintained or improved feature stability score

## Phase 4: Two-Stage Modeling

### Objective
Implement a two-stage modeling approach with separate models for return prediction and risk prediction.

### Why This Approach
This represents a more significant architectural change that should only be attempted after the feature engineering phases have been validated. It allows specialized models for return and risk, potentially improving both predictions.

### Key Implementation Components
1. Develop separate return prediction model
2. Develop separate risk prediction model
3. Combine predictions to create a risk-adjusted score
4. Compare performance to the single-model approach

### Success Metrics
1. Improved prediction accuracy for both returns and risk
2. Better overall risk-adjusted performance
3. More transparent decision-making process
4. Maintained or improved feature stability score

## Timeline and Resources

### Phase 1: Beta and Volatility Features
- **Timeline**: 1-2 weeks
- **Key Resources**: Historical market index data (S&P 500)
- **Dependencies**: None

### Phase 2: Risk-Adjusted Target Variable
- **Timeline**: 1-2 weeks
- **Key Resources**: None
- **Dependencies**: Successful completion of Phase 1

### Phase 3: Market Regime Awareness
- **Timeline**: 2-3 weeks
- **Key Resources**: Market regime classification data
- **Dependencies**: Successful completion of Phase 2

### Phase 4: Two-Stage Modeling
- **Timeline**: 3-4 weeks
- **Key Resources**: None
- **Dependencies**: Successful completion of Phase 3

## Conclusion

This phased approach allows us to address the meme stock issue in a systematic, incremental manner. Each phase builds on the previous one, but also delivers value on its own. By evaluating the results after each phase, we can make informed decisions about whether and how to proceed with subsequent phases.

Phase 1 focuses on adding explicit risk metrics while maintaining the current model architecture, providing a low-risk starting point that directly addresses the root cause of the issue. If successful, it may be sufficient on its own. If not, subsequent phases offer increasingly sophisticated approaches to the problem. 