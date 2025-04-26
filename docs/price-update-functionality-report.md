# Price Update Functionality Report

This document provides a comprehensive analysis of how price updating works in the Folio application, including the initial price loading, manual price updates, and the impact on portfolio calculations.

> **Note**: This report has been updated to reflect the improvements made in the [Price Update Functionality Improvements](devlog/20250409_165254.md) devlog, which implemented changes from the [Price Data Model Refactoring](devplan/2025-04-06-price-data-model-refactoring.md) plan.

## Overview

The Folio application has a price update mechanism that allows users to refresh the prices of their portfolio positions. This functionality is implemented through:

1. A data model that stores prices for each position
2. Functions to fetch and update prices
3. A UI component (navbar) with a button to trigger updates
4. Callbacks to process the updates and refresh the UI

## Initial Price Loading

When a portfolio is first loaded (either through file upload or sample data), the following process occurs:

1. The CSV data is parsed and processed in `process_portfolio_data()` function
2. For each position:
   - The price is extracted from the "Last Price" column in the CSV
   - This price is stored in the `price` attribute of `StockPosition` and `OptionPosition` objects
   - The `market_exposure` is calculated as `quantity * price`
   - For stocks, `beta_adjusted_exposure` is calculated as `market_exposure * beta`

3. A timestamp is set in the `PortfolioSummary` object:
   ```python
   # In calculate_portfolio_summary()
   current_time = datetime.now(UTC).isoformat()
   summary = PortfolioSummary(
       # ... other fields ...
       price_updated_at=current_time,  # Set the timestamp
   )
   ```

**Important**: During initial loading, prices are NOT updated from external sources. The application uses the prices provided in the CSV file.

## Manual Price Updates

When a user clicks the "Update Prices" button in the navbar, the following process occurs:

1. The `update_prices()` callback in `navbar.py` is triggered
2. This callback calls `update_portfolio_summary_with_prices()` from `portfolio.py`
3. `update_portfolio_summary_with_prices()` performs these steps:
   - Calls `update_portfolio_prices()` to fetch the latest prices
   - Extracts cash-like positions from the current summary
   - Recalculates the portfolio summary with the updated prices and cash-like positions
   - Sets the `price_updated_at` timestamp
   - Updates the portfolio estimate value to include both net market exposure and cash-like value

4. The `update_portfolio_prices()` function:
   - Extracts unique tickers from all positions
   - Filters out cash-like instruments (no need to update their prices)
   - Fetches the latest prices for each ticker using the data fetcher
   - Updates the `price` attribute of each position
   - For stock positions, recalculates:
     - `market_exposure = price * quantity`
     - `beta_adjusted_exposure = market_exposure * beta`
   - For option positions:
     - Updates the price
     - Calls `recalculate_option_metrics()` to update option metrics
   - After updating all positions, calls `recalculate_group_metrics()` for each group
   - Returns a timestamp of when the update occurred

5. The `recalculate_option_metrics()` function:
   - Gets the underlying ticker and price
   - Creates an `OptionPosition` object for delta calculation
   - Recalculates delta using the Black-Scholes model
   - Updates notional value based on the new underlying price
   - Recalculates delta exposure and beta-adjusted exposure

6. The `recalculate_group_metrics()` function:
   - Calculates total delta exposure from options
   - Updates group metrics (net exposure, total delta exposure, beta-adjusted exposure)

7. After prices are updated, the portfolio summary is recalculated using `calculate_portfolio_summary()`
8. The updated data is returned to the UI and displayed

## Impact on Portfolio Calculations

When prices are updated, the following calculations are affected:

### For Stock Positions:
- `market_exposure` is recalculated as `price * quantity`
- `beta_adjusted_exposure` is recalculated as `market_exposure * beta`

### For Option Positions:
- The `price` attribute is updated
- The `delta` is recalculated using the Black-Scholes model
- The `notional_value` is recalculated based on the new underlying price
- The `delta_exposure` is recalculated as `delta * notional_value * (1 if quantity > 0 else -1)`
- The `beta_adjusted_exposure` is recalculated as `delta_exposure * beta`

### For Portfolio Groups:
- The `total_delta_exposure` is recalculated as the sum of all option delta exposures
- The `net_exposure` is recalculated as stock exposure + options delta exposure
- The `beta_adjusted_exposure` is recalculated as stock beta-adjusted + options beta-adjusted

### For Portfolio Summary:
- The entire portfolio summary is recalculated using `calculate_portfolio_summary()`
- Cash-like positions are included in the recalculation
- The `portfolio_estimate_value` is calculated as `net_market_exposure + cash_like_value`
- This includes:
  - Net market exposure
  - Portfolio beta
  - Long and short exposures
  - Options exposures
  - Short percentage
  - Cash percentage
  - Portfolio estimated value

## Improvements Made

Based on the analysis of the price update functionality, several improvements have been implemented:

1. **Complete Option Recalculation**: Option exposures are now fully recalculated when prices are updated, including delta, notional value, and delta exposure.

2. **Modular Code Structure**: The code has been refactored to be more modular, with separate functions for recalculating option metrics and group metrics.

3. **Consistent Portfolio Value Calculation**: The portfolio estimate value is now calculated consistently as net market exposure + cash-like value.

4. **Enhanced Option Symbol Handling**: Added support for parsing option symbols in different formats, including the '-AMAT250516P130' format.

5. **Comprehensive Integration Tests**: Added integration tests to verify that prices and exposures are updated correctly.

## Remaining Recommendations

While significant improvements have been made, there are still some recommendations for future enhancements:

1. **Visual Feedback**: Add visual feedback to indicate which values have changed after a price update (e.g., highlighting changed values).

2. **Loading Indicator**: Add a loading indicator while prices are being updated to provide better user feedback.

3. **Confirmation Message**: Display a confirmation message when prices have been successfully updated.

4. **Differential Display**: Show the difference between old and new values to help users understand the impact of price changes.

5. **Throttling**: Implement throttling to prevent multiple rapid price updates.

6. **Error Handling**: Improve error handling to provide better feedback when price updates fail.

## Conclusion

The price update functionality in Folio has been significantly improved, with complete recalculation of option exposures and consistent portfolio value calculation. These changes ensure that all portfolio metrics are accurately updated when prices change, providing users with a more reliable and accurate view of their portfolio.

Future enhancements should focus on improving the user experience with better visual feedback and error handling.
