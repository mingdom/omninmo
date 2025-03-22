# Remove Sample Data Functionality

## Overview
Refactoring the codebase to remove the sample data functionality and always use real data from the API.

## Changes
1. data_fetcher.py:
   - Remove `force_sample` parameter from `fetch_data` and `fetch_market_data` methods
   - Always require API key
   - Move sample data generation to a separate test module

2. train.py:
   - Remove `force_sample` parameter from `train_model` function
   - Update function calls to remove sample data option

3. console_app.py:
   - Remove `use_sample_data` parameter from `run_predictions` method
   - Update related code paths

4. Scripts:
   - Remove `--force-sample` argument from v2_train.py
   - Remove `--sample` argument from v2_predict.py

5. Test Updates:
   - Update test code to use real data or mock responses
   - Move sample data generation to dedicated test utilities

## Rationale
- Simplify codebase by removing unnecessary complexity
- Ensure consistent behavior by always using real data
- Better align with production use cases
- Improve code maintainability

## Impact
- API key will now be required for all operations
- Tests will need to be updated to use real data or mocks
- No more synthetic data generation in main code path

## Migration
Users will need to:
1. Always provide an API key
2. Update any scripts that used sample data
3. Use real data for testing or implement proper mocks 