# AI Feature Update: Integrating Latest Portfolio Data

## Overview

The current AI feature in the Folio app doesn't include the latest summary data or portfolio allocation breakdowns. This plan outlines how to update the AI integration to provide more comprehensive and up-to-date information to the AI model, enhancing its ability to provide meaningful portfolio analysis.

## Current Implementation Analysis

### AI Data Preparation
- The `prepare_portfolio_data_for_analysis` function in `src/folio/ai_utils.py` currently includes:
  - Position data (stocks and options)
  - Basic summary data (net exposure, portfolio beta, long/short exposure)
- It does not include:
  - Portfolio value (which is now a higher-level object)
  - Allocation breakdowns from the charts
  - Percentage values for each metric

### AI Integration
- The AI feature is implemented in `src/folio/components/premium_chat.py`
- It uses the Gemini API to generate responses based on the portfolio data
- The data is prepared using the `prepare_portfolio_data_for_analysis` function

### Chart Data
- The allocations chart data is generated in `transform_for_allocations_chart` in `src/folio/chart_data.py`
- The exposure chart data is generated in `transform_for_exposure_chart`
- These charts provide valuable visualizations that could enhance the AI's understanding of the portfolio

## Proposed Changes

### 1. Enhance the `prepare_portfolio_data_for_analysis` Function

Update the function to include portfolio value and reuse existing chart data transformation functions:

```python
def prepare_portfolio_data_for_analysis(
    groups: list[PortfolioGroup], summary: PortfolioSummary
) -> dict[str, Any]:
    """
    Prepare portfolio data for AI analysis.

    Args:
        groups: List of portfolio groups
        summary: Portfolio summary object

    Returns:
        Dictionary with formatted portfolio data
    """
    # Existing code for processing positions
    positions = []
    for group in groups:
        if group.stock_position:
            stock = group.stock_position
            positions.append(
                {
                    "ticker": stock.ticker,
                    "position_type": "stock",
                    "market_value": stock.market_exposure,
                    "beta": stock.beta,
                    "weight": calculate_position_weight(
                        stock.market_exposure, summary.net_market_exposure
                    ),
                    "quantity": stock.quantity,
                }
            )

        for option in group.option_positions:
            positions.append(
                {
                    "ticker": option.ticker,
                    "position_type": "option",
                    "market_value": option.market_exposure,
                    "beta": option.beta,
                    "weight": calculate_position_weight(
                        option.market_exposure, summary.net_market_exposure
                    ),
                    "option_type": option.option_type,
                    "strike": option.strike,
                    "expiry": option.expiry,
                    "delta": option.delta,
                }
            )

    # Enhanced summary data with portfolio value
    summary_data = {
        "portfolio_value": summary.portfolio_estimate_value,
        "net_market_exposure": summary.net_market_exposure,
        "portfolio_beta": summary.portfolio_beta,
        "long_exposure": summary.long_exposure.to_dict(),
        "short_exposure": summary.short_exposure.to_dict(),
        "options_exposure": summary.options_exposure.to_dict(),
        "cash_like_value": summary.cash_like_value,
    }

    # Get allocation data from existing portfolio_value functions
    values = get_portfolio_component_values(summary)
    percentages = calculate_component_percentages(values)

    # Create allocation data structure
    allocation_data = {
        "values": values,
        "percentages": percentages
    }

    return {
        "positions": positions,
        "summary": summary_data,
        "allocations": allocation_data
    }
```

### 2. Update the Gemini Client Context Creation

Enhance the `_create_conversation_context` method in `src/folio/gemini_client.py` to include the new data, using multi-line formatted strings for cleaner code:

```python
def _create_conversation_context(self, portfolio_data: dict[str, Any] | None) -> str:
    """
    Create a context string with portfolio information for the AI.

    Args:
        portfolio_data: Dictionary containing portfolio information

    Returns:
        Formatted context string
    """
    if not portfolio_data:
        return ""

    # Extract key portfolio metrics
    positions = portfolio_data.get("positions", [])
    summary = portfolio_data.get("summary", {})
    allocations = portfolio_data.get("allocations", {})

    # Get values and percentages
    values = allocations.get("values", {})
    percentages = allocations.get("percentages", {})

    # Format positions data (limit to top 10 by value for context size)
    sorted_positions = sorted(
        positions, key=lambda p: abs(p.get("market_value", 0)), reverse=True
    )[:10]

    # Build context using multi-line f-strings
    context = f"""Portfolio Analysis Context:

Portfolio Summary:
- Total Portfolio Value: ${summary.get('portfolio_value', 0):,.2f}
- Net Market Exposure: ${summary.get('net_market_exposure', 0):,.2f}
- Portfolio Beta: {summary.get('portfolio_beta', 0):.2f}

Exposure Breakdown:
- Long Exposure: ${summary.get('long_exposure', {}).get('total_exposure', 0):,.2f} ({percentages.get('long_stocks', 0) + percentages.get('long_options', 0):.1f}% of portfolio)
- Short Exposure: ${abs(summary.get('short_exposure', {}).get('total_exposure', 0)):,.2f} ({percentages.get('short_stocks', 0) + percentages.get('short_options', 0):.1f}% of portfolio)
- Options Exposure: ${abs(summary.get('options_exposure', {}).get('total_exposure', 0)):,.2f} ({percentages.get('long_options', 0) + percentages.get('short_options', 0):.1f}% of portfolio)
- Cash & Equivalents: ${summary.get('cash_like_value', 0):,.2f} ({percentages.get('cash', 0):.1f}% of portfolio)

Portfolio Allocation:
- Long Stocks: ${values.get('long_stocks', 0):,.2f} ({percentages.get('long_stocks', 0):.1f}%)
- Long Options: ${values.get('long_options', 0):,.2f} ({percentages.get('long_options', 0):.1f}%)
- Short Stocks: ${abs(values.get('short_stocks', 0)):,.2f} ({percentages.get('short_stocks', 0):.1f}%)
- Short Options: ${abs(values.get('short_options', 0)):,.2f} ({percentages.get('short_options', 0):.1f}%)
- Cash: ${values.get('cash', 0):,.2f} ({percentages.get('cash', 0):.1f}%)
- Pending Activity: ${values.get('pending', 0):,.2f} ({percentages.get('pending', 0):.1f}%)

Top Positions (by market value):
"""

    # Add top positions
    for i, pos in enumerate(sorted_positions, 1):
        ticker = pos.get("ticker", "Unknown")
        pos_type = pos.get("position_type", "Unknown")
        market_value = pos.get("market_value", 0)
        weight = pos.get("weight", 0) * 100  # Convert to percentage

        if pos_type == "option":
            option_type = pos.get("option_type", "Unknown")
            strike = pos.get("strike", 0)
            expiry = pos.get("expiry", "Unknown")
            delta = pos.get("delta", 0)
            context += f"{i}. {ticker} {option_type.upper()} ${strike} {expiry} - ${market_value:,.2f} ({weight:.1f}% of portfolio, delta: {delta:.2f})\n"
        else:
            context += f"{i}. {ticker} - ${market_value:,.2f} ({weight:.1f}% of portfolio)\n"

    return context
```

### 3. Update the System Prompt

Enhance the system prompt in `src/folio/ai_utils.py` to reference the new data:

```python
PORTFOLIO_ADVISOR_SYSTEM_PROMPT = """
You are a professional financial advisor specializing in portfolio analysis. Your role is strictly limited to:

1. Analyzing the client's investment portfolio
2. Providing insights on portfolio composition, risk, diversification, and performance
3. Offering investment advice related to the client's holdings
4. Answering questions about financial markets, investment strategies, and specific securities

Important guidelines:
- ONLY respond to questions related to investing, finance, and the client's portfolio
- REFUSE to answer any questions unrelated to finance or investments
- If asked about non-financial topics, politely redirect the conversation back to the portfolio
- Maintain a professional, knowledgeable tone
- Base your analysis on the portfolio data provided
- Be transparent about limitations in your analysis
- When discussing portfolio allocation, refer to the detailed breakdown provided in the context
- When discussing exposure, consider both the raw exposure values and beta-adjusted values
- Pay attention to the percentage of portfolio for each metric to provide context

Your goal is to help clients understand their investments and make informed decisions about their portfolio.
"""
```

### 4. Update Tests

Update the tests in `tests/test_ai_integration.py` to verify the new data is included:

```python
def test_prepare_portfolio_data_for_analysis_with_allocations():
    """Test that prepare_portfolio_data_for_analysis includes allocation data."""
    # Use existing test data setup

    # Test prepare_portfolio_data_for_analysis
    ai_data = prepare_portfolio_data_for_analysis([portfolio_group], summary)

    # Verify the structure of the prepared data
    assert "positions" in ai_data
    assert "summary" in ai_data
    assert "allocations" in ai_data

    # Verify summary includes portfolio value
    assert "portfolio_value" in ai_data["summary"]

    # Verify allocation data structure
    allocations = ai_data["allocations"]
    assert "values" in allocations
    assert "percentages" in allocations

    # Verify values and percentages contain expected keys
    values = allocations["values"]
    percentages = allocations["percentages"]
    expected_keys = ["long_stocks", "long_options", "short_stocks", "short_options", "cash", "pending"]
    for key in expected_keys:
        assert key in values
        assert key in percentages
```

## Implementation Plan

1. **Update `ai_utils.py`**:
   - Enhance `prepare_portfolio_data_for_analysis` function to include portfolio value
   - Reuse existing `get_portfolio_component_values` and `calculate_component_percentages` functions
   - Update the system prompt

2. **Update `gemini_client.py`**:
   - Enhance `_create_conversation_context` method to include the new data
   - Use multi-line formatted strings for cleaner code

3. **Update Tests**:
   - Update existing tests in `tests/test_ai_integration.py`
   - Add new tests for the allocation data

4. **Test the Integration**:
   - Test the AI feature with a sample portfolio
   - Verify that the AI responses include insights based on the new data

## Conclusion

This development plan outlines how to update the AI feature to include the latest summary data and portfolio allocation breakdowns. By reusing existing functions like `get_portfolio_component_values` and `calculate_component_percentages`, we maintain code consistency and avoid duplication. The use of multi-line formatted strings makes the code more readable and maintainable, aligning with the lean code principles.
