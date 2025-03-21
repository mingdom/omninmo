# Model Documentation

## Overview
The stock prediction model uses XGBoost for regression to predict future stock returns. The model is designed to be simple and efficient, focusing on key technical indicators and price patterns.

## Model Architecture
1. **Regression Model**
   - Uses XGBoost regressor
   - Predicts future returns directly (percentage change over the next N days)
   - Default configuration: `learning_rate=0.1`, `max_depth=6`, `n_estimators=100`

## Features
The model uses a variety of technical indicators as features:

- **Price Returns**
  - 1-day returns: Recent price momentum
  - 20-day returns: Medium-term trend
  
- **Moving Averages**
  - 50-day SMA: Medium-term trend indicator
  - 200-day SMA: Long-term trend indicator
  - SMA crossovers: Trend change signals
  
- **Oscillators**
  - RSI (14-day): Oversold/overbought conditions
  - Stochastic: Price position relative to range
  
- **Volatility Metrics**
  - 30-day historical volatility
  - Volatility trend (expanding/contracting)
  
- **Volume Analysis**
  - Volume relative to average
  - Volume trend
  - Price/volume divergence

## Training Process
1. **Data Preprocessing**
   - Fetch historical price data for multiple tickers
   - Remove tickers with insufficient data
   - Calculate future returns for target variable
   
2. **Feature Generation**
   - Calculate technical indicators
   - Handle missing values
   - Ensure feature quality
   
3. **Cross-Validation**
   - K-fold validation to assess model stability
   - Feature importance analysis across folds
   
4. **Final Model Training**
   - Train on complete dataset after validation
   - Save model and feature importance
   
5. **Performance Evaluation**
   - Calculate accuracy metrics
   - Generate training summary

## Prediction Horizon
The model predicts returns over a configurable time horizon (default: 30 days). This parameter can be adjusted in the configuration file:
```yaml
training:
  forward_days: 30  # Number of days to look ahead
```

## Model Output

The model produces two primary outputs for each prediction:

1. **Predicted Return**
   - Raw predicted return value (e.g., -17.60%)
   - Direct output from the XGBoost regression model
   - Represents expected price change over the prediction horizon
   - Example: A predicted return of +8% means the model expects the stock price to increase by 8% over the next 30 days
   - Example: A predicted return of -17.60% indicates an expected significant decline

2. **Normalized Score (0-1)**
   - Transformation of the predicted return to a [0,1] range for easier comparison
   - Uses one of three normalization methods (configurable):
     - Sigmoid: score = 1/(1 + e^(-k*return))
     - Tanh: score = (tanh(k*return) + 1)/2
     - Linear: score = (return - min)/(max - min)
   - Score interpretation:
     - 0.5: Neutral outlook (no expected change)
     - > 0.5: Positive outlook (stronger the higher it goes)
     - < 0.5: Negative outlook (stronger the lower it goes)
   - The 'k' parameter controls sensitivity (default: 10)
   - Examples:
     - Score of 0.75: Strong positive outlook
     - Score of 0.03: Very strong negative outlook
     - Score of 0.55: Slightly positive outlook

Note: The normalized score provides a standardized way to compare predictions across different market conditions and time periods, while the raw predicted return provides directly actionable insights about expected price movement.

## Interpreting Predictions

When using model predictions, consider:

1. **Prediction Horizon**: All predictions are for the configured time period (default: 30 days)
2. **Return vs Score**: 
   - Use the predicted return for understanding expected price movement
   - Use the score for comparing predictions across different stocks/time periods
3. **Context Matters**: Consider market conditions and company-specific news
4. **Uncertainty**: All predictions have inherent uncertainty
5. **Ensemble Approach**: Use predictions as one of multiple signals in investment decisions

## Performance Metrics
- **RMSE** (Root Mean Square Error): Measures prediction accuracy, with lower values indicating better performance
- **MAE** (Mean Absolute Error): Average absolute difference between predicted and actual returns
- **R²** (R-squared): Proportion of variance explained by the model (0-1, higher is better)

## Future Improvements
- Enhanced feature selection
- Hyperparameter optimization
- Improved risk metrics
- Better uncertainty estimation
- Sector-specific models
- Integration of fundamental data
