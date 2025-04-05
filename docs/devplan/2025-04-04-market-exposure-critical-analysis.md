# Market Exposure Refactor: Critical Analysis and Implementation Plan

## Fundamental Principle

**WE CANNOT CALCULATE VALUE ACCURATELY.** This is the most critical insight that must drive our entire approach. Portfolio values in CSV files are constantly changing, making them unreliable for risk assessment. Instead, we must focus exclusively on market exposure as our core metric.

## Critical Analysis of Current Data Model

### CSV Input Fields (sample-portfolio.csv)
| Field | Keep? | Reason |
|-------|-------|--------|
| Symbol | ✅ | Essential for identifying positions. Used as the primary key for grouping related positions and for fetching current market data (prices, beta) at runtime. |
| Description | ✅ | Contains critical information for option parsing (strike, expiry, option type) and helps with cash detection through pattern matching. Also provides human-readable context. |
| Quantity | ✅ | Core component for calculating exposure (Quantity × Price). Represents the size of the position and determines if it's long (positive) or short (negative). |
| Last Price | ❌ | Not needed - we fetch current prices on app load |
| Last Price Change | ❌ | Irrelevant for exposure calculation |
| Current Value | ⚠️❌ | We should stop using it, even as a fall back |
| Today's Gain/Loss Dollar | ❌ | Irrelevant for exposure calculation |
| Today's Gain/Loss Percent | ❌ | Irrelevant for exposure calculation |
| Total Gain/Loss Dollar | ❌ | Irrelevant for exposure calculation |
| Total Gain/Loss Percent | ❌ | Irrelevant for exposure calculation |
| Percent Of Account | ⚠️❌ | Used for UI display to show relative position size. However, we should stop using it.
| Cost Basis Total | ❌ | Irrelevant for exposure calculation |
| Average Cost Basis | ❌ | Irrelevant for exposure calculation |
| Type | ⚠️❌ | Irrelevant (Margin vs Cash) - we should combine positions with the same symbol |

### Position Classes

#### StockPosition
| Field | Keep? | Reason |
|-------|-------|--------|
| ticker | ✅ | Essential identifier that links the position to market data. Used for fetching current prices and beta values at runtime. |
| quantity | ✅ | Represents the number of shares held. Critical for calculating market exposure (quantity × price). Negative values indicate short positions. |
| market_value | ❌ | **REMOVE** - Unreliable and constantly changing. We calculate exposure using current prices fetched at runtime. |
| beta | ✅ | Measures the stock's volatility relative to the market (SPY). Essential for risk calculation as it determines how much the position contributes to portfolio risk. |
| beta_adjusted_exposure | ✅ | Represents the risk-adjusted market exposure (market exposure × beta). This is the core metric for understanding portfolio risk relative to the market. |

#### OptionPosition
| Field | Keep? | Reason |
|-------|-------|--------|
| ticker | ✅ | Identifies the underlying security. Used to link the option to its underlying stock for price and beta data. |
| position_type | ✅ | Designates this as an option position, allowing the system to apply option-specific calculations. |
| quantity | ✅ | Number of option contracts. Sign indicates long (positive) or short (negative) position. Each contract typically represents 100 shares. |
| market_value | ❌ | **REMOVE** - Unreliable and constantly changing. Option prices are highly volatile and not useful for risk assessment. |
| beta | ✅ | The beta of the underlying security, used to calculate beta-adjusted exposure. |
| beta_adjusted_exposure | ✅ | The risk-adjusted market exposure (delta_exposure × underlying_beta). Core metric for understanding how the option contributes to portfolio risk. |
| clean_value | ❌ | **REMOVE** - Duplicate of market_value and not relevant for exposure calculations. |
| weight | ❌ | **REMOVE** - Not used meaningfully in exposure calculations. |
| position_beta | ❌ | **REMOVE** - Duplicate of beta and not needed. |
| strike | ✅ | The price at which the option can be exercised. Critical for calculating option delta and understanding moneyness. |
| expiry | ✅ | The date when the option expires. Essential for calculating time value component of delta. |
| option_type | ✅ | Whether it's a CALL or PUT option. Determines the direction of exposure (calls increase exposure, puts decrease it). |
| delta | ✅ | Measures the rate of change in option price relative to the underlying. The key metric for calculating option exposure. |
| delta_exposure | ✅ | The market exposure created by the option (delta × notional_value). This is the core metric for understanding how the option affects portfolio exposure. |
| notional_value | ✅ | The value of the underlying shares controlled by the option (100 × underlying_price × |quantity|). Used to calculate delta_exposure. |
| underlying_beta | ✅ | The beta of the underlying security. Used to calculate how the option's exposure contributes to portfolio risk. |

### Portfolio Group
| Field | Keep? | Reason |
|-------|-------|--------|
| ticker | ✅ | The underlying security identifier that groups related positions. Used as the primary key for organizing positions and fetching market data. |
| stock_position | ✅ | Contains the stock component of this group. Essential for calculating the base exposure before considering options. |
| option_positions | ✅ | List of option positions related to this underlying. Essential for calculating the complete exposure profile including derivatives. |
| total_value | ❌ | **REMOVE** - Unreliable and constantly changing. We should focus on exposure metrics instead. |
| net_exposure | ✅ | The combined market exposure of the stock and all options (stock exposure + sum of option delta exposures). This is the core metric for understanding directional risk. |
| beta | ✅ | The beta of the underlying security. Used to understand how the entire group moves relative to the market. |
| beta_adjusted_exposure | ✅ | The risk-adjusted market exposure for the entire group. This is the key metric for understanding how this group contributes to portfolio risk. |
| total_delta_exposure | ✅ | The sum of all option delta exposures in this group. Shows how much market exposure comes from options alone. |
| options_delta_exposure | ✅ | Same as total_delta_exposure. Shows the net directional exposure from all options in this group. |
| call_count | ✅ | Number of call option positions. Useful for analyzing the composition of option strategies. |
| put_count | ✅ | Number of put option positions. Useful for analyzing the composition of option strategies. |
| net_option_value | ❌ | **REMOVE** - Based on unreliable market values of options which are constantly changing. |

### ExposureBreakdown
| Field | Keep? | Reason |
|-------|-------|--------|
| stock_value | ❌ | **RENAME** to stock_exposure - Represents the market exposure from stock positions only. Calculated as quantity × current price. |
| stock_beta_adjusted | ✅ | The risk-adjusted stock exposure (stock_exposure × beta). Shows how stock positions contribute to portfolio risk relative to the market. |
| option_delta_value | ❌ | **RENAME** to option_delta_exposure - Represents the market exposure from option positions only. Calculated using delta and notional value. |
| option_beta_adjusted | ✅ | The risk-adjusted option exposure (option_delta_exposure × underlying_beta). Shows how option positions contribute to portfolio risk. |
| total_value | ❌ | **RENAME** to total_exposure - The combined market exposure from stocks and options. This is the core metric for understanding the total directional exposure. |
| total_beta_adjusted | ✅ | The combined risk-adjusted exposure (stock_beta_adjusted + option_beta_adjusted). This is the key metric for understanding total risk contribution. |
| description | ✅ | Human-readable explanation of what this exposure breakdown represents. Useful for documentation and UI tooltips. |
| formula | ✅ | The calculation formula used to derive the exposure values. Provides transparency and helps with debugging. |
| components | ✅ | Detailed breakdown of the individual components that make up the total exposure. Useful for analysis and understanding exposure sources. |

### PortfolioSummary
| Field | Keep? | Reason |
|-------|-------|--------|
| total_exposure | ✅ | The net market exposure of the entire portfolio (long - short). Needs clear definition as it should exclude cash positions. This is the core metric for understanding directional risk. |
| portfolio_beta | ✅ | The weighted average beta of all positions, representing how the portfolio moves relative to the market. Essential for understanding overall portfolio risk and volatility. |
| long_exposure | ✅ | Detailed breakdown of all long market exposures (stocks + positive delta options). Essential for understanding the bullish component of the portfolio. |
| short_exposure | ✅ | Detailed breakdown of all short market exposures (stocks + negative delta options). Essential for understanding the bearish component of the portfolio. |
| options_exposure | ✅ | Detailed breakdown of all option exposures. Essential for understanding the derivative component of the portfolio and its impact on risk. |
| short_percentage | ✅ | The percentage of gross market exposure that is short. Needs proper calculation as (short_exposure / gross_market_exposure) × 100. Key metric for understanding portfolio hedging. |
| cash_like_positions | ✅ | List of all cash and cash-equivalent positions. Essential for tracking the non-market-exposed portion of the portfolio. |
| cash_like_value | ✅ | The total value of all cash and cash-equivalent positions. Essential for understanding the defensive/liquid portion of the portfolio. |
| cash_like_count | ✅ | The number of cash and cash-equivalent positions. Useful for analyzing diversification of the defensive portion of the portfolio. |
| help_text | ✅ | Detailed explanations of each metric. Useful for documentation, UI tooltips, and ensuring consistent understanding of metrics. |

## Core Issues to Address

1. **Eliminate All Value-Based Calculations**: We must purge all calculations that rely on market values, which are constantly changing and unreliable.

2. **Focus Exclusively on Exposure**:
   - For stocks: Exposure = Quantity × Current Price × Beta
   - For options: Exposure = Delta × 100 × Underlying Price × Quantity × Underlying Beta

3. **Clarify Terminology**:
   - Eliminate all references to "value" when we mean "exposure"
   - Be explicit about what each metric represents
   - Use consistent naming throughout the codebase

4. **Proper Cash Handling**:
   - Cash has zero market exposure (beta = 0)
   - Cash should be tracked separately from market exposure
   - Cash should be included in total portfolio size but not in exposure calculations
   - Positions should be combined regardless of account type (Margin vs Cash)
   - **Analysis of Net Exposure Calculation**: Our current implementation calculates net_market_exposure as (long_exposure - short_exposure), which already includes both stocks and options but explicitly excludes cash. Specifically:
     - long_exposure.total_exposure = long_stock_value + long_option_value
     - short_exposure.total_exposure = short_stock_value + short_option_value
     - net_market_exposure = long_exposure.total_exposure - short_exposure.total_exposure

     This is the correct approach because:
     - Cash and cash-like instruments have minimal market correlation (beta ≈ 0)
     - Including cash would artificially inflate the market exposure metrics
     - Cash is properly tracked separately via cash_percentage and cash_like_value
     - Total portfolio size (gross_market_exposure + cash_like_value) provides the complete picture

5. **Accurate Short Percentage Calculation**:
   - Should be calculated as: (Short Exposure / Gross Market Exposure) × 100
   - Gross Market Exposure = Long Exposure + Short Exposure (absolute values)
   - This ensures the percentage is always between 0-100%

## Proposed Data Model Changes

### 1. Rename Fields to Clarify Purpose

```python
@dataclass
class ExposureBreakdown:
    """Detailed breakdown of exposure by type"""

    stock_exposure: float  # Was stock_value
    stock_beta_adjusted: float
    option_delta_exposure: float  # Was option_delta_value
    option_beta_adjusted: float
    total_exposure: float  # Was total_value
    total_beta_adjusted: float
    description: str
    formula: str
    components: dict[str, float]
```

### 2. Restructure PortfolioSummary

```python
@dataclass
class PortfolioSummary:
    """Summary of portfolio metrics with detailed breakdowns"""

    # Market exposure metrics (excluding cash)
    net_market_exposure: float  # Long - Short (excluding cash)
    gross_market_exposure: float  # Long + Short (excluding cash)

    # Risk metrics
    portfolio_beta: float

    # Exposure breakdowns
    long_exposure: ExposureBreakdown
    short_exposure: ExposureBreakdown
    options_exposure: ExposureBreakdown

    # Derived metrics
    short_percentage: float  # Short / Gross Market Exposure

    # Cash metrics (separate from market exposure)
    cash_like_positions: list[StockPosition] = None
    cash_like_value: float = 0.0
    cash_like_count: int = 0
    cash_percentage: float = 0.0  # Cash / (Cash + Gross Market Exposure)

    # Total portfolio size (for reference only)
    total_portfolio_size: float = 0.0  # Gross Market Exposure + Cash

    # Help text for each metric
    help_text: dict[str, str] | None = None
```

### 3. Revise StockPosition

```python
@dataclass
class StockPosition:
    """Details of a stock position"""

    ticker: str
    quantity: int
    beta: float
    market_exposure: float  # Quantity * Current Price (fetched at runtime)
    beta_adjusted_exposure: float  # Market Exposure * Beta
```

### 4. Revise OptionPosition

```python
@dataclass
class OptionPosition:
    """Class for option positions"""

    # Base fields
    ticker: str
    position_type: Literal["option"]
    quantity: float

    # Option-specific fields
    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]

    # Exposure-related fields
    delta: float
    notional_value: float  # 100 * Underlying Price (fetched at runtime) * |Quantity|
    delta_exposure: float  # Delta * Notional Value * sign(Quantity)

    # Risk-related fields
    underlying_beta: float
    beta_adjusted_exposure: float  # Delta Exposure * Underlying Beta
```

### 5. Revise PortfolioGroup

```python
@dataclass
class PortfolioGroup:
    """Group of related positions (stock + options)"""

    ticker: str
    stock_position: StockPosition | None
    option_positions: list[OptionPosition]

    # Group metrics
    net_exposure: float  # Stock Exposure + Sum(Option Delta Exposures)
    beta: float  # Underlying beta
    beta_adjusted_exposure: float  # Sum of all beta-adjusted exposures
    total_delta_exposure: float  # Sum of all option delta exposures
    options_delta_exposure: float  # Same as total_delta_exposure

    # Option counts
    call_count: int = 0
    put_count: int = 0
```

## Implementation Plan

### Phase 1: Data Model Refactoring
1. Update `data_model.py` with revised class definitions
2. Ensure backward compatibility with existing code
3. Add new fields and rename existing ones as needed

### Phase 2: Calculation Logic Updates
1. Revise `calculate_portfolio_summary()` in `portfolio.py`
2. Update cash handling logic
3. Implement new exposure calculations

### Phase 3: UI Updates
1. Update dashboard components to use new data model
2. Revise summary cards and charts
3. Improve tooltips and help text

### Phase 4: Testing
1. Create new test cases for the revised calculations
2. Ensure all edge cases are handled correctly
3. Verify backward compatibility

## Conclusion

By focusing exclusively on market exposure and eliminating unreliable value-based calculations, we can create a more accurate and useful portfolio analysis tool. The revised data model will provide a clearer picture of portfolio risk and help users make better investment decisions.

Remember: **WE CANNOT CALCULATE VALUE ACCURATELY.** Our entire approach must be built around this fundamental limitation.
