import re

"""Cash detection functionality for portfolio analysis.

This module provides functions for identifying cash-like positions in a portfolio.
"""


def is_likely_money_market(
    ticker: str | float | None, description: str | float | None = ""
) -> bool:
    """Determine if a position is likely a money market fund based on patterns and keywords.

    This function uses pattern matching on the ticker symbol and description to identify
    common money market funds and cash-like instruments.

    Args:
        ticker: The ticker symbol to check
        description: The description of the security

    Returns:
        True if the position is likely a money market fund, False otherwise
    """
    # Handle None or non-string inputs
    if ticker is None or not isinstance(ticker, str):
        return False
    if description is None or not isinstance(description, str):
        description = ""

    # Convert to uppercase for case-insensitive matching
    ticker = ticker.upper()
    description = description.upper()

    # Pattern 1: Common money market fund symbol patterns (ending with XX)
    if re.search(r"[A-Z]{2,4}XX$", ticker):
        return True

    # Pattern 2: Description contains money market related terms
    money_market_terms = [
        "MONEY MARKET",
        "CASH RESERVES",
        "TREASURY ONLY",
        "GOVERNMENT LIQUIDITY",
        "CASH MANAGEMENT",
        "LIQUID ASSETS",
        "CASH EQUIVALENT",
        "TREASURY FUND",
        "LIQUIDITY FUND",
        "CASH FUND",
        "RESERVE FUND",
    ]

    for term in money_market_terms:
        if term in description:
            return True

    # Pattern 3: Common prefixes for money market funds
    money_market_prefixes = ["SPAXX", "FMPXX", "VMFXX", "SWVXX"]
    for prefix in money_market_prefixes:
        if ticker.startswith(prefix):
            return True

    # Pattern 4: Common short-term treasury ETFs
    short_term_treasury_etfs = ["BIL", "SHY", "SGOV", "GBIL"]
    if ticker in short_term_treasury_etfs:
        return True

    return False


def is_cash_or_short_term(
    ticker: str | float | None,
    beta: float | None = None,
    description: str | float | None = "",
) -> bool:
    """Determine if a position should be considered cash or cash-like.

    This function checks if a position is likely cash or a cash-like instrument
    based on its ticker, beta, and description. Cash-like instruments include
    money market funds, short-term bond funds, and other low-volatility assets.

    Args:
        ticker: The ticker symbol to check
        beta: The calculated beta value for the position
        description: The description of the security

    Returns:
        True if the position is likely cash or cash-like, False otherwise
    """
    # Handle None or non-string inputs for ticker and description
    if ticker is None or not isinstance(ticker, str):
        return False
    if description is None or not isinstance(description, str):
        description = ""

    # Convert to uppercase for case-insensitive matching
    ticker = ticker.upper()
    description = description.upper()

    # Check if it's a money market fund
    if is_likely_money_market(ticker, description):
        return True

    # Check for very low beta (near zero)
    if beta is not None and abs(beta) < 0.1:
        return True

    # Check for short-term bond fund keywords
    short_term_keywords = [
        "SHORT TERM BOND",
        "SHORT DURATION",
        "ULTRA SHORT",
        "TREASURY BILL",
        "T-BILL",
        "MONEY FUND",
        "CASH EQUIVALENT",
        "FLOATING RATE",
    ]

    for keyword in short_term_keywords:
        if keyword in description:
            return True

    # Check for common short-term bond ETFs
    short_term_etfs = [
        "SHV",  # iShares Short Treasury Bond ETF
        "BIL",  # SPDR Bloomberg 1-3 Month T-Bill ETF
        "SGOV",  # iShares 0-3 Month Treasury Bond ETF
        "GBIL",  # Goldman Sachs Treasury Access 0-1 Year ETF
        "NEAR",  # iShares Short Maturity Bond ETF
        "FLOT",  # iShares Floating Rate Bond ETF
        "MINT",  # PIMCO Enhanced Short Maturity Active ETF
        "GSY",  # Invesco Ultra Short Duration ETF
    ]

    if ticker in short_term_etfs:
        return True

    return False
