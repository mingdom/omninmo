# Option Utilities Refactoring

Date: 2025-04-11

## Summary

This development log documents the refactoring of option-related utilities in the Folio application. The goal was to improve error handling, reduce code bloat, and make the code more maintainable by applying Python best practices.

## Changes

### 1. Refactored `parse_option_description` Function

Improved the error handling in the `parse_option_description` function:

- Consolidated multiple try/except blocks into a single block with more specific error messages
- Provided better context in error messages based on which component failed
- Reduced code duplication and improved readability

Before:
```python
# Validate and convert the month
try:
    month = parse_month(month_str)
except ValueError as e:
    logger.error(f"Invalid month in option description: {description}")
    raise ValueError(f"Invalid month in option description: {description}") from e

# Validate and convert the day
try:
    day = int(day_str)
    if not 1 <= day <= 31:  # Basic range check
        error_msg = f"Day out of range: {day}"
        logger.error(error_msg)
        raise ValueError(error_msg)
except ValueError as e:
    logger.error(f"Invalid day in option description: {description}")
    raise ValueError(f"Invalid day in option description: {description}") from e

# ... more similar blocks for year, strike price, option type, expiry date
```

After:
```python
try:
    # Parse month
    month = parse_month(month_str)
    
    # Parse day
    day = int(day_str)
    if not 1 <= day <= 31:  # Basic range check
        raise ValueError(f"Day out of range: {day}")
        
    # ... more parsing logic
    
except ValueError as e:
    # Provide a more specific error message based on which component failed
    error_context = str(e)
    if "month" in error_context.lower():
        error_msg = f"Invalid month '{month_str}' in option description: {description}"
    elif "day" in error_context.lower():
        error_msg = f"Invalid day '{day_str}' in option description: {description}"
    # ... more specific error messages
    else:
        error_msg = f"Invalid option description: {description}. Error: {e}"
        
    logger.error(error_msg)
    raise ValueError(error_msg) from e
```

### 2. Refactored `calculate_option_delta` Function

Improved the error handling in the `calculate_option_delta` function:

- Removed unused parameter `use_black_scholes` (kept for backward compatibility)
- Added explicit input validation at the beginning of the function
- Wrapped the calculation in a try/except block to provide better error messages
- Simplified the docstring to focus on the most important information

Before:
```python
def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    use_black_scholes: bool = True,  # Kept for backward compatibility
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,  # Allow optional IV override
) -> float:
    # ... docstring ...
    
    # Black-Scholes delta calculation
    logger.debug(f"Calculating Black-Scholes delta for {option.description}")

    # Determine the IV to use
    iv_to_use = implied_volatility  # Use provided IV if available
    if iv_to_use is None:
        logger.debug(f"No IV provided, estimating IV for {option.description}")
        iv_to_use = get_implied_volatility(option, underlying_price, risk_free_rate)
        logger.debug(f"Estimated IV: {iv_to_use:.4f}")
    elif not (0.001 <= iv_to_use <= 3.0):  # Basic sanity check on provided IV
        logger.warning(f"Unusual IV value ({iv_to_use}) for {option.description}")

    # Get the raw delta from Black-Scholes
    raw_delta = calculate_black_scholes_delta(
        option, underlying_price, risk_free_rate, iv_to_use
    )

    # Adjust for position direction (short positions have inverted delta)
    adjusted_delta = raw_delta if option.quantity >= 0 else -raw_delta

    logger.debug(f"Black-Scholes delta calculated: {adjusted_delta:.4f}")
    return adjusted_delta
```

After:
```python
def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,  # Allow optional IV override
) -> float:
    # ... simplified docstring ...
    
    # Validate inputs
    if underlying_price <= 0:
        error_msg = f"Underlying price must be positive: {underlying_price}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    # Log the calculation
    logger.debug(f"Calculating delta for {option.description}")

    try:
        # Determine the IV to use
        iv_to_use = implied_volatility  # Use provided IV if available
        if iv_to_use is None:
            logger.debug(f"No IV provided, estimating IV for {option.description}")
            iv_to_use = get_implied_volatility(option, underlying_price, risk_free_rate)
            logger.debug(f"Estimated IV: {iv_to_use:.4f}")
        elif not (0.001 <= iv_to_use <= 3.0):  # Basic sanity check on provided IV
            logger.warning(f"Unusual IV value ({iv_to_use}) for {option.description}")

        # Get the raw delta from Black-Scholes
        raw_delta = calculate_black_scholes_delta(
            option, underlying_price, risk_free_rate, iv_to_use
        )

        # Adjust for position direction (short positions have inverted delta)
        adjusted_delta = raw_delta if option.quantity >= 0 else -raw_delta

        logger.debug(f"Delta calculated: {adjusted_delta:.4f}")
        return adjusted_delta
        
    except Exception as e:
        error_msg = f"Error calculating delta for {option.description}: {e}"
        logger.error(error_msg)
        # Re-raise with a more specific message
        raise ValueError(error_msg) from e
```

## Benefits

1. **Improved Error Handling**: The refactored code provides more specific error messages and better error handling.

2. **Reduced Code Bloat**: Consolidated multiple try/except blocks into a single block with more specific error messages.

3. **Better Maintainability**: The code is now more readable and easier to maintain.

4. **Simplified Interface**: Removed unused parameters and simplified the function signatures.

## Next Steps

In the next phase, we'll refactor the portfolio processing code in `src/folio/portfolio.py` to use our new validation utilities, which will further reduce code bloat and improve error handling.

## Related Documents

- [Error Handling and Code Bloat Refactoring Plan](../devplan/2025-04-11-error-handling-and-code-bloat-refactoring.md)
- [Validation Utilities Implementation](./2025-04-11-validation-utilities-implementation.md)
