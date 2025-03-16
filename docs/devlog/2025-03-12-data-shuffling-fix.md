# Data Shuffling Fix for Training Pipeline

## Issue
The training pipeline was producing identical results across different runs due to data being processed and combined in a deterministic order (by ticker and date), leading to identical splits during cross-validation even with random seeds.

## Changes Made
- Modified `train_model` function in `src/v2/train.py` to shuffle the combined dataset before training
- Added random shuffling using `np.random.permutation` to ensure different splits in each run
- Maintained feature-target alignment during shuffling
- Added logging of data types and sample values for debugging

## Impact
- Cross-validation now produces different splits each run
- Results show proper variation between runs while maintaining overall model stability
- Example from two consecutive runs:

Run 1:
```
Mean RMSE: 0.2618 ± 0.0088
Mean R²: 0.6713 ± 0.0282
Feature stability: 0.6968
```

Run 2:
```
Mean RMSE: 0.2615 ± 0.0098
Mean R²: 0.6735 ± 0.0130
Feature stability: 0.7431
```

## Benefits
1. More reliable cross-validation results
2. Better assessment of model generalization
3. Reduced risk of overfitting to specific data splits
4. More accurate feature importance stability scores

## Next Steps
- Monitor feature stability scores over multiple runs
- Consider implementing stratified sampling if needed
- Add tests to verify data shuffling behavior 