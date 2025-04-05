"""Chart components for the Folio dashboard.

This module provides reusable chart components for visualizing portfolio data.
Each component is designed to work with the data model and can be integrated
into the main dashboard layout.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..logger import logger
from .summary_cards import create_summary_cards


def create_asset_allocation_chart():
    """Create an asset allocation pie chart component."""
    logger.debug("Creating asset allocation chart component")
    return html.Div(
        [
            dcc.Graph(
                id="asset-allocation-chart",
                config={"displayModeBar": False},
                className="dash-chart",
            ),
            # Add controls for toggling between absolute value and percentage
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        "Exposure",
                        id="allocation-value-btn",
                        color="primary",
                        outline=True,
                        size="sm",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        "Percentage",
                        id="allocation-percent-btn",
                        color="primary",
                        outline=True,
                        size="sm",
                        active=True,
                        n_clicks=0,
                    ),
                ],
                size="sm",
                className="mt-2",
            ),
        ],
        className="mb-4",
    )


def create_exposure_chart():
    """Create an exposure bar chart component."""
    logger.debug("Creating exposure chart component")
    return html.Div(
        [
            dcc.Graph(
                id="exposure-chart",
                config={"displayModeBar": False},
                className="dash-chart",
            ),
            # Add controls for toggling between net and beta-adjusted
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        "Net Exposure",
                        id="exposure-net-btn",
                        color="primary",
                        outline=True,
                        size="sm",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        "Beta-Adjusted",
                        id="exposure-beta-btn",
                        color="primary",
                        outline=True,
                        size="sm",
                        active=True,
                        n_clicks=0,
                    ),
                ],
                size="sm",
                className="mt-2",
            ),
        ],
        className="mb-4",
    )


def create_position_treemap():
    """Create a position treemap component."""
    logger.debug("Creating position treemap component")
    return html.Div(
        [
            dcc.Graph(
                id="position-treemap",
                config={"displayModeBar": False},
                className="dash-chart",
            ),
            # Hidden input to maintain the 'ticker' grouping without a visible toggle
            html.Div(
                dbc.Input(
                    id="treemap-group-by",
                    type="hidden",
                    value="ticker",  # Always group by ticker
                ),
                style={"display": "none"},
            ),
        ],
        className="mb-4",
    )


# Sector chart removed for now - will be implemented in a separate task


def create_dashboard_section():
    """Create the dashboard section with all charts.

    Returns:
        html.Div: A div containing all dashboard components
    """
    logger.info("Creating dashboard section with charts")

    # Import the summary cards component

    # Create the summary section using the dedicated component
    summary_section = create_summary_cards()

    # Create the charts section
    charts_section = dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-chart-bar me-2"),
                        "Portfolio Visualizations",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="charts-collapse-icon",
                        ),
                    ],
                    id="charts-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        # Asset Allocation Chart (in its own card)
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5("Asset Allocation", className="m-0"),
                                ),
                                dbc.CardBody(
                                    [
                                        create_asset_allocation_chart(),
                                    ]
                                ),
                            ],
                            className="mb-4 chart-card",
                        ),
                        # Market Exposure Chart (in its own card)
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5("Market Exposure", className="m-0"),
                                ),
                                dbc.CardBody(
                                    [
                                        create_exposure_chart(),
                                    ]
                                ),
                            ],
                            className="mb-4 chart-card",
                        ),
                        # Position Treemap (in its own card)
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5(
                                        "Position Size by Exposure", className="m-0"
                                    ),
                                ),
                                dbc.CardBody(
                                    [
                                        create_position_treemap(),
                                    ]
                                ),
                            ],
                            className="mb-4 chart-card",
                        ),
                    ]
                ),
                id="charts-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3",
    )

    # We don't need to create the positions section here as it's already in app.py

    # Combine all sections
    return html.Div(
        [
            summary_section,
            charts_section,
            # positions_section is handled in app.py
        ],
        id="dashboard-section",
    )
