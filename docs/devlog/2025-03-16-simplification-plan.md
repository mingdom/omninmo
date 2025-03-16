# Codebase Simplification Plan
Date: 2024-03-16

## Objective
Simplify the training architecture to enable faster iteration and reduce complexity while maintaining core functionality.

## Current Complexity Issues
1. Feature Engineering:
   - Excessive number of features with overlapping time windows
   - Complex risk metrics requiring market data
   - Multiple feature generation paths (standard/enhanced)
   - Complex distribution and conditional performance metrics

2. Training Pipeline:
   - Dual mode support (regression/classification)
   - Complex risk-adjusted target calculations
   - Extensive error handling and logging
   - Complex cross-validation process

3. Configuration:
   - Many unused or redundant parameters
   - Multiple normalization methods
   - Complex rating thresholds
   - Large default ticker list

## Simplification Strategy

### 1. Feature Engineering Simplification
#### Keep Only Essential Features:
- Price returns (1d, 20d)
- Simple moving averages (50d, 200d)
- RSI (14d)
- Basic volatility (30d)
- Volume metrics

#### Remove:
- Market-dependent features (beta, correlation)
- Complex risk metrics
- Multiple time window variants
- Distribution features
- Conditional performance metrics

### 2. Training Pipeline Simplification
#### Changes:
- Standardize on regression mode only
- Use simple return as target (remove risk-adjusted)
- Simplify cross-validation
- Remove complex error handling
- Streamline data preprocessing

### 3. Configuration Cleanup
#### Simplify:
- Remove unused parameters
- Use single normalization method
- Remove complex rating thresholds
- Reduce default tickers list
- Simplify model parameters

## Implementation Plan

### Phase 1: Configuration Update
1. Update config.yaml:
   - Remove unused parameters
   - Simplify configuration structure
   - Reduce default tickers list
   - Update model parameters

### Phase 2: Feature Engineering
1. Modify features.py:
   - Remove enhanced features
   - Keep only core technical indicators
   - Simplify feature generation pipeline
   - Remove market data dependency

### Phase 3: Training Pipeline
1. Update train.py:
   - Remove classification mode
   - Simplify training process
   - Remove complex error handling
   - Streamline data preprocessing

2. Clean up predictor.py:
   - Remove classification logic
   - Simplify prediction pipeline
   - Remove complex metrics

### Phase 4: Testing & Documentation
1. Test simplified pipeline
2. Update documentation
3. Create new example notebooks
4. Update README

## Expected Benefits
1. Faster Training:
   - Reduced feature computation time
   - Simpler data preprocessing
   - No market data dependencies

2. Easier Maintenance:
   - Cleaner codebase
   - Fewer dependencies
   - Simpler configuration

3. Better Iteration Speed:
   - Faster training cycles
   - Easier to modify and test
   - Clearer results interpretation

## Success Metrics
1. Training time reduction
2. Code complexity reduction:
   - Fewer lines of code
   - Reduced cyclomatic complexity
   - Fewer dependencies
3. Maintained or improved prediction accuracy

## Timeline
1. Phase 1: 1 day
2. Phase 2: 2 days
3. Phase 3: 2 days
4. Phase 4: 1 day

Total: 6 days

## Risks and Mitigations
1. Risk: Performance degradation
   Mitigation: Benchmark against current version, adjust feature set if needed

2. Risk: Loss of important signals
   Mitigation: Validate removed features' importance, keep if proven valuable

3. Risk: Breaking changes
   Mitigation: Create backup branch, thorough testing before merge 