"""Tests for chart data transformation functions."""

import pytest

# Asset Allocation Chart has been removed in favor of the more accurate Exposure Chart
from src.folio.chart_data import transform_for_exposure_chart, transform_for_treemap
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
        expected_beta_adjusted_net = (
            mock_portfolio_summary.long_exposure.total_beta_adjusted
            - mock_portfolio_summary.short_exposure.total_beta_adjusted
        )

        # Verify that the net value matches the expected beta-adjusted net exposure
        assert value_dict["Net"] == expected_beta_adjusted_net

        # Verify that the net value equals long minus short (since short is stored as positive)
        assert value_dict["Net"] == value_dict["Long"] - value_dict["Short"]

        # Verify that the net value is not equal to long plus short (the previous incorrect calculation)
        assert value_dict["Net"] != value_dict["Long"] + value_dict["Short"]

        # Verify that the net value is not equal to long minus short plus options
        # (the previous incorrect calculation in summary_cards.py)
        incorrect_calculation = (
            value_dict["Long"] - value_dict["Short"] + value_dict["Options"]
        )
        assert value_dict["Net"] != incorrect_calculation, (
            "Net value should not include options separately as they are already in long/short"
        )

    # Asset Allocation Chart has been removed in favor of the more accurate Exposure Chart
    def test_asset_allocation_chart_values(self):
        """Test that asset allocation chart values are correctly calculated."""
        import pytest

        pytest.skip(
            "Asset Allocation Chart has been removed in favor of the more accurate Exposure Chart"
        )

        # Verify that the chart has the expected structure
        assert "data" in chart_data

        # We now have 7 traces for the stacked bar chart:
        # 1. Long Stock, 2. Long Options, 3. Short Stock, 4. Short Options,
        # 5. Cash & Bonds, 6. Total Long (invisible), 7. Total Short (invisible)
        assert len(chart_data["data"]) == 7

        # Verify we have the expected trace names
        trace_names = [trace["name"] for trace in chart_data["data"]]
        assert "Long Stock" in trace_names
        assert "Long Options" in trace_names
        assert "Short Stock" in trace_names
        assert "Short Options" in trace_names
        assert "Cash & Bonds" in trace_names

        # Verify the title does not include beta-adjusted
        assert "(Beta-Adjusted)" not in chart_data["layout"]["title"]["text"]
        assert "(Exposure)" in chart_data["layout"]["title"]["text"]

        # Test with beta-adjusted values
        chart_data = transform_for_asset_allocation(
            mock_portfolio_summary, use_beta_adjusted=True
        )

        # Extract the values from the chart data for each component
        long_stock_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Long Stock"
        )
        long_options_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Long Options"
        )
        short_stock_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Short Stock"
        )
        short_options_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Short Options"
        )
        cash_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Cash & Bonds"
        )

        # Verify the title includes beta-adjusted
        assert "(Beta-Adjusted)" in chart_data["layout"]["title"]["text"]
        assert "(Exposure)" not in chart_data["layout"]["title"]["text"]

        # Verify the values match the expected beta-adjusted values
        assert (
            long_stock_trace["y"][0]
            == mock_portfolio_summary.long_exposure.stock_exposure
            * mock_portfolio_summary.portfolio_beta
        )
        # Options should not be beta-adjusted
        assert (
            long_options_trace["y"][0]
            == mock_portfolio_summary.long_exposure.option_delta_exposure
        )
        assert short_stock_trace["y"][1] == abs(
            mock_portfolio_summary.short_exposure.stock_exposure
            * mock_portfolio_summary.portfolio_beta
        )
        # Options should not be beta-adjusted
        assert short_options_trace["y"][1] == abs(
            mock_portfolio_summary.short_exposure.option_delta_exposure
        )
        # Cash should not be beta-adjusted
        assert cash_trace["y"][2] == mock_portfolio_summary.cash_like_value

        # Test with regular exposure values again to verify we can switch back
        chart_data = transform_for_asset_allocation(
            mock_portfolio_summary, use_beta_adjusted=False
        )

        # Extract the values again
        long_stock_trace = next(
            trace for trace in chart_data["data"] if trace["name"] == "Long Stock"
        )

        # Verify the values match the expected non-beta-adjusted values
        assert (
            long_stock_trace["y"][0]
            == mock_portfolio_summary.long_exposure.stock_exposure
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
