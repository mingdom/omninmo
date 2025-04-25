# Fix Exposure Calculation Inconsistency

## Problem Statement

We've identified an inconsistency in how net exposure is calculated in different parts of the codebase. This inconsistency is causing the `test_exposures.py` test to fail with the following error:

```
Net Exposure in summary cards ($1,053,776.80) does not match the total market value shown in the UI ($1,010,007.08)
```

The difference of $43,769.72 is the sum of discrepancies between the stored `net_exposure` values in each `PortfolioGroup` and what would be calculated as `stock_position.market_exposure + sum(opt.delta_exposure for opt in option_positions)`.

This issue was introduced when we changed the notional value calculation for options from using strike price to underlying price. Some parts of the code are using the new calculation method, while others are still using the old method.

## Root Cause Analysis

Through detailed debugging, we've identified that for each portfolio group, there's a discrepancy between:

1. The value stored in `PortfolioGroup.net_exposure`
2. What we would calculate as `stock_position.market_exposure + sum(opt.delta_exposure for opt in option_positions)`

For example, for AMZN:
```
AMZN: $380,594.64
  Stock Exposure: $283,485.01
  Option Delta Exposure: $105,794.79
  Calculated Net Exposure: $389,279.80
  DISCREPANCY: $-8,685.16
```

The sum of these discrepancies across all groups equals the $43,769.72 difference that the test is catching.

The issue is that when we load portfolio data from a CSV file, we're not recalculating the `net_exposure` values for each group using the new notional value calculation method. Instead, we're using the values that were calculated using the old method.

## Proposed Solution

Following lean code principles, we should:

1. **Simplify the calculation path**: Ensure there's only one canonical way to calculate net exposure
2. **Eliminate redundancy**: Remove duplicate calculations and ensure all code paths use the same method
3. **Make the code more maintainable**: Add clear documentation about how these calculations should be performed

### Implementation Plan

1. **Create a canonical function for calculating net exposure**:

   Create a single function that calculates net exposure for a portfolio group. This function should be used everywhere in the codebase where net exposure is calculated.

   ```python
   def calculate_net_exposure(
       stock_position: StockPosition | None,
       option_positions: list[OptionPosition]
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

2. **Update `create_portfolio_group` to use the canonical function**:

   ```python
   def create_portfolio_group(
       stock_data: dict[str, str | int | float] | None = None,
       option_data: list[dict[str, str | int | float]] | None = None,
   ) -> PortfolioGroup | None:
       # ... existing code ...
       
       # Calculate net exposure using the canonical function
       net_exposure = calculate_net_exposure(stock_position, option_positions)
       
       # ... rest of the function ...
   ```

3. **Update `process_portfolio_data` to recalculate net exposure**:

   Ensure that when we load portfolio data from a CSV file, we recalculate the net exposure for each group using the canonical function.

   ```python
   def process_portfolio_data(portfolio_df: pd.DataFrame) -> tuple[list[PortfolioGroup], PortfolioSummary, dict]:
       # ... existing code ...
       
       # Recalculate net exposure for each group
       for group in groups:
           group.net_exposure = calculate_net_exposure(group.stock_position, group.option_positions)
       
       # ... rest of the function ...
   ```

4. **Update `update_portfolio_prices` to recalculate net exposure**:

   Ensure that when we update prices, we also recalculate the net exposure for each group.

   ```python
   def update_portfolio_prices(groups: list[PortfolioGroup]) -> list[PortfolioGroup]:
       # ... existing code ...
       
       # Recalculate net exposure for each group
       for group in groups:
           group.net_exposure = calculate_net_exposure(group.stock_position, group.option_positions)
       
       # ... rest of the function ...
   ```

5. **Add a method to `PortfolioGroup` to recalculate net exposure**:

   ```python
   @dataclass
   class PortfolioGroup:
       # ... existing code ...
       
       def recalculate_net_exposure(self) -> None:
           """Recalculate net exposure using the canonical function."""
           self.net_exposure = calculate_net_exposure(self.stock_position, self.option_positions)
   ```

## Benefits

1. **Simplicity**: One canonical way to calculate net exposure
2. **Maintainability**: Clear documentation about how these calculations should be performed
3. **Reliability**: Consistent calculations across the codebase
4. **Testability**: Easier to test since there's only one function to test

## Risks and Mitigations

1. **Risk**: The change might affect other parts of the codebase that rely on the current calculation method.
   **Mitigation**: Run all tests to ensure nothing else breaks.

2. **Risk**: The change might affect the UI and how values are displayed.
   **Mitigation**: Manually verify that the UI displays the correct values after the change.

## Testing Plan

1. Run the failing test (`test_exposures.py`) to verify that it passes after the change.
2. Run all other tests to ensure nothing else breaks.
3. Manually verify that the UI displays the correct values after the change.

## Implementation Notes

- The canonical function should be placed in a module that's accessible to all parts of the codebase that need to calculate net exposure.
- Consider adding a unit test specifically for the canonical function to ensure it calculates net exposure correctly.
- Add clear documentation about how net exposure should be calculated and why it's important to use the canonical function.
