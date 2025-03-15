# Risk-Adjusted Model Enhancement - Phase 1 Implementation

**Date:** 2023-05-15  
**Author:** Development Team  
**Status:** Completed

## Overview

This log documents the implementation of Phase 1 of the risk-adjusted model enhancement plan. The goal of this phase was to address the issue of our model consistently assigning "Strong Buy" ratings to high-beta, volatile "meme stocks" by implementing enhanced risk metrics and a risk-adjusted target variable.

## Implementation Details

### 1. Enhanced Features Implementation

We enhanced the existing `Features` class with additional risk metrics by adding new methods and parameters:

- Added a `use_enhanced_features` parameter to the `generate` method to control whether to generate enhanced risk-adjusted features
- Added a `market_data` parameter to the `generate` method to provide market index data for beta calculations

The enhanced risk metrics include:

- **Beta and Market Sensitivity Features**:
  - Rolling beta calculation (60-day and 120-day)
  - Correlation with market indices
  - Relative strength vs. market

- **Volatility and Downside Risk Metrics**:
  - Historical volatility over multiple timeframes (30, 60, 90 days)
  - Downside deviation (focusing on negative returns)
  - Volatility ratio (comparing recent to longer-term volatility)

- **Return Distribution Characteristics**:
  - Skewness (asymmetry of returns)
  - Kurtosis (tailedness of returns)
  - Drawdown to volatility ratio

- **Conditional Performance Metrics**:
  - Performance in bull markets
  - Performance in bear markets
  - Bull/bear return ratio

### 2. Risk-Adjusted Target Variable

We implemented a risk-adjusted target variable using the Sharpe ratio:

```python
# Calculate Sharpe ratio as target
quarterly_rfr = 0.05 / 4  # Quarterly risk-free rate (assuming 5% annual)
df['target_sharpe_ratio'] = (df['future_return_90d'] - quarterly_rfr) / df['volatility_90d']
```

This transforms our prediction target from raw returns to risk-adjusted returns, which should help the model better account for the risk associated with high-volatility stocks.

### 3. Data Fetcher Enhancement

We enhanced the `DataFetcher` class to fetch market data (S&P 500) for beta calculations:

```python
def fetch_market_data(self, market_index='SPY', period='5y', interval='1d', force_sample=False):
    """Fetch market index data for beta calculations"""
    return self.fetch_data(market_index, period, interval, force_sample)
```

### 4. Training Process Updates

We updated the training process to support the enhanced features and risk-adjusted target:

- Added options to use enhanced features and risk-adjusted target
- Added market data fetching for beta calculations
- Modified the target variable selection based on configuration

## Testing Results

We created a test script (`scripts/test_risk_adjusted_model.py`) to evaluate the performance of the enhanced model. The script compares three models:

1. **Standard Model**: Using the original features and raw returns as target
2. **Enhanced Model**: Using the enhanced features but still with raw returns as target
3. **Risk-Adjusted Model**: Using the enhanced features with Sharpe ratio as target

### Key Findings

1. **Feature Importance**: The risk metrics (especially beta and volatility) are now among the top features in the enhanced model.

2. **Model Performance**: The risk-adjusted model shows improved R² and RMSE compared to the standard model.

3. **High-Beta Stock Predictions**: The risk-adjusted model assigns lower predicted returns to high-beta stocks compared to the standard model, which is the desired behavior.

4. **Ratio of High-Beta to Other Stocks**: The ratio of predicted returns for high-beta stocks to other stocks is significantly lower in the risk-adjusted model, indicating that the model is now properly accounting for risk.

## Next Steps

1. **Production Deployment**: Deploy the enhanced model to production after thorough validation.

2. **Phase 2 Planning**: Begin planning for Phase 2 (Market Regime Awareness) implementation.

3. **Monitoring**: Set up monitoring to track the performance of the enhanced model, particularly focusing on high-beta stocks during market downturns.

## Conclusion

Phase 1 of the risk-adjusted model enhancement plan has been successfully implemented. The enhanced model now properly accounts for risk when making predictions, which should help address the issue of assigning inappropriately high ratings to high-beta, volatile stocks. The risk-adjusted target variable (Sharpe ratio) has proven effective in balancing return expectations with risk considerations.

By implementing these enhancements directly in the existing `Features` class rather than creating a new class, we've maintained a simpler project structure while still achieving the desired functionality. This approach makes it easier to maintain and update the features in the future. 