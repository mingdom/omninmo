# Browser Freeze Investigation Plan

**Date:** May 1, 2025  
**Author:** Augment AI Assistant  
**Issue:** Browser freezes when app is left open on start screen without uploading a CSV file

## 1. Issue Summary

The Folio application appears to freeze when left open on the start screen (empty state) without uploading a CSV file. This suggests a potential memory leak, excessive re-rendering, or an infinite callback loop that gradually consumes browser resources until the browser becomes unresponsive.

## 2. Investigation Approach

We'll take a systematic approach to identify the root cause of the freezing issue:

1. **Diagnostic Instrumentation**: Add logging and monitoring to track callback execution and resource usage
2. **Controlled Testing**: Test specific scenarios to isolate the problematic component
3. **Root Cause Analysis**: Identify the underlying cause based on collected data
4. **Solution Design**: Develop targeted fixes based on the identified cause

## 3. Potential Causes

Based on code review, several potential causes have been identified:

### 3.1 Callback Chain Reactions

The app has a complex callback structure that might be creating unintended chain reactions:

- The `initial-trigger` clientside callback fires on URL changes
- This triggers the `update_portfolio_data` callback
- Which updates `portfolio-summary` data (even with empty data)
- Which triggers the `update_summary_cards` callback
- Which might trigger other callbacks through component updates

This chain could potentially create a loop or excessive re-rendering.

### 3.2 Memory Leaks in Chart Components

Chart components might be attempting to render with empty data repeatedly:

- The dashboard section includes chart components that are present in the DOM even when hidden
- These components might be accumulating memory with each render attempt
- Plotly.js (used for charts) is known to be memory-intensive

### 3.3 Background Data Fetching

While no explicit interval component is used, there might be implicit data fetching:

- Data fetcher calls in the portfolio processing code
- Cache validation logic that might run periodically
- Potential browser-side polling not visible in the server code

## 4. Diagnostic Plan

### 4.1 Add Enhanced Logging

#### 4.1.1 Client-Side Logging

Add clientside callbacks to log key events and state changes:

```python
# Add to app.py
app.clientside_callback(
    """
    function(timestamp) {
        console.log("Empty state heartbeat check:", new Date().toISOString(), timestamp);
        return window.dash_clientside.no_update;
    }
    """,
    Output("empty-state-container", "data-timestamp", allow_duplicate=True),
    Input("empty-state-container", "children"),
    prevent_initial_call=False,
)

# Add memory usage tracking
app.clientside_callback(
    """
    function(trigger) {
        if (window.performance && window.performance.memory) {
            console.log("Memory usage:", {
                jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit / 1048576 + " MB",
                totalJSHeapSize: window.performance.memory.totalJSHeapSize / 1048576 + " MB",
                usedJSHeapSize: window.performance.memory.usedJSHeapSize / 1048576 + " MB"
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("empty-state-container", "data-memory", allow_duplicate=True),
    Input("empty-state-container", "children"),
    prevent_initial_call=False,
)
```

#### 4.1.2 Server-Side Logging

Enhance server-side logging to track callback execution frequency:

```python
# Add to toggle_empty_state callback
def toggle_empty_state(groups_data):
    """Show empty state when no data is loaded and collapse upload section when data is loaded"""
    logger.info(f"TOGGLE_EMPTY_STATE called with groups_data: {bool(groups_data)}, timestamp: {time.time()}")
    # ...

# Add to update_summary_cards callback
def update_summary_cards(summary_data):
    """Update summary cards with latest data"""
    logger.info(f"UPDATE_SUMMARY_CARDS called, timestamp: {time.time()}")
    # ...
```

### 4.2 Add Callback Execution Counter

Create a mechanism to count how many times each callback is executed:

```python
# Add to app.py
callback_counters = {
    "toggle_empty_state": 0,
    "update_portfolio_data": 0,
    "update_summary_cards": 0,
    # Add other callbacks as needed
}

# Modify each callback to increment its counter
def toggle_empty_state(groups_data):
    callback_counters["toggle_empty_state"] += 1
    logger.info(f"TOGGLE_EMPTY_STATE called {callback_counters['toggle_empty_state']} times")
    # ...
```

### 4.3 Test Specific Component Isolation

Create a simplified test version of the app with only essential components to isolate the issue:

1. Create a test app with only the empty state and minimal components
2. Gradually add components back to identify which one triggers the freezing
3. Focus on chart components and their initialization with empty data

## 5. Testing Methodology

### 5.1 Controlled Environment Testing

1. Launch the app with diagnostic instrumentation
2. Leave the app open on the start screen for 30 minutes
3. Monitor browser console logs and server logs
4. Track memory usage over time using browser developer tools
5. Note any patterns in callback execution or memory growth

### 5.2 Component Isolation Testing

1. Create test versions of the app with different components disabled
2. Test each version to see if the freezing still occurs
3. Focus on:
   - Chart components (disable all charts)
   - Summary cards (disable the summary cards component)
   - Data stores (simplify the data store structure)

### 5.3 Browser Compatibility Testing

Test the issue across different browsers to determine if it's browser-specific:
- Chrome
- Firefox
- Safari
- Edge

## 6. Potential Solutions

Based on the likely causes, here are potential solutions to implement once the root cause is identified:

### 6.1 For Callback Chain Issues

```python
# Modify update_portfolio_data to prevent triggering other callbacks when no data
@app.callback(
    # ... outputs ...
    # ... inputs ...
)
def update_portfolio_data(_initial_trigger, _pathname, contents, filename):
    # ...
    if not contents and "initial-trigger" in trigger_id:
        # Return no_update for all outputs to prevent triggering downstream callbacks
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    # ...
```

### 6.2 For Chart Component Memory Issues

```python
# Modify create_dashboard_section to conditionally render charts
def create_dashboard_section():
    # ...
    return html.Div(
        [
            summary_section,
            # Only include charts when data is available
            html.Div(id="charts-container"),  # Empty container to be filled when data is available
        ],
        id="dashboard-section",
    )

# Add callback to populate charts only when data is available
@app.callback(
    Output("charts-container", "children"),
    [Input("portfolio-groups", "data")]
)
def render_charts(groups_data):
    if not groups_data:
        return html.Div()  # Return empty div when no data
    
    # Create charts only when data is available
    return charts_section
```

### 6.3 For Background Data Fetching Issues

```python
# Modify data fetcher to explicitly disable background fetching in empty state
def fetch_data(self, ticker, period="5y", interval="1d", empty_state=False):
    """Fetch stock data for a ticker"""
    if empty_state:
        # Skip API calls entirely when in empty state
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    
    # Regular implementation...
```

## 7. Implementation Plan

Once the root cause is identified, we'll implement the appropriate solution in phases:

### Phase 1: Minimal Fix

Implement the smallest possible change to prevent the freezing issue without major refactoring.

### Phase 2: Comprehensive Solution

Develop a more robust solution that addresses the underlying architectural issue to prevent similar problems in the future.

### Phase 3: Testing and Validation

Thoroughly test the solution to ensure:
- The freezing issue is resolved
- No new issues are introduced
- Performance is improved or maintained

## 8. Success Criteria

The investigation and fix will be considered successful when:

1. The root cause of the freezing issue is clearly identified and documented
2. A fix is implemented that prevents the browser from freezing when left on the start screen
3. The fix does not negatively impact other functionality
4. Memory usage remains stable over time when the app is in the empty state

## 9. Timeline

- Investigation and Diagnostics: 1-2 days
- Root Cause Analysis: 1 day
- Solution Implementation: 1-2 days
- Testing and Validation: 1 day
- Documentation and Code Review: 1 day

Total estimated time: 5-7 days
