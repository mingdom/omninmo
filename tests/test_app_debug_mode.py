"""Tests for app debug mode configuration."""

import os
from unittest.mock import patch

import pytest

from src.folio.app import create_app


@pytest.fixture
def mock_environment_variables():
    """Fixture to mock environment variables."""
    original_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_environ)


def test_debug_mode_disabled_in_production():
    """Test that debug mode is disabled in production environments."""
    # Mock the environment variables to simulate production environment
    with patch.dict(os.environ, {"HF_SPACE": "1", "ENVIRONMENT": "production"}):
        # Mock the existence of /.dockerenv to simulate Docker environment
        with patch("os.path.exists", return_value=True):
            # Create the app with debug=True (should be overridden)
            with patch("src.folio.app.logger"):  # Mock logger to avoid actual logging
                app = create_app(debug_mode=True, is_reloader=False)

                # Verify that debug mode is disabled
                assert not getattr(app, "_debug_mode", True)

                # Verify that the app's server debug mode would be disabled
                # Note: We don't actually call run_server, so we check the attribute


def test_debug_mode_enabled_in_development():
    """Test that debug mode is enabled in development environments."""
    # Mock the environment variables to simulate development environment
    with patch.dict(os.environ, {"HF_SPACE": "", "ENVIRONMENT": "development"}):
        # Mock the existence of /.dockerenv to simulate Docker environment
        with patch("os.path.exists", return_value=False):
            # Create the app with debug=True
            with patch("src.folio.app.logger"):  # Mock logger to avoid actual logging
                app = create_app(debug_mode=True, is_reloader=False)

                # Verify that debug mode is enabled
                assert getattr(app, "_debug_mode", False)

                # Verify that the app's server debug mode would be enabled
                # Note: We don't actually call run_server, so we check the attribute
