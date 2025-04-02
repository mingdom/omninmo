# Development Plan: Fix Table Selection Error

## Issue Description

When launching the Folio application, the following error appears in the logs:

```
ERROR: Row index out of range or not found: None, groups length: 31
ERROR:folio:Row index out of range or not found: None, groups length: 31
```

This error occurs in the `store_selected_position` callback function when handling table selection events. The function attempts to validate a row index when no cell is selected (i.e., `active_cell` is `None`), resulting in an unnecessary error message.

## Root Cause Analysis

1. The error occurs in the `store_selected_position` function in `app.py`
2. When the application first loads, no cell is selected in the portfolio table
3. The function logs an error when it can't find a valid row index, even though this is an expected state
4. This is not a critical error that affects functionality, but it clutters the logs with unnecessary error messages

## Implementation Plan

### 1. Modify the `store_selected_position` function

Update the function to handle the case when no cell is selected more gracefully:

- Add a check to distinguish between "no selection" and "invalid selection"
- Only log an error when there's an actual invalid selection (not when there's no selection)
- Add debug-level logging for the "no selection" case instead of error-level

### 2. Improve Error Logging

- Ensure stack traces are included in error logs for better debugging
- Add more context to error messages to make them more actionable

### 3. Testing

- Test the application to ensure the error no longer appears during normal startup
- Verify that actual invalid selections still trigger appropriate error messages
- Check that the application's functionality remains unchanged

## Success Criteria

1. The application starts without showing the "Row index out of range" error
2. The logs are cleaner and only show actual errors
3. All functionality related to table selection continues to work correctly

## Implementation Details

### File to Modify

- `src/folio/app.py` - Update the `store_selected_position` callback function

### Code Changes

The main change will be in the `store_selected_position` function to distinguish between:
- No selection (expected state during initialization)
- Invalid selection (actual error condition)

This will involve modifying the error handling logic to only log errors for actual error conditions.
