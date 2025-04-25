#!/usr/bin/env python
"""
Test script for the Portfolio SPY Simulator.

This script loads a portfolio from a CSV file, updates any zero prices,
and then simulates how the portfolio value changes as SPY moves up or down.
"""

import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("spy_simulator_debug.log", mode="w"),
        logging.StreamHandler(),
    ],
)
# Set specific loggers to INFO to reduce noise
logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.INFO)

import pandas as pd

from src.folio.formatting import format_currency
from src.folio.portfolio import process_portfolio_data
from src.folio.simulator import simulate_portfolio_with_spy_changes


def debug_simulate_portfolio(
    portfolio_groups,
    cash_like_positions=None,
    pending_activity_value=0.0,
    spy_range=10.0,
    steps=21,
):
    """Run the portfolio simulator with detailed logging for debugging.

    Args:
        portfolio_groups: Dictionary of portfolio position groups
        cash_like_positions: List of cash-like positions
        pending_activity_value: Value of pending activity
        spy_range: Range of SPY changes to simulate (e.g., 10.0 for ±10%)
        steps: Number of steps in the simulation (default: 21)
    """
    logger = logging.getLogger("debug_simulator")
    logger.info("Starting detailed portfolio simulation")
    logger.info(f"Using SPY range of ±{spy_range}% with {steps} steps")

    # Calculate the step size
    step_size = (2 * spy_range) / (steps - 1) if steps > 1 else 0

    # Generate the SPY changes
    spy_changes = [-spy_range + i * step_size for i in range(steps)]

    # Ensure we have a zero point
    if 0.0 not in spy_changes and steps > 2:
        # Find the closest point to zero and replace it with zero
        closest_to_zero = min(spy_changes, key=lambda x: abs(x))
        zero_index = spy_changes.index(closest_to_zero)
        spy_changes[zero_index] = 0.0

    # Convert to percentages
    spy_changes = [change / 100.0 for change in spy_changes]

    logger.info(f"SPY changes: {[f'{change:.1%}' for change in spy_changes]}")

    # Get the original results from the simulator
    results = simulate_portfolio_with_spy_changes(
        portfolio_groups=portfolio_groups,
        spy_changes=spy_changes,
        cash_like_positions=cash_like_positions,
        pending_activity_value=pending_activity_value,
    )

    # Add position-by-position analysis
    logger.info("Analyzing position-by-position behavior")

    # Track original values for each position
    original_values = {}
    zero_index = spy_changes.index(0.0)

    # For each position, track how it changes with SPY
    for group in portfolio_groups:
        ticker = group.ticker
        logger.info(f"Analyzing position: {ticker}")

        # Calculate total market value
        stock_value = group.stock_position.market_value if group.stock_position else 0
        option_value = (
            sum(op.market_value for op in group.option_positions)
            if group.option_positions
            else 0
        )
        total_market_value = stock_value + option_value

        # Skip positions with no market value
        if total_market_value == 0:
            logger.info(f"  Skipping {ticker} - zero market value")
            continue

        # Log position details
        logger.info(f"  Beta: {group.beta:.2f}")
        logger.info(f"  Market Value: {format_currency(total_market_value)}")

        if group.stock_position:
            logger.info(
                f"  Stock: {group.stock_position.quantity} shares @ {group.stock_position.price:.2f}"
            )
            logger.info(
                f"    Stock Value: {format_currency(group.stock_position.market_value)}"
            )

        if group.option_positions:
            logger.info(f"  Options: {len(group.option_positions)}")
            for i, option in enumerate(group.option_positions):
                logger.info(
                    f"    Option {i + 1}: {option.quantity} {option.option_type} @ {option.strike:.2f}, expires {option.expiry}"
                )
                logger.info(
                    f"      Price: {option.price:.4f}, Delta: {option.delta:.4f}"
                )
                logger.info(f"      Value: {format_currency(option.market_value)}")

        # Calculate total market value
        stock_value = group.stock_position.market_value if group.stock_position else 0
        option_value = (
            sum(op.market_value for op in group.option_positions)
            if group.option_positions
            else 0
        )
        total_market_value = stock_value + option_value

        # Calculate expected behavior based on beta
        expected_change_at_10pct = group.beta * 0.1 * total_market_value
        logger.info(
            f"  Expected change at +10% SPY: {format_currency(expected_change_at_10pct)}"
        )

        # Store original value
        original_values[ticker] = total_market_value

    # Analyze the results
    logger.info("\nAnalyzing simulation results")

    # Find positions with unexpected behavior

    # Find the indices for min, max, and zero values
    zero_index = next(
        (i for i, change in enumerate(spy_changes) if abs(change) < 0.001), 0
    )
    min_index = 0  # First element (most negative)
    max_index = len(spy_changes) - 1  # Last element (most positive)

    # Calculate the total portfolio change
    total_min = results["portfolio_values"][min_index]
    total_zero = results["portfolio_values"][zero_index]
    total_max = results["portfolio_values"][max_index]

    min_change = spy_changes[min_index]
    max_change = spy_changes[max_index]

    logger.info(
        f"Portfolio value at {min_change:.1%} SPY: {format_currency(total_min)}"
    )
    logger.info(f"Portfolio value at 0% SPY: {format_currency(total_zero)}")
    logger.info(
        f"Portfolio value at {max_change:.1%} SPY: {format_currency(total_max)}"
    )

    down_change = total_min - total_zero
    up_change = total_max - total_zero

    logger.info(
        f"Change on {min_change:.1%} SPY: {format_currency(down_change)} ({down_change / total_zero * 100:.2f}%)"
    )
    logger.info(
        f"Change on {max_change:.1%} SPY: {format_currency(up_change)} ({up_change / total_zero * 100:.2f}%)"
    )

    # Calculate implied beta
    down_beta = -down_change / (total_zero * 0.1)
    up_beta = up_change / (total_zero * 0.1)

    logger.info(f"Implied beta on down moves: {down_beta:.2f}")
    logger.info(f"Implied beta on up moves: {up_beta:.2f}")

    # Add position-level analysis
    if "position_values" in results:
        logger.info("\nAnalyzing position-level contributions:")

        # Calculate position-level changes
        position_changes = {}
        for ticker, values in results["position_values"].items():
            if len(values) > zero_index:
                base_value = values[zero_index]
                if base_value == 0:
                    continue

                # Calculate changes at min and max SPY values
                min_spy_value = values[min_index] if min_index < len(values) else 0
                max_spy_value = values[max_index] if max_index < len(values) else 0

                down_change = min_spy_value - base_value
                up_change = max_spy_value - base_value

                # Calculate percentage changes
                down_pct = (down_change / base_value) * 100 if base_value != 0 else 0
                up_pct = (up_change / base_value) * 100 if base_value != 0 else 0

                # Store the changes
                position_changes[ticker] = {
                    "base_value": base_value,
                    "min_spy_value": min_spy_value,
                    "max_spy_value": max_spy_value,
                    "down_change": down_change,
                    "up_change": up_change,
                    "down_pct": down_pct,
                    "up_pct": up_pct,
                }

                logger.info(f"  {ticker}:")
                logger.info(f"    Base Value: {format_currency(base_value)}")
                logger.info(
                    f"    Change at -10% SPY: {format_currency(down_change)} ({down_pct:.2f}%)"
                )
                logger.info(
                    f"    Change at +10% SPY: {format_currency(up_change)} ({up_pct:.2f}%)"
                )

        # Find positions with largest contributions
        sorted_down = sorted(
            position_changes.items(), key=lambda x: x[1]["down_change"]
        )
        sorted_up = sorted(
            position_changes.items(), key=lambda x: x[1]["up_change"], reverse=True
        )

        logger.info("\nLargest contributors to downside moves:")
        for ticker, data in sorted_down[:5]:
            logger.info(
                f"  {ticker}: {format_currency(data['down_change'])} ({data['down_pct']:.2f}%)"
            )

        logger.info("\nLargest contributors to upside moves:")
        for ticker, data in sorted_up[:5]:
            logger.info(
                f"  {ticker}: {format_currency(data['up_change'])} ({data['up_pct']:.2f}%)"
            )

    # Add the analysis to the results
    results["analysis"] = {
        "down_beta": down_beta,
        "up_beta": up_beta,
        "original_values": original_values,
        "position_changes": position_changes if "position_values" in results else {},
    }

    return results


def main():
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the SPY simulator with detailed analysis"
    )
    parser.add_argument(
        "--focus", type=str, help="Comma-separated list of tickers to focus on"
    )
    parser.add_argument(
        "--range", type=float, default=10.0, help="SPY change range (default: 10.0)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=21,
        help="Number of steps in the simulation (default: 21)",
    )
    args = parser.parse_args()

    # Path to the portfolio CSV file
    csv_path = Path(os.getcwd()) / "private-data" / "portfolio-private.csv"

    if not csv_path.exists():
        sys.exit(1)


    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)

        # Process the portfolio data with price updates
        groups, summary, _ = process_portfolio_data(df, update_prices=True)


        # Filter portfolio if focus is specified
        focus_tickers = []
        if args.focus:
            focus_tickers = [ticker.strip().upper() for ticker in args.focus.split(",")]

            # Create a filtered portfolio with only the specified positions
            filtered_groups = {}

            # Convert list to dictionary if needed
            if isinstance(groups, list):
                groups_dict = {group.ticker: group for group in groups}
            else:
                groups_dict = groups

            for ticker, group in groups_dict.items():
                if ticker in focus_tickers:
                    filtered_groups[ticker] = group

            if not filtered_groups:
                pass
            # Use the filtered groups
            elif isinstance(groups, list):
                groups = list(filtered_groups.values())
            else:
                groups = filtered_groups

        # Run the simulation with detailed debugging
        results = debug_simulate_portfolio(
            portfolio_groups=groups,
            cash_like_positions=summary.cash_like_positions,
            pending_activity_value=getattr(summary, "pending_activity_value", 0.0),
            spy_range=args.range,
            steps=args.steps,
        )

        # Print the results

        # Get the current value (at 0% SPY change)
        current_value = results["current_value"]

        # Print each data point
        for i, spy_change in enumerate(results["spy_changes"]):
            portfolio_value = results["portfolio_values"][i]
            value_change = portfolio_value - current_value
            (
                (value_change / current_value) * 100 if current_value != 0 else 0
            )



        # Create a simple text-based visualization

        # Find min and max values for scaling
        min_value = min(results["portfolio_values"])
        max_value = max(results["portfolio_values"])
        value_range = max_value - min_value

        # Create the visualization
        chart_width = 50
        chart_height = 10
        chart = [" " * chart_width for _ in range(chart_height)]

        # Map SPY changes to x positions
        x_positions = []
        for spy_change in results["spy_changes"]:
            # Map from -10% to +10% to 0 to chart_width-1
            x_pos = int((spy_change + 0.1) / 0.2 * (chart_width - 1))
            x_positions.append(max(0, min(chart_width - 1, x_pos)))

        # Map portfolio values to y positions
        y_positions = []
        for value in results["portfolio_values"]:
            if value_range > 0:
                # Map from min_value to max_value to 0 to chart_height-1
                y_pos = int((value - min_value) / value_range * (chart_height - 1))
                y_positions.append(max(0, min(chart_height - 1, y_pos)))
            else:
                y_positions.append(chart_height // 2)

        # Plot the points
        for x, y in zip(x_positions, y_positions, strict=False):
            row = chart[y]
            chart[y] = row[:x] + "*" + row[x + 1 :]

        # Print the chart (bottom to top)
        for i in range(chart_height - 1, -1, -1):
            pass

        # Add value scale

        # Print summary analysis
        min_value = min(results["portfolio_values"])
        max_value = max(results["portfolio_values"])
        min_change = min_value - current_value
        max_change = max_value - current_value
        min_pct_change = (min_change / current_value) * 100 if current_value != 0 else 0
        max_pct_change = (max_change / current_value) * 100 if current_value != 0 else 0

        min_index = results["portfolio_values"].index(min_value)
        max_index = results["portfolio_values"].index(max_value)
        min_spy_change = results["spy_changes"][min_index]
        max_spy_change = results["spy_changes"][max_index]


        # Print position-level analysis
        if "position_values" in results:
            # Find the indices for min, max, and zero values
            try:
                zero_index = next(
                    (
                        i
                        for i, change in enumerate(results["spy_changes"])
                        if abs(change) < 0.001
                    ),
                    0,
                )
                min_index = 0  # First element (most negative)
                max_index = (
                    len(results["spy_changes"]) - 1
                )  # Last element (most positive)

                # Calculate position-level changes
                position_changes = {}
                for ticker, values in results["position_values"].items():
                    if len(values) > zero_index:
                        base_value = values[zero_index]
                        if base_value == 0:
                            continue

                        # Calculate changes at min and max SPY values
                        min_spy_value = (
                            values[min_index] if min_index < len(values) else 0
                        )
                        max_spy_value = (
                            values[max_index] if max_index < len(values) else 0
                        )

                        down_change = min_spy_value - base_value
                        up_change = max_spy_value - base_value

                        # Calculate percentage changes
                        down_pct = (
                            (down_change / base_value) * 100 if base_value != 0 else 0
                        )
                        up_pct = (
                            (up_change / base_value) * 100 if base_value != 0 else 0
                        )

                        # Store the changes
                        position_changes[ticker] = {
                            "base_value": base_value,
                            "min_spy_value": min_spy_value,
                            "max_spy_value": max_spy_value,
                            "down_change": down_change,
                            "up_change": up_change,
                            "down_pct": down_pct,
                            "up_pct": up_pct,
                        }

                # Get position details for comparison
                position_details = results.get("position_details", {})

                # Find positions with largest contributions
                sorted_down = sorted(
                    position_changes.items(), key=lambda x: x[1]["down_change"]
                )
                sorted_up = sorted(
                    position_changes.items(),
                    key=lambda x: x[1]["up_change"],
                    reverse=True,
                )

                for ticker, data in sorted_down[:5]:
                    # Calculate expected change based on beta
                    beta = position_details.get(ticker, {}).get("beta", 0)
                    base_value = data["base_value"]
                    expected_change = (
                        beta * -0.1 * base_value
                    )  # Expected change at -10% SPY
                    actual_change = data["down_change"]
                    difference = actual_change - expected_change
                    (
                        (difference / abs(expected_change)) * 100
                        if expected_change != 0
                        else 0
                    )


                for ticker, data in sorted_up[:5]:
                    # Calculate expected change based on beta
                    beta = position_details.get(ticker, {}).get("beta", 0)
                    base_value = data["base_value"]
                    expected_change = (
                        beta * 0.1 * base_value
                    )  # Expected change at +10% SPY
                    actual_change = data["up_change"]
                    difference = actual_change - expected_change
                    (
                        (difference / abs(expected_change)) * 100
                        if expected_change != 0
                        else 0
                    )

            except (StopIteration, IndexError):
                pass

        # Calculate the portfolio's beta based on the simulation results
        try:
            # Get the min and max values
            min_index = 0  # First element (most negative)
            max_index = len(results["spy_changes"]) - 1  # Last element (most positive)

            min_value = results["portfolio_values"][min_index]
            max_value = results["portfolio_values"][max_index]

            min_spy_change = results["spy_changes"][min_index]
            max_spy_change = results["spy_changes"][max_index]

            min_pct_change = (min_value / current_value - 1) * 100
            max_pct_change = (max_value / current_value - 1) * 100

            # Calculate beta for up and down moves
            beta_up = max_pct_change / (
                max_spy_change * 100
            )  # How much portfolio changes per 1% SPY up move
            beta_down = min_pct_change / (
                min_spy_change * 100
            )  # How much portfolio changes per 1% SPY down move
            (beta_up + beta_down) / 2


            if abs(beta_up - beta_down) > 0.5:
                pass
        except (StopIteration, IndexError):
            pass

    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
