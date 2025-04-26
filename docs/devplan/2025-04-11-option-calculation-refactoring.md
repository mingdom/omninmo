# Option Calculation Refactoring Plan

Date: 2025-04-11

## Overview

This document outlines a plan to refactor the option-related calculations in the Folio application. The goal is to improve code organization, reduce duplication, and ensure consistent handling of option calculations across the codebase.

## Current State Analysis

### Option Utilities in `src/folio/option_utils.py`

The `option_utils.py` module provides a comprehensive set of tools for option calculations:

1. **`OptionPosition` Class**
   - Represents a single option position with all relevant attributes
   - Provides calculated properties like `notional_value`, `signed_notional_value`, and `market_value`
   - Handles both long and short positions through the `quantity` attribute (positive for long, negative for short)

2. **Option Description Parsing**
   - `parse_month()`: Helper function to convert month abbreviations to numeric values
   - `parse_option_description()`: Parses option description strings into `OptionPosition` objects

3. **Option Pricing and Greeks Calculations**
   - `calculate_black_scholes_delta()`: Calculates raw delta using the Black-Scholes model
   - `calculate_bs_price()`: Calculates theoretical option price using Black-Scholes
   - `calculate_implied_volatility()`: Calculates implied volatility using bisection method
   - `estimate_volatility_with_skew()`: Estimates IV using a simplified volatility skew model
   - `get_implied_volatility()`: Primary interface for obtaining IV, with fallbacks
   - `calculate_option_delta()`: Wrapper that calculates delta and adjusts for position direction

4. **Option Grouping**
   - `group_options_by_underlying()`: Groups options by their underlying ticker

### Option Processing in `src/folio/portfolio.py`

The `portfolio.py` module contains several sections that deal with options:

1. **Option Identification and Parsing**
   - Identifies options based on description patterns
   - Parses option descriptions using `parse_option_description()`
   - Validates option fields (quantity, price, etc.)

2. **Option Metrics Calculation**
   - Calculates delta using `calculate_option_delta()`
   - Calculates notional value using `parsed_option.notional_value`
   - Calculates delta exposure as `delta * parsed_option.notional_value`
   - Calculates beta-adjusted exposure as `delta_exposure * beta`

3. **Option Exposure Aggregation**
   - Aggregates option exposures by direction (long/short)
   - Combines with stock exposures to calculate portfolio-level metrics

4. **Orphaned Options Processing**
   - Handles options without a corresponding stock position
   - Duplicates much of the same logic used for regular option processing

## Issues with Current Implementation

1. **Code Duplication**
   - Option processing logic is duplicated between regular and orphaned options
   - Similar validation and calculation steps are repeated in multiple places

2. **Inconsistent Exposure Calculation**
   - The exposure calculation (`delta * notional_value`) is duplicated in multiple places
   - Risk of inconsistent implementation if one location is updated but not others

3. **Mixing of Concerns**
   - `portfolio.py` contains both data processing logic and option calculation logic
   - Option-specific calculations should be centralized in `option_utils.py`

4. **Limited Reusability**
   - Option exposure calculation logic is embedded in the portfolio processing flow
   - Not easily reusable in other contexts or for testing

## Refactoring Goals

1. **Centralize Option Calculations**
   - Move all option-specific calculations to `option_utils.py`
   - Ensure `portfolio.py` only handles data processing and aggregation

2. **Reduce Duplication**
   - Create helper functions for common operations
   - Unify the processing of regular and orphaned options

3. **Improve Consistency**
   - Ensure consistent calculation of option exposures
   - Standardize how option positions are represented and processed

4. **Enhance Reusability**
   - Make option calculation functions more modular and reusable
   - Improve testability of option-related functionality

## Proposed Changes

### 1. Add Option Exposure Calculation to `option_utils.py`

Create a new function to calculate option exposure:

```python
def calculate_option_exposure(
    option: OptionPosition,
    underlying_price: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> dict[str, float]:
    """Calculate exposure metrics for an option position.

    Args:
        option: The option position
        underlying_price: The price of the underlying asset
        beta: The beta of the underlying asset relative to the market
        risk_free_rate: The risk-free interest rate
        implied_volatility: Optional override for implied volatility

    Returns:
        A dictionary containing exposure metrics:
        - 'delta': The option's delta
        - 'delta_exposure': The delta-adjusted exposure (delta * notional_value)
        - 'beta_adjusted_exposure': The beta-adjusted exposure (delta_exposure * beta)
    """
    # Calculate delta using Black-Scholes
    delta = calculate_option_delta(
        option, underlying_price, risk_free_rate=risk_free_rate, implied_volatility=implied_volatility
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

### 2. Add Batch Processing Function to `option_utils.py`

Create a function to process multiple options at once:

```python
def process_options(
    options_data: list[dict],
    prices: dict[str, float],
    betas: dict[str, float],
) -> list[dict]:
    """Process a list of option data dictionaries.

    Args:
        options_data: List of dictionaries containing option data
            Each dictionary must have:
            - 'description': Option description string
            - 'quantity': Option quantity
            - 'price': Option price
        prices: Dictionary mapping tickers to prices
        betas: Dictionary mapping tickers to betas

    Returns:
        List of dictionaries with processed option data including exposures
    """
    processed_options = []
    
    for opt_data in options_data:
        try:
            # Parse option description
            parsed_option = parse_option_description(
                opt_data['description'],
                opt_data['quantity'],
                opt_data['price']
            )
            
            # Get underlying price and beta
            underlying = parsed_option.underlying
            if underlying not in prices:
                logger.warning(f"No price found for {underlying}. Skipping option {parsed_option.description}.")
                continue
                
            underlying_price = prices[underlying]
            beta = betas.get(underlying, 1.0)  # Default to 1.0 if no beta found
            
            # Calculate exposures
            exposures = calculate_option_exposure(
                parsed_option, underlying_price, beta
            )
            
            # Combine original data with calculated metrics
            processed_opt = {
                'ticker': underlying,
                'option_symbol': opt_data.get('symbol', ''),
                'description': parsed_option.description,
                'quantity': parsed_option.quantity,
                'beta': beta,
                'strike': parsed_option.strike,
                'expiry': parsed_option.expiry.strftime('%Y-%m-%d'),
                'option_type': parsed_option.option_type,
                'price': parsed_option.current_price,
                'delta': exposures['delta'],
                'delta_exposure': exposures['delta_exposure'],
                'beta_adjusted_exposure': exposures['beta_adjusted_exposure'],
                'notional_value': parsed_option.notional_value,
            }
            
            processed_options.append(processed_opt)
            
        except Exception as e:
            logger.error(f"Error processing option {opt_data.get('description', 'unknown')}: {e}")
            continue
            
    return processed_options
```

### 3. Refactor `portfolio.py` to Use New Functions

Modify the option processing in `portfolio.py` to use the new functions:

```python
# In portfolio.py, replace the option processing code with:

# Prepare option data for processing
options_data = []
for opt_index, opt_row in option_df.iterrows():
    if pd.isna(opt_row["Description"]) or pd.isna(opt_row["Quantity"]) or pd.isna(opt_row["Last Price"]):
        continue
        
    try:
        opt_quantity = int(float(opt_row["Quantity"]))
        opt_last_price = clean_currency_value(opt_row["Last Price"])
        
        options_data.append({
            'description': opt_row["Description"],
            'symbol': opt_row["Symbol"],
            'quantity': opt_quantity,
            'price': opt_last_price,
        })
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing option data: {e}")
        continue

# Process all options at once
from .option_utils import process_options
processed_options = process_options(options_data, prices, betas)

# Group options by underlying
options_by_underlying = {}
for opt in processed_options:
    underlying = opt['ticker']
    options_by_underlying.setdefault(underlying, []).append(opt)

# Now use the grouped options in the portfolio processing
```

### 4. Unify Regular and Orphaned Option Processing

Modify the orphaned options processing to use the same approach:

```python
# Instead of duplicating the option processing logic, use the same function:
orphaned_options = process_options(orphaned_options_data, prices, betas)
```

## Implementation Plan

1. **Phase 1: Add New Functions to `option_utils.py`**
   - Implement `calculate_option_exposure()`
   - Implement `process_options()`
   - Add comprehensive tests for these functions

2. **Phase 2: Refactor Regular Option Processing in `portfolio.py`**
   - Modify the main option processing loop to use the new functions
   - Ensure all existing functionality is preserved
   - Add tests to verify the refactored code

3. **Phase 3: Refactor Orphaned Option Processing**
   - Modify the orphaned options processing to use the same functions
   - Remove duplicated code
   - Add tests to verify the refactored code

4. **Phase 4: Clean Up and Documentation**
   - Remove any unused code
   - Update docstrings and comments
   - Update documentation to reflect the new architecture

## Testing Strategy

1. **Unit Tests**
   - Add tests for the new functions in `option_utils.py`
   - Ensure they handle all edge cases correctly

2. **Integration Tests**
   - Test the interaction between `portfolio.py` and `option_utils.py`
   - Verify that the refactored code produces the same results as the original

3. **End-to-End Tests**
   - Test the entire portfolio processing flow with various option scenarios
   - Verify that the portfolio summary metrics are calculated correctly

## Risks and Mitigations

1. **Risk: Breaking Changes**
   - Mitigation: Implement changes incrementally and run tests after each step
   - Mitigation: Maintain backward compatibility where possible

2. **Risk: Performance Impact**
   - Mitigation: Profile the code before and after changes to ensure no significant performance degradation
   - Mitigation: Optimize the new functions if necessary

3. **Risk: Edge Cases**
   - Mitigation: Add comprehensive tests for edge cases
   - Mitigation: Add robust error handling to the new functions

## Conclusion

This refactoring will significantly improve the organization, maintainability, and reliability of the option-related code in the Folio application. By centralizing option calculations in `option_utils.py` and reducing duplication, we'll create a more consistent and robust implementation that's easier to test and extend in the future.
