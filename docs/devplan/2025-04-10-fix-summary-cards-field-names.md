# Summary Cards Field Names Fix - 2025-04-10

## Overview

This development plan outlines the approach to fix the issue with summary cards not displaying values in the Folio dashboard. Based on the analysis of the previous engineer's work documented in `docs/devlog/2025-04-05-summary-cards-refactor.md`, the issue appears to be related to a field name mismatch between the data model and the summary cards component.

## Problem Analysis

After reviewing the code and the devlog, I've identified the root cause of the issue:

1. **Field Name Mismatch**: The `format_summary_card_values` function in `summary_cards.py` is looking for `total_exposure` in the exposure breakdowns, but the previous implementation used `total_value`. The data model has been updated to use `total_exposure`, but the summary cards component isn't properly handling both field names.

2. **Overly Strict Validation**: The validation in the summary cards component is rejecting data that doesn't have the exact field names it expects, even though the data is valid and could be used with minor adjustments.

## Implementation Plan

### Phase 1: Add Support for Both Field Names

1. **Modify Validation Logic**
   - Update the validation in `format_summary_card_values` to accept either `total_exposure` or `total_value` field names
   - Add a helper function to check for both field names and return the appropriate value

2. **Update Access Patterns**
   - Use the helper function when accessing exposure values throughout the function
   - Ensure all code paths handle both field names correctly

### Phase 2: Add Tests

1. **Update Unit Tests**
   - Ensure the existing unit tests cover both field name variations
   - Add tests specifically for the field name handling

2. **Add Integration Test**
   - Create a test that verifies the full callback chain for summary cards
   - Test with both old and new field names

## Implementation Details

### 1. Modify Validation Logic

Update the validation in `format_summary_card_values` to accept either `total_exposure` or `total_value` field names:

```python
# Check for required sub-keys - support both old and new field names
required_sub_keys = []
if "total_beta_adjusted" not in summary_data[exposure_key]:
    required_sub_keys.append("total_beta_adjusted")

if required_sub_keys:
    logger.error(
        f"Missing required sub-keys in {exposure_key}: {required_sub_keys}"
    )
    return default_values()
```

### 2. Add Helper Function

Add a helper function to check for both field names:

```python
# Helper function to get exposure value (supports both total_exposure and total_value field names)
def get_exposure_value(exposure_dict):
    if "total_exposure" in exposure_dict:
        return exposure_dict["total_exposure"]
    elif "total_value" in exposure_dict:
        return exposure_dict["total_value"]
    return 0.0
```

### 3. Update Access Patterns

Use the helper function when accessing exposure values:

```python
# Get total exposure values with defaults (supporting both field names)
long_total_exposure = get_exposure_value(long_exposure)
long_total_beta_adjusted = long_exposure.get("total_beta_adjusted", 0.0)
short_total_exposure = get_exposure_value(short_exposure)
short_total_beta_adjusted = short_exposure.get("total_beta_adjusted", 0.0)
options_total_exposure = get_exposure_value(options_exposure)
options_total_beta_adjusted = options_exposure.get("total_beta_adjusted", 0.0)
```

## Testing Strategy

1. **Unit Testing**
   - Run the existing unit tests to ensure they still pass
   - Add tests for the new helper function
   - Add tests with both field name variations

2. **Manual Testing**
   - Test with the sample portfolio to verify that the summary cards display correctly
   - Check the logs for any errors or warnings

## Success Criteria

The fix will be considered successful if:

1. The summary cards display the correct values when loading the sample portfolio
2. The unit tests for the summary cards component pass
3. There are no errors in the logs related to the summary cards

## Rollback Plan

If the fix causes new issues:

1. Revert the changes to `summary_cards.py`
2. Document the issues encountered in a new devlog
3. Consider a different approach based on the new information

## Timeline

- Implementation: 1 day
- Testing: 1 day
- Documentation: 0.5 day

Total: 2.5 days
