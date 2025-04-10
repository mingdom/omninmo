# Calculation Issues in Folio

This document outlines issues related to the handling of negative numbers, short positions, and areas of code duplication or high complexity in the Folio project.

## Negative Numbers and Short Positions

### Inconsistencies in Handling Short Positions

1. **Stock Positions vs. Options**
   - **Stock Positions**: Short stock positions are stored with positive quantities in `StockPosition` objects, but their market exposure is calculated as negative (quantity * price). This is inconsistent with how options are handled.
   - **Options**: Option positions correctly store negative quantities for short positions in `OptionPosition` objects, and the delta exposure is calculated accordingly. The `OptionPosition` class even has an explicit `is_short` property that checks if `quantity < 0`.

2. **Exposure Calculations**
   - In `portfolio.py` (lines 998-1002), short stock positions are handled by checking if `stock.quantity >= 0`, and if not, adding the absolute value to short exposure. This approach is inconsistent with the data model and creates complexity.
   - For options (lines 1006-1022), the code checks if `opt.delta_exposure >= 0` to determine if it's a long or short exposure, which is more consistent with the actual exposure direction.
   - The `calculate_beta_adjusted_net_exposure` function (line 1382) subtracts short beta-adjusted exposure from long beta-adjusted exposure, but this assumes short exposure is stored as a positive value, which is inconsistent with the natural representation of negative values.

3. **Absolute Values in Calculations**
   - Several places in the code use `abs()` when calculating totals, which can hide the true directional exposure:
     - In `calculate_portfolio_summary` (line 1018), short options delta exposure uses `abs(opt.delta_exposure)`
     - In `transform_for_treemap` (line 164), absolute exposure is used for sizing: `values.append(abs(exposure))`
     - In `calculate_portfolio_summary` (line 1001), short stock beta-adjusted exposure uses `abs(stock.beta_adjusted_exposure)`

### Specific Issues

1. **Stock Position Quantity Representation**
   - In `src/folio/portfolio.py` (line 260), stock quantities are parsed as integers, but there's no explicit handling to make short positions negative:
     ```python
     quantity = int(float(row["Quantity"]))
     ```
   - In `src/folio/data_model.py`, the `StockPosition` class stores quantity as an integer without explicitly documenting that negative values represent short positions, unlike the `OptionPosition` class which has an `is_short` property.
   - The documentation in `docs/datamodel.md` mentions that quantity can be negative for short positions, but this isn't consistently implemented in the code.

2. **Market Exposure Calculation**
   - In `update_portfolio_prices` (lines 1242-1247), market exposure is calculated as `price * quantity`:
     ```python
     group.stock_position.market_exposure = (
         group.stock_position.price * group.stock_position.quantity
     )
     ```
     This would be negative for short positions if quantity were negative, but the code doesn't explicitly handle this.
   - In `portfolio.py` (line 1090), net market exposure is calculated by subtracting short exposure from long exposure:
     ```python
     net_market_exposure = (
         long_exposure.total_exposure - short_exposure.total_exposure
     )
     ```
     This assumes short exposure is stored as a positive value, which is inconsistent with the natural representation of negative values.

3. **Inconsistent Handling in UI**
   - In `components/position_details.py`, short positions are not visually distinguished from long positions in the UI.
   - In `components/portfolio_table.py`, the quantity is displayed without indicating whether it's a long or short position:
     ```python
     html.Span(f"{stock.quantity:,}" if stock.quantity is not None else "N/A")
     ```

## Code Duplication and Complexity

1. **Option Processing Logic**
   - Significant duplication between the main option processing loop (lines 427-582) and the orphaned options processing (lines 622-845) in `portfolio.py`.
   - Both sections have nearly identical validation, parsing, and calculation logic, including:
     ```python
     # In main option processing
     parsed_option = parse_option_description(option_desc, opt_quantity, opt_last_price)
     delta = calculate_option_delta(parsed_option, stock_info["price"], use_black_scholes=True)

     # In orphaned options processing (duplicated)
     parsed_option = parse_option_description(option_desc, opt_quantity, opt_last_price)
     delta = calculate_option_delta(parsed_option, underlying_price, use_black_scholes=True)
     ```
   - Error handling is duplicated in both sections with similar try-except blocks.

2. **Exposure Calculation Duplication**
   - Multiple places calculate exposure in slightly different ways:
     - In `portfolio.py`, `process_portfolio_data` calculates stock exposure as:
       ```python
       stock_data_for_group = {
           "market_exposure": value,  # This is the market exposure (quantity * price)
           "beta_adjusted_exposure": value * beta,
       }
       ```
     - In `update_portfolio_prices`, it's calculated as:
       ```python
       group.stock_position.market_exposure = (group.stock_position.price * group.stock_position.quantity)
       group.stock_position.beta_adjusted_exposure = (group.stock_position.market_exposure * group.stock_position.beta)
       ```
     - In `data_model.py`, `create_portfolio_group` recalculates net exposure:
       ```python
       net_exposure = (stock_position.market_exposure if stock_position else 0) + sum(opt.delta_exposure for opt in option_positions)
       ```
     - In `chart_data.py`, exposure metrics are transformed again for visualization.

3. **High Complexity Areas**
   - The `process_portfolio_data` function in `portfolio.py` is over 300 lines long with multiple nested try-except blocks and complex conditional logic.
   - The function has 5 levels of nesting in some places, making it difficult to follow the control flow.
   - The option delta calculation in `option_utils.py` has multiple fallback mechanisms and complex error handling:
     ```python
     # First try Black-Scholes
     try:
         delta = calculate_black_scholes_delta(...)
     except Exception as e:
         # Fall back to simple delta
         return _calculate_simple_delta(...)
     ```

4. **Redundant Data Transformations**
   - Multiple conversions between object models and dictionaries:
     - Every data model class has `to_dict` and `from_dict` methods:
       ```python
       def to_dict(self) -> StockPositionDict:
           return {
               "ticker": self.ticker,
               "quantity": self.quantity,
               # ...
           }
       ```
     - `chart_data.py` has transformation functions that convert the same data again:
       ```python
       def transform_for_treemap(portfolio_groups: list[PortfolioGroup], _group_by: str = "ticker") -> dict[str, Any]:
           # ...
       ```
     - UI components in `components/portfolio_table.py` and `components/position_details.py` transform the data yet again for display.

## Recommendations

### Short Position Handling

1. **Consistent Representation**
   - Store all position quantities with their natural sign (negative for short positions) throughout the codebase.
   - Update the `StockPosition` class to explicitly document that negative quantities represent short positions and add an `is_short` property similar to the one in `OptionPosition`:
     ```python
     @property
     def is_short(self) -> bool:
         """Check if position is short (quantity is negative)."""
         return self.quantity < 0
     ```
   - Modify the stock quantity parsing in `portfolio.py` to preserve negative values for short positions:
     ```python
     # Check if this is a short position (indicated by negative value or special marker)
     is_short = False
     if isinstance(row["Quantity"], str) and row["Quantity"].startswith("-"):
         is_short = True
     # or check other indicators like account type or position type

     quantity = int(float(row["Quantity"]))
     if is_short:
         quantity = -abs(quantity)  # Ensure negative for short positions
     ```

2. **Exposure Calculations**
   - Simplify exposure calculations by using the natural sign of quantities and exposures:
     ```python
     # In calculate_portfolio_summary
     if exposure > 0:  # Positive exposure (long)
         long_exposure += exposure
     else:  # Negative exposure (short)
         short_exposure += exposure  # Store as negative value
     ```
   - Update `calculate_beta_adjusted_net_exposure` to simply add the exposures (since short is already negative):
     ```python
     def calculate_beta_adjusted_net_exposure(long_beta_adjusted: float, short_beta_adjusted: float) -> float:
         """Calculate the beta-adjusted net exposure by adding the exposures.

         Note: short_beta_adjusted should be a negative value.
         """
         return long_beta_adjusted + short_beta_adjusted  # short is already negative
     ```

3. **Remove Absolute Value Operations**
   - Remove unnecessary `abs()` calls in calculations where the sign is meaningful:
     ```python
     # Before
     short_stocks["value"] += abs(stock.market_exposure)

     # After
     short_stocks["value"] += stock.market_exposure  # Already negative for short positions
     ```
   - Only use `abs()` for display purposes or when calculating percentage weights:
     ```python
     # For percentage calculations where direction doesn't matter
     gross_market_exposure = sum(abs(exposure) for exposure in all_exposures)
     ```

### Code Improvements

1. **Refactor Option Processing**
   - Extract common option processing logic into helper functions to reduce duplication:
     ```python
     def process_option(option_desc, quantity, price, underlying_price, beta):
         """Process an option and return its metrics."""
         try:
             parsed_option = parse_option_description(option_desc, quantity, price)
             delta = calculate_option_delta(parsed_option, underlying_price)
             # Calculate exposures
             return {
                 "parsed_option": parsed_option,
                 "delta": delta,
                 "delta_exposure": delta * parsed_option.notional_value,
                 "beta_adjusted_exposure": delta * parsed_option.notional_value * beta,
             }
         except Exception as e:
             logger.error(f"Error processing option {option_desc}: {e}")
             return None
     ```

2. **Simplify Exposure Calculations**
   - Centralize exposure calculation logic in the data model:
     ```python
     # In StockPosition class
     @property
     def market_exposure(self) -> float:
         """Calculate market exposure based on quantity and price."""
         return self.quantity * self.price

     @property
     def beta_adjusted_exposure(self) -> float:
         """Calculate beta-adjusted exposure."""
         return self.market_exposure * self.beta
     ```

3. **Break Down Complex Functions**
   - Split `process_portfolio_data` into smaller, focused functions:
     ```python
     def process_stock_positions(stock_df):
         """Process stock positions from DataFrame."""
         # ...

     def process_option_positions(option_df, stock_positions):
         """Process option positions from DataFrame."""
         # ...

     def create_portfolio_groups(stock_positions, option_positions):
         """Create portfolio groups from processed positions."""
         # ...
     ```

4. **Standardize Data Transformations**
   - Create a dedicated transformation layer:
     ```python
     # In a new file: src/folio/transformers.py
     def transform_for_ui(portfolio_groups, portfolio_summary):
         """Transform portfolio data for UI display."""
         # ...

     def transform_for_charts(portfolio_groups, portfolio_summary):
         """Transform portfolio data for charts."""
         # ...
     ```

## Implementation Priority

1. **Fix Short Position Representation**
   - Update `StockPosition` class to add `is_short` property
   - Modify stock quantity parsing to preserve negative values
   - Update documentation to clarify that negative quantities represent short positions

2. **Update Exposure Calculations**
   - Modify `calculate_portfolio_summary` to handle negative exposures naturally
   - Update `calculate_beta_adjusted_net_exposure` to add exposures (with short as negative)
   - Remove unnecessary `abs()` calls in calculations

3. **Refactor Option Processing**
   - Extract common option processing logic into helper functions
   - Create a unified option processing pipeline

4. **Improve UI for Short Positions**
   - Update `components/position_details.py` to visually distinguish short positions
   - Add indicators in `components/portfolio_table.py` for short positions
