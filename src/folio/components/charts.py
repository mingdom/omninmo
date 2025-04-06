"""Chart components for the Folio dashboard.

This module provides reusable chart components for visualizing portfolio data.
Each component is designed to work with the data model and can be integrated
into the main dashboard layout. It also includes the callbacks for chart interactivity.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from ..chart_data import (
    create_dashboard_metrics,
    transform_for_asset_allocation,
    transform_for_exposure_chart,
    transform_for_treemap,
)
from ..data_model import PortfolioGroup, PortfolioSummary
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


def register_callbacks(app):
    """Register callbacks for chart interactivity.

    Args:
        app: The Dash application instance
    """
    logger.info("Registering chart callbacks")

    # Dashboard metrics callback
    @app.callback(
        Output("dashboard-metrics", "children"),
        [Input("portfolio-summary", "data")],
    )
    def update_dashboard_metrics(summary_data):
        """Update the dashboard metrics based on portfolio summary data."""
        if not summary_data:
            return html.Div("No portfolio data available")

        try:
            # Convert the JSON data back to a PortfolioSummary object
            portfolio_summary = PortfolioSummary.from_dict(summary_data)

            # Create metric cards
            metrics = create_dashboard_metrics(portfolio_summary)

            # Create a row of metric cards
            return dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H5(metric["title"], className="metric-title"),
                                html.H3(metric["value"], className="metric-value"),
                                html.Div(
                                    metric["help_text"],
                                    className="metric-help-text small text-muted",
                                ),
                            ],
                            className="metric-card",
                        ),
                        width=3,
                    )
                    for metric in metrics
                ]
            )
        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {e}", exc_info=True)
            return html.Div(f"Error loading metrics: {e!s}", className="text-danger")

    # Asset Allocation Chart callback
    @app.callback(
        [
            Output("asset-allocation-chart", "figure"),
            Output("allocation-value-btn", "active"),
            Output("allocation-percent-btn", "active"),
        ],
        [
            Input("portfolio-summary", "data"),
            Input("allocation-value-btn", "n_clicks"),
            Input("allocation-percent-btn", "n_clicks"),
        ],
        [
            State("allocation-value-btn", "active"),
            State("allocation-percent-btn", "active"),
        ],
    )
    def update_asset_allocation_chart(
        summary_data, _value_clicks, _percent_clicks, value_active, percent_active
    ):
        """Update the asset allocation chart based on user selection."""
        if not summary_data:
            # Return empty figure if no data
            return {"data": [], "layout": {"height": 300}}, False, True

        try:
            # Determine which view to use based on button clicks
            ctx = dash.callback_context
            if not ctx.triggered:
                # Default to percentage view
                use_percentage = True
                value_active = False
                percent_active = True
            else:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]
                if button_id == "allocation-value-btn":
                    use_percentage = False
                    value_active = True
                    percent_active = False
                elif button_id == "allocation-percent-btn":
                    use_percentage = True
                    value_active = False
                    percent_active = True
                else:
                    # If triggered by data update, maintain current state
                    use_percentage = percent_active
                    # Keep button states as they are

            # Convert the JSON data back to a PortfolioSummary object
            portfolio_summary = PortfolioSummary.from_dict(summary_data)

            # Transform the data for the chart
            chart_data = transform_for_asset_allocation(
                portfolio_summary, use_percentage
            )
            return chart_data, value_active, percent_active
        except Exception as e:
            logger.error(f"Error updating asset allocation chart: {e}", exc_info=True)
            error_figure = {
                "data": [],
                "layout": {
                    "height": 300,
                    "annotations": [
                        {
                            "text": f"Error: {e!s}",
                            "showarrow": False,
                            "font": {"color": "red"},
                        }
                    ],
                },
            }
            # Return error figure and maintain button states
            return error_figure, value_active, percent_active

    # Exposure Chart callback
    @app.callback(
        [
            Output("exposure-chart", "figure"),
            Output("exposure-net-btn", "active"),
            Output("exposure-beta-btn", "active"),
        ],
        [
            Input("portfolio-summary", "data"),
            Input("exposure-net-btn", "n_clicks"),
            Input("exposure-beta-btn", "n_clicks"),
        ],
        [
            State("exposure-net-btn", "active"),
            State("exposure-beta-btn", "active"),
        ],
    )
    def update_exposure_chart(
        summary_data, _net_clicks, _beta_clicks, net_active, beta_active
    ):
        """Update the exposure chart based on user selection."""
        if not summary_data:
            # Return empty figure if no data
            return {"data": [], "layout": {"height": 300}}, True, False

        try:
            # Determine which view to use based on button clicks
            ctx = dash.callback_context
            if not ctx.triggered:
                # Default to beta-adjusted view
                use_beta_adjusted = True
                net_active = False
                beta_active = True
            else:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]
                if button_id == "exposure-net-btn":
                    use_beta_adjusted = False
                    net_active = True
                    beta_active = False
                elif button_id == "exposure-beta-btn":
                    use_beta_adjusted = True
                    net_active = False
                    beta_active = True
                else:
                    # If triggered by data update, maintain current state
                    use_beta_adjusted = beta_active
                    # Keep button states as they are

            # Convert the JSON data back to a PortfolioSummary object
            portfolio_summary = PortfolioSummary.from_dict(summary_data)

            # Transform the data for the chart
            chart_data = transform_for_exposure_chart(
                portfolio_summary, use_beta_adjusted
            )
            return chart_data, net_active, beta_active
        except Exception as e:
            logger.error(f"Error updating exposure chart: {e}", exc_info=True)
            error_figure = {
                "data": [],
                "layout": {
                    "height": 300,
                    "annotations": [
                        {
                            "text": f"Error: {e!s}",
                            "showarrow": False,
                            "font": {"color": "red"},
                        }
                    ],
                },
            }
            # Return error figure and maintain button states
            return error_figure, net_active, beta_active

    # Position Treemap callback
    @app.callback(
        Output("position-treemap", "figure"),
        [
            Input("portfolio-groups", "data"),
            Input("treemap-group-by", "value"),
        ],
    )
    def update_position_treemap(groups_data, group_by):
        """Update the position treemap based on user selection."""
        if not groups_data:
            # Return empty figure if no data
            return {"data": [], "layout": {"height": 400}}

        try:
            # Convert the JSON data back to a list of PortfolioGroup objects
            portfolio_groups = [
                PortfolioGroup.from_dict(group) for group in groups_data
            ]

            # Transform the data for the chart
            return transform_for_treemap(portfolio_groups, group_by)
        except Exception as e:
            logger.error(f"Error updating position treemap: {e}", exc_info=True)
            return {
                "data": [],
                "layout": {
                    "height": 400,
                    "annotations": [
                        {
                            "text": f"Error: {e!s}",
                            "showarrow": False,
                            "font": {"color": "red"},
                        }
                    ],
                },
            }

    # Sector Chart callback
    # Sector chart callback removed - will be implemented in a separate task


# For backward compatibility
register_chart_callbacks = register_callbacks
