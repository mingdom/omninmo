# 2024-03-14: Integrated MLflow and SHAP for Enhanced Model Tracking

## Changes Made

1. **Added MLflow Integration**
   - Installed MLflow for experiment tracking
   - Created function `log_mlflow_metrics()` to log parameters, metrics, and artifacts
   - Updated `train.py` to use MLflow tracking
   - Set up local tracking in `./logs/mlruns` directory

2. **Added SHAP for Model Interpretability**
   - Installed SHAP library for advanced feature importance analysis
   - Implemented SHAP summary plots for global feature importance
   - Added SHAP dependence plots for top features
   - Integrated with MLflow for visualization storage

3. **Enhanced Visualization**
   - Feature importance bar charts
   - SHAP summary plots
   - SHAP dependence plots for top features

4. **Documentation**
   - Created `docs/mlflow_usage.md` with instructions for using MLflow UI
   - Added interpretation guide for SHAP visualizations
   - Documented best practices for comparing model runs

## Technical Details

### MLflow Integration
- Local tracking URI: `file:./logs/mlruns`
- Logged parameters:
  - Model configuration (learning rate, max depth, etc.)
  - Data coverage (processed/skipped tickers)
  - Dataset statistics (sample count, feature count)
- Logged metrics:
  - Cross-validation metrics with standard deviations
  - Final model performance metrics
  - Feature stability score
- Logged artifacts:
  - Trained model file
  - Feature importance plots
  - SHAP visualizations

### SHAP Implementation
- Used `shap.Explainer` for model-agnostic explanations
- Limited to 1000 samples for large datasets
- Generated three types of visualizations:
  1. Summary plot (global feature importance)
  2. Dependence plots for top 3 features
  3. Feature importance bar chart

## Benefits

1. **Enhanced Model Understanding**
   - Deeper insights into feature importance
   - Visual representation of feature impacts
   - Better understanding of model behavior

2. **Improved Experiment Tracking**
   - Comprehensive history of all training runs
   - Easy comparison between different models
   - Parameter impact visualization

3. **Better Decision Making**
   - Data-driven model selection
   - Clear visualization of trade-offs
   - Identification of key features

## Next Steps

1. **Potential Improvements**
   - Add hyperparameter optimization with MLflow
   - Implement model versioning and promotion
   - Create automated reports comparing runs

2. **Usage Recommendations**
   - Run MLflow UI after training to analyze results
   - Compare runs with different parameters
   - Use SHAP plots to understand feature impacts

## Usage

To view training results:
```bash
mlflow ui --backend-store-uri file:./logs/mlruns
```

Then open your browser to http://127.0.0.1:5000 