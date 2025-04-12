"""Chart data transformation utilities.

This module provides functions to transform portfolio data into formats
suitable for visualization with Plotly charts.
"""

from typing import Any

from .data_model import PortfolioGroup, PortfolioSummary
from .logger import logger
from .portfolio import calculate_beta_adjusted_net_exposure
from .utils import format_currency


class ChartColors:
    """Chart color constants for consistent visualization.

    This class defines the color palette used across all charts in the application.
    Use these constants instead of hardcoded hex values to ensure consistency.
    """

    # Position colors
    LONG = "#1A5D38"  # Dark green for long positions
    SHORT = "#2F3136"  # Dark gray for short positions
    OPTIONS = "#9B59B6"  # Purple for options
    NET = "#3498DB"  # Blue for net values


# transform_for_asset_allocation function has been removed in favor of the more accurate Exposure Chart


def transform_for_exposure_chart(
    portfolio_summary: PortfolioSummary, use_beta_adjusted: bool = False
) -> dict[str, Any]:
    """Transform portfolio summary data for the exposure chart.

    Args:
        portfolio_summary: Portfolio summary data from the data model
        use_beta_adjusted: Whether to use beta-adjusted values

    Returns:
        Dict containing data and layout for the bar chart
    """
    logger.debug("Transforming data for exposure chart")

    # Extract values based on whether we want beta-adjusted or not
    if use_beta_adjusted:
        long_value = portfolio_summary.long_exposure.total_beta_adjusted
        # Show short exposure as negative
        short_value = portfolio_summary.short_exposure.total_beta_adjusted
        options_value = portfolio_summary.options_exposure.total_beta_adjusted
        # Use the utility function for beta-adjusted net exposure
        net_value = calculate_beta_adjusted_net_exposure(
            portfolio_summary.long_exposure.total_beta_adjusted,
            portfolio_summary.short_exposure.total_beta_adjusted,
        )
    else:
        long_value = portfolio_summary.long_exposure.total_exposure
        # Show short exposure as negative
        short_value = portfolio_summary.short_exposure.total_exposure
        options_value = portfolio_summary.options_exposure.total_exposure
        # Use the pre-calculated net market exposure
        net_value = portfolio_summary.net_market_exposure

    # Categories and values for the chart
    categories = ["Long", "Short", "Options", "Net"]
    values = [long_value, short_value, options_value, net_value]

    # Format values for display
    text_values = [format_currency(value) for value in values]

    # Colors for the bars - using ChartColors constants
    colors = [
        ChartColors.LONG,
        ChartColors.SHORT,
        ChartColors.OPTIONS,
        ChartColors.NET,
    ]

    # Create the chart data
    chart_data = {
        "data": [
            {
                "type": "bar",
                "x": categories,
                "y": values,
                "text": text_values,
                "textposition": "auto",
                "hoverinfo": "text",
                "hovertemplate": "<b>%{x}</b><br>%{text}<extra></extra>",
                "marker": {"color": colors, "line": {"width": 0}, "opacity": 0.9},
            }
        ],
        "layout": {
            "title": {
                "text": "Market Exposure"
                + (" (Beta-Adjusted)" if use_beta_adjusted else ""),
                "font": {"size": 16, "color": "#2C3E50"},
                "x": 0.5,  # Center the title
                "xanchor": "center",
            },
            "xaxis": {
                "title": "Exposure Type",
                "titlefont": {"size": 12, "color": "#7F8C8D"},
                "tickfont": {"size": 11},
            },
            "yaxis": {
                "title": "Exposure ($)",
                "titlefont": {"size": 12, "color": "#7F8C8D"},
                "tickfont": {"size": 11},
                "gridcolor": "#ECF0F1",
                "zerolinecolor": "#BDC3C7",
            },
            "margin": {"l": 50, "r": 20, "t": 50, "b": 50, "pad": 4},
            "autosize": True,  # Allow the chart to resize with its container
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
        },
    }

    return chart_data


def transform_for_treemap(
    portfolio_groups: list[PortfolioGroup], _group_by: str = "ticker"
) -> dict[str, Any]:
    """Transform portfolio groups data for the treemap chart.

    Args:
        portfolio_groups: List of portfolio groups from the data model
        _group_by: Unused parameter (kept for backward compatibility)

    Returns:
        Dict containing data and layout for the treemap chart
    """
    logger.debug("Transforming data for treemap chart (grouped by ticker)")

    # Initialize lists for treemap data
    labels = []
    parents = []
    values = []
    texts = []
    colors = []

    # Add root node
    labels.append("Portfolio")
    parents.append("")
    values.append(0)  # Will be sum of children
    texts.append("Portfolio")
    colors.append("#FFFFFF")  # White for root

    # Group by ticker
    # First, collect all unique tickers and calculate their total exposure
    ticker_exposures = {}
    for group in portfolio_groups:
        ticker = group.ticker
        exposure = 0

        # Add stock position exposure
        if group.stock_position:
            # Use market exposure for stocks
            exposure += group.stock_position.market_exposure

        # Add option positions exposure (delta exposure)
        for option in group.option_positions:
            exposure += option.delta_exposure

        # Store the net exposure value for sizing (not absolute)
        ticker_exposures[ticker] = exposure

    # Sort tickers by absolute exposure (largest first)
    sorted_tickers = sorted(
        ticker_exposures.keys(), key=lambda t: abs(ticker_exposures[t]), reverse=True
    )

    # Add ticker nodes
    for ticker in sorted_tickers:
        # Skip tickers with zero exposure
        if ticker_exposures[ticker] == 0:
            continue

        exposure = ticker_exposures[ticker]
        labels.append(ticker)
        parents.append("Portfolio")
        values.append(abs(exposure))  # Use absolute exposure for sizing
        texts.append(f"{ticker}: {format_currency(exposure)}")

        # Color based on long/short - using ChartColors constants
        color = ChartColors.LONG if exposure > 0 else ChartColors.SHORT
        colors.append(color)

    # We don't need to add individual positions anymore - just show the ticker level

    # Create the chart data
    chart_data = {
        "data": [
            {
                "type": "treemap",
                "labels": labels,
                "parents": parents,
                "values": values,
                "text": texts,
                "hoverinfo": "text",
                "marker": {
                    "colors": colors,
                    "line": {"width": 1, "color": "#FFFFFF"},
                    "pad": 3,
                },
                "textfont": {
                    "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                    "size": 12,
                    "color": "#FFFFFF",
                },
                "hovertemplate": "%{text}<extra></extra>",
            }
        ],
        "layout": {
            "title": {
                "text": "Position Size by Exposure",
                "font": {"size": 16, "color": "#2C3E50"},
                "x": 0.5,  # Center the title
                "xanchor": "center",
            },
            "margin": {"l": 0, "r": 0, "t": 50, "b": 0, "pad": 4},
            "autosize": True,  # Allow the chart to resize with its container
            "paper_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
        },
    }

    return chart_data


# Sector allocation chart has been removed as it's not currently supported


def create_dashboard_metrics(
    portfolio_summary: PortfolioSummary,
) -> list[dict[str, str]]:
    """Create a list of key metrics for the dashboard.

    Args:
        portfolio_summary: Portfolio summary data from the data model

    Returns:
        List of dictionaries with title, value, and help_text for each metric
    """
    logger.debug("Creating dashboard metrics")

    # Define the metrics to display
    metrics = [
        {
            "title": "Total Value",
            "value": format_currency(portfolio_summary.total_value_net),
            "help_text": portfolio_summary.help_text.get("total_value_net", ""),
        },
        {
            "title": "Portfolio Beta",
            "value": f"{portfolio_summary.portfolio_beta:.2f}",
            "help_text": portfolio_summary.help_text.get("portfolio_beta", ""),
        },
        {
            "title": "Long Exposure",
            "value": format_currency(portfolio_summary.long_exposure.total_value),
            "help_text": portfolio_summary.help_text.get("long_exposure", ""),
        },
        {
            "title": "Short Exposure",
            "value": format_currency(portfolio_summary.short_exposure.total_value),
            "help_text": portfolio_summary.help_text.get("short_exposure", ""),
        },
        {
            "title": "Options Exposure",
            "value": format_currency(portfolio_summary.options_exposure.total_value),
            "help_text": portfolio_summary.help_text.get("options_exposure", ""),
        },
    ]

    return metrics
