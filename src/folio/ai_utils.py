"""Utility functions for AI portfolio analysis."""

import logging
from typing import Any

from .data_model import PortfolioGroup, PortfolioSummary

logger = logging.getLogger(__name__)

# System prompt for the AI portfolio advisor
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

Your goal is to help clients understand their investments and make informed decisions about their portfolio.
"""


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
    positions = []

    # Process each portfolio group
    for group in groups:
        # Add stock position if present
        if group.stock_position:
            stock = group.stock_position
            positions.append(
                {
                    "ticker": stock.ticker,
                    "position_type": "stock",
                    "market_value": stock.market_value,
                    "beta": stock.beta,
                    "weight": stock.market_value / summary.net_market_exposure
                    if summary.net_market_exposure
                    else 0,
                    "quantity": stock.quantity,
                }
            )

        # Add option positions if present
        for option in group.option_positions:
            positions.append(
                {
                    "ticker": option.ticker,
                    "position_type": "option",
                    "market_value": option.market_value,
                    "beta": option.beta,
                    "weight": option.market_value / summary.net_market_exposure
                    if summary.net_market_exposure
                    else 0,
                    "option_type": option.option_type,
                    "strike": option.strike,
                    "expiry": option.expiry,
                    "delta": option.delta,
                }
            )

    # Create summary data
    summary_data = {
        "net_market_exposure": summary.net_market_exposure,
        "portfolio_beta": summary.portfolio_beta,
        "long_exposure": {
            "total": summary.long_exposure.total_value,
            "beta_adjusted": summary.long_exposure.total_beta_adjusted,
        },
        "short_exposure": {
            "total": summary.short_exposure.total_value,
            "beta_adjusted": summary.short_exposure.total_beta_adjusted,
        },
    }

    return {"positions": positions, "summary": summary_data}
