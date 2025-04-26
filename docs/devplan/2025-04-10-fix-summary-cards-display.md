# Summary Cards Display Fix - 2025-04-10

## Overview

This development plan outlines the approach to fix the issue with summary cards not displaying values in the Folio dashboard. Based on the analysis of the previous engineer's work documented in `docs/devlog/2025-04-05-summary-cards-refactor.md`, the issue appears to be related to the integration between the summary cards component and the Dash callback system.

## Problem Analysis

After reviewing the code and the devlog, I've identified several potential issues:

1. **Callback Chain Issue**: The `update_summary_cards` callback in `app.py` is triggered by changes to the `portfolio-summary` Store component, but there might be an issue with how this data is being passed or processed.

2. **Data Structure Mismatch**: The data structure expected by the `format_summary_card_values` function in `summary_cards.py` might not match what's being stored in the `portfolio-summary` Store.

3. **Hidden Exception**: There might be an exception being thrown somewhere in the callback chain that's being swallowed by Dash's error handling.

4. **Missing Integration Tests**: There are unit tests for the summary cards component, but no integration tests that verify the full callback chain works correctly.

## Implementation Plan

### Phase 1: Diagnostic Improvements

1. **Add Client-Side Debugging**
   - Add client-side JavaScript to log the contents of the `portfolio-summary` Store to the browser console
   - This will help verify if the data is being stored correctly

2. **Enhance Server-Side Logging**
   - Add more detailed logging in the `update_summary_cards` callback to track the exact flow of data
   - Log the structure and content of the summary data at each step

### Phase 2: Fix Core Issues

1. **Fix Data Structure Mismatch**
   - Ensure the data structure in the `portfolio-summary` Store matches what's expected by the `format_summary_card_values` function
   - Update the `format_summary_card_values` function to handle potential data structure variations

2. **Fix Callback Chain**
   - Verify that the `update_summary_cards` callback is being triggered correctly
   - Ensure the callback dependencies are properly set up

3. **Improve Error Handling**
   - Add more explicit error handling in the callback to surface any hidden exceptions
   - Make errors visible in the UI rather than silently failing

### Phase 3: Add Integration Tests

1. **Create Integration Test for Summary Cards**
   - Develop a test that verifies the full callback chain for summary cards
   - Test that the `update_summary_cards` callback correctly processes data from the `portfolio-summary` Store

2. **Test with Sample Data**
   - Create a test that loads the sample portfolio and verifies that summary cards display correctly
   - This will help ensure the fix works with real-world data

## Implementation Details

### 1. Client-Side Debugging

Add the following client-side callback to `app.py` to log the contents of the `portfolio-summary` Store:

```python
app.clientside_callback(
    """
    function(data) {
        console.log("Portfolio Summary Data:", data);
        return window.dash_clientside.no_update;
    }
    """,
    Output("portfolio-summary", "data", allow_duplicate=True),
    Input("portfolio-summary", "data"),
    prevent_initial_call=True,
)
```

### 2. Enhanced Server-Side Logging

Update the `update_summary_cards` callback in `app.py` to include more detailed logging:

```python
@app.callback(
    [
        Output("portfolio-value", "children"),
        # ... other outputs ...
    ],
    [Input("portfolio-summary", "data")],
    prevent_initial_call=False,
)
def update_summary_cards(summary_data):
    """Update summary cards with latest data"""
    logger.info("Updating summary cards")
    logger.info(f"Summary data type: {type(summary_data)}")
    
    # Log the structure of the summary data
    if summary_data:
        logger.info("Summary data keys: %s", list(summary_data.keys()))
        for key in summary_data.keys():
            if isinstance(summary_data[key], dict):
                logger.info(f"  {key} (dict): {list(summary_data[key].keys())}")
            elif isinstance(summary_data[key], list):
                logger.info(f"  {key} (list): {len(summary_data[key])} items")
            else:
                logger.info(f"  {key}: {summary_data[key]}")
    
    # ... rest of the function ...
```

### 3. Fix Data Structure Mismatch

Update the `format_summary_card_values` function in `summary_cards.py` to handle potential data structure variations:

```python
def format_summary_card_values(summary_data):
    """Format summary card values from summary data."""
    # Log the entire summary_data for debugging
    logger.info(f"Formatting summary cards with data: {summary_data}")
    
    # Ensure summary_data is a dictionary
    if not summary_data or not isinstance(summary_data, dict):
        logger.error(f"Invalid summary data: {type(summary_data)}")
        return default_values()
    
    # Check for required keys
    required_keys = ["portfolio_estimate_value", "net_market_exposure", "portfolio_beta"]
    missing_keys = [key for key in required_keys if key not in summary_data]
    if missing_keys:
        logger.error(f"Missing required keys in summary data: {missing_keys}")
        
    # ... rest of the function ...
```

### 4. Integration Test

Create a new test file `tests/test_summary_cards_integration.py`:

```python
"""Integration tests for summary cards component."""

import pytest
from dash.testing.application_runners import import_app
from dash.testing.composite import DashComposite

from src.folio.data_model import ExposureBreakdown, PortfolioSummary


@pytest.fixture
def test_app():
    """Create a test app with sample data."""
    # Import the app module
    app_module = import_app("src.folio.app")
    
    # Create a test app
    app = app_module.create_app()
    
    # Create test data
    # ... create test data ...
    
    # Return the app
    return app


def test_summary_cards_display(dash_duo, test_app):
    """Test that summary cards display correctly."""
    # Start the app
    dash_duo.start_server(test_app)
    
    # Wait for the app to load
    dash_duo.wait_for_element("#portfolio-value")
    
    # Check that the summary cards display the correct values
    assert dash_duo.find_element("#portfolio-value").text != "$0.00"
    assert dash_duo.find_element("#total-value").text != "$0.00"
    # ... check other values ...
```

## Testing Strategy

1. **Manual Testing**
   - Run the app with the sample portfolio data using `make portfolio`
   - Verify that the summary cards display the correct values
   - Check the browser console and server logs for any errors

2. **Automated Testing**
   - Run the unit tests for the summary cards component using `make test`
   - Run the new integration test to verify the full callback chain

## Success Criteria

The fix will be considered successful if:

1. The summary cards display the correct values when loading the sample portfolio
2. The unit tests for the summary cards component pass
3. The new integration test passes
4. There are no errors in the browser console or server logs

## Rollback Plan

If the fix causes new issues:

1. Revert the changes to `app.py` and `summary_cards.py`
2. Document the issues encountered in a new devlog
3. Consider a different approach based on the new information

## Timeline

- Phase 1 (Diagnostic Improvements): 1 day
- Phase 2 (Fix Core Issues): 2 days
- Phase 3 (Add Integration Tests): 1 day
- Testing and Verification: 1 day

Total: 5 days
