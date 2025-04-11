"""
Options calculation module.
Uses QuantLib for option pricing and Greeks calculations.
Uses American-style options for US stocks.
"""

import datetime
import logging
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

from dataclasses import dataclass

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class OptionContract:
    """Represents a single option contract, storing its key characteristics and providing calculated properties.

    Attributes:
        underlying (str): The ticker symbol of the underlying asset (e.g., "AAPL").
        expiry (datetime): The expiration date of the option.
        strike (float): The strike price of the option.
        option_type (str): The type of the option, either 'CALL' or 'PUT'.
        quantity (int): The number of contracts held. Positive for long positions, negative for short positions.
        current_price (float): The current market price per contract of the option.
        description (str): The original description string from the data source (e.g., "AAPL APR 17 2025 $220 CALL").

    Properties:
        notional_value (float): The absolute value controlled by the option contract(s), calculated as
                              `strike * 100 * abs(quantity)`. Always positive regardless of position direction.
        signed_notional_value (float): The signed value controlled by the option contract(s), calculated as
                                    `strike * 100 * quantity`. Positive for long positions, negative for short.
        market_value (float): The current market value of the option position(s), calculated as
                           `current_price * 100 * quantity`. Positive for long positions, negative for short.

    Note:
        A position is considered short if quantity < 0, and long if quantity > 0.
    """

    underlying: str
    expiry: datetime
    strike: float
    option_type: str  # 'CALL' or 'PUT'
    quantity: int
    current_price: float
    description: str

    @property
    def notional_value(self) -> float:
        """Calculate notional value (strike * 100 * abs(quantity)).

        Note: This returns the absolute notional value (always positive) regardless of
        whether the position is long or short. This is used for calculating the size
        of the position, not its directional exposure.
        """
        # Contract size is typically 100 shares per option contract
        return self.strike * 100 * abs(self.quantity)

    @property
    def signed_notional_value(self) -> float:
        """Calculate signed notional value (strike * 100 * quantity).

        Note: This returns a signed notional value that is positive for long positions
        and negative for short positions. This is useful for calculating directional
        exposure directly.
        """
        # Contract size is typically 100 shares per option contract
        return self.strike * 100 * self.quantity

    @property
    def market_value(self) -> float:
        """Calculate market value (current_price * 100 * quantity)."""
        # Market value reflects the direction (long/short) via quantity sign
        return self.current_price * 100 * self.quantity


def calculate_black_scholes_delta(
    option_position: OptionContract,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float | None = None,
) -> float:
    """
    Calculate option delta using QuantLib.
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
    option_position: OptionContract,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float | None = None,
) -> float:
    """
    Calculate option price using QuantLib.
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
    option_position: OptionContract,
    underlying_price: float,
    option_price: float | None = None,
    risk_free_rate: float = 0.05,
) -> float:
    """
    Calculate implied volatility using QuantLib.
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


def parse_option_description(
    description: str, quantity: int = 1, current_price: float = 0.0
) -> dict | OptionContract:
    """
    Parse option description string.

    This function doesn't use QuantLib, but is included for completeness.

    Args:
        description: The option description string to parse
        quantity: The number of contracts (positive for long, negative for short)
        current_price: The current market price per contract

    Returns:
        If called with just description, returns a dictionary with parsed components.
        If called with all parameters, returns an OptionPosition object.
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

    # If only description is provided, return a dictionary
    if quantity == 1 and current_price == 0.0 and len(description.strip().split()) == 6:
        return {
            "underlying": underlying,
            "expiry": expiry,
            "strike": strike,
            "option_type": option_type,
        }

    # Otherwise, return an OptionContract object
    return OptionContract(
        underlying=underlying,
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        quantity=quantity,
        current_price=abs(
            current_price
        ),  # Ensure price is positive; directionality is handled by quantity
        description=description,
    )


def calculate_option_delta(
    option: OptionContract,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> float:
    """Calculates the option delta using QuantLib.

    This function serves as a wrapper to compute delta using QuantLib,
    which accounts for time, volatility, and interest rates.

    Args:
        option: The `OptionPosition` object.
        underlying_price: The current market price of the underlying asset.
        risk_free_rate: The annualized risk-free interest rate. Defaults to 0.05 (5%).
        implied_volatility: Optional override for implied volatility. Defaults to None.

    Returns:
        The calculated delta value for the option position (between -1.0 and 1.0),
        adjusted for the position direction (negative for short positions).
    """
    # Validate inputs
    if underlying_price <= 0:
        raise ValueError(f"Underlying price must be positive: {underlying_price}")

    # Use provided volatility or default
    if implied_volatility is None:
        implied_volatility = 0.3  # Default volatility

    # Calculate raw delta using QuantLib
    raw_delta = calculate_black_scholes_delta(
        option, underlying_price, risk_free_rate, implied_volatility
    )

    # Adjust for position direction (short positions have inverted delta)
    adjusted_delta = raw_delta if option.quantity >= 0 else -raw_delta

    return adjusted_delta


def calculate_option_exposure(
    option: OptionContract,
    underlying_price: float,
    beta: float = 1.0,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,
) -> dict[str, float]:
    """Calculate exposure metrics for an option position.

    This function calculates various exposure metrics for an option position, including
    delta, delta exposure (delta * notional_value), and beta-adjusted exposure
    (delta_exposure * beta).

    Args:
        option: The option position
        underlying_price: The price of the underlying asset
        beta: The beta of the underlying asset relative to the market. Defaults to 1.0.
        risk_free_rate: The risk-free interest rate. Defaults to 0.05 (5%).
        implied_volatility: Optional override for implied volatility. Defaults to None.

    Returns:
        A dictionary containing exposure metrics:
        - 'delta': The option's delta
        - 'delta_exposure': The delta-adjusted exposure (delta * notional_value)
        - 'beta_adjusted_exposure': The beta-adjusted exposure (delta_exposure * beta)
    """
    # Calculate delta using QuantLib
    delta = calculate_option_delta(
        option,
        underlying_price,
        risk_free_rate=risk_free_rate,
        implied_volatility=implied_volatility,
    )

    # Calculate delta exposure
    delta_exposure = delta * option.notional_value

    # Calculate beta-adjusted exposure
    beta_adjusted_exposure = delta_exposure * beta

    return {
        "delta": delta,
        "delta_exposure": delta_exposure,
        "beta_adjusted_exposure": beta_adjusted_exposure,
    }


def estimate_volatility_with_skew(
    option: OptionContract,
    underlying_price: float,
    base_volatility: float = 0.3,
) -> float:
    """Estimate implied volatility with a simple volatility skew model.

    This function applies a simple volatility skew model to adjust the base volatility
    based on the moneyness of the option. Out-of-the-money puts and in-the-money calls
    typically have higher implied volatility (volatility smile/skew).

    Args:
        option: The option position
        underlying_price: Current price of the underlying asset
        base_volatility: Base volatility to adjust from (default: 0.3 or 30%)

    Returns:
        Adjusted implied volatility estimate
    """
    # Calculate moneyness (K/S for calls, S/K for puts)
    if option.option_type == "CALL":
        moneyness = option.strike / underlying_price
    else:  # PUT
        moneyness = underlying_price / option.strike

    # Apply a simple skew model
    # - For calls: Higher IV for ITM (moneyness < 1)
    # - For puts: Higher IV for OTM (moneyness < 1)
    skew_factor = 1.0

    # Adjust skew based on moneyness
    if moneyness < 0.8:
        skew_factor = 1.2  # Significantly OTM/ITM
    elif moneyness < 0.9:
        skew_factor = 1.1  # Moderately OTM/ITM
    elif moneyness > 1.2:
        skew_factor = 1.2  # Significantly ITM/OTM
    elif moneyness > 1.1:
        skew_factor = 1.1  # Moderately ITM/OTM

    # Apply time-to-expiry adjustment (longer expiry = less skew)
    days_to_expiry = (option.expiry - datetime.datetime.now()).days
    if days_to_expiry > 180:  # Long-dated options
        skew_factor = (skew_factor + 1.0) / 2.0  # Reduce skew effect

    return base_volatility * skew_factor


def get_implied_volatility(
    option: OptionContract,
    underlying_price: float,
    risk_free_rate: float = 0.05,
) -> float:
    """Get implied volatility for an option, either from market price or estimated.

    This function attempts to calculate implied volatility from the option's market price.
    If that fails (e.g., due to invalid market price), it falls back to a volatility
    estimation model based on option characteristics.

    Args:
        option: The option position
        underlying_price: Current price of the underlying asset
        risk_free_rate: Risk-free interest rate (default: 0.05 or 5%)

    Returns:
        Implied volatility estimate
    """
    try:
        # First try to calculate IV from market price
        if option.current_price > 0:
            iv = calculate_implied_volatility(
                option, underlying_price, option.current_price, risk_free_rate
            )

            # Sanity check on the result
            if 0.01 <= iv <= 2.0:  # IV between 1% and 200%
                return iv
    except Exception as e:
        logger.debug(f"Error calculating IV from market price: {e}")

    # Fall back to volatility estimation model
    return estimate_volatility_with_skew(option, underlying_price)


def process_options(
    options_data: list[dict],
    prices: dict[str, float],
    betas: dict[str, float] | None = None,
) -> list[dict]:
    """Process a list of option data dictionaries.

    This function takes a list of dictionaries containing option data, parses the option
    descriptions, calculates exposure metrics, and returns a list of dictionaries with
    the processed data.

    Args:
        options_data: List of dictionaries containing option data.
            Each dictionary must have:
            - 'description': Option description string
            - 'quantity': Option quantity
            - 'price': Option price
            It may optionally have:
            - 'symbol': Option symbol
        prices: Dictionary mapping tickers to prices
        betas: Dictionary mapping tickers to betas. If None, all betas default to 1.0.

    Returns:
        List of dictionaries with processed option data including exposures
    """
    if betas is None:
        betas = {}

    processed_options = []

    for opt_data in options_data:
        try:
            # Parse option description
            parsed_option = parse_option_description(
                opt_data["description"], opt_data["quantity"], opt_data["price"]
            )

            # Get underlying price and beta
            underlying = parsed_option.underlying
            if underlying not in prices:
                logger.warning(
                    f"No price found for {underlying}. Skipping option {parsed_option.description}."
                )
                continue

            underlying_price = prices[underlying]
            beta = betas.get(underlying, 1.0)  # Default to 1.0 if no beta found

            # Calculate exposures
            exposures = calculate_option_exposure(parsed_option, underlying_price, beta)

            # Combine original data with calculated metrics
            processed_opt = {
                "ticker": underlying,
                "option_symbol": opt_data.get("symbol", ""),
                "description": parsed_option.description,
                "quantity": parsed_option.quantity,
                "beta": beta,
                "strike": parsed_option.strike,
                "expiry": parsed_option.expiry.strftime("%Y-%m-%d"),
                "option_type": parsed_option.option_type,
                "price": parsed_option.current_price,
                "delta": exposures["delta"],
                "delta_exposure": exposures["delta_exposure"],
                "beta_adjusted_exposure": exposures["beta_adjusted_exposure"],
                "notional_value": parsed_option.notional_value,
            }

            processed_options.append(processed_opt)

        except Exception as e:
            logger.error(
                f"Error processing option {opt_data.get('description', 'unknown')}: {e}"
            )
            continue

    return processed_options
