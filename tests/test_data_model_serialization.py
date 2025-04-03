"""Tests for data model serialization and deserialization."""

from src.folio.data_model import (
    ExposureBreakdown,
    OptionPosition,
    PortfolioGroup,
    PortfolioSummary,
    StockPosition,
)


class TestDataModelSerialization:
    """Tests for data model serialization and deserialization."""

    def test_stock_position_serialization(self):
        """Test StockPosition serialization and deserialization."""
        # Create a test stock position
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            market_value=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0
        )

        # Serialize to dict
        stock_dict = stock_position.to_dict()

        # Deserialize back to object
        stock_restored = StockPosition.from_dict(stock_dict)

        # Verify key attributes
        assert stock_restored.ticker == stock_position.ticker
        assert stock_restored.quantity == stock_position.quantity
        assert stock_restored.market_value == stock_position.market_value
        assert stock_restored.beta == stock_position.beta
        assert stock_restored.beta_adjusted_exposure == stock_position.beta_adjusted_exposure

    def test_option_position_serialization(self):
        """Test OptionPosition serialization and deserialization."""
        # Create a test option position
        option_position = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_value=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            clean_value=1500.0,
            weight=0.1,
            position_beta=1.2,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=1050.0,
            notional_value=15000.0,
            underlying_beta=1.2
        )

        # Serialize to dict
        option_dict = option_position.to_dict()

        # Deserialize back to object
        option_restored = OptionPosition.from_dict(option_dict)

        # Verify key attributes
        assert option_restored.ticker == option_position.ticker
        assert option_restored.position_type == option_position.position_type
        assert option_restored.quantity == option_position.quantity
        assert option_restored.market_value == option_position.market_value
        assert option_restored.beta == option_position.beta
        assert option_restored.strike == option_position.strike
        assert option_restored.expiry == option_position.expiry
        assert option_restored.option_type == option_position.option_type
        assert option_restored.delta == option_position.delta
        assert option_restored.delta_exposure == option_position.delta_exposure
        assert option_restored.notional_value == option_position.notional_value

    def test_portfolio_group_serialization(self):
        """Test PortfolioGroup serialization and deserialization."""
        # Create test positions
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            market_value=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0
        )

        option_position = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_value=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            clean_value=1500.0,
            weight=0.1,
            position_beta=1.2,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=1050.0,
            notional_value=15000.0,
            underlying_beta=1.2
        )

        # Create portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=stock_position,
            option_positions=[option_position],
            total_value=16500.0,
            net_exposure=16500.0,
            beta=1.2,
            beta_adjusted_exposure=19800.0,
            total_delta_exposure=1050.0,
            options_delta_exposure=1050.0
        )

        # Serialize to dict
        group_dict = portfolio_group.to_dict()

        # Deserialize back to object
        group_restored = PortfolioGroup.from_dict(group_dict)

        # Verify key attributes
        assert group_restored.ticker == portfolio_group.ticker
        assert group_restored.total_value == portfolio_group.total_value
        assert group_restored.net_exposure == portfolio_group.net_exposure
        assert group_restored.beta == portfolio_group.beta
        assert group_restored.beta_adjusted_exposure == portfolio_group.beta_adjusted_exposure
        assert group_restored.total_delta_exposure == portfolio_group.total_delta_exposure
        assert group_restored.options_delta_exposure == portfolio_group.options_delta_exposure

        # Verify stock position
        assert group_restored.stock_position is not None
        assert group_restored.stock_position.ticker == portfolio_group.stock_position.ticker
        assert group_restored.stock_position.quantity == portfolio_group.stock_position.quantity

        # Verify option positions
        assert len(group_restored.option_positions) == len(portfolio_group.option_positions)
        assert group_restored.option_positions[0].ticker == portfolio_group.option_positions[0].ticker
        assert group_restored.option_positions[0].strike == portfolio_group.option_positions[0].strike

    def test_exposure_breakdown_serialization(self):
        """Test ExposureBreakdown serialization and deserialization."""
        # Create test exposure breakdown
        exposure = ExposureBreakdown(
            stock_value=15000.0,
            stock_beta_adjusted=18000.0,
            option_delta_value=1050.0,
            option_beta_adjusted=1260.0,
            total_value=16050.0,
            total_beta_adjusted=19260.0,
            description="Test Exposure",
            formula="Stock + Options",
            components={"stock": 15000.0, "options": 1050.0}
        )

        # Serialize to dict
        exposure_dict = exposure.to_dict()

        # Deserialize back to object
        exposure_restored = ExposureBreakdown.from_dict(exposure_dict)

        # Verify key attributes
        assert exposure_restored.stock_value == exposure.stock_value
        assert exposure_restored.stock_beta_adjusted == exposure.stock_beta_adjusted
        assert exposure_restored.option_delta_value == exposure.option_delta_value
        assert exposure_restored.option_beta_adjusted == exposure.option_beta_adjusted
        assert exposure_restored.total_value == exposure.total_value
        assert exposure_restored.total_beta_adjusted == exposure.total_beta_adjusted
        assert exposure_restored.description == exposure.description
        assert exposure_restored.formula == exposure.formula
        assert exposure_restored.components == exposure.components

    def test_portfolio_summary_serialization(self):
        """Test PortfolioSummary serialization and deserialization."""
        # Create test exposure breakdowns
        exposure = ExposureBreakdown(
            stock_value=15000.0,
            stock_beta_adjusted=18000.0,
            option_delta_value=1050.0,
            option_beta_adjusted=1260.0,
            total_value=16050.0,
            total_beta_adjusted=19260.0,
            description="Test Exposure",
            formula="Stock + Options",
            components={"stock": 15000.0, "options": 1050.0}
        )

        # Create test cash-like position
        cash_position = StockPosition(
            ticker="SPAXX",
            quantity=1,
            market_value=5000.0,
            beta=0.0,
            beta_adjusted_exposure=0.0
        )

        # Create portfolio summary
        summary = PortfolioSummary(
            total_value_net=21050.0,
            total_value_abs=21050.0,
            portfolio_beta=0.91,
            long_exposure=exposure,
            short_exposure=exposure,
            options_exposure=exposure,
            short_percentage=0.0,
            exposure_reduction_percentage=0.0,
            cash_like_positions=[cash_position],
            cash_like_value=5000.0,
            cash_like_count=1
        )

        # Serialize to dict
        summary_dict = summary.to_dict()

        # Deserialize back to object
        summary_restored = PortfolioSummary.from_dict(summary_dict)

        # Verify key attributes
        assert summary_restored.total_value_net == summary.total_value_net
        assert summary_restored.total_value_abs == summary.total_value_abs
        assert summary_restored.portfolio_beta == summary.portfolio_beta
        assert summary_restored.short_percentage == summary.short_percentage
        assert summary_restored.exposure_reduction_percentage == summary.exposure_reduction_percentage
        assert summary_restored.cash_like_value == summary.cash_like_value
        assert summary_restored.cash_like_count == summary.cash_like_count

        # Verify exposure breakdowns
        assert summary_restored.long_exposure.total_value == summary.long_exposure.total_value
        assert summary_restored.short_exposure.total_value == summary.short_exposure.total_value
        assert summary_restored.options_exposure.total_value == summary.options_exposure.total_value

        # Verify cash-like positions
        assert len(summary_restored.cash_like_positions) == len(summary.cash_like_positions)
        assert summary_restored.cash_like_positions[0].ticker == summary.cash_like_positions[0].ticker
        assert summary_restored.cash_like_positions[0].market_value == summary.cash_like_positions[0].market_value

    def test_complete_serialization_cycle(self):
        """Test a complete serialization cycle with nested objects."""
        # Create test positions
        stock_position = StockPosition(
            ticker="AAPL",
            quantity=100,
            market_value=15000.0,
            beta=1.2,
            beta_adjusted_exposure=18000.0
        )

        option_position = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_value=1500.0,
            beta=1.2,
            beta_adjusted_exposure=1800.0,
            clean_value=1500.0,
            weight=0.1,
            position_beta=1.2,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=1050.0,
            notional_value=15000.0,
            underlying_beta=1.2
        )

        # Create portfolio group
        portfolio_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=stock_position,
            option_positions=[option_position],
            total_value=16500.0,
            net_exposure=16500.0,
            beta=1.2,
            beta_adjusted_exposure=19800.0,
            total_delta_exposure=1050.0,
            options_delta_exposure=1050.0
        )

        # Create test exposure breakdowns
        exposure = ExposureBreakdown(
            stock_value=15000.0,
            stock_beta_adjusted=18000.0,
            option_delta_value=1050.0,
            option_beta_adjusted=1260.0,
            total_value=16050.0,
            total_beta_adjusted=19260.0,
            description="Test Exposure",
            formula="Stock + Options",
            components={"stock": 15000.0, "options": 1050.0}
        )

        # Create portfolio summary
        summary = PortfolioSummary(
            total_value_net=16500.0,
            total_value_abs=16500.0,
            portfolio_beta=1.2,
            long_exposure=exposure,
            short_exposure=exposure,
            options_exposure=exposure,
            short_percentage=0.0,
            exposure_reduction_percentage=0.0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0
        )

        # Convert to dictionary format as would be stored in Dash
        groups_data = [portfolio_group.to_dict()]
        summary_data = summary.to_dict()

        # Deserialize back to objects
        restored_groups = [PortfolioGroup.from_dict(g) for g in groups_data]
        restored_summary = PortfolioSummary.from_dict(summary_data)

        # Verify key attributes
        assert len(restored_groups) == 1
        assert restored_groups[0].ticker == "AAPL"
        assert restored_groups[0].total_value == 16500.0
        assert restored_summary.total_value_net == 16500.0
        assert restored_summary.portfolio_beta == 1.2
