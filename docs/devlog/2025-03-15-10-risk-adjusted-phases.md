# Risk-Adjusted Model Enhancement: Phased Implementation Plan (March 21, 2024)

## Overview

Today I developed a phased implementation plan for addressing the critical issue with our model's handling of high-beta "meme stocks." The current model consistently assigns "Strong Buy" ratings to volatile stocks like PLTR, IONQ, and AI, which creates significant downside risk for users following our recommendations.

Rather than implementing all proposed changes at once, I've broken down the risk-adjusted model enhancement into four discrete, testable phases. Each phase is designed to deliver value independently while building toward a comprehensive solution.

## Phase 1: Beta and Volatility Features

The first phase focuses on adding explicit risk metrics while maintaining the current model architecture:

1. **Beta Calculation**: Add rolling beta (60-day, 120-day) against S&P 500
2. **Volatility Metrics**: Add historical volatility, downside deviation, and volatility ratio
3. **Return Distribution**: Add skewness, kurtosis, and drawdown-to-volatility ratio

**Why This Approach**: The core issue is that our model lacks features that explicitly measure a stock's sensitivity to market movements. By adding these features while keeping the same model architecture, we directly address the root cause with minimal implementation complexity.

**Success Metrics**:
- No more than 1 high-beta stock (beta > 1.5) in top 5 recommendations
- 15% improvement in portfolio Sharpe ratio
- 20% reduction in maximum drawdown during market corrections
- At least 2 new risk metrics in top 10 important features

## Phase 2: Risk-Adjusted Target Variable

If Phase 1 doesn't sufficiently address the issue, Phase 2 will modify the target variable to predict Sharpe ratio instead of raw returns:

1. Calculate historical Sharpe ratio for each stock
2. Modify target variable to predict future Sharpe ratio
3. Adjust evaluation metrics to focus on risk-adjusted performance

**Why This Approach**: By predicting Sharpe ratio instead of raw returns, we explicitly incorporate risk into the target variable itself, fundamentally changing what the model is optimizing for.

## Phase 3: Market Regime Awareness

Phase 3 adds features that identify the current market regime and how stocks perform in different regimes:

1. Add market regime classification features
2. Add conditional performance metrics (performance in bull vs. bear markets)

**Why This Approach**: High-beta stocks tend to outperform in bull markets and underperform in bear markets. By adding market regime awareness, we help the model understand this context.

## Phase 4: Two-Stage Modeling

The final phase implements a two-stage modeling approach with separate models for return prediction and risk prediction:

1. Develop separate return prediction model
2. Develop separate risk prediction model
3. Combine predictions to create a risk-adjusted score

**Why This Approach**: This more significant architectural change allows specialized models for return and risk, potentially improving both predictions.

## Portfolio-Based Evaluation

A key component of our evaluation framework will be portfolio-based evaluation, which assesses how a portfolio constructed from the model's recommendations would perform in practice:

1. Create a simulated portfolio of top 10 recommended stocks
2. Track performance during recent market corrections
3. Calculate portfolio Sharpe ratio, maximum drawdown, and volatility
4. Compare to benchmark indices

This approach aligns with how users would actually apply the model's recommendations and provides a more holistic view of performance.

## Go/No-Go Decision Criteria

After each phase, we'll evaluate results against success metrics to decide whether to proceed:
- If 3+ success metrics are met: Proceed to next phase
- If 1-2 success metrics are met: Refine current phase before proceeding
- If 0 success metrics are met: Reconsider approach before proceeding

## Next Steps

1. Implement Phase 1 (Beta and Volatility Features)
   - Add beta calculation against S&P 500
   - Add volatility and downside risk metrics
   - Add return distribution characteristics
   - Develop portfolio-based evaluation framework

2. Evaluate results against success metrics
   - Track changes in ratings for high-beta stocks
   - Measure portfolio performance metrics
   - Analyze feature importance of new risk metrics

3. Decide whether to proceed to Phase 2 based on results

A detailed implementation plan has been created in `docs/devplan/risk_adjusted_model_phases.md`. 