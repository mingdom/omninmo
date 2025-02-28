# omninmo - Stock Performance Prediction

`omninmo` is the palindrome of `omni`, our aim is to become an investor super-app that can predict stock performance.

## Overview

**Input:** Stock ticker (e.g., `NVDA`)  
**Output:** omninmo Rating (e.g., `Strong Buy`)

We ingest price and financial data to train prediction models and produce analysis. While we have an ambitious roadmap, our goal is to start simple and get an MVP out ASAP.

## Tech Stack

- **Backend:** Python 3
- **Frontend:** Streamlit (for easy prototyping)
- **Data Sources:** `yfinance` or FMP API (FinancialModelingPrep) for financial data
- **Machine Learning:** Scikit-learn for prediction models

## Project Structure

```
omninmo/
├── src/
│   ├── data/         # Data fetching and processing
│   ├── models/       # Prediction models
│   ├── utils/        # Utility functions
│   └── app/          # Streamlit application
├── scripts/          # Supporting scripts
├── docs/             # Documentation
└── tests/            # Unit and integration tests
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip3 (Python package installer)
- virtualenv or venv module

### Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/omninmo.git
   cd omninmo
   ```

2. Set up a virtual environment
   ```
   make env
   ```

3. Activate the virtual environment
   ```
   source activate-venv.sh
   ```

4. Install dependencies
   ```
   make install
   ```

### Running the Application

1. Train the model (first time only)
   ```
   make train
   ```

2. Run the application
   ```
   make run
   ```

### Using the Makefile

The project includes a Makefile with various targets for common operations:

- `make help` - Show available targets
- `make env` - Set up a virtual environment
- `make install` - Install dependencies
- `make test` - Run all tests
- `make train` - Train the model
- `make run` - Run the Streamlit app
- `make predict TICKER=AAPL` - Predict rating for a ticker
- `make clean` - Clean up generated files
- `make pipeline` - Run the full pipeline (tests, training, prediction)
- `make executable` - Make all scripts executable

## Current Status

The MVP is nearly complete, with core functionality implemented. See [Progress Tracking](./docs/progress.md) for details on current status and next steps.

## Documentation

For detailed documentation, please refer to the [docs](./docs/) directory.
