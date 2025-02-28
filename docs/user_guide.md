# User Guide

This guide provides instructions for using the omninmo stock prediction application.

## Getting Started

After following the installation steps in the [Setup Guide](./setup_guide.md), you can launch the application with:

```bash
python run_app.py
```

This will open the Streamlit web interface in your default browser, typically at http://localhost:8501.

## Using the Web Interface

### Main Dashboard

The main dashboard provides an overview of the application's capabilities and a search box for entering stock tickers.

### Analyzing a Stock

1. **Enter a Stock Ticker**
   - Type a valid stock ticker symbol (e.g., AAPL, MSFT, NVDA) in the search box
   - Click the "Analyze" button or press Enter

2. **View Stock Data**
   - The application will display historical price data for the selected stock
   - Interactive charts show price movements and key technical indicators

3. **Prediction Results**
   - The omninmo Rating will be displayed prominently (e.g., Strong Buy, Buy, Hold, Sell, Strong Sell)
   - The rating is color-coded for easy interpretation (green for buy ratings, red for sell ratings)
   - Confidence metrics show how certain the model is about its prediction

4. **Technical Analysis**
   - Scroll down to view detailed technical indicators
   - Hover over charts for specific data points
   - Use the interactive controls to adjust time periods or indicators

### Advanced Features

1. **Comparative Analysis**
   - Compare multiple stocks by entering comma-separated tickers
   - View side-by-side comparisons of ratings and key metrics

2. **Historical Performance**
   - Check how previous predictions performed over time
   - View backtesting results for the prediction model

3. **Custom Time Periods**
   - Adjust the time period for analysis using the date range selector
   - Compare short-term vs. long-term predictions

## Command-Line Usage

For quick predictions without the web interface, use the command-line tool:

```bash
python predict_ticker.py TICKER_SYMBOL
```

Replace `TICKER_SYMBOL` with a stock ticker (e.g., AAPL, MSFT, NVDA).

Example output:
```
Analyzing AAPL...
omninmo Rating: BUY (Confidence: 78%)
Key Indicators:
- RSI: 62.4 (Neutral)
- MACD: Positive (Bullish)
- Moving Averages: Above 50-day and 200-day (Bullish)
```

## Interpreting Results

### Rating Categories

- **Strong Buy**: High confidence in positive future performance
- **Buy**: Moderate confidence in positive future performance
- **Hold**: Neutral outlook or uncertain direction
- **Sell**: Moderate confidence in negative future performance
- **Strong Sell**: High confidence in negative future performance

### Confidence Metrics

The confidence percentage indicates how certain the model is about its prediction. Higher percentages indicate greater confidence.

### Technical Indicators

The application uses several technical indicators for its predictions:

- **Relative Strength Index (RSI)**: Measures momentum
- **Moving Average Convergence Divergence (MACD)**: Trend-following momentum indicator
- **Simple Moving Averages (SMA)**: Average price over specific time periods
- **Bollinger Bands**: Volatility indicator

## Troubleshooting

### Common Issues

1. **No Data Available**
   - Ensure you entered a valid ticker symbol
   - Check your internet connection
   - Some tickers may not be available through the current data provider

2. **Slow Performance**
   - Initial analysis may take longer as data is fetched and processed
   - Subsequent analyses of the same ticker will be faster due to caching

3. **Unexpected Results**
   - Stock prediction is inherently uncertain
   - The model uses historical data and technical analysis, but cannot account for unexpected news or events

### Getting Help

If you encounter any issues not covered here, please refer to the [Development Guide](./development_guide.md) or open an issue on the project repository. 