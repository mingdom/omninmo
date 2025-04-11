"""
QuantLib implementation of option calculations.
Direct replacement for option_utils.py
Uses American-style options for US stocks.
"""

import datetime
import warnings

# Import QuantLib and suppress SWIG-related DeprecationWarnings
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="builtin type SwigPyPacked has no __module__ attribute",
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="builtin type SwigPyObject has no __module__ attribute",
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="builtin type swigvarlink has no __module__ attribute",
    )
    import QuantLib as ql  # noqa: N813

from src.folio.data_model import OptionPosition


def calculate_black_scholes_delta(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float | None = None,
) -> float:
    """
    Calculate option delta using QuantLib.
    Direct replacement for option_utils.calculate_black_scholes_delta.
    Uses American-style options.
    """
    # Use provided volatility or default
    if volatility is None:
        volatility = 0.3  # Default volatility

    # Set up dates
    today = ql.Date.todaysDate()
    expiry_date = ql.Date(
        option_position.expiry.day,
        option_position.expiry.month,
        option_position.expiry.year,
    )

    # Set up the option
    option_type = (
        ql.Option.Call if option_position.option_type == "CALL" else ql.Option.Put
    )
    strike = option_position.strike

    # Set up the pricing environment
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, 0.0, ql.Actual365Fixed())
    )
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    vol_handle = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, volatility, ql.Actual365Fixed())
    )

    # Create the Black-Scholes process
    process = ql.BlackScholesMertonProcess(
        spot_handle, dividend_handle, rate_handle, vol_handle
    )

    # Create the option with American exercise
    exercise = ql.AmericanExercise(today, expiry_date)
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    option = ql.VanillaOption(payoff, exercise)

    # Set up the pricing engine - use binomial tree for American options
    time_steps = 100  # Number of time steps in the tree
    engine = ql.BinomialVanillaEngine(process, "crr", time_steps)
    option.setPricingEngine(engine)

    # Calculate delta - no exception handling as requested
    delta = option.delta()
    return delta


def calculate_bs_price(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float | None = None,
) -> float:
    """
    Calculate option price using QuantLib.
    Direct replacement for option_utils.calculate_bs_price.
    Uses American-style options.
    """
    # Use provided volatility or default
    if volatility is None:
        volatility = 0.3  # Default volatility

    # Set up dates
    today = ql.Date.todaysDate()
    expiry_date = ql.Date(
        option_position.expiry.day,
        option_position.expiry.month,
        option_position.expiry.year,
    )

    # Set up the option
    option_type = (
        ql.Option.Call if option_position.option_type == "CALL" else ql.Option.Put
    )
    strike = option_position.strike

    # Set up the pricing environment
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, 0.0, ql.Actual365Fixed())
    )
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
    vol_handle = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, volatility, ql.Actual365Fixed())
    )

    # Create the Black-Scholes process
    process = ql.BlackScholesMertonProcess(
        spot_handle, dividend_handle, rate_handle, vol_handle
    )

    # Create the option with American exercise
    exercise = ql.AmericanExercise(today, expiry_date)
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    option = ql.VanillaOption(payoff, exercise)

    # Set up the pricing engine - use binomial tree for American options
    time_steps = 100  # Number of time steps in the tree
    engine = ql.BinomialVanillaEngine(process, "crr", time_steps)
    option.setPricingEngine(engine)

    # Calculate price - no exception handling as requested
    price = option.NPV()
    return price


def calculate_implied_volatility(
    option_position: OptionPosition,
    underlying_price: float,
    option_price: float | None = None,
    risk_free_rate: float = 0.05,
) -> float:
    """
    Calculate implied volatility using QuantLib.
    Direct replacement for option_utils.calculate_implied_volatility.
    Uses American-style options.
    """
    # Use provided option price or the option's current_price
    if option_price is None:
        option_price = option_position.current_price

    # Set up dates
    today = ql.Date.todaysDate()
    expiry_date = ql.Date(
        option_position.expiry.day,
        option_position.expiry.month,
        option_position.expiry.year,
    )

    # Set up the option
    option_type = (
        ql.Option.Call if option_position.option_type == "CALL" else ql.Option.Put
    )
    strike = option_position.strike

    # Create the option with American exercise
    exercise = ql.AmericanExercise(today, expiry_date)
    payoff = ql.PlainVanillaPayoff(option_type, strike)
    option = ql.VanillaOption(payoff, exercise)

    # Set up for implied volatility calculation
    spot = ql.SimpleQuote(underlying_price)
    vol = ql.SimpleQuote(0.3)  # Initial guess
    rate = ql.SimpleQuote(risk_free_rate)
    dividend = ql.SimpleQuote(0.0)

    spot_handle = ql.QuoteHandle(spot)
    vol_handle = ql.QuoteHandle(vol)
    rate_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, ql.QuoteHandle(rate), ql.Actual365Fixed())
    )
    dividend_handle = ql.YieldTermStructureHandle(
        ql.FlatForward(today, ql.QuoteHandle(dividend), ql.Actual365Fixed())
    )

    # Create process and pricing engine
    process = ql.BlackScholesMertonProcess(
        spot_handle,
        dividend_handle,
        rate_handle,
        ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                today,
                ql.UnitedStates(ql.UnitedStates.NYSE),
                vol_handle,
                ql.Actual365Fixed(),
            )
        ),
    )

    # For American options, we need to use a binomial tree for implied vol
    time_steps = 100
    engine = ql.BinomialVanillaEngine(process, "crr", time_steps)
    option.setPricingEngine(engine)

    # Calculate implied volatility using bisection method - no exception handling as requested
    min_vol = 0.001
    max_vol = 5.0
    tolerance = 0.0001
    max_iterations = 100

    for _i in range(max_iterations):
        mid_vol = (min_vol + max_vol) / 2
        vol.setValue(mid_vol)

        price = option.NPV()
        price_diff = price - option_price

        if abs(price_diff) < tolerance:
            return mid_vol

        if price_diff > 0:
            max_vol = mid_vol
        else:
            min_vol = mid_vol

    # If we reach here, we've hit max iterations
    return (min_vol + max_vol) / 2


def parse_option_description(description: str) -> dict:
    """
    Parse option description string.
    Direct replacement for option_utils.parse_option_description.

    This function doesn't use QuantLib, but is included for completeness.
    """
    parts = description.strip().split()
    if len(parts) != 6:
        raise ValueError(f"Invalid option description format: {description}")

    underlying = parts[0]
    option_type = parts[5]
    strike_str = parts[4]

    if not strike_str.startswith("$"):
        raise ValueError(f"Invalid strike format: {strike_str}")

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
    if not month:
        raise ValueError(f"Invalid month: {month_str}")

    day = int(day_str)
    year = int(year_str)

    expiry = datetime.datetime(year, month, day)

    return {
        "underlying": underlying,
        "expiry": expiry,
        "strike": strike,
        "option_type": option_type,
    }
