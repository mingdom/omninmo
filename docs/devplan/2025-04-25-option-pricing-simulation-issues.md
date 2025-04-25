# Option Pricing Simulation Issues

## Overview

This document outlines several issues identified with option pricing in the SPY simulator that may also affect the broader application. These issues cause the portfolio simulation to behave unexpectedly, particularly for portfolios with short option positions (covered calls and sold puts).

## Background

During testing of the SPY simulator, we observed that the portfolio showed unexpected behavior:

1. Positions with sold puts and covered calls showed large negative contributions on downside moves
2. The portfolio had a negative beta on upside moves, meaning it decreased in value as SPY increased beyond +4%
3. There were large discrepancies between expected and actual behavior based on beta values

These behaviors are inconsistent with how a portfolio of long stock positions with covered calls and sold puts should behave in the market.

## Key Issues Identified

### 1. Notional Value Calculation

**Problem**: In the `OptionContract` class, the notional value is calculated using the strike price instead of the underlying price:

```python
@property
def notional_value(self) -> float:
    """Calculate notional value (strike * 100 * abs(quantity))."""
    return self.strike * 100 * abs(self.quantity)
```

This is problematic because:
- The notional value should represent the total value of the underlying asset controlled by the option
- Using the strike price instead of the underlying price causes the notional value to remain static
- For deep in-the-money or out-of-the-money options, this creates significant discrepancies

**Impact**: This affects delta exposure calculations, which are used to determine how option positions contribute to portfolio exposure and value changes.

### 2. Notional Value Updates During Simulation

**Problem**: In the `recalculate_with_price` method of the `OptionPosition` class, the notional value was not being updated when the underlying price changed:

```python
# Create a new instance with updated values
return OptionPosition(
    # ... other parameters ...
    notional_value=self.notional_value,  # Using old notional value
    # ... other parameters ...
)
```

**Impact**: This caused option positions to have incorrect delta exposure during simulation, leading to unrealistic portfolio behavior for large price moves.

### 3. Volatility Assumptions

**Problem**: The Black-Scholes model uses a fixed volatility (default 0.3 or 30%) for all options regardless of market conditions:

```python
# Use provided volatility or default
if volatility is None:
    volatility = 0.3  # Default volatility
```

In reality, volatility typically:
- Increases during market downturns (volatility skew)
- Varies based on option moneyness (strike relative to underlying price)
- Changes with time to expiration

**Impact**: This causes option prices and deltas to be inaccurate, especially for large price moves.

### 4. Delta Calculation for Short Options

**Problem**: The `calculate_option_delta` function adjusts delta for short positions by inverting the sign:

```python
# Adjust for position direction (short positions have inverted delta)
adjusted_delta = raw_delta if option.quantity >= 0 else -raw_delta
```

While this correctly represents the directional exposure, it may not accurately capture how short options behave in extreme market conditions.

**Impact**: This contributes to the unrealistic behavior of short option positions in the simulation.

### 5. Intrinsic Value Fallback

**Problem**: The fallback calculation for option prices in case of errors uses a simple intrinsic value plus a small time value:

```python
# Return a reasonable default price based on intrinsic value
if option_position.option_type == "CALL":
    intrinsic = max(0, underlying_price - strike)
else:  # PUT
    intrinsic = max(0, strike - underlying_price)
# Add a small time value
return intrinsic + (underlying_price * 0.01)
```

This doesn't accurately capture how option prices change with large underlying price movements, especially for options with significant time value.

**Impact**: If the QuantLib calculation fails, the simulation falls back to this simplified model, which may produce unrealistic results.

## Scope of Impact

These issues affect:

1. **SPY Simulator**: Most directly affected, as it relies heavily on accurate option pricing for different market scenarios.

2. **Portfolio Exposure Calculations**: The delta exposure calculations may be inaccurate, affecting the reported market exposure.

3. **Risk Metrics**: Beta calculations and other risk metrics may be affected if they rely on option delta exposures.

4. **Portfolio Value Projections**: Any feature that projects portfolio value based on market changes may be affected.

The core portfolio value calculation based on current market prices should not be affected, as it uses actual market prices rather than model-based calculations.

## Proposed Solutions

### 1. Fix Notional Value Calculation

Update the `OptionContract` class to use the underlying price for notional value calculation:

```python
@property
def notional_value(self) -> float:
    """Calculate notional value (underlying_price * 100 * abs(quantity))."""
    # Need to store or pass the underlying price
    return self.underlying_price * 100 * abs(self.quantity)
```

### 2. Update Notional Value During Simulation

Ensure the `recalculate_with_price` method correctly updates the notional value:

```python
# Calculate new notional value based on new underlying price
new_notional_value = 100 * abs(self.quantity) * new_underlying_price

# Create a new instance with updated values
return OptionPosition(
    # ... other parameters ...
    notional_value=new_notional_value,  # Use the new notional value
    # ... other parameters ...
)
```

### 3. Implement Volatility Skew

Implement and use the `estimate_volatility_with_skew` function that's already defined but not used:

```python
def calculate_option_exposure(
    option: OptionContract,
    underlying_price: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> dict[str, float]:
    # Apply volatility skew if no implied volatility is provided
    if implied_volatility is None:
        implied_volatility = estimate_volatility_with_skew(option, underlying_price)
    
    # Rest of the function...
```

### 4. Improve Option Price Calculation for Large Moves

Enhance the option pricing model to better handle large price moves:

1. Implement a more sophisticated fallback model for when QuantLib calculations fail
2. Consider using a binomial tree model for American options, which may be more accurate for deep in/out-of-the-money options
3. Add gamma calculations to better capture how delta changes with price

### 5. Add Comprehensive Testing

Create detailed tests for option pricing and exposure calculations:

1. Test with various market scenarios (large up/down moves)
2. Test with different option types (calls, puts) and positions (long, short)
3. Test with different moneyness levels (in-the-money, at-the-money, out-of-the-money)
4. Test with different time to expiration values

## Implementation Plan

### Phase 1: Critical Fixes

1. Fix the notional value update in `recalculate_with_price` method (already implemented)
2. Implement volatility skew in option exposure calculations
3. Add comprehensive logging to track option calculations during simulation

### Phase 2: Enhanced Option Modeling

1. Update the `OptionContract` class to use underlying price for notional value
2. Improve the option pricing model for large price moves
3. Add gamma calculations to better capture non-linear option behavior

### Phase 3: Testing and Validation

1. Create comprehensive tests for option pricing and exposure calculations
2. Validate simulation results against expected behavior for different portfolio compositions
3. Compare model-based calculations with actual market data

## Conclusion

The issues identified with option pricing in the SPY simulator highlight the challenges of accurately modeling option behavior, especially for large market moves. By implementing the proposed solutions, we can significantly improve the accuracy of the simulation and provide more realistic projections of portfolio behavior under different market scenarios.

These improvements will not only enhance the SPY simulator but also improve the accuracy of exposure calculations and risk metrics throughout the application.
