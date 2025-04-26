# Position P&L Visualization Development Plan

**Date: 2025-04-12**

## 1. Overview

This development plan outlines the implementation of P&L (Profit and Loss) visualization for position groups in the Folio application, with a particular focus on multi-leg options strategies. The feature will allow users to visualize the potential profit or loss of a position or group of related positions (such as multi-leg options strategies) across a range of underlying prices.

## 2. Feature Requirements

### 2.1 Core Requirements

1. Generate P&L graphs for:
   - Individual option positions
   - Multi-leg option strategies (e.g., spreads, straddles, iron condors)
   - Combined stock and option positions

2. Display P&L at different points:
   - Current date (immediate P&L)
   - At expiration (terminal P&L)
   - At user-selected dates between now and expiration

3. UI Integration:
   - Add a "P&L" button to position table rows
   - Display P&L graphs in a modal/popup
   - Allow toggling between different visualization modes

### 2.2 Advanced Features (Future Enhancements)

1. Volatility surface visualization
2. Greeks visualization across price ranges
3. Probability cones for price movement
4. Scenario analysis with custom parameters

## 3. Technology Evaluation

### 3.1 Core Financial Library: QuantLib

**Strengths for P&L Visualization:**
- Already integrated into our codebase for option pricing
- Provides accurate pricing for American options
- Can calculate option prices at different dates and underlying prices
- Supports all option Greeks for sensitivity analysis
- Industry-standard library with active maintenance
- Proven reliability for financial calculations

**Limitations:**
- No built-in visualization capabilities
- Requires custom code to generate P&L data points
- Complex API for some advanced features

**Implementation Approach:**
- Use QuantLib for the pricing engine
- Leverage our existing option pricing functions in `src/folio/options.py`
- Generate price points across a range of underlying prices
- Calculate P&L for each price point based on position details

### 3.2 Visualization Library: Plotly/Dash

**Strengths for P&L Visualization:**
- Already used in our application for charts
- Interactive visualizations with zoom, pan, and tooltips
- Supports multiple chart types (line, area, etc.)
- Responsive design works well in modals
- Well-maintained with active community support

**Implementation Approach:**
- Use Plotly for the visualization layer
- Leverage existing Dash components for the UI
- Create reusable chart components
- Implement modal popup for displaying P&L charts

### 3.3 Custom Implementation Considerations

**Benefits of Custom Implementation:**
- Full control over calculation logic
- No dependency on third-party libraries beyond QuantLib
- Can be tailored exactly to our needs
- Easier to maintain and extend over time
- Consistent with our existing codebase

**Implementation Challenges:**
- Need to handle various position types (stocks, options, multi-leg strategies)
- Must account for different evaluation dates
- Requires careful testing to ensure accuracy
- More initial development effort than using specialized libraries

## 4. Recommended Approach

### 4.1 Technology Stack

1. **Core Calculation Engine**: QuantLib (already integrated)
   - Use existing `calculate_bs_price` function in `src/folio/options.py`
   - Extend to calculate prices at different dates and underlying prices
   - Leverage for accurate American options pricing

2. **Data Generation**: Custom Python code
   - Create functions to generate P&L data points across price ranges
   - Support different dates (current, expiration, custom)
   - Handle both stock and option positions

3. **Visualization**: Plotly/Dash
   - Create interactive line charts for P&L visualization
   - Use existing Dash modal components for the popup UI
   - Consistent with our current UI framework

4. **Integration Approach**: Direct UI Integration
   - Implement UI components from the start
   - Use the UI for testing the feature
   - Avoid creating separate experimental scripts

### 4.2 Implementation Plan

1. Create a new module `src/folio/pnl.py` for P&L calculation functions
2. Create a new UI component `src/folio/components/pnl_chart.py` for the visualization
3. Add a P&L button to the position table
4. Implement the modal popup with the P&L chart
5. Register callbacks for the interactive features

## 5. Technical Design

### 5.1 P&L Calculation Module (`src/folio/pnl.py`)

```python
"""
P&L calculation functions for positions and strategies.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import datetime

import QuantLib as ql

from .options import OptionContract, calculate_bs_price
from .data_model import Position


def calculate_position_pnl(
    position: Position,
    price_range: Optional[Tuple[float, float]] = None,
    num_points: int = 50,
    evaluation_date: Optional[datetime.datetime] = None,
) -> Dict[str, Any]:
    """
    Calculate P&L for a single position across a range of underlying prices.

    Args:
        position: The position to calculate P&L for
        price_range: Optional tuple of (min_price, max_price). If None, auto-calculated.
        num_points: Number of price points to calculate
        evaluation_date: Date to evaluate P&L at. If None, uses current date.

    Returns:
        Dictionary with price points and corresponding P&L values
    """
    # Determine price range if not provided
    if price_range is None:
        current_price = position.current_price
        price_range = determine_price_range([position], current_price)

    min_price, max_price = price_range
    price_points = np.linspace(min_price, max_price, num_points)

    # Calculate P&L for each price point
    pnl_values = []

    for price in price_points:
        if position.type == "stock":
            # For stock positions, P&L is linear
            entry_price = position.cost_basis / abs(position.quantity) if position.quantity != 0 else 0
            pnl = (price - entry_price) * position.quantity
        elif position.type == "option":
            # For option positions, calculate using QuantLib
            option_contract = OptionContract(
                underlying=position.underlying,
                expiry=position.expiry,
                strike=position.strike,
                option_type=position.option_type,
                quantity=position.quantity,
                current_price=position.current_price,
                description=position.description
            )

            # Calculate theoretical price at the given underlying price
            theo_price = calculate_bs_price(
                option_contract,
                underlying_price=price,
                evaluation_date=evaluation_date
            )

            # P&L = (current theoretical value - entry price) * quantity
            entry_price = position.cost_basis / abs(position.quantity) if position.quantity != 0 else 0
            pnl = (theo_price - entry_price) * position.quantity
        else:
            # Unsupported position type
            pnl = 0

        pnl_values.append(pnl)

    return {
        "price_points": price_points.tolist(),
        "pnl_values": pnl_values,
        "position": position.to_dict(),
    }


def calculate_strategy_pnl(
    positions: List[Position],
    price_range: Optional[Tuple[float, float]] = None,
    num_points: int = 50,
    evaluation_date: Optional[datetime.datetime] = None,
) -> Dict[str, Any]:
    """
    Calculate P&L for a group of positions (strategy) across a range of underlying prices.

    Args:
        positions: List of positions in the strategy
        price_range: Optional tuple of (min_price, max_price). If None, auto-calculated.
        num_points: Number of price points to calculate
        evaluation_date: Date to evaluate P&L at. If None, uses current date.

    Returns:
        Dictionary with price points and corresponding P&L values
    """
    if not positions:
        return {"price_points": [], "pnl_values": [], "positions": []}

    # Ensure all positions have the same underlying
    underlying = positions[0].underlying
    if not all(p.underlying == underlying for p in positions):
        raise ValueError("All positions must have the same underlying asset")

    # Determine price range if not provided
    if price_range is None:
        current_price = next((p.current_price for p in positions if hasattr(p, 'current_price')), 100)
        price_range = determine_price_range(positions, current_price)

    min_price, max_price = price_range
    price_points = np.linspace(min_price, max_price, num_points)

    # Calculate P&L for each position at each price point
    position_pnls = []
    for position in positions:
        position_pnl = calculate_position_pnl(
            position,
            price_range=(min_price, max_price),
            num_points=num_points,
            evaluation_date=evaluation_date
        )
        position_pnls.append(position_pnl)

    # Combine P&L values for all positions
    combined_pnl = np.zeros(num_points)
    for pnl_data in position_pnls:
        combined_pnl += np.array(pnl_data["pnl_values"])

    return {
        "price_points": price_points.tolist(),
        "pnl_values": combined_pnl.tolist(),
        "individual_pnls": position_pnls,
        "positions": [p.to_dict() for p in positions],
    }


def determine_price_range(
    positions: List[Position],
    current_price: float,
    width_factor: float = 0.3,
) -> Tuple[float, float]:
    """
    Determine an appropriate price range for P&L visualization.

    Args:
        positions: List of positions to consider
        current_price: Current price of the underlying
        width_factor: Factor to determine width of price range (0.3 = ±30%)

    Returns:
        Tuple of (min_price, max_price)
    """
    # Start with default range based on current price
    min_price = current_price * (1 - width_factor)
    max_price = current_price * (1 + width_factor)

    # Adjust range to include all option strikes
    for position in positions:
        if hasattr(position, 'strike') and position.strike is not None:
            min_price = min(min_price, position.strike * 0.8)
            max_price = max(max_price, position.strike * 1.2)

    return (min_price, max_price)
```

### 5.2 P&L Chart Component (`src/folio/components/pnl_chart.py`)

```python
"""
P&L chart component for position visualization.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

from ..pnl import calculate_position_pnl, calculate_strategy_pnl
from ..logger import logger


def create_pnl_modal():
    """
    Create a modal for displaying P&L charts.

    Returns:
        dbc.Modal: The modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Position P&L Analysis"),
                close_button=True,
            ),
            dbc.ModalBody([
                # Date selection controls
                dbc.Row([
                    dbc.Col([
                        html.Label("Evaluation Date"),
                        dbc.RadioItems(
                            id="pnl-date-selector",
                            options=[
                                {"label": "Current", "value": "current"},
                                {"label": "Expiration", "value": "expiration"},
                                {"label": "Custom", "value": "custom"},
                            ],
                            value="current",
                            inline=True,
                        ),
                    ]),
                    dbc.Col([
                        html.Div(
                            dcc.DatePickerSingle(
                                id="pnl-custom-date",
                                min_date_allowed=datetime.date.today().isoformat(),
                                date=datetime.date.today().isoformat(),
                                disabled=True,
                            ),
                            id="pnl-custom-date-container",
                            style={"display": "none"},
                        ),
                    ]),
                ], className="mb-3"),

                # P&L Chart
                dcc.Graph(
                    id="pnl-chart",
                    config={"displayModeBar": True, "responsive": True},
                    className="pnl-chart",
                ),

                # Position details
                html.Div(id="pnl-position-details", className="mt-3"),
            ]),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="close-pnl-modal",
                    className="ms-auto",
                ),
            ),
        ],
        id="pnl-modal",
        size="lg",
    )


def register_callbacks(app):
    """
    Register callbacks for the P&L chart component.

    Args:
        app: The Dash app
    """
    # Implementation details...
```

### 5.3 Position Table Integration

Add a P&L button to the position table:

```python
# In src/folio/components/portfolio_table.py

def create_position_table(data):
    """Create the portfolio position table."""
    # Existing code...

    # Add P&L button to actions column
    actions = html.Div([
        # Existing buttons...
        html.Button(
            html.I(className="fas fa-chart-line"),
            id={"type": "position-pnl", "index": position_id},
            className="btn btn-sm btn-outline-primary ms-1",
            title="View P&L Analysis",
        ),
    ])

    # Existing code...
```

### 5.4 Callback Integration

Register callbacks for the P&L modal and chart:

```python
# In src/folio/app.py or appropriate callback file

@app.callback(
    [
        Output("pnl-modal", "is_open"),
        Output("pnl-chart", "figure"),
        Output("pnl-position-details", "children"),
    ],
    [
        Input({"type": "position-pnl", "index": ALL}, "n_clicks"),
        Input("pnl-date-selector", "value"),
        Input("pnl-custom-date", "date"),
        Input("close-pnl-modal", "n_clicks"),
    ],
    [
        State("portfolio-data", "data"),
        State("pnl-modal", "is_open"),
    ],
)
def toggle_pnl_modal(btn_clicks, date_type, custom_date, close_clicks, portfolio_data, is_open):
    """Toggle P&L modal and update chart."""
    # Implementation details...
```

## 6. Implementation Phases

### Phase 1: Core P&L Calculation (1-2 weeks)

1. Implement `pnl.py` module with QuantLib-based calculation functions
2. Create unit tests for P&L calculations
3. Validate calculations against known strategies
4. Support both stock and option positions

### Phase 2: UI Components (1-2 weeks)

1. Create P&L modal component
2. Add P&L button to position table
3. Implement basic chart visualization with Plotly
4. Integrate with portfolio data

### Phase 3: Interactive Features (1 week)

1. Add date selection controls
2. Implement price range controls
3. Add tooltips and interactive elements
4. Support toggling between individual and combined P&L views

### Phase 4: Testing and Refinement (1 week)

1. Test with real portfolio data, including stock+options combinations
2. Optimize performance for complex strategies
3. Refine UI based on feedback
4. Add error handling for edge cases

## 7. Design Trade-offs

### 7.1 Complexity vs. Functionality

| Approach | Pros | Cons |
|----------|------|------|
| **Full QuantLib implementation** | - Highest accuracy<br>- Support for all option types<br>- Handles complex multi-leg strategies | - Higher computational complexity<br>- Steeper learning curve<br>- Potentially slower performance |
| **Simplified analytical approach** | - Faster performance<br>- Easier to implement<br>- More maintainable code | - Less accurate for American options<br>- Limited support for exotic strategies<br>- May diverge from market prices |
| **Hybrid approach (recommended)** | - Good balance of accuracy and performance<br>- Uses QuantLib for core pricing<br>- Simplified interface for common use cases | - Requires careful API design<br>- Some duplication of functionality<br>- May still be complex for edge cases |

### 7.2 UI Design Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Dedicated page for P&L analysis** | - More screen space for visualization<br>- Can show more details and controls<br>- Better for complex analysis | - Disrupts user workflow<br>- Requires navigation away from portfolio<br>- More complex implementation |
| **Modal popup (recommended)** | - Maintains context of portfolio<br>- Simpler implementation<br>- Consistent with existing UI patterns | - Limited screen space<br>- Fewer controls can be shown<br>- May feel cramped for complex strategies |
| **Inline expansion in table** | - No navigation required<br>- Direct context for each position<br>- Minimal disruption | - Very limited space<br>- Difficult to compare strategies<br>- Technical challenges with Dash |

### 7.3 Calculation Performance Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Pre-calculate all P&L points** | - Instant display when requested<br>- No calculation delay for users<br>- Can handle more complex calculations | - Higher memory usage<br>- Stale data if prices change<br>- Calculation overhead for unused positions |
| **Calculate on demand (recommended)** | - Always fresh calculations<br>- Lower memory footprint<br>- Only calculate what's needed | - Potential UI delay during calculation<br>- Need for loading indicators<br>- May feel less responsive |
| **Client-side calculation** | - Reduced server load<br>- More responsive UI<br>- No round-trips to server | - Duplicated code (Python and JS)<br>- Potential inconsistencies<br>- Limited to simpler models |

## 8. Complexity & Risks

### 8.1 Implementation Complexity Assessment

| Component | Complexity | Reasoning |
|-----------|------------|----------|
| **P&L Calculation Engine** | Medium | - Using specialized libraries reduces complexity<br>- OptionLab handles multi-leg strategies natively<br>- Less custom code needed for core calculations |
| **Data Generation** | Medium | - Generating appropriate price ranges<br>- Handling different evaluation dates<br>- Ensuring calculations are performant |
| **UI Components** | Medium-Low | - Leverages existing Dash components<br>- Modal pattern already exists in codebase<br>- Chart visualization is straightforward with Plotly |
| **Integration** | Medium | - Connecting to existing portfolio data<br>- Ensuring consistent state management<br>- Handling loading states and errors |

**Overall Complexity: Medium**

### 8.2 Key Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Calculation accuracy issues** | High | Medium | - Validate against known strategies<br>- Comprehensive test suite<br>- Compare with external calculators |
| **Performance bottlenecks** | Medium | High | - Optimize calculation code<br>- Consider caching strategies<br>- Implement loading indicators |
| **UI responsiveness** | Medium | Medium | - Async calculations<br>- Progressive loading of data<br>- Optimize number of data points |
| **Complex strategy handling** | High | Medium | - Start with common strategies<br>- Incremental implementation<br>- Clear error handling for unsupported cases |
| **Date handling complexity** | Medium | Low | - Careful date conversion between JS and Python<br>- Thorough testing of date-based calculations<br>- Clear validation of user inputs |

## 9. Assumptions and Open Questions

### 9.1 Assumptions

1. **User Needs**: We assume users primarily want to visualize P&L at current date and expiration, with custom dates being secondary.

2. **Data Availability**: We assume all necessary data (option prices, greeks, etc.) is already available in the system or can be calculated using existing functions.

3. **Performance Expectations**: We assume users are willing to wait 1-2 seconds for P&L calculations of complex strategies.

4. **Option Types**: We assume the focus is on standard American options, which are already supported by our QuantLib implementation.

5. **UI Integration**: We assume the modal pattern is appropriate and consistent with the rest of the application.

6. **Position Grouping**: We assume the system can already identify related positions (e.g., options on the same underlying).

### 9.2 Open Questions

1. **Volatility Assumptions**: Should we use current implied volatility for future dates, or implement a term structure?

2. **UI Controls**: What level of customization should users have for the P&L visualization (e.g., adjusting volatility, interest rates)?

3. **Performance Targets**: What is an acceptable calculation time for complex strategies? Should we implement caching?

4. **Error Handling**: How should we handle unsupported strategies or calculation errors in the UI?

5. **Expiration Handling**: How do we handle positions with different expiration dates in the same strategy?

6. **Data Persistence**: Should P&L calculations be saved between sessions or always calculated fresh?

7. **Testing Strategy**: Which specific multi-leg option positions should we focus on for initial testing?

8. **Calculation Accuracy**: How do we validate the accuracy of our P&L calculations for complex strategies?

## 10. Test Cases

### 10.1 Unit Tests

#### P&L Calculation Module

1. **Basic Option P&L Tests**:
   - Test P&L calculation for a single long call option
   - Test P&L calculation for a single short call option
   - Test P&L calculation for a single long put option
   - Test P&L calculation for a single short put option
   - Verify P&L at different evaluation dates

2. **Strategy P&L Tests**:
   - Test P&L for a vertical call spread (long lower strike, short higher strike)
   - Test P&L for a vertical put spread (long higher strike, short lower strike)
   - Test P&L for a straddle (long call and put at same strike)
   - Test P&L for an iron condor (four legs with different strikes)
   - Test P&L for a covered call (long stock, short call)

3. **Edge Case Tests**:
   - Test with very short-dated options (near expiry)
   - Test with very long-dated options (LEAPS)
   - Test with deep in-the-money and out-of-the-money options
   - Test with zero or negative time to expiration
   - Test with extreme price ranges

4. **Price Range Function Tests**:
   - Test price range determination for different strategy types
   - Verify appropriate range for high and low volatility underlyings
   - Test with mixed strategy types (stock + options)

### 10.2 Integration Tests

1. **Data Flow Tests**:
   - Verify correct position data is passed to P&L calculation functions
   - Test integration with portfolio data store
   - Verify position grouping logic correctly identifies related positions

2. **UI Component Tests**:
   - Test modal opening and closing behavior
   - Verify date selector controls work correctly
   - Test chart rendering with different data sets
   - Verify tooltips and interactive elements function properly

3. **Callback Tests**:
   - Test P&L button click triggers correct callbacks
   - Verify date selection updates the chart
   - Test error handling in callbacks
   - Verify loading states are correctly managed

### 10.3 Manual Test Cases

1. **Single Position Tests**:
   - Verify P&L chart for a long stock position shows linear P&L
   - Verify P&L chart for a long call shows correct hockey-stick pattern
   - Verify P&L chart for a short put shows correct risk profile

2. **Multi-leg Strategy Tests**:
   - Verify vertical spread shows correct max profit and loss
   - Verify iron condor shows appropriate profit range
   - Verify straddle shows V-shaped P&L centered at strike

3. **UI Interaction Tests**:
   - Test zooming and panning on the chart
   - Verify tooltips show correct values at different price points
   - Test date selection changes reflect correctly in the chart
   - Verify position details are displayed correctly

4. **Performance Tests**:
   - Measure calculation time for simple vs. complex strategies
   - Test with large number of positions (stress test)
   - Verify UI responsiveness during calculations

5. **Real Portfolio Tests**:
   - Test with actual multi-leg SPY options from the portfolio
   - Verify calculations match expected P&L for known strategies
   - Compare with external calculators for validation

## 11. Conclusion

The P&L visualization feature will significantly enhance the Folio application by providing users with powerful tools to analyze the risk and reward profiles of their positions and strategies. By leveraging our existing QuantLib integration for pricing and Plotly/Dash for visualization, we can implement this feature efficiently while maintaining high accuracy in the calculations.

Our approach focuses on building a custom implementation that gives us full control over the calculation logic and visualization, rather than relying on third-party libraries that may not be actively maintained. This ensures long-term maintainability and allows us to tailor the feature exactly to our needs.

The implementation will support both stock and option positions, including multi-leg strategies like covered calls, which addresses a key requirement. By directly integrating with the UI from the start, we can use the interface itself for testing and validation, streamlining the development process.

The modular design allows for future enhancements such as volatility surface visualization and probability cones without significant refactoring. The implementation plan provides a clear roadmap for delivering this feature in manageable phases over a 4-6 week timeframe.

While there are some complexities and risks to consider, particularly around calculation accuracy and performance with complex strategies, these can be mitigated through careful implementation and thorough testing. The design trade-offs outlined in this plan aim to balance functionality, performance, and implementation complexity to deliver a valuable feature that enhances the user experience without introducing undue technical debt.
