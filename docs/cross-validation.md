# Cross-Validation Specification

## Why Cross-Validation?

### Problem Statement
Our current stock prediction system uses a simple train-test split to evaluate model performance. This approach has several limitations:
1. High variance in performance estimates due to the randomness of the split
2. Risk of overfitting to a particular market regime in the test set
3. Inability to detect if the model is learning generalizable patterns or just memorizing data
4. Limited understanding of feature importance stability across different data subsets

### Business Impact
Poor model evaluation can lead to:
- Deploying models that perform well in testing but fail in production
- Missing opportunities to improve model robustness
- Reduced confidence in model predictions
- Potential financial losses from overconfident trading decisions

### Goals
1. **Reliability**: Get more reliable estimates of model performance
2. **Robustness**: Ensure models generalize well across different market conditions
3. **Confidence**: Provide clear confidence intervals for performance metrics
4. **Insight**: Better understand feature importance stability
5. **Quality**: Catch overfitting early in the development cycle

## Overview
This document specifies the implementation of k-fold cross-validation in the stock prediction system. Cross-validation is essential for assessing model performance, detecting overfitting, and ensuring the model generalizes well to unseen data.

## Implementation Details

### Core Functionality
- **Method**: K-fold cross-validation
- **Default Configuration**: 5 folds
- **Data Handling**: 
  - Memory-optimized using NumPy arrays
  - Shuffled data splits
  - Consistent random seed for reproducibility
  - Maintains temporal order within folds

### Data Validation
- Minimum sample requirements:
  - At least 2 samples per fold
  - For classification: at least 2 classes
  - Warning if any class has fewer samples than folds
- Data quality checks:
  - No NaN values in features
  - No NaN values in target
  - Appropriate number of classes for classification

### Metrics Tracked

#### Regression Mode
- Root Mean Square Error (RMSE)
- Mean Absolute Error (MAE)
- R² Score
- Standard deviation of all metrics across folds
- Warnings for high variance (> 20% of mean)

#### Classification Mode
- Accuracy
- Detailed classification report per fold
- Standard deviation of accuracy across folds
- Warnings for high variance (> 20% of mean)

### Feature Importance Analysis
- Calculates feature importance for each fold
- Averages importance scores across folds
- Reports top 10 most important features
- Feature stability metrics:
  - Spearman rank correlation between folds
  - Stability score (target > 0.8)
  - Warnings for low stability

### Memory Optimization
- Uses NumPy arrays for data splitting
- Converts to pandas only when required by XGBoost
- Explicit memory cleanup after each fold
- Efficient feature importance storage

## Usage

### Basic Usage
```python
from src.v2.predictor import Predictor

# Initialize predictor
predictor = Predictor(mode='regression')  # or 'classification'

# Perform cross-validation
results = predictor.cross_validate(X, y, n_splits=5)
```

### Return Value Structure

#### Regression Mode
```python
{
    'fold_metrics': [
        {
            'fold': 1,
            'rmse': float,
            'mae': float,
            'r2': float
        },
        # ... one dict per fold
    ],
    'mean_rmse': float,
    'mean_mae': float,
    'mean_r2': float,
    'std_rmse': float,
    'std_mae': float,
    'std_r2': float,
    'feature_importance': {
        'feature_name': importance_score,
        # ... for top features
    },
    'feature_stability': float  # Spearman correlation score
}
```

#### Classification Mode
```python
{
    'fold_metrics': [
        {
            'fold': 1,
            'accuracy': float,
            'classification_report': dict
        },
        # ... one dict per fold
    ],
    'mean_accuracy': float,
    'std_accuracy': float,
    'feature_importance': {
        'feature_name': importance_score,
        # ... for top features
    },
    'feature_stability': float  # Spearman correlation score
}
```

## Logging

### Standard Output
- Progress indicators for each fold
- Key metrics for each fold
- Final averaged results with standard deviations
- Top 10 important features

### Log File
- Detailed metrics for each fold
- Complete feature importance rankings
- Warning messages for any anomalies
- Full classification reports (classification mode)

## Error Handling

### Data Validation
- Checks for sufficient data in each fold
- Validates feature consistency across folds
- Ensures target variable is appropriate for mode

### Graceful Degradation
- Continues processing if a single fold fails
- Reports partial results if available
- Clear error messages for debugging

## Performance Considerations

### Memory Usage
- Processes one fold at a time
- Cleans up intermediate results
- Efficient feature importance storage

### Computation Time
- Reports progress during long runs
- Parallel processing potential for future optimization
- Caches feature importance calculations

## Future Enhancements

### Planned Improvements
1. Stratified k-fold for classification
2. Time-series aware folding
3. Feature importance stability metrics
4. Automated hyperparameter tuning
5. Cross-validation visualization tools

### Integration Points
1. Model selection workflow
2. Automated reporting system
3. Performance monitoring dashboard
4. Model versioning system

## Success Metrics

### Performance Metrics
1. **Model Reliability**
   - Reduced variance between fold performances (target: < 20% std dev)
   - Consistent feature importance rankings across folds (top 5 features should appear in at least 4/5 folds)
   - Clear confidence intervals for all metrics

2. **Statistical Robustness**
   - R² score improvement > 15% compared to single train-test split
   - RMSE reduction > 10% in production predictions
   - Feature importance stability score > 0.8 (measured by Spearman correlation)

3. **Operational Efficiency**
   - Cross-validation runtime < 10 minutes for standard dataset
   - Memory usage < 4GB during validation
   - Zero production incidents due to model overfitting

### Business Success Metrics
1. **Trading Performance**
   - Reduced false signal rate by 25%
   - Improved win rate in live trading by 15%
   - More consistent performance across different market conditions

2. **Development Efficiency**
   - 50% reduction in time spent debugging model issues
   - 30% reduction in model iteration cycles
   - Clear go/no-go criteria for model deployment

### User Experience Metrics
1. **Developer Experience**
   - Clear, actionable insights from validation results
   - Easy to understand validation reports
   - Automated validation as part of CI/CD pipeline

2. **Stakeholder Confidence**
   - Transparent model performance reporting
   - Clear understanding of model limitations
   - Quantifiable confidence in predictions

## Dependencies
- scikit-learn >= 1.0.0
- numpy >= 1.20.0
- pandas >= 1.3.0
- xgboost >= 1.5.0

## Testing Strategy

### Unit Tests
1. Basic functionality with small dataset
2. Edge cases (small folds, missing data)
3. Mode switching (regression/classification)
4. Feature importance calculation

### Integration Tests
1. End-to-end training workflow
2. Results persistence and loading
3. Logging system integration
4. Memory usage monitoring

## Documentation

### Code Documentation
- Detailed docstrings
- Type hints
- Usage examples
- Performance notes

### User Documentation
- Quick start guide
- Configuration options
- Results interpretation
- Troubleshooting guide 