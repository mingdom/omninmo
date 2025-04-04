"""Beta calculation utilities for the Folio application."""

import pandas as pd

from ..logger import logger


def get_beta(ticker, description=None):
    """Get beta for a ticker.

    Args:
        ticker: The ticker symbol
        description: Optional description to help identify cash-like instruments

    Returns:
        float: The beta value (0.0 for cash-like instruments)
    """
    # Special case for cash-like instruments
    if description and any(
        cash_term in description.lower()
        for cash_term in [
            "cash",
            "money market",
            "treasury",
            "t-bill",
            "tbill",
            "govt",
            "government",
        ]
    ):
        logger.debug(f"Identified {ticker} as cash-like from description, setting beta=0")
        return 0.0

    # Special case for common cash tickers
    if ticker in ["SPAXX", "FDRXX", "SPRXX", "FZFXX", "SPAXX", "FDIC"]:
        logger.debug(f"Identified {ticker} as known cash-like ticker, setting beta=0")
        return 0.0

    # For other tickers, we would normally calculate beta using historical data
    # For simplicity in this implementation, we'll use some default values
    default_betas = {
        "SPY": 1.0,
        "QQQ": 1.1,
        "AAPL": 1.2,
        "MSFT": 1.1,
        "GOOGL": 1.15,
        "AMZN": 1.3,
        "META": 1.25,
        "TSLA": 1.5,
        "NVDA": 1.4,
        "AMD": 1.45,
    }

    # Return default beta if available, otherwise use 1.0
    return default_betas.get(ticker, 1.0)
