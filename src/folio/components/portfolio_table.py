from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import html

from ..data_model import PortfolioGroup
from ..utils import (
    format_beta,
    format_currency,
    format_percentage,
)


def get_group_ticker(group: PortfolioGroup) -> str:
    """Get the primary ticker for a portfolio group"""
    if group.stock_position:
        return group.stock_position.ticker
    elif group.option_positions:
        return group.option_positions[0].ticker
    return "Unknown"


def create_position_row(group: PortfolioGroup, metrics: Dict) -> dbc.Row:
    """Create a row for a position in the portfolio table"""
    ticker = get_group_ticker(group)
    return dbc.Row(
        [
            dbc.Col(html.Strong(ticker), width=2),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span("Stock" if group.stock_position else ""),
                            html.Span(
                                f" ({len(group.option_positions)} options)"
                                if group.option_positions
                                else ""
                            ),
                        ]
                    )
                ],
                width=2,
            ),
            dbc.Col(format_currency(group.net_exposure), width=2),
            dbc.Col(
                format_beta(
                    group.beta_adjusted_exposure / group.net_exposure
                    if group.net_exposure != 0
                    else 0
                ),
                width=2,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Div(format_currency(group.beta_adjusted_exposure)),
                            html.Small(
                                f"Δ: {format_percentage(group.total_delta_exposure / group.net_exposure * 100 if group.net_exposure != 0 else 0)}"
                            ),
                        ]
                    )
                ],
                width=2,
            ),
            dbc.Col(
                dbc.Button(
                    "Details",
                    id={"type": "position-details", "index": ticker},
                    color="primary",
                    size="sm",
                    className="float-end",
                ),
                width=2,
            ),
        ],
        className="g-0 border-bottom py-2 position-row",
        id=f"row-{ticker}",
    )


def create_portfolio_table(
    groups: List[PortfolioGroup], search: str = None, sort_by: str = "value-desc"
) -> html.Div:
    """Create the portfolio table with all positions"""
    # Filter groups based on search
    if search:
        search = search.lower()
        filtered_groups = []
        for g in groups:
            ticker = get_group_ticker(g)
            if search in ticker.lower():
                filtered_groups.append(g)
        groups = filtered_groups

    # Sort groups
    sort_key, sort_direction = (
        sort_by.split("-") if "-" in sort_by else (sort_by, "desc")
    )
    if sort_key == "value":
        groups.sort(key=lambda x: abs(x.net_exposure), reverse=sort_direction == "desc")
    elif sort_key == "beta":
        groups.sort(
            key=lambda x: abs(x.beta_adjusted_exposure),
            reverse=sort_direction == "desc",
        )
    elif sort_key == "exposure":
        groups.sort(
            key=lambda x: abs(x.total_delta_exposure), reverse=sort_direction == "desc"
        )

    # Create table header
    header = dbc.Row(
        [
            dbc.Col(html.Strong("Ticker"), width=2),
            dbc.Col(html.Strong("Type"), width=2),
            dbc.Col(html.Strong("Value"), width=2),
            dbc.Col(html.Strong("Beta"), width=2),
            dbc.Col(html.Strong("Exposure"), width=2),
            dbc.Col("", width=2),
        ],
        className="g-0 border-bottom py-2 bg-light",
    )

    # Create table rows
    rows = [create_position_row(group, {}) for group in groups]

    return html.Div(
        [header, html.Div(rows, className="portfolio-table-body")],
        className="portfolio-table",
    )
