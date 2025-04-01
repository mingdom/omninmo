"""
Utilities for handling option positions and calculations.
"""

import math
from dataclasses import dataclass
from datetime import datetime

from scipy.stats import norm


@dataclass
class OptionPosition:
    """Represents a single option position."""

    underlying: str
    expiry: datetime
    strike: float
    option_type: str  # 'CALL' or 'PUT'
    quantity: int
    current_price: float
    description: str

    @property
    def notional_value(self) -> float:
        """Calculate notional value (strike * 100 * quantity)."""
        return self.strike * 100 * abs(self.quantity)

    @property
    def market_value(self) -> float:
        """Calculate market value (current_price * 100 * quantity)."""
        return self.current_price * 100 * self.quantity

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0


def parse_month(month_str: str) -> int:
    """Convert month string to number."""
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
    return month_map[month_str.upper()]


def parse_option_description(
    description: str, quantity: int, current_price: float
) -> OptionPosition:
    """
    Parse option description string into OptionPosition object.
    Example format: "GOOGL MAY 16 2025 $170 CALL"
    """
    # Remove any extra whitespace and split
    parts = description.strip().split()

    if len(parts) != 6 or not parts[4].startswith("$"):
        raise ValueError(f"Invalid option description format: {description}")

    underlying = parts[0]
    month = parse_month(parts[1])
    day = int(parts[2])
    year = int(parts[3])
    strike = float(parts[4].replace("$", ""))
    option_type = parts[5].upper()

    if option_type not in ["CALL", "PUT"]:
        raise ValueError(f"Invalid option type: {option_type}")

    expiry = datetime(year, month, day)

    return OptionPosition(
        underlying=underlying,
        expiry=expiry,
        strike=strike,
        option_type=option_type,
        quantity=quantity,
        current_price=abs(current_price),  # Ensure positive
        description=description,
    )


def calculate_simple_delta(option: OptionPosition, underlying_price: float) -> float:
    """
    Calculate a simple delta based on moneyness.
    TODO: This is a placeholder for more sophisticated delta calculation.
    """
    if option.option_type == "CALL":
        moneyness = underlying_price / option.strike
        if moneyness >= 1.1:  # Deep ITM
            delta = 0.95
        elif moneyness <= 0.9:  # Deep OTM
            delta = 0.05
        else:  # Near the money
            delta = 0.5 + (moneyness - 1) * 2  # Linear approximation
    else:  # PUT
        moneyness = option.strike / underlying_price  # Invert moneyness for puts
        if moneyness >= 1.1:  # Deep ITM for puts
            delta = -0.95
        elif moneyness <= 0.9:  # Deep OTM for puts
            delta = -0.05
        else:  # Near the money
            delta = -0.5 - (moneyness - 1) * 2  # Linear approximation

    # Ensure delta is within bounds
    delta = max(min(delta, 1.0), -1.0)

    # Adjust for position direction
    if option.is_short:
        delta = -delta

    return delta


def calculate_black_scholes_delta(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float = 0.30,
) -> float:
    """
    Calculate option delta using the Black-Scholes model.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        risk_free_rate: Risk-free interest rate (default: 5%)
        implied_volatility: Implied volatility of the option (default: 30%)

    Returns:
        Delta value of the option
    """
    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Handle expired options
    if time_to_expiry <= 0:
        if option.option_type == "CALL":
            return 1.0 if underlying_price > option.strike else 0.0
        else:  # PUT
            return -1.0 if underlying_price < option.strike else 0.0

    # Calculate d1 from Black-Scholes formula
    d1 = (
        math.log(underlying_price / option.strike)
        + (risk_free_rate + 0.5 * implied_volatility**2) * time_to_expiry
    ) / (implied_volatility * math.sqrt(time_to_expiry))

    # Calculate delta based on option type
    if option.option_type == "CALL":
        delta = norm.cdf(d1)
    else:  # PUT
        delta = norm.cdf(d1) - 1

    # Adjust for position direction
    if option.is_short:
        delta = -delta

    return delta


def calculate_bs_price(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float = 0.30,
) -> float:
    """
    Calculate the theoretical option price using the Black-Scholes model.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        risk_free_rate: Risk-free interest rate (default: 5%)
        implied_volatility: Implied volatility of the option (default: 30%)

    Returns:
        Theoretical option price
    """
    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Handle expired options
    if time_to_expiry <= 0:
        if option.option_type == "CALL":
            return max(0, underlying_price - option.strike)
        else:  # PUT
            return max(0, option.strike - underlying_price)

    # Calculate d1 and d2 from Black-Scholes formula
    d1 = (
        math.log(underlying_price / option.strike)
        + (risk_free_rate + 0.5 * implied_volatility**2) * time_to_expiry
    ) / (implied_volatility * math.sqrt(time_to_expiry))

    d2 = d1 - implied_volatility * math.sqrt(time_to_expiry)

    # Calculate option price based on type
    if option.option_type == "CALL":
        price = underlying_price * norm.cdf(d1) - option.strike * math.exp(
            -risk_free_rate * time_to_expiry
        ) * norm.cdf(d2)
    else:  # PUT
        price = option.strike * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(
            -d2
        ) - underlying_price * norm.cdf(-d1)

    return price


def calculate_implied_volatility(
    option: OptionPosition,
    underlying_price: float,
    market_price: float = None,
    risk_free_rate: float = 0.05,
    max_iterations: int = 100,
    precision: float = 0.0001,
) -> float:
    """
    Calculate implied volatility by iteratively solving the Black-Scholes formula.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        market_price: Market price of the option (if None, use option.current_price)
        risk_free_rate: Risk-free interest rate (default: 5%)
        max_iterations: Maximum number of iterations for the solver
        precision: Desired precision for the result

    Returns:
        Implied volatility value
    """
    # Use the provided market price or the option's current price
    market_price = market_price if market_price is not None else option.current_price

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Check for expired options or zero time to expiry
    if time_to_expiry <= 0:
        return 0.0

    # Handle intrinsic value cases to avoid division by zero
    intrinsic_value = 0
    if option.option_type == "CALL":
        intrinsic_value = max(0, underlying_price - option.strike)
    else:  # PUT
        intrinsic_value = max(0, option.strike - underlying_price)

    if market_price <= intrinsic_value:
        # For options trading at or below intrinsic value, use a high IV
        return 0.9  # 90% as a default for deep ITM options with no time value

    # Initialize volatility search range
    vol_low = 0.001  # 0.1%
    vol_high = 3.0  # 300%

    # Bisection method to find implied volatility
    for _ in range(max_iterations):
        vol_mid = (vol_low + vol_high) / 2.0
        price = calculate_bs_price(option, underlying_price, risk_free_rate, vol_mid)

        # If we're close enough to the market price, return the current volatility
        if abs(price - market_price) < precision:
            return vol_mid

        # Adjust the search range based on the result
        if price > market_price:
            vol_high = vol_mid
        else:
            vol_low = vol_mid

        # If the range gets too small, we've found our best approximation
        if abs(vol_high - vol_low) < precision:
            break

    # Return the midpoint of our final search range
    return (vol_low + vol_high) / 2.0


def estimate_volatility_with_skew(
    option: OptionPosition,
    underlying_price: float,
    base_volatility: float = 0.3,
) -> float:
    """
    Estimate implied volatility using a volatility skew model if market price isn't available.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        base_volatility: Base volatility to adjust (default: 30%)

    Returns:
        Estimated implied volatility considering volatility skew
    """
    # Calculate moneyness (how far ITM/OTM the option is)
    # K/S for puts, S/K for calls
    if option.option_type == "CALL":
        moneyness = underlying_price / option.strike
    else:  # PUT
        moneyness = option.strike / underlying_price

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Apply a simple volatility smile (higher IV for OTM options)
    if moneyness < 0.8:  # Deep OTM
        skew_factor = 1.4  # Increase IV for deep OTM
    elif moneyness < 0.95:  # OTM
        skew_factor = 1.2  # Slight increase for OTM
    elif moneyness > 1.2:  # Deep ITM
        skew_factor = 1.1  # Slight increase for deep ITM
    elif moneyness > 1.05:  # ITM
        skew_factor = 1.05  # Minimal increase for ITM
    else:  # ATM
        skew_factor = 1.0  # No adjustment for ATM

    # Adjust for time to expiration (term structure)
    # Shorter-term options typically have higher IV
    if time_to_expiry < 0.1:  # Less than ~1 month
        term_factor = 1.2
    elif time_to_expiry < 0.25:  # Less than 3 months
        term_factor = 1.1
    elif time_to_expiry > 1.0:  # More than a year
        term_factor = 0.9
    else:
        term_factor = 1.0

    # Apply both adjustments to the base volatility
    estimated_iv = base_volatility * skew_factor * term_factor

    # Cap the maximum IV to avoid unrealistic values
    return min(estimated_iv, 1.5)


def get_implied_volatility(
    option: OptionPosition, underlying_price: float, risk_free_rate: float = 0.05
) -> float:
    """
    Get the implied volatility for an option using market price if available,
    or estimate it using a volatility skew model.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        risk_free_rate: Risk-free interest rate (default: 5%)

    Returns:
        Implied volatility value
    """
    try:
        # First try to calculate IV from the option's market price
        if hasattr(option, "current_price") and option.current_price > 0:
            iv = calculate_implied_volatility(
                option, underlying_price, option.current_price, risk_free_rate
            )

            # If we got a reasonable result, return it
            if 0.01 <= iv <= 2.0:  # IV between 1% and 200%
                return iv

        # If we couldn't calculate IV from price or got an unreasonable value,
        # use the volatility skew model
        return estimate_volatility_with_skew(option, underlying_price)

    except Exception as e:
        # If anything fails, fall back to a reasonable default
        print(
            f"Error calculating IV for {option.underlying} {option.option_type} ${option.strike}: {e}"
        )
        return 0.3  # 30% as a conservative default


def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    use_black_scholes: bool = True,
    risk_free_rate: float = 0.05,
    implied_volatility: float = None,
) -> float:
    """
    Calculate option delta using either Black-Scholes model or simple approximation.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        use_black_scholes: Whether to use Black-Scholes model (True) or simple approximation (False)
        risk_free_rate: Risk-free interest rate (only used for Black-Scholes)
        implied_volatility: Implied volatility of the option (if None, will be estimated)

    Returns:
        Delta value of the option
    """
    if use_black_scholes:
        # If implied_volatility isn't provided, estimate it
        if implied_volatility is None:
            implied_volatility = get_implied_volatility(
                option, underlying_price, risk_free_rate
            )

        return calculate_black_scholes_delta(
            option, underlying_price, risk_free_rate, implied_volatility
        )
    else:
        return calculate_simple_delta(option, underlying_price)


def group_options_by_underlying(options: list[OptionPosition]) -> dict:
    """Group option positions by underlying symbol."""
    grouped = {}
    for option in options:
        if option.underlying not in grouped:
            grouped[option.underlying] = []
        grouped[option.underlying].append(option)
    return grouped


if __name__ == "__main__":
    # Test the parser
    test_desc = "GOOGL MAY 16 2025 $170 CALL"
    test_option = parse_option_description(test_desc, -10, 2.75)
    print(f"Parsed option: {test_option}")

    # Test delta calculation
    underlying_price = 154.33  # Current GOOGL price
    delta = calculate_simple_delta(test_option, underlying_price)
    print(f"Simple delta: {delta:.2f}")
    print(f"Delta-adjusted exposure: ${test_option.notional_value * delta:,.2f}")

    # Test Black-Scholes delta calculation
    bs_delta = calculate_black_scholes_delta(test_option, underlying_price)
    print(f"Black-Scholes delta: {bs_delta:.4f}")
    print(
        f"Black-Scholes delta-adjusted exposure: ${test_option.notional_value * bs_delta:,.2f}"
    )

    print("\nFor comprehensive testing of option delta calculations, run:")
    print("python -m pytest tests/test_option_delta.py -v")
