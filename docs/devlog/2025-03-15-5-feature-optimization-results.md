# Feature Optimization Results (March 21, 2024)

## Overview
Trained a new model with the optimized feature set and compared performance metrics with the previous model. The feature optimization successfully reduced model complexity while maintaining strong predictive performance.

## Training Results

### Performance Metrics
| Metric | Previous Model | Optimized Model | Change |
|--------|---------------|-----------------|--------|
| Cross-validation R² | 0.6809 ± 0.0131 | 0.6503 ± 0.0216 | -4.5% |
| Final model R² | 0.7610 | 0.7378 | -3.0% |
| Feature stability score | 0.7882 | 0.7840 | -0.5% |

### Top Features Comparison
| Previous Model | Importance | Optimized Model | Importance |
|----------------|------------|-----------------|------------|
| max_drawdown_90d | 10.28% | max_drawdown_90d | 10.47% |
| ema_21 | 7.51% | sma_50 | 7.00% |
| sma_50 | 7.34% | bb_std | 6.51% |
| bb_std | 6.89% | sma_200 | 6.03% |
| sma_200 | 5.38% | macd | 5.83% |

## Analysis

### Performance Impact
- The optimized model shows a slight decrease in R² (-4.5% in cross-validation, -3.0% in final model)
- Feature stability remained nearly identical (-0.5%)
- The performance trade-off is acceptable given the 18.4% reduction in feature count

### Feature Importance Shifts
- max_drawdown_90d remains the most important feature and increased in importance
- Technical indicators (sma_50, bb_std) gained relative importance
- Feature importance distribution became more balanced
- Top 10 features now account for 60.67% of total importance

### Benefits Achieved
1. **Reduced Complexity**: 31 features vs. 38 features (18.4% reduction)
2. **Improved Interpretability**: Removed redundant features
3. **Maintained Stability**: Feature stability score nearly unchanged
4. **Computational Efficiency**: Fewer features to calculate and process
5. **More Balanced Feature Importance**: Better distribution across feature categories

## Conclusions

The feature optimization successfully achieved its primary goals:
1. Reduced feature count to the target range (30-35)
2. Maintained strong predictive performance (R² > 0.65)
3. Preserved feature stability
4. Removed redundant features with minimal impact on model quality

The slight decrease in R² is an acceptable trade-off for the benefits gained in model simplicity, interpretability, and efficiency. The optimized model provides a stronger foundation for adding the planned Phase 2B features.

## Next Steps
1. Implement Phase 2B trend strength indicators (ADX, linear regression slope, MA acceleration)
2. Evaluate if these new features can recover or exceed the previous R² performance
3. Continue monitoring feature stability as new features are added
4. Consider additional feature selection techniques (SHAP, permutation importance) for future optimization

## Technical Details
- Previous model: 38 features, R² = 0.7610, stability = 0.7882
- Optimized model: 31 features, R² = 0.7378, stability = 0.7840
- Model file: models/st_predictor_regression_20250315_100539.pkl
- MLflow run ID: cb4259421fa94246a365e829f4749392 