"""Integration test for price update functionality.

This test verifies that the price update functionality correctly updates prices
and recalculates all relevant metrics in the portfolio.

Note: This test requires internet access to fetch prices from yfinance.
"""

import os
from datetime import datetime

import pandas as pd
import pytest

from src.folio.data_model import OptionPosition, PortfolioGroup, StockPosition
from src.folio.portfolio import (
    process_portfolio_data,
    update_portfolio_summary_with_prices,
)


class TestPriceUpdate:
    """Test the price update functionality."""

    @pytest.fixture
    def sample_portfolio(self):
        """Load the sample portfolio."""
        # Get the path to the sample portfolio
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../.."))

        # Try to use real-portfolio.csv if it exists, otherwise fall back to sample-portfolio.csv
        real_portfolio_path = os.path.join(project_root, ".tmp", "real-portfolio.csv")
        sample_path = os.path.join(
            project_root, "src", "folio", "assets", "sample-portfolio.csv"
        )

        if os.path.exists(real_portfolio_path):
            portfolio_path = real_portfolio_path
        else:
            portfolio_path = sample_path

        # Load the portfolio
        df = pd.read_csv(portfolio_path)
        return df

    def test_price_update_changes_values(self, sample_portfolio):
        """Test that price updates change the relevant values in the portfolio."""
        # Process the portfolio data
        groups, summary, _ = process_portfolio_data(sample_portfolio)

        # Record initial values
        initial_values = {
            "price_updated_at": summary.price_updated_at,
            "net_market_exposure": summary.net_market_exposure,
            "portfolio_beta": summary.portfolio_beta,
            "long_exposure_total": summary.long_exposure.total_exposure,
            "short_exposure_total": summary.short_exposure.total_exposure,
            "options_exposure_total": summary.options_exposure.total_exposure,
            "portfolio_estimate_value": summary.portfolio_estimate_value,
        }

        # Record some individual position prices
        initial_position_values = {}
        for group in groups:
            if group.stock_position:
                initial_position_values[f"{group.ticker}_price"] = (
                    group.stock_position.price
                )
                initial_position_values[f"{group.ticker}_market_exposure"] = (
                    group.stock_position.market_exposure
                )
                initial_position_values[f"{group.ticker}_beta_adjusted"] = (
                    group.stock_position.beta_adjusted_exposure
                )

            for option in group.option_positions:
                initial_position_values[f"{option.ticker}_price"] = option.price

        # Wait a moment to ensure the timestamp will be different
        # (This is just for the test - in real usage, time between updates would be longer)
        import time

        time.sleep(1)

        # Update prices
        updated_summary = update_portfolio_summary_with_prices(groups, summary)

        # Record updated values
        updated_values = {
            "price_updated_at": updated_summary.price_updated_at,
            "net_market_exposure": updated_summary.net_market_exposure,
            "portfolio_beta": updated_summary.portfolio_beta,
            "long_exposure_total": updated_summary.long_exposure.total_exposure,
            "short_exposure_total": updated_summary.short_exposure.total_exposure,
            "options_exposure_total": updated_summary.options_exposure.total_exposure,
            "portfolio_estimate_value": updated_summary.portfolio_estimate_value,
        }

        # Record updated position values
        updated_position_values = {}
        for group in groups:
            if group.stock_position:
                updated_position_values[f"{group.ticker}_price"] = (
                    group.stock_position.price
                )
                updated_position_values[f"{group.ticker}_market_exposure"] = (
                    group.stock_position.market_exposure
                )
                updated_position_values[f"{group.ticker}_beta_adjusted"] = (
                    group.stock_position.beta_adjusted_exposure
                )

            for option in group.option_positions:
                updated_position_values[f"{option.ticker}_price"] = option.price

        # Determine which portfolio was used
        portfolio_type = (
            "real"
            if os.path.exists(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "../..",
                    ".tmp",
                    "real-portfolio.csv",
                )
            )
            else "sample"
        )

        # Save the values to a file for detailed analysis
        output_file = f"price_update_test_results_{portfolio_type}.txt"
        with open(output_file, "w") as f:
            f.write("=== Initial Values ===\n")
            for key, value in initial_values.items():
                f.write(f"{key}: {value}\n")

            f.write("\n=== Updated Values ===\n")
            for key, value in updated_values.items():
                f.write(f"{key}: {value}\n")

            f.write("\n=== Changes in Portfolio Values ===\n")
            for key, value in initial_values.items():
                if key == "price_updated_at":
                    # Convert timestamps to datetime for comparison
                    initial_time = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    updated_time = datetime.fromisoformat(
                        updated_values[key].replace("Z", "+00:00")
                    )
                    time_diff = updated_time - initial_time
                    f.write(f"{key}: Changed by {time_diff}\n")
                else:
                    diff = updated_values[key] - value
                    percent = (diff / value * 100) if value != 0 else float("inf")
                    f.write(
                        f"{key}: {value} -> {updated_values[key]} (Diff: {diff}, {percent:.2f}%)\n"
                    )

            f.write("\n=== Changes in Position Values ===\n")
            for key, value in initial_position_values.items():
                if key in updated_position_values:
                    diff = updated_position_values[key] - value
                    percent = (diff / value * 100) if value != 0 else float("inf")
                    f.write(
                        f"{key}: {value} -> {updated_position_values[key]} (Diff: {diff}, {percent:.2f}%)\n"
                    )

        # Also print to console

        # Verify that the timestamp has changed
        assert initial_values["price_updated_at"] != updated_values["price_updated_at"]

        # Verify that at least some values have changed
        # We can't predict exactly how prices will change, but we can check that something changed
        values_changed = False
        for key, value in initial_values.items():
            if key != "price_updated_at" and value != updated_values[key]:
                values_changed = True
                break

        assert values_changed, "No portfolio values changed after price update"

        # Verify that at least some position prices have changed
        prices_changed = False
        for key, value in initial_position_values.items():
            if "_price" in key and key in updated_position_values:
                if value != updated_position_values[key]:
                    prices_changed = True
                    break

        assert prices_changed, "No position prices changed after price update"

        # Verify that market exposures have been recalculated for stocks
        exposures_changed = False
        for key, value in initial_position_values.items():
            if "_market_exposure" in key and key in updated_position_values:
                if value != updated_position_values[key]:
                    exposures_changed = True
                    break

        assert exposures_changed, "No market exposures changed after price update"

        # Verify that beta-adjusted exposures have been recalculated for stocks
        beta_adjusted_changed = False
        for key, value in initial_position_values.items():
            if "_beta_adjusted" in key and key in updated_position_values:
                if value != updated_position_values[key]:
                    beta_adjusted_changed = True
                    break

        assert beta_adjusted_changed, (
            "No beta-adjusted exposures changed after price update"
        )

    def test_price_update_with_mock_data(self, mocker):
        """Test price update with mock data to verify specific calculations."""
        # Create a mock portfolio with known values
        stock1 = StockPosition(
            ticker="AAPL",
            quantity=100,
            beta=1.2,
            market_exposure=15000.0,  # 100 shares at $150/share
            beta_adjusted_exposure=18000.0,  # 15000 * 1.2
            price=150.0,
        )

        stock2 = StockPosition(
            ticker="MSFT",
            quantity=50,
            beta=1.1,
            market_exposure=17500.0,  # 50 shares at $350/share
            beta_adjusted_exposure=19250.0,  # 17500 * 1.1
            price=350.0,
        )

        option1 = OptionPosition(
            ticker="AAPL230616C00160000",
            position_type="option",
            quantity=2,
            beta=1.2,
            beta_adjusted_exposure=1440.0,  # 1200 * 1.2
            strike=160.0,
            expiry="2023-06-16",
            option_type="CALL",
            delta=0.6,
            delta_exposure=1200.0,  # 0.6 * 100 * 150 * 2 * 0.01
            notional_value=30000.0,  # 100 * 150 * 2
            underlying_beta=1.2,
            market_exposure=1200.0,
            price=6.0,  # $6 per share, or $600 per contract
        )

        group1 = PortfolioGroup(
            ticker="AAPL",
            stock_position=stock1,
            option_positions=[option1],
            net_exposure=16200.0,  # 15000 + 1200
            beta=1.2,
            beta_adjusted_exposure=19440.0,  # 18000 + 1440
            total_delta_exposure=1200.0,
            options_delta_exposure=1200.0,
        )

        group2 = PortfolioGroup(
            ticker="MSFT",
            stock_position=stock2,
            option_positions=[],
            net_exposure=17500.0,
            beta=1.1,
            beta_adjusted_exposure=19250.0,
            total_delta_exposure=0.0,
            options_delta_exposure=0.0,
        )

        groups = [group1, group2]

        # Create a mock summary
        from src.folio.data_model import ExposureBreakdown, PortfolioSummary

        long_exposure = ExposureBreakdown(
            stock_exposure=32500.0,  # 15000 + 17500
            stock_beta_adjusted=37250.0,  # 18000 + 19250
            option_delta_exposure=1200.0,
            option_beta_adjusted=1440.0,
            total_exposure=33700.0,  # 32500 + 1200
            total_beta_adjusted=38690.0,  # 37250 + 1440
            description="Long exposure",
            formula="Sum of all long positions",
            components={},
        )

        short_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=0.0,
            option_beta_adjusted=0.0,
            total_exposure=0.0,
            total_beta_adjusted=0.0,
            description="Short exposure",
            formula="Sum of all short positions",
            components={},
        )

        options_exposure = ExposureBreakdown(
            stock_exposure=0.0,
            stock_beta_adjusted=0.0,
            option_delta_exposure=1200.0,
            option_beta_adjusted=1440.0,
            total_exposure=1200.0,
            total_beta_adjusted=1440.0,
            description="Options exposure",
            formula="Sum of all options delta exposures",
            components={},
        )

        summary = PortfolioSummary(
            net_market_exposure=33700.0,  # 15000 + 17500 + 1200
            portfolio_beta=1.15,  # Weighted average
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            options_exposure=options_exposure,
            short_percentage=0.0,
            cash_like_positions=[],
            cash_like_value=0.0,
            cash_like_count=0,
            cash_percentage=0.0,
            portfolio_estimate_value=33700.0,
            price_updated_at=datetime.now().isoformat(),
        )

        # Mock the data fetcher to return specific prices
        mock_fetcher = mocker.MagicMock()
        mock_df_aapl = pd.DataFrame({"Close": [160.0]})  # AAPL price increased to $160
        mock_df_msft = pd.DataFrame({"Close": [340.0]})  # MSFT price decreased to $340
        mock_df_option = pd.DataFrame({"Close": [7.0]})  # Option price increased to $7

        # Configure the mock to return different prices for different tickers
        def mock_fetch_data(
            ticker,
            period=None,  # noqa: ARG001 - period is unused but required by the interface
        ):
            if ticker == "AAPL":
                return mock_df_aapl
            elif ticker == "MSFT":
                return mock_df_msft
            elif ticker == "AAPL230616C00160000":
                return mock_df_option
            return pd.DataFrame()  # Empty dataframe for unknown tickers

        mock_fetcher.fetch_data.side_effect = mock_fetch_data

        # Mock the create_data_fetcher function to return our mock
        mocker.patch(
            "src.folio.portfolio.create_data_fetcher", return_value=mock_fetcher
        )

        # Update prices
        updated_summary = update_portfolio_summary_with_prices(
            groups, summary, mock_fetcher
        )

        # Verify that prices were updated correctly
        assert groups[0].stock_position.price == 160.0
        assert groups[1].stock_position.price == 340.0
        assert groups[0].option_positions[0].price == 7.0

        # Verify that market exposures were recalculated for stocks
        assert groups[0].stock_position.market_exposure == 16000.0  # 100 * 160
        assert groups[1].stock_position.market_exposure == 17000.0  # 50 * 340

        # Verify that beta-adjusted exposures were recalculated for stocks
        assert groups[0].stock_position.beta_adjusted_exposure == 19200.0  # 16000 * 1.2
        assert groups[1].stock_position.beta_adjusted_exposure == 18700.0  # 17000 * 1.1

        # Verify that the portfolio summary was recalculated
        assert updated_summary.net_market_exposure != summary.net_market_exposure
        assert updated_summary.long_exposure.stock_exposure == 33000.0  # 16000 + 17000
        assert (
            updated_summary.long_exposure.stock_beta_adjusted == 37900.0
        )  # 19200 + 18700

        # Verify that the timestamp was updated
        assert updated_summary.price_updated_at != summary.price_updated_at
