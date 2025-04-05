# UI Improvements Development Plan

## Overview

This development plan outlines the changes needed to improve the UI of the Folio application, focusing on three main areas:

1. Portfolio visualizations layout
2. Portfolio summary cards
3. Treemap simplification

## Current Issues

### 1. Portfolio Visualizations

- Charts are currently arranged in rows with two charts per row, which is not optimal for mobile viewing
- Toggle switches for the asset allocation and exposure charts are not working correctly
- Each chart is not in its own container, making it difficult to manage spacing and layout

### 2. Portfolio Summary Cards

- Beta values are displayed in each card, cluttering the UI
- Cards are arranged in a single row with 4 cards, making them too small on mobile devices
- "Total Exposure" should be renamed to "Net Exposure" for clarity

### 3. Treemap

- Treemap is showing too much detail per position (beta values, delta values, etc.)
- We want to simplify it to show just the total net exposure per symbol

## Implementation Plan

### 1. Portfolio Visualizations

#### Changes Needed:

1. Modify the `create_dashboard_section` function in `src/folio/components/charts.py` to:
   - Place each chart in its own row
   - Wrap each chart in its own card container
   - Ensure each chart takes the full width of the container

2. Fix the toggle buttons for the asset allocation and exposure charts:
   - Review the callbacks in `src/folio/callbacks/chart_callbacks.py`
   - Ensure the button state is properly managed
   - Update the button styling to make it clear which option is active

### 2. Portfolio Summary Cards

#### Changes Needed:

1. Modify the summary cards in `src/folio/components/charts.py` to:
   - Remove beta values from individual cards
   - Add a new "Net Beta" card next to "Net Exposure" (formerly "Total Exposure")
   - Arrange cards in rows with 2 cards per row
   - Place "Net Exposure" and "Net Beta" in the first row

2. Update the summary cards callback in `src/folio/app.py` to:
   - Rename "Total Exposure" to "Net Exposure"
   - Create a separate output for the "Net Beta" card
   - Remove beta outputs for individual exposure cards

### 3. Treemap Simplification

#### Changes Needed:

1. Modify the `transform_for_treemap` function in `src/folio/chart_data.py` to:
   - Simplify the text displayed for each position
   - Focus on showing total net exposure per symbol
   - Remove detailed information like beta values, delta values, etc.
   - Keep the color coding for long/short positions

## Testing Plan

1. Manual testing:
   - Test on desktop and mobile devices
   - Verify that charts are properly displayed in their own rows
   - Check that toggle buttons work correctly
   - Ensure summary cards are properly arranged and display the correct information
   - Verify that the treemap shows the simplified information

2. Automated testing:
   - Update existing tests to reflect the new UI structure
   - Add tests for the new "Net Beta" card
   - Ensure all tests pass before submitting the changes

## Implementation Order

1. Fix the toggle buttons first, as this is a functional issue
2. Update the portfolio summary cards
3. Simplify the treemap
4. Modify the chart layout to place each chart in its own row

This order ensures that we fix functional issues first before making layout changes.
