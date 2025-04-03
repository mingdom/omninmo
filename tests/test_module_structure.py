"""Tests for module structure and dependencies."""

import importlib

import pytest


class TestModuleStructure:
    """Tests for module structure and dependencies."""

    def test_utils_module_functions(self):
        """Test that utils module functions are correctly imported and working."""
        # Import the utils module
        from src.folio import portfolio, utils

        # Verify that key functions exist in utils.py
        assert hasattr(utils, "format_beta")
        assert hasattr(utils, "format_currency")
        assert hasattr(utils, "format_percentage")
        assert hasattr(utils, "get_beta")

        # Verify that key functions exist in portfolio.py
        assert hasattr(portfolio, "process_portfolio_data")
        assert hasattr(portfolio, "is_cash_or_short_term")
        assert hasattr(portfolio, "is_likely_money_market")

        # Test that the formatting functions work correctly
        assert utils.format_beta(1.2) == "1.20β"
        assert utils.format_currency(1500.0) == "$1,500.00"
        assert utils.format_percentage(0.25) == "25.0%"

        # Test cash detection functions
        assert portfolio.is_cash_or_short_term("SPAXX")
        assert portfolio.is_cash_or_short_term("FDRXX")
        assert not portfolio.is_cash_or_short_term("AAPL")

        # Test beta function with a known ticker
        # Note: This might need to be mocked in a real test
        # assert utils.get_beta("SPY") is not None

    def test_module_dependencies(self):
        """Test module dependencies and structure."""
        # Import all key modules to ensure they load correctly
        modules_to_test = [
            "src.folio.utils",
            "src.folio.data_model",
            "src.folio.ai_utils",
            "src.folio.gemini_client",
        ]

        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e!s}")

        # Verify that key classes exist in data_model
        from src.folio import data_model

        assert hasattr(data_model, "PortfolioGroup")
        assert hasattr(data_model, "StockPosition")
        assert hasattr(data_model, "OptionPosition")
        assert hasattr(data_model, "PortfolioSummary")
        assert hasattr(data_model, "ExposureBreakdown")

        # Verify that from_dict methods exist
        assert hasattr(data_model.PortfolioGroup, "from_dict")
        assert hasattr(data_model.StockPosition, "from_dict")
        assert hasattr(data_model.OptionPosition, "from_dict")
        assert hasattr(data_model.PortfolioSummary, "from_dict")
        assert hasattr(data_model.ExposureBreakdown, "from_dict")

        # Verify AI utilities
        from src.folio import ai_utils

        assert hasattr(ai_utils, "prepare_portfolio_data_for_analysis")
        assert hasattr(ai_utils, "PORTFOLIO_ADVISOR_SYSTEM_PROMPT")

        # Verify Gemini client
        from src.folio import gemini_client

        assert hasattr(gemini_client, "GeminiClient")
        assert hasattr(gemini_client.GeminiClient, "chat")
        assert hasattr(gemini_client.GeminiClient, "chat_sync")

    def test_app_imports(self):
        """Test that the app imports are working correctly."""
        try:
            # Import the app module
            from src.folio import app

            # Verify that key components exist
            assert hasattr(app, "create_app")

            # Verify utils import in app
            assert hasattr(app, "utils")

            # Verify that the app can access utils functions
            assert app.utils.format_beta(1.2) == "1.20β"
            assert app.utils.format_currency(1500.0) == "$1,500.00"

        except ImportError as e:
            pytest.fail(f"Failed to import app module: {e!s}")
        except AttributeError as e:
            pytest.fail(f"Failed to access attribute in app module: {e!s}")
