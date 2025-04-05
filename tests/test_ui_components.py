"""Tests for UI components.

This module tests the UI components of the Folio application.
"""

import dash_bootstrap_components as dbc
from dash import html

from src.folio.components.charts import create_dashboard_section


def test_dashboard_section_structure():
    """Test that the dashboard section has the correct structure."""
    # Create the dashboard section
    dashboard = create_dashboard_section()

    # Check that it's a div
    assert isinstance(dashboard, html.Div)

    # Check that it has two cards (summary and charts)
    assert len(dashboard.children) == 2

    # Check that the first card is the summary section
    summary_section = dashboard.children[0]
    assert isinstance(summary_section, dbc.Card)

    # Check that the summary section has the correct ID for the collapse button
    assert summary_section.children[0].children.id == "summary-collapse-button"

    # Check that the summary section has the correct IDs for the metrics
    summary_body = summary_section.children[1].children

    # Check that the metrics have the correct IDs
    metric_ids = [
        "total-value",
        "total-beta",
        "long-exposure",
        "long-beta",
        "short-exposure",
        "short-beta",
        "options-exposure",
        "options-beta",
        "cash-like-value",
        "cash-like-percent",
    ]

    # Extract all IDs from the summary body
    all_ids = []

    def extract_ids(component):
        """Recursively extract all IDs from a component."""
        if hasattr(component, "id") and component.id is not None:
            all_ids.append(component.id)

        if hasattr(component, "children") and component.children is not None:
            if isinstance(component.children, list):
                for child in component.children:
                    extract_ids(child)
            else:
                extract_ids(component.children)

    extract_ids(summary_body)

    # Check that all required IDs are present
    for metric_id in metric_ids:
        assert metric_id in all_ids, f"Missing ID: {metric_id}"


def test_dashboard_metrics_ids():
    """Test that the dashboard metrics IDs match the ones used in the app.py callbacks."""
    # Create the dashboard section
    dashboard = create_dashboard_section()

    # Extract all IDs from the dashboard
    all_ids = []

    def extract_ids(component):
        """Recursively extract all IDs from a component."""
        if hasattr(component, "id") and component.id is not None:
            all_ids.append(component.id)

        if hasattr(component, "children") and component.children is not None:
            if isinstance(component.children, list):
                for child in component.children:
                    extract_ids(child)
            else:
                extract_ids(component.children)

    extract_ids(dashboard)

    # Check that all required IDs are present
    required_ids = [
        "total-value",
        "total-value-percent",
        "total-beta",
        "long-exposure",
        "long-exposure-percent",
        "long-beta",
        "short-exposure",
        "short-exposure-percent",
        "short-beta",
        "options-exposure",
        "options-exposure-percent",
        "options-beta",
        "cash-like-value",
        "cash-like-percent",
    ]

    for required_id in required_ids:
        assert required_id in all_ids, f"Missing ID: {required_id}"
