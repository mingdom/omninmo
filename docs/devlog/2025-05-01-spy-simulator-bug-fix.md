# SPY Simulator Bug Fix

## Issue Description

When running the SPY simulator, we discovered a critical issue where the SPY position itself shows an inverted correlation with SPY price changes:

- When SPY goes up, the SPY position value decreases
- When SPY goes down, the SPY position value increases

This is counterintuitive and incorrect for a long position in SPY.

## Root Cause Analysis

After investigating the code, we found that the SPY position is being treated incorrectly in the simulation:

1. The SPY position value at 0% change is showing as negative (-$66,405.72), suggesting it's being treated as a short position when it should be a long position.

2. The simulation is applying the beta-based price adjustment to all positions, including SPY itself. Since SPY has a beta of 1.0 relative to itself, this means:
   - When SPY goes up by 10%, the SPY position's price is also increased by 10%
   - When SPY goes down by 10%, the SPY position's price is also decreased by 10%

3. However, the market value calculation is not correctly handling the sign of the position. For a long position, the market value should increase when the price increases, but the code is treating it as if it were a short position.

## Evidence

Running the simulator with focus on SPY shows:

```
SPY position value at 0% change: $-66405.72
SPY position value at -20.0% change: $-426700.76
Change: $-360295.04 (542.57%)
```

This indicates that:
1. The base value is negative, which is incorrect for a long position
2. The value becomes more negative when SPY decreases, which is the opposite of expected behavior

## Proposed Fix

1. In `src/folio/simulator.py`, modify the `simulate_portfolio_with_spy_changes` function to correctly handle the sign of positions:

```python
# Calculate price adjustments for each ticker based on its beta
price_adjustments = {}
for group in portfolio_groups:
    ticker = group.ticker
    beta = group.beta
    
    # Special case for SPY itself - use direct correlation
    if ticker == "SPY":
        price_adjustment = 1.0 + spy_change  # Direct 1:1 correlation
    else:
        price_adjustment = 1.0 + (spy_change * beta)
        
    price_adjustments[ticker] = price_adjustment
```

2. In `src/folio/portfolio.py`, ensure that the `recalculate_portfolio_with_prices` function correctly handles the sign of positions:

```python
# Recalculate stock position if it exists
recalculated_stock = None
if group.stock_position:
    current_price = group.stock_position.price
    new_price = current_price * adjustment_factor
    
    # Ensure market value calculation respects position sign
    recalculated_stock = group.stock_position.recalculate_with_price(new_price)
    
    # Verify that market value has the correct sign based on position direction
    if group.stock_position.quantity > 0:  # Long position
        assert recalculated_stock.market_value > 0, f"Long position {ticker} has negative market value"
    elif group.stock_position.quantity < 0:  # Short position
        assert recalculated_stock.market_value < 0, f"Short position {ticker} has positive market value"
```

3. Add more detailed logging to help diagnose similar issues in the future.

## Testing Plan

1. Run the simulator with focus on SPY to verify that:
   - SPY position value increases when SPY price increases
   - SPY position value decreases when SPY price decreases

2. Run the simulator on the full portfolio to verify that the overall portfolio behavior is more intuitive:
   - Portfolio value should generally increase when SPY increases (for a net long portfolio)
   - Portfolio value should generally decrease when SPY decreases (for a net long portfolio)

3. Add specific test cases to `tests/test_simulator.py` to verify correct handling of SPY and other positions.
