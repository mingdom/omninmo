# Development Errors Log

This file documents errors encountered during development along with their resolutions.

## Format

```
## YYYY-MM-DD: Error Description

### Error
Error message goes here

### Context
What we were trying to do when the error occurred

### Resolution
How the error was resolved

## 2023-06-13: Random.normalvariate() Error in Sample Data Generation

### Error
```
Random.normalvariate() takes from 1 to 3 positional arguments but 4 were given
```

### Context
When running the pipeline with sample data, we encountered an error in the data_fetcher.py file. The random.normalvariate() function was being called with incorrect arguments when generating sample data.

### Resolution
Changed the implementation to use numpy's random functions instead:

```python
# Before
df['Open'] = df['Close'] * (1 + random.normalvariate(0, 0.005, len(df)))
df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + abs(random.normalvariate(0, 0.005, len(df))))
df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - abs(random.normalvariate(0, 0.005, len(df))))
df['Volume'] = random.normalvariate(1000000, 200000, len(df))

# After
df['Open'] = df['Close'] * (1 + np.random.normal(0, 0.005, len(df)))
df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + abs(np.random.normal(0, 0.005, len(df))))
df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - abs(np.random.normal(0, 0.005, len(df))))
df['Volume'] = np.random.normal(1000000, 200000, len(df))
```

The Python `random.normalvariate()` function takes only a mean and standard deviation, while we were trying to generate an array of random values. Numpy's `np.random.normal()` can generate arrays of random values, which is what we needed.

## 2023-06-13: XGBoost Error with Non-numeric Data

### Error
```
DataFrame.dtypes for data must be int, float, bool or category. When categorical type is supplied, The experimental DMatrix parameter`enable_categorical` must be set to `True`. Invalid columns:label: object
```

### Context
When trying to make predictions with our trained model, we encountered an error because some of the feature columns contained non-numeric data. XGBoost requires all input data to be numeric.

### Resolution
Added preprocessing in the predict method to ensure all features are numeric:

```python
# Ensure all features are numeric
for col in features.columns:
    if features[col].dtype == 'object':
        logger.warning(f"Converting non-numeric column {col} to numeric")
        features[col] = pd.to_numeric(features[col], errors='coerce')

# Fill any NaN values that might have been introduced
features = features.fillna(0)
```

This code converts any non-numeric columns to numeric values, and fills any resulting NaN values with zeros to ensure the data is valid for XGBoost.

## 2023-06-13: XGBoost Feature Mismatch Error

### Error
```
feature_names mismatch: ['Close', 'Open', 'High', 'Low', 'Volume', ...] ['Open', 'High', 'Low', 'Close', 'adjClose', 'Volume', 'unadjustedVolume', 'change', 'changePercent', 'vwap', 'label', 'changeOverTime', ...]
training data did not have the following fields: change, vwap, changePercent, label, changeOverTime, adjClose, unadjustedVolume
```

### Context
When making predictions, we encountered a feature mismatch error because the features used during training were different from the features available during prediction. This can happen when data comes from different sources or when the feature engineering process changes.

### Resolution
Enhanced the predict method to handle feature mismatches:

1. Store feature names during training:
```python
# Store feature names for prediction
self.feature_names = X.columns.tolist()
```

2. Ensure prediction data has the same features in the same order:
```python
# Check if we have the expected feature names
if self.feature_names is not None:
    # Get the intersection of available features
    common_features = list(set(features.columns) & set(self.feature_names))
    
    if len(common_features) < len(self.feature_names):
        missing_features = set(self.feature_names) - set(common_features)
        logger.warning(f"Missing features: {missing_features}")
        
        # Add missing features with zeros
        for feature in missing_features:
            features[feature] = 0
    
    # Remove extra features not used in training
    extra_features = set(features.columns) - set(self.feature_names)
    if extra_features:
        logger.warning(f"Removing extra features not used in training: {extra_features}")
        features = features[self.feature_names]
    
    # Ensure features are in the same order as during training
    features = features[self.feature_names]
```

This ensures that the prediction data has exactly the same features in the same order as the training data, which is required by XGBoost.

## Non-numeric Feature Error in Training Data

### Error Message
```
ValueError: DataFrame.dtypes for data must be int, float, bool or category. When categorical type is supplied, The experimental DMatrix parameter `enable_categorical` must be set to `True`. Invalid columns:label: object
```

### Context
When training the model with real market data, XGBoost rejected a non-numeric column named 'label' that contained date strings (e.g., "March 13, 20").

### Investigation
- The 'label' column appears to be coming from the API data
- Sample values show it contains date strings in the format "Month DD, YY"
- This column is not actually a feature we want to use for training
- The column was inadvertently included in the feature set

### Resolution
1. Modified the `generate` method in `Features` class to explicitly list all desired columns
2. Created a comprehensive list of 46 numeric features to use for training:
   - Price data (Open, High, Low, Close, Volume)
   - Returns (1d, 5d, 10d, 20d, 60d, log)
   - Moving averages (SMA and EMA with periods 5, 10, 20, 50, 200)
   - Technical indicators (RSI, MACD, Bollinger Bands)
   - Volatility measures
3. Verified that all selected features are numeric (float64 or int64)
4. Successfully trained model with R² score of 0.5948

### Prevention
- Always explicitly specify which columns to use for training
- Add data type validation earlier in the pipeline
- Document expected data types for all features
- Consider adding automated tests for feature data types

## MLflow Experiment Not Found Error (2024-03-14)

### Error Message
```
mlflow.exceptions.MlflowException: Could not find experiment with ID 0
```

### Reproduction Steps
1. Installed MLflow and SHAP packages
2. Created MLflow integration in `training_summary.py`
3. Attempted to run training with `python -m src.v2.train --force-sample --yes`
4. Error occurred when trying to start an MLflow run without creating an experiment first

### Root Cause
MLflow requires an experiment to be created before starting a run. By default, it tries to use experiment ID 0, but this doesn't exist in a fresh MLflow installation.

### Solution
Modified the `log_mlflow_metrics` function in `training_summary.py` to:
1. Check if the experiment exists
2. Create the experiment if it doesn't exist
3. Pass the experiment ID explicitly when starting a run

```python
# Create experiment if it doesn't exist
experiment_name = "stock_prediction"
try:
    experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
except:
    experiment_id = mlflow.create_experiment(experiment_name)

# Start a new MLflow run with explicit experiment ID
with mlflow.start_run(run_name=run_name, experiment_id=experiment_id) as run:
    # ... rest of the code
```

### Prevention
Always check if an experiment exists before starting an MLflow run, especially in a new environment or when setting up MLflow for the first time.

## March 12, 2024 - Perfect Model Consistency Error

### Error Description
Model training was showing perfect consistency in performance metrics and feature importance across different training runs, which is statistically improbable.

### Repro Steps
1. Run training multiple times with same parameters:
```bash
python -m src.v2.train --period 10y --forward-days 90 -y
```
2. Compare cross-validation results and feature importance scores
3. Observe identical metrics across runs:
   - R² scores: 0.6809 ± 0.0131
   - Feature stability: 0.7882
   - Feature rankings identical

### Root Cause
1. Fixed random state (42) in model initialization
2. Same model instance being reused across cross-validation folds
3. No randomization in final model training

### Fix
1. Modified `Predictor` class to use timestamp-based random states
2. Updated cross-validation to create new model instances per fold
3. Added fresh random state for final model training

### Verification
After fix:
- R² scores show natural variation (0.6723 ± 0.0260)
- Feature stability score decreased to 0.6547
- Feature rankings vary between runs

### Prevention
1. Always use dynamic random states in model training
2. Create fresh model instances for each training iteration
3. Add unit tests to verify training variability

## Silent Error Swallowing in DataFetcher

## Error Description
The `DataFetcher` class was silently falling back to sample data in several error conditions without informing the user or requiring explicit permission. This violated our tenet of never hiding errors.

## Repro Steps
1. Run training without setting FMP_API_KEY:
```bash
make train
```
2. Observe that the training proceeds with sample data without any error

## Root Cause
The `fetch_data` method in `DataFetcher` was designed to automatically fall back to sample data in three cases:
1. When no API key was set (`if force_sample or not self.api_key`)
2. When API request failed (in the exception handler)
3. When API returned no data (in the empty data check)

This design choice prioritized convenience over error visibility and control.

## Fix
1. Modified `fetch_data` to raise errors instead of falling back to sample data:
   - Added `ValueError` when no API key is set
   - Propagate API errors instead of catching and swallowing them
   - Raise `ValueError` when API returns no data
2. Only use sample data when explicitly requested via `force_sample=True`
3. Added clear error messages with instructions on how to fix issues

## Verification
1. Run without API key:
```bash
unset FMP_API_KEY
make train
```
Expected: Error about missing API key

2. Run with explicit sample data request:
```bash
make train-sample
```
Expected: Successfully runs with sample data

## Prevention
1. Added docstring documenting error cases
2. Error messages include actionable steps
3. Follow the tenet: "Debug errors fully! Never hide an error by swallowing it"

## Data Shuffling Error in Training Pipeline

### Error Description
Training pipeline was producing identical results across different runs, even with random seeds in cross-validation.

### Reproduction Steps
1. Run `make train` multiple times
2. Observe identical metrics across runs
3. Check cross-validation splits - they are identical despite random seeds

### Root Cause
Data was being processed and combined in a deterministic order:
1. Tickers processed alphabetically
2. Each ticker's data sorted by date
3. Data concatenated in this fixed order
4. Cross-validation splits on ordered data produced identical folds

### Fix
Modified `src/v2/train.py`:
- Added random shuffling of combined dataset before training
- Used `np.random.permutation` to generate random indices
- Applied same shuffling to both features and targets
- Added data type logging for debugging

### Verification
Run training multiple times and observe:
- Different metrics across runs
- Variation in cross-validation splits
- Stable overall performance
- Different feature importance rankings

### Prevention
- Added documentation about data ordering effects
- Added logging of data shapes and types
- Consider adding tests for data shuffling
- Monitor feature stability scores
