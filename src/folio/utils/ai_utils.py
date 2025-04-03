"""Utility functions for AI portfolio analysis."""

import logging
from typing import Dict, List, Any

from ..data_model import PortfolioGroup, PortfolioSummary

logger = logging.getLogger(__name__)

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
