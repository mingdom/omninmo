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
        Dict containing data and layout for the stacked bar chart
    """
    logger.debug("Transforming data for asset allocation chart")

    # Extract values from portfolio summary
    long_stock_value = portfolio_summary.long_exposure.stock_exposure
    long_option_value = portfolio_summary.long_exposure.option_delta_exposure
    short_stock_value = abs(portfolio_summary.short_exposure.stock_exposure)
    short_option_value = abs(portfolio_summary.short_exposure.option_delta_exposure)
    cash_like_value = portfolio_summary.cash_like_value

    # Create data for the three bars: long exposure, short exposure, and cash
    long_exposure = long_stock_value + long_option_value
    short_exposure = short_stock_value + short_option_value

    # Create the stacked bar chart data
    categories = ["Long Exposure", "Short Exposure", "Cash & Bonds"]

    # Values for each category
    values = [long_exposure, short_exposure, cash_like_value]

    # Note: In the future, we could implement stacked bars for each category
    # to show the breakdown of stocks vs options within each exposure type

    # Format text for display
    if use_percentage:
        total_value = sum(values)
        title_text = "Asset Allocation (% of Portfolio)"

        def text_format(v):
            return f"{(v / total_value * 100):.1f}%" if total_value > 0 else "0.0%"
    else:
        title_text = "Asset Allocation (Exposure)"
        text_format = format_currency

    # Create the chart data with three separate traces
    chart_data = {
        "data": [
            # Long Exposure Bar
            {
                "type": "bar",
                "name": "Long Exposure",
                "x": [categories[0]],
                "y": [values[0]],
                "text": [text_format(values[0])],
                "textposition": "auto",
                "marker": {"color": "#4CAF50"},  # Green for long
                "hoverinfo": "text",
            },
            # Short Exposure Bar
            {
                "type": "bar",
                "name": "Short Exposure",
                "x": [categories[1]],
                "y": [values[1]],
                "text": [text_format(values[1])],
                "textposition": "auto",
                "marker": {"color": "#F44336"},  # Red for short
                "hoverinfo": "text",
            },
            # Cash Bar
            {
                "type": "bar",
                "name": "Cash & Bonds",
                "x": [categories[2]],
                "y": [values[2]],
                "text": [text_format(values[2])],
                "textposition": "auto",
                "marker": {"color": "#9E9E9E"},  # Grey for cash
                "hoverinfo": "text",
            },
        ],
        "layout": {
            "title": title_text,
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.1},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 50},
            "autosize": True,
            "barmode": "group",
            "yaxis": {"title": "Exposure" if not use_percentage else "Percentage"},
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
        # Use the pre-calculated beta-adjusted net exposure
        net_value = (
            portfolio_summary.long_exposure.total_beta_adjusted
            - portfolio_summary.short_exposure.total_beta_adjusted
        )
    else:
        long_value = portfolio_summary.long_exposure.total_exposure
        short_value = portfolio_summary.short_exposure.total_exposure
        options_value = portfolio_summary.options_exposure.total_exposure
        # Use the pre-calculated net market exposure
        net_value = portfolio_summary.net_market_exposure

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
            "yaxis": {"title": "Exposure ($)"},
            "margin": {"l": 50, "r": 20, "t": 30, "b": 50},
            "autosize": True,  # Allow the chart to resize with its container
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

        # Color based on long/short
        color = (
            "#4CAF50" if exposure > 0 else "#F44336"
        )  # Green for long, Red for short
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
                "marker": {"colors": colors},
            }
        ],
        "layout": {
            "title": "Position Size by Exposure",
            "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
            "autosize": True,  # Allow the chart to resize with its container
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
    logger.debug(
        f"Transforming data for sector allocation chart with {len(portfolio_groups)} groups"
    )
    logger.debug(f"Use percentage: {use_percentage}")

    # Collect sector data
    sector_values = {}
    for i, group in enumerate(portfolio_groups):
        logger.debug(f"Processing group {i}: {group.ticker}")
        if group.stock_position:
            position = group.stock_position
            logger.debug(f"  Found stock position: {position.ticker}")

            # Check for sector attribute
            has_sector = hasattr(position, "sector")
            logger.debug(f"  Has sector attribute: {has_sector}")

            # Check for cash-like attribute
            has_cash_like = hasattr(position, "is_cash_like")
            logger.debug(f"  Has is_cash_like attribute: {has_cash_like}")

            if has_cash_like and position.is_cash_like:
                sector = "Cash"
                logger.debug("  Identified as cash-like position")
            else:
                # Use sector from position if available, otherwise "Unknown"
                sector = getattr(position, "sector", "Unknown")
                logger.debug(f"  Sector assigned: {sector}")

            # Add value to sector total
            if sector in sector_values:
                sector_values[sector] += position.market_value
                logger.debug(
                    f"  Added {position.market_value} to existing sector {sector}"
                )
            else:
                sector_values[sector] = position.market_value
                logger.debug(
                    f"  Created new sector {sector} with value {position.market_value}"
                )
        else:
            logger.debug("  No stock position in this group")

    # Convert to lists for chart
    sectors = list(sector_values.keys())
    values = list(sector_values.values())
    logger.debug(f"Sectors found: {sectors}")
    logger.debug(f"Values: {values}")

    # Check if we have any sectors
    if not sectors:
        logger.warning("No sectors found in portfolio data")
        return {
            "data": [],
            "layout": {
                "title": "No sector data available",
                "height": 400,
                "annotations": [
                    {
                        "text": "No sector data available in portfolio",
                        "showarrow": False,
                        "font": {"size": 16},
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5,
                    }
                ],
            },
        }

    # Calculate total for percentage calculation
    total_value = sum(abs(v) for v in values)
    logger.debug(f"Total value: {total_value}")

    # Convert to percentages if requested
    if use_percentage:
        chart_values = [(abs(v) / total_value) * 100 for v in values]
        text_values = [f"{v:.1f}%" for v in chart_values]
        title_text = "Sector Allocation (% of Portfolio)"
        logger.debug(f"Using percentage values: {chart_values}")
    else:
        chart_values = [abs(v) for v in values]
        text_values = [format_currency(value) for value in chart_values]
        title_text = "Sector Allocation (Value)"
        logger.debug(f"Using absolute values: {chart_values}")

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

    logger.debug(f"Created sector chart with {len(sectors)} sectors")

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
