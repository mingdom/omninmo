from typing import Dict, List, Tuple

import pandas as pd

from src.lab.option_utils import (
    calculate_simple_delta,
    parse_option_description,
)
from src.v2.data_fetcher import DataFetcher

from .data_model import (
    PortfolioGroup,
    PortfolioSummary,
    create_portfolio_group,
)
from .logger import logger

# Initialize data fetcher
try:
    data_fetcher = DataFetcher()
except ValueError as e:
    logger.error(f"Failed to initialize DataFetcher: {e}")
    data_fetcher = None


def get_beta(ticker: str, description: str = "") -> float:
    """Get beta for a ticker, handling special cases"""
    # Handle special cases
    if ticker == "SPAXX**" or "MONEY MARKET" in description.upper():
        logger.info(f"Using beta of 0.0 for money market fund {ticker}")
        return 0.0

    if "ESCROW" in description.upper():
        logger.info(f"Using beta of 0.0 for escrow shares {ticker}")
        return 0.0

    if not data_fetcher:
        raise RuntimeError("DataFetcher not initialized - check API key configuration")

    try:
        # Fetch stock and market data
        stock_data = data_fetcher.fetch_data(ticker)
        market_data = data_fetcher.fetch_market_data()

        if stock_data is None or market_data is None:
            logger.warning(
                f"Could not fetch data for {ticker} or market index, using default beta of 1.0"
            )
            return 1.0

        # Calculate returns
        stock_returns = stock_data["Close"].pct_change()
        market_returns = market_data["Close"].pct_change()

        # Calculate beta
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        beta = covariance / market_variance

        logger.info(f"Calculated beta of {beta:.2f} for {ticker}")
        return beta
    except Exception as e:
        logger.warning(
            f"Error calculating beta for {ticker}: {e}, using default beta of 1.0"
        )
        return 1.0


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


def is_option(symbol: str) -> bool:
    """Check if a symbol represents an option (starts with '-')"""
    if not isinstance(symbol, str):
        return False
    return symbol.strip().startswith("-")


def process_portfolio_data(
    df: pd.DataFrame,
) -> Tuple[List[PortfolioGroup], PortfolioSummary]:
    """Process portfolio data from DataFrame into PortfolioGroup objects and summary"""
    if df is None or df.empty:
        raise ValueError("Portfolio data is empty or None")

    logger.info("=== Portfolio Loading Started ===")
    logger.info(f"Processing portfolio with {len(df)} positions")

    # Validate required columns
    required_columns = [
        "Symbol",
        "Description",
        "Quantity",
        "Current Value",
        "Percent Of Account",
        "Last Price",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    # Clean and prepare data
    logger.info("Cleaning and validating data...")
    df = df.copy()
    df["Symbol"] = df["Symbol"].str.strip()
    df["Type"] = df["Type"].fillna("")
    df["Description"] = df["Description"].fillna("")

    # Basic portfolio statistics
    total_positions = len(df)
    total_value = df["Current Value"].apply(clean_currency_value).sum()
    unique_stocks = len(df[~df["Symbol"].apply(is_option)]["Symbol"].unique())
    unique_options = len(df[df["Symbol"].apply(is_option)]["Symbol"].unique())

    logger.info("\n=== Portfolio Overview ===")
    logger.info(f"Total Positions: {total_positions}")
    logger.info(f"Total Portfolio Value: {format_currency(total_value)}")
    logger.info(f"Unique Stocks: {unique_stocks}")
    logger.info(f"Unique Options: {unique_options}")

    # Create a map of stock positions and prices for option delta calculations
    stock_positions = {}
    for _, row in df[~df["Symbol"].apply(is_option)].iterrows():
        if row["Last Price"] and isinstance(row["Last Price"], str):
            try:
                price = clean_currency_value(row["Last Price"])
                if price > 0:
                    symbol = row["Symbol"].rstrip("*")  # Remove trailing asterisks
                    stock_positions[symbol] = {
                        "price": price,
                        "quantity": int(row["Quantity"])
                        if pd.notna(row["Quantity"])
                        else 0,
                        "value": clean_currency_value(row["Current Value"]),
                        "beta": get_beta(symbol, row["Description"]),
                    }
            except Exception as e:
                logger.warning(f"Error processing stock position {row['Symbol']}: {e}")
                continue

    # Group by underlying symbol (using stock symbols as base)
    logger.info("\n=== Position Analysis ===")
    groups = []
    total_long_value = 0
    total_short_value = 0
    total_call_value = 0
    total_put_value = 0

    # Process stock positions first
    for symbol, stock_info in stock_positions.items():
        try:
            logger.info(f"\nProcessing {symbol}")

            # Create stock position data
            value = stock_info["value"]
            quantity = stock_info["quantity"]
            beta = stock_info["beta"]

            if quantity > 0:
                total_long_value += value
            else:
                total_short_value += abs(value)

            logger.info(f"  Stock: {symbol}")
            logger.info(f"    Quantity: {quantity:,.0f}")
            logger.info(f"    Value: {format_currency(value)}")
            logger.info(f"    Beta: {format_beta(beta)}")
            logger.info(f"    Beta-Adjusted Exposure: {format_currency(value * beta)}")

            stock_data = {
                "ticker": symbol,
                "quantity": quantity,
                "market_value": value,
                "beta": beta,
                "beta_adjusted_exposure": value * beta,
                "clean_value": value,
                "weight": float(
                    str(
                        df[df["Symbol"] == symbol]["Percent Of Account"].iloc[0]
                    ).replace("%", "")
                )
                / 100,
                "position_beta": beta,
            }

            # Process related options
            option_data = []
            option_rows = df[df["Symbol"].apply(is_option)]

            for _, opt in option_rows.iterrows():
                try:
                    # Parse option details using option_utils
                    last_price = clean_currency_value(opt["Last Price"])
                    option = parse_option_description(
                        opt["Description"], int(opt["Quantity"]), last_price
                    )

                    # Skip if not related to this stock
                    if option.underlying != symbol:
                        continue

                    # Calculate delta using underlying price
                    delta = calculate_simple_delta(option, stock_info["price"])
                    market_value = clean_currency_value(opt["Current Value"])

                    # Update option type totals
                    if option.option_type == "CALL":
                        total_call_value += abs(market_value)
                    else:
                        total_put_value += abs(market_value)

                    logger.info(f"  Option: {opt['Symbol']}")
                    logger.info(f"    Type: {option.option_type}")
                    logger.info(f"    Strike: {format_currency(option.strike)}")
                    logger.info(f"    Expiry: {option.expiry}")
                    logger.info(f"    Quantity: {option.quantity:,.0f}")
                    logger.info(f"    Value: {format_currency(market_value)}")
                    logger.info(f"    Delta: {delta:.2f}")
                    logger.info(
                        f"    Delta-Adjusted Exposure: {format_currency(market_value * delta)}"
                    )
                    logger.info(
                        f"    Beta-Adjusted Exposure: {format_currency(market_value * beta * delta)}"
                    )

                    option_data.append(
                        {
                            "ticker": symbol,
                            "quantity": option.quantity,
                            "market_value": market_value,
                            "beta": beta,
                            "beta_adjusted_exposure": market_value * beta * delta,
                            "clean_value": market_value,
                            "weight": float(
                                str(opt["Percent Of Account"]).replace("%", "")
                            )
                            / 100,
                            "position_beta": beta * delta,
                            "strike": option.strike,
                            "expiry": str(option.expiry),
                            "option_type": option.option_type,
                            "delta": delta,
                            "delta_exposure": market_value * delta,
                            "notional_value": option.strike
                            * abs(option.quantity)
                            * 100,
                            "underlying_beta": beta,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error processing option {opt['Symbol']}: {e}")
                    continue

            # Create portfolio group
            if stock_data or option_data:
                group = create_portfolio_group(stock_data, option_data)
                if group:
                    groups.append(group)
                else:
                    logger.warning(f"Failed to create portfolio group for {symbol}")

        except Exception as e:
            logger.warning(f"Error processing group for symbol {symbol}: {e}")
            continue

    if not groups:
        raise ValueError("No valid portfolio groups created")

    logger.info(f"\nSuccessfully created {len(groups)} portfolio groups")

    # Print portfolio composition summary
    logger.info("\n=== Portfolio Composition ===")
    logger.info(
        f"Long Stock Value: {format_currency(total_long_value)} ({format_percentage(100 * total_long_value/total_value)})"
    )
    logger.info(
        f"Short Stock Value: {format_currency(total_short_value)} ({format_percentage(100 * total_short_value/total_value)})"
    )
    logger.info(
        f"Call Option Value: {format_currency(total_call_value)} ({format_percentage(100 * total_call_value/total_value)})"
    )
    logger.info(
        f"Put Option Value: {format_currency(total_put_value)} ({format_percentage(100 * total_put_value/total_value)})"
    )

    # Calculate portfolio summary
    logger.info("\n=== Risk Metrics ===")
    try:
        summary = calculate_portfolio_summary(df, groups)

        # Log key risk metrics
        logger.info(f"Net Exposure: {format_currency(summary.total_value_net)}")
        logger.info(f"Gross Exposure: {format_currency(summary.total_value_abs)}")
        logger.info(f"Portfolio Beta: {format_beta(summary.portfolio_beta)}")
        logger.info(
            f"Long/Short Ratio: {format_percentage(100 * (1 - summary.short_percentage))} / {format_percentage(100 * summary.short_percentage)}"
        )
        logger.info(
            f"Exposure Reduction: {format_percentage(100 * summary.exposure_reduction_percentage)}"
        )
        logger.info("=== Portfolio Loading Complete ===\n")

        return groups, summary
    except Exception as e:
        logger.error(f"Error calculating portfolio summary: {e}")
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
