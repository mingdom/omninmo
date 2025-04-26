# Fix Portfolio Data Processing Errors

**Date**: 2025-04-02

## Overview

This development log documents the fixes implemented to address several errors that were occurring during portfolio data processing:

1. Downgraded "No historical data found" errors to warnings
2. Fixed `'float' object has no attribute 'rstrip'` errors when processing NaN values in the Symbol column
3. Improved handling of non-string inputs in cash-like position detection functions

## Issues and Fixes

### 1. "No historical data found" Errors

**Issue**: The application was logging errors when it couldn't find historical data for certain symbols like "021ESC017" and "Pending Activity". These errors were not actionable and should be warnings instead.

**Fix**: 
- Modified `src/v2/data_fetcher.py` to return an empty DataFrame with appropriate columns instead of raising an exception when no historical data is found
- Updated `get_beta` function in `src/folio/utils.py` to handle "No historical data found" errors gracefully by logging a warning and returning a default beta value of 0.0

```python
if "No historical data found" in str(e):
    # This is not a critical error - just log a warning
    logger.warning(f"Error calculating beta for {ticker}: {e}. Assuming not cash-like.")
    return 0.0
```

### 2. `'float' object has no attribute 'rstrip'` Errors

**Issue**: The application was trying to call `rstrip()` on `symbol_raw` in the `process_portfolio_data` function, but `symbol_raw` was sometimes a float (NaN) instead of a string.

**Fix**: Added validation to check if `symbol_raw` is a string before calling `rstrip()`:

```python
# Handle NaN or non-string symbols
if pd.isna(symbol_raw) or not isinstance(symbol_raw, str):
    logger.warning(
        f"Row {index}: Invalid symbol type: {type(symbol_raw)}. Skipping."
    )
    continue
```

### 3. Non-String Inputs in Cash-Like Position Detection

**Issue**: The `is_likely_money_market` and `is_cash_or_short_term` functions were assuming string inputs, but sometimes received NaN or other non-string values.

**Fix**: Updated both functions to handle non-string inputs:

```python
# Handle NaN, None, or non-string inputs
if pd.isna(ticker) or ticker is None:
    return False

# Convert to string if needed
if not isinstance(ticker, str):
    try:
        ticker = str(ticker)
    except:
        return False
```

## Testing

The changes were tested by running the application with the sample portfolio data and verifying that:

1. "No historical data found" messages now appear as warnings instead of errors
2. No `'float' object has no attribute 'rstrip'` errors occur
3. The application processes the portfolio data correctly, including handling of cash-like positions

## Conclusion

These fixes improve the robustness of the portfolio data processing by:

1. Properly distinguishing between actionable errors and expected conditions
2. Adding proper type checking before operations that require specific types
3. Handling edge cases in the data more gracefully

The application now processes the portfolio data more reliably, with fewer unnecessary error messages in the logs.
