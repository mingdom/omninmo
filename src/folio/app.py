import argparse
import sys
from pathlib import Path
from typing import Optional

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, dcc, html

from .components.portfolio_table import create_portfolio_table
from .components.position_details import create_position_details
from .data_model import OptionPosition, PortfolioGroup, Position, StockPosition
from .logger import logger
from .utils import format_beta, format_currency, process_portfolio_data


def create_header() -> dbc.Card:
    """Create the header section with summary cards"""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Portfolio Summary", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Total Exposure", className="card-subtitle"
                                            ),
                                            html.H5(
                                                id="total-value",
                                                className="card-title text-primary",
                                            ),
                                            html.P(
                                                id="total-beta",
                                                className="card-text text-muted",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                    id="total-value-card",
                                ),
                                dbc.Tooltip(
                                    "Net portfolio value (Long - Short). Includes stock positions and option market values.",
                                    target="total-value-card",
                                    placement="top",
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Long Exposure",
                                                className="card-subtitle",
                                            ),
                                            html.H5(
                                                id="long-exposure",
                                                className="card-title text-success",
                                            ),
                                            html.P(
                                                id="long-beta",
                                                className="card-text text-muted",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                    id="long-exposure-card",
                                ),
                                dbc.Tooltip(
                                    "Long market exposure from stocks and options. Includes long stock positions, long call options (delta-adjusted), and short put options (delta-adjusted).",
                                    target="long-exposure-card",
                                    placement="top",
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Short Exposure",
                                                className="card-subtitle",
                                            ),
                                            html.H5(
                                                id="short-exposure",
                                                className="card-title text-danger",
                                            ),
                                            html.P(
                                                id="short-beta",
                                                className="card-text text-muted",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                    id="short-exposure-card",
                                ),
                                dbc.Tooltip(
                                    "Short market exposure from stocks and options. Includes short stock positions, short call options (delta-adjusted), and long put options (delta-adjusted).",
                                    target="short-exposure-card",
                                    placement="top",
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Options Exposure",
                                                className="card-subtitle",
                                            ),
                                            html.H5(
                                                id="options-exposure",
                                                className="card-title text-info",
                                            ),
                                            html.P(
                                                id="options-beta",
                                                className="card-text text-muted",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                    id="options-exposure-card",
                                ),
                                dbc.Tooltip(
                                    "Option positions' market exposure. For calls: +delta * notional for long, -delta * notional for short. For puts: -delta * notional for long, +delta * notional for short.",
                                    target="options-exposure-card",
                                    placement="top",
                                ),
                            ],
                            width=3,
                        ),
                    ]
                ),
                # Add a new row for cash-like positions
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Cash-Like Positions",
                                                className="card-subtitle",
                                            ),
                                            html.H5(
                                                id="cash-like-value",
                                                className="card-title text-info",
                                            ),
                                            html.P(
                                                id="cash-like-percent",
                                                className="card-text text-muted",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                    id="cash-like-card",
                                ),
                                dbc.Tooltip(
                                    "Positions with very low beta (< 0.1). Includes money market funds, short-term treasuries, and other cash-like instruments.",
                                    target="cash-like-card",
                                    placement="top",
                                ),
                            ],
                            width=3,
                        ),
                    ]
                ),
            ]
        ),
        className="mb-3",
    )


def create_upload_section() -> dbc.Card:
    """Create the file upload section"""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Upload Portfolio", className="mb-3"),
                dcc.Upload(
                    id="upload-portfolio",
                    children=html.Div(
                        [
                            "Drag and Drop or ",
                            html.A("Select a CSV File", className="text-primary"),
                        ]
                    ),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px 0",
                    },
                    # Filter for CSV files
                    accept=".csv",
                    multiple=False,
                ),
                html.Div(id="upload-status"),
            ]
        ),
        className="mb-3",
    )


def create_filters() -> dbc.InputGroup:
    """Create the search and filter controls"""
    return dbc.InputGroup(
        [
            dbc.Input(
                id="search-input",
                type="text",
                placeholder="Search positions...",
                className="border-end-0",
            ),
            dbc.InputGroupText(
                html.I(className="fas fa-search"),
                className="bg-transparent border-start-0",
            ),
            dbc.Button(
                "All",
                id="filter-all",
                color="primary",
                outline=True,
                className="ms-2",
            ),
            dbc.Button(
                "Stocks",
                id="filter-stocks",
                color="primary",
                outline=True,
                className="ms-2",
            ),
            dbc.Button(
                "Options",
                id="filter-options",
                color="primary",
                outline=True,
                className="ms-2",
            ),
            dbc.Button(
                "Cash",
                id="filter-cash",
                color="primary",
                outline=True,
                className="ms-2",
            ),
        ],
        className="mb-3",
    )


def create_main_table() -> html.Div:
    """Create the main portfolio table"""
    return html.Div(
        [
            dbc.Table(
                id="portfolio-table",
                className="portfolio-table",
            ),
            # Add a Store to track sort state
            dcc.Store(id="sort-state", data={"column": "value", "direction": "desc"}),
        ]
    )


def create_position_modal() -> dbc.Modal:
    """Create the position details modal"""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Position Details"),
                close_button=True,
            ),
            dbc.ModalBody(id="position-modal-body"),
        ],
        id="position-modal",
        size="lg",
    )


def create_app(portfolio_file: Optional[str] = None, debug: bool = False) -> dash.Dash:
    """Create and configure the Dash application"""
    logger.info("Initializing Dash application")

    # Create Dash app
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
        ],
        title="Folio",
    )

    # Define custom CSS
    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                .sort-header:hover {
                    background-color: rgba(0,0,0,0.05);
                }
                .sort-header {
                    transition: background-color 0.2s;
                    padding: 8px 4px;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """

    # Store portfolio file path
    app.portfolio_file = portfolio_file
    logger.info(f"Portfolio file path set to: {portfolio_file}")

    # Define layout
    app.layout = dbc.Container(
        [
            dcc.Location(id="url", refresh=False),  # Add URL component
            html.H2("Folio", className="my-3"),
            create_upload_section(),  # Always show upload section
            create_header(),
            create_filters(),
            create_main_table(),
            create_position_modal(),
            dcc.Store(id="portfolio-data"),
            dcc.Store(id="portfolio-summary"),  # Add portfolio summary store
            dcc.Store(id="portfolio-groups"),  # Add portfolio groups store
            dcc.Store(id="selected-position"),
            dcc.Store(id="loading-output"),  # Add loading output store
            dcc.Interval(
                id="interval-component",
                interval=5 * 60 * 1000,  # 5 minutes in milliseconds
                n_intervals=0,
            ),
            # Add initial trigger
            dcc.Store(id="initial-trigger", data=True),
        ],
        fluid=True,
        className="px-4",
    )

    # Add clientside callback to ensure initial trigger fires
    app.clientside_callback(
        """
        function(pathname) {
            return true;
        }
        """,
        Output("initial-trigger", "data"),
        Input("url", "pathname"),
    )

    @app.callback(
        [
            Output("portfolio-data", "data"),
            Output("portfolio-summary", "data"),
            Output("portfolio-groups", "data"),
            Output("loading-output", "children"),
            Output("upload-status", "children"),
            Output("portfolio-table", "active_cell"),
        ],
        [
            Input("initial-trigger", "data"),
            Input("url", "pathname"),
            Input("upload-portfolio", "contents"),
        ],
        [
            State("upload-portfolio", "filename"),
        ],
    )
    def update_portfolio_data(initial_trigger, pathname, contents, filename):
        """Update portfolio data when triggered"""
        try:
            logger.info("Loading portfolio data...")
            ctx = dash.callback_context
            trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
            logger.info(f"Trigger: {trigger_id}")

            # Handle file upload if provided
            if contents and "upload-portfolio.contents" in trigger_id:
                import base64
                import io

                logger.info(f"Processing uploaded file: {filename}")
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
                logger.info(
                    f"Successfully read {len(df)} rows from uploaded file {filename}"
                )
                status = html.Div(
                    f"Successfully loaded {filename}", className="text-success"
                )
            elif app.portfolio_file:
                # Use default portfolio file
                df = pd.read_csv(app.portfolio_file)
                logger.info(f"Successfully read {len(df)} rows from portfolio file")
                status = html.Div(
                    "Using default portfolio file", className="text-muted"
                )
            else:
                # No data available
                return (
                    [],
                    {},
                    [],
                    "",
                    html.Div("Please upload a portfolio file", className="text-muted"),
                    None,
                )

            # Process portfolio data
            groups, summary, cash_like_positions = process_portfolio_data(df)
            logger.info(f"Successfully processed {len(groups)} portfolio groups and {len(cash_like_positions)} cash-like positions")

            # Convert to Dash-compatible format
            groups_data = [g.to_dict() for g in groups]
            summary_data = summary.to_dict()
            portfolio_data = df.to_dict("records")

            return portfolio_data, summary_data, groups_data, "", status, None

        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}", exc_info=True)
            error_msg = f"Error loading portfolio: {e!s}"
            error_div = html.Div(error_msg, className="text-danger")
            return [], {}, [], error_msg, error_div, None

    @app.callback(
        [
            Output("total-value", "children"),
            Output("total-beta", "children"),
            Output("long-exposure", "children"),
            Output("long-beta", "children"),
            Output("short-exposure", "children"),
            Output("short-beta", "children"),
            Output("options-exposure", "children"),
            Output("options-beta", "children"),
            Output("cash-like-value", "children"),
            Output("cash-like-percent", "children"),
        ],
        Input("portfolio-summary", "data"),
    )
    def update_summary_cards(summary_data):
        """Update summary cards with latest data"""
        logger.debug("Updating summary cards")
        try:
            if not summary_data:
                return ["$0.00"] * 4 + ["0.00β"] * 4 + ["$0.00", "0.0%"]

            # Calculate cash-like percentage
            cash_like_percent = (
                summary_data["cash_like_value"] / summary_data["total_value_abs"] * 100
                if summary_data["total_value_abs"] != 0
                else 0.0
            )

            return [
                format_currency(summary_data["total_value_net"]),
                format_beta(summary_data["portfolio_beta"]),
                format_currency(summary_data["long_exposure"]["total_value"]),
                format_beta(
                    summary_data["long_exposure"]["total_beta_adjusted"]
                    / summary_data["long_exposure"]["total_value"]
                    if summary_data["long_exposure"]["total_value"] != 0
                    else 0
                ),
                format_currency(summary_data["short_exposure"]["total_value"]),
                format_beta(
                    summary_data["short_exposure"]["total_beta_adjusted"]
                    / summary_data["short_exposure"]["total_value"]
                    if summary_data["short_exposure"]["total_value"] != 0
                    else 0
                ),
                format_currency(summary_data["options_exposure"]["total_value"]),
                format_beta(
                    summary_data["options_exposure"]["total_beta_adjusted"]
                    / summary_data["options_exposure"]["total_value"]
                    if summary_data["options_exposure"]["total_value"] != 0
                    else 0
                ),
                format_currency(summary_data["cash_like_value"]),
                f"{cash_like_percent:.1f}%",
            ]

        except Exception as e:
            logger.error(f"Error updating summary cards: {e}", exc_info=True)
            return ["$0.00"] * 4 + ["0.00β"] * 4 + ["$0.00", "0.0%"]

    @app.callback(
        Output("portfolio-table", "children"),
        [
            Input("portfolio-groups", "data"),
            Input("search-input", "value"),
            Input("filter-all", "n_clicks"),
            Input("filter-stocks", "n_clicks"),
            Input("filter-options", "n_clicks"),
            Input("filter-cash", "n_clicks"),
            Input("sort-state", "data"),  # Add sort state input
        ],
        [State("portfolio-summary", "data")],  # Add portfolio summary as state
    )
    def update_portfolio_table(
        groups_data, search, all_clicks, stocks_clicks, options_clicks, cash_clicks, sort_state, summary_data
    ):
        """Update portfolio table based on filters and sorting"""
        logger.debug("Updating portfolio table")
        try:
            if not groups_data:
                return html.Tr(
                    html.Td(
                        "No portfolio data available",
                        colSpan=6,
                        className="text-center",
                    )
                )

            # Convert data back to PortfolioGroup objects
            groups = []
            for g in groups_data:
                stock_position = (
                    Position(**g["stock_position"]) if g["stock_position"] else None
                )
                option_positions = [
                    OptionPosition(**opt) for opt in g["option_positions"]
                ]
                group = PortfolioGroup(
                    ticker=g["ticker"],
                    stock_position=stock_position,
                    option_positions=option_positions,
                    total_value=g["total_value"],
                    net_exposure=g["net_exposure"],
                    beta=g["beta"],
                    beta_adjusted_exposure=g["beta_adjusted_exposure"],
                    total_delta_exposure=g["total_delta_exposure"],
                    options_delta_exposure=g["options_delta_exposure"],
                )
                groups.append(group)

            # Determine which filter button was clicked
            ctx = dash.callback_context
            if ctx.triggered:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]
                logger.debug(f"Filter button clicked: {button_id}")
            else:
                button_id = "filter-all"  # Default to showing all

            # Get cash-like positions from summary data
            cash_like_positions = []
            if summary_data and "cash_like_positions" in summary_data:
                # Convert cash-like positions to PortfolioGroup objects
                for pos in summary_data["cash_like_positions"]:
                    # Create a StockPosition
                    stock_pos = StockPosition(
                        ticker=pos["ticker"],
                        quantity=pos["quantity"],
                        market_value=pos["market_value"],
                        beta=pos["beta"],
                        beta_adjusted_exposure=pos["beta_adjusted_exposure"]
                    )

                    # Create a PortfolioGroup with just this stock position
                    cash_group = PortfolioGroup(
                        ticker=pos["ticker"],
                        stock_position=stock_pos,
                        option_positions=[],
                        total_value=pos["market_value"],
                        net_exposure=pos["market_value"],
                        beta=pos["beta"],
                        beta_adjusted_exposure=pos["beta_adjusted_exposure"],
                        total_delta_exposure=0.0,
                        options_delta_exposure=0.0
                    )
                    cash_like_positions.append(cash_group)

            # Apply filters based on button clicked
            filtered_groups = []
            if button_id == "filter-all":
                # Include all positions (including cash-like)
                filtered_groups = groups + cash_like_positions
            elif button_id == "filter-stocks":
                # Only include groups with stock positions (excluding cash-like)
                filtered_groups = [g for g in groups if g.stock_position]
            elif button_id == "filter-options":
                # Only include groups with option positions
                filtered_groups = [g for g in groups if g.option_positions]
            elif button_id == "filter-cash":
                # Only include cash-like positions
                filtered_groups = cash_like_positions
            else:
                # Default to all positions
                filtered_groups = groups + cash_like_positions

            # Apply search filter if provided
            if search:
                search = search.lower()
                filtered_groups = [
                    g
                    for g in filtered_groups
                    if (
                        (g.stock_position and search in g.stock_position.ticker.lower())
                        or any(
                            search in opt.ticker.lower() for opt in g.option_positions
                        )
                    )
                ]

            # Get sort information
            sort_column = sort_state.get("column", "value")
            sort_direction = sort_state.get("direction", "desc")
            sort_by = f"{sort_column}-{sort_direction}"

            # Create table with sorting applied
            return create_portfolio_table(filtered_groups, search, sort_by)

        except Exception as e:
            logger.error(f"Error updating portfolio table: {e}", exc_info=True)
            return html.Tr(
                html.Td(
                    "Error loading portfolio data",
                    colSpan=6,
                    className="text-center text-danger",
                )
            )

    @app.callback(
        Output("selected-position", "data"),
        [
            Input("portfolio-table", "active_cell"),
            Input({"type": "position-details", "index": ALL}, "n_clicks"),
        ],
        [
            State("portfolio-groups", "data"),
            State("portfolio-table", "active_cell"),
        ],
    )
    def store_selected_position(active_cell, btn_clicks, groups_data, prev_active_cell):
        """Store selected position data when row is clicked or Details button is clicked"""
        logger.debug("Storing selected position")
        position_data = None

        if groups_data:
            ctx = dash.callback_context
            trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
            logger.debug(f"Trigger ID: {trigger_id}")

            try:
                row = None

                if "position-details" in trigger_id:
                    # Button click
                    button_idx = ctx.triggered[0]["prop_id"].split(".")[0]
                    try:
                        # Parse the button index JSON-like string without using eval
                        # Example format: {"type":"position-details","index":"AAPL"}
                        if not button_idx or not button_idx.startswith("{"):
                            logger.error(f"Invalid button index format: {button_idx}")
                            return None

                        # Extract the index part safely using string manipulation
                        import json

                        button_data = json.loads(button_idx.replace("'", '"'))
                        ticker = button_data.get("index")

                        if not ticker:
                            logger.error("No ticker found in button data")
                            return None

                        logger.debug(f"Button clicked for ticker: {ticker}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(
                            f"Error parsing button index: {e}, button_idx: {button_idx}"
                        )
                        return None

                    # Find the group with matching ticker
                    for i, group_data in enumerate(groups_data):
                        try:
                            stock_ticker = (
                                group_data["stock_position"]["ticker"]
                                if group_data["stock_position"]
                                else None
                            )
                            option_tickers = [
                                opt["ticker"] for opt in group_data["option_positions"]
                            ]

                            if stock_ticker == ticker or ticker in option_tickers:
                                row = i
                                logger.debug(
                                    f"Found matching position at row {row} for ticker {ticker}"
                                )
                                break
                        except Exception as e:
                            logger.error(f"Error processing group {i}: {e}")
                            continue
                elif active_cell and active_cell != prev_active_cell:
                    row = active_cell["row"]
                    logger.debug(f"Table cell clicked at row {row}")

                # Validate and return row data if found
                if row is not None and 0 <= row < len(groups_data):
                    position_data = groups_data[row]
                else:
                    logger.error(
                        f"Row index out of range or not found: {row}, groups length: {len(groups_data)}"
                    )

            except Exception as e:
                logger.error(f"Error storing selected position: {e}", exc_info=True)
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.debug("No portfolio data available for selection")

        return position_data

    @app.callback(
        [
            Output("position-modal", "is_open"),
            Output("position-modal-body", "children"),
        ],
        [
            Input("selected-position", "data"),
            Input("position-modal", "is_open"),
        ],
        [
            State("portfolio-table", "active_cell"),
            State({"type": "position-details", "index": ALL}, "n_clicks"),
        ],
    )
    def toggle_position_modal(position_data, is_open, active_cell, btn_clicks):
        """Toggle position details modal"""
        logger.debug("Toggling position modal")
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        logger.debug(f"Modal toggle trigger: {trigger_id}")

        # If modal is open and we click outside, close it
        if is_open and "position-modal.is_open" in trigger_id:
            return False, dash.no_update

        # Only open modal if position data changed AND it was from a user action
        if "selected-position" in trigger_id and position_data:
            # Check if this was triggered by a user action (either button click or cell click)
            was_button_click = any(n for n in btn_clicks if n)  # Any button was clicked
            was_cell_click = active_cell is not None  # Cell was clicked

            if not (was_button_click or was_cell_click):
                logger.debug("Position data changed but not from user action")
                return False, dash.no_update

            logger.debug(
                f"Position data received: {position_data.keys() if position_data else None}"
            )
            try:
                # Convert data back to PortfolioGroup
                if not position_data:
                    logger.error("Position data is None")
                    return False, html.Div(
                        "No position data available", className="text-danger p-3"
                    )

                stock_position = (
                    Position(**position_data["stock_position"])
                    if position_data["stock_position"]
                    else None
                )
                option_positions = [
                    OptionPosition(**opt) for opt in position_data["option_positions"]
                ]
                group = PortfolioGroup(
                    ticker=position_data["ticker"],
                    stock_position=stock_position,
                    option_positions=option_positions,
                    total_value=position_data["total_value"],
                    net_exposure=position_data["net_exposure"],
                    beta=position_data["beta"],
                    beta_adjusted_exposure=position_data["beta_adjusted_exposure"],
                    total_delta_exposure=position_data["total_delta_exposure"],
                    options_delta_exposure=position_data["options_delta_exposure"],
                )
                logger.debug("Successfully created PortfolioGroup from position data")

                # Create position details
                details = create_position_details(group)
                logger.debug("Successfully created position details")
                return True, details

            except Exception as e:
                logger.error(f"Error creating position details: {e}", exc_info=True)
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                return True, html.Div(
                    f"Error loading position details: {e!s}",
                    className="text-danger p-3",
                )

        # Keep modal state unchanged for all other cases
        logger.debug(f"No action needed, keeping modal state: {is_open}")
        return is_open, dash.no_update

    # Add callback to handle column sorting
    @app.callback(
        Output("sort-state", "data"),
        [Input({"type": "sort-header", "column": ALL}, "n_clicks")],
        [State("sort-state", "data")],
    )
    def update_sort_state(header_clicks, current_sort_state):
        """Update sort state when a column header is clicked"""
        ctx = dash.callback_context

        if not ctx.triggered:
            return current_sort_state

        trigger_id = ctx.triggered[0]["prop_id"]
        if not trigger_id or "sort-header" not in trigger_id:
            return current_sort_state

        # Extract column name from trigger ID (in format {"type":"sort-header","column":"value"}.n_clicks)
        import json

        column_data = json.loads(trigger_id.split(".")[0])
        clicked_column = column_data.get("column")

        if not clicked_column:
            return current_sort_state

        # Update sort direction if same column clicked, otherwise reset to descending
        if clicked_column == current_sort_state.get("column"):
            new_direction = (
                "asc" if current_sort_state.get("direction") == "desc" else "desc"
            )
        else:
            new_direction = "desc"

        return {"column": clicked_column, "direction": new_direction}

    return app


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Folio - Portfolio Dashboard")
    parser.add_argument(
        "--portfolio",
        type=str,
        help="Path to portfolio CSV file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port to run the server on",
    )
    args = parser.parse_args()

    # Validate portfolio file if provided
    portfolio_file = None
    if args.portfolio:
        portfolio_file = Path(args.portfolio)
        if not portfolio_file.exists():
            logger.error(f"Portfolio file not found: {portfolio_file}")
            return 1
        portfolio_file = str(portfolio_file)

    # Create and run app
    app = create_app(portfolio_file, args.debug)
    app.run_server(debug=args.debug, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
