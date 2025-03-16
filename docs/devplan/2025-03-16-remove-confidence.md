# Development Plan: Remove Confidence Metric

## Background
Currently, the prediction system includes a confidence metric that is hardcoded to 0.7 and doesn't provide meaningful information. This plan outlines the minimal changes needed to remove this placeholder metric.

## Current State
- `predictor.predict()` returns a 4-tuple: (predicted_return, score, rating, confidence)
- Confidence is hardcoded to 0.7 in predictor.py
- Console output displays this non-meaningful confidence value

## Proposed Changes

### 1. Modify Predictor Class
**File**: `src/v2/predictor.py`
- Remove hardcoded confidence value
- Update `predict()` method to return 3-tuple: (predicted_return, score, rating)
- Update docstring to reflect new return type

### 2. Update Console App
**File**: `src/v2/console_app.py`
- Update tuple unpacking to expect 3 values instead of 4
- Remove confidence from results dictionary
- Remove confidence from display output

### 3. Documentation
- Document changes in devlog
- Update any relevant docstrings

## Why This Approach
1. **Minimal Impact**: Only changes what's necessary to remove the placeholder metric
2. **Clean Code**: Removes rather than maintains meaningless data
3. **No Functionality Loss**: The removed confidence value wasn't providing real information

## Future Enhancement Path
If confidence measurement is needed in the future, it should be implemented properly using one or more of:
- Prediction intervals from the model
- Model uncertainty estimates
- Cross-validation variance
- Ensemble disagreement metrics

## Testing Plan
1. Run `make predict` to verify changes
2. Verify console output format is correct
3. Verify no regression in prediction functionality

## Rollback Plan
If issues are encountered:
1. Revert commits
2. Restore original 4-tuple return type
3. Restore confidence display in console output 