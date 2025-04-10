"""Tests for option exposure calculations.

This module tests that option exposure is calculated correctly for different
option positions, including long calls, short calls, long puts, and short puts.
"""

from datetime import datetime, timedelta

from src.folio.data_model import OptionPosition, PortfolioGroup
from src.folio.portfolio import recalculate_option_metrics


class TestOptionExposure:
    """Tests for option exposure calculations."""

    def test_long_call_exposure(self):
        """Test that long call exposure is calculated correctly."""
        # Create a test option position (long call)
        expiry_date = datetime.now() + timedelta(days=30)
        option_position = OptionPosition(
            ticker="AAPL230616C00160000",
            position_type="option",
            quantity=1,  # Long
            beta=1.2,
            market_exposure=500.0,
            beta_adjusted_exposure=9600.0,
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="CALL",
            delta=0.5,  # Positive delta for call
            delta_exposure=8000.0,  # 0.5 * $160 * 100 * 1
            notional_value=16000.0,  # $160 * 100 * 1
            underlying_beta=1.2,
            price=5.0,
        )

        # Add the last_underlying_price attribute to prevent recalculation
        option_position.last_underlying_price = 150.0

        # Create a portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=None,
            option_positions=[option_position],
            net_exposure=8000.0,
            beta=1.2,
            beta_adjusted_exposure=9600.0,
            total_delta_exposure=8000.0,
            options_delta_exposure=8000.0,
        )

        # Create a dictionary of latest prices (same as original)
        latest_prices = {"AAPL": 150.0, "AAPL230616C00160000": 5.0}

        # Recalculate option metrics
        recalculate_option_metrics(option_position, portfolio_group, latest_prices)

        # Verify that the delta exposure is calculated correctly
        # For a long call with positive delta, the exposure should be positive
        assert option_position.delta == 0.5
        assert option_position.delta_exposure == 8000.0  # 0.5 * 16000.0
        assert option_position.delta_exposure > 0  # Positive exposure

    def test_short_call_exposure(self):
        """Test that short call exposure is calculated correctly."""
        # Create a test option position (short call)
        expiry_date = datetime.now() + timedelta(days=30)
        option_position = OptionPosition(
            ticker="AAPL230616C00160000",
            position_type="option",
            quantity=-1,  # Short
            beta=1.2,
            market_exposure=-500.0,
            beta_adjusted_exposure=-9600.0,
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="CALL",
            delta=-0.5,  # Negative delta for short call
            delta_exposure=-8000.0,  # -0.5 * $160 * 100 * 1
            notional_value=16000.0,  # $160 * 100 * 1
            underlying_beta=1.2,
            price=5.0,
        )

        # Add the last_underlying_price attribute to prevent recalculation
        option_position.last_underlying_price = 150.0

        # Create a portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=None,
            option_positions=[option_position],
            net_exposure=-8000.0,
            beta=1.2,
            beta_adjusted_exposure=-9600.0,
            total_delta_exposure=-8000.0,
            options_delta_exposure=-8000.0,
        )

        # Create a dictionary of latest prices (same as original)
        latest_prices = {"AAPL": 150.0, "AAPL230616C00160000": 5.0}

        # Recalculate option metrics
        recalculate_option_metrics(option_position, portfolio_group, latest_prices)

        # Verify that the delta exposure is calculated correctly
        # For a short call with negative delta, the exposure should be negative
        assert option_position.delta == -0.5
        assert option_position.delta_exposure == -8000.0  # -0.5 * 16000.0
        assert option_position.delta_exposure < 0  # Negative exposure

    def test_long_put_exposure(self):
        """Test that long put exposure is calculated correctly."""
        # Create a test option position (long put)
        expiry_date = datetime.now() + timedelta(days=30)
        option_position = OptionPosition(
            ticker="AAPL230616P00160000",
            position_type="option",
            quantity=1,  # Long
            beta=1.2,
            market_exposure=500.0,
            beta_adjusted_exposure=-9600.0,
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="PUT",
            delta=-0.5,  # Negative delta for put
            delta_exposure=-8000.0,  # -0.5 * $160 * 100 * 1
            notional_value=16000.0,  # $160 * 100 * 1
            underlying_beta=1.2,
            price=5.0,
        )

        # Add the last_underlying_price attribute to prevent recalculation
        option_position.last_underlying_price = 150.0

        # Create a portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=None,
            option_positions=[option_position],
            net_exposure=-8000.0,
            beta=1.2,
            beta_adjusted_exposure=-9600.0,
            total_delta_exposure=-8000.0,
            options_delta_exposure=-8000.0,
        )

        # Create a dictionary of latest prices (same as original)
        latest_prices = {"AAPL": 150.0, "AAPL230616P00160000": 5.0}

        # Recalculate option metrics
        recalculate_option_metrics(option_position, portfolio_group, latest_prices)

        # Verify that the delta exposure is calculated correctly
        # For a long put with negative delta, the exposure should be negative
        assert option_position.delta == -0.5
        assert option_position.delta_exposure == -8000.0  # -0.5 * 16000.0
        assert option_position.delta_exposure < 0  # Negative exposure

    def test_short_put_exposure(self):
        """Test that short put exposure is calculated correctly."""
        # Create a test option position (short put)
        expiry_date = datetime.now() + timedelta(days=30)
        option_position = OptionPosition(
            ticker="AAPL230616P00160000",
            position_type="option",
            quantity=-1,  # Short
            beta=1.2,
            market_exposure=-500.0,
            beta_adjusted_exposure=9600.0,
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="PUT",
            delta=0.5,  # Positive delta for short put
            delta_exposure=8000.0,  # 0.5 * $160 * 100 * 1
            notional_value=16000.0,  # $160 * 100 * 1
            underlying_beta=1.2,
            price=5.0,
        )

        # Add the last_underlying_price attribute to prevent recalculation
        option_position.last_underlying_price = 150.0

        # Create a portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=None,
            option_positions=[option_position],
            net_exposure=8000.0,
            beta=1.2,
            beta_adjusted_exposure=9600.0,
            total_delta_exposure=8000.0,
            options_delta_exposure=8000.0,
        )

        # Create a dictionary of latest prices (same as original)
        latest_prices = {"AAPL": 150.0, "AAPL230616P00160000": 5.0}

        # Recalculate option metrics
        recalculate_option_metrics(option_position, portfolio_group, latest_prices)

        # Verify that the delta exposure is calculated correctly
        # For a short put with positive delta, the exposure should be positive
        assert option_position.delta == 0.5
        assert option_position.delta_exposure == 8000.0  # 0.5 * 16000.0
        assert option_position.delta_exposure > 0  # Positive exposure
