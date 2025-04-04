"""Chart data transformation utilities.

This module provides functions to transform portfolio data into formats
suitable for visualization with Plotly charts.
"""

from typing import Any

# Import utility functions directly from the main utils module
from .. import utils
from ..data_model import PortfolioGroup, PortfolioSummary
from ..logger import logger


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

    # Calculate total for percentage calculation if needed
    total_value = sum(values)

    # Format values for display
    if use_percentage:
        # Convert to percentages
        display_values = [
            (value / total_value) * 100 if total_value > 0 else 0 for value in values
        ]
        textinfo = "label+percent"
    else:
        # Use absolute values
        display_values = values
        textinfo = "label+value"

    # Create the figure data
    return {
        "data": [
            {
                "labels": labels,
                "values": display_values,
                "type": "pie",
                "hole": 0.4,  # Create a donut chart
                "marker": {
                    "colors": ["#4CAF50", "#F44336", "#2196F3", "#FF9800", "#9E9E9E"],
                },
                "textinfo": textinfo,
                "hoverinfo": "label+percent+value",
                "hovertemplate": "%{label}<br>%{percent}<br>Value: %{value:$,.2f}<extra></extra>",
            }
        ],
        "layout": {
            "margin": {"l": 10, "r": 10, "t": 10, "b": 10},
            "legend": {"orientation": "h", "y": -0.2},
            "height": 300,
            "uirevision": "asset_allocation",  # Preserve zoom/pan state on updates
        },
    }


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
    text_values = [utils.format_currency(value) for value in values]

    # Create colors based on values (positive/negative)
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in values]

    # Create the figure data
    return {
        "data": [
            {
                "x": categories,
                "y": values,
                "type": "bar",
                "marker": {"color": colors},
                "text": text_values,
                "textposition": "auto",
                "hovertemplate": "%{x}<br>%{text}<extra></extra>",
            }
        ],
        "layout": {
            "margin": {"l": 40, "r": 10, "t": 10, "b": 40},
            "yaxis": {
                "title": "Beta-Adjusted Exposure" if use_beta_adjusted else "Exposure",
                "tickformat": "$,.0f",
            },
            "height": 300,
            "uirevision": "exposure_chart",  # Preserve zoom/pan state on updates
        },
    }


def transform_for_position_treemap(
    portfolio_groups: list[PortfolioGroup], group_by: str = "type"
) -> dict[str, Any]:
    """Transform portfolio groups data for the position treemap.

    Args:
        portfolio_groups: List of portfolio groups from the data model
        group_by: How to group the positions ("type" or "ticker")

    Returns:
        Dict containing data and layout for the treemap
    """
    logger.debug(f"Transforming data for position treemap, grouping by {group_by}")

    # Initialize lists for treemap data
    labels = ["All"]  # Root node
    parents = [""]  # Root has no parent
    values = [0]  # Will be calculated as sum of children
    colors = [0]  # For color gradient based on position value

    # Process each portfolio group
    for group in portfolio_groups:
        # Add the ticker as a child of "All" if grouping by ticker
        if group_by == "ticker" and group.total_value != 0:
            labels.append(group.ticker)
            parents.append("All")
            values.append(abs(group.total_value))
            # Use a color value based on whether the position is net long or short
            colors.append(1 if group.total_value > 0 else -1)

        # Process stock position
        if group.stock_position:
            stock = group.stock_position
            if stock.market_value != 0:
                # Determine parent based on grouping
                parent = group.ticker if group_by == "ticker" else "All"

                # Add type category if grouping by type
                if group_by == "type":
                    type_label = "Long Stocks" if stock.quantity > 0 else "Short Stocks"
                    if type_label not in labels:
                        labels.append(type_label)
                        parents.append("All")
                        values.append(0)  # Will be updated as we add positions
                        colors.append(1 if "Long" in type_label else -1)
                    parent = type_label

                # Add the stock position
                position_label = f"{stock.ticker} Stock"
                labels.append(position_label)
                parents.append(parent)
                values.append(abs(stock.market_value))
                colors.append(1 if stock.market_value > 0 else -1)

                # Update parent value
                if parent != "All" and parent in labels:
                    parent_idx = labels.index(parent)
                    values[parent_idx] += abs(stock.market_value)

        # Process option positions
        for option in group.option_positions:
            if option.market_value != 0:
                # Determine parent based on grouping
                parent = group.ticker if group_by == "ticker" else "All"

                # Add type category if grouping by type
                if group_by == "type":
                    if option.option_type == "CALL":
                        type_label = (
                            "Long Calls" if option.quantity > 0 else "Short Calls"
                        )
                    else:  # PUT
                        type_label = (
                            "Long Puts" if option.quantity > 0 else "Short Puts"
                        )

                    if type_label not in labels:
                        labels.append(type_label)
                        parents.append("All")
                        values.append(0)  # Will be updated as we add positions
                        colors.append(1 if "Long" in type_label else -1)
                    parent = type_label

                # Add the option position
                position_label = f"{option.ticker} {option.option_type} {option.strike} {option.expiry}"
                labels.append(position_label)
                parents.append(parent)
                values.append(abs(option.market_value))
                colors.append(1 if option.market_value > 0 else -1)

                # Update parent value
                if parent != "All" and parent in labels:
                    parent_idx = labels.index(parent)
                    values[parent_idx] += abs(option.market_value)

    # Calculate total value for the root node
    values[0] = sum(values[1:])

    # Create a colorscale that shows long positions in green and short in red
    colorscale = [
        [0, "#F44336"],  # Red for short positions
        [0.5, "#FFFFFF"],  # White for neutral
        [1, "#4CAF50"],  # Green for long positions
    ]

    # Create the figure data
    return {
        "data": [
            {
                "type": "treemap",
                "labels": labels,
                "parents": parents,
                "values": values,
                "marker": {
                    "colors": colors,
                    "colorscale": colorscale,
                    "cmid": 0,  # Center of the colorscale
                },
                "textinfo": "label+value",
                "hovertemplate": "<b>%{label}</b><br>Value: %{value:$,.2f}<br>%{percentRoot} of portfolio<extra></extra>",
                "branchvalues": "total",  # Use "total" to show absolute values
            }
        ],
        "layout": {
            "margin": {"l": 10, "r": 10, "t": 10, "b": 10},
            "height": 400,
            "uirevision": "position_treemap",  # Preserve zoom/pan state on updates
        },
    }


def transform_for_sector_chart(
    portfolio_groups: list[PortfolioGroup], compare_to_benchmark: bool = False
) -> dict[str, Any]:
    """Transform portfolio groups data for the sector chart.

    Args:
        portfolio_groups: List of portfolio groups from the data model
        compare_to_benchmark: Whether to include benchmark comparison

    Returns:
        Dict containing data and layout for the sector chart
    """
    logger.debug("Transforming data for sector chart")

    # TODO: Implement actual sector classification
    # For now, use placeholder data

    # Placeholder sector mapping (in a real implementation, this would come from yfinance or another data source)
    sector_mapping = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "GOOGL": "Communication Services",
        "AMZN": "Consumer Cyclical",
        "META": "Communication Services",
        "NVDA": "Technology",
        "TSLA": "Consumer Cyclical",
        "BKNG": "Consumer Cyclical",
        "UBER": "Technology",
        "TCEHY": "Communication Services",
        "TLT": "Fixed Income",
        "FFRHX": "Fixed Income",
        "SPAXX": "Cash",
        "SMH": "Technology",
        "UPRO": "ETF",
    }

    # Default sectors to include
    sectors = [
        "Technology",
        "Communication Services",
        "Consumer Cyclical",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Fixed Income",
        "Cash",
        "ETF",
        "Other",
    ]

    # Calculate sector values from portfolio groups
    sector_values = {sector: 0.0 for sector in sectors}
    total_value = 0.0

    for group in portfolio_groups:
        # Get sector for this ticker
        sector = sector_mapping.get(group.ticker, "Other")

        # Add stock position value
        if group.stock_position:
            sector_values[sector] += abs(group.stock_position.market_value)
            total_value += abs(group.stock_position.market_value)

        # Add option position values
        for option in group.option_positions:
            sector_values[sector] += abs(option.market_value)
            total_value += abs(option.market_value)

    # Convert to percentages
    sector_percentages = {
        sector: (value / total_value) * 100 if total_value > 0 else 0
        for sector, value in sector_values.items()
    }

    # Filter out sectors with zero value
    active_sectors = [sector for sector in sectors if sector_percentages[sector] > 0]
    portfolio_values = [sector_percentages[sector] for sector in active_sectors]

    # Create the data for the chart
    data = [
        {
            "x": active_sectors,
            "y": portfolio_values,
            "type": "bar",
            "name": "Portfolio",
            "marker": {"color": "#2196F3"},
            "hovertemplate": "%{x}<br>%{y:.1f}%<extra></extra>",
        }
    ]

    if compare_to_benchmark:
        # Placeholder benchmark data (S&P 500 sector weights)
        # In a real implementation, this would come from an API or database
        benchmark_mapping = {
            "Technology": 28.5,
            "Communication Services": 8.7,
            "Consumer Cyclical": 10.2,
            "Financial Services": 12.8,
            "Healthcare": 13.5,
            "Industrials": 8.3,
            "Energy": 4.2,
            "Consumer Defensive": 6.5,
            "Utilities": 2.5,
            "Real Estate": 2.4,
            "Basic Materials": 2.4,
            "Fixed Income": 0,
            "Cash": 0,
            "ETF": 0,
            "Other": 0,
        }

        benchmark_values = [
            benchmark_mapping.get(sector, 0) for sector in active_sectors
        ]

        data.append(
            {
                "x": active_sectors,
                "y": benchmark_values,
                "type": "bar",
                "name": "S&P 500",
                "marker": {"color": "#9E9E9E"},
                "hovertemplate": "%{x}<br>%{y:.1f}%<extra></extra>",
            }
        )

    # Create the figure data
    return {
        "data": data,
        "layout": {
            "margin": {"l": 40, "r": 10, "t": 10, "b": 80},
            "yaxis": {"title": "Allocation (%)"},
            "legend": {"orientation": "h", "y": -0.2},
            "barmode": "group",
            "height": 300,
            "uirevision": "sector_chart",  # Preserve zoom/pan state on updates
        },
    }


def create_dashboard_metrics(
    portfolio_summary: PortfolioSummary,
) -> list[dict[str, Any]]:
    """Create dashboard metric cards from portfolio summary.

    Args:
        portfolio_summary: Portfolio summary data from the data model

    Returns:
        List of metric card definitions
    """
    logger.debug("Creating dashboard metrics from portfolio summary")

    # Define the metrics to display
    metrics = [
        {
            "title": "Total Value",
            "value": utils.format_currency(portfolio_summary.total_value_net),
            "help_text": portfolio_summary.help_text.get("total_value_net", ""),
        },
        {
            "title": "Portfolio Beta",
            "value": f"{portfolio_summary.portfolio_beta:.2f}",
            "help_text": portfolio_summary.help_text.get("portfolio_beta", ""),
        },
        {
            "title": "Long Exposure",
            "value": utils.format_currency(portfolio_summary.long_exposure.total_value),
            "help_text": portfolio_summary.help_text.get("long_exposure", ""),
        },
        {
            "title": "Short Exposure",
            "value": utils.format_currency(
                portfolio_summary.short_exposure.total_value
            ),
            "help_text": portfolio_summary.help_text.get("short_exposure", ""),
        },
        {
            "title": "Options Exposure",
            "value": utils.format_currency(
                portfolio_summary.options_exposure.total_value
            ),
            "help_text": portfolio_summary.help_text.get("options_exposure", ""),
        },
    ]

    return metrics
