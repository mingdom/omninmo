# Portfolio Calculations

This document provides a comprehensive overview of how portfolio metrics are calculated in the Folio application.

## Core Principles

1. **Focus on Exposure**: We focus on market exposure rather than value, as prices in CSV files change frequently.
2. **Beta Adjustment**: We adjust exposures by beta to account for different market sensitivities.
3. **Cash Separation**: Cash and cash-like instruments are tracked separately from market exposure.

## Key Metrics

### Exposure Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Long Exposure | Long Stocks + Long Options Delta | Total positive market exposure |
| Short Exposure | Short Stocks + Short Options Delta | Total negative market exposure (stored as positive value) |
| Net Market Exposure | Long Exposure - Short Exposure | Directional market exposure |
| Options Exposure | Long Options Delta + Short Options Delta | Total options exposure (both long and short) |
| Net Options Exposure | Long Options Delta - Short Options Delta | Directional options exposure |
| Portfolio Estimated Value | Net Market Exposure + Cash | Estimated total value of the portfolio |

### Percentage Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Short Percentage | Short Exposure / (Long Exposure + Short Exposure) * 100 | Percentage of market exposure that is short |
| Cash Percentage | Cash Value / Portfolio Estimated Value * 100 | Percentage of portfolio in cash |

### Beta Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Portfolio Beta | Net Beta-Adjusted Exposure / Net Market Exposure | Weighted average beta of all positions |

## Calculation Details

### Stock Positions

- **Long Stock Exposure**: Sum of market exposure for stocks with positive quantity
- **Short Stock Exposure**: Sum of absolute market exposure for stocks with negative quantity

### Option Positions

- **Long Option Exposure**: Sum of delta exposure for:
  - Long call options (positive delta)
  - Short put options (positive delta)
- **Short Option Exposure**: Sum of absolute delta exposure for:
  - Short call options (negative delta)
  - Long put options (negative delta)

#### Options Exposure Calculation

Options exposure is calculated based on the option's delta and the underlying security's price:

1. **Delta Exposure** = Option Delta × Contract Size × Underlying Price × Number of Contracts
   - For call options: Positive delta (0 to 1)
   - For put options: Negative delta (-1 to 0)

2. **Beta-Adjusted Options Exposure** = Delta Exposure × Underlying Beta
   - Adjusts the exposure based on the underlying security's market sensitivity

3. **Options are categorized as**:
   - **Long Exposure**: Options with positive delta exposure (long calls, short puts)
   - **Short Exposure**: Options with negative delta exposure (short calls, long puts)

4. **Total Options Exposure** = Sum of absolute values of all options delta exposures

5. **Net Options Exposure** = Long Options Exposure - Short Options Exposure

### Cash-like Positions

Cash-like positions are identified by:
- Money market funds
- Treasury bills
- Positions with beta close to zero

## Implementation Notes

1. Short exposure is stored as a positive value throughout the codebase.
2. When calculating percentages, we use Portfolio Estimated Value as the denominator.
3. Beta-adjusted exposure = Market Exposure * Beta

## Data Model Structure

### Exposure Breakdowns

The data model uses `ExposureBreakdown` objects to store detailed information about different types of exposure:

```python
@dataclass
class ExposureBreakdown:
    stock_exposure: float        # Stock-only exposure
    stock_beta_adjusted: float   # Beta-adjusted stock exposure
    option_delta_exposure: float # Options-only exposure
    option_beta_adjusted: float  # Beta-adjusted options exposure
    total_exposure: float        # Combined exposure (stock + options)
    total_beta_adjusted: float   # Combined beta-adjusted exposure
    components: dict[str, float] # Detailed breakdown of components
```

### Portfolio Summary

The `PortfolioSummary` class contains three separate exposure breakdowns:

```python
@dataclass
class PortfolioSummary:
    # Exposure breakdowns
    long_exposure: ExposureBreakdown   # Detailed breakdown of long exposures
    short_exposure: ExposureBreakdown  # Detailed breakdown of short exposures
    options_exposure: ExposureBreakdown # Detailed breakdown of option exposures
```

This structure makes it easy to determine the portion of long/short exposure that comes from options versus stocks:

- `long_exposure.stock_exposure`: Long stock-only exposure
- `long_exposure.option_delta_exposure`: Long options-only exposure
- `short_exposure.stock_exposure`: Short stock-only exposure
- `short_exposure.option_delta_exposure`: Short options-only exposure
- `options_exposure.total_exposure`: Total options exposure (both long and short)

The components dictionary in each breakdown provides even more detailed information about specific exposure types.
