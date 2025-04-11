# Error Handling and Code Bloat Refactoring

Date: 2025-04-11

## Overview

This document outlines a plan to refactor error handling patterns and reduce code bloat in the Folio application, with a particular focus on `src/folio/option_utils.py` and `src/folio/portfolio.py`. The goal is to improve code maintainability, readability, and performance by applying Python best practices for error handling and code organization.

## Current State Analysis

### Error Handling Issues

1. **Excessive Try/Except Blocks**: Both files contain numerous nested try/except blocks, often with similar error handling logic duplicated throughout the codebase.

2. **Inconsistent Error Handling**: Different parts of the application handle errors in different ways, with varying levels of detail and context.

3. **Overly Broad Exception Catching**: Many exception handlers catch `Exception`, which can mask bugs and make debugging difficult.

4. **Redundant Logging**: Similar error messages are logged in multiple places, leading to verbose logs with duplicate information.

5. **Missing Error Context**: Many error messages lack sufficient context about what operation was being performed when the error occurred.

### Code Bloat Issues

1. **Duplicated Validation Logic**: Similar validation code is repeated in multiple functions, particularly for option data validation.

2. **Long Functions**: Several functions exceed 100 lines, making them difficult to understand and maintain.

3. **Nested Conditionals**: Deep nesting of if/else statements makes the code flow difficult to follow.

4. **Redundant Comments**: Many comments simply restate what the code does rather than explaining why.

5. **Inconsistent Function Signatures**: Similar functions have different parameter orders and naming conventions.

## Python Error Handling Best Practices

1. **EAFP (Easier to Ask Forgiveness than Permission)**: Python encourages a coding style where you assume the operation will succeed and handle exceptions if it doesn't, rather than checking conditions beforehand.

2. **Specific Exception Types**: Catch specific exception types rather than broad `Exception` classes to avoid masking bugs.

3. **Context Managers**: Use context managers (`with` statements) for resource management and error handling.

4. **Custom Exceptions**: Define application-specific exception classes to provide better context and handling.

5. **Error Handling Utilities**: Create reusable utilities for common error handling patterns.

6. **Fail Fast**: Validate inputs early and raise exceptions with clear error messages.

7. **Centralized Error Handling**: Handle errors at the appropriate level of abstraction, not necessarily where they occur.

## Implementation Plan

### 1. Utilize Existing Error Handling Utilities

The codebase already has some good error handling utilities in `src/folio/error_utils.py` and custom exceptions in `src/folio/exceptions.py`. We should leverage these more consistently:

```python
# Instead of:
try:
    result = some_operation()
except Exception as e:
    logger.error(f"Error doing something: {e}")
    return default_value

# Use:
from .error_utils import handle_callback_error

@handle_callback_error(default_return=default_value, error_message="Error doing something")
def my_function():
    return some_operation()
```

### 2. Create Validation Utilities

Extract common validation logic into reusable functions:

```python
def validate_option_data(option_row):
    """Validate option data and return cleaned values or raise appropriate exceptions."""
    if pd.isna(option_row["Quantity"]) or option_row["Quantity"] == "--":
        raise DataError(f"Missing quantity for option {option_row.get('Description', 'unknown')}")
        
    if pd.isna(option_row["Last Price"]) or option_row["Last Price"] in ("--", ""):
        raise DataError(f"Missing price for option {option_row.get('Description', 'unknown')}")
        
    try:
        quantity = int(float(option_row["Quantity"]))
        price = clean_currency_value(option_row["Last Price"])
        return quantity, price
    except (ValueError, TypeError) as e:
        raise DataError(f"Invalid data format: {e}")
```

### 3. Refactor Option Processing in `portfolio.py`

Simplify the option processing code by extracting common patterns into helper functions:

```python
def extract_option_data(option_df, filter_func=None):
    """Extract and validate option data from a DataFrame."""
    options_data = []
    
    for idx, row in option_df.iterrows():
        if filter_func and not filter_func(row):
            continue
            
        try:
            option_desc = row.get("Description")
            if pd.isna(option_desc) or option_desc == "--":
                logger.warning(f"Option with index {idx}: Missing description. Skipping.")
                continue
                
            quantity, price = validate_option_data(row)
            
            options_data.append({
                'description': option_desc,
                'symbol': row["Symbol"],
                'quantity': quantity,
                'price': price,
                'current_value': row.get("Current Value"),
                'row_index': idx,
            })
        except DataError as e:
            logger.warning(f"{e}. Skipping option.")
            continue
            
    return options_data
```

### 4. Refactor Error Handling in `option_utils.py`

Improve error handling in option utilities by using more specific exceptions and consistent patterns:

```python
def get_implied_volatility(option, underlying_price, risk_free_rate=0.05):
    """Get implied volatility with better error handling."""
    if underlying_price <= 0:
        raise ValueError("Underlying price must be positive")
        
    if option.current_price <= 0:
        logger.debug(f"Market price missing or non-positive for {option.description}. Using estimation.")
        return estimate_volatility_with_skew(option, underlying_price)
        
    try:
        calculated_iv = calculate_implied_volatility(
            option=option,
            underlying_price=underlying_price,
            risk_free_rate=risk_free_rate,
        )
        
        if MIN_IV <= calculated_iv <= MAX_IV:
            return calculated_iv
            
        logger.warning(f"Calculated IV ({calculated_iv:.4f}) outside expected range. Using estimation.")
        return estimate_volatility_with_skew(option, underlying_price)
    except Exception as e:
        logger.error(f"Error calculating IV for {option.description}: {e}")
        return estimate_volatility_with_skew(option, underlying_price)
```

### 5. Break Down Large Functions

Split large functions into smaller, more focused functions:

```python
# Instead of one large process_portfolio_data function:
def process_portfolio_data(df):
    """Process portfolio data from a DataFrame."""
    if df is None or df.empty:
        return create_empty_results()
        
    # Validate and clean data
    df = validate_and_clean_data(df)
    
    # Process stock positions
    stock_positions = process_stock_positions(df)
    
    # Process option positions
    option_positions, processed_indices = process_option_positions(df, stock_positions)
    
    # Process orphaned options
    orphaned_options = process_orphaned_options(df, processed_indices)
    
    # Create portfolio groups
    groups = create_portfolio_groups(stock_positions, option_positions, orphaned_options)
    
    # Calculate portfolio summary
    summary = calculate_portfolio_summary(groups)
    
    # Identify cash-like positions
    cash_like = identify_cash_like_positions(df)
    
    return groups, summary, cash_like
```

### 6. Use Context Managers for Resource Management

Use context managers for operations that need cleanup:

```python
# Instead of:
try:
    file = open(filename, 'r')
    data = file.read()
    file.close()
except Exception as e:
    logger.error(f"Error reading file: {e}")
    
# Use:
try:
    with open(filename, 'r') as file:
        data = file.read()
except FileNotFoundError:
    logger.error(f"File not found: {filename}")
except PermissionError:
    logger.error(f"Permission denied: {filename}")
except Exception as e:
    logger.error(f"Unexpected error reading file: {e}")
```

### 7. Improve Function Documentation

Enhance docstrings to clearly document function behavior, parameters, return values, and exceptions:

```python
def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> float:
    """Calculate the delta of an option position.
    
    Args:
        option: The option position
        underlying_price: The price of the underlying asset
        risk_free_rate: The risk-free interest rate (default: 0.05)
        implied_volatility: Optional override for implied volatility
        
    Returns:
        The option delta, adjusted for position direction
        
    Raises:
        ValueError: If underlying_price is non-positive
        ValueError: If option.strike is non-positive
    """
```

## Implementation Phases

### Phase 1: Create Helper Functions

1. Create validation utilities in a new module `src/folio/validation.py`
2. Create option data extraction helpers in `src/folio/option_utils.py`
3. Add unit tests for new utilities

### Phase 2: Refactor `option_utils.py`

1. Improve error handling in `calculate_option_delta`
2. Refactor `get_implied_volatility`
3. Simplify `calculate_implied_volatility`
4. Update tests to verify error handling

### Phase 3: Refactor `portfolio.py`

1. Break down `process_portfolio_data` into smaller functions
2. Improve error handling in option processing
3. Simplify orphaned option processing
4. Update tests to verify refactored code

### Phase 4: Documentation and Cleanup

1. Improve docstrings throughout the codebase
2. Remove redundant comments
3. Ensure consistent naming conventions
4. Update documentation to reflect changes

## Testing Strategy

1. **Unit Tests**: Add tests for new utility functions
2. **Integration Tests**: Ensure refactored code works with existing components
3. **Error Handling Tests**: Add tests that verify error handling behavior
4. **Regression Tests**: Run existing tests to ensure no functionality is broken

## Risks and Mitigations

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Comprehensive test coverage before and after changes

2. **Risk**: Introducing new bugs in error handling
   - **Mitigation**: Add specific tests for error cases

3. **Risk**: Performance impact from additional function calls
   - **Mitigation**: Profile code before and after changes

4. **Risk**: Inconsistent adoption of new patterns
   - **Mitigation**: Create clear guidelines and examples

## Success Criteria

1. Reduced code size (at least 20% reduction in lines of code)
2. Improved test coverage for error cases
3. More consistent error handling patterns
4. Better documentation of error handling behavior
5. No regression in existing functionality

## Conclusion

This refactoring will significantly improve the maintainability and reliability of the Folio application by applying Python best practices for error handling and code organization. By reducing code bloat and improving error handling, we'll create a more robust codebase that's easier to extend and maintain in the future.
