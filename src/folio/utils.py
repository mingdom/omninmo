"""Utility functions for portfolio analysis and data processing.

This module provides core functionality for portfolio analysis, including:
- Beta calculation and cash-like instrument detection
- Portfolio data processing and grouping
- Currency and number formatting
- Portfolio metrics and summary calculations

Error Handling Principles:
-------------------------
1. DO NOT swallow errors unless absolutely critical to the application's stability.
2. Functions should propagate errors up the call stack to allow proper handling at the appropriate level.
3. If error handling is needed, it should be:
   - Explicitly documented in the function's docstring
   - Limited to specific, known error cases
   - Accompanied by detailed logging
   - Justified by a critical need (e.g., preventing application crash in a core service)

Example of good error handling:
```python
def critical_service_function():
    try:
        result = potentially_failing_operation()
        return result
    except KnownError as e:
        # Log detailed error info
        logger.error(f"Critical operation failed: {e}")
        # Re-raise with context
        raise ServiceError("Service cannot continue") from e
```

Example of bad error handling (avoid this):
```python
def utility_function():
    try:
        result = operation()
        return result
    except Exception as e:
        # DON'T DO THIS - swallowing errors silently
        logger.warning(f"Operation failed: {e}")
        return None  # or some default value
```
"""

import re
from typing import Optional

import pandas as pd

from src.lab.option_utils import (calculate_option_delta,
                                  parse_option_description)
from src.v2.data_fetcher import DataFetcher

from .data_model import (ExposureBreakdown, PortfolioGroup, PortfolioSummary,
                         StockPosition, create_portfolio_group)
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
    """Calculates the beta (systematic risk) for a given financial instrument.

    Beta measures the volatility of an instrument in relation to the overall market.
    Returns 0.0 when beta cannot be meaningfully calculated (e.g., for money market funds,
    or instruments with insufficient price history).

    Args:
        ticker: The instrument's symbol
        description: Description of the security, used to identify cash-like positions

    Returns:
        float: The calculated beta value, or 0.0 if beta cannot be meaningfully calculated

    Raises:
        RuntimeError: If the DataFetcher has not been initialized or fails to fetch data
        ValueError: If the data is invalid or calculations result in invalid values
        KeyError: If the data format is invalid (missing required columns)
    """
    # For cash-like instruments, return 0 without calculation
    if ticker in ["CASH", "USD"] or is_likely_money_market(ticker, description):
        logger.info(f"Using default beta of 0.0 for cash-like position: {ticker}")
        return 0.0

    if not data_fetcher:
        raise RuntimeError("DataFetcher not initialized - check API key configuration")

    # Fetch required data
    stock_data = data_fetcher.fetch_data(ticker)
    market_data = data_fetcher.fetch_market_data()

    if stock_data is None:
        raise RuntimeError(f"Failed to fetch data for ticker {ticker}")
    if market_data is None:
        raise RuntimeError("Failed to fetch market index data")

    try:
        # Calculate returns - let KeyError propagate if 'Close' column missing
        stock_returns = stock_data["Close"].pct_change(fill_method=None).dropna()
        market_returns = market_data["Close"].pct_change(fill_method=None).dropna()

        # Align data by index
        aligned_stock, aligned_market = stock_returns.align(
            market_returns, join="inner"
        )

        if aligned_stock.empty or len(aligned_stock) < 2:
            logger.debug(
                f"Insufficient overlapping data points for {ticker}, cannot calculate meaningful beta"
            )
            return 0.0

        # Calculate beta components
        market_variance = aligned_market.var()
        covariance = aligned_stock.cov(aligned_market)

        if pd.isna(market_variance):
            raise ValueError(
                f"Market variance calculation resulted in NaN for {ticker}"
            )
        if abs(market_variance) < 1e-12:
            logger.debug(
                f"Market variance is near-zero for {ticker}, cannot calculate meaningful beta"
            )
            return 0.0
        if pd.isna(covariance):
            raise ValueError(f"Covariance calculation resulted in NaN for {ticker}")

        beta = covariance / market_variance
        if pd.isna(beta):
            raise ValueError(f"Beta calculation resulted in NaN for {ticker}")

        logger.info(f"Calculated beta of {beta:.2f} for {ticker}")
        return beta

    except (ValueError, pd.errors.InvalidIndexError) as e:
        # Only catch calculation-related errors
        if "No historical data found" in str(e):
            # This is not a critical error - just log a warning
            logger.warning(f"Error calculating beta for {ticker}: {e}. Assuming not cash-like.")
            return 0.0
        else:
            # Log other calculation errors as errors
            logger.error(f"Error calculating beta for {ticker}: {e}")
            raise


def format_currency(value: float) -> str:
    """Formats a numerical value as a currency string (USD).

    Includes a dollar sign, comma separators for thousands, and two decimal places.
    Negative values are represented with a leading minus sign.

    Args:
        value: The numerical value to format.

    Returns:
        A string representing the value in USD currency format (e.g., "$1,234.56", "-$500.00").
    """
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Formats a numerical value as a percentage string.

    Multiplies the value by 100 and appends a percentage sign. Displays one decimal place.

    Args:
        value: The numerical value to format (e.g., 0.25 for 25%).

    Returns:
        A string representing the value as a percentage (e.g., "25.0%").

    Note:
        This function assumes the input value is a decimal representation of the percentage.
        If you have a whole number (e.g., 25 for 25%), divide it by 100 first.
    """
    # The original function multiplied by 100 implicitly in the f-string format.
    # Making it explicit for clarity, though the format specifier handles it.
    return f"{value * 100:.1f}%"


def format_beta(value: float) -> str:
    """Formats a beta value with a trailing Greek beta symbol (β).

    Displays the value with two decimal places.

    Args:
        value: The numerical beta value.

    Returns:
        A string representing the beta value followed by 'β' (e.g., "1.23β").
    """
    return f"{value:.2f}β"


def clean_currency_value(value_str: str) -> float:
    """Converts a formatted currency string into a float.

    Handles various common currency formats:
    - Removes dollar signs ($)
    - Removes comma separators (,)
    - Handles empty strings or double dashes ("--") by returning 0.0
    - Interprets values enclosed in parentheses, e.g., "(123.45)", as negative numbers

    Args:
        value_str: The currency string to clean (e.g., "$1,234.56", "(500.00)", "--")

    Returns:
        The numerical float representation of the currency string

    Raises:
        TypeError: If input is not a string or string-convertible type
        ValueError: If the string cannot be converted to a float after cleaning
    """
    if not isinstance(value_str, (str, int, float)):
        raise TypeError(f"Expected string or numeric input, got {type(value_str)}")

    value_str = str(value_str)

    # Handle empty or dash values
    if value_str in ("--", ""):
        return 0.0

    # Remove currency symbols and commas
    cleaned_str = value_str.replace("$", "").replace(",", "")

    # Handle negative values in parentheses like (123.45)
    is_negative = False
    if cleaned_str.startswith("(") and cleaned_str.endswith(")"):
        cleaned_str = cleaned_str[1:-1]
        is_negative = True

    try:
        value = float(cleaned_str)
        return -value if is_negative else value
    except ValueError as e:
        raise ValueError(
            f"Could not convert '{value_str}' to float: invalid format"
        ) from e


def is_option(symbol: str) -> bool:
    """Determines if a financial symbol likely represents an option contract.

    This function checks if the provided symbol string starts with a hyphen ('-').
    This is a common convention used by some brokers (like Fidelity) in exported
    data files to distinguish options from their underlying stocks.

    Args:
        symbol: The financial symbol string to check.

    Returns:
        True if the symbol starts with '-', False otherwise or if the input is not a string.

    Note:
        This method is based on a specific formatting convention and might not be
        universally applicable to all data sources. A more robust approach might involve
        parsing the option's description string. See `is_option_desc`.
    """
    if not isinstance(symbol, str):
        return False
    return symbol.strip().startswith("-")


def process_portfolio_data(
    df: pd.DataFrame,
) -> tuple[list[PortfolioGroup], PortfolioSummary, list[dict]]:
    """Processes a raw portfolio DataFrame to generate structured portfolio data and summary metrics.

    This core function takes a DataFrame, typically loaded from a broker's CSV export,
    and transforms it into a list of `PortfolioGroup` objects and a `PortfolioSummary`.
    Each `PortfolioGroup` aggregates a stock position and its associated option positions.

    Steps:
    1.  **Validation:** Checks for required columns in the input DataFrame.
    2.  **Cleaning:** Strips whitespace from symbols, fills missing values in 'Type' and 'Description'.
    3.  **Option Identification:** Defines a helper function `is_option_desc` to identify options based on
        description format (e.g., 'AAPL APR 17 2025 $220 CALL').
    4.  **Statistics:** Calculates basic portfolio stats (total positions, value, unique stocks/options).
    5.  **Stock Processing:** Iterates through non-option rows, cleans data (price, quantity), calculates
        beta using `get_beta`, and stores stock info in `stock_positions` dictionary.
        *Important:* Skips rows with missing quantity or invalid price (<=0). This is where cash positions
        like SPAXX might be filtered out if they lack a quantity.
    6.  **Grouping:** Iterates through the identified `stock_positions`. For each stock:
        a.  Creates `stock_data` dictionary.
        b.  Finds all related option rows in the original DataFrame using `is_option_desc` and matching
            the underlying symbol.
        c.  Parses each related option using `parse_option_description` from `option_utils`.
        d.  Calculates option delta using `calculate_option_delta` (Black-Scholes).
        e.  Calculates various exposure metrics (notional, delta-adjusted, beta-adjusted).
        f.  Collects option data in `option_data` list.
        g.  Creates a `PortfolioGroup` using `create_portfolio_group` with stock and option data.
        h.  Appends the group to the `groups` list.
    7.  **Summary Calculation:** Calculates overall portfolio summary metrics (total values, beta,
        exposure breakdowns) using `calculate_portfolio_summary`.
    8.  **Return:** Returns the list of `PortfolioGroup` objects and the `PortfolioSummary`.

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
            components={}
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
        logger.info(f"Filtered out {filtered_count} invalid entries: {filtered_symbols}")
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
    # Iterate only over rows identified as non-options
    for index, row in stock_df.iterrows():
        symbol_raw = row["Symbol"]
        description = row["Description"]

        # Proceed with processing potentially valid stock/ETF positions
        try:
            # Handle NaN or non-string symbols
            if pd.isna(symbol_raw) or not isinstance(symbol_raw, str):
                logger.warning(
                    f"Row {index}: Invalid symbol type: {type(symbol_raw)}. Skipping."
                )
                continue

            symbol = symbol_raw.rstrip(
                "*"
            )  # Remove trailing asterisks (common for preferred shares etc.)

            # Validate critical data is present
            if not symbol:
                logger.warning(
                    f"Row {index}: Empty symbol found in row: {row.to_dict()}. Skipping."
                )
                continue

            # Check for quantity - this is the key filter for SPAXX previously
            if pd.isna(row["Quantity"]) or row["Quantity"] == "--":
                # Allow positions with zero quantity if they have value (e.g., settled options?)
                # But log a warning if value exists without quantity.
                current_val = clean_currency_value(row["Current Value"])
                if current_val != 0:
                    logger.warning(
                        f"Row {index}: Stock {symbol} has missing/invalid quantity ('{row['Quantity']}') but non-zero value ({format_currency(current_val)}). Processing based on value only."
                    )
                    # Assign quantity 0, maybe handle differently later
                    quantity = 0
                else:
                    logger.warning(
                        f"Row {index}: Stock {symbol} has missing/invalid quantity ('{row['Quantity']}') and zero value. Skipping."
                    )
                    continue
            else:
                try:
                    # Attempt to convert quantity to integer, handle potential errors
                    quantity = int(
                        float(row["Quantity"])
                    )  # Convert potential float string first
                except (ValueError, TypeError) as qty_err:
                    logger.warning(
                        f"Row {index}: Stock {symbol} has invalid quantity format ('{row['Quantity']}'): {qty_err}. Skipping."
                    )
                    continue

            # Check if this is a known cash-like position before handling missing price
            is_known_cash = is_cash_or_short_term(symbol, beta=None, description=description)

            # Check for price - required for beta and option calculations (unless it's a known cash-like position)
            if pd.isna(row["Last Price"]) or row["Last Price"] in ("--", ""):
                if is_known_cash:
                    logger.info(
                        f"Row {index}: Cash-like position {symbol} has missing price ('{row['Last Price']}'). Using default beta of 0."
                    )
                    # Continue processing with default values for cash-like positions
                    price = 0.0
                    beta = 0.0
                    is_cash_like = True
                else:
                    logger.warning(
                        f"Row {index}: Stock {symbol} has missing price ('{row['Last Price']}'). Cannot calculate beta or use for options. Skipping."
                    )
                    continue

            price = clean_currency_value(row["Last Price"])
            # Allow zero price? Maybe for delisted stocks? Log carefully.
            if price < 0:
                logger.warning(
                    f"Row {index}: Stock {symbol} has invalid negative price ({price}). Skipping."
                )
                continue
            elif price == 0:
                logger.warning(
                    f"Row {index}: Stock {symbol} has zero price. Beta/Option calculations may be affected."
                )

            # Recalculate value based on cleaned price and quantity for consistency
            # Use original 'Current Value' if quantity is zero or price is zero? Need a consistent rule.
            cleaned_current_value = clean_currency_value(row["Current Value"])
            calculated_value = (
                price * quantity
                if quantity != 0 and price != 0
                else cleaned_current_value
            )

            # Sanity check: Compare calculated value with reported 'Current Value'
            if (
                quantity != 0
                and price != 0
                and abs(calculated_value - cleaned_current_value) > 0.01
            ):  # Tolerance for float issues
                logger.warning(
                    f"Row {index}: Stock {symbol} calculated value ({format_currency(calculated_value)}) differs from reported 'Current Value' ({format_currency(cleaned_current_value)}). Using reported value."
                )
                value_to_use = cleaned_current_value
            else:
                value_to_use = calculated_value

            # Get Beta - requires valid ticker and fetcher
            beta = get_beta(symbol, description)

            # Check if this is a cash-like instrument based on beta, symbol, or description
            is_cash_like = is_cash_or_short_term(symbol, beta=beta, description=description)

            if is_cash_like:
                logger.info(f"Identified cash-like position: {symbol} (beta: {beta:.4f}, description: '{description}'), Value: {format_currency(value_to_use)}")

                # Check if we already have a cash-like position with this ticker
                if symbol in cash_like_by_ticker:
                    # Add to existing position's market value
                    cash_like_by_ticker[symbol]["market_value"] += value_to_use
                    # Update quantity if applicable
                    if quantity != 0:  # Only update if the new quantity is non-zero
                        cash_like_by_ticker[symbol]["quantity"] += quantity
                    # Recalculate beta-adjusted exposure
                    cash_like_by_ticker[symbol]["beta_adjusted_exposure"] = cash_like_by_ticker[symbol]["market_value"] * beta
                    logger.info(f"Combined with existing cash-like position for {symbol}. New total: {format_currency(cash_like_by_ticker[symbol]['market_value'])}")
                else:
                    # Create new cash-like position
                    cash_like_position = {
                        "ticker": symbol,
                        "quantity": quantity,
                        "market_value": value_to_use,
                        "beta": beta,
                        "beta_adjusted_exposure": value_to_use * beta,
                        "description": description
                    }
                    cash_like_by_ticker[symbol] = cash_like_position
                    cash_like_positions.append(cash_like_position)
            else:
                # Regular stock position
                stock_positions[symbol] = {
                    "price": price,
                    "quantity": quantity,
                    "value": value_to_use,
                    "beta": beta,
                    "percent_of_account": float(
                        str(row["Percent Of Account"]).replace("%", "")
                    )
                    / 100.0
                    if pd.notna(row["Percent Of Account"])
                    and row["Percent Of Account"] != "--"
                    else 0.0,
                    "account_type": row["Type"],  # Store account type (Cash/Margin) for reference - not related to position type
                }
                logger.debug(
                    f"Successfully processed stock: {symbol}, Qty: {quantity}, Price: {price}, Value: {value_to_use}, Beta: {beta:.2f}"
                )

        except ValueError as e:
            # More specific exception for data conversion errors (e.g., clean_currency_value)
            logger.warning(
                f"Row {index}: Data conversion error for stock '{symbol_raw}': {e}. Skipping row."
            )
            continue
        except TypeError as e:
            # More specific exception for type errors during processing
            logger.warning(
                f"Row {index}: Type error for stock '{symbol_raw}': {e}. Skipping row."
            )
            continue
        except Exception as e:
            # Catch unexpected errors during stock processing
            logger.error(
                f"Row {index}: Unexpected error processing stock '{symbol_raw}': {e}",
                exc_info=True,  # Include stack trace in log
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
                # 'clean_value': value, # Redundant? market_value is clean
                "weight": percent_of_account,
                "position_beta": beta,  # Seems redundant with 'beta'? Clarify usage.
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
        logger.warning("No valid portfolio groups were created after processing. This may be an all-cash portfolio.")
        # Instead of raising an error, proceed with just cash-like positions if any exist
        if not cash_like_positions:
            logger.warning("No cash-like positions found either. Returning empty summary.")
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
                components={}
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
        summary = calculate_portfolio_summary(
            groups, cash_like_positions
        )
        logger.info("Portfolio summary calculated successfully.")
    except Exception as summary_err:
        logger.error(
            f"Failed to calculate portfolio summary: {summary_err}", exc_info=True
        )
        # Decide how to handle summary failure - raise or return groups with None summary?
        raise  # Raising seems safer to indicate incomplete results

    logger.info(f"=== Portfolio Loading Finished: {len(groups)} groups created, {len(cash_like_positions)} cash-like positions identified. ===")
    return groups, summary, cash_like_positions


def calculate_portfolio_summary(
    groups: list[PortfolioGroup], cash_like_positions: Optional[list[dict]] = None
) -> PortfolioSummary:
    """Calculates aggregated summary metrics for the entire portfolio.

    This function iterates through the provided list of `PortfolioGroup` objects
    (each containing a stock and its options) and computes various portfolio-level
    statistics like total value, overall beta, and exposure breakdowns (long, short, options).

    It categorizes exposure based on:
    - **Stocks:** Long stock positions contribute to long exposure, short stock positions
      contribute to short exposure.
    - **Options:** Delta-adjusted notional value is used.
        - Long Calls & Short Puts contribute to *long* options delta exposure.
        - Short Calls & Long Puts contribute to *short* options delta exposure.
    Beta adjustments are applied to both stock and option exposures.

    Args:
        df: The original raw portfolio DataFrame (potentially used for fetching
            overall values or cash balances in the future, currently unused).
        groups: A list of `PortfolioGroup` objects representing the processed
                and grouped portfolio positions.
        cash_like_positions: A list of dictionaries representing cash-like positions
                           identified during portfolio processing.

    Returns:
        A `PortfolioSummary` object containing the calculated metrics:
        - `total_value_net`: Net market value (Long Exposure - Short Exposure).
        - `total_value_abs`: Absolute market value (Long Exposure + Short Exposure).
        - `portfolio_beta`: Weighted average beta of the portfolio.
        - `long_exposure`: Breakdown of long value (stocks, options, total, beta-adjusted).
        - `short_exposure`: Breakdown of short value (stocks, options, total, beta-adjusted).
        - `options_exposure`: Breakdown of total option delta exposure (long, short, total, beta-adjusted).
        - `short_percentage`: Short exposure as a percentage of absolute total exposure.
        - `exposure_reduction_percentage`: Short exposure as a percentage of long exposure.
        - `cash_like_positions`: List of positions with very low beta (< 0.1).
        - `cash_like_value`: Total value of cash-like positions.
        - `cash_like_count`: Number of cash-like positions.

    Raises:
        Exception: Propagates any exceptions encountered during calculation.

    TODO:
        - Incorporate cash balances explicitly into the summary (e.g., from SPAXX).
        - Enhance exposure classification for options: Consider moneyness, IV, expiry.
          Deep ITM calls behave like stock, while far OTM options have different risk profiles.
        - Calculate and include portfolio-level Greeks (Theta, Vega, Gamma) for more
          advanced risk assessment.
        - Add scenario analysis / stress testing capabilities.
        - Utilize the input `df` for potentially missing information or cross-checks.
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

        # --- Create ExposureBreakdown objects ---
        long_exposure = ExposureBreakdown(
            stock_value=long_stocks["value"],
            stock_beta_adjusted=long_stocks["beta_adjusted"],
            option_delta_value=long_options_delta["value"],
            option_beta_adjusted=long_options_delta["beta_adjusted"],
            total_value=long_stocks["value"] + long_options_delta["value"],
            total_beta_adjusted=long_stocks["beta_adjusted"]
            + long_options_delta["beta_adjusted"],
            description="Long market exposure (Stocks + Positive Delta Options)",
            formula="Long Stocks + Long Calls Delta Exp + Short Puts Delta Exp",
            components={
                "Long Stocks Value": long_stocks["value"],
                "Long Options Delta Exp": long_options_delta["value"],
            },
        )

        short_exposure = ExposureBreakdown(
            stock_value=short_stocks["value"],
            stock_beta_adjusted=short_stocks["beta_adjusted"],
            option_delta_value=short_options_delta["value"],
            option_beta_adjusted=short_options_delta["beta_adjusted"],
            total_value=short_stocks["value"] + short_options_delta["value"],
            total_beta_adjusted=short_stocks["beta_adjusted"]
            + short_options_delta["beta_adjusted"],
            description="Short market exposure (Stocks + Negative Delta Options)",
            formula="Short Stocks + Short Calls Delta Exp + Long Puts Delta Exp",
            components={
                "Short Stocks Value": short_stocks["value"],
                "Short Options Delta Exp": short_options_delta["value"],
            },
        )

        # Total options exposure based on delta contributions
        options_exposure = ExposureBreakdown(
            stock_value=0,  # Options only view
            stock_beta_adjusted=0,
            option_delta_value=long_options_delta["value"]
            + short_options_delta["value"],  # Sum of absolute delta exposures
            option_beta_adjusted=long_options_delta["beta_adjusted"]
            + short_options_delta[
                "beta_adjusted"
            ],  # Sum of absolute beta-adjusted delta exposures
            total_value=long_options_delta["value"] + short_options_delta["value"],
            total_beta_adjusted=long_options_delta["beta_adjusted"]
            + short_options_delta["beta_adjusted"],
            description="Total absolute delta exposure from options",
            formula="Sum(|Option Delta Exposures|)",
            components={
                "Long Options Delta Exp": long_options_delta["value"],
                "Short Options Delta Exp": short_options_delta["value"],
                "Net Options Delta Exp": long_options_delta["value"]
                - short_options_delta["value"],  # Add net for info
                "Total Option Market Value": total_option_market_value,  # Add market value sum for info
            },
        )

        # --- Calculate total portfolio values ---
        # Net Value: Total market value of long positions minus short positions
        # This should ideally align with the broker's total account value if cash is included.
        # Currently calculated based on directional exposure.
        total_value_net = long_exposure.total_value - short_exposure.total_value

        # Absolute Value: Sum of market values of all positions, ignoring direction.
        # Represents the total capital deployed or leverage.
        total_value_abs = long_exposure.total_value + short_exposure.total_value

        # --- Calculate portfolio beta ---
        # Weighted average beta: (Net Beta-Adjusted Exposure) / (Net Total Value)
        # This represents the portfolio's expected volatility relative to the market.
        net_beta_adjusted_exposure = (
            long_exposure.total_beta_adjusted - short_exposure.total_beta_adjusted
        )
        portfolio_beta = (
            net_beta_adjusted_exposure / total_value_net
            if total_value_net != 0  # Avoid division by zero
            else 0.0
        )

        # --- Calculate exposure percentages ---
        # Short Percentage: How much of the total deployed capital is short?
        short_percentage = (
            short_exposure.total_value / total_value_abs if total_value_abs > 0 else 0.0
        )
        # Exposure Reduction: How much is the long exposure offset by short positions?
        exposure_reduction = (
            short_exposure.total_value / long_exposure.total_value
            if long_exposure.total_value > 0  # Avoid division by zero
            else 0.0  # If no long exposure, reduction is 0 or undefined? Treat as 0.
        )

        # --- Process cash-like positions ---
        cash_like_value = sum(pos["market_value"] for pos in cash_like_positions)
        cash_like_count = len(cash_like_positions)

        # Create StockPosition objects for cash-like positions
        cash_like_stock_positions = [
            StockPosition(
                ticker=pos["ticker"],
                quantity=pos["quantity"],
                market_value=pos["market_value"],
                beta=pos["beta"],
                beta_adjusted_exposure=pos["beta_adjusted_exposure"]
            )
            for pos in cash_like_positions
        ]

        logger.info(f"Processed {cash_like_count} cash-like positions with total value: {format_currency(cash_like_value)}")

        # Include cash-like positions in total value
        if cash_like_value > 0:
            # Add cash-like value to total_value_abs
            total_value_abs += cash_like_value
            # Add cash-like value to total_value_net (cash is always positive)
            total_value_net += cash_like_value

        # --- Create and return summary object ---
        summary = PortfolioSummary(
            total_value_net=total_value_net,
            total_value_abs=total_value_abs,
            portfolio_beta=portfolio_beta,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=short_percentage * 100,  # Convert to percentage
            exposure_reduction_percentage=exposure_reduction * 100,  # Convert to percentage
            cash_like_positions=cash_like_stock_positions,
            cash_like_value=cash_like_value,
            cash_like_count=cash_like_count
        )

        logger.info("Portfolio summary created successfully.")
        log_summary_details(summary)  # Add helper to log details
        return summary

    except Exception as e:
        logger.error("Error calculating portfolio summary", exc_info=True)
        # Re-raise the exception to signal failure
        raise RuntimeError("Failed to calculate portfolio summary") from e


def log_summary_details(summary: PortfolioSummary):
    """Helper function to log the details of the PortfolioSummary object."""
    logger.info("--- Portfolio Summary Details ---")
    logger.info(f"Net Total Value: {format_currency(summary.total_value_net)}")
    logger.info(f"Absolute Total Value: {format_currency(summary.total_value_abs)}")
    logger.info(f"Portfolio Beta: {format_beta(summary.portfolio_beta)}")
    logger.info(f"Short Exposure % (of Abs Value): {summary.short_percentage:.1f}%")
    logger.info(
        f"Exposure Reduction % (Short/Long): {summary.exposure_reduction_percentage:.1f}%"
    )

    # Log cash-like information
    logger.info(f"Cash-Like Value: {format_currency(summary.cash_like_value)}")
    logger.info(f"Cash-Like Count: {summary.cash_like_count}")
    logger.info(f"Cash-Like % of Portfolio: {summary.cash_like_value / summary.total_value_abs * 100:.1f}% (of Abs Value)" if summary.total_value_abs > 0 else "Cash-Like % of Portfolio: 0.0%")

    logger.info("  Long Exposure Breakdown:")
    logger.info(
        f"    Total Value: {format_currency(summary.long_exposure.total_value)}"
    )
    logger.info(
        f"    Beta-Adj Value: {format_currency(summary.long_exposure.total_beta_adjusted)}"
    )
    logger.info(
        f"    Stock Value: {format_currency(summary.long_exposure.stock_value)}"
    )
    logger.info(
        f"    Option Delta Value: {format_currency(summary.long_exposure.option_delta_value)}"
    )

    logger.info("  Short Exposure Breakdown:")
    logger.info(
        f"    Total Value: {format_currency(summary.short_exposure.total_value)}"
    )
    logger.info(
        f"    Beta-Adj Value: {format_currency(summary.short_exposure.total_beta_adjusted)}"
    )
    logger.info(
        f"    Stock Value: {format_currency(summary.short_exposure.stock_value)}"
    )
    logger.info(
        f"    Option Delta Value: {format_currency(summary.short_exposure.option_delta_value)}"
    )

    logger.info("  Options Exposure Breakdown:")
    logger.info(
        f"    Total Absolute Delta Value: {format_currency(summary.options_exposure.total_value)}"
    )
    logger.info(
        f"    Total Absolute Beta-Adj Value: {format_currency(summary.options_exposure.total_beta_adjusted)}"
    )
    logger.info(
        f"    Long Delta Contribution: {format_currency(summary.options_exposure.components.get('Long Options Delta Exp', 0))}"
    )
    logger.info(
        f"    Short Delta Contribution: {format_currency(summary.options_exposure.components.get('Short Options Delta Exp', 0))}"
    )
    logger.info(
        f"    Net Delta Contribution: {format_currency(summary.options_exposure.components.get('Net Options Delta Exp', 0))}"
    )
    logger.info(
        f"    Total Option Market Value: {format_currency(summary.options_exposure.components.get('Total Option Market Value', 0))}"
    )
    logger.info("--------------------------------")


def calculate_position_metrics(group: PortfolioGroup) -> dict:
    """Calculates display-focused metrics for a single PortfolioGroup.

    This function takes a `PortfolioGroup` (representing a stock and its associated options)
    and computes several key metrics formatted for display in the UI or reports.

    Args:
        group: The `PortfolioGroup` object to calculate metrics for.

    Returns:
        A dictionary containing formatted string representations of:
        - 'total_value': The combined market value of the stock and options in the group.
        - 'beta': The beta of the underlying stock.
        - 'beta_adjusted_exposure': The group's total value adjusted by the underlying's beta.
        - 'options_delta_exposure': The net delta exposure contribution from all options
          in the group (sum of individual option delta exposures). Returns "N/A" if
          the group has no options.

    Raises:
        ValueError: If the input `group` is None or if an error occurs during calculation.
                    This is raised to prevent silently showing incorrect data in the UI.
    """
    logger.debug(
        f"Calculating display metrics for group {group.ticker if group else 'None'}"
    )

    if not group:
        logger.error("Cannot calculate metrics for a None group.")
        # Raising ValueError as per the docstring to signal failure clearly
        raise ValueError("Input PortfolioGroup cannot be None")

    try:
        # Access pre-calculated values from the PortfolioGroup object
        total_value = group.total_value
        beta = group.beta  # This should be the underlying's beta stored in the group
        beta_adjusted_exposure = group.beta_adjusted_exposure
        options_delta_exposure = (
            group.options_delta_exposure
        )  # Net delta exposure from options

        return {
            "total_value": format_currency(total_value),
            "beta": format_beta(beta),
            "beta_adjusted_exposure": format_currency(beta_adjusted_exposure),
            # Check if there were any options processed for this group
            "options_delta_exposure": format_currency(options_delta_exposure)
            if group.option_positions  # Check if the list is non-empty
            else "N/A",
            # TODO: Add other useful display metrics like:
            # - Stock Weight within group
            # - Options Weight within group
            # - Net Options Premium Value
            # - Total Gamma/Theta/Vega for the group (if calculated)
        }
    except AttributeError as e:
        logger.error(
            f"Error accessing attributes for group {group.ticker}: {e}", exc_info=True
        )
        raise ValueError(
            f"Missing expected attribute in PortfolioGroup for {group.ticker}"
        ) from e
    except Exception as e:
        # Catch any other unexpected errors during formatting or calculation
        logger.error(
            f"Unexpected error calculating metrics for group {group.ticker}: {e}",
            exc_info=True,
        )
        # Raise to avoid silently showing incorrect data
        raise ValueError(
            f"Error calculating position metrics for {group.ticker}"
        ) from e


# Patterns and keywords to identify cash-like instruments without hardcoding specific symbols
def is_likely_money_market(ticker: str | float | None, description: str | float | None = "") -> bool:
    """Determines if a position is likely a money market fund based on patterns and keywords.

    Args:
        ticker: The instrument's symbol
        description: The instrument's description

    Returns:
        bool: True if the position is likely a money market fund
    """
    # Handle NaN, None, or non-string inputs
    if pd.isna(ticker) or ticker is None:
        return False

    # Convert to string if needed
    if not isinstance(ticker, str):
        try:
            ticker = str(ticker)
        except:
            return False

    # Handle description similarly
    if pd.isna(description) or description is None:
        description = ""
    elif not isinstance(description, str):
        try:
            description = str(description)
        except:
            description = ""

    # Convert inputs to uppercase for case-insensitive matching
    ticker_upper = ticker.upper()
    description_upper = description.upper() if description else ""

    # Pattern 1: Common money market fund symbol patterns (ending with XX)
    if re.search(r'[A-Z]{2,4}XX$', ticker_upper):
        return True

    # Pattern 2: Description contains money market related terms
    money_market_terms = [
        "MONEY MARKET", "CASH RESERVES", "TREASURY ONLY", "GOVERNMENT LIQUIDITY",
        "CASH MANAGEMENT", "LIQUID ASSETS", "CASH EQUIVALENT", "TREASURY FUND",
        "LIQUIDITY FUND", "CASH FUND", "RESERVE FUND"
    ]

    for term in money_market_terms:
        if term in description_upper:
            return True

    # Pattern 3: Common prefixes for money market funds
    money_market_prefixes = ["SPAXX", "FMPXX", "VMFXX", "SWVXX"]
    for prefix in money_market_prefixes:
        if ticker_upper.startswith(prefix):
            return True

    # Pattern 4: Common short-term treasury ETFs
    short_term_treasury_etfs = ["BIL", "SHY", "SGOV", "GBIL"]
    if ticker_upper in short_term_treasury_etfs:
        return True

    return False

def is_cash_or_short_term(ticker: str | float | None, beta: float | None = None, description: str | float | None = "") -> bool:
    """Determines if a position should be considered cash or cash-like.

    A position is considered cash-like if any of these conditions are met:
    1. It has a very low beta (abs(beta) < 0.1)
    2. It's identified as a likely money market fund based on patterns and keywords
    3. It's a cash symbol like "CASH" or "USD"

    Args:
        ticker: The instrument's symbol
        beta: Pre-calculated beta value if available. If None, will be calculated.
        description: The instrument's description, used for pattern matching

    Returns:
        bool: True if the position should be treated as cash-like, False otherwise.

    Examples:
        >>> is_cash_or_short_term("BIL", beta=0.001)  # Short-term treasury ETF
        True
        >>> is_cash_or_short_term("SPAXX")  # Money market fund (pattern match)
        True
        >>> is_cash_or_short_term("XYZ", description="ABC MONEY MARKET FUND")  # Pattern match in description
        True
        >>> is_cash_or_short_term("AAPL", beta=1.2)  # Regular stock
        False
    """
    # Handle NaN, None, or non-string inputs
    if pd.isna(ticker) or ticker is None:
        return False

    # Convert to string if needed
    if not isinstance(ticker, str):
        try:
            ticker = str(ticker)
        except:
            return False

    # Handle description similarly
    if pd.isna(description) or description is None:
        description = ""
    elif not isinstance(description, str):
        try:
            description = str(description)
        except:
            description = ""

    # Check if it's a cash symbol
    if ticker in ["CASH", "USD"]:
        return True

    # Check if it's likely a money market fund based on patterns
    if is_likely_money_market(ticker, description):
        return True

    # If beta was provided, use it
    if beta is not None:
        return abs(beta) < 0.1

    # Calculate beta if not provided - let errors propagate up
    try:
        calculated_beta = get_beta(ticker)
        return abs(calculated_beta) < 0.1
    except Exception as e:
        logger.warning(f"Error calculating beta for {ticker}: {e}. Assuming not cash-like.")
        return False
