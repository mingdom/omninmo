"""Chart callbacks for the Folio dashboard.

This module registers callbacks for the chart components, handling user
interactions and data updates.
"""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

from ..chart_data import (
    create_dashboard_metrics,
    transform_for_asset_allocation,
    transform_for_exposure_chart,
    transform_for_treemap,
)
from ..data_model import PortfolioGroup, PortfolioSummary
from ..logger import logger


def register_chart_callbacks(app):
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
        summary_data, value_clicks, percent_clicks, value_active, percent_active
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
        summary_data, net_clicks, beta_clicks, net_active, beta_active
    ):
        """Update the exposure chart based on user selection."""
        if not summary_data:
            # Return empty figure if no data
            return {"data": [], "layout": {"height": 300}}, True, False

        try:
            # Determine which view to use based on button clicks
            ctx = dash.callback_context
            if not ctx.triggered:
                # Default to net exposure view
                use_beta_adjusted = False
                net_active = True
                beta_active = False
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
