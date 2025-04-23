"""Tests for chart data transformation functions."""

import pytest

from src.folio.chart_data import (
    transform_for_allocations_chart,
    transform_for_exposure_chart,
    transform_for_treemap,
)
from src.folio.data_model import (
    ExposureBreakdown,
    OptionPosition,
    PortfolioGroup,
    PortfolioSummary,
    StockPosition,
)


class TestChartDataTransformations:
    """Tests for chart data transformation functions."""

    @pytest.fixture
    def mock_portfolio_summary(self):
        """Create a mock portfolio summary for testing."""
        # Create exposure breakdowns
        long_exposure = ExposureBreakdown(
            stock_exposure=10000.0,
            stock_beta_adjusted=12000.0,
            option_delta_exposure=2000.0,
            option_beta_adjusted=2400.0,
            total_exposure=12000.0,
            total_beta_adjusted=14400.0,
            description="Long exposure",
            formula="Long formula",
            components={
                "Long Stocks Exposure": 10000.0,
                "Long Options Delta Exp": 2000.0,
            },
        )

        short_exposure = ExposureBreakdown(
            stock_exposure=5000.0,
            stock_beta_adjusted=6000.0,
            option_delta_exposure=1000.0,
            option_beta_adjusted=1200.0,
            total_exposure=6000.0,
            total_beta_adjusted=7200.0,
            description="Short exposure",
            formula="Short formula",
            components={
                "Short Stocks Exposure": 5000.0,
                "Short Options Delta Exp": 1000.0,
            },
        )

        options_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=1000.0,
            option_beta_adjusted=1200.0,
            total_exposure=1000.0,
            total_beta_adjusted=1200.0,
            description="Options exposure",
            formula="Options formula",
            components={
                "Long Options Delta Exp": 2000.0,
                "Short Options Delta Exp": 1000.0,
                "Net Options Delta Exp": 1000.0,
            },
        )

        # Create portfolio summary with a net market exposure of 6000.0 (12000.0 - 6000.0)
        return PortfolioSummary(
            net_market_exposure=6000.0,
            portfolio_beta=1.2,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=33.0,
            cash_like_value=4000.0,
            cash_like_count=1,
            cash_percentage=40.0,
            portfolio_estimate_value=10000.0,
        )

    @pytest.fixture
    def mock_portfolio_groups(self):
        """Create mock portfolio groups for testing."""
        # Create stock positions
        aapl_stock = StockPosition(
            ticker="AAPL",
            position_type="stock",
            quantity=100,
            market_exposure=5000.0,
            beta=1.2,
            beta_adjusted_exposure=6000.0,
        )

        msft_stock = StockPosition(
            ticker="MSFT",
            position_type="stock",
            quantity=50,
            market_exposure=3000.0,
            beta=1.1,
            beta_adjusted_exposure=3300.0,
        )

        # Create option positions
        aapl_option = OptionPosition(
            ticker="AAPL",
            position_type="option",
            quantity=10,
            market_exposure=1000.0,
            beta=1.2,
            beta_adjusted_exposure=1200.0,
            strike=150.0,
            expiry="2023-01-01",
            option_type="CALL",
            delta=0.7,
            delta_exposure=700.0,
            notional_value=10000.0,
            underlying_beta=1.2,
        )

        # Create portfolio groups
        aapl_group = PortfolioGroup(
            ticker="AAPL",
            stock_position=aapl_stock,
            option_positions=[aapl_option],
            net_exposure=5700.0,
            beta=1.2,
            beta_adjusted_exposure=6840.0,
            total_delta_exposure=700.0,
            options_delta_exposure=700.0,
        )

        msft_group = PortfolioGroup(
            ticker="MSFT",
            stock_position=msft_stock,
            option_positions=[],
            net_exposure=3000.0,
            beta=1.1,
            beta_adjusted_exposure=3300.0,
            total_delta_exposure=0.0,
            options_delta_exposure=0.0,
        )

        return [aapl_group, msft_group]

    def test_exposure_chart_net_value_calculation(self, mock_portfolio_summary):
        """Test that net exposure is correctly calculated in the exposure chart.

        This test specifically verifies that the net exposure value in the chart
        matches the net_market_exposure value in the portfolio summary, ensuring
        consistency between the chart and the summary cards.
        """
        # Test with regular (non-beta-adjusted) values
        chart_data = transform_for_exposure_chart(
            mock_portfolio_summary, use_beta_adjusted=False
        )

        # Extract the values from the chart data
        values = chart_data["data"][0]["y"]
        categories = ["Long", "Short", "Options", "Net"]
        value_dict = dict(zip(categories, values, strict=False))

        # Verify that the net value matches the portfolio summary's net_market_exposure
        assert value_dict["Net"] == mock_portfolio_summary.net_market_exposure

        # Verify that the net value equals long minus short (since short is stored as positive)
        assert value_dict["Net"] == value_dict["Long"] - value_dict["Short"]

        # Verify that the net value is not equal to long plus short (the previous incorrect calculation)
        assert value_dict["Net"] != value_dict["Long"] + value_dict["Short"]

    def test_exposure_chart_beta_adjusted_calculation(self, mock_portfolio_summary):
        """Test that beta-adjusted net exposure is correctly calculated in the exposure chart.

        This test verifies that when using beta-adjusted values, the net exposure in the chart
        matches the difference between long and short beta-adjusted exposures in the portfolio summary.
        """
        # Test with beta-adjusted values
        chart_data = transform_for_exposure_chart(
            mock_portfolio_summary, use_beta_adjusted=True
        )

        # Extract the values from the chart data
        values = chart_data["data"][0]["y"]
        categories = ["Long", "Short", "Options", "Net"]
        value_dict = dict(zip(categories, values, strict=False))

        # Calculate the expected beta-adjusted net exposure
        # Note: short_exposure is now stored as a negative value
        expected_beta_adjusted_net = (
            mock_portfolio_summary.long_exposure.total_beta_adjusted
            + mock_portfolio_summary.short_exposure.total_beta_adjusted
        )

        # Verify that the net value matches the expected beta-adjusted net exposure
        assert value_dict["Net"] == expected_beta_adjusted_net

        # Verify that the net value equals long plus short (since short is stored as negative)
        assert value_dict["Net"] == value_dict["Long"] + value_dict["Short"]

        # Verify that the net value is not equal to long minus short (the previous incorrect calculation)
        assert value_dict["Net"] != value_dict["Long"] - value_dict["Short"]

        # Verify that the net value is not equal to long minus short plus options
        # (the previous incorrect calculation in summary_cards.py)
        incorrect_calculation = (
            value_dict["Long"] - value_dict["Short"] + value_dict["Options"]
        )
        assert value_dict["Net"] != incorrect_calculation, (
            "Net value should not include options separately as they are already in long/short"
        )

    def test_treemap_chart_values(self, mock_portfolio_groups):
        """Test that treemap chart values are correctly calculated."""
        chart_data = transform_for_treemap(mock_portfolio_groups)

        # Verify that the chart has the expected structure
        assert "data" in chart_data
        assert len(chart_data["data"]) == 1  # One trace for the treemap

        # Verify that the treemap has the expected data points
        trace = chart_data["data"][0]
        assert "Portfolio" in trace["labels"]
        assert "AAPL" in trace["labels"]
        assert "MSFT" in trace["labels"]

        # Verify that the values are absolute exposures
        values = trace["values"]
        assert len(values) > 2  # Root + at least 2 tickers

    @pytest.fixture
    def mock_portfolio_summary_with_negative_shorts(self):
        """Create a mock portfolio summary with negative short values for testing."""
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

    @pytest.fixture
    def empty_portfolio_summary(self):
        """Create an empty portfolio summary for testing."""
        # Create empty exposure breakdowns
        empty_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=0.0,
            option_beta_adjusted=0.0,
            total_exposure=0.0,
            total_beta_adjusted=0.0,
            description="Empty exposure",
            formula="N/A",
            components={},
        )

        # Create empty portfolio summary
        return PortfolioSummary(
            net_market_exposure=0.0,
            portfolio_beta=0.0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure,
            short_percentage=0.0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0,
            cash_percentage=0.0,
            stock_value=0.0,
            option_value=0.0,
            pending_activity_value=0.0,
            portfolio_estimate_value=0.0,
        )

    def test_allocations_chart_transformation(
        self, mock_portfolio_summary_with_negative_shorts
    ):
        """Test that portfolio summary data is correctly transformed for the allocations chart."""
        # Transform data for allocations chart
        chart_data = transform_for_allocations_chart(
            mock_portfolio_summary_with_negative_shorts
        )

        # Verify that chart data is correctly structured
        assert "data" in chart_data
        assert "layout" in chart_data
        assert (
            len(chart_data["data"]) == 6
        )  # 6 bars: long stock, long option, short stock, short option, cash, pending

        # Verify that long stock bar is correct
        long_stock_bar = chart_data["data"][0]
        assert long_stock_bar["name"] == "Long Stocks"
        assert long_stock_bar["x"] == ["Long"]
        assert long_stock_bar["y"][0] == 10000.0  # Value at "Long" position

        # Verify that long option bar is correct
        long_option_bar = chart_data["data"][1]
        assert long_option_bar["name"] == "Long Options"
        assert long_option_bar["x"] == ["Long"]
        assert long_option_bar["y"][0] == 2000.0  # Value at "Long" position

        # Verify that short stock bar is correct and uses absolute value for display
        short_stock_bar = chart_data["data"][2]
        assert short_stock_bar["name"] == "Short Stocks"
        assert short_stock_bar["x"] == ["Short"]
        assert (
            short_stock_bar["y"][0] == 5000.0
        )  # Value at "Short" position (absolute value of -5000.0)

        # Verify that short option bar is correct and uses absolute value for display
        short_option_bar = chart_data["data"][3]
        assert short_option_bar["name"] == "Short Options"
        assert short_option_bar["x"] == ["Short"]
        assert (
            short_option_bar["y"][0] == 1000.0
        )  # Value at "Short" position (absolute value of -1000.0)

        # Verify that cash bar is correct
        cash_bar = chart_data["data"][4]
        assert cash_bar["name"] == "Cash"
        assert cash_bar["x"] == ["Cash"]
        assert cash_bar["y"][0] == 3000.0  # Value at "Cash" position

        # Verify that pending bar is correct
        pending_bar = chart_data["data"][5]
        assert pending_bar["name"] == "Pending"
        assert pending_bar["x"] == ["Pending"]
        assert pending_bar["y"][0] == 500.0  # Value at "Pending" position

        # Verify that layout is correctly configured
        assert chart_data["layout"]["barmode"] == "stack"
        assert chart_data["layout"]["yaxis"]["title"] == "Value ($)"
        assert chart_data["layout"]["yaxis2"]["title"] == "Percentage (%)"
        assert chart_data["layout"]["yaxis2"]["range"] == [0, 100]

    def test_allocations_chart_with_empty_portfolio(self, empty_portfolio_summary):
        """Test that the allocations chart handles empty portfolios correctly."""
        # Transform data for allocations chart
        chart_data = transform_for_allocations_chart(empty_portfolio_summary)

        # Verify that chart data is correctly structured for an empty portfolio
        assert "data" in chart_data
        assert "layout" in chart_data
        assert len(chart_data["data"]) == 0  # No bars for empty portfolio
        assert "annotations" in chart_data["layout"]
        assert (
            chart_data["layout"]["annotations"][0]["text"]
            == "No portfolio data available"
        )

    def test_allocations_chart_with_complex_portfolio(self):
        """Test that the allocations chart handles complex portfolios correctly.

        This test verifies that the chart correctly handles portfolios with:
        1. Large differences between component values
        2. Negative short values that need to be displayed as absolute values
        3. Proper calculation of percentages
        4. Correct total portfolio value calculation
        """
        # Create a complex portfolio summary with significant differences in component values
        # and both long and short positions
        from src.folio.data_model import ExposureBreakdown, PortfolioSummary

        # Create a portfolio with large long positions, small short positions, and cash
        long_exposure = ExposureBreakdown(
            stock_exposure=2000000.0,  # $2M in stocks
            stock_beta_adjusted=2200000.0,
            option_delta_exposure=500000.0,  # $500K in options
            option_beta_adjusted=550000.0,
            total_exposure=2500000.0,  # $2.5M total long exposure
            total_beta_adjusted=2750000.0,  # Higher beta
            description="Long Exposure",
            formula="Long Stock + Long Call Delta + Short Put Delta",
            components={
                "Long Stocks Value": 2000000.0,
                "Long Options Value": 500000.0,
            },
        )

        short_exposure = ExposureBreakdown(
            stock_exposure=-300000.0,  # -$300K in stocks
            stock_beta_adjusted=-270000.0,
            option_delta_exposure=-100000.0,  # -$100K in options
            option_beta_adjusted=-90000.0,
            total_exposure=-400000.0,  # -$400K total short exposure
            total_beta_adjusted=-360000.0,  # Lower beta
            description="Short Exposure",
            formula="Short Stock + Short Call Delta + Long Put Delta",
            components={
                "Short Stocks Value": -300000.0,
                "Short Options Value": -100000.0,
            },
        )

        # Create options exposure breakdown
        options_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=400000.0,  # Net options exposure
            option_beta_adjusted=460000.0,
            total_exposure=400000.0,
            total_beta_adjusted=460000.0,
            description="Options Exposure",
            formula="Long Options Delta - Short Options Delta",
            components={
                "Long Options": 500000.0,
                "Short Options": -100000.0,
                "Net": 400000.0,
            },
        )

        # Create portfolio summary
        portfolio_summary = PortfolioSummary(
            net_market_exposure=2100000.0,  # Net exposure
            portfolio_beta=1.1,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=16.0,  # 16% short
            cash_like_positions=[],
            cash_like_value=700000.0,  # $700K in cash
            cash_like_count=1,
            cash_percentage=23.3,  # $700K / $3M
            stock_value=1700000.0,  # Net stock value
            option_value=400000.0,  # Net option value
            pending_activity_value=200000.0,  # $200K pending
            portfolio_estimate_value=3000000.0,  # $3M total
            help_text={},
        )

        # Transform data for allocations chart
        chart_data = transform_for_allocations_chart(portfolio_summary)

        # Extract values from chart data
        chart_values = {}
        for trace in chart_data["data"]:
            name = trace["name"]
            value = trace["y"][0]
            chart_values[name] = value

        # Verify component values
        assert chart_values["Long Stocks"] == 2000000.0
        assert chart_values["Long Options"] == 500000.0
        assert chart_values["Short Stocks"] == 300000.0  # Absolute value
        assert chart_values["Short Options"] == 100000.0  # Absolute value
        assert chart_values["Cash"] == 700000.0
        assert chart_values["Pending"] == 200000.0

        # Calculate total from chart values (using the correct formula)
        chart_total = (
            (
                chart_values["Long Stocks"] - chart_values["Short Stocks"]
            )  # Net stock value
            + (
                chart_values["Long Options"] - chart_values["Short Options"]
            )  # Net option value
            + chart_values["Cash"]
            + chart_values["Pending"]
        )

        # Verify that the total matches the portfolio summary
        assert chart_total == pytest.approx(
            portfolio_summary.portfolio_estimate_value, abs=0.01
        )

        # Extract percentages from hover text
        percentages = {}
        for trace in chart_data["data"]:
            name = trace["name"]
            hover_text = trace["text"][0]
            if "%" in hover_text:
                percentage_str = hover_text.split("(")[1].split("%")[0]
                percentages[name] = float(percentage_str)

        # Verify percentages
        assert percentages["Long Stocks"] == pytest.approx(
            2000000.0 / 3000000.0 * 100, abs=0.1
        )
        assert percentages["Long Options"] == pytest.approx(
            500000.0 / 3000000.0 * 100, abs=0.1
        )
        assert percentages["Short Stocks"] == pytest.approx(
            300000.0 / 3000000.0 * 100, abs=0.1
        )
        assert percentages["Short Options"] == pytest.approx(
            100000.0 / 3000000.0 * 100, abs=0.1
        )
        assert percentages["Cash"] == pytest.approx(700000.0 / 3000000.0 * 100, abs=0.1)
        assert percentages["Pending"] == pytest.approx(
            200000.0 / 3000000.0 * 100, abs=0.1
        )

        # Verify that the net percentage calculation is correct
        long_percentage = percentages["Long Stocks"] + percentages["Long Options"]
        short_percentage = percentages["Short Stocks"] + percentages["Short Options"]
        cash_percentage = percentages["Cash"]
        pending_percentage = percentages["Pending"]

        net_percentage = (
            long_percentage - short_percentage + cash_percentage + pending_percentage
        )
        assert net_percentage == pytest.approx(100.0, abs=1.0)

    def test_allocations_chart_with_imbalanced_portfolio(self):
        """Test that the allocations chart handles imbalanced portfolios correctly.

        This test verifies that the chart correctly handles portfolios with:
        1. Very large short positions compared to long positions
        2. Correct calculation of percentages in extreme cases
        3. Proper handling of negative values in the total calculation
        """
        from src.folio.data_model import ExposureBreakdown, PortfolioSummary

        # Create a portfolio with small long positions and large short positions
        long_exposure = ExposureBreakdown(
            stock_exposure=300000.0,  # $300K in stocks
            stock_beta_adjusted=330000.0,
            option_delta_exposure=200000.0,  # $200K in options
            option_beta_adjusted=220000.0,
            total_exposure=500000.0,  # $500K total long exposure
            total_beta_adjusted=550000.0,
            description="Long Exposure",
            formula="Long Stock + Long Call Delta + Short Put Delta",
            components={
                "Long Stocks Value": 300000.0,
                "Long Options Value": 200000.0,
            },
        )

        short_exposure = ExposureBreakdown(
            stock_exposure=-1000000.0,  # -$1M in stocks
            stock_beta_adjusted=-1100000.0,
            option_delta_exposure=-500000.0,  # -$500K in options
            option_beta_adjusted=-550000.0,
            total_exposure=-1500000.0,  # -$1.5M total short exposure
            total_beta_adjusted=-1650000.0,
            description="Short Exposure",
            formula="Short Stock + Short Call Delta + Long Put Delta",
            components={
                "Short Stocks Value": -1000000.0,
                "Short Options Value": -500000.0,
            },
        )

        # Create options exposure breakdown
        options_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=-300000.0,  # Net options exposure
            option_beta_adjusted=-330000.0,
            total_exposure=-300000.0,
            total_beta_adjusted=-330000.0,
            description="Options Exposure",
            formula="Long Options Delta - Short Options Delta",
            components={
                "Long Options": 200000.0,
                "Short Options": -500000.0,
                "Net": -300000.0,
            },
        )

        # Create portfolio summary with large cash position to balance
        portfolio_summary = PortfolioSummary(
            net_market_exposure=-1000000.0,  # Net exposure (negative)
            portfolio_beta=1.5,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=300.0,  # 300% short (extreme case)
            cash_like_positions=[],
            cash_like_value=2000000.0,  # $2M in cash
            cash_like_count=1,
            cash_percentage=181.8,  # $2M / $1.1M
            stock_value=-700000.0,  # Net stock value (negative)
            option_value=-300000.0,  # Net option value (negative)
            pending_activity_value=100000.0,  # $100K pending
            portfolio_estimate_value=1100000.0,  # $1.1M total (net of shorts)
            help_text={},
        )

        # Transform data for allocations chart
        chart_data = transform_for_allocations_chart(portfolio_summary)

        # Extract values from chart data
        chart_values = {}
        for trace in chart_data["data"]:
            name = trace["name"]
            value = trace["y"][0]
            chart_values[name] = value

        # Verify component values
        assert chart_values["Long Stocks"] == 300000.0
        assert chart_values["Long Options"] == 200000.0
        assert chart_values["Short Stocks"] == 1000000.0  # Absolute value
        assert chart_values["Short Options"] == 500000.0  # Absolute value
        assert chart_values["Cash"] == 2000000.0
        assert chart_values["Pending"] == 100000.0

        # Calculate total from chart values (using the correct formula)
        chart_total = (
            (
                chart_values["Long Stocks"] - chart_values["Short Stocks"]
            )  # Net stock value (negative)
            + (
                chart_values["Long Options"] - chart_values["Short Options"]
            )  # Net option value (negative)
            + chart_values["Cash"]
            + chart_values["Pending"]
        )

        # Verify that the total matches the portfolio summary
        assert chart_total == pytest.approx(
            portfolio_summary.portfolio_estimate_value, abs=0.01
        )

        # Extract percentages from hover text
        percentages = {}
        for trace in chart_data["data"]:
            name = trace["name"]
            hover_text = trace["text"][0]
            if "%" in hover_text:
                percentage_str = hover_text.split("(")[1].split("%")[0]
                percentages[name] = float(percentage_str)

        # Verify that percentages are calculated correctly even in extreme cases
        total = portfolio_summary.portfolio_estimate_value
        assert percentages["Long Stocks"] == pytest.approx(
            300000.0 / total * 100, abs=0.1
        )
        assert percentages["Long Options"] == pytest.approx(
            200000.0 / total * 100, abs=0.1
        )
        assert percentages["Short Stocks"] == pytest.approx(
            1000000.0 / total * 100, abs=0.1
        )
        assert percentages["Short Options"] == pytest.approx(
            500000.0 / total * 100, abs=0.1
        )
        assert percentages["Cash"] == pytest.approx(2000000.0 / total * 100, abs=0.1)
        assert percentages["Pending"] == pytest.approx(100000.0 / total * 100, abs=0.1)

        # Verify that the net percentage calculation is correct
        long_percentage = percentages["Long Stocks"] + percentages["Long Options"]
        short_percentage = percentages["Short Stocks"] + percentages["Short Options"]
        cash_percentage = percentages["Cash"]
        pending_percentage = percentages["Pending"]

        net_percentage = (
            long_percentage - short_percentage + cash_percentage + pending_percentage
        )
        assert net_percentage == pytest.approx(100.0, abs=1.0)
