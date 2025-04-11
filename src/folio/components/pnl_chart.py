"""
P&L chart component for position visualization.

This module provides components for visualizing position P&L across different price points.
It includes a modal for displaying P&L charts and the necessary callbacks for interactivity.
"""

from typing import Any

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback_context, dcc, html

from ..data_model import OptionPosition, PortfolioGroup, StockPosition
from ..logger import logger
from ..pnl import calculate_strategy_pnl, determine_price_range, summarize_strategy_pnl
from ..utils import format_currency


def create_pnl_chart(
    pnl_data: dict[str, Any],
    summary: dict[str, Any],
    current_price: float,
    ticker: str,
    mode: str = "default",
) -> go.Figure:
    """
    Create a Plotly figure for P&L visualization.

    Args:
        pnl_data: P&L data from calculate_strategy_pnl
        summary: Summary data from summarize_strategy_pnl
        current_price: Current price of the underlying
        ticker: Ticker symbol
        mode: Mode used for P&L calculation ("default" or "cost_basis")

    Returns:
        Plotly figure object
    """
    # Create figure
    fig = go.Figure()

    # Plot combined P&L
    fig.add_trace(
        go.Scatter(
            x=pnl_data["price_points"],
            y=pnl_data["pnl_values"],
            mode="lines",
            name=f"{ticker} Strategy P&L",
            line=dict(color="#1f77b4", width=3),
        )
    )

    # Plot individual position P&Ls
    if "individual_pnls" in pnl_data:
        for i, pos_pnl in enumerate(pnl_data["individual_pnls"]):
            position_data = pos_pnl.get("position", {})
            pos_type = position_data.get("position_type", "unknown")
            pos_ticker = position_data.get("ticker", f"Position {i + 1}")

            # Create a more descriptive label for options
            if pos_type == "option":
                option_type = position_data.get("option_type", "")
                strike = position_data.get("strike", 0)
                pos_desc = f"{pos_ticker} {option_type} {strike}"
            else:
                pos_desc = pos_ticker

            fig.add_trace(
                go.Scatter(
                    x=pos_pnl["price_points"],
                    y=pos_pnl["pnl_values"],
                    mode="lines",
                    name=pos_desc,
                    line=dict(dash="dash", width=1.5),
                    opacity=0.7,
                )
            )

    # Add reference lines
    fig.add_hline(
        y=0,
        line=dict(color="red", width=1, dash="solid"),
        opacity=0.5,
        annotation_text="Break-even",
        annotation_position="bottom right",
    )

    fig.add_vline(
        x=current_price,
        line=dict(color="green", width=1, dash="dash"),
        opacity=0.7,
        annotation_text=f"Current: ${current_price:.2f}",
        annotation_position="top right",
    )

    # Add breakeven points
    for bp in summary["breakeven_points"]:
        fig.add_vline(
            x=bp,
            line=dict(color="orange", width=1, dash="dot"),
            opacity=0.5,
            annotation_text=f"BE: ${bp:.2f}",
            annotation_position="bottom",
        )

    # Add max profit/loss points
    max_profit = summary["max_profit"]
    max_profit_price = summary["max_profit_price"]
    fig.add_trace(
        go.Scatter(
            x=[max_profit_price],
            y=[max_profit],
            mode="markers+text",
            marker=dict(color="green", size=10),
            text=f"Max Profit: ${max_profit:.2f}",
            textposition="top center",
            showlegend=False,
        )
    )

    max_loss = summary["max_loss"]
    max_loss_price = summary["max_loss_price"]
    fig.add_trace(
        go.Scatter(
            x=[max_loss_price],
            y=[max_loss],
            mode="markers+text",
            marker=dict(color="red", size=10),
            text=f"Max Loss: ${max_loss:.2f}",
            textposition="bottom center",
            showlegend=False,
        )
    )

    # Add current P&L
    current_pnl = summary["current_pnl"]
    fig.add_trace(
        go.Scatter(
            x=[current_price],
            y=[current_pnl],
            mode="markers+text",
            marker=dict(color="gold", size=10),
            text=f"Current P&L: ${current_pnl:.2f}",
            textposition="top right",
            showlegend=False,
        )
    )

    # Set layout
    mode_label = "Using Cost Basis" if mode == "cost_basis" else "Using Current Price"
    fig.update_layout(
        title=f"P&L Analysis for {ticker} Position Group ({mode_label})",
        xaxis_title=f"{ticker} Price",
        yaxis_title="P&L ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )

    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgrey")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgrey")

    return fig


def create_pnl_modal() -> dbc.Modal:
    """
    Create a modal for displaying P&L charts.

    Returns:
        dbc.Modal: The modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Position P&L Analysis"),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    # Mode toggle
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            dbc.Label("P&L Calculation Mode:"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "Current Price",
                                                        id="pnl-mode-default",
                                                        color="primary",
                                                        outline=False,
                                                        active=True,
                                                        size="sm",
                                                        className="me-1",
                                                    ),
                                                    dbc.Button(
                                                        "Cost Basis",
                                                        id="pnl-mode-cost-basis",
                                                        color="primary",
                                                        outline=True,
                                                        active=False,
                                                        size="sm",
                                                    ),
                                                ]
                                            ),
                                            dbc.Tooltip(
                                                "Current Price mode shows future P&L projections from the current price. "
                                                "Cost Basis mode shows P&L relative to your purchase price.",
                                                target="pnl-mode-default",
                                            ),
                                            dbc.Tooltip(
                                                "Cost Basis mode shows P&L relative to your purchase price. "
                                                "Current Price mode shows future P&L projections from the current price.",
                                                target="pnl-mode-cost-basis",
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                ]
                            ),
                        ]
                    ),
                    # Loading spinner for the chart
                    dbc.Spinner(
                        dcc.Graph(
                            id="pnl-chart",
                            config={"displayModeBar": True, "responsive": True},
                            className="dash-chart",
                        ),
                        color="primary",
                        type="border",
                        fullscreen=False,
                    ),
                    # Summary information
                    html.Div(id="pnl-summary", className="mt-3"),
                    # Position details
                    html.Div(id="pnl-position-details", className="mt-3"),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="close-pnl-modal",
                    className="ms-auto",
                ),
            ),
        ],
        id="pnl-modal",
        size="xl",
    )


def create_pnl_summary(summary: dict[str, Any], mode: str) -> html.Div:
    """
    Create a summary of P&L metrics.

    Args:
        summary: Summary data from summarize_strategy_pnl
        mode: Mode used for P&L calculation ("default" or "cost_basis")

    Returns:
        html.Div: The summary component
    """
    mode_label = "Using Cost Basis" if mode == "cost_basis" else "Using Current Price"

    return html.Div(
        [
            html.H5(f"P&L Summary ({mode_label})"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Current P&L", className="card-subtitle"
                                            ),
                                            html.H4(
                                                format_currency(summary["current_pnl"]),
                                                className="card-title text-primary",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Max Profit", className="card-subtitle"
                                            ),
                                            html.H4(
                                                format_currency(summary["max_profit"]),
                                                className="card-title text-success",
                                            ),
                                            html.Small(
                                                f"at ${summary['max_profit_price']:.2f}"
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Max Loss", className="card-subtitle"
                                            ),
                                            html.H4(
                                                format_currency(summary["max_loss"]),
                                                className="card-title text-danger",
                                            ),
                                            html.Small(
                                                f"at ${summary['max_loss_price']:.2f}"
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Break-even Points",
                                                className="card-subtitle",
                                            ),
                                            html.H4(
                                                ", ".join(
                                                    [
                                                        f"${bp:.2f}"
                                                        for bp in summary[
                                                            "breakeven_points"
                                                        ]
                                                    ]
                                                )
                                                if summary["breakeven_points"]
                                                else "N/A",
                                                className="card-title",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        width=3,
                    ),
                ]
            ),
        ]
    )


def register_callbacks(app):
    """
    Register callbacks for the P&L chart component.

    Args:
        app: The Dash app
    """

    @app.callback(
        [
            Output("pnl-modal", "is_open"),
            Output("pnl-chart", "figure"),
            Output("pnl-summary", "children"),
            Output("pnl-position-details", "children"),
            Output("pnl-mode-default", "active"),
            Output("pnl-mode-cost-basis", "active"),
            Output("pnl-mode-default", "outline"),
            Output("pnl-mode-cost-basis", "outline"),
        ],
        [
            Input({"type": "position-pnl", "index": ALL}, "n_clicks"),
            Input("pnl-mode-default", "n_clicks"),
            Input("pnl-mode-cost-basis", "n_clicks"),
            Input("close-pnl-modal", "n_clicks"),
        ],
        [
            State("portfolio-groups", "data"),
            State("pnl-modal", "is_open"),
            State("pnl-mode-default", "active"),
            State("pnl-mode-cost-basis", "active"),
        ],
        # Prevent the callback from firing when the app first loads
        prevent_initial_call=True,
    )
    def toggle_pnl_modal(
        btn_clicks,
        default_mode_clicks,  # noqa: ARG001 - required by Dash
        cost_basis_mode_clicks,  # noqa: ARG001 - required by Dash
        close_clicks,  # noqa: ARG001 - required by Dash
        groups_data,
        is_open,
        default_mode_active,
        cost_basis_mode_active,
    ):
        """Toggle P&L modal and update chart."""
        ctx = callback_context
        if not ctx.triggered:
            return (False, {}, html.Div(), html.Div(), True, False, False, True)

        trigger_id = ctx.triggered[0]["prop_id"]
        logger.debug(f"PNL modal trigger: {trigger_id}")

        # Handle close button
        if "close-pnl-modal" in trigger_id:
            return (
                False,
                {},
                html.Div(),
                html.Div(),
                default_mode_active,
                cost_basis_mode_active,
                not default_mode_active,
                not cost_basis_mode_active,
            )

        # Handle mode toggle
        use_cost_basis = False
        if "pnl-mode-default" in trigger_id:
            default_mode_active = True
            cost_basis_mode_active = False
            use_cost_basis = False
        elif "pnl-mode-cost-basis" in trigger_id:
            default_mode_active = False
            cost_basis_mode_active = True
            use_cost_basis = True

        # If modal is already open and we're just changing modes, we need the current position data
        if is_open and (
            "pnl-mode-default" in trigger_id or "pnl-mode-cost-basis" in trigger_id
        ):
            # We need to get the current position data from the client-side store
            # This will be implemented in a separate callback
            pass

        # Handle position button click
        ticker = None
        position_data = None

        # Check if any of the P&L buttons have been clicked
        pnl_button_clicked = False
        if "position-pnl" in trigger_id and any(
            clicks for clicks in btn_clicks if clicks
        ):
            pnl_button_clicked = True
            # Extract ticker from button ID
            button_id = trigger_id.split(".")[0]
            ticker = button_id.split('"index":"')[1].split('"')[0]

            # Find matching group by ticker
            for group_data in groups_data:
                group_ticker = group_data["ticker"]
                if group_ticker == ticker:
                    position_data = group_data
                    break

            if not position_data:
                logger.warning(f"No position data found for ticker {ticker}")
                return (
                    False,
                    {},
                    html.Div("No position data found"),
                    html.Div(),
                    default_mode_active,
                    cost_basis_mode_active,
                    not default_mode_active,
                    not cost_basis_mode_active,
                )

        # If we don't have position data or no P&L button was clicked, return
        if (not position_data and not is_open) or (
            not pnl_button_clicked and not is_open
        ):
            return (
                False,
                {},
                html.Div(),
                html.Div(),
                default_mode_active,
                cost_basis_mode_active,
                not default_mode_active,
                not cost_basis_mode_active,
            )

        # Convert position data to objects
        if position_data:
            # Create stock position if it exists
            stock_position = None
            if position_data["stock_position"]:
                stock_data = position_data["stock_position"]
                stock_position = StockPosition(
                    ticker=stock_data["ticker"],
                    quantity=stock_data["quantity"],
                    price=stock_data["price"],
                    beta=stock_data["beta"],
                    market_exposure=stock_data["market_exposure"],
                    beta_adjusted_exposure=stock_data["beta_adjusted_exposure"],
                    cost_basis=stock_data.get("cost_basis", stock_data["price"]),
                )

            # Create option positions if they exist
            option_positions = []
            for opt_data in position_data["option_positions"]:
                option_position = OptionPosition(
                    ticker=opt_data["ticker"],
                    position_type="option",
                    quantity=opt_data["quantity"],
                    strike=opt_data["strike"],
                    expiry=opt_data["expiry"],
                    option_type=opt_data["option_type"],
                    price=opt_data["price"],
                    delta=opt_data["delta"],
                    delta_exposure=opt_data["delta_exposure"],
                    notional_value=opt_data["notional_value"],
                    beta=opt_data.get("beta", 1.0),
                    beta_adjusted_exposure=opt_data["beta_adjusted_exposure"],
                    market_exposure=opt_data["market_exposure"],
                    underlying_beta=opt_data.get("underlying_beta", 1.0),
                    cost_basis=opt_data.get("cost_basis", opt_data["price"]),
                )
                option_positions.append(option_position)

            # Create portfolio group
            group = PortfolioGroup(
                ticker=position_data["ticker"],
                stock_position=stock_position,
                option_positions=option_positions,
                net_exposure=position_data["net_exposure"],
                beta=position_data["beta"],
                beta_adjusted_exposure=position_data["beta_adjusted_exposure"],
                total_delta_exposure=position_data["total_delta_exposure"],
                options_delta_exposure=position_data["options_delta_exposure"],
            )

            # Get all positions
            all_positions = []
            if group.stock_position:
                all_positions.append(group.stock_position)
            all_positions.extend(group.option_positions)

            # Get current price
            current_price = None
            if group.stock_position:
                current_price = group.stock_position.price
            elif group.option_positions:
                # Try to estimate underlying price from notional value and quantity
                first_option = group.option_positions[0]
                if hasattr(first_option, "notional_value") and hasattr(
                    first_option, "quantity"
                ):
                    # Notional value is 100 * underlying price * abs(quantity)
                    abs_quantity = abs(first_option.quantity)
                    if abs_quantity > 0:
                        current_price = first_option.notional_value / (
                            100 * abs_quantity
                        )

            if current_price is None:
                # Fallback to a default value
                current_price = 100.0
                logger.warning(
                    f"Could not determine current price for {group.ticker}, using default: ${current_price:.2f}"
                )

            # Calculate price range
            price_range = determine_price_range(all_positions, current_price)

            # Calculate P&L
            pnl_data = calculate_strategy_pnl(
                all_positions,
                price_range=price_range,
                num_points=100,
                use_cost_basis=use_cost_basis,
            )

            # Generate summary
            summary = summarize_strategy_pnl(pnl_data, current_price)

            # Create chart
            fig = create_pnl_chart(
                pnl_data,
                summary,
                current_price,
                group.ticker,
                mode="cost_basis" if use_cost_basis else "default",
            )

            # Create summary
            summary_component = create_pnl_summary(
                summary,
                mode="cost_basis" if use_cost_basis else "default",
            )

            # Create position details (reuse existing component)
            from .position_details import create_position_details

            position_details = create_position_details(group)

            return (
                True,
                fig,
                summary_component,
                position_details,
                default_mode_active,
                cost_basis_mode_active,
                not default_mode_active,
                not cost_basis_mode_active,
            )

        # If we get here, something went wrong
        return (
            False,
            {},
            html.Div("Error loading P&L data"),
            html.Div(),
            default_mode_active,
            cost_basis_mode_active,
            not default_mode_active,
            not cost_basis_mode_active,
        )
