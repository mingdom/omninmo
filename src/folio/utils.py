from typing import Dict, List, Tuple

import pandas as pd

from .data_model import (
    PortfolioGroup,
    PortfolioSummary,
    create_portfolio_group,
)
from .logger import logger


def format_currency(value: float) -> str:
    """Format a value as currency"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a value as percentage"""
    return f"{value:.1f}%"


def format_beta(value: float) -> str:
    """Format a beta value"""
    return f"{value:.2f}β"


def clean_currency_value(value_str: str) -> float:
    """Convert currency string to float, handling negative values in parentheses"""
    value_str = str(value_str)  # Convert to string in case it's already a numeric type

    # Handle empty or dash values
    if value_str == "--" or value_str == "":
        return 0.0

    # Remove currency symbols and commas
    value_str = value_str.replace("$", "").replace(",", "")

    # Handle negative values in parentheses like (123.45)
    if value_str.startswith("(") and value_str.endswith(")"):
        value_str = "-" + value_str[1:-1]

    return float(value_str)


def process_portfolio_data(
    df: pd.DataFrame,
) -> Tuple[List[PortfolioGroup], PortfolioSummary]:
    """Process portfolio data from DataFrame into PortfolioGroup objects and summary"""
    logger.info("Starting portfolio data processing")

    # Clean and prepare data
    logger.debug("Cleaning and preparing data")
    df = df.copy()
    df["Symbol"] = df["Symbol"].str.strip()
    df["Type"] = df["Type"].fillna("")

    # Group by underlying symbol (strip option symbols to get underlying)
    logger.debug("Grouping positions by underlying symbol")
    groups = []

    # Get base symbols (remove option identifiers)
    df["BaseSymbol"] = df["Symbol"].apply(
        lambda x: x.split("-")[-1][:4] if "-" in x else x
    )
    unique_symbols = df["BaseSymbol"].unique()
    logger.info(f"Found {len(unique_symbols)} unique base symbols")

    for symbol in unique_symbols:
        try:
            # Get all positions for this symbol
            positions = df[df["BaseSymbol"] == symbol]

            # Separate stock and option positions
            stock_positions = positions[~positions["Symbol"].str.contains("-")]
            option_positions = positions[positions["Symbol"].str.contains("-")]

            # Create stock data if exists
            stock_data = None
            if not stock_positions.empty:
                first_stock = stock_positions.iloc[0]
                stock_data = {
                    "ticker": first_stock["Symbol"],
                    "quantity": float(first_stock["Quantity"]),
                    "market_value": clean_currency_value(first_stock["Current Value"]),
                    "beta": 1.0,  # Default beta
                    "beta_adjusted_exposure": clean_currency_value(
                        first_stock["Current Value"]
                    ),
                    "clean_value": clean_currency_value(first_stock["Current Value"]),
                    "weight": float(
                        str(first_stock["Percent Of Account"]).replace("%", "")
                    )
                    / 100,
                    "position_beta": 1.0,  # Default position beta
                }

            # Create option data list
            option_data = []
            for _, opt in option_positions.iterrows():
                try:
                    # Parse option symbol for details
                    opt_symbol = opt["Symbol"]
                    opt_parts = opt_symbol.split("-")[1]  # e.g., "AAPL250417C220"
                    ticker = opt_parts[:4]

                    # Handle option expiry date parsing
                    try:
                        expiry = (
                            "20"
                            + opt_parts[4:6]
                            + "-"
                            + opt_parts[6:8]
                            + "-"
                            + opt_parts[8:10]
                        )
                    except:
                        # Use a default expiry if parsing fails
                        expiry = "2025-01-01"

                    # Determine option type
                    option_type = "CALL" if "C" in opt_parts else "PUT"

                    # Parse strike with error handling
                    try:
                        strike_part = opt_parts[
                            opt_parts.find("C" if "C" in opt_parts else "P") + 1 :
                        ]
                        strike = float(strike_part) if strike_part.isdigit() else 100.0
                    except:
                        strike = 100.0  # Default strike if parsing fails

                    market_value = clean_currency_value(opt["Current Value"])
                    quantity = float(opt["Quantity"])

                    option_data.append(
                        {
                            "ticker": ticker,
                            "quantity": quantity,
                            "market_value": market_value,
                            "beta": 1.0,  # Default beta
                            "beta_adjusted_exposure": market_value,  # Simple beta-adjusted exposure
                            "clean_value": market_value,
                            "weight": float(
                                str(opt["Percent Of Account"]).replace("%", "")
                            )
                            / 100,
                            "position_beta": 1.0,  # Default position beta
                            "strike": strike,
                            "expiry": expiry,
                            "option_type": option_type,
                            "delta": 0.5
                            if option_type == "CALL"
                            else -0.5,  # Default delta
                            "delta_exposure": market_value,  # Simple delta exposure
                            "notional_value": strike
                            * abs(quantity)
                            * 100,  # Standard option multiplier
                            "underlying_beta": 1.0,  # Default underlying beta
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing option position: {e}", exc_info=True
                    )
                    # Continue with next option position

            # Create portfolio group if we have either stock or options
            if stock_data or option_data:
                group = create_portfolio_group(stock_data, option_data)
                if group:
                    groups.append(group)

        except Exception as e:
            logger.error(
                f"Error processing group for symbol {symbol}: {e}", exc_info=True
            )

    logger.info(f"Created {len(groups)} portfolio groups")

    # Calculate portfolio summary
    logger.debug("Calculating portfolio summary")
    try:
        summary = calculate_portfolio_summary(df, groups)
        logger.info("Portfolio summary calculation complete")
        return groups, summary
    except Exception as e:
        logger.error(f"Error calculating portfolio summary: {e}", exc_info=True)
        raise


def calculate_portfolio_summary(
    df: pd.DataFrame, groups: List[PortfolioGroup]
) -> PortfolioSummary:
    """Calculate various portfolio summary metrics"""
    logger.debug("Starting portfolio summary calculations")

    try:
        # Calculate total values
        total_value_net = sum(group.net_exposure for group in groups)
        total_value_abs = sum(abs(group.net_exposure) for group in groups)
        logger.debug(f"Total portfolio value (net): {total_value_net:,.2f}")

        # Calculate exposures
        long_value = sum(g.net_exposure for g in groups if g.net_exposure > 0)
        short_value = abs(sum(g.net_exposure for g in groups if g.net_exposure < 0))
        options_exposure = sum(
            g.total_delta_exposure for g in groups if g.option_positions
        )
        logger.debug(f"Long value: {long_value:,.2f}, Short value: {short_value:,.2f}")

        # Calculate beta exposures
        long_beta_exposure = sum(
            g.beta_adjusted_exposure for g in groups if g.net_exposure > 0
        )
        short_beta_exposure = abs(
            sum(g.beta_adjusted_exposure for g in groups if g.net_exposure < 0)
        )
        options_beta_adjusted = sum(
            g.beta_adjusted_exposure for g in groups if g.option_positions
        )

        # Calculate betas
        long_beta = long_beta_exposure / long_value if long_value else 0
        short_beta = short_beta_exposure / short_value if short_value else 0
        logger.debug(f"Long beta: {long_beta:.2f}, Short beta: {short_beta:.2f}")

        # Calculate portfolio beta
        portfolio_beta = (
            sum(g.beta_adjusted_exposure for g in groups) / total_value_net
            if total_value_net
            else 0
        )
        logger.debug(f"Portfolio beta: {portfolio_beta:.2f}")

        # Calculate short percentage and exposure reduction
        short_percentage = (short_value / total_value_abs) if total_value_abs > 0 else 0
        exposure_reduction_amount = short_value
        exposure_reduction_percentage = (
            (short_value / (long_value + options_exposure))
            if (long_value + options_exposure) > 0
            else 0
        )

        # Create summary
        summary = PortfolioSummary(
            total_value_net=total_value_net,
            total_value_abs=total_value_abs,
            portfolio_beta=portfolio_beta,
            long_value=long_value,
            long_beta_exposure=long_beta_exposure,
            long_portfolio_beta=long_beta,
            short_value=short_value,
            short_beta_exposure=short_beta_exposure,
            short_portfolio_beta=short_beta,
            short_percentage=short_percentage,
            options_delta_exposure=options_exposure,
            options_beta_adjusted=options_beta_adjusted,
            total_exposure_before_shorts=long_value + options_exposure,
            total_exposure_after_shorts=(long_value + options_exposure - short_value),
            exposure_reduction_amount=exposure_reduction_amount,
            exposure_reduction_percentage=exposure_reduction_percentage,
        )
        logger.info("Portfolio summary created successfully")
        return summary

    except Exception:
        logger.error("Error calculating portfolio summary", exc_info=True)
        raise


def calculate_position_metrics(group: PortfolioGroup) -> Dict:
    """Calculate additional metrics for a position"""
    logger.debug(f"Calculating metrics for group {group.ticker}")
    try:
        return {
            "total_value": format_currency(group.total_value),
            "beta": format_beta(group.beta),
            "beta_adjusted_exposure": format_currency(group.beta_adjusted_exposure),
            "options_delta_exposure": format_currency(group.options_delta_exposure)
            if group.option_positions
            else "N/A",
        }
    except Exception as e:
        logger.error(
            f"Error calculating metrics for {group.ticker}: {e}", exc_info=True
        )
        return {
            "total_value": "Error",
            "beta": "Error",
            "beta_adjusted_exposure": "Error",
            "options_delta_exposure": "Error",
        }
