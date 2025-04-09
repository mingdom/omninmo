"""Tests for the navbar component."""

import dash_bootstrap_components as dbc

from src.folio.components.navbar import create_navbar, register_callbacks


def test_create_navbar():
    """Test that the navbar component is created correctly."""
    # Create the navbar
    navbar = create_navbar()

    # Check that it's a dbc.Navbar component
    assert isinstance(navbar, dbc.Navbar)

    # Check that it contains the expected elements
    navbar_str = str(navbar)
    assert "olio" in navbar_str  # Check for the 'olio' part of the logo
    assert "logo-letter-primary" in navbar_str  # Check for the styled 'F'
    assert "price-timestamp-display" in str(navbar)
    assert "update-prices-button" in str(navbar)


def test_register_callbacks(mocker):
    """Test that the navbar callbacks are registered correctly."""
    # Create a mock app
    app = mocker.MagicMock()
    app.callback = mocker.MagicMock()

    # Register the callbacks
    register_callbacks(app)

    # Check that the callback was registered
    assert app.callback.call_count >= 2

    # Check that the callbacks were registered with the correct outputs
    output_ids = []
    for call in app.callback.call_args_list:
        args, _ = call
        outputs = args[0]
        if not isinstance(outputs, list):
            outputs = [outputs]
        for output in outputs:
            output_ids.append(output.component_id)

    assert "price-timestamp-display" in output_ids
    assert "portfolio-summary" in output_ids
    assert "portfolio-groups" in output_ids
