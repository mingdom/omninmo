# Improved Handling of "Pending Activity" in Portfolio Data

## Issue

When processing the portfolio CSV file, the code was encountering an error related to the "Pending Activity" row:

```
ERROR:src.v2.data_fetcher:Error fetching data for Pending Activity: No historical data found for Pending Activity
```

"Pending Activity" is not a valid stock symbol but rather an informational row in the brokerage CSV that represents transactions that haven't settled yet. Initially, we attempted to handle this by treating it as a cash position with a beta of 0, but this approach wasn't semantically correct.

## Solution: Filter Out Invalid Symbols

Instead of treating "Pending Activity" as a special case cash position, we've implemented a more robust solution by filtering out such invalid entries at the beginning of the data processing pipeline.

1. Added explicit validation logic in `process_portfolio_data`:

```python
# Filter out invalid entries like "Pending Activity" which aren't actual positions
invalid_symbols = ["Pending Activity"]
valid_rows = ~df["Symbol"].isin(invalid_symbols)
if (~valid_rows).any():
    filtered_count = (~valid_rows).sum()
    filtered_symbols = df.loc[~valid_rows, "Symbol"].tolist()
    logger.info(f"Filtered out {filtered_count} invalid entries: {filtered_symbols}")
    df = df[valid_rows].reset_index(drop=True)
    logger.info(f"Continuing with {len(df)} remaining rows")
```

2. Removed the special case handling for "Pending Activity" from:
   - `get_beta` function
   - `is_cash_like` function
   - The cash position handling in `process_portfolio_data`

## Benefits

1. **Semantic Correctness**: "Pending Activity" is not treated as a real position, which better reflects its true nature in the portfolio.

2. **Better Error Prevention**: Prevents attempting to fetch market data for a non-existent symbol.

3. **Extensibility**: The filter list can be expanded to handle other invalid or special rows that might appear in brokerage exports.

4. **Improved Logging**: Clear logs about what entries are being filtered out, allowing for better troubleshooting.

## Validation

Tests have been updated and all pass, including:
- Verifying that "Pending Activity" is properly filtered out
- Ensuring all existing tests continue to work
- Confirming that the actual portfolio data is processed correctly

This approach is more robust and correctly handles the semantics of the data, rather than trying to force special rows into existing categories. 