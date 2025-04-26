# Fix for Non-String Symbols in Portfolio Data

## Issue

When loading portfolio data with non-string symbol values (like numeric IDs, None values, or NaN), the application was crashing with an `AttributeError: 'float' object has no attribute 'rstrip'`. This occurred in the `process_portfolio_data` function in `utils.py` when it tried to call `rstrip("*")` on a symbol that was a float instead of a string.

The error was identified in the portfolio loading logs:
```
ERROR: Error updating portfolio data: 'float' object has no attribute 'rstrip'
Traceback (most recent call last):
  File "/Users/dongming/projects/omninmo/src/folio/app.py", line 448, in update_portfolio_data
    groups, summary = process_portfolio_data(df)
  File "/Users/dongming/projects/omninmo/src/folio/utils.py", line 334, in process_portfolio_data
    clean_symbol = symbol.rstrip("*")  # Clean symbol for checks
AttributeError: 'float' object has no attribute 'rstrip'
```

## Fix

1. Modified the `process_portfolio_data` function to check if a symbol is a string before calling `rstrip("*")`:

```python
# Check if symbol is a string, convert if not
if not isinstance(symbol, str):
    logger.debug(f"Converting non-string symbol to string: {symbol}")
    symbol = str(symbol) if symbol is not None else ""

# Now safely get clean_symbol
clean_symbol = symbol.rstrip("*")  # Clean symbol for checks
```

2. Added a new test file `tests/test_portfolio_non_string_symbol.py` to verify the fix:
   - Created test fixtures with various non-string symbols (numbers, None, NaN)
   - Added tests to verify the function handles these symbols without errors
   - Confirmed that valid positions are still processed correctly

## Validation

All tests now pass, including the existing test suite and the new tests specifically for non-string symbols. The fix allows the application to:

1. Convert numeric symbols to strings
2. Handle None and NaN values safely
3. Continue processing valid positions

The fix is minimally invasive, ensuring that we maintain backward compatibility while adding robustness for edge cases found in real portfolio data files.

## Best Practices

This fix follows our established best practices:

1. **Defensive Programming**: Added type checking before operations that assume a specific type
2. **Clear Logging**: Added debug logs to indicate when non-string symbols are encountered
3. **Test Coverage**: Created comprehensive tests to verify the fix and prevent regression
4. **Minimal Changes**: Only modified what was necessary to fix the specific issue

The fix ensures we can handle a wider variety of real-world portfolio data without breaking the application. 