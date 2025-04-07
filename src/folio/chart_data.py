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


def transform_for_spy_sensitivity_chart(
    portfolio_summary: PortfolioSummary,
    portfolio_groups: list[PortfolioGroup],
    spy_changes: list[float] | None = None,
) -> dict[str, Any]:
    """Transform portfolio data for the SPY sensitivity chart.

    This chart shows how the portfolio would perform when SPY moves up or down
    by various percentages, using each position's beta to estimate the impact.

    The calculation recalculates each position's value individually based on its beta,
    then categorizes them as long or short exposure, calculates the net market exposure,
    and finally adds the cash value to get the total portfolio value. This matches how
    portfolio_estimate_value is calculated in the codebase.

    Args:
        portfolio_summary: Portfolio summary data from the data model
        portfolio_groups: List of portfolio groups from the data model
        spy_changes: List of SPY percentage changes to calculate (default: -30% to +30% in 10% increments)

    Returns:
        Dict containing data and layout for the line chart
    """
    logger.debug("Transforming data for SPY sensitivity chart")

    # Default SPY changes if not provided - using more points to better show non-linearity
    if spy_changes is None:
        spy_changes = [-30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30]

    # Get the cash value (which doesn't change with market movements)
    cash_value = portfolio_summary.cash_like_value

    # Log portfolio composition to help understand why the chart might appear linear
    total_value = portfolio_summary.portfolio_estimate_value
    stock_value = sum(
        g.stock_position.market_value if g.stock_position else 0
        for g in portfolio_groups
    )
    option_value = sum(
        sum(o.market_value for o in g.option_positions) for g in portfolio_groups
    )

    logger.debug("Portfolio composition:")
    logger.debug(f"  Total value: {format_currency(total_value)}")
    logger.debug(
        f"  Cash value: {format_currency(cash_value)} ({cash_value / total_value * 100:.1f}% of portfolio)"
    )
    logger.debug(
        f"  Stock value: {format_currency(stock_value)} ({stock_value / total_value * 100:.1f}% of portfolio)"
    )
    logger.debug(
        f"  Option value: {format_currency(option_value)} ({option_value / total_value * 100:.1f}% of portfolio)"
    )
    logger.debug(f"  Portfolio beta: {portfolio_summary.portfolio_beta:.2f}")

    # Calculate portfolio value at each SPY change percentage
    portfolio_values = []
    position_contributions = []

    for spy_change_pct in spy_changes:
        spy_change_decimal = spy_change_pct / 100.0  # Convert to decimal
        logger.debug(f"Calculating for SPY change: {spy_change_pct}%")

        # For each SPY change, we'll recalculate:
        # 1. Long exposure (stocks + options with positive delta)
        # 2. Short exposure (stocks + options with negative delta)
        # 3. Net market exposure (long - short)
        # 4. Portfolio value (net market exposure + cash)
        long_exposure = 0.0
        short_exposure = 0.0
        position_detail = []

        # Process each group (stock + options)
        for group in portfolio_groups:
            group_ticker = group.ticker

            # Process stock position if it exists
            if group.stock_position:
                stock = group.stock_position
                stock_beta = stock.beta
                stock_value = stock.market_exposure  # Current market value
                stock_quantity = stock.quantity

                # Calculate new stock value based on its beta
                stock_pct_change = stock_beta * spy_change_decimal
                new_stock_value = stock_value * (1 + stock_pct_change)

                # Add to long or short exposure based on position direction
                if stock_quantity >= 0:  # Long position
                    long_exposure += new_stock_value
                else:  # Short position
                    short_exposure += abs(
                        new_stock_value
                    )  # Use absolute value for short

                position_detail.append(
                    {
                        "ticker": group_ticker,
                        "type": "stock",
                        "beta": stock_beta,
                        "original_value": stock_value,
                        "new_value": new_stock_value,
                        "pct_change": stock_pct_change * 100,  # Convert to percentage
                    }
                )

            # Process option positions
            for option in group.option_positions:
                from .option_utils import calculate_option_delta

                option_beta = option.beta
                option_value = option.market_exposure
                current_delta = option.delta
                current_delta_exposure = option.delta_exposure

                # Track whether we use linear approximation for this option
                linear_approx = False

                # Get the current underlying price (we need this to calculate the new delta)
                current_underlying_price = 0
                price_source = "none"

                # First try to get it from the option's underlying_price attribute
                if hasattr(option, "underlying_price") and option.underlying_price > 0:
                    current_underlying_price = option.underlying_price
                    price_source = "option.underlying_price"
                    logger.debug(
                        f"Using underlying_price attribute: {current_underlying_price}"
                    )

                # Next try to get it from the stock position
                elif hasattr(group, "stock_position") and group.stock_position:
                    # Check if current_price exists
                    if hasattr(group.stock_position, "current_price"):
                        current_underlying_price = group.stock_position.current_price
                        price_source = "stock.current_price"
                        logger.debug(
                            f"Using stock.current_price: {current_underlying_price}"
                        )
                    else:
                        # Log the available attributes for debugging
                        stock_attrs = dir(group.stock_position)
                        logger.error(
                            f"StockPosition has no current_price attribute. Available attributes: {stock_attrs}"
                        )
                        logger.error(
                            f"StockPosition market_exposure: {group.stock_position.market_exposure}, quantity: {group.stock_position.quantity}"
                        )

                # Finally try to derive it from notional value
                elif option.notional_value > 0 and option.quantity != 0:
                    current_underlying_price = option.notional_value / (
                        100 * abs(option.quantity)
                    )
                    price_source = "derived from notional_value"
                    logger.debug(
                        f"Derived price from notional_value: {current_underlying_price}"
                    )

                # Log the result
                if current_underlying_price > 0:
                    logger.debug(
                        f"Found underlying price for {option.ticker}: {current_underlying_price} (source: {price_source})"
                    )
                else:
                    logger.error(
                        f"Could not determine underlying price for {option.ticker} from any source"
                    )

                if current_underlying_price > 0:
                    # Calculate the new underlying price based on the SPY change and the underlying's beta
                    # Use the underlying_beta if available, otherwise use the group's beta
                    underlying_beta = (
                        option.underlying_beta
                        if hasattr(option, "underlying_beta")
                        and option.underlying_beta != 0
                        else group.beta
                    )
                    if underlying_beta == 0:
                        underlying_beta = 1.0  # Default to 1.0 if we don't have a beta

                    underlying_pct_change = underlying_beta * spy_change_decimal
                    new_underlying_price = current_underlying_price * (
                        1 + underlying_pct_change
                    )

                    try:
                        # Log the option details for debugging
                        logger.debug(
                            f"Option {option.ticker} ({option.option_type}, strike={option.strike})"
                        )
                        logger.debug(
                            f"  Current underlying price: {current_underlying_price:.2f}, New: {new_underlying_price:.2f} (change: {underlying_pct_change * 100:.2f}%)"
                        )
                        logger.debug(
                            f"  Current delta: {current_delta:.4f}, Current delta exposure: {current_delta_exposure:.2f}"
                        )

                        # Calculate new delta using Black-Scholes
                        implied_vol = 0.30  # Default implied volatility
                        if (
                            hasattr(option, "implied_volatility")
                            and option.implied_volatility > 0
                        ):
                            implied_vol = option.implied_volatility

                        # Calculate the new delta based on the new underlying price
                        new_delta = calculate_option_delta(
                            option=option,
                            underlying_price=new_underlying_price,
                            use_black_scholes=True,
                            risk_free_rate=0.05,  # Default risk-free rate
                            implied_volatility=implied_vol,
                        )

                        # Calculate the new notional value based on the new underlying price
                        new_notional_value = (
                            new_underlying_price * 100 * abs(option.quantity)
                        )

                        # Calculate the new delta exposure (delta * notional_value / 100)
                        new_delta_exposure = (
                            new_delta * new_notional_value / 100
                        )  # Divide by 100 because delta is per share

                        # Calculate the percentage change in delta exposure
                        if current_delta_exposure != 0:
                            delta_exposure_pct_change = (
                                new_delta_exposure / current_delta_exposure - 1
                            ) * 100
                        else:
                            delta_exposure_pct_change = 0

                        # Use the new delta exposure as the new option value
                        new_option_value = new_delta_exposure

                        logger.debug(
                            f"  New delta: {new_delta:.4f}, New delta exposure: {new_delta_exposure:.2f} (change: {delta_exposure_pct_change:.2f}%)"
                        )

                    except Exception as e:
                        # Log the error in detail
                        logger.error(
                            f"Delta calculation failed for {option.ticker}: {e}. Stack trace:",
                            exc_info=True,
                        )
                        logger.error(
                            f"Option details: ticker={option.ticker}, strike={option.strike}, type={option.option_type}, delta={current_delta}"
                        )
                        logger.error(
                            f"Underlying details: price={current_underlying_price}, beta={underlying_beta}"
                        )

                        # Use the option's beta to approximate the change in delta exposure
                        delta_exposure_pct_change = (
                            option_beta * spy_change_decimal * 100
                        )
                        new_option_value = current_delta_exposure * (
                            1 + delta_exposure_pct_change / 100
                        )

                        # Make it very clear we're using a linear approximation
                        logger.error(
                            f"USING LINEAR APPROXIMATION for {option.ticker}: new_value={new_option_value:.2f} (change: {delta_exposure_pct_change:.2f}%)"
                        )

                        # Track that this option used a linear approximation
                        linear_approx = True
                else:
                    # Log the error in detail
                    logger.error(
                        f"Cannot calculate non-linear option behavior for {option.ticker}: No underlying price available"
                    )

                    # Use the option's beta to approximate the change in delta exposure
                    delta_exposure_pct_change = option_beta * spy_change_decimal * 100
                    new_option_value = current_delta_exposure * (
                        1 + delta_exposure_pct_change / 100
                    )

                    # Make it very clear we're using a linear approximation
                    logger.error(
                        f"USING LINEAR APPROXIMATION for {option.ticker}: new_value={new_option_value:.2f} (change: {delta_exposure_pct_change:.2f}%)"
                    )

                    # Track that this option used a linear approximation
                    linear_approx = True

                # Add to long or short exposure based on delta exposure sign
                if current_delta_exposure >= 0:  # Long exposure (positive delta)
                    long_exposure += new_option_value
                else:  # Short exposure (negative delta)
                    short_exposure += abs(
                        new_option_value
                    )  # Use absolute value for short

                position_detail.append(
                    {
                        "ticker": f"{group_ticker} (option)",
                        "type": "option",
                        "beta": option_beta,
                        "original_value": current_delta_exposure,
                        "new_value": new_option_value,
                        "pct_change": delta_exposure_pct_change,
                        "linear_approx": linear_approx,  # Track whether we used linear approximation
                    }
                )

        # Calculate net market exposure (long - short)
        net_market_exposure = long_exposure - short_exposure

        # Calculate portfolio value (net market exposure + cash)
        # This matches how portfolio_estimate_value is calculated in the codebase
        new_portfolio_value = net_market_exposure + cash_value

        # Store the calculated values
        portfolio_values.append(new_portfolio_value)
        position_contributions.append(
            {
                "long_exposure": long_exposure,
                "short_exposure": short_exposure,
                "net_market_exposure": net_market_exposure,
                "cash_value": cash_value,
                "portfolio_value": new_portfolio_value,
                "positions": position_detail,
            }
        )

    # Count how many options used linear approximations
    linear_approx_count = sum(
        1
        for contrib in position_contributions
        for pos in contrib.get("positions", [])
        if pos.get("type") == "option" and pos.get("linear_approx", False)
    )
    total_options_count = sum(
        1
        for contrib in position_contributions
        for pos in contrib.get("positions", [])
        if pos.get("type") == "option"
    )

    # Log a summary of linear approximations
    if total_options_count > 0:
        linear_approx_pct = (linear_approx_count / total_options_count) * 100
        if linear_approx_count > 0:
            logger.warning(
                f"Used linear approximation for {linear_approx_count} out of {total_options_count} options ({linear_approx_pct:.1f}%)"
            )
            logger.warning(
                "This may cause the chart to appear more linear than it should be"
            )
        else:
            logger.info(
                f"All {total_options_count} options used non-linear Black-Scholes calculations"
            )

    # Format values for display
    text_values = [format_currency(value) for value in portfolio_values]

    # Format SPY changes for display
    spy_change_labels = [f"{change}%" for change in spy_changes]

    # Calculate percentage changes for the portfolio
    base_value = portfolio_values[spy_changes.index(0)]  # Value at 0% change
    pct_changes = [(value / base_value - 1) * 100 for value in portfolio_values]
    pct_change_text = [f"{change:.1f}%" for change in pct_changes]

    # Log some details for debugging
    logger.debug(
        f"Base portfolio value (at 0% SPY change): {format_currency(base_value)}"
    )
    for i, change in enumerate(spy_changes):
        logger.debug(
            f"SPY {change}%: Portfolio value = {format_currency(portfolio_values[i])} "
            f"(change: {pct_changes[i]:.2f}%)"
        )

    # Create the chart data
    chart_data = {
        "data": [
            {
                "type": "scatter",
                "x": spy_change_labels,
                "y": portfolio_values,
                "mode": "lines+markers",
                "name": "Portfolio Value",
                "text": text_values,
                "hovertemplate": "<b>SPY: %{x}</b><br>Portfolio: %{text}<br>Change: %{customdata}<extra></extra>",
                "customdata": pct_change_text,
                "line": {
                    "color": "#3498DB",
                    "width": 3,
                    "shape": "spline",  # Use spline for smoother curves
                },
                "marker": {
                    "size": 8,
                    "color": "#3498DB",
                    "line": {"width": 1, "color": "#FFFFFF"},
                },
            },
            # Add a reference line for 1:1 movement with SPY
            {
                "type": "scatter",
                "x": spy_change_labels,
                "y": [
                    base_value * (1 + spy_change / 100) for spy_change in spy_changes
                ],
                "mode": "lines",
                "name": "SPY (1:1)",
                "line": {
                    "color": "#95A5A6",  # Gray color
                    "width": 2,
                    "dash": "dash",
                },
                "hoverinfo": "skip",
            },
            # Add a reference line for portfolio beta movement
            {
                "type": "scatter",
                "x": spy_change_labels,
                "y": [
                    base_value
                    * (1 + portfolio_summary.portfolio_beta * spy_change / 100)
                    for spy_change in spy_changes
                ],
                "mode": "lines",
                "name": f"Portfolio Beta ({portfolio_summary.portfolio_beta:.2f})",
                "line": {
                    "color": "#E74C3C",  # Red color
                    "width": 2,
                    "dash": "dot",
                },
                "hoverinfo": "skip",
            },
        ],
        "layout": {
            "title": {
                "text": "Portfolio Sensitivity to SPY Movement",
                "font": {"size": 16, "color": "#2C3E50"},
            },
            "showlegend": True,  # Explicitly show the legend
            "xaxis": {
                "title": "SPY Change (%)",
                "titlefont": {"size": 12, "color": "#7F8C8D"},
                "tickfont": {"size": 11},
                "gridcolor": "#ECF0F1",
                "zerolinecolor": "#BDC3C7",
            },
            "yaxis": {
                "title": "Portfolio Value ($)",
                "titlefont": {"size": 12, "color": "#7F8C8D"},
                "tickfont": {"size": 11},
                "gridcolor": "#ECF0F1",
                "zerolinecolor": "#BDC3C7",
            },
            "margin": {"l": 50, "r": 20, "t": 50, "b": 50, "pad": 4},
            "autosize": True,
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
            "hovermode": "closest",
            "legend": {
                "orientation": "h",
                "y": -0.15,
                "x": 0.5,
                "xanchor": "center",
                "bgcolor": "rgba(255, 255, 255, 0.9)",
                "bordercolor": "#E2E2E2",
                "borderwidth": 1,
                "font": {"size": 11},
            },
            "annotations": [
                {
                    "text": "* Each position is recalculated individually with Black-Scholes for options",
                    "showarrow": False,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": -0.22,
                    "font": {"size": 10, "color": "#7F8C8D"},
                    "align": "left",
                }
            ],
        },
    }

    return chart_data
