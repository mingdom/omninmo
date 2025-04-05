"""Script to analyze portfolio values and identify discrepancies."""

import os
import sys

import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.folio.portfolio import process_portfolio_data


def parse_currency(x):
    """Parse currency values from the CSV file."""
    if not isinstance(x, str):
        return 0
    # Handle negative values in parentheses like ($1100.00)
    if x.startswith("(") and x.endswith(")"):
        return -float(
            x.replace("(", "")
            .replace(")", "")
            .replace("$", "")
            .replace(",", "")
            .strip()
        )
    else:
        return float(x.replace("$", "").replace(",", "").strip())


def main():
    """Analyze portfolio values and identify discrepancies."""
    # Load the sample portfolio
    sample_path = os.path.join("src", "folio", "assets", "sample-portfolio.csv")
    df = pd.read_csv(sample_path)

    # Process the portfolio
    groups, summary, cash_like_positions = process_portfolio_data(df)

    # Calculate values directly from the CSV
    csv_values = {}
    csv_values["total"] = df["Current Value"].apply(parse_currency).sum()

    # Calculate long and short values
    long_values = []
    short_values = []
    cash_values = []

    for _index, row in df.iterrows():
        symbol = row["Symbol"]
        value = parse_currency(row["Current Value"])

        # Identify if it's a cash position
        is_cash = False
        if "Type" in row and isinstance(row["Type"], str) and row["Type"].upper() == "CASH":
            is_cash = True
            cash_values.append((symbol, value))

        # Identify if it's a short position (negative value or starts with -)
        if value < 0 or (isinstance(symbol, str) and symbol.strip().startswith("-")):
            short_values.append((symbol, value))
        elif not is_cash:
            long_values.append((symbol, value))

    # Calculate totals
    csv_values["long_total"] = sum(value for _, value in long_values)
    csv_values["short_total"] = sum(value for _, value in short_values)
    csv_values["cash_total"] = sum(value for _, value in cash_values)
    csv_values["net"] = csv_values["long_total"] + csv_values["short_total"] + csv_values["cash_total"]

    # Get values from the processed portfolio
    processed_values = {}
    processed_values["portfolio_value"] = summary.portfolio_value
    processed_values["total_value_net"] = summary.total_value_net
    processed_values["total_value_abs"] = summary.total_value_abs
    processed_values["long_exposure"] = summary.long_exposure.total_value
    processed_values["short_exposure"] = summary.short_exposure.total_value
    processed_values["cash_like_value"] = summary.cash_like_value

    # Print the results



    # Print detailed position lists
    for symbol, value in sorted(long_values, key=lambda x: abs(x[1]), reverse=True):
        pass

    for symbol, value in sorted(short_values, key=lambda x: abs(x[1]), reverse=True):
        pass

    for symbol, value in sorted(cash_values, key=lambda x: abs(x[1]), reverse=True):
        pass

    for _pos in cash_like_positions:
        pass


if __name__ == "__main__":
    main()
