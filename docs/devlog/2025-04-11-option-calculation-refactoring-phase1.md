# Option Calculation Refactoring - Phase 1

Date: 2025-04-11

## Summary

This is the first phase of the option calculation refactoring plan outlined in `docs/devplan/2025-04-11-option-calculation-refactoring.md`. In this phase, we've added new functions to `src/folio/option_utils.py` to centralize option exposure calculations and improve code reuse.

## Changes

### 1. Added `calculate_option_exposure` Function

Added a new function to calculate option exposure metrics:

```python
def calculate_option_exposure(
    option: OptionPosition,
    underlying_price: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> dict[str, float]:
    """Calculate exposure metrics for an option position."""
    # Calculate delta using Black-Scholes
    delta = calculate_option_delta(
        option, 
        underlying_price, 
        risk_free_rate=risk_free_rate, 
        implied_volatility=implied_volatility
    )
    
    # Calculate delta exposure
    delta_exposure = delta * option.notional_value
    
    # Calculate beta-adjusted exposure
    beta_adjusted_exposure = delta_exposure * beta
    
    return {
        'delta': delta,
        'delta_exposure': delta_exposure,
        'beta_adjusted_exposure': beta_adjusted_exposure,
    }
```

This function centralizes the calculation of option exposures, ensuring consistent calculation across the codebase.

### 2. Added `process_options` Function

Added a new function to process multiple options at once:

```python
def process_options(
    options_data: list[dict],
    prices: dict[str, float],
    betas: dict[str, float] | None = None,
) -> list[dict]:
    """Process a list of option data dictionaries."""
    # Implementation details...
```

This function handles:
- Parsing option descriptions
- Calculating exposures
- Error handling
- Returning processed option data

### 3. Added Comprehensive Tests

Added tests for the new functions:
- `test_calculate_option_exposure`: Tests that exposure calculations are correct for different option types and positions
- `test_process_options`: Tests the batch processing of options
- `test_process_options_with_missing_price`: Tests handling of missing prices
- `test_process_options_with_error`: Tests error handling

## Next Steps

In the next phase, we'll refactor the option processing in `src/folio/portfolio.py` to use these new functions, which will:
1. Reduce code duplication
2. Improve consistency
3. Separate concerns (data processing vs. option calculations)

## Related Documents

- [Option Calculation Refactoring Plan](../devplan/2025-04-11-option-calculation-refactoring.md)
