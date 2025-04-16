#!/usr/bin/env python3
"""
Script to analyze portfolio values and identify discrepancies between
calculated values and CSV values.
"""

import sys

import pandas as pd

from src.folio.cash_detection import is_cash_or_short_term
from src.folio.utils import clean_currency_value


def analyze_portfolio_values(csv_path):
    """
    Analyze portfolio values and identify discrepancies.

    Args:
        csv_path: Path to the portfolio CSV file
    """

    # Load the CSV file
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return

    # Initialize counters and accumulators
    total_csv_value = 0.0
    total_calculated_value = 0.0
    discrepancies = []

    # Process each row
    for index, row in df.iterrows():
        symbol = row["Symbol"] if pd.notna(row["Symbol"]) else "N/A"
        description = row["Description"] if pd.notna(row["Description"]) else ""

        # Clean the Current Value from CSV
        csv_value = 0.0
        if pd.notna(row["Current Value"]):
            try:
                csv_value = clean_currency_value(row["Current Value"])
                total_csv_value += csv_value
            except (ValueError, TypeError):
                continue

        # Calculate value based on price and quantity
        calculated_value = 0.0
        if (
            pd.notna(row["Quantity"])
            and pd.notna(row["Last Price"])
            and row["Last Price"] != "--"
        ):
            try:
                quantity = float(row["Quantity"]) if pd.notna(row["Quantity"]) else 0.0
                price = (
                    clean_currency_value(row["Last Price"])
                    if pd.notna(row["Last Price"])
                    else 0.0
                )

                # Check if this is an option (symbol starts with '-' or description has standard option format)
                is_option = False
                if (
                    pd.notna(row["Symbol"])
                    and isinstance(row["Symbol"], str)
                    and row["Symbol"].startswith("-")
                ):
                    is_option = True
                elif pd.notna(row["Description"]) and isinstance(
                    row["Description"], str
                ):
                    desc_parts = row["Description"].strip().split()
                    if len(desc_parts) == 6 and desc_parts[-1] in ["CALL", "PUT"]:
                        is_option = True

                # Apply 100x multiplier for options
                if is_option:
                    calculated_value = quantity * price * 100
                else:
                    calculated_value = quantity * price

                total_calculated_value += calculated_value
            except (ValueError, TypeError):
                calculated_value = csv_value  # Fall back to CSV value
                total_calculated_value += calculated_value
        else:
            # If we can't calculate, use the CSV value
            calculated_value = csv_value
            total_calculated_value += calculated_value

        # Check if this is a cash-like position
        is_cash_like = False
        if pd.notna(symbol) and isinstance(symbol, str):
            is_cash_like = is_cash_or_short_term(symbol, description=description)

        # Check for discrepancy
        discrepancy = abs(csv_value - calculated_value)
        if discrepancy > 0.01:  # Allow for small floating-point differences
            discrepancies.append(
                {
                    "index": index,
                    "symbol": symbol,
                    "description": description,
                    "csv_value": csv_value,
                    "calculated_value": calculated_value,
                    "discrepancy": discrepancy,
                    "is_cash_like": is_cash_like,
                    "quantity": row["Quantity"] if pd.notna(row["Quantity"]) else "N/A",
                    "price": row["Last Price"]
                    if pd.notna(row["Last Price"])
                    else "N/A",
                }
            )

    # Print summary

    # Print discrepancies
    if discrepancies:
        for _d in sorted(discrepancies, key=lambda x: x["discrepancy"], reverse=True):
            pass
    else:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = "private-data/portfolio-private.csv"

    analyze_portfolio_values(csv_path)
