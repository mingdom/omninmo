*** NOTE ***: This file is no longer used. We should create new log files for every new log entry moving forward.

# Development Log

## 2023-06-12: Project Reboot

### Goals
- Simplify the project architecture by moving from a Streamlit app to a console-based application
- Keep the folder structure flat and minimalist in `src/v2`
- Maintain core functionality: model training and stock predictions

### Implementation Plan
1. Create flat structure in `src/v2` with just a few Python scripts
2. Maintain the ability to train models via `make train`
3. Create a new console app for predictions
4. Focus on simplicity and readability

### Today's Changes
- Created basic directory structure
- Set up development logs
- Planning simpler implementations of core components

## 2023-06-13: Implementing v2

### Components Created
- **src/v2/config.py**: Simple configuration utility
- **src/v2/data_fetcher.py**: Data fetching from API or sample generator
- **src/v2/features.py**: Feature engineering for stock data
- **src/v2/predictor.py**: XGBoost-based prediction model
- **src/v2/train.py**: Training script
- **src/v2/console_app.py**: Console application for predictions
- **scripts/v2_train.py**: Command-line script for training
- **scripts/v2_predict.py**: Command-line script for predictions

### Makefile Updates
- Updated `make train` to use v2 implementation
- Added `make predict` for running predictions on watchlist
- Added `make predict-ticker` for single ticker predictions
- Updated `make pipeline` for end-to-end testing

### Key Improvements
- Simplified flat structure without nested directories
- Focused on console output rather than web UI
- Maintained core prediction functionality
- Kept configuration through config.yaml
- Improved error handling and logging

### Next Steps
- Test the implementation with real data
- Evaluate prediction accuracy
- Consider additional console features (e.g., charts, comparison)

## 2025-03-10: End-to-End Testing and Fixes

Successfully completed end-to-end testing of the prediction pipeline:

1. Model Training
   - Trained model on sample data for 50 tickers
   - Generated 41 features per ticker
   - Achieved R² score of 0.3896 on test set
   - Top features by importance:
     - EMA 50-day (0.0571)
     - SMA 200-day (0.0466)
     - EMA 20-day (0.0449)

2. Prediction Testing
   - Successfully loaded trained model
   - Tested predictions with AAPL ticker
   - Fixed DataFrame modification warnings in predictor
   - Improved feature handling:
     - Safe removal of unused columns
     - Proper handling of non-numeric data
     - Consistent feature ordering

3. Next Steps
   - Consider adding more features to improve model performance
   - Implement backtesting to validate prediction accuracy
   - Add more comprehensive error handling for edge cases

## 2024-03-12: Training with Real Market Data

After fixing the non-numeric feature issue by properly filtering columns in the feature generation process, successfully trained the model with real market data:

### Data Overview
- Successfully processed 50 tickers
- 60,359 total samples with 46 features
- All features confirmed to be numeric (float64 or int64)

### Top 10 Most Important Features
1. SMA 5-day (10.90%)
2. SMA 20-day (5.73%)
3. 10-day Volatility (5.09%)
4. Bollinger Band Lower (4.61%)
5. EMA 50-day (4.42%)
6. MACD Signal (4.39%)
7. 60-day Return (3.73%)
8. Close to SMA 200 (3.60%)
9. Open Price (3.59%)
10. SMA 200-day (3.24%)

### Model Performance
- RMSE: 0.1442
- MAE: 0.0953
- R²: 0.5948

### Key Insights
- Model performance improved significantly with real data (R² increased from 0.3774 to 0.5948)
- Short-term indicators (SMA 5-day, volatility) are more influential than in sample data
- Moving averages remain important predictors
- Price momentum (returns) and volatility play significant roles
- The cumulative importance of the top 10 features is 49.29%

### Next Steps
- Consider feature selection based on importance scores
- Investigate potential overfitting given the higher R² score
- Implement cross-validation to validate model robustness
- Test prediction accuracy on out-of-sample data
