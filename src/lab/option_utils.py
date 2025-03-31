"""
Utilities for handling option positions and calculations.
"""

from dataclasses import dataclass
from datetime import datetime


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
    This is a placeholder for more sophisticated delta calculation.
    """
    moneyness = underlying_price / option.strike

    if option.option_type == "CALL":
        if moneyness >= 1.1:  # Deep ITM
            delta = 0.95
        elif moneyness <= 0.9:  # Deep OTM
            delta = 0.05
        else:  # Near the money
            delta = 0.5 + (moneyness - 1) * 2  # Linear approximation
    elif moneyness >= 1.1:  # Deep OTM
        delta = -0.05
    elif moneyness <= 0.9:  # Deep ITM
        delta = -0.95
    else:  # Near the money
        delta = -0.5 - (moneyness - 1) * 2  # Linear approximation

    # Ensure delta is within bounds
    delta = max(min(delta, 1.0), -1.0)

    # Adjust for position direction
    if option.is_short:
        delta = -delta

    return delta


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
