# Development Log: Fix Table Selection Error

**Date**: 2025-04-02

## Issue Description

When launching the Folio application, the following error appears in the logs:

```
ERROR: Row index out of range or not found: None, groups length: 31
ERROR:folio:Row index out of range or not found: None, groups length: 31
```

This error occurs in the `store_selected_position` callback function when handling table selection events. The function attempts to validate a row index when no cell is selected (i.e., `active_cell` is `None`), resulting in an unnecessary error message.

## Root Cause Analysis

The issue is in the `store_selected_position` function in `src/folio/app.py`. When the application first loads, no cell is selected in the portfolio table, so `row` is `None`. The function logs an error message when it can't find a valid row index, even though this is an expected state during initialization.

The problematic code was:

```python
# Validate and return row data if found
if row is not None and 0 <= row < len(groups_data):
    position_data = groups_data[row]
else:
    logger.error(
        f"Row index out of range or not found: {row}, groups length: {len(groups_data)}"
    )
```

This code treats both "no selection" (`row` is `None`) and "invalid selection" (`row` is out of range) as the same error condition, which is not correct.

## Solution

I modified the code to distinguish between "no selection" (which is normal during initialization) and "invalid selection" (which is an actual error):

```python
# Validate and return row data if found
if row is not None:
    if 0 <= row < len(groups_data):
        position_data = groups_data[row]
    else:
        # This is an actual error - row index is invalid
        logger.error(
            f"Row index out of range: {row}, groups length: {len(groups_data)}"
        )
else:
    # This is not an error - just no selection yet
    logger.debug("No row selected (normal during initialization)")
```

This change:
1. First checks if `row` is `None` (no selection)
2. Only logs an error when there's an actual invalid row index
3. Adds a debug-level log message for the "no selection" case to provide context

## Testing

The changes were tested according to the test plan in `docs/devplan/2025-04-02-fix-table-selection-error-test.md`. The application now starts without showing the "Row index out of range" error, and all table selection functionality continues to work correctly.

## Conclusion

This was a minor fix to improve the quality of the logs by not treating expected states as errors. The change doesn't affect the core functionality of the application but makes the logs cleaner and more useful for debugging actual issues.
