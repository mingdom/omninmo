"""
Utilities for handling option positions and calculations.

This module provides functionality for parsing, analyzing, and calculating metrics for
option positions. It includes tools for parsing option descriptions, calculating option
deltas using both Black-Scholes and simplified models, and estimating implied volatility.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime

from scipy.stats import norm

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class OptionPosition:
    """Represents a single option position, storing its key characteristics and providing calculated properties.

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

    TODO:
        - Consider adding fields for Greeks (delta, gamma, theta, vega) if calculated elsewhere
          and need to be stored with the position.
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

    # Removed redundant is_short property - use quantity < 0 directly


def parse_month(month_str: str) -> int:
    """Convert a month abbreviation to its numerical value (1-12).

    This function takes a three-letter month abbreviation (e.g., "JAN", "FEB") and
    returns the corresponding month number (1-12). The function is case-insensitive
    and will convert the input to uppercase before processing.

    Args:
        month_str: Three-letter month abbreviation (e.g., "JAN", "FEB")

    Returns:
        int: Month number (1-12)

    Raises:
        ValueError: If the month abbreviation is invalid
    """
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

    if not month_str or len(month_str) != 3:
        logger.error(
            f"Invalid month format: '{month_str}'. Expected 3-letter abbreviation."
        )
        raise ValueError(
            f"Invalid month format: '{month_str}'. Expected 3-letter abbreviation."
        )

    try:
        month_num = month_map[month_str.upper()]  # Ensure uppercase
        logger.debug(f"Parsed month '{month_str}' to {month_num}")
        return month_num
    except KeyError as err:
        logger.error(f"Invalid month abbreviation: '{month_str}'")
        raise ValueError(f"Invalid month abbreviation: '{month_str}'") from err


def parse_option_description(
    description: str, quantity: int, current_price: float
) -> OptionPosition:
    """Parses a specific option description string format into an OptionPosition object.

    This function expects a description string with exactly 6 space-separated parts:
    1. Underlying ticker (e.g., "AAPL")
    2. Month abbreviation (e.g., "JAN", "FEB")
    3. Day (e.g., "15")
    4. Year (e.g., "2023")
    5. Strike price with $ prefix (e.g., "$150")
    6. Option type (e.g., "CALL", "PUT")

    Example: "AAPL JAN 20 2023 $150 CALL"

    Args:
        description: The option description string to parse
        quantity: The number of contracts (positive for long, negative for short)
        current_price: The current market price per contract

    Returns:
        OptionPosition: A populated OptionPosition object

    Raises:
        ValueError: If the description string does not match the expected 6-part format,
                    if the month abbreviation is invalid, if the day/year/strike cannot
                    be converted to numbers, or if the option type is not 'CALL' or 'PUT'.
    """

    logger.debug(f"Parsing option description: '{description}'")

    # Split the description into parts
    parts = description.strip().split()

    # Validate the number of parts
    if len(parts) != 6:
        error_msg = f"Invalid option description format: {description}. Expected 6 parts, got {len(parts)}."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Extract the parts
    underlying = parts[0]
    month_str = parts[1]
    day_str = parts[2]
    year_str = parts[3]
    strike_str = parts[4]
    option_type = parts[5]

    # Parse the components with better error handling
    try:
        # Parse month
        month = parse_month(month_str)

        # Parse day
        day = int(day_str)
        if not 1 <= day <= 31:  # Basic range check
            raise ValueError(f"Day out of range: {day}")

        # Parse year
        year = int(year_str)
        if not 2000 <= year <= 2100:  # Reasonable range check
            raise ValueError(f"Year out of range: {year}")

        # Parse strike price
        if not strike_str.startswith("$"):
            raise ValueError("Strike price must start with $")

        strike = float(strike_str[1:])  # Remove the $ and convert to float
        if strike <= 0:
            raise ValueError(f"Strike price must be positive: {strike}")

        # Validate option type
        option_type = option_type.upper()
        if option_type not in ["CALL", "PUT"]:
            raise ValueError(
                f"Invalid option type: '{option_type}'. Expected 'CALL' or 'PUT'."
            )

        # Create the expiry date
        expiry = datetime(year, month, day)

    except ValueError as e:
        # Provide a more specific error message based on which component failed
        error_context = str(e)
        if "month" in error_context.lower():
            error_msg = (
                f"Invalid month '{month_str}' in option description: {description}"
            )
        elif "day" in error_context.lower():
            error_msg = f"Invalid day '{day_str}' in option description: {description}"
        elif "year" in error_context.lower():
            error_msg = (
                f"Invalid year '{year_str}' in option description: {description}"
            )
        elif "strike" in error_context.lower():
            error_msg = f"Invalid strike price '{strike_str}' in option description: {description}"
        elif "option type" in error_context.lower():
            error_msg = f"Invalid option type '{option_type}' in option description: {description}"
        elif "out of range" in error_context.lower():
            error_msg = f"Date out of range in option description: {description}"
        else:
            error_msg = f"Invalid option description: {description}. Error: {e}"

        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Create and return the OptionPosition
    logger.debug(
        f"Successfully parsed option: {underlying} {expiry.strftime('%b %d %Y')} ${strike} {option_type}"
    )
    return OptionPosition(
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


def calculate_black_scholes_delta(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float = 0.30,
) -> float:
    """Calculates the option delta using the Black-Scholes-Merton (BSM) model.

    Delta represents the rate of change of the option price with respect to a $1
    change in the underlying asset price. It's a key measure of directional exposure.

    This function implements the standard BSM delta calculation:
    - For Calls: Delta = N(d1)
    - For Puts: Delta = N(d1) - 1
    where N is the cumulative distribution function (CDF) of the standard normal
    distribution, and d1 is a standardized measure incorporating underlying price,
    strike, time to expiry, risk-free rate, and volatility.

    The final delta returned is adjusted for the position direction (long/short).

    Args:
        option: The `OptionPosition` object containing option details (strike, expiry, type, quantity).
        underlying_price: The current market price of the underlying asset.
        risk_free_rate: The annualized risk-free interest rate (e.g., T-bill rate). Defaults to 0.05 (5%).
        implied_volatility: The annualized implied volatility of the option. Defaults to 0.30 (30%).

    Returns:
        The calculated delta value for the option position (between -1.0 and 1.0).

    Raises:
        ValueError: If `implied_volatility` or `underlying_price` is non-positive, or if `option.strike` is non-positive.
        ZeroDivisionError: If `time_to_expiry` is exactly zero and `implied_volatility` is also zero (mathematically undefined).

    TODO:
        - Consider adding dividend yield to the BSM calculation for more accuracy on dividend-paying stocks.
        - Handle potential numerical instability for very deep ITM/OTM or near-expiry options.
    """
    # Input validation
    if underlying_price <= 0:
        raise ValueError("Underlying price must be positive.")
    if option.strike <= 0:
        raise ValueError("Strike price must be positive.")
    if implied_volatility <= 0:
        raise ValueError("Implied volatility must be positive.")
    if not (0 <= risk_free_rate < 1):
        # Warn if rate seems unusual, but allow calculation
        logger.warning(
            f"Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
        )

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Handle expired options or options very close to expiry
    if time_to_expiry <= 1e-9:  # Use a small epsilon instead of exact zero
        # For expired options, delta is deterministic based on moneyness
        if option.option_type == "CALL":
            delta_signed = 1.0 if underlying_price > option.strike else 0.0
        else:  # PUT
            delta_signed = -1.0 if underlying_price < option.strike else 0.0
        # Return the raw delta without adjusting for short positions
        return delta_signed

    # Calculate d1 component of the BSM formula
    # Standard deviation for the time period
    vol_sqrt_t = implied_volatility * math.sqrt(time_to_expiry)

    # Check for zero vol_sqrt_t to prevent division by zero
    if vol_sqrt_t == 0:
        # This occurs if IV is 0. Result is essentially deterministic.
        # Re-evaluate based on moneyness, similar to expired case but considering rate.
        # Discounted strike price for comparison
        discounted_strike = option.strike * math.exp(-risk_free_rate * time_to_expiry)
        if option.option_type == "CALL":
            delta_signed = 1.0 if underlying_price > discounted_strike else 0.0
        else:  # PUT
            delta_signed = -1.0 if underlying_price < discounted_strike else 0.0
        # Return the raw delta without adjusting for short positions
        return delta_signed

    d1 = (
        math.log(underlying_price / option.strike)
        + (risk_free_rate + 0.5 * implied_volatility**2) * time_to_expiry
    ) / vol_sqrt_t

    # Calculate delta based on option type using the standard normal CDF
    if option.option_type == "CALL":
        delta_signed = norm.cdf(d1)
    else:  # PUT
        delta_signed = norm.cdf(d1) - 1  # Equivalent to -norm.cdf(-d1)

    # Return the raw delta without adjusting for short positions
    # The adjustment for short positions should be done at the exposure calculation level
    # by using the signed notional value or by the caller

    # Clamp result to ensure it's within the theoretical [-1, 1] bounds
    return max(-1.0, min(delta_signed, 1.0))


def calculate_bs_price(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float = 0.30,
) -> float:
    """Calculates the theoretical option price using the Black-Scholes-Merton (BSM) model.

    This provides the fair value of an option based on the BSM assumptions. It does not
    consider the actual market price or the quantity held.

    BSM formulas:
    - Call Price = S * N(d1) - K * exp(-r*T) * N(d2)
    - Put Price  = K * exp(-r*T) * N(-d2) - S * N(-d1)
    where:
        S = underlying price
        K = strike price
        r = risk-free rate
        T = time to expiry (in years)
        N = standard normal CDF
        d1, d2 = intermediate parameters involving S, K, r, T, volatility

    Args:
        option: The `OptionPosition` object (only uses strike, expiry, type).
        underlying_price: The current market price of the underlying asset.
        risk_free_rate: The annualized risk-free interest rate. Defaults to 0.05 (5%).
        implied_volatility: The annualized implied volatility of the option. Defaults to 0.30 (30%).

    Returns:
        The theoretical BSM price per contract of the option.

    Raises:
        ValueError: If `implied_volatility` or `underlying_price` is non-positive, or if `option.strike` is non-positive.
        ZeroDivisionError: If `time_to_expiry` is exactly zero and `implied_volatility` is also zero.

    TODO:
        - Add dividend yield to the calculation for accuracy on dividend stocks.
    """
    # Input validation (similar to delta calculation)
    if underlying_price <= 0:
        raise ValueError("Underlying price must be positive.")
    if option.strike <= 0:
        raise ValueError("Strike price must be positive.")
    if implied_volatility <= 0:
        raise ValueError("Implied volatility must be positive.")
    if not (0 <= risk_free_rate < 1):
        logger.warning(
            f"Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
        )

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Handle expired options: price is intrinsic value
    if time_to_expiry <= 1e-9:
        if option.option_type == "CALL":
            return max(0.0, underlying_price - option.strike)
        else:  # PUT
            return max(0.0, option.strike - underlying_price)

    # Calculate d1 and d2 components of the BSM formula
    vol_sqrt_t = implied_volatility * math.sqrt(time_to_expiry)

    if vol_sqrt_t == 0:
        # Handle zero volatility case - price is discounted intrinsic value
        discount_factor = math.exp(-risk_free_rate * time_to_expiry)
        if option.option_type == "CALL":
            return max(0.0, underlying_price - option.strike * discount_factor)
        else:  # PUT
            return max(0.0, option.strike * discount_factor - underlying_price)

    d1 = (
        math.log(underlying_price / option.strike)
        + (risk_free_rate + 0.5 * implied_volatility**2) * time_to_expiry
    ) / vol_sqrt_t

    d2 = d1 - vol_sqrt_t

    # Calculate option price based on type
    discount_factor = math.exp(-risk_free_rate * time_to_expiry)
    if option.option_type == "CALL":
        price = underlying_price * norm.cdf(
            d1
        ) - option.strike * discount_factor * norm.cdf(d2)
    else:  # PUT
        price = option.strike * discount_factor * norm.cdf(
            -d2
        ) - underlying_price * norm.cdf(-d1)

    # Price cannot be negative
    return max(0.0, price)


def calculate_implied_volatility(
    option: OptionPosition,
    underlying_price: float,
    market_price: float | None = None,
    risk_free_rate: float = 0.05,
    max_iterations: int = 100,
    precision: float = 0.0001,
) -> float:
    """Calculates the implied volatility (IV) of an option given its market price.

    Implied volatility is the value of the volatility parameter that, when plugged into
    the Black-Scholes-Merton model (`calculate_bs_price`), yields the option's current
    market price.

    This function uses a numerical root-finding algorithm (bisection method) to iteratively
    search for the volatility value that makes the theoretical BSM price match the
    observed market price.

    Args:
        option: The `OptionPosition` object (uses strike, expiry, type, and potentially current_price).
        underlying_price: The current market price of the underlying asset.
        market_price: The market price per contract of the option. If None, it uses
                      `option.current_price` from the input object. Defaults to None.
        risk_free_rate: The annualized risk-free interest rate. Defaults to 0.05 (5%).
        max_iterations: The maximum number of iterations for the bisection search.
                        Defaults to 100.
        precision: The desired precision (tolerance) for the difference between the
                   calculated BSM price and the market price. Defaults to 0.0001.

    Returns:
        The calculated implied volatility (as a decimal, e.g., 0.30 for 30%). Returns 0.0
        for expired options. Might return an estimate (e.g., 0.9) for options priced at
        or below intrinsic value where IV is mathematically difficult to determine precisely.

    Raises:
        ValueError: If `underlying_price`, `option.strike`, or `market_price` is non-positive.

    TODO:
        - Implement a more robust root-finding algorithm (e.g., Newton-Raphson) which might converge faster.
        - Handle cases where no IV can be found within the search bounds (e.g., arbitrage opportunities).
        - Add dividend yield input for accuracy.
        - Improve the handling of options at/below intrinsic value - returning a fixed high IV might not always be ideal.
    """
    # Use the provided market price or the option's current price
    target_price = market_price if market_price is not None else option.current_price

    # Input validation
    if underlying_price <= 0:
        raise ValueError("Underlying price must be positive.")
    if option.strike <= 0:
        raise ValueError("Strike price must be positive.")
    if target_price <= 0:
        # If market price is zero or negative, IV is effectively zero or undefined.
        # Warn and return 0, as it often indicates an issue with the price data.
        logger.warning(
            f"Market price ({target_price}) for {option.description} is non-positive. Returning IV=0.0"
        )
        return 0.0
    if not (0 <= risk_free_rate < 1):
        logger.warning(
            f"Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
        )

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # Check for expired options or zero time to expiry
    if time_to_expiry <= 1e-9:
        return 0.0  # IV is meaningless for expired options

    # Handle intrinsic value cases: If market price is at or below intrinsic value,
    # IV calculation is problematic (might imply negative time value).
    intrinsic_value = 0.0
    if option.option_type == "CALL":
        intrinsic_value = max(0.0, underlying_price - option.strike)
    else:  # PUT
        intrinsic_value = max(0.0, option.strike - underlying_price)

    # Use a small tolerance for floating point comparisons
    if target_price <= intrinsic_value + 1e-6:
        # For options trading at or very close to intrinsic value, especially deep ITM,
        # IV is highly sensitive and often meaningless. Returning a default might be necessary.
        # A low IV (e.g., 0.001) or a high one (0.9) could be argued. Let's use a low one
        # assuming minimal extrinsic value implies low expected future volatility.
        logger.warning(
            f"Option {option.description} trading near/below intrinsic value. Returning low default IV."
        )
        return 0.01  # Return 1% as a default low IV

    # Initialize volatility search range [lower_bound, upper_bound]
    vol_low = 0.001  # Min realistic IV (0.1%)
    vol_high = 3.0  # Max realistic IV (300%)
    # Initial guess using vol_high to check if price is achievable
    price_at_high_vol = calculate_bs_price(
        option, underlying_price, risk_free_rate, vol_high
    )

    # If the target price is higher than the price achievable even with max volatility,
    # it might indicate an arbitrage or data error. Return max vol as best guess.
    if target_price > price_at_high_vol:
        logger.warning(
            f"Market price {target_price} > theoretical max price {price_at_high_vol} for {option.description}. Returning max IV."
        )
        return vol_high

    # Bisection method to find implied volatility
    for _ in range(max_iterations):
        vol_mid = (vol_low + vol_high) / 2.0

        # If range is already very small, return midpoint
        if (vol_high - vol_low) < precision:
            return vol_mid

        # Calculate theoretical price at the midpoint volatility
        try:
            price_at_mid_vol = calculate_bs_price(
                option, underlying_price, risk_free_rate, vol_mid
            )
        except ValueError:
            # Should not happen if vol_mid is positive, but handle defensively
            # If BSM calculation fails, try adjusting bounds slightly
            # This indicates potential instability, might need different approach
            logger.warning(
                f"BSM price calculation failed at IV={vol_mid}. Adjusting bounds."
            )
            # If price tends to increase with vol (most common), failing likely means vol_low was too low
            # Try slightly increasing vol_low - this is heuristic
            vol_low += precision
            continue

        # Compare theoretical price with target market price
        if price_at_mid_vol < target_price:
            # If theoretical price is too low, need higher volatility
            vol_low = vol_mid
        else:
            # If theoretical price is too high, need lower volatility
            vol_high = vol_mid

    # After max_iterations, return the midpoint of the final range
    final_iv = (vol_low + vol_high) / 2.0
    logger.debug(
        f"IV calculation finished for {option.description}. IV: {final_iv:.4f}"
    )
    return final_iv


def estimate_volatility_with_skew(
    option: OptionPosition,
    underlying_price: float,
    base_volatility: float = 0.3,
) -> float:
    """Estimates implied volatility using a simplified volatility skew and term structure model.

    This function is a fallback for when the actual market price of the option is unavailable
    or unreliable, preventing direct calculation of implied volatility via `calculate_implied_volatility`.

    It starts with a `base_volatility` (e.g., historical volatility or ATM IV) and adjusts it based on:
    1.  **Moneyness (Skew/Smile):** Options further Out-of-The-Money (OTM) or In-The-Money (ITM)
        often have higher implied volatility than At-The-Money (ATM) options. This function applies
        simple multiplicative factors based on moneyness categories.
    2.  **Time to Expiration (Term Structure):** Shorter-term options typically exhibit higher IV
        than longer-term options. Simple multiplicative factors are applied based on time remaining.

    Args:
        option: The `OptionPosition` object (uses strike, expiry, type).
        underlying_price: The current market price of the underlying asset.
        base_volatility: The initial volatility estimate to adjust (e.g., 30-day historical vol).
                         Defaults to 0.30 (30%).

    Returns:
        An estimated implied volatility value (decimal), capped between reasonable bounds (e.g., 0.1% to 150%).

    Note:
        This is a heuristic model. The actual volatility skew and term structure can be complex
        and vary significantly between assets and market conditions. The factors used here
        are illustrative and may need tuning.

    TODO:
        - Use a more sophisticated skew model (e.g., quadratic fit based on moneyness).
        - Incorporate market data (like VIX or HV) to inform the `base_volatility`.
        - Allow customization of the skew and term structure factors.
        - Validate underlying_price and option.strike are positive.
    """
    # Input validation
    if underlying_price <= 0:
        raise ValueError("Underlying price must be positive.")
    if option.strike <= 0:
        raise ValueError("Strike price must be positive.")
    if not (
        0.01 <= base_volatility <= 2.0
    ):  # Check if base vol is reasonable (1% to 200%)
        logger.warning(
            f"Base volatility ({base_volatility}) is outside typical [0.01, 2.0] range."
        )

    # Calculate moneyness (how far ITM/OTM the option is)
    moneyness = 0.0
    if option.option_type == "CALL":
        # Avoid division by zero
        moneyness = underlying_price / option.strike if option.strike > 0 else 1.0
    else:  # PUT
        # Avoid division by zero
        moneyness = option.strike / underlying_price if underlying_price > 0 else 1.0

    # Calculate time to expiration in years
    now = datetime.now()
    time_to_expiry = (option.expiry - now).total_seconds() / (365.25 * 24 * 60 * 60)

    # If expired, estimated IV is irrelevant (use 0 or low value)
    if time_to_expiry <= 1e-9:
        return 0.01  # Return minimal IV for near/at expiry

    # --- Apply Volatility Smile/Skew Adjustment ---
    # Example: Higher IV for OTM/deep ITM, lower for ATM
    # These factors are purely illustrative!
    if moneyness < 0.8:  # Deep OTM (relative to strike)
        skew_factor = 1.4
    elif moneyness < 0.95:  # OTM
        skew_factor = 1.2
    elif moneyness > 1.2:  # Deep ITM
        skew_factor = (
            1.1  # Often lower than OTM for calls, but can be higher for puts (skew)
        )
    elif moneyness > 1.05:  # ITM
        skew_factor = 1.05
    else:  # ATM (0.95 <= moneyness <= 1.05)
        skew_factor = 1.0

    # --- Apply Term Structure Adjustment ---
    # Example: Higher IV for shorter-term options
    if time_to_expiry < 0.083:  # Less than ~1 month
        term_factor = 1.2
    elif time_to_expiry < 0.25:  # Less than 3 months
        term_factor = 1.1
    elif time_to_expiry > 1.0:  # More than a year (LEAPS often have lower IV)
        term_factor = 0.9
    else:  # 3 months to 1 year
        term_factor = 1.0

    # Apply both adjustments to the base volatility
    estimated_iv = base_volatility * skew_factor * term_factor

    # Ensure the estimated IV is within reasonable bounds (e.g., 1% to 150%)
    final_iv = max(0.01, min(estimated_iv, 1.5))

    logger.debug(
        f"Estimated IV for {option.description}: Base={base_volatility:.2f}, SkewF={skew_factor:.2f}, TermF={term_factor:.2f} => Final={final_iv:.3f}"
    )
    return final_iv


def get_implied_volatility(
    option: OptionPosition, underlying_price: float, risk_free_rate: float = 0.05
) -> float:
    """Determines the implied volatility (IV) for an option, prioritizing calculation from market price.

    This function acts as a primary interface for obtaining IV.
    1. It first attempts to calculate the IV directly using the option's market price
       (`option.current_price`) via `calculate_implied_volatility`.
    2. If `option.current_price` is missing, zero, or leads to an unreasonable IV
       (outside a plausible range like 1% to 200%), it falls back to estimating IV.
    3. The estimation uses `estimate_volatility_with_skew`, which applies adjustments for
       moneyness and time-to-expiry to a default base volatility.
    4. If any calculation step encounters an error, it logs the error and returns a
       conservative default IV (e.g., 30%).

    Args:
        option: The `OptionPosition` object.
        underlying_price: The current market price of the underlying asset.
        risk_free_rate: The annualized risk-free interest rate. Defaults to 0.05 (5%).

    Returns:
        The calculated or estimated implied volatility (decimal), or a default value (0.30)
        if errors occur.

    TODO:
        - Make the acceptable IV range [0.01, 2.0] configurable.
        - Allow passing a `base_volatility` to the skew estimation fallback.
        - Improve error handling to distinguish between calculation failures and invalid inputs.
    """
    # Define a reasonable IV range
    MIN_IV = 0.01  # 1%
    MAX_IV = 2.00  # 200%
    DEFAULT_IV = 0.30  # 30% fallback

    try:
        # 1. Attempt calculation from market price if available and positive
        if hasattr(option, "current_price") and option.current_price > 0:
            try:
                logger.debug(
                    f"Attempting IV calculation from market price {option.current_price} for {option.description}"
                )
                calculated_iv = calculate_implied_volatility(
                    option=option,  # Pass the whole object
                    underlying_price=underlying_price,
                    market_price=option.current_price,  # Explicitly pass market price
                    risk_free_rate=risk_free_rate,
                    # Use default precision/iterations from calculate_implied_volatility
                )

                # 2. Check if calculated IV is within the reasonable range
                if MIN_IV <= calculated_iv <= MAX_IV:
                    logger.debug(
                        f"Successfully calculated IV from market price: {calculated_iv:.4f}"
                    )
                    return calculated_iv
                else:
                    # Calculated IV was outside the expected range (e.g., due to price near intrinsic)
                    logger.warning(
                        f"Calculated IV ({calculated_iv:.4f}) for {option.description} is outside range [{MIN_IV}, {MAX_IV}]. Falling back to estimation."
                    )

            except ValueError as ve:
                logger.error(
                    f"ValueError during IV calculation for {option.description}: {ve}. Falling back to estimation."
                )
            except RuntimeError as re:
                logger.error(
                    f"RuntimeError during IV calculation for {option.description}: {re}. Falling back to estimation."
                )
            # Catch any other unexpected errors during calculation
            except Exception as iv_calc_err:
                logger.error(
                    f"Unexpected error during IV calculation for {option.description}: {iv_calc_err}. Falling back to estimation."
                )
        else:
            # Market price not available or non-positive
            logger.debug(
                f"Market price missing or non-positive for {option.description}. Falling back to IV estimation."
            )
            pass  # Proceed to estimation

        # 3. Fallback: Estimate IV using skew model
        logger.debug(f"Estimating IV using skew model for {option.description}")
        estimated_iv = estimate_volatility_with_skew(
            option=option,
            underlying_price=underlying_price,
            base_volatility=DEFAULT_IV,  # Use the default as base for estimation
        )
        logger.debug(f"Estimated IV: {estimated_iv:.4f}")
        return estimated_iv

    except Exception as e:
        # 4. Catch-all for errors in the estimation step or unexpected issues
        logger.error(
            f"Error getting IV for {option.description}: {e}. Returning default IV {DEFAULT_IV}."
        )
        return DEFAULT_IV  # Return conservative default on any failure


def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,  # Allow optional IV override
) -> float:
    """Calculates the option delta using the Black-Scholes-Merton model.

    This function serves as a wrapper to compute delta using the Black-Scholes-Merton model,
    which accounts for time, volatility, and interest rates.

    If `implied_volatility` is not provided, this function will attempt to obtain it
    using `get_implied_volatility` (which may calculate from market price or estimate
    using a skew model).

    Args:
        option: The `OptionPosition` object.
        underlying_price: The current market price of the underlying asset.
        risk_free_rate: The annualized risk-free interest rate. Defaults to 0.05 (5%).
        implied_volatility: Optional. If provided, this IV value is used directly for the
                            BSM calculation, overriding the value obtained by
                            `get_implied_volatility`. Defaults to None.

    Returns:
        The calculated delta value for the option position (between -1.0 and 1.0),
        adjusted for the position direction (negative for short positions).

    Raises:
        ValueError: If underlying_price is non-positive or if option data is invalid.
    """
    # Validate inputs
    if underlying_price <= 0:
        error_msg = f"Underlying price must be positive: {underlying_price}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log the calculation
    logger.debug(f"Calculating delta for {option.description}")

    try:
        # Determine the IV to use
        iv_to_use = implied_volatility  # Use provided IV if available
        if iv_to_use is None:
            logger.debug(f"No IV provided, estimating IV for {option.description}")
            iv_to_use = get_implied_volatility(option, underlying_price, risk_free_rate)
            logger.debug(f"Estimated IV: {iv_to_use:.4f}")
        elif not (0.001 <= iv_to_use <= 3.0):  # Basic sanity check on provided IV
            logger.warning(f"Unusual IV value ({iv_to_use}) for {option.description}")

        # Get the raw delta from Black-Scholes
        raw_delta = calculate_black_scholes_delta(
            option, underlying_price, risk_free_rate, iv_to_use
        )

        # Adjust for position direction (short positions have inverted delta)
        adjusted_delta = raw_delta if option.quantity >= 0 else -raw_delta

        logger.debug(f"Delta calculated: {adjusted_delta:.4f}")
        return adjusted_delta

    except Exception as e:
        error_msg = f"Error calculating delta for {option.description}: {e}"
        logger.error(error_msg)
        # Re-raise with a more specific message
        raise ValueError(error_msg) from e


# _calculate_simple_delta function has been removed


def calculate_option_exposure(
    option: OptionPosition,
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
    # Calculate delta using Black-Scholes
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


def group_options_by_underlying(
    options: list[OptionPosition],
) -> dict[str, list[OptionPosition]]:
    """Groups a list of OptionPosition objects into a dictionary keyed by the underlying symbol.

    Args:
        options: A list of `OptionPosition` objects.

    Returns:
        A dictionary where keys are underlying ticker symbols (str) and values are lists
        containing all `OptionPosition` objects related to that underlying.
    """
    grouped = {}
    for option in options:
        if not isinstance(option, OptionPosition):
            logger.warning(
                f"Item in list is not an OptionPosition: {option}. Skipping."
            )
            continue
        # Add option to the list for its underlying ticker
        grouped.setdefault(option.underlying, []).append(option)
    return grouped
