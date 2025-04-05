#!/usr/bin/env python3
"""
Portfolio Exposure Debugging Script

This script loads a portfolio CSV file and prints out detailed exposure calculations.
It can be used to debug exposure calculations for any portfolio.

Usage:
    python debug_portfolio.py [path_to_portfolio.csv]

If no path is provided, it will use the default sample portfolio.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

# Add the src directory to the Python path
script_dir = Path(__file__).resolve().parent
src_dir = script_dir.parent
sys.path.append(str(src_dir))

from src.folio.portfolio import process_portfolio_data
from src.folio.utils import format_beta, format_currency


def print_section_header(title):
    """Print a section header with formatting."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_exposure_breakdown(name, breakdown):
    """Print details of an exposure breakdown."""
    print(f"\n{name}:")
    print(f"  Stock Exposure:        {format_currency(breakdown.stock_exposure)}")
    print(f"  Stock Beta-Adjusted:   {format_currency(breakdown.stock_beta_adjusted)}")
    print(
        f"  Option Delta Exposure: {format_currency(breakdown.option_delta_exposure)}"
    )
    print(f"  Option Beta-Adjusted:  {format_currency(breakdown.option_beta_adjusted)}")
    print(f"  Total Exposure:        {format_currency(breakdown.total_exposure)}")
    print(f"  Total Beta-Adjusted:   {format_currency(breakdown.total_beta_adjusted)}")

    # Calculate percentages
    if breakdown.total_exposure > 0:
        stock_pct = (breakdown.stock_exposure / breakdown.total_exposure) * 100
        option_pct = (breakdown.option_delta_exposure / breakdown.total_exposure) * 100
        print(f"  Stock Percentage:      {stock_pct:.2f}%")
        print(f"  Option Percentage:     {option_pct:.2f}%")

    # Print components if available
    if hasattr(breakdown, "components") and breakdown.components:
        print("\n  Components:")
        for key, value in breakdown.components.items():
            print(f"    {key}: {format_currency(value)}")


def print_portfolio_summary(summary):
    """Print a detailed portfolio summary."""
    print_section_header("PORTFOLIO SUMMARY")

    print(f"Net Market Exposure:     {format_currency(summary.net_market_exposure)}")
    print(f"Portfolio Beta:          {format_beta(summary.portfolio_beta)}")
    print(f"Short Percentage:        {summary.short_percentage:.2f}%")
    print(f"Cash-like Value:         {format_currency(summary.cash_like_value)}")
    print(f"Cash-like Count:         {summary.cash_like_count}")
    print(f"Cash Percentage:         {summary.cash_percentage:.2f}%")
    print(
        f"Portfolio Estimated Value: {format_currency(summary.portfolio_estimate_value)}"
    )

    # Calculate options metrics
    long_options = summary.long_exposure.option_delta_exposure
    short_options = summary.short_exposure.option_delta_exposure
    net_options = long_options - short_options

    # Calculate stock metrics
    long_stocks = summary.long_exposure.stock_exposure
    short_stocks = summary.short_exposure.stock_exposure

    # Calculate percentages
    total_exposure = (
        summary.long_exposure.total_exposure + summary.short_exposure.total_exposure
    )
    if total_exposure > 0:
        options_exposure = long_options + short_options
        options_pct = (options_exposure / total_exposure) * 100
        stocks_pct = ((long_stocks + short_stocks) / total_exposure) * 100
        print("\nEXPOSURE BREAKDOWN:")
        print(f"  Options % of Exposure:  {options_pct:.2f}%")
        print(f"  Stocks % of Exposure:   {stocks_pct:.2f}%")

    # Calculate options exposure (absolute sum of long and short)
    options_exposure = long_options + short_options

    print("\nOPTIONS SUMMARY:")
    print(f"  Long Options Exposure:  {format_currency(long_options)}")
    print(f"  Short Options Exposure: {format_currency(short_options)}")
    print(f"  Net Options Exposure:   {format_currency(net_options)}")

    # Print exposure breakdowns
    print_exposure_breakdown("LONG EXPOSURE", summary.long_exposure)
    print_exposure_breakdown("SHORT EXPOSURE", summary.short_exposure)
    print_exposure_breakdown("OPTIONS EXPOSURE", summary.options_exposure)


def print_portfolio_groups(groups):
    """Print details of portfolio groups."""
    print_section_header("PORTFOLIO GROUPS")

    for i, group in enumerate(groups):
        print(f"\nGroup {i+1}: {group.ticker}")
        print(f"  Net Exposure:           {format_currency(group.net_exposure)}")
        print(f"  Beta:                   {format_beta(group.beta)}")
        print(
            f"  Beta-Adjusted Exposure: {format_currency(group.beta_adjusted_exposure)}"
        )
        print(
            f"  Total Delta Exposure:   {format_currency(group.total_delta_exposure)}"
        )
        print(
            f"  Options Delta Exposure: {format_currency(group.options_delta_exposure)}"
        )

        # Print stock position if available
        if group.stock_position:
            stock = group.stock_position
            print("\n  Stock Position:")
            print(f"    Ticker:               {stock.ticker}")
            print(f"    Quantity:             {stock.quantity}")
            print(f"    Beta:                 {format_beta(stock.beta)}")
            print(f"    Market Exposure:      {format_currency(stock.market_exposure)}")
            print(
                f"    Beta-Adjusted Exp:    {format_currency(stock.beta_adjusted_exposure)}"
            )

        # Print option positions if available
        if group.option_positions:
            print("\n  Option Positions:")
            for j, option in enumerate(group.option_positions):
                print(f"    Option {j+1}:")
                print(f"      Ticker:             {option.ticker}")
                print(
                    f"      Description:        {option.option_description if hasattr(option, 'option_description') else 'N/A'}"
                )
                print(f"      Quantity:           {option.quantity}")
                print(f"      Delta:              {option.delta:.4f}")
                print(f"      Beta:               {format_beta(option.beta)}")
                print(
                    f"      Delta Exposure:     {format_currency(option.delta_exposure)}"
                )
                print(
                    f"      Beta-Adjusted Exp:  {format_currency(option.beta_adjusted_exposure)}"
                )


def print_cash_like_positions(positions):
    """Print details of cash-like positions."""
    print_section_header("CASH-LIKE POSITIONS")

    if not positions:
        print("No cash-like positions found.")
        return

    for i, pos in enumerate(positions):
        print(f"\nCash-like Position {i+1}:")
        print(f"  Ticker:               {pos.ticker}")
        print(f"  Quantity:             {pos.quantity}")
        print(f"  Beta:                 {format_beta(pos.beta)}")
        print(f"  Market Exposure:      {format_currency(pos.market_exposure)}")
        print(f"  Beta-Adjusted Exp:    {format_currency(pos.beta_adjusted_exposure)}")


def main():
    """Main function to load portfolio and print exposure calculations."""
    parser = argparse.ArgumentParser(
        description="Debug portfolio exposure calculations"
    )
    parser.add_argument(
        "portfolio_path",
        nargs="?",
        default=os.path.join(src_dir, "src", "folio", "assets", "sample-portfolio.csv"),
        help="Path to portfolio CSV file",
    )
    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.portfolio_path):
        print(f"Error: File not found: {args.portfolio_path}")
        sys.exit(1)

    print(f"Loading portfolio from: {args.portfolio_path}")

    try:
        # Load portfolio data
        df = pd.read_csv(args.portfolio_path)

        # Process portfolio data
        groups, summary, _ = process_portfolio_data(df)

        # Print portfolio groups
        print_portfolio_groups(groups)

        # Print cash-like positions
        print_cash_like_positions(summary.cash_like_positions)

        # Print portfolio summary (at the end for easy reference)
        print_portfolio_summary(summary)

    except Exception as e:
        print(f"Error processing portfolio: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
