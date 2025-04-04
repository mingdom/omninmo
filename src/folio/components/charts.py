"""Chart components for the Folio dashboard.

This module provides reusable chart components for visualizing portfolio data.
Each component is designed to work with the data model and can be integrated
into the main dashboard layout.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..logger import logger


def create_asset_allocation_chart():
    """Create an asset allocation pie chart component.

    Returns:
        dbc.Card: A collapsible card containing the chart and controls
    """
    logger.debug("Creating asset allocation chart component")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-chart-pie me-2"),
                        "Asset Allocation",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="allocation-collapse-icon",
                        ),
                    ],
                    id="allocation-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
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
                                    "Value",
                                    id="allocation-value-btn",
                                    color="primary",
                                    outline=True,
                                    n_clicks=0,
                                ),
                                dbc.Button(
                                    "Percent",
                                    id="allocation-percent-btn",
                                    color="primary",
                                    outline=True,
                                    active=True,
                                    n_clicks=0,
                                ),
                            ],
                            size="sm",
                            className="mt-2",
                        ),
                    ]
                ),
                id="allocation-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3 chart-card",
    )


def create_exposure_chart():
    """Create an exposure visualization chart component.

    Returns:
        dbc.Card: A collapsible card containing the chart and controls
    """
    logger.debug("Creating exposure chart component")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-balance-scale me-2"),
                        "Exposure Breakdown",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="exposure-collapse-icon",
                        ),
                    ],
                    id="exposure-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id="exposure-chart",
                            config={"displayModeBar": False},
                            className="dash-chart",
                        ),
                        # Add controls for toggling between different exposure views
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    "Net",
                                    id="exposure-net-btn",
                                    color="primary",
                                    outline=True,
                                    active=True,
                                    n_clicks=0,
                                ),
                                dbc.Button(
                                    "Beta-Adjusted",
                                    id="exposure-beta-btn",
                                    color="primary",
                                    outline=True,
                                    n_clicks=0,
                                ),
                            ],
                            size="sm",
                            className="mt-2",
                        ),
                    ]
                ),
                id="exposure-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3 chart-card",
    )


def create_position_treemap():
    """Create a position size treemap visualization component.

    Returns:
        dbc.Card: A collapsible card containing the chart and controls
    """
    logger.debug("Creating position treemap component")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-th-large me-2"),
                        "Position Sizes",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="treemap-collapse-icon",
                        ),
                    ],
                    id="treemap-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id="position-treemap",
                            config={"displayModeBar": False},
                            className="dash-chart",
                        ),
                        # Add controls for different grouping options
                        dbc.RadioItems(
                            id="treemap-group-by",
                            options=[
                                {"label": "Position Type", "value": "type"},
                                {"label": "Ticker", "value": "ticker"},
                            ],
                            value="type",
                            inline=True,
                            className="mt-2",
                        ),
                    ]
                ),
                id="treemap-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3 chart-card",
    )


def create_sector_chart():
    """Create a sector allocation chart component.

    Returns:
        dbc.Card: A collapsible card containing the chart and controls
    """
    logger.debug("Creating sector chart component")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-industry me-2"),
                        "Sector Allocation",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="sector-collapse-icon",
                        ),
                    ],
                    id="sector-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        dcc.Graph(
                            id="sector-chart",
                            config={"displayModeBar": False},
                            className="dash-chart",
                        ),
                        # Add controls for comparing to benchmark
                        dbc.Checklist(
                            id="sector-benchmark-toggle",
                            options=[{"label": "Compare to S&P 500", "value": True}],
                            value=[],
                            switch=True,
                            className="mt-2",
                        ),
                    ]
                ),
                id="sector-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3 chart-card",
    )


def create_dashboard_section():
    """Create the main dashboard section with all charts.

    Returns:
        dbc.Card: A collapsible card containing all visualization charts
    """
    logger.info("Creating dashboard section with charts")
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-chart-bar me-2"),
                        "Portfolio Visualizations",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="dashboard-collapse-icon",
                        ),
                    ],
                    id="dashboard-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        # Summary metrics will be populated by callbacks
                        html.Div(id="dashboard-metrics", className="mb-4"),
                        # First row - Asset Allocation and Exposure
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        create_asset_allocation_chart(),
                                    ],
                                    lg=6,
                                    md=12,
                                ),
                                dbc.Col(
                                    [
                                        create_exposure_chart(),
                                    ],
                                    lg=6,
                                    md=12,
                                ),
                            ],
                        ),
                        # Second row - Sector Allocation and Position Treemap
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        create_sector_chart(),
                                    ],
                                    lg=6,
                                    md=12,
                                ),
                                dbc.Col(
                                    [
                                        create_position_treemap(),
                                    ],
                                    lg=6,
                                    md=12,
                                ),
                            ],
                        ),
                    ]
                ),
                id="dashboard-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3",
    )
