"""Tests for the portfolio_value module."""

import pytest

from src.folio.data_model import (
    ExposureBreakdown,
    OptionPosition,
    PortfolioGroup,
    PortfolioSummary,
    StockPosition,
)
from src.folio.portfolio_value import (
    calculate_component_percentages,
    calculate_portfolio_metrics,
    calculate_portfolio_values,
    create_value_breakdowns,
    get_portfolio_component_values,
    process_option_positions,
    process_stock_positions,
)


def create_test_portfolio_summary():
    """Create a test portfolio summary for testing."""
    # Create exposure breakdowns
    long_exposure = ExposureBreakdown(
        stock_exposure=10000.0,
        stock_beta_adjusted=12000.0,
        option_delta_exposure=2000.0,
        option_beta_adjusted=2400.0,
        total_exposure=12000.0,
        total_beta_adjusted=14400.0,
        description="Long market value (Stocks + Options)",
        formula="Long Stocks + Long Options",
        components={
            "Long Stocks Value": 10000.0,
            "Long Options Value": 2000.0,
        },
    )

    short_exposure = ExposureBreakdown(
        stock_exposure=-5000.0,  # Negative value
        stock_beta_adjusted=-6000.0,
        option_delta_exposure=-1000.0,  # Negative value
        option_beta_adjusted=-1200.0,
        total_exposure=-6000.0,
        total_beta_adjusted=-7200.0,
        description="Short market value (Stocks + Options)",
        formula="Short Stocks + Short Options",
        components={
            "Short Stocks Value": -5000.0,  # Negative value
            "Short Options Value": -1000.0,  # Negative value
        },
    )

    options_exposure = ExposureBreakdown(
        stock_exposure=0.0,
        stock_beta_adjusted=0.0,
        option_delta_exposure=1000.0,
        option_beta_adjusted=1200.0,
        total_exposure=1000.0,
        total_beta_adjusted=1200.0,
        description="Net market value from options",
        formula="Long Options Value + Short Options Value (where Short is negative)",
        components={
            "Long Options Value": 2000.0,
            "Short Options Value": -1000.0,  # Negative value
            "Net Options Value": 1000.0,
        },
    )

    # Create portfolio summary
    return PortfolioSummary(
        net_market_exposure=6000.0,
        portfolio_beta=1.2,
        long_exposure=long_exposure,
        short_exposure=short_exposure,
        options_exposure=options_exposure,
        short_percentage=50.0,
        cash_like_positions=[],
        cash_like_value=3000.0,
        cash_like_count=1,
        cash_percentage=20.0,
        stock_value=5000.0,
        option_value=1000.0,
        pending_activity_value=500.0,
        portfolio_estimate_value=15000.0,
    )


def create_test_portfolio_groups():
    """Create test portfolio groups for testing."""
    # Create a long stock position
    long_stock = StockPosition(
        ticker="AAPL",
        quantity=100,
        beta=1.2,
        market_exposure=10000.0,
        beta_adjusted_exposure=12000.0,
        price=100.0,
        cost_basis=90.0,
        market_value=10000.0,
    )

    # Create a short stock position
    short_stock = StockPosition(
        ticker="MSFT",
        quantity=-50,
        beta=1.0,
        market_exposure=-5000.0,  # Negative value
        beta_adjusted_exposure=-5000.0,  # Negative value
        price=100.0,
        cost_basis=110.0,
        market_value=-5000.0,  # Negative value
    )

    # Create a long call option position
    long_call = OptionPosition(
        ticker="AAPL",
        position_type="option",
        quantity=10,
        beta=1.2,
        beta_adjusted_exposure=1200.0,
        market_exposure=1000.0,
        strike=150.0,
        expiry="2022-01-21",
        option_type="CALL",
        delta=0.5,
        delta_exposure=1000.0,
        notional_value=15000.0,
        underlying_beta=1.2,
        price=10.0,
        cost_basis=8.0,
        market_value=1000.0,
    )

    # Create a short put option position
    short_put = OptionPosition(
        ticker="MSFT",
        position_type="option",
        quantity=-5,
        beta=1.0,
        beta_adjusted_exposure=-500.0,  # Negative value
        market_exposure=-500.0,  # Negative value
        strike=90.0,
        expiry="2022-01-21",
        option_type="PUT",
        delta=-0.2,
        delta_exposure=-500.0,  # Negative value
        notional_value=4500.0,
        underlying_beta=1.0,
        price=10.0,
        cost_basis=12.0,
        market_value=-500.0,  # Negative value
    )

    # Create portfolio groups
    long_group = PortfolioGroup(
        ticker="AAPL",
        stock_position=long_stock,
        option_positions=[long_call],
        net_exposure=11000.0,
        beta_adjusted_exposure=13200.0,
        options_delta_exposure=1000.0,
        total_delta_exposure=1000.0,
        beta=1.2,
    )
    # Set call_count and put_count after initialization
    long_group.call_count = 1
    long_group.put_count = 0

    short_group = PortfolioGroup(
        ticker="MSFT",
        stock_position=short_stock,
        option_positions=[short_put],
        net_exposure=-5500.0,  # Negative value
        beta_adjusted_exposure=-5500.0,  # Negative value
        options_delta_exposure=-500.0,  # Negative value
        total_delta_exposure=-500.0,  # Negative value
        beta=1.0,
    )
    # Set call_count and put_count after initialization
    short_group.call_count = 0
    short_group.put_count = 1

    return [long_group, short_group]


def test_process_stock_positions():
    """Test that stock positions are correctly processed into long and short components."""
    # Create test portfolio groups
    groups = create_test_portfolio_groups()

    # Process stock positions
    long_stocks, short_stocks = process_stock_positions(groups)

    # Verify that long stocks are processed correctly
    assert long_stocks["value"] == 10000.0
    assert long_stocks["beta_adjusted"] == 12000.0

    # Verify that short stocks are processed correctly and remain negative
    assert short_stocks["value"] == -5000.0  # Negative value
    assert short_stocks["beta_adjusted"] == -5000.0  # Negative value


def test_process_option_positions():
    """Test that option positions are correctly processed into long and short components."""
    # Create test portfolio groups
    groups = create_test_portfolio_groups()

    # Process option positions
    long_options, short_options = process_option_positions(groups)

    # Verify that long options are processed correctly
    assert long_options["value"] == 1000.0
    assert long_options["beta_adjusted"] == 1200.0

    # Verify that short options are processed correctly and remain negative
    assert short_options["value"] == -500.0  # Negative value
    assert short_options["beta_adjusted"] == -500.0  # Negative value


def test_create_value_breakdowns():
    """Test that value breakdowns are correctly created from position data."""
    # Create test data
    long_stocks = {"value": 10000.0, "beta_adjusted": 12000.0}
    short_stocks = {"value": -5000.0, "beta_adjusted": -5000.0}  # Negative values
    long_options = {"value": 2000.0, "beta_adjusted": 2400.0}
    short_options = {"value": -1000.0, "beta_adjusted": -1200.0}  # Negative values

    # Create value breakdowns
    long_value, short_value, options_value = create_value_breakdowns(
        long_stocks, short_stocks, long_options, short_options
    )

    # Verify that long value breakdown is correct
    assert long_value.stock_exposure == 10000.0
    assert long_value.stock_beta_adjusted == 12000.0
    assert long_value.option_delta_exposure == 2000.0
    assert long_value.option_beta_adjusted == 2400.0
    assert long_value.total_exposure == 12000.0
    assert long_value.total_beta_adjusted == 14400.0
    assert long_value.components["Long Stocks Value"] == 10000.0
    assert long_value.components["Long Options Value"] == 2000.0

    # Verify that short value breakdown is correct and contains negative values
    assert short_value.stock_exposure == -5000.0  # Negative value
    assert short_value.stock_beta_adjusted == -5000.0  # Negative value
    assert short_value.option_delta_exposure == -1000.0  # Negative value
    assert short_value.option_beta_adjusted == -1200.0  # Negative value
    assert short_value.total_exposure == -6000.0  # Negative value
    assert short_value.total_beta_adjusted == -6200.0  # Negative value
    assert short_value.components["Short Stocks Value"] == -5000.0  # Negative value
    assert short_value.components["Short Options Value"] == -1000.0  # Negative value

    # Verify that options value breakdown is correct
    assert options_value.option_delta_exposure == 1000.0
    assert options_value.option_beta_adjusted == 1200.0
    assert options_value.total_exposure == 1000.0
    assert options_value.total_beta_adjusted == 1200.0
    assert options_value.components["Long Options Value"] == 2000.0
    assert options_value.components["Short Options Value"] == -1000.0  # Negative value
    assert options_value.components["Net Options Value"] == 1000.0


def test_calculate_portfolio_metrics():
    """Test that portfolio metrics are correctly calculated from value breakdowns."""
    # Create test data
    long_value = ExposureBreakdown(
        stock_exposure=10000.0,
        stock_beta_adjusted=12000.0,
        option_delta_exposure=2000.0,
        option_beta_adjusted=2400.0,
        total_exposure=12000.0,
        total_beta_adjusted=14400.0,
        description="Long market value (Stocks + Options)",
        formula="Long Stocks + Long Options",
        components={
            "Long Stocks Value": 10000.0,
            "Long Options Value": 2000.0,
        },
    )

    short_value = ExposureBreakdown(
        stock_exposure=-5000.0,  # Negative value
        stock_beta_adjusted=-5000.0,  # Negative value
        option_delta_exposure=-1000.0,  # Negative value
        option_beta_adjusted=-1200.0,  # Negative value
        total_exposure=-6000.0,  # Negative value
        total_beta_adjusted=-6200.0,  # Negative value
        description="Short market value (Stocks + Options)",
        formula="Short Stocks + Short Options",
        components={
            "Short Stocks Value": -5000.0,  # Negative value
            "Short Options Value": -1000.0,  # Negative value
        },
    )

    # Calculate portfolio metrics
    net_market_exposure, portfolio_beta, short_percentage = calculate_portfolio_metrics(
        long_value, short_value
    )

    # Verify that metrics are correctly calculated
    assert net_market_exposure == 6000.0
    assert portfolio_beta == pytest.approx(1.37, 0.01)  # (14400 - 6200) / 6000 = 1.37
    assert short_percentage == 50.0  # (6000 / 12000) * 100 = 50.0


def test_calculate_portfolio_values():
    """Test that portfolio values are correctly calculated from position data."""
    # Create test portfolio groups
    groups = create_test_portfolio_groups()

    # Create test cash-like positions
    cash_like_positions = [
        {
            "ticker": "SPAXX",
            "quantity": 3000,
            "market_value": 3000.0,
            "beta": 0.0,
            "beta_adjusted_exposure": 0.0,
        }
    ]

    # Calculate portfolio values
    (
        stock_value,
        option_value,
        cash_like_value,
        portfolio_estimate_value,
        cash_percentage,
    ) = calculate_portfolio_values(groups, cash_like_positions, 500.0)

    # Verify that values are correctly calculated
    assert stock_value == 5000.0  # 10000 - 5000 = 5000
    assert option_value == 500.0  # 1000 - 500 = 500
    assert cash_like_value == 3000.0
    assert portfolio_estimate_value == 9000.0  # 5000 + 500 + 3000 + 500 = 9000
    assert cash_percentage == pytest.approx(33.33, 0.01)  # (3000 / 9000) * 100 = 33.33


def test_get_portfolio_component_values():
    """Test that component values are correctly extracted from a portfolio summary."""
    # Create test portfolio summary
    portfolio_summary = create_test_portfolio_summary()

    # Get component values
    values = get_portfolio_component_values(portfolio_summary)

    # Verify that values are correctly extracted
    assert values["long_stock"] == 10000.0
    assert values["short_stock"] == -5000.0  # Negative value
    assert values["long_option"] == 2000.0
    assert values["short_option"] == -1000.0  # Negative value
    assert values["cash"] == 3000.0
    assert values["pending"] == 500.0
    assert values["total"] == 15000.0


def test_calculate_component_percentages():
    """Test that percentages are correctly calculated from component values."""
    # Create test component values
    component_values = {
        "long_stock": 10000.0,
        "short_stock": -5000.0,  # Negative value
        "long_option": 2000.0,
        "short_option": -1000.0,  # Negative value
        "cash": 3000.0,
        "pending": 500.0,
        "total": 15000.0,
    }

    # Calculate percentages
    percentages = calculate_component_percentages(component_values)

    # Verify that percentages are correctly calculated and signs are preserved
    assert percentages["long_stock"] == pytest.approx(
        66.67, 0.01
    )  # (10000 / 15000) * 100 = 66.67
    assert percentages["short_stock"] == pytest.approx(
        -33.33, 0.01
    )  # (-5000 / 15000) * 100 = -33.33
    assert percentages["long_option"] == pytest.approx(
        13.33, 0.01
    )  # (2000 / 15000) * 100 = 13.33
    assert percentages["short_option"] == pytest.approx(
        -6.67, 0.01
    )  # (-1000 / 15000) * 100 = -6.67
    assert percentages["cash"] == pytest.approx(
        20.0, 0.01
    )  # (3000 / 15000) * 100 = 20.0
    assert percentages["pending"] == pytest.approx(
        3.33, 0.01
    )  # (500 / 15000) * 100 = 3.33
    assert percentages["total"] == 100.0


def test_short_values_remain_negative():
    """Test that short values remain negative throughout the process."""
    # Create test portfolio summary
    portfolio_summary = create_test_portfolio_summary()

    # Get component values
    values = get_portfolio_component_values(portfolio_summary)

    # Verify that short values are negative
    assert values["short_stock"] < 0, "Short stock value should be negative"
    assert values["short_option"] < 0, "Short option value should be negative"

    # Verify exact values
    assert values["short_stock"] == -5000.0, "Short stock value should be -5000.0"
    assert values["short_option"] == -1000.0, "Short option value should be -1000.0"

    # Calculate percentages
    percentages = calculate_component_percentages(values)

    # Verify that percentage signs match value signs
    assert (percentages["short_stock"] < 0) == (values["short_stock"] < 0), (
        "Short stock percentage sign should match value sign"
    )
    assert (percentages["short_option"] < 0) == (values["short_option"] < 0), (
        "Short option percentage sign should match value sign"
    )
