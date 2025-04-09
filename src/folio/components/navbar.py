"""Navigation bar component for the Folio application."""

import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, no_update

from ..logger import logger


def create_navbar():
    """Create the application navbar with price update functionality."""

    # Format the timestamp (this will be updated by the callback)
    timestamp_display = html.Span(
        "No data loaded", id="price-timestamp-display", className="text-muted me-2"
    )

    # Create the update button
    update_button = dbc.Button(
        [html.I(className="fas fa-sync-alt me-2"), "Update Prices"],
        id="update-prices-button",
        color="primary",
        outline=True,
        size="sm",
        className="ms-2 px-3 py-1",
    )

    # Create the navbar
    navbar = dbc.Navbar(
        dbc.Container(
            [
                # Logo/Brand
                dbc.NavbarBrand(
                    html.Span(
                        [
                            html.Span("F", className="logo-letter logo-letter-primary"),
                            "olio",
                        ],
                        className="logo-text",
                    ),
                    className="me-auto fw-bold",
                ),
                # Price update section
                html.Div(
                    [
                        html.Span("Prices: ", className="text-muted me-1"),
                        timestamp_display,
                        update_button,
                    ],
                    className="d-flex align-items-center",
                ),
                # Future navigation links will go here when needed
            ],
            fluid=True,
        ),
        color="light",
        className="mb-4",
    )

    return navbar


def register_callbacks(app):
    """Register callbacks for the navbar component."""
    logger.info("Registering navbar callbacks")

    @app.callback(
        Output("price-timestamp-display", "children"),
        Input("portfolio-summary", "data"),
    )
    def update_timestamp_display(summary_data):
        """Update the timestamp display based on portfolio summary data."""
        if (
            not summary_data
            or "price_updated_at" not in summary_data
            or not summary_data["price_updated_at"]
        ):
            return "No data loaded"

        # Parse the ISO timestamp
        try:
            from datetime import datetime

            timestamp = datetime.fromisoformat(
                summary_data["price_updated_at"].replace("Z", "+00:00")
            )
            # Format it in a user-friendly way
            formatted_time = timestamp.strftime("%b %d, %Y %I:%M %p")
            return formatted_time
        except Exception as e:
            logger.error(f"Error formatting timestamp: {e}")
            return "Unknown"

    # This callback will be implemented to update prices when the button is clicked
    @app.callback(
        [
            Output("portfolio-summary", "data", allow_duplicate=True),
            Output("portfolio-groups", "data", allow_duplicate=True),
        ],
        Input("update-prices-button", "n_clicks"),
        [State("portfolio-groups", "data"), State("portfolio-summary", "data")],
        prevent_initial_call=True,
    )
    def update_prices(n_clicks, groups_data, summary_data):
        """Update prices for all positions in the portfolio."""
        if not n_clicks or not groups_data or not summary_data:
            return no_update, no_update

        logger.info("Updating prices for portfolio positions")

        try:
            from ..data_model import PortfolioSummary
            from ..portfolio import update_portfolio_summary_with_prices

            # Convert data back to PortfolioGroup objects
            groups = []
            for g in groups_data:
                group = _create_portfolio_group_from_data(g)
                groups.append(group)

            # Create a PortfolioSummary object from the summary data
            summary = PortfolioSummary.from_dict(summary_data)

            # Update prices
            updated_summary = update_portfolio_summary_with_prices(groups, summary)

            # Convert back to dictionaries for Dash
            updated_summary_data = updated_summary.to_dict()
            updated_groups_data = [g.to_dict() for g in groups]

            logger.info("Prices updated successfully")
            return updated_summary_data, updated_groups_data

        except Exception as e:
            logger.error(f"Error updating prices: {e}", exc_info=True)
            return summary_data, groups_data


def _create_portfolio_group_from_data(position_data):
    """Helper function to create a PortfolioGroup from position data."""
    from ..data_model import OptionPosition, PortfolioGroup, StockPosition

    stock_position = None
    if position_data["stock_position"]:
        stock_position_data = position_data["stock_position"].copy()
        # Remove attributes that don't exist in Position class
        if "sector" in stock_position_data:
            stock_position_data.pop("sector")
        if "is_cash_like" in stock_position_data:
            stock_position_data.pop("is_cash_like")
        stock_position = StockPosition(**stock_position_data)

    option_positions = [
        OptionPosition(**opt) for opt in position_data["option_positions"]
    ]

    return PortfolioGroup(
        ticker=position_data["ticker"],
        stock_position=stock_position,
        option_positions=option_positions,
        net_exposure=position_data["net_exposure"],
        beta=position_data["beta"],
        beta_adjusted_exposure=position_data["beta_adjusted_exposure"],
        total_delta_exposure=position_data["total_delta_exposure"],
        options_delta_exposure=position_data["options_delta_exposure"],
    )
