# Development Plan: Portfolio Allocations Stacked Bar Chart

## Overview

This development plan outlines the implementation of a Portfolio Allocations Stacked Bar Chart that visualizes how a portfolio's value is distributed across different asset types and position directions. The implementation will follow a two-phase approach:

1. Refactor the `calculate_portfolio_summary` function in portfolio.py to make it more modular and lean
2. Implement the stacked bar chart using the refactored functions

## Phase 1: Refactor Portfolio Summary Calculation

The current `calculate_portfolio_summary` function is large (300+ lines) and handles multiple responsibilities. We'll refactor it following the principles in `docs/lean-code.md` to create smaller, focused functions that can be reused for the chart implementation.

### Step 1.1: Extract Position Processing Functions

Create modular functions to process stock and option positions:

```python
def process_stock_positions(groups: list[PortfolioGroup]) -> tuple[dict, dict]:
    """Process stock positions from portfolio groups.

    Extracts and categorizes stock positions into long and short components.
    Short values are stored as negative numbers.

    Args:
        groups: List of portfolio groups

    Returns:
        Tuple of (long_stocks, short_stocks) dictionaries with keys:
        - 'value': Market exposure value
        - 'beta_adjusted': Beta-adjusted exposure value
    """
    long_stocks = {"value": 0.0, "beta_adjusted": 0.0}
    short_stocks = {"value": 0.0, "beta_adjusted": 0.0}  # Will contain negative values

    for group in groups:
        if group.stock_position:
            stock = group.stock_position
            if stock.quantity >= 0:  # Long position
                long_stocks["value"] += stock.market_exposure
                long_stocks["beta_adjusted"] += stock.beta_adjusted_exposure
            else:  # Short position
                # Keep negative values for short positions
                short_stocks["value"] += stock.market_exposure  # Already negative
                short_stocks["beta_adjusted"] += stock.beta_adjusted_exposure  # Already negative

    return long_stocks, short_stocks
```

```python
def process_option_positions(groups: list[PortfolioGroup]) -> tuple[dict, dict]:
    """Process option positions from portfolio groups.

    Extracts and categorizes option positions into long and short components
    based on their market value. Short values are stored as negative numbers.

    Args:
        groups: List of portfolio groups

    Returns:
        Tuple of (long_options, short_options) dictionaries with keys:
        - 'value': Market value
        - 'beta_adjusted': Beta-adjusted value
    """
    long_options = {"value": 0.0, "beta_adjusted": 0.0}
    short_options = {"value": 0.0, "beta_adjusted": 0.0}  # Will contain negative values

    for group in groups:
        for opt in group.option_positions:
            if opt.quantity >= 0:  # Long position
                long_options["value"] += opt.market_value
                long_options["beta_adjusted"] += opt.beta_adjusted_exposure
            else:  # Short position
                # Keep negative values for short positions
                short_options["value"] += opt.market_value  # Already negative for short positions
                short_options["beta_adjusted"] += opt.beta_adjusted_exposure  # Already negative

    return long_options, short_options
```

### Step 1.2: Extract Value Breakdown Creation

Create a function to build value breakdowns from position data:

```python
def create_value_breakdowns(
    long_stocks: dict,
    short_stocks: dict,  # Contains negative values
    long_options: dict,
    short_options: dict,  # Contains negative values
) -> tuple[ExposureBreakdown, ExposureBreakdown, ExposureBreakdown]:
    """Create value breakdown objects from position data for portfolio allocation.

    This function creates breakdowns of portfolio values for the allocations chart,
    showing how the total portfolio value is distributed across different types of positions.

    Args:
        long_stocks: Long stock values (positive)
        short_stocks: Short stock values (negative)
        long_options: Long option values (positive)
        short_options: Short option values (negative)

    Returns:
        Tuple of (long_value, short_value, options_value) breakdowns
    """
    # 1. Long value (stocks + options)
    long_stock_value = long_stocks["value"]
    long_option_value = long_options["value"]  # Market value
    long_stock_beta_adj = long_stocks["beta_adjusted"]
    long_option_beta_adj = long_options["beta_adjusted"]

    long_value = ExposureBreakdown(
        stock_exposure=long_stock_value,
        stock_beta_adjusted=long_stock_beta_adj,
        option_delta_exposure=long_option_value,  # Using market value here
        option_beta_adjusted=long_option_beta_adj,
        total_exposure=long_stock_value + long_option_value,
        total_beta_adjusted=long_stock_beta_adj + long_option_beta_adj,
        description="Long market value (Stocks + Options)",
        formula="Long Stocks + Long Options",
        components={
            "Long Stocks Value": long_stock_value,
            "Long Options Value": long_option_value,
        },
    )

    # 2. Short value (stocks + options)
    short_stock_value = short_stocks["value"]  # Already negative
    short_option_value = short_options["value"]  # Already negative, market value
    short_stock_beta_adj = short_stocks["beta_adjusted"]  # Already negative
    short_option_beta_adj = short_options["beta_adjusted"]  # Already negative

    short_value = ExposureBreakdown(
        stock_exposure=short_stock_value,
        stock_beta_adjusted=short_stock_beta_adj,
        option_delta_exposure=short_option_value,  # Using market value here
        option_beta_adjusted=short_option_beta_adj,
        total_exposure=short_stock_value + short_option_value,
        total_beta_adjusted=short_stock_beta_adj + short_option_beta_adj,
        description="Short market value (Stocks + Options)",
        formula="Short Stocks + Short Options",
        components={
            "Short Stocks Value": short_stock_value,
            "Short Options Value": short_option_value,
        },
    )

    # 3. Options value (net market value from all options)
    net_option_value = long_option_value + short_option_value
    net_option_beta_adj = long_option_beta_adj + short_option_beta_adj

    options_value = ExposureBreakdown(
        stock_exposure=0,  # Options only view
        stock_beta_adjusted=0,
        option_delta_exposure=net_option_value,  # Using market value here
        option_beta_adjusted=net_option_beta_adj,
        total_exposure=net_option_value,
        total_beta_adjusted=net_option_beta_adj,
        description="Net market value from options",
        formula="Long Options Value + Short Options Value (where Short is negative)",
        components={
            "Long Options Value": long_option_value,
            "Short Options Value": short_option_value,
            "Net Options Value": net_option_value,
        },
    )

    return long_value, short_value, options_value
```

### Step 1.3: Extract Portfolio Metrics Calculation

Create a function to calculate portfolio-level metrics:

```python
def calculate_portfolio_metrics(
    long_value: ExposureBreakdown,
    short_value: ExposureBreakdown,
) -> tuple[float, float, float]:
    """Calculate portfolio-level metrics from value breakdowns.

    Args:
        long_value: Long value breakdown
        short_value: Short value breakdown (with negative values)

    Returns:
        Tuple of (net_market_exposure, portfolio_beta, short_percentage)
    """
    # Calculate net market exposure
    net_market_exposure = long_value.total_exposure + short_value.total_exposure

    # Calculate portfolio beta
    net_beta_adjusted_exposure = long_value.total_beta_adjusted + short_value.total_beta_adjusted
    portfolio_beta = (
        net_beta_adjusted_exposure / net_market_exposure
        if net_market_exposure != 0
        else 0.0
    )

    # Calculate short percentage as a percentage of the total long exposure
    short_percentage = (
        (abs(short_value.total_exposure) / long_value.total_exposure) * 100
        if long_value.total_exposure > 0
        else 0.0
    )

    return net_market_exposure, portfolio_beta, short_percentage
```

### Step 1.4: Extract Portfolio Value Calculation

Create a function to calculate portfolio value metrics:

```python
def calculate_portfolio_values(
    groups: list[PortfolioGroup],
    cash_like_positions: list[dict],
    pending_activity_value: float,
) -> tuple[float, float, float, float, float]:
    """Calculate portfolio value metrics.

    Args:
        groups: List of portfolio groups
        cash_like_positions: List of cash-like positions
        pending_activity_value: Value of pending activity

    Returns:
        Tuple of (stock_value, option_value, cash_like_value, portfolio_estimate_value, cash_percentage)
    """
    # Calculate stock and option values
    stock_value = 0.0
    option_value = 0.0

    for group in groups:
        if group.stock_position:
            stock_value += group.stock_position.market_value

        for opt in group.option_positions:
            option_value += opt.market_value

    # Calculate cash-like value
    cash_like_value = sum(pos["market_value"] for pos in cash_like_positions)

    # Calculate portfolio estimated value
    portfolio_estimate_value = stock_value + option_value + cash_like_value + pending_activity_value

    # Calculate cash percentage
    cash_percentage = (
        (cash_like_value / portfolio_estimate_value * 100)
        if portfolio_estimate_value > 0
        else 0.0
    )

    return stock_value, option_value, cash_like_value, portfolio_estimate_value, cash_percentage
```

### Step 1.5: Refactor Main Portfolio Summary Function

Refactor the main `calculate_portfolio_summary` function to use the new helper functions:

```python
def calculate_portfolio_summary(
    groups: list[PortfolioGroup],
    cash_like_positions: list[dict] | None = None,
    pending_activity_value: float = 0.0,
) -> PortfolioSummary:
    """Calculate comprehensive summary metrics for the entire portfolio.

    This function aggregates data from all portfolio groups to produce a complete
    portfolio summary with exposure breakdowns, risk metrics, and cash analysis.

    IMPORTANT: Short values are stored as negative numbers throughout this function
    and in the returned PortfolioSummary object.

    Args:
        groups: List of portfolio groups
        cash_like_positions: List of cash-like positions
        pending_activity_value: Value of pending activity

    Returns:
        Portfolio summary with calculated metrics
    """
    logger.debug(f"Starting portfolio summary calculations for {len(groups)} groups.")

    # Validate inputs
    if not groups and not cash_like_positions and pending_activity_value == 0.0:
        logger.warning(
            "Cannot calculate summary for an empty portfolio. Returning default summary."
        )
        return create_empty_portfolio_summary(pending_activity_value)

    # Initialize cash-like positions list if None
    if cash_like_positions is None:
        cash_like_positions = []

    try:
        # Process positions
        long_stocks, short_stocks = process_stock_positions(groups)
        long_options, short_options = process_option_positions(groups)

        # Create value breakdowns
        long_value, short_value, options_value = create_value_breakdowns(
            long_stocks, short_stocks, long_options, short_options
        )

        # Calculate portfolio metrics
        net_market_exposure, portfolio_beta, short_percentage = calculate_portfolio_metrics(
            long_value, short_value
        )

        # Calculate portfolio values
        stock_value, option_value, cash_like_value, portfolio_estimate_value, cash_percentage = calculate_portfolio_values(
            groups, cash_like_positions, pending_activity_value
        )

        # Convert cash-like positions to StockPosition objects
        cash_like_stock_positions = convert_cash_positions_to_stock_positions(cash_like_positions)

        # Get current timestamp
        from datetime import UTC, datetime
        current_time = datetime.now(UTC).isoformat()

        # Create and return the portfolio summary
        summary = PortfolioSummary(
            net_market_exposure=net_market_exposure,
            portfolio_beta=portfolio_beta,
            long_exposure=long_value,  # Using value breakdown
            short_exposure=short_value,  # Using value breakdown
            options_exposure=options_value,  # Using value breakdown
            short_percentage=short_percentage,
            cash_like_positions=cash_like_stock_positions,
            cash_like_value=cash_like_value,
            cash_like_count=len(cash_like_positions),
            cash_percentage=cash_percentage,
            stock_value=stock_value,
            option_value=option_value,
            pending_activity_value=pending_activity_value,
            portfolio_estimate_value=portfolio_estimate_value,
            price_updated_at=current_time,
        )

        logger.debug("Portfolio summary created successfully.")
        log_summary_details(summary)
        return summary

    except Exception as e:
        logger.error("Error calculating portfolio summary", exc_info=True)
        raise RuntimeError("Failed to calculate portfolio summary") from e
```

### Step 1.6: Add Component Value Extraction Functions

Add functions to extract component values from a portfolio summary:

```python
def get_portfolio_component_values(portfolio_summary: PortfolioSummary) -> dict[str, float]:
    """Get all component values from a portfolio summary.

    This function extracts the component values from the value breakdowns
    in the portfolio summary, providing direct access to the long and short
    components for stocks and options.

    IMPORTANT: Short values are stored as negative numbers to maintain sign consistency
    throughout the codebase.

    Args:
        portfolio_summary: The portfolio summary to extract values from

    Returns:
        A dictionary with the following keys:
        - long_stock: Value of long stock positions (positive)
        - short_stock: Value of short stock positions (negative)
        - long_option: Value of long option positions (positive)
        - short_option: Value of short option positions (negative)
        - cash: Value of cash-like positions
        - pending: Value of pending activity
        - total: Total portfolio value
    """
    long_stock = portfolio_summary.long_exposure.components.get("Long Stocks Value", 0.0)
    short_stock = portfolio_summary.short_exposure.components.get("Short Stocks Value", 0.0)  # Already negative
    long_option = portfolio_summary.long_exposure.components.get("Long Options Value", 0.0)
    short_option = portfolio_summary.short_exposure.components.get("Short Options Value", 0.0)  # Already negative
    cash = portfolio_summary.cash_like_value
    pending = portfolio_summary.pending_activity_value
    total = portfolio_summary.portfolio_estimate_value

    logger.debug("Portfolio component values:")
    logger.debug(f"  Long Stock: {format_currency(long_stock)}")
    logger.debug(f"  Short Stock: {format_currency(short_stock)} (negative value)")
    logger.debug(f"  Long Option: {format_currency(long_option)}")
    logger.debug(f"  Short Option: {format_currency(short_option)} (negative value)")
    logger.debug(f"  Cash: {format_currency(cash)}")
    logger.debug(f"  Pending: {format_currency(pending)}")
    logger.debug(f"  Total: {format_currency(total)}")

    return {
        "long_stock": long_stock,
        "short_stock": short_stock,  # Kept as negative
        "long_option": long_option,
        "short_option": short_option,  # Kept as negative
        "cash": cash,
        "pending": pending,
        "total": total,
    }
```

### Step 1.7: Write Tests for Refactored Functions

Create comprehensive tests for all the new functions:

```python
def test_process_stock_positions():
    """Test that stock positions are correctly processed into long and short components."""
    # Create test data...
    # Verify that short values remain negative...

def test_process_option_positions():
    """Test that option positions are correctly processed into long and short components."""
    # Create test data...
    # Verify that short values remain negative...

def test_create_value_breakdowns():
    """Test that value breakdowns are correctly created from position data."""
    # Create test data...
    # Verify that components are correctly populated...

def test_calculate_portfolio_metrics():
    """Test that portfolio metrics are correctly calculated from exposure breakdowns."""
    # Create test data...
    # Verify that metrics are correctly calculated...

def test_calculate_portfolio_values():
    """Test that portfolio values are correctly calculated from position data."""
    # Create test data...
    # Verify that values are correctly calculated...

def test_get_portfolio_component_values():
    """Test that component values are correctly extracted from a portfolio summary."""
    # Create test data...
    # Verify that values are correctly extracted...
    # Verify that short values remain negative...
```

## Phase 2: Implement Allocations Stacked Bar Chart

With the refactored portfolio summary calculation in place, we can now implement the allocations stacked bar chart.

### Step 2.1: Create Chart Data Transformation Function

Create a function to transform portfolio summary data into a format suitable for the stacked bar chart:

```python
def transform_for_allocations_chart(portfolio_summary: PortfolioSummary) -> dict:
    """Transform portfolio summary data for the allocations stacked bar chart.

    This function takes a portfolio summary and transforms it into a format
    suitable for a stacked bar chart showing portfolio allocations. The chart
    has four main categories:
    - Long: Stacked with Long Stocks and Long Options
    - Short: Stacked with Short Stocks and Short Options (negative values)
    - Cash: Cash-like positions
    - Pending: Pending activity

    IMPORTANT: Short values are stored as negative numbers in the portfolio summary.
    For display purposes in the chart, we use the absolute values but maintain
    separate bars for long and short positions.

    Args:
        portfolio_summary: The portfolio summary to transform

    Returns:
        A dictionary with 'data' and 'layout' keys suitable for a Plotly chart
    """
    # Skip empty portfolios
    if portfolio_summary.portfolio_estimate_value == 0:
        logger.warning("Empty portfolio - no data for allocations chart")
        return {
            "data": [],
            "layout": {
                "height": 300,
                "annotations": [
                    {
                        "text": "No portfolio data available",
                        "showarrow": False,
                        "font": {"color": "#7F8C8D"},
                    }
                ],
            },
        }

    # Get component values (short values are negative)
    values = get_portfolio_component_values(portfolio_summary)

    # Calculate percentages
    total = values["total"]
    percentages = {}

    for k, v in values.items():
        if k == "total":
            percentages[k] = 100.0
        elif total > 0:
            # Calculate percentage based on absolute value, but preserve sign for display
            percentages[k] = (v / total) * 100

    # Format values for display
    long_stock_text = f"Long Stocks: {format_currency(values['long_stock'])} ({percentages['long_stock']:.1f}%)"
    short_stock_text = f"Short Stocks: {format_currency(abs(values['short_stock']))} ({abs(percentages['short_stock']):.1f}%)"
    long_option_text = f"Long Options: {format_currency(values['long_option'])} ({percentages['long_option']:.1f}%)"
    short_option_text = f"Short Options: {format_currency(abs(values['short_option']))} ({abs(percentages['short_option']):.1f}%)"
    cash_text = f"Cash: {format_currency(values['cash'])} ({percentages['cash']:.1f}%)"
    pending_text = f"Pending: {format_currency(values['pending'])} ({percentages['pending']:.1f}%)"

    # Create the stacked bar chart data
    chart_data = {
        "data": [
            # Long Stocks (bottom of "Long" stack)
            {
                "name": "Long Stocks",
                "x": ["Long"],
                "y": [values["long_stock"]],
                "type": "bar",
                "marker": {"color": ChartColors.LONG},
                "text": [long_stock_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Long Options (top of "Long" stack)
            {
                "name": "Long Options",
                "x": ["Long"],
                "y": [values["long_option"]],
                "type": "bar",
                "marker": {"color": ChartColors.OPTIONS},
                "text": [long_option_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Short Stocks (bottom of "Short" stack)
            {
                "name": "Short Stocks",
                "x": ["Short"],
                "y": [abs(values["short_stock"])],  # Use absolute value for display
                "type": "bar",
                "marker": {"color": ChartColors.SHORT},
                "text": [short_stock_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Short Options (top of "Short" stack)
            {
                "name": "Short Options",
                "x": ["Short"],
                "y": [abs(values["short_option"])],  # Use absolute value for display
                "type": "bar",
                "marker": {"color": ChartColors.SHORT_OPTIONS},
                "text": [short_option_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Cash (single bar)
            {
                "name": "Cash",
                "x": ["Cash"],
                "y": [values["cash"]],
                "type": "bar",
                "marker": {"color": ChartColors.CASH},
                "text": [cash_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
            # Pending (single bar)
            {
                "name": "Pending",
                "x": ["Pending"],
                "y": [values["pending"]],
                "type": "bar",
                "marker": {"color": ChartColors.PENDING},
                "text": [pending_text],
                "hoverinfo": "text",
                "hovertemplate": "%{text}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Portfolio Allocation",
                "font": {"size": 16, "color": "#2C3E50"},
                "x": 0.5,  # Center the title
                "xanchor": "center",
            },
            "barmode": "stack",
            "margin": {"l": 60, "r": 60, "t": 50, "b": 40, "pad": 4},
            "autosize": True,  # Allow the chart to resize with its container
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
            "font": {
                "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
            },
            "showlegend": True,
            "legend": {
                "orientation": "h",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.15,
            },
            "yaxis": {
                "title": "Value ($)",
                "tickformat": "$,.0f",
                "gridcolor": "#E5E5E5",
            },
            "yaxis2": {
                "title": "Percentage (%)",
                "overlaying": "y",
                "side": "right",
                "tickformat": ".1f%",
                "range": [0, 100],  # Fixed range for percentage
                "tickmode": "array",
                "tickvals": [0, 25, 50, 75, 100],
                "ticktext": ["0%", "25%", "50%", "75%", "100%"],
                "gridcolor": "#E5E5E5",
            },
            "height": 300,
        },
    }

    # Calculate the maximum y-value for setting the y-axis range
    max_value = max(
        values["long_stock"] + values["long_option"],
        abs(values["short_stock"]) + abs(values["short_option"]),
        values["cash"],
        values["pending"],
        1  # Ensure we have a non-zero range
    )

    # Set the y-axis range with some padding
    chart_data["layout"]["yaxis"]["range"] = [0, max_value * 1.1]

    return chart_data
```

### Step 2.2: Create Chart Component

Create a Dash component for the allocations chart:

```python
def create_allocations_chart(portfolio_summary: PortfolioSummary) -> dcc.Graph:
    """Create a Dash Graph component for the allocations chart.

    Args:
        portfolio_summary: The portfolio summary to visualize

    Returns:
        A Dash Graph component
    """
    chart_data = transform_for_allocations_chart(portfolio_summary)

    return dcc.Graph(
        id="allocations-chart",
        figure=chart_data,
        config={
            "displayModeBar": False,  # Hide the mode bar
            "responsive": True,  # Make the chart responsive
            "scrollZoom": False,  # Disable scroll zoom to prevent interference with page scrolling
        },
        style={"height": "100%", "width": "100%"},
    )
```

### Step 2.3: Add Chart to Layout

Add the allocations chart to the application layout:

```python
def create_portfolio_charts_layout(portfolio_summary: PortfolioSummary) -> html.Div:
    """Create the layout for the portfolio charts section.

    Args:
        portfolio_summary: The portfolio summary to visualize

    Returns:
        A Dash Div component containing the charts
    """
    return html.Div(
        [
            # Other charts...

            # Allocations Chart
            html.Div(
                [
                    html.H3("Portfolio Allocation", className="chart-title"),
                    create_allocations_chart(portfolio_summary),
                ],
                className="chart-container",
            ),
        ],
        className="charts-section",
    )
```

### Step 2.4: Write Tests for Chart Functions

Create tests for the chart functions:

```python
def test_transform_for_allocations_chart():
    """Test that portfolio summary data is correctly transformed for the allocations chart."""
    # Create test data...
    # Verify that chart data is correctly structured...
    # Verify that short values are handled correctly...

def test_allocations_chart_with_empty_portfolio():
    """Test that the allocations chart handles empty portfolios correctly."""
    # Create empty portfolio...
    # Verify that appropriate message is displayed...

def test_allocations_chart_with_mixed_portfolio():
    """Test that the allocations chart correctly displays a mixed portfolio."""
    # Create portfolio with long and short positions...
    # Verify that stacked bars are correctly structured...
    # Verify that values and percentages are correct...
```

## Implementation Timeline

### Week 1: Refactor Portfolio Summary Calculation
- Day 1-2: Extract position processing functions and write tests
- Day 3-4: Extract exposure breakdown and metrics calculation functions and write tests
- Day 5: Refactor main portfolio summary function and ensure all tests pass

### Week 2: Implement Allocations Chart
- Day 1-2: Create chart data transformation function and write tests
- Day 3: Create chart component and add to layout
- Day 4-5: Test chart with various portfolio compositions and fix any issues

## Conclusion

This development plan outlines a comprehensive approach to implementing the Portfolio Allocations Stacked Bar Chart. By first refactoring the portfolio summary calculation to be more modular and lean, we create reusable functions that can be leveraged for the chart implementation. This approach ensures that the chart accurately represents the portfolio's composition while maintaining consistent sign conventions (shorts as negative values) throughout the codebase.
