# Portfolio and Utils Module Refactoring

## Overview

This document outlines the refactoring of the `src/folio/utils.py` file to separate portfolio processing and CSV loading logic into a dedicated `src/folio/portfolio.py` module. This improves code modularity and makes the codebase more maintainable.

## Module Responsibilities

### src/folio/utils.py

Utility functions for formatting and data processing:

1. **get_beta(ticker, description)** - Calculates the beta (systematic risk) for a given financial instrument
2. **format_currency(value)** - Formats a numerical value as a currency string (USD)
3. **format_percentage(value)** - Formats a numerical value as a percentage string
4. **format_beta(value)** - Formats a beta value with a trailing Greek beta symbol (β)
5. **clean_currency_value(value_str)** - Converts a formatted currency string into a float
6. **is_option(symbol)** - Determines if a financial symbol likely represents an option contract

### src/folio/portfolio.py

Portfolio data processing and CSV loading functionality:

1. **process_portfolio_data(df)** - Processes a raw portfolio DataFrame to generate structured portfolio data and summary metrics
2. **calculate_portfolio_summary(groups, cash_like_positions)** - Calculates aggregated summary metrics for the entire portfolio
3. **log_summary_details(summary)** - Helper function to log the details of the PortfolioSummary object
4. **is_likely_money_market(ticker, description)** - Determines if a position is likely a money market fund based on patterns and keywords
5. **is_cash_or_short_term(ticker, beta, description)** - Determines if a position should be considered cash or cash-like

## Implementation Plan

1. Create a new file `src/folio/portfolio.py` with a copy of the content from `src/folio/utils.py`
2. Update imports in `portfolio.py` to include any necessary references to functions that remain in `utils.py`
3. Remove functions from `portfolio.py` that should remain in `utils.py`
4. Update imports in files that use the portfolio processing functions to import from `portfolio.py` instead
5. Run tests after each function removal to ensure everything still works

## Testing

Run `make test` after each function removal to ensure that the refactoring doesn't break any functionality.
Run `make portfolio` to verify that the Folio app still works correctly with the refactored code.
