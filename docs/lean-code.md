# Writing Lean Code

This document outlines principles and patterns for writing lean, maintainable code. Lean code is characterized by its clarity, simplicity, and focus on the "happy path" with proper error handling.

## Core Principles

1. **Validate Early, Return/Throw Fast**
2. **Keep the Happy Path Clean**
3. **Minimize Nesting and Branching**
4. **Modular Functions with Single Responsibility**
5. **Clear Error Handling**

## Patterns and Examples

### ❌ Bad: Deeply Nested Conditionals

```python
def process_data(data):
    if data is not None:
        if "key" in data:
            if data["key"] > 0:
                # Process the data
                result = data["key"] * 2
                if result > 10:
                    return "Large result"
                else:
                    return "Small result"
            else:
                return "Invalid value"
        else:
            return "Missing key"
    else:
        return "No data"
```

### ✅ Good: Early Returns

```python
def process_data(data):
    # Validate inputs first
    if data is None:
        return "No data"

    if "key" not in data:
        return "Missing key"

    if data["key"] <= 0:
        return "Invalid value"

    # Happy path (main logic) is clean and obvious
    result = data["key"] * 2

    # Simple condition at the end
    return "Large result" if result > 10 else "Small result"
```

### ❌ Bad: Excessive Branching

```python
def determine_boundedness(pnl_data, max_profit_idx, max_loss_idx, price_points):
    # Use asymptotic analysis if we have position data
    if "positions" in pnl_data:
        # Log SPY positions for debugging
        is_spy = any(p.get("ticker", "") == "SPY" for p in pnl_data["positions"])
        if is_spy:
            logger.info(f"SPY position detected with {len(pnl_data['positions'])} positions")

        # Get asymptotic behavior
        results = analyze_asymptotic_behavior(pnl_data["positions"])

        # Combine high/low results
        unbounded_profit = results["unbounded_profit_high"] or results["unbounded_profit_low"]
        unbounded_loss = results["unbounded_loss_high"] or results["unbounded_loss_low"]

        if is_spy:
            logger.info(f"SPY asymptotic results: {results}")
            logger.info(f"Final SPY determination: profit={unbounded_profit}, loss={unbounded_loss}")

        return unbounded_profit, unbounded_loss
    else:
        # Fallback to edge detection if no position data
        # Profit is unbounded if max profit is at edge of price range
        unbounded_profit = max_profit_idx == 0 or max_profit_idx == len(price_points) - 1
        # Loss is unbounded if max loss is at edge of price range
        unbounded_loss = max_loss_idx == 0 or max_loss_idx == len(price_points) - 1
        return unbounded_profit, unbounded_loss
```

### ✅ Good: Validate First, Clean Main Path

```python
def determine_boundedness(pnl_data):
    # Validate input - positions data must be available
    if "positions" not in pnl_data:
        logger.warning("No position data available for asymptotic analysis")
        raise ValueError("Position data is required for boundedness determination")

    # Log SPY positions for debugging
    is_spy = any(p.get("ticker", "") == "SPY" for p in pnl_data["positions"])
    if is_spy:
        logger.info(f"SPY position detected with {len(pnl_data['positions'])} positions")

    # Get asymptotic behavior
    results = analyze_asymptotic_behavior(pnl_data["positions"])

    # Combine high/low results
    unbounded_profit = results["unbounded_profit_high"] or results["unbounded_profit_low"]
    unbounded_loss = results["unbounded_loss_high"] or results["unbounded_loss_low"]

    if is_spy:
        logger.info(f"SPY asymptotic results: {results}")
        logger.info(f"Final SPY determination: profit={unbounded_profit}, loss={unbounded_loss}")

    return unbounded_profit, unbounded_loss
```

### ❌ Bad: Mixing Validation and Logic

```python
def calculate_exposure(positions):
    total_exposure = 0

    for position in positions:
        if position is not None:
            if "quantity" in position and "price" in position:
                if position["quantity"] != 0 and position["price"] > 0:
                    exposure = position["quantity"] * position["price"]
                    total_exposure += exposure
                else:
                    print("Invalid quantity or price")
            else:
                print("Missing quantity or price")
        else:
            print("None position found")

    return total_exposure
```

### ✅ Good: Separate Validation from Logic

```python
def calculate_exposure(positions):
    # Validate input
    if not positions:
        raise ValueError("Positions list cannot be empty")

    # Validate each position
    for position in positions:
        if position is None:
            raise ValueError("None position found")

        if "quantity" not in position or "price" not in position:
            raise ValueError(f"Missing quantity or price in position: {position}")

        if position["quantity"] == 0 or position["price"] <= 0:
            raise ValueError(f"Invalid quantity or price in position: {position}")

    # Clean main logic
    total_exposure = sum(p["quantity"] * p["price"] for p in positions)
    return total_exposure
```

## Key Takeaways

1. **Check for errors first**: Validate inputs at the beginning of your function and return/throw immediately.

2. **Avoid nested conditionals**: Each level of nesting makes code harder to read and maintain.

3. **Keep the happy path linear**: The main logic of your function should flow from top to bottom without jumping around through conditionals.

4. **Use exceptions appropriately**: Throw exceptions for truly exceptional conditions rather than using them for control flow.

5. **Modularize**: Break complex functions into smaller, focused functions with clear responsibilities.

6. **Be explicit about requirements**: Document what your function expects and what it will do if those expectations aren't met.

7. **Avoid silent failures**: Don't hide errors or silently fall back to different behavior - be explicit about failures.

## Benefits of Lean Code

- **Readability**: Code is easier to understand at a glance
- **Maintainability**: Simpler structure makes changes easier and safer
- **Testability**: Clear paths make testing more straightforward
- **Reliability**: Proper error handling prevents unexpected behavior
- **Performance**: Less branching can lead to better performance
