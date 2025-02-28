# omninmo Application Documentation

## Overview

omninmo is a stock prediction application that uses machine learning to provide stock ratings based on technical indicators. The application analyzes historical stock data, calculates various technical indicators, and uses a RandomForest classifier to predict stock ratings.

## Features

- **Stock Data Analysis**: Fetch and analyze historical stock data
- **Technical Indicators**: Calculate and visualize key technical indicators
- **Prediction Model**: Use machine learning to predict stock ratings
- **Interactive UI**: User-friendly Streamlit interface with interactive charts
- **Command-line Tools**: Quick predictions and model training from the command line

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/omninmo.git
   cd omninmo
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Application

Run the Streamlit web application:

```bash
python scripts/run_app.py
```

This will launch the web interface where you can:
- Enter a stock ticker symbol
- Select a time period for analysis
- View interactive charts and technical indicators
- Get the omninmo Rating prediction

### Command-line Tools

#### Train the Model

Train the prediction model on default tickers:

```bash
python scripts/train_model.py
```

Options:
- `--model-path`: Path to save the trained model (default: models/stock_predictor.pkl)
- `--period`: Time period for historical data (default: 2y)
- `--tickers`: List of ticker symbols to use for training

#### Test the Model

Evaluate the model's performance:

```bash
python scripts/test_model.py
```

Options:
- `--model-path`: Path to the trained model (default: models/stock_predictor.pkl)
- `--tickers`: List of ticker symbols to test on
- `--period`: Time period for historical data (default: 1y)

#### Quick Predictions

Get a quick prediction for a specific ticker:

```bash
python scripts/predict_ticker.py AAPL
```

Options:
- `--model-path`: Path to the trained model (default: models/stock_predictor.pkl)
- `--period`: Time period for historical data (default: 1y)

## Project Structure

```
omninmo/
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   └── stock_data_fetcher.py  # Fetches stock data using yfinance
│   ├── models/
│   │   ├── __init__.py
│   │   └── stock_rating_predictor.py  # RandomForest model for predictions
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── feature_engineer.py  # Calculates technical indicators
│   │   ├── visualizer.py  # Visualization utilities
│   │   └── trainer.py  # Model training utilities
│   └── app/
│       ├── __init__.py
│       └── streamlit_app.py  # Streamlit web application
├── scripts/
│   ├── run_app.py  # Launches the Streamlit app
│   ├── train_model.py  # Pre-trains the model
│   ├── test_model.py  # Evaluates model performance
│   └── predict_ticker.py  # Command-line predictions
├── models/  # Directory for saved models
├── cache/  # Directory for cached stock data
├── docs/  # Documentation
└── tests/  # Unit and integration tests
```

## Technical Indicators

The application calculates the following technical indicators:

- **Moving Averages**: Simple and Exponential Moving Averages (5, 10, 20, 50, 200 days)
- **MACD**: Moving Average Convergence Divergence
- **RSI**: Relative Strength Index
- **Bollinger Bands**: Upper, Middle, and Lower bands
- **ATR**: Average True Range
- **Volume Indicators**: Volume moving averages and ratios
- **Price Momentum**: Rate of Change (ROC) for different periods
- **Price Relative to Moving Averages**: Price to SMA ratios
- **Golden/Death Cross**: SMA 50/200 ratio

## Rating System

The omninmo Rating system includes five categories:

- **Strong Buy**: High confidence in positive future performance
- **Buy**: Moderate confidence in positive future performance
- **Hold**: Neutral outlook or uncertain direction
- **Sell**: Moderate confidence in negative future performance
- **Strong Sell**: High confidence in negative future performance

## Model Training

The prediction model is trained on historical stock data from a set of default tickers. For each ticker, the application:

1. Fetches historical price data
2. Calculates technical indicators
3. Generates labels based on future price movements
4. Trains a RandomForest classifier on the features and labels

## Limitations

- The model is based solely on technical indicators and does not consider fundamental data or news
- Stock prediction is inherently uncertain, and the model's predictions should not be the sole basis for investment decisions
- The application uses simplified labeling for training, which may not capture all market dynamics

## Future Enhancements

- Add fundamental data analysis
- Implement news sentiment analysis
- Support for portfolio analysis
- Backtesting capabilities
- Advanced machine learning models (deep learning, ensemble methods)

## Troubleshooting

### Common Issues

1. **Model Not Found**
   - Ensure you've trained the model first with `python scripts/train_model.py`

2. **Import Errors**
   - Make sure you're running scripts from the project root directory
   - Verify that all dependencies are installed

3. **Data Fetching Issues**
   - Check your internet connection
   - Some tickers may not be available through yfinance
   - API rate limits may temporarily prevent data fetching

## License

[Specify your license here]

## Acknowledgments

- yfinance for providing access to Yahoo Finance data
- Streamlit for the interactive web interface
- scikit-learn for machine learning capabilities
