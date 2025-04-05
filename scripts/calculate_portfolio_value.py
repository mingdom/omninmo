"""Script to calculate the sum of all position values from the sample portfolio."""

import os
import sys

import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



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
    """Calculate the sum of all position values from the sample portfolio."""
    # Load the sample portfolio
    sample_path = os.path.join("src", "folio", "assets", "sample-portfolio.csv")
    df = pd.read_csv(sample_path)

    # Calculate the sum of all position values
    df["Current Value"].apply(parse_currency).sum()

    # Print all positions with their values
    for _index, row in df.iterrows():
        row["Symbol"]
        value = parse_currency(row["Current Value"])

    # Check for potential issues in the data
    for _index, row in df.iterrows():
        row["Symbol"]
        value_str = row["Current Value"]
        try:
            value = parse_currency(value_str)
            # Check for unusually large values
            if abs(value) > 1000000:
                pass
        except Exception:
            pass


if __name__ == "__main__":
    main()
