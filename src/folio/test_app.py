"""Test application to isolate the AI button and portfolio loading issue."""

import os
import logging
import pandas as pd
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",
    ],
    suppress_callback_exceptions=True,
)

# Define the layout
app.layout = html.Div(
    [
        # Header
        html.H1("Test Application", className="mb-4"),
        
        # Portfolio loading section
        html.Div(
            [
                html.H3("Portfolio Loading"),
                dbc.Button(
                    "Load Sample Portfolio",
                    id="load-sample-button",
                    color="primary",
                    className="mb-3"
                ),
                html.Div(id="portfolio-status", className="mt-3")
            ],
            className="mb-4 p-3 border rounded"
        ),
        
        # AI Button (fixed position)
        html.Div(
            [
                html.Button(
                    html.I(className="fas fa-robot"),
                    id="chat-button",
                    style={
                        "position": "fixed",
                        "bottom": "20px",
                        "right": "20px",
                        "zIndex": "9999",
                        "width": "60px",
                        "height": "60px",
                        "borderRadius": "50%",
                        "backgroundColor": "#4facfe",
                        "color": "white",
                        "border": "none",
                        "boxShadow": "0 4px 10px rgba(79, 172, 254, 0.3)",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontSize": "24px"
                    }
                ),
                
                # Chat Panel
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("AI Chat", className="m-0 text-white"),
                                html.Button(
                                    html.I(className="fas fa-times"),
                                    id="close-chat",
                                    style={
                                        "background": "none",
                                        "border": "none",
                                        "color": "white",
                                        "fontSize": "20px"
                                    }
                                )
                            ],
                            style={
                                "display": "flex",
                                "justifyContent": "space-between",
                                "alignItems": "center",
                                "padding": "15px",
                                "background": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                                "color": "white"
                            }
                        ),
                        html.Div(
                            [
                                html.Div(
                                    "Hi! I'm your AI assistant.",
                                    style={
                                        "maxWidth": "80%",
                                        "padding": "10px 15px",
                                        "borderRadius": "15px",
                                        "backgroundColor": "#f0f7ff",
                                        "borderTopLeftRadius": "0",
                                        "alignSelf": "flex-start",
                                        "marginBottom": "10px"
                                    }
                                )
                            ],
                            id="chat-messages",
                            style={
                                "flex": "1",
                                "overflowY": "auto",
                                "padding": "15px",
                                "display": "flex",
                                "flexDirection": "column"
                            }
                        ),
                        html.Div(
                            [
                                dbc.Input(
                                    id="chat-input",
                                    placeholder="Type a message...",
                                    style={
                                        "flex": "1",
                                        "borderRadius": "20px",
                                        "padding": "8px 15px"
                                    }
                                ),
                                html.Button(
                                    html.I(className="fas fa-paper-plane"),
                                    id="send-message",
                                    style={
                                        "backgroundColor": "#4facfe",
                                        "border": "none",
                                        "borderRadius": "50%",
                                        "width": "40px",
                                        "height": "40px",
                                        "marginLeft": "10px",
                                        "color": "white",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }
                                )
                            ],
                            style={
                                "display": "flex",
                                "padding": "10px",
                                "borderTop": "1px solid #eee"
                            }
                        )
                    ],
                    id="chat-panel",
                    style={
                        "position": "fixed",
                        "bottom": "90px",
                        "right": "20px",
                        "width": "350px",
                        "height": "500px",
                        "backgroundColor": "white",
                        "borderRadius": "10px",
                        "boxShadow": "0 5px 20px rgba(0, 0, 0, 0.15)",
                        "display": "none",
                        "flexDirection": "column",
                        "overflow": "hidden",
                        "zIndex": "1000"
                    }
                )
            ],
            id="chat-container"
        ),
        
        # Store for portfolio data
        dcc.Store(id="portfolio-data")
    ],
    className="container py-4"
)

# Callback to toggle chat panel
@app.callback(
    Output("chat-panel", "style"),
    [Input("chat-button", "n_clicks"), Input("close-chat", "n_clicks")],
    [State("chat-panel", "style")],
    prevent_initial_call=True
)
def toggle_chat_panel(open_clicks, close_clicks, current_style):
    """Toggle the chat panel when the button is clicked."""
    logger.info(f"Toggle chat panel - open_clicks: {open_clicks}, close_clicks: {close_clicks}")
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_style
        
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "chat-button":
        current_style["display"] = "flex"
        return current_style
    elif trigger_id == "close-chat":
        current_style["display"] = "none"
        return current_style
        
    return current_style

# Callback to send chat messages
@app.callback(
    [Output("chat-messages", "children"), Output("chat-input", "value")],
    [Input("send-message", "n_clicks"), Input("chat-input", "n_submit")],
    [State("chat-input", "value"), State("chat-messages", "children")],
    prevent_initial_call=True
)
def send_chat_message(send_clicks, input_submit, message, current_messages):
    """Send a message to the AI and display the response."""
    logger.info(f"Send chat message - message: {message}")
    
    if not send_clicks and not input_submit or not message or message.strip() == "":
        raise PreventUpdate
        
    # Get current messages or initialize
    if current_messages is None:
        current_messages = []
    
    # Add user message
    user_message = html.Div(
        message,
        style={
            "maxWidth": "80%",
            "padding": "10px 15px",
            "borderRadius": "15px",
            "backgroundColor": "#e3f2fd",
            "borderTopRightRadius": "0",
            "alignSelf": "flex-end",
            "marginBottom": "10px"
        }
    )
    
    # Add AI response
    ai_response = "I'm a simple AI assistant. I can't actually analyze portfolios yet, but I'm here to demonstrate the UI!"
    ai_message = html.Div(
        ai_response,
        style={
            "maxWidth": "80%",
            "padding": "10px 15px",
            "borderRadius": "15px",
            "backgroundColor": "#f0f7ff",
            "borderTopLeftRadius": "0",
            "alignSelf": "flex-start",
            "marginBottom": "10px"
        }
    )
    
    # Return updated messages and clear input
    return current_messages + [user_message, ai_message], ""

# Callback to load sample portfolio
@app.callback(
    [Output("portfolio-status", "children"), Output("portfolio-data", "data")],
    [Input("load-sample-button", "n_clicks")],
    prevent_initial_call=True
)
def load_sample_portfolio(n_clicks):
    """Load a sample portfolio when the button is clicked."""
    logger.info(f"Load sample portfolio - n_clicks: {n_clicks}")
    
    if not n_clicks:
        raise PreventUpdate
    
    try:
        # Simulate loading a portfolio
        logger.info("Simulating portfolio loading...")
        
        # Create a simple portfolio DataFrame
        data = {
            "Symbol": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "Quantity": [10, 5, 2, 3, 8],
            "Price": [150.0, 300.0, 2800.0, 3300.0, 900.0],
            "Value": [1500.0, 1500.0, 5600.0, 9900.0, 7200.0],
            "Sector": ["Technology", "Technology", "Technology", "Consumer Cyclical", "Automotive"]
        }
        df = pd.DataFrame(data)
        
        # Process the portfolio data
        logger.info("Processing portfolio data...")
        portfolio_data = df.to_dict("records")
        
        return html.Div([
            html.P("Portfolio loaded successfully!", className="text-success"),
            html.P(f"Loaded {len(portfolio_data)} positions.")
        ]), portfolio_data
        
    except Exception as e:
        logger.error(f"Error loading portfolio: {str(e)}", exc_info=True)
        return html.Div(f"Error loading portfolio: {str(e)}", className="text-danger"), None

# Run the app
if __name__ == "__main__":
    logger.info("Starting test application...")
    app.run_server(debug=True)
