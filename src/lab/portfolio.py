import argparse
import os
import re  # Regular expressions for cleaning
import sys

import pandas as pd

from src.lab.option_utils import (
    calculate_simple_delta,
    parse_option_description,
)
from src.v2.data_fetcher import DataFetcher


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate portfolio beta from a CSV file."
    )
    parser.add_argument("portfolio_csv", help="Path to the portfolio CSV file")
    return parser.parse_args()


# --- Helper Functions ---
def clean_currency(value):
    """Removes currency symbols, commas, and handles parentheses for negatives."""
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return 0.0

    # Remove leading/trailing whitespace and non-breaking spaces
    value = value.strip().replace("\u00a0", "")

    # Remove currency symbols and commas
    value = re.sub(r"[$,]", "", value)

    # Handle parentheses for negative numbers
    is_negative = value.startswith("(") and value.endswith(")")
    if is_negative:
        value = "-" + value[1:-1]

    # Convert to float, return 0.0 if conversion fails
    try:
        return float(value)
    except ValueError:
        return 0.0


def clean_symbol(symbol):
    """Removes leading non-breaking spaces and asterisks.
    Does NOT remove leading hyphen used for options."""
    if not isinstance(symbol, str):
        return None
    # Remove leading non-breaking space and potential spaces
    symbol = symbol.lstrip("\u00a0 ")
    # Remove trailing asterisks often used for footnotes
    symbol = symbol.rstrip("*")
    # We keep the leading hyphen here as it's used by is_option
    return symbol


def is_option(symbol):
    """Check if a symbol represents an option (starts with '-')."""
    # Ensure symbol is cleaned first if needed, but here we check original format primarily
    if not isinstance(symbol, str):
        return False
    return symbol.strip().startswith("-")  # Check stripped original symbol


def is_valid_ticker(symbol):
    """Check if a symbol is a valid stock/ETF ticker."""
    if not isinstance(symbol, str):
        return False
    # Remove any leading/trailing whitespace
    symbol = symbol.strip()
    # Check if empty
    if not symbol:
        return False
    # Check if it's a known invalid symbol
    invalid_symbols = ["021ESC017", "Pending Activity"]
    if symbol in invalid_symbols:
        return False
    # Basic pattern for valid tickers (letters and possibly numbers)
    return bool(re.match(r"^[A-Z]+[A-Z0-9]*$", symbol))


def get_betas(tickers):
    """Fetches beta values for a list of STOCK/ETF tickers using FMP API."""
    print(f"\nFetching beta data for {len(tickers)} stock/ETF tickers...")
    fetcher = DataFetcher()
    betas = {}
    missing_beta = []

    for ticker in tickers:
        # Skip any None or empty strings that might have slipped through
        if not ticker or not isinstance(ticker, str):
            continue

        # Double-check it's not an option symbol (shouldn't happen if filtering in main is correct)
        if is_option(ticker):
            print(
                f"WARN: Option symbol '{ticker}' unexpectedly passed to get_betas. Skipping."
            )
            continue

        try:
            # Fetch data for beta calculation
            df_hist = fetcher.fetch_data(ticker, period="1y")
            if df_hist is not None and not df_hist.empty:
                # Calculate beta using daily returns against SPY
                market_data = fetcher.fetch_market_data("SPY", period="1y")

                # Calculate daily returns
                stock_returns = df_hist["Close"].pct_change().dropna()
                market_returns = market_data["Close"].pct_change().dropna()

                # Align the data
                common_dates = stock_returns.index.intersection(market_returns.index)
                if (
                    len(common_dates) < 10
                ):  # Require minimum data points for reliable beta
                    print(
                        f"  Insufficient overlapping data for {ticker} ({len(common_dates)} points). Using default (1.0)."
                    )
                    betas[ticker] = 1.0
                    missing_beta.append(ticker)
                    continue

                stock_returns = stock_returns[common_dates]
                market_returns = market_returns[common_dates]

                # Calculate beta
                covariance = stock_returns.cov(market_returns)
                market_variance = market_returns.var()

                if market_variance == 0:
                    print(
                        f"  Market variance is zero for {ticker}. Cannot calculate beta. Using default (1.0)."
                    )
                    betas[ticker] = 1.0
                    missing_beta.append(ticker)
                    continue

                beta = covariance / market_variance
                betas[ticker] = beta
                print(f"  Calculated beta for {ticker}: {beta:.2f}")
            else:
                print(f"  No data available for {ticker}. Using default (1.0).")
                betas[ticker] = 1.0
                missing_beta.append(ticker)
        except Exception as e:
            print(
                f"  Could not fetch/calculate beta for {ticker}: {e}. Using default (1.0)."
            )
            betas[ticker] = 1.0
            missing_beta.append(ticker)

    print("\nBeta calculation complete.")
    if missing_beta:
        print(
            "\nWarning: Beta data was unavailable or defaulted to 1.0 for the following tickers:"
        )
        print(", ".join(missing_beta))

    return betas


def process_options(df: pd.DataFrame, beta_map: dict) -> tuple[pd.DataFrame, dict]:
    """Process option positions and calculate exposures."""
    option_positions = []

    # Filter for option rows
    option_rows = df[df["Symbol"].apply(is_option)]

    # Create a map of stock positions and prices
    stock_positions = {}
    for _, row in df[~df["Symbol"].apply(is_option)].iterrows():
        try:
            price = clean_currency(row["Last Price"])
            if price > 0:
                symbol = row["Cleaned Symbol"]
                stock_positions[symbol] = {
                    "price": price,
                    "quantity": int(row["Quantity"]),
                    "value": clean_currency(row["Current Value"]),
                    "beta": beta_map.get(symbol, 1.0),
                }
        except Exception:
            continue

    for _, row in option_rows.iterrows():
        try:
            # Clean the last price
            last_price = clean_currency(row["Last Price"])

            # Parse option details
            option = parse_option_description(
                row["Description"], int(row["Quantity"]), last_price
            )

            # Get underlying price
            stock_info = stock_positions.get(option.underlying)
            if not stock_info:
                print(
                    f"Warning: No price found for underlying {option.underlying} for option {row['Symbol']}"
                )
                continue

            underlying_price = stock_info["price"]

            # Calculate delta
            delta = calculate_simple_delta(option, underlying_price)

            # Store option with its calculations
            option_positions.append(
                {
                    "Symbol": row["Symbol"],
                    "Underlying": option.underlying,
                    "Type": f"{option.option_type}",
                    "Strike": option.strike,
                    "Expiry": option.expiry.strftime("%Y-%m-%d"),
                    "Quantity": option.quantity,
                    "Current Value": option.market_value,
                    "Notional Value": option.notional_value,
                    "Delta": delta,
                    "Delta Exposure": delta * option.notional_value,
                    "Beta": beta_map.get(option.underlying, 1.0),
                    "Beta-Adjusted Exposure": delta
                    * option.notional_value
                    * beta_map.get(option.underlying, 1.0),
                }
            )

        except Exception as e:
            print(f"Warning: Could not process option {row['Symbol']}: {e}")
            continue

    # Convert to DataFrame
    if option_positions:
        options_df = pd.DataFrame(option_positions)
        # Group by underlying for summary
        summary = {}
        for underlying, group in options_df.groupby("Underlying"):
            stock_info = stock_positions.get(underlying, {})
            stock_value = stock_info.get("value", 0)
            stock_quantity = stock_info.get("quantity", 0)
            stock_beta = stock_info.get("beta", 1.0)

            total_delta_exposure = group["Delta Exposure"].sum()
            total_beta_adjusted = group["Beta-Adjusted Exposure"].sum()

            summary[underlying] = {
                "Stock Position": stock_quantity if stock_quantity != 0 else None,
                "Stock Value": stock_value,
                "Stock Beta": stock_beta,
                "Total Delta Exposure": total_delta_exposure,
                "Total Beta-Adjusted Exposure": total_beta_adjusted,
                "Net Exposure": stock_value + total_delta_exposure,
                "Net Beta-Adjusted": (stock_value * stock_beta) + total_beta_adjusted,
                "Call Count": len(group[group["Type"] == "CALL"]),
                "Put Count": len(group[group["Type"] == "PUT"]),
                "Net Option Value": group["Current Value"].sum(),
            }
        return options_df, summary
    else:
        return pd.DataFrame(), {}


def main():
    """Main function to calculate portfolio beta."""
    args = parse_args()

    # Check if file exists
    if not os.path.exists(args.portfolio_csv):
        print(f"Error: File not found: {args.portfolio_csv}")
        sys.exit(1)

    # 1. Load data from CSV file
    try:
        df = pd.read_csv(args.portfolio_csv)

        # Simple check if headers look right
        if (
            "Symbol" not in df.columns
            or "Current Value" not in df.columns
            or "Type" not in df.columns
        ):
            raise ValueError("CSV headers not found or incorrect. Check data format.")

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        print("Please ensure the file exists and starts with the header row.")
        sys.exit(1)  # Stop execution if CSV parsing fails

    # 2. Clean values and symbols
    df["Clean Value"] = df["Current Value"].apply(clean_currency)
    df["Cleaned Symbol"] = df["Symbol"].apply(clean_symbol)

    # Remove rows with no valid original symbol
    df = df.dropna(subset=["Symbol"])

    # 3. Filter Holdings (using original Symbol)
    cash_symbols = ["SPAXX", "FMPXX"]
    exclude_types = ["Cash", None, ""]  # Also exclude rows with empty/None Type

    # Filter out cash, options, invalid tickers, and rows with missing Type
    df_filtered = df[
        (~df["Type"].isin(exclude_types))
        & (~df["Symbol"].isin(cash_symbols))
        & (~df["Symbol"].apply(is_option))
        & (df["Cleaned Symbol"].apply(is_valid_ticker))  # Add valid ticker check
    ].copy()

    # Remove rows where cleaning resulted in None or empty string
    df_filtered = df_filtered.dropna(subset=["Cleaned Symbol"])
    df_filtered = df_filtered[df_filtered["Cleaned Symbol"] != ""]

    original_rows = len(df)
    filtered_rows = original_rows - len(df_filtered)
    print(f"\nFiltered out {filtered_rows} rows:")
    print(f"- {len(df[df['Type'].isin(exclude_types)])} cash/invalid type positions")
    print(f"- {len(df[df['Symbol'].apply(is_option)])} option positions")
    print(f"- {len(df[~df['Cleaned Symbol'].apply(is_valid_ticker)])} invalid tickers")
    print(f"Calculating beta based on {len(df_filtered)} stock/ETF positions.")

    if df_filtered.empty:
        print(
            "\nNo valid stock/ETF positions found after filtering. Cannot calculate beta."
        )
        sys.exit(1)

    # 4. Fetch Betas (for cleaned stock symbols)
    # Use the 'Cleaned Symbol' column for fetching beta
    tickers_to_fetch = df_filtered["Cleaned Symbol"].unique().tolist()
    beta_map = get_betas(tickers_to_fetch)  # Pass only the list of tickers

    # Map betas back using the cleaned symbol
    df_filtered["Beta"] = df_filtered["Cleaned Symbol"].map(beta_map)
    df_filtered["Beta"] = df_filtered["Beta"].fillna(1.0)  # Default beta for any misses

    # 5. Calculate Portfolio Beta
    total_portfolio_value_net = df_filtered["Clean Value"].sum()
    total_portfolio_value_abs = df_filtered["Clean Value"].abs().sum()

    if total_portfolio_value_net == 0:
        print("\nNet portfolio value is zero. Cannot calculate beta.")
        sys.exit(1)

    # Use net value for weights to properly represent position impact
    df_filtered["Weight"] = df_filtered["Clean Value"] / total_portfolio_value_net
    df_filtered["Position_Beta"] = df_filtered["Weight"] * df_filtered["Beta"]

    portfolio_beta = df_filtered["Position_Beta"].sum()

    # Process options
    options_df, options_summary = process_options(df, beta_map)

    # Display Results
    print("\n=== Stock-Only Portfolio Analysis ===")
    display_df = df_filtered[
        ["Cleaned Symbol", "Type", "Clean Value", "Weight", "Beta", "Position_Beta"]
    ].copy()
    display_df.rename(columns={"Cleaned Symbol": "Symbol"}, inplace=True)

    display_df["Clean Value"] = display_df["Clean Value"].map("${:,.2f}".format)
    display_df["Weight"] = display_df["Weight"].map(
        "{:+.2%}".format
    )  # Added + to show sign
    display_df["Beta"] = display_df["Beta"].map("{:.3f}".format)
    display_df["Position_Beta"] = display_df["Position_Beta"].map(
        "{:+.4f}".format
    )  # Added + to show sign

    print(display_df.to_string(index=False))

    print("\n--- Final Result ---")
    print(f"Total Stock/ETF Value (Net): ${total_portfolio_value_net:,.2f}")
    print(f"Total Stock/ETF Value (Abs): ${total_portfolio_value_abs:,.2f}")
    print(f"Portfolio Beta (stocks only): {portfolio_beta:.3f}")

    # Calculate and display dollar sensitivities using net value
    spy_moves = [0.01, 0.05, 0.10]  # 1%, 5%, 10% moves
    print("\n--- Dollar Value Sensitivity to SPY Movements ---")
    print("If SPY moves by:      Your portfolio is expected to move by:")
    for move in spy_moves:
        dollar_impact = total_portfolio_value_net * portfolio_beta * move
        print(
            f"  {move:>7.1%}           ${dollar_impact:>12,.2f}  ({(portfolio_beta * move):>+6.2%})"
        )

    print("\nNotes:")
    print(
        "- Cash, Money Market funds, and Options were excluded from this calculation."
    )
    print("- Beta values calculated using FMP API with 1-year daily returns vs SPY.")
    print("- Stocks/ETFs with unavailable beta defaulted to 1.0.")
    print("- Dollar sensitivities assume linear market relationship.")
    print("- Past performance and correlations do not guarantee future results.")
    print("\nTo properly include options in the future, we would need to:")
    print("1. Parse option details from the Description column in portfolio.csv")
    print(
        "2. Calculate implied volatility for each option using market prices (requires option data source)"
    )
    print("3. Use Black-Scholes (or similar model) to compute option deltas")
    print("4. Adjust position sizes by option deltas")
    print("5. Use underlying stock betas for option positions")
    print("6. Consider gamma risk for large market moves")

    if not options_df.empty:
        print("\n=== Options Analysis ===")
        print("\nOptions Positions:")
        display_options = options_df[
            [
                "Underlying",
                "Type",
                "Strike",
                "Expiry",
                "Quantity",
                "Delta",
                "Delta Exposure",
                "Beta-Adjusted Exposure",
            ]
        ].copy()

        # Format numeric columns
        display_options["Delta"] = display_options["Delta"].map("{:+.2f}".format)
        display_options["Delta Exposure"] = display_options["Delta Exposure"].map(
            "${:+,.2f}".format
        )
        display_options["Beta-Adjusted Exposure"] = display_options[
            "Beta-Adjusted Exposure"
        ].map("${:+,.2f}".format)

        print(display_options.to_string(index=False))

        print("\nOptions and Stock Summary by Underlying:")
        for underlying, summary in options_summary.items():
            print(f"\n{underlying}:")
            # Show stock position if exists
            if summary["Stock Position"] is not None:
                print(
                    f"  Stock Position: {summary['Stock Position']:+,d} shares (${summary['Stock Value']:,.2f})"
                )
                print(f"  Stock Beta: {summary['Stock Beta']:.2f}")
            else:
                print("  Stock Position: None")

            print(
                f"  Options: {summary['Call Count']} calls, {summary['Put Count']} puts"
            )
            print(f"  Net Option Value: ${summary['Net Option Value']:,.2f}")
            print(f"  Option Delta Exposure: ${summary['Total Delta Exposure']:+,.2f}")
            print(f"  Net Position Exposure: ${summary['Net Exposure']:+,.2f}")
            print(
                f"  Net Beta-Adjusted Exposure: ${summary['Net Beta-Adjusted']:+,.2f}"
            )

        # Calculate combined exposure
        print("\n=== Combined Portfolio Analysis ===")

        # Calculate long and short exposures
        long_positions = df_filtered[df_filtered["Clean Value"] > 0]
        short_positions = df_filtered[df_filtered["Clean Value"] < 0]

        # Long exposure calculations
        total_long_value = long_positions["Clean Value"].sum()
        total_long_beta_exposure = (
            long_positions["Clean Value"] * long_positions["Beta"]
        ).sum()
        long_beta = (
            total_long_beta_exposure / total_long_value if total_long_value != 0 else 0
        )

        # Short exposure calculations
        total_short_value = abs(short_positions["Clean Value"].sum())
        total_short_beta_exposure = abs(
            (short_positions["Clean Value"] * short_positions["Beta"]).sum()
        )
        short_beta = (
            total_short_beta_exposure / total_short_value
            if total_short_value != 0
            else 0
        )

        # Options exposure
        total_options_delta = sum(
            s["Total Delta Exposure"] for s in options_summary.values()
        )
        total_options_beta_adjusted = sum(
            s["Total Beta-Adjusted Exposure"] for s in options_summary.values()
        )

        print("\n=== Exposure Analysis ===")
        print("\n1. Long Stock Positions:")
        print(f"Long Value: ${total_long_value:,.2f}")
        print(f"Beta-Adjusted Long Exposure: ${total_long_beta_exposure:,.2f}")
        print(f"Long Portfolio Beta: {long_beta:.2f}")

        print("\n2. Short Stock Positions:")
        print(f"Short Value: ${total_short_value:,.2f}")
        print(f"Beta-Adjusted Short Exposure: ${total_short_beta_exposure:,.2f}")
        print(f"Short Portfolio Beta: {short_beta:.2f}")
        print(
            f"Short % of Portfolio (by Abs Value): {(total_short_value/total_portfolio_value_abs)*100:.1f}%"
        )

        print("\n3. Options Positions:")
        print(f"Net Options Delta Exposure: ${total_options_delta:,.2f}")
        print(f"Beta-Adjusted Options Exposure: ${total_options_beta_adjusted:,.2f}")

        print("\n4. Net Portfolio Exposure:")
        print("Before Shorts:")
        before_shorts = total_long_beta_exposure + total_options_beta_adjusted
        print(f"Beta-Adjusted Exposure (Long + Options): ${before_shorts:,.2f}")

        print("\nAfter Shorts:")
        after_shorts = before_shorts - total_short_beta_exposure
        print(
            f"Net Beta-Adjusted Exposure (Long + Options - Shorts): ${after_shorts:,.2f}"
        )
        print(
            f"Shorts Reduce Exposure By: ${total_short_beta_exposure:,.2f} ({(total_short_beta_exposure/before_shorts)*100:.1f}%)"
        )

        print("\nDetailed Short Positions:")
        for _, row in short_positions.iterrows():
            print(
                f"  {row['Cleaned Symbol']}: ${abs(row['Clean Value']):,.2f} (Beta: {row['Beta']:.2f}, Beta-Adjusted: ${abs(row['Clean Value'] * row['Beta']):,.2f})"
            )

        # Update dollar sensitivities to use combined exposure
        print("\n--- Dollar Value Sensitivity (All Positions) ---")
        print("If SPY moves by:      Your portfolio is expected to move by:")
        for move in spy_moves:
            dollar_impact = total_portfolio_value_net * portfolio_beta * move
            print(
                f"  {move:>7.1%}           ${dollar_impact:>12,.2f}  ({(portfolio_beta * move):>+6.2%})"
            )


if __name__ == "__main__":
    main()
