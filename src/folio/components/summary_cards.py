"""Summary cards component for the Folio dashboard.

This module provides the summary cards component for displaying portfolio metrics
at the top of the dashboard. It includes functions for creating the cards and
formatting the values.
"""

import dash_bootstrap_components as dbc
from dash import html

from .. import utils
from ..logger import logger


def error_values():
    """Return error values for summary cards.

    This function provides a consistent set of error values for the summary cards
    when data is missing or invalid.

    Returns:
        Tuple of error formatted values for all summary cards
    """
    return (
        "Error",  # Portfolio Value
        "Error",  # Net Exposure
        "Data missing",  # Net Exposure Percent
        "Error",  # Net Beta
        "Error",  # Long Exposure
        "Data missing",  # Long Exposure Percent
        "Error",  # Long Beta
        "Error",  # Short Exposure
        "Data missing",  # Short Exposure Percent
        "Error",  # Short Beta
        "Error",  # Options Exposure
        "Data missing",  # Options Exposure Percent
        "Error",  # Options Beta
        "Error",  # Cash Value
        "Data missing",  # Cash Percent
    )


def format_summary_card_values(summary_data):
    """Format summary card values from summary data.

    This function takes the portfolio summary data and formats it for display
    in the summary cards. It handles missing values and calculates derived metrics.

    Args:
        summary_data: Dictionary containing portfolio summary data

    Returns:
        Tuple of formatted values for all summary cards
    """
    # Log the entire summary_data for debugging
    logger.info(f"Formatting summary cards with data: {summary_data}")

    # Flag to track if we should return error values
    show_error_values = False

    # Ensure summary_data is a dictionary
    if not summary_data or not isinstance(summary_data, dict):
        logger.error(f"Invalid summary data: {type(summary_data)}")
        show_error_values = True

    if not show_error_values:
        # Check for required keys
        required_keys = [
            "portfolio_estimate_value",
            "net_market_exposure",
            "portfolio_beta",
            "long_exposure",
            "short_exposure",
            "options_exposure",
            "cash_like_value",
        ]
        missing_keys = [key for key in required_keys if key not in summary_data]
        if missing_keys:
            logger.error(f"Missing required keys in summary data: {missing_keys}")

            # Try to fix missing portfolio_estimate_value
            if (
                "portfolio_estimate_value" in missing_keys
                and "net_market_exposure" in summary_data
                and "cash_like_value" in summary_data
            ):
                logger.warning(
                    "portfolio_estimate_value not found in summary data, calculating it"
                )
                # Calculate it as net_market_exposure + cash_like_value
                net_market_exposure = summary_data.get("net_market_exposure", 0.0)
                cash_like_value = summary_data.get("cash_like_value", 0.0)
                summary_data["portfolio_estimate_value"] = (
                    net_market_exposure + cash_like_value
                )
                logger.info(
                    f"Calculated portfolio_estimate_value: {summary_data['portfolio_estimate_value']}"
                )
                # Remove from missing keys if we fixed it
                missing_keys.remove("portfolio_estimate_value")

            # If we still have missing keys, show error values
            if missing_keys:
                logger.error(f"Still missing required keys after fixes: {missing_keys}")
                show_error_values = True

    if not show_error_values:
        # Log all the keys in the summary_data
        logger.info(f"Summary data keys: {list(summary_data.keys())}")

        # Log the specific values we're going to use
        logger.info(
            f"Portfolio estimate value: {summary_data.get('portfolio_estimate_value')}"
        )
        logger.info(f"Net market exposure: {summary_data.get('net_market_exposure')}")
        logger.info(f"Portfolio beta: {summary_data.get('portfolio_beta')}")

        # Validate exposure dictionaries
        for exposure_key in ["long_exposure", "short_exposure", "options_exposure"]:
            if exposure_key not in summary_data:
                logger.error(f"'{exposure_key}' key missing from summary_data")
                show_error_values = True
                break

            if not isinstance(summary_data[exposure_key], dict):
                logger.error(
                    f"'{exposure_key}' is not a dictionary: {type(summary_data[exposure_key])}"
                )
                show_error_values = True
                break

            # Check for required sub-keys - support both old and new field names
            required_sub_keys = []
            if "total_beta_adjusted" not in summary_data[exposure_key]:
                required_sub_keys.append("total_beta_adjusted")

            if required_sub_keys:
                logger.error(
                    f"Missing required sub-keys in {exposure_key}: {required_sub_keys}"
                )
                show_error_values = True
                break

    if show_error_values:
        return error_values()

    # Log exposure values
    # Helper function to get exposure value (supports both total_exposure and total_value field names)
    def get_exposure_value(exposure_dict):
        if "total_exposure" in exposure_dict:
            return exposure_dict["total_exposure"]
        elif "total_value" in exposure_dict:
            return exposure_dict["total_value"]
        return 0.0

    # Log the values we're using
    logger.info(f"Long exposure: {get_exposure_value(summary_data['long_exposure'])}")
    logger.info(
        f"Long beta adjusted: {summary_data['long_exposure'].get('total_beta_adjusted')}"
    )
    logger.info(f"Short exposure: {get_exposure_value(summary_data['short_exposure'])}")
    logger.info(
        f"Short beta adjusted: {summary_data['short_exposure'].get('total_beta_adjusted')}"
    )
    logger.info(
        f"Options exposure: {get_exposure_value(summary_data['options_exposure'])}"
    )
    logger.info(
        f"Options beta adjusted: {summary_data['options_exposure'].get('total_beta_adjusted')}"
    )
    logger.info(f"Cash like value: {summary_data.get('cash_like_value')}")

    # Get values with defaults to prevent KeyError
    portfolio_estimate_value = summary_data.get("portfolio_estimate_value", 0.0)
    net_market_exposure = summary_data.get("net_market_exposure", 0.0)
    portfolio_beta = summary_data.get("portfolio_beta", 0.0)
    cash_like_value = summary_data.get("cash_like_value", 0.0)

    # Get exposure values with defaults
    long_exposure = summary_data.get("long_exposure", {})
    short_exposure = summary_data.get("short_exposure", {})
    options_exposure = summary_data.get("options_exposure", {})

    # Get total exposure values with defaults (supporting both field names)
    long_total_exposure = get_exposure_value(long_exposure)
    long_total_beta_adjusted = long_exposure.get("total_beta_adjusted", 0.0)
    short_total_exposure = get_exposure_value(short_exposure)
    short_total_beta_adjusted = short_exposure.get("total_beta_adjusted", 0.0)
    options_total_exposure = get_exposure_value(options_exposure)
    options_total_beta_adjusted = options_exposure.get("total_beta_adjusted", 0.0)

    # Calculate betas safely
    if not show_error_values:
        try:
            long_beta = (
                long_total_beta_adjusted / long_total_exposure
                if long_total_exposure != 0
                else 0
            )
            short_beta = (
                short_total_beta_adjusted / short_total_exposure
                if short_total_exposure != 0
                else 0
            )
            options_beta = (
                options_total_beta_adjusted / options_total_exposure
                if options_total_exposure != 0
                else 0
            )
        except Exception as e:
            logger.error(f"Error calculating betas: {e}", exc_info=True)
            show_error_values = True

    # Format the values for display
    if not show_error_values:
        try:
            formatted_values = (
                # Portfolio Value
                utils.format_currency(portfolio_estimate_value),
                # Net Exposure
                utils.format_currency(net_market_exposure),
                "",  # Removed percentage
                # Net Beta
                utils.format_beta(portfolio_beta),
                # Long Exposure
                utils.format_currency(long_total_exposure),
                "",  # Removed percentage
                utils.format_beta(long_beta),
                # Short Exposure
                utils.format_currency(short_total_exposure),
                "",  # Removed percentage
                utils.format_beta(short_beta),
                # Options Exposure
                utils.format_currency(options_total_exposure),
                "",  # Removed percentage
                utils.format_beta(options_beta),
                # Cash & Equivalents
                utils.format_currency(cash_like_value),
                "",  # Removed percentage
            )

            # Log the formatted values
            logger.info(f"Formatted values: {formatted_values}")

            return formatted_values
        except Exception as e:
            logger.error(f"Error formatting values: {e}", exc_info=True)
            show_error_values = True

    # If we get here, we need to show error values
    return error_values()


def create_portfolio_value_card():
    """Create the portfolio value card."""
    # Create the portfolio value component
    portfolio_value = html.H5(
        id="portfolio-value",
        className="card-title text-primary",
        children="$0.00",  # Default value
    )

    # Create the card with the portfolio value component nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Portfolio Value",
                            className="card-subtitle",
                        ),
                        portfolio_value,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="portfolio-value-card",
            ),
            dbc.Tooltip(
                "Estimated total portfolio value (Net Market Exposure + Cash).",
                target="portfolio-value-card",
                placement="top",
            ),
        ],
        width=3,
    )


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
        children="",  # Default value
    )

    total_beta = html.P(
        id="total-beta",
        className="card-text text-muted",
        children="0.00β",  # Default value
    )

    # Create the card with the components nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Net Exposure",
                            className="card-subtitle",
                        ),
                        total_value,  # Nest the component here
                        total_value_percent,  # Nest the component here
                        total_beta,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="total-value-card",
            ),
            dbc.Tooltip(
                "Net market exposure (Long - Short). Includes stock positions and option market values.",
                target="total-value-card",
                placement="top",
            ),
        ],
        width=3,
    )


def create_long_exposure_card():
    """Create the long exposure card."""
    # Create the components
    long_exposure = html.H5(
        id="long-exposure",
        className="card-title text-success",
        children="$0.00",  # Default value
    )

    long_exposure_percent = html.P(
        id="long-exposure-percent",
        className="card-text text-muted",
        children="",  # Default value
    )

    long_beta = html.P(
        id="long-beta",
        className="card-text text-muted",
        children="0.00β",  # Default value
    )

    # Create the card with the components nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Long Exposure",
                            className="card-subtitle",
                        ),
                        long_exposure,  # Nest the component here
                        long_exposure_percent,  # Nest the component here
                        long_beta,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="long-exposure-card",
            ),
            dbc.Tooltip(
                "Total long market exposure from stocks and options.",
                target="long-exposure-card",
                placement="top",
            ),
        ],
        width=3,
    )


def create_short_exposure_card():
    """Create the short exposure card."""
    # Create the components
    short_exposure = html.H5(
        id="short-exposure",
        className="card-title text-danger",
        children="$0.00",  # Default value
    )

    short_exposure_percent = html.P(
        id="short-exposure-percent",
        className="card-text text-muted",
        children="",  # Default value
    )

    short_beta = html.P(
        id="short-beta",
        className="card-text text-muted",
        children="0.00β",  # Default value
    )

    # Create the card with the components nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Short Exposure",
                            className="card-subtitle",
                        ),
                        short_exposure,  # Nest the component here
                        short_exposure_percent,  # Nest the component here
                        short_beta,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="short-exposure-card",
            ),
            dbc.Tooltip(
                "Total short market exposure from stocks and options.",
                target="short-exposure-card",
                placement="top",
            ),
        ],
        width=3,
    )


def create_options_exposure_card():
    """Create the options exposure card."""
    # Create the components
    options_exposure = html.H5(
        id="options-exposure",
        className="card-title text-info",
        children="$0.00",  # Default value
    )

    options_exposure_percent = html.P(
        id="options-exposure-percent",
        className="card-text text-muted",
        children="",  # Default value
    )

    options_beta = html.P(
        id="options-beta",
        className="card-text text-muted",
        children="0.00β",  # Default value
    )

    # Create the card with the components nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Options Exposure",
                            className="card-subtitle",
                        ),
                        options_exposure,  # Nest the component here
                        options_exposure_percent,  # Nest the component here
                        options_beta,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="options-exposure-card",
            ),
            dbc.Tooltip(
                "Net delta exposure from all options (Long - Short).",
                target="options-exposure-card",
                placement="top",
            ),
        ],
        width=3,
    )


def create_cash_card():
    """Create the cash card."""
    # Create the components
    cash_like_value = html.H5(
        id="cash-like-value",
        className="card-title text-secondary",
        children="$0.00",  # Default value
    )

    cash_like_percent = html.P(
        id="cash-like-percent",
        className="card-text text-muted",
        children="",  # Default value
    )

    # Create the card with the components nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Cash & Equivalents",
                            className="card-subtitle",
                        ),
                        cash_like_value,  # Nest the component here
                        cash_like_percent,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="cash-like-card",
            ),
            dbc.Tooltip(
                "Total value of cash and cash-equivalent positions.",
                target="cash-like-card",
                placement="top",
            ),
        ],
        width=3,
    )


def create_summary_cards():
    """Create the header section with summary cards.

    Returns:
        dbc.Card: A card containing all summary cards
    """
    logger.info("Creating summary cards")

    # Create the portfolio value card with the ID directly in the parent component
    portfolio_value_card = dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Portfolio Value",
                            className="card-subtitle",
                        ),
                        html.H5(
                            id="portfolio-value",
                            className="card-title text-primary",
                        ),
                    ]
                ),
                className="mb-3",
                id="portfolio-value-card",
            ),
            dbc.Tooltip(
                "Estimated total portfolio value (Net Market Exposure + Cash).",
                target="portfolio-value-card",
                placement="top",
            ),
        ],
        width=3,
    )

    # Create the net exposure card with the ID directly in the parent component
    net_exposure_card = create_net_exposure_card()

    # Create the long exposure card with the ID directly in the parent component
    long_exposure_card = create_long_exposure_card()

    # Create the short exposure card with the ID directly in the parent component
    short_exposure_card = create_short_exposure_card()

    # Create the options exposure card with the ID directly in the parent component
    options_exposure_card = create_options_exposure_card()

    # Create the cash card with the ID directly in the parent component
    cash_card = create_cash_card()

    # Create the summary card with all the components nested inside it
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Portfolio Summary", className="mb-3"),
                dbc.Row(
                    [
                        portfolio_value_card,
                        net_exposure_card,
                        long_exposure_card,
                        short_exposure_card,
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        options_exposure_card,
                        cash_card,
                        # Empty columns to balance the row
                        dbc.Col(width=3),
                        dbc.Col(width=3),
                    ],
                    className="mb-3",
                ),
            ]
        ),
        className="mb-3",
        id="summary-card",
    )


def register_callbacks(app):
    """Register callbacks for summary cards.

    Args:
        app: The Dash app
    """
    logger.info("Registering summary cards callbacks")
    # Debug logging for callback registration
    logger.debug(
        f"Callback map before summary cards registration: {len(app.callback_map)} callbacks"
    )

    from dash import Input, Output

    @app.callback(
        [
            Output("portfolio-value", "children"),
            Output("total-value", "children"),
            Output("total-value-percent", "children"),
            Output("total-beta", "children"),
            Output("long-exposure", "children"),
            Output("long-exposure-percent", "children"),
            Output("long-beta", "children"),
            Output("short-exposure", "children"),
            Output("short-exposure-percent", "children"),
            Output("short-beta", "children"),
            Output("options-exposure", "children"),
            Output("options-exposure-percent", "children"),
            Output("options-beta", "children"),
            Output("cash-like-value", "children"),
            Output("cash-like-percent", "children"),
        ],
        [Input("portfolio-summary", "data")],
        # Prevent initial call to avoid errors when data is not yet loaded
        prevent_initial_call=False,
    )
    def update_summary_cards(summary_data):
        """Update summary cards with latest data"""
        logger.info("Updating summary cards")
        logger.info(f"Summary data type: {type(summary_data)}")

        # Log the structure of the summary data
        if summary_data:
            logger.info("Summary data keys: %s", list(summary_data.keys()))
            for key in summary_data.keys():
                if isinstance(summary_data[key], dict):
                    logger.info(f"  {key} (dict): {list(summary_data[key].keys())}")
                elif isinstance(summary_data[key], list):
                    logger.info(f"  {key} (list): {len(summary_data[key])} items")
                else:
                    logger.info(f"  {key}: {summary_data[key]}")
        else:
            logger.warning("No summary data available, returning error values")
            return error_values()

        try:
            # Call the format function
            formatted_values = format_summary_card_values(summary_data)

            # Log the formatted values
            logger.info(f"Formatted summary card values: {formatted_values}")

            return formatted_values
        except Exception as e:
            # Log the error with full stack trace
            logger.error(f"Error in update_summary_cards: {e}", exc_info=True)
            return error_values()

    # Debug logging for callback registration
    logger.debug(
        f"Callback map after summary cards registration: {len(app.callback_map)} callbacks"
    )
