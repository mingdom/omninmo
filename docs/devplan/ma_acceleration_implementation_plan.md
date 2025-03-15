# MA Acceleration Implementation Plan

## Overview
The Moving Average Acceleration feature measures the rate of change in moving average slopes, identifying strengthening or weakening trends by analyzing the second derivative of price movement. This feature provides early signals of trend changes before they become apparent in price or other indicators.

## Feature Details

### Purpose
- Detect early signs of trend acceleration or deceleration
- Identify momentum shifts before they appear in price
- Provide leading indicators for trend changes
- Quantify the strength of trend momentum

### Technical Background
Moving average acceleration uses calculus concepts applied to price data:
- First derivative (velocity): Rate of change in moving averages
- Second derivative (acceleration): Rate of change in velocity
- Positive acceleration indicates strengthening trend
- Negative acceleration indicates weakening trend
- Zero crossing in acceleration often precedes trend changes

## Implementation Details

### New Features
- `ema_21_velocity`: First derivative of EMA-21 (rate of change)
- `sma_50_velocity`: First derivative of SMA-50 (rate of change)
- `ema_21_accel_norm`: Normalized second derivative of EMA-21 (acceleration)
- `sma_50_accel_norm`: Normalized second derivative of SMA-50 (acceleration)

### Code Implementation
```python
def _add_ma_acceleration(self, df):
    """Add Moving Average Acceleration features"""
    # Calculate first derivative (velocity)
    df['ema_21_velocity'] = df['ema_21'].diff(5) / 5
    df['sma_50_velocity'] = df['sma_50'].diff(10) / 10
    
    # Calculate second derivative (acceleration)
    df['ema_21_accel'] = df['ema_21_velocity'].diff(5) / 5
    df['sma_50_accel'] = df['sma_50_velocity'].diff(10) / 10
    
    # Normalize by price level
    df['ema_21_accel_norm'] = df['ema_21_accel'] / df['Close'] * 100
    df['sma_50_accel_norm'] = df['sma_50_accel'] / df['Close'] * 100
    
    return df
```

### Integration Steps
1. Add the `_add_ma_acceleration` method to the `Features` class in `src/v2/features.py`
2. Call this method after moving averages are calculated in the `generate` method
3. Add the new features to the `keep_columns` list
4. Update documentation in `docs/features.md`

### Testing Approach
1. Verify calculations on sample data
2. Test on known trend acceleration/deceleration examples:
   - Accelerating uptrend: NVDA (early 2023)
   - Decelerating uptrend: AAPL (mid-2023)
   - Trend reversal: META (late 2022 to early 2023)
3. Check for excessive noise in the signal
4. Validate as a leading indicator for trend changes
5. Assess lag/lead characteristics compared to price movements

## Expected Impact

### Model Performance
- Earlier detection of trend changes
- Improved timing of entry/exit signals
- Enhanced feature stability through trend momentum context
- Potential reduction in false signals

### Prediction Quality
- More responsive to changing market conditions
- Better identification of sustainable vs. fading trends
- Improved timing of trend-based predictions
- Reduced lag in trend change identification

### Feature Importance
- Expected importance of acceleration features: 2-4%
- May show higher importance during volatile markets
- Likely to complement existing trend indicators

## Success Metrics
1. **Primary Metrics**
   - Feature stability score improvement
   - Cross-validation R² maintained or improved
   - Lead time advantage in trend change detection

2. **Secondary Metrics**
   - Reduced lag in prediction adjustments
   - Improved performance during trend transitions
   - Better handling of acceleration/deceleration phases
   - Computational efficiency (processing time < 5% increase)

## Implementation Timeline
- Implementation: 1 day
- Testing and validation: 1 day
- Model training and evaluation: 1 day
- Documentation and review: 0.5 day

## Next Steps After Implementation
1. Evaluate acceleration feature performance
2. Consider signal smoothing if noise is excessive
3. Explore zero-crossing events as specific signals
4. Investigate combining with ADX and linear regression
5. Proceed with Phase 2C features if results are positive 