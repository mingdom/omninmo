"""Chat component for the portfolio dashboard."""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import dash
from ..logger import logger


def create_chat_component():
    """Create a chat component using Dash Bootstrap Components."""
    return html.Div(
        [
            # Chat header
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("AI Portfolio Advisor", className="chat-header-title"),
                        html.Button(
                            "×",
                            id="chat-close",
                            className="chat-close-button",
                            n_clicks=0,
                        ),
                    ]
                ),
                className="chat-header",
            ),
            
            # Chat messages container
            dbc.Card(
                dbc.CardBody(
                    html.Div(id="chat-messages", className="chat-messages"),
                    className="chat-messages-container",
                ),
                className="chat-body",
            ),
            
            # Chat input
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.InputGroup(
                            [
                                dbc.Input(
                                    id="chat-input",
                                    placeholder="Ask about your portfolio...",
                                    type="text",
                                    className="chat-input",
                                ),
                                dbc.InputGroupText(
                                    html.Button(
                                        html.I(className="fas fa-paper-plane"),
                                        id="chat-send",
                                        className="chat-send-button",
                                        n_clicks=0,
                                    ),
                                    className="chat-send-container",
                                ),
                            ]
                        ),
                    ]
                ),
                className="chat-footer",
            ),
            
            # Chat history store
            dcc.Store(id="chat-history", storage_type="session"),
        ],
        id="chat-panel",
        className="chat-panel",
        style={"display": "none"},
    )


def format_message(content, is_user=True):
    """Format a chat message."""
    message_class = "user-message" if is_user else "ai-message"
    avatar_class = "user-avatar" if is_user else "ai-avatar"
    avatar_icon = "fa-user" if is_user else "fa-robot"
    
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    html.I(className=f"fas {avatar_icon}"),
                    className=f"message-avatar {avatar_class}",
                ),
                html.Div(
                    dbc.Markdown(content),
                    className="message-content",
                ),
            ],
            className="d-flex",
        ),
        className=f"message-card {message_class} mb-2",
    )


def register_callbacks(app):
    """Register callbacks for the chat component."""
    
    @app.callback(
        Output("chat-panel", "style"),
        [
            Input("chat-button", "n_clicks"),
            Input("chat-close", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def toggle_chat_panel(open_clicks, close_clicks):
        """Toggle the chat panel when the button is clicked."""
        logger.info(f"TOGGLE_CHAT_PANEL called with open_clicks: {open_clicks}, close_clicks: {close_clicks}")
        
        ctx = dash.callback_context
        if not ctx.triggered:
            logger.info("TOGGLE_CHAT_PANEL: No trigger, keeping panel hidden")
            return {"display": "none"}
        
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.info(f"TOGGLE_CHAT_PANEL: Triggered by {trigger_id}")
        
        if trigger_id == "chat-button":
            logger.info("TOGGLE_CHAT_PANEL: Opening chat panel")
            return {"display": "flex"}
        elif trigger_id == "chat-close":
            logger.info("TOGGLE_CHAT_PANEL: Closing chat panel")
            return {"display": "none"}
        
        logger.info("TOGGLE_CHAT_PANEL: Default case, keeping panel hidden")
        return {"display": "none"}
