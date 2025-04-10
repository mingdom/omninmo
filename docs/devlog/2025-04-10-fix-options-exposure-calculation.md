# Fix Options Exposure Calculation and Remove Unnecessary Metrics

Date: 2025-04-10

## Summary

This update addresses several issues with the portfolio exposure calculations, particularly focusing on options exposure and the display of short positions. It also removes unnecessary metrics and code that were no longer needed.

## Changes

### 1. Fixed Options Exposure Calculation

- Modified the calculation of net delta exposure to correctly handle short positions
- Updated the formula description to accurately reflect the calculation
- Ensured consistent handling of signed values throughout the codebase

Before this fix, the options exposure calculation was using `long_option_value - short_option_value`, but since `short_option_value` was already negative, this was effectively adding the absolute values, which was incorrect. The fix changes this to `long_option_value + short_option_value`, which correctly accounts for the sign of the short positions.

### 2. Updated Exposure Chart Display

- Modified the exposure chart to show short positions as negative values
- This provides a more accurate visual representation of the portfolio's directional exposure

### 3. Removed Sector Allocation Code

- Removed the sector allocation chart code as it's not currently supported
- This simplifies the codebase and removes unused functionality

### 4. Removed Gross Market Exposure Metric

- Removed the `gross_market_exposure` metric as it was deemed unnecessary
- Updated the short percentage calculation to use long exposure as the denominator instead
- This provides a more meaningful measure of how much the portfolio is hedged

### 5. Added Signed Notional Value Property

- Added a `signed_notional_value` property to the `OptionPosition` class
- This property returns a signed notional value (positive for long positions, negative for short positions)
- This helps distinguish between long and short positions in calculations

### 6. Added Comprehensive Tests

- Added tests to verify the notional value and delta exposure calculations
- Ensured that the exposures have the correct signs and magnitudes

## Technical Details

The key issue was in how we were handling the sign of short positions in various calculations. We were using `abs()` in places where we should have preserved the sign, and we were subtracting values that were already negative, effectively adding them.

The fix ensures that:
- Short positions are consistently represented with negative values
- Exposure calculations correctly account for direction
- `abs()` is only used when appropriate (for magnitude calculations)

## Related Issues

This fix addresses the issue where options exposure was being calculated incorrectly, leading to inflated exposure values.

## Testing

All tests are now passing, including the new tests for option notional value and exposure calculations.
