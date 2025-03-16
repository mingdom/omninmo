# Trend Consistency Score Implementation Plan

## Overview
The Trend Consistency Score measures how consistently price moves in the trend direction, penalizing whipsaw movements and rewarding steady trends. This feature focuses on the quality of trends rather than just their strength or direction, aligning with our system's shift toward quality and stability.

## Feature Details

### Purpose
- Measure the consistency of price movements within a trend
- Identify stocks with steady, reliable trends
- Reduce exposure to erratic price movements
- Quantify trend quality beyond simple strength metrics

### Technical Background
Trend consistency evaluates how well daily price movements align with the overall trend:
- Overall trend direction is determined by comparing current price to price N days ago
- Daily price movements are compared to the overall trend direction
- Higher scores indicate more days moving in the same direction as the overall trend
- Lower scores indicate erratic, whipsaw movements despite an overall trend
- This metric complements trend strength indicators by focusing on movement quality

## Implementation Details

### New Features
- `trend_direction`: Sign of the overall trend (+1 for uptrend, -1 for downtrend)
- `trend_consistency`: Percentage of days moving in the same direction as the overall trend (0-1 scale)

### Code Implementation
```python
def _add_trend_consistency(self, df, window=90):
    """Add Trend Consistency Score"""
    # Determine trend direction over window
    df['trend_direction'] = np.sign(df['Close'] - df['Close'].shift(window))
    
    # Count days moving in trend direction
    daily_moves = np.sign(df['Close'].diff(1))
    
    def consistency_score(window_moves, trend_dir):
        if np.isnan(trend_dir):
            return np.nan
        # Calculate percentage of days moving in trend direction
        matching_days = (window_moves * trend_dir > 0).sum()
        return matching_days / len(window_moves)
    
    # Calculate rolling consistency score
    df['trend_consistency'] = df.rolling(window=window).apply(
        lambda x: consistency_score(
            x['Close'].diff(1).apply(np.sign).values,
            x['trend_direction'].iloc[-1]
        ),
        raw=False
    )
    
    return df
```

### Integration Steps
1. Add the `_add_trend_consistency` method to the `Features` class in `src/v2/features.py`
2. Call this method from the `generate` method after basic price features
3. Add the new features to the `keep_columns` list
4. Update documentation in `docs/features.md`

### Testing Approach
1. Verify calculations on sample data
2. Test on different trend quality examples:
   - Steady uptrend: MSFT (2023)
   - Erratic uptrend: TSLA (2023)
   - Steady downtrend: TDOC (2022)
   - Erratic downtrend: BYND (2022)
3. Validate correlation with risk-adjusted returns
4. Assess computational performance (custom rolling function may be intensive)
5. Check for NaN handling and edge cases

## Expected Impact

### Model Performance
- Improved identification of high-quality trends
- Better risk-adjusted returns through focus on consistent trends
- Enhanced feature stability through quality filtering
- Potential reduction in drawdowns

### Prediction Quality
- More accurate identification of sustainable trends
- Reduced exposure to whipsaw price movements
- Better differentiation between quality and noisy trends
- Improved medium-term prediction reliability

### Feature Importance
- Expected importance of trend_consistency: 3-6%
- May show synergy with drawdown and stability metrics
- Likely to complement existing trend indicators

## Success Metrics
1. **Primary Metrics**
   - Feature stability score improvement
   - Cross-validation R² maintained or improved
   - Reduced maximum drawdown in predictions

2. **Secondary Metrics**
   - Improved performance on stocks with consistent trends
   - Reduced exposure to erratic price movements
   - Better risk-adjusted returns in backtests
   - Computational efficiency (processing time < 15% increase)

## Implementation Timeline
- Implementation: 1-2 days
- Testing and validation: 1 day
- Model training and evaluation: 1 day
- Documentation and review: 0.5 day

## Next Steps After Implementation
1. Evaluate trend consistency feature performance
2. Consider additional timeframes (30d, 180d) if beneficial
3. Explore combining with ADX for enhanced trend quality assessment
4. Investigate relationship with risk metrics
5. Proceed with MA Compression/Expansion feature if results are positive 