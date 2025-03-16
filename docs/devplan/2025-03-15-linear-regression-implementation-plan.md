# Linear Regression Slope Implementation Plan

## Overview
The Linear Regression Slope feature measures trend strength and direction using statistical methods. It helps identify steady trends versus erratic price movements and quantifies trend quality through a more sophisticated approach than traditional technical indicators.

## Feature Details

### Purpose
- Quantify trend strength and direction using statistical methods
- Differentiate between steady trends and erratic price movements
- Measure trend quality through R-squared values
- Provide a more objective measure of trend characteristics

### Technical Background
Linear regression in the context of price analysis:
- Fits a straight line to price data over a specified period
- Slope indicates trend direction and strength
- R-squared measures how well prices follow the trend line
- Higher R-squared values indicate more consistent trends
- Normalized slope allows comparison across different price levels

## Implementation Details

### New Features
- `lr_slope_90d`: Raw slope value from linear regression (absolute price change per day)
- `lr_slope_pct`: Normalized slope as percentage of average price (relative change)
- `lr_r2_90d`: R-squared value indicating trend quality (0-1 scale)

### Code Implementation
```python
def _add_linear_regression(self, df, window=90):
    """Add Linear Regression features"""
    # Calculate indices for rolling windows
    indices = np.array(range(window))
    
    # Function to calculate slope for a window
    def calc_slope(window_prices):
        if len(window_prices) < window:
            return np.nan
        return np.polyfit(indices, window_prices, 1)[0]
    
    # Calculate rolling slope
    df['lr_slope_90d'] = df['Close'].rolling(window=window).apply(
        calc_slope, raw=True
    )
    
    # Normalize slope to percentage
    df['lr_slope_pct'] = df['lr_slope_90d'] / df['Close'].rolling(window=window).mean() * 100
    
    # Trend strength from R-squared
    def calc_r2(window_prices):
        if len(window_prices) < window:
            return np.nan
        slope, intercept = np.polyfit(indices, window_prices, 1)
        fitted = indices * slope + intercept
        r2 = 1 - np.sum((window_prices - fitted) ** 2) / np.sum((window_prices - np.mean(window_prices)) ** 2)
        return r2
    
    df['lr_r2_90d'] = df['Close'].rolling(window=window).apply(
        calc_r2, raw=True
    )
    
    return df
```

### Integration Steps
1. Add the `_add_linear_regression` method to the `Features` class in `src/v2/features.py`
2. Call this method from the `generate` method after basic price features
3. Add the new features to the `keep_columns` list
4. Update documentation in `docs/features.md`

### Testing Approach
1. Verify calculations against manual examples and external tools
2. Test on different trend types:
   - Strong uptrend: NVDA (2023)
   - Choppy uptrend: XOM (2023)
   - Sideways market: KO (2023)
   - Downtrend: META (2022)
3. Validate R-squared as a trend quality measure
4. Assess computational performance (may be more intensive than simple indicators)
5. Check for NaN handling and edge cases

## Expected Impact

### Model Performance
- Improved identification of high-quality trends
- Better differentiation between steady and erratic price movements
- Enhanced feature stability through more objective trend measurement
- Potential synergy with existing trend indicators

### Prediction Quality
- More accurate identification of sustainable trends
- Reduced exposure to choppy, low-quality price movements
- Better risk-adjusted returns through focus on quality trends
- Improved medium-term prediction accuracy

### Feature Importance
- Expected importance of lr_r2_90d: 3-6%
- Expected importance of lr_slope_pct: 2-4%
- May reduce importance of more volatile indicators

## Success Metrics
1. **Primary Metrics**
   - Feature stability score improvement
   - Cross-validation R² maintained or improved
   - Linear regression features in top 10 importance

2. **Secondary Metrics**
   - Improved performance on stocks with steady trends
   - Reduced exposure to erratic price movements
   - Better differentiation between trend types
   - Computational efficiency (processing time < 10% increase)

## Implementation Timeline
- Implementation: 1-2 days
- Testing and validation: 1 day
- Model training and evaluation: 1 day
- Documentation and review: 0.5 day

## Next Steps After Implementation
1. Evaluate linear regression feature performance
2. Consider additional timeframes (30d, 180d) if beneficial
3. Explore trend change detection using slope changes
4. Investigate combining with ADX for enhanced trend quality assessment
5. Proceed with MA Acceleration feature if results are positive 