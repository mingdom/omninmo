# ADX Implementation Plan

## Overview
The Average Directional Index (ADX) measures trend strength regardless of direction. It helps distinguish between strong trending markets and sideways/consolidating markets, which aligns with our goal of improving feature stability and reducing false signals.

## Feature Details

### Purpose
- Identify strong trends regardless of direction (up or down)
- Filter out sideways/consolidation periods
- Provide context for other technical indicators
- Reduce false signals during non-trending periods

### Technical Background
ADX is a component of the Directional Movement System developed by J. Welles Wilder. It combines:
- Plus Directional Indicator (+DI): Measures upward price movement strength
- Minus Directional Indicator (-DI): Measures downward price movement strength
- Average Directional Index (ADX): Measures overall trend strength

ADX values are interpreted as:
- 0-25: Weak or no trend (sideways market)
- 25-50: Strong trend
- 50-75: Very strong trend
- 75-100: Extremely strong trend

## Implementation Details

### New Features
- `adx`: The ADX value (0-100 scale)
- `adx_trend_strength`: Binary indicator for strong trend (ADX > 25)

### Code Implementation
```python
def _add_adx(self, df, period=14):
    """Add Average Directional Index (ADX)"""
    # Calculate +DI and -DI
    high_diff = df['High'].diff()
    low_diff = df['Low'].diff().multiply(-1)
    
    plus_dm = (high_diff > low_diff) & (high_diff > 0)
    plus_dm = high_diff.where(plus_dm, 0)
    
    minus_dm = (low_diff > high_diff) & (low_diff > 0)
    minus_dm = low_diff.where(minus_dm, 0)
    
    # Calculate ATR
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # Calculate +DI and -DI
    plus_di = 100 * plus_dm.rolling(period).mean() / atr
    minus_di = 100 * minus_dm.rolling(period).mean() / atr
    
    # Calculate DX and ADX
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    df['adx'] = dx.rolling(period).mean()
    df['adx_trend_strength'] = (df['adx'] > 25).astype(int)
    
    return df
```

### Integration Steps
1. Add the `_add_adx` method to the `Features` class in `src/v2/features.py`
2. Call this method from the `generate` method after other technical indicators
3. Add the new features to the `keep_columns` list
4. Update documentation in `docs/features.md`

### Testing Approach
1. Verify ADX calculation against known examples
2. Check for NaN values and handling of edge cases
3. Validate trend strength identification on sample stocks:
   - Strong uptrend: NVDA (2023)
   - Strong downtrend: META (2022)
   - Sideways market: KO (2023)
4. Compare with external ADX calculations for verification

## Expected Impact

### Model Performance
- Improved feature stability score (target > 0.8)
- Maintained or improved R² (target > 0.7)
- Better performance across different market regimes

### Prediction Quality
- Reduced false signals in sideways markets
- More accurate trend identification
- Better context for existing technical indicators
- Improved signal quality in consolidation periods

### Feature Importance
- Expected ADX importance: 3-5%
- Potential synergy with existing trend indicators
- May reduce importance of noisy features

## Success Metrics
1. **Primary Metrics**
   - Feature stability score improvement (target > 0.8)
   - Cross-validation R² maintained above 0.65
   - ADX feature importance > 3%

2. **Secondary Metrics**
   - Reduced prediction variance in sideways markets
   - Improved performance on stocks with clear trends
   - Better handling of consolidation periods

## Implementation Timeline
- Implementation: 1 day
- Testing and validation: 1 day
- Model training and evaluation: 1 day
- Documentation and review: 0.5 day

## Next Steps After Implementation
1. Evaluate ADX performance and impact on model
2. Consider implementing +DI and -DI as additional features if beneficial
3. Proceed with Linear Regression Slope feature if ADX shows positive results
4. Fine-tune ADX parameters based on performance analysis 