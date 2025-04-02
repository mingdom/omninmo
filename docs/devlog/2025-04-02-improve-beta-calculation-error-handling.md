# Improve Beta Calculation Error Handling

**Date**: 2025-04-02

## Overview

This development log documents improvements to the beta calculation error handling in the Folio application. The changes ensure that:

1. The `get_beta` function properly raises exceptions for missing data instead of returning 0.0
2. The `is_cash_or_short_term` function properly handles these exceptions
3. Symbols with no historical data are not incorrectly classified as cash-like positions
4. Tests are properly mocked to avoid real API calls

## Issue Analysis

We identified several issues with the current error handling:

1. The `get_beta` function was returning 0.0 for symbols with no historical data, which was misleading since it implied a specific beta value (zero correlation with the market) rather than indicating missing data.

2. This was causing symbols with no historical data to be incorrectly classified as cash-like positions (since beta < 0.1).

3. Tests were not properly mocking the `get_beta` function, leading to real API calls and inconsistent test results.

## Implementation

### 1. Improved `get_beta` Function

Modified the `get_beta` function to raise exceptions for missing data instead of returning 0.0:

```python
if "No historical data found" in str(e):
    # This is not a critical error - just log a warning
    logger.warning(f"Error calculating beta for {ticker}: {e}. Unable to determine beta.")
    # Re-raise with a more specific message
    raise ValueError(f"No historical data available for beta calculation: {ticker}") from e
```

### 2. Enhanced `is_cash_or_short_term` Function

Restructured the `is_cash_or_short_term` function to:

1. First check for known cash-like symbols based on patterns
2. Only attempt beta calculation if pattern matching fails
3. Properly handle exceptions from beta calculation

```python
# Check if it's a known cash-like symbol based on patterns before attempting beta calculation
if ticker in ["CASH", "USD"] or is_likely_money_market(ticker, description):
    logger.debug(f"Symbol {ticker} identified as cash-like based on pattern matching.")
    return True
    
# Calculate beta if not provided
try:
    calculated_beta = get_beta(ticker)
    return abs(calculated_beta) < 0.1
except ValueError as e:
    # Handle specific case of no historical data
    if "No historical data available for beta calculation" in str(e):
        logger.warning(f"Cannot classify {ticker} as cash-like: {e}")
        # Not enough information to classify as cash-like
        return False
    else:
        # Other value errors
        logger.warning(f"Error calculating beta for {ticker}: {e}. Assuming not cash-like.")
        return False
```

### 3. Updated Tests

Modified the `test_pattern_based_detection` test to properly mock the `get_beta` function:

```python
def test_pattern_based_detection(mock_get_beta):
    """Test pattern-based detection of money market funds."""
    # Set up mock to return a default beta value
    mock_get_beta.return_value = 0.5  # Non-cash-like beta
    
    # Test XX pattern in symbol
    assert is_cash_or_short_term("SPAXX")
    # ...
```

## Testing

The changes were tested by:

1. Running the specific test that was failing: `python -m pytest tests/test_cash_detection.py::test_pattern_based_detection -v`
2. Running all tests to ensure no regressions: `make test`

All tests now pass, confirming that our changes have fixed the issues without introducing new problems.

## Conclusion

These improvements make the application more robust by:

1. Properly handling missing data in beta calculations
2. Ensuring that symbols with no historical data are not incorrectly classified as cash-like
3. Maintaining compatibility with existing tests and functionality

The changes align with our best practices of minimal edits, simplicity over complexity, and thorough debugging. We've also emphasized the importance of always running `make test` after any change by updating the BEST_PRACTICES.md file.
