# Remove Confidence Metric

## Goal
The goal was to remove the non-meaningful confidence metric that was hardcoded to 0.7, making the prediction output cleaner and more honest about what we can actually measure.

## Changes Made

### Modified Files
- `src/v2/predictor.py`: Updated predict() method to return 3-tuple
- `src/v2/console_app.py`: Updated to handle 3-tuple return value

### Key Changes
1. Removed hardcoded confidence value from predictor.predict()
2. Updated return type to (predicted_return, score, rating)
3. Removed confidence from console output display
4. Updated docstrings to reflect new return types

## Approach
Used a minimal change approach to remove the placeholder metric:
1. Only modified the specific lines related to confidence
2. Kept all other functionality intact
3. Updated documentation to reflect changes

## Testing
Verified changes by running `make predict` successfully. The command now completes without errors and displays a cleaner output without the meaningless confidence metric.

## Future Enhancement Note
If confidence measurement is needed in the future, it should be implemented properly using:
- Prediction intervals from the model
- Model uncertainty estimates
- Cross-validation variance
- Ensemble disagreement metrics 