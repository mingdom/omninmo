# Proposal: Canonical Functions Pattern for Consistent Calculations

## Background

During a recent bug fix, we discovered inconsistencies in how net exposure and beta-adjusted exposure were calculated across different parts of the codebase. This led to discrepancies between summary cards and position details, making it difficult for users to trust the data presented. The root cause was duplicated calculation logic spread across multiple files, with subtle differences in implementation.

## Problem Statement

Our codebase currently suffers from several issues related to calculation consistency:

1. **Duplicated Logic**: The same calculations are implemented in multiple places with slight variations
2. **Implicit Dependencies**: Functions rely on specific object properties without clear documentation
3. **Difficult Traceability**: It's hard to trace where a specific value is calculated
4. **Brittle Maintenance**: Changes to calculation logic must be made in multiple places
5. **Inconsistent Results**: Different parts of the UI show different values for the same metric

These issues make the codebase harder to maintain, more prone to bugs, and less resilient to changes.

## Proposed Solution: Canonical Functions Pattern

I propose implementing a "Canonical Functions Pattern" across our codebase to ensure consistent calculations and improve maintainability. This pattern involves:

1. **Single Source of Truth**: Define one canonical implementation for each important calculation
2. **Explicit Documentation**: Clearly document the purpose, inputs, and outputs of each canonical function
3. **Centralized Location**: Place all canonical functions in logical modules based on domain
4. **Consistent Naming**: Use a naming convention that makes canonical functions easily identifiable
5. **Comprehensive Testing**: Thoroughly test canonical functions to ensure correctness

### Implementation Details

#### 1. Identify Core Calculations

First, we should identify all core calculations in our application that are used in multiple places:

- Net exposure calculation
- Beta-adjusted exposure calculation
- Portfolio value calculation
- Cash percentage calculation
- Short percentage calculation
- Option delta exposure calculation
- Notional value calculation
- etc.

#### 2. Create Canonical Functions

For each core calculation, create a canonical function in an appropriate module:

```python
# Example in portfolio_value.py
def calculate_net_exposure(
    stock_position: StockPosition | None,
    option_positions: list[OptionPosition],
) -> float:
    """Calculate net exposure for a portfolio group.
    
    This is the canonical implementation that should be used everywhere in the codebase.
    
    Args:
        stock_position: The stock position (if any)
        option_positions: List of option positions
        
    Returns:
        Net exposure (stock market exposure + sum of option delta exposures)
    """
    stock_exposure = stock_position.market_exposure if stock_position else 0.0
    option_delta_exposure = sum(opt.delta_exposure for opt in option_positions)
    
    return stock_exposure + option_delta_exposure
```

#### 3. Replace Duplicated Logic

Replace all instances of duplicated calculation logic with calls to the canonical functions:

```python
# Before
net_exposure = (stock_position.market_exposure if stock_position else 0) + sum(
    opt.delta_exposure for opt in option_positions
)

# After
from .portfolio_value import calculate_net_exposure
net_exposure = calculate_net_exposure(stock_position, option_positions)
```

#### 4. Add Recalculation Methods

Add methods to recalculate derived values using canonical functions:

```python
def recalculate_net_exposure(self) -> None:
    """Recalculate net exposure using the canonical function."""
    from .portfolio_value import calculate_net_exposure
    self.net_exposure = calculate_net_exposure(self.stock_position, self.option_positions)
```

#### 5. Update Tests

Update tests to verify that all parts of the application use the canonical functions and produce consistent results.

## Benefits

Implementing the Canonical Functions Pattern will provide several benefits:

1. **Consistency**: All parts of the application will use the same calculation logic
2. **Maintainability**: Changes to calculation logic only need to be made in one place
3. **Readability**: Code is more self-documenting with clear function names
4. **Testability**: Easier to test calculation logic in isolation
5. **Reliability**: Reduced chance of bugs due to inconsistent implementations

## Implementation Plan

1. **Phase 1**: Identify and document all core calculations in the codebase
2. **Phase 2**: Create canonical functions for the most critical calculations (exposure, portfolio value)
3. **Phase 3**: Replace duplicated logic with calls to canonical functions
4. **Phase 4**: Add comprehensive tests for canonical functions
5. **Phase 5**: Create a code review checklist to ensure new code follows the pattern

## Additional Recommendations

Beyond the Canonical Functions Pattern, I recommend several other improvements to enhance code quality:

### 1. Explicit Dependencies

Make dependencies explicit by passing required values as function parameters rather than relying on object properties:

```python
# Before (implicit dependency on underlying_price)
option.notional_value  # Requires underlying_price to be set

# After (explicit dependency)
calculate_notional_value(option, underlying_price)
```

### 2. Consistent Error Handling

Implement consistent error handling for calculation functions:

```python
def calculate_beta_adjusted_exposure(stock_position, option_positions):
    try:
        # Calculation logic
        return result
    except ZeroDivisionError:
        logger.warning("Division by zero in beta-adjusted exposure calculation")
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating beta-adjusted exposure: {e}")
        raise ValueError(f"Failed to calculate beta-adjusted exposure: {e}") from e
```

### 3. Validation Functions

Create validation functions to check inputs before performing calculations:

```python
def validate_option_data(option):
    """Validate option data before calculation."""
    if option.strike <= 0:
        raise ValueError(f"Invalid strike price: {option.strike}")
    if not hasattr(option, "underlying_price") or option.underlying_price is None:
        raise ValueError("Underlying price must be set")
```

### 4. Logging and Debugging

Add consistent logging to canonical functions to aid debugging:

```python
def calculate_net_exposure(stock_position, option_positions):
    stock_exposure = stock_position.market_exposure if stock_position else 0.0
    option_delta_exposure = sum(opt.delta_exposure for opt in option_positions)
    
    logger.debug("Calculating net exposure:")
    logger.debug(f"  Stock exposure: {stock_exposure}")
    logger.debug(f"  Option delta exposure: {option_delta_exposure}")
    logger.debug(f"  Net exposure: {stock_exposure + option_delta_exposure}")
    
    return stock_exposure + option_delta_exposure
```

## Conclusion

The Canonical Functions Pattern will help us build a more maintainable, consistent, and reliable codebase. By centralizing our calculation logic and making dependencies explicit, we can reduce bugs, improve code quality, and make future development more efficient.

This approach aligns with our lean code principles by:
- Reducing duplication (SIMPLICITY)
- Making dependencies explicit (PRECISION)
- Providing consistent error handling (RELIABILITY)
- Creating a more maintainable codebase (USABILITY)

I recommend we start implementing this pattern immediately, beginning with the most critical calculations that affect user-facing metrics.
