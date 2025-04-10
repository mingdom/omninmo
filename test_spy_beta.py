"""Test script to check SPY's beta calculation."""

from src.folio.utils import get_beta


def main():
    """Calculate and print SPY's beta."""
    get_beta("SPY")

if __name__ == "__main__":
    main()
