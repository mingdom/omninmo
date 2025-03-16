# Risk-Adjusted Model Enhancement Plan Restructuring

## Overview

Today I restructured the risk-adjusted model enhancement plan to address the meme stock issue with a more phased, independently testable approach. The original plan had a good foundation but needed clearer separation between phases to allow for incremental evaluation and decision-making.

## Key Changes

### Restructured Implementation Phases

The implementation plan has been reorganized into three distinct, independently testable phases:

1. **Phase 1: Risk-Adjusted Target Transformation**
   - Added beta and volatility features
   - Changed target variable from raw returns to Sharpe ratio
   - This phase directly addresses the core issue by fundamentally changing what the model optimizes for

2. **Phase 2: Market Regime Awareness**
   - Added market regime classification features
   - Implemented conditional performance metrics
   - Added conditional feature importance analysis
   - This phase makes the model aware of different market conditions

3. **Phase 3: Advanced Risk Modeling**
   - Added tail risk features (skewness, kurtosis, VaR, CVaR)
   - Explored ensemble approaches for different market conditions
   - This phase adds more sophisticated risk modeling capabilities

### Clarified Individual Stock Focus

The plan now clearly maintains focus on individual stock analysis throughout all phases. The Sharpe ratio target variable is applied at the individual stock level, calculated as:

```
Sharpe Ratio = (Expected Return - Risk-Free Rate) / Standard Deviation of Returns
```

This approach doesn't require portfolio context - it's simply a different metric to predict for each individual stock. The model will learn to identify stocks that are likely to deliver good risk-adjusted returns rather than just high raw returns.

### Added Success Metrics for Each Phase

Each phase now has specific success metrics to determine whether to proceed to the next phase:

- **Phase 1**: Reduction in high-beta stocks receiving "Strong Buy" ratings, improved risk-adjusted performance
- **Phase 2**: More consistent performance across different market regimes, better downside protection
- **Phase 3**: Further reduction in maximum drawdown, improved performance in extreme market conditions

## Implementation Timeline

The updated implementation timeline provides more realistic timeframes for each phase:

- **Phase 1**: 1-4 weeks
- **Phase 2**: 2-4 weeks
- **Phase 3**: 3-6 weeks

This allows for proper evaluation between phases and the option to adjust or pivot based on results.

## Next Steps

1. Begin implementing Phase 1 by adding beta and volatility features
2. Modify the target variable to predict Sharpe ratio instead of raw returns
3. Train and evaluate the model with the new target and features
4. Document results and decide whether to proceed to Phase 2

## Technical Notes

The most significant technical change is moving the Sharpe ratio target variable from Phase 2 to Phase 1, as this directly addresses the core issue with meme stocks. By optimizing for risk-adjusted returns rather than raw returns, the model should naturally assign lower ratings to high-volatility stocks unless they offer commensurately higher expected returns.

The full updated plan can be found in `docs/devplan/risk_adjusted_model_enhancement.md`. 