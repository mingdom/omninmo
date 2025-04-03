"""AI Chat component for portfolio analysis."""

import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

logger = logging.getLogger(__name__)

def create_ai_chat_panel() -> html.Div:
    """Create the AI chat panel with collapsible content."""
    return html.Div(
        [
            # Floating button to toggle the chat panel
            html.Div(
                dbc.Button(
                    [
                        html.I(className="fas fa-robot me-2"),
                        "AI Advisor"
                    ],
                    id="toggle-chat-button",
                    color="primary",
                    className="ai-toggle-button",
                ),
                className="ai-toggle-container"
            ),

            # Collapsible chat panel
            dbc.Collapse(
                html.Div(
                    [
                        # Chat header
                        html.Div(
                            [
                                html.H4(
                                    [
                                        html.I(className="fas fa-robot me-2"),
                                        "Portfolio AI Advisor"
                                    ],
                                    className="m-0"
                                ),
                                dbc.Button(
                                    html.I(className="fas fa-times"),
                                    id="close-chat-button",
                                    color="link",
                                    size="sm",
                                    className="p-0 border-0"
                                )
                            ],
                            className="d-flex justify-content-between align-items-center p-3 border-bottom"
                        ),

                        # Chat messages container
                        html.Div(
                            [
                                # Welcome message
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(className="fas fa-robot ai-avatar"),
                                                html.Div(
                                                    dcc.Markdown(
                                                        """
                                                        👋 Hello! I'm your AI Portfolio Advisor powered by Google Gemini 2.5 Pro.

                                                        I can help you analyze your portfolio and provide insights on:
                                                        - Risk assessment
                                                        - Sector concentration
                                                        - Diversification
                                                        - Improvement recommendations

                                                        What would you like to know about your portfolio?
                                                        """,
                                                        className="ai-message-content"
                                                    ),
                                                    className="ai-message-bubble"
                                                )
                                            ],
                                            className="ai-message"
                                        )
                                    ],
                                    id="chat-messages",
                                    className="chat-messages p-3"
                                ),

                                # Loading indicator
                                html.Div(
                                    dbc.Spinner(color="primary", size="sm"),
                                    id="chat-loading",
                                    className="chat-loading p-3 d-none"
                                ),

                                # Input area
                                html.Div(
                                    [
                                        dbc.Textarea(
                                            id="chat-input",
                                            placeholder="Ask about your portfolio...",
                                            className="chat-input",
                                            rows=1,
                                            style={"resize": "none"}
                                        ),
                                        dbc.Button(
                                            html.I(className="fas fa-paper-plane"),
                                            id="send-message-button",
                                            color="primary",
                                            className="send-button ms-2"
                                        )
                                    ],
                                    className="d-flex align-items-center p-3 border-top"
                                )
                            ],
                            className="chat-container"
                        )
                    ],
                    className="ai-chat-panel"
                ),
                id="ai-chat-collapse",
                is_open=False,
            ),

            # Store for chat history
            dcc.Store(id="chat-history", data={"messages": []}),

            # Store for chat portfolio data
            dcc.Store(id="chat-portfolio-data", data=None)
        ],
        className="ai-chat-container"
    )

def create_user_message(message: str) -> html.Div:
    """Create a user message bubble."""
    return html.Div(
        [
            html.Div(
                dcc.Markdown(message, className="user-message-content"),
                className="user-message-bubble"
            ),
            html.I(className="fas fa-user user-avatar")
        ],
        className="user-message"
    )

def create_ai_message(message: str) -> html.Div:
    """Create an AI message bubble."""
    return html.Div(
        [
            html.I(className="fas fa-robot ai-avatar"),
            html.Div(
                dcc.Markdown(message, className="ai-message-content"),
                className="ai-message-bubble"
            )
        ],
        className="ai-message"
    )

def format_analysis_for_chat(analysis: dict[str, Any]) -> str:
    """Format analysis results for chat display."""
    if analysis.get("error"):
        return f"Error: {analysis.get('message')}"

    sections = []

    # Risk Assessment
    if analysis.get("risk_assessment"):
        sections.append("## Risk Assessment\n" + analysis["risk_assessment"])

    # Sector Concentration
    if analysis.get("sector_concentration"):
        sections.append("## Sector Concentration\n" + analysis["sector_concentration"])

    # Diversification
    if analysis.get("diversification"):
        sections.append("## Diversification\n" + analysis["diversification"])

    # Recommendations
    if analysis.get("recommendations"):
        sections.append("## Recommendations\n" + analysis["recommendations"])

    return "\n\n".join(sections)
