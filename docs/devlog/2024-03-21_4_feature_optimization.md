# Feature Optimization (March 21, 2024)

## Overview
Implemented feature optimization recommendations from the roadmap to reduce redundancy and improve model efficiency. The changes focus on removing highly correlated features while maintaining predictive power.

## Changes Implemented

### Feature Removals
1. **Return Metrics**
   - Removed `return_5d` and `return_10d` (high correlation with other return metrics)
   - Kept `return_1d`, `return_20d`, and `return_60d` for short/medium/long-term signals

2. **Moving Averages**
   - Removed `close_to_ema_8` and `ema_8` from feature list (kept `ema_8` calculation for crossover only)
   - Kept `ema_21` provides better short-term trend signals
   - Maintained key crossover signals

3. **Bollinger Bands**
   - Removed redundant bands (`bb_middle`, `bb_upper`, `bb_lower`)
   - Kept essential components (`bb_std`, `bb_width`, `bb_pct_b`)
   - Optimized calculations to use temporary variables

### Feature Count Changes
- Previous feature count: 38
- Current feature count: 31
- Reduction: 7 features (18.4%)

### Rationale
1. **Return Features**
   - Short-term returns (5d, 10d) showed high correlation with 1d returns
   - 20d and 60d returns provide cleaner medium-term signals
   - Log returns maintained for statistical properties

2. **Moving Average Features**
   - EMA-8 relative position was noisy and less reliable
   - EMA-21 provides better short-term trend signals
   - Maintained key crossover signals

3. **Bollinger Band Features**
   - Middle band duplicated SMA calculation
   - Upper/lower bands not needed after calculating %B
   - Width and %B capture essential volatility information

## Next Steps
1. Train new model with optimized feature set
2. Compare performance metrics:
   - Feature stability score (target: >0.8)
   - Cross-validation R² (maintain >0.7)
   - Prediction consistency across market regimes
3. Monitor feature importance distribution
4. Consider implementing Phase 2B features if needed

## Technical Details
- Modified: src/v2/features.py
- Previous feature stability: 0.7882
- Target feature count range: 30-35 (currently 31)
- Implementation follows research suggesting optimal range of 30-40 features 