# Portfolio SPY Simulator Specification

## Overview

The Portfolio SPY Simulator is a feature that will allow users to visualize how their entire portfolio is expected to perform as the benchmark index (SPY) moves up or down. This simulation will use beta values for stocks and delta values for options to create a realistic projection of portfolio performance across a range of market scenarios.

## Business Value

1. **Risk Assessment**: Enables users to understand how their portfolio might perform in different market conditions.
2. **Portfolio Hedging**: Helps identify if the portfolio is properly hedged against market movements.
3. **Strategy Validation**: Allows users to validate if their portfolio construction aligns with their market outlook.
4. **Exposure Visualization**: Provides a clear visualization of the portfolio's actual market exposure.

## Feature Requirements

### Core Functionality

1. **SPY Movement Simulation**:
   - Simulate portfolio performance across a range of SPY price movements (from -30% to +30%).
   - Calculate data points at regular intervals (e.g., every 5%).
   - Center the simulation at 0% (current market level).

2. **Beta-Based Stock Simulation**:
   - For each stock position, calculate expected price changes based on its beta value.
   - Example: If a stock has beta of 2.0, it should move 2% for every 1% SPY movement.

3. **Option Simulation**:
   - For option positions, use delta to calculate expected price changes.
   - Account for non-linear price movements of options as underlying prices change.
   - Incorporate existing option pricing models from the codebase.

4. **Aggregate Portfolio View**:
   - Combine all position simulations to show total portfolio performance.
   - Display both absolute dollar value changes and percentage changes.

### Visualization Requirements

1. **Chart Visualization**:
   - Primary view: Line chart showing portfolio value across SPY price changes.
   - X-axis: SPY price change percentage (-30% to +30%).
   - Y-axis: Portfolio value or percentage change.
   - Clear indication of current position (0% SPY change).

2. **Data Table View** (optional):
   - Tabular representation of the simulation data.
   - Columns: SPY change %, Portfolio value, Portfolio change %, Key metrics.

3. **Interactive Elements**:
   - Ability to hover over points to see detailed information.
   - Optional: Toggle between absolute values and percentage changes.
   - Optional: Ability to show/hide individual position contributions.

## Technical Approach

### Simulation Algorithm

1. **For each SPY movement percentage** (e.g., -30%, -25%, ..., 0%, ..., +25%, +30%):
   - Calculate the corresponding SPY price.
   - For each stock position:
     - Calculate the expected price change using its beta value.
     - Calculate the new position value.
   - For each option position:
     - Calculate the expected underlying price change.
     - Use option pricing models to determine the new option price.
     - Calculate the new position value.
   - Sum all position values to get the total portfolio value at that SPY level.

2. **Calculation Formulas**:
   - For stocks: `new_price = current_price * (1 + (spy_change_percent * beta))`
   - For options: Use existing option pricing models with the new underlying price.

### Integration Points

1. **Data Sources**:
   - Portfolio positions from the existing data model.
   - Beta values from the existing beta calculation functions.
   - Option deltas and pricing from existing option utility functions.

2. **UI Integration**:
   - Add a new chart component to the portfolio dashboard.
   - Integrate with existing chart styling and configuration.

## User Experience

1. **Access Point**:
   - Add a "Portfolio Simulator" card or tab in the main dashboard.
   - Place alongside existing portfolio analysis tools.

2. **Interaction Flow**:
   - User loads their portfolio.
   - The simulator automatically calculates and displays the projection.
   - User can interact with the chart to see specific data points.
   - Optional: User can adjust simulation parameters (range, intervals).

3. **Visual Design**:
   - Consistent with existing chart components.
   - Clear color coding for gains and losses.
   - Prominent display of current portfolio value at 0% SPY change.

## Implementation Considerations

1. **Performance Optimization**:
   - Calculate simulation points on demand rather than continuously.
   - Consider caching results until portfolio changes.
   - Optimize option pricing calculations for multiple price points.

2. **Edge Cases**:
   - Handle portfolios with no beta exposure (all cash, etc.).
   - Account for extreme market movements and potential non-linear effects.
   - Handle options near expiration appropriately.

3. **Limitations**:
   - The simulation assumes a linear relationship between SPY movements and stock price changes (via beta).
   - Option pricing becomes less accurate for large price movements.
   - The simulation does not account for changes in volatility, interest rates, or time decay.

## Open Questions

1. Should we include a volatility adjustment factor for extreme market movements?
2. How should we handle cash and cash-like instruments in the simulation?
3. Should we provide additional metrics like maximum drawdown or risk measures?
4. How should we visualize positions with negative beta (inverse ETFs, etc.)?
5. Should we allow users to simulate custom SPY movement scenarios?

## Success Criteria

1. The simulator accurately reflects expected portfolio behavior based on beta and delta values.
2. Users can clearly understand their portfolio's sensitivity to market movements.
3. The feature integrates seamlessly with the existing portfolio analysis tools.
4. Performance remains acceptable even with large portfolios containing many options.
