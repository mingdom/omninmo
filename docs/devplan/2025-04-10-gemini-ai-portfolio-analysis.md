# Gemini AI Portfolio Analysis Integration

**Date:** 2025-04-10
**Author:** Dong Ming
**Status:** Draft

## Overview

This document outlines the design and implementation plan for integrating Google Gemini AI into the Folio portfolio dashboard application. The integration will enable AI-powered analysis of portfolio data, providing users with insights on risk assessment, sector concentration, diversification recommendations, and other portfolio metrics.

## Implementation Checklist

- [ ] Phase 1: Core AI Integration (MVP)
- [ ] Phase 2: Enhanced Analysis Features
- [ ] Phase 3: Interactive AI Capabilities
- [ ] Phase 4: Personalized Recommendations

## Feature Requirements

### MVP Requirements (Phase 1)

1. **UI Components**
   - Add an "Analyze Portfolio" button above the portfolio table
   - Create a collapsible section to display AI analysis results
   - Implement loading indicator during analysis

2. **AI Integration**
   - Integrate with Google Gemini 2.5 Pro Experimental model
   - Create structured prompts for portfolio analysis
   - Process and format AI responses for display

3. **Analysis Capabilities**
   - Overall portfolio risk assessment
   - Sector concentration analysis
   - Diversification evaluation
   - Basic improvement recommendations

### Future Enhancements (Phases 2-4)

1. **Enhanced Analysis**
   - Historical performance comparison
   - Correlation analysis between holdings
   - Market condition sensitivity assessment
   - Tax efficiency analysis

2. **Interactive Capabilities**
   - Follow-up questions about the analysis
   - Ability to ask specific questions about portfolio components
   - Scenario analysis ("What if I add/remove this position?")

3. **Personalized Recommendations**
   - Investment goal-based suggestions
   - Risk tolerance-aligned recommendations
   - Tax-optimized rebalancing suggestions

## Technical Design

### 1. UI Components

#### 1.1 Analysis Button and Section

Add a new button and collapsible section to the main layout in `app.py`:

```python
def create_ai_analysis_section():
    """Create the AI analysis section with button and collapsible content"""
    return html.Div(
        [
            dbc.Button(
                [
                    html.I(className="fas fa-robot me-2"),
                    "Analyze Portfolio"
                ],
                id="analyze-portfolio-button",
                color="primary",
                className="mb-3"
            ),
            dbc.Collapse(
                dbc.Card(
                    [
                        dbc.CardHeader("AI Portfolio Analysis"),
                        dbc.CardBody(
                            [
                                html.Div(id="ai-analysis-content"),
                            ],
                            id="ai-analysis-body"
                        )
                    ],
                    className="mb-3"
                ),
                id="ai-analysis-collapse",
                is_open=False,
            )
        ],
        className="mb-4"
    )
```

This section will be placed above the portfolio table in the main layout.

### 2. Gemini AI Integration

#### 2.1 API Client Module

Create a new module `src/folio/utils/gemini_client.py` to handle Gemini API interactions:

```python
"""Google Gemini AI client for portfolio analysis."""

import os
import logging
from typing import Dict, List, Any, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google Gemini AI API."""

    def __init__(self):
        """Initialize the Gemini client with API key from environment."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro-experimental",
            generation_config=GenerationConfig(
                temperature=0.2,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        logger.info("Gemini client initialized successfully")

    async def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze portfolio data using Gemini AI.

        Args:
            portfolio_data: Dictionary containing portfolio information

        Returns:
            Dictionary with structured analysis results
        """
        prompt = self._create_analysis_prompt(portfolio_data)

        try:
            response = await self.model.generate_content_async(prompt)

            # Process and structure the response
            structured_analysis = self._process_analysis_response(response.text)
            logger.info("Portfolio analysis completed successfully")
            return structured_analysis

        except Exception as e:
            logger.error(f"Error during portfolio analysis: {str(e)}")
            return {
                "error": True,
                "message": f"Analysis failed: {str(e)}",
            }

    def _create_analysis_prompt(self, portfolio_data: Dict[str, Any]) -> str:
        """
        Create a structured prompt for portfolio analysis.

        Args:
            portfolio_data: Dictionary containing portfolio information

        Returns:
            Formatted prompt string
        """
        # Extract key portfolio metrics
        positions = portfolio_data.get("positions", [])
        summary = portfolio_data.get("summary", {})

        # Format positions data
        positions_text = "\n".join([
            f"- {pos['ticker']}: {pos['position_type'].upper()}, "
            f"Value: ${pos['market_value']:.2f}, "
            f"Beta: {pos['beta']:.2f}, "
            f"Weight: {pos['weight']:.2%}"
            for pos in positions
        ])

        # Format summary data
        total_value = summary.get("total_value_net", 0)
        portfolio_beta = summary.get("portfolio_beta", 0)

        # Construct the prompt
        prompt = f"""
        You are a professional financial advisor analyzing a stock portfolio.
        Provide a comprehensive analysis of the following portfolio data:

        PORTFOLIO SUMMARY:
        - Total Value: ${total_value:.2f}
        - Portfolio Beta: {portfolio_beta:.2f}

        POSITIONS:
        {positions_text}

        Please analyze this portfolio and provide insights on:
        1. Overall risk assessment (based on beta, diversification, and position sizes)
        2. Sector concentration analysis
        3. Diversification evaluation
        4. Specific improvement recommendations

        Format your response in clear sections with headers. Be specific and actionable in your recommendations.
        """

        return prompt

    def _process_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process and structure the raw AI response.

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Dictionary with structured analysis sections
        """
        # Simple processing for MVP - future versions can implement more sophisticated parsing
        sections = {
            "risk_assessment": "",
            "sector_concentration": "",
            "diversification": "",
            "recommendations": "",
            "raw_response": response_text
        }

        # Extract sections based on headers in the response
        current_section = None

        for line in response_text.split("\n"):
            line = line.strip()

            if "risk assessment" in line.lower():
                current_section = "risk_assessment"
                continue
            elif "sector concentration" in line.lower():
                current_section = "sector_concentration"
                continue
            elif "diversification" in line.lower():
                current_section = "diversification"
                continue
            elif "recommendation" in line.lower():
                current_section = "recommendations"
                continue

            if current_section and line:
                sections[current_section] += line + "\n"

        return sections
```

#### 2.2 Portfolio Data Preparation

Create a utility function in `src/folio/utils/ai_utils.py` to prepare portfolio data for AI analysis:

```python
"""Utility functions for AI portfolio analysis."""

from typing import Dict, List, Any

from ..data_model import PortfolioGroup, PortfolioSummary

def prepare_portfolio_data_for_analysis(
    groups: List[PortfolioGroup],
    summary: PortfolioSummary
) -> Dict[str, Any]:
    """
    Prepare portfolio data for AI analysis.

    Args:
        groups: List of portfolio groups
        summary: Portfolio summary object

    Returns:
        Dictionary with formatted portfolio data
    """
    positions = []

    # Process each portfolio group
    for group in groups:
        # Add stock position if present
        if group.stock_position:
            stock = group.stock_position
            positions.append({
                "ticker": stock.ticker,
                "position_type": "stock",
                "market_value": stock.market_value,
                "beta": stock.beta,
                "weight": stock.market_value / summary.total_value_net if summary.total_value_net else 0,
                "quantity": stock.quantity
            })

        # Add option positions if present
        for option in group.option_positions:
            positions.append({
                "ticker": option.ticker,
                "position_type": "option",
                "market_value": option.market_value,
                "beta": option.beta,
                "weight": option.market_value / summary.total_value_net if summary.total_value_net else 0,
                "option_type": option.option_type,
                "strike": option.strike,
                "expiry": option.expiry,
                "delta": option.delta
            })

    # Create summary data
    summary_data = {
        "total_value_net": summary.total_value_net,
        "total_value_abs": summary.total_value_abs,
        "portfolio_beta": summary.portfolio_beta,
        "long_exposure": {
            "total": summary.long_exposure.total_value,
            "beta_adjusted": summary.long_exposure.total_beta_adjusted
        },
        "short_exposure": {
            "total": summary.short_exposure.total_value,
            "beta_adjusted": summary.short_exposure.total_beta_adjusted
        }
    }

    return {
        "positions": positions,
        "summary": summary_data
    }
```

### 3. UI Integration

#### 3.1 Callbacks for AI Analysis

Add callbacks in `app.py` to handle the AI analysis button and display results:

```python
@app.callback(
    [
        Output("ai-analysis-collapse", "is_open"),
        Output("ai-analysis-content", "children"),
        Output("ai-analysis-body", "className")
    ],
    [Input("analyze-portfolio-button", "n_clicks")],
    [
        State("ai-analysis-collapse", "is_open"),
        State("portfolio-groups", "data"),
        State("portfolio-summary", "data")
    ],
    prevent_initial_call=True
)
async def toggle_ai_analysis(n_clicks, is_open, groups_data, summary_data):
    """Toggle AI analysis section and generate analysis when button is clicked"""
    if not n_clicks:
        return is_open, None, ""

    if not groups_data or not summary_data:
        return True, html.Div("No portfolio data available for analysis", className="text-danger"), ""

    # If already open, just close it
    if is_open:
        return False, dash.no_update, ""

    # Initialize loading state
    loading_class = "ai-loading"

    # Deserialize data
    groups = [PortfolioGroup.from_dict(g) for g in groups_data]
    summary = PortfolioSummary.from_dict(summary_data)

    # Prepare data for analysis
    portfolio_data = prepare_portfolio_data_for_analysis(groups, summary)

    try:
        # Initialize Gemini client
        client = GeminiClient()

        # Get analysis
        analysis = await client.analyze_portfolio(portfolio_data)

        if analysis.get("error"):
            return True, html.Div(analysis.get("message"), className="text-danger"), ""

        # Create analysis content
        content = html.Div([
            html.Div([
                html.H5("Risk Assessment"),
                html.Div(analysis["risk_assessment"], className="analysis-section")
            ], className="mb-3"),

            html.Div([
                html.H5("Sector Concentration"),
                html.Div(analysis["sector_concentration"], className="analysis-section")
            ], className="mb-3"),

            html.Div([
                html.H5("Diversification"),
                html.Div(analysis["diversification"], className="analysis-section")
            ], className="mb-3"),

            html.Div([
                html.H5("Recommendations"),
                html.Div(analysis["recommendations"], className="analysis-section")
            ], className="mb-3"),
        ])

        return True, content, ""

    except Exception as e:
        error_message = f"Error generating portfolio analysis: {str(e)}"
        return True, html.Div(error_message, className="text-danger"), ""
```

#### 3.2 CSS Styling

Add CSS styles in `assets/styles.css` for the AI analysis section:

```css
/* AI Analysis Section Styles */
.analysis-section {
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: rgba(0, 0, 0, 0.03);
    border-radius: 0.25rem;
}

.ai-loading {
    position: relative;
}

.ai-loading::after {
    content: "Analyzing...";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(255, 255, 255, 0.8);
    font-weight: bold;
    z-index: 10;
}
```

### 4. Environment Configuration

#### 4.1 Environment Variables

Add the required environment variable for the Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

This should be added to the deployment environment and documented for local development.

## Implementation Plan

### Phase 1: MVP Implementation (2-3 days)

1. **Day 1: Setup and Basic Integration**
   - Create the Gemini client module
   - Implement portfolio data preparation utilities
   - Add UI components for the analysis button and collapsible section

2. **Day 2: Core Functionality**
   - Implement the analysis callback
   - Create prompt engineering for basic portfolio analysis
   - Add response processing and formatting

3. **Day 3: Testing and Refinement**
   - Test with various portfolio compositions
   - Refine prompt engineering based on results
   - Add error handling and edge cases

### Phase 2: Enhanced Analysis Features (Future)

1. **Historical Performance Analysis**
   - Integrate historical data into the analysis
   - Compare current portfolio to past performance
   - Identify trends and patterns

2. **Correlation Analysis**
   - Analyze correlations between holdings
   - Identify potential diversification improvements
   - Suggest alternative assets with lower correlations

3. **Market Condition Sensitivity**
   - Analyze portfolio performance under different market conditions
   - Stress test against historical market events
   - Provide resilience recommendations

### Phase 3: Interactive AI Capabilities (Future)

1. **Conversational Interface**
   - Allow follow-up questions about the analysis
   - Enable specific queries about portfolio components
   - Provide clarification on recommendations

2. **Scenario Analysis**
   - "What if" analysis for adding/removing positions
   - Portfolio rebalancing simulations
   - Market scenario impact projections

### Phase 4: Personalized Recommendations (Future)

1. **User Preferences Integration**
   - Incorporate user investment goals
   - Consider risk tolerance in recommendations
   - Adapt to time horizon preferences

2. **Tax-Optimized Suggestions**
   - Consider tax implications in recommendations
   - Suggest tax-efficient rebalancing strategies
   - Identify tax-loss harvesting opportunities

## Security and Privacy Considerations

1. **API Key Management**
   - Store API keys securely in environment variables
   - Never expose API keys in client-side code
   - Implement key rotation procedures

2. **Data Privacy**
   - Only send necessary portfolio data to the API
   - Do not include personally identifiable information
   - Implement data minimization principles

3. **Error Handling**
   - Gracefully handle API failures
   - Provide meaningful error messages without exposing sensitive details
   - Implement retry mechanisms with backoff

## Testing Strategy

1. **Unit Tests**
   - Test data preparation functions
   - Test response processing logic
   - Mock API responses for consistent testing

2. **Integration Tests**
   - Test end-to-end flow with mock portfolios
   - Verify UI updates correctly with analysis results
   - Test error handling and edge cases

3. **Prompt Engineering Tests**
   - Evaluate analysis quality with different portfolio compositions
   - Test extreme cases (very concentrated, very diversified)
   - Verify recommendations are appropriate for the portfolio

## Conclusion

The Gemini AI Portfolio Analysis integration will provide users with valuable insights into their portfolios, helping them make more informed investment decisions. The phased approach allows for incremental delivery of value while building toward a more sophisticated AI-powered advisory capability.

The MVP focuses on delivering core analysis capabilities with a simple, intuitive UI, while future phases will expand the depth and interactivity of the analysis, ultimately creating a personalized AI financial assistant within the Folio application.
