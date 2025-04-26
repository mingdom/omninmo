# Summary Cards UI Revamp

## Overview
This development plan outlines the changes needed to revamp the summary cards UI in the Folio dashboard. The changes include:
1. Removing the portfolio beta card and related code
2. Elevating portfolio value to a higher-level UI element
3. Adding percentage of portfolio value as sub-text to each summary card

## Current Implementation Analysis

### Summary Cards Structure
The current implementation in `src/folio/components/summary_cards.py` creates a set of summary cards organized in two rows:
- Row 1: Portfolio Value, Net Exposure, Portfolio Beta, Beta-Adjusted Net Exposure
- Row 2: Long Exposure, Short Exposure, Options Exposure, Cash & Equivalents

Each card displays a title, value, and some include a percentage. The cards are created by individual functions and assembled in the `create_summary_cards()` function.

### Portfolio Beta Implementation
Portfolio beta is currently:
- Calculated in `portfolio.py` as part of the `calculate_portfolio_metrics` function
- Displayed in a dedicated card created by `create_portfolio_beta_card()`
- Updated via the callback in `register_callbacks()`

### Portfolio Value Implementation
Portfolio value is currently:
- Calculated in `portfolio_value.py` as part of the `calculate_portfolio_values` function
- Displayed in a card created by `create_portfolio_value_card()`
- Updated via the callback in `register_callbacks()`

## Proposed Changes

### 1. Remove Portfolio Beta

#### Code to Remove:
- In `src/folio/components/summary_cards.py`:
  - `create_portfolio_beta_card()` function
  - References to portfolio beta card in `create_summary_cards()` function
  - Portfolio beta output in the callback in `register_callbacks()`
  - Portfolio beta validation in `format_summary_card_values()`
  - Portfolio beta formatting in `format_summary_card_values()`
  - Portfolio beta error handling in `error_values()`

- In `tests/test_summary_cards.py`:
  - Update test assertions that check for portfolio beta values
  - Update test assertions that check for portfolio beta in the layout
  - Update expected values in `test_format_summary_card_values`
  - Update expected values in `test_format_summary_card_values_with_missing_keys`
  - Update expected values in `test_error_values`
  - Update component ID checks in `test_summary_cards_rendered_and_callback_registered`

#### Code to Keep:
- The `portfolio_beta` calculation in `portfolio.py` as it's used for beta-adjusted exposure
- The `calculate_beta_adjusted_net_exposure` function in `portfolio.py`
- Beta calculation functions in `utils.py` as they're used for other beta-related calculations
- Tests in `tests/test_beta.py` as they test the beta calculation functions
- Tests in `tests/e2e/test_portfolio_calculations.py` that test portfolio beta calculation

#### Impact Analysis:
- The portfolio beta calculation in `portfolio.py` is also used for beta-adjusted exposure, so we'll keep that function but remove any code that's exclusively for the portfolio beta card.
- The removal will free up space in the UI for better organization of the remaining cards.
- We need to update tests to reflect the removal of the portfolio beta card, but we should keep tests that verify the underlying beta calculation logic since it's still used for beta-adjusted exposure.

### 2. Elevate Portfolio Value Display

#### Options for Portfolio Value Display:

1. **Header Integration**
   - Move portfolio value to the app header next to the "Folio" title
   - Implementation: Modify `app.py` to include portfolio value in the header
   - Pros: Very prominent placement, clearly separates it from other metrics
   - Cons: May require additional styling work

2. **Standalone Banner**
   - Create a new banner component above the summary cards
   - Implementation: Add a new function `create_portfolio_value_banner()` in `summary_cards.py`
   - Pros: Visually distinct, can include additional context
   - Cons: Takes up vertical space

3. **Card Header Integration**
   - Move portfolio value to the header of the summary cards section
   - Implementation: Modify `create_summary_cards()` to include portfolio value in the card header
   - Pros: Maintains relationship with other metrics, doesn't require new UI elements
   - Cons: Less visually distinct than other options

#### Recommended Approach:
Option 3: Card Header Integration. This approach maintains the relationship between portfolio value and the other metrics while elevating its importance. The implementation would look like:

```python
# In create_summary_cards()
return dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4("Portfolio Summary", className="d-inline-block mb-0 me-3"),
                    html.H4(
                        [
                            html.Span("Total Value: ", className="text-muted"),
                            html.Span(id="portfolio-value", children="$0.00", className="text-primary"),
                        ],
                        className="d-inline-block mb-0"
                    ),
                ],
                className="d-flex align-items-center mb-3"
            ),
            # Rest of the cards...
        ]
    ),
    className="mb-3",
    id="summary-card",
)
```

### 3. Add Percentage to Each Card

#### Implementation:
- Modify the `format_summary_card_values()` function to calculate percentages for each metric
- Update each card creation function to include percentage display
- Update the callback to provide percentage values

#### Example for Net Exposure Card:
```python
def create_net_exposure_card():
    """Create the net exposure card."""
    # Create the components
    total_value = html.H5(
        id="total-value",
        className="card-title text-primary",
        children="$0.00",  # Default value
    )

    total_value_percent = html.P(
        id="total-value-percent",
        className="card-text text-muted",
        children="0% of portfolio",  # Default value with "of portfolio" text
    )

    # Rest of the function...
```

## Implementation Plan

1. **Remove Portfolio Beta Card and Related Code**
   - Remove `create_portfolio_beta_card()` function from `summary_cards.py`
   - Update `create_summary_cards()` to remove portfolio beta card
   - Update callback in `register_callbacks()` to remove portfolio beta output
   - Update `format_summary_card_values()` to remove portfolio beta validation and formatting
   - Update `error_values()` to remove portfolio beta error handling
   - Reorganize the remaining cards to fill the space

2. **Elevate Portfolio Value Display**
   - Implement the card header integration approach
   - Remove the existing portfolio value card
   - Update the callback to update the new portfolio value element
   - Add appropriate styling to make the portfolio value stand out

3. **Add Percentage to Each Card**
   - Update `format_summary_card_values()` to calculate percentages for each metric
   - Modify each card creation function to include percentage display
   - Update the callback to provide percentage values
   - Add "of portfolio" text to each percentage for clarity

4. **Update Tests**
   - Update `tests/test_summary_cards.py` to reflect the removal of portfolio beta
   - Update expected values in test assertions
   - Update component ID checks in tests
   - Add tests for the new percentage display functionality
   - Ensure all tests pass with the new implementation

## UI Mockup

```
+---------------------------------------------------------------+
| Portfolio Summary                Total Value: $100,000.00     |
+---------------------------------------------------------------+
|                                                               |
| +-------------------+ +-------------------+ +-------------------+ |
| | Net Exposure      | | Beta-Adjusted Net | | Long Exposure    | |
| | $80,000.00        | | $96,000.00        | | $90,000.00       | |
| | 80% of portfolio  | | 96% of portfolio  | | 90% of portfolio | |
| +-------------------+ +-------------------+ +-------------------+ |
|                                                               |
| +-------------------+ +-------------------+ +-------------------+ |
| | Short Exposure    | | Options Exposure  | | Cash & Equivalents| |
| | -$10,000.00       | | $15,000.00        | | $20,000.00       | |
| | 10% of portfolio  | | 15% of portfolio  | | 20% of portfolio | |
| +-------------------+ +-------------------+ +-------------------+ |
|                                                               |
+---------------------------------------------------------------+
```

## Conclusion

This revamp will streamline the summary cards UI by removing the less valuable portfolio beta metric, elevating the portfolio value to a more prominent position, and adding percentage context to each metric. These changes will make the dashboard more informative and easier to understand at a glance.
