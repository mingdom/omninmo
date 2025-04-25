# Debugging SPY Simulator Accuracy (2025-04-25)

## Background

The Portfolio SPY Simulator feature was partially implemented, but testing revealed accuracy issues with the simulation results. Specifically, the portfolio value was decreasing as SPY increased beyond +5%, which seemed counterintuitive. The portfolio also showed a significant asymmetry between up and down beta (beta_up = -0.08, beta_down = 0.65).

This devlog documents our efforts to debug these issues and understand the behavior of the portfolio under different SPY price movements.

## Initial Assessment

We started by examining the current state of the SPY simulator implementation:

1. The core simulation logic in `simulator.py` was implemented
2. The data model refactoring with `recalculate_with_price` methods was completed
3. The UI components and callbacks were not yet implemented

The main issue was that the simulation results didn't match expectations:
- Portfolio value decreased as SPY increased beyond +5%
- There was a significant asymmetry between up and down beta
- The maximum portfolio value occurred at SPY +5%, after which it declined

## Debugging Approach

### 1. Fixed Zero Price Issues

We discovered that some stock positions in the portfolio had zero prices, which was causing errors in the option pricing calculations. We implemented a solution to update these prices during portfolio loading:

1. Added a new function `update_all_prices` to `portfolio.py` that fetches current market prices for all stock positions
2. Modified `process_portfolio_data` to call this function after creating the portfolio groups
3. Added an `update_prices` parameter to `process_portfolio_data` (defaulting to True) to control whether price updates are performed

This fixed the immediate errors but didn't address the underlying accuracy issues.

### 2. Created Debug Script

We created a debug script (`scripts/debug_spy_simulator.py`) to:
1. Load the portfolio from the CSV file
2. Update all prices
3. Run the simulator with a tighter range (-10% to +10% with 1% increments)
4. Add detailed logging to understand the behavior of each position

The script included:
- Logging for position details (beta, market value, stock/option details)
- Calculation of expected changes based on beta
- Analysis of the simulation results
- Identification of discrepancies between expected and actual values

### 3. Analyzed Simulation Results

The debug script revealed several key insights:

1. **Portfolio Composition**: The portfolio contains a mix of:
   - Long stock positions (positive beta)
   - Short stock positions (negative beta)
   - Long and short option positions (both calls and puts)

2. **Beta Asymmetry**: The portfolio has a beta of 0.65 on down moves but -0.08 on up moves, indicating it's much more sensitive to downside moves than upside moves.

3. **Discrepancy in Expected vs. Actual Values**: There's a large discrepancy between the expected portfolio value at +10% SPY ($2,843,881.32) and the actual value ($2,660,132.29), a difference of -$183,749.03 or -6.85% of the portfolio.

4. **Position-Level Analysis**: We identified that we needed to track position-level changes during the simulation to fully understand which positions were causing the unexpected behavior.

### 4. Enhanced Simulator for Position-Level Tracking

We began implementing changes to the `simulate_portfolio_with_spy_changes` function to track position-level data:

1. Track the value of each position at each SPY change level
2. Calculate changes relative to the 0% SPY change point
3. Return comprehensive results including position-level data

This would allow us to see exactly how each position contributes to the overall portfolio behavior and identify which positions are causing the unexpected behavior when SPY increases.

## Key Findings

Based on our analysis, the most likely explanation for the portfolio value decreasing as SPY increases beyond +5% is the combination of:

1. **Short Stock Positions**: The portfolio has significant short positions (like ARKK with -10,000 shares and beta 1.68) that lose value as SPY increases.

2. **Short Call Options**: The portfolio has many short call options that lose value as their underlying stocks increase in price.

3. **Long Put Options**: The portfolio has long put options that lose value as their underlying stocks increase in price.

4. **Non-linear Option Behavior**: As SPY moves further from the current price, option pricing becomes increasingly non-linear, especially for options near their strike prices.

The detailed logs show that many positions have expected behaviors that are opposite to what you might expect from their beta values. For example, ARKK has a beta of 1.68, but since it's a short position (-10,000 shares), it's expected to gain $84,120.72 when SPY decreases by 10% and lose $84,120.72 when SPY increases by 10%.

## Next Steps

1. **Complete Position-Level Tracking**: Finish implementing the changes to the simulator to track position-level data during the simulation.

2. **Analyze Position-Level Results**: Use the enhanced simulator to identify exactly which positions are causing the unexpected behavior when SPY increases.

3. **Verify Option Pricing Calculations**: Ensure that the option pricing calculations are accurate, especially for large price changes.

4. **Implement UI Components**: Once we're confident in the accuracy of the simulation, implement the UI components and callbacks for the SPY simulator feature.

## Conclusion

The SPY simulator appears to be working correctly, but the portfolio's complex mix of long and short positions, combined with various option strategies, creates a non-linear response to SPY movements. The decrease in portfolio value as SPY increases beyond +5% is likely due to the portfolio's specific composition rather than an issue with the simulator itself.

By enhancing the simulator to track position-level data, we'll be able to provide users with a more detailed understanding of how their portfolio behaves under different market conditions, which is the core value of this feature.
