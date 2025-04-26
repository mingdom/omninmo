# MLflow Guide

## Overview
This guide explains how to use MLflow for tracking model training experiments and managing model artifacts.

## Tracked Metrics
- RMSE (Root Mean Square Error)
- MAE (Mean Absolute Error)
- R² (R-squared)
- Feature importance
- Training time

## Parameters
- Learning rate
- Max depth
- Number of estimators
- Random state
- Training period
- Forward days

## Example Usage

### Basic Training Run
```python
# Train model with MLflow tracking
python -m src.v2.train
```

### Parameter Tuning
```python
# Try different learning rates
python -m src.v2.train --learning-rate 0.05
python -m src.v2.train --learning-rate 0.1
```

## Viewing Results
1. Start MLflow UI:
```bash
mlflow ui
```

2. Open browser at http://localhost:5000

## Best Practices
1. Tag important runs
2. Log all parameters
3. Save model artifacts
4. Document experiments

## Troubleshooting
1. Check logs for errors
2. Verify metrics are logged
3. Ensure artifacts are saved

## Further Reading

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [SHAP Documentation](https://shap.readthedocs.io/en/latest/)
- [XGBoost with MLflow Tutorial](https://mlflow.org/docs/latest/tutorials-and-examples/tutorial.html) 