"""Comprehensive tests for option utilities.

This module provides extensive tests for the option utilities in src/folio/option_utils.py,
focusing on the calculation of option deltas, notional values, and exposures.
"""

import math
from datetime import datetime, timedelta

import pytest
from scipy.stats import norm

from src.folio.option_utils import (
    OptionPosition,
    calculate_black_scholes_delta,
    calculate_option_delta,
    group_options_by_underlying,
    parse_month,
    parse_option_description,
)


@pytest.fixture
def option_fixtures():
    """Create a set of option fixtures for testing."""
    current_date = datetime.now()
    future_date_short = current_date + timedelta(days=30)  # 1 month
    future_date_medium = current_date + timedelta(days=180)  # 6 months
    future_date_long = current_date + timedelta(days=365)  # 1 year

    # Create a variety of options with different strikes, types, and quantities
    return {
        # At-the-money options
        "long_call_atm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=100.0,
            option_type="CALL",
            quantity=2,
            current_price=5.0,
            description="TEST JUN 15 2025 $100 CALL",
        ),
        "short_call_atm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=100.0,
            option_type="CALL",
            quantity=-2,
            current_price=5.0,
            description="TEST JUN 15 2025 $100 CALL",
        ),
        "long_put_atm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=100.0,
            option_type="PUT",
            quantity=2,
            current_price=5.0,
            description="TEST JUN 15 2025 $100 PUT",
        ),
        "short_put_atm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=100.0,
            option_type="PUT",
            quantity=-2,
            current_price=5.0,
            description="TEST JUN 15 2025 $100 PUT",
        ),
        # In-the-money options
        "long_call_itm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=80.0,
            option_type="CALL",
            quantity=2,
            current_price=25.0,
            description="TEST JUN 15 2025 $80 CALL",
        ),
        "short_call_itm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=80.0,
            option_type="CALL",
            quantity=-2,
            current_price=25.0,
            description="TEST JUN 15 2025 $80 CALL",
        ),
        "long_put_itm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=120.0,
            option_type="PUT",
            quantity=2,
            current_price=25.0,
            description="TEST JUN 15 2025 $120 PUT",
        ),
        "short_put_itm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=120.0,
            option_type="PUT",
            quantity=-2,
            current_price=25.0,
            description="TEST JUN 15 2025 $120 PUT",
        ),
        # Out-of-the-money options
        "long_call_otm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=120.0,
            option_type="CALL",
            quantity=2,
            current_price=2.0,
            description="TEST JUN 15 2025 $120 CALL",
        ),
        "short_call_otm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=120.0,
            option_type="CALL",
            quantity=-2,
            current_price=2.0,
            description="TEST JUN 15 2025 $120 CALL",
        ),
        "long_put_otm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=80.0,
            option_type="PUT",
            quantity=2,
            current_price=2.0,
            description="TEST JUN 15 2025 $80 PUT",
        ),
        "short_put_otm": OptionPosition(
            underlying="TEST",
            expiry=future_date_medium,
            strike=80.0,
            option_type="PUT",
            quantity=-2,
            current_price=2.0,
            description="TEST JUN 15 2025 $80 PUT",
        ),
        # Different expiration dates
        "long_call_short_term": OptionPosition(
            underlying="TEST",
            expiry=future_date_short,
            strike=100.0,
            option_type="CALL",
            quantity=2,
            current_price=3.0,
            description="TEST MAY 15 2025 $100 CALL",
        ),
        "long_call_long_term": OptionPosition(
            underlying="TEST",
            expiry=future_date_long,
            strike=100.0,
            option_type="CALL",
            quantity=2,
            current_price=8.0,
            description="TEST APR 15 2026 $100 CALL",
        ),
    }


def test_parse_month():
    """Test the parse_month function."""
    # Test all valid month abbreviations
    assert parse_month("JAN") == 1
    assert parse_month("FEB") == 2
    assert parse_month("MAR") == 3
    assert parse_month("APR") == 4
    assert parse_month("MAY") == 5
    assert parse_month("JUN") == 6
    assert parse_month("JUL") == 7
    assert parse_month("AUG") == 8
    assert parse_month("SEP") == 9
    assert parse_month("OCT") == 10
    assert parse_month("NOV") == 11
    assert parse_month("DEC") == 12

    # Test case insensitivity
    assert parse_month("jan") == 1
    assert parse_month("Feb") == 2
    assert parse_month("mAr") == 3

    # Test invalid month abbreviation
    with pytest.raises(ValueError):
        parse_month("FOO")


def test_parse_option_description():
    """Test the parse_option_description function."""
    # Test valid option descriptions
    option = parse_option_description("AAPL JAN 20 2025 $150 CALL", 1, 5.0)
    assert option.underlying == "AAPL"
    assert option.expiry.month == 1
    assert option.expiry.day == 20
    assert option.expiry.year == 2025
    assert option.strike == 150.0
    assert option.option_type == "CALL"
    assert option.quantity == 1
    assert option.current_price == 5.0
    assert option.description == "AAPL JAN 20 2025 $150 CALL"

    # Test with negative quantity (short position)
    option = parse_option_description("AAPL JAN 20 2025 $150 PUT", -2, 3.0)
    assert option.underlying == "AAPL"
    assert option.option_type == "PUT"
    assert option.quantity == -2
    assert option.current_price == 3.0

    # Test invalid option descriptions
    with pytest.raises(ValueError):
        # Not enough parts
        parse_option_description("AAPL JAN 20 2025 $150", 1, 5.0)

    with pytest.raises(ValueError):
        # Invalid month
        parse_option_description("AAPL FOO 20 2025 $150 CALL", 1, 5.0)

    with pytest.raises(ValueError):
        # Invalid day
        parse_option_description("AAPL JAN XX 2025 $150 CALL", 1, 5.0)

    with pytest.raises(ValueError):
        # Invalid year
        parse_option_description("AAPL JAN 20 XXXX $150 CALL", 1, 5.0)

    with pytest.raises(ValueError):
        # Invalid strike (missing $)
        parse_option_description("AAPL JAN 20 2025 150 CALL", 1, 5.0)

    with pytest.raises(ValueError):
        # Invalid option type
        parse_option_description("AAPL JAN 20 2025 $150 XXX", 1, 5.0)


def test_option_position_properties(option_fixtures):
    """Test the properties of the OptionPosition class."""
    # Test notional_value property
    long_call = option_fixtures["long_call_atm"]
    assert long_call.notional_value == 100.0 * 100 * 2  # strike * 100 * quantity
    assert long_call.notional_value > 0  # Always positive

    short_call = option_fixtures["short_call_atm"]
    assert short_call.notional_value == 100.0 * 100 * 2  # strike * 100 * abs(quantity)
    assert short_call.notional_value > 0  # Always positive

    # Test signed_notional_value property
    assert long_call.signed_notional_value == 100.0 * 100 * 2  # Positive for long
    assert short_call.signed_notional_value == 100.0 * 100 * (-2)  # Negative for short

    # Test market_value property
    assert long_call.market_value == 5.0 * 100 * 2  # price * 100 * quantity
    assert short_call.market_value == 5.0 * 100 * (-2)  # Negative for short


def test_delta_calculation_for_calls(option_fixtures):
    """Test delta calculation for call options."""
    underlying_price = 100.0
    iv = 0.3  # 30% implied volatility

    # Test ATM call deltas
    long_call_atm = option_fixtures["long_call_atm"]
    short_call_atm = option_fixtures["short_call_atm"]

    long_call_delta = calculate_option_delta(
        long_call_atm, underlying_price, implied_volatility=iv
    )
    short_call_delta = calculate_option_delta(
        short_call_atm, underlying_price, implied_volatility=iv
    )

    # ATM call delta should be around 0.5-0.6 for 6-month options
    assert 0.45 <= abs(long_call_delta) <= 0.65
    # Short call delta should be approximately negative of long call delta
    assert abs(long_call_delta + short_call_delta) < 1e-8

    # Test ITM call deltas
    long_call_itm = option_fixtures["long_call_itm"]
    short_call_itm = option_fixtures["short_call_itm"]

    long_call_itm_delta = calculate_option_delta(
        long_call_itm, underlying_price, implied_volatility=iv
    )
    short_call_itm_delta = calculate_option_delta(
        short_call_itm, underlying_price, implied_volatility=iv
    )

    # ITM call delta should be > 0.5
    assert 0.7 <= abs(long_call_itm_delta) <= 0.95
    # Short call delta should be approximately negative of long call delta
    assert abs(long_call_itm_delta + short_call_itm_delta) < 1e-8

    # Test OTM call deltas
    long_call_otm = option_fixtures["long_call_otm"]
    short_call_otm = option_fixtures["short_call_otm"]

    long_call_otm_delta = calculate_option_delta(
        long_call_otm, underlying_price, implied_volatility=iv
    )
    short_call_otm_delta = calculate_option_delta(
        short_call_otm, underlying_price, implied_volatility=iv
    )

    # OTM call delta should be < 0.5
    assert 0.05 <= abs(long_call_otm_delta) <= 0.3
    # Short call delta should be approximately negative of long call delta
    assert abs(long_call_otm_delta + short_call_otm_delta) < 1e-8


def test_delta_calculation_for_puts(option_fixtures):
    """Test delta calculation for put options."""
    underlying_price = 100.0
    iv = 0.3  # 30% implied volatility

    # Test ATM put deltas
    long_put_atm = option_fixtures["long_put_atm"]
    short_put_atm = option_fixtures["short_put_atm"]

    long_put_delta = calculate_option_delta(
        long_put_atm, underlying_price, implied_volatility=iv
    )
    short_put_delta = calculate_option_delta(
        short_put_atm, underlying_price, implied_volatility=iv
    )

    # ATM put delta should be around -0.4 to -0.5 for 6-month options
    assert -0.55 <= long_put_delta <= -0.35
    # Short put delta should be approximately negative of long put delta
    assert abs(long_put_delta + short_put_delta) < 1e-8

    # Test ITM put deltas
    long_put_itm = option_fixtures["long_put_itm"]
    short_put_itm = option_fixtures["short_put_itm"]

    long_put_itm_delta = calculate_option_delta(
        long_put_itm, underlying_price, implied_volatility=iv
    )
    short_put_itm_delta = calculate_option_delta(
        short_put_itm, underlying_price, implied_volatility=iv
    )

    # ITM put delta should be < -0.5
    assert -0.95 <= long_put_itm_delta <= -0.7
    # Short put delta should be approximately negative of long put delta
    assert abs(long_put_itm_delta + short_put_itm_delta) < 1e-8

    # Test OTM put deltas
    long_put_otm = option_fixtures["long_put_otm"]
    short_put_otm = option_fixtures["short_put_otm"]

    long_put_otm_delta = calculate_option_delta(
        long_put_otm, underlying_price, implied_volatility=iv
    )
    short_put_otm_delta = calculate_option_delta(
        short_put_otm, underlying_price, implied_volatility=iv
    )

    # OTM put delta should be > -0.5
    assert -0.3 <= long_put_otm_delta <= -0.05
    # Short put delta should be approximately negative of long put delta
    assert abs(long_put_otm_delta + short_put_otm_delta) < 1e-8


def test_delta_exposure_calculation(option_fixtures):
    """Test the calculation of delta exposure."""
    underlying_price = 100.0
    iv = 0.3  # 30% implied volatility

    # Test for long call
    long_call = option_fixtures["long_call_atm"]
    long_call_delta = calculate_option_delta(
        long_call, underlying_price, implied_volatility=iv
    )

    # Calculate delta exposure
    # Delta exposure = delta * notional_value
    expected_long_call_exposure = long_call_delta * long_call.notional_value

    # Test for short call
    short_call = option_fixtures["short_call_atm"]
    short_call_delta = calculate_option_delta(
        short_call, underlying_price, implied_volatility=iv
    )

    # Calculate delta exposure
    # Delta exposure = delta * notional_value
    expected_short_call_exposure = short_call_delta * short_call.notional_value

    # Verify that long call and short call exposures have opposite signs
    assert expected_long_call_exposure > 0, "Long call exposure should be positive"
    assert expected_short_call_exposure < 0, "Short call exposure should be negative"

    # Test for long put
    long_put = option_fixtures["long_put_atm"]
    long_put_delta = calculate_option_delta(
        long_put, underlying_price, implied_volatility=iv
    )

    # Calculate delta exposure
    # Delta exposure = delta * notional_value
    expected_long_put_exposure = long_put_delta * long_put.notional_value

    # Test for short put
    short_put = option_fixtures["short_put_atm"]
    short_put_delta = calculate_option_delta(
        short_put, underlying_price, implied_volatility=iv
    )

    # Calculate delta exposure
    # Delta exposure = delta * notional_value
    expected_short_put_exposure = short_put_delta * short_put.notional_value

    # Verify that long put and short put exposures have opposite signs
    assert expected_long_put_exposure < 0, "Long put exposure should be negative"
    assert expected_short_put_exposure > 0, "Short put exposure should be positive"

    # Verify that the absolute values of the exposures are proportional to the quantity
    # Use a small epsilon for floating-point comparison
    assert (
        abs(abs(expected_long_call_exposure) - abs(expected_short_call_exposure)) < 1e-8
    )
    assert (
        abs(abs(expected_long_put_exposure) - abs(expected_short_put_exposure)) < 1e-8
    )


def test_delta_exposure_with_signed_notional(option_fixtures):
    """Test the calculation of delta exposure using signed notional value."""
    underlying_price = 100.0
    iv = 0.3  # 30% implied volatility

    # Test for long call
    long_call = option_fixtures["long_call_atm"]
    long_call_delta_unsigned = calculate_black_scholes_delta(
        long_call, underlying_price, implied_volatility=iv
    )
    # For a long call, the delta is positive and the signed notional is positive
    # So the exposure should be positive
    expected_long_call_exposure = (
        long_call_delta_unsigned * long_call.signed_notional_value
    )

    # Test for short call
    short_call = option_fixtures["short_call_atm"]
    short_call_delta_unsigned = calculate_black_scholes_delta(
        short_call, underlying_price, implied_volatility=iv
    )
    # For a short call, the delta is negative and the signed notional is negative
    # So the exposure should be positive (double negative)
    expected_short_call_exposure = (
        short_call_delta_unsigned * short_call.signed_notional_value
    )

    # This test will fail if the delta calculation doesn't correctly account for short positions
    # The issue is that calculate_black_scholes_delta already adjusts the delta for short positions,
    # so multiplying by signed_notional_value would double-count the sign
    assert expected_long_call_exposure > 0, "Long call exposure should be positive"
    assert expected_short_call_exposure < 0, "Short call exposure should be negative"


def test_group_options_by_underlying(option_fixtures):
    """Test the group_options_by_underlying function."""
    options = list(option_fixtures.values())

    # Group options by underlying
    grouped = group_options_by_underlying(options)

    # All options have the same underlying in our fixtures
    assert len(grouped) == 1
    assert "TEST" in grouped
    assert len(grouped["TEST"]) == len(options)

    # Test with mixed underlyings
    mixed_options = [
        OptionPosition(
            underlying="AAPL",
            expiry=datetime.now() + timedelta(days=30),
            strike=150.0,
            option_type="CALL",
            quantity=1,
            current_price=5.0,
            description="AAPL MAY 15 2025 $150 CALL",
        ),
        OptionPosition(
            underlying="MSFT",
            expiry=datetime.now() + timedelta(days=30),
            strike=300.0,
            option_type="PUT",
            quantity=2,
            current_price=10.0,
            description="MSFT MAY 15 2025 $300 PUT",
        ),
        OptionPosition(
            underlying="AAPL",
            expiry=datetime.now() + timedelta(days=60),
            strike=160.0,
            option_type="PUT",
            quantity=-1,
            current_price=7.0,
            description="AAPL JUN 15 2025 $160 PUT",
        ),
    ]

    grouped_mixed = group_options_by_underlying(mixed_options)
    assert len(grouped_mixed) == 2
    assert "AAPL" in grouped_mixed
    assert "MSFT" in grouped_mixed
    assert len(grouped_mixed["AAPL"]) == 2
    assert len(grouped_mixed["MSFT"]) == 1


def test_delta_calculation_near_expiry():
    """Test delta calculation for options near expiry."""
    # Create options that are about to expire
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=1)  # 1 day to expiry

    # ATM call about to expire
    atm_call = OptionPosition(
        underlying="TEST",
        expiry=expiry_date,
        strike=100.0,
        option_type="CALL",
        quantity=1,
        current_price=1.0,
        description="TEST APR 16 2025 $100 CALL",
    )

    # ITM call about to expire
    itm_call = OptionPosition(
        underlying="TEST",
        expiry=expiry_date,
        strike=90.0,
        option_type="CALL",
        quantity=1,
        current_price=10.0,
        description="TEST APR 16 2025 $90 CALL",
    )

    # OTM call about to expire
    otm_call = OptionPosition(
        underlying="TEST",
        expiry=expiry_date,
        strike=110.0,
        option_type="CALL",
        quantity=1,
        current_price=0.1,
        description="TEST APR 16 2025 $110 CALL",
    )

    # Calculate deltas
    underlying_price = 100.0
    iv = 0.3

    atm_delta = calculate_option_delta(
        atm_call, underlying_price, implied_volatility=iv
    )
    itm_delta = calculate_option_delta(
        itm_call, underlying_price, implied_volatility=iv
    )
    otm_delta = calculate_option_delta(
        otm_call, underlying_price, implied_volatility=iv
    )

    # For options near expiry:
    # - ATM options should have delta close to 0.5
    # - ITM options should have delta close to 1.0
    # - OTM options should have delta close to 0.0
    assert 0.45 <= atm_delta <= 0.55, (
        "ATM call near expiry should have delta around 0.5"
    )
    assert itm_delta > 0.9, "ITM call near expiry should have delta close to 1.0"
    assert otm_delta < 0.1, "OTM call near expiry should have delta close to 0.0"


def test_delta_exposure_with_different_calculation_methods(option_fixtures):
    """Test different methods of calculating delta exposure."""
    underlying_price = 100.0
    iv = 0.3

    # Get a long call option
    long_call = option_fixtures["long_call_atm"]

    # Method 1: Using calculate_option_delta (which already adjusts for short positions)
    delta1 = calculate_option_delta(long_call, underlying_price, implied_volatility=iv)
    exposure1 = delta1 * long_call.notional_value

    # Method 2: Using calculate_black_scholes_delta directly
    delta2 = calculate_black_scholes_delta(
        long_call, underlying_price, risk_free_rate=0.05, implied_volatility=iv
    )
    exposure2 = delta2 * long_call.notional_value

    # Method 3: Using signed_notional_value with calculate_black_scholes_delta
    # This is problematic because calculate_black_scholes_delta already adjusts for short positions
    delta3 = calculate_black_scholes_delta(
        long_call, underlying_price, risk_free_rate=0.05, implied_volatility=iv
    )
    exposure3 = delta3 * long_call.signed_notional_value

    # Method 4: Using the raw delta (before adjusting for short positions) with signed_notional_value
    # This would be the correct approach if we want to use signed_notional_value
    if long_call.option_type == "CALL":
        raw_delta = norm.cdf(
            (math.log(underlying_price / long_call.strike) + (0.05 + 0.5 * iv**2) * 0.5)
            / (iv * math.sqrt(0.5))
        )
    else:  # PUT
        raw_delta = (
            norm.cdf(
                (
                    math.log(underlying_price / long_call.strike)
                    + (0.05 + 0.5 * iv**2) * 0.5
                )
                / (iv * math.sqrt(0.5))
            )
            - 1
        )
    exposure4 = raw_delta * long_call.signed_notional_value

    # Methods 1 and 2 should give the same result
    assert abs(exposure1 - exposure2) < 1e-8, (
        "Methods 1 and 2 should give the same result"
    )

    # Method 3 should give the same result as methods 1 and 2 for long positions
    # But for short positions, it would double-count the sign
    assert abs(exposure1 - exposure3) < 1e-8, (
        "Method 3 should give the same result as methods 1 and 2 for long positions"
    )

    # Method 4 should give approximately the same result as methods 1 and 2
    # There might be significant differences due to how we calculate d1 and time_to_expiry
    # The important thing is that the sign is correct and the magnitude is in the same ballpark
    assert abs(exposure1 - exposure4) < 20.0, (
        "Method 4 should give approximately the same result as methods 1 and 2"
    )

    # Now test with a short call
    short_call = option_fixtures["short_call_atm"]

    # Method 1: Using calculate_option_delta (which already adjusts for short positions)
    delta1 = calculate_option_delta(short_call, underlying_price, implied_volatility=iv)
    exposure1 = delta1 * short_call.notional_value

    # Method 2: Using calculate_black_scholes_delta directly with adjustment for position direction
    raw_delta2 = calculate_black_scholes_delta(
        short_call, underlying_price, risk_free_rate=0.05, implied_volatility=iv
    )
    delta2 = raw_delta2 if short_call.quantity >= 0 else -raw_delta2
    exposure2 = delta2 * short_call.notional_value

    # Method 3: Using signed_notional_value with calculate_black_scholes_delta
    # This is problematic because calculate_black_scholes_delta already adjusts for short positions
    delta3 = calculate_black_scholes_delta(
        short_call, underlying_price, risk_free_rate=0.05, implied_volatility=iv
    )
    exposure3 = delta3 * short_call.signed_notional_value

    # Method 4: Using the raw delta (before adjusting for short positions) with signed_notional_value
    # This would be the correct approach if we want to use signed_notional_value
    if short_call.option_type == "CALL":
        raw_delta = norm.cdf(
            (
                math.log(underlying_price / short_call.strike)
                + (0.05 + 0.5 * iv**2) * 0.5
            )
            / (iv * math.sqrt(0.5))
        )
    else:  # PUT
        raw_delta = (
            norm.cdf(
                (
                    math.log(underlying_price / short_call.strike)
                    + (0.05 + 0.5 * iv**2) * 0.5
                )
                / (iv * math.sqrt(0.5))
            )
            - 1
        )
    exposure4 = raw_delta * short_call.signed_notional_value

    # Methods 1 and 2 should give the same result
    assert abs(exposure1 - exposure2) < 1e-8, (
        "Methods 1 and 2 should give the same result for short call"
    )

    # Method 3 should give the same result as methods 1 and 2 for short positions
    # This is because calculate_black_scholes_delta no longer adjusts for short positions
    assert abs(exposure1 - exposure3) < 1e-8, (
        "Method 3 should give the same result as methods 1 and 2 for short positions"
    )

    # Method 4 should give approximately the same result as methods 1 and 2
    # There might be significant differences due to how we calculate d1 and time_to_expiry
    # The important thing is that the sign is correct and the magnitude is in the same ballpark
    assert abs(exposure1 - exposure4) < 20.0, (
        "Method 4 should give approximately the same result as methods 1 and 2 for short call"
    )
