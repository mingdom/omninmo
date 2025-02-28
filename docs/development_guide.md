# Development Guide

This guide provides information for developers contributing to the omninmo project.

## Development Environment

Follow the [Setup Guide](./setup_guide.md) to set up your development environment.

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
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── setup_guide.md
│   ├── development_guide.md
│   └── progress.md
└── tests/
    ├── __init__.py
    ├── test_data_fetcher.py
    ├── test_feature_engineer.py
    └── test_predictor.py
```

## Coding Standards

1. **PEP 8**: Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.
2. **Docstrings**: Use Google-style docstrings for all functions and classes.
3. **Type Hints**: Use type hints where appropriate to improve code readability and IDE support.
4. **Comments**: Add comments for complex logic, but prefer self-explanatory code.

## Development Workflow

1. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**

   Implement your changes and test them thoroughly.

3. **Run Tests**

   ```bash
   python -m unittest discover tests
   ```

4. **Commit Changes**

   ```bash
   git add .
   git commit -m "Add your meaningful commit message"
   ```

5. **Push Changes**

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

   Create a pull request on GitHub with a clear description of your changes.

## Adding New Features

### Data Module

To add support for a new data source:

1. Create a new class in `src/data/` that implements the same interface as `StockDataFetcher`
2. Update the factory method to support the new data source

### Feature Engineering

To add new technical indicators:

1. Add the calculation method to `FeatureEngineer` in `src/utils/feature_engineer.py`
2. Update the feature list in the model training code

### Prediction Models

To implement a new prediction model:

1. Create a new class in `src/models/` that implements the same interface as `StockRatingPredictor`
2. Add appropriate training and evaluation code

### UI Components

To add new UI components:

1. Modify the Streamlit app in `src/app/streamlit_app.py`
2. Follow Streamlit's documentation for component design

## Debugging Tips

1. Use Streamlit's built-in debugging features:
   ```python
   st.write(debug_variable)
   ```

2. For data processing issues, use pandas' inspection methods:
   ```python
   st.write(df.describe())
   st.write(df.info())
   ```

3. For model debugging, use scikit-learn's inspection tools:
   ```python
   from sklearn.inspection import permutation_importance
   ```

## Documentation

When adding new features, please update the relevant documentation:

1. Update docstrings in the code
2. Update the architecture document if the system design changes
3. Update the progress document with your contributions 