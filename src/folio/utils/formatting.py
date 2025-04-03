"""Formatting utilities for the Folio application."""

def format_currency(value: float) -> str:
    """Formats a numerical value as a currency string (USD).

    Includes a dollar sign, comma separators for thousands, and two decimal places.
    Negative values are represented with a leading minus sign.

    Args:
        value: The numerical value to format.

    Returns:
        A string representing the value in USD currency format (e.g., "$1,234.56", "-$500.00").
    """
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Formats a numerical value as a percentage string.

    Multiplies the value by 100 and appends a percentage sign. Displays one decimal place.

    Args:
        value: The numerical value to format (e.g., 0.25 for 25%).

    Returns:
        A string representing the value as a percentage (e.g., "25.0%").
    """
    return f"{value * 100:.1f}%"


def format_beta(value: float) -> str:
    """Formats a beta value with a trailing Greek beta symbol (β).

    Displays the value with two decimal places.

    Args:
        value: The numerical beta value.

    Returns:
        A string representing the beta value followed by 'β' (e.g., "1.23β").
    """
    return f"{value:.2f}β"
