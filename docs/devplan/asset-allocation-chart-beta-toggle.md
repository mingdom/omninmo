# Development Plan: Adding Beta-Adjusted Toggle to Asset Allocation Chart

**Date:** 2023-07-25

## Overview

This development plan outlines the implementation of a beta-adjusted toggle for the asset allocation chart. With the recent enhancement of the asset allocation chart to display stacked bars for stock and options exposure, we can now consolidate functionality by adding a beta-adjusted toggle similar to the one in the exposure chart. This will allow users to view their portfolio allocation with or without beta adjustment, providing more insight into market exposure.

## Background

The current implementation of the asset allocation chart shows the breakdown of stock and options exposure within long and short positions, as well as cash holdings. However, it only displays raw exposure values without beta adjustment. The separate exposure chart currently provides beta-adjusted views, but with our enhanced asset allocation chart, we can incorporate this functionality directly and potentially eliminate redundancy.

## Implementation Plan

### 1. Add Toggle Button to Asset Allocation Chart Component

Update the `create_asset_allocation_chart` function in `src/folio/components/charts.py` to include toggle buttons for switching between net exposure and beta-adjusted views:

```python
def create_asset_allocation_chart():
    """Create an asset allocation chart component."""
    return html.Div([
        dcc.Graph(
            id="asset-allocation-chart",
            config={"displayModeBar": False, "responsive": True},
            className="dash-chart",
        ),
        # Add toggle for beta-adjusted view
        html.Div(
            dbc.ButtonGroup([
                dbc.Button(
                    "Net Exposure",
                    id="allocation-net-btn",
                    color="primary",
                    outline=True,
                    size="sm",
                    active=True,
                    n_clicks=0,
                    className="px-3",
                ),
                dbc.Button(
                    "Beta-Adjusted",
                    id="allocation-beta-btn",
                    color="primary",
                    outline=True,
                    size="sm",
                    n_clicks=0,
                    className="px-3",
                ),
            ],
            size="sm",
            className="chart-toggle-buttons",
            ),
            className="d-flex justify-content-center mt-3",
        ),
    ],
    className="mb-4",
    )
```

### 2. Update the Callback to Handle Beta-Adjustment

Modify the `update_asset_allocation_chart` callback in `src/folio/components/charts.py` to handle the beta-adjusted toggle:

```python
@app.callback(
    Output("asset-allocation-chart", "figure"),
    [
        Input("portfolio-summary", "data"),
        Input("allocation-net-btn", "n_clicks"),
        Input("allocation-beta-btn", "n_clicks"),
    ],
    [
        State("allocation-net-btn", "active"),
        State("allocation-beta-btn", "active"),
    ],
)
def update_asset_allocation_chart(
    summary_data, _net_clicks, _beta_clicks, net_active, beta_active
):
    """Update the asset allocation chart based on user selection."""
    if not summary_data:
        # Return empty figure if no data
        return {"data": [], "layout": {"height": 300}}

    try:
        # Determine which view to use based on button clicks
        ctx = dash.callback_context
        if not ctx.triggered:
            # Default to net exposure view
            use_beta_adjusted = False
            net_active = True
            beta_active = False
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "allocation-net-btn":
                use_beta_adjusted = False
                net_active = True
                beta_active = False
            elif button_id == "allocation-beta-btn":
                use_beta_adjusted = True
                net_active = False
                beta_active = True
            else:
                # If triggered by data update, maintain current state
                use_beta_adjusted = beta_active
                # Keep button states as they are

        # Convert the JSON data back to a PortfolioSummary object
        portfolio_summary = PortfolioSummary.from_dict(summary_data)

        # Transform the data for the chart with beta adjustment if selected
        chart_data = transform_for_asset_allocation(
            portfolio_summary, use_beta_adjusted=use_beta_adjusted
        )
        return chart_data
    except Exception as e:
        logger.error(f"Error updating asset allocation chart: {e}", exc_info=True)
        # Return empty figure on error
        return {"data": [], "layout": {"height": 300}}
```

### 3. Modify the Chart Data Transformation Function

Update the `transform_for_asset_allocation` function in `src/folio/chart_data.py` to support beta adjustment:

```python
def transform_for_asset_allocation(
    portfolio_summary: PortfolioSummary, use_beta_adjusted: bool = False
) -> dict[str, Any]:
    """Transform portfolio summary data for the asset allocation chart.

    Args:
        portfolio_summary: Portfolio summary data from the data model
        use_beta_adjusted: Whether to use beta-adjusted values (True) or raw values (False)

    Returns:
        Dict containing data and layout for the stacked bar chart
    """
    logger.debug("Transforming data for asset allocation chart")

    # Extract values from portfolio summary
    long_stock_value = portfolio_summary.long_exposure.stock_exposure
    long_option_value = portfolio_summary.long_exposure.option_delta_exposure
    short_stock_value = abs(portfolio_summary.short_exposure.stock_exposure)
    short_option_value = abs(portfolio_summary.short_exposure.option_delta_exposure)
    cash_like_value = portfolio_summary.cash_like_value

    # Apply beta adjustment if selected
    if use_beta_adjusted:
        # Adjust stock values by beta
        long_stock_value = long_stock_value * portfolio_summary.portfolio_beta
        short_stock_value = short_stock_value * portfolio_summary.portfolio_beta
        
        # Options already account for market exposure through delta, so no adjustment needed
        # Cash and bonds typically have very low beta, so minimal adjustment needed
        
    # Categories for the chart
    categories = ["Long", "Short", "Cash"]
    
    # Format values for display
    title_text = "Asset Allocation " + ("(Beta-Adjusted)" if use_beta_adjusted else "(Exposure)")
    
    # Create the chart data with stacked bars for long and short exposure
    # ... rest of the function remains the same
```

### 4. Update Tests

Update the tests in `tests/test_charts.py` and `tests/test_chart_data.py` to verify the beta-adjusted functionality:

- Test that the toggle buttons are present and working
- Test that the chart data is correctly beta-adjusted when that option is selected
- Test that the title changes appropriately based on the selected view

## Beta Adjustment Considerations

When applying beta adjustment to the asset allocation chart, we need to consider:

1. **Stock Exposure**: Apply the portfolio beta to adjust the market exposure
2. **Options Exposure**: Options already account for market exposure through delta, so no additional adjustment is needed
3. **Cash and Bonds**: These typically have very low beta, so minimal adjustment is needed

## Testing Strategy

1. **Unit Tests**: Update existing tests to cover the new functionality
2. **Manual Testing**: Verify that the toggle buttons work correctly and that the chart updates appropriately
3. **Edge Cases**: Test with extreme beta values and with empty portfolios

## Future Considerations

1. **Consolidation**: Consider whether to keep or remove the separate exposure chart now that the asset allocation chart provides similar functionality
2. **Additional Toggles**: Consider adding more toggles for different views (e.g., sector allocation, asset class allocation)
3. **Customization**: Allow users to customize which components are beta-adjusted

## Implementation Timeline

This enhancement should be relatively straightforward and can be completed in a single development cycle:

1. Update the asset allocation chart component and callback (1 hour)
2. Modify the chart data transformation function (1 hour)
3. Update tests (1 hour)
4. Manual testing and refinement (1 hour)

Total estimated time: 4 hours
