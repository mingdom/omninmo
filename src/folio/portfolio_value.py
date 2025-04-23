"""Portfolio value calculation utilities.

This module provides functions for calculating and extracting portfolio values
from portfolio groups and summaries. These functions are used for portfolio
analysis and visualization, particularly for the allocations chart.
"""

from .data_model import ExposureBreakdown, PortfolioGroup, PortfolioSummary
from .logger import logger
from .utils import format_currency


def process_stock_positions(groups: list[PortfolioGroup]) -> tuple[dict, dict]:
    """Process stock positions from portfolio groups.

    Extracts and categorizes stock positions into long and short components.
    Short values are stored as negative numbers.

    Args:
        groups: List of portfolio groups

    Returns:
        Tuple of (long_stocks, short_stocks) dictionaries with keys:
        - 'value': Market value
        - 'beta_adjusted': Beta-adjusted value
    """
    long_stocks = {"value": 0.0, "beta_adjusted": 0.0}
    short_stocks = {"value": 0.0, "beta_adjusted": 0.0}  # Will contain negative values

    for group in groups:
        if group.stock_position:
            stock = group.stock_position
            if stock.quantity >= 0:  # Long position
                long_stocks["value"] += stock.market_value
                long_stocks["beta_adjusted"] += stock.beta_adjusted_exposure
            else:  # Short position
                # Keep negative values for short positions
                short_stocks["value"] += stock.market_value  # Already negative
                short_stocks["beta_adjusted"] += (
                    stock.beta_adjusted_exposure
                )  # Already negative

    return long_stocks, short_stocks


def process_option_positions(groups: list[PortfolioGroup]) -> tuple[dict, dict]:
    """Process option positions from portfolio groups.

    Extracts and categorizes option positions into long and short components
    based on their market value. Short values are stored as negative numbers.

    This function handles option positions safely, logging any errors but continuing
    processing to ensure the chart can still be displayed even if some options
    have issues.

    Args:
        groups: List of portfolio groups

    Returns:
        Tuple of (long_options, short_options) dictionaries with keys:
        - 'value': Market value
        - 'beta_adjusted': Beta-adjusted value
    """
    long_options = {"value": 0.0, "beta_adjusted": 0.0}
    short_options = {"value": 0.0, "beta_adjusted": 0.0}  # Will contain negative values

    for group in groups:
        for opt in group.option_positions:
            try:
                if opt.quantity >= 0:  # Long position
                    long_options["value"] += opt.market_value
                    long_options["beta_adjusted"] += opt.beta_adjusted_exposure
                else:  # Short position
                    # Keep negative values for short positions
                    short_options["value"] += (
                        opt.market_value
                    )  # Already negative for short positions
                    short_options["beta_adjusted"] += (
                        opt.beta_adjusted_exposure
                    )  # Already negative
            except Exception as e:
                # Log the error but continue processing other options
                logger.error(
                    f"Error processing option {opt.description if hasattr(opt, 'description') else 'unknown'}: {e}"
                )
                # Don't add this option to the totals
                continue

    logger.debug(
        f"Processed option positions: Long={format_currency(long_options['value'])}, Short={format_currency(short_options['value'])}"
    )
    return long_options, short_options


def create_value_breakdowns(
    long_stocks: dict,
    short_stocks: dict,  # Contains negative values
    long_options: dict,
    short_options: dict,  # Contains negative values
) -> tuple[ExposureBreakdown, ExposureBreakdown, ExposureBreakdown]:
    """Create value breakdown objects from position data for portfolio allocation.

    This function creates breakdowns of portfolio values for the allocations chart,
    showing how the total portfolio value is distributed across different types of positions.

    Args:
        long_stocks: Long stock values (positive)
        short_stocks: Short stock values (negative)
        long_options: Long option values (positive)
        short_options: Short option values (negative)

    Returns:
        Tuple of (long_value, short_value, options_value) breakdowns
    """
    # 1. Long value (stocks + options)
    long_stock_value = long_stocks["value"]
    long_option_value = long_options["value"]  # Market value
    long_stock_beta_adj = long_stocks["beta_adjusted"]
    long_option_beta_adj = long_options["beta_adjusted"]

    long_value = ExposureBreakdown(
        stock_exposure=long_stock_value,
        stock_beta_adjusted=long_stock_beta_adj,
        option_delta_exposure=long_option_value,  # Using market value here
        option_beta_adjusted=long_option_beta_adj,
        total_exposure=long_stock_value + long_option_value,
        total_beta_adjusted=long_stock_beta_adj + long_option_beta_adj,
        description="Long market value (Stocks + Options)",
        formula="Long Stocks + Long Options",
        components={
            "Long Stocks Value": long_stock_value,
            "Long Options Value": long_option_value,
        },
    )

    # 2. Short value (stocks + options)
    short_stock_value = short_stocks["value"]  # Already negative
    short_option_value = short_options["value"]  # Already negative, market value
    short_stock_beta_adj = short_stocks["beta_adjusted"]  # Already negative
    short_option_beta_adj = short_options["beta_adjusted"]  # Already negative

    short_value = ExposureBreakdown(
        stock_exposure=short_stock_value,
        stock_beta_adjusted=short_stock_beta_adj,
        option_delta_exposure=short_option_value,  # Using market value here
        option_beta_adjusted=short_option_beta_adj,
        total_exposure=short_stock_value + short_option_value,
        total_beta_adjusted=short_stock_beta_adj + short_option_beta_adj,
        description="Short market value (Stocks + Options)",
        formula="Short Stocks + Short Options",
        components={
            "Short Stocks Value": short_stock_value,
            "Short Options Value": short_option_value,
        },
    )

    # 3. Options value (net market value from all options)
    net_option_value = long_option_value + short_option_value
    net_option_beta_adj = long_option_beta_adj + short_option_beta_adj

    options_value = ExposureBreakdown(
        stock_exposure=0,  # Options only view
        stock_beta_adjusted=0,
        option_delta_exposure=net_option_value,  # Using market value here
        option_beta_adjusted=net_option_beta_adj,
        total_exposure=net_option_value,
        total_beta_adjusted=net_option_beta_adj,
        description="Net market value from options",
        formula="Long Options Value + Short Options Value (where Short is negative)",
        components={
            "Long Options Value": long_option_value,
            "Short Options Value": short_option_value,
            "Net Options Value": net_option_value,
        },
    )

    return long_value, short_value, options_value


def calculate_portfolio_metrics(
    long_value: ExposureBreakdown,
    short_value: ExposureBreakdown,
) -> tuple[float, float, float]:
    """Calculate portfolio-level metrics from value breakdowns.

    Args:
        long_value: Long value breakdown
        short_value: Short value breakdown (with negative values)

    Returns:
        Tuple of (net_market_exposure, portfolio_beta, short_percentage)
    """
    # Calculate net market exposure
    net_market_exposure = long_value.total_exposure + short_value.total_exposure

    # Calculate portfolio beta
    net_beta_adjusted_exposure = (
        long_value.total_beta_adjusted + short_value.total_beta_adjusted
    )
    portfolio_beta = (
        net_beta_adjusted_exposure / net_market_exposure
        if net_market_exposure != 0
        else 0.0
    )

    # Calculate short percentage as a percentage of the total long exposure
    short_percentage = (
        (abs(short_value.total_exposure) / long_value.total_exposure) * 100
        if long_value.total_exposure > 0
        else 0.0
    )

    return net_market_exposure, portfolio_beta, short_percentage


def calculate_portfolio_values(
    groups: list[PortfolioGroup],
    cash_like_positions: list[dict],
    pending_activity_value: float,
) -> tuple[float, float, float, float, float]:
    """Calculate portfolio value metrics.

    This function calculates the total values for stocks, options, cash, and the overall
    portfolio. It handles errors gracefully to ensure the chart can still be displayed
    even if some positions have issues.

    Args:
        groups: List of portfolio groups
        cash_like_positions: List of cash-like positions
        pending_activity_value: Value of pending activity

    Returns:
        Tuple of (stock_value, option_value, cash_like_value, portfolio_estimate_value, cash_percentage)
    """
    # Calculate stock and option values
    stock_value = 0.0
    option_value = 0.0

    for group in groups:
        try:
            if group.stock_position:
                stock_value += group.stock_position.market_value
        except Exception as e:
            logger.error(f"Error processing stock position for {group.ticker}: {e}")
            # Continue with other positions

        for opt in group.option_positions:
            try:
                option_value += opt.market_value
            except Exception as e:
                logger.error(f"Error processing option position in {group.ticker}: {e}")
                # Continue with other positions

    # Calculate cash-like value
    cash_like_value = 0.0
    for pos in cash_like_positions:
        try:
            cash_like_value += pos.get("market_value", 0.0)
        except Exception as e:
            logger.error(f"Error processing cash-like position: {e}")
            # Continue with other positions

    # Calculate portfolio estimated value
    portfolio_estimate_value = (
        stock_value + option_value + cash_like_value + pending_activity_value
    )

    # Calculate cash percentage
    cash_percentage = (
        (cash_like_value / portfolio_estimate_value * 100)
        if portfolio_estimate_value > 0
        else 0.0
    )

    logger.debug(
        f"Portfolio values: Stock={format_currency(stock_value)}, Option={format_currency(option_value)}, Cash={format_currency(cash_like_value)}, Pending={format_currency(pending_activity_value)}, Total={format_currency(portfolio_estimate_value)}"
    )

    return (
        stock_value,
        option_value,
        cash_like_value,
        portfolio_estimate_value,
        cash_percentage,
    )


def get_portfolio_component_values(
    portfolio_summary: PortfolioSummary,
) -> dict[str, float]:
    """Get all component values from a portfolio summary.

    This function extracts the component values from the value breakdowns
    in the portfolio summary, providing direct access to the long and short
    components for stocks and options.

    IMPORTANT: Short values are stored as negative numbers to maintain sign consistency
    throughout the codebase.

    Args:
        portfolio_summary: The portfolio summary to extract values from

    Returns:
        A dictionary with the following keys:
        - long_stock: Value of long stock positions (positive)
        - short_stock: Value of short stock positions (negative)
        - long_option: Value of long option positions (positive)
        - short_option: Value of short option positions (negative)
        - cash: Value of cash-like positions
        - pending: Value of pending activity
        - total: Total portfolio value
    """
    long_stock = portfolio_summary.long_exposure.components.get(
        "Long Stocks Value", 0.0
    )
    short_stock = portfolio_summary.short_exposure.components.get(
        "Short Stocks Value", 0.0
    )  # Already negative
    long_option = portfolio_summary.long_exposure.components.get(
        "Long Options Value", 0.0
    )
    short_option = portfolio_summary.short_exposure.components.get(
        "Short Options Value", 0.0
    )  # Already negative
    cash = portfolio_summary.cash_like_value
    pending = portfolio_summary.pending_activity_value
    total = portfolio_summary.portfolio_estimate_value

    logger.debug("Portfolio component values:")
    logger.debug(f"  Long Stock: {format_currency(long_stock)}")
    logger.debug(f"  Short Stock: {format_currency(short_stock)} (negative value)")
    logger.debug(f"  Long Option: {format_currency(long_option)}")
    logger.debug(f"  Short Option: {format_currency(short_option)} (negative value)")
    logger.debug(f"  Cash: {format_currency(cash)}")
    logger.debug(f"  Pending: {format_currency(pending)}")
    logger.debug(f"  Total: {format_currency(total)}")

    return {
        "long_stock": long_stock,
        "short_stock": short_stock,  # Kept as negative
        "long_option": long_option,
        "short_option": short_option,  # Kept as negative
        "cash": cash,
        "pending": pending,
        "total": total,
    }


def calculate_component_percentages(
    component_values: dict[str, float],
) -> dict[str, float]:
    """Calculate percentages for each component based on total portfolio value.

    IMPORTANT: Short values are stored as negative numbers. The percentages
    are calculated based on the absolute values to represent portion of portfolio,
    but the sign is preserved in the returned dictionary.

    Args:
        component_values: Dictionary of component values

    Returns:
        Dictionary of component percentages (short values remain negative)
    """
    total = component_values["total"]

    if total <= 0:
        return {k: 0.0 for k in component_values.keys()}

    result = {}
    for k, v in component_values.items():
        if k == "total":
            result[k] = 100.0
        else:
            # Calculate percentage based on absolute value, but preserve sign
            sign = -1 if v < 0 else 1
            result[k] = sign * (abs(v) / total) * 100

    return result
