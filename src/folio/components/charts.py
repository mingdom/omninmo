"""Chart components for the Folio dashboard.

This module provides reusable chart components for visualizing portfolio data.
Each component is designed to work with the data model and can be integrated
into the main dashboard layout.
"""

import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from ..logger import logger


def create_asset_allocation_chart():
    """Create an asset allocation pie chart component.

    Returns:
        html.Div: A div containing the chart and controls
    """
    logger.debug("Creating asset allocation chart component")
    return html.Div(
        [
            html.H4("Asset Allocation", className="chart-title"),
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
        ],
        className="chart-container",
    )


def create_exposure_chart():
    """Create an exposure visualization chart component.

    Returns:
        html.Div: A div containing the chart and controls
    """
    logger.debug("Creating exposure chart component")
    return html.Div(
        [
            html.H4("Exposure Breakdown", className="chart-title"),
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
        ],
        className="chart-container",
    )


def create_position_treemap():
    """Create a position size treemap visualization component.

    Returns:
        html.Div: A div containing the chart and controls
    """
    logger.debug("Creating position treemap component")
    return html.Div(
        [
            html.H4("Position Sizes", className="chart-title"),
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
        ],
        className="chart-container",
    )


def create_sector_chart():
    """Create a sector allocation chart component.

    Returns:
        html.Div: A div containing the chart and controls
    """
    logger.debug("Creating sector chart component")
    return html.Div(
        [
            html.H4("Sector Allocation", className="chart-title"),
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
        ],
        className="chart-container",
    )


def create_dashboard_section():
    """Create the main dashboard section with all charts.

    Returns:
        html.Div: The dashboard section with charts arranged in a grid
    """
    logger.info("Creating dashboard section with charts")
    return html.Div(
        [
            html.H3("Portfolio Dashboard", className="mb-4"),
            # Top row - Summary metrics will be populated by callbacks
            html.Div(id="dashboard-metrics", className="mb-4"),
            # Middle row - Main charts
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_asset_allocation_chart(),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            create_exposure_chart(),
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Bottom row - Additional charts
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_sector_chart(),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            create_position_treemap(),
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        id="dashboard-container",
        className="dashboard-container mb-4",
    )
