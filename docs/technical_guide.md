# Technical Guide: How omninmo Works

This document provides a technical deep dive into the omninmo stock prediction system, explaining how the model works, how predictions are made, and the technical architecture behind the application.

## Table of Contents

1. [Model Architecture](#model-architecture)
2. [Data Pipeline](#data-pipeline)
3. [Feature Engineering](#feature-engineering)
4. [Prediction System](#prediction-system)
5. [Sample Data Generation](#sample-data-generation)
6. [Training Process](#training-process)
7. [Logging System](#logging-system)
8. [Deployment Architecture](#deployment-architecture)
9. [Model Maintenance](#model-maintenance)
10. [Model Improvement Strategies](#model-improvement-strategies)
11. [Troubleshooting](#troubleshooting)

## Model Architecture

### Overview

omninmo uses a **Random Forest Classifier** as its core prediction model. This ensemble learning method was chosen for several key reasons:

- **Robustness to overfitting**: Random forests are less prone to overfitting compared to individual decision trees
- **Feature importance**: They provide built-in feature importance metrics to understand which technical indicators are most predictive
- **Non-linear relationships**: They can capture complex, non-linear relationships in financial data
- **Handling missing values**: They can handle missing values and don't require extensive preprocessing

The model is implemented in the `StockRatingPredictor` class in `src/models/stock_rating_predictor.py`.

### Classification Approach

Rather than predicting exact price movements (regression), omninmo uses a classification approach with five distinct rating categories:

1. **Strong Buy**: Expected significant positive returns (>10%)
2. **Buy**: Expected moderate positive returns (3-10%)
3. **Hold**: Expected minimal movement (-3% to +3%)
4. **Sell**: Expected moderate negative returns (-3% to -10%)
5. **Strong Sell**: Expected significant negative returns (<-10%)

This classification approach simplifies the prediction task and provides actionable insights for users.

### XGBoost Classifier

As part of our model improvement strategy, we've implemented an XGBoost classifier as an alternative to the Random Forest model. XGBoost (eXtreme Gradient Boosting) is an optimized distributed gradient boosting library designed to be highly efficient, flexible, and portable.

Key advantages of XGBoost:

- **Gradient Boosting Framework**: Uses a more sophisticated algorithm that builds trees sequentially, with each new tree correcting errors made by previous trees.
- **Regularization**: Includes L1 (Lasso) and L2 (Ridge) regularization to prevent overfitting.
- **Handling Missing Values**: Built-in capability to handle missing values.
- **Tree Pruning**: Uses a depth-first approach to grow trees and prune them, which can lead to more efficient models.
- **Parallel Processing**: Optimized for performance with parallel computing capabilities.

Like the Random Forest model, XGBoost is used to classify stocks into five rating categories: Strong Buy, Buy, Hold, Sell, and Strong Sell.

### Model Comparison

We've implemented a model comparison framework to evaluate the performance of different models. The comparison:

1. **Trains both models** on the same dataset
2. **Evaluates performance** using metrics like accuracy, precision, recall, and F1-score
3. **Compares feature importance** to understand which features are most predictive in each model
4. **Visualizes results** through charts and confusion matrices
5. **Generates detailed reports** for further analysis

To run a model comparison:

```bash
make compare-models
```

This will generate a comprehensive report in the `model_comparison` directory, including:
- Accuracy comparison charts
- Feature importance visualizations
- Confusion matrices
- Detailed classification reports
- CSV files with performance metrics

## Data Pipeline

### Data Sources

The primary data source for omninmo is **Yahoo Finance**, accessed through the `yfinance` library. The data pipeline is implemented in the `StockDataFetcher` class in `src/data/stock_data_fetcher.py`.

Key features of the data pipeline:

- **Caching**: Data is cached locally to reduce API calls and improve performance
- **Error handling**: Robust retry logic handles temporary API failures
- **Sample data generation**: Fallback to synthetic data when API access fails
- **Flexible time periods**: Support for various historical periods (1d to 10y)

### Data Flow

1. User requests data for a specific ticker
2. System checks local cache for recent data
3. If cache is missing or outdated, system fetches from Yahoo Finance
4. If API fails, system generates sample data
5. Data is processed and returned as a pandas DataFrame

## Feature Engineering

### Technical Indicators

The system calculates over 30 technical indicators for each stock, implemented in the `FeatureEngineer` class in `src/utils/feature_engineer.py`. These include:

#### Price-based Indicators
- **Simple Moving Averages (SMA)**: 5, 10, 20, 50, and 200-day
- **Exponential Moving Averages (EMA)**: 5, 10, 20, 50, and 200-day
- **Bollinger Bands**: Middle band, upper band, lower band, and width
- **Price relative to moving averages**: Price/SMA50, Price/SMA200

#### Momentum Indicators
- **Relative Strength Index (RSI)**: 14-day period
- **Moving Average Convergence Divergence (MACD)**: 12/26/9 parameters
- **Rate of Change (ROC)**: 5, 10, and 20-day periods

#### Volatility Indicators
- **Average True Range (ATR)**: 14-day period
- **Bollinger Band Width**: Measure of volatility

#### Volume Indicators
- **Volume Moving Averages**: 5 and 10-day
- **Volume Ratio**: Current volume relative to average

### Feature Importance

Based on model training, the most predictive features typically include:
- RSI (Relative Strength Index)
- Price to SMA-200 ratio
- Bollinger Band Width
- MACD Histogram

## Prediction System

### Prediction Process

The prediction process follows these steps:

1. **Data Retrieval**: Fetch historical data for the requested ticker
2. **Feature Calculation**: Calculate technical indicators
3. **Model Input**: Prepare the most recent data point as input
4. **Classification**: Apply the Random Forest model to classify the stock
5. **Confidence Score**: Calculate prediction confidence based on class probabilities

### Confidence Calculation

The confidence score is derived from the probability distribution of the Random Forest classifier. Higher confidence indicates stronger consensus among the decision trees in the ensemble.

## Sample Data Generation

### Synthetic Data Generation

When real data is unavailable (due to API issues or for testing), omninmo generates synthetic stock data with realistic properties:

- **Price trends**: Simulated with random trend changes
- **Volatility**: Ticker-specific volatility parameters
- **Volume**: Realistic trading volumes based on price
- **OHLC relationships**: Maintains proper relationships between Open, High, Low, and Close prices

The sample data generation is implemented in the `_generate_sample_data` and `_generate_realistic_price_series` methods in `StockDataFetcher`.

### Usage Scenarios

Sample data is used in three scenarios:
1. When the Yahoo Finance API is unavailable
2. During development and testing
3. When explicitly requested via the `--sample-data` flag or `force_sample=True` parameter

## Training Process

### Training Data

The model is trained on historical data from a set of diverse stocks (by default, 15 major tickers including AAPL, MSFT, AMZN, etc.). The training process:

1. Fetches historical data for each ticker
2. Calculates technical indicators
3. Creates target labels based on future returns
4. Combines data from all tickers
5. Trains the Random Forest model

### Target Creation

The training labels are created by looking at future returns over a specified period (default: 20 trading days). Returns are categorized into the five rating classes based on percentage thresholds.

### Model Evaluation

The model is evaluated using:
- **Accuracy**: Percentage of correct predictions
- **Classification Report**: Precision, recall, and F1-score for each rating class
- **Feature Importance**: Ranking of most predictive features

## Logging System

The omninmo application implements a comprehensive logging system to facilitate debugging, monitoring, and troubleshooting. The logging system is built using Python's standard `logging` module with enhancements for file rotation and structured output.

### Logging Architecture

- **Module-Level Loggers**: Each module has its own logger instance, allowing for granular control of log levels
- **Rotating File Handlers**: Log files automatically rotate when they reach a certain size (10MB by default)
- **Consistent Formatting**: All logs follow a consistent format: `timestamp - module - level - message`
- **Multiple Log Files**: Different components log to separate files:
  - `trainer.log`: Model training logs
  - `feature_engineer.log`: Feature engineering logs
  - `xgboost_predictor.log`: Model prediction logs
  - `fmp_data_fetcher.log`: Data fetching logs

### Log Levels

The system uses standard Python logging levels:

1. **DEBUG** (10): Detailed information for debugging purposes
   - Data shapes and dimensions
   - Feature values and distributions
   - Processing steps and intermediate results
   
2. **INFO** (20): Confirmation that things are working as expected
   - Model training started/completed
   - Data fetching completed
   - Application startup/shutdown
   
3. **WARNING** (30): Indication that something unexpected happened
   - Missing data for certain dates
   - Fallback to sample data
   - Non-critical API issues
   
4. **ERROR** (40): Error conditions that prevent a function from working
   - API connection failures
   - Model training failures
   - File I/O errors
   
5. **CRITICAL** (50): Critical errors that prevent the application from running
   - Database connection failures
   - Missing critical files
   - Unrecoverable system errors

### Command-Line Control

The logging level can be controlled via command-line arguments:

```bash
# Run with DEBUG level logging (most verbose)
python scripts/train_model.py -l DEBUG

# Run with INFO level logging (default)
python scripts/train_model.py -l INFO

# Run with WARNING level logging (less verbose)
python scripts/train_model.py -l WARNING
```

### Implementation Details

Each module configures its logger with both console and file handlers:

```python
# Setup logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Module's internal level

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Setup file handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    'logs/module_name.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)
```

The root logger's level is set based on the command-line argument, which propagates to all module loggers unless they explicitly override it.

## Deployment Architecture

### Application Components

The omninmo application consists of:

1. **Streamlit Web Interface**: Interactive UI for users
2. **Data Fetching Layer**: Retrieves and caches stock data
3. **Feature Engineering Layer**: Calculates technical indicators
4. **Prediction Layer**: Applies the trained model
5. **Visualization Layer**: Creates interactive charts and displays

### Execution Flow

1. User enters a ticker in the Streamlit interface
2. Application fetches data (real or sample)
3. Technical indicators are calculated
4. Model generates a rating prediction
5. Results are displayed with visualizations

## Model Maintenance

### Keeping the Model Up-to-Date

The stock market is dynamic and constantly evolving, which means our prediction model needs regular updates to maintain its accuracy. Here's how we keep the omninmo model up-to-date:

#### Automated Retraining Schedule

1. **Daily Incremental Updates**:
   - The model can be retrained daily with the most recent market data
   - Run `make train` as part of a scheduled job (e.g., using cron)
   - This ensures the model incorporates the latest market patterns

2. **Weekly Full Retraining**:
   - A complete retraining on the full dataset should be performed weekly
   - This helps capture medium-term market trends
   - Command: `make train PERIOD=1y` to use a 1-year training window

3. **Monthly Evaluation**:
   - Evaluate model performance against recent market behavior
   - Adjust hyperparameters if necessary
   - Consider expanding the ticker set if market conditions change

#### Implementation Strategy

To implement this maintenance schedule:

1. **Create a maintenance script**:
   ```python
   # scripts/maintain_model.py
   import os
   import sys
   import argparse
   from datetime import datetime
   
   # Add project root to path
   project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
   sys.path.insert(0, project_root)
   
   from src.utils.trainer import train_on_default_tickers, evaluate_model
   
   def main():
       parser = argparse.ArgumentParser(description='Maintain the stock prediction model')
       parser.add_argument('--mode', choices=['daily', 'weekly', 'monthly'], 
                          default='daily', help='Maintenance mode')
       args = parser.parse_args()
       
       if args.mode == 'daily':
           # Daily incremental update
           print("Performing daily model update...")
           train_on_default_tickers(period='30d')
       elif args.mode == 'weekly':
           # Weekly full retraining
           print("Performing weekly full retraining...")
           train_on_default_tickers(period='1y')
       elif args.mode == 'monthly':
           # Monthly evaluation
           print("Performing monthly model evaluation...")
           # Implement evaluation logic here
           
       print(f"Model maintenance ({args.mode}) completed at {datetime.now()}")
       
   if __name__ == "__main__":
       main()
   ```

2. **Set up cron jobs** (on Unix-based systems):
   ```bash
   # Daily update at 1:00 AM
   0 1 * * * cd /path/to/omninmo && source ./activate-venv.sh && python scripts/maintain_model.py --mode daily
   
   # Weekly update on Sunday at 2:00 AM
   0 2 * * 0 cd /path/to/omninmo && source ./activate-venv.sh && python scripts/maintain_model.py --mode weekly
   
   # Monthly evaluation on the 1st of each month at 3:00 AM
   0 3 1 * * cd /path/to/omninmo && source ./activate-venv.sh && python scripts/maintain_model.py --mode monthly
   ```

3. **Version control for models**:
   - Store dated versions of models
   - Implement a rollback mechanism if a new model performs poorly
   - Example naming: `stock_predictor_YYYY_MM_DD.pkl`

#### Data Freshness Monitoring

To ensure the model uses fresh data:

1. **Cache invalidation**: Automatically invalidate cached data older than 24 hours
2. **API health checks**: Monitor the Yahoo Finance API for availability issues
3. **Data quality validation**: Verify incoming data meets quality standards before training

## Model Improvement Strategies

### Enhancing Prediction Performance

While the current Random Forest model provides a solid foundation, several strategies can improve prediction performance:

#### Advanced Model Architectures

1. **Ensemble Methods**:
   - Implement a stacked ensemble combining multiple models
   - Add gradient boosting models (XGBoost, LightGBM) alongside Random Forest
   - Use a meta-learner to combine predictions from different models

2. **Deep Learning Approaches**:
   - LSTM (Long Short-Term Memory) networks for time series prediction
   - Transformer models for capturing long-range dependencies
   - Hybrid CNN-LSTM architectures for both spatial and temporal patterns

3. **Reinforcement Learning**:
   - Frame stock prediction as a reinforcement learning problem
   - Use Deep Q-Networks (DQN) to learn optimal trading strategies
   - Implement A2C (Advantage Actor-Critic) for policy-based learning

#### Feature Engineering Improvements

1. **Additional Technical Indicators**:
   - Ichimoku Cloud components
   - Elliott Wave patterns
   - Market breadth indicators (Advance/Decline Line, McClellan Oscillator)
   - Sentiment-based indicators

2. **Alternative Data Sources**:
   - News sentiment analysis using NLP
   - Social media sentiment (Twitter, Reddit)
   - Options market data (implied volatility, put/call ratio)
   - Macroeconomic indicators (interest rates, GDP, unemployment)

3. **Feature Selection and Dimensionality Reduction**:
   - Recursive Feature Elimination (RFE)
   - Principal Component Analysis (PCA)
   - Mutual Information scoring
   - SHAP (SHapley Additive exPlanations) values for feature importance

#### Training Enhancements

1. **Hyperparameter Optimization**:
   - Implement Bayesian optimization for hyperparameter tuning
   - Use cross-validation with time-series splits
   - Automate hyperparameter search with libraries like Optuna or Ray Tune

2. **Handling Class Imbalance**:
   - Apply SMOTE (Synthetic Minority Over-sampling Technique)
   - Use class weights in the model
   - Implement focal loss for imbalanced classification

3. **Transfer Learning**:
   - Pre-train models on large market datasets
   - Fine-tune on specific sectors or individual stocks
   - Implement domain adaptation techniques

#### Evaluation Improvements

1. **Better Metrics**:
   - Focus on financial metrics (e.g., risk-adjusted returns)
   - Implement custom metrics like Profit Factor or Sharpe Ratio
   - Use confusion matrix cost-sensitive evaluation

2. **Backtesting Framework**:
   - Develop a comprehensive backtesting system
   - Simulate trading strategies based on model predictions
   - Account for transaction costs and slippage

3. **Explainability**:
   - Implement LIME (Local Interpretable Model-agnostic Explanations)
   - Use SHAP values to explain individual predictions
   - Create visualization tools for model decision processes

#### Implementation Roadmap

For implementing these improvements, we recommend the following phased approach:

1. **Phase 1: Enhanced Features** (1-2 weeks)
   - Add 5-10 new technical indicators
   - Implement feature selection
   - Integrate basic sentiment analysis

2. **Phase 2: Model Upgrades** (2-4 weeks)
   - Add XGBoost and LightGBM models
   - Implement stacked ensemble
   - Optimize hyperparameters

3. **Phase 3: Alternative Data** (3-6 weeks)
   - Integrate news sentiment API
   - Add macroeconomic indicators
   - Implement social media sentiment analysis

4. **Phase 4: Deep Learning** (4-8 weeks)
   - Develop LSTM model for time series
   - Create hybrid architecture
   - Implement transfer learning

Each phase should include thorough evaluation and comparison with the baseline model to ensure improvements are genuine and significant.

### Implementation Example: XGBoost Model

We've implemented an XGBoost model as an example of our model improvement strategies. The implementation can be found in `src/models/xgboost_predictor.py`.

Key components of the implementation:

1. **XGBoostRatingPredictor class**: A complete implementation that follows the same interface as our RandomForestRatingPredictor.
2. **Hyperparameter configuration**: Includes learning rate, max depth, and number of estimators.
3. **Feature importance analysis**: Calculates and stores feature importance for analysis.
4. **Comprehensive evaluation**: Includes methods for model evaluation and performance reporting.

To compare the XGBoost model with the current Random Forest model:

```bash
python scripts/compare_models.py
```

This script:
- Prepares a dataset from historical stock data
- Trains both models on the same data
- Evaluates performance using multiple metrics
- Generates visualizations and reports
- Calculates the percentage improvement of XGBoost over Random Forest

The comparison results can help guide decisions about which model to use in production.

## Troubleshooting

### Common Issues

1. **Yahoo Finance API Issues**
   - **Symptom**: Empty data or API errors
   - **Solution**: Use sample data mode with `make run-sample` or check the "Use sample data" checkbox

2. **Missing Model File**
   - **Symptom**: "Model not found" warning
   - **Solution**: Train the model with `make train` or `make train-sample`

3. **Insufficient Data for Indicators**
   - **Symptom**: Missing technical indicators
   - **Solution**: Use a longer time period (e.g., "1y" instead of "1mo")

### Debugging Tips

- Check the application logs for detailed error messages
- Use the sample data mode to isolate API-related issues
- Examine the feature importance to understand model decisions

---

This technical guide provides a comprehensive overview of how omninmo works. For implementation details, refer to the source code in the `src` directory. 