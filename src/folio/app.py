import argparse
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dcc, html

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

    # Define layout
    app.layout = dbc.Container(
        [
            html.H2("Folio", className="my-3"),
            create_upload_section() if not portfolio_file else None,
            create_header(),
            create_filters(),
            create_main_table(),
            create_position_modal(),
            dcc.Store(id="portfolio-data"),
            dcc.Store(id="selected-position"),
            dcc.Interval(
                id="interval-component",
                interval=5 * 60 * 1000,  # 5 minutes in milliseconds
                n_intervals=0,
            ),
        ],
        fluid=True,
        className="px-4",
    )

    @app.callback(
        [
            Output("portfolio-data", "data"),
            Output("upload-status", "children"),
        ],
        [
            Input("interval-component", "n_intervals"),
            Input("upload-portfolio", "contents"),
        ],
        [
            State("upload-portfolio", "filename"),
        ],
    )
    def update_portfolio_data(n_intervals, contents, filename):
        """Update portfolio data from CSV file or upload"""
        logger.info("Updating portfolio data")
        try:
            if portfolio_file:
                # Use provided portfolio file
                df = pd.read_csv(portfolio_file)
                logger.debug(f"Read {len(df)} rows from {portfolio_file}")
            elif contents:
                # Handle uploaded file
                import base64
                import io

                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
                logger.debug(f"Read {len(df)} rows from uploaded file {filename}")
                status = html.Div(
                    f"Successfully loaded {filename}", className="text-success"
                )
            else:
                # No data available
                return None, html.Div(
                    "Please upload a portfolio CSV file", className="text-muted"
                )

            # Process data
            groups, summary = process_portfolio_data(df)
            logger.info(f"Processed {len(groups)} portfolio groups")

            # Convert to serializable format
            data = {
                "groups": [
                    {
                        "stock": vars(g.stock_position) if g.stock_position else None,
                        "options": [vars(opt) for opt in g.option_positions],
                        "net_exposure": g.net_exposure,
                        "beta_adjusted_exposure": g.beta_adjusted_exposure,
                        "total_delta_exposure": g.total_delta_exposure,
                        "call_count": g.call_count,
                        "put_count": g.put_count,
                        "net_option_value": g.net_option_value,
                    }
                    for g in groups
                ],
                "summary": vars(summary),
            }
            status = html.Div(
                "Portfolio data loaded successfully", className="text-success"
            )
            return data, status

        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}", exc_info=True)
            status = html.Div(
                f"Error loading portfolio data: {e!s}", className="text-danger"
            )
            return None, status

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
        Input("portfolio-data", "data"),
    )
    def update_summary_cards(data):
        """Update summary cards with latest data"""
        logger.debug("Updating summary cards")
        try:
            if not data or "summary" not in data:
                return ["$0.00"] * 4 + ["0.00β"] * 4

            summary = data["summary"]
            return [
                format_currency(summary["total_value_net"]),
                format_beta(summary["portfolio_beta"]),
                format_currency(summary["long_value"]),
                format_beta(summary["long_portfolio_beta"]),
                format_currency(summary["short_value"]),
                format_beta(summary["short_portfolio_beta"]),
                format_currency(summary["options_delta_exposure"]),
                format_beta(summary["options_beta_adjusted"]),
            ]

        except Exception as e:
            logger.error(f"Error updating summary cards: {e}", exc_info=True)
            return ["$0.00"] * 4 + ["0.00β"] * 4

    @app.callback(
        Output("portfolio-table", "children"),
        [
            Input("portfolio-data", "data"),
            Input("search-input", "value"),
            Input("filter-all", "n_clicks"),
            Input("filter-stocks", "n_clicks"),
            Input("filter-options", "n_clicks"),
        ],
    )
    def update_portfolio_table(data, search, all_clicks, stocks_clicks, options_clicks):
        """Update portfolio table based on filters"""
        logger.debug("Updating portfolio table")
        try:
            if not data or "groups" not in data:
                return html.Tr(
                    html.Td(
                        "No portfolio data available",
                        colSpan=6,
                        className="text-center",
                    )
                )

            # Convert data back to PortfolioGroup objects
            groups = []
            for g in data["groups"]:
                stock_position = Position(**g["stock"]) if g["stock"] else None
                option_positions = [OptionPosition(**opt) for opt in g["options"]]
                group = PortfolioGroup(
                    stock_position=stock_position,
                    option_positions=option_positions,
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
        Input("portfolio-table", "active_cell"),
        State("portfolio-data", "data"),
    )
    def store_selected_position(active_cell, data):
        """Store selected position data when row is clicked"""
        logger.debug("Storing selected position")
        if not active_cell or not data or "groups" not in data:
            return None

        try:
            row = active_cell["row"]
            group_data = data["groups"][row]

            # Convert to PortfolioGroup
            stock_position = (
                Position(**group_data["stock"]) if group_data["stock"] else None
            )
            option_positions = [OptionPosition(**opt) for opt in group_data["options"]]
            group = PortfolioGroup(
                stock_position=stock_position,
                option_positions=option_positions,
            )

            return {
                "stock": vars(group.stock_position) if group.stock_position else None,
                "options": [vars(opt) for opt in group.option_positions],
                "net_exposure": group.net_exposure,
                "beta_adjusted_exposure": group.beta_adjusted_exposure,
                "total_delta_exposure": group.total_delta_exposure,
                "call_count": group.call_count,
                "put_count": group.put_count,
                "net_option_value": group.net_option_value,
            }

        except Exception as e:
            logger.error(f"Error storing selected position: {e}", exc_info=True)
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
        if not position_data:
            return False, None

        try:
            # Convert data back to PortfolioGroup
            stock_position = (
                Position(**position_data["stock"]) if position_data["stock"] else None
            )
            option_positions = [
                OptionPosition(**opt) for opt in position_data["options"]
            ]
            group = PortfolioGroup(
                stock_position=stock_position,
                option_positions=option_positions,
            )

            # Create position details
            return True, create_position_details(group)

        except Exception as e:
            logger.error(f"Error creating position details: {e}", exc_info=True)
            return False, html.Div(
                "Error loading position details",
                className="text-danger",
            )

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
