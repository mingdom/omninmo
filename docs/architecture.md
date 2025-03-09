# omninmo Architecture

This document outlines the architecture of the omninmo stock prediction application.

## System Overview

omninmo is designed with a modular architecture to separate concerns and allow for easy maintenance and extension. The system consists of four main components:

1. **Data Module** - Responsible for fetching and processing stock data
2. **Feature Engineering Module** - Calculates technical indicators and prepares features for the model
3. **Prediction Module** - Contains the machine learning models for stock rating predictions
4. **Application Interface** - Streamlit-based web interface for user interaction

## Component Details

### Data Module

The data module is responsible for retrieving stock data from external sources:

- **StockDataFetcher** - Uses `yfinance` to fetch historical stock data
- Handles data cleaning and preprocessing
- Provides a consistent interface for accessing stock data regardless of the source
- Implements intelligent caching to minimize API calls (see [Cache Documentation](cache.md))

### Feature Engineering Module

The feature engineering module transforms raw stock data into features suitable for machine learning:

- **FeatureEngineer** - Calculates technical indicators (e.g., moving averages, RSI, MACD)
- Performs feature normalization and scaling
- Handles missing data and outliers
- Uses Streamlit caching for performance optimization

### Prediction Module

The prediction module contains the machine learning models for stock rating predictions:

- **StockRatingPredictor** - Uses RandomForest algorithm to predict stock ratings
- Supports model training, evaluation, and prediction
- Provides confidence scores for predictions
- Implements model versioning and persistence

### Application Interface

The application interface is built using Streamlit:

- Interactive user interface for entering stock tickers
- Visualization of stock data and predictions using Plotly
- Color-coded rating display system
- Leverages Streamlit's caching system for responsiveness

## Data Flow

1. User enters a stock ticker in the Streamlit interface
2. StockDataFetcher retrieves historical data for the ticker
3. FeatureEngineer calculates technical indicators and prepares features
4. StockRatingPredictor generates a rating prediction
5. Results are displayed to the user with visualizations

## Supporting Scripts

- **run_app.py** - Launches the Streamlit application
- **train_model.py** - Pre-trains the prediction model
- **test_model.py** - Evaluates model performance
- **predict_ticker.py** - Command-line tool for quick predictions

## Future Architecture Considerations

As the project evolves, we plan to:

1. Implement a more robust data pipeline with caching
2. Add support for alternative data sources
3. Explore more advanced machine learning models
4. Develop a more sophisticated frontend with additional visualizations
5. Add natural language processing for earnings transcript analysis 