# SPY Simulator Feature Handoff (2025-04-25)

## Overview

The SPY Simulator feature allows users to visualize how their portfolio would perform under different SPY price movements. This is a critical feature for understanding portfolio risk and market exposure. The core functionality is implemented but requires further refinement and UI integration.

## Current Status

- **Core Simulation Logic**: Implemented in `src/folio/simulator.py`
- **Price Update Functionality**: Enhanced in `src/folio/portfolio.py`
- **App Integration**: Basic integration in `src/folio/app.py`
- **UI Components**: Not yet implemented
- **Testing**: Basic test script in `scripts/test_spy_simulator.py`
- **Debugging**: Enhanced debugging script in `scripts/debug_spy_simulator.py`

## Issues Identified

1. **Simulation Accuracy**: The portfolio value decreases as SPY increases beyond +5%, which initially seemed counterintuitive. After investigation, this appears to be correct behavior due to the portfolio's composition:
   - Significant short positions (e.g., ARKK with -10,000 shares)
   - Many short call options and long put options
   - Complex option strategies with non-linear price responses

2. **Beta Asymmetry**: The portfolio has a beta of 0.65 on down moves but -0.08 on up moves, indicating it's much more sensitive to downside moves than upside moves.

3. **Price Updates**: Some positions had zero or missing prices, causing calculation issues. This has been addressed with enhanced price updating functionality.

## What's Been Done

1. **Enhanced Simulator**:
   - Modified `simulate_portfolio_with_spy_changes` to track position-level data
   - Added detailed position tracking and analysis to simulation results
   - Implemented calculation of position-level changes relative to baseline

2. **Improved Price Updates**:
   - Added `update_all_prices` function to fetch current market prices
   - Modified `process_portfolio_data` to update prices during portfolio loading
   - Added handling for positions with zero or missing prices

3. **Debugging Tools**:
   - Created `scripts/test_spy_simulator.py` for basic testing
   - Created `scripts/debug_spy_simulator.py` with detailed logging and analysis
   - Added comprehensive logging to understand position-level behavior

4. **Documentation**:
   - Created implementation plan in `docs/devplan/2025-04-24-portfolio-spy-simulator-implementation.md`
   - Documented debugging process in `docs/devlog/2025-04-25-debugging-spy-simulator-accuracy.md`

## Key Findings

1. The simulator is working correctly, but the portfolio's complex composition creates a non-linear response to SPY movements.

2. The decrease in portfolio value as SPY increases beyond +5% is due to:
   - Short stock positions losing value as SPY increases
   - Short call options losing value as underlying stocks increase
   - Long put options losing value as underlying stocks increase
   - Non-linear option pricing behavior, especially for options near strike prices

3. There's a significant discrepancy between the expected portfolio value at +10% SPY ($2,843,881.32) and the actual value ($2,660,132.29), a difference of -$183,749.03 or -6.85% of the portfolio.

## Next Steps

1. **UI Implementation**:
   - Create chart component to visualize portfolio performance across SPY changes
   - Add summary cards for key metrics (beta, max gain/loss, etc.)
   - Implement position-level breakdown to show which positions drive performance

2. **Feature Enhancements**:
   - Add ability to customize simulation range and increments
   - Implement position-level contribution analysis
   - Add option to exclude specific positions from simulation

3. **Testing and Validation**:
   - Create comprehensive test suite for the simulator
   - Validate simulation results against expected behavior
   - Test with different portfolio compositions

4. **Documentation**:
   - Update user documentation to explain the feature
   - Add tooltips and explanations in the UI
   - Document any limitations or caveats

## Implementation Details

### Simulator Function

The enhanced `simulate_portfolio_with_spy_changes` function in `simulator.py` now:
1. Tracks position-level values and exposures at each SPY change level
2. Calculates changes relative to the 0% SPY change point
3. Returns comprehensive results including position-level data

Example usage:
```python
results = simulate_portfolio_with_spy_changes(
    portfolio_groups=groups,
    spy_changes=np.arange(-0.10, 0.11, 0.01).tolist(),  # -10% to +10% in 1% increments
    cash_like_positions=summary.cash_like_positions,
    pending_activity_value=summary.pending_activity_value,
)
```

The results now include:
- `spy_changes`: List of SPY change percentages
- `portfolio_values`: List of portfolio values at each SPY change
- `portfolio_exposures`: List of portfolio exposures at each SPY change
- `position_values`: Dictionary mapping tickers to lists of position values
- `position_exposures`: Dictionary mapping tickers to lists of position exposures
- `position_details`: Dictionary with detailed information about each position
- `position_changes`: Dictionary with calculated changes for each position

### Price Update Functions

Two new functions in `portfolio.py` handle price updates:

1. `update_zero_price_positions`: Updates only positions with zero prices
2. `update_all_prices`: Updates prices for all positions

The `process_portfolio_data` function now accepts an `update_prices` parameter (default: True) to control whether price updates are performed.

## Testing

Use the following scripts for testing and debugging:

1. `scripts/test_spy_simulator.py`: Basic test script that loads a portfolio and runs the simulator
2. `scripts/debug_spy_simulator.py`: Enhanced debugging script with detailed logging and analysis

To run the tests:
```bash
python scripts/test_spy_simulator.py
python scripts/debug_spy_simulator.py
```

## Known Limitations

1. **Performance**: The simulator can be slow for large portfolios with many options due to the recalculation of option prices at each SPY change level.

2. **Option Pricing**: The Black-Scholes model used for option pricing may not accurately reflect real-world option price changes, especially for large price movements.

3. **Beta Calculation**: The beta values used for price adjustments are static and may not capture the dynamic nature of market correlations.

## Conclusion

The SPY Simulator feature is functionally implemented but requires UI integration and further refinement. The core simulation logic is working correctly, but the portfolio's complex composition creates a non-linear response to SPY movements that may initially seem counterintuitive.

By completing the UI implementation and adding the suggested enhancements, this feature will provide users with valuable insights into their portfolio's behavior under different market conditions.

## Contact Information

If you have any questions while I'm away, please refer to:
- The detailed debugging log in `docs/devlog/2025-04-25-debugging-spy-simulator-accuracy.md`
- The implementation plan in `docs/devplan/2025-04-24-portfolio-spy-simulator-implementation.md`
- The test scripts in `scripts/test_spy_simulator.py` and `scripts/debug_spy_simulator.py`
