# Development Errors Log

This file documents errors encountered during development and their solutions.

## 2025-03-09: Refactoring to Simplify Codebase

During our refactoring to simplify the codebase by removing yfinance and focusing only on XGBoost with FMP API, we encountered the following challenges:

### Challenge: Multiple Data Source Dependencies

**Problem:** The codebase had dependencies on both yfinance and FMP API, with fallback mechanisms between them, creating unnecessary complexity.

**Solution:** 
- Removed all yfinance-related code
- Enhanced the FMP data fetcher to include its own sample data generator
- Updated all references to use FMP data fetcher exclusively

### Challenge: Multiple Model Implementations

**Problem:** The codebase had multiple model implementations (RandomForest, GradientBoostingClassifier fallback, XGBoost) which made maintenance and testing more difficult.

**Solution:**
- Removed all non-XGBoost model implementations
- Simplified the XGBoost predictor to remove fallback mechanisms
- Updated all training scripts to only use XGBoost

### Challenge: XGBoost Class Label Compatibility

**Problem:** During training, XGBoost threw the error `Invalid classes inferred from unique values of y. Expected: [0 1 2 3 4], got [-2. -1. 0. 1. 2.]`. This was because we were using class labels from -2 to 2 (Strong Sell to Strong Buy), but XGBoost expects non-negative integer labels starting from 0.

**Solution:**
- Changed our rating system to use values 0-4 instead of -2 to 2:
  - 0: Strong Sell (was -2)
  - 1: Sell (was -1)
  - 2: Hold (was 0)
  - 3: Buy (was 1)
  - 4: Strong Buy (was 2)
- Created a mapping dictionary for consistent conversion between numeric and string labels
- Updated the evaluation logic to align with the new labeling scheme

### Challenge: Index Alignment in Training Data

**Problem:** We encountered issues where feature and target dataframes would have different indices or lengths, causing training to fail.

**Solution:**
- Used `reset_index(drop=True)` to ensure proper index alignment of features and targets
- Added explicit intersection of indices to ensure features and targets shared the same rows
- Implemented validation checks to ensure data length consistency
- Used `ignore_index=True` when concatenating data from multiple tickers

## 2025-03-09: Implementing Proper Logging System

When replacing print statements with a proper logging system, we encountered the following challenges:

### Challenge: Consistent Log Management Across Modules

**Problem:** Different parts of the codebase were using different logging approaches (some using print statements, others using basic logging), making it difficult to control verbosity and format logs consistently.

**Solution:**
- Implemented a centralized logging configuration in key modules
- Created a logs directory to store log files
- Added file handlers to enable persistent logging
- Set consistent formatting for all log messages

### Challenge: Log Level Control from Command Line

**Problem:** Users needed a way to control logging verbosity without changing code, especially when debugging issues.

**Solution:**
- Added a command-line argument `--log-level` to the training script
- Implemented dynamic setting of log levels based on the argument
- Configured the root logger to propagate the level to all child loggers
- Provided clear documentation on how to use different log levels

### Challenge: Balancing Verbosity and Performance

**Problem:** Debug logging can generate enormous amounts of data, potentially slowing down the application and creating large log files.

**Solution:**
- Used appropriate log levels to categorize messages (DEBUG, INFO, WARNING, ERROR)
- Made DEBUG the most verbose level with detailed data shape, content, and processing information
- Set INFO as the default level for normal operation
- Ensured logging statements use lazy evaluation for expensive operations (e.g., `f"Large data: {large_data}"` only evaluated when that log level is enabled)

These improvements significantly enhanced our ability to diagnose issues during development while maintaining clean operation in production use.

## Test Refactoring Errors

### 2023-03-09: Test Refactoring

#### Missing Dependencies
When running the tests, we encountered several missing dependencies:
```
ModuleNotFoundError: No module named 'pandas'
ModuleNotFoundError: No module named 'numpy'
ModuleNotFoundError: No module named 'streamlit'
```

Need to install the required dependencies before running the tests. 