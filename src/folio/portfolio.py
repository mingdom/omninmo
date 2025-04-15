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
from .utils import clean_currency_value, format_beta, format_currency, get_beta

# Initialize data fetcher
try:
    # Get data source from config (default to "yfinance" if not specified)
    data_source = "yfinance"  # Default value

    # Try to load from config file if it exists
    config_path = os.path.join(os.path.dirname(__file__), "folio.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
        data_source = config.get("app", {}).get("data_source", "yfinance")

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
            total_exposure=0,
            portfolio_beta=0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure,
            short_percentage=0,
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

    # Capture Pending Activity value before filtering it out
    pending_activity_value = 0.0
    pending_activity_rows = df[df["Symbol"] == "Pending Activity"]
    if not pending_activity_rows.empty:
        for _, row in pending_activity_rows.iterrows():
            if pd.notna(row["Current Value"]):
                try:
                    pending_activity_value += clean_currency_value(row["Current Value"])
                    logger.info(
                        f"Found Pending Activity with value: {format_currency(pending_activity_value)}"
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing Pending Activity value: {e}")

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
    # Note: We no longer calculate portfolio_value from the CSV as it may be out of date

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
    # We no longer calculate or display the total portfolio value from the CSV
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
                    # Parse quantity, preserving negative values for short positions
                    raw_quantity = row["Quantity"]
                    # Check if this is a short position (indicated by negative value)
                    quantity = float(raw_quantity)
                    # Convert to int but preserve the sign
                    quantity = int(quantity)

                    logger.debug(f"Row {index}: {symbol} quantity parsed as {quantity}")
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
                        "market_value": value_to_use,  # Keep market_value for cash positions
                        "beta": beta,
                        "beta_adjusted_exposure": value_to_use * beta,
                        "description": description,
                        "price": price,  # Store the price
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

                # Sector determination removed - will be implemented in a separate task

                # Get cost basis if available
                cost_basis = 0.0
                if (
                    pd.notna(row["Average Cost Basis"])
                    and row["Average Cost Basis"] != "--"
                ):
                    try:
                        cost_basis = clean_currency_value(row["Average Cost Basis"])
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Row {index}: {symbol} has invalid cost basis: '{row['Average Cost Basis']}'. Using 0.0."
                        )

                stock_positions[symbol] = {
                    "price": price,
                    "quantity": quantity,
                    "value": value_to_use,
                    "beta": beta,
                    "percent_of_account": percent_of_account,
                    "account_type": row["Type"],
                    "description": description,
                    "cost_basis": cost_basis,
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
                "beta": beta,
                "market_exposure": value,  # This is the market exposure (quantity * price)
                "beta_adjusted_exposure": value * beta,
                "description": stock_info.get("description", ""),
                "price": stock_info["price"],  # Store the price
                "cost_basis": stock_info.get("cost_basis", 0.0),  # Store the cost basis
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

            # Import the necessary functions
            from .options import process_options
            from .validation import extract_option_data

            # Extract and validate option data using our utility function
            # This replaces all the manual validation and extraction code
            options_data = extract_option_data(
                potential_options,
                # Filter function to skip already processed options
                filter_func=lambda row: row.name not in processed_option_indices,
                include_row_index=True,
            )

            # Process all options at once using our new function
            prices = {symbol: stock_info["price"]}  # Use the fetched stock price
            betas = {symbol: beta}  # Use the beta we already calculated

            try:
                processed_options = process_options(options_data, prices, betas)

                # Filter out options with mismatched underlying
                processed_options = [
                    opt for opt in processed_options if opt["ticker"] == symbol
                ]

                # Convert to the format expected by create_portfolio_group
                option_data_for_group = []
                for opt in processed_options:
                    # Mark the option as processed
                    row_index = next(
                        data["row_index"]
                        for data in options_data
                        if data["description"] == opt["description"]
                        and data["quantity"] == opt["quantity"]
                    )
                    processed_option_indices.add(row_index)

                    # Log the option details
                    logger.info(f"    Option Added: {opt['description']}")
                    logger.info(f"      Quantity: {opt['quantity']:,.0f}")
                    logger.info(f"      Delta: {opt['delta']:.3f}")
                    logger.info(
                        f"      Notional Value: {format_currency(opt['notional_value'])}"
                    )
                    logger.info(
                        f"      Delta Exposure: {format_currency(opt['delta_exposure'])}"
                    )
                    logger.info(
                        f"      Beta-Adjusted Exposure: {format_currency(opt['beta_adjusted_exposure'])}"
                    )

                    # Add to the group data
                    option_data_for_group.append(
                        {
                            "ticker": opt["ticker"],
                            "option_symbol": opt["option_symbol"],
                            "description": opt["description"],
                            "quantity": opt["quantity"],
                            "beta": opt["beta"],
                            "beta_adjusted_exposure": opt["beta_adjusted_exposure"],
                            "market_exposure": opt[
                                "delta_exposure"
                            ],  # Delta-adjusted exposure is the market exposure
                            "strike": opt["strike"],
                            "expiry": opt["expiry"],
                            "option_type": opt["option_type"],
                            "delta": opt["delta"],
                            "delta_exposure": opt["delta_exposure"],
                            "notional_value": opt["notional_value"],
                            "price": opt["price"],
                            "cost_basis": opt.get(
                                "cost_basis", opt["price"]
                            ),  # Use price as default cost basis
                        }
                    )
            except Exception as e:
                logger.error(
                    f"    Error processing options for {symbol}: {e}", exc_info=True
                )
                option_data_for_group = []  # Use an empty list if processing fails

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

    # Process any options that were not matched to a stock position
    unprocessed_options = set(option_df.index) - processed_option_indices
    if unprocessed_options:
        logger.info(
            f"{len(unprocessed_options)} options without matching stock positions found - creating standalone option groups"
        )

        # Group unprocessed options by underlying symbol
        orphaned_options_by_underlying = {}
        for idx in unprocessed_options:
            opt_row = option_df.loc[idx]
            opt_desc = opt_row["Description"]

            # Extract the underlying symbol from the description
            # Description format is expected to be: "SPY JUN 20 2025 $580 CALL"
            parts = opt_desc.strip().split()
            if len(parts) >= 1:
                underlying = parts[0]  # First part should be the underlying symbol

                # Add to the dictionary, grouped by underlying
                if underlying not in orphaned_options_by_underlying:
                    orphaned_options_by_underlying[underlying] = []
                orphaned_options_by_underlying[underlying].append(idx)
                logger.info(
                    f"  - Orphaned option: {opt_desc} (Underlying: {underlying})"
                )
            else:
                logger.warning(
                    f"  - Could not extract underlying from option description: {opt_desc}"
                )

        # Process each group of orphaned options
        for underlying, option_indices in orphaned_options_by_underlying.items():
            logger.info(
                f"Creating standalone option group for {underlying} with {len(option_indices)} options"
            )

            # Import the necessary functions
            from .options import process_options
            from .validation import extract_option_data

            # Extract option data for the specified indices
            orphaned_df = option_df.loc[option_indices]

            # Extract and validate option data using our utility function
            options_data = extract_option_data(orphaned_df, include_row_index=True)

            # Get beta for the underlying
            try:
                beta = get_beta(underlying)
            except ValueError as beta_err:
                # Only handle specific ValueError cases that we know how to handle
                if "No historical data available" in str(beta_err):
                    logger.warning(
                        f"No historical data for {underlying}: {beta_err}. Cannot calculate beta."
                    )
                    # Re-raise with more context to be handled by the caller
                    raise ValueError(
                        f"Cannot process orphaned options for {underlying} without beta data"
                    ) from beta_err
                else:
                    # Re-raise other ValueError cases
                    raise
            except Exception as beta_err:
                # Log unexpected errors and re-raise
                logger.error(
                    f"Unexpected error getting beta for {underlying}: {beta_err}",
                    exc_info=True,
                )
                raise

            # Get the latest price for the underlying
            try:
                # Try to fetch the latest price
                price_data = data_fetcher.fetch_data(underlying, period="1d")
                if price_data is not None and not price_data.empty:
                    underlying_price = price_data.iloc[-1]["Close"]
                    if underlying_price <= 0:
                        # If we get an invalid price, we can't process the options
                        logger.error(
                            f"Invalid price for {underlying}: {underlying_price}"
                        )
                        raise ValueError(
                            f"Cannot process options for {underlying} with invalid price: {underlying_price}"
                        )
                else:
                    # If we can't get the price data, we can't process the options
                    logger.error(f"Could not fetch price data for {underlying}")
                    raise ValueError(
                        f"Cannot process options for {underlying} without price data"
                    )
            except (pd.errors.EmptyDataError, KeyError) as data_err:
                # Handle specific data errors
                logger.error(f"Data error for {underlying}: {data_err}", exc_info=True)
                raise ValueError(
                    f"Cannot process options for {underlying} due to data error"
                ) from data_err
            except Exception as price_err:
                # Log unexpected errors and re-raise
                logger.error(
                    f"Error fetching price for {underlying}: {price_err}", exc_info=True
                )
                raise ValueError(
                    f"Cannot process options for {underlying} without price data"
                ) from price_err

            # Process all options at once using our new function
            prices = {underlying: underlying_price}
            betas = {underlying: beta}

            try:
                processed_options = process_options(options_data, prices, betas)

                # Convert to the format expected by create_portfolio_group
                option_data_for_group = []
                for opt in processed_options:
                    # Mark the option as processed
                    row_index = next(
                        data["row_index"]
                        for data in options_data
                        if data["description"] == opt["description"]
                        and data["quantity"] == opt["quantity"]
                    )
                    processed_option_indices.add(row_index)

                    # Log the option details
                    logger.info(f"Orphaned Option Added: {opt['description']}")
                    logger.info(f"  Quantity: {opt['quantity']:,.0f}")
                    logger.info(f"  Delta: {opt['delta']:.3f}")
                    logger.info(
                        f"  Notional Value: {format_currency(opt['notional_value'])}"
                    )
                    logger.info(
                        f"  Delta Exposure: {format_currency(opt['delta_exposure'])}"
                    )
                    logger.info(
                        f"  Beta-Adjusted Exposure: {format_currency(opt['beta_adjusted_exposure'])}"
                    )

                    # Add to the group data
                    option_data_for_group.append(
                        {
                            "ticker": opt["ticker"],
                            "option_symbol": opt["option_symbol"],
                            "description": opt["description"],
                            "quantity": opt["quantity"],
                            "beta": opt["beta"],
                            "beta_adjusted_exposure": opt["beta_adjusted_exposure"],
                            "market_exposure": opt[
                                "delta_exposure"
                            ],  # Delta-adjusted exposure is the market exposure
                            "strike": opt["strike"],
                            "expiry": opt["expiry"],
                            "option_type": opt["option_type"],
                            "delta": opt["delta"],
                            "delta_exposure": opt["delta_exposure"],
                            "notional_value": opt["notional_value"],
                            "price": opt["price"],
                            "cost_basis": opt.get(
                                "cost_basis", opt["price"]
                            ),  # Use price as default cost basis
                        }
                    )
            except Exception as e:
                logger.error(
                    f"Error processing orphaned options for {underlying}: {e}",
                    exc_info=True,
                )
                option_data_for_group = []  # Use an empty list if processing fails

            # Create a portfolio group with just options (no stock position)
            if option_data_for_group:
                # For options-only groups, we'll create the group with a zero-quantity stock position
                # We need to pass a minimal stock_data dictionary to create_portfolio_group
                # but we'll set the quantity to 0 so it doesn't affect calculations
                stock_data_for_group = {
                    "ticker": underlying,
                    "quantity": 0,
                    "beta": beta,
                    "market_exposure": 0,
                    "beta_adjusted_exposure": 0,
                    "description": f"{underlying} (Options Only)",
                    "price": 0,
                }

                # Create the group
                group = create_portfolio_group(
                    stock_data_for_group, option_data_for_group
                )
                if group:
                    # We'll keep the stock_position with quantity=0 to maintain the ticker information
                    # This ensures the group is properly displayed in the UI
                    groups.append(group)
                    logger.info(
                        f"Successfully created options-only group for {underlying} with {len(option_data_for_group)} options"
                    )

                    # Log the group details
                    logger.info(f"Group details for {underlying}:")
                    logger.info(
                        f"  Net Exposure: {format_currency(group.net_exposure)}"
                    )
                    logger.info(f"  Beta: {format_beta(group.beta)}")
                    logger.info(
                        f"  Beta-Adjusted Exposure: {format_currency(group.beta_adjusted_exposure)}"
                    )
                    logger.info(
                        f"  Options Delta Exposure: {format_currency(group.options_delta_exposure)}"
                    )
                    logger.info(f"  Number of Options: {len(group.option_positions)}")
                    logger.info(
                        f"  Stock Position: {'Yes' if group.stock_position else 'No'}"
                    )
                    if group.stock_position:
                        logger.info(
                            f"  Stock Quantity: {group.stock_position.quantity}"
                        )
                        logger.info(
                            f"  Stock Market Exposure: {format_currency(group.stock_position.market_exposure)}"
                        )
                        logger.info(
                            f"  Stock Beta-Adjusted Exposure: {format_currency(group.stock_position.beta_adjusted_exposure)}"
                        )
                    logger.info(
                        f"  Option Types: {group.call_count} calls, {group.put_count} puts"
                    )
                else:
                    logger.warning(
                        f"Failed to create options-only group for {underlying}"
                    )

    # Check if we have any valid groups after processing
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
                stock_exposure=0.0,
                stock_beta_adjusted=0.0,
                option_delta_exposure=0.0,
                option_beta_adjusted=0.0,
                total_exposure=0.0,
                total_beta_adjusted=0.0,
                description="Empty exposure",
                formula="N/A",
                components={},
            )

            empty_summary = PortfolioSummary(
                net_market_exposure=0.0,
                portfolio_beta=0.0,
                long_exposure=empty_exposure,
                short_exposure=empty_exposure,
                options_exposure=empty_exposure,
                short_percentage=0.0,
                cash_like_positions=[],
                cash_like_value=0.0,
                cash_like_count=0,
                cash_percentage=0.0,
                stock_value=0.0,
                option_value=0.0,
                portfolio_estimate_value=pending_activity_value,  # Include pending activity value
            )
            return [], empty_summary, []

    # Calculate portfolio summary using the final list of groups
    logger.info("Calculating final portfolio summary...")
    try:
        summary = calculate_portfolio_summary(
            groups, cash_like_positions, pending_activity_value
        )
        if pending_activity_value > 0:
            logger.info(
                f"Including Pending Activity value: {format_currency(pending_activity_value)}"
            )
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
    groups: list[PortfolioGroup],
    cash_like_positions: list[dict] | None = None,
    pending_activity_value: float = 0.0,
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

    if not groups and not cash_like_positions and pending_activity_value == 0.0:
        logger.warning(
            "Cannot calculate summary for an empty portfolio. Returning default summary."
        )
        # Return a default or empty summary object to avoid downstream errors
        empty_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=0.0,
            option_beta_adjusted=0.0,
            total_exposure=0.0,
            total_beta_adjusted=0.0,
            description="Empty exposure",
            formula="N/A",
            components={},
        )

        return PortfolioSummary(
            net_market_exposure=0.0,
            portfolio_beta=0.0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure,
            short_percentage=0.0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0,
            cash_percentage=0.0,
            stock_value=0.0,
            option_value=0.0,
            portfolio_estimate_value=pending_activity_value,  # Include pending activity value
        )

    try:
        # Initialize exposure breakdowns using the structure from data_model
        long_stocks = {"value": 0.0, "beta_adjusted": 0.0}
        long_options_delta = {"value": 0.0, "beta_adjusted": 0.0}
        short_stocks = {"value": 0.0, "beta_adjusted": 0.0}
        short_options_delta = {"value": 0.0, "beta_adjusted": 0.0}

        # Process each group
        for group in groups:
            # --- Process stock position ---
            if group.stock_position:
                stock = group.stock_position
                # For stocks, market_exposure = quantity * price, so it's already negative for short positions
                if stock.quantity >= 0:  # Treat quantity 0 as neutral/long for value
                    long_stocks["value"] += stock.market_exposure
                    long_stocks["beta_adjusted"] += stock.beta_adjusted_exposure
                else:  # Negative quantity means short - store as negative value
                    # No need for abs() - keep the negative sign for short positions
                    short_stocks["value"] += stock.market_exposure  # Already negative
                    short_stocks["beta_adjusted"] += (
                        stock.beta_adjusted_exposure
                    )  # Already negative

            # --- Process option positions ---
            for opt in group.option_positions:
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
                    # Store as negative value - no need for abs()
                    short_options_delta["value"] += (
                        opt.delta_exposure
                    )  # Already negative
                    # Beta-adjusted exposure is also negative
                    short_options_delta["beta_adjusted"] += (
                        opt.beta_adjusted_exposure
                    )  # Already negative

        # Create exposure breakdown objects
        # 1. Long exposure (stocks + positive delta options)
        long_stock_value = long_stocks["value"]
        long_option_value = long_options_delta["value"]
        long_stock_beta_adj = long_stocks["beta_adjusted"]
        long_option_beta_adj = long_options_delta["beta_adjusted"]

        long_exposure = ExposureBreakdown(
            stock_exposure=long_stock_value,
            stock_beta_adjusted=long_stock_beta_adj,
            option_delta_exposure=long_option_value,
            option_beta_adjusted=long_option_beta_adj,
            total_exposure=long_stock_value + long_option_value,
            total_beta_adjusted=long_stock_beta_adj + long_option_beta_adj,
            description="Long market exposure (Stocks + Positive Delta Options)",
            formula="Long Stocks + Long Calls Delta Exp + Short Puts Delta Exp",
            components={
                "Long Stocks Exposure": long_stock_value,
                "Long Options Delta Exp": long_option_value,
            },
        )

        # 2. Short exposure (stocks + negative delta options)
        short_stock_value = short_stocks["value"]
        short_option_value = short_options_delta["value"]
        short_stock_beta_adj = short_stocks["beta_adjusted"]
        short_option_beta_adj = short_options_delta["beta_adjusted"]

        short_exposure = ExposureBreakdown(
            stock_exposure=short_stock_value,
            stock_beta_adjusted=short_stock_beta_adj,
            option_delta_exposure=short_option_value,
            option_beta_adjusted=short_option_beta_adj,
            total_exposure=short_stock_value + short_option_value,
            total_beta_adjusted=short_stock_beta_adj + short_option_beta_adj,
            description="Short market exposure (Stocks + Negative Delta Options)",
            formula="Short Stocks + Short Calls Delta Exp + Long Puts Delta Exp",
            components={
                "Short Stocks Exposure": short_stock_value,
                "Short Options Delta Exp": short_option_value,
            },
        )

        # 3. Options exposure (net delta exposure from all options)
        # Since short_option_value is already negative, we can simply add them
        net_delta_exposure = long_option_value + short_option_value
        net_option_beta_adj = long_option_beta_adj + short_option_beta_adj
        options_exposure = ExposureBreakdown(
            stock_exposure=0,  # Options only view
            stock_beta_adjusted=0,
            option_delta_exposure=net_delta_exposure,
            option_beta_adjusted=net_option_beta_adj,
            total_exposure=net_delta_exposure,
            total_beta_adjusted=net_option_beta_adj,
            description="Net delta exposure from options",
            formula="Long Options Delta + Short Options Delta (where Short is negative)",
            components={
                "Long Options Delta Exp": long_option_value,
                "Short Options Delta Exp": short_option_value,
                "Net Options Delta Exp": net_delta_exposure,
            },
        )

        # Calculate portfolio metrics
        # 1. Market exposure metrics
        # Note: short_exposure is now stored as a negative value, so we can simply add them
        net_market_exposure = (
            long_exposure.total_exposure + short_exposure.total_exposure
        )

        # 2. Portfolio beta (weighted average)
        net_beta_adjusted_exposure = calculate_beta_adjusted_net_exposure(
            long_exposure.total_beta_adjusted, short_exposure.total_beta_adjusted
        )
        portfolio_beta = (
            net_beta_adjusted_exposure / net_market_exposure
            if net_market_exposure != 0
            else 0.0
        )

        # 3. Exposure percentages
        # Calculate short percentage as a percentage of the total long exposure
        # This gives a more meaningful measure of how much the portfolio is hedged
        short_percentage = (
            (abs(short_exposure.total_exposure) / long_exposure.total_exposure) * 100
            if long_exposure.total_exposure > 0
            else 0.0
        )

        # Calculate total position values
        stock_value = 0.0
        option_value = 0.0

        # Process each group to calculate stock and option values
        for group in groups:
            # --- Process stock position ---
            if group.stock_position:
                stock = group.stock_position
                stock_value += stock.market_value

            # --- Process option positions ---
            for opt in group.option_positions:
                option_value += opt.market_value

        # Process cash-like positions
        cash_like_value = sum(pos["market_value"] for pos in cash_like_positions)
        cash_like_count = len(cash_like_positions)

        # Convert to StockPosition objects for consistent handling
        cash_like_stock_positions = [
            StockPosition(
                ticker=pos["ticker"],
                quantity=pos["quantity"],
                beta=pos["beta"],
                market_exposure=pos[
                    "market_value"
                ],  # Cash has no market exposure, but we store the value
                beta_adjusted_exposure=pos["beta_adjusted_exposure"],
                price=pos.get("price", 0.0),  # Get price if it exists
                cost_basis=pos.get("price", 0.0),  # For cash, use price as cost basis
            )
            for pos in cash_like_positions
        ]

        # Calculate portfolio estimated value and cash percentage
        total_position_value = stock_value + option_value
        portfolio_estimate_value = (
            total_position_value + cash_like_value + pending_activity_value
        )
        cash_percentage = (
            (cash_like_value / portfolio_estimate_value * 100)
            if portfolio_estimate_value > 0
            else 0.0
        )

        if cash_like_value > 0:
            logger.info(
                f"Adding {cash_like_count} cash positions worth {format_currency(cash_like_value)}"
            )
            logger.info(
                f"Cash represents {cash_percentage:.2f}% of the portfolio estimated value"
            )

        # Get current timestamp in ISO format
        from datetime import UTC, datetime

        # If prices have been updated, use that timestamp, otherwise use current time
        current_time = datetime.now(UTC).isoformat()

        # Create and return the portfolio summary
        summary = PortfolioSummary(
            net_market_exposure=net_market_exposure,
            portfolio_beta=portfolio_beta,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=short_percentage,  # Already calculated as percentage
            cash_like_positions=cash_like_stock_positions,
            cash_like_value=cash_like_value,
            cash_like_count=cash_like_count,
            cash_percentage=cash_percentage,
            stock_value=stock_value,  # Add stock value
            option_value=option_value,  # Add option value
            pending_activity_value=pending_activity_value,  # Add pending activity value
            portfolio_estimate_value=portfolio_estimate_value,
            price_updated_at=current_time,  # Set the timestamp
        )

        logger.info("Portfolio summary created successfully.")
        log_summary_details(summary)
        return summary

    except Exception as e:
        logger.error("Error calculating portfolio summary", exc_info=True)
        raise RuntimeError("Failed to calculate portfolio summary") from e


def update_portfolio_prices(
    portfolio_groups: list[PortfolioGroup], data_fetcher=None
) -> str:
    """Update prices for all positions in the portfolio groups.

    Args:
        portfolio_groups: List of portfolio groups to update prices for
        data_fetcher: Optional data fetcher to use for price updates

    Returns:
        ISO format timestamp of when prices were updated
    """
    from datetime import UTC, datetime

    # Use the default data fetcher if none is provided
    if data_fetcher is None:
        data_fetcher = create_data_fetcher()

    # Extract unique tickers from all positions
    tickers = set()
    for group in portfolio_groups:
        # Add stock position ticker
        if group.stock_position:
            tickers.add(group.stock_position.ticker)

        # Add option position tickers
        for option in group.option_positions:
            tickers.add(option.ticker)

    # Remove cash-like instruments as we don't need to update their prices
    tickers = [ticker for ticker in tickers if not is_cash_or_short_term(ticker)]

    if not tickers:
        logger.info("No tickers to update prices for")
        return datetime.now(UTC).isoformat()

    # Fetch latest prices for all tickers
    logger.info(f"Fetching latest prices for {len(tickers)} tickers")

    # Use a small period to get just the latest price
    latest_prices = {}
    for ticker in tickers:
        try:
            # Fetch data for the last day
            df = data_fetcher.fetch_data(ticker, period="1d")
            if not df.empty:
                # Get the latest close price
                latest_prices[ticker] = df.iloc[-1]["Close"]
                logger.debug(f"Updated price for {ticker}: {latest_prices[ticker]}")
            else:
                logger.warning(f"No price data available for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e!s}")

    # Update prices for all positions
    for group in portfolio_groups:
        # Update stock position price
        if group.stock_position and group.stock_position.ticker in latest_prices:
            group.stock_position.price = latest_prices[group.stock_position.ticker]
            # Update market exposure and market value based on new price
            group.stock_position.market_exposure = (
                group.stock_position.price * group.stock_position.quantity
            )
            group.stock_position.market_value = (
                group.stock_position.price * group.stock_position.quantity
            )
            group.stock_position.beta_adjusted_exposure = (
                group.stock_position.market_exposure * group.stock_position.beta
            )

        # Update option position prices
        for option in group.option_positions:
            if option.ticker in latest_prices:
                option.price = latest_prices[option.ticker]
                # Update market_value based on new price
                option.market_value = option.price * option.quantity
                # We don't update market_exposure for options as it's based on notional value

    # Return the current timestamp
    current_time = datetime.now(UTC).isoformat()
    logger.info(f"Prices updated at {current_time}")
    return current_time


def update_portfolio_summary_with_prices(
    portfolio_groups: list[PortfolioGroup], _: PortfolioSummary, data_fetcher=None
) -> PortfolioSummary:
    """Update the portfolio summary with the latest prices.

    Args:
        portfolio_groups: List of portfolio groups to update prices for
        summary: The current portfolio summary
        data_fetcher: Optional data fetcher to use for price updates

    Returns:
        Updated portfolio summary with the latest prices
    """
    # Update prices for all positions
    price_updated_at = update_portfolio_prices(portfolio_groups, data_fetcher)

    # Recalculate the portfolio summary with the updated prices
    updated_summary = calculate_portfolio_summary(portfolio_groups)

    # Set the price_updated_at timestamp
    updated_summary.price_updated_at = price_updated_at

    return updated_summary


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
    if summary.price_updated_at:
        logger.info(f"Prices Last Updated: {summary.price_updated_at}")
    logger.info(f"Net Market Exposure: {format_currency(summary.net_market_exposure)}")

    logger.info(
        f"Portfolio Estimated Value: {format_currency(summary.portfolio_estimate_value)}"
    )
    logger.info(f"Stock Value: {format_currency(summary.stock_value)}")
    logger.info(f"Option Value: {format_currency(summary.option_value)}")
    if summary.pending_activity_value != 0.0:
        logger.info(
            f"Pending Activity: {format_currency(summary.pending_activity_value)}"
        )
    logger.info(f"Beta: {format_beta(summary.portfolio_beta)}")
    logger.info(f"Short %: {summary.short_percentage:.1f}%")
    logger.info(f"Cash %: {summary.cash_percentage:.1f}%")

    # Cash positions
    logger.info(
        f"Cash: {format_currency(summary.cash_like_value)} ({summary.cash_like_count} positions)"
    )

    # Long exposure
    logger.info("Long Exposure:")
    logger.info(f"  Total: {format_currency(summary.long_exposure.total_exposure)}")
    logger.info(f"  Stocks: {format_currency(summary.long_exposure.stock_exposure)}")
    logger.info(
        f"  Options: {format_currency(summary.long_exposure.option_delta_exposure)}"
    )

    # Short exposure
    logger.info("Short Exposure:")
    logger.info(f"  Total: {format_currency(summary.short_exposure.total_exposure)}")
    logger.info(f"  Stocks: {format_currency(summary.short_exposure.stock_exposure)}")
    logger.info(
        f"  Options: {format_currency(summary.short_exposure.option_delta_exposure)}"
    )

    # Options exposure
    logger.info("Options Exposure:")
    logger.info(
        f"  Total Delta: {format_currency(summary.options_exposure.total_exposure)}"
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


def calculate_position_weight(
    position_market_exposure: float, portfolio_net_exposure: float
) -> float:
    """Calculate a position's weight in the portfolio.

    Args:
        position_market_exposure: The market exposure of the position
        portfolio_net_exposure: The net market exposure of the entire portfolio

    Returns:
        The position's weight as a decimal (0.0 to 1.0)
    """
    if not portfolio_net_exposure:
        raise ValueError("Portfolio net exposure cannot be zero")
    return position_market_exposure / portfolio_net_exposure


def calculate_beta_adjusted_net_exposure(
    long_beta_adjusted: float, short_beta_adjusted: float
) -> float:
    """Calculate the beta-adjusted net exposure.

    This function calculates the beta-adjusted net exposure by adding the
    long and short beta-adjusted exposures. Short exposures should be
    represented as negative values. This is the single source of truth
    for this calculation throughout the application.

    Args:
        long_beta_adjusted: The beta-adjusted exposure of long positions (positive value)
        short_beta_adjusted: The beta-adjusted exposure of short positions (negative value)

    Returns:
        The beta-adjusted net exposure
    """
    return long_beta_adjusted + short_beta_adjusted


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
            "net_exposure": format_currency(group.net_exposure),
            "beta": format_beta(group.beta),
            "beta_adjusted_exposure": format_currency(group.beta_adjusted_exposure),
            "options_delta_exposure": format_currency(group.options_delta_exposure)
            if has_options
            else "N/A",
        }
    except Exception as e:
        logger.error(f"Error formatting metrics for {group.ticker}: {e}", exc_info=True)
        raise ValueError(f"Error calculating metrics for {group.ticker}") from e
