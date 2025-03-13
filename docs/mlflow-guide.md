# MLflow Guide: Model Tracking and Analysis

This guide explains how to use MLflow with omninmo to track, analyze, and compare model training experiments.

## What is MLflow?

MLflow is an open-source platform for managing the machine learning lifecycle, including experimentation, reproducibility, deployment, and a central model registry. In omninmo, we use MLflow primarily for:

1. **Experiment Tracking**: Recording parameters, metrics, and artifacts for each training run
2. **Model Comparison**: Comparing different models side-by-side
3. **Feature Analysis**: Understanding which features have the most impact on predictions
4. **Model Interpretability**: Using SHAP plots to understand how features affect predictions

## Getting Started with MLflow

### Viewing Training Results

After running a training command like `make train` or `make train-sample`, two things happen:

1. A console-based executive summary is displayed
2. A detailed MLflow run is created with all metrics, parameters, and visualizations

To view the detailed results:

```bash
# Start the MLflow UI
make mlflow
```

Then open your browser to http://127.0.0.1:5000 to access the MLflow UI.

### MLflow Directory Structure

MLflow stores its data in the `mlruns` directory:

```
mlruns/
├── 0/                      # Default experiment
│   ├── <run_id>/          # Individual run data
│   │   ├── metrics/       # Run metrics
│   │   ├── params/        # Run parameters
│   │   └── artifacts/     # Run artifacts (plots, models)
└── 1/                     # Custom experiment
```

## Integration with omninmo

### How Training Creates MLflow Runs

When you train a model using `make train` or `make train-sample`:

1. The training process runs in `src/v2/train.py`
2. Features are generated and the model is trained
3. Cross-validation results are calculated
4. The `log_mlflow_metrics` function in `src/v2/training_summary.py` logs:
   - Model parameters (learning rate, max depth, etc.)
   - Data coverage (processed/skipped tickers)
   - Performance metrics (RMSE, R², accuracy, etc.)
   - Feature importance plots
   - SHAP visualizations
5. The model is saved to the `models` directory
6. A summary is displayed in the console

### Relationship to Other Components

MLflow integrates with several components of omninmo:

- **Training Pipeline**: Logs metrics and artifacts during training
- **Feature Engineering**: Tracks which features are most important
- **Model Evaluation**: Records cross-validation and final model performance
- **Prediction**: Models tracked in MLflow can be loaded for prediction

## Using the MLflow UI

### Experiments View

The main MLflow UI shows all experiments and runs:

1. **Experiments**: Listed on the left sidebar
2. **Runs**: Displayed in the main table
3. **Metrics**: Shown as columns in the table
4. **Parameters**: Can be displayed as columns

### Run Details

Click on a run to see detailed information:

1. **Overview**: Summary of the run
2. **Metrics**: Performance metrics over time
3. **Parameters**: Model configuration
4. **Artifacts**: Visualizations and model files

### Comparing Runs

To compare multiple runs:

1. Select runs using the checkboxes
2. Click "Compare" in the top right
3. View side-by-side comparisons of:
   - Metrics
   - Parameters
   - Visualizations

### Parallel Coordinates Plot

This powerful visualization shows how parameters affect metrics:

1. Select runs to compare
2. Click "Compare"
3. Select "Parallel Coordinates Plot"
4. Each line represents a run
5. See how changing parameters affects metrics

## Practical Examples

### Example 1: Compare Different Training Periods

```bash
# Train with 30-day forward period (default)
make train-sample

# Train with 60-day forward period
python -m src.v2.train --force-sample --forward-days 60

# Compare in MLflow UI
make mlflow
```

In the MLflow UI, select both runs and click "Compare" to see how the different forward periods affect model performance.

### Example 2: Compare Regression vs Classification

```bash
# Train regression model
python -m src.v2.train --force-sample --mode regression

# Train classification model
python -m src.v2.train --force-sample --mode classification

# Compare in MLflow UI
make mlflow
```

Compare the runs to see which approach works better for your use case.

### Example 3: Feature Importance Analysis

1. Run training: `make train-sample`
2. Start MLflow UI: `make mlflow`
3. Click on the run
4. Go to "Artifacts"
5. View the feature importance plots:
   - `feature_importance.png`: Bar chart of feature importance
   - `shap_summary.png`: SHAP summary plot
   - `shap_dependence_*.png`: SHAP dependence plots for top features

## Interpreting Visualizations

### Feature Importance Plot

This bar chart shows the relative importance of each feature:

- Longer bars = more important features
- Features are sorted by importance
- Use this to identify which features drive predictions

### SHAP Summary Plot

This plot shows how features impact predictions:

- Features are ordered by importance (top to bottom)
- Each point represents a sample
- Red points = higher feature values, blue = lower values
- Points to the right = positive impact on prediction, left = negative impact
- Spread indicates the range of impact

### SHAP Dependence Plots

These plots show how specific features affect predictions:

- X-axis: Feature value
- Y-axis: SHAP value (impact on prediction)
- Colors: Interaction with another important feature
- Trend: How the feature's impact changes across its range

## Advanced Usage

### Custom Queries

You can run custom queries on your MLflow data:

```bash
# Get runs with R² > 0.7
mlflow search runs --experiment-ids 572766249267779371 \
  --filter "metrics.final_r2 > 0.7"
```

### Programmatic Access

You can access MLflow data programmatically:

```python
import os
import mlflow

# Set tracking URI to local mlruns directory
mlflow.set_tracking_uri("file:./mlruns")

# Get experiment
experiment = mlflow.get_experiment_by_name("stock_prediction")

# Get runs
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# Analyze runs
best_run = runs.sort_values("metrics.final_r2", ascending=False).iloc[0]
print(f"Best run: {best_run.run_id}, R²: {best_run['metrics.final_r2']}")
```

## Best Practices

1. **Always check feature stability**: A score > 0.8 indicates stable feature importance
2. **Compare similar runs**: Use filters to focus on specific parameters
3. **Look for patterns**: Which features consistently appear as important?
4. **Track progress over time**: Are newer models improving on key metrics?
5. **Document experiments**: Add notes to important runs
6. **Use consistent naming**: Makes it easier to compare similar experiments

## Troubleshooting

### Common Issues

1. **MLflow UI doesn't start**:
   - Check if port 5000 is already in use
   - Try `make mlflow PORT=5001` to use a different port

2. **Missing visualizations**:
   - SHAP plots may not generate for very large datasets
   - Check logs for specific error messages

3. **Experiment not found**:
   - MLflow creates experiments on demand
   - First training run will create the experiment

### Getting Help

If you encounter issues:

1. Check the logs in `logs/train.log`
2. Look for errors in the console output
3. Check the MLflow documentation at https://mlflow.org/docs/latest/index.html

## Further Reading

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [SHAP Documentation](https://shap.readthedocs.io/en/latest/)
- [XGBoost with MLflow Tutorial](https://mlflow.org/docs/latest/tutorials-and-examples/tutorial.html) 