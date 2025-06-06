# Folio Data Model Documentation

**Date:** 2025-04-05
**Status:** Current

## Fundamental Principle

**SEPARATE VALUE FROM EXPOSURE.** This is the most critical insight that drives our approach. While portfolio values are constantly changing, we can calculate them accurately at a point in time. However, for risk assessment, we must focus on market exposure rather than market value.

## Data Model Overview

The Folio data model is designed around exposure-based metrics rather than value-based metrics. This approach provides a more accurate and useful view of portfolio risk and helps users make better investment decisions.

### Key Concepts

1. **Market Value**: The actual worth of a position, calculated as:
   - For stocks: Quantity × Current Price
   - For options: Quantity × Current Price

2. **Market Exposure**: The amount of money exposed to market movements, calculated as:
   - For stocks: Quantity × Current Price
   - For options: Delta × Notional Value (100 × Underlying Price × |Quantity|)

3. **Beta-Adjusted Exposure**: Market exposure adjusted for the security's volatility relative to the market (SPY), calculated as:
   - Market Exposure × Beta

4. **Net Market Exposure**: The combined directional exposure of the portfolio, calculated as:
   - Long Exposure - Short Exposure

5. **Gross Market Exposure**: The total market exposure regardless of direction, calculated as:
   - Long Exposure + Short Exposure

6. **Short Percentage**: The percentage of gross market exposure that is short, calculated as:
   - (Short Exposure / Gross Market Exposure) × 100

7. **Cash**: Cash and cash-like instruments have minimal market correlation (beta ≈ 0) and are tracked separately from market exposure.

## Data Model Classes

### Position (Base Class)

The base class for all position types.

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | `str` | The security identifier |
| `quantity` | `int` | Number of shares or contracts |
| `market_exposure` | `float` | The market exposure of the position |
| `market_value` | `float` | The actual market value of the position (quantity * price) |
| `beta` | `float` | The security's volatility relative to the market |
| `beta_adjusted_exposure` | `float` | Market exposure adjusted for beta |

### StockPosition

Represents a stock position in the portfolio.

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | `str` | The stock symbol |
| `quantity` | `int` | Number of shares (negative for short positions) |
| `market_exposure` | `float` | Quantity × Current Price |
| `market_value` | `float` | Quantity × Current Price (same as market_exposure for stocks) |
| `beta` | `float` | The stock's volatility relative to the market |
| `beta_adjusted_exposure` | `float` | Market exposure adjusted for beta |

### OptionPosition

Represents an option position in the portfolio.

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | `str` | The underlying security symbol |
| `position_type` | `str` | Always "option" |
| `quantity` | `int` | Number of contracts (negative for short positions) |
| `market_exposure` | `float` | Delta × Notional Value |
| `market_value` | `float` | Quantity × Current Price (actual worth of the position) |
| `beta` | `float` | The underlying security's beta |
| `beta_adjusted_exposure` | `float` | Market exposure adjusted for beta |
| `strike` | `float` | The option strike price |
| `expiry` | `str` | The option expiration date |
| `option_type` | `str` | "CALL" or "PUT" |
| `delta` | `float` | The option's delta (rate of change relative to underlying) |
| `delta_exposure` | `float` | Delta × Notional Value |
| `notional_value` | `float` | 100 × Underlying Price × |Quantity| |
| `underlying_beta` | `float` | The underlying security's beta |

#### Deprecated Fields

| Field | Replacement | Description |
|-------|-------------|-------------|
| `clean_value` | Removed | Not needed for exposure calculations |
| `weight` | Calculated on-the-fly | Use `calculate_position_weight(position_market_exposure, portfolio_net_exposure)` |
| `position_beta` | `beta` | Use `beta` instead |

### PortfolioGroup

Groups a stock and its related options.

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | `str` | The underlying security symbol |
| `stock_position` | `StockPosition` | The stock component of this group |
| `option_positions` | `list[OptionPosition]` | List of option positions related to this underlying |
| `net_exposure` | `float` | Combined market exposure of stock and options |
| `beta` | `float` | The underlying security's beta |
| `beta_adjusted_exposure` | `float` | Net exposure adjusted for beta |
| `total_delta_exposure` | `float` | Sum of all option delta exposures |
| `options_delta_exposure` | `float` | Same as total_delta_exposure |
| `call_count` | `int` | Number of call option positions |
| `put_count` | `int` | Number of put option positions |

#### Deprecated Fields

| Field | Replacement | Description |
|-------|-------------|-------------|
| `total_value` | `net_exposure` | Use `net_exposure` instead |
| `net_option_value` | Removed | Based on unreliable market values |

### ExposureBreakdown

Detailed breakdown of exposure by type.

| Field | Type | Description |
|-------|------|-------------|
| `stock_exposure` | `float` | Market exposure from stock positions |
| `stock_beta_adjusted` | `float` | Stock exposure adjusted for beta |
| `option_delta_exposure` | `float` | Market exposure from option positions |
| `option_beta_adjusted` | `float` | Option exposure adjusted for beta |
| `total_exposure` | `float` | Combined market exposure |
| `total_beta_adjusted` | `float` | Combined beta-adjusted exposure |
| `description` | `str` | Human-readable explanation |
| `formula` | `str` | Calculation formula used |
| `components` | `dict[str, float]` | Detailed breakdown of components |

#### Deprecated Fields

| Field | Replacement | Description |
|-------|-------------|-------------|
| `stock_value` | `stock_exposure` | Use `stock_exposure` instead |
| `option_delta_value` | `option_delta_exposure` | Use `option_delta_exposure` instead |
| `total_value` | `total_exposure` | Use `total_exposure` instead |

### PortfolioSummary

Summary of portfolio metrics with detailed breakdowns.

| Field | Type | Description |
|-------|------|-------------|
| `net_market_exposure` | `float` | Long - Short (excluding cash) |
| `portfolio_beta` | `float` | Weighted average beta of all positions |
| `long_exposure` | `ExposureBreakdown` | Detailed breakdown of long exposures |
| `short_exposure` | `ExposureBreakdown` | Detailed breakdown of short exposures |
| `options_exposure` | `ExposureBreakdown` | Detailed breakdown of option exposures |
| `short_percentage` | `float` | Short / (Long + Short) |
| `cash_like_positions` | `list[StockPosition]` | List of cash and cash-equivalent positions |
| `cash_like_value` | `float` | Total value of cash positions |
| `cash_like_count` | `int` | Number of cash positions |
| `cash_percentage` | `float` | Cash / (Cash + Gross Market Exposure) |
| `stock_value` | `float` | Total value of stock positions |
| `option_value` | `float` | Total value of option positions |
| `portfolio_estimate_value` | `float` | Stock Value + Option Value + Cash Value |

#### Deprecated Fields

| Field | Replacement | Description |
|-------|-------------|-------------|
| `total_exposure` | `net_market_exposure` | Use `net_market_exposure` instead |
| `net_exposure` | `net_market_exposure` | Use `net_market_exposure` instead |
| `exposure_reduction_percentage` | Removed | Not useful |

## Utility Functions

### `calculate_position_weight`

Calculates a position's weight in the portfolio.

```python
def calculate_position_weight(position_market_exposure: float, portfolio_net_exposure: float) -> float:
    """Calculate a position's weight in the portfolio."""
    if not portfolio_net_exposure:
        return 0.0
    return position_market_exposure / portfolio_net_exposure
```

## Best Practices

1. **Separate Value from Exposure**: Understand the difference between market value (the actual worth of a position) and market exposure (the amount of money exposed to market movements).

2. **Use Appropriate Metrics**: Use market value for portfolio valuation and market exposure for risk assessment.

3. **Calculate Weight On-the-Fly**: Weight is a derived property that depends on both the position's market value and the portfolio's total exposure. Calculate it on the fly using the `calculate_position_weight` function.

4. **Handle Cash Separately**: Cash has zero market exposure and should be tracked separately from market exposure.

5. **Use Consistent Naming**: Use consistent field names across the codebase to avoid confusion.

6. **Document Deprecated Fields**: Clearly document deprecated fields and their replacements to help with the transition.

## Future Considerations

1. **Remove Deprecated Fields**: Eventually, we should remove the deprecated fields and their backward compatibility layers to simplify the codebase.

2. **Add More Risk Metrics**: Consider adding additional risk metrics like Value at Risk (VaR) and Expected Shortfall (ES) to provide a more comprehensive view of portfolio risk.

3. **Improve Cash Handling**: Enhance the handling of cash and cash-like instruments to provide a more accurate view of portfolio liquidity.

4. **Add Sector Analysis**: Add support for sector analysis to help users understand their sector exposures and diversification.

## Conclusion

By separating market value from market exposure, we can create a more accurate and useful portfolio analysis tool. The revised data model provides a clearer picture of both portfolio value and risk, helping users make better investment decisions.

Remember: **SEPARATE VALUE FROM EXPOSURE.** This fundamental principle allows us to accurately track both the worth of our positions and their risk exposure.
