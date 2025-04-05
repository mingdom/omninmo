"""Chart components for the Folio dashboard.

This module provides reusable chart components for visualizing portfolio data.
Each component is designed to work with the data model and can be integrated
into the main dashboard layout.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..logger import logger


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

    # Create the summary section - using the original dashboard metrics
    summary_section = dbc.Card(
        [
            dbc.CardHeader(
                dbc.Button(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "Portfolio Summary",
                        html.I(
                            className="fas fa-chevron-down ms-2",
                            id="summary-collapse-icon",
                        ),
                    ],
                    id="summary-collapse-button",
                    color="link",
                    className="text-decoration-none text-dark p-0 d-flex align-items-center w-100 justify-content-between",
                ),
            ),
            dbc.Collapse(
                dbc.CardBody(
                    [
                        # First row: Net Exposure and Net Beta
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H6(
                                                        "Net Exposure",
                                                        className="card-subtitle",
                                                    ),
                                                    html.H5(
                                                        id="total-value",
                                                        className="card-title text-primary",
                                                    ),
                                                    html.P(
                                                        id="total-value-percent",
                                                        className="card-text text-muted",
                                                    ),
                                                ]
                                            ),
                                            className="mb-3",
                                            id="total-value-card",
                                        ),
                                        dbc.Tooltip(
                                            "Net portfolio exposure (Long - Short). Includes stock positions and option delta exposures.",
                                            target="total-value-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H6(
                                                        "Net Beta",
                                                        className="card-subtitle",
                                                    ),
                                                    html.H5(
                                                        id="total-beta",
                                                        className="card-title text-primary",
                                                    ),
                                                ]
                                            ),
                                            className="mb-3",
                                            id="total-beta-card",
                                        ),
                                        dbc.Tooltip(
                                            "Portfolio beta measures correlation with the overall market. Beta > 1 means higher volatility than the market.",
                                            target="total-beta-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                        ),
                        # Third row: Long and Short Exposure
                        dbc.Row(
                            [
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
                                                        id="long-exposure-percent",
                                                        className="card-text text-muted",
                                                    ),
                                                ]
                                            ),
                                            className="mb-3",
                                            id="long-exposure-card",
                                        ),
                                        dbc.Tooltip(
                                            "Total long exposure (stocks + options delta). Positive market correlation.",
                                            target="long-exposure-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
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
                                                        id="short-exposure-percent",
                                                        className="card-text text-muted",
                                                    ),
                                                ]
                                            ),
                                            className="mb-3",
                                            id="short-exposure-card",
                                        ),
                                        dbc.Tooltip(
                                            "Total short exposure (stocks + options delta). Negative market correlation.",
                                            target="short-exposure-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                        ),
                        # Fourth row: Options Exposure and Cash
                        dbc.Row(
                            [
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
                                                        id="options-exposure-percent",
                                                        className="card-text text-muted",
                                                    ),
                                                ]
                                            ),
                                            className="mb-3",
                                            id="options-exposure-card",
                                        ),
                                        dbc.Tooltip(
                                            "Options exposure (delta-adjusted). Includes long and short options.",
                                            target="options-exposure-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H6(
                                                        "Cash & Equivalents",
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
                                            "Cash and cash equivalents (money market, T-bills, etc). Low market correlation.",
                                            target="cash-like-card",
                                            placement="top",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                        ),
                        # Hidden elements to maintain compatibility with callbacks
                        html.Div(
                            [
                                html.P(id="long-beta", style={"display": "none"}),
                                html.P(id="short-beta", style={"display": "none"}),
                                html.P(id="options-beta", style={"display": "none"}),
                            ],
                            style={"display": "none"},
                        ),
                    ]
                ),
                id="summary-collapse",
                is_open=True,  # Initially open
            ),
        ],
        className="mb-3",
    )

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
        ]
    )
