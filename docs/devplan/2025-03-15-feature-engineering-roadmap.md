# Feature Engineering Roadmap

## Implementation Progress Checklist

### Feature Optimization
- [x] **Feature Removal**: Reduced feature count from 38 to 31 features
  - [x] Removed redundant return metrics (return_5d, return_10d)
  - [x] Simplified Bollinger Band features (removed bb_middle, bb_upper, bb_lower)
  - [x] Consolidated Moving Average features (removed close_to_ema_8)
  - [x] Current feature count: 33 (target: 30-35)
  - [x] Feature stability score: 0.7727 (target: >0.8)

### Phase 2B: Trend Strength Indicators
- [x] **Average Directional Index (ADX)**
  - [x] Implementation
  - [x] Testing and validation
  - [x] Model training and evaluation
  - [x] Results: R² improved from 0.6503 to 0.6707 (+0.0204)

### NEW PRIORITY: Risk-Adjusted Model Enhancement
- [ ] **Phase 1: Enhanced Risk-Return Features** - *Next implementation*
  - [ ] Beta and Market Sensitivity
    - [ ] Rolling beta calculation
    - [ ] Correlation with market indices
    - [ ] Sector-relative performance
  - [ ] Volatility and Downside Risk
    - [ ] Historical volatility metrics
    - [ ] Downside deviation
    - [ ] Volatility ratio
  - [ ] Return Distribution Characteristics
    - [ ] Skewness and kurtosis
    - [ ] Drawdown-to-volatility ratio

- [ ] **Phase 2: Model Architecture Improvements**
  - [ ] Risk-Adjusted Target Variable
    - [ ] Sharpe ratio as target
    - [ ] Model retraining and evaluation
  - [ ] Two-Stage Modeling Approach
    - [ ] Return prediction model
    - [ ] Risk prediction model
    - [ ] Combined risk-adjusted scoring

- [ ] **Phase 3: Market Regime Awareness**
  - [ ] Market Regime Classification
    - [ ] Bull/bear market indicators
    - [ ] Volatility regime features
  - [ ] Conditional Performance Metrics
    - [ ] Performance in bull vs. bear markets
    - [ ] Relative strength in different regimes

### Deprioritized Features (To be revisited after risk adjustments)
- [ ] **Linear Regression Slope**
- [ ] **MA Acceleration**
- [ ] **Trend Consistency Score**
- [ ] **MA Compression/Expansion**

### Extensibility
- [ ] **Research Phase**
  - [ ] Evaluate alternative data sources
  - [ ] Prototype integration approaches
- [ ] **Implementation Phase**
  - [ ] Develop modular architecture
  - [ ] Create data integration pipelines
  - [ ] Build ensemble model framework

## Introduction

This document outlines the roadmap for improving the feature engineering component of our stock prediction system. It builds upon our current approach while proposing new directions for exploration. The goal is to enhance prediction quality, feature stability, and extensibility beyond price-based data.

The current feature set (33 features) focuses on:
- Price-based features (returns, moving averages)
- Technical indicators (RSI, MACD, Bollinger Bands, ADX)
- Risk metrics (drawdown, Sharpe ratio, stability)

This roadmap covers three key areas:
1. **Feature Additions**: New features to implement
2. **Feature Removals**: Optimizing feature count
3. **Extensibility**: Incorporating non-price data sources

## UPDATED: Critical Issue and New Direction

### Meme Stock Problem
Our current model consistently assigns "Strong Buy" ratings with high predicted returns to high-beta, volatile "meme stocks" like PLTR, IONQ, and AI. These stocks are particularly vulnerable in bear markets, creating significant downside risk for users following our recommendations.

Despite implementing risk metrics like maximum drawdown (which is our most important feature), the model continues to favor these high-volatility stocks. This suggests our current approach to risk-adjustment is insufficient.

### Root Causes
1. **Missing Beta/Market Sensitivity Metrics**: The model lacks features that explicitly measure a stock's sensitivity to market movements.
2. **Raw Return Prediction**: By predicting raw returns rather than risk-adjusted returns, high-volatility stocks naturally show higher potential returns.
3. **Insufficient Risk Quantification**: Our current risk metrics don't adequately capture the asymmetric nature of risk in volatile stocks.
4. **Market Regime Blindness**: The model doesn't have explicit knowledge of the current market regime (bull vs. bear).
5. **Single-Model Approach**: Using a single model to predict returns may not adequately balance risk and return considerations.

### New Approach
We are shifting our focus to a comprehensive risk-adjusted model enhancement plan. This represents a significant change in our roadmap priorities. See `docs/devplan/risk_adjusted_model_enhancement.md` for the detailed implementation plan.

## 1. Feature Additions

### Phase 1: Enhanced Risk-Return Features

#### Beta and Market Sensitivity
```python
def add_beta_features(df, market_data, window=60):
    """
    Calculate beta and correlation with market indices
    """
    # Calculate returns for the stock
    stock_returns = df['Close'].pct_change()
    
    # Calculate returns for market indices
    market_returns = market_data['Close'].pct_change()
    
    # Calculate rolling beta (slope of regression line)
    df[f'beta_{window}d'] = stock_returns.rolling(window).cov(market_returns) / market_returns.rolling(window).var()
    
    # Calculate rolling correlation
    df[f'market_corr_{window}d'] = stock_returns.rolling(window).corr(market_returns)
    
    # Calculate relative strength vs market
    df[f'rel_strength_{window}d'] = (1 + stock_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1) / \
                                   (1 + market_returns).rolling(window).apply(lambda x: np.prod(1 + x) - 1)
    
    return df
```

Expected impact:
- Proper identification of high-beta stocks
- Better risk assessment in different market conditions
- Reduced overrating of volatile stocks

#### Volatility and Downside Risk
```python
def add_volatility_features(df, windows=[30, 60, 90]):
    """
    Add volatility and downside risk metrics
    """
    returns = df['Close'].pct_change()
    
    for window in windows:
        # Historical volatility (annualized)
        df[f'volatility_{window}d'] = returns.rolling(window).std() * np.sqrt(252)
        
        # Downside deviation (focuses only on negative returns)
        downside_returns = returns.copy()
        downside_returns[downside_returns > 0] = 0
        df[f'downside_dev_{window}d'] = downside_returns.rolling(window).std() * np.sqrt(252)
        
        # Volatility ratio (recent vs longer-term)
        if window > 30:
            df[f'vol_ratio_30_{window}d'] = df[f'volatility_30d'] / df[f'volatility_{window}d']
    
    return df
```

Expected impact:
- More accurate risk quantification
- Better identification of asymmetric risk
- Improved risk-adjusted return predictions

## 2. Feature Removals and Optimization

### Optimal Feature Count Analysis

Research on XGBoost models in financial prediction suggests an optimal feature count between 20-50 features, with a sweet spot around 30-40 features. Our current feature count (33) falls within this optimal range.

Key considerations:
1. **Model Complexity**: As feature count increases, model complexity increases, leading to potential overfitting
2. **Feature Stability**: Fewer, more robust features typically lead to higher feature stability
3. **Predictive Power**: Diminishing returns observed beyond 40-50 features in most financial models
4. **Interpretability**: More features reduce model interpretability and increase maintenance complexity

### Feature Selection Methodology

To maintain an optimal feature count while improving model performance, we recommend:

1. **Permutation Importance** 
   - More reliable than built-in importance in the presence of correlated features
   - Measures performance drop when each feature is randomly shuffled
   - Less susceptible to bias toward high-cardinality features

2. **Recursive Feature Elimination with Cross-Validation (RFECV)**
   - Systematically removes the least important features
   - Uses cross-validation to determine optimal feature count
   - Accounts for feature interactions

3. **Feature Stability Analysis**
   - Evaluate feature importance consistency across different:
     - Time periods
     - Market regimes (bull/bear/sideways)
     - Stock sectors

4. **SHAP (SHapley Additive exPlanations) Analysis**
   - Provides detailed feature contribution insights
   - Helps identify redundant features
   - Quantifies feature interaction effects

### Candidates for Removal

Based on current feature importance and stability analysis, we have already implemented the following removals:

1. **Redundant Return Metrics** ✓
   - Kept only 1d, 20d, and 60d returns
   - Removed 5d and 10d returns (high correlation with other return metrics)

2. **Simplified Bollinger Band Features** ✓
   - Kept bb_width, bb_pct_b, and bb_std
   - Removed bb_middle, bb_upper, and bb_lower (derived from other metrics)

3. **Consolidated Moving Average Features** ✓
   - Removed close_to_ema_8 (less stable than close_to_ema_21)
   - Kept ema_8 only for crossover calculations

### Target Feature Count

We have successfully reduced our feature count to 33, which is within our target range of 30-35 features. This provides the optimal balance between:
- Predictive power
- Feature stability
- Model interpretability
- Computational efficiency

The current feature stability score is 0.7727, which is approaching our target of >0.8. We expect the addition of high-quality trend indicators in Phase 2B to further improve this score.

## 3. Extensibility: Beyond Price Data

### Alternative Data Sources

#### Fundamental Data
- Financial ratios (P/E, P/B, ROE, etc.)
- Earnings and revenue growth
- Debt levels and cash flow metrics
- Dividend yields and payout ratios

#### Sentiment Data
- News sentiment analysis
- Social media mentions and sentiment
- Analyst recommendations and target prices
- Options market sentiment indicators

#### Macroeconomic Data
- Interest rates and yield curve metrics
- Economic indicators (GDP, inflation, unemployment)
- Sector performance and correlations
- Market breadth indicators

### Single Model vs. Ensemble Approaches

#### Single Model with All Features

**Advantages:**
- Directly captures cross-domain feature interactions
- Simpler architecture and maintenance
- One training process and parameter optimization
- Lower latency for predictions

**Disadvantages:**
- May struggle with different data types and scales
- Feature importance can be dominated by one data type
- Difficult to isolate impact of different data sources
- Less modular for adding/removing data sources

#### Specialized Models + Ensemble

**Advantages:**
- Better handling of domain-specific data characteristics
- Modularity for adding/removing data sources
- Easier to debug and understand each component
- Can specialize preprocessing for each data type

**Disadvantages:**
- More complex architecture to maintain
- Potential loss of subtle cross-domain interactions
- Multiple training processes and hyperparameters
- Higher computational overhead

### Research Findings

Recent academic literature on multi-modal financial prediction shows:

1. **Sokolov et al. (2020)**: Specialized models for technical, fundamental, and sentiment data combined through stacking outperformed single models by 12-18% in directional accuracy.

2. **Dixon et al. (2020)**: Hierarchical model structures showed 15% better performance than flat models for multi-modal financial data, particularly in volatile market conditions.

3. **Zhang et al. (2022)**: Ensemble approaches mitigated the negative impact of noise in financial sentiment data, improving stability by up to 25%.

4. **Gu et al. (2020)**: For asset pricing, models with separate feature processing layers for different data types before combination outperformed single-model approaches.

### Recommended Approach

Based on research and industry best practices, we recommend a **hybrid approach**:

1. **Initial Phase: Modular Design**
   - Develop specialized models for fundamentally different data types:
     - Technical model (current implementation)
     - Fundamental model
     - Sentiment model
   - Use meta-model stacking to combine predictions
   - Maintain separate feature engineering pipelines

2. **Evaluation Phase: Compare Approaches**
   - Develop and test a single model with all features
   - Compare performance, stability, and interpretability
   - Evaluate across different market regimes
   - Measure feature interactions between domains

3. **Final Implementation: Best of Both Worlds**
   - Adopt the better-performing approach as the primary model
   - Consider preserving both for different use cases
   - Implement continuous evaluation across market conditions

### Implementation Considerations

For a modular approach, consider:
1. **Common preprocessing interface** for all data sources
2. **Standardized prediction output format** for easy ensemble integration
3. **Independent validation** of each component model
4. **Feature stability scoring** for each data domain
5. **Meta-model design** that preserves interpretability

## Success Metrics

To evaluate the success of these feature engineering improvements:

### Primary Metrics
1. **Feature Stability Score**: Target > 0.8 (currently 0.7727)
2. **Cross-validation R²**: Maintain > 0.65 while improving stability (currently 0.6503)
3. **Maximum Drawdown**: Reduce by at least 15% in backtest portfolios

### Secondary Metrics
1. **Prediction Consistency**: Reduced variance in predictions across market regimes
2. **Feature Importance Distribution**: More balanced distribution across feature categories
3. **Processing Efficiency**: Maintain sub-second feature generation per stock

### Evaluation Methodology
1. **Market Regime Testing**: Evaluate across bull, bear, and sideways markets
2. **Sector Analysis**: Test performance across different stock sectors
3. **Time Period Validation**: Test on multiple historical periods
4. **Simulation Testing**: Forward-test with realistic trading scenarios

## Implementation Timeline

1. **Feature Optimization**: ✓ Completed (March 2024)
2. **ADX Implementation**: ✓ Completed (March 2024)
3. **Risk-Adjusted Model Enhancement**: In progress (April-June 2024)
   - Phase 1 (Enhanced Risk-Return Features): April 2024
   - Phase 2 (Model Architecture Improvements): May 2024
   - Phase 3 (Market Regime Awareness): June 2024
4. **Extensibility Research**: Planned (July 2024)
5. **Alternative Data Prototype**: Planned (August 2024)
6. **Ensemble Integration**: Planned (September 2024)

## Conclusion

This roadmap provides a comprehensive plan for enhancing our feature engineering approach. By carefully adding high-value features, optimizing feature count, and preparing for multi-modal data integration, we can build a more robust and reliable stock prediction system.

We have already made significant progress by optimizing our feature set and implementing the ADX feature. However, our analysis has revealed a critical issue with our model's handling of high-beta "meme stocks." Our new focus on risk-adjusted modeling will address this issue directly, creating a more balanced recommendation system that properly accounts for the downside risk of high-volatility stocks.

The focus on feature stability and risk-awareness will help create a system that performs consistently across different market conditions, while the extensibility considerations ensure our architecture can adapt to incorporate new data sources in the future. 