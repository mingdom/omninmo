#!/usr/bin/env python
"""
Debug script for the Portfolio SPY Simulator.

This script loads a portfolio from a CSV file, updates prices,
and then simulates how the portfolio value changes as SPY moves up or down,
with detailed logging to help diagnose accuracy issues.
"""

import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logger = logging.getLogger("spy_simulator_debug")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# File handler
file_handler = logging.FileHandler("spy_simulator_debug.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Set specific loggers to INFO to reduce noise
logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.INFO)

# Test logging
logger.debug("Debug logging initialized")
logger.info("Info logging initialized")

import pandas as pd

from src.folio.formatting import format_currency
from src.folio.portfolio import process_portfolio_data
from src.folio.simulator import simulate_portfolio_with_spy_changes


def debug_simulate_portfolio(
    portfolio_groups, cash_like_positions=None, pending_activity_value=0.0
):
    """Run the portfolio simulator with detailed logging for debugging."""
    logger = logging.getLogger("debug_simulator")
    logger.info("Starting detailed portfolio simulation")

    # Use a tighter range with 1% increments
    spy_changes = [i / 100 for i in range(-10, 11, 1)]  # -10% to +10% in 1% increments

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

    # Get the values at -10%, 0%, and +10%
    minus_10_index = spy_changes.index(-0.1)
    plus_10_index = spy_changes.index(0.1)

    # Calculate the total portfolio change
    total_minus_10 = results["portfolio_values"][minus_10_index]
    total_zero = results["portfolio_values"][zero_index]
    total_plus_10 = results["portfolio_values"][plus_10_index]

    logger.info(f"Portfolio value at -10% SPY: {format_currency(total_minus_10)}")
    logger.info(f"Portfolio value at 0% SPY: {format_currency(total_zero)}")
    logger.info(f"Portfolio value at +10% SPY: {format_currency(total_plus_10)}")

    down_change = total_minus_10 - total_zero
    up_change = total_plus_10 - total_zero

    logger.info(
        f"Change on -10% SPY: {format_currency(down_change)} ({down_change / total_zero * 100:.2f}%)"
    )
    logger.info(
        f"Change on +10% SPY: {format_currency(up_change)} ({up_change / total_zero * 100:.2f}%)"
    )

    # Calculate implied beta
    down_beta = -down_change / (total_zero * 0.1)
    up_beta = up_change / (total_zero * 0.1)

    logger.info(f"Implied beta on down moves: {down_beta:.2f}")
    logger.info(f"Implied beta on up moves: {up_beta:.2f}")

    # Add the analysis to the results
    results["analysis"] = {
        "down_beta": down_beta,
        "up_beta": up_beta,
        "original_values": original_values,
    }

    return results


def main():
    # Path to the portfolio CSV file
    csv_path = Path(os.getcwd()) / "private-data" / "portfolio-private.csv"

    if not csv_path.exists():
        sys.exit(1)


    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)

        # Process the portfolio data with price updates
        groups, summary, _ = process_portfolio_data(df, update_prices=True)


        # Run the simulation with detailed debugging

        # Use a tighter range with 1% increments
        spy_changes = [
            i / 100 for i in range(-10, 11, 1)
        ]  # -10% to +10% in 1% increments

        # Add detailed logging for the simulation
        logger.info("Starting portfolio simulation with detailed logging")
        logger.info(f"Using SPY changes: {[f'{change:.1%}' for change in spy_changes]}")

        # Get the original results from the simulator
        results = simulate_portfolio_with_spy_changes(
            portfolio_groups=groups,
            spy_changes=spy_changes,
            cash_like_positions=summary.cash_like_positions,
            pending_activity_value=getattr(summary, "pending_activity_value", 0.0),
        )

        # Analyze the results
        logger.info("\nAnalyzing simulation results:")

        # Find the index for 0% change
        zero_index = next(
            (i for i, change in enumerate(spy_changes) if abs(change) < 0.001), None
        )
        minus_10_index = next(
            (i for i, change in enumerate(spy_changes) if abs(change + 0.1) < 0.001),
            None,
        )
        plus_10_index = next(
            (i for i, change in enumerate(spy_changes) if abs(change - 0.1) < 0.001),
            None,
        )

        if (
            zero_index is not None
            and minus_10_index is not None
            and plus_10_index is not None
        ):
            # Calculate the total portfolio change
            total_minus_10 = results["portfolio_values"][minus_10_index]
            total_zero = results["portfolio_values"][zero_index]
            total_plus_10 = results["portfolio_values"][plus_10_index]

            logger.info(
                f"Portfolio value at -10% SPY: {format_currency(total_minus_10)}"
            )
            logger.info(f"Portfolio value at 0% SPY: {format_currency(total_zero)}")
            logger.info(
                f"Portfolio value at +10% SPY: {format_currency(total_plus_10)}"
            )

            down_change = total_minus_10 - total_zero
            up_change = total_plus_10 - total_zero

            logger.info(
                f"Change on -10% SPY: {format_currency(down_change)} ({down_change / total_zero * 100:.2f}%)"
            )
            logger.info(
                f"Change on +10% SPY: {format_currency(up_change)} ({up_change / total_zero * 100:.2f}%)"
            )

            # Calculate implied beta
            down_beta = -down_change / (total_zero * 0.1)
            up_beta = up_change / (total_zero * 0.1)

            logger.info(f"Implied beta on down moves: {down_beta:.2f}")
            logger.info(f"Implied beta on up moves: {up_beta:.2f}")

            # Calculate expected changes for each position
            logger.info("\nAnalyzing individual positions:")

            for group in groups:
                ticker = group.ticker
                beta = group.beta

                # Calculate total market value
                stock_value = (
                    group.stock_position.market_value if group.stock_position else 0
                )
                option_value = (
                    sum(op.market_value for op in group.option_positions)
                    if group.option_positions
                    else 0
                )
                total_value = stock_value + option_value

                # Skip positions with no market value
                if total_value == 0:
                    continue

                logger.info(f"\nPosition: {ticker}")
                logger.info(f"  Beta: {beta:.2f}")
                logger.info(f"  Total Value: {format_currency(total_value)}")

                # Calculate expected changes
                expected_down_change = -0.1 * beta * total_value
                expected_up_change = 0.1 * beta * total_value

                logger.info(
                    f"  Expected change at -10% SPY: {format_currency(expected_down_change)}"
                )
                logger.info(
                    f"  Expected change at +10% SPY: {format_currency(expected_up_change)}"
                )

                # Log stock position details
                if group.stock_position:
                    logger.info(
                        f"  Stock: {group.stock_position.quantity} shares @ {group.stock_position.price:.2f}"
                    )
                    logger.info(
                        f"    Value: {format_currency(group.stock_position.market_value)}"
                    )
                    logger.info(
                        f"    Expected change at -10% SPY: {format_currency(-0.1 * beta * group.stock_position.market_value)}"
                    )
                    logger.info(
                        f"    Expected change at +10% SPY: {format_currency(0.1 * beta * group.stock_position.market_value)}"
                    )

                # Log option position details
                if group.option_positions:
                    logger.info(f"  Options: {len(group.option_positions)}")
                    for i, option in enumerate(group.option_positions):
                        logger.info(
                            f"    Option {i + 1}: {option.quantity} {option.option_type} @ {option.strike:.2f}, expires {option.expiry}"
                        )
                        logger.info(
                            f"      Price: {option.price:.4f}, Delta: {option.delta:.4f}"
                        )
                        logger.info(
                            f"      Value: {format_currency(option.market_value)}"
                        )

                        # Calculate expected option behavior
                        if option.option_type == "CALL":
                            # For calls, value increases when underlying increases
                            expected_direction = (
                                "increases" if option.delta > 0 else "decreases"
                            )
                        else:  # PUT
                            # For puts, value decreases when underlying increases
                            expected_direction = (
                                "decreases" if option.delta > 0 else "increases"
                            )

                        logger.info(
                            f"      Expected behavior: Value {expected_direction} when SPY increases"
                        )

                        # Calculate expected change based on delta
                        underlying_price = (
                            group.stock_position.price if group.stock_position else 0
                        )
                        if underlying_price > 0:
                            expected_price_change_down = -0.1 * beta * underlying_price
                            expected_price_change_up = 0.1 * beta * underlying_price

                            expected_option_change_down = (
                                option.delta
                                * expected_price_change_down
                                * option.quantity
                            )
                            expected_option_change_up = (
                                option.delta
                                * expected_price_change_up
                                * option.quantity
                            )

                            logger.info(
                                f"      Expected change at -10% SPY: {format_currency(expected_option_change_down)}"
                            )
                            logger.info(
                                f"      Expected change at +10% SPY: {format_currency(expected_option_change_up)}"
                            )
                        else:
                            logger.warning(
                                "      Cannot calculate expected change - no underlying price available"
                            )

        # Print the results

        # Get the current value (at 0% SPY change)
        current_value = results["current_value"]

        # Print each data point
        for i, _spy_change in enumerate(results["spy_changes"]):
            portfolio_value = results["portfolio_values"][i]
            value_change = portfolio_value - current_value
            (
                (value_change / current_value) * 100 if current_value != 0 else 0
            )



        # Print summary analysis
        min_value = min(results["portfolio_values"])
        max_value = max(results["portfolio_values"])
        min_change = min_value - current_value
        max_change = max_value - current_value
        (min_change / current_value) * 100 if current_value != 0 else 0
        (max_change / current_value) * 100 if current_value != 0 else 0

        min_index = results["portfolio_values"].index(min_value)
        max_index = results["portfolio_values"].index(max_value)
        results["spy_changes"][min_index]
        results["spy_changes"][max_index]


        # Calculate the portfolio's beta based on the simulation results
        try:
            plus_10_index = next(
                i
                for i, change in enumerate(results["spy_changes"])
                if abs(change - 0.1) < 0.001
            )
            minus_10_index = next(
                i
                for i, change in enumerate(results["spy_changes"])
                if abs(change + 0.1) < 0.001
            )

            plus_10_value = results["portfolio_values"][plus_10_index]
            minus_10_value = results["portfolio_values"][minus_10_index]

            plus_10_pct_change = (plus_10_value / current_value - 1) * 100
            minus_10_pct_change = (minus_10_value / current_value - 1) * 100

            # Average the two beta calculations
            beta_up = (
                plus_10_pct_change / 10
            )  # How much portfolio changes per 1% SPY up move
            beta_down = (
                minus_10_pct_change / -10
            )  # How much portfolio changes per 1% SPY down move
            (beta_up + beta_down) / 2


            if abs(beta_up - beta_down) > 0.5:
                pass

            # Analyze the portfolio in more detail

            # Calculate the expected portfolio value change at +10% SPY
            total_expected_change = 0
            for group in groups:
                stock_value = (
                    group.stock_position.market_value if group.stock_position else 0
                )
                option_value = (
                    sum(op.market_value for op in group.option_positions)
                    if group.option_positions
                    else 0
                )
                total_market_value = stock_value + option_value
                expected_change = group.beta * 0.1 * total_market_value
                total_expected_change += expected_change

            expected_value_at_plus_10 = current_value + total_expected_change
            actual_value_at_plus_10 = plus_10_value
            actual_value_at_plus_10 - expected_value_at_plus_10


            # Find positions with unexpected behavior

            # Sort groups by absolute discrepancy
            position_discrepancies = []

            for group in groups:
                ticker = group.ticker
                beta = group.beta

                # Calculate total market value
                stock_value = (
                    group.stock_position.market_value if group.stock_position else 0
                )
                option_value = (
                    sum(op.market_value for op in group.option_positions)
                    if group.option_positions
                    else 0
                )
                original_value = stock_value + option_value

                # Skip positions with no market value
                if original_value == 0:
                    continue

                # Calculate expected change based on beta
                expected_change = beta * 0.1 * original_value

                # We don't have actual changes per position from the simulation
                # This is a limitation of our current approach
                # We'll note this in the analysis

                position_discrepancies.append(
                    {
                        "ticker": ticker,
                        "beta": beta,
                        "original_value": original_value,
                        "expected_change": expected_change,
                    }
                )

            # Sort by absolute expected change
            position_discrepancies.sort(
                key=lambda x: abs(x["expected_change"]), reverse=True
            )

            # Print the top 10 positions by expected change
            for _pos in position_discrepancies[:10]:
                pass


        except (StopIteration, IndexError):
            pass

    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
