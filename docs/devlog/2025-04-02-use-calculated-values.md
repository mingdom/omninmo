# Use Calculated Values Instead of Reported Values

**Date**: 2025-04-02

## Overview

This development log documents a change in how we handle position values in the portfolio data processing pipeline. Previously, when there was a discrepancy between our calculated value (price × quantity) and the reported value from the CSV file, we would use the reported value. Now, we always use our calculated value as it's likely more up-to-date.

## Issue Analysis

When processing portfolio data, we were seeing warnings like:

```
WARNING: Row 12: Stock MELI calculated value ($80,463.05) differs from reported 'Current Value' ($81,171.89). Using reported value.
```

These warnings occurred when our calculated value (based on the current price and quantity) differed from the reported value in the CSV file. We were defaulting to using the reported value, but this might not be optimal because:

1. Our price data is likely more up-to-date since we fetch it daily
2. The portfolio CSV file might be stale or contain outdated prices
3. Using our calculated values provides more consistency across the application

## Implementation

We modified the code to always use our calculated values instead of the reported values:

```python
# Sanity check: Compare calculated value with reported 'Current Value'
if (
    quantity != 0
    and price != 0
    and abs(calculated_value - cleaned_current_value) > 0.01
):  # Tolerance for float issues
    logger.info(
        f"Row {index}: Stock {symbol} calculated value ({format_currency(calculated_value)}) differs from reported 'Current Value' ({format_currency(cleaned_current_value)}). Using calculated value as it's likely more up-to-date."
    )
# Always use our calculated value as it's likely more up-to-date
value_to_use = calculated_value
```

Key changes:
1. Changed the log level from WARNING to INFO since this is not a warning but just informational
2. Updated the message to indicate that we're using the calculated value
3. Always set `value_to_use = calculated_value` regardless of whether there's a discrepancy

## Rationale

The rationale for this change is:

1. **Data Freshness**: Our price data is likely more up-to-date than the CSV file
2. **Consistency**: Using calculated values provides more consistency across the application
3. **Accuracy**: The calculated value is based on the current price, which should be more accurate for current analysis

## Testing

The changes were tested by running the application with the sample portfolio data and verifying that:

1. The application uses calculated values instead of reported values
2. The log messages are updated to reflect this change
3. The portfolio summary and analysis are based on the most up-to-date values

## Conclusion

By always using our calculated values instead of the reported values from the CSV file, we ensure that our portfolio analysis is based on the most up-to-date data available. This should provide more accurate and consistent results across the application.
