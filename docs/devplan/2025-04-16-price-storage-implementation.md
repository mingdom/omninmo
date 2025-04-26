# Price Storage Implementation Plan

## Overview

This development plan outlines how to implement price storage for both stocks and options in the portfolio CSV, allowing prices to be loaded from the CSV on initial load and updated with current market data when requested.

## Current State

Currently, the application:

1. Loads prices from the "Last Price" column in the CSV file during initial portfolio loading
2. Stores these prices in the `price` attribute of `StockPosition` and `OptionPosition` objects
3. Uses these prices to calculate market exposure and other metrics
4. Provides a function `update_portfolio_prices()` to fetch current prices from external data sources
5. However, there is no UI component to trigger price updates (the navbar component mentioned in documentation doesn't exist yet)

## Implementation Plan

### Phase 1: Ensure Proper Price Loading from CSV

1. Verify that the current code correctly loads prices from the "Last Price" column in the CSV
2. Add validation to ensure prices are properly formatted and handled
3. Add tests to verify price loading functionality

### Phase 2: Create Navbar Component with Price Update Button

1. Create a new `navbar.py` component with a price update button
2. Add a timestamp display to show when prices were last updated
3. Implement callbacks to trigger price updates when the button is clicked
4. Update the app layout to include the navbar component

### Phase 3: Implement Price Update Functionality

1. Enhance the existing `update_portfolio_prices()` function to handle both stocks and options
2. Ensure proper error handling for failed price updates
3. Add visual feedback for successful/failed price updates
4. Implement caching to prevent excessive API calls

### Phase 4: Add Price Storage in CSV Export

1. Modify the CSV export functionality to include current prices
2. Ensure prices are properly formatted in the exported CSV
3. Add tests to verify price export functionality

### Phase 5: Testing and Documentation

1. Add comprehensive tests for all new functionality
2. Update documentation to reflect the new price storage and update features
3. Create user documentation explaining how to use the price update feature

## Detailed Implementation

### Phase 1: Ensure Proper Price Loading from CSV

The current code already loads prices from the "Last Price" column in the CSV file. We need to verify that this works correctly for both stocks and options.

```python
# In src/folio/portfolio.py - process_portfolio_data function

# Process price
if pd.isna(row["Last Price"]) or row["Last Price"] in ("--", ""):
    if is_known_cash:
        # Use default values for cash-like positions with missing price
        price = 0.0
        beta = 0.0
        is_cash_like = True
        logger.info(
            f"Row {index}: Cash-like position {symbol} missing price. Using defaults."
        )
    else:
        logger.warning(
            f"Row {index}: {symbol} has missing price. Skipping."
        )
        continue
else:
    price = clean_currency_value(row["Last Price"])
    if price < 0:
        logger.warning(
            f"Row {index}: {symbol} has negative price ({price}). Skipping."
        )
        continue
    elif price == 0:
        logger.warning(
            f"Row {index}: {symbol} has zero price. Calculations may be affected."
        )
```

This code already handles price loading from the CSV file. We should add tests to verify that it works correctly for both stocks and options.

### Phase 2: Create Navbar Component with Price Update Button

Create a new file `src/folio/components/navbar.py` with the following content:

```python
"""Navbar component for the Folio application."""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context

from ..logger import logger
from ..portfolio import update_portfolio_summary_with_prices
from datetime import datetime


def create_navbar():
    """Create the navbar component with price update button."""
    return dbc.Navbar(
        dbc.Container(
            [
                # Brand/logo
                dbc.NavbarBrand("Folio", className="me-auto"),
                
                # Price update section
                html.Div(
                    [
                        # Last updated timestamp
                        html.Span(
                            "Prices as of: ",
                            className="me-2 text-muted",
                        ),
                        html.Span(
                            id="price-updated-at",
                            className="me-3",
                        ),
                        
                        # Update button
                        dbc.Button(
                            [
                                html.I(className="fas fa-sync-alt me-2"),
                                "Update Prices",
                            ],
                            id="update-prices-button",
                            color="primary",
                            size="sm",
                            className="ms-2",
                        ),
                    ],
                    className="d-flex align-items-center",
                ),
            ],
            fluid=True,
        ),
        color="light",
        className="mb-4",
    )


def register_callbacks(app):
    """Register callbacks for the navbar component."""
    
    @app.callback(
        [
            Output("portfolio-summary", "data"),
            Output("portfolio-groups", "data"),
            Output("price-updated-at", "children"),
            Output("update-prices-button", "disabled"),
            Output("update-prices-button", "children"),
        ],
        [Input("update-prices-button", "n_clicks")],
        [
            State("portfolio-groups", "data"),
            State("portfolio-summary", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_prices(n_clicks, groups_data, summary_data):
        """Update prices for all positions in the portfolio."""
        if not n_clicks:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        if not groups_data or not summary_data:
            return dash.no_update, dash.no_update, "No data loaded", True, [
                html.I(className="fas fa-sync-alt me-2"),
                "Update Prices",
            ]
        
        # Disable button and show loading state
        ctx = callback_context
        if ctx.triggered and "update-prices-button" in ctx.triggered[0]["prop_id"]:
            # Show loading state
            loading_button = [
                html.I(className="fas fa-spinner fa-spin me-2"),
                "Updating...",
            ]
            
            try:
                # Convert JSON data back to Python objects
                from ..data_model import PortfolioGroup, PortfolioSummary
                portfolio_groups = [PortfolioGroup.from_dict(group) for group in groups_data]
                portfolio_summary = PortfolioSummary.from_dict(summary_data)
                
                # Update prices
                updated_summary = update_portfolio_summary_with_prices(
                    portfolio_groups, portfolio_summary
                )
                
                # Format timestamp for display
                timestamp = updated_summary.price_updated_at
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = "Unknown"
                
                # Convert back to JSON-serializable format
                updated_groups_data = [group.to_dict() for group in portfolio_groups]
                updated_summary_data = updated_summary.to_dict()
                
                # Re-enable button and restore original text
                return (
                    updated_summary_data,
                    updated_groups_data,
                    formatted_time,
                    False,
                    [html.I(className="fas fa-sync-alt me-2"), "Update Prices"],
                )
            
            except Exception as e:
                logger.error(f"Error updating prices: {e}", exc_info=True)
                # Re-enable button and show error state
                return (
                    dash.no_update,
                    dash.no_update,
                    "Update failed",
                    False,
                    [html.I(className="fas fa-exclamation-triangle me-2"), "Update Failed"],
                )
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    
    @app.callback(
        Output("price-updated-at", "children"),
        [Input("portfolio-summary", "data")],
        prevent_initial_call=False,
    )
    def update_timestamp(summary_data):
        """Update the timestamp display when portfolio data changes."""
        if not summary_data or "price_updated_at" not in summary_data or not summary_data["price_updated_at"]:
            return "Not updated"
        
        try:
            # Parse ISO timestamp and format for display
            timestamp = summary_data["price_updated_at"]
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing timestamp: {e}")
            return "Unknown"
```

### Phase 3: Implement Price Update Functionality

The existing `update_portfolio_prices()` function already handles updating prices for both stocks and options. We need to ensure it works correctly and add proper error handling.

```python
# In src/folio/portfolio.py - update_portfolio_prices function

def update_portfolio_prices(
    portfolio_groups: list[PortfolioGroup], data_fetcher=None
) -> str:
    """Update prices for all positions in the portfolio groups.

    Args:
        portfolio_groups: List of portfolio groups to update prices for
        data_fetcher: Optional data fetcher to use for price updates

    Returns:
        ISO format timestamp of when prices were updated
    """
    from datetime import UTC, datetime

    # Use the default data fetcher if none is provided
    if data_fetcher is None:
        data_fetcher = create_data_fetcher()

    # Extract unique tickers from all positions
    tickers = set()
    for group in portfolio_groups:
        # Add stock position ticker
        if group.stock_position:
            tickers.add(group.stock_position.ticker)

        # Add option position tickers
        for option in group.option_positions:
            tickers.add(option.ticker)

    # Remove cash-like instruments as we don't need to update their prices
    tickers = [ticker for ticker in tickers if not is_cash_or_short_term(ticker)]

    if not tickers:
        logger.info("No tickers to update prices for")
        return datetime.now(UTC).isoformat()

    # Fetch latest prices for all tickers
    logger.info(f"Fetching latest prices for {len(tickers)} tickers")

    # Use a small period to get just the latest price
    latest_prices = {}
    for ticker in tickers:
        try:
            # Fetch data for the last day
            df = data_fetcher.fetch_data(ticker, period="1d")
            if not df.empty:
                # Get the latest close price
                latest_prices[ticker] = df.iloc[-1]["Close"]
                logger.debug(f"Updated price for {ticker}: {latest_prices[ticker]}")
            else:
                logger.warning(f"No price data available for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e!s}")

    # Update prices for all positions
    for group in portfolio_groups:
        # Update stock position price
        if group.stock_position and group.stock_position.ticker in latest_prices:
            group.stock_position.price = latest_prices[group.stock_position.ticker]
            # Update market exposure based on new price
            group.stock_position.market_exposure = (
                group.stock_position.price * group.stock_position.quantity
            )
            group.stock_position.beta_adjusted_exposure = (
                group.stock_position.market_exposure * group.stock_position.beta
            )

        # Update option position prices
        for option in group.option_positions:
            if option.ticker in latest_prices:
                option.price = latest_prices[option.ticker]
                # We don't update market_exposure for options as it's based on notional value

    # Return the current timestamp
    current_time = datetime.now(UTC).isoformat()
    logger.info(f"Prices updated at {current_time}")
    return current_time
```

This function already handles updating prices for both stocks and options. We need to update the app layout to include the navbar component.

### Phase 4: Add Price Storage in CSV Export

We need to modify the CSV export functionality to include current prices. This will ensure that when a user exports their portfolio, the prices are preserved.

```python
# In src/folio/callbacks/export.py - export_portfolio function

def export_portfolio(portfolio_groups, summary):
    """Export portfolio data to CSV."""
    # Create a DataFrame from the portfolio groups
    rows = []
    for group in portfolio_groups:
        # Add stock position
        if group.stock_position:
            row = {
                "Symbol": group.stock_position.ticker,
                "Description": group.stock_position.description,
                "Quantity": group.stock_position.quantity,
                "Last Price": group.stock_position.price,  # Include current price
                # ... other fields ...
            }
            rows.append(row)
        
        # Add option positions
        for option in group.option_positions:
            row = {
                "Symbol": option.ticker,
                "Description": option.description,
                "Quantity": option.quantity,
                "Last Price": option.price,  # Include current price
                # ... other fields ...
            }
            rows.append(row)
    
    # Create DataFrame and export to CSV
    df = pd.DataFrame(rows)
    csv_string = df.to_csv(index=False)
    return csv_string
```

## Risk Assessment

### Complexity

**Medium**

- The core functionality for loading and updating prices already exists
- The main work is creating the UI component and integrating it with the existing functionality
- Error handling and edge cases need careful consideration

### Design Trade-offs

1. **CSV Format vs. Database Storage**
   - **CSV Format**: 
     - Pros: Simple, portable, easy to edit manually, compatible with existing systems
     - Cons: Limited data validation, no schema enforcement, potential for data corruption
   - **Database Storage**: 
     - Pros: Better data integrity, schema enforcement, more powerful queries
     - Cons: More complex setup, requires database management, less portable

   **Decision**: Stick with CSV format for now as it aligns with the current application architecture and user expectations. The simplicity and portability of CSV files outweigh the benefits of database storage for this specific use case.

2. **Price Update Mechanism**
   - **On-demand Updates**: 
     - Pros: User has control over when prices are updated, reduces API calls
     - Cons: Prices may be stale if user forgets to update
   - **Automatic Updates**: 
     - Pros: Always up-to-date prices, better user experience
     - Cons: More API calls, potential rate limiting issues

   **Decision**: Implement on-demand updates with a clear UI indicator showing when prices were last updated. This balances user control with system performance and avoids potential API rate limiting issues.

3. **Price Source**
   - **CSV Prices**: 
     - Pros: Fast loading, no API calls required, works offline
     - Cons: Prices may be stale, requires manual updates
   - **External API Prices**: 
     - Pros: Always up-to-date, more accurate
     - Cons: Requires network connection, potential API rate limiting

   **Decision**: Use a hybrid approach - load initial prices from CSV for fast startup, provide a clear button to update prices from external APIs when needed.

4. **Price Update Scope**
   - **Update All Prices**: 
     - Pros: Simpler implementation, consistent data
     - Cons: More API calls, slower updates
   - **Selective Updates**: 
     - Pros: Fewer API calls, faster updates
     - Cons: More complex implementation, potential for inconsistent data

   **Decision**: Update all prices at once for simplicity and data consistency. The number of positions in a typical portfolio is not large enough to cause performance issues.

## Conclusion

This implementation plan provides a comprehensive approach to introducing and storing prices for both stocks and options in the portfolio. By leveraging existing functionality and adding a clear UI component, we can provide users with the ability to load prices from CSV and update them with current market data when needed.

The plan balances simplicity, performance, and user experience, while considering the trade-offs between different approaches. The hybrid approach of loading initial prices from CSV and providing on-demand updates from external APIs offers the best of both worlds - fast startup and accurate data when needed.
