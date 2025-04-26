# Log Level Adjustments

**Date:** 2025-04-17  
**Author:** Augment AI Assistant

## Overview

This update further reduces the verbosity of logs by downgrading many INFO level logs to DEBUG and WARNING level logs to INFO. This change makes the logs cleaner and more focused on important events while still preserving detailed information at the DEBUG level for troubleshooting.

## Changes Implemented

### 1. Downgraded INFO to DEBUG

The following INFO logs were downgraded to DEBUG:

#### In `src/folio/app.py`:
- "LOAD_SAMPLE_PORTFOLIO: Processing sample portfolio"
- "Found private portfolio at: {private_path}"
- "Using sample portfolio at: {sample_path}"
- "Read {len(file_content)} bytes from portfolio file"
- "Processing uploaded file: {filename}"
- "Successfully read {len(df)} rows from portfolio file"
- "Successfully processed {len(groups)} portfolio groups and {len(cash_like_positions)} cash-like positions"

#### In `src/folio/portfolio.py`:
- "Found Pending Activity with value: {format_currency(pending_activity_value)}"
- "Filtered out {filtered_count} invalid entries: {filtered_symbols}"
- "Continuing with {len(df)} remaining rows"
- "Including Pending Activity value: {format_currency(pending_activity_value)}"

#### In `src/folio/utils.py`:
- "Using default beta of 0.0 for cash-like position: {ticker}"
- "Calculated beta of {beta:.2f} for {ticker}"

### 2. Downgraded WARNING to INFO

The following WARNING logs were downgraded to INFO:

#### In `src/folio/portfolio.py`:
- "Row {index}: {symbol} missing quantity but has value. Using quantity=0."
- "Row {index}: {symbol} has invalid cost basis: '{row['Average Cost Basis']}'. Using 0.0."
- "Row {index}: Error processing '{symbol_raw}': {e}. Skipping row."
- "Row {index}: Invalid symbol: {symbol_raw}. Skipping."
- "Row {index}: {symbol} has invalid quantity: '{row['Quantity']}'. Skipping."
- "Row {index}: {symbol} has missing price. Skipping."
- "Row {index}: {symbol} has negative price ({price}). Skipping."
- "Row {index}: {symbol} has zero price. Calculations may be affected."

## Benefits

1. **Cleaner Logs**: INFO and higher logs are now less cluttered, making it easier to identify important events
2. **Better Signal-to-Noise Ratio**: Important events stand out more clearly in the logs
3. **Preserved Debugging Capability**: All detailed information is still available at DEBUG level
4. **Appropriate Warning Level**: True warnings are still logged at WARNING level, while informational messages about skipped rows are now at INFO level

## Testing

The changes were tested by running the linter to ensure no issues were introduced:

```bash
make lint
```

All checks passed successfully.

## Future Improvements

1. **Component-Level Log Control**: Consider allowing different log levels for different components
2. **Structured Logging**: Implement structured logging for better log analysis
3. **Log Rotation**: Implement log rotation for log files to manage disk space better
