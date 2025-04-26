# 2024-04-15: Added Mode Parameter to Train Function

## Changes Made

1. **Enhanced Train Function**
   - Added `mode` parameter to `train_model()` function in `src/v2/train.py`
   - Supports both 'classification' and 'regression' modes
   - Implemented conditional logic for target preparation based on mode
   - Added rating category conversion for classification mode

2. **Implementation Details**
   - Classification mode converts returns to 5 rating categories (0-4)
   - Rating thresholds: Strong Buy (>15%), Buy (>5%), Hold (>-5%), Sell (>-15%), Strong Sell (≤-15%)
   - Regression mode continues to use raw returns or risk-adjusted targets

## Benefits

1. **Flexibility**
   - Allows switching between classification and regression approaches
   - Supports different prediction use cases with the same codebase
   - Enables comparison between classification and regression performance

2. **Improved Model Interpretability**
   - Classification provides clear rating categories
   - More intuitive for end users to understand predictions

## Technical Details

- Modified: `src/v2/train.py`
- Added parameter: `mode` (default value from config)
- Classification target: Integer values 0-4 representing rating categories
- Regression target: Unchanged (future returns or risk-adjusted returns)

## Next Steps

1. Update model evaluation metrics to handle both classification and regression outputs
2. Consider adding classification report metrics for classification mode
3. Test performance differences between classification and regression approaches
