"""
Stock analysis and visualization utilities for omninmo.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def calculate_returns(df, periods=[1, 5, 20, 60, 120, 252]):
    """
    Calculate returns for different periods.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        periods (list): List of periods to calculate returns for

    Returns:
        dict: Dictionary with returns for each period
    """
    returns = {}
    for period in periods:
        if len(df) > period:
            returns[f"{period}d"] = (
                df["Close"].iloc[-1] / df["Close"].iloc[-period - 1] - 1
            ) * 100
        else:
            returns[f"{period}d"] = None

    return returns


def calculate_volatility(df, window=20):
    """
    Calculate volatility.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        window (int): Window for volatility calculation

    Returns:
        float: Volatility (annualized)
    """
    if len(df) < window:
        return None

    # Calculate daily returns
    returns = df["Close"].pct_change().dropna()

    # Calculate volatility (standard deviation of returns)
    volatility = returns.std() * np.sqrt(252)  # Annualized

    return volatility


def calculate_sharpe_ratio(df, risk_free_rate=0.02, window=252):
    """
    Calculate Sharpe ratio.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        risk_free_rate (float): Risk-free rate (annual)
        window (int): Window for Sharpe ratio calculation

    Returns:
        float: Sharpe ratio
    """
    if len(df) < window:
        return None

    # Calculate daily returns
    returns = df["Close"].pct_change().dropna()

    # Calculate excess returns
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate

    # Calculate Sharpe ratio
    sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252)  # Annualized

    return sharpe_ratio


def calculate_drawdown(df):
    """
    Calculate maximum drawdown.

    Args:
        df (pd.DataFrame): DataFrame with stock data

    Returns:
        tuple: (maximum drawdown, start date, end date)
    """
    # Calculate cumulative returns
    cum_returns = (1 + df["Close"].pct_change().fillna(0)).cumprod()

    # Calculate running maximum
    running_max = cum_returns.cummax()

    # Calculate drawdown
    drawdown = cum_returns / running_max - 1

    # Find maximum drawdown
    max_drawdown = drawdown.min()
    max_drawdown_idx = drawdown.idxmin()

    # Find start of drawdown period
    start_idx = cum_returns[:max_drawdown_idx].idxmax()

    return max_drawdown * 100, start_idx, max_drawdown_idx


def plot_stock_price(df, ticker, figsize=(12, 8)):
    """
    Plot stock price with volume.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        ticker (str): Stock ticker
        figsize (tuple): Figure size

    Returns:
        plt.Figure: Matplotlib figure
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=figsize, gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    # Plot price
    ax1.plot(df.index, df["Close"], label="Close Price")

    # Add moving averages
    if len(df) >= 20:
        ax1.plot(
            df.index,
            df["Close"].rolling(window=20).mean(),
            label="20-day MA",
            alpha=0.7,
        )
    if len(df) >= 50:
        ax1.plot(
            df.index,
            df["Close"].rolling(window=50).mean(),
            label="50-day MA",
            alpha=0.7,
        )
    if len(df) >= 200:
        ax1.plot(
            df.index,
            df["Close"].rolling(window=200).mean(),
            label="200-day MA",
            alpha=0.7,
        )

    ax1.set_title(f"{ticker} Stock Price")
    ax1.set_ylabel("Price")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot volume
    ax2.bar(df.index, df["Volume"], alpha=0.5, color="navy")
    ax2.set_ylabel("Volume")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    return fig


def plot_interactive_chart(df, ticker):
    """
    Create an interactive Plotly chart.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        ticker (str): Stock ticker

    Returns:
        go.Figure: Plotly figure
    """
    # Create subplots
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f"{ticker} Stock Price", "Volume"),
        row_heights=[0.7, 0.3],
    )

    # Add price candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # Add moving averages
    if len(df) >= 20:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"].rolling(window=20).mean(),
                name="20-day MA",
                line=dict(color="rgba(255, 165, 0, 0.7)"),
            ),
            row=1,
            col=1,
        )

    if len(df) >= 50:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"].rolling(window=50).mean(),
                name="50-day MA",
                line=dict(color="rgba(255, 0, 0, 0.7)"),
            ),
            row=1,
            col=1,
        )

    if len(df) >= 200:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"].rolling(window=200).mean(),
                name="200-day MA",
                line=dict(color="rgba(0, 0, 255, 0.7)"),
            ),
            row=1,
            col=1,
        )

    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color="rgba(0, 0, 128, 0.5)"),
        ),
        row=2,
        col=1,
    )

    # Update layout
    fig.update_layout(
        title=f"{ticker} Stock Analysis",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=800,
        width=1000,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


def plot_technical_indicators(df, ticker):
    """
    Create a Plotly figure with technical indicators.

    Args:
        df (pd.DataFrame): DataFrame with technical indicators
        ticker (str): Stock ticker

    Returns:
        go.Figure: Plotly figure
    """
    # Create subplots: 3 rows, 1 column
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=("Price", "RSI & Stochastic", "MACD"),
        row_heights=[0.5, 0.25, 0.25],
    )

    # Add price and Bollinger Bands
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    # Add Bollinger Bands if available
    if "bb_high" in df.columns and "bb_mid" in df.columns and "bb_low" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["bb_high"],
                name="BB Upper",
                line=dict(color="rgba(0, 128, 0, 0.3)"),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["bb_mid"],
                name="BB Middle",
                line=dict(color="rgba(0, 128, 0, 0.7)"),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["bb_low"],
                name="BB Lower",
                line=dict(color="rgba(0, 128, 0, 0.3)"),
            ),
            row=1,
            col=1,
        )

    # Add RSI if available
    if "rsi_14" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["rsi_14"], name="RSI (14)", line=dict(color="blue")
            ),
            row=2,
            col=1,
        )

        # Add RSI reference lines
        fig.add_trace(
            go.Scatter(
                x=[df.index[0], df.index[-1]],
                y=[70, 70],
                name="RSI Overbought",
                line=dict(color="red", dash="dash"),
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=[df.index[0], df.index[-1]],
                y=[30, 30],
                name="RSI Oversold",
                line=dict(color="green", dash="dash"),
            ),
            row=2,
            col=1,
        )

    # Add Stochastic if available
    if "stoch_k" in df.columns and "stoch_d" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["stoch_k"], name="Stoch %K", line=dict(color="orange")
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["stoch_d"], name="Stoch %D", line=dict(color="purple")
            ),
            row=2,
            col=1,
        )

    # Add MACD if available
    if (
        "macd" in df.columns
        and "macd_signal" in df.columns
        and "macd_diff" in df.columns
    ):
        fig.add_trace(
            go.Scatter(x=df.index, y=df["macd"], name="MACD", line=dict(color="blue")),
            row=3,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["macd_signal"],
                name="MACD Signal",
                line=dict(color="red"),
            ),
            row=3,
            col=1,
        )

        # Add MACD histogram
        colors = ["green" if val >= 0 else "red" for val in df["macd_diff"]]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["macd_diff"],
                name="MACD Histogram",
                marker=dict(color=colors),
            ),
            row=3,
            col=1,
        )

    # Update layout
    fig.update_layout(
        title=f"{ticker} Technical Analysis",
        xaxis_title="Date",
        height=900,
        width=1000,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Update y-axis labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="RSI / Stoch", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    return fig


def generate_summary(df, ticker, rating):
    """
    Generate a summary of the stock analysis.

    Args:
        df (pd.DataFrame): DataFrame with stock data
        ticker (str): Stock ticker
        rating (str): Stock rating

    Returns:
        dict: Dictionary with summary information
    """
    summary = {
        "ticker": ticker,
        "rating": rating,
        "current_price": df["Close"].iloc[-1],
        "change_1d": (
            df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1 if len(df) > 1 else None
        ),
        "volume": df["Volume"].iloc[-1],
        "avg_volume_20d": df["Volume"].iloc[-20:].mean() if len(df) >= 20 else None,
    }

    # Add returns
    returns = calculate_returns(df)
    summary.update(returns)

    # Add volatility
    summary["volatility"] = calculate_volatility(df)

    # Add Sharpe ratio
    summary["sharpe_ratio"] = calculate_sharpe_ratio(df)

    # Add maximum drawdown
    max_drawdown, start_date, end_date = calculate_drawdown(df)
    summary["max_drawdown"] = max_drawdown
    summary["max_drawdown_start"] = start_date
    summary["max_drawdown_end"] = end_date

    return summary
