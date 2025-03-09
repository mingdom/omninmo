# Development Log

## 2025-03-10: Fixed Virtual Environment and Pip Installation Issues

- Fixed recurring pip installation issues in macOS:
  - Updated `install-reqs.sh` to use `python3 -m pip` with proper flags
  - Added `--no-warn-script-location` to avoid script location warnings
  - Improved virtual environment handling in Makefile targets
  - Removed dependency on `activate-venv.sh` for make commands
  - Added proper pip upgrade step during installation
  - Fixed the "externally-managed-environment" error permanently

These changes ensure a more robust installation process that works consistently across different macOS environments and Python versions.

## 2025-03-10: Added MIT License

- Added MIT License to the project:
  - Created a LICENSE file in the root directory
  - Updated README.md with license information
  - Selected MIT License as it's permissive and business-friendly while still protecting the work
  - This license allows for both open-source collaboration and potential future commercial use

## 2025-03-10: Improved Makefile and Standardized Command Usage

- Enhanced the Makefile to streamline development workflow:
  - Modified `make env` to automatically handle virtual environment activation
  - Added automatic virtual environment activation to all relevant make targets
  - Eliminated the need for manual `source activate-venv.sh` step
  - Improved user feedback with clearer messages

- Standardized command usage in documentation:
  - Updated README.md to consistently use `make` commands instead of direct Python script calls
  - Reorganized command documentation for better clarity
  - Added more comprehensive list of available make commands
  - Simplified the Quick Start guide to use standardized commands

These changes improve the developer experience by reducing the number of manual steps required and ensuring consistent command usage throughout the project.

## 2025-03-09: Implemented Proper Logging System

- Replaced print statements with a comprehensive logging system for better debugging and monitoring:
  - Used Python's logging module consistently across all key components
  - Implemented structured logging with consistent formats
  - Added file-based logging with daily rotation to store logs at logs/*.log
  - Created different log levels (DEBUG, INFO, WARNING, ERROR) for controlling verbosity
  - Added command-line control of logging levels via --log-level argument in train_model.py

- Key improvements:
  - Enhanced traceability by including timestamps, module names, and log levels in all messages
  - Added detailed debug logs for tracking data shapes, processing steps, and model training progress
  - Implemented rotating file handlers to prevent log files from growing too large
  - Added proper exception handling with full tracebacks in log files
  - Made log verbosity controllable through command-line arguments

- Components updated with proper logging:
  - src/utils/trainer.py
  - src/utils/feature_engineer.py
  - src/models/xgboost_predictor.py
  - scripts/train_model.py

This comprehensive logging system provides better visibility into the model training process and helps diagnose issues more effectively. Normal operation remains clean and focused on essential information, while detailed logs are available when needed for debugging.

## 2025-03-09: Refactored Codebase to Focus on XGBoost and FMP API

Major refactoring to simplify the codebase by removing yfinance and focusing solely on XGBoost:

- Removed yfinance-related data fetching code:
  - Deleted src/data/stock_data_fetcher.py
  - Deleted src/data/fetcher.py
  - Deleted scripts/test_yfinance.py
  
- Consolidated on FMP API as the sole data source:
  - Enhanced src/data/fmp_data_fetcher.py with improved error handling
  - Added sample data capabilities to FMP fetcher
  
- Simplified model architecture to use only XGBoost:
  - Removed src/models/predictor.py (RandomForest-based)
  - Removed src/models/stock_rating_predictor.py (alternative model)
  - Updated src/models/xgboost_predictor.py to remove fallback options
  
- Updated package imports to reflect focus on XGBoost and FMP:
  - Fixed relative vs absolute imports
  - Removed unused imports
  
- Simplified training utilities:
  - Updated src/utils/trainer.py to focus on XGBoost training workflow
  - Updated scripts/train_model.py with command-line arguments
  - Added -y option to automatically overwrite model file
  - Fixed rating system to use 0-4 integer values instead of -2 to 2 for better XGBoost compatibility

These changes significantly reduced code complexity while maintaining all core functionality.

## 2025-03-08: Added FMP API Integration

- Added support for Financial Modeling Prep (FMP) API as an alternative data source
- Implemented caching mechanism to reduce API calls
- Added configuration for API key in .env file
- Created automated tests for the FMP integration

## 2025-03-07: Initial Release

- Deployed basic version with yfinance data fetching
- Implemented Random Forest and XGBoost models
- Created streamlit-based UI for interactive analysis
- Set up CI/CD pipeline for testing and deployment

## 2023-03-09: Test Deletion
We deleted all the tests for now because they are out of date and not worth maintaining atm.

## 2024-03-09: Test Suite Improvements
- Fixed stratification issue in XGBoostRatingPredictor when training with small sample sizes
- Updated test data to use consistent class labels (0, 1, 2)
- All 24 tests now passing successfully

## 2024-03-09
- Fixed XGBoost model training by:
  - Added label encoding to handle string labels
  - Updated train method to return a dictionary with accuracy and classification report
  - Fixed error handling in model training
- Migrated from StockDataFetcher to FMPDataFetcher across all modules
- Updated all code references to use FMPDataFetcher for data fetching
- Added python-dotenv dependency for environment variable management
- dming: Deleted compare_models (deprecated)