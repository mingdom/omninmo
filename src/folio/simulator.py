"""Portfolio simulator module.

This module provides functionality for simulating portfolio performance
under different market scenarios, particularly changes in the SPY index.
"""

import numpy as np

from .data_model import PortfolioGroup
from .logger import logger
from .portfolio import recalculate_portfolio_with_prices


def simulate_portfolio_with_spy_changes(
    portfolio_groups: list[PortfolioGroup],
    spy_changes: list[float] | None = None,
    cash_like_positions: list[dict] | None = None,
    pending_activity_value: float = 0.0,
) -> dict:
    """Simulate portfolio performance across different SPY price changes.

    Args:
        portfolio_groups: Portfolio groups to simulate
        spy_changes: List of SPY price change percentages (e.g., [-0.3, -0.25, ..., 0.25, 0.3])
                    If None, uses default range from -30% to +30% in 5% increments
        cash_like_positions: Cash-like positions
        pending_activity_value: Value of pending activity

    Returns:
        Dictionary with simulation results containing:
        - 'spy_changes': List of SPY change percentages
        - 'portfolio_values': List of portfolio values at each SPY change
        - 'portfolio_exposures': List of portfolio exposures at each SPY change
        - 'current_value': Current portfolio value (at 0% change)
        - 'current_exposure': Current portfolio exposure (at 0% change)
    """
    if not portfolio_groups:
        logger.warning("Cannot simulate an empty portfolio")
        return {
            "spy_changes": [],
            "portfolio_values": [],
            "portfolio_exposures": [],
            "current_value": 0.0,
            "current_exposure": 0.0,
        }

    # Use default SPY changes if none provided
    if spy_changes is None:
        spy_changes = np.arange(-0.30, 0.31, 0.05).tolist()

    # Initialize results
    portfolio_values = []
    portfolio_exposures = []

    # Get current portfolio value and exposure (at 0% change)
    current_value = 0.0
    current_exposure = 0.0

    # Simulate for each SPY change
    for spy_change in spy_changes:
        # Calculate price adjustments for each ticker based on its beta
        price_adjustments = {}
        for group in portfolio_groups:
            # Use the group's beta to calculate price adjustment
            beta = group.beta
            price_adjustment = 1.0 + (spy_change * beta)
            price_adjustments[group.ticker] = price_adjustment

        # Recalculate portfolio with adjusted prices
        recalculated_groups, recalculated_summary = recalculate_portfolio_with_prices(
            portfolio_groups,
            price_adjustments,
            cash_like_positions,
            pending_activity_value
        )

        # Store results
        portfolio_values.append(recalculated_summary.portfolio_estimate_value)
        portfolio_exposures.append(recalculated_summary.net_market_exposure)

        # Store current values (at 0% change)
        if abs(spy_change) < 0.001:  # Close to 0%
            current_value = recalculated_summary.portfolio_estimate_value
            current_exposure = recalculated_summary.net_market_exposure

    return {
        "spy_changes": spy_changes,
        "portfolio_values": portfolio_values,
        "portfolio_exposures": portfolio_exposures,
        "current_value": current_value,
        "current_exposure": current_exposure,
    }


def calculate_percentage_changes(
    values: list[float],
    base_value: float
) -> list[float]:
    """Calculate percentage changes relative to a base value.

    Args:
        values: List of values
        base_value: Base value to calculate percentage changes from

    Returns:
        List of percentage changes
    """
    if base_value == 0:
        return [0.0] * len(values)

    return [(value / base_value - 1.0) * 100.0 for value in values]
