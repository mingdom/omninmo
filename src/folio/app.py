import argparse
import base64
import io
import os
import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, dcc, html

# Import portfolio processing functions
# Import utility functions
from . import portfolio, utils
from .callbacks.chart_callbacks import register_chart_callbacks

# Import AI utilities directly
# Import components
from .components import create_premium_chat_component, register_premium_chat_callbacks
from .components.charts import create_dashboard_section
from .components.portfolio_table import create_portfolio_table
from .components.position_details import create_position_details
from .data_model import OptionPosition, PortfolioGroup, Position, StockPosition
from .error_utils import handle_callback_error
from .exceptions import StateError
from .logger import logger
from .security import sanitize_dataframe, validate_csv_upload


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
                                                "Total Exposure",
                                                className="card-subtitle",
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


def create_empty_state() -> html.Div:
    """Create the empty state with instructions"""
    return html.Div(
        [
            html.H4("Welcome to Folio", className="text-center mb-3"),
            html.P(
                "Upload your portfolio CSV file to get started", className="text-center"
            ),
            html.Div(
                [
                    html.I(className="fas fa-upload fa-3x"),
                ],
                className="text-center my-4",
            ),
            html.P(
                "Or try a sample portfolio to explore the features",
                className="text-center mt-3",
            ),
            dbc.Button(
                "Load Sample Portfolio",
                id="load-sample",
                color="primary",
                className="mx-auto d-block",
            ),
            # Keyboard shortcut hint removed
        ],
        className="empty-state py-5",
    )


def create_upload_section() -> dbc.Card:
    """Create the file upload section with collapsible functionality"""
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-upload me-2"),
                        "Upload Portfolio",
                        html.I(
                            className="fas fa-chevron-down ms-2", id="collapse-icon"
                        ),
                    ],
                    id="upload-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center",
                ),
                className="d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        dcc.Upload(
                            id="upload-portfolio",
                            children=html.Div(
                                [
                                    html.I(className="fas fa-file-upload me-2"),
                                    "Drag and Drop or ",
                                    html.A(
                                        "Select a CSV File", className="text-primary"
                                    ),
                                ]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "textAlign": "center",
                                "margin": "10px 0",
                            },
                            # Filter for CSV files
                            accept=".csv",
                            multiple=False,
                        ),
                        dcc.Loading(
                            id="upload-loading",
                            type="circle",
                            children=[html.Div(id="upload-status")],
                        ),
                    ]
                ),
                id="upload-collapse",
                is_open=True,  # Initially open
            ),
        ],
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


def create_app(portfolio_file: str | None = None, _debug: bool = False) -> dash.Dash:
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
        # Enable async callbacks
        use_pages=False,
        suppress_callback_exceptions=True,
    )

    # Enhanced UI CSS is automatically loaded from the assets folder

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
                kbd {
                    display: inline-block;
                    padding: 0.2em 0.4em;
                    font-size: 0.85em;
                    font-weight: 700;
                    line-height: 1;
                    color: #fff;
                    background-color: #212529;
                    border-radius: 0.2rem;
                    box-shadow: 0 2px 0 rgba(0,0,0,0.2);
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
            html.Div(html.H2("Folio"), className="app-header my-3"),
            create_upload_section(),  # Always show upload section
            # Wrap the main content in a loading component with gradient border
            html.Div(
                dcc.Loading(
                    id="main-loading",
                    type="circle",
                    children=[
                        html.Div(
                            [
                                # Add visualization dashboard section near the top
                                create_dashboard_section(),
                                # Add filters below visualizations
                                create_filters(),
                                # Move table to the end
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-table me-2"
                                                    ),
                                                    "Portfolio Positions",
                                                    html.I(
                                                        className="fas fa-chevron-down ms-2",
                                                        id="positions-collapse-icon",
                                                    ),
                                                ],
                                                id="positions-collapse-button",
                                                color="link",
                                                className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                                            ),
                                        ),
                                        dbc.Collapse(
                                            dbc.CardBody(
                                                create_main_table(),
                                            ),
                                            id="positions-collapse",
                                            is_open=True,  # Initially open
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ],
                            id="main-content",
                        )
                    ],
                ),
                className="gradient-border",
            ),
            create_position_modal(),
            # Empty state container (shown when no data is loaded)
            html.Div(id="empty-state-container"),
            # Add keyboard shortcut listener
            html.Div(id="keyboard-shortcut-listener"),
            # Premium AI Chat Interface
            create_premium_chat_component(),
            # AI Modal
            dbc.Modal(
                [
                    dbc.ModalHeader("AI Portfolio Advisor"),
                    dbc.ModalBody(
                        [
                            html.P("What would you like to know about your portfolio?"),
                            dbc.Textarea(
                                id="ai-query-input",
                                placeholder="Ask about your portfolio...",
                                rows=3,
                                className="mb-3",
                            ),
                            dbc.Button(
                                "Analyze",
                                id="analyze-portfolio-button",
                                color="primary",
                                className="mb-3",
                            ),
                            html.Div(id="ai-analysis-result"),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="close-ai-modal",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="ai-modal",
                size="lg",
                is_open=False,
            ),
            # Stores
            dcc.Store(id="portfolio-data"),
            dcc.Store(id="portfolio-summary"),  # Add portfolio summary store
            dcc.Store(id="portfolio-groups"),  # Add portfolio groups store
            dcc.Store(id="selected-position"),
            dcc.Store(id="loading-output"),  # Add loading output store
            dcc.Store(id="theme-store", storage_type="local"),  # Theme preference store
            dcc.Store(id="ai-analysis-data"),  # Store for AI analysis results
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

    # Keyboard shortcut functionality removed as it was causing issues

    # Toggle upload section collapse
    @app.callback(
        [
            Output("upload-collapse", "is_open", allow_duplicate=True),
            Output("collapse-icon", "className"),
        ],
        [Input("upload-collapse-button", "n_clicks")],
        [State("upload-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_upload_collapse(n_clicks, is_open):
        """Toggle the upload section collapse state"""
        if n_clicks:
            # Toggle the collapse state
            new_state = not is_open
            # Update the icon based on the new state
            icon_class = (
                "fas fa-chevron-up ms-2" if new_state else "fas fa-chevron-down ms-2"
            )
            return new_state, icon_class
        return is_open, "fas fa-chevron-down ms-2"

    # Show/hide empty state based on portfolio data
    @app.callback(
        [
            Output("empty-state-container", "children"),
            Output("main-content", "style"),
            # Also collapse the upload section when data is loaded
            Output("upload-collapse", "is_open"),
        ],
        [Input("portfolio-groups", "data")],
    )
    def toggle_empty_state(groups_data):
        """Show empty state when no data is loaded and collapse upload section when data is loaded"""
        logger.info(f"TOGGLE_EMPTY_STATE called with groups_data: {bool(groups_data)}")

        if not groups_data:
            # No data, show empty state, hide main content, keep upload open
            logger.info(
                "TOGGLE_EMPTY_STATE: No data, showing empty state, hiding main content"
            )
            return create_empty_state(), {"display": "none"}, True
        else:
            # Data loaded, hide empty state, show main content, collapse upload
            logger.info(
                "TOGGLE_EMPTY_STATE: Data loaded, hiding empty state, showing main content"
            )
            return None, {"display": "block"}, False

    # Handle sample portfolio loading
    @app.callback(
        [
            Output("upload-portfolio", "contents"),
            Output("upload-portfolio", "filename"),
        ],
        Input("load-sample", "n_clicks"),
        prevent_initial_call=True,
    )
    def load_sample_portfolio(n_clicks):
        """Load a sample portfolio when the button is clicked"""
        logger.info(f"LOAD_SAMPLE_PORTFOLIO: Button clicked: {n_clicks}")
        if n_clicks:
            logger.info("LOAD_SAMPLE_PORTFOLIO: Processing sample portfolio")
            try:
                # Path to sample portfolio in assets directory
                sample_path = Path(__file__).parent / "assets" / "sample-portfolio.csv"
                logger.info(f"Looking for sample portfolio at: {sample_path}")

                if not sample_path.exists():
                    logger.warning(f"Sample portfolio not found at {sample_path}")
                    return None, None

                logger.info(f"Sample portfolio found at: {sample_path}")

                # Debug the file content
                with open(sample_path) as f:
                    content = f.read()
                    logger.info(
                        f"Sample portfolio content (first 100 chars): {content[:100]}"
                    )

                # Read the sample portfolio file
                with open(sample_path, "rb") as f:
                    file_content = f.read()
                    logger.info(
                        f"Read {len(file_content)} bytes from sample portfolio file"
                    )

                # Validate the sample file content
                # We'll sanitize it during the normal processing flow
                df = pd.read_csv(sample_path)

                # Check for any potentially dangerous content
                df = sanitize_dataframe(df)

                # Re-encode the sanitized dataframe
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_str = csv_buffer.getvalue()

                # Encode the content as base64 for the upload component
                content_type = "text/csv"
                content_string = base64.b64encode(csv_str.encode("utf-8")).decode(
                    "utf-8"
                )

                # Return both the contents and the filename
                return (
                    f"data:{content_type};base64,{content_string}",
                    "sample-portfolio.csv",
                )
            except Exception as e:
                logger.error(f"Error loading sample portfolio: {e}", exc_info=True)
                return None, None
        return None, None

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
    def update_portfolio_data(_initial_trigger, _pathname, contents, filename):
        """Update portfolio data when triggered"""
        try:
            logger.info("Loading portfolio data...")
            ctx = dash.callback_context
            trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
            logger.info(f"Trigger: {trigger_id}")

            # Handle file upload if provided
            if contents and "upload-portfolio.contents" in trigger_id:
                try:
                    logger.info(f"Processing uploaded file: {filename}")
                    # Validate and sanitize the CSV file
                    df, error = validate_csv_upload(contents, filename)
                    if error:
                        raise ValueError(error)

                    logger.info(
                        f"Successfully read and validated {len(df)} rows from uploaded file {filename}"
                    )
                    status = html.Div(
                        f"Successfully loaded {filename}", className="text-success"
                    )
                except ValueError as e:
                    logger.error(f"CSV validation error: {e}")
                    error_msg = f"Error loading file: {e!s}"
                    error_div = html.Div(error_msg, className="text-danger")
                    return [], {}, [], error_msg, error_div, None
            elif app.portfolio_file:
                # Use default portfolio file
                try:
                    # Try to read the CSV file with standard settings
                    df = pd.read_csv(app.portfolio_file)
                except pd.errors.ParserError as e:
                    logger.warning(f"Parser error with standard settings: {e}")
                    # Try again with more flexible quoting to handle commas in option symbols
                    df = pd.read_csv(app.portfolio_file, quoting=3)  # QUOTE_NONE
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
            groups, summary, cash_like_positions = portfolio.process_portfolio_data(df)
            logger.info(
                f"Successfully processed {len(groups)} portfolio groups and {len(cash_like_positions)} cash-like positions"
            )

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
        Input("portfolio-summary", "data"),
    )
    def update_summary_cards(summary_data):
        """Update summary cards with latest data"""
        logger.debug("Updating summary cards")
        try:
            if not summary_data:
                # Return default values for all outputs
                return (
                    ["$0.00"]
                    + ["0.0%"]
                    + ["0.00β"]
                    + ["$0.00", "0.0%", "0.00β"] * 3
                    + ["$0.00", "0.0%"]
                )

            # No need to calculate percentages as we're not displaying them

            return [
                # Net Exposure
                utils.format_currency(summary_data["net_market_exposure"]),
                "",  # Removed percentage
                # Net Beta
                utils.format_beta(summary_data["portfolio_beta"]),
                # Long Exposure
                utils.format_currency(summary_data["long_exposure"]["total_exposure"]),
                "",  # Removed percentage
                utils.format_beta(
                    summary_data["long_exposure"]["total_beta_adjusted"]
                    / summary_data["long_exposure"]["total_exposure"]
                    if summary_data["long_exposure"]["total_exposure"] != 0
                    else 0
                ),
                # Short Exposure
                utils.format_currency(summary_data["short_exposure"]["total_exposure"]),
                "",  # Removed percentage
                utils.format_beta(
                    summary_data["short_exposure"]["total_beta_adjusted"]
                    / summary_data["short_exposure"]["total_exposure"]
                    if summary_data["short_exposure"]["total_exposure"] != 0
                    else 0
                ),
                # Options Exposure
                utils.format_currency(
                    summary_data["options_exposure"]["total_exposure"]
                ),
                "",  # Removed percentage
                utils.format_beta(
                    summary_data["options_exposure"]["total_beta_adjusted"]
                    / summary_data["options_exposure"]["total_exposure"]
                    if summary_data["options_exposure"]["total_exposure"] != 0
                    else 0
                ),
                # Cash & Equivalents
                utils.format_currency(summary_data["cash_like_value"]),
                "",  # Removed percentage
            ]

        except Exception as e:
            logger.error(f"Error updating summary cards: {e}", exc_info=True)
            # Return default values for all outputs
            return (
                ["$0.00"]
                + ["$0.00"]
                + ["0.0%"]
                + ["0.00β"]
                + ["$0.00", "0.0%", "0.00β"] * 3
                + ["$0.00", "0.0%"]
            )

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
        groups_data,
        search,
        _all_clicks,
        _stocks_clicks,
        _options_clicks,
        _cash_clicks,
        sort_state,
        summary_data,
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
                # Filter out attributes that don't exist in Position class
                stock_position = None
                if g["stock_position"]:
                    stock_position_data = g["stock_position"].copy()
                    # Remove attributes that don't exist in Position class
                    if "sector" in stock_position_data:
                        stock_position_data.pop("sector")
                    if "is_cash_like" in stock_position_data:
                        stock_position_data.pop("is_cash_like")
                    stock_position = Position(**stock_position_data)
                option_positions = [
                    OptionPosition(**opt) for opt in g["option_positions"]
                ]
                group = PortfolioGroup(
                    ticker=g["ticker"],
                    stock_position=stock_position,
                    option_positions=option_positions,
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
                        beta=pos["beta"],
                        market_exposure=pos.get(
                            "market_exposure", pos.get("market_value", 0.0)
                        ),  # Use market_exposure or fall back to market_value
                        beta_adjusted_exposure=pos["beta_adjusted_exposure"],
                    )

                    # Create a PortfolioGroup with just this stock position
                    cash_group = PortfolioGroup(
                        ticker=pos["ticker"],
                        stock_position=stock_pos,
                        option_positions=[],
                        net_exposure=pos.get(
                            "market_exposure", pos.get("market_value", 0.0)
                        ),
                        beta=pos["beta"],
                        beta_adjusted_exposure=pos["beta_adjusted_exposure"],
                        total_delta_exposure=0.0,
                        options_delta_exposure=0.0,
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
    @handle_callback_error(
        default_return=None, error_message="Error selecting position"
    )
    def store_selected_position(
        active_cell, _btn_clicks, groups_data, prev_active_cell
    ):
        """Store selected position data when row is clicked or Details button is clicked"""
        logger.debug("Storing selected position")
        position_data = None

        # Early return if no data available
        if not groups_data:
            logger.debug("No portfolio data available for selection")
            return None

        # Get trigger information
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        logger.debug(f"Trigger ID: {trigger_id}")

        # Handle different trigger types
        row = None

        if "position-details" in trigger_id:
            # Button click - extract ticker from button ID
            row = _get_row_from_button_click(trigger_id, ctx, groups_data)
        elif active_cell and active_cell != prev_active_cell:
            # Table cell click
            row = active_cell["row"]
            logger.debug(f"Table cell clicked at row {row}")

        # Validate row and return data if valid
        if row is not None:
            if 0 <= row < len(groups_data):
                position_data = groups_data[row]
            else:
                # Invalid row index - this is an actual error
                raise StateError.invalid_row(row, len(groups_data))
        else:
            # No selection - this is normal during initialization
            logger.debug("No row selected (normal during initialization)")

        return position_data

    def _get_row_from_button_click(_trigger_id, ctx, groups_data):
        """Helper function to extract row index from button click"""
        import json

        button_idx = ctx.triggered[0]["prop_id"].split(".")[0]

        # Validate button index format
        if not button_idx or not button_idx.startswith("{"):
            raise ValueError(f"Invalid button index format: {button_idx}")

        # Parse button data to extract ticker
        button_data = json.loads(button_idx.replace("'", '"'))
        ticker = button_data.get("index")

        if not ticker:
            raise ValueError("No ticker found in button data")

        logger.debug(f"Button clicked for ticker: {ticker}")

        # Find matching group by ticker
        for i, group_data in enumerate(groups_data):
            stock_ticker = (
                group_data["stock_position"]["ticker"]
                if group_data["stock_position"]
                else None
            )
            option_tickers = [opt["ticker"] for opt in group_data["option_positions"]]

            if stock_ticker == ticker or ticker in option_tickers:
                logger.debug(f"Found matching position at row {i} for ticker {ticker}")
                return i

        # No matching ticker found
        logger.warning(f"No matching position found for ticker {ticker}")
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
        [
            State("portfolio-table", "active_cell"),
            State({"type": "position-details", "index": ALL}, "n_clicks"),
        ],
    )
    @handle_callback_error(
        default_return=(
            False,
            html.Div("Error loading position details", className="text-danger p-3"),
        ),
        error_message="Error toggling position modal",
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

            # Convert data back to PortfolioGroup
            if not position_data:
                logger.warning("Position data is None")
                return False, html.Div(
                    "No position data available", className="text-danger p-3"
                )

            # Create PortfolioGroup from position data
            group = _create_portfolio_group_from_data(position_data)
            logger.debug("Successfully created PortfolioGroup from position data")

            # Create position details
            details = create_position_details(group)
            logger.debug("Successfully created position details")
            return True, details

        # Keep modal state unchanged for all other cases
        logger.debug(f"No action needed, keeping modal state: {is_open}")
        return is_open, dash.no_update

    def _create_portfolio_group_from_data(position_data):
        """Helper function to create a PortfolioGroup from position data"""
        stock_position = None
        if position_data["stock_position"]:
            stock_position_data = position_data["stock_position"].copy()
            # Remove attributes that don't exist in Position class
            if "sector" in stock_position_data:
                stock_position_data.pop("sector")
            if "is_cash_like" in stock_position_data:
                stock_position_data.pop("is_cash_like")
            stock_position = Position(**stock_position_data)

        option_positions = [
            OptionPosition(**opt) for opt in position_data["option_positions"]
        ]

        return PortfolioGroup(
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

    # Old chat panel toggle callback removed - using premium chat component instead

    # Old dash-chat callback removed - using premium chat component instead

    # Add callback to handle column sorting
    @app.callback(
        Output("sort-state", "data"),
        [Input({"type": "sort-header", "column": ALL}, "n_clicks")],
        [State("sort-state", "data")],
    )
    @handle_callback_error(
        default_return=None, error_message="Error updating sort state"
    )
    def update_sort_state(_header_clicks, current_sort_state):
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
            logger.debug(f"No column found in trigger data: {column_data}")
            return current_sort_state

        # Update sort direction if same column clicked, otherwise reset to descending
        if clicked_column == current_sort_state.get("column"):
            new_direction = (
                "asc" if current_sort_state.get("direction") == "desc" else "desc"
            )
        else:
            new_direction = "desc"

        logger.debug(f"Sorting by {clicked_column} in {new_direction} order")
        return {"column": clicked_column, "direction": new_direction}

    # Add callbacks for collapsible chart sections
    @app.callback(
        [
            Output("dashboard-collapse", "is_open"),
            Output("dashboard-collapse-icon", "className"),
        ],
        [Input("dashboard-collapse-button", "n_clicks")],
        [State("dashboard-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_dashboard_collapse(n_clicks, is_open):
        """Toggle the dashboard section collapse state"""
        if n_clicks:
            # Toggle the collapse state
            new_state = not is_open
            # Update the icon based on the new state
            icon_class = (
                "fas fa-chevron-up ms-2" if new_state else "fas fa-chevron-down ms-2"
            )
            return new_state, icon_class
        return is_open, "fas fa-chevron-down ms-2"

    # Add callbacks for main section collapses
    for section in ["summary", "charts"]:

        @app.callback(
            [
                Output(f"{section}-collapse", "is_open"),
                Output(f"{section}-collapse-icon", "className"),
            ],
            [Input(f"{section}-collapse-button", "n_clicks")],
            [State(f"{section}-collapse", "is_open")],
            prevent_initial_call=True,
        )
        def toggle_chart_collapse(n_clicks, is_open, section=section):
            """Toggle the chart section collapse state"""
            if n_clicks:
                # Toggle the collapse state
                new_state = not is_open
                # Update the icon based on the new state
                icon_class = (
                    "fas fa-chevron-up ms-2"
                    if new_state
                    else "fas fa-chevron-down ms-2"
                )
                return new_state, icon_class
            return is_open, "fas fa-chevron-down ms-2"

    # Add callback for positions collapse
    @app.callback(
        [
            Output("positions-collapse", "is_open"),
            Output("positions-collapse-icon", "className"),
        ],
        [Input("positions-collapse-button", "n_clicks")],
        [State("positions-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_positions_collapse(n_clicks, is_open):
        """Toggle the positions section collapse state"""
        if n_clicks:
            # Toggle the collapse state
            new_state = not is_open
            # Update the icon based on the new state
            icon_class = (
                "fas fa-chevron-up ms-2" if new_state else "fas fa-chevron-down ms-2"
            )
            return new_state, icon_class
        return is_open, "fas fa-chevron-down ms-2"

    # Register chart callbacks
    register_chart_callbacks(app)

    # Register premium chat callbacks
    register_premium_chat_callbacks(app)

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
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the server on",
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

    # Display a helpful message about where to access the app
    is_docker = os.path.exists("/.dockerenv")
    is_huggingface = (
        os.environ.get("HF_SPACE") == "1" or os.environ.get("SPACE_ID") is not None
    )

    if is_huggingface:
        logger.info("\n\n🚀 Folio is running on Hugging Face Spaces!")
        logger.info("📊 Access the dashboard at the URL provided by Hugging Face\n")
    elif is_docker and args.host == "0.0.0.0":
        logger.info("\n\n🚀 Folio is running inside a Docker container!")
        logger.info(f"📊 Access the dashboard at: http://localhost:{args.port}")
        logger.info(
            f"💻 (The app is bound to {args.host}:{args.port} inside the container)\n"
        )
    else:
        logger.info("\n\n🚀 Folio is running!")
        logger.info(f"📊 Access the dashboard at: http://localhost:{args.port}\n")

    app.run_server(debug=args.debug, port=args.port, host=args.host)
    return 0


# Create the app instance for Uvicorn to use
app = create_app()
server = app.server

if __name__ == "__main__":
    sys.exit(main())
