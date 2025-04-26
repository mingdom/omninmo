# Spec: Robust Beta Calculation and Cash-Like Grouping

## Overview

Our goal is to create a robust, flexible, and resilient implementation for beta calculation and grouping of cash-like instruments in our portfolio processing system. The new implementation is designed to reduce complexity and avoid hardcoding values based on symbols.

## Phase 1: Robust Beta Calculation

### Goals
Ultimately we want to be able to group cash and cash-like instruments in the portfolio and summarize it. In order to achieve this, we plan on the following steps:
- Implement a generic beta calculation function that:
   - Returns 0.0 for instruments with no inherent beta (e.g., money market funds).
   - Returns 1.0 for the market proxy (SPY).
   - Computes realistic beta values for stocks, ETFs, and bonds based on historical data.
- Avoid hardcoded values; rely on data-driven insights and robust error handling.
- Use the check_beta.py script as a validation harness.

### Implementation Steps
1. Revise the beta function in src/folio/utils.py:
   - Remove hardcoded symbol checks.
   - Implement early exit criteria to return 0.0 when instrument characteristics indicate a money market or similar non-risk asset.
   - Ensure SPY always returns a beta of 1.0.
2. Enhance error handling and logging for debugging.
3. Validate outputs using the check_beta.py script for a variety of instrument types.

## Phase 2: Cash-Like Grouping via Beta Threshold

### Goals
- Classify positions as cash-like if abs(beta) < 0.1.
- Use the updated beta function in portfolio processing to identify and group these instruments.
- Preserve pure cash positions (based on explicit cash descriptions) separately from cash-like instruments.
- Aggregate cash-like instruments for a dedicated summary while keeping them out of the standard stock grouping.

### Implementation Steps
1. Update the portfolio processing logic:
   - For each instrument, compute the beta using the revised function.
   - If abs(beta) < 0.1, classify the instrument as cash-like.
   - Accumulate these instruments into a separate group for later summary display.
2. Ensure minimal changes to existing grouping logic to avoid a full refactor.

## Phase 3: Minimal UI Changes for Cash-Like Summary

### Goals
- Integrate a new UI summary group that displays aggregated data for cash-like instruments.
- Implement the UI change with minimal disruption to existing components.

### Implementation Steps
1. Update the portfolio summary component in the UI:
   - Add a new section titled "Cash-Like Instruments".
   - Display aggregated metrics (total value, count, percentage of portfolio) for cash-like positions.
2. Validate that the new UI component renders correctly and that its data reflects the underlying calculations.

## Testing Plan

1. **Beta Function Tests:**
   - Use check_beta.py to ensure:
     - Money market funds return 0.0.
     - SPY returns 1.0.
     - Other instruments produce realistic beta values.
2. **Portfolio Processing Tests:**
   - Write unit tests to verify:
     - Correct classification of positions with abs(beta) < 0.1 as cash-like.
     - Accurate aggregation of cash and cash-like values.
3. **UI Tests:**
   - Ensure the new summary group for cash-like instruments renders correctly and updates in real-time.
   - Confirm that standard groupings remain unaffected.

---

# Reference Material (Salvaged Insights)

**From 2025-04-01-035850-cash-handling.md:**
- Emphasis on data-driven identification of cash/money market instruments rather than hardcoding based on symbol names.

**Additional DevPlan Documents (e.g., 20250401-052104-fix-etf-cash-miscategorization.md):**
- Previous challenges with redundant logic and excessive refactoring highlight the need for a minimal, incremental approach and clear separation of concerns.

**Recent DevLog Changes:**
- Improvements in logging and error handling underlined the importance of modular, minimal changes. These lessons will guide us to avoid previous pitfalls.

This spec serves as a clear blueprint for our new implementation, ensuring robust beta calculation, effective cash-like grouping, and minimal UI updates. The approach is designed to be flexible, resilient, and easy to maintain. 