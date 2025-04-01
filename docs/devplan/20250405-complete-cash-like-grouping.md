# DevPlan: Completing Cash-Like Instrument Grouping

**Date: 2025-04-05**

## Overview

This plan outlines the steps to complete the cash-like instrument grouping feature in the Folio portfolio dashboard. After reviewing the current implementation, I've identified that while some foundational components exist (like the `is_cash_or_short_term()` function), the feature is incomplete, particularly in the portfolio processing logic and UI integration.

## Current State Assessment

### What Works
- The `get_beta()` function calculates beta values based on historical price data
- The `is_cash_or_short_term()` function correctly identifies positions with abs(beta) < 0.1
- Tests exist for beta calculation and cash detection

### What's Missing
- The `is_cash_or_short_term()` function is implemented but not utilized in portfolio processing
- No dedicated grouping for cash-like instruments in the portfolio summary
- No UI component to display cash-like instrument aggregation
- No comprehensive tests for the end-to-end feature

## Implementation Plan

### Phase 1: Enhance Portfolio Processing

1. **Modify `process_portfolio_data()` in `src/folio/utils.py`**
   - Utilize the existing `is_cash_or_short_term()` function to identify cash-like instruments
   - Create a separate collection for cash-like positions during processing
   - Ensure cash positions with missing quantity are properly handled using their "Current Value"
   - Avoid special-casing specific symbols; rely on the beta-based identification

2. **Update `PortfolioSummary` in `src/folio/data_model.py`**
   - Add fields for cash-like instruments:
     ```python
     cash_like_positions: list[StockPosition]
     cash_like_value: float
     cash_like_count: int
     ```
   - Update the `__post_init__` method to initialize these fields
   - Add help text for the new fields

3. **Enhance `calculate_portfolio_summary()` in `src/folio/utils.py`**
   - Add logic to aggregate cash-like positions
   - Calculate total value, count, and percentage of portfolio
   - Ensure these metrics are included in the returned `PortfolioSummary`

### Phase 2: UI Integration

1. **Update Summary Cards in `src/folio/app.py`**
   - Add a new summary card for cash-like instruments
   - Include total value and percentage of portfolio
   - Ensure the card updates with the portfolio data

2. **Enhance Portfolio Table in `src/folio/components/portfolio_table.py`**
   - Add an option to filter/view cash-like instruments
   - Ensure cash-like positions are visually distinct (if displayed in the main table)
   - Consider adding a dedicated section for cash-like positions

3. **Update Position Details Modal**
   - Ensure cash-like positions display appropriate details
   - Add an indicator that the position is considered cash-like

### Phase 3: Testing

1. **Enhance Unit Tests**
   - Add tests for the updated portfolio processing logic
   - Verify correct identification and aggregation of cash-like positions
   - Test edge cases (e.g., positions with beta exactly at the threshold)

2. **Add Integration Tests**
   - Test the end-to-end flow from data processing to UI display
   - Verify that cash-like positions are correctly displayed in the UI
   - Test with various portfolio compositions

3. **Update Validation Script**
   - Enhance `check_beta.py` to validate the cash-like grouping
   - Add test cases for different types of instruments

## Implementation Details

### Portfolio Processing Logic

```python
# Pseudocode for the enhanced portfolio processing
def process_portfolio_data(df):
    # ... existing validation and setup ...
    
    # Initialize collections
    stock_positions = {}
    cash_like_positions = []
    
    # Process non-option rows
    for _, row in non_option_rows.iterrows():
        # ... existing cleaning and validation ...
        
        # Calculate beta
        beta = get_beta(symbol, description)
        
        # Check if position is cash-like
        is_cash_like = is_cash_or_short_term(symbol, beta=beta)
        
        if is_cash_like:
            # Handle cash-like position
            cash_like_positions.append({
                "ticker": symbol,
                "quantity": quantity,
                "market_value": value_to_use,
                "beta": beta,
                "description": description
            })
        else:
            # Handle regular stock position (existing logic)
            stock_positions[symbol] = {...}
    
    # ... existing group creation logic ...
    
    # Calculate summary including cash-like metrics
    summary = calculate_portfolio_summary(df, groups, cash_like_positions)
    
    return groups, summary
```

### Summary Calculation Enhancement

```python
# Pseudocode for the enhanced summary calculation
def calculate_portfolio_summary(df, groups, cash_like_positions):
    # ... existing summary calculation ...
    
    # Calculate cash-like metrics
    cash_like_value = sum(pos["market_value"] for pos in cash_like_positions)
    cash_like_count = len(cash_like_positions)
    
    # Create StockPosition objects for cash-like positions
    cash_like_stock_positions = [
        StockPosition(
            ticker=pos["ticker"],
            quantity=pos["quantity"],
            market_value=pos["market_value"],
            beta=pos["beta"],
            beta_adjusted_exposure=pos["market_value"] * pos["beta"],
            weight=1.0  # Default weight
        )
        for pos in cash_like_positions
    ]
    
    # Update summary with cash-like information
    summary = PortfolioSummary(
        # ... existing fields ...
        cash_like_positions=cash_like_stock_positions,
        cash_like_value=cash_like_value,
        cash_like_count=cash_like_count
    )
    
    return summary
```

### UI Component Update

```python
# Pseudocode for the UI summary card update
@app.callback(
    [
        # ... existing outputs ...
        Output("cash-like-value", "children"),
        Output("cash-like-percent", "children"),
    ],
    Input("portfolio-summary", "data"),
)
def update_summary_cards(summary_data):
    # ... existing logic ...
    
    # Add cash-like information
    cash_like_value = format_currency(summary_data["cash_like_value"])
    cash_like_percent = format_percentage(
        summary_data["cash_like_value"] / summary_data["total_value_abs"] * 100
        if summary_data["total_value_abs"] != 0
        else 0
    )
    
    return [
        # ... existing returns ...
        cash_like_value,
        cash_like_percent,
    ]
```

## Testing Strategy

1. **Unit Tests**
   - Test `process_portfolio_data()` with various portfolio compositions
   - Verify cash-like positions are correctly identified and aggregated
   - Test edge cases (e.g., beta exactly at threshold, missing data)

2. **Integration Tests**
   - Test the end-to-end flow from data processing to UI display
   - Verify cash-like summary card displays correct information
   - Test with different portfolio compositions

## Considerations

1. **Beta Threshold**
   - The current threshold of 0.1 for cash-like instruments is reasonable but could be made configurable
   - Consider adding a configuration option for this threshold

2. **Performance**
   - The enhanced processing adds minimal overhead
   - No significant performance impact is expected

3. **UI Design**
   - The cash-like summary should be visually distinct but consistent with the existing UI
   - Consider using a different color or icon to indicate cash-like status

## Success Criteria

1. Cash-like instruments are correctly identified based on their beta values
2. Cash-like positions are aggregated and displayed in the UI
3. All tests pass, including the new tests for cash-like grouping
4. The feature works with various portfolio compositions

## Timeline

- Phase 1 (Portfolio Processing): 1 day
- Phase 2 (UI Integration): 1 day
- Phase 3 (Testing): 1 day
- Total: 3 days
