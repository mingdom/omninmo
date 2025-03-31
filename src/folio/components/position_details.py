import dash_bootstrap_components as dbc
from dash import html

from ..data_model import PortfolioGroup
from ..utils import (
    format_beta,
    format_currency,
    format_percentage,
)


def create_stock_section(group: PortfolioGroup) -> dbc.Card:
    """Create the stock position section of the details view"""
    if not group.stock_position:
        return None

    stock = group.stock_position
    return dbc.Card(
        [
            dbc.CardHeader("Stock Position"),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("Position Details"),
                                    html.P(
                                        [
                                            html.Strong("Shares: "),
                                            html.Span(f"{stock.quantity:,}"),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Market Value: "),
                                            html.Span(
                                                format_currency(stock.market_value)
                                            ),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Beta: "),
                                            html.Span(format_beta(stock.beta)),
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H5("Risk Metrics"),
                                    html.P(
                                        [
                                            html.Strong("Portfolio Weight: "),
                                            html.Span(
                                                format_percentage(stock.weight * 100)
                                            ),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Beta-Adjusted Exposure: "),
                                            html.Span(
                                                format_currency(
                                                    stock.beta_adjusted_exposure
                                                )
                                            ),
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


def create_options_section(group: PortfolioGroup) -> dbc.Card:
    """Create the options section of the details view"""
    if not group.option_positions:
        return None

    # Group options by expiration
    options_by_expiry = {}
    for opt in group.option_positions:
        expiry_str = opt.expiry
        if expiry_str not in options_by_expiry:
            options_by_expiry[expiry_str] = []
        options_by_expiry[expiry_str].append(opt)

    # Create tables for each expiration
    expiry_tables = []
    for expiry, options in sorted(options_by_expiry.items()):
        table = dbc.Table(
            [
                html.Thead(
                    [
                        html.Tr(
                            [
                                html.Th("Type"),
                                html.Th("Strike"),
                                html.Th("Quantity"),
                                html.Th("Value"),
                                html.Th("Delta"),
                                html.Th("Exposure"),
                            ]
                        )
                    ]
                ),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(opt.option_type),
                                html.Td(f"${opt.strike:,.2f}"),
                                html.Td(f"{opt.quantity:,}"),
                                html.Td(format_currency(opt.market_value)),
                                html.Td(format_percentage(opt.delta * 100)),
                                html.Td(format_currency(opt.delta_exposure)),
                            ]
                        )
                        for opt in sorted(
                            options, key=lambda x: (x.option_type, x.strike)
                        )
                    ]
                ),
            ],
            bordered=True,
            size="sm",
        )

        expiry_tables.append(
            dbc.Card(
                [dbc.CardHeader(f"Expiration: {expiry}"), dbc.CardBody(table)],
                className="mb-3",
            )
        )

    return dbc.Card(
        [
            dbc.CardHeader("Option Positions"),
            dbc.CardBody(
                [
                    html.H5("Options Summary"),
                    html.P(
                        [
                            html.Strong("Total Positions: "),
                            html.Span(
                                f"{len(group.option_positions)} ({group.call_count} calls, {group.put_count} puts)"
                            ),
                        ]
                    ),
                    html.P(
                        [
                            html.Strong("Net Option Value: "),
                            html.Span(format_currency(group.net_option_value)),
                        ]
                    ),
                    html.P(
                        [
                            html.Strong("Total Delta Exposure: "),
                            html.Span(format_currency(group.total_delta_exposure)),
                        ]
                    ),
                    html.Hr(),
                    html.Div(expiry_tables),
                ]
            ),
        ]
    )


def create_combined_metrics(group: PortfolioGroup) -> dbc.Card:
    """Create the combined metrics section"""
    return dbc.Card(
        [
            dbc.CardHeader("Combined Position Metrics"),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5("Value & Exposure"),
                                    html.P(
                                        [
                                            html.Strong("Total Value: "),
                                            html.Span(
                                                format_currency(group.net_exposure)
                                            ),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Net Delta: "),
                                            html.Span(
                                                format_percentage(
                                                    group.total_delta_exposure
                                                    / group.net_exposure
                                                    * 100
                                                    if group.net_exposure != 0
                                                    else 0
                                                )
                                            ),
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H5("Risk Metrics"),
                                    html.P(
                                        [
                                            html.Strong("Beta-Adjusted Exposure: "),
                                            html.Span(
                                                format_currency(
                                                    group.beta_adjusted_exposure
                                                )
                                            ),
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Position Beta: "),
                                            html.Span(
                                                format_beta(
                                                    group.beta_adjusted_exposure
                                                    / group.net_exposure
                                                    if group.net_exposure != 0
                                                    else 0
                                                )
                                            ),
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


def create_position_details(group: PortfolioGroup) -> html.Div:
    """Create the full position details view"""
    sections = []

    # Add stock section if exists
    stock_section = create_stock_section(group)
    if stock_section:
        sections.append(stock_section)

    # Add options section if exists
    options_section = create_options_section(group)
    if options_section:
        sections.append(options_section)

    # Add combined metrics
    sections.append(create_combined_metrics(group))

    return html.Div(
        [
            html.H3(f"{group.ticker} Position Details", className="mb-4"),
            html.Div(sections, className="position-details"),
        ]
    )
