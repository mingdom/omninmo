"""Tests for position details component."""

from dash import html

from src.folio.components.position_details import create_position_details
from src.folio.data_model import OptionPosition, PortfolioGroup, StockPosition


class TestPositionDetails:
    """Tests for position details component."""

    def test_create_position_details(self):
        """Test that position details can be created correctly."""
        # Create test positions
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            market_exposure=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0,
        )

        option_position = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_exposure=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=1050.0,
            notional_value=15000.0,
            underlying_beta=1.2,
        )

        # Create portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=stock_position,
            option_positions=[option_position],
            net_exposure=16500.0,
            beta=1.2,
            beta_adjusted_exposure=19800.0,
            total_delta_exposure=1050.0,
            options_delta_exposure=1050.0,
        )

        # Create position details
        details = create_position_details(portfolio_group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for stock, options, and combined metrics
        assert len(details.children[1].children) == 3

    def test_create_position_details_no_stock(self):
        """Test that position details can be created correctly without a stock position."""
        # Create test positions
        option_position = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_exposure=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=1050.0,
            notional_value=15000.0,
            underlying_beta=1.2,
        )

        # Create portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=None,
            option_positions=[option_position],
            net_exposure=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            total_delta_exposure=1050.0,
            options_delta_exposure=1050.0,
        )

        # Create position details
        details = create_position_details(portfolio_group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for options and combined metrics (no stock)
        assert len(details.children[1].children) == 2

    def test_create_position_details_no_options(self):
        """Test that position details can be created correctly without option positions."""
        # Create test positions
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            market_exposure=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0,
        )

        # Create portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=stock_position,
            option_positions=[],
            net_exposure=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0,
            total_delta_exposure=0.0,
            options_delta_exposure=0.0,
        )

        # Create position details
        details = create_position_details(portfolio_group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for stock and combined metrics (no options)
        assert len(details.children[1].children) == 2
