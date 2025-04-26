# Portfolio SPY Simulator Development Plan

## Overview

This development plan outlines the implementation approach for the Portfolio SPY Simulator feature, which will simulate how a portfolio performs as the benchmark index (SPY) moves up or down. The simulation will use beta values for stocks and delta values for options to create realistic projections.

## Requirements Summary

Based on the specification in `docs/specs/portfolio-spy-simulator.md`, we need to:

1. Simulate portfolio performance across SPY price movements from -30% to +30%
2. Calculate data points at 5% increments
3. Use beta-based simulation for stocks and delta-based simulation for options
4. Display both portfolio value and exposure at each simulation point
5. Implement as a chart visualization with a tab-based UI

## Implementation Approach

### 1. Core Simulation Logic

We'll create a new module `src/folio/simulator.py` that will contain the core simulation logic. This module will:

1. Calculate simulated prices for each underlying stock based on its beta and the SPY movement
2. Recalculate portfolio value and exposure at each simulation point
3. Aggregate the results into a format suitable for visualization

### 2. Refactoring Existing Code

Before implementing the simulator, we need to refactor some existing code to support variable prices:

1. **Portfolio Value Calculation**: Currently, portfolio value calculations use the current price of each position. We need to modify these functions to accept an optional price parameter.

2. **Option Exposure Calculation**: Similarly, option exposure calculations need to be modified to accept a variable underlying price.

3. **Portfolio Summary Calculation**: The portfolio summary calculation needs to be refactored to use the modified functions.

### 3. UI Components

We'll create new UI components for the simulator:

1. **Tab Component**: A new tab component for the simulator
2. **Chart Component**: A chart component to visualize the simulation results
3. **Controls**: Optional controls for adjusting simulation parameters

## Detailed Implementation Plan

### Phase 1: Refactoring Existing Code

#### 1.1 Refactor Stock Position Class

Modify the `StockPosition` class to support recalculation with a different price:

```python
def recalculate_with_price(self, new_price: float) -> 'StockPosition':
    """Create a new StockPosition with recalculated values based on a new price.
    
    Args:
        new_price: The new price to use for calculations
        
    Returns:
        A new StockPosition instance with updated values
    """
    # Calculate new market exposure and beta-adjusted exposure
    new_market_exposure = self.quantity * new_price
    new_beta_adjusted_exposure = new_market_exposure * self.beta
    
    # Create a new instance with updated values
    return StockPosition(
        ticker=self.ticker,
        quantity=self.quantity,
        beta=self.beta,
        beta_adjusted_exposure=new_beta_adjusted_exposure,
        market_exposure=new_market_exposure,
        price=new_price,
        position_type=self.position_type,
        cost_basis=self.cost_basis,
        market_value=new_market_exposure
    )
```

#### 1.2 Refactor Option Position Class

Modify the `OptionPosition` class to support recalculation with a different underlying price:

```python
def recalculate_with_price(
    self, 
    new_underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None
) -> 'OptionPosition':
    """Create a new OptionPosition with recalculated values based on a new underlying price.
    
    Args:
        new_underlying_price: The new price of the underlying asset
        risk_free_rate: The risk-free interest rate
        implied_volatility: Optional override for implied volatility
        
    Returns:
        A new OptionPosition instance with updated values
    """
    from .options import calculate_bs_price, calculate_option_exposure
    
    # Create a temporary OptionContract for calculations
    from .options import OptionContract
    temp_contract = OptionContract(
        underlying=self.ticker,
        expiry=self.expiry,
        strike=self.strike,
        option_type=self.option_type,
        quantity=self.quantity,
        current_price=self.price,
        description=getattr(self, 'description', f"{self.ticker} {self.option_type} {self.strike} {self.expiry}")
    )
    
    # Calculate new option price
    new_price = calculate_bs_price(
        temp_contract,
        new_underlying_price,
        risk_free_rate,
        implied_volatility
    )
    
    # Calculate new exposures
    exposures = calculate_option_exposure(
        temp_contract,
        new_underlying_price,
        self.underlying_beta,
        risk_free_rate,
        implied_volatility
    )
    
    # Create a new instance with updated values
    return OptionPosition(
        ticker=self.ticker,
        position_type=self.position_type,
        quantity=self.quantity,
        beta=self.beta,
        beta_adjusted_exposure=exposures['beta_adjusted_exposure'],
        strike=self.strike,
        expiry=self.expiry,
        option_type=self.option_type,
        delta=exposures['delta'],
        delta_exposure=exposures['delta_exposure'],
        notional_value=self.notional_value,
        underlying_beta=self.underlying_beta,
        market_exposure=exposures['delta_exposure'],
        price=new_price,
        cost_basis=self.cost_basis,
        market_value=new_price * self.quantity * 100
    )
```

#### 1.3 Create Portfolio Recalculation Function

Create a new function in `portfolio.py` to recalculate portfolio groups with new prices:

```python
def recalculate_portfolio_with_prices(
    groups: list[PortfolioGroup],
    price_adjustments: dict[str, float],
    cash_like_positions: list[dict] | None = None,
    pending_activity_value: float = 0.0,
) -> tuple[list[PortfolioGroup], PortfolioSummary]:
    """Recalculate portfolio groups and summary with adjusted prices.
    
    Args:
        groups: Original portfolio groups
        price_adjustments: Dictionary mapping tickers to price adjustment factors
                          (e.g., {'SPY': 1.05} for a 5% increase)
        cash_like_positions: Cash-like positions
        pending_activity_value: Value of pending activity
        
    Returns:
        Tuple of (recalculated_groups, recalculated_summary)
    """
    # Implementation details...
```

### Phase 2: Implementing the Simulator

#### 2.1 Create Simulator Module

Create a new module `src/folio/simulator.py` with the core simulation logic:

```python
def simulate_portfolio_with_spy_changes(
    portfolio_groups: list[PortfolioGroup],
    spy_changes: list[float],
    cash_like_positions: list[dict] | None = None,
    pending_activity_value: float = 0.0,
) -> dict[str, Any]:
    """Simulate portfolio performance across different SPY price changes.
    
    Args:
        portfolio_groups: Portfolio groups to simulate
        spy_changes: List of SPY price change percentages (e.g., [-0.3, -0.25, ..., 0.25, 0.3])
        cash_like_positions: Cash-like positions
        pending_activity_value: Value of pending activity
        
    Returns:
        Dictionary with simulation results
    """
    # Implementation details...
```

#### 2.2 Create Chart Data Transformation Function

Add a new function to `chart_data.py` to transform simulation results for visualization:

```python
def transform_for_spy_simulator_chart(
    simulation_results: dict[str, Any]
) -> dict[str, Any]:
    """Transform simulation results for the SPY simulator chart.
    
    Args:
        simulation_results: Results from simulate_portfolio_with_spy_changes
        
    Returns:
        Dict containing data and layout for the chart
    """
    # Implementation details...
```

### Phase 3: Implementing the UI

#### 3.1 Create Tab Component

Create a new tab component for the simulator:

```python
def create_simulator_tab():
    """Create the simulator tab component."""
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardHeader("Portfolio SPY Simulator"),
                    dbc.CardBody(
                        [
                            create_spy_simulator_chart(),
                        ]
                    ),
                ],
                className="mb-4 chart-card",
            ),
        ],
        id="simulator-tab",
    )
```

#### 3.2 Create Chart Component

Create a chart component for the simulator:

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
                        "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
                        "paper_bgcolor": "white",
                        "plot_bgcolor": "white",
                        "autosize": True,
                    },
                },
                style={"width": "100%", "height": "100%"},
            ),
        ],
        className="mb-4",
    )
```

#### 3.3 Implement Callback

Implement a callback to update the simulator chart when the portfolio changes:

```python
@app.callback(
    Output("spy-simulator-chart", "figure"),
    [Input("portfolio-summary", "data")],
)
def update_spy_simulator_chart(portfolio_summary_json):
    """Update the SPY simulator chart based on portfolio data."""
    # Implementation details...
```

### Phase 4: Testing

#### 4.1 Unit Tests

Create unit tests for the simulator functions:

1. Test the recalculation functions for stock and option positions
2. Test the portfolio recalculation function
3. Test the simulator function with different SPY changes

#### 4.2 Integration Tests

Create integration tests for the simulator:

1. Test the simulator with a sample portfolio
2. Test the chart data transformation function
3. Test the UI components and callbacks

## Implementation Details

### Simulation Algorithm

For each SPY change percentage:

1. Calculate the new SPY price: `new_spy_price = current_spy_price * (1 + spy_change)`
2. For each stock position:
   - Calculate the new stock price: `new_stock_price = current_stock_price * (1 + (spy_change * beta))`
   - Recalculate the position with the new price
3. For each option position:
   - Calculate the new underlying price: `new_underlying_price = current_underlying_price * (1 + (spy_change * beta))`
   - Recalculate the option price and exposures with the new underlying price
4. Recalculate the portfolio summary with the new positions
5. Store the results for that SPY change

### Chart Visualization

The chart will show:

1. Portfolio value on the primary y-axis
2. Portfolio exposure on the secondary y-axis (optional)
3. SPY change percentage on the x-axis
4. A vertical line at 0% to indicate the current position

## Dependencies

This feature depends on:

1. Existing portfolio data model (`data_model.py`)
2. Existing option pricing functions (`options.py`)
3. Existing portfolio calculation functions (`portfolio.py`, `portfolio_value.py`)
4. Existing chart components and utilities (`charts.py`, `chart_data.py`)

## Timeline

1. Phase 1 (Refactoring): 2-3 days
2. Phase 2 (Simulator): 2-3 days
3. Phase 3 (UI): 1-2 days
4. Phase 4 (Testing): 1-2 days

Total estimated time: 6-10 days

## Risks and Mitigations

1. **Risk**: Option pricing calculations may be slow for large portfolios
   **Mitigation**: Implement caching or optimize the calculations

2. **Risk**: Extreme price changes may lead to unrealistic option prices
   **Mitigation**: Add bounds checking and warnings for extreme scenarios

3. **Risk**: UI performance may degrade with large datasets
   **Mitigation**: Optimize chart rendering and consider pagination or sampling

## Future Enhancements

1. Allow users to customize the simulation range and increments
2. Add the ability to simulate custom scenarios (e.g., specific price changes for individual stocks)
3. Include volatility adjustments for more realistic option pricing
4. Add risk metrics like VaR (Value at Risk) based on the simulation results
