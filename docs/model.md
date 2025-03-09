# Model Training Documentation

## Current Model Training Process

### Overview

The project uses XGBoost for stock rating prediction, with data fetched from the Financial Modeling Prep (FMP) API. The training process is orchestrated by the `scripts/train_model.py` script, which integrates several key components:

1. **FMPDataFetcher** - Fetches historical stock data from FMP API or generates sample data
2. **FeatureEngineer** - Calculates technical indicators from the raw stock data
3. **XGBoostRatingPredictor** - The actual model that's trained on the engineered features

### Training Process Steps

The training process follows these steps:

1. Fetch historical stock data for a list of tickers (either from API or sample data)
2. For each ticker:
   - Calculate technical indicators (SMA, EMA, MACD, RSI, Bollinger Bands, etc.)
   - Prepare target variable (future returns converted to rating categories)
   - Remove rows with NaN values
3. Combine data from all tickers
4. Train the XGBoost model on the combined dataset
5. Save the model with versioning

### Feature Engineering

The feature engineering process calculates various technical indicators:

- Moving Averages (SMA_20, SMA_50, SMA_200)
- Exponential Moving Averages (EMA_12, EMA_26)
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Bollinger Bands
- ATR (Average True Range)
- Volume indicators
- Price momentum (ROC_5, ROC_10, ROC_20)
- Price relative to moving averages
- Golden/Death Cross indicator

### Target Variable

The target variable (stock rating) is derived from future returns over a specified period (default is 20 days). The returns are categorized into 5 rating classes:

- **Strong Buy**: return > 5%
- **Buy**: return between 2% and 5%
- **Hold**: return between -2% and 2%
- **Sell**: return between -5% and -2%
- **Strong Sell**: return < -5%

This makes the problem a multi-class classification task rather than a regression task.

### Model Configuration

The XGBoost model uses these default parameters:

- learning_rate: 0.1
- max_depth: 6
- n_estimators: 100
- random_state: 42
- eval_metric: 'mlogloss' (appropriate for multi-class classification)

The training process includes:

1. Encoding the string labels to numeric values
2. Splitting data into training and test sets (80/20 split by default)
3. Using stratification when possible (when there are enough samples per class)
4. Training the model and calculating feature importance
5. Evaluating on the test set and reporting accuracy and classification metrics

### Model Versioning

The model versioning system includes:

1. Models saved with datetime-stamped filenames
2. A symlink 'latest_model.pkl' that always points to the most recent model
3. Old models archived in 'models/archive/'
4. Cleanup functionality to remove old models while keeping:
   - At least 5 most recent models
   - Models less than 30 days old

This allows for easy rollback to previous models if needed and maintains a clear history of model versions.

### Training Approach

The project previously had an automated model maintenance system but it was removed in favor of manual, deliberate training. This was done because:

- Stock prediction models benefit from human oversight during training
- Automated retraining could be risky without proper validation
- It follows the tenet of preferring simplicity over complexity

This suggests a more cautious approach to model training and deployment, prioritizing quality over automation.

### Logging System

The codebase has a comprehensive logging system that tracks the training process:

- Different log levels (DEBUG, INFO, WARNING, ERROR) for controlling verbosity
- Structured logging with consistent formats
- File-based logging with rotation to prevent log files from growing too large
- Detailed logs for tracking data shapes, processing steps, and model training progress

## Potential Improvements

Based on analysis of the current model training process, here are potential areas for improvement:

1. **Cross-validation**: The current approach uses a simple train-test split. Implementing k-fold cross-validation could provide more robust model evaluation.

2. **Hyperparameter tuning**: There's no automated hyperparameter tuning. Adding grid search or Bayesian optimization could improve model performance.

3. **Feature selection**: While feature importance is calculated, there's no automated feature selection process to remove irrelevant features.

4. **Class imbalance handling**: There's no explicit handling of class imbalance, which is common in stock rating prediction.

5. **Model explainability**: Beyond feature importance, more advanced explainability techniques (SHAP values, partial dependence plots) could be added.

6. **Alternative models**: The codebase focuses solely on XGBoost. Experimenting with other algorithms or ensemble methods could be beneficial.

7. **Time-based validation**: Stock data is time-series data, but the validation doesn't account for this. Implementing time-based cross-validation would be more appropriate.

8. **Online learning**: The model is trained in batch mode. Implementing online learning could allow the model to adapt to changing market conditions.

9. **Data augmentation**: There's no data augmentation to increase the training set size or handle rare market conditions.

10. **Model monitoring**: While there's versioning, there's no automated monitoring of model performance over time to detect drift.

11. **Expanded ticker dataset**: The current training set uses only 15 large-cap tickers, primarily from the technology sector. Expanding the training dataset to include:
    - More tickers (100+ stocks)
    - Greater sector diversity (energy, healthcare, utilities, real estate, etc.)
    - Different market capitalizations (small-cap, mid-cap)
    - International stocks
    - Different market conditions (growth, value, cyclical)
    
    This would likely improve the model's generalization ability and make it more robust when predicting ratings for stocks not seen during training. It would also help balance the dataset across different market sectors and conditions, potentially reducing bias toward tech stocks. 