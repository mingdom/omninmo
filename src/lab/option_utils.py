"""
Utilities for handling option positions and calculations.
"""

import math
from dataclasses import dataclass
from datetime import datetime

from scipy.stats import norm


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
        notional_value (float): The total value controlled by the option contract(s), calculated as
                                  `strike * 100 * abs(quantity)`.
        market_value (float): The current market value of the option position(s), calculated as
                                `current_price * 100 * quantity`.
        is_short (bool): True if the quantity is negative, indicating a short position.

    TODO:
        - Add fields for cost basis and purchase date for P/L calculations.
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
        """Calculate notional value (strike * 100 * quantity)."""
        # Contract size is typically 100 shares per option contract
        return self.strike * 100 * abs(self.quantity)

    @property
    def market_value(self) -> float:
        """Calculate market value (current_price * 100 * quantity)."""
        # Market value reflects the direction (long/short) via quantity sign
        return self.current_price * 100 * self.quantity

    @property
    def is_short(self) -> bool:
        """Check if position is short (quantity is negative)."""
        return self.quantity < 0


def parse_month(month_str: str) -> int:
    """Converts a three-letter uppercase month abbreviation string to its corresponding month number.

    Args:
        month_str: The three-letter uppercase month abbreviation (e.g., "JAN", "FEB").

    Returns:
        The integer month number (1 for JAN, 2 for FEB, ..., 12 for DEC).

    Raises:
        KeyError: If the input string is not a valid three-letter uppercase month abbreviation.
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
    # Using .get() with a default or handling KeyError is safer than direct access
    # return month_map[month_str.upper()] # Original was case-sensitive implicitly
    try:
        return month_map[month_str.upper()]  # Ensure uppercase
    except KeyError:
        raise ValueError(f"Invalid month abbreviation: {month_str}")


def parse_option_description(
    description: str, quantity: int, current_price: float
) -> OptionPosition:
    """Parses a specific option description string format into an OptionPosition object.

    This function expects a description string with exactly 6 space-separated parts:
    `UNDERLYING MONTH DAY YEAR $STRIKE TYPE`
    Example: "GOOGL MAY 16 2025 $170 CALL"

    It extracts the components, converts them to the appropriate types (using `parse_month`),
    and constructs an `OptionPosition` dataclass instance.

    Args:
        description: The option description string in the expected 6-part format.
        quantity: The number of option contracts (positive for long, negative for short).
        current_price: The current market price per contract of the option.

    Returns:
        An `OptionPosition` object populated with the parsed details.

    Raises:
        ValueError: If the description string does not match the expected 6-part format,
                    if the month abbreviation is invalid, if the day/year/strike cannot
                    be converted to numbers, or if the option type is not 'CALL' or 'PUT'.

    TODO:
        - Increase robustness to handle variations in spacing or formatting.
        - Support different date formats (e.g., YYMMDD). Use regex for flexibility?
        - Handle weekly or non-standard options if their format differs.
        - Consider passing the original symbol ('-GOOGL...') as well for reference.
    """
    # Remove any extra whitespace and split
    parts = description.strip().split()

    if len(parts) != 6:
        raise ValueError(
            f"Invalid option description format (expected 6 parts): {description}"
        )
    if not parts[4].startswith("$"):
        raise ValueError(
            f"Invalid option description format (strike missing '$'): {description}"
        )

    try:
        underlying = parts[0]
        month = parse_month(parts[1])  # Raises ValueError if invalid month
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
            # Ensure price is positive; directionality is handled by quantity
            current_price=abs(current_price),
            description=description,  # Store the original description
        )
    except ValueError as e:  # Catch conversion errors (int, float, parse_month)
        raise ValueError(
            f"Error parsing components of description '{description}': {e}"
        ) from e
    except Exception as e:  # Catch unexpected errors
        raise RuntimeError(
            f"Unexpected error parsing option description '{description}': {e}"
        ) from e


def calculate_simple_delta(option: OptionPosition, underlying_price: float) -> float:
    """Estimates option delta using a simplified linear approximation based on moneyness.

    This function provides a very basic delta estimation:
    - Deep In-The-Money (ITM): +/- 0.95
    - Deep Out-of-The-Money (OTM): +/- 0.05
    - Near-The-Money (NTM): Linearly interpolates between 0.05 and 0.95 based on moneyness.

    Moneyness definition:
    - Calls: `underlying_price / strike`
    - Puts: `strike / underlying_price`

    The delta sign depends on the option type (positive for calls, negative for puts)
    and the position direction (long/short).

    Args:
        option: The `OptionPosition` object.
        underlying_price: The current price of the underlying asset.

    Returns:
        An estimated delta value between -1.0 and 1.0.

    Note:
        This is a rough approximation and does NOT account for volatility, time to expiry,
        or interest rates. Use `calculate_black_scholes_delta` for a more accurate calculation.

    TODO:
        - Consider deprecating this in favor of always using Black-Scholes or another
          more standard model, unless a very fast, rough estimate is specifically required.
        - The linear interpolation logic could be refined.
    """
    delta_unsigned = 0.0  # Initialize unsigned delta

    if option.option_type == "CALL":
        # Avoid division by zero if strike is 0 (shouldn't happen for valid options)
        if option.strike <= 0:
            return 0.0
        moneyness = underlying_price / option.strike
        if moneyness >= 1.1:  # Deep ITM
            delta_unsigned = 0.95
        elif moneyness <= 0.9:  # Deep OTM
            delta_unsigned = 0.05
        else:  # Near the money (interpolate between 0.9 and 1.1 moneyness)
            # Linear interpolation: maps [0.9, 1.1] moneyness to [0.05, 0.95] delta
            # Formula: delta = min_delta + (moneyness - min_moneyness) * (max_delta - min_delta) / (max_moneyness - min_moneyness)
            delta_unsigned = 0.05 + (moneyness - 0.9) * (0.95 - 0.05) / (1.1 - 0.9)
            delta_unsigned = max(0.05, min(delta_unsigned, 0.95))  # Clamp within bounds
        delta_signed = delta_unsigned
    else:  # PUT
        # Avoid division by zero if underlying price is 0
        if underlying_price <= 0:
            return 0.0
        moneyness = option.strike / underlying_price  # Invert moneyness for puts
        if moneyness >= 1.1:  # Deep ITM for puts
            delta_unsigned = 0.95
        elif moneyness <= 0.9:  # Deep OTM for puts
            delta_unsigned = 0.05
        else:  # Near the money
            delta_unsigned = 0.05 + (moneyness - 0.9) * (0.95 - 0.05) / (1.1 - 0.9)
            delta_unsigned = max(0.05, min(delta_unsigned, 0.95))  # Clamp within bounds
        delta_signed = -delta_unsigned  # Puts have negative delta

    # Final delta depends on whether the position is long or short
    # If short, invert the delta.
    final_delta = delta_signed if not option.is_short else -delta_signed

    # Ensure final delta is strictly within [-1.0, 1.0]
    return max(-1.0, min(final_delta, 1.0))


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
        print(
            f"Warning: Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
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
        return delta_signed if not option.is_short else -delta_signed

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
        return delta_signed if not option.is_short else -delta_signed

    d1 = (
        math.log(underlying_price / option.strike)
        + (risk_free_rate + 0.5 * implied_volatility**2) * time_to_expiry
    ) / vol_sqrt_t

    # Calculate delta based on option type using the standard normal CDF
    if option.option_type == "CALL":
        delta_signed = norm.cdf(d1)
    else:  # PUT
        delta_signed = norm.cdf(d1) - 1  # Equivalent to -norm.cdf(-d1)

    # Adjust final delta based on position direction (short position has inverted delta)
    final_delta = delta_signed if not option.is_short else -delta_signed

    # Clamp result to ensure it's within the theoretical [-1, 1] bounds
    return max(-1.0, min(final_delta, 1.0))


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
        print(
            f"Warning: Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
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
        print(
            f"Warning: Market price ({target_price}) for {option.description} is non-positive. Returning IV=0.0"
        )
        return 0.0
    if not (0 <= risk_free_rate < 1):
        print(
            f"Warning: Risk-free rate ({risk_free_rate}) is outside typical [0, 1) range."
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
        # print(f"Warning: Option {option.description} trading near/below intrinsic value. Returning low default IV.")
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
        # print(f"Warning: Market price {target_price} > theoretical max price {price_at_high_vol} for {option.description}. Returning max IV.")
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
            print(
                f"Warning: BSM price calculation failed at IV={vol_mid}. Adjusting bounds."
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
    # print(f"IV calculation finished for {option.description}. IV: {final_iv:.4f}")
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
        print(
            f"Warning: Base volatility ({base_volatility}) is outside typical [0.01, 2.0] range."
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

    # print(f"Estimated IV for {option.description}: Base={base_volatility:.2f}, SkewF={skew_factor:.2f}, TermF={term_factor:.2f} => Final={final_iv:.3f}")
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
                # print(f"Attempting IV calculation from market price {option.current_price} for {option.description}")
                calculated_iv = calculate_implied_volatility(
                    option=option,  # Pass the whole object
                    underlying_price=underlying_price,
                    market_price=option.current_price,  # Explicitly pass market price
                    risk_free_rate=risk_free_rate,
                    # Use default precision/iterations from calculate_implied_volatility
                )

                # 2. Check if calculated IV is within the reasonable range
                if MIN_IV <= calculated_iv <= MAX_IV:
                    # print(f"Successfully calculated IV from market price: {calculated_iv:.4f}")
                    return calculated_iv
                else:
                    # Calculated IV was outside the expected range (e.g., due to price near intrinsic)
                    print(
                        f"Warning: Calculated IV ({calculated_iv:.4f}) for {option.description} is outside range [{MIN_IV}, {MAX_IV}]. Falling back to estimation."
                    )

            except ValueError as ve:
                print(
                    f"ValueError during IV calculation for {option.description}: {ve}. Falling back to estimation."
                )
            except RuntimeError as re:
                print(
                    f"RuntimeError during IV calculation for {option.description}: {re}. Falling back to estimation."
                )
            # Catch any other unexpected errors during calculation
            except Exception as iv_calc_err:
                print(
                    f"Unexpected error during IV calculation for {option.description}: {iv_calc_err}. Falling back to estimation."
                )
        else:
            # Market price not available or non-positive
            # print(f"Market price missing or non-positive for {option.description}. Falling back to IV estimation.")
            pass  # Proceed to estimation

        # 3. Fallback: Estimate IV using skew model
        # print(f"Estimating IV using skew model for {option.description}")
        estimated_iv = estimate_volatility_with_skew(
            option=option,
            underlying_price=underlying_price,
            base_volatility=DEFAULT_IV,  # Use the default as base for estimation
        )
        # print(f"Estimated IV: {estimated_iv:.4f}")
        return estimated_iv

    except Exception as e:
        # 4. Catch-all for errors in the estimation step or unexpected issues
        print(
            f"Error getting IV for {option.description}: {e}. Returning default IV {DEFAULT_IV}."
        )
        return DEFAULT_IV  # Return conservative default on any failure


def calculate_option_delta(
    option: OptionPosition,
    underlying_price: float,
    use_black_scholes: bool = True,
    risk_free_rate: float = 0.05,
    implied_volatility: float | None = None,  # Allow optional IV override
) -> float:
    """Calculates the option delta, offering a choice between Black-Scholes and a simple model.

    This function serves as a wrapper to compute delta using either:
    - The Black-Scholes-Merton model (`calculate_black_scholes_delta`): More accurate,
      accounts for time, volatility, and interest rates. Requires implied volatility.
    - A simple linear approximation (`calculate_simple_delta`): Less accurate, only considers
      moneyness. Does not require volatility or rates.

    If using Black-Scholes and `implied_volatility` is not provided, this function will
    attempt to obtain it using `get_implied_volatility` (which may calculate from market
    price or estimate using a skew model).

    Args:
        option: The `OptionPosition` object.
        underlying_price: The current market price of the underlying asset.
        use_black_scholes: If True (default), uses the BSM model. If False, uses the
                           simple approximation.
        risk_free_rate: The annualized risk-free interest rate (only used if `use_black_scholes`
                        is True). Defaults to 0.05 (5%).
        implied_volatility: Optional. If provided, this IV value is used directly for the
                            BSM calculation, overriding the value obtained by
                            `get_implied_volatility`. Defaults to None.

    Returns:
        The calculated delta value for the option position (between -1.0 and 1.0).

    Raises:
        Propagates exceptions from the underlying calculation functions (e.g., `ValueError`
        from `calculate_black_scholes_delta` if inputs are invalid).

    TODO:
        - Add logging for which model (BSM or simple) was used and the IV value employed.
    """
    if use_black_scholes:
        # print(f"Calculating BSM delta for {option.description}")
        # Determine the IV to use
        iv_to_use = implied_volatility  # Use provided IV if available
        if iv_to_use is None:
            # print(f"  IV not provided, calling get_implied_volatility...")
            iv_to_use = get_implied_volatility(option, underlying_price, risk_free_rate)
            # print(f"  Obtained IV: {iv_to_use:.4f}")
        elif not (0.001 <= iv_to_use <= 3.0):  # Basic sanity check on provided IV
            print(
                f"Warning: Provided IV ({iv_to_use}) for {option.description} seems unusual."
            )

        try:
            delta = calculate_black_scholes_delta(
                option, underlying_price, risk_free_rate, iv_to_use
            )
            # print(f"  BSM Delta calculated: {delta:.4f}")
            return delta
        except (ValueError, ZeroDivisionError, RuntimeError) as e:
            print(
                f"Error calculating BSM delta for {option.description}: {e}. Falling back to simple delta."
            )
            # Fallback to simple delta on BSM calculation error
            return calculate_simple_delta(option, underlying_price)
        except Exception as e:
            print(
                f"Unexpected error in BSM delta calculation for {option.description}: {e}. Falling back to simple delta."
            )
            return calculate_simple_delta(option, underlying_price)

    else:
        # print(f"Calculating simple delta for {option.description}")
        return calculate_simple_delta(option, underlying_price)


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
            print(
                f"Warning: Item in list is not an OptionPosition: {option}. Skipping."
            )
            continue
        # Use .setdefault() for cleaner dictionary population
        grouped.setdefault(option.underlying, []).append(option)
        # if option.underlying not in grouped:
        #     grouped[option.underlying] = []
        # grouped[option.underlying].append(option)
    return grouped


if __name__ == "__main__":
    # Example Usage and Testing
    print("--- Option Utils Testing ---")

    # --- Test OptionPosition ---
    try:
        test_option_pos = OptionPosition(
            underlying="XYZ",
            expiry=datetime(2025, 6, 20),
            strike=100.0,
            option_type="CALL",
            quantity=5,
            current_price=2.50,
            description="XYZ JUN 20 2025 $100 CALL",
        )
        print(f"Test OptionPosition: {test_option_pos}")
        print(f"  Is Short: {test_option_pos.is_short}")
        print(f"  Market Value: ${test_option_pos.market_value:,.2f}")
        print(f"  Notional Value: ${test_option_pos.notional_value:,.2f}")

        test_option_short = OptionPosition(
            underlying="XYZ",
            expiry=datetime(2025, 6, 20),
            strike=90.0,
            option_type="PUT",
            quantity=-10,
            current_price=1.50,
            description="XYZ JUN 20 2025 $90 PUT",
        )
        print(f"Test Short Option: {test_option_short}")
        print(f"  Is Short: {test_option_short.is_short}")
        print(f"  Market Value: ${test_option_short.market_value:,.2f}")
        print(f"  Notional Value: ${test_option_short.notional_value:,.2f}")
    except Exception as e:
        print(f"Error testing OptionPosition: {e}")

    # --- Test parse_month ---
    try:
        print(f"Parse 'APR': {parse_month('APR')}")
        # print(f"Parse 'XYZ': {parse_month('XYZ')}") # Should raise ValueError
    except ValueError as e:
        print(f"Error testing parse_month: {e}")

    # --- Test parse_option_description ---
    test_desc = "GOOGL MAY 16 2025 $170 CALL"
    try:
        parsed_option = parse_option_description(test_desc, -10, 2.75)
        print(f"Parsed Option Desc: {parsed_option}")
        # Test invalid format
        # parse_option_description("INVALID DESC", 1, 1.0)
        # parse_option_description("GOOGL MAY 16 2025 170 CALL", 1, 1.0) # Missing $
    except (ValueError, RuntimeError) as e:
        print(f"Error testing parse_option_description: {e}")

    # --- Test Delta Calculations (using parsed_option) ---
    underlying_price = 154.33  # Example GOOGL price
    if "parsed_option" in locals():
        try:
            simple_delta = calculate_simple_delta(parsed_option, underlying_price)
            print(f"Simple Delta ({parsed_option.description}): {simple_delta:.3f}")
            print(
                f"  Simple Delta Exposure: ${parsed_option.notional_value * simple_delta:,.2f}"
            )
        except Exception as e:
            print(f"Error calculating simple delta: {e}")

        # Test Black-Scholes delta
        try:
            # 1. Calculate IV first (will likely estimate as price is low)
            iv = get_implied_volatility(parsed_option, underlying_price)
            print(f"Implied Volatility for BSM Delta: {iv:.4f}")

            # 2. Calculate delta using the obtained IV
            bs_delta = calculate_black_scholes_delta(
                parsed_option, underlying_price, implied_volatility=iv
            )
            print(f"Black-Scholes Delta ({parsed_option.description}): {bs_delta:.4f}")
            print(
                f"  BSM Delta Exposure: ${parsed_option.notional_value * bs_delta:,.2f}"
            )

            # 3. Test the wrapper function calculate_option_delta
            wrapper_bs_delta = calculate_option_delta(
                parsed_option, underlying_price, use_black_scholes=True
            )
            print(f"Wrapper BSM Delta: {wrapper_bs_delta:.4f}")
            wrapper_simple_delta = calculate_option_delta(
                parsed_option, underlying_price, use_black_scholes=False
            )
            print(f"Wrapper Simple Delta: {wrapper_simple_delta:.3f}")

        except Exception as e:
            print(f"Error calculating BSM delta: {e}")

    # --- Test BSM Price Calculation ---
    try:
        call_option_price = OptionPosition(
            "TEST", datetime(2025, 1, 17), 100, "CALL", 1, 0, "Desc"
        )  # Price doesn't matter here
        bsm_price = calculate_bs_price(
            call_option_price,
            underlying_price=105,
            risk_free_rate=0.05,
            implied_volatility=0.25,
        )
        print(f"BSM Price (105 SP, 100C, 25% IV): ${bsm_price:,.2f}")
    except Exception as e:
        print(f"Error testing BSM price: {e}")

    # --- Test Grouping ---
    try:
        options_list = [
            OptionPosition("AAPL", datetime(2025, 1, 17), 200, "CALL", 2, 5.5, "D1"),
            OptionPosition("MSFT", datetime(2025, 1, 17), 400, "PUT", -3, 8.1, "D2"),
            OptionPosition("AAPL", datetime(2025, 3, 21), 210, "CALL", 1, 3.2, "D3"),
            "Not an option",  # Add invalid item
        ]
        grouped_opts = group_options_by_underlying(options_list)
        print("Grouped Options:")
        for underlying, opts in grouped_opts.items():
            print(f"  {underlying}: {[o.description for o in opts]}")
    except Exception as e:
        print(f"Error testing grouping: {e}")

    print("--- End Option Utils Testing ---")
    print(
        "\nFor more comprehensive testing, consider using pytest with dedicated test files."
    )
    # print("python -m pytest tests/test_option_delta.py -v")
