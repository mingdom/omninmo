# Config Refactoring Plan

## Current State
- Single `config.yaml` file containing all configuration settings
- File includes settings for models, app, data sources, logging, etc.
- Growing complexity makes it harder to maintain
- Several configuration sections are no longer actively used (from a previous Streamlit app)

## Proposed Structure
```
config/
├── app.yaml         # App UI and general settings (partially used)
├── charts.yaml      # Chart visualization settings (deprecated)
├── data.yaml        # Data sources and sample data (partially used)
├── features.yaml    # Feature engineering parameters (actively used)
├── logging.yaml     # Logging configuration (deprecated)
├── model.yaml       # ML model parameters (actively used)
├── rating.yaml      # Rating scales and colors (deprecated)
└── config.yaml      # Main file that imports all others
```

## Implementation Steps

1. Create the `config` directory
2. Extract each section into its own YAML file:
   - `model.yaml`: All XGBoost settings, normalization, training parameters (actively used)
   - `rating.yaml`: Rating mappings and color schemes (deprecated - previously used in Streamlit UI)
   - `app.yaml`: UI settings, layout, cache, watchlist (partially used)
   - `data.yaml`: FMP API settings, sample data (partially used)
   - `logging.yaml`: Log levels, handlers, file settings (deprecated - logging configured in code)
   - `charts.yaml`: Chart types, colors, technical indicators (deprecated - previously used in Streamlit UI)
   - `features.yaml`: Feature engineering thresholds and parameters (actively used)
3. Create a main `config.yaml` that imports all section files
4. Mark deprecated configuration values to indicate they are not currently used
5. Update documentation to reflect the new structure

## Benefits
- Improved maintainability
- Better organization of related settings
- Easier to locate and modify specific configurations
- Reduced merge conflicts when multiple developers work on different aspects
- Clearer distinction between active and deprecated settings

## Considerations
- Ensure proper documentation of the new structure
- Consider implementing validation for each config section
- Add clear comments for deprecated sections that are preserved for potential future use

## Active vs. Deprecated Analysis

After analyzing the codebase, we found that several configuration sections are no longer actively used. This is likely due to the project's transition from a Streamlit app to a console-based application (referenced in devlog from 2025-03-10). Here's the breakdown:

### Actively Used Configurations

- **model.xgboost**: Used in predictor.py for model parameters
- **model.normalization**: Used in predictor.py for normalizing predictions
- **model.training**: Used in train.py for specifying training parameters
- **app.watchlist.default**: Used in console_app.py for default tickers
- **data.max_age_days**: Used in console_app.py for data freshness checks
- **data.fmp.api_key**: Used in data_fetcher.py for API authentication
- **features.thresholds**: Used in features.py for feature generation parameters
- **features.min_rolling_periods**: Used in features.py for calculations
- **features.volatility**: Used in features.py for volatility calculations

### Deprecated/Unused Configurations

- **rating.map** and **rating.colors**: No direct usage found (likely for Streamlit UI)
- **app.title**, **app.icon**, **app.layout**, **app.initial_sidebar_state**: No direct usage found (likely for Streamlit UI)
- **app.parallel_processing.max_workers**: No direct usage found
- **data.sample_data**: Not directly used (sample data generation uses hardcoded values)
- **logging.level**, **logging.file**, **logging.handlers**: Not directly used (logging configured in code)
- **charts.candlestick**, **charts.technical**: No direct usage found (likely for Streamlit UI)

## Technical Implementation

### Configuration Loading Approach

We'll need to implement a configuration loader that:

1. Loads the main `config.yaml` file
2. Processes the `imports` section to load and merge all specified configuration files
3. Builds a unified configuration object that maintains the same structure as the current config

Example Python implementation:

```python
import os
import yaml
from typing import Dict, Any


def load_config(config_dir: str = "config") -> Dict[str, Any]:
    """
    Load the configuration from multiple YAML files.
    
    Args:
        config_dir: Directory containing the configuration files
        
    Returns:
        Dict containing the merged configuration
    """
    # Load the main config file
    main_config_path = os.path.join(config_dir, "config.yaml")
    with open(main_config_path, "r") as f:
        main_config = yaml.safe_load(f)
    
    # Initialize the merged config
    merged_config = {}
    
    # Process imports
    for import_file in main_config.get("imports", []):
        import_path = os.path.join(config_dir, import_file)
        with open(import_path, "r") as f:
            section_config = yaml.safe_load(f)
            
        # Get section name from filename (without extension)
        section_name = os.path.splitext(os.path.basename(import_file))[0]
        
        # Add to merged config
        merged_config[section_name] = section_config
    
    return merged_config
```

## Migration Plan

1. Create the new config directory and files (as outlined above)
2. Implement the configuration loading mechanism
3. Mark deprecated sections with comments
4. Modify the code to use the new configuration structure
5. Test thoroughly to ensure all functionality works correctly
6. Update documentation to reflect the changes

## File Examples

### 1. config/model.yaml (actively used)
```yaml
# Model Configuration
xgboost:
  learning_rate: 0.1
  max_depth: 6
  n_estimators: 100
  random_state: 42
  test_size: 0.2
normalization:
  method: "sigmoid"  # Options: sigmoid, linear, tanh
  sigmoid_k: 10      # Scaling factor for sigmoid
  linear_min: -0.1   # -10% maps to 0 (for linear method)
  linear_max: 0.1    # +10% maps to 1 (for linear method)
training:
  # Number of days to look ahead for prediction
  forward_days: 90
  # Historical data period for training
  period: "10y"
  # Data interval
  interval: "1d"
  # Minimum data requirements
  min_data_days: 60
  min_feature_days: 30
  # Score thresholds
  score_thresholds:
    strong_buy: 0.8
    buy: 0.6
    hold: 0.4
    sell: 0.2
    strong_sell: 0.0
  # Return thresholds
  rating_thresholds:
    strong_buy: 0.15
    buy: 0.08
    hold: -0.08
    sell: -0.15
    strong_sell: -0.15
  # Default tickers for training
  default_tickers:
    - AAPL
    - AMAT
    # ... remaining tickers
```

### 2. config/rating.yaml (deprecated)
```yaml
# Rating Configuration
# DEPRECATED: These settings are not currently used in the console application
# They were likely used in the previous Streamlit UI
map:
  0: "Strong Sell"
  1: "Sell"
  2: "Hold"
  3: "Buy"
  4: "Strong Buy"
colors:
  strong_buy: "#1E8449"  # Dark Green
  buy: "#82E0AA"        # Light Green
  hold: "#F4D03F"       # Yellow
  sell: "#F5B041"       # Orange
  strong_sell: "#C0392B" # Red
```

### 3. config/app.yaml (partially used)
```yaml
# App Configuration
# NOTE: Only the watchlist section is currently used in the console application
# Other settings are preserved for potential future UI implementation

# DEPRECATED: Used in previous Streamlit UI
title: "omninmo - Stock Prediction"
icon: "📈"
layout: "wide"
initial_sidebar_state: "expanded"

# ACTIVE: Used for cache timeouts
cache:
  ttl: 86400  # Cache time to live in seconds

# ACTIVE: Used in console_app.py
watchlist:
  default:
    - AI
    - AMAT
    # ... remaining tickers

# DEPRECATED: Not currently used
parallel_processing:
  max_workers: 5
```

### 4. config/data.yaml (partially used)
```yaml
# Data Configuration
# ACTIVE: Used for API access
fmp:
  api_key: ${FMP_API_KEY}  # Will be loaded from environment variable
  cache_dir: "cache"

# ACTIVE: Used in console_app.py
max_age_days: 30  # Maximum age of data before requiring refresh

# DEPRECATED: Sample data generation uses hardcoded values instead
sample_data:
  default_prices:
    AAPL: 175.0
    MSFT: 380.0
    # ... remaining price data
  default_volatility:
    AAPL: 0.015
    MSFT: 0.018
    # ... remaining volatility data
```

### 5. config/logging.yaml (deprecated)
```yaml
# Logging Configuration
# DEPRECATED: Logging is currently configured directly in each file
# These settings are preserved for potential future centralized logging
level: DEBUG
file:
  max_bytes: 10485760  # 10MB
  backup_count: 5
  directory: "logs"
handlers:
  trainer: "trainer.log"
  feature_engineer: "feature_engineer.log"
  xgboost_predictor: "xgboost_predictor.log"
  fmp_data_fetcher: "fmp_data_fetcher.log"
```

### 6. config/charts.yaml (deprecated)
```yaml
# Chart Configuration
# DEPRECATED: These settings are not currently used in the console application
# They were likely used in the previous Streamlit UI
candlestick:
  height: 600
  template: "plotly_white"
technical:
  moving_averages:
    - 50
    - 200
  colors:
    ma_50: "orange"
    ma_200: "red"
    volume: "rgba(0, 0, 255, 0.5)"
```

### 7. config/features.yaml (actively used)
```yaml
# Feature Configuration
# ACTIVE: Used in features.py
thresholds:
  rsi: 30  # RSI oversold/overbought threshold
  stochastic:
    low: 30  # Stochastic oversold threshold
    high: 70  # Stochastic overbought threshold
  volume_increase: 25  # Volume increase threshold (percentage)
  trend_strength: 25  # ADX trend strength threshold
min_rolling_periods: 30  # Minimum periods for rolling calculations
volatility:
  base_window: 30  # Base window for volatility comparisons (days)
```

### 8. config/config.yaml (Main file)
```yaml
# Main configuration file that imports all section files
imports:
  # Actively used configurations
  - model.yaml
  - features.yaml
  
  # Partially used configurations
  - app.yaml
  - data.yaml
  
  # Deprecated configurations (preserved for potential future use)
  - rating.yaml
  - logging.yaml
  - charts.yaml
``` 