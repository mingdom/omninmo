"""AI Advisor panel component for portfolio dashboard."""

import logging
from typing import Dict, Any

import dash_bootstrap_components as dbc
from dash import html, dcc

logger = logging.getLogger(__name__)

def create_ai_advisor_panel() -> html.Div:
    """Create the AI advisor panel with collapsible content."""
    return html.Div(
        [
            # Floating button to toggle the panel
            html.Div(
                dbc.Button(
                    html.I(className="fas fa-robot"),
                    id="toggle-advisor-button",
                    color="primary",
                    className="rounded-circle p-3 ai-toggle-button",
                    title="AI Portfolio Advisor"
                ),
                className="ai-toggle-container"
            ),
            
            # Collapsible panel
            dbc.Collapse(
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4(
                                    [
                                        html.I(className="fas fa-robot me-2"),
                                        "AI Portfolio Advisor"
                                    ],
                                    className="mb-3"
                                ),
                                html.Hr(),
                                html.P(
                                    "Get AI-powered insights and analysis for your portfolio.",
                                    className="mb-4"
                                ),
                                dbc.Button(
                                    "Analyze Portfolio",
                                    id="analyze-portfolio-button",
                                    color="primary",
                                    className="w-100 mb-3"
                                ),
                                dbc.Collapse(
                                    dbc.Card(
                                        [
                                            dbc.CardHeader("AI Analysis Results"),
                                            dbc.CardBody(
                                                [
                                                    html.Div(id="ai-analysis-content"),
                                                ],
                                                id="ai-analysis-body"
                                            )
                                        ],
                                        className="mb-3"
                                    ),
                                    id="ai-analysis-collapse",
                                    is_open=False,
                                ),
                                html.Hr(),
                                html.Div(
                                    [
                                        html.Small(
                                            "Powered by Google Gemini 2.5 Pro",
                                            className="text-muted"
                                        ),
                                        html.Br(),
                                        html.Small(
                                            [
                                                "AI analysis is for informational purposes only. ",
                                                "Not financial advice."
                                            ],
                                            className="text-muted"
                                        )
                                    ],
                                    className="mt-auto"
                                )
                            ],
                            className="ai-advisor-content p-3"
                        )
                    ],
                    className="ai-advisor-panel"
                ),
                id="ai-advisor-collapse",
                is_open=False,
            )
        ],
        className="ai-advisor-container"
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
