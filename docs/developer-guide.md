# Developer Guide

## Introduction

Welcome to the Omninmo stock prediction system! This guide will help you understand the system architecture, development workflow, and best practices for contributing to the project.

## Project Structure

```
omninmo/
├── config/                  # Configuration files
├── src/                     # Source code
│   └── v2/                  # Version 2 of the prediction system
│       ├── config.py        # Configuration utilities
│       ├── console_app.py   # Console application
│       ├── data_fetcher.py  # Data fetching and caching
│       ├── exceptions.py    # Custom exception classes
│       ├── features.py      # Feature engineering
│       ├── predictor.py     # XGBoost prediction model
│       ├── train.py         # Model training script
│       └── training_summary.py # Training evaluation utilities
├── models/                  # Saved model files
├── cache/                   # Data cache
├── logs/                    # Log files and MLflow tracking
│   └── mlruns/              # MLflow experiment tracking
└── docs/                    # Documentation
    ├── architecture.md      # System architecture
    ├── developer-guide.md   # This guide
    ├── devlog/              # Development log entries
    ├── devplan/             # Development planning documents
    └── future-experiments.md # Future enhancement ideas
```

## Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/omninmo.git
   cd omninmo
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **API Key Setup**
   - Get an API key from Financial Modeling Prep
   - Set it as an environment variable:
     ```bash
     export FMP_API_KEY="your-api-key"
     ```
   - Alternatively, add it to your configuration file

## Core Components

### Configuration System

The `config.py` module provides a flexible configuration system that supports both a legacy single YAML file and a newer multi-file structure. Configuration values can be accessed using dot notation:

```python
from src.v2.config import config

# Get configuration values with defaults
interval = config.get("model.training.interval", "1d")
```

### Data Fetching

The `data_fetcher.py` module handles data retrieval and caching:

```python
from src.v2.data_fetcher import DataFetcher

# Create data fetcher with custom cache directory
fetcher = DataFetcher(cache_dir="custom_cache")

# Fetch data with caching
data = fetcher.fetch_data("AAPL", period="5y", interval="1d")

# Force using sample data
sample_data = fetcher.fetch_data("AAPL", force_sample=True)

# Get market data for comparison
market_data = fetcher.fetch_market_data()
```

### Feature Engineering

The `features.py` module contains the feature generation logic:

```python
from src.v2.features import Features

# Create feature generator
feature_generator = Features()

# Generate standard features
features_df = feature_generator.generate(price_data)

# Generate enhanced features with market comparison
enhanced_features = feature_generator.generate(
    price_data,
    market_data=market_data,
    use_enhanced_features=True
)
```

### Prediction Model

The `predictor.py` module implements the XGBoost prediction model:

```python
from src.v2.predictor import Predictor

# Create and train a new model
predictor = Predictor()
predictor.train(X_train, y_train)

# Make predictions
predictions = predictor.predict(features)

# Analyze feature importance
importance = predictor.analyze_feature_importance()

# Save and load models
predictor.save("models/my_model.pkl")
loaded_predictor = Predictor.load("models/my_model.pkl")
```

### Training Pipeline

The `train.py` module provides the full training workflow:

```python
from src.v2.train import train_model

# Train with default settings
predictor, results = train_model()

# Train with custom settings
predictor, results = train_model(
    tickers=["AAPL", "MSFT", "GOOG"],
    period="10y",
    forward_days=30,
    use_enhanced_features=True,
    use_risk_adjusted_target=True
)
```

## Development Workflow

### Adding New Features

1. Review existing feature calculation in `features.py`
2. Add new feature calculation method following naming convention `_add_*`
3. Update the `generate()` method to call your new feature method
4. Add appropriate configuration parameters to the config file

### Improving the Model

1. Review current model performance in the MLflow tracking
2. Modify hyperparameters in the configuration
3. Experiment with new features or target definitions
4. Document your experiments in `docs/devlog/`

### Adding Tests

1. Use pytest for all test cases
2. Create unit tests for individual components
3. Add integration tests for full workflows
4. Test with both real and sample data scenarios

## Debugging Tips

1. **Configure Logging Level**
   ```bash
   # Run with DEBUG level logging
   LOG_LEVEL=DEBUG make folio
   ```

   For more details on logging configuration, see [logging.md](logging.md).

2. **Inspect Feature Engineering**
   - Set breakpoints in feature generation methods
   - Check for NaN values or abnormal distributions
   - Visualize feature correlations with the target

3. **MLflow Tracking**
   - Review experiments in MLflow UI:
     ```bash
     mlflow ui --backend-store-uri logs/mlruns
     ```

## Code Style and Conventions

1. **Naming Conventions**
   - Use `-` instead of `_` for file names
   - Use snake_case for variables and functions
   - Use CamelCase for class names

2. **Documentation**
   - Document progress in `docs/devlog/` with timestamped files
   - Write development plans in `docs/devplan/`
   - Keep code comments focused and minimal

3. **Error Handling**
   - Use custom exceptions from `exceptions.py`
   - Never hide errors without good reason
   - Log all significant events appropriately

## Deployment

1. **Train a Production Model**
   ```bash
   python -m src.v2.train --tickers SPY,QQQ,DIA --period 10y --output models/production_model.pkl
   ```

2. **Run Predictions**
   ```bash
   python -m src.v2.console_app --model models/production_model.pkl --tickers AAPL,MSFT,TSLA
   ```

## Contributing

1. Create a clear development plan in `docs/devplan/`
2. Document your progress in `docs/devlog/`
3. Follow the existing code style and patterns
4. Test thoroughly before submitting changes
5. Keep changes minimal and focused on specific features

## Additional Resources

- XGBoost Documentation: https://xgboost.readthedocs.io/
- Financial Modeling Prep API: https://financialmodelingprep.com/developer/docs/
- MLflow Documentation: https://www.mlflow.org/docs/latest/index.html
- Pandas Documentation: https://pandas.pydata.org/docs/
