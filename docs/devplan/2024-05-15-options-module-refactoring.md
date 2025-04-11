# Options Module Refactoring

## Overview

This document outlines the plan to refactor the options-related functionality from `quantlib_utils.py` into a new dedicated `options.py` module. This refactoring aims to improve separation of concerns and make it easier to potentially swap out the underlying implementation in the future.

## Current Structure

Currently, all options-related functionality is contained in `src/folio/quantlib_utils.py`, which includes:

1. `OptionContract` dataclass - Represents a single option contract with its properties
2. Black-Scholes calculation functions:
   - `calculate_black_scholes_delta` - Calculates option delta using QuantLib
   - `calculate_bs_price` - Calculates option price using QuantLib
   - `calculate_implied_volatility` - Calculates implied volatility using QuantLib
3. Helper functions:
   - `parse_option_description` - Parses option description strings
   - `calculate_option_delta` - Wrapper for delta calculation with position adjustment
   - `calculate_option_exposure` - Calculates exposure metrics for an option position
   - `estimate_volatility_with_skew` - Estimates volatility with a simple skew model
   - `get_implied_volatility` - Gets implied volatility from market price or estimation
   - `process_options` - Processes a list of option data dictionaries

## Planned Refactoring

### 1. Create New Module

Create a new file `src/folio/options.py` that will contain all the options-related functionality.

### 2. Functions to Move

The following components will be moved from `quantlib_utils.py` to `options.py`:

- `OptionContract` dataclass
- `calculate_black_scholes_delta`
- `calculate_bs_price`
- `calculate_implied_volatility`
- `parse_option_description`
- `calculate_option_delta`
- `calculate_option_exposure`
- `estimate_volatility_with_skew`
- `get_implied_volatility`
- `process_options`

### 3. Test Updates

Update the test files to import from the new module:

- `tests/test_quantlib_utils.py` will be renamed to `tests/test_options.py`
- `tests/test_option_exposure.py` will be updated to import from the new module

### 4. Implementation Approach

1. Create the new `options.py` file with all the functions from `quantlib_utils.py`
2. Update imports in the test files
3. Create a new `test_options.py` file
4. Remove `quantlib_utils.py` completely
5. Run tests to ensure everything works correctly

### 5. Benefits

- Better separation of concerns
- Easier to swap out the underlying implementation in the future
- More maintainable codebase
- Clearer module structure

## Future Considerations

In the future, we might want to consider:

1. Creating an abstract interface for option calculations to make it even easier to swap implementations
2. Adding more sophisticated volatility models
3. Supporting additional option types beyond vanilla calls and puts

## Timeline

This refactoring should be completed in a single PR to avoid any integration issues.
