# Model Documentation

## Overview
The stock prediction model uses XGBoost for regression to predict future stock returns. The model is designed to be simple and efficient, focusing on key technical indicators and price patterns.

## Model Architecture
1. **Regression Model**
   - Uses XGBoost regressor
   - Predicts future returns directly
   - Converts predictions to ratings based on return thresholds

## Features
- Price returns (1d, 20d)
- Simple moving averages (50d, 200d)
- RSI (14-day)
- Basic volatility (30-day)
- Volume metrics

## Training Process
1. Data preprocessing
2. Feature generation
3. Cross-validation
4. Final model training
5. Performance evaluation

## Model Output
- Predicted return
- Normalized score (0-1)
- Rating (Strong Buy to Strong Sell)
- Confidence score

## Performance Metrics
- RMSE (Root Mean Square Error)
- MAE (Mean Absolute Error)
- R² (R-squared)

## Future Improvements
- Enhanced feature selection
- Hyperparameter optimization
- Improved risk metrics
- Better confidence estimation
