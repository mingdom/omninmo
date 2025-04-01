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


def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    use_black_scholes: bool = True,
    risk_free_rate: float = 0.05,
    implied_volatility: float = 0.30,
) -> float:
    """
    Calculate option delta using either Black-Scholes model or simple approximation.

    Args:
        option: OptionPosition object containing option details
        underlying_price: Current price of the underlying asset
        use_black_scholes: Whether to use Black-Scholes model (True) or simple approximation (False)
        risk_free_rate: Risk-free interest rate (only used for Black-Scholes)
        implied_volatility: Implied volatility of the option (only used for Black-Scholes)

    Returns:
        Delta value of the option
    """
    if use_black_scholes:
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
