import pandas as pd

from src.lab.option_utils import (
    calculate_simple_delta,
    parse_option_description,
)
from src.v2.data_fetcher import DataFetcher

from .data_model import (
    ExposureBreakdown,
    PortfolioGroup,
    PortfolioSummary,
    create_portfolio_group,
)
from .logger import logger

# Initialize data fetcher
try:
    data_fetcher = DataFetcher()
    if data_fetcher is None:
        raise RuntimeError(
            "DataFetcher initialization failed but didn't raise an exception"
        )
except ValueError as e:
    logger.error(f"Failed to initialize DataFetcher: {e}")
    # Re-raise to fail fast rather than continuing with a null reference
    raise RuntimeError(
        f"Critical component DataFetcher could not be initialized: {e}"
    ) from e


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
    if value_str in ("--", ""):
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
) -> tuple[list[PortfolioGroup], PortfolioSummary]:
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
        "Type",
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

    # Function to identify options based on description format
    def is_option_desc(desc: str) -> bool:
        """Check if a description matches option format (e.g. 'TSM APR 17 2025 $190 CALL')"""
        if not isinstance(desc, str):
            return False
        parts = desc.strip().split()
        if len(parts) != 6:
            return False
        return parts[4].startswith("$") and parts[5] in ["CALL", "PUT"]

    # Basic portfolio statistics
    total_positions = len(df)
    total_value = df["Current Value"].apply(clean_currency_value).sum()
    unique_stocks = len(df[~df["Description"].apply(is_option_desc)]["Symbol"].unique())
    unique_options = len(df[df["Description"].apply(is_option_desc)]["Symbol"].unique())

    logger.info("\n=== Portfolio Overview ===")
    logger.info(f"Total Positions: {total_positions}")
    logger.info(f"Total Portfolio Value: {format_currency(total_value)}")
    logger.info(f"Unique Stocks: {unique_stocks}")
    logger.info(f"Unique Options: {unique_options}")

    # Create a map of stock positions and prices for option delta calculations
    stock_positions = {}
    for _, row in df[~df["Description"].apply(is_option_desc)].iterrows():
        if row["Last Price"] and isinstance(row["Last Price"], str):
            try:
                symbol = row["Symbol"].rstrip("*")  # Remove trailing asterisks

                # Validate critical data is present
                if not symbol:
                    logger.warning(f"Empty symbol found in row: {row}")
                    continue

                if pd.isna(row["Quantity"]):
                    logger.warning(f"Missing quantity for stock {symbol}")
                    continue

                price = clean_currency_value(row["Last Price"])
                if price <= 0:
                    logger.warning(f"Invalid price (≤0) for stock {symbol}: {price}")
                    continue

                stock_positions[symbol] = {
                    "price": price,
                    "quantity": int(row["Quantity"]),
                    "value": clean_currency_value(row["Current Value"]),
                    "beta": get_beta(symbol, row["Description"]),
                }
            except ValueError as e:
                # More specific exception for data conversion errors
                logger.warning(f"Data conversion error for stock {row['Symbol']}: {e}")
                continue
            except TypeError as e:
                # More specific exception for type errors
                logger.warning(f"Type error for stock {row['Symbol']}: {e}")
                continue
            except Exception as e:
                # Still catch everything else but with better logging
                logger.error(
                    f"Unexpected error processing stock {row['Symbol']}: {e}",
                    exc_info=True,
                )
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
            option_rows = df[df["Description"].apply(is_option_desc)]

            for _, opt in option_rows.iterrows():
                try:
                    # Validate critical fields first
                    if not opt["Symbol"] or pd.isna(opt["Symbol"]):
                        logger.warning("Missing option symbol, skipping")
                        continue

                    if pd.isna(opt["Last Price"]) or pd.isna(opt["Quantity"]):
                        logger.warning(
                            f"Missing price or quantity for option {opt['Symbol']}"
                        )
                        continue

                    # Parse option details using option_utils
                    last_price = clean_currency_value(opt["Last Price"])

                    # More specific try blocks for parsing vs calculation
                    try:
                        option = parse_option_description(
                            opt["Description"], int(opt["Quantity"]), last_price
                        )
                    except ValueError as e:
                        logger.warning(
                            f"Could not parse option description for {opt['Symbol']}: {e}"
                        )
                        continue

                    # Skip if not related to this stock
                    if option.underlying != symbol:
                        continue

                    # Calculate delta using underlying price
                    delta = calculate_simple_delta(option, stock_info["price"])
                    market_value = clean_currency_value(opt["Current Value"])
                    notional_value = option.strike * abs(option.quantity) * 100

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
                        f"    Notional Value: {format_currency(notional_value)}"
                    )
                    logger.info(
                        f"    Delta-Adjusted Exposure: {format_currency(delta * notional_value)}"
                    )
                    logger.info(
                        f"    Beta-Adjusted Exposure: {format_currency(delta * notional_value * beta)}"
                    )

                    option_data.append(
                        {
                            "ticker": symbol,
                            "quantity": option.quantity,
                            "market_value": market_value,
                            "beta": beta,
                            "beta_adjusted_exposure": delta * notional_value * beta,
                            "strike": option.strike,
                            "expiry": option.expiry.strftime("%Y-%m-%d"),
                            "option_type": option.option_type,
                            "delta": delta,
                            "delta_exposure": delta * notional_value,
                            "notional_value": notional_value,
                        }
                    )
                except TypeError as e:
                    logger.warning(f"Type error processing option {opt['Symbol']}: {e}")
                    continue
                except Exception as e:
                    # Still catch generic exceptions but with better logging
                    logger.error(
                        f"Unexpected error processing option {opt.get('Symbol', 'unknown')}: {e}",
                        exc_info=True,
                    )
                    continue

            # Create portfolio group
            group = create_portfolio_group(stock_data, option_data)
            if group:
                groups.append(group)

        except Exception as e:
            # This is critical functionality, so let's log a lot more detail
            logger.error(f"Error processing group for {symbol}: {e}", exc_info=True)
            # If we have no groups yet and this is the first one failing, we should raise
            # to avoid returning an empty portfolio
            if not groups:
                logger.critical(
                    "First portfolio group failed, cannot continue with empty portfolio"
                )
                raise
            continue

    if not groups:
        raise ValueError("No valid portfolio groups created")

    # Calculate portfolio summary
    summary = calculate_portfolio_summary(df, groups)

    return groups, summary


def calculate_portfolio_summary(
    df: pd.DataFrame, groups: list[PortfolioGroup]
) -> PortfolioSummary:
    """Calculate various portfolio summary metrics with detailed breakdowns"""
    logger.debug("Starting portfolio summary calculations")

    try:
        # Initialize exposure breakdowns
        long_stocks = {"value": 0, "beta_adjusted": 0}
        long_options = {"value": 0, "beta_adjusted": 0}
        short_stocks = {"value": 0, "beta_adjusted": 0}
        short_options = {"value": 0, "beta_adjusted": 0}

        # Process each group
        for group in groups:
            # Process stock position
            if group.stock_position:
                if group.stock_position.quantity > 0:
                    long_stocks["value"] += group.stock_position.market_value
                    long_stocks["beta_adjusted"] += (
                        group.stock_position.beta_adjusted_exposure
                    )
                else:
                    short_stocks["value"] += abs(group.stock_position.market_value)
                    short_stocks["beta_adjusted"] += abs(
                        group.stock_position.beta_adjusted_exposure
                    )

            # Process option positions
            for opt in group.option_positions:
                # Calculate if option position is effectively long or short
                is_long = (opt.option_type == "CALL" and opt.quantity > 0) or (
                    opt.option_type == "PUT" and opt.quantity < 0
                )

                if is_long:
                    long_options["value"] += abs(opt.delta_exposure)
                    long_options["beta_adjusted"] += abs(opt.beta_adjusted_exposure)
                else:
                    short_options["value"] += abs(opt.delta_exposure)
                    short_options["beta_adjusted"] += abs(opt.beta_adjusted_exposure)

        # Create exposure breakdowns
        long_exposure = ExposureBreakdown(
            stock_value=long_stocks["value"],
            stock_beta_adjusted=long_stocks["beta_adjusted"],
            option_delta_value=long_options["value"],
            option_beta_adjusted=long_options["beta_adjusted"],
            total_value=long_stocks["value"] + long_options["value"],
            total_beta_adjusted=long_stocks["beta_adjusted"]
            + long_options["beta_adjusted"],
            description="Long market exposure from stocks and options",
            formula="Long stocks + Long calls + Short puts",
            components={
                "Long Stocks": long_stocks["value"],
                "Long Options Delta": long_options["value"],
            },
        )

        short_exposure = ExposureBreakdown(
            stock_value=short_stocks["value"],
            stock_beta_adjusted=short_stocks["beta_adjusted"],
            option_delta_value=short_options["value"],
            option_beta_adjusted=short_options["beta_adjusted"],
            total_value=short_stocks["value"] + short_options["value"],
            total_beta_adjusted=short_stocks["beta_adjusted"]
            + short_options["beta_adjusted"],
            description="Short market exposure from stocks and options",
            formula="Short stocks + Short calls + Long puts",
            components={
                "Short Stocks": short_stocks["value"],
                "Short Options Delta": short_options["value"],
            },
        )

        options_exposure = ExposureBreakdown(
            stock_value=0,  # Options only
            stock_beta_adjusted=0,
            option_delta_value=long_options["value"] + short_options["value"],
            option_beta_adjusted=long_options["beta_adjusted"]
            + short_options["beta_adjusted"],
            total_value=long_options["value"] + short_options["value"],
            total_beta_adjusted=long_options["beta_adjusted"]
            + short_options["beta_adjusted"],
            description="Total option exposure (both long and short)",
            formula="Sum of all option delta exposures",
            components={
                "Long Options": long_options["value"],
                "Short Options": short_options["value"],
            },
        )

        # Calculate total values
        total_value_net = long_exposure.total_value - short_exposure.total_value
        total_value_abs = long_exposure.total_value + short_exposure.total_value

        # Calculate portfolio beta
        portfolio_beta = (
            (long_exposure.total_beta_adjusted - short_exposure.total_beta_adjusted)
            / total_value_net
            if total_value_net != 0
            else 0
        )

        # Calculate exposure percentages
        short_percentage = (
            short_exposure.total_value / total_value_abs if total_value_abs > 0 else 0
        )
        exposure_reduction = (
            short_exposure.total_value / long_exposure.total_value
            if long_exposure.total_value > 0
            else 0
        )

        # Create and return summary
        summary = PortfolioSummary(
            total_value_net=total_value_net,
            total_value_abs=total_value_abs,
            portfolio_beta=portfolio_beta,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=short_percentage,
            exposure_reduction_percentage=exposure_reduction,
        )

        logger.info("Portfolio summary created successfully")
        return summary

    except Exception:
        logger.error("Error calculating portfolio summary", exc_info=True)
        raise


def calculate_position_metrics(group: PortfolioGroup) -> dict:
    """Calculate additional metrics for a position"""
    logger.debug(f"Calculating metrics for group {group.ticker}")

    if not group:
        logger.error("Cannot calculate metrics for None group")
        raise ValueError("Cannot calculate metrics for None group")

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
        # Raise to avoid silently showing incorrect data
        raise ValueError(f"Error calculating position metrics: {e}") from e
