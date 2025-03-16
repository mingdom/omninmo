# MA Compression/Expansion Implementation Plan

## Overview
The Moving Average Compression/Expansion feature measures the spacing between moving averages to identify potential breakout opportunities and market regime changes. Tight compression often precedes strong moves, while expansion indicates an established trend.

## Feature Details

### Purpose
- Identify potential breakout opportunities
- Detect market regime changes
- Provide early signals for volatility expansion
- Reduce false trend signals during compression periods

### Technical Background
Moving average compression/expansion analysis is based on the concept that:
- Moving averages tend to converge during consolidation periods
- Extreme compression often precedes significant price moves
- Expansion indicates an established trend
- The relationship between short-term and long-term MA spacing provides context
- Historical compression extremes are particularly significant

## Implementation Details

### New Features
- `ma_dist_8_21`: Distance between 8-day and 21-day EMAs (normalized)
- `ma_dist_50_200`: Distance between 50-day and 200-day SMAs (normalized)
- `ma_compression_ratio`: Ratio of short-term to long-term MA distances
- `ma_compressed`: Binary indicator for extreme compression events

### Code Implementation
```python
def _add_ma_compression(self, df):
    """Add Moving Average Compression/Expansion features"""
    # Calculate distances between key MAs
    df['ma_dist_8_21'] = (df['ema_8'] - df['ema_21']).abs() / df['Close'] * 100
    df['ma_dist_50_200'] = (df['sma_50'] - df['sma_200']).abs() / df['Close'] * 100
    
    # Calculate normalized compression ratio
    df['ma_compression_ratio'] = df['ma_dist_8_21'] / df['ma_dist_50_200']
    
    # Identify extreme compression (bottom 10% of historical values)
    df['ma_compressed'] = (
        df['ma_compression_ratio'] < df['ma_compression_ratio'].rolling(252).quantile(0.1)
    ).astype(int)
    
    return df
```

### Integration Steps
1. Add the `_add_ma_compression` method to the `Features` class in `src/v2/features.py`
2. Call this method after moving averages are calculated in the `generate` method
3. Add the new features to the `keep_columns` list
4. Update documentation in `docs/features.md`

### Testing Approach
1. Verify calculations on sample data
2. Test on known compression/expansion examples:
   - Pre-breakout compression: NVDA (late 2022)
   - Strong trend expansion: AAPL (early 2023)
   - Prolonged consolidation: KO (mid-2023)
3. Validate breakout prediction capability
4. Check for NaN handling and edge cases
5. Assess computational performance (rolling quantile may be intensive)

## Expected Impact

### Model Performance
- Improved identification of potential breakout opportunities
- Better timing of entry signals
- Enhanced feature stability through regime context
- Potential reduction in false trend signals

### Prediction Quality
- Earlier detection of emerging trends
- Reduced exposure to false breakouts
- Better handling of consolidation periods
- Improved context for other technical indicators

### Feature Importance
- Expected importance of ma_compressed: 2-4%
- Expected importance of ma_compression_ratio: 1-3%
- May show higher importance during market transitions
- Likely to complement trend strength indicators

## Success Metrics
1. **Primary Metrics**
   - Feature stability score improvement
   - Cross-validation R² maintained or improved
   - Improved performance during trend transitions

2. **Secondary Metrics**
   - Better identification of breakout opportunities
   - Reduced false signals during consolidation
   - Improved timing of trend-based predictions
   - Computational efficiency (processing time < 10% increase)

## Implementation Timeline
- Implementation: 1 day
- Testing and validation: 1 day
- Model training and evaluation: 1 day
- Documentation and review: 0.5 day

## Next Steps After Implementation
1. Evaluate MA compression feature performance
2. Consider additional MA pairs if beneficial
3. Explore adaptive thresholds based on volatility
4. Investigate combining with ADX and trend consistency
5. Evaluate overall Phase 2B/2C feature performance 