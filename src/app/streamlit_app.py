"""
Streamlit web application for the omninmo stock prediction project.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import project modules
try:
    from src.data.stock_data_fetcher import StockDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.utils.trainer import load_model
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Set page configuration
st.set_page_config(
    page_title="omninmo - Stock Prediction",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def get_data_fetcher():
    cache_dir = os.path.join(project_root, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return StockDataFetcher(cache_dir=cache_dir)

@st.cache_resource
def get_feature_engineer():
    return FeatureEngineer()

@st.cache_resource
def get_model():
    model_path = os.path.join(project_root, "models", "stock_predictor.pkl")
    model = load_model(model_path=model_path)
    if model is None:
        st.warning("Model not found. Please train the model first using 'make train'.")
    return model

# Helper functions
def get_rating_color(rating):
    """Get color based on rating."""
    colors = {
        'Strong Buy': 'green',
        'Buy': 'lightgreen',
        'Hold': 'yellow',
        'Sell': 'orange',
        'Strong Sell': 'red'
    }
    return colors.get(rating, 'gray')

def plot_stock_data(data, ticker):
    """Create interactive stock chart."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{ticker} Price", "Volume"),
        row_heights=[0.7, 0.3]
    )
    
    # Add price candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(0, 0, 255, 0.5)'
        ),
        row=2, col=1
    )
    
    # Add moving averages
    ma_50 = data['Close'].rolling(window=50).mean()
    ma_200 = data['Close'].rolling(window=200).mean()
    
    if not ma_50.isna().all():
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma_50,
                name="50-day MA",
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )
    
    if not ma_200.isna().all():
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma_200,
                name="200-day MA",
                line=dict(color='red', width=1)
            ),
            row=1, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f"{ticker} Stock Data",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=600,
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )
    
    return fig

def plot_technical_indicators(data, features):
    """Create technical indicators chart."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("RSI", "MACD", "Bollinger Bands"),
        row_heights=[0.33, 0.33, 0.33]
    )
    
    # Check if features contain the necessary columns
    if 'RSI' in features.columns:
        # Add RSI
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['RSI'],
                name="RSI",
                line=dict(color='purple', width=1)
            ),
            row=1, col=1
        )
        
        # Add RSI reference lines
        fig.add_trace(
            go.Scatter(
                x=[features.index[0], features.index[-1]],
                y=[70, 70],
                name="Overbought",
                line=dict(color='red', width=1, dash='dash')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[features.index[0], features.index[-1]],
                y=[30, 30],
                name="Oversold",
                line=dict(color='green', width=1, dash='dash')
            ),
            row=1, col=1
        )
    
    if all(col in features.columns for col in ['MACD', 'MACD_Signal', 'MACD_Hist']):
        # Add MACD
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['MACD'],
                name="MACD",
                line=dict(color='blue', width=1)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['MACD_Signal'],
                name="Signal",
                line=dict(color='red', width=1)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=features.index,
                y=features['MACD_Hist'],
                name="Histogram",
                marker_color='rgba(0, 255, 0, 0.5)'
            ),
            row=2, col=1
        )
    
    if all(col in features.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
        # Add Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                name="Price",
                line=dict(color='black', width=1)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['BB_Upper'],
                name="Upper Band",
                line=dict(color='rgba(0, 0, 255, 0.5)', width=1)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['BB_Middle'],
                name="Middle Band",
                line=dict(color='rgba(0, 0, 255, 0.8)', width=1)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=features.index,
                y=features['BB_Lower'],
                name="Lower Band",
                line=dict(color='rgba(0, 0, 255, 0.5)', width=1)
            ),
            row=3, col=1
        )
    
    # Update layout
    fig.update_layout(
        title="Technical Indicators",
        height=800,
        template="plotly_white"
    )
    
    return fig

# Main application
def main():
    # Sidebar
    st.sidebar.title("omninmo")
    st.sidebar.markdown("Stock Performance Prediction")
    
    # Initialize components
    data_fetcher = get_data_fetcher()
    feature_engineer = get_feature_engineer()
    model = get_model()
    
    # Main content
    st.title("omninmo Stock Prediction")
    st.markdown("""
    Enter a stock ticker to get the omninmo Rating and technical analysis.
    """)
    
    # User input
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, NVDA):", "AAPL").upper()
    period = st.select_slider(
        "Select Time Period:",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"],
        value="1y"
    )
    
    # Check environment variable for default sample data setting
    default_use_real_data = not os.environ.get('OMNINMO_USE_SAMPLE_DATA', '').lower() == 'true'
    use_real_data = st.checkbox("Attempt to use real data (may fail due to API issues)", value=default_use_real_data)
    
    if st.button("Analyze"):
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Fetch stock data
                data = data_fetcher.fetch_data(ticker, period=period, force_sample=not use_real_data)
                
                if data is None or data.empty:
                    st.error(f"No data available for {ticker}. Please check the ticker symbol.")
                    st.stop()
                
                # Calculate features
                features = feature_engineer.calculate_indicators(data)
                
                if features is None or features.empty:
                    st.error("Failed to calculate technical indicators.")
                    st.stop()
                
                # Display stock chart
                st.subheader(f"{ticker} Stock Chart")
                fig = plot_stock_data(data, ticker)
                st.plotly_chart(fig, use_container_width=True)
                
                # Make prediction if model is available
                if model is not None:
                    try:
                        # Get the most recent features for prediction
                        recent_features = features.iloc[[-1]]
                        
                        # Make prediction
                        rating, confidence = model.predict(recent_features)
                        
                        # Display prediction
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("omninmo Rating")
                            rating_color = get_rating_color(rating)
                            st.markdown(
                                f"<div style='background-color: {rating_color}; padding: 20px; "
                                f"border-radius: 10px; text-align: center;'>"
                                f"<h1 style='color: white;'>{rating}</h1>"
                                f"<p style='color: white;'>Confidence: {confidence:.2%}</p>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            st.subheader("Key Indicators")
                            indicators = {}
                            
                            # Only include indicators that exist in the features
                            if 'RSI' in features.columns:
                                indicators["RSI"] = features.iloc[-1]['RSI']
                            if 'MACD' in features.columns:
                                indicators["MACD"] = features.iloc[-1]['MACD']
                            if 'Price_to_SMA_50' in features.columns:
                                indicators["Price to 50-day MA"] = features.iloc[-1]['Price_to_SMA_50']
                            if 'Price_to_SMA_200' in features.columns:
                                indicators["Price to 200-day MA"] = features.iloc[-1]['Price_to_SMA_200']
                            if 'BB_Width' in features.columns:
                                indicators["Bollinger Band Width"] = features.iloc[-1]['BB_Width']
                            
                            for name, value in indicators.items():
                                st.metric(name, f"{value:.2f}")
                    except Exception as e:
                        st.error(f"Error making prediction: {e}")
                        logger.error(f"Error making prediction: {e}")
                
                # Display technical indicators
                st.subheader("Technical Analysis")
                fig2 = plot_technical_indicators(data, features)
                st.plotly_chart(fig2, use_container_width=True)
                
                # Display recent data
                st.subheader("Recent Data")
                st.dataframe(data.tail(10))
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                logger.error(f"Error analyzing {ticker}: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("omninmo - Stock Performance Prediction")

if __name__ == "__main__":
    main() 