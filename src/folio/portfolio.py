"""Portfolio data processing and CSV loading functionality.

This module provides core functionality for portfolio analysis, including:
- Portfolio data processing and grouping
- CSV loading and parsing
- Cash-like instrument detection
- Portfolio metrics and summary calculations
"""

import os

import pandas as pd
import yaml

from src.stockdata import create_data_fetcher

from .cash_detection import is_cash_or_short_term
from .data_model import (
    ExposureBreakdown,
    PortfolioGroup,
    PortfolioSummary,
    StockPosition,
    create_portfolio_group,
)
from .logger import logger
from .option_utils import calculate_option_delta, parse_option_description
from .utils import clean_currency_value, format_beta, format_currency, get_beta

# Initialize data fetcher
try:
    # Get data source from config (default to "yfinance" if not specified)
    data_source = "yfinance"  # Default value

    # Try to load from config file if it exists
    config_path = os.path.join(os.path.dirname(__file__), "folio.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                data_source = config.get("app", {}).get("data_source", "yfinance")
        except Exception as e:
            logger.warning(
                f"Failed to load folio.yaml: {e}. Using default data source: {data_source}"
            )

    logger.info(f"Using data source: {data_source}")

    # Create data fetcher using factory
    data_fetcher = create_data_fetcher(source=data_source)

    if data_fetcher is None:
        raise RuntimeError(
            "Data fetcher initialization failed but didn't raise an exception"
        )
except ValueError as e:
    logger.error(f"Failed to initialize data fetcher: {e}")
    # Re-raise to fail fast rather than continuing with a null reference
    raise RuntimeError(
        f"Critical component data fetcher could not be initialized: {e}"
    ) from e


def process_portfolio_data(
    df: pd.DataFrame,
) -> tuple[list[PortfolioGroup], PortfolioSummary, list[dict]]:
    """Process portfolio data from a DataFrame into structured groups and summary.

    This function transforms raw portfolio data into an organized structure by:
    1. Validating and cleaning the input data
    2. Identifying cash-like positions (money market funds, etc.)
    3. Grouping related positions (stocks with their options)
    4. Calculating exposure metrics for each position and group
    5. Generating a comprehensive portfolio summary

    The processing flow includes:
    - Validating required columns in the DataFrame
    - Cleaning data (stripping whitespace, handling missing values)
    - Identifying options based on description patterns
    - Processing stock positions with beta calculations
    - Matching options to their underlying stocks
    - Calculating option metrics (delta, notional value, exposures)
    - Creating portfolio groups that combine stocks with their options
    - Identifying cash-like positions for separate tracking
    - Calculating portfolio-level summary statistics

    Args:
        df: A pandas DataFrame containing the portfolio positions, expected to have columns like
            'Symbol', 'Description', 'Quantity', 'Current Value', 'Last Price', 'Type' (account type: Cash/Margin), etc.

    Returns:
        A tuple containing:
        - list[PortfolioGroup]: A list where each element groups a stock and its related options.
        - PortfolioSummary: An object containing aggregated metrics for the entire portfolio.
        - list[dict]: A list of cash-like positions identified during processing.

    Raises:
        ValueError: If the input DataFrame is None, empty, missing required columns, or if no
                    valid portfolio groups can be created after processing.
        RuntimeError: If the `DataFetcher` (needed for beta calculation) is not initialized.

    TODO:
        - Handle cash positions (like SPAXX) explicitly instead of skipping them due to missing quantity.
          Perhaps aggregate them into a separate 'Cash' group or add to the summary.
        - Improve robustness of `is_option_desc` to handle various option formats (weeklies, LEAPS).
        - Make risk-free rate and default implied volatility configurable for delta calculations.
        - Add support for other asset types (bonds, futures, crypto) if needed.
        - Refactor the main loop for clarity and potential performance improvements.
    """
    if df is None or df.empty:
        logger.warning("Input DataFrame is empty or None. Returning empty results.")
        # Return empty results instead of raising an error
        # Create empty exposure breakdowns with all required fields
        empty_exposure = ExposureBreakdown(
            stock_value=0.0,
            stock_beta_adjusted=0.0,
            option_delta_value=0.0,
            option_beta_adjusted=0.0,
            total_value=0.0,
            total_beta_adjusted=0.0,
            description="Empty exposure",
            formula="N/A",
            components={},
        )

        empty_summary = PortfolioSummary(
            total_value_net=0,
            total_value_abs=0,
            portfolio_beta=0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure,
            short_percentage=0,
            exposure_reduction_percentage=0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0,
        )
        return [], empty_summary, []

    logger.info("=== Portfolio Loading Started ===")
    logger.info(f"Processing portfolio with {len(df)} initial rows")

    # Validate required columns
    required_columns = [
        "Symbol",
        "Description",
        "Quantity",
        "Current Value",
        "Percent Of Account",  # Needed for weights calculation later
        "Last Price",
        "Type",
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {', '.join(missing_columns)}")
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    # Clean and prepare data
    logger.info("Cleaning and validating data...")
    df = df.copy()  # Avoid SettingWithCopyWarning
    df["Symbol"] = df["Symbol"].str.strip()
    df["Type"] = df["Type"].fillna("")  # Ensure Type is never NaN
    df["Description"] = df["Description"].fillna("")  # Ensure Description is never NaN

    # Filter out invalid entries like "Pending Activity" which aren't actual positions
    invalid_symbols = ["Pending Activity", "021ESC017"]
    valid_rows = ~df["Symbol"].isin(invalid_symbols)
    if (~valid_rows).any():
        filtered_count = (~valid_rows).sum()
        filtered_symbols = df.loc[~valid_rows, "Symbol"].tolist()
        logger.info(
            f"Filtered out {filtered_count} invalid entries: {filtered_symbols}"
        )
        df = df[valid_rows].reset_index(drop=True)
        logger.info(f"Continuing with {len(df)} remaining rows")

    # Function to identify options based on description format
    def is_option_desc(desc: str) -> bool:
        """Checks if a description string matches a specific option format.

        Example format: 'TSM APR 17 2025 $190 CALL'

        Args:
            desc: The description string to check.

        Returns:
            True if the description appears to be an option in the expected format, False otherwise.

        TODO:
            - Implement more robust option description detection that handles different formats
              and edge cases, including weekly options, non-standard date formats, and LEAPS.
              Current implementation is very brittle and only works with one specific format (6 parts).
            - Consider using regular expressions for more flexible parsing.
        """
        if not isinstance(desc, str):
            return False
        parts = desc.strip().split()
        # Expecting format: UNDERLYING MONTH DAY YEAR $STRIKE TYPE (6 parts)
        if len(parts) != 6:
            return False
        # Check if the 5th part starts with '$' and the 6th is CALL/PUT
        return parts[4].startswith("$") and parts[5].upper() in ["CALL", "PUT"]

    # Basic portfolio statistics
    total_positions = len(df)
    # Calculate total value *after* cleaning currency values
    try:
        total_value = df["Current Value"].apply(clean_currency_value).sum()
    except ValueError as e:
        logger.error(
            f"Error calculating total portfolio value during initial cleaning: {e}"
        )
        # Depending on severity, you might want to raise here or continue with 0
        total_value = 0  # Or re-raise

    # Filter for non-options and options using the description parser
    is_opt_mask = df["Description"].apply(is_option_desc)
    stock_df = df[~is_opt_mask]
    option_df = df[is_opt_mask]

    unique_stocks = len(stock_df["Symbol"].unique())
    # Unique options might be better counted by the full description or parsed details later
    unique_options = len(
        option_df["Description"].unique()
    )  # Using description as proxy

    logger.info("=== Portfolio Overview ===")
    logger.info(f"Total Input Rows: {total_positions}")
    logger.info(f"Identified Stocks Rows: {len(stock_df)}")
    logger.info(f"Identified Option Rows: {len(option_df)}")
    logger.info(
        f"Total Portfolio Value (sum of 'Current Value' column): {format_currency(total_value)}"
    )
    logger.info(f"Unique Stock Symbols: {unique_stocks}")
    logger.info(
        f"Unique Option Descriptions: {unique_options}"
    )  # Might include duplicates if format varies slightly

    # Create a map of stock positions and prices for option delta calculations
    stock_positions = {}
    cash_like_positions = []
    # Create a dictionary to track cash-like positions by ticker for deduplication
    cash_like_by_ticker = {}
    logger.info("Processing stock-like positions...")
    # Process non-option positions
    for index, row in stock_df.iterrows():
        symbol_raw = row["Symbol"]
        description = row["Description"]

        # Proceed with processing potentially valid stock/ETF positions
        try:
            # Skip invalid symbols
            if (
                pd.isna(symbol_raw)
                or not isinstance(symbol_raw, str)
                or not symbol_raw.strip()
            ):
                logger.warning(f"Row {index}: Invalid symbol: {symbol_raw}. Skipping.")
                continue

            # Clean symbol (remove trailing asterisks for preferred shares)
            symbol = symbol_raw.rstrip("*")

            # Process quantity
            if pd.isna(row["Quantity"]) or row["Quantity"] == "--":
                current_val = clean_currency_value(row["Current Value"])
                if current_val == 0:
                    logger.warning(
                        f"Row {index}: {symbol} has no quantity and zero value. Skipping."
                    )
                    continue
                # Process based on value only
                logger.warning(
                    f"Row {index}: {symbol} missing quantity but has value. Using quantity=0."
                )
                quantity = 0
            else:
                try:
                    quantity = int(float(row["Quantity"]))
                except (ValueError, TypeError):
                    logger.warning(
                        f"Row {index}: {symbol} has invalid quantity: '{row['Quantity']}'. Skipping."
                    )
                    continue

            # Check if this is a known cash-like position
            is_known_cash = is_cash_or_short_term(
                symbol, beta=None, description=description
            )

            # Process price
            if pd.isna(row["Last Price"]) or row["Last Price"] in ("--", ""):
                if is_known_cash:
                    # Use default values for cash-like positions with missing price
                    price = 0.0
                    beta = 0.0
                    is_cash_like = True
                    logger.info(
                        f"Row {index}: Cash-like position {symbol} missing price. Using defaults."
                    )
                else:
                    logger.warning(
                        f"Row {index}: {symbol} has missing price. Skipping."
                    )
                    continue
            else:
                price = clean_currency_value(row["Last Price"])
                if price < 0:
                    logger.warning(
                        f"Row {index}: {symbol} has negative price ({price}). Skipping."
                    )
                    continue
                elif price == 0:
                    logger.warning(
                        f"Row {index}: {symbol} has zero price. Calculations may be affected."
                    )

            # Calculate position value
            cleaned_current_value = clean_currency_value(row["Current Value"])
            value_to_use = (
                price * quantity
                if quantity != 0 and price != 0
                else cleaned_current_value
            )

            # Get Beta - requires valid ticker and fetcher
            beta = get_beta(symbol, description)

            # Determine if position is cash-like
            is_cash_like = is_cash_or_short_term(
                symbol, beta=beta, description=description
            )

            if is_cash_like:
                # Process cash-like position
                logger.info(
                    f"Identified cash-like position: {symbol}, Value: {format_currency(value_to_use)}"
                )

                # Add to existing cash position or create new one
                if symbol in cash_like_by_ticker:
                    cash_like_by_ticker[symbol]["market_value"] += value_to_use
                    if quantity != 0:
                        cash_like_by_ticker[symbol]["quantity"] += quantity
                    cash_like_by_ticker[symbol]["beta_adjusted_exposure"] = (
                        cash_like_by_ticker[symbol]["market_value"] * beta
                    )
                else:
                    # Create new cash-like position
                    cash_like_position = {
                        "ticker": symbol,
                        "quantity": quantity,
                        "market_value": value_to_use,
                        "beta": beta,
                        "beta_adjusted_exposure": value_to_use * beta,
                        "description": description,
                    }
                    cash_like_by_ticker[symbol] = cash_like_position
                    cash_like_positions.append(cash_like_position)
            else:
                # Process regular stock position
                percent_of_account = 0.0
                if (
                    pd.notna(row["Percent Of Account"])
                    and row["Percent Of Account"] != "--"
                ):
                    percent_of_account = (
                        float(str(row["Percent Of Account"]).replace("%", "")) / 100.0
                    )

                stock_positions[symbol] = {
                    "price": price,
                    "quantity": quantity,
                    "value": value_to_use,
                    "beta": beta,
                    "percent_of_account": percent_of_account,
                    "account_type": row["Type"],
                    "description": description,
                }

        except (ValueError, TypeError) as e:
            # Handle data conversion and type errors
            logger.warning(
                f"Row {index}: Error processing '{symbol_raw}': {e}. Skipping row."
            )
            continue
        except Exception as e:
            # Catch unexpected errors
            logger.error(
                f"Row {index}: Unexpected error for '{symbol_raw}': {e}", exc_info=True
            )
            continue

    # Group by underlying symbol (using stock symbols as base)
    logger.info("=== Position Grouping and Analysis ===")
    groups = []
    processed_option_indices = (
        set()
    )  # Keep track of options already assigned to a group

    # Process stock positions first to form the basis of groups
    for symbol, stock_info in stock_positions.items():
        try:
            logger.info(f"Processing Group for Underlying: {symbol}")

            # Create stock position data structure for the group
            value = stock_info["value"]
            quantity = stock_info["quantity"]
            beta = stock_info["beta"]
            percent_of_account = stock_info["percent_of_account"]

            logger.info("  Stock Details:")
            logger.info(f"    Symbol: {symbol}")
            logger.info(f"    Quantity: {quantity:,.0f}")
            logger.info(f"    Market Value: {format_currency(value)}")
            logger.info(f"    Beta: {format_beta(beta)}")
            logger.info(f"    Beta-Adjusted Exposure: {format_currency(value * beta)}")
            logger.info(f"    Percent of Account: {percent_of_account:.2%}")

            stock_data_for_group = {
                "ticker": symbol,
                "quantity": quantity,
                "market_value": value,
                "beta": beta,
                "beta_adjusted_exposure": value * beta,
                "weight": percent_of_account,
                "position_beta": beta,  # Used for compatibility with existing code
                # TODO: Add other relevant stock fields if needed (e.g., cost basis)
            }

            # Find and process related options from the filtered option_df
            option_data_for_group = []
            # Filter option_df for options whose description contains the stock symbol as the first word
            # This is a potential point of failure if descriptions aren't standard.
            potential_options = option_df[
                option_df["Description"].str.startswith(symbol + " ")
            ]

            logger.debug(
                f"  Found {len(potential_options)} potential option(s) for {symbol} based on description prefix."
            )

            for opt_index, opt_row in potential_options.iterrows():
                # Skip if this option index was already processed (e.g., duplicate description)
                if opt_index in processed_option_indices:
                    continue

                try:
                    option_desc = opt_row["Description"]
                    option_symbol = opt_row["Symbol"]  # May start with '-'

                    logger.debug(
                        f"    Attempting to process potential option: {option_desc} (Symbol: {option_symbol})"
                    )

                    # --- Validate critical option fields ---
                    if pd.isna(opt_row["Quantity"]) or opt_row["Quantity"] == "--":
                        logger.warning(
                            f"    Option {option_desc}: Missing quantity. Skipping."
                        )
                        continue
                    try:
                        opt_quantity = int(float(opt_row["Quantity"]))
                    except (ValueError, TypeError):
                        logger.warning(
                            f"    Option {option_desc}: Invalid quantity format '{opt_row['Quantity']}'. Skipping."
                        )
                        continue

                    if pd.isna(opt_row["Last Price"]) or opt_row["Last Price"] in (
                        "--",
                        "",
                    ):
                        logger.warning(
                            f"    Option {option_desc}: Missing price. Skipping."
                        )
                        continue
                    try:
                        opt_last_price = clean_currency_value(opt_row["Last Price"])
                    except ValueError:
                        logger.warning(
                            f"    Option {option_desc}: Invalid price format '{opt_row['Last Price']}'. Skipping."
                        )
                        continue

                    # --- Parse option details using option_utils ---
                    try:
                        parsed_option = parse_option_description(
                            option_desc, opt_quantity, opt_last_price
                        )
                    except ValueError as e:
                        # This happens if the description doesn't match the expected 6-part format
                        logger.warning(
                            f"    Could not parse option description for '{option_desc}': {e}. Skipping."
                        )
                        continue

                    # --- Sanity check: Ensure parsed underlying matches the current group symbol ---
                    if parsed_option.underlying != symbol:
                        # This should theoretically not happen with the current filtering, but good practice
                        logger.error(
                            f"    Mismatch! Option '{option_desc}' parsed underlying '{parsed_option.underlying}' does not match group symbol '{symbol}'. Skipping."
                        )
                        continue

                    # --- Calculate Delta ---
                    # Use the stock's current price from stock_info
                    # TODO: Make risk-free rate and default IV configurable
                    # TODO: Consider fetching/calculating IV per option instead of using a default
                    try:
                        delta = calculate_option_delta(
                            parsed_option,
                            stock_info[
                                "price"
                            ],  # Use the fetched stock price for consistency
                            use_black_scholes=True,
                            risk_free_rate=0.05,  # Default RFR
                            implied_volatility=None,  # Let calculate_option_delta estimate IV
                        )
                    except Exception as delta_err:
                        logger.error(
                            f"    Error calculating delta for option '{option_desc}': {delta_err}. Using delta=0.",
                            exc_info=True,
                        )
                        delta = 0.0

                    # --- Calculate Market Value and Notional Value ---
                    try:
                        market_value = clean_currency_value(opt_row["Current Value"])
                    except ValueError:
                        logger.warning(
                            f"    Option {option_desc}: Invalid 'Current Value' format '{opt_row['Current Value']}'. Using 0."
                        )
                        market_value = 0.0

                    # Notional value calculation moved inside OptionPosition dataclass in option_utils
                    notional_value = parsed_option.notional_value
                    delta_exposure = (
                        delta * notional_value
                    )  # Delta-adjusted notional exposure
                    beta_adjusted_exposure = (
                        delta_exposure * beta
                    )  # Factor in underlying's beta

                    logger.info(f"    Option Added: {option_desc}")
                    logger.info(f"      Quantity: {parsed_option.quantity:,.0f}")
                    logger.info(f"      Market Value: {format_currency(market_value)}")
                    logger.info(f"      Delta: {delta:.3f}")
                    logger.info(
                        f"      Notional Value: {format_currency(notional_value)}"
                    )
                    logger.info(
                        f"      Delta Exposure: {format_currency(delta_exposure)}"
                    )
                    logger.info(
                        f"      Beta-Adjusted Exposure: {format_currency(beta_adjusted_exposure)}"
                    )

                    # --- Append structured option data ---
                    option_data_for_group.append(
                        {
                            "ticker": symbol,  # Underlying ticker
                            "option_symbol": option_symbol,  # The actual option symbol (e.g., '-AAPL...')
                            "description": option_desc,
                            "quantity": parsed_option.quantity,
                            "market_value": market_value,  # Actual market value of the option position
                            "beta": beta,  # Underlying's beta
                            "beta_adjusted_exposure": beta_adjusted_exposure,
                            "strike": parsed_option.strike,
                            "expiry": parsed_option.expiry.strftime("%Y-%m-%d"),
                            "option_type": parsed_option.option_type,
                            "delta": delta,
                            "delta_exposure": delta_exposure,
                            "notional_value": notional_value,
                            # TODO: Add additional Greeks (gamma, theta, vega) to option data
                            # requires extending parsing/calculation functions.
                        }
                    )
                    processed_option_indices.add(opt_index)  # Mark as processed

                except ValueError as opt_val_err:
                    logger.warning(
                        f"    Data conversion error processing option row {opt_index} ('{opt_row.get('Description', 'N/A')}'): {opt_val_err}. Skipping option."
                    )
                    continue
                except TypeError as opt_type_err:
                    logger.warning(
                        f"    Type error processing option row {opt_index} ('{opt_row.get('Description', 'N/A')}'): {opt_type_err}. Skipping option."
                    )
                    continue
                except Exception as opt_err:
                    # Catch unexpected errors during option processing for this group
                    logger.error(
                        f"    Unexpected error processing option row {opt_index} ('{opt_row.get('Description', 'N/A')}') for group {symbol}: {opt_err}",
                        exc_info=True,
                    )
                    continue  # Skip this option, continue with the next for this group

            # Create portfolio group using the dedicated function from data_model
            # Ensure the create function handles cases with stock only, or stock + options
            group = create_portfolio_group(stock_data_for_group, option_data_for_group)
            if group:
                groups.append(group)
                logger.debug(
                    f"  Successfully created group for {symbol} with {len(option_data_for_group)} options."
                )
            else:
                logger.warning(
                    f"  Failed to create a portfolio group for {symbol}. Check 'create_portfolio_group' logic."
                )

        except Exception as group_err:
            # Catch errors during the processing of an entire stock group
            logger.error(
                f"Critical error processing group for underlying '{symbol}': {group_err}",
                exc_info=True,
            )
            # Decide if one group failure should stop everything or just skip the group
            # If it's the first group failing, maybe raise to avoid empty results
            if not groups:
                logger.critical(
                    "First portfolio group failed processing, cannot continue with potentially empty portfolio."
                )
                raise  # Stop processing if the very first group fails
            else:
                logger.warning(f"Skipping group '{symbol}' due to error.")
                continue  # Continue processing other groups

    # Log any options that were not processed (didn't match any stock group)
    unprocessed_options = set(option_df.index) - processed_option_indices
    if unprocessed_options:
        logger.info(
            f"{len(unprocessed_options)} options without matching stock positions found (normal for some strategies):"
        )
        for idx in unprocessed_options:
            logger.info(f"  - Index {idx}: {option_df.loc[idx, 'Description']}")

    if not groups:
        logger.warning(
            "No valid portfolio groups were created after processing. This may be an all-cash portfolio."
        )
        # Instead of raising an error, proceed with just cash-like positions if any exist
        if not cash_like_positions:
            logger.warning(
                "No cash-like positions found either. Returning empty summary."
            )
            # Create empty exposure breakdowns with all required fields
            empty_exposure = ExposureBreakdown(
                stock_value=0.0,
                stock_beta_adjusted=0.0,
                option_delta_value=0.0,
                option_beta_adjusted=0.0,
                total_value=0.0,
                total_beta_adjusted=0.0,
                description="Empty exposure",
                formula="N/A",
                components={},
            )

            empty_summary = PortfolioSummary(
                total_value_net=0,
                total_value_abs=0,
                portfolio_beta=0,
                long_exposure=empty_exposure,
                short_exposure=empty_exposure,
                options_exposure=empty_exposure,
                short_percentage=0,
                exposure_reduction_percentage=0,
                cash_like_positions=[],
                cash_like_value=0.0,
                cash_like_count=0,
            )
            return [], empty_summary, []

    # Calculate portfolio summary using the final list of groups
    logger.info("Calculating final portfolio summary...")
    try:
        summary = calculate_portfolio_summary(groups, cash_like_positions)
        logger.info("Portfolio summary calculated successfully.")
    except Exception as summary_err:
        logger.error(
            f"Failed to calculate portfolio summary: {summary_err}", exc_info=True
        )
        # Decide how to handle summary failure - raise or return groups with None summary?
        raise  # Raising seems safer to indicate incomplete results

    logger.info(
        f"=== Portfolio Loading Finished: {len(groups)} groups created, {len(cash_like_positions)} cash-like positions identified. ==="
    )
    return groups, summary, cash_like_positions


def calculate_portfolio_summary(
    groups: list[PortfolioGroup], cash_like_positions: list[dict] | None = None
) -> PortfolioSummary:
    """Calculate comprehensive summary metrics for the entire portfolio.

    This function aggregates data from all portfolio groups to produce a complete
    portfolio summary with exposure breakdowns, risk metrics, and cash analysis.

    The calculation process:
    1. Processes each portfolio group (stock + options)
    2. Categorizes exposures into long and short components
    3. Calculates beta-adjusted values for risk assessment
    4. Computes portfolio-level statistics and ratios
    5. Incorporates cash-like positions into the analysis

    Exposure categorization rules:
    - Long stocks → long exposure
    - Short stocks → short exposure
    - Long calls & short puts → long options exposure
    - Short calls & long puts → short options exposure

    Args:
        groups: List of PortfolioGroup objects containing processed positions
        cash_like_positions: List of dictionaries representing cash-like positions
                           (money markets, short-term bonds, etc.)

    Returns:
        A PortfolioSummary object with calculated metrics including:
        - Total values (net and absolute)
        - Portfolio beta
        - Exposure breakdowns (long/short/options)
        - Risk ratios (short percentage, exposure reduction)
        - Cash position analysis

    Raises:
        RuntimeError: If calculation fails due to data issues
    """
    logger.debug(f"Starting portfolio summary calculations for {len(groups)} groups.")

    # Initialize cash-like positions list if None
    if cash_like_positions is None:
        cash_like_positions = []

    if not groups and not cash_like_positions:
        logger.warning(
            "Cannot calculate summary for an empty portfolio. Returning default summary."
        )
        # Return a default or empty summary object to avoid downstream errors
        return PortfolioSummary(
            total_value_net=0,
            total_value_abs=0,
            portfolio_beta=0,
            long_exposure=ExposureBreakdown(),
            short_exposure=ExposureBreakdown(),
            options_exposure=ExposureBreakdown(),
            short_percentage=0,
            exposure_reduction_percentage=0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0,
        )

    try:
        # Initialize exposure breakdowns using the structure from data_model
        long_stocks = {"value": 0.0, "beta_adjusted": 0.0}
        long_options_delta = {"value": 0.0, "beta_adjusted": 0.0}
        short_stocks = {"value": 0.0, "beta_adjusted": 0.0}
        short_options_delta = {"value": 0.0, "beta_adjusted": 0.0}
        total_option_market_value = 0.0  # Actual market value sum of options

        # Process each group
        for group in groups:
            # --- Process stock position ---
            if group.stock_position:
                stock = group.stock_position
                # Use abs() for short value calculation
                if stock.quantity >= 0:  # Treat quantity 0 as neutral/long for value
                    long_stocks["value"] += stock.market_value
                    long_stocks["beta_adjusted"] += stock.beta_adjusted_exposure
                else:  # Negative quantity means short
                    short_stocks["value"] += abs(stock.market_value)
                    short_stocks["beta_adjusted"] += abs(
                        stock.beta_adjusted_exposure
                    )  # Beta exposure is also negative

            # --- Process option positions ---
            for opt in group.option_positions:
                # Accumulate total market value of options (useful for P/L or weighting)
                total_option_market_value += opt.market_value

                # Determine if the option contributes positively (long-like) or negatively (short-like)
                # to the portfolio's directional delta exposure.
                # Long Call / Short Put => Positive Delta Exposure contribution
                # Short Call / Long Put => Negative Delta Exposure contribution
                # Note: opt.delta_exposure already accounts for quantity (long/short)
                # Note: opt.beta_adjusted_exposure also accounts for quantity

                if opt.delta_exposure >= 0:
                    long_options_delta["value"] += opt.delta_exposure
                    long_options_delta["beta_adjusted"] += opt.beta_adjusted_exposure
                else:
                    # Add the absolute value to short exposure
                    short_options_delta["value"] += abs(opt.delta_exposure)
                    # Beta-adjusted exposure is also negative, so add its absolute value
                    short_options_delta["beta_adjusted"] += abs(
                        opt.beta_adjusted_exposure
                    )

        # Create exposure breakdown objects
        # 1. Long exposure (stocks + positive delta options)
        long_stock_value = long_stocks["value"]
        long_option_value = long_options_delta["value"]
        long_stock_beta_adj = long_stocks["beta_adjusted"]
        long_option_beta_adj = long_options_delta["beta_adjusted"]

        long_exposure = ExposureBreakdown(
            stock_value=long_stock_value,
            stock_beta_adjusted=long_stock_beta_adj,
            option_delta_value=long_option_value,
            option_beta_adjusted=long_option_beta_adj,
            total_value=long_stock_value + long_option_value,
            total_beta_adjusted=long_stock_beta_adj + long_option_beta_adj,
            description="Long market exposure (Stocks + Positive Delta Options)",
            formula="Long Stocks + Long Calls Delta Exp + Short Puts Delta Exp",
            components={
                "Long Stocks Value": long_stock_value,
                "Long Options Delta Exp": long_option_value,
            },
        )

        # 2. Short exposure (stocks + negative delta options)
        short_stock_value = short_stocks["value"]
        short_option_value = short_options_delta["value"]
        short_stock_beta_adj = short_stocks["beta_adjusted"]
        short_option_beta_adj = short_options_delta["beta_adjusted"]

        short_exposure = ExposureBreakdown(
            stock_value=short_stock_value,
            stock_beta_adjusted=short_stock_beta_adj,
            option_delta_value=short_option_value,
            option_beta_adjusted=short_option_beta_adj,
            total_value=short_stock_value + short_option_value,
            total_beta_adjusted=short_stock_beta_adj + short_option_beta_adj,
            description="Short market exposure (Stocks + Negative Delta Options)",
            formula="Short Stocks + Short Calls Delta Exp + Long Puts Delta Exp",
            components={
                "Short Stocks Value": short_stock_value,
                "Short Options Delta Exp": short_option_value,
            },
        )

        # 3. Options exposure (total delta exposure from all options)
        options_exposure = ExposureBreakdown(
            stock_value=0,  # Options only view
            stock_beta_adjusted=0,
            option_delta_value=long_option_value + short_option_value,
            option_beta_adjusted=long_option_beta_adj + short_option_beta_adj,
            total_value=long_option_value + short_option_value,
            total_beta_adjusted=long_option_beta_adj + short_option_beta_adj,
            description="Total absolute delta exposure from options",
            formula="Sum(|Option Delta Exposures|)",
            components={
                "Long Options Delta Exp": long_option_value,
                "Short Options Delta Exp": short_option_value,
                "Net Options Delta Exp": long_option_value - short_option_value,
                "Total Option Market Value": total_option_market_value,
            },
        )

        # Calculate portfolio metrics
        # 1. Portfolio values
        total_value_net = long_exposure.total_value - short_exposure.total_value
        total_value_abs = long_exposure.total_value + short_exposure.total_value

        # 2. Portfolio beta (weighted average)
        net_beta_adjusted_exposure = (
            long_exposure.total_beta_adjusted - short_exposure.total_beta_adjusted
        )
        portfolio_beta = (
            net_beta_adjusted_exposure / total_value_net
            if total_value_net != 0
            else 0.0
        )

        # 3. Exposure percentages
        short_percentage = (
            short_exposure.total_value / total_value_abs if total_value_abs > 0 else 0.0
        )
        exposure_reduction = (
            short_exposure.total_value / long_exposure.total_value
            if long_exposure.total_value > 0
            else 0.0
        )

        # Process cash-like positions
        cash_like_value = sum(pos["market_value"] for pos in cash_like_positions)
        cash_like_count = len(cash_like_positions)

        # Convert to StockPosition objects for consistent handling
        cash_like_stock_positions = [
            StockPosition(
                ticker=pos["ticker"],
                quantity=pos["quantity"],
                market_value=pos["market_value"],
                beta=pos["beta"],
                beta_adjusted_exposure=pos["beta_adjusted_exposure"],
            )
            for pos in cash_like_positions
        ]

        # Add cash to portfolio totals
        if cash_like_value > 0:
            logger.info(
                f"Adding {cash_like_count} cash positions worth {format_currency(cash_like_value)}"
            )
            total_value_abs += cash_like_value
            total_value_net += cash_like_value

        # Create and return the portfolio summary
        summary = PortfolioSummary(
            total_value_net=total_value_net,
            total_value_abs=total_value_abs,
            portfolio_beta=portfolio_beta,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=short_percentage * 100,  # Convert to percentage
            exposure_reduction_percentage=exposure_reduction
            * 100,  # Convert to percentage
            cash_like_positions=cash_like_stock_positions,
            cash_like_value=cash_like_value,
            cash_like_count=cash_like_count,
        )

        logger.info("Portfolio summary created successfully.")
        log_summary_details(summary)
        return summary

    except Exception as e:
        logger.error("Error calculating portfolio summary", exc_info=True)
        raise RuntimeError("Failed to calculate portfolio summary") from e


def log_summary_details(summary: PortfolioSummary):
    """Log detailed portfolio summary information for monitoring and debugging.

    This function outputs formatted portfolio metrics to the logger, including:
    - Portfolio valuation (net and absolute)
    - Risk metrics (beta, exposure percentages)
    - Cash position details
    - Exposure breakdowns (long, short, options)

    Args:
        summary: The PortfolioSummary object containing calculated metrics
    """
    # Portfolio overview
    logger.info("--- Portfolio Summary ---")
    logger.info(f"Net Value: {format_currency(summary.total_value_net)}")
    logger.info(f"Absolute Value: {format_currency(summary.total_value_abs)}")
    logger.info(f"Beta: {format_beta(summary.portfolio_beta)}")
    logger.info(f"Short %: {summary.short_percentage:.1f}%")
    logger.info(f"Exposure Reduction: {summary.exposure_reduction_percentage:.1f}%")

    # Cash positions
    cash_pct = (
        summary.cash_like_value / summary.total_value_abs * 100
        if summary.total_value_abs > 0
        else 0
    )
    logger.info(
        f"Cash: {format_currency(summary.cash_like_value)} ({summary.cash_like_count} positions, {cash_pct:.1f}%)"
    )

    # Long exposure
    logger.info("Long Exposure:")
    logger.info(f"  Total: {format_currency(summary.long_exposure.total_value)}")
    logger.info(f"  Stocks: {format_currency(summary.long_exposure.stock_value)}")
    logger.info(
        f"  Options: {format_currency(summary.long_exposure.option_delta_value)}"
    )

    # Short exposure
    logger.info("Short Exposure:")
    logger.info(f"  Total: {format_currency(summary.short_exposure.total_value)}")
    logger.info(f"  Stocks: {format_currency(summary.short_exposure.stock_value)}")
    logger.info(
        f"  Options: {format_currency(summary.short_exposure.option_delta_value)}"
    )

    # Options exposure
    logger.info("Options Exposure:")
    logger.info(
        f"  Total Delta: {format_currency(summary.options_exposure.total_value)}"
    )
    logger.info(
        f"  Long Delta: {format_currency(summary.options_exposure.components.get('Long Options Delta Exp', 0))}"
    )
    logger.info(
        f"  Short Delta: {format_currency(summary.options_exposure.components.get('Short Options Delta Exp', 0))}"
    )
    logger.info(
        f"  Net Delta: {format_currency(summary.options_exposure.components.get('Net Options Delta Exp', 0))}"
    )
    logger.info("--------------------------------")


def calculate_position_metrics(group: PortfolioGroup) -> dict:
    """Format portfolio group metrics for display in the UI.

    This function extracts key metrics from a PortfolioGroup and formats them as
    human-readable strings for presentation. It handles formatting of currency values,
    beta values, and special cases like missing options.

    Args:
        group: The PortfolioGroup object containing a stock and its related options

    Returns:
        A dictionary with formatted metrics including:
        - 'total_value': Combined market value formatted as currency
        - 'beta': Underlying stock beta formatted with precision
        - 'beta_adjusted_exposure': Risk-adjusted exposure formatted as currency
        - 'options_delta_exposure': Net options exposure or "N/A" if no options

    Raises:
        ValueError: If group is None or missing required attributes
    """
    if not group:
        raise ValueError("Input PortfolioGroup cannot be None")

    try:
        # Format the group's metrics for display
        has_options = bool(group.option_positions)

        return {
            "total_value": format_currency(group.total_value),
            "beta": format_beta(group.beta),
            "beta_adjusted_exposure": format_currency(group.beta_adjusted_exposure),
            "options_delta_exposure": format_currency(group.options_delta_exposure)
            if has_options
            else "N/A",
        }
    except Exception as e:
        logger.error(f"Error formatting metrics for {group.ticker}: {e}", exc_info=True)
        raise ValueError(f"Error calculating metrics for {group.ticker}") from e
