"""Chart data transformation utilities.

This module provides functions to transform portfolio data into formats
suitable for visualization with Plotly charts.
"""

from typing import Any

from .data_model import PortfolioGroup, PortfolioSummary
from .logger import logger
from .portfolio import calculate_beta_adjusted_net_exposure
from .utils import format_currency

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
        short_value = portfolio_summary.short_exposure.total_beta_adjusted
        options_value = portfolio_summary.options_exposure.total_beta_adjusted
        # Use the utility function for beta-adjusted net exposure
        net_value = calculate_beta_adjusted_net_exposure(
            portfolio_summary.long_exposure.total_beta_adjusted,
            portfolio_summary.short_exposure.total_beta_adjusted,
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

    # Colors for the bars - modern financial palette
    colors = ["#27AE60", "#E74C3C", "#9B59B6", "#3498DB"]  # Green, Red, Purple, Blue

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

        # Color based on long/short - using modern financial colors
        color = (
            "#27AE60" if exposure > 0 else "#E74C3C"
        )  # Modern green for long, modern red for short
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
                "marker": {
                    "line": {"width": 1, "color": "#FFFFFF"},
                    "colors": [
                        "#3498DB",
                        "#2ECC71",
                        "#9B59B6",
                        "#F1C40F",
                        "#E74C3C",
                        "#1ABC9C",
                        "#34495E",
                        "#D35400",
                        "#7F8C8D",
                        "#27AE60",
                        "#2980B9",
                        "#8E44AD",
                    ],
                },
                "textfont": {
                    "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                    "size": 11,
                    "color": "#FFFFFF",
                },
                "hole": 0.4,  # Creates a donut chart for a more modern look
            }
        ],
        "layout": {
            "title": {"text": title_text, "font": {"size": 16, "color": "#2C3E50"}},
            "showlegend": True,
            "legend": {
                "orientation": "h",
                "y": -0.1,
                "bgcolor": "rgba(255,255,255,0.9)",
            },
            "margin": {"l": 0, "r": 0, "t": 50, "b": 0, "pad": 4},
            "height": 400,
            "paper_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
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
