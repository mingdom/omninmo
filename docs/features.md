# Stock Prediction System: Feature Engineering

## Introduction

Feature engineering is a critical component of the stock prediction system, transforming raw price data into meaningful signals that the model can use to predict future price movements. This document provides a comprehensive overview of the current features, their evolution, and planned improvements.

The system's feature engineering philosophy emphasizes:
- **Reliability**: Features that provide consistent signals across different market conditions
- **Risk awareness**: Balancing return potential with downside risk
- **Medium-term focus**: Optimized for 90-day prediction horizons
- **Feature stability**: Ensuring consistent feature importance across different datasets

## Current Feature Categories

### 1. Price-based Features

#### Returns
| Feature | Description | Usage |
|---------|-------------|-------|
| `return_1d` | 1-day percentage price change | Short-term momentum indicator |
| `return_5d` | 5-day percentage price change | Short-term trend indicator |
| `return_10d` | 10-day percentage price change | Short-term trend strength |
| `return_20d` | 20-day percentage price change | Medium-term momentum |
| `return_60d` | 60-day percentage price change | Medium-term trend strength |
| `log_return_1d` | Natural logarithm of 1-day return | Reduces return skewness for better statistical properties |

Returns are fundamental features that directly measure price changes over various time periods. They provide the model with a sense of momentum and recent performance. Log returns are particularly useful for normalizing the distribution of returns.

#### Moving Averages
| Feature | Description | Usage |
|---------|-------------|-------|
| `ema_8` | 8-day exponential moving average | Very short-term trend indicator |
| `ema_21` | 21-day exponential moving average | Short-term trend indicator |
| `sma_50` | 50-day simple moving average | Medium-term trend indicator |
| `sma_200` | 200-day simple moving average | Long-term trend indicator |
| `close_to_ema_8` | Percentage difference between price and 8-day EMA | Short-term overbought/oversold indicator |
| `close_to_ema_21` | Percentage difference between price and 21-day EMA | Short-term trend strength |
| `close_to_sma_50` | Percentage difference between price and 50-day SMA | Medium-term trend strength |
| `close_to_sma_200` | Percentage difference between price and 200-day SMA | Long-term trend strength |

Moving averages smooth out price data to identify trends. EMAs respond more quickly to recent price changes, while SMAs provide a more stable long-term view. The relative position of price to these averages helps identify potential reversal points and trend strength.

#### Crossovers
| Feature | Description | Usage |
|---------|-------------|-------|
| `ema_8_21_cross` | Binary indicator for 8-day EMA crossing above 21-day EMA | Short-term trend change signal |
| `sma_50_200_cross` | Binary indicator for 50-day SMA crossing above 200-day SMA | Major trend change signal (golden/death cross) |
| `macd_cross` | Binary indicator for MACD line crossing above signal line | Momentum shift signal |

Crossover features capture significant technical events that often precede trend changes. The 50/200 SMA crossover (golden cross/death cross) is particularly significant as a long-term trend indicator.

### 2. Technical Indicators

#### Relative Strength Index (RSI)
| Feature | Description | Usage |
|---------|-------------|-------|
| `rsi` | 14-period RSI | Overbought/oversold indicator (0-100 scale) |
| `rsi_ma_context` | RSI extremes with 50-day MA context | Identifies potential reversals with trend context |

RSI measures the speed and change of price movements, indicating overbought conditions (>70) or oversold conditions (<30). The RSI-MA context feature adds trend context to these signals, reducing false positives.

#### Moving Average Convergence Divergence (MACD)
| Feature | Description | Usage |
|---------|-------------|-------|
| `macd` | MACD line (difference between fast and slow EMAs) | Trend and momentum indicator |
| `macd_signal` | Signal line (EMA of MACD line) | Trigger line for MACD signals |
| `macd_hist` | MACD histogram (difference between MACD and signal) | Momentum acceleration/deceleration |

The MACD has been optimized for medium-term prediction with parameters (50,100,20) instead of the traditional (12,26,9). This configuration is more suitable for capturing medium-term trends while filtering out short-term noise.

#### Bollinger Bands
| Feature | Description | Usage |
|---------|-------------|-------|
| `bb_middle` | Middle band (20-day SMA) | Base trend line |
| `bb_std` | Standard deviation of price | Volatility measure |
| `bb_upper` | Upper band (middle + 2 std) | Resistance level |
| `bb_lower` | Lower band (middle - 2 std) | Support level |
| `bb_width` | Band width relative to middle band | Volatility indicator |
| `bb_pct_b` | Position within bands (0-1 scale) | Relative price position |

Bollinger Bands adapt to market volatility, widening during volatile periods and narrowing during stable periods. They help identify potential reversal points and measure relative volatility.

### 3. Risk Metrics

#### Drawdown Measures
| Feature | Description | Usage |
|---------|-------------|-------|
| `max_drawdown_90d` | Maximum percentage drop from peak over 90 days | Medium-term downside risk |
| `max_drawdown_180d` | Maximum percentage drop from peak over 180 days | Long-term downside risk |

Maximum drawdown is a key risk metric that measures the largest percentage drop from a peak to a subsequent trough. It helps identify stocks with significant downside risk, even if their overall returns are positive.

#### Risk-Adjusted Metrics
| Feature | Description | Usage |
|---------|-------------|-------|
| `sharpe_ratio_90d` | 90-day Sharpe ratio (excess return / volatility) | Risk-adjusted performance |
| `risk_adjusted_momentum` | Momentum divided by drawdown | Quality of momentum |

These metrics balance return potential with risk, helping the model identify stocks with steady, sustainable growth rather than volatile price movements.

#### Stability Measures
| Feature | Description | Usage |
|---------|-------------|-------|
| `price_stability` | Percentage of time price stays above major MAs | Trend stability indicator |

Price stability measures how consistently a stock maintains its trend, helping identify steady performers versus erratic movers.

## Feature Evolution

### Phase 1: Medium-Term Focus (March 2024)
The initial feature set was optimized for medium-term (90-day) predictions:

- Extended moving average periods (8/21 for EMA, 50/200 for SMA)
- Adjusted MACD parameters (50,100,20) for medium-term signals
- Added RSI-MA context feature
- Included volatility metrics (later removed)

**Results:**
- Cross-validation R²: 0.7150 ± 0.0145
- Final model R²: 0.7733
- Feature stability score: 0.7816

**Top features:**
1. volatility_60d: 10.24%
2. sma_200: 7.51%
3. sma_50: 7.01%
4. macd: 6.78%
5. bb_middle: 6.34%

### Phase 2A: Risk-Focused Features (March 2024)
This phase shifted from volatility-based to risk-aware prediction:

- Removed all volatility-based features
- Added risk management features (drawdown, Sharpe ratio)
- Added stability measures (price stability score)
- Introduced risk-adjusted momentum

**Results:**
- Cross-validation R²: 0.6809 ± 0.0131
- Final model R²: 0.7610
- Feature stability score: 0.7882 (improved)

**Top features:**
1. max_drawdown_90d: 10.28%
2. ema_21: 7.51%
3. sma_50: 7.34%
4. bb_std: 6.89%
5. sma_200: 5.38%

The shift to risk-focused features resulted in a slightly lower R² but improved feature stability, indicating more consistent decision-making across different market conditions.

## Future Development

For detailed plans on future feature engineering improvements, including feature additions, optimizations, and extensibility beyond price data, see the [Feature Engineering Roadmap](./devplan/feature-engineering-roadmap.md).

## Conclusion

Feature engineering is a critical component of the stock prediction system, transforming raw price data into meaningful signals. The evolution from volatility-focused to risk-aware prediction represents a significant improvement in the system's ability to identify quality investment opportunities.

The current feature set balances traditional technical indicators with risk metrics, providing a comprehensive view of both return potential and downside risk. Our ongoing focus is on feature stability and consistent performance across different market regimes.

The ultimate goal is to achieve high feature stability (>0.8) while maintaining strong predictive performance (R² >0.7) across different market regimes. 