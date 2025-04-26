# Dev Plan: Fix Asset Miscategorization & Refactor Cash Logic (2025-04-01)

**REVISED based on new understanding of `Type` column, observed regressions, and consistent use of `is_cash_like`**

## Goal
1.  Correctly classify all assets based on intrinsic characteristics (`Symbol`, `Description`, calculated `beta`), irrespective of account type (`Type` column).
2.  Fix regression causing missing `weight` attribute errors when viewing stock position details.
3.  Fix regression causing missing short position and option exposure data in the summary and UI.
4.  Remove *all* incorrect logic relying on `Type` (account type) for asset classification.
5.  **Refactor code to consistently use the `is_cash_like` helper function (or its logic) for identifying pure cash/money market funds.**

## Problem Summary

1.  **Miscategorization (Main Logic):** `Type` column (`Cash`/`Margin`) was incorrectly used in `process_portfolio_data`.
2.  **Miscategorization (Helper Function):** `is_cash_like` helper function also incorrectly used `Type == "CASH"`.
3.  **Miscategorization (Error Handling):** `except` block for invalid `Current Value` incorrectly used `Type` and hardcoded symbols.
4.  **Inconsistent Cash Checks:** Direct checks for `"MONEY MARKET"` or `"SPAXX**"` existed alongside `is_cash_like`, violating DRY principle.
5.  **Missing `weight`:** `StockPosition` dataclass lacked `weight` attribute.
6.  **Missing Exposure:** Option processing logic was incomplete.
7.  **Potential Confusion:** `stock_positions["type"]` stored account type.

## Revised Proposed Solution
Modify `src/folio/utils.py`, `src/folio/data_model.py`.

1.  **Correct Asset Classification (Main Logic - No `Type`):**
    *   Add comment clarifying `Type` column.
    *   Remove flawed ETF detection block.
    *   **Refactor pure cash identification logic (around line 506) to use `is_cash_like(row)`.**
    *   Maintain `cash_like` classification based *only* on low calculated beta.

2.  **Fix `StockPosition.weight` Error:**
    *   **(data_model.py)** Add `weight: float` attribute.
    *   **(utils.py)** Ensure `weight` is passed when creating `StockPosition`.

3.  **Restore Option & Short Exposure Processing:**
    *   **(utils.py)** Restore/implement option detail parsing and `OptionPosition` creation.
    *   Verify `PortfolioSummary` aggregation.

4.  **Fix Invalid `Current Value` Error Handling (Use `is_cash_like`):**
    *   **(utils.py)** Modify the `if` condition *inside* the `except (ValueError, TypeError)` block (around line 476) to use `is_cash_like({'Symbol': symbol, 'Description': description})`.

5.  **Fix `is_cash_like` Function (Remove `Type` check):**
    *   **(utils.py)** Remove `position_type.upper() == "CASH"` condition.

6.  **Clarify `stock_positions["type"]`:**
    *   **(utils.py)** Add comment clarifying it's *account* type.

7.  **Refactor `get_beta` for Consistency:**
    *   **(utils.py)** Modify the initial check (around line 157) to handle both money market descriptions and `**` symbols consistently with `is_cash_like` logic: `if (description and "MONEY MARKET" in description.upper()) or ticker.endswith("**"): return 0.0`. Keep the separate "ESCROW" check.

## Implementation Steps
1.  **(data_model.py)** Add `weight: float` to `StockPosition` dataclass.
2.  **(utils.py)** Update `create_portfolio_group` to pass the `weight`.
3.  **(utils.py)** Add the clarifying comment about the `Type` column.
4.  **(utils.py)** Delete the flawed ETF detection block.
5.  **(utils.py)** Correct the *main* pure cash identification condition (around line 506) to use `is_cash_like(row)`.
6.  **(utils.py)** Correct the `if` condition *inside the `except` block* (around line 476) to use `is_cash_like` with a constructed dict.
7.  **(utils.py)** Correct the `is_cash_like` function by removing the `Type` check.
8.  **(utils.py)** Add clarifying comment for `stock_positions["type"]` assignment.
9.  **(utils.py)** Refactor the initial check in `get_beta` for money market/`**` symbols.
10. **(utils.py)** Restore/fix the option processing logic within the grouping loop.
11. **(Testing)** Run `make test`.
12. **(Testing)** Run `scripts/debug_etf_beta.py`.
13. **(Testing)** Run `make run` and check UI thoroughly. 