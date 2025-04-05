"""Tests for position details component in the UI flow."""

from dash import html

from src.folio.components.position_details import create_position_details
from src.folio.data_model import OptionPosition, PortfolioGroup, StockPosition


def create_portfolio_group_from_data(position_data):
    """Helper function to create a PortfolioGroup from position data"""
    stock_position = None
    if position_data["stock_position"]:
        stock_position_data = position_data["stock_position"].copy()
        # Remove attributes that don't exist in Position class
        if "sector" in stock_position_data:
            stock_position_data.pop("sector")
        if "is_cash_like" in stock_position_data:
            stock_position_data.pop("is_cash_like")
        stock_position = StockPosition(**stock_position_data)

    option_positions = [
        OptionPosition(**opt) for opt in position_data["option_positions"]
    ]

    return PortfolioGroup(
        ticker=position_data["ticker"],
        stock_position=stock_position,
        option_positions=option_positions,
        net_exposure=position_data["net_exposure"],
        beta=position_data["beta"],
        beta_adjusted_exposure=position_data["beta_adjusted_exposure"],
        total_delta_exposure=position_data["total_delta_exposure"],
        options_delta_exposure=position_data["options_delta_exposure"],
    )


class TestPositionDetailsUI:
    """Tests for position details component in the UI flow."""

    def test_create_position_details_from_data(self):
        """Test that position details can be created correctly from position data."""
        # Create position data as it would be stored in the UI
        position_data = {
            "ticker": "AAPL",
            "stock_position": {
                "ticker": "AAPL",
                "quantity": 100,
                "market_exposure": 15000.0,
                "beta": 1.2,
                "beta_adjusted_exposure": 18000.0,
            },
            "option_positions": [
                {
                    "ticker": "AAPL",
                    "position_type": "option",
                    "quantity": 10,
                    "market_exposure": 1500.0,
                    "beta": 1.2,
                    "beta_adjusted_exposure": 1800.0,
                    "strike": 150.0,
                    "expiry": "2023-01-01",
                    "option_type": "CALL",
                    "delta": 0.7,
                    "delta_exposure": 1050.0,
                    "notional_value": 15000.0,
                    "underlying_beta": 1.2,
                }
            ],
            "net_exposure": 16500.0,
            "beta": 1.2,
            "beta_adjusted_exposure": 19800.0,
            "total_delta_exposure": 1050.0,
            "options_delta_exposure": 1050.0,
        }

        # Create portfolio group from position data
        group = create_portfolio_group_from_data(position_data)

        # Create position details
        details = create_position_details(group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for stock, options, and combined metrics
        assert len(details.children[1].children) == 3

    def test_create_position_details_from_data_no_stock(self):
        """Test that position details can be created correctly from position data without a stock position."""
        # Create position data as it would be stored in the UI
        position_data = {
            "ticker": "AAPL",
            "stock_position": None,
            "option_positions": [
                {
                    "ticker": "AAPL",
                    "position_type": "option",
                    "quantity": 10,
                    "market_exposure": 1500.0,
                    "beta": 1.2,
                    "beta_adjusted_exposure": 1800.0,
                    "strike": 150.0,
                    "expiry": "2023-01-01",
                    "option_type": "CALL",
                    "delta": 0.7,
                    "delta_exposure": 1050.0,
                    "notional_value": 15000.0,
                    "underlying_beta": 1.2,
                }
            ],
            "net_exposure": 1500.0,
            "beta": 1.2,
            "beta_adjusted_exposure": 1800.0,
            "total_delta_exposure": 1050.0,
            "options_delta_exposure": 1050.0,
        }

        # Create portfolio group from position data
        group = create_portfolio_group_from_data(position_data)

        # Create position details
        details = create_position_details(group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for options and combined metrics (no stock)
        assert len(details.children[1].children) == 2

    def test_create_position_details_from_data_no_options(self):
        """Test that position details can be created correctly from position data without option positions."""
        # Create position data as it would be stored in the UI
        position_data = {
            "ticker": "AAPL",
            "stock_position": {
                "ticker": "AAPL",
                "quantity": 100,
                "market_exposure": 15000.0,
                "beta": 1.2,
                "beta_adjusted_exposure": 18000.0,
            },
            "option_positions": [],
            "net_exposure": 15000.0,
            "beta": 1.2,
            "beta_adjusted_exposure": 18000.0,
            "total_delta_exposure": 0.0,
            "options_delta_exposure": 0.0,
        }

        # Create portfolio group from position data
        group = create_portfolio_group_from_data(position_data)

        # Create position details
        details = create_position_details(group)

        # Verify that details is a Dash component
        assert isinstance(details, html.Div)

        # Verify that the ticker is in the title
        assert "AAPL" in details.children[0].children

        # Verify that there are sections for stock and combined metrics (no options)
        assert len(details.children[1].children) == 2
