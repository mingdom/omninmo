"""Formatting utility functions for the Folio application."""

import re


def clean_currency_value(value):
    """Clean a currency value string and convert to float.

    Args:
        value: A string or numeric value representing currency

    Returns:
        float: The cleaned numeric value
    """
    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return 0.0

    # Remove currency symbols, commas, and other non-numeric characters
    # Keep negative signs and decimal points
    cleaned = re.sub(r"[^0-9.-]", "", value)

    # Handle empty strings or just symbols
    if not cleaned or cleaned in ["-", "."]:
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        # If we still can't convert, return 0
        return 0.0


def format_currency(value: float) -> str:
    """Formats a numerical value as a currency string (USD).

    Includes a dollar sign, comma separators for thousands, and two decimal places.

    Args:
        value: The numerical value to format

    Returns:
        str: The formatted currency string
    """
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Formats a numerical value as a percentage string.

    Includes a percent sign and two decimal places.

    Args:
        value: The numerical value to format (0.01 = 1%)

    Returns:
        str: The formatted percentage string
    """
    return f"{value * 100:.2f}%"


def format_beta(beta: float) -> str:
    """Formats a beta value with two decimal places.

    Args:
        beta: The beta value to format

    Returns:
        str: The formatted beta string
    """
    return f"{beta:.2f}β"
