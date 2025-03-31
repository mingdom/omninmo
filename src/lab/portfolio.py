import argparse
import os
import re  # Regular expressions for cleaning

import pandas as pd
import yfinance as yf


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
    """Removes leading non-breaking spaces and asterisks."""
    if not isinstance(symbol, str):
        return None
    # Remove leading non-breaking space and potential spaces
    symbol = symbol.lstrip("\u00a0 ")
    # Remove trailing asterisks often used for footnotes
    symbol = symbol.rstrip("*")
    # Remove option prefixes (like '-') if they exist after cleaning spaces
    if symbol.startswith("-"):
        symbol = symbol[
            1:
        ]  # Keep the core symbol if needed, but we filter these rows later
    return symbol


def get_betas(tickers):
    """Fetches beta values for a list of tickers using yfinance."""
    print(f"\nFetching beta data for {len(tickers)} tickers...")
    # yfinance sometimes struggles with many tickers at once, fetch in batches if needed
    # For simplicity here, fetching all at once.
    yf_tickers = yf.Tickers(tickers)
    betas = {}
    missing_beta = []

    # Accessing history often triggers fetching info if not already cached
    # We access .info directly which should be sufficient for beta
    for ticker in yf_tickers.tickers:
        try:
            # .info can be slow as it fetches a lot of data
            info = yf_tickers.tickers[ticker].info
            beta = info.get("beta")
            if beta is not None:
                betas[ticker] = beta
                print(f"  Fetched beta for {ticker}: {beta:.2f}")
            else:
                # Handle cases where beta is explicitly None (e.g., some funds, preferred shares)
                print(f"  Beta not available for {ticker}. Using default (1.0).")
                betas[ticker] = 1.0  # Default beta if not found
                missing_beta.append(ticker)
        except Exception as e:
            # Handle potential errors during fetch for a specific ticker
            print(
                f"  Could not fetch data for {ticker}: {e}. Using default beta (1.0)."
            )
            betas[ticker] = 1.0  # Default beta on error
            missing_beta.append(ticker)

    print("Beta fetching complete.")
    if missing_beta:
        print(
            "\nWarning: Beta data was unavailable or defaulted to 1.0 for the following tickers:"
        )
        print(", ".join(missing_beta))
    return betas


def main():
    """Main function to calculate portfolio beta."""
    args = parse_args()

    # Check if file exists
    if not os.path.exists(args.portfolio_csv):
        print(f"Error: File not found: {args.portfolio_csv}")
        exit(1)

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
        exit(1)  # Stop execution if CSV parsing fails

    # 2. Clean Data
    df["Symbol"] = df["Symbol"].apply(clean_symbol)
    df["Clean Value"] = df["Current Value"].apply(clean_currency)

    # Remove rows with no valid symbol after cleaning
    df = df.dropna(subset=["Symbol"])

    # 3. Filter Holdings
    # Define symbols/types to exclude
    cash_symbols = ["SPAXX", "FMPXX"]  # Add any other cash/MM symbols
    exclude_types = ["Cash"]
    # Filter out options (heuristics: starts with '-', or has non-stock symbol structure)
    # This regex checks if symbol looks like a standard stock ticker (1-5 letters)
    valid_ticker_regex = re.compile(r"^[A-Z]{1,5}$")

    # Apply filters
    original_rows = len(df)
    df_filtered = df[~df["Type"].isin(exclude_types)]
    df_filtered = df_filtered[~df_filtered["Symbol"].isin(cash_symbols)]

    # Filter out potential options based on symbol format (less reliable than specific flags)
    # We also exclude the '021ESC017' which is not a standard ticker
    df_filtered = df_filtered[
        df_filtered["Symbol"].str.match(valid_ticker_regex, na=False)
    ]

    print(
        f"\nFiltered out {original_rows - len(df_filtered)} rows (Cash, MMF, Options, Other)."
    )
    print(f"Calculating beta based on {len(df_filtered)} positions.")

    if df_filtered.empty:
        print(
            "\nNo valid stock/ETF positions found after filtering. Cannot calculate beta."
        )
        exit(1)

    # 4. Fetch Betas
    tickers_to_fetch = df_filtered["Symbol"].unique().tolist()
    beta_map = get_betas(tickers_to_fetch)
    df_filtered["Beta"] = df_filtered["Symbol"].map(beta_map)

    # Handle cases where mapping might result in NaN (if get_betas failed unexpectedly)
    df_filtered["Beta"] = df_filtered["Beta"].fillna(1.0)

    # 5. Calculate Portfolio Beta
    # Use absolute value for weighting denominator
    total_portfolio_value = df_filtered["Clean Value"].abs().sum()

    if total_portfolio_value == 0:
        print(
            "\nTotal portfolio value of included positions is zero. Cannot calculate beta."
        )
        exit(1)

    df_filtered["Weight"] = df_filtered["Clean Value"].abs() / total_portfolio_value

    # Calculate weighted beta: negative for shorts, positive for longs
    # Assumes 'Type' == 'Short' correctly identifies short positions
    df_filtered["Weighted Beta"] = df_filtered.apply(
        lambda row: -row["Weight"] * row["Beta"]
        if row["Type"] == "Short"
        else row["Weight"] * row["Beta"],
        axis=1,
    )

    portfolio_beta = df_filtered["Weighted Beta"].sum()

    # 6. Display Results
    print("\n--- Portfolio Beta Calculation Summary ---")
    # Select and format columns for display
    display_df = df_filtered[
        ["Symbol", "Type", "Clean Value", "Weight", "Beta", "Weighted Beta"]
    ].copy()
    display_df["Clean Value"] = display_df["Clean Value"].map("${:,.2f}".format)
    display_df["Weight"] = display_df["Weight"].map("{:.2%}".format)
    display_df["Beta"] = display_df["Beta"].map("{:.3f}".format)
    display_df["Weighted Beta"] = display_df["Weighted Beta"].map("{:.4f}".format)

    # Use pandas to_string for better console table formatting
    print(display_df.to_string(index=False))

    print("\n--- Final Result ---")
    print(f"Total Value Included (Abs): ${total_portfolio_value:,.2f}")
    print(f"Calculated Portfolio Beta: {portfolio_beta:.3f}")
    print("\nNotes:")
    print("- Options, Cash, and Money Market funds were excluded.")
    print("- Beta values fetched using yfinance (may be historical beta).")
    print("- Tickers with unavailable beta data were assigned a default beta of 1.0.")


if __name__ == "__main__":
    main()
