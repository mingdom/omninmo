# Risk-Adjusted Model Enhancement Plan (March 21, 2024)

## Problem Analysis

Today we conducted a critical analysis of our model's recommendations, focusing on a persistent issue: our model consistently assigns "Strong Buy" ratings with high predicted returns to high-beta, volatile "meme stocks" like PLTR, IONQ, and AI.

The latest prediction results show:

| Ticker | Price  | Predicted Return | Rating      |
|--------|--------|------------------|-------------|
| PLTR   | $83.65 | 107.62%          | Strong Buy  |
| IONQ   | $21.82 | 31.39%           | Strong Buy  |
| AI     | $21.62 | 22.80%           | Strong Buy  |

These stocks are particularly vulnerable in bear markets, creating significant downside risk for users following our recommendations. Despite implementing risk metrics like maximum drawdown (which is our most important feature at 0.1187 importance), the model continues to favor these high-volatility stocks.

## Root Cause Analysis

After careful examination, we've identified several key issues:

1. **Missing Beta/Market Sensitivity Metrics**: Our model lacks features that explicitly measure a stock's sensitivity to market movements. Without beta metrics, the model can't properly account for how these stocks might perform in different market conditions.

2. **Raw Return Prediction**: By predicting raw returns rather than risk-adjusted returns, high-volatility stocks naturally show higher potential returns without proper risk consideration.

3. **Insufficient Risk Quantification**: Our current risk metrics don't adequately capture the asymmetric nature of risk in volatile stocks - they can drop much faster than they rise.

4. **Market Regime Blindness**: The model doesn't have explicit knowledge of the current market regime (bull vs. bear) or how stocks perform in different regimes.

5. **Single-Model Approach**: Using a single model to predict returns may not adequately balance risk and return considerations.

## New Approach

We've developed a comprehensive three-phase approach to address these issues:

### Phase 1: Enhanced Risk-Return Features
- Add beta calculation against major indices
- Implement volatility and downside risk metrics
- Add return distribution characteristics (skewness, kurtosis)

### Phase 2: Model Architecture Improvements
- Modify target variable to predict risk-adjusted returns (Sharpe ratio)
- Implement two-stage modeling (separate return and risk models)
- Develop custom loss functions that penalize errors in high-volatility stocks

### Phase 3: Market Regime Awareness
- Add market regime classification features
- Implement conditional performance metrics
- Develop stress testing framework

## Roadmap Impact

This analysis requires a significant shift in our feature engineering roadmap:

1. **Deprioritize**: Linear Regression Slope and MA Acceleration features
2. **Prioritize**: Beta, volatility, and risk-adjusted return features
3. **Add**: Two-stage modeling approach and risk-adjusted target variables
4. **Accelerate**: Market regime detection features

## Next Steps

Our immediate next steps (1-2 weeks):

1. **Implement Beta and Volatility Features**
   - Add rolling beta calculation
   - Add historical volatility metrics
   - Add downside deviation features

2. **Modify Evaluation Framework**
   - Implement portfolio-based evaluation
   - Add risk-adjusted performance metrics
   - Create separate evaluation for different volatility quintiles

A detailed implementation plan has been created in `docs/devplan/risk_adjusted_model_enhancement.md`.

## Technical Details

- **Current Issue**: High-beta "meme stocks" receiving inappropriately high ratings
- **Key Missing Features**: Beta, volatility metrics, market regime awareness
- **Proposed Solution**: Three-phase approach focusing on risk-adjusted modeling
- **Expected Outcome**: More balanced recommendations with appropriate risk consideration
- **Timeline**: Initial improvements in 1-2 weeks, comprehensive solution in 2-3 months 