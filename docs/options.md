# Options Concepts and Calculations

This document explains key concepts related to options in our portfolio management system, how we calculate various metrics, and current challenges we're facing.

## Key Concepts

### Options Basics

An option is a financial derivative that gives the buyer the right, but not the obligation, to buy (call option) or sell (put option) an underlying asset at a specified price (strike price) on or before a specified date (expiration date).

- **Call Option**: Right to buy the underlying asset
- **Put Option**: Right to sell the underlying asset
- **Long Position**: Buying an option (positive quantity)
- **Short Position**: Selling an option (negative quantity)

### Market Value vs. Market Exposure

One of the most important distinctions in options trading is between the market value of an option and the market exposure it represents:

- **Market Value**: The actual dollar amount invested in the option (price × quantity × 100)
- **Market Exposure**: The directional risk the option represents in the market

For stocks, these values are typically the same (price × quantity). For options, the market exposure can be much larger than the market value due to leverage.

### Notional Value

Notional value represents the total value of the underlying asset controlled by the option contracts.

**Formula**: `notional_value = 100 × |quantity| × underlying_price`

Where:
- `100` is the multiplier (each option contract controls 100 shares)
- `|quantity|` is the absolute number of contracts
- `underlying_price` is the price of the underlying asset

Notional value is always positive, regardless of whether the position is long or short.

### Delta

Delta measures the rate of change in an option's price relative to changes in the underlying asset's price.

- Delta ranges from -1.0 to 1.0
- Call options have positive delta (0 to 1)
- Put options have negative delta (-1 to 0)
- Delta approaches 1 (calls) or -1 (puts) as the option becomes deeper in-the-money

### Delta Exposure

Delta exposure represents the equivalent stock position that would have the same price movement as the option position.

**Formula**: `delta_exposure = delta × notional_value × sign(quantity)`

Where:
- `delta` is the option's delta value
- `notional_value` is the notional value of the position
- `sign(quantity)` is 1 for long positions and -1 for short positions

Delta exposure can be positive or negative, representing long or short market exposure.

### Beta

Beta measures the volatility of a security relative to the market (typically the S&P 500).

- Beta of 1.0: Moves in line with the market
- Beta > 1.0: More volatile than the market
- Beta < 1.0: Less volatile than the market
- Beta of 0: No correlation with the market (e.g., cash)

### Beta-Adjusted Exposure

Beta-adjusted exposure adjusts the market exposure by the beta of the underlying asset to represent the true market risk.

**For Stocks**:
```
beta_adjusted_exposure = market_exposure × beta
```

**For Options**:
```
beta_adjusted_exposure = delta_exposure × beta
```

Beta-adjusted exposure allows for comparing the market risk of different positions on an equal footing.

## Current Implementation

### Notional Value Calculation

We calculate notional value using a centralized function in `options.py`:

```python
def calculate_notional_value(quantity: float, underlying_price: float) -> float:
    """Calculate the notional value of an option position."""
    return 100 * abs(quantity) * underlying_price
```

### Delta Exposure Calculation

Delta exposure is calculated in the `calculate_option_exposure` function:

```python
# Calculate notional value using the canonical implementation
notional_value = calculate_notional_value(quantity, underlying_price)

# Calculate delta exposure
# For long positions, delta_exposure = delta * notional_value
# For short positions, delta_exposure = -delta * notional_value
delta_exposure = delta * notional_value * (1 if quantity >= 0 else -1)
```

### Beta-Adjusted Exposure Calculation

For options, beta-adjusted exposure is calculated as:

```python
# Calculate beta-adjusted exposure
beta_adjusted_exposure = delta_exposure * beta
```

For stocks, beta-adjusted exposure is calculated as:

```python
beta_adjusted_exposure = market_exposure * beta
```

## Portfolio Aggregation

### Portfolio Groups

We organize positions into portfolio groups, where each group consists of:
- A stock position (optional)
- Multiple option positions (optional)

Each group's beta-adjusted exposure is the sum of:
- The stock position's beta-adjusted exposure
- The beta-adjusted exposures of all option positions

### Portfolio Summary

The portfolio summary includes:
- Long exposure (stocks + options with positive delta exposure)
- Short exposure (stocks + options with negative delta exposure)
- Options exposure (net delta exposure from all options)
- Cash-like positions (money market funds, T-bills, etc.)
- Pending activity (unsettled transactions)

## Current Challenges

### 1. Inconsistent Calculation Paths

We currently have multiple paths for calculating beta-adjusted exposure:
- Through the summary cards using `format_summary_card_values`
- By summing individual group exposures in the UI

These calculations sometimes produce different results, leading to inconsistencies in the displayed values.

### 2. Handling of Pending Activity

Pending activity represents unsettled transactions that don't yet have a defined beta. We need to decide how to handle this in beta-adjusted exposure calculations.

### 3. Cash-Like Positions

Cash and cash equivalents have a beta of 0, so they don't contribute to beta-adjusted exposure. However, they are included in portfolio value calculations, which can lead to confusion.

### 4. Option Greeks Calculation

We calculate option Greeks (delta, gamma, theta, vega) using the Black-Scholes model, which requires:
- Underlying price
- Strike price
- Time to expiration
- Risk-free rate
- Implied volatility

Getting accurate values for the risk-free rate and implied volatility can be challenging.

## Best Practices

1. **Centralized Calculations**: Use centralized functions for all exposure calculations to ensure consistency
2. **Clear Separation**: Maintain a clear distinction between market value and market exposure
3. **Consistent Sign Convention**: Use negative values for short positions throughout the codebase
4. **Proper Aggregation**: When aggregating exposures, ensure that the calculation methodology is consistent
5. **Documentation**: Clearly document the calculation methodology for all exposure metrics

## Future Improvements

1. **Unified Calculation Path**: Implement a single source of truth for all exposure calculations
2. **Enhanced Visualization**: Provide clearer visualization of the difference between market value and market exposure
3. **Improved Greeks Calculation**: Enhance the accuracy of option Greeks calculations with better volatility models
4. **Stress Testing**: Implement stress testing to show how portfolio exposures would change under different market conditions
