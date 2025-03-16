# Random State Fix - March 12, 2024

## Issue
We discovered that the model was showing perfect consistency in performance metrics and feature importance across different training runs. This was traced to two issues:
1. Fixed random state (42) in model initialization
2. Reuse of the same model instance across cross-validation folds

## Changes Made
1. Modified `Predictor` class to use dynamic random states based on current timestamp
2. Updated `cross_validate` method to create new model instances for each fold
3. Updated `train` method to use fresh random state for final model training

## Impact
Comparing runs before and after the fix:

### Before Fix
- Cross-validation R²: 0.6809 ± 0.0131 (identical across runs)
- Feature stability score: 0.7882
- Top feature: `bb_std`

### After Fix
- Cross-validation R²: 0.6723 ± 0.0260 (varies between runs)
- Feature stability score: 0.6547
- Top features: `sma_50`, `max_drawdown_90d`

## Implications
1. Model now shows expected natural variation in performance
2. Lower feature stability score indicates more realistic feature importance variability
3. Different top features emerging suggests better exploration of feature space

## Next Steps
1. Monitor model performance across multiple runs to establish baseline variability
2. Consider increasing number of cross-validation folds if needed
3. May need to adjust feature stability threshold based on new baseline 