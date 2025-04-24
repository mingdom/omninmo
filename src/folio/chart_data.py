"""Chart data transformation utilities.

This module provides functions to transform portfolio data into formats
suitable for visualization with Plotly charts.
"""

from typing import Any

from .data_model import PortfolioGroup, PortfolioSummary
from .logger import logger
from .portfolio import calculate_beta_adjusted_net_exposure
from .portfolio_value import (
    calculate_component_percentages,
    get_portfolio_component_values,
)
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

    # Allocations chart colors
    LONG_OPTIONS = "#4CAF50"  # Light green for long options
    SHORT_OPTIONS = "#607D8B"  # Light gray for short options
    CASH = "#9E9E9E"  # Medium gray for cash
    PENDING = "#BDBDBD"  # Light gray for pending activity


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

    # Log portfolio summary fields for debugging
    logger.debug(
        f"Portfolio summary net_market_exposure: {portfolio_summary.net_market_exposure}"
    )
    logger.debug(f"Portfolio summary long_exposure: {portfolio_summary.long_exposure}")
    logger.debug(
        f"Portfolio summary short_exposure: {portfolio_summary.short_exposure}"
    )
    logger.debug(
        f"Portfolio summary options_exposure: {portfolio_summary.options_exposure}"
    )

    # Extract values based on whether we want beta-adjusted or not
    if use_beta_adjusted:
        logger.debug("Using beta-adjusted values for exposure chart")
        long_value = portfolio_summary.long_exposure.total_beta_adjusted
        # Show short exposure as negative
        short_value = portfolio_summary.short_exposure.total_beta_adjusted
        options_value = portfolio_summary.options_exposure.total_beta_adjusted
        # Use the utility function for beta-adjusted net exposure
        net_value = calculate_beta_adjusted_net_exposure(
            portfolio_summary.long_exposure.total_beta_adjusted,
            portfolio_summary.short_exposure.total_beta_adjusted,
        )
        logger.debug(
            f"Beta-adjusted values - Long: {long_value}, Short: {short_value}, Options: {options_value}, Net: {net_value}"
        )
    else:
        logger.debug("Using net exposure values for exposure chart")
        long_value = portfolio_summary.long_exposure.total_exposure
        # Show short exposure as negative
        short_value = portfolio_summary.short_exposure.total_exposure
        options_value = portfolio_summary.options_exposure.total_exposure
        # Use the pre-calculated net market exposure
        net_value = portfolio_summary.net_market_exposure
        logger.debug(
            f"Net exposure values - Long: {long_value}, Short: {short_value}, Options: {options_value}, Net: {net_value}"
        )

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
    logger.debug(f"Number of portfolio groups: {len(portfolio_groups)}")

    # Log some details about the first few groups for debugging
    for i, group in enumerate(portfolio_groups[:3]):
        logger.debug(f"Group {i} ticker: {group.ticker}")
        logger.debug(f"Group {i} net_exposure: {group.net_exposure}")
        if group.stock_position:
            logger.debug(
                f"Group {i} stock position market_exposure: {group.stock_position.market_exposure}"
            )
        logger.debug(f"Group {i} has {len(group.option_positions)} option positions")

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
        stock_exposure = 0
        if group.stock_position:
            # Use market exposure for stocks
            stock_exposure = group.stock_position.market_exposure
            logger.debug(f"Ticker {ticker} stock exposure: {stock_exposure}")
            exposure += stock_exposure

        # Add option positions exposure (delta exposure)
        option_exposure = 0
        for option in group.option_positions:
            logger.debug(
                f"Ticker {ticker} option {option.option_type} delta_exposure: {option.delta_exposure}"
            )
            option_exposure += option.delta_exposure

        exposure += option_exposure
        logger.debug(
            f"Ticker {ticker} total exposure: {exposure} (stock: {stock_exposure}, options: {option_exposure})"
        )

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


def transform_for_allocations_chart(
    portfolio_summary: PortfolioSummary,
) -> dict[str, Any]:
    """Transform portfolio summary data for the allocations stacked bar chart.

    This function takes a portfolio summary and transforms it into a format
    suitable for a stacked bar chart showing portfolio allocations. The chart
    has four main categories:
    - Long: Stacked with Long Stocks and Long Options
    - Short: Stacked with Short Stocks and Short Options (negative values)
    - Cash: Cash-like positions
    - Pending: Pending activity

    IMPORTANT: Short values are stored as negative numbers in the portfolio summary.
    For display purposes in the chart, we use the absolute values but maintain
    separate bars for long and short positions.

    Args:
        portfolio_summary: The portfolio summary to transform

    Returns:
        A dictionary with 'data' and 'layout' keys suitable for a Plotly chart
    """
    logger.debug("Transforming data for allocations chart")

    # Skip empty portfolios
    if portfolio_summary.portfolio_estimate_value == 0:
        logger.warning("Empty portfolio - no data for allocations chart")
        return {
            "data": [],
            "layout": {
                "height": 300,
                "annotations": [
                    {
                        "text": "No portfolio data available",
                        "showarrow": False,
                        "font": {"color": "#7F8C8D"},
                    }
                ],
            },
        }

    # Get component values (short values are negative)
    values = get_portfolio_component_values(portfolio_summary)

    # Calculate percentages
    percentages = calculate_component_percentages(values)

    # Format values for display
    long_stock_text = f"Long Stocks: {format_currency(values['long_stock'])} ({abs(percentages['long_stock']):.1f}%)"
    short_stock_text = f"Short Stocks: {format_currency(abs(values['short_stock']))} ({abs(percentages['short_stock']):.1f}%)"
    long_option_text = f"Long Options: {format_currency(values['long_option'])} ({abs(percentages['long_option']):.1f}%)"
    short_option_text = f"Short Options: {format_currency(abs(values['short_option']))} ({abs(percentages['short_option']):.1f}%)"
    cash_text = (
        f"Cash: {format_currency(values['cash'])} ({abs(percentages['cash']):.1f}%)"
    )
    pending_text = f"Pending: {format_currency(values['pending'])} ({abs(percentages['pending']):.1f}%)"

    # Create the stacked bar chart data with separate traces for each category
    chart_data = {
        "data": [
            # Long position group
            # Long Stocks (bottom of "Long" stack)
            {
                "name": "Long Stocks",
                "x": ["Long"],
                "y": [values["long_stock"]],
                "type": "bar",
                "marker": {"color": ChartColors.LONG},
                "text": [long_stock_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Long Options (top of "Long" stack)
            {
                "name": "Long Options",
                "x": ["Long"],
                "y": [values["long_option"]],
                "type": "bar",
                "marker": {"color": ChartColors.LONG_OPTIONS},
                "text": [long_option_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Short position group
            # Short Stocks (bottom of "Short" stack)
            {
                "name": "Short Stocks",
                "x": ["Short"],
                "y": [abs(values["short_stock"])],  # Use absolute value for display
                "type": "bar",
                "marker": {"color": ChartColors.SHORT},
                "text": [short_stock_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Short Options (top of "Short" stack)
            {
                "name": "Short Options",
                "x": ["Short"],
                "y": [abs(values["short_option"])],  # Use absolute value for display
                "type": "bar",
                "marker": {"color": ChartColors.SHORT_OPTIONS},
                "text": [short_option_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Cash (single bar)
            {
                "name": "Cash",
                "x": ["Cash"],
                "y": [values["cash"]],
                "type": "bar",
                "marker": {"color": ChartColors.CASH},
                "text": [cash_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Pending (single bar)
            {
                "name": "Pending",
                "x": ["Pending"],
                "y": [values["pending"]],
                "type": "bar",
                "marker": {"color": ChartColors.PENDING},
                "text": [pending_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Portfolio Allocation",
                "font": {"size": 16, "color": "#2C3E50"},
                "x": 0.5,  # Center the title
                "xanchor": "center",
            },
            "barmode": "stack",
            "margin": {"l": 60, "r": 60, "t": 50, "b": 40, "pad": 4},
            "autosize": True,  # Allow the chart to resize with its container
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
            "showlegend": True,
            "legend": {
                "orientation": "h",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.15,
            },
            "yaxis": {
                "title": "Value ($)",
                "tickformat": "$,.0f",
                "gridcolor": "#E5E5E5",
            },
            "yaxis2": {
                "title": "Percentage (%)",
                "overlaying": "y",
                "side": "right",
                "tickformat": ".1f%",
                "range": [0, 100],  # Fixed range for percentage
                "tickmode": "array",
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0%", "25%", "50%", "75%", "100%"],
                "gridcolor": "#E5E5E5",
            },
            "height": 300,
        },
    }

    # Calculate the maximum y-value for setting the y-axis range
    max_value = max(
        values["long_stock"] + values["long_option"],
        abs(values["short_stock"]) + abs(values["short_option"]),
        values["cash"],
        values["pending"],
        1,  # Ensure we have a non-zero range
    )

    # Set the y-axis range with some padding
    chart_data["layout"]["yaxis"]["range"] = [0, max_value * 1.1]

    return chart_data


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
