# omninmo - Stock Performance Prediction

A machine learning-powered stock rating system that predicts future stock performance.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/d3ming/omninmo.git
cd omninmo

# Set up environment and install dependencies
make env
make install

# Train the model
make train-sample # for quick testing with sample data
make train # once you are ready for a full training run (could take some time)

# Run the application
make run
```

## What is omninmo?

**Input:** Stock ticker (e.g., `NVDA`)  
**Output:** Rating prediction (e.g., `Strong Buy`)

omninmo analyzes stock price data and technical indicators to predict one of five ratings:
- **Strong Buy** (4)
- **Buy** (3)
- **Hold** (2)
- **Sell** (1)
- **Strong Sell** (0)

## Features

- **Data Analysis**: Fetches and analyzes historical stock data
- **Technical Indicators**: Calculates 25+ technical indicators
- **ML Prediction**: Uses XGBoost to predict stock ratings
- **Interactive UI**: User-friendly interface with charts
- **Command-line Tools**: Quick predictions from the terminal
- **Model Tracking**: Uses MLflow to track experiments and visualize results

## Common Commands

```bash
# Set up the environment (only needed once)
make env

# Install or update dependencies
make install

# Train with real data (requires FMP API key)
make train

# Run the application
make run

# Get a prediction for a specific ticker
make predict TICKER=AAPL

# View model training results with MLflow
make mlflow

# Run all tests
make test

# Clean up generated files
make clean
```

## Project Structure

```
omninmo/
├── src/             # Core application code
├── scripts/         # Command-line tools
├── models/          # Saved ML models
├── docs/            # Detailed documentation
├── logs/           # All logs and run data
│   ├── mlruns/     # MLflow experiment tracking data
│   └── training/   # Training summary reports
└── tests/           # Unit and integration tests
```

## Tech Stack

- **Backend**: Python 3
- **Data Source**: Financial Modeling Prep (FMP) API
- **ML Framework**: XGBoost
- **Model Tracking**: MLflow
- **Model Interpretability**: SHAP
- **Frontend**: Streamlit

## Model Tracking with MLflow

omninmo uses MLflow to track model training experiments, metrics, and artifacts. This provides several benefits:

### Key Features
- **Experiment Tracking**: Log parameters, metrics, and artifacts for each training run
- **Model Comparison**: Compare different models side-by-side
- **Feature Importance**: Visualize which features have the most impact on predictions
- **Model Interpretability**: SHAP plots help understand how features affect predictions

### Using MLflow
After training a model, you can view the results in the MLflow UI:

```bash
# Start the MLflow UI
make mlflow
```

Then open your browser to http://127.0.0.1:5000 to access the MLflow UI.

For a comprehensive guide on using MLflow with omninmo, see the [MLflow Guide](./docs/mlflow_usage.md).

## Documentation

For detailed documentation, see the [Documentation Index](./docs/README.md) in the docs directory. Our documentation is organized into three main categories:

1. **Current Implementation** (top-level docs)
   - [Architecture Guide](./docs/architecture.md)
   - [Features Documentation](./docs/features.md)
   - [Model Documentation](./docs/models.md)
   - [Cross-validation Guide](./docs/cross-validation.md)
   - [MLflow Guide](./docs/mlflow-guide.md)

2. **Development Plans** (`docs/devplan/`)
   - Future improvements
   - Design documents
   - Migration guides

3. **Implementation Progress** (`docs/devlog/`)
   - Daily development notes
   - Implementation details
   - Performance improvements

See the [Documentation Index](./docs/README.md) for:
- Complete documentation listing
- Documentation philosophy
- Contribution guidelines
- Cross-referencing guide

## All Available Make Commands

Run `make help` to see all available commands. Here are the most useful ones:

- `make help` - Show available targets
- `make env` - Set up and activate a virtual environment
- `make install` - Install dependencies
- `make train` - Train the model with real data
- `make train-sample` - Train the model with sample data
- `make run` - Run the application
- `make run-sample` - Run the application with sample data
- `make predict TICKER=AAPL` - Predict rating for a ticker
- `make mlflow` - Start the MLflow UI to view training results
- `make test` - Run all tests
- `make clean` - Clean up generated files
- `make clear-cache` - Clear the data cache
- `make pipeline` - Run the full pipeline (tests, training, prediction)
- `make maintain MODE=daily|weekly|monthly` - Run model maintenance

## License

MIT License

Copyright (c) 2025 omninmo Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
