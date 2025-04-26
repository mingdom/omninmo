# Test Plan: Fix Table Selection Error

## Overview

This test plan outlines the steps to verify that the fix for the "Row index out of range or not found" error works correctly and doesn't introduce any regressions.

## Test Environment

- Local development environment
- Sample portfolio data

## Test Cases

### 1. Application Startup

**Objective**: Verify that the application starts without showing the "Row index out of range" error.

**Steps**:
1. Launch the application with `make portfolio` or `python -m src.folio.main --portfolio <path_to_portfolio_file>`
2. Check the logs for any errors

**Expected Result**:
- The application should start without showing the "Row index out of range" error
- The debug log should show "No row selected (normal during initialization)" instead

### 2. Table Selection

**Objective**: Verify that selecting a row in the table works correctly.

**Steps**:
1. Launch the application with sample portfolio data
2. Click on a row in the portfolio table
3. Check the logs

**Expected Result**:
- The row should be selected
- The position details modal should open
- No errors should be logged

### 3. Invalid Selection

**Objective**: Verify that attempting to select an invalid row still logs an error.

**Steps**:
1. Modify the application code temporarily to simulate an invalid row selection (e.g., by setting `row` to a value outside the valid range)
2. Check the logs

**Expected Result**:
- An error should be logged with the message "Row index out of range: <row>, groups length: <length>"

### 4. Details Button

**Objective**: Verify that clicking the "Details" button for a position works correctly.

**Steps**:
1. Launch the application with sample portfolio data
2. Click the "Details" button for a position
3. Check the logs

**Expected Result**:
- The position details modal should open
- No errors should be logged

## Success Criteria

The fix will be considered successful if:

1. The application starts without showing the "Row index out of range" error
2. All table selection functionality continues to work correctly
3. The logs are cleaner and only show actual errors
4. The application's functionality remains unchanged

## Notes

- This is a minor fix that doesn't affect the core functionality of the application
- The main goal is to reduce log noise by not logging expected states as errors
