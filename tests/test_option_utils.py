"""Tests for the option utilities module.

This module tests the functionality in src/folio/option_utils.py for parsing option
descriptions and symbols, calculating option deltas, and other option-related utilities.
"""

from datetime import datetime

import pytest

from src.folio.option_utils import (
    OptionPosition,
    calculate_option_delta,
    parse_month,
    parse_option_description,
    parse_option_symbol,
)


class TestOptionParsing:
    """Tests for option parsing functionality."""

    def test_parse_month(self):
        """Test parsing month abbreviations."""
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

        # Test invalid month
        with pytest.raises(ValueError):
            parse_month("FOO")

    def test_parse_option_description(self):
        """Test parsing option descriptions."""
        # Test a call option
        call_option = parse_option_description("AAPL JAN 20 2023 $150 CALL", 10, 5.0)
        assert call_option.underlying == "AAPL"
        assert call_option.expiry == datetime(2023, 1, 20)
        assert call_option.strike == 150.0
        assert call_option.option_type == "CALL"
        assert call_option.quantity == 10
        assert call_option.current_price == 5.0
        assert call_option.description == "AAPL JAN 20 2023 $150 CALL"

        # Test a put option
        put_option = parse_option_description("SPY MAR 17 2023 $400 PUT", -5, 10.0)
        assert put_option.underlying == "SPY"
        assert put_option.expiry == datetime(2023, 3, 17)
        assert put_option.strike == 400.0
        assert put_option.option_type == "PUT"
        assert put_option.quantity == -5
        assert put_option.current_price == 10.0
        assert put_option.description == "SPY MAR 17 2023 $400 PUT"

        # Test invalid description format
        with pytest.raises(ValueError):
            parse_option_description("Invalid description", 1, 1.0)

    def test_parse_option_symbol(self):
        """Test parsing option symbols."""
        # Test a call option
        call_option = parse_option_symbol("AAPL230120C150", 10, 5.0)
        assert call_option.underlying == "AAPL"
        assert call_option.expiry == datetime(2023, 1, 20)
        assert call_option.strike == 150.0
        assert call_option.option_type == "CALL"
        assert call_option.quantity == 10
        assert call_option.current_price == 5.0
        assert call_option.description == "AAPL230120C150"

        # Test a put option with leading minus sign (short)
        put_option = parse_option_symbol("-SPY230317P400", -5, 10.0)
        assert put_option.underlying == "SPY"
        assert put_option.expiry == datetime(2023, 3, 17)
        assert put_option.strike == 400.0
        assert put_option.option_type == "PUT"
        assert put_option.quantity == -5
        assert put_option.current_price == 10.0
        assert put_option.description == "-SPY230317P400"

        # Test with custom description
        custom_desc_option = parse_option_symbol(
            "MSFT240621C400", 2, 15.0, "MSFT JUN 21 2024 $400 CALL"
        )
        assert custom_desc_option.underlying == "MSFT"
        assert custom_desc_option.expiry == datetime(2024, 6, 21)
        assert custom_desc_option.strike == 400.0
        assert custom_desc_option.option_type == "CALL"
        assert custom_desc_option.quantity == 2
        assert custom_desc_option.current_price == 15.0
        assert custom_desc_option.description == "MSFT JUN 21 2024 $400 CALL"

        # Test with strike price that includes decimal point (e.g., 132.5)
        decimal_strike_option = parse_option_symbol("AMAT250516P1325", 3, 7.5)
        assert decimal_strike_option.underlying == "AMAT"
        assert decimal_strike_option.expiry == datetime(2025, 5, 16)
        assert (
            decimal_strike_option.strike == 13.25
        )  # 1325 is parsed as 13.25 (decimal point 2 places from end)
        assert decimal_strike_option.option_type == "PUT"
        assert decimal_strike_option.quantity == 3
        assert decimal_strike_option.current_price == 7.5

        # Test invalid symbol format
        with pytest.raises(ValueError):
            parse_option_symbol("Invalid-Symbol", 1, 1.0)

        # Test missing date part
        with pytest.raises(ValueError):
            parse_option_symbol("AAPLC150", 1, 1.0)

        # Test missing option type
        with pytest.raises(ValueError):
            parse_option_symbol("AAPL230120150", 1, 1.0)

        # Test invalid date
        with pytest.raises(ValueError):
            parse_option_symbol("AAPL999999C150", 1, 1.0)


class TestOptionCalculations:
    """Tests for option calculation functionality."""

    def test_option_position_properties(self):
        """Test the properties of the OptionPosition class."""
        # Long call option
        long_call = OptionPosition(
            underlying="AAPL",
            expiry=datetime(2023, 1, 20),
            strike=150.0,
            option_type="CALL",
            quantity=10,
            current_price=5.0,
            description="AAPL JAN 20 2023 $150 CALL",
        )
        assert long_call.notional_value == 150000.0  # 10 contracts * 100 shares * $150
        assert long_call.market_value == 5000.0  # 10 contracts * 100 shares * $5
        assert not long_call.is_short

        # Short put option
        short_put = OptionPosition(
            underlying="SPY",
            expiry=datetime(2023, 3, 17),
            strike=400.0,
            option_type="PUT",
            quantity=-5,
            current_price=10.0,
            description="SPY MAR 17 2023 $400 PUT",
        )
        assert short_put.notional_value == 200000.0  # 5 contracts * 100 shares * $400
        assert short_put.market_value == -5000.0  # -5 contracts * 100 shares * $10
        assert short_put.is_short

    def test_calculate_option_delta(self):
        """Test calculating option delta."""
        # Create a test option
        call_option = OptionPosition(
            underlying="AAPL",
            expiry=datetime.now().replace(
                year=datetime.now().year + 1
            ),  # 1 year from now
            strike=150.0,
            option_type="CALL",
            quantity=1,
            current_price=5.0,
            description="AAPL CALL",
        )

        # Calculate delta with Black-Scholes
        delta = calculate_option_delta(
            call_option,
            underlying_price=150.0,  # At the money
            use_black_scholes=True,
            risk_free_rate=0.05,
            implied_volatility=0.3,
        )

        # For an at-the-money call with 1 year to expiry, delta should be around 0.5-0.65
        # (exact value depends on volatility and time to expiry)
        assert 0.45 <= delta <= 0.65

        # Test put option delta
        put_option = OptionPosition(
            underlying="AAPL",
            expiry=datetime.now().replace(
                year=datetime.now().year + 1
            ),  # 1 year from now
            strike=150.0,
            option_type="PUT",
            quantity=1,
            current_price=5.0,
            description="AAPL PUT",
        )

        # Calculate delta with Black-Scholes
        put_delta = calculate_option_delta(
            put_option,
            underlying_price=150.0,  # At the money
            use_black_scholes=True,
            risk_free_rate=0.05,
            implied_volatility=0.3,
        )

        # For an at-the-money put with 1 year to expiry, delta should be around -0.35 to -0.55
        # (exact value depends on volatility and time to expiry)
        assert -0.55 <= put_delta <= -0.35

        # Test short option delta (should be negated)
        short_call_option = OptionPosition(
            underlying="AAPL",
            expiry=datetime.now().replace(
                year=datetime.now().year + 1
            ),  # 1 year from now
            strike=150.0,
            option_type="CALL",
            quantity=-1,  # Short
            current_price=5.0,
            description="AAPL CALL",
        )

        # Calculate delta with Black-Scholes
        short_delta = calculate_option_delta(
            short_call_option,
            underlying_price=150.0,  # At the money
            use_black_scholes=True,
            risk_free_rate=0.05,
            implied_volatility=0.3,
        )

        # For a short at-the-money call with 1 year to expiry, delta should be around -0.5 to -0.65
        # (exact value depends on volatility and time to expiry)
        assert -0.65 <= short_delta <= -0.45
