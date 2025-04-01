from datetime import datetime, timedelta

import pytest

from src.lab.option_utils import (
    OptionPosition,
    calculate_bs_price,
    calculate_implied_volatility,
    estimate_volatility_with_skew,
    get_implied_volatility,
)


@pytest.fixture
def sample_option():
    """Create a sample option object for testing."""
    future_date = datetime.now() + timedelta(days=90)  # 3 months from now

    return OptionPosition(
        underlying="TEST",
        expiry=future_date,
        strike=100.0,
        option_type="CALL",
        quantity=1,
        current_price=5.0,
        description="TEST 90-day CALL Option",
    )


def test_bs_price_calculation(sample_option):
    """Test that Black-Scholes price calculation is working properly."""
    # For ATM option, price should be positive
    price_atm = calculate_bs_price(sample_option, 100.0, 0.05, 0.3)
    assert price_atm > 0, "ATM option price should be positive"

    # For deep ITM call, price should be close to intrinsic value
    price_itm = calculate_bs_price(sample_option, 150.0, 0.05, 0.3)
    intrinsic_value = max(0, 150.0 - sample_option.strike)
    assert price_itm > intrinsic_value, "ITM option price should exceed intrinsic value"
    assert (
        price_itm - intrinsic_value < 15.0
    ), "ITM option premium over intrinsic value should be reasonable"


def test_implied_volatility_calculation(sample_option):
    """Test that implied volatility can be back-calculated from a known price."""
    # Create a price using known IV
    known_iv = 0.3  # 30%
    underlying_price = 100.0
    option_price = calculate_bs_price(sample_option, underlying_price, 0.05, known_iv)

    # Now calculate IV from the price
    calculated_iv = calculate_implied_volatility(
        sample_option, underlying_price, option_price, 0.05
    )

    # The calculated IV should be close to the original IV we used
    assert (
        abs(calculated_iv - known_iv) < 0.01
    ), "Calculated IV should be close to original IV"


def test_implied_volatility_bounds():
    """Test that implied volatility calculations stay within reasonable bounds."""
    # Create test options with different expirations
    current_date = datetime.now()
    short_term = current_date + timedelta(days=30)
    mid_term = current_date + timedelta(days=180)
    long_term = current_date + timedelta(days=365)

    options = [
        OptionPosition(
            "TEST", short_term, 100.0, "CALL", 1, 5.0, "TEST short-term CALL"
        ),
        OptionPosition("TEST", mid_term, 100.0, "CALL", 1, 10.0, "TEST mid-term CALL"),
        OptionPosition(
            "TEST", long_term, 100.0, "CALL", 1, 15.0, "TEST long-term CALL"
        ),
        OptionPosition("TEST", mid_term, 100.0, "PUT", 1, 10.0, "TEST mid-term PUT"),
    ]

    # Test with various option prices
    for option in options:
        for price_multiple in [0.5, 1.0, 2.0]:  # Test with different price levels
            option.current_price = option.current_price * price_multiple

            # Calculate IV for different underlying prices
            for underlying in [80.0, 100.0, 120.0]:
                iv = calculate_implied_volatility(option, underlying)

                # IV should be in a reasonable range
                assert (
                    0.0 <= iv <= 3.0
                ), f"IV should be between 0% and 300%, got {iv*100:.1f}%"


def test_volatility_skew_model(sample_option):
    """Test that volatility skew model applies expected adjustments."""
    base_volatility = 0.3  # 30%

    # For ATM options, should be close to base volatility
    atm_iv = estimate_volatility_with_skew(sample_option, 100.0, base_volatility)
    assert (
        abs(atm_iv - base_volatility) < 0.05
    ), "ATM IV should be close to base volatility"

    # OTM options should have higher IV (volatility smile)
    otm_iv = estimate_volatility_with_skew(sample_option, 80.0, base_volatility)
    assert otm_iv > base_volatility, "OTM options should have higher IV"

    # Change to PUT to test OTM puts
    sample_option.option_type = "PUT"
    otm_put_iv = estimate_volatility_with_skew(sample_option, 120.0, base_volatility)
    assert otm_put_iv > base_volatility, "OTM puts should have higher IV"


def test_integrated_iv_estimation():
    """Test the integrated implied volatility estimation function."""
    # Create test options
    current_date = datetime.now()
    test_date = current_date + timedelta(days=90)

    # Option with price - should use IV calculation
    option_with_price = OptionPosition(
        "TEST", test_date, 100.0, "CALL", 1, 8.0, "TEST option with price"
    )

    # Option without price - should use skew model
    option_without_price = OptionPosition(
        "TEST", test_date, 100.0, "CALL", 1, 0.0, "TEST option without price"
    )

    # Test IV estimation for both
    iv_with_price = get_implied_volatility(option_with_price, 100.0)
    iv_without_price = get_implied_volatility(option_without_price, 100.0)

    # Both should return reasonable values
    assert (
        0.1 <= iv_with_price <= 1.0
    ), f"IV for option with price should be reasonable, got {iv_with_price*100:.1f}%"
    assert (
        0.1 <= iv_without_price <= 1.0
    ), f"IV for option without price should be reasonable, got {iv_without_price*100:.1f}%"

    # They should typically be different
    assert (
        iv_with_price != iv_without_price
    ), "Different estimation methods should yield different results"
