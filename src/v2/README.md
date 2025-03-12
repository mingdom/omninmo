# omninmo v2

This is a simplified version of the omninmo stock prediction system. It focuses on a console-based interface rather than a web app, and uses a flat directory structure for simplicity.

## Files

- **config.py**: Configuration handling using YAML
- **data_fetcher.py**: Fetches stock data from API or generates sample data
- **features.py**: Generates technical features from price data
- **predictor.py**: XGBoost model for making predictions
- **train.py**: Script for training the model
- **console_app.py**: Console application for viewing predictions

## Usage

The application can be run using the Makefile commands:

```bash
# Train a new model
make train

# Train with sample data (no API key needed)
make train-sample

# Run predictions on the watchlist in config.yaml
make predict

# Predict for a specific ticker
make predict-ticker TICKER=AAPL
```

## Design Philosophy

The v2 implementation focuses on:

1. **Simplicity**: Flat directory structure, simpler code
2. **Reliability**: Better error handling and failovers
3. **Console-First**: Designed for command-line use rather than web interface
4. **Configurability**: Still using the central config.yaml file 