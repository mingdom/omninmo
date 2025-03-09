"""
Streamlit app for omninmo.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import joblib
from pathlib import Path

import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.fmp_data_fetcher import FMPDataFetcher
from src.data.features import FeatureEngineer
from src.models.predictor import StockRatingPredictor
from src.utils.analysis import (
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_drawdown,
    plot_interactive_chart,
    plot_technical_indicators,
    generate_summary,
)
from src.utils.trainer import train_on_default_tickers, DEFAULT_TICKERS
from src.utils.model_utils import get_latest_model_path

# Set page config
st.set_page_config(
    page_title="omninmo - Stock Rating Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
MODEL_PATH = "models/stock_rating_model.joblib"
RATING_COLORS = {
    "Strong Buy": "#1E8449",  # Dark Green
    "Buy": "#82E0AA",  # Light Green
    "Hold": "#F4D03F",  # Yellow
    "Sell": "#F5B041",  # Orange
    "Strong Sell": "#C0392B",  # Red
}


def load_or_train_model():
    """
    Load the model if it exists, otherwise train a new one.

    Returns:
        StockRatingPredictor: Loaded or trained model
    """
    model_path = get_latest_model_path()
    
    if os.path.exists(model_path):
        st.sidebar.info("Loading existing model...")
        predictor = StockRatingPredictor(model_path=model_path)
        return predictor
    else:
        st.sidebar.warning("No model found. Training a new model...")
        # Use a smaller set of tickers for demo purposes
        demo_tickers = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "JPM",
            "V",
            "JNJ",
        ]
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        # Train on demo tickers
        predictor = train_on_default_tickers(model_path=model_path)
        if predictor:
            st.sidebar.success("Model trained successfully!")
        else:
            st.sidebar.error("Failed to train model!")
        return predictor


def get_stock_data(ticker, period="1y", interval="1d"):
    """
    Get stock data for a given ticker.

    Args:
        ticker (str): Stock ticker
        period (str): Period to fetch data for
        interval (str): Data interval

    Returns:
        tuple: (df, df_with_indicators, info) where df is the raw data,
               df_with_indicators is the data with technical indicators,
               and info is the company information
    """
    fetcher = FMPDataFetcher()
    feature_engineer = FeatureEngineer()

    # Fetch data
    with st.spinner(f"Fetching data for {ticker}..."):
        df = fetcher.fetch_stock_data(ticker, period=period, interval=interval)
        info = fetcher.fetch_stock_info(ticker)

    if df is None or df.empty:
        st.error(f"No data found for {ticker}")
        return None, None, None

    # Add technical indicators
    with st.spinner("Calculating technical indicators..."):
        df_with_indicators = feature_engineer.add_technical_indicators(df)

    return df, df_with_indicators, info


def predict_rating(model, df_with_indicators):
    """
    Predict rating for a stock.

    Args:
        model (StockRatingPredictor): Trained model
        df_with_indicators (pd.DataFrame): DataFrame with technical indicators

    Returns:
        str: Predicted rating
    """
    feature_engineer = FeatureEngineer()

    # Prepare features
    X, _ = feature_engineer.prepare_features(df_with_indicators)

    if X is None or len(X) == 0:
        st.error("Could not generate features for prediction")
        return None

    # Make prediction
    with st.spinner("Predicting rating..."):
        ratings = model.predict(X)

    # Get the most recent rating
    latest_rating = ratings[-1] if ratings else None

    return latest_rating


def display_company_info(info):
    """
    Display company information.

    Args:
        info (dict): Company information
    """
    if info is None:
        st.warning("No company information available")
        return

    # Create columns for company info
    col1, col2 = st.columns(2)

    with col1:
        # Company name and logo
        if "longName" in info:
            st.subheader(info["longName"])
        elif "shortName" in info:
            st.subheader(info["shortName"])

        # Industry and sector
        if "industry" in info and "sector" in info:
            st.write(f"**Industry:** {info['industry']} | **Sector:** {info['sector']}")

        # Website
        if "website" in info:
            st.write(f"**Website:** [{info['website']}]({info['website']})")

    with col2:
        # Market cap
        if "marketCap" in info:
            market_cap = info["marketCap"]
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.2f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.2f}M"
            else:
                market_cap_str = f"${market_cap:.2f}"
            st.write(f"**Market Cap:** {market_cap_str}")

        # P/E ratio
        if "trailingPE" in info:
            st.write(f"**P/E Ratio:** {info['trailingPE']:.2f}")

        # 52-week range
        if "fiftyTwoWeekLow" in info and "fiftyTwoWeekHigh" in info:
            st.write(
                f"**52-Week Range:** ${info['fiftyTwoWeekLow']:.2f} - ${info['fiftyTwoWeekHigh']:.2f}"
            )

    # Company description
    if "longBusinessSummary" in info:
        with st.expander("Company Description"):
            st.write(info["longBusinessSummary"])


def display_rating(rating, ticker):
    """
    Display the predicted rating.

    Args:
        rating (str): Predicted rating
        ticker (str): Stock ticker
    """
    if rating is None:
        st.warning("Could not predict rating")
        return

    # Get color for rating
    color = RATING_COLORS.get(rating, "#808080")  # Default to gray if rating not found

    # Display rating in a large, colored box
    st.markdown(
        f"""
        <div style="
            background-color: {color};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h1 style="color: white; margin: 0;">omninmo Rating: {rating}</h1>
            <h3 style="color: white; margin: 0;">{ticker}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_stock_charts(df, df_with_indicators, ticker):
    """
    Display stock charts.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        df_with_indicators (pd.DataFrame): DataFrame with technical indicators
        ticker (str): Stock ticker
    """
    if df is None or df.empty:
        st.warning("No data available for charts")
        return

    # Create tabs for different charts
    tab1, tab2 = st.tabs(["Price Chart", "Technical Indicators"])

    with tab1:
        # Display interactive price chart
        fig = plot_interactive_chart(df, ticker)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if df_with_indicators is not None and not df_with_indicators.empty:
            # Display technical indicators chart
            fig = plot_technical_indicators(df_with_indicators, ticker)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Technical indicators not available")


def display_summary(df, ticker, rating):
    """
    Display summary information.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        ticker (str): Stock ticker
        rating (str): Predicted rating
    """
    if df is None or df.empty:
        st.warning("No data available for summary")
        return

    # Generate summary
    summary = generate_summary(df, ticker, rating)

    # Create columns for summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Price Information")
        st.write(f"**Current Price:** ${summary['current_price']:.2f}")
        if summary["change_1d"] is not None:
            change_color = "green" if summary["change_1d"] >= 0 else "red"
            st.write(
                f"**1-Day Change:** <span style='color:{change_color}'>{summary['change_1d']*100:.2f}%</span>",
                unsafe_allow_html=True,
            )
        st.write(f"**Volume:** {summary['volume']:,.0f}")
        if summary["avg_volume_20d"] is not None:
            st.write(f"**Avg. Volume (20d):** {summary['avg_volume_20d']:,.0f}")

    with col2:
        st.subheader("Returns")
        for period in ["1d", "5d", "20d", "60d", "120d", "252d"]:
            if period in summary and summary[period] is not None:
                change_color = "green" if summary[period] >= 0 else "red"
                st.write(
                    f"**{period}:** <span style='color:{change_color}'>{summary[period]:.2f}%</span>",
                    unsafe_allow_html=True,
                )

    with col3:
        st.subheader("Risk Metrics")
        if summary["volatility"] is not None:
            st.write(f"**Volatility (Ann.):** {summary['volatility']*100:.2f}%")
        if summary["sharpe_ratio"] is not None:
            st.write(f"**Sharpe Ratio:** {summary['sharpe_ratio']:.2f}")
        if summary["max_drawdown"] is not None:
            st.write(f"**Max Drawdown:** {summary['max_drawdown']:.2f}%")


def main():
    """
    Main function for the Streamlit app.
    """
    # App title
    st.title("omninmo - Stock Rating Predictor")
    st.markdown("*Input: Stock ticker, Output: omninmo Rating*")

    # Sidebar
    st.sidebar.title("Settings")

    # Load or train model
    model = load_or_train_model()

    # Time period selection
    period_options = {
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y",
        "Max": "max",
    }
    selected_period = st.sidebar.selectbox(
        "Select Time Period", list(period_options.keys()), index=3  # Default to 1 Year
    )
    period = period_options[selected_period]

    # Interval selection
    interval_options = {"Daily": "1d", "Weekly": "1wk", "Monthly": "1mo"}
    selected_interval = st.sidebar.selectbox(
        "Select Interval", list(interval_options.keys()), index=0  # Default to Daily
    )
    interval = interval_options[selected_interval]

    # Stock ticker input
    ticker = st.text_input(
        "Enter Stock Ticker (e.g., NVDA, AAPL, MSFT)", "NVDA"
    ).upper()

    # Button to get prediction
    if st.button("Get Rating"):
        if not ticker:
            st.error("Please enter a stock ticker")
        else:
            # Get stock data
            df, df_with_indicators, info = get_stock_data(
                ticker, period=period, interval=interval
            )

            if df is not None and not df.empty:
                # Predict rating
                rating = predict_rating(model, df_with_indicators)

                # Display rating
                display_rating(rating, ticker)

                # Display company info
                display_company_info(info)

                # Display summary
                display_summary(df, ticker, rating)

                # Display charts
                display_stock_charts(df, df_with_indicators, ticker)

    # Footer
    st.markdown("---")
    st.markdown("omninmo - Stock Rating Predictor | Developed as an MVP")


if __name__ == "__main__":
    main()
