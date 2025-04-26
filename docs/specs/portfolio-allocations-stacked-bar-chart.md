# Portfolio Allocations Stacked Bar Chart Specification

## Overview

The Portfolio Allocations Stacked Bar Chart provides a visual representation of how a portfolio's value is distributed across different asset types and position directions. It shows the composition of the portfolio in terms of long positions, short positions, cash, and pending activity.

## Feature Requirements

### Chart Structure

1. **X-Axis Categories**: The chart will have four main categories on the x-axis:
   - Long: Represents all long positions (positive values)
   - Short: Represents all short positions (negative values)
   - Cash: Represents cash-like positions
   - Pending: Represents pending activity

2. **Stacked Bars**:
   - The "Long" bar will be stacked with:
     - Long Stocks (bottom)
     - Long Options (top)
   - The "Short" bar will be stacked with:
     - Short Stocks (bottom)
     - Short Options (top)
   - "Cash" and "Pending" will be single-segment bars

3. **Dual Y-Axes**:
   - Left Y-Axis: Absolute dollar values
   - Right Y-Axis: Percentage of total portfolio value

### Data Representation

1. **Value Calculation**:
   - Long Stock Value: Sum of market values of all long stock positions
   - Long Option Value: Sum of market values of all long option positions
   - Short Stock Value: Sum of market values of all short stock positions (stored as negative values)
   - Short Option Value: Sum of market values of all short option positions (stored as negative values)
   - Cash Value: Sum of all cash-like positions
   - Pending Value: Sum of all pending activity

2. **Percentage Calculation**:
   - Each component's percentage is calculated as: (Component Value / Total Portfolio Value) × 100
   - For short positions, the percentage will be negative to maintain sign consistency

### Visual Design

1. **Colors**:
   - Long Stocks: Dark green
   - Long Options: Light green
   - Short Stocks: Dark gray
   - Short Options: Light gray
   - Cash: Medium gray
   - Pending: Light gray

2. **Labels and Tooltips**:
   - Each segment will be labeled with its name
   - Tooltips will show: Component name, dollar value, and percentage of portfolio
   - Example: "Long Stocks: $1,831,034.12 (70.4%)"

3. **Legend**:
   - Positioned below the chart
   - Shows all six components (Long Stocks, Long Options, Short Stocks, Short Options, Cash, Pending)

## User Interaction

1. **Hover Information**:
   - When hovering over a segment, display detailed information about that segment
   - Show both dollar value and percentage of portfolio

2. **Responsiveness**:
   - Chart should resize appropriately based on container size
   - Maintain readability at different screen sizes

## Edge Cases

1. **Empty Portfolio**:
   - If the portfolio is empty, display a message: "No portfolio data available"

2. **Zero Values**:
   - If a component has zero value, it should not appear in the chart
   - The stacked bar should only show non-zero components

3. **Negative Total Value**:
   - If the total portfolio value is negative or zero, percentages should be calculated as zero
   - A warning message should be displayed

## Test Plan

### Unit Tests

1. **Component Value Extraction Tests**:
   - Test that long/short stock and option values are correctly extracted from the portfolio summary
   - Verify that short values remain negative throughout the process
   - Test with various portfolio compositions (all long, all short, mixed, empty)

2. **Percentage Calculation Tests**:
   - Test that percentages are correctly calculated based on total portfolio value
   - Verify that percentage signs match value signs (negative for shorts)
   - Test edge cases (zero total value, negative total value)

3. **Chart Data Transformation Tests**:
   - Test that the chart data structure is correctly generated
   - Verify that the stacked bar structure is maintained
   - Test that tooltips and labels contain correct information

### Integration Tests

1. **Chart Rendering Tests**:
   - Test that the chart renders correctly with various portfolio compositions
   - Verify that stacking works as expected
   - Test that dual y-axes show correct values and percentages

2. **Edge Case Handling**:
   - Test with empty portfolio
   - Test with portfolio containing only one type of asset
   - Test with extreme values (very large or very small)

### Visual Regression Tests

1. **Layout Tests**:
   - Verify that the chart layout matches the design specification
   - Test that colors are applied correctly
   - Verify that the legend is positioned correctly

2. **Responsiveness Tests**:
   - Test chart rendering at different screen sizes
   - Verify that the chart remains readable on small screens

## Acceptance Criteria

1. The chart correctly displays four main categories: Long, Short, Cash, and Pending.
2. Long and Short bars are properly stacked with their respective components.
3. Dual y-axes correctly show both dollar values and percentages.
4. Short values are consistently represented as negative throughout the codebase.
5. Tooltips show correct values and percentages for each component.
6. The chart handles all edge cases gracefully.
7. The chart is visually consistent with the rest of the application.
8. The implementation reuses existing portfolio calculation functions rather than duplicating logic.

## Development Plan
See docs/devplan/2025-04-20-allocations-stacked-bar-chart-implementation.md
