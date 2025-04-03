"""Portfolio processing utilities."""

import pandas as pd

from ..data_model import PortfolioGroup, PortfolioSummary


def process_portfolio_data(
    df: pd.DataFrame,
) -> tuple[list[PortfolioGroup], PortfolioSummary, list[dict]]:
    """Processes a raw portfolio DataFrame to generate structured portfolio data and summary metrics.

    This is a wrapper around the original process_portfolio_data function in utils.py.
    """
    # Import the original function directly from the main utils.py module
    # This avoids circular imports by importing at function call time
    import importlib

    # Get the module dynamically to avoid circular imports
    utils_module = importlib.import_module('src.folio.utils')

    # Call the original function
    return utils_module.process_portfolio_data(df)
