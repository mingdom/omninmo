"""Chart data transformation utilities.

This module provides functions to transform portfolio data into formats
suitable for visualization with Plotly charts.
"""

from typing import Any

from .data_model import PortfolioGroup, PortfolioSummary
from .logger import logger
from .utils import format_currency


def transform_for_asset_allocation(
    portfolio_summary: PortfolioSummary, use_percentage: bool = True
) -> dict[str, Any]:
    """Transform portfolio summary data for the asset allocation chart.

    Args:
        portfolio_summary: Portfolio summary data from the data model
        use_percentage: Whether to use percentage values (True) or absolute values (False)

    Returns:
        Dict containing data and layout for the pie chart
    """
    logger.debug("Transforming data for asset allocation chart")

    # Extract values from portfolio summary
    long_stock_value = portfolio_summary.long_exposure.stock_value
    short_stock_value = abs(portfolio_summary.short_exposure.stock_value)
    long_option_value = portfolio_summary.long_exposure.option_delta_value
    short_option_value = abs(portfolio_summary.short_exposure.option_delta_value)
    cash_like_value = portfolio_summary.cash_like_value

    # Create labels and values arrays
    labels = [
        "Long Stocks",
        "Short Stocks",
        "Long Options",
        "Short Options",
        "Cash-like",
    ]
    values = [
        long_stock_value,
        short_stock_value,
        long_option_value,
        short_option_value,
        cash_like_value,
    ]

    # Add options exposure as a separate category
    labels.append("Options Exposure")
    values.append(portfolio_summary.options_exposure.total_value)

    # Calculate total for percentage calculation
    total_value = sum(values)

    # Convert to percentages if requested
    if use_percentage:
        values = [(v / total_value) * 100 for v in values]
        text_values = [f"{v:.1f}%" for v in values]
        title_text = "Asset Allocation (% of Portfolio)"
    else:
        text_values = [format_currency(value) for value in values]
        title_text = "Asset Allocation (Value)"

    # Create the chart data
    chart_data = {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "text": text_values,
                "textinfo": "label+text",
                "hoverinfo": "label+text+percent",
                "marker": {
                    "colors": [
                        "#4CAF50",  # Green for long stocks
                        "#F44336",  # Red for short stocks
                        "#2196F3",  # Blue for long options
                        "#FF9800",  # Orange for short options
                        "#9E9E9E",  # Grey for cash
                        "#673AB7",  # Purple for options exposure
                    ]
                },
            }
        ],
        "layout": {
            "title": title_text,
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.1},
            "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
            "height": 400,
        },
    }

    return chart_data


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
        short_value = portfolio_summary.short_exposure.total_beta_adjusted
        options_value = portfolio_summary.options_exposure.total_beta_adjusted
    else:
        long_value = portfolio_summary.long_exposure.total_value
        short_value = portfolio_summary.short_exposure.total_value
        options_value = portfolio_summary.options_exposure.total_value

    # Calculate net value
    net_value = (
        long_value + short_value
    )  # Note: options_value is already included in long/short

    # Categories and values for the chart
    categories = ["Long", "Short", "Options", "Net"]
    values = [long_value, short_value, options_value, net_value]

    # Format values for display
    text_values = [format_currency(value) for value in values]

    # Colors for the bars
    colors = ["#4CAF50", "#F44336", "#673AB7", "#2196F3"]  # Green, Red, Purple, Blue

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
                "marker": {"color": colors},
            }
        ],
        "layout": {
            "title": "Market Exposure"
            + (" (Beta-Adjusted)" if use_beta_adjusted else ""),
            "xaxis": {"title": "Exposure Type"},
            "yaxis": {"title": "Value ($)"},
            "margin": {"l": 50, "r": 20, "t": 30, "b": 50},
            "height": 400,
        },
    }

    return chart_data


def transform_for_treemap(
    portfolio_groups: list[PortfolioGroup], group_by: str = "type"
) -> dict[str, Any]:
    """Transform portfolio groups data for the treemap chart.

    Args:
        portfolio_groups: List of portfolio groups from the data model
        group_by: How to group the positions ('type' or 'ticker')

    Returns:
        Dict containing data and layout for the treemap chart
    """
    logger.debug(f"Transforming data for treemap chart, grouping by: {group_by}")

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

    # Process groups based on grouping type
    if group_by == "type":
        # Add type nodes
        type_nodes = ["Stocks", "Options", "Cash"]
        type_colors = ["#4CAF50", "#2196F3", "#9E9E9E"]  # Green, Blue, Grey

        for node, color in zip(type_nodes, type_colors, strict=False):
            labels.append(node)
            parents.append("Portfolio")
            values.append(0)  # Will be sum of children
            texts.append(node)
            colors.append(color)

        # Add individual positions
        for group in portfolio_groups:
            # Add stock position (if exists)
            if group.stock_position:
                position = group.stock_position
                parent = "Stocks"
                value = abs(position.market_value)
                text = (
                    f"{position.ticker}: {format_currency(position.market_value)}<br>"
                    f"Quantity: {position.quantity:,.0f}"
                )
                # Determine color based on long/short
                color = (
                    "#4CAF50" if position.quantity > 0 else "#F44336"
                )  # Green or Red

                labels.append(position.ticker)
                parents.append(parent)
                values.append(value)
                texts.append(text)
                colors.append(color)

            # Add option positions
            for position in group.option_positions:
                parent = "Options"
                value = abs(position.market_value)
                # Create a description from the available attributes
                option_desc = f"{position.ticker} {position.option_type} {position.strike} {position.expiry}"
                text = (
                    f"{option_desc}: {format_currency(position.market_value)}<br>"
                    f"Quantity: {position.quantity:,.0f}<br>"
                    f"Delta: {position.delta:.2f}"
                )
                # Determine color based on call/put and long/short
                if position.option_type == "CALL":
                    color = (
                        "#2196F3" if position.quantity > 0 else "#FF9800"
                    )  # Blue or Orange
                else:
                    color = (
                        "#673AB7" if position.quantity > 0 else "#E91E63"
                    )  # Purple or Pink

                labels.append(f"{position.ticker} {position.option_type}")
                parents.append(parent)
                values.append(value)
                texts.append(text)
                colors.append(color)

        # Add cash positions
        for group in portfolio_groups:
            if (
                group.stock_position
                and hasattr(group.stock_position, "is_cash_like")
                and group.stock_position.is_cash_like
            ):
                position = group.stock_position
                parent = "Cash"
                value = abs(position.market_value)
                text = f"{position.ticker}: {format_currency(position.market_value)}"
                color = "#9E9E9E"  # Grey for cash

                labels.append(f"Cash: {position.ticker}")
                parents.append(parent)
                values.append(value)
                texts.append(text)
                colors.append(color)

    else:  # group_by == "ticker"
        # Add ticker nodes (one for each group)
        for group in portfolio_groups:
            ticker = group.ticker
            # Calculate total value
            total_value = 0
            if group.stock_position:
                total_value += abs(group.stock_position.market_value)
            for p in group.option_positions:
                total_value += abs(p.market_value)

            # Skip empty groups
            if total_value == 0:
                continue

            labels.append(ticker)
            parents.append("Portfolio")
            values.append(total_value)
            texts.append(f"{ticker}: {format_currency(total_value)}")
            colors.append("#2196F3")  # Blue for all tickers

            # Add stock position under ticker (if exists)
            if group.stock_position:
                position = group.stock_position
                value = abs(position.market_value)
                text = (
                    f"{position.ticker}: {format_currency(position.market_value)}<br>"
                    f"Quantity: {position.quantity:,.0f}"
                )
                # Determine color based on long/short
                color = (
                    "#4CAF50" if position.quantity > 0 else "#F44336"
                )  # Green or Red

                labels.append(f"{ticker} Stock")
                parents.append(ticker)
                values.append(value)
                texts.append(text)
                colors.append(color)

            # Add option positions
            for position in group.option_positions:
                value = abs(position.market_value)
                # Create a description from the available attributes
                option_desc = f"{position.ticker} {position.option_type} {position.strike} {position.expiry}"
                text = (
                    f"{option_desc}: {format_currency(position.market_value)}<br>"
                    f"Quantity: {position.quantity:,.0f}<br>"
                    f"Delta: {position.delta:.2f}"
                )
                # Determine color based on call/put and long/short
                if position.option_type == "CALL":
                    color = (
                        "#2196F3" if position.quantity > 0 else "#FF9800"
                    )  # Blue or Orange
                else:
                    color = (
                        "#673AB7" if position.quantity > 0 else "#E91E63"
                    )  # Purple or Pink

                option_type = position.option_type
                labels.append(f"{ticker} {option_type}")
                parents.append(ticker)
                values.append(value)
                texts.append(text)
                colors.append(color)

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
                "marker": {"colors": colors},
            }
        ],
        "layout": {
            "title": f"Position Size Treemap (Grouped by {group_by.capitalize()})",
            "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
            "height": 500,
        },
    }

    return chart_data


def transform_for_sector_allocation(
    portfolio_groups: list[PortfolioGroup], use_percentage: bool = True
) -> dict[str, Any]:
    """Transform portfolio groups data for the sector allocation chart.

    Args:
        portfolio_groups: List of portfolio groups from the data model
        use_percentage: Whether to use percentage values (True) or absolute values (False)

    Returns:
        Dict containing data and layout for the pie chart
    """
    logger.debug("Transforming data for sector allocation chart")

    # Collect sector data
    sector_values = {}
    for group in portfolio_groups:
        if group.stock_position:
            position = group.stock_position
            if hasattr(position, "is_cash_like") and position.is_cash_like:
                sector = "Cash"
            else:
                # Use sector from position if available, otherwise "Unknown"
                sector = getattr(position, "sector", "Unknown")

            # Add value to sector total
            if sector in sector_values:
                sector_values[sector] += position.market_value
            else:
                sector_values[sector] = position.market_value

    # Convert to lists for chart
    sectors = list(sector_values.keys())
    values = list(sector_values.values())

    # Calculate total for percentage calculation
    total_value = sum(abs(v) for v in values)

    # Convert to percentages if requested
    if use_percentage:
        chart_values = [(abs(v) / total_value) * 100 for v in values]
        text_values = [f"{v:.1f}%" for v in chart_values]
        title_text = "Sector Allocation (% of Portfolio)"
    else:
        chart_values = [abs(v) for v in values]
        text_values = [format_currency(value) for value in chart_values]
        title_text = "Sector Allocation (Value)"

    # Create the chart data
    chart_data = {
        "data": [
            {
                "type": "pie",
                "labels": sectors,
                "values": chart_values,
                "text": text_values,
                "textinfo": "label+text",
                "hoverinfo": "label+text+percent",
            }
        ],
        "layout": {
            "title": title_text,
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.1},
            "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
            "height": 400,
        },
    }

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
