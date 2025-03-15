# Phase 1: Core Technical Indicator Improvements

## Feature Set Analysis

### Base Technical Indicators
1. **Moving Averages (Primary)**
   - EMA 8  (short-term trend)
   - EMA 21 (intermediate trend)
   - SMA 50 (medium-term trend)
   - SMA 200 (long-term trend)

2. **MACD Configuration**
   - Extended MACD (50,100,20) for medium-term trend detection
   - Signal line crossovers
   - MACD histogram for momentum measurement

3. **RSI**
   - Maintain RSI 14 as core momentum indicator
   - Add RSI divergence detection

## Feature Selection Strategy

### Approach 1: Let Model Optimize (Pros & Cons)
**Pros:**
- Let the model discover non-obvious relationships
- May find unexpected feature interactions
- More robust across different market conditions

**Cons:**
- Risk of overfitting
- Increased computational complexity
- Harder to interpret model decisions
- May learn spurious correlations

### Approach 2: Manual Feature Reduction (Pros & Cons)
**Pros:**
- Cleaner, more interpretable model
- Faster training and inference
- Based on proven market mechanics
- Easier to debug and maintain

**Cons:**
- May miss valuable feature combinations
- Requires strong domain assumptions
- Less adaptive to changing market conditions

## Recommended Approach: Hybrid Selection
1. **Start with Core Features**
   - The 4 specified moving averages
   - Extended MACD (50,100,20)
   - RSI 14

2. **Feature Engineering**
   - Create composite features:
     * MA crossovers (e.g., EMA8 vs EMA21)
     * Price distance from moving averages
     * RSI extremes with MA context

3. **Validation Process**
   - Use feature importance analysis
   - Remove features with correlation > 0.85
   - Keep top 70% most important features
   - Cross-validate on different market regimes

## Implementation Steps

1. **Data Pipeline Updates**
   ```python
   # Example feature calculation structure
   def calculate_core_features(df):
       # Moving Averages
       df['ema_8'] = calculate_ema(df['close'], 8)
       df['ema_21'] = calculate_ema(df['close'], 21)
       df['sma_50'] = calculate_sma(df['close'], 50)
       df['sma_200'] = calculate_sma(df['close'], 200)
       
       # MACD
       df['macd'], df['signal'], df['hist'] = calculate_macd(
           df['close'], 
           fast=50, 
           slow=100, 
           signal=20
       )
       
       # RSI
       df['rsi_14'] = calculate_rsi(df['close'], 14)
       
       return df
   ```

2. **Feature Selection Framework**
   ```python
   # Example selection process
   def select_features(df, correlation_threshold=0.85):
       # Calculate correlation matrix
       corr_matrix = df.corr()
       
       # Remove highly correlated features
       features_to_drop = []
       for i in range(len(corr_matrix.columns)):
           for j in range(i):
               if abs(corr_matrix.iloc[i, j]) > correlation_threshold:
                   features_to_drop.append(corr_matrix.columns[i])
                   
       return df.drop(columns=features_to_drop)
   ```

3. **Validation Framework**
   ```python
   # Example validation structure
   def validate_features(df, target_periods=[90, 180]):
       results = {}
       for period in target_periods:
           # Create labels for different prediction periods
           df[f'target_{period}d'] = create_labels(df, period)
           
           # Train/test split with time series CV
           scores = time_series_cv(df, period)
           results[period] = scores
           
       return results
   ```

## Success Metrics

1. **Primary Metrics**
   - Prediction accuracy at 90/180 days
   - Sharpe ratio of predictions
   - Maximum drawdown reduction

2. **Secondary Metrics**
   - Feature importance stability
   - Cross-validation consistency
   - Computational efficiency

## Timeline

1. **Week 1**: Implementation of core features
2. **Week 2**: Feature engineering and selection
3. **Week 3**: Validation framework and testing
4. **Week 4**: Optimization and documentation

## Next Steps

1. Implement the core feature calculation pipeline
2. Set up the feature selection framework
3. Create validation scripts
4. Run initial tests with reduced feature set
5. Compare performance with current model 