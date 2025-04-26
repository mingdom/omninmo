# Fix Missing Prediction Output

## Issue
The `make predict` command was no longer displaying the prediction results table. While the command was successfully fetching data and making predictions (as evidenced by the logging output), the actual prediction table was not being shown to the user.

## Root Cause
In `src/v2/console_app.py`'s `main()` function, we were calling `run_predictions()` but not capturing or printing its return value. The `run_predictions()` method returns a formatted string (table/CSV/JSON) that needs to be printed to stdout.

## Changes Made
1. Updated the `main()` function in `src/v2/console_app.py` to:
   - Capture the output from `run_predictions()`
   - Print the results to stdout
   - Add proper error handling
   - Add a "Prediction Results:" header for better readability

## Impact
- The `make predict` command now properly displays the prediction results table
- Added error handling for prediction failures
- Improved user experience with better output formatting

## Testing
To verify the fix:
1. Run `make predict` without specifying tickers
2. The command should now show:
   - The data fetching logs
   - A "Prediction Results:" header
   - The formatted prediction table 