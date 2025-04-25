# SPY Simulator Accuracy Debugging Plan (2025-04-25)

## Problem Statement

The SPY simulator is producing results that appear inaccurate and counterintuitive. Specifically:

1. The portfolio value decreases as SPY increases (beyond +5%), which is unexpected for a typical portfolio
2. There's a significant asymmetry between up and down beta (beta_up = -0.08, beta_down = 0.65)
3. The maximum portfolio value occurs at SPY +5%, after which it declines, suggesting potential calculation issues

These results suggest there may be issues with how we're calculating adjusted prices, particularly for options, or how we're aggregating the portfolio value after price adjustments.

## Debugging Approach

### 1. Enhanced Logging and Tracing

Add detailed logging throughout the simulation process to identify where calculations might be going wrong:

#### 1.1 Price Adjustment Calculation

```python
# In simulate_portfolio_with_spy_changes function
for spy_change in spy_changes:
    logger.debug(f"\n--- Simulating SPY change: {spy_change:.1%} ---")
    
    # Calculate price adjustments for each ticker based on its beta
    price_adjustments = {}
    for group in portfolio_groups:
        # Use the group's beta to calculate price adjustment
        beta = group.beta
        price_adjustment = 1.0 + (spy_change * beta)
        price_adjustments[group.ticker] = price_adjustment
        logger.debug(f"  {group.ticker}: beta={beta:.2f}, adjustment={price_adjustment:.4f}")
```

#### 1.2 Position Value Calculation

Add logging to the recalculate_portfolio_with_prices function to show before/after values:

```python
# In recalculate_portfolio_with_prices function
logger.debug(f"Recalculating portfolio with price adjustments for SPY change: {spy_change:.1%}")

# Log original values before adjustment
total_original_value = sum(group.total_market_value for group in portfolio_groups)
logger.debug(f"Original portfolio value: {format_currency(total_original_value)}")

# Log each group's original values
for group in portfolio_groups:
    logger.debug(f"  {group.ticker}: original value={format_currency(group.total_market_value)}")
    
    # Log stock position details
    if group.stock_position:
        logger.debug(f"    Stock: price={group.stock_position.price:.2f}, value={format_currency(group.stock_position.market_value)}")
    
    # Log option position details
    for option in group.option_positions:
        logger.debug(f"    Option {option.ticker}: price={option.price:.2f}, delta={option.delta:.2f}, value={format_currency(option.market_value)}")

# After recalculation, log the new values
logger.debug(f"Recalculated portfolio value: {format_currency(recalculated_summary.portfolio_estimate_value)}")
for group in recalculated_groups:
    value_change = group.total_market_value - original_values.get(group.ticker, 0)
    pct_change = (value_change / original_values.get(group.ticker, 1)) * 100 if original_values.get(group.ticker, 0) != 0 else 0
    logger.debug(f"  {group.ticker}: new value={format_currency(group.total_market_value)}, change={format_currency(value_change)} ({pct_change:.2f}%)")
    
    # Log significant changes
    if abs(pct_change) > 20:
        logger.warning(f"  Large value change for {group.ticker}: {pct_change:.2f}%")
```

#### 1.3 Option Pricing Calculation

Add detailed logging to the option pricing calculation to identify potential issues:

```python
# In OptionPosition.recalculate_with_price method
logger.debug(f"Recalculating option {self.ticker} with new underlying price: {new_underlying_price:.2f}")
logger.debug(f"  Original: price={self.price:.4f}, delta={self.delta:.4f}, value={format_currency(self.market_value)}")

try:
    # Calculate new option price
    new_price = calculate_option_price(
        option_type=self.option_type,
        strike=self.strike,
        underlying_price=new_underlying_price,
        days_to_expiry=self.days_to_expiry,
        volatility=self.implied_volatility,
        risk_free_rate=self.risk_free_rate,
    )
    
    # Calculate new delta
    new_delta = calculate_option_delta(
        option_type=self.option_type,
        strike=self.strike,
        underlying_price=new_underlying_price,
        days_to_expiry=self.days_to_expiry,
        volatility=self.implied_volatility,
        risk_free_rate=self.risk_free_rate,
    )
    
    # Calculate new market value and exposure
    new_market_value = new_price * self.quantity
    new_market_exposure = new_delta * new_underlying_price * self.quantity
    
    logger.debug(f"  New: price={new_price:.4f}, delta={new_delta:.4f}, value={format_currency(new_market_value)}")
    logger.debug(f"  Change: price={new_price-self.price:.4f}, delta={new_delta-self.delta:.4f}, value={format_currency(new_market_value-self.market_value)}")
    
    # Check for extreme changes
    price_pct_change = ((new_price / self.price) - 1) * 100 if self.price != 0 else float('inf')
    if abs(price_pct_change) > 100:
        logger.warning(f"  Extreme price change for {self.ticker}: {price_pct_change:.2f}%")
    
    return OptionPosition(
        ticker=self.ticker,
        quantity=self.quantity,
        price=new_price,
        delta=new_delta,
        market_value=new_market_value,
        market_exposure=new_market_exposure,
        option_type=self.option_type,
        strike=self.strike,
        expiry=self.expiry,
        days_to_expiry=self.days_to_expiry,
        implied_volatility=self.implied_volatility,
        risk_free_rate=self.risk_free_rate,
    )
except Exception as e:
    logger.error(f"Error recalculating option {self.ticker}: {e}")
    # Return the original option position if calculation fails
    return self
```

### 2. Tighten Simulation Range

Modify the simulator to use a tighter range with smaller increments to better analyze the behavior:

```python
def simulate_portfolio_with_spy_changes(
    portfolio_groups,
    spy_changes=None,
    cash_like_positions=None,
    pending_activity_value=0.0,
):
    """Simulate portfolio performance across different SPY price movements."""
    if not portfolio_groups:
        logger.warning("Cannot simulate an empty portfolio")
        return {
            "spy_changes": [],
            "portfolio_values": [],
            "portfolio_exposures": [],
            "current_value": 0.0,
            "current_exposure": 0.0,
        }

    # Use a tighter range with 1% increments for debugging
    if spy_changes is None:
        spy_changes = [i / 100 for i in range(-10, 11, 1)]  # -10% to +10% in 1% increments
```

### 3. Add Position-by-Position Breakdown

Create a detailed breakdown of each position's contribution to the portfolio value at each SPY change level:

```python
# In simulate_portfolio_with_spy_changes function
# Initialize position breakdown
position_breakdown = {ticker: [] for ticker in [group.ticker for group in portfolio_groups]}

# For each SPY change
for spy_change in spy_changes:
    # ... existing code ...
    
    # Store position-by-position breakdown
    for group in recalculated_groups:
        position_breakdown[group.ticker].append({
            "spy_change": spy_change,
            "market_value": group.total_market_value,
            "stock_value": group.stock_position.market_value if group.stock_position else 0,
            "option_value": sum(op.market_value for op in group.option_positions),
            "beta": group.beta,
        })

# Add position breakdown to results
results["position_breakdown"] = position_breakdown
```

### 4. Identify Outliers

Add code to identify positions that behave unexpectedly:

```python
# After simulation is complete
logger.debug("\nAnalyzing position behavior:")

# Find positions with unexpected behavior (value decreases as SPY increases)
negative_correlation_positions = []
for ticker, values in position_breakdown.items():
    # Skip positions with no values
    if not values:
        continue
        
    # Calculate correlation between SPY change and position value
    spy_changes = [v["spy_change"] for v in values]
    position_values = [v["market_value"] for v in values]
    
    # Simple correlation check: compare values at -10% and +10%
    minus_10_value = next((v["market_value"] for v in values if abs(v["spy_change"] + 0.1) < 0.001), None)
    plus_10_value = next((v["market_value"] for v in values if abs(v["spy_change"] - 0.1) < 0.001), None)
    
    if minus_10_value is not None and plus_10_value is not None:
        expected_direction = 1 if values[0]["beta"] > 0 else -1
        actual_direction = 1 if plus_10_value > minus_10_value else -1
        
        if expected_direction != actual_direction:
            negative_correlation_positions.append({
                "ticker": ticker,
                "beta": values[0]["beta"],
                "minus_10_value": minus_10_value,
                "plus_10_value": plus_10_value,
                "change": plus_10_value - minus_10_value,
            })

logger.debug(f"Found {len(negative_correlation_positions)} positions with unexpected behavior:")
for pos in negative_correlation_positions:
    logger.debug(f"  {pos['ticker']}: beta={pos['beta']:.2f}, -10% value={format_currency(pos['minus_10_value'])}, +10% value={format_currency(pos['plus_10_value'])}, change={format_currency(pos['change'])}")
```

### 5. Test Script Modifications

Update the test script to include the enhanced logging and analysis:

```python
# In test_spy_simulator.py
import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler("spy_simulator_debug.log"),
                       logging.StreamHandler()
                   ])

# ... existing code ...

# Add position breakdown analysis
if "position_breakdown" in results:
    print("\nPosition Breakdown Analysis:")
    print("-" * 80)
    
    # Find positions with largest positive and negative changes
    largest_positive_change = None
    largest_negative_change = None
    max_positive_value = 0
    max_negative_value = 0
    
    for ticker, values in results["position_breakdown"].items():
        if not values:
            continue
            
        # Get values at -10% and +10%
        minus_10_value = next((v["market_value"] for v in values if abs(v["spy_change"] + 0.1) < 0.001), None)
        plus_10_value = next((v["market_value"] for v in values if abs(v["spy_change"] - 0.1) < 0.001), None)
        
        if minus_10_value is not None and plus_10_value is not None:
            change = plus_10_value - minus_10_value
            
            if change > max_positive_value:
                max_positive_value = change
                largest_positive_change = {
                    "ticker": ticker,
                    "change": change,
                    "minus_10_value": minus_10_value,
                    "plus_10_value": plus_10_value,
                }
                
            if change < max_negative_value:
                max_negative_value = change
                largest_negative_change = {
                    "ticker": ticker,
                    "change": change,
                    "minus_10_value": minus_10_value,
                    "plus_10_value": plus_10_value,
                }
    
    if largest_positive_change:
        print(f"Largest positive change: {largest_positive_change['ticker']}")
        print(f"  -10% value: {format_currency(largest_positive_change['minus_10_value'])}")
        print(f"  +10% value: {format_currency(largest_positive_change['plus_10_value'])}")
        print(f"  Change: {format_currency(largest_positive_change['change'])}")
        
    if largest_negative_change:
        print(f"Largest negative change: {largest_negative_change['ticker']}")
        print(f"  -10% value: {format_currency(largest_negative_change['minus_10_value'])}")
        print(f"  +10% value: {format_currency(largest_negative_change['plus_10_value'])}")
        print(f"  Change: {format_currency(largest_negative_change['change'])}")
```

## Implementation Plan

### Phase 1: Enhanced Logging (1 day)

1. Add detailed logging to the simulator.py file
   - Add logging for price adjustment calculations
   - Add logging for portfolio value calculations
   - Add logging for option pricing calculations

2. Modify the simulator to use a tighter range (-10% to +10% with 1% increments)

### Phase 2: Position Breakdown Analysis (1 day)

1. Add position-by-position breakdown to the simulation results
2. Add code to identify positions with unexpected behavior
3. Update the test script to include the enhanced analysis

### Phase 3: Investigation and Fixes (1-2 days)

1. Run the test script with enhanced logging
2. Analyze the logs to identify issues
3. Focus on option pricing calculations, as they are likely the source of the issues
4. Implement fixes for any identified issues

### Phase 4: Validation (1 day)

1. Run the test script with the fixes
2. Verify that the simulation results are now more accurate and intuitive
3. Document the issues found and the fixes implemented

## Potential Issues to Investigate

1. **Option Pricing Model**: The Black-Scholes model may not be accurately calculating option prices for large price changes. We should verify that the model is working correctly and consider adding bounds checking.

2. **Delta Calculation**: The delta values may not be accurately reflecting how option prices change with underlying price changes. We should verify that delta calculations are correct.

3. **Implied Volatility**: We may need to adjust implied volatility as prices change, as volatility tends to increase as prices fall and decrease as prices rise.

4. **Short Positions**: We should verify that short positions (negative quantities) are being handled correctly in the simulation.

5. **Beta Values**: We should verify that beta values are being applied correctly to calculate price adjustments.

6. **Cash-Like Positions**: We should verify that cash-like positions are being handled correctly in the simulation.

7. **Aggregation**: We should verify that the portfolio value is being correctly aggregated from individual position values.

## Expected Outcome

By implementing these debugging steps, we expect to:

1. Identify the specific issues causing the unexpected simulation results
2. Implement fixes for these issues
3. Produce more accurate and intuitive simulation results
4. Better understand the behavior of the portfolio under different market conditions

This will provide users with a more reliable tool for understanding their portfolio's sensitivity to market movements.
