# Progress on Calculation Issues

Date: 2025-04-10

## Summary

This document summarizes the progress made on addressing the calculation issues outlined in `docs/devplan/calculation-issues.md`. We've made significant progress in fixing the exposure calculations, particularly for options, but there are still some important items remaining.

## Completed Items

### 1. Fixed Options Exposure Calculation

- Added a `signed_notional_value` property to the `OptionPosition` class to provide a directionally-correct notional value
- Fixed the calculation of net delta exposure to correctly handle short positions
- Updated the formula description to accurately reflect the calculation
- Ensured consistent handling of signed values throughout the codebase

### 2. Updated Exposure Chart Display

- Modified the exposure chart to show short positions as negative values
- This provides a more accurate visual representation of the portfolio's directional exposure

### 3. Removed Unnecessary Metrics and Code

- Removed the `gross_market_exposure` metric as it was deemed unnecessary
- Removed the sector allocation chart code as it's not currently supported
- Updated the short percentage calculation to use long exposure as the denominator instead
- This provides a more meaningful measure of how much the portfolio is hedged

### 4. Added Comprehensive Tests

- Added tests to verify the notional value and delta exposure calculations
- Ensured that the exposures have the correct signs and magnitudes

## Remaining Items

### 1. Fix Short Position Representation

- Ensure stock quantities are stored with their natural sign (negative for short positions)
- Remove any redundant `is_short` properties and use `quantity < 0` directly in the code
- Update documentation to clarify that negative quantities represent short positions

Currently, stock positions are not consistently represented with negative quantities for short positions, unlike options which correctly use negative quantities. This inconsistency makes the code more complex and error-prone. We should simplify by using the sign of the quantity directly rather than adding redundant properties.

### 2. Refactor Option Processing

- Extract common option processing logic into helper functions
- Create a unified option processing pipeline

There's significant duplication between the main option processing loop and the orphaned options processing in `portfolio.py`. Both sections have nearly identical validation, parsing, and calculation logic.

### 3. Improve UI for Short Positions

- Update `components/position_details.py` to visually distinguish short positions
- Add indicators in `components/portfolio_table.py` for short positions

Currently, short positions are not visually distinguished from long positions in the UI, which can be confusing for users.

## Next Steps

The next priority should be to fix the short position representation for stock positions. This will make the codebase more consistent and reduce the complexity of the exposure calculations. After that, we can focus on refactoring the option processing logic and improving the UI for short positions.

## Related Documents

- [Calculation Issues Plan](../devplan/calculation-issues.md)
- [Fix Options Exposure Calculation](./2025-04-10-fix-options-exposure-calculation.md)
