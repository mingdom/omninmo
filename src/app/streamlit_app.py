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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Import project modules
try:
    from src.data.fmp_data_fetcher import FMPDataFetcher
    from src.utils.feature_engineer import FeatureEngineer
    from src.utils.trainer import load_model
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Default watch list
DEFAULT_WATCHLIST = [
    "GOOGL", "AMZN", "AAPL", "META", "NVDA", "CRWD", "FTNT", "UBER", "LRCX", "LULU",
    "BKNG", "AXP", "V", "AMAT", "PANW", "QCOM", "ZS", "APP", "HPE", "PLTR",
    "AI", "BABA", "PDD", "ANET", "SNOW", "WDAY", "CRM", "IONQ", "MELI", "BKNG"
]

# Set page configuration
st.set_page_config(
    page_title="omninmo - Stock Prediction",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #757575;
    }
    .last-updated {
        font-size: 0.8rem;
        color: #757575;
        font-style: italic;
    }
    .watchlist-item {
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .watchlist-item:hover {
        background-color: #f0f0f0;
    }
    .rating-badge {
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
    }
    .strong-buy {
        background-color: green;
        color: white;
    }
    .buy {
        background-color: lightgreen;
        color: black;
    }
    .hold {
        background-color: yellow;
        color: black;
    }
    .sell {
        background-color: orange;
        color: black;
    }
    .strong-sell {
        background-color: red;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def get_data_fetcher():
    cache_dir = os.path.join(project_root, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Use FMP data fetcher by default, fall back to Yahoo Finance if needed
    try:
        logger.info("Initializing FMP data fetcher")
        return FMPDataFetcher(cache_dir=cache_dir)
    except Exception as e:
        logger.warning(f"Failed to initialize FMP data fetcher: {e}. Falling back to Yahoo Finance.")
        return FMPDataFetcher(cache_dir=cache_dir)

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
    """Get background and text colors based on rating."""
    colors = {
        'Strong Buy': {'bg': 'green', 'text': 'white'},
        'Buy': {'bg': 'lightgreen', 'text': 'black'},
        'Hold': {'bg': 'yellow', 'text': 'black'},
        'Sell': {'bg': 'orange', 'text': 'black'},
        'Strong Sell': {'bg': 'red', 'text': 'white'}
    }
    return colors.get(rating, {'bg': 'gray', 'text': 'white'})

def get_rating_class(rating):
    """Get CSS class for rating."""
    classes = {
        'Strong Buy': 'strong-buy',
        'Buy': 'buy',
        'Hold': 'hold',
        'Sell': 'sell',
        'Strong Sell': 'strong-sell'
    }
    return classes.get(rating, '')

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

# Fix caching issue by adding underscore prefix to non-hashable parameters
@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def analyze_ticker(ticker, period, _data_fetcher, _feature_engineer, _model, use_sample_data=False):
    """Analyze a single ticker and return the results."""
    try:
        # Fetch stock data
        data = _data_fetcher.fetch_data(ticker, period=period, force_sample=use_sample_data)
        
        if data is None or data.empty:
            logger.warning(f"No data available for {ticker}")
            return None
        
        # Calculate features
        features = _feature_engineer.calculate_indicators(data)
        
        if features is None or features.empty:
            logger.warning(f"Failed to calculate indicators for {ticker}")
            return None
        
        # Make prediction if model is available
        if _model is not None:
            # Get the most recent features for prediction
            recent_features = features.iloc[[-1]]
            
            # Make prediction
            rating, confidence = _model.predict(recent_features)
            
            # Get latest price and change
            latest_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else latest_price
            price_change = latest_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0
            
            # Get key indicators
            indicators = {}
            if 'RSI' in features.columns:
                indicators["RSI"] = features.iloc[-1]['RSI']
            if 'MACD' in features.columns:
                indicators["MACD"] = features.iloc[-1]['MACD']
            if 'Price_to_SMA_50' in features.columns:
                indicators["Price_to_SMA_50"] = features.iloc[-1]['Price_to_SMA_50']
            if 'Price_to_SMA_200' in features.columns:
                indicators["Price_to_SMA_200"] = features.iloc[-1]['Price_to_SMA_200']
            if 'BB_Width' in features.columns:
                indicators["BB_Width"] = features.iloc[-1]['BB_Width']
            
            return {
                'ticker': ticker,
                'data': data,
                'features': features,
                'rating': rating,
                'confidence': confidence,
                'latest_price': latest_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'indicators': indicators,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return None

def analyze_single_ticker_for_watchlist(ticker, period, data_fetcher, feature_engineer, model, use_sample_data=False):
    """Wrapper function to analyze a single ticker for the watchlist without Streamlit caching."""
    try:
        # Fetch stock data
        data = data_fetcher.fetch_data(ticker, period=period, force_sample=use_sample_data)
        
        if data is None or data.empty:
            logger.warning(f"No data available for {ticker}")
            return None
        
        # Calculate features
        features = feature_engineer.calculate_indicators(data)
        
        if features is None or features.empty:
            logger.warning(f"Failed to calculate indicators for {ticker}")
            return None
        
        # Make prediction if model is available
        if model is not None:
            # Get the most recent features for prediction
            recent_features = features.iloc[[-1]]
            
            # Make prediction
            rating, confidence = model.predict(recent_features)
            
            # Get latest price and change
            latest_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else latest_price
            price_change = latest_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price > 0 else 0
            
            # Get key indicators
            indicators = {}
            if 'RSI' in features.columns:
                indicators["RSI"] = features.iloc[-1]['RSI']
            if 'MACD' in features.columns:
                indicators["MACD"] = features.iloc[-1]['MACD']
            if 'Price_to_SMA_50' in features.columns:
                indicators["Price_to_SMA_50"] = features.iloc[-1]['Price_to_SMA_50']
            if 'Price_to_SMA_200' in features.columns:
                indicators["Price_to_SMA_200"] = features.iloc[-1]['Price_to_SMA_200']
            if 'BB_Width' in features.columns:
                indicators["BB_Width"] = features.iloc[-1]['BB_Width']
            
            return {
                'ticker': ticker,
                'data': data,
                'features': features,
                'rating': rating,
                'confidence': confidence,
                'latest_price': latest_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'indicators': indicators,
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return None

def analyze_watchlist(tickers, period, data_fetcher, feature_engineer, model, use_sample_data=False, max_workers=5):
    """Analyze multiple tickers in parallel and return the results."""
    results = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Create a list to store futures and results
    futures = []
    
    # Use ThreadPoolExecutor to parallelize the analysis
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        for ticker in tickers:
            future = executor.submit(
                analyze_single_ticker_for_watchlist, 
                ticker, 
                period, 
                data_fetcher, 
                feature_engineer, 
                model, 
                use_sample_data
            )
            futures.append((future, ticker))
        
        # Process results as they complete
        completed = 0
        for future, ticker in futures:
            try:
                result = future.result()
                if result:
                    results[ticker] = result
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
            
            # Update progress
            completed += 1
            progress = completed / len(tickers)
            progress_bar.progress(progress)
            status_text.text(f"Analyzed {completed}/{len(tickers)} stocks...")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return results

def display_watchlist_table(watchlist_results):
    """Display the watchlist as an interactive table."""
    if not watchlist_results:
        st.warning("No data available for the watchlist. Please try again later.")
        return None
    
    # Prepare data for the table
    table_data = []
    for ticker, result in watchlist_results.items():
        if result:
            table_data.append({
                'Ticker': ticker,
                'Price': f"${result['latest_price']:.2f}",
                'Change': f"{result['price_change_pct']:.2f}%",
                'Rating': result['rating'],
                'Confidence': f"{result['confidence']:.2%}",
                'RSI': f"{result['indicators'].get('RSI', 0):.2f}" if 'RSI' in result['indicators'] else "N/A",
                'Last Updated': result['last_updated']
            })
    
    if not table_data:
        st.warning("No valid data in the watchlist. Please try again later.")
        return None
    
    # Convert to DataFrame for display
    df = pd.DataFrame(table_data)
    
    # Add color coding for price change
    def color_change(val):
        try:
            val = float(val.strip('%'))
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
            else:
                return ''
        except:
            return ''
    
    # Add color coding for rating
    def color_rating(val):
        rating_class = get_rating_class(val)
        return f'background-color: {get_rating_color(val)["bg"]}; color: {get_rating_color(val)["text"]}'
    
    # Style the DataFrame
    styled_df = df.style.applymap(color_change, subset=['Change'])
    styled_df = styled_df.applymap(color_rating, subset=['Rating'])
    
    # Display the table
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    return df

def display_stock_details(ticker, result):
    """Display detailed analysis for a single stock."""
    if not result:
        st.error(f"No data available for {ticker}. Please try again later.")
        return
    
    data = result['data']
    features = result['features']
    rating = result['rating']
    confidence = result['confidence']
    indicators = result['indicators']
    
    # Display prediction and key indicators at the top
    st.markdown(f"<h2 class='sub-header'>{ticker} Analysis Results</h2>", unsafe_allow_html=True)
    
    # Add last updated timestamp
    st.markdown(f"<p class='last-updated'>Last updated: {result['last_updated']}</p>", unsafe_allow_html=True)
    
    # Create two columns for rating and indicators
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("omninmo Rating")
        rating_colors = get_rating_color(rating)
        st.markdown(
            f"<div style='background-color: {rating_colors['bg']}; padding: 20px; "
            f"border-radius: 10px; text-align: center;'>"
            f"<h1 style='color: {rating_colors['text']};'>{rating}</h1>"
            f"<p style='color: {rating_colors['text']};'>Confidence: {confidence:.2%}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.subheader("Key Indicators")
        for name, value in indicators.items():
            display_name = name.replace('_', ' ')
            st.metric(display_name, f"{value:.2f}")
    
    # Display stock chart
    st.markdown("<h2 class='sub-header'>Stock Chart</h2>", unsafe_allow_html=True)
    fig = plot_stock_data(data, ticker)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display technical indicators
    st.markdown("<h2 class='sub-header'>Technical Analysis</h2>", unsafe_allow_html=True)
    fig2 = plot_technical_indicators(data, features)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Display recent data
    st.markdown("<h2 class='sub-header'>Recent Data</h2>", unsafe_allow_html=True)
    st.dataframe(data.tail(10))

# Main application
def main():
    # Initialize session state for selected ticker
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = None
    
    # Sidebar
    st.sidebar.title("omninmo")
    st.sidebar.markdown("Stock Performance Prediction")
    
    # Initialize components
    data_fetcher = get_data_fetcher()
    feature_engineer = get_feature_engineer()
    model = get_model()
    
    # Move user inputs to sidebar
    st.sidebar.subheader("Analysis Controls")
    
    # Add tabs for Watch List and Single Stock Analysis
    tab_options = ["Watch List", "Single Stock Analysis"]
    selected_tab = st.sidebar.radio("Select View:", tab_options)
    
    # Period selection (used by both tabs)
    period = st.sidebar.select_slider(
        "Select Time Period:",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"],
        value="1y"
    )
    
    # Check environment variable for default sample data setting
    default_use_sample_data = os.environ.get('OMNINMO_USE_SAMPLE_DATA', '').lower() == 'true'
    use_sample_data = st.sidebar.checkbox("Use sample data instead of real data (recommended if API issues occur)", value=default_use_sample_data)
    
    # Main content
    st.markdown("<h1 class='main-header'>omninmo Stock Prediction</h1>", unsafe_allow_html=True)
    
    if selected_tab == "Watch List":
        st.markdown("<div class='info-box'>Your personalized watch list with AI-powered stock ratings.</div>", unsafe_allow_html=True)
        
        # Allow customization of watch list
        watchlist_input = st.sidebar.text_area("Customize Watch List (comma-separated tickers):", 
                                              value=",".join(DEFAULT_WATCHLIST))
        
        # Parse the watch list
        watchlist = [ticker.strip().upper() for ticker in watchlist_input.split(",") if ticker.strip()]
        
        # Button to analyze the watch list
        analyze_button = st.sidebar.button("Analyze Watch List")
        
        if analyze_button or ('watchlist_results' not in st.session_state):
            with st.spinner("Analyzing watch list..."):
                # Analyze the watch list
                watchlist_results = analyze_watchlist(
                    watchlist, period, data_fetcher, feature_engineer, model, use_sample_data
                )
                
                # Store results in session state
                st.session_state.watchlist_results = watchlist_results
        
        # Display the watch list table
        st.subheader("Watch List")
        watchlist_df = display_watchlist_table(st.session_state.get('watchlist_results', {}))
        
        # Allow selection of a ticker from the watch list
        if watchlist_df is not None:
            st.markdown("### Select a ticker from the watch list for detailed analysis")
            selected_ticker = st.selectbox("", watchlist_df['Ticker'].tolist())
            
            if st.button("Show Detailed Analysis"):
                st.session_state.selected_ticker = selected_ticker
                st.session_state.selected_tab = "Single Stock Analysis"
                st.experimental_rerun()
    
    else:  # Single Stock Analysis
        st.markdown("<div class='info-box'>Get AI-powered stock ratings and technical analysis for any ticker.</div>", unsafe_allow_html=True)
        
        # Ticker input for single stock analysis
        ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, NVDA):", 
                                      value=st.session_state.selected_ticker or "AAPL").upper()
        
        # Reset selected ticker
        st.session_state.selected_ticker = None
        
        # Button to analyze the single stock
        analyze_button = st.sidebar.button("Analyze")
        
        if analyze_button:
            with st.spinner(f"Analyzing {ticker}..."):
                # Analyze the single stock
                result = analyze_ticker(ticker, period, data_fetcher, feature_engineer, model, use_sample_data)
                
                if result:
                    # Display the stock details
                    display_stock_details(ticker, result)
                else:
                    st.error(f"No data available for {ticker}. Please check the ticker symbol.")
        else:
            # Display instructions when no analysis has been run
            st.info("👈 Enter a stock ticker in the sidebar and click 'Analyze' to get started.")
    
    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='footer'>omninmo - Stock Performance Prediction</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 