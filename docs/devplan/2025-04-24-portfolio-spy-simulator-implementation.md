# Portfolio SPY Simulator Implementation Plan (2025-04-24)

## Current Status Assessment

After a thorough investigation of the codebase, I've determined that the Portfolio SPY Simulator feature is partially implemented. Here's a breakdown of what has been completed and what still needs to be done:

### Completed Components

1. **Core Simulation Logic**:
   - The `simulator.py` module has been created with the `simulate_portfolio_with_spy_changes` function
   - The function correctly simulates portfolio performance across different SPY price movements
   - Unit tests for the simulator have been implemented in `tests/test_simulator.py`

2. **Data Model Refactoring**:
   - The `StockPosition` class has been updated with a `recalculate_with_price` method
   - The `OptionPosition` class has been updated with a `recalculate_with_price` method
   - The `recalculate_portfolio_with_prices` function has been implemented in `portfolio.py`

### Missing Components

1. **Chart Data Transformation**:
   - The `transform_for_spy_simulator_chart` function has not been implemented in `chart_data.py`

2. **UI Components**:
   - The `create_simulator_tab` function has not been implemented
   - The `create_spy_simulator_chart` function has not been implemented
   - No UI component has been added to the dashboard to display the simulator

3. **Callbacks**:
   - The callback to update the simulator chart when the portfolio changes has not been implemented

## Implementation Plan

### Phase 1: Chart Data Transformation (1 day)

1. **Create Chart Data Transformation Function**:
   - Implement the `transform_for_spy_simulator_chart` function in `chart_data.py`
   - Add unit tests for the transformation function

### Phase 2: UI Components (1-2 days)

1. **Create Chart Component**:
   - Implement the `create_spy_simulator_chart` function in a new file `src/folio/components/simulator.py`
   - Design the chart to show portfolio value and exposure across SPY price changes

2. **Create Tab Component**:
   - Implement the `create_simulator_tab` function in `src/folio/components/simulator.py`
   - Integrate the chart component into the tab

3. **Integrate with Dashboard**:
   - Add the simulator tab to the dashboard in `src/folio/app.py`
   - Add it as a new card in the charts section

### Phase 3: Callbacks (1 day)

1. **Implement Chart Update Callback**:
   - Create a callback to update the simulator chart when the portfolio changes
   - Register the callback in the application

2. **Add Optional Controls** (if time permits):
   - Add controls to adjust simulation parameters (range, intervals)
   - Implement callbacks for the controls

### Phase 4: Testing and Refinement (1-2 days)

1. **Integration Testing**:
   - Test the simulator with various portfolios
   - Verify that the chart updates correctly when the portfolio changes

2. **Performance Optimization**:
   - Implement caching for simulation results
   - Optimize chart rendering for large datasets

3. **UI Refinements**:
   - Add tooltips and help text
   - Ensure consistent styling with other charts

## Technical Approach

### Chart Data Transformation

The `transform_for_spy_simulator_chart` function will:

1. Take simulation results from `simulate_portfolio_with_spy_changes`
2. Create a line chart with SPY change percentages on the x-axis
3. Show portfolio value on the primary y-axis
4. Optionally show portfolio exposure on a secondary y-axis
5. Add a vertical line at 0% to indicate the current position
6. Format hover text to show detailed information at each point

```python
def transform_for_spy_simulator_chart(
    simulation_results: dict[str, Any],
    show_exposure: bool = True,
) -> dict[str, Any]:
    """Transform simulation results for the SPY simulator chart.
    
    Args:
        simulation_results: Results from simulate_portfolio_with_spy_changes
        show_exposure: Whether to show exposure on a secondary y-axis
        
    Returns:
        Dict containing data and layout for the chart
    """
    # Extract data from simulation results
    spy_changes = simulation_results["spy_changes"]
    portfolio_values = simulation_results["portfolio_values"]
    portfolio_exposures = simulation_results["portfolio_exposures"]
    current_value = simulation_results["current_value"]
    
    # Format spy_changes as percentages for display
    spy_changes_pct = [f"{change * 100:.1f}%" for change in spy_changes]
    
    # Create traces for the chart
    traces = [
        {
            "type": "scatter",
            "x": spy_changes,
            "y": portfolio_values,
            "mode": "lines+markers",
            "name": "Portfolio Value",
            "line": {"color": "#1f77b4", "width": 3},
            "marker": {"size": 8},
            "hovertemplate": "SPY Change: %{x:.1%}<br>Portfolio Value: %{y:$,.2f}<extra></extra>",
        }
    ]
    
    # Add exposure trace if requested
    if show_exposure:
        traces.append({
            "type": "scatter",
            "x": spy_changes,
            "y": portfolio_exposures,
            "mode": "lines+markers",
            "name": "Portfolio Exposure",
            "line": {"color": "#ff7f0e", "width": 2, "dash": "dash"},
            "marker": {"size": 6},
            "yaxis": "y2",
            "hovertemplate": "SPY Change: %{x:.1%}<br>Portfolio Exposure: %{y:$,.2f}<extra></extra>",
        })
    
    # Create the layout
    layout = {
        "title": {
            "text": "Portfolio SPY Simulator",
            "font": {"size": 16, "color": "#2C3E50"},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "title": "SPY Change (%)",
            "tickformat": ".0%",
            "gridcolor": "#E5E5E5",
            "zerolinecolor": "#000000",
            "zerolinewidth": 2,
        },
        "yaxis": {
            "title": "Portfolio Value ($)",
            "tickformat": "$,.0f",
            "gridcolor": "#E5E5E5",
            "zerolinecolor": "#BDC3C7",
        },
        "shapes": [
            {
                "type": "line",
                "x0": 0,
                "x1": 0,
                "y0": 0,
                "y1": 1,
                "yref": "paper",
                "line": {
                    "color": "#000000",
                    "width": 1,
                    "dash": "dot",
                },
            }
        ],
        "annotations": [
            {
                "x": 0,
                "y": current_value,
                "text": f"Current: {format_currency(current_value)}",
                "showarrow": True,
                "arrowhead": 2,
                "arrowsize": 1,
                "arrowwidth": 1,
                "arrowcolor": "#636363",
                "ax": 0,
                "ay": -40,
            }
        ],
        "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
        "autosize": True,
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font": {
            "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    }
    
    # Add secondary y-axis if showing exposure
    if show_exposure:
        layout["yaxis2"] = {
            "title": "Portfolio Exposure ($)",
            "tickformat": "$,.0f",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
        }
    
    return {"data": traces, "layout": layout}
```

### UI Components

The simulator UI components will be implemented in a new file `src/folio/components/simulator.py`:

```python
def create_spy_simulator_chart():
    """Create the SPY simulator chart component."""
    return html.Div(
        [
            dcc.Graph(
                id="spy-simulator-chart",
                config=get_chart_config(),
                className="dash-chart",
                figure={
                    "data": [],
                    "layout": {
                        "height": 400,
                        "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
                        "paper_bgcolor": "white",
                        "plot_bgcolor": "white",
                        "autosize": True,
                    },
                },
                style={"width": "100%", "height": "100%"},
            ),
            # Optional: Add controls for simulation parameters
            html.Div(
                [
                    dbc.Switch(
                        id="show-exposure-switch",
                        label="Show Exposure",
                        value=True,
                        className="mt-2",
                    ),
                ],
                className="d-flex justify-content-end",
            ),
        ],
        className="mb-4",
    )

def create_simulator_tab():
    """Create the simulator tab component."""
    return dbc.Card(
        [
            dbc.CardHeader("Portfolio SPY Simulator"),
            dbc.CardBody(
                [
                    create_spy_simulator_chart(),
                ]
            ),
        ],
        className="mb-4 chart-card",
    )
```

### Callbacks

The callbacks will be implemented in the same file:

```python
def register_callbacks(app):
    """Register callbacks for the simulator component."""
    
    @app.callback(
        Output("spy-simulator-chart", "figure"),
        [
            Input("portfolio-groups", "data"),
            Input("portfolio-summary", "data"),
            Input("show-exposure-switch", "value"),
        ],
    )
    def update_spy_simulator_chart(groups_json, summary_json, show_exposure):
        """Update the SPY simulator chart based on portfolio data."""
        if not groups_json or not summary_json:
            # Return empty chart if no data
            return {
                "data": [],
                "layout": {
                    "height": 400,
                    "annotations": [
                        {
                            "text": "No portfolio data available",
                            "showarrow": False,
                            "font": {"color": "#7F8C8D"},
                        }
                    ],
                },
            }
        
        try:
            # Parse the JSON data
            portfolio_groups = [PortfolioGroup.from_dict(group) for group in groups_json]
            portfolio_summary = PortfolioSummary.from_dict(summary_json)
            
            # Get cash-like positions and pending activity value
            cash_like_positions = portfolio_summary.cash_like_positions
            pending_activity_value = getattr(portfolio_summary, "pending_activity_value", 0.0)
            
            # Simulate portfolio performance
            simulation_results = simulate_portfolio_with_spy_changes(
                portfolio_groups=portfolio_groups,
                cash_like_positions=cash_like_positions,
                pending_activity_value=pending_activity_value,
            )
            
            # Transform results for chart
            chart_data = transform_for_spy_simulator_chart(
                simulation_results=simulation_results,
                show_exposure=show_exposure,
            )
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error updating SPY simulator chart: {e}", exc_info=True)
            return {
                "data": [],
                "layout": {
                    "height": 400,
                    "annotations": [
                        {
                            "text": f"Error: {e!s}",
                            "showarrow": False,
                            "font": {"color": "red"},
                        }
                    ],
                },
            }
```

### Integration with Dashboard

The simulator tab will be added to the charts section in `src/folio/app.py`:

```python
# Import the simulator component
from .components.simulator import create_simulator_tab, register_callbacks as register_simulator_callbacks

# In the create_dashboard_section function
charts_section = dbc.Card(
    [
        dbc.CardHeader(
            # ... existing code ...
        ),
        dbc.Collapse(
            dbc.CardBody(
                [
                    # ... existing charts ...
                    
                    # Add the simulator tab
                    create_simulator_tab(),
                ]
            ),
            id="charts-collapse",
            is_open=True,  # Initially open
        ),
    ],
    className="mb-3",
)

# Register the simulator callbacks
register_simulator_callbacks(app)
```

## Timeline

1. **Phase 1 (Chart Data Transformation)**: 1 day
2. **Phase 2 (UI Components)**: 1-2 days
3. **Phase 3 (Callbacks)**: 1 day
4. **Phase 4 (Testing and Refinement)**: 1-2 days

Total estimated time: 4-6 days

## Risks and Mitigations

1. **Risk**: Option pricing calculations may be slow for large portfolios
   **Mitigation**: Implement caching for simulation results

2. **Risk**: Chart may be difficult to interpret with many data points
   **Mitigation**: Add clear annotations and tooltips, consider adding a toggle for simplified view

3. **Risk**: Extreme price changes may lead to unrealistic option prices
   **Mitigation**: Add bounds checking and warnings for extreme scenarios

4. **Risk**: UI performance may degrade with large datasets
   **Mitigation**: Optimize chart rendering, consider reducing the number of data points for very large portfolios

## Future Enhancements

1. Allow users to customize the simulation range and increments
2. Add the ability to simulate custom scenarios (e.g., specific price changes for individual stocks)
3. Include volatility adjustments for more realistic option pricing
4. Add risk metrics like VaR (Value at Risk) based on the simulation results
5. Add a tabular view of the simulation data
