import argparse
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, dcc, html

from .components.portfolio_table import create_portfolio_table
from .components.position_details import create_position_details
from .data_model import OptionPosition, PortfolioGroup, Position
from .logger import logger
from .utils import (
    format_beta,
    format_currency,
    process_portfolio_data,
)


def create_header() -> dbc.Card:
    """Create the header section with summary cards"""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Portfolio Summary", className="mb-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H6(
                                            "Total Value", className="card-subtitle"
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
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H6(
                                            "Long Exposure", className="card-subtitle"
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
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H6(
                                            "Short Exposure", className="card-subtitle"
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
                            ),
                            width=3,
                        ),
                        dbc.Col(
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
                            ),
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


def create_app(portfolio_file: str = None, debug: bool = False) -> dash.Dash:
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
                )

            # Process portfolio data
            groups, summary = process_portfolio_data(df)
            logger.info(f"Successfully processed {len(groups)} portfolio groups")

            # Convert to Dash-compatible format
            groups_data = [g.to_dict() for g in groups]
            summary_data = summary.to_dict()
            portfolio_data = df.to_dict("records")

            return portfolio_data, summary_data, groups_data, "", status

        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}", exc_info=True)
            error_msg = f"Error loading portfolio: {e!s}"
            error_div = html.Div(error_msg, className="text-danger")
            return [], {}, [], error_msg, error_div

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
        ],
        Input("portfolio-summary", "data"),
    )
    def update_summary_cards(summary_data):
        """Update summary cards with latest data"""
        logger.debug("Updating summary cards")
        try:
            if not summary_data:
                return ["$0.00"] * 4 + ["0.00β"] * 4

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
            ]

        except Exception as e:
            logger.error(f"Error updating summary cards: {e}", exc_info=True)
            return ["$0.00"] * 4 + ["0.00β"] * 4

    @app.callback(
        Output("portfolio-table", "children"),
        [
            Input("portfolio-groups", "data"),
            Input("search-input", "value"),
            Input("filter-all", "n_clicks"),
            Input("filter-stocks", "n_clicks"),
            Input("filter-options", "n_clicks"),
        ],
    )
    def update_portfolio_table(
        groups_data, search, all_clicks, stocks_clicks, options_clicks
    ):
        """Update portfolio table based on filters"""
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

            # Apply filters
            if search:
                search = search.lower()
                groups = [
                    g
                    for g in groups
                    if (
                        (g.stock_position and search in g.stock_position.ticker.lower())
                        or any(
                            search in opt.ticker.lower() for opt in g.option_positions
                        )
                    )
                ]

            # Create table
            return create_portfolio_table(groups)

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
        if not groups_data:
            logger.debug("No portfolio data available for selection")
            return None

        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        logger.debug(f"Trigger ID: {trigger_id}")

        try:
            if "position-details" in trigger_id:
                # Button click
                button_idx = ctx.triggered[0]["prop_id"].split(".")[0]
                try:
                    ticker = eval(button_idx)["index"]
                    logger.debug(f"Button clicked for ticker: {ticker}")
                except Exception as e:
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
                else:
                    logger.error(f"Could not find group for ticker: {ticker}")
                    return None
            else:
                # Table cell click
                if not active_cell:
                    logger.debug("No active cell selected")
                    return None
                row = active_cell["row"]
                logger.debug(f"Table cell clicked at row {row}")

            # Validate row index
            if row < 0 or row >= len(groups_data):
                logger.error(
                    f"Row index out of range: {row}, groups length: {len(groups_data)}"
                )
                return None

            # Return the group data directly since it's already in the right format
            return groups_data[row]

        except Exception as e:
            logger.error(f"Error storing selected position: {e}", exc_info=True)
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @app.callback(
        [
            Output("position-modal", "is_open"),
            Output("position-modal-body", "children"),
        ],
        [
            Input("selected-position", "data"),
            Input("position-modal", "is_open"),
        ],
    )
    def toggle_position_modal(position_data, is_open):
        """Toggle position details modal"""
        logger.debug("Toggling position modal")
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        logger.debug(f"Modal toggle trigger: {trigger_id}")

        if "selected-position" in trigger_id and position_data:
            # If new position data was loaded, open the modal
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

        # Keep modal state unchanged if it's not the selected-position trigger
        logger.debug(f"No action needed, keeping modal state: {is_open}")
        return is_open, dash.no_update

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
