from datetime import datetime, timedelta

import pytest

from src.lab.option_utils import (
    OptionPosition,
    calculate_black_scholes_delta,
    calculate_option_delta,
    calculate_simple_delta,
    parse_option_description,
)


@pytest.fixture
def sample_options():
    """Create sample option objects for testing."""
    # Create a date in the future for option expiry
    future_date = datetime.now() + timedelta(days=365)  # One year from now

    # Sample calls and puts with various moneyness levels
    return {
        "atm_call": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=100.0,
            option_type="CALL",
            quantity=1,
            current_price=5.0,
            description="AAPL Test ATM Call",
        ),
        "itm_call": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=80.0,
            option_type="CALL",
            quantity=1,
            current_price=25.0,
            description="AAPL Test ITM Call",
        ),
        "otm_call": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=120.0,
            option_type="CALL",
            quantity=1,
            current_price=1.0,
            description="AAPL Test OTM Call",
        ),
        "atm_put": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=100.0,
            option_type="PUT",
            quantity=1,
            current_price=5.0,
            description="AAPL Test ATM Put",
        ),
        "itm_put": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=120.0,
            option_type="PUT",
            quantity=1,
            current_price=25.0,
            description="AAPL Test ITM Put",
        ),
        "otm_put": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=80.0,
            option_type="PUT",
            quantity=1,
            current_price=1.0,
            description="AAPL Test OTM Put",
        ),
        "short_call": OptionPosition(
            underlying="AAPL",
            expiry=future_date,
            strike=100.0,
            option_type="CALL",
            quantity=-1,
            current_price=5.0,
            description="AAPL Test Short Call",
        ),
    }


@pytest.fixture
def real_option_samples():
    """Create option samples from real portfolio data."""
    return [
        # symbol, description, qty, price, und_price
        ("AAPL", "AAPL APR 17 2025 $220 CALL", -1, 4.83, 217.90),
        ("AMZN", "AMZN APR 17 2025 $200 CALL", -12, 2.92, 192.72),
        ("AMZN", "AMZN MAY 16 2025 $200 PUT", -5, 13.90, 192.72),
        ("GOOGL", "GOOGL MAY 16 2025 $170 CALL", -10, 2.75, 154.33),
        ("GOOGL", "GOOGL MAY 16 2025 $150 PUT", -5, 6.00, 154.33),
        ("TSM", "TSM APR 17 2025 $190 CALL", -4, 0.87, 165.25),
        ("VRT", "VRT MAY 16 2025 $75 PUT", -2, 8.40, 74.25),
    ]


def test_bs_delta_is_bounded():
    """Test that Black-Scholes delta is bounded between -1 and 1."""
    # Create test option with arbitrary values
    current_date = datetime.now()
    future_date = current_date + timedelta(days=365)

    call_option = OptionPosition(
        underlying="TEST",
        expiry=future_date,
        strike=100.0,
        option_type="CALL",
        quantity=1,
        current_price=5.0,
        description="Test Call",
    )

    put_option = OptionPosition(
        underlying="TEST",
        expiry=future_date,
        strike=100.0,
        option_type="PUT",
        quantity=1,
        current_price=5.0,
        description="Test Put",
    )

    # Test with various prices and volatilities
    for price in [50.0, 100.0, 150.0]:
        for vol in [0.1, 0.3, 0.5, 0.8]:
            call_delta = calculate_black_scholes_delta(call_option, price, 0.05, vol)
            put_delta = calculate_black_scholes_delta(put_option, price, 0.05, vol)

            # Check bounds for call option
            assert -1.0 <= call_delta <= 1.0, f"Call delta {call_delta} outside bounds"

            # Check bounds for put option
            assert -1.0 <= put_delta <= 1.0, f"Put delta {put_delta} outside bounds"


def test_bs_delta_equals_1_for_deep_itm_call():
    """Test that deep in-the-money calls have delta approaching 1."""
    # Create a deep ITM call option expiring very soon
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=30)  # One month from now

    deep_itm_call = OptionPosition(
        underlying="TEST",
        expiry=expiry_date,
        strike=50.0,
        option_type="CALL",
        quantity=1,
        current_price=50.0,
        description="Deep ITM Call",
    )

    # Test with a price far above strike
    delta = calculate_black_scholes_delta(deep_itm_call, 100.0, 0.05, 0.3)

    # Delta should be very close to 1
    assert delta > 0.95, f"Deep ITM call delta {delta} should be close to 1"


def test_bs_delta_near_0_for_deep_otm_call():
    """Test that deep out-of-the-money calls have delta approaching 0."""
    # Create a deep OTM call option expiring very soon
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=30)  # One month from now

    deep_otm_call = OptionPosition(
        underlying="TEST",
        expiry=expiry_date,
        strike=200.0,
        option_type="CALL",
        quantity=1,
        current_price=0.1,
        description="Deep OTM Call",
    )

    # Test with a price far below strike
    delta = calculate_black_scholes_delta(deep_otm_call, 100.0, 0.05, 0.3)

    # Delta should be very close to 0
    assert delta < 0.05, f"Deep OTM call delta {delta} should be close to 0"


def test_bs_delta_negated_for_short_options(sample_options):
    """Test that delta is negated for short options."""
    current_price = 100.0

    # Test with long call
    long_call_delta = calculate_black_scholes_delta(
        sample_options["atm_call"], current_price
    )

    # Test with short call
    short_call_delta = calculate_black_scholes_delta(
        sample_options["short_call"], current_price
    )

    # Short delta should be negative of long delta
    assert (
        abs(long_call_delta + short_call_delta) < 1e-10
    ), "Short option delta should be negative of long option delta"


def test_bs_delta_put_call_parity(sample_options):
    """Test that put-call parity holds for delta."""
    current_price = 100.0

    # Get deltas for ATM call and put
    call_delta = calculate_black_scholes_delta(
        sample_options["atm_call"], current_price
    )
    put_delta = calculate_black_scholes_delta(sample_options["atm_put"], current_price)

    # For options with same strike, put delta should be call delta - 1
    assert (
        abs((call_delta - 1) - put_delta) < 1e-10
    ), "Put-call parity not satisfied for delta"


def test_bs_delta_vs_simple_delta_real_options(real_option_samples):
    """Compare Black-Scholes and simple delta for real options from portfolio."""
    # Test each real option and collect results
    results = []

    for symbol, desc, qty, price, und_price in real_option_samples:
        option = parse_option_description(desc, qty, price)

        simple_delta = calculate_simple_delta(option, und_price)
        bs_delta = calculate_black_scholes_delta(option, und_price)

        # Store results for assertion
        results.append(
            {
                "symbol": symbol,
                "description": desc,
                "simple_delta": simple_delta,
                "bs_delta": bs_delta,
                "difference": bs_delta - simple_delta,
            }
        )

        # Choose one assertion per option type for test validation
        if "CALL" in desc and symbol == "GOOGL":
            assert abs(bs_delta) < abs(
                simple_delta
            ), "BS delta for OTM call should be smaller than simple delta"
        elif "PUT" in desc and symbol == "AMZN":
            assert abs(bs_delta) != abs(
                simple_delta
            ), "BS and simple delta should differ for AMZN put"

    # Verify we have results
    assert len(results) > 0, "No results collected from real option samples"


def test_delta_calculator_interface():
    """Test the calculate_option_delta interface works correctly."""
    # Create a test option
    current_date = datetime.now()
    future_date = current_date + timedelta(days=180)

    test_option = OptionPosition(
        underlying="TEST",
        expiry=future_date,
        strike=100.0,
        option_type="CALL",
        quantity=1,
        current_price=5.0,
        description="Test Call",
    )

    # Using Black-Scholes
    bs_delta = calculate_option_delta(
        test_option,
        100.0,
        use_black_scholes=True,
        risk_free_rate=0.05,
        implied_volatility=0.3,
    )

    # Using simple delta
    simple_delta = calculate_option_delta(test_option, 100.0, use_black_scholes=False)

    # Using default (should be Black-Scholes)
    default_delta = calculate_option_delta(test_option, 100.0)

    # Verify behavior - use approximate equality for floating point
    assert (
        abs(bs_delta - default_delta) < 1e-10
    ), "Default delta should use Black-Scholes"
    assert (
        abs(bs_delta - simple_delta) > 1e-10
    ), "Black-Scholes and simple delta should be different"
