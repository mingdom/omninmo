# Phase 2: Quality-Focused Feature Improvements

## Problem Statement
Current model shows bias towards high-volatility stocks (like IONQ, PLTR) due to:
1. Over-reliance on volatility as a predictive feature
2. Recent bull market conditions favoring speculative stocks
3. Insufficient consideration of downside risk

## Proposed Changes

### 1. Features to Remove
- All raw volatility features:
  ```python
  'volatility_10d'
  'volatility_20d'
  'volatility_60d'
  'day_range'
  'avg_range_10d'
  ```

### 2. New Feature Categories

#### A. Trend Strength Indicators
1. **Average Directional Index (ADX)**
   ```python
   def add_adx(df, period=14):
       """
       ADX measures trend strength regardless of direction
       Values > 25 indicate strong trend
       """
       # Implementation will use standard ADX calculation
       pass
   ```

2. **Linear Regression Slope**
   ```python
   def add_linear_regression(df, window=90):
       """
       Measures trend strength and direction using linear regression
       Helps identify steady trends vs erratic movement
       """
       # Calculate rolling linear regression slope
       pass
   ```

3. **MA Acceleration**
   ```python
   def add_ma_acceleration(df):
       """
       Rate of change in moving average slopes
       Identifies strengthening/weakening trends
       """
       # Calculate first and second derivatives of MAs
       pass
   ```

#### B. Risk Management Features
1. **Maximum Drawdown**
   ```python
   def add_max_drawdown(df, windows=[90, 180]):
       """
       Rolling maximum drawdown over specified windows
       Key risk metric for downside protection
       """
       # Calculate rolling max drawdown
       pass
   ```

2. **Risk-Adjusted Momentum**
   ```python
   def add_risk_adjusted_momentum(df, momentum_window=90, risk_window=90):
       """
       Momentum divided by maximum drawdown
       Rewards steady gainers over volatile movers
       """
       # Implementation details
       pass
   ```

3. **Price Stability Score**
   ```python
   def add_price_stability(df):
       """
       Percentage of time price stays above major MAs
       Higher scores indicate more stable uptrends
       """
       # Calculate stability metrics
       pass
   ```

#### C. Quality Metrics
1. **Rolling Sharpe Ratio**
   ```python
   def add_rolling_sharpe(df, window=90, risk_free_rate=0.05):
       """
       Risk-adjusted returns metric
       Higher values indicate better risk-adjusted performance
       """
       # Calculate rolling Sharpe ratio
       pass
   ```

2. **Trend Consistency Score**
   ```python
   def add_trend_consistency(df, window=90):
       """
       Measures how consistently price moves in trend direction
       Penalizes whipsaw movements
       """
       # Calculate consistency metrics
       pass
   ```

3. **MA Compression/Expansion**
   ```python
   def add_ma_compression(df):
       """
       Measures spacing between moving averages
       Tight compression often precedes strong moves
       """
       # Calculate MA relationships
       pass
   ```

## Expected Benefits

1. **Better Risk Management**
   - Early warning for potential drawdowns
   - Focus on steady performers over volatile movers
   - Better handling of market regime changes

2. **Quality Over Volatility**
   - Preference for consistent trends
   - Reduced exposure to speculative moves
   - Better risk-adjusted returns

3. **More Robust Predictions**
   - Less dependent on market conditions
   - Better handling of different market regimes
   - More emphasis on fundamental trend strength

## Implementation Plan

### Phase 2A: Core Risk Features
1. Implement maximum drawdown features
2. Add Sharpe ratio calculation
3. Remove volatility features
4. Initial testing and validation

### Phase 2B: Trend Quality Features
1. Implement ADX
2. Add linear regression features
3. Develop trend consistency metrics
4. Validation and tuning

### Phase 2C: Advanced Features
1. Implement MA acceleration
2. Add compression/expansion metrics
3. Fine-tune risk-adjusted momentum
4. Final testing and optimization

## Success Metrics

1. **Primary Metrics**
   - Lower maximum drawdown in predictions
   - More consistent R² across market regimes
   - Better performance on quality stocks vs speculative ones

2. **Secondary Metrics**
   - Reduced prediction volatility
   - Higher average Sharpe ratio of predictions
   - Better feature stability scores

## Timeline
- Phase 2A: 1 week
- Phase 2B: 1 week
- Phase 2C: 1 week
- Testing and Validation: 1 week

## Next Steps
1. Review and approve feature proposals
2. Implement Phase 2A features
3. Run initial validation tests
4. Proceed with Phase 2B based on results 