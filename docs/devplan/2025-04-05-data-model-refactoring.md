# Data Model Refactoring: Value-Based to Exposure-Based Metrics

**Date:** 2025-04-05
**Author:** Augment AI Assistant
**Status:** Proposed

## Overview

This development plan outlines a comprehensive refactoring of the Folio data model to transition from value-based metrics to exposure-based metrics. The refactoring is necessary because value cannot be accurately calculated for options, making exposure-based metrics more appropriate for a unified view of portfolio risk.

## Background

The Folio application has been transitioning from value-based metrics (e.g., `market_value`, `total_value`) to exposure-based metrics (e.g., `market_exposure`, `net_exposure`). This transition is partially complete, resulting in inconsistencies in the codebase where some components still use the old value-based field names while others use the new exposure-based field names.

These inconsistencies are causing errors in the application, particularly in the AI integration features where the old field names are still being used.

## Current Issues

1. **Inconsistent Field Names**: Some classes use `market_value` while others use `market_exposure` for the same concept
2. **Missing Backward Compatibility**: Classes have been updated without providing backward compatibility for code that still uses the old field names
3. **Incomplete Refactoring**: Some parts of the codebase have been updated to use the new field names while others have not
4. **Test Failures**: Tests are failing because they use the old field names that no longer exist in the updated classes

## Goals

1. Provide backward compatibility for all renamed fields
2. Ensure consistent naming across the codebase
3. Fix all test failures related to the refactoring
4. Document the transition for future developers
5. Create a plan for eventually removing the deprecated fields

## Field Mapping and Action Items

Below is a comprehensive list of all fields that need to be addressed, organized by class:

### StockPosition

| Old Field | New Field | Action |
|-----------|-----------|--------|
| `market_value` | `market_exposure` | ✅ Added property that returns `market_exposure` with deprecation warning |
| | | ✅ Updated constructor to accept `market_value` parameter |

### OptionPosition

| Old Field | New Field | Action |
|-----------|-----------|--------|
| `market_value` | `market_exposure` | ✅ Inherits from Position which has the compatibility property |
| | | ✅ Updated constructor to accept `market_value` parameter |

### PortfolioGroup

| Old Field | New Field | Action |
|-----------|-----------|--------|
| `total_value` | `net_exposure` | ✅ Added property that returns `net_exposure` with deprecation warning |
| | | ✅ Updated constructor to accept `total_value` parameter |

### ExposureBreakdown

| Old Field | New Field | Action |
|-----------|-----------|--------|
| `stock_value` | `stock_exposure` | ✅ Added property that returns `stock_exposure` with deprecation warning |
| | | ✅ Updated constructor to accept `stock_value` parameter |
| `option_delta_value` | `option_delta_exposure` | ✅ Added property that returns `option_delta_exposure` with deprecation warning |
| | | ✅ Updated constructor to accept `option_delta_value` parameter |
| `total_value` | `total_exposure` | ✅ Added property that returns `total_exposure` with deprecation warning |
| | | ✅ Updated constructor to accept `total_value` parameter |

### PortfolioSummary

| Old Field | New Field | Action |
|-----------|-----------|--------|
| `total_exposure` | `net_market_exposure` | ❌ Rename all usages to `net_market_exposure` without compatibility layer |
| `net_exposure` | `net_market_exposure` | ❌ Rename all usages to `net_market_exposure` without compatibility layer |
| `exposure_reduction_percentage` | N/A | ❌ Remove all usages of this field (not useful) |

### AI Utils (src/folio/ai_utils.py)

| Old Usage | New Usage | Action |
|-----------|-----------|--------|
| `stock.market_value` | `stock.market_exposure` | ✅ Keep using `market_value` with compatibility layer (will log warnings) |
| `option.market_value` | `option.market_exposure` | ✅ Keep using `market_value` with compatibility layer (will log warnings) |
| `summary.total_exposure` | `summary.net_market_exposure` | ❌ Rename all usages to `net_market_exposure` without compatibility layer |
| `summary.long_exposure.total_value` | `summary.long_exposure.total_exposure` | ✅ Keep using `total_value` with compatibility layer (will log warnings) |
| `summary.short_exposure.total_value` | `summary.short_exposure.total_exposure` | ✅ Keep using `total_value` with compatibility layer (will log warnings) |

### Tests (tests/test_ai_integration.py)

| Old Usage | New Usage | Action |
|-----------|-----------|--------|
| `market_value` parameter | `market_exposure` parameter | ✅ Using backward compatibility |
| `total_value` parameter | `net_exposure` parameter | ✅ Using backward compatibility |
| `stock_value` parameter | `stock_exposure` parameter | ✅ Using backward compatibility |
| `option_delta_value` parameter | `option_delta_exposure` parameter | ✅ Using backward compatibility |
| `total_value` parameter (ExposureBreakdown) | `total_exposure` parameter | ✅ Using backward compatibility |
| `net_exposure` parameter (PortfolioSummary) | `net_market_exposure` parameter | ❌ Rename all usages to `net_market_exposure` without compatibility layer |
| `exposure_reduction_percentage` parameter | N/A | ❌ Remove all usages of this field (not useful) |
| Assertions using `total_exposure` | `net_market_exposure` | ❌ Rename all usages to `net_market_exposure` without compatibility layer |
| Assertions using `total_value` | `total_exposure` | ✅ Keep using `total_value` with compatibility layer (will log warnings) |

## Implementation Plan

### Phase 1: Complete Backward Compatibility (Current Phase)

1. ✅ Add backward compatibility to `StockPosition` for `market_value`
2. ✅ Add backward compatibility to `OptionPosition` for `market_value`
3. ✅ Add backward compatibility to `PortfolioGroup` for `total_value`
4. ✅ Add backward compatibility to `ExposureBreakdown` for `stock_value`, `option_delta_value`, and `total_value`
5. ❌ Rename all usages of `total_exposure` and `net_exposure` to `net_market_exposure` in `PortfolioSummary` without compatibility layer
6. ❌ Remove all usages of `exposure_reduction_percentage` field

### Phase 2: Update AI Utils

1. ❌ Rename all usages of `total_exposure` to `net_market_exposure` in `ai_utils.py` without compatibility layer
2. ✅ Keep using other old field names with compatibility layers (will log warnings)
3. ❌ Update tests to verify that the AI utils work with the compatibility layers

### Phase 3: Update Tests

1. ❌ Rename all usages of `total_exposure` and `net_exposure` to `net_market_exposure` in tests without compatibility layer
2. ❌ Add tests that verify backward compatibility works correctly
3. ❌ Add tests that verify deprecation warnings are issued when using old field names

### Phase 4: Documentation and Cleanup

1. ❌ Update docstrings to reflect the new field names
2. ❌ Add comments explaining the backward compatibility for future developers
3. ❌ Create a plan for eventually removing the deprecated fields
4. ❌ Update any documentation that references the old field names

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking changes to the API | High | Medium | Maintain backward compatibility with properties and constructor parameters |
| Inconsistent naming in the codebase | Medium | High | Comprehensive audit of all field names and usages |
| Confusion for developers | Medium | Medium | Clear documentation and deprecation warnings |
| Performance impact of property access | Low | Low | Monitor performance and optimize if necessary |

## Testing Strategy

1. **Unit Tests**: Update existing tests to use the new field names
2. **Backward Compatibility Tests**: Add tests that verify backward compatibility works correctly
3. **Deprecation Warning Tests**: Add tests that verify deprecation warnings are issued when using old field names
4. **Integration Tests**: Test the entire application to ensure all components work together correctly

## Conclusion

This refactoring will standardize the Folio data model on exposure-based metrics, which are more appropriate for a unified view of portfolio risk. By providing backward compatibility, we can ensure a smooth transition without breaking existing code.

The immediate focus is on fixing the current issues with the AI integration features, but the long-term goal is to have a consistent, well-documented data model that accurately represents the portfolio's risk characteristics.
