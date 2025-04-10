"""Tests for price recalculation consistency.

This module tests that recalculating portfolio metrics with the same prices
produces the same results, ensuring consistency in the calculation logic.
"""

import copy
from datetime import datetime, timedelta

from src.folio.data_model import OptionPosition, PortfolioGroup, StockPosition
from src.folio.portfolio import (
    recalculate_group_metrics,
    recalculate_option_metrics,
    update_portfolio_prices,
)


class TestPriceRecalculation:
    """Tests for price recalculation consistency."""

    def test_same_price_recalculation(self):
        """Test that recalculating with the same prices produces the same results."""
        # Create a test portfolio with a stock and an option
        expiry_date = datetime.now() + timedelta(days=30)

        # Create a stock position
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            beta=1.2,
            market_exposure=15000.0,  # 100 shares * $150
            beta_adjusted_exposure=18000.0,  # $15000 * 1.2
            price=150.0,
        )

        # Create an option position (AAPL call)
        option_position = OptionPosition(
            ticker="AAPL230616C00160000",
            position_type="option",
            quantity=1,
            beta=1.2,
            market_exposure=500.0,
            beta_adjusted_exposure=9600.0,  # 8000.0 * 1.2
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="CALL",
            delta=0.5,
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
            stock_position=stock_position,
            option_positions=[option_position],
            net_exposure=23000.0,  # $15000 (stock) + $8000 (option delta)
            beta=1.2,
            beta_adjusted_exposure=27600.0,  # $18000 (stock) + $9600 (option)
            total_delta_exposure=8000.0,
            options_delta_exposure=8000.0,
        )

        # Make a deep copy of the original group for comparison
        original_group = copy.deepcopy(portfolio_group)

        # Create a mock data fetcher that returns the same prices
        class MockDataFetcher:
            def fetch_data(self, ticker, period=None):  # noqa: ARG002 - period is unused but required by the interface
                import pandas as pd

                # Return the same prices as the original positions
                if ticker == "AAPL":
                    return pd.DataFrame({"Close": [150.0]})
                elif ticker == "AAPL230616C00160000":
                    return pd.DataFrame({"Close": [5.0]})
                return pd.DataFrame()

        # Update prices with the mock data fetcher (same prices)
        update_portfolio_prices([portfolio_group], MockDataFetcher())

        # Compare the original and updated groups
        # Stock position should be unchanged
        assert (
            portfolio_group.stock_position.price == original_group.stock_position.price
        )
        assert (
            portfolio_group.stock_position.market_exposure
            == original_group.stock_position.market_exposure
        )
        assert (
            portfolio_group.stock_position.beta_adjusted_exposure
            == original_group.stock_position.beta_adjusted_exposure
        )

        # Option position should be unchanged
        assert (
            portfolio_group.option_positions[0].price
            == original_group.option_positions[0].price
        )
        assert (
            portfolio_group.option_positions[0].delta
            == original_group.option_positions[0].delta
        )
        assert (
            portfolio_group.option_positions[0].notional_value
            == original_group.option_positions[0].notional_value
        )
        assert (
            portfolio_group.option_positions[0].delta_exposure
            == original_group.option_positions[0].delta_exposure
        )
        assert (
            portfolio_group.option_positions[0].beta_adjusted_exposure
            == original_group.option_positions[0].beta_adjusted_exposure
        )

        # Group metrics should be unchanged
        assert portfolio_group.net_exposure == original_group.net_exposure
        assert (
            portfolio_group.beta_adjusted_exposure
            == original_group.beta_adjusted_exposure
        )
        assert (
            portfolio_group.total_delta_exposure == original_group.total_delta_exposure
        )
        assert (
            portfolio_group.options_delta_exposure
            == original_group.options_delta_exposure
        )

    def test_option_metrics_recalculation(self):
        """Test that recalculating option metrics with the same prices produces the same results."""
        # Create a test option position
        expiry_date = datetime.now() + timedelta(days=30)
        option_position = OptionPosition(
            ticker="AAPL230616C00160000",
            position_type="option",
            quantity=1,
            beta=1.2,
            market_exposure=500.0,
            beta_adjusted_exposure=9600.0,  # 8000.0 * 1.2
            strike=160.0,
            expiry=expiry_date.isoformat(),
            option_type="CALL",
            delta=0.5,
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

        # Make a deep copy of the original option for comparison
        original_option = copy.deepcopy(option_position)

        # Create a dictionary of latest prices (same as original)
        latest_prices = {"AAPL": 150.0, "AAPL230616C00160000": 5.0}

        # Recalculate option metrics
        recalculate_option_metrics(option_position, portfolio_group, latest_prices)

        # Compare the original and recalculated option
        assert option_position.price == original_option.price
        assert option_position.delta == original_option.delta
        assert option_position.notional_value == original_option.notional_value
        assert option_position.delta_exposure == original_option.delta_exposure
        assert (
            option_position.beta_adjusted_exposure
            == original_option.beta_adjusted_exposure
        )

        # Recalculate group metrics
        recalculate_group_metrics(portfolio_group)

        # Group metrics should be unchanged
        assert portfolio_group.net_exposure == 8000.0
        assert portfolio_group.beta_adjusted_exposure == 9600.0
        assert portfolio_group.total_delta_exposure == 8000.0
        assert portfolio_group.options_delta_exposure == 8000.0
