#!/usr/bin/env python3
"""
Script to compare summary card exposures with position details exposures,
using the same methods as the UI components.

This script loads portfolio data from a CSV file, calculates the summary card values,
and compares them with the sum of exposures from the position details as they would
appear in the UI.
"""

import os
import sys
import pandas as pd

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.folio.portfolio import process_portfolio_data
from src.folio.components.summary_cards import format_summary_card_values
from src.folio.utils import format_currency


def load_portfolio_data(csv_path):
    """Load portfolio data from a CSV file."""
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded portfolio data from {csv_path} with {len(df)} rows")
        return df
    except Exception as e:
        print(f"Error loading portfolio data: {e}")
        return None


def compare_exposures():
    """Compare summary card exposures with position details exposures."""
    # Try to load the private portfolio data first
    private_csv_path = "private-data/portfolio-private.csv"
    sample_csv_path = "sample-data/sample-portfolio.csv"
    
    if os.path.exists(private_csv_path):
        df = load_portfolio_data(private_csv_path)
        csv_path = private_csv_path
    elif os.path.exists(sample_csv_path):
        df = load_portfolio_data(sample_csv_path)
        csv_path = sample_csv_path
    else:
        print("No portfolio data found")
        return
    
    if df is None:
        return
    
    # Process the portfolio data
    print("Processing portfolio data...")
    result = process_portfolio_data(df)
    
    # Check the structure of the result
    if isinstance(result, tuple):
        if len(result) == 3:
            # Newer version: (groups, summary, cash_like_positions)
            groups, summary, cash_like_positions = result
        elif len(result) == 2:
            # Possible alternative: (groups, cash_like_positions)
            groups, cash_like_positions = result
            from src.folio.portfolio import calculate_portfolio_summary
            summary = calculate_portfolio_summary(groups, cash_like_positions, 0.0)
    else:
        # If result is not a tuple, it's likely just the groups
        groups = result
        from src.folio.portfolio import calculate_portfolio_summary
        summary = calculate_portfolio_summary(groups, [], 0.0)
        
    # Ensure we have a valid summary object
    if not hasattr(summary, 'to_dict'):
        print("Error: summary object does not have to_dict method")
        print(f"Type of summary: {type(summary)}")
        # Create a minimal summary for testing
        from src.folio.data_model import PortfolioSummary, ExposureBreakdown
        empty_exposure = ExposureBreakdown()
        summary = PortfolioSummary(
            net_market_exposure=0.0,
            portfolio_beta=0.0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure
        )
    
    # Get the summary card values
    summary_dict = summary.to_dict()
    formatted_values = format_summary_card_values(summary_dict)
    
    # Extract the values from the formatted values
    portfolio_value = formatted_values[0]
    net_exposure = formatted_values[1]
    portfolio_beta = formatted_values[3]
    beta_adjusted_net_exposure = formatted_values[4]
    long_exposure = formatted_values[5]
    short_exposure = formatted_values[7]
    options_exposure = formatted_values[9]
    cash_value = formatted_values[11]
    
    print("\nSummary Card Values:")
    print(f"Portfolio Value: {portfolio_value}")
    print(f"Net Exposure: {net_exposure}")
    print(f"Portfolio Beta: {portfolio_beta}")
    print(f"Beta-Adjusted Net Exposure: {beta_adjusted_net_exposure}")
    print(f"Long Exposure: {long_exposure}")
    print(f"Short Exposure: {short_exposure}")
    print(f"Options Exposure: {options_exposure}")
    print(f"Cash Value: {cash_value}")
    
    # Calculate the sum of exposures from the position details as they would appear in the UI
    print("\nCalculating position details exposures as shown in the UI...")
    
    # Initialize counters for UI exposures
    total_ui_market_value = 0.0
    total_ui_beta_adjusted_exposure = 0.0
    total_ui_delta_exposure = 0.0
    
    # Process each group as it would be displayed in the UI
    print("\nPosition Details (as shown in the UI):")
    print("=" * 80)
    print(f"{'Ticker':<10} {'Market Value':<15} {'Beta-Adjusted':<15} {'Delta Exposure':<15}")
    print("-" * 80)
    
    for group in groups:
        ticker = group.ticker
        
        # Get values as they would be displayed in the UI
        market_value = group.net_exposure  # This is what's shown as "Total Value" in the UI
        beta_adjusted = group.beta_adjusted_exposure  # This is what's shown as "Beta-Adjusted Exposure" in the UI
        delta_exposure = group.total_delta_exposure  # This is what's shown as "Total Delta Exposure" in the UI
        
        # Print the values for this group
        print(f"{ticker:<10} {format_currency(market_value):<15} {format_currency(beta_adjusted):<15} {format_currency(delta_exposure):<15}")
        
        # Add to totals
        total_ui_market_value += market_value
        total_ui_beta_adjusted_exposure += beta_adjusted
        total_ui_delta_exposure += delta_exposure
    
    print("-" * 80)
    print(f"{'TOTAL':<10} {format_currency(total_ui_market_value):<15} {format_currency(total_ui_beta_adjusted_exposure):<15} {format_currency(total_ui_delta_exposure):<15}")
    print("=" * 80)
    
    # Extract numeric values from formatted strings
    def extract_numeric(value):
        return float(value.replace("$", "").replace(",", ""))
    
    summary_net_exposure = extract_numeric(net_exposure)
    summary_beta_adjusted_net_exposure = extract_numeric(beta_adjusted_net_exposure)
    summary_long_exposure = extract_numeric(long_exposure)
    summary_short_exposure = extract_numeric(short_exposure)
    summary_options_exposure = extract_numeric(options_exposure)
    
    # Compare with summary card values
    print("\nComparison with Summary Card Values:")
    print(f"Net Exposure (Summary): {net_exposure}")
    print(f"Net Exposure (UI Total): {format_currency(total_ui_market_value)}")
    print(f"Difference: {format_currency(summary_net_exposure - total_ui_market_value)}")
    
    print(f"\nBeta-Adjusted Net Exposure (Summary): {beta_adjusted_net_exposure}")
    print(f"Beta-Adjusted Exposure (UI Total): {format_currency(total_ui_beta_adjusted_exposure)}")
    print(f"Difference: {format_currency(summary_beta_adjusted_net_exposure - total_ui_beta_adjusted_exposure)}")
    
    # Calculate long and short exposures from UI values
    ui_long_exposure = 0.0
    ui_short_exposure = 0.0
    
    for group in groups:
        if group.stock_position:
            stock = group.stock_position
            if stock.quantity >= 0:  # Long position
                ui_long_exposure += stock.market_value
            else:  # Short position
                ui_short_exposure += stock.market_value  # Already negative
        
        # Process option positions
        for opt in group.option_positions:
            if opt.delta_exposure >= 0:  # Long position
                ui_long_exposure += opt.delta_exposure
            else:  # Short position
                ui_short_exposure += opt.delta_exposure  # Already negative
    
    print(f"\nLong Exposure (Summary): {long_exposure}")
    print(f"Long Exposure (UI Calculated): {format_currency(ui_long_exposure)}")
    print(f"Difference: {format_currency(summary_long_exposure - ui_long_exposure)}")
    
    print(f"\nShort Exposure (Summary): {short_exposure}")
    print(f"Short Exposure (UI Calculated): {format_currency(ui_short_exposure)}")
    print(f"Difference: {format_currency(summary_short_exposure - ui_short_exposure)}")
    
    print(f"\nOptions Exposure (Summary): {options_exposure}")
    print(f"Options Exposure (UI Total): {format_currency(total_ui_delta_exposure)}")
    print(f"Difference: {format_currency(summary_options_exposure - total_ui_delta_exposure)}")
    
    # Determine if the summary card values match the UI values
    print("\nConclusion:")
    if abs(summary_net_exposure - total_ui_market_value) < 0.01:
        print("Net Exposure in summary cards MATCHES the total market value shown in the UI")
    else:
        print("Net Exposure in summary cards DOES NOT MATCH the total market value shown in the UI")
    
    if abs(summary_beta_adjusted_net_exposure - total_ui_beta_adjusted_exposure) < 0.01:
        print("Beta-Adjusted Net Exposure in summary cards MATCHES the total beta-adjusted exposure shown in the UI")
    else:
        print("Beta-Adjusted Net Exposure in summary cards DOES NOT MATCH the total beta-adjusted exposure shown in the UI")
    
    if abs(summary_options_exposure - total_ui_delta_exposure) < 0.01:
        print("Options Exposure in summary cards MATCHES the total delta exposure shown in the UI")
    else:
        print("Options Exposure in summary cards DOES NOT MATCH the total delta exposure shown in the UI")


if __name__ == "__main__":
    compare_exposures()
