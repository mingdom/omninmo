# Model Analysis Guide: Evaluating Training Results

This guide explains how to analyze and compare model training results in omninmo, using both the executive summary and MLflow metrics.

## Understanding the Executive Summary

After each training run, omninmo displays an executive summary in the console. This provides a quick overview of the model's performance.

### Example Executive Summary

```
=== TRAINING EXECUTIVE SUMMARY ===
Timestamp: 20250312_170821
Mode: regression

Data Coverage:
- Processed tickers: 50
- Success rate: 100.0%

Model Performance:
- Cross-validation R²: 0.6260 ± 0.0236
- Final model R²: 0.7208
- Cross-validation RMSE: 0.1405 ± 0.0036
- Final model RMSE: 0.1216

Feature Analysis:
- Feature stability score: 0.7583
- Top 5 features:
  1. sma_20: 0.0936
  2. ema_20: 0.0612
  3. volatility_10d: 0.0526
  4. macd_signal: 0.0407
  5. return_60d: 0.0373
```

### Interpreting the Executive Summary

#### Data Coverage
- **Processed tickers**: Number of stock tickers successfully processed
- **Success rate**: Percentage of tickers that were successfully processed
  - Higher is better; low rates may indicate data quality issues

#### Model Performance
- **Cross-validation metrics**: Performance across k-fold cross-validation
  - The ± value represents standard deviation across folds
  - Lower standard deviation indicates more consistent performance
- **Final model metrics**: Performance of the model trained on the full dataset
  - Usually better than cross-validation metrics (but beware of overfitting)

#### Feature Analysis
- **Feature stability score**: Measures consistency of feature importance across folds
  - Range: 0-1, where higher is better
  - Values > 0.8 indicate stable feature importance
  - Values < 0.8 suggest feature importance varies between folds
- **Top features**: Most influential features in the model
  - Higher values indicate stronger influence on predictions

## Understanding MLflow Metrics

MLflow logs more detailed metrics than the executive summary. Here's what each metric means:

### Regression Metrics

| Metric | Description | Better When | Typical Range |
|--------|-------------|-------------|--------------|
| `final_r2` | Coefficient of determination (R²) for the final model | Higher | 0 to 1 |
| `final_rmse` | Root Mean Squared Error for the final model | Lower | Depends on data scale |
| `final_mae` | Mean Absolute Error for the final model | Lower | Depends on data scale |
| `cv_r2_mean` | Mean R² across cross-validation folds | Higher | 0 to 1 |
| `cv_r2_std` | Standard deviation of R² across folds | Lower | 0 to 0.1 |
| `cv_rmse_mean` | Mean RMSE across cross-validation folds | Lower | Depends on data scale |
| `cv_rmse_std` | Standard deviation of RMSE across folds | Lower | Depends on data scale |
| `cv_mae_mean` | Mean MAE across cross-validation folds | Lower | Depends on data scale |
| `cv_mae_std` | Standard deviation of MAE across folds | Lower | Depends on data scale |
| `feature_stability` | Consistency of feature importance across folds | Higher | 0 to 1 |

### Classification Metrics

| Metric | Description | Better When | Typical Range |
|--------|-------------|-------------|--------------|
| `final_accuracy` | Accuracy of the final model | Higher | 0 to 1 |
| `cv_accuracy_mean` | Mean accuracy across cross-validation folds | Higher | 0 to 1 |
| `cv_accuracy_std` | Standard deviation of accuracy across folds | Lower | 0 to 0.1 |
| `feature_stability` | Consistency of feature importance across folds | Higher | 0 to 1 |

### Other Parameters

MLflow also logs various parameters that can help you understand the model configuration:

- **Model parameters**: `learning_rate`, `max_depth`, `n_estimators`
- **Data parameters**: `processed_tickers_count`, `total_samples`, `feature_count`
- **Training parameters**: `mode` (regression or classification)

## Systematically Comparing Training Runs

To determine if one training run is superior to another, follow these steps:

### Step 1: Identify Your Primary Metric

Choose the most important metric for your use case:

- **Regression**: Usually `final_r2` or `cv_r2_mean`
- **Classification**: Usually `final_accuracy` or `cv_accuracy_mean`

### Step 2: Check Model Stability

Evaluate the model's stability:

1. **Cross-validation standard deviation**: Lower values indicate more consistent performance
   - `cv_r2_std` < 0.05 is generally good for regression
   - `cv_accuracy_std` < 0.03 is generally good for classification

2. **Feature stability score**: Higher values indicate more stable feature importance
   - `feature_stability` > 0.8 is considered good
   - `feature_stability` < 0.7 suggests potential issues

### Step 3: Compare Primary Metrics

Compare your primary metric across runs:

1. **For regression models**:
   - Higher R² is better (closer to 1)
   - Lower RMSE and MAE are better (closer to 0)

2. **For classification models**:
   - Higher accuracy is better (closer to 1)

### Step 4: Check for Overfitting

Compare final model metrics to cross-validation metrics:

- If `final_r2` is much higher than `cv_r2_mean` (e.g., >0.1 difference), the model may be overfitting
- Similarly for classification, if `final_accuracy` is much higher than `cv_accuracy_mean`

### Step 5: Consider Feature Importance

Analyze which features are driving predictions:

- Are the top features consistent across runs?
- Do the important features make logical sense for stock prediction?
- Is the cumulative importance of top features high enough? (>0.4 is generally good)

## Practical Examples

### Example 1: Comparing Regression Models

Suppose we have two training runs with these metrics:

| Metric | Run A | Run B |
|--------|-------|-------|
| `final_r2` | 0.72 | 0.68 |
| `cv_r2_mean` | 0.63 | 0.65 |
| `cv_r2_std` | 0.024 | 0.015 |
| `feature_stability` | 0.76 | 0.85 |

**Analysis**:
- Run A has higher `final_r2` but lower `cv_r2_mean`
- Run A has higher standard deviation and lower feature stability
- Run B has more consistent performance across folds
- **Conclusion**: Run B is likely superior despite lower `final_r2`, as it's more stable and generalizes better

### Example 2: Detecting Overfitting

| Metric | Run C | Run D |
|--------|-------|-------|
| `final_r2` | 0.85 | 0.72 |
| `cv_r2_mean` | 0.64 | 0.68 |
| `cv_r2_std` | 0.032 | 0.018 |

**Analysis**:
- Run C has much higher `final_r2` than `cv_r2_mean` (0.21 difference)
- Run D has a smaller gap between `final_r2` and `cv_r2_mean` (0.04 difference)
- **Conclusion**: Run C is likely overfitting, while Run D generalizes better

## Using MLflow UI for Comparison

The MLflow UI provides powerful tools for comparing runs:

### Basic Comparison

1. Go to the MLflow UI: `make mlflow`
2. Select the runs you want to compare using the checkboxes
3. Click "Compare" in the top right
4. View side-by-side comparisons of metrics and parameters

### Parallel Coordinates Plot

This visualization is especially useful for understanding how parameters affect metrics:

1. Select runs to compare
2. Click "Compare"
3. Select "Parallel Coordinates Plot"
4. Each line represents a run
5. See how changing parameters affects metrics

### Scatter Plot

To visualize the relationship between two metrics:

1. Select runs to compare
2. Click "Compare"
3. Select "Scatter Plot"
4. Choose metrics for X and Y axes
5. Identify patterns and outliers

## Best Practices for Model Evaluation

1. **Prioritize cross-validation metrics** over final model metrics
   - They better represent how the model will perform on unseen data

2. **Look for consistency** across folds
   - Low standard deviation in cross-validation metrics
   - High feature stability score

3. **Be wary of overfitting**
   - Large gaps between final and cross-validation metrics
   - Unusually high performance on training data

4. **Consider multiple metrics**
   - For regression: R², RMSE, and MAE together
   - For classification: Accuracy along with precision/recall

5. **Check feature importance**
   - Do the important features make logical sense?
   - Is feature importance stable across runs?

6. **Document your findings**
   - Save notes about what worked and what didn't
   - Track improvements over time

## Troubleshooting Common Issues

### Poor Model Performance

If your model has low R² or accuracy:

1. **Check data quality**:
   - How many tickers were successfully processed?
   - Are there enough samples for training?

2. **Examine feature importance**:
   - Are the expected features showing up as important?
   - Is feature importance stable?

3. **Try different parameters**:
   - Adjust learning rate, max depth, or number of estimators
   - Try different prediction modes (regression vs. classification)

### Inconsistent Results

If you see high standard deviation in cross-validation:

1. **Check feature stability score**:
   - Low scores indicate unstable feature importance

2. **Consider data augmentation**:
   - Add more tickers or longer time periods
   - Ensure balanced representation of market conditions

3. **Simplify the model**:
   - Reduce max_depth to prevent overfitting
   - Focus on the most stable features

## Conclusion

Effective model analysis requires looking beyond simple metrics to understand stability, generalization, and feature importance. By systematically comparing runs using both the executive summary and MLflow metrics, you can identify truly superior models that will perform well in production.

Remember that the "best" model isn't always the one with the highest R² or accuracy—it's the one that generalizes well to new data and provides consistent, reliable predictions. 