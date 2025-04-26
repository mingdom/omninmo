# Position Value Implementation Plan

## Overview

This development plan outlines how to implement proper position value calculations for both stocks and options in the portfolio, separating market value from market exposure to provide a more accurate representation of the portfolio's total value.

## Current State

Currently, the application:

1. Uses `market_exposure` as the primary value metric for positions
2. For stocks, `market_exposure = quantity * price` (which is correct for value)
3. For options, `market_exposure = delta_exposure` (which represents directional exposure, not actual value)
4. Sets `market_value = market_exposure` for backward compatibility
5. Calculates `portfolio_estimate_value = net_market_exposure + cash_like_value`

This approach conflates market exposure (a risk metric) with market value (an asset value metric), leading to inaccurate portfolio valuation, especially for options positions. We need to properly separate these concepts to get an accurate portfolio value.

## Implementation Plan

### Phase 1: Update Data Models

1. Modify the `Position`, `StockPosition`, and `OptionPosition` classes to properly separate value from exposure
2. Update the `PortfolioSummary` class to include proper portfolio value calculations
3. Ensure backward compatibility with existing code

### Phase 2: Update Portfolio Calculation Logic

1. Update the portfolio processing logic to calculate proper position values
2. Modify the portfolio summary calculation to use position values instead of exposures
3. Add new metrics for total portfolio value

### Phase 3: Update UI Components

1. Update the summary cards to display the new value metrics
2. Modify the portfolio table to show position values
3. Ensure all charts and visualizations use the correct metrics

### Phase 4: Testing and Documentation

1. Add comprehensive tests for the new value calculations
2. Update documentation to reflect the new approach
3. Update the `datamodel.md` file to document the changes
4. Verify that all existing functionality continues to work correctly

## Detailed Implementation

### Phase 1: Update Data Models

#### 1.1 Update the `Position` class

```python
@dataclass
class Position:
    """Base class for all positions"""

    ticker: str
    position_type: Literal["stock", "option"]
    quantity: float
    beta: float
    beta_adjusted_exposure: float
    market_exposure: float  # Quantity * Current Price (for stocks) or Delta * Notional Value (for options)
    market_value: float  # Actual market value of the position (quantity * price)

    def __init__(
        self,
        ticker: str,
        position_type: Literal["stock", "option"],
        quantity: float,
        beta: float,
        beta_adjusted_exposure: float,
        market_exposure: float,
        market_value: float,
    ):
        """Initialize a Position.

        Args:
            ticker: Security ticker symbol
            position_type: Type of position (stock or option)
            quantity: Number of shares or contracts
            beta: Position beta
            beta_adjusted_exposure: Beta-adjusted market exposure
            market_exposure: Market exposure (quantity * price for stocks, delta * notional for options)
            market_value: Actual market value of the position (quantity * price)
        """

        self.ticker = ticker
        self.position_type = position_type
        self.quantity = quantity
        self.beta = beta
        self.beta_adjusted_exposure = beta_adjusted_exposure
        self.market_exposure = market_exposure
        self.market_value = market_value
```

#### 1.2 Update the `StockPosition` class

```python
@dataclass
class StockPosition:
    """Details of a stock position

    A stock position represents a holding of shares in a particular security.
    Negative quantity values represent short positions.
    """

    ticker: str
    quantity: int
    beta: float
    market_exposure: float  # Quantity * Price (fetched at runtime)
    beta_adjusted_exposure: float  # Market Exposure * Beta
    price: float = 0.0  # Price per share
    position_type: str = "stock"  # Always "stock" for StockPosition
    cost_basis: float = 0.0  # Cost basis per share
    market_value: float = 0.0  # Actual market value (quantity * price)

    def __init__(
        self,
        ticker: str,
        quantity: int,
        beta: float,
        beta_adjusted_exposure: float,
        market_exposure: float,
        price: float = 0.0,
        position_type: str = "stock",
        cost_basis: float = 0.0,
        market_value: float = None,  # Default to None to calculate from price and quantity
    ):
        """Initialize a StockPosition.

        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares
            beta: Stock beta
            beta_adjusted_exposure: Beta-adjusted market exposure
            market_exposure: Market exposure (quantity * price)
            price: Price per share
            position_type: Type of position, always "stock" for StockPosition
            cost_basis: Cost basis per share (for P&L calculations)
            market_value: Actual market value (quantity * price), calculated if None
        """

        self.ticker = ticker
        self.quantity = quantity
        self.beta = beta
        self.beta_adjusted_exposure = beta_adjusted_exposure
        self.position_type = position_type
        self.price = price
        self.cost_basis = cost_basis
        self.market_exposure = market_exposure

        # For stocks, market_value is the same as market_exposure
        # But we explicitly calculate it to ensure consistency
        if market_value is None:
            self.market_value = price * quantity
        else:
            self.market_value = market_value
```

#### 1.3 Update the `OptionPosition` class

```python
@dataclass
class OptionPosition:
    """Details of an option position

    An option position represents a holding of option contracts.
    Negative quantity values represent short positions.
    """

    ticker: str
    position_type: Literal["option"]
    quantity: int
    beta: float
    beta_adjusted_exposure: float
    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float
    notional_value: float
    underlying_beta: float
    market_exposure: float  # Delta * Notional Value
    price: float = 0.0  # Price per contract
    cost_basis: float = 0.0  # Cost basis per contract
    market_value: float = 0.0  # Actual market value (price * quantity)

    def __init__(
        self,
        ticker: str,
        position_type: Literal["option"],
        quantity: int,
        beta: float,
        beta_adjusted_exposure: float,
        strike: float,
        expiry: str,
        option_type: Literal["CALL", "PUT"],
        delta: float,
        delta_exposure: float,
        notional_value: float,
        underlying_beta: float,
        market_exposure: float,
        price: float = 0.0,
        cost_basis: float = 0.0,
        market_value: float = None,  # Default to None to calculate from price and quantity
    ):
        """Initialize an OptionPosition.

        Args:
            ticker: Option ticker symbol
            position_type: Type of position, always "option" for OptionPosition
            quantity: Number of contracts
            beta: Option beta
            beta_adjusted_exposure: Beta-adjusted market exposure
            strike: Strike price
            expiry: Expiration date
            option_type: Type of option (CALL or PUT)
            delta: Option delta
            delta_exposure: Delta-adjusted exposure
            notional_value: Notional value of the option
            underlying_beta: Beta of the underlying security
            market_exposure: Market exposure (delta * notional_value)
            price: Price per contract
            cost_basis: Cost basis per contract (for P&L calculations)
            market_value: Actual market value (price * quantity), calculated if None
        """

        self.ticker = ticker
        self.position_type = position_type
        self.quantity = quantity
        self.beta = beta
        self.beta_adjusted_exposure = beta_adjusted_exposure
        self.strike = strike
        self.expiry = expiry
        self.option_type = option_type
        self.delta = delta
        self.delta_exposure = delta_exposure
        self.notional_value = notional_value
        self.underlying_beta = underlying_beta
        self.market_exposure = market_exposure
        self.price = price
        self.cost_basis = cost_basis

        # For options, market_value is price * quantity
        if market_value is None:
            self.market_value = price * quantity
        else:
            self.market_value = market_value
```

#### 1.4 Update the `PortfolioSummary` class

```python
@dataclass
class PortfolioSummary:
    """Summary of portfolio metrics"""

    # Exposure metrics
    net_market_exposure: float
    portfolio_beta: float
    long_exposure: ExposureBreakdown
    short_exposure: ExposureBreakdown
    options_exposure: ExposureBreakdown
    short_percentage: float  # Short / (Long + Short)

    # Cash metrics
    cash_like_positions: list[StockPositionDict]
    cash_like_value: float
    cash_like_count: int
    cash_percentage: float  # Cash / Portfolio Value

    # Value metrics
    stock_value: float  # Total value of stock positions
    option_value: float  # Total value of option positions

    # Portfolio value (total value of all positions including cash)
    portfolio_estimate_value: float  # Net Market Exposure + Cash + Option Value

    # Price update timestamp
    price_updated_at: str | None = None
```

### Phase 2: Update Portfolio Calculation Logic

#### 2.1 Update the portfolio processing logic

```python
# In src/folio/portfolio.py - process_portfolio_data function

# For stock positions
stock_positions[symbol] = {
    "price": price,
    "quantity": quantity,
    "value": value_to_use,
    "beta": beta,
    "percent_of_account": percent_of_account,
    "account_type": row["Type"],
    "description": description,
    "cost_basis": cost_basis,
    "market_value": price * quantity,  # Add explicit market value calculation
}

# For option positions
option_data_for_group.append({
    "ticker": opt["ticker"],
    "option_symbol": opt["option_symbol"],
    "description": opt["description"],
    "quantity": opt["quantity"],
    "beta": opt["beta"],
    "beta_adjusted_exposure": opt["beta_adjusted_exposure"],
    "market_exposure": opt["delta_exposure"],  # Delta-adjusted exposure is the market exposure
    "strike": opt["strike"],
    "expiry": opt["expiry"],
    "option_type": opt["option_type"],
    "delta": opt["delta"],
    "delta_exposure": opt["delta_exposure"],
    "notional_value": opt["notional_value"],
    "price": opt["price"],
    "cost_basis": opt.get("cost_basis", opt["price"]),  # Use price as default cost basis
    "market_value": opt["price"] * opt["quantity"],  # Add explicit market value calculation
})
```

#### 2.2 Update the portfolio summary calculation

```python
# In src/folio/portfolio.py - calculate_portfolio_summary function

# Calculate total position values
stock_value = 0.0
option_value = 0.0

# Process each group
for group in groups:
    # --- Process stock position ---
    if group.stock_position:
        stock = group.stock_position
        stock_value += stock.market_value

    # --- Process option positions ---
    for opt in group.option_positions:
        option_value += opt.market_value

# Calculate portfolio value
total_position_value = stock_value + option_value
portfolio_value = total_position_value + cash_like_value

# Create and return the portfolio summary
summary = PortfolioSummary(
    net_market_exposure=net_market_exposure,
    portfolio_beta=portfolio_beta,
    long_exposure=long_exposure,
    short_exposure=short_exposure,
    options_exposure=options_exposure,
    short_percentage=short_percentage,
    cash_like_positions=cash_like_stock_positions,
    cash_like_value=cash_like_value,
    cash_like_count=cash_like_count,
    cash_percentage=cash_percentage,
    stock_value=stock_value,  # New field
    option_value=option_value,  # New field
    portfolio_estimate_value=portfolio_value,  # Update with accurate portfolio value
    price_updated_at=current_time,
)
```

### Phase 3: Update UI Components

#### 3.1 Update the summary cards

```python
# In src/folio/components/summary_cards.py - create_portfolio_value_card function

def create_portfolio_value_card():
    """Create the portfolio value card."""
    # Create the portfolio value component
    portfolio_value = html.H5(
        id="portfolio-value",
        className="card-title text-primary",
        children="$0.00",  # Default value
    )

    # Create the card with the portfolio value component nested inside it
    return dbc.Col(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H6(
                            "Portfolio Value",
                            className="card-subtitle",
                        ),
                        portfolio_value,  # Nest the component here
                    ]
                ),
                className="mb-3",
                id="portfolio-value-card",
            ),
            dbc.Tooltip(
                "Total value of all positions (stocks, options, and cash).",
                target="portfolio-value-card",
                placement="top",
            ),
        ],
        width=3,
    )
```

#### 3.2 Update the portfolio table

```python
# In src/folio/components/portfolio_table.py - create_position_row function

def create_position_row(group: PortfolioGroup, _metrics: dict) -> dbc.Row:
    """Create a row for a position in the portfolio table"""
    ticker = get_group_ticker(group)

    # Calculate total market value for the group
    total_market_value = 0
    if group.stock_position:
        total_market_value += group.stock_position.market_value

    for option in group.option_positions:
        total_market_value += option.market_value

    return dbc.Row(
        [
            dbc.Col(
                html.Strong(ticker),
                width=2,
                className="text-truncate text-center",
                style={"padding": "0.5rem"},
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.Span("Stock" if group.stock_position else ""),
                            html.Span(
                                f" ({len(group.option_positions)} options)"
                                if group.option_positions
                                else ""
                            ),
                        ]
                    )
                ],
                width=2,
                className="text-truncate text-center",
            ),
            dbc.Col(
                format_currency(total_market_value),  # Show market value instead of exposure
                width=2,
                className="text-truncate text-center",
            ),
            dbc.Col(
                format_currency(group.net_exposure),  # Keep showing exposure
                width=2,
                className="text-truncate text-center",
            ),
            dbc.Col(
                format_beta(
                    group.beta_adjusted_exposure / group.net_exposure
                    if group.net_exposure != 0
                    else 0
                ),
                width=2,
                className="text-truncate text-center",
            ),
            dbc.Col(
                html.Div(
                    [
                        dbc.Button(
                            html.I(className="fas fa-chart-line"),
                            id={"type": "position-pnl", "index": ticker},
                            color="primary",
                            size="sm",
                            className="btn-icon",
                        ),
                        dbc.Tooltip(
                            "View position analysis and P&L chart",
                            target={"type": "position-pnl", "index": ticker},
                            placement="left",
                        ),
                    ],
                    className="d-flex justify-content-center",
                ),
                width=2,
            ),
        ],
        className="g-0 border-bottom py-2 position-row",
        id=f"row-{ticker}",
    )
```

### Phase 4: Testing and Documentation

#### 4.1 Add tests for the new value calculations

```python
# In tests/test_portfolio.py

def test_position_market_value():
    """Test that position market values are calculated correctly."""
    # Create a stock position
    stock = StockPosition(
        ticker="AAPL",
        quantity=100,
        beta=1.2,
        beta_adjusted_exposure=12000.0,
        market_exposure=10000.0,
        price=100.0,
    )

    # Verify market value is calculated correctly
    assert stock.market_value == 10000.0

    # Create an option position
    option = OptionPosition(
        ticker="AAPL250417C220",
        position_type="option",
        quantity=10,
        beta=1.2,
        beta_adjusted_exposure=12000.0,
        strike=220.0,
        expiry="2025-04-17",
        option_type="CALL",
        delta=0.5,
        delta_exposure=10000.0,
        notional_value=20000.0,
        underlying_beta=1.2,
        market_exposure=10000.0,
        price=5.0,
    )

    # Verify market value is calculated correctly (price * quantity)
    assert option.market_value == 50.0

def test_portfolio_value_calculation():
    """Test that portfolio value is calculated correctly."""
    # Create a portfolio with stocks, options, and cash
    # ... (implementation details)

    # Verify portfolio value is calculated correctly
    assert summary.portfolio_estimate_value == summary.stock_value + summary.option_value + summary.cash_like_value
```

## Risk Assessment

### Complexity

**Medium**

- The core functionality for calculating position values already exists
- The main work is separating value from exposure and updating the UI
- Backward compatibility needs careful consideration

### Design Trade-offs

1. **Market Value vs. Market Exposure**
   - **Market Value**:
     - Pros: Accurate representation of position worth, consistent with financial statements
     - Cons: Doesn't capture directional risk exposure
   - **Market Exposure**:
     - Pros: Better represents directional risk, useful for risk management
     - Cons: Not an accurate representation of position worth

   **Decision**: Implement both metrics separately. Use market value for portfolio valuation and market exposure for risk analysis.

2. **Option Value Calculation**
   - **Contract Price * Quantity**:
     - Pros: Simple, accurate representation of current market value
     - Cons: Doesn't account for leverage or risk
   - **Delta * Notional Value**:
     - Pros: Better represents directional exposure
     - Cons: Not an accurate representation of current market value

   **Decision**: Use contract price * quantity for market value and delta * notional value for market exposure.

3. **UI Representation**
   - **Show Both Metrics**:
     - Pros: Complete information, clear distinction between value and exposure
     - Cons: More complex UI, potential for confusion
   - **Focus on One Metric**:
     - Pros: Simpler UI, less confusing
     - Cons: Incomplete information

   **Decision**: Show both metrics in the UI, but clearly label them and provide tooltips explaining the difference.

### Phase 5: Update datamodel.md

After implementing the changes, we need to update the `datamodel.md` file to reflect the new approach. Here's what needs to be updated:

1. Update the "Fundamental Principle" section to acknowledge that we can calculate value accurately for positions, but we need to separate value from exposure
2. Update the "Key Concepts" section to include market value as a separate concept from market exposure
3. Update the field descriptions for all classes to reflect the separation of value and exposure
4. Remove the "Deprecated Fields" sections that suggest using market_exposure instead of market_value
5. Add new sections explaining the difference between value and exposure

Here's a sample of the changes needed:

```markdown
## Fundamental Principle

**SEPARATE VALUE FROM EXPOSURE.** This is the most critical insight that drives our approach. While portfolio values are constantly changing, we can calculate them accurately at a point in time. However, for risk assessment, we must focus on market exposure rather than market value.

## Key Concepts

1. **Market Value**: The actual worth of a position, calculated as:
   - For stocks: Quantity × Current Price
   - For options: Quantity × Current Price

2. **Market Exposure**: The amount of money exposed to market movements, calculated as:
   - For stocks: Quantity × Current Price
   - For options: Delta × Notional Value (100 × Underlying Price × |Quantity|)
```

## Conclusion

This implementation plan provides a comprehensive approach to separating position values from exposure calculations, resulting in a more accurate representation of portfolio value. By maintaining both metrics, we can provide users with a complete picture of their portfolio's worth and risk exposure.

The plan balances accuracy, usability, and backward compatibility, while considering the trade-offs between different approaches. The result will be a more accurate and useful portfolio management tool that clearly distinguishes between position value and market exposure.
