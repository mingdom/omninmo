# Option Notional Value Calculation Refactoring

## Problem Statement

We recently updated the notional value calculation for options to use the underlying price instead of the strike price, which is more accurate for exposure calculations. However, this change has revealed a significant code smell in our codebase:

1. **Multiple Calculation Paths**: We have multiple places where notional value is calculated, leading to inconsistencies.
2. **Duplicate Logic**: The same calculation is repeated in different parts of the codebase.
3. **Inconsistent Results**: The summary cards and position details show different values for the same metrics.
4. **Test Failures**: The e2e test `test_summary_cards_match_position_details` is failing because it compares values from different calculation paths.

This violates the DRY (Don't Repeat Yourself) principle and makes the code harder to maintain. When we updated the notional value calculation in one place, we missed updating it in other places, leading to inconsistencies.

## Current Architecture

The current architecture has several calculation paths:

1. **OptionContract.notional_value property**:
   - Now uses underlying price if available, falls back to strike price with a warning
   - Added a `signed_notional_value` property that still uses strike price for backward compatibility

2. **calculate_option_exposure function**:
   - Now calculates notional value directly using underlying price
   - Used for calculating delta exposure and beta-adjusted exposure

3. **process_options function**:
   - Now calculates notional value directly using underlying price
   - Used for processing options from CSV data

4. **PortfolioGroup creation**:
   - Uses `opt.delta_exposure` values that come from different sources
   - Some may use the old calculation (strike price), others the new one (underlying price)

5. **recalculate_portfolio_with_prices function**:
   - Uses `OptionPosition.recalculate_with_price` which uses the new calculation
   - But the `PortfolioGroup` creation still has inconsistencies

## Root Cause

The root cause is that we don't have a single source of truth for notional value calculation. Instead, we have multiple places where this calculation is performed, leading to inconsistencies when we update one but not all of them.

## Proposed Solution

We need to refactor the code to ensure that all notional value calculations use the same method and that there's a single source of truth. Here's the plan:

### 1. Create a Single Source of Truth

1. **Update OptionContract class**:
   ```python
   @property
   def notional_value(self) -> float:
       """Calculate notional value using underlying price.
       
       This is the canonical implementation that should be used throughout the codebase.
       It requires the underlying_price to be set.
       """
       if not hasattr(self, 'underlying_price') or self.underlying_price is None:
           raise ValueError(
               f"Cannot calculate notional value for {self.underlying} {self.option_type} "
               f"{self.strike} without underlying_price. Set underlying_price first."
           )
       return 100 * abs(self.quantity) * self.underlying_price
   
   @property
   def legacy_notional_value(self) -> float:
       """Calculate notional value using strike price (legacy method).
       
       This is kept for backward compatibility but should not be used for new code.
       """
       return 100 * abs(self.quantity) * self.strike
   
   @property
   def signed_notional_value(self) -> float:
       """Calculate signed notional value using underlying price.
       
       This returns a signed value (positive for long, negative for short).
       """
       if not hasattr(self, 'underlying_price') or self.underlying_price is None:
           raise ValueError(
               f"Cannot calculate signed notional value for {self.underlying} {self.option_type} "
               f"{self.strike} without underlying_price. Set underlying_price first."
           )
       return 100 * self.quantity * self.underlying_price
   
   @property
   def legacy_signed_notional_value(self) -> float:
       """Calculate signed notional value using strike price (legacy method).
       
       This is kept for backward compatibility but should not be used for new code.
       """
       return 100 * self.quantity * self.strike
   ```

2. **Update OptionPosition class**:
   ```python
   @property
   def notional_value(self) -> float:
       """Return the notional value of the option position.
       
       This is a pass-through to the stored notional_value attribute,
       which should be calculated using the underlying price.
       """
       return self._notional_value
   
   @notional_value.setter
   def notional_value(self, value: float):
       """Set the notional value of the option position."""
       self._notional_value = value
   ```

### 2. Ensure Consistent Calculation in All Places

1. **Update calculate_option_exposure function**:
   ```python
   def calculate_option_exposure(
       option: OptionContract, 
       underlying_price: float, 
       beta: float = 1.0,
       risk_free_rate: float = 0.05,
       implied_volatility: float | None = None,
   ) -> dict[str, float]:
       """Calculate exposure metrics for an option position."""
       # Set the underlying price on the option contract
       option.underlying_price = underlying_price
       
       # Calculate delta using QuantLib
       delta = calculate_option_delta(
           option,
           underlying_price,
           risk_free_rate=risk_free_rate,
           implied_volatility=implied_volatility,
       )
       
       # Use the option's notional_value property
       notional_value = option.notional_value
       
       # Calculate delta exposure
       delta_exposure = delta * notional_value * (1 if option.quantity > 0 else -1)
       
       # Calculate beta-adjusted exposure
       beta_adjusted_exposure = delta_exposure * beta
       
       return {
           "delta": delta,
           "notional_value": notional_value,
           "delta_exposure": delta_exposure,
           "beta_adjusted_exposure": beta_adjusted_exposure,
       }
   ```

2. **Update process_options function**:
   ```python
   def process_options(
       options_data: list[dict],
       prices: dict[str, float],
       betas: dict[str, float] | None = None,
   ) -> list[dict]:
       """Process a list of option data dictionaries."""
       # ... existing code ...
       
       for opt_data in options_data:
           # ... existing code ...
           
           # Set the underlying price on the parsed option
           parsed_option.underlying_price = underlying_price
           
           # Calculate exposures
           exposures = calculate_option_exposure(parsed_option, underlying_price, beta)
           
           # Use the notional_value from exposures
           processed_opt = {
               # ... existing fields ...
               "notional_value": exposures["notional_value"],
               # ... other fields ...
           }
           
           # ... rest of the function ...
   ```

3. **Update create_portfolio_group function**:
   ```python
   def create_portfolio_group(
       stock_data: dict[str, str | int | float] | None = None,
       option_data: list[dict[str, str | int | float]] | None = None,
   ) -> PortfolioGroup | None:
       """Create a PortfolioGroup from stock and option data."""
       # ... existing code ...
       
       # Calculate group metrics
       # For stock positions, market_exposure is quantity * price
       # For option positions, delta_exposure is delta * notional_value * sign(quantity)
       # where notional_value is 100 * abs(quantity) * underlying_price
       net_exposure = (stock_position.market_exposure if stock_position else 0) + sum(
           opt.delta_exposure for opt in option_positions
       )
       
       # ... rest of the function ...
   ```

4. **Update recalculate_portfolio_with_prices function**:
   ```python
   def recalculate_portfolio_with_prices(
       groups: list[PortfolioGroup],
       price_adjustments: dict[str, float],
       cash_like_positions: list[dict] | None = None,
       pending_activity_value: float = 0.0,
   ) -> tuple[list[PortfolioGroup], PortfolioSummary]:
       """Recalculate portfolio groups and summary with adjusted prices."""
       # ... existing code ...
       
       for group in groups:
           # ... existing code ...
           
           # Calculate group metrics
           # For stock positions, market_exposure is quantity * price
           # For option positions, delta_exposure is delta * notional_value * sign(quantity)
           # where notional_value is 100 * abs(quantity) * underlying_price
           net_exposure = (
               recalculated_stock.market_exposure if recalculated_stock else 0
           ) + sum(opt.delta_exposure for opt in recalculated_options)
           
           # ... rest of the function ...
   ```

### 3. Update Tests

1. **Revert the tolerance changes in test_summary_cards_match_position_details**:
   ```python
   # Test that summary card values match position details
   assert abs(summary_net_exposure - total_ui_market_value) < 0.01, (
       f"Net Exposure in summary cards ({format_currency(summary_net_exposure)}) does not match the total market value shown in the UI ({format_currency(total_ui_market_value)})"
   )
   ```

2. **Add tests for the new notional value calculation**:
   ```python
   def test_option_notional_value_calculation():
       """Test that option notional value is calculated correctly using underlying price."""
       # Create an option contract
       option = OptionContract(
           underlying="AAPL",
           expiry=datetime.datetime(2023, 1, 1),
           strike=150.0,
           option_type="CALL",
           quantity=10,
           current_price=15.0,
           description="AAPL CALL $150 2023-01-01",
       )
       
       # Set the underlying price
       option.underlying_price = 160.0
       
       # Calculate notional value
       notional_value = option.notional_value
       
       # Verify that notional value is calculated using underlying price
       assert notional_value == 100 * 10 * 160.0
       
       # Verify that legacy notional value is calculated using strike price
       assert option.legacy_notional_value == 100 * 10 * 150.0
   ```

### 4. Add Documentation

1. **Update docstrings** to clearly explain the notional value calculation and its importance.
2. **Add comments** in key places to explain the calculation method.
3. **Create a devlog** documenting the refactoring and its rationale.

## Implementation Plan

1. **Phase 1: Update OptionContract class**
   - Add the new properties and methods
   - Update docstrings and add comments
   - Add tests for the new properties

2. **Phase 2: Update calculation functions**
   - Update calculate_option_exposure
   - Update process_options
   - Update create_portfolio_group
   - Update recalculate_portfolio_with_prices
   - Add tests for each function

3. **Phase 3: Update tests**
   - Revert tolerance changes in e2e tests
   - Add new tests for notional value calculation
   - Run all tests to ensure they pass

4. **Phase 4: Documentation**
   - Update docstrings throughout the codebase
   - Add comments in key places
   - Create a devlog documenting the refactoring

## Benefits

1. **Single Source of Truth**: All notional value calculations will use the same method.
2. **Consistency**: The summary cards and position details will show the same values.
3. **Maintainability**: Future changes to the calculation will only need to be made in one place.
4. **Reliability**: Tests will pass with strict tolerances, ensuring accuracy.
5. **Clarity**: The code will be easier to understand and reason about.

## Risks and Mitigations

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Comprehensive test coverage, including e2e tests

2. **Risk**: Performance impact from additional property access
   - **Mitigation**: Profile the code before and after changes to ensure no significant impact

3. **Risk**: Backward compatibility issues
   - **Mitigation**: Keep legacy methods for backward compatibility, but mark them as deprecated

## Conclusion

This refactoring will address the code smell of duplicate calculation paths and ensure that all notional value calculations use the same method. It will make the code more maintainable, reliable, and easier to understand.

By following the DRY principle and creating a single source of truth, we'll avoid similar issues in the future and make the codebase more robust.
