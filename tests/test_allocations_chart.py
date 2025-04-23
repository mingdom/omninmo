"""Tests for the allocations stacked bar chart."""

import pytest

from src.folio.chart_data import transform_for_allocations_chart
from src.folio.data_model import ExposureBreakdown, PortfolioSummary
from src.folio.portfolio_value import get_portfolio_component_values


class TestAllocationsChart:
    """Tests for the allocations stacked bar chart."""

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
            stock_exposure=-5000.0,
            stock_beta_adjusted=-6000.0,
            option_delta_exposure=-1000.0,
            option_beta_adjusted=-1200.0,
            total_exposure=-6000.0,
            total_beta_adjusted=-7200.0,
            description="Short exposure",
            formula="Short formula",
            components={
                "Short Stocks Exposure": -5000.0,
                "Short Options Delta Exp": -1000.0,
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
                "Short Options Delta Exp": -1000.0,
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
            stock_value=5000.0,  # Net stock value (10000 - 5000)
            option_value=1000.0,  # Net option value (2000 - 1000)
            pending_activity_value=500.0,
            portfolio_estimate_value=10500.0,  # 5000 + 1000 + 4000 + 500
        )

    def test_allocations_stacked_bar_chart(self, mock_portfolio_summary):
        """Test that allocations chart correctly creates a stacked bar chart with four main categories."""
        # Given a portfolio summary with known values
        # When we transform it for the allocations chart
        chart_data = transform_for_allocations_chart(mock_portfolio_summary)

        # Then the chart should have the correct structure
        assert "data" in chart_data
        assert "layout" in chart_data
        assert chart_data["layout"]["barmode"] == "stack"

        # And it should have six traces (Long Stocks, Long Options, Short Stocks, Short Options, Cash, Pending)
        traces = chart_data["data"]
        assert len(traces) == 6

        # And the traces should be correctly named
        trace_names = [trace["name"] for trace in traces]
        assert "Long Stocks" in trace_names
        assert "Long Options" in trace_names
        assert "Short Stocks" in trace_names
        assert "Short Options" in trace_names
        assert "Cash" in trace_names
        assert "Pending" in trace_names

        # And the x values should place the traces in the correct categories
        long_stocks_trace = next(t for t in traces if t["name"] == "Long Stocks")
        long_options_trace = next(t for t in traces if t["name"] == "Long Options")
        short_stocks_trace = next(t for t in traces if t["name"] == "Short Stocks")
        short_options_trace = next(t for t in traces if t["name"] == "Short Options")
        cash_trace = next(t for t in traces if t["name"] == "Cash")
        pending_trace = next(t for t in traces if t["name"] == "Pending")

        assert long_stocks_trace["x"] == ["Long"]
        assert long_options_trace["x"] == ["Long"]
        assert short_stocks_trace["x"] == ["Short"]
        assert short_options_trace["x"] == ["Short"]
        assert cash_trace["x"] == ["Cash"]
        assert pending_trace["x"] == ["Pending"]

        # And the y values should match the expected values from the get_portfolio_component_values function
        component_values = get_portfolio_component_values(mock_portfolio_summary)

        assert long_stocks_trace["y"][0] == component_values["long_stock"]
        assert long_options_trace["y"][0] == component_values["long_option"]
        assert short_stocks_trace["y"][0] == abs(
            component_values["short_stock"]
        )  # Use absolute value for display
        assert short_options_trace["y"][0] == abs(
            component_values["short_option"]
        )  # Use absolute value for display
        assert cash_trace["y"][0] == mock_portfolio_summary.cash_like_value
        assert pending_trace["y"][0] == mock_portfolio_summary.pending_activity_value

        # And the layout should have dual y-axes
        assert "yaxis" in chart_data["layout"]
        assert "yaxis2" in chart_data["layout"]
        assert chart_data["layout"]["yaxis2"]["overlaying"] == "y"
        assert chart_data["layout"]["yaxis2"]["side"] == "right"

        # And the percentages should be calculated correctly

        # Check that the y2 axis shows percentages
        assert chart_data["layout"]["yaxis2"]["tickformat"] == ".1f%"
        assert chart_data["layout"]["yaxis2"]["range"] == [0, 100]

    def test_allocations_chart_with_empty_portfolio(self):
        """Test that allocations chart handles empty portfolios correctly."""
        # Create an empty portfolio summary
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

        empty_summary = PortfolioSummary(
            net_market_exposure=0.0,
            portfolio_beta=0.0,
            long_exposure=empty_exposure,
            short_exposure=empty_exposure,
            options_exposure=empty_exposure,
            short_percentage=0.0,
            cash_like_value=0.0,
            cash_like_count=0,
            cash_percentage=0.0,
            stock_value=0.0,
            option_value=0.0,
            pending_activity_value=0.0,
            portfolio_estimate_value=0.0,
        )

        # Get the chart data
        chart_data = transform_for_allocations_chart(empty_summary)

        # Verify that an empty chart is returned
        assert "data" in chart_data
        assert len(chart_data["data"]) == 0
        assert "annotations" in chart_data["layout"]
        assert (
            "No portfolio data available"
            in chart_data["layout"]["annotations"][0]["text"]
        )
