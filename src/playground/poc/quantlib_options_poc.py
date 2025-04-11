#!/usr/bin/env python
"""
QuantLib Options POC

This script demonstrates using QuantLib for option calculations as an alternative
to our custom Black-Scholes implementation. It loads real portfolio data from
.tmp/real-portfolio.csv, calculates option metrics using both implementations,
and compares the results.

Requirements:
- QuantLib: pip install QuantLib
- matplotlib: pip install matplotlib
- pandas: pip install pandas
- yfinance: pip install yfinance

Usage:
python src/playground/poc/quantlib_options_poc.py
"""

import datetime
import os
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import QuantLib as ql  # noqa: N813

import yfinance as yf

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import our current implementation
from src.folio.option_utils import (
    OptionPosition,
    calculate_black_scholes_delta,
    calculate_bs_price,
)


def load_portfolio_data(file_path: str) -> pd.DataFrame:
    """Load portfolio data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception:
        return pd.DataFrame()


def extract_option_data(portfolio_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Extract option data from portfolio DataFrame."""
    options_data = []

    # Filter for options
    options_df = portfolio_df[
        portfolio_df["Description"].apply(
            lambda x: isinstance(x, str) and ("CALL" in x or "PUT" in x)
        )
    ]

    if options_df.empty:
        return options_data

    # Process each option
    for _idx, row in options_df.iterrows():
        try:
            # Parse option description
            description = row["Description"]
            quantity = row["Quantity"]
            price_str = row.get("Last Price", "0.0")
            # Remove $ and convert to float
            price = (
                float(price_str.replace("$", ""))
                if isinstance(price_str, str)
                else float(price_str)
            )

            # Skip if description is not a string
            if not isinstance(description, str):
                continue

            # Parse option details
            parts = description.strip().split()
            if len(parts) != 6:
                continue

            underlying = parts[0]
            option_type = parts[5]
            strike_str = parts[4]

            if not strike_str.startswith("$"):
                continue

            strike = float(strike_str[1:])

            # Parse expiry
            month_map = {
                "JAN": 1,
                "FEB": 2,
                "MAR": 3,
                "APR": 4,
                "MAY": 5,
                "JUN": 6,
                "JUL": 7,
                "AUG": 8,
                "SEP": 9,
                "OCT": 10,
                "NOV": 11,
                "DEC": 12,
            }

            month_str = parts[1]
            day_str = parts[2]
            year_str = parts[3]

            month = month_map.get(month_str.upper())
            day = int(day_str)
            year = int(year_str)

            if not month or not day or not year:
                continue

            expiry = datetime.datetime(year, month, day)
            expiry_str = expiry.strftime("%Y-%m-%d")

            # Calculate days to expiry
            days_to_expiry = (expiry.date() - datetime.datetime.now().date()).days

            # Add to options data
            option_data = {
                "underlying": underlying,
                "expiry": expiry,
                "expiry_str": expiry_str,
                "days_to_expiry": days_to_expiry,
                "strike": strike,
                "option_type": option_type,
                "quantity": quantity,
                "price": price,
                "description": description,
            }

            options_data.append(option_data)

            # Log the option details

        except Exception:
            continue

    return options_data


def fetch_current_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current prices for a list of tickers using yfinance."""
    prices = {}

    # Try to fetch real prices first
    try:
        # Download data for all tickers at once
        data = yf.download(tickers, period="1d", progress=False)

        # Process the data based on whether we have one ticker or multiple
        if len(tickers) == 1:
            # Single ticker case
            if not data.empty and "Close" in data and len(data["Close"]) > 0:
                ticker = tickers[0]
                prices[ticker] = data["Close"].iloc[-1]
            else:
                prices[tickers[0]] = 100.0
        # Multiple tickers case
        elif not data.empty and "Close" in data:
            for ticker in tickers:
                try:
                    # Check if we have data for this ticker
                    if ticker in data["Close"].columns:
                        close_price = data["Close"][ticker].iloc[-1]
                        if not pd.isna(close_price):
                            prices[ticker] = close_price
                        else:
                            raise ValueError("NaN price value")
                    else:
                        # Try individual download as fallback
                        ticker_data = yf.download(ticker, period="1d", progress=False)
                        if not ticker_data.empty and len(ticker_data["Close"]) > 0:
                            prices[ticker] = ticker_data["Close"].iloc[-1]
                        else:
                            raise ValueError("No data available")
                except Exception:
                    prices[ticker] = 100.0
    except Exception:
        # Try individual downloads as fallback
        for ticker in tickers:
            try:
                ticker_data = yf.download(ticker, period="1d", progress=False)
                if not ticker_data.empty and len(ticker_data["Close"]) > 0:
                    prices[ticker] = ticker_data["Close"].iloc[-1]
                else:
                    raise ValueError("No data available")
            except Exception:
                prices[ticker] = 100.0

    # Fill in any missing tickers with default prices
    for ticker in tickers:
        if ticker not in prices:
            prices[ticker] = 100.0

    return prices


def calculate_quantlib_delta(
    option_type: str,
    strike: float,
    expiry_date: datetime.datetime,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float = 0.30,
    dividend_yield: float = 0.0,
) -> float:
    """Calculate option delta using QuantLib."""
    # Convert option_type to QuantLib format
    ql_option_type = ql.Option.Call if option_type.upper() == "CALL" else ql.Option.Put

    # Convert expiry_date to QuantLib date
    ql_expiry_date = ql.Date(expiry_date.day, expiry_date.month, expiry_date.year)

    # Set evaluation date to today
    today = ql.Date().todaysDate()
    ql.Settings.instance().evaluationDate = today

    # Create the option
    payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
    exercise = ql.EuropeanExercise(ql_expiry_date)
    option = ql.VanillaOption(payoff, exercise)

    # Set up the Black-Scholes process
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, dividend_yield, ql.Actual365Fixed())
    )
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    vol_handle = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, volatility, ql.Actual365Fixed())
    )

    process = ql.BlackScholesMertonProcess(
        spot_handle, dividend_handle, rate_handle, vol_handle
    )

    # Set up the pricing engine
    engine = ql.AnalyticEuropeanEngine(process)
    option.setPricingEngine(engine)

    # Calculate delta
    try:
        delta = option.delta()
        return delta
    except Exception:
        return 0.0


def calculate_quantlib_price(
    option_type: str,
    strike: float,
    expiry_date: datetime.datetime,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float = 0.30,
    dividend_yield: float = 0.0,
) -> float:
    """Calculate option price using QuantLib."""
    # Convert option_type to QuantLib format
    ql_option_type = ql.Option.Call if option_type.upper() == "CALL" else ql.Option.Put

    # Convert expiry_date to QuantLib date
    ql_expiry_date = ql.Date(expiry_date.day, expiry_date.month, expiry_date.year)

    # Set evaluation date to today
    today = ql.Date().todaysDate()
    ql.Settings.instance().evaluationDate = today

    # Create the option
    payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
    exercise = ql.EuropeanExercise(ql_expiry_date)
    option = ql.VanillaOption(payoff, exercise)

    # Set up the Black-Scholes process
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, dividend_yield, ql.Actual365Fixed())
    )
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    vol_handle = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, volatility, ql.Actual365Fixed())
    )

    process = ql.BlackScholesMertonProcess(
        spot_handle, dividend_handle, rate_handle, vol_handle
    )

    # Set up the pricing engine
    engine = ql.AnalyticEuropeanEngine(process)
    option.setPricingEngine(engine)

    # Calculate price
    try:
        price = option.NPV()
        return price
    except Exception:
        return 0.0


def calculate_quantlib_greeks(
    option_type: str,
    strike: float,
    expiry_date: datetime.datetime,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float = 0.30,
    dividend_yield: float = 0.0,
) -> dict[str, float]:
    """Calculate all option Greeks using QuantLib."""
    # Convert option_type to QuantLib format
    ql_option_type = ql.Option.Call if option_type.upper() == "CALL" else ql.Option.Put

    # Convert expiry_date to QuantLib date
    ql_expiry_date = ql.Date(expiry_date.day, expiry_date.month, expiry_date.year)

    # Set evaluation date to today
    today = ql.Date().todaysDate()
    ql.Settings.instance().evaluationDate = today

    # Create the option
    payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
    exercise = ql.EuropeanExercise(ql_expiry_date)
    option = ql.VanillaOption(payoff, exercise)

    # Set up the Black-Scholes process
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, dividend_yield, ql.Actual365Fixed())
    )
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    vol_handle = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, volatility, ql.Actual365Fixed())
    )

    process = ql.BlackScholesMertonProcess(
        spot_handle, dividend_handle, rate_handle, vol_handle
    )

    # Set up the pricing engine
    engine = ql.AnalyticEuropeanEngine(process)
    option.setPricingEngine(engine)

    # Calculate Greeks
    try:
        price = option.NPV()
        delta = option.delta()
        gamma = option.gamma()
        theta = option.theta() / 365.0  # Convert from daily to annual
        vega = option.vega() / 100.0  # Convert from 1% to 0.01 (decimal)
        rho = option.rho() / 100.0  # Convert from 1% to 0.01 (decimal)

        return {
            "price": price,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
        }
    except Exception:
        return {
            "price": 0.0,
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
        }


def compare_implementations(
    option_data: dict[str, Any],
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float = 0.30,
) -> dict[str, Any]:
    """Compare option calculations between QuantLib and our current implementation."""
    # Log the comparison details

    # Create OptionPosition for our current implementation
    option_position = OptionPosition(
        underlying=option_data["underlying"],
        expiry=option_data["expiry"],
        strike=option_data["strike"],
        option_type=option_data["option_type"],
        quantity=int(option_data["quantity"]),
        current_price=option_data["price"],
        description=option_data["description"],
    )

    # Calculate using our current implementation
    current_delta = calculate_black_scholes_delta(
        option_position,
        underlying_price,
        risk_free_rate,
        volatility,
    )
    current_price = calculate_bs_price(
        option_position,
        underlying_price,
        risk_free_rate,
        volatility,
    )

    # Calculate using QuantLib
    ql_delta = calculate_quantlib_delta(
        option_data["option_type"],
        option_data["strike"],
        option_data["expiry"],
        underlying_price,
        risk_free_rate,
        volatility,
    )
    ql_price = calculate_quantlib_price(
        option_data["option_type"],
        option_data["strike"],
        option_data["expiry"],
        underlying_price,
        risk_free_rate,
        volatility,
    )

    # Calculate additional Greeks with QuantLib
    ql_greeks = calculate_quantlib_greeks(
        option_data["option_type"],
        option_data["strike"],
        option_data["expiry"],
        underlying_price,
        risk_free_rate,
        volatility,
    )

    # Calculate notional value and exposures
    notional_value = option_data["strike"] * 100 * abs(option_data["quantity"])

    current_delta_exposure = current_delta * notional_value
    if option_data["quantity"] < 0:
        current_delta_exposure = -current_delta_exposure

    ql_delta_exposure = ql_delta * notional_value
    if option_data["quantity"] < 0:
        ql_delta_exposure = -ql_delta_exposure

    # Calculate differences
    price_diff = ql_price - current_price
    price_diff_pct = (
        (ql_price - current_price) / current_price * 100
        if current_price != 0
        else float("inf")
    )

    delta_diff = ql_delta - current_delta
    delta_diff_pct = (
        (ql_delta - current_delta) / current_delta * 100
        if current_delta != 0
        else float("inf")
    )

    exposure_diff = ql_delta_exposure - current_delta_exposure
    exposure_diff_pct = (
        (ql_delta_exposure - current_delta_exposure) / current_delta_exposure * 100
        if current_delta_exposure != 0
        else float("inf")
    )

    # Log the calculation results

    # Flag significant differences
    if abs(delta_diff_pct) > 10 and not np.isinf(delta_diff_pct):
        pass
    if abs(price_diff_pct) > 10 and not np.isinf(price_diff_pct):
        pass

    # Compare results
    return {
        "option_details": {
            "underlying": option_data["underlying"],
            "strike": option_data["strike"],
            "expiry": option_data["expiry_str"],
            "option_type": option_data["option_type"],
            "quantity": option_data["quantity"],
            "days_to_expiry": option_data["days_to_expiry"],
        },
        "current_implementation": {
            "price": current_price,
            "delta": current_delta,
            "delta_exposure": current_delta_exposure,
        },
        "quantlib_implementation": {
            "price": ql_price,
            "delta": ql_delta,
            "delta_exposure": ql_delta_exposure,
            "gamma": ql_greeks["gamma"],
            "theta": ql_greeks["theta"],
            "vega": ql_greeks["vega"],
            "rho": ql_greeks["rho"],
        },
        "differences": {
            "price_diff": price_diff,
            "price_diff_pct": price_diff_pct,
            "delta_diff": delta_diff,
            "delta_diff_pct": delta_diff_pct,
            "exposure_diff": exposure_diff,
            "exposure_diff_pct": exposure_diff_pct,
        },
    }


def plot_comparison_results(comparison_results: list[dict[str, Any]]) -> None:
    """Plot comparison results between QuantLib and our current implementation."""
    if not comparison_results:
        return

    # Extract data for plotting
    deltas_current = [r["current_implementation"]["delta"] for r in comparison_results]
    deltas_ql = [r["quantlib_implementation"]["delta"] for r in comparison_results]
    delta_diffs_pct = [r["differences"]["delta_diff_pct"] for r in comparison_results]

    # Filter out infinite values
    delta_diffs_pct_filtered = [d for d in delta_diffs_pct if not np.isinf(d)]

    # Create figure with subplots
    fig, axs = plt.subplots(1, 2, figsize=(15, 6))

    # Plot scatter comparison
    axs[0].scatter(deltas_current, deltas_ql, alpha=0.7)

    # Add diagonal line
    min_val = min(*deltas_current, *deltas_ql)
    max_val = max(*deltas_current, *deltas_ql)
    axs[0].plot([min_val, max_val], [min_val, max_val], "k--", alpha=0.5)

    axs[0].set_title("Delta Comparison")
    axs[0].set_xlabel("Current Implementation Delta")
    axs[0].set_ylabel("QuantLib Delta")
    axs[0].grid(True)

    # Plot difference histogram
    axs[1].hist(delta_diffs_pct_filtered, bins=20, alpha=0.7)
    axs[1].set_title("Delta Difference (%)")
    axs[1].set_xlabel("Difference (%)")
    axs[1].set_ylabel("Count")
    axs[1].grid(True)

    # Add vertical line at 0
    axs[1].axvline(x=0, color="r", linestyle="--", alpha=0.5)

    # Add summary statistics
    mean_diff = np.mean(delta_diffs_pct_filtered)
    median_diff = np.median(delta_diffs_pct_filtered)
    std_diff = np.std(delta_diffs_pct_filtered)

    stats_text = (
        f"Mean: {mean_diff:.2f}%\nMedian: {median_diff:.2f}%\nStd Dev: {std_diff:.2f}%"
    )

    axs[1].text(
        0.95,
        0.95,
        stats_text,
        transform=axs[1].transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()

    # Save the figure
    os.makedirs(".tmp", exist_ok=True)
    plt.savefig(".tmp/quantlib_delta_comparison.png")

    # Plot Greeks distribution
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    # Extract Greeks data
    gammas = [r["quantlib_implementation"]["gamma"] for r in comparison_results]
    thetas = [r["quantlib_implementation"]["theta"] for r in comparison_results]
    vegas = [r["quantlib_implementation"]["vega"] for r in comparison_results]
    [r["quantlib_implementation"]["rho"] for r in comparison_results]

    # Plot Greeks distributions
    axs[0, 0].hist(deltas_ql, bins=20, alpha=0.7)
    axs[0, 0].set_title("Delta Distribution")
    axs[0, 0].set_xlabel("Delta")
    axs[0, 0].set_ylabel("Count")
    axs[0, 0].grid(True)

    axs[0, 1].hist(gammas, bins=20, alpha=0.7)
    axs[0, 1].set_title("Gamma Distribution")
    axs[0, 1].set_xlabel("Gamma")
    axs[0, 1].set_ylabel("Count")
    axs[0, 1].grid(True)

    axs[1, 0].hist(thetas, bins=20, alpha=0.7)
    axs[1, 0].set_title("Theta Distribution")
    axs[1, 0].set_xlabel("Theta")
    axs[1, 0].set_ylabel("Count")
    axs[1, 0].grid(True)

    axs[1, 1].hist(vegas, bins=20, alpha=0.7)
    axs[1, 1].set_title("Vega Distribution")
    axs[1, 1].set_xlabel("Vega")
    axs[1, 1].set_ylabel("Count")
    axs[1, 1].grid(True)

    plt.tight_layout()

    # Save the figure
    plt.savefig(".tmp/quantlib_greeks_distribution.png")


def plot_option_metrics(
    option_data: dict[str, Any],
    underlying_price: float,
    price_range: tuple[float, float] | None = None,
    num_points: int = 50,
) -> None:
    """Plot option metrics across a range of underlying prices."""
    # Calculate price range if not provided
    if price_range is None:
        price_range = (underlying_price * 0.8, underlying_price * 1.2)

    # Generate price points
    min_price, max_price = price_range
    prices = np.linspace(min_price, max_price, num_points)

    # Calculate metrics at each price point
    deltas = []
    gammas = []
    thetas = []
    vegas = []
    option_prices = []

    for price in prices:
        greeks = calculate_quantlib_greeks(
            option_data["option_type"],
            option_data["strike"],
            option_data["expiry"],
            price,
        )
        deltas.append(greeks["delta"])
        gammas.append(greeks["gamma"])
        thetas.append(greeks["theta"])
        vegas.append(greeks["vega"])
        option_prices.append(greeks["price"])

    # Create figure with subplots
    fig, axs = plt.subplots(3, 2, figsize=(12, 10))
    fig.suptitle(
        f"{option_data['underlying']} {option_data['option_type']} {option_data['strike']} {option_data['expiry_str']}",
        fontsize=16,
    )

    # Plot option price
    axs[0, 0].plot(prices, option_prices, "b-")
    axs[0, 0].set_title("Option Price")
    axs[0, 0].set_xlabel("Underlying Price")
    axs[0, 0].set_ylabel("Option Price")
    axs[0, 0].grid(True)

    # Plot delta
    axs[0, 1].plot(prices, deltas, "r-")
    axs[0, 1].set_title("Delta")
    axs[0, 1].set_xlabel("Underlying Price")
    axs[0, 1].set_ylabel("Delta")
    axs[0, 1].grid(True)

    # Plot gamma
    axs[1, 0].plot(prices, gammas, "g-")
    axs[1, 0].set_title("Gamma")
    axs[1, 0].set_xlabel("Underlying Price")
    axs[1, 0].set_ylabel("Gamma")
    axs[1, 0].grid(True)

    # Plot theta
    axs[1, 1].plot(prices, thetas, "m-")
    axs[1, 1].set_title("Theta")
    axs[1, 1].set_xlabel("Underlying Price")
    axs[1, 1].set_ylabel("Theta")
    axs[1, 1].grid(True)

    # Plot vega
    axs[2, 0].plot(prices, vegas, "c-")
    axs[2, 0].set_title("Vega")
    axs[2, 0].set_xlabel("Underlying Price")
    axs[2, 0].set_ylabel("Vega")
    axs[2, 0].grid(True)

    # Add strike price line to all plots
    strike = float(option_data["strike"])
    for i in range(3):
        for j in range(2):
            if i < 2 or j == 0:  # Skip the empty subplot
                axs[i, j].axvline(x=strike, color="k", linestyle="--", alpha=0.5)

    # Add current price marker if available
    if option_data["price"] > 0:
        current_price = option_data["price"]
        axs[0, 0].scatter(
            [underlying_price], [current_price], color="r", s=100, zorder=5
        )
        axs[0, 0].annotate(
            f"Current: ${current_price:.2f}",
            (underlying_price, current_price),
            xytext=(10, 10),
            textcoords="offset points",
            color="r",
        )

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Remove the unused subplot
    fig.delaxes(axs[2, 1])

    # Save the figure
    plt.savefig(".tmp/quantlib_option_metrics.png")


def main():
    """Main function to run the QuantLib options POC."""

    # Load portfolio data
    portfolio_file = ".tmp/real-portfolio.csv"
    if not os.path.exists(portfolio_file):
        return

    portfolio_df = load_portfolio_data(portfolio_file)
    if portfolio_df.empty:
        return

    # Extract option data
    options_data = extract_option_data(portfolio_df)
    if not options_data:
        return

    # Extract unique underlying tickers
    underlyings = list(set(opt["underlying"] for opt in options_data))

    # Fetch current prices
    prices = fetch_current_prices(underlyings)
    if not prices:
        return

    # Compare implementations
    comparison_results = []
    for option_data in options_data:
        underlying = option_data["underlying"]
        if underlying not in prices:
            continue

        underlying_price = prices[underlying]
        comparison = compare_implementations(option_data, underlying_price)
        comparison_results.append(comparison)

    if not comparison_results:
        return

    # Display summary statistics

    # Analyze delta differences
    delta_diffs = [r["differences"]["delta_diff_pct"] for r in comparison_results]
    delta_diffs_filtered = [d for d in delta_diffs if not np.isinf(d)]

    if delta_diffs_filtered:
        # Count options with large differences
        sum(1 for d in delta_diffs_filtered if abs(d) > 10)
    else:
        pass

    # Analyze price differences
    price_diffs = [r["differences"]["price_diff_pct"] for r in comparison_results]
    price_diffs_filtered = [d for d in price_diffs if not np.isinf(d)]

    if price_diffs_filtered:
        # Count options with large differences
        sum(1 for d in price_diffs_filtered if abs(d) > 10)
    else:
        pass

    # Analyze by option type
    [r for r in comparison_results if r["option_details"]["option_type"] == "CALL"]
    [r for r in comparison_results if r["option_details"]["option_type"] == "PUT"]

    # Analyze by days to expiry
    [r for r in comparison_results if r["option_details"]["days_to_expiry"] <= 30]
    [r for r in comparison_results if 30 < r["option_details"]["days_to_expiry"] <= 90]
    [r for r in comparison_results if r["option_details"]["days_to_expiry"] > 90]

    # Plot comparison results
    plot_comparison_results(comparison_results)

    # Plot detailed metrics for a sample option
    if comparison_results:
        sample_option = comparison_results[0]["option_details"]
        sample_option_data = next(
            (
                opt
                for opt in options_data
                if opt["underlying"] == sample_option["underlying"]
            ),
            None,
        )

        if sample_option_data:
            underlying_price = prices[sample_option_data["underlying"]]
            plot_option_metrics(sample_option_data, underlying_price)


if __name__ == "__main__":
    main()
