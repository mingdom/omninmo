"""AI analysis component for portfolio dashboard."""

import logging
from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)

def create_ai_analysis_section() -> html.Div:
    """Create the AI analysis section with button and collapsible content."""
    return html.Div(
        [
            # More prominent button with gradient background and larger size
            dbc.Button(
                [
                    html.I(className="fas fa-robot me-2"),
                    "Analyze Portfolio with AI"
                ],
                id="analyze-portfolio-button",
                color="primary",
                size="lg",  # Larger button
                className="mb-3 ai-analyze-button w-100"  # Full width and custom class
            ),
            dbc.Collapse(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H4("AI Portfolio Analysis", className="m-0"),
                            className="ai-card-header"
                        ),
                        dbc.CardBody(
                            [
                                html.Div(id="ai-analysis-content"),
                            ],
                            id="ai-analysis-body"
                        )
                    ],
                    className="mb-3 ai-analysis-card"
                ),
                id="ai-analysis-collapse",
                is_open=False,
            )
        ],
        className="mb-4"
    )

def create_analysis_content(analysis: Dict[str, Any]) -> html.Div:
    """Create formatted content from analysis results."""
    if analysis.get("error"):
        return html.Div(analysis.get("message"), className="text-danger")

    return html.Div([
        html.Div([
            html.H5("Risk Assessment"),
            html.Div(analysis["risk_assessment"], className="analysis-section")
        ], className="mb-3"),

        html.Div([
            html.H5("Sector Concentration"),
            html.Div(analysis["sector_concentration"], className="analysis-section")
        ], className="mb-3"),

        html.Div([
            html.H5("Diversification"),
            html.Div(analysis["diversification"], className="analysis-section")
        ], className="mb-3"),

        html.Div([
            html.H5("Recommendations"),
            html.Div(analysis["recommendations"], className="analysis-section")
        ], className="mb-3"),
    ])
