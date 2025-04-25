# Beta-Adjusted Exposure Calculation Discrepancy

## Context

While implementing the SPY simulator feature (as documented in [SPY Simulator Handoff](docs/devlog/2025-04-25-spy-simulator-handoff.md)), we encountered a regression in the `test_exposures.py` test. This test previously passed but began failing after our recent changes to centralize and standardize exposure calculations.

The test is designed to verify that the beta-adjusted exposure values displayed in the UI match those calculated for the summary cards. This ensures consistency in how we present portfolio risk metrics to users across different parts of the application.

## Error Observed

The `test_exposures.py` test is failing with the following assertion error:

```
E       assert 1181434.56 == 1130221.32 ± 0.01
E        +  where 1181434.56 = summary_beta_adjusted_net_exposure
E        +  and   1130221.32 = total_ui_beta_adjusted_exposure
```

The test is comparing two values:
1. `summary_beta_adjusted_net_exposure`: The beta-adjusted exposure value shown in the summary cards
2. `total_ui_beta_adjusted_exposure`: The sum of beta-adjusted exposures from all portfolio groups shown in the UI

These values should be identical, but there's a discrepancy of approximately $51,213.

## Investigation

The test loads a portfolio from `private-data/test/test-portfolio.csv` and processes it through two different calculation paths:

1. **Summary Cards Path**:
   - Calculates beta-adjusted exposure using `long_exposure.total_beta_adjusted + short_exposure.total_beta_adjusted`
   - These values come from `process_stock_positions` and `process_option_positions` in `portfolio_value.py`

2. **UI Components Path**:
   - Sums `group.beta_adjusted_exposure` for all portfolio groups
   - Each group's beta-adjusted exposure is calculated in `create_portfolio_group` in `data_model.py`

These two paths should produce the same result, but they're currently diverging.

## Changes Made

1. **Centralized Calculation Functions**:
   - Added a centralized `calculate_beta_adjusted_option_exposure` function in `options.py`
   - Updated various functions to use this centralized function for consistency
   - This improved code maintainability but didn't resolve the test failure

## Attempted Solutions (Not Yet Working)

1. **Investigating Cash-Like Positions**:
   - Verified that cash positions have a beta of 0 and shouldn't contribute to beta-adjusted exposure
   - Confirmed that both calculation paths correctly exclude cash from beta-adjusted exposure

2. **Examining Option Calculations**:
   - Reviewed how option beta-adjusted exposure is calculated in both paths
   - No discrepancies found in the calculation methodology

3. **Checking for Rounding Issues**:
   - Verified that the discrepancy is too large to be explained by rounding differences

## Suggested Next Steps

1. **Add Debug Logging**:
   - Add detailed logging to both calculation paths to identify exactly where they diverge
   - Log intermediate values to pinpoint the source of the discrepancy

2. **Examine Test Portfolio Data**:
   - Analyze the test portfolio data to identify any unusual positions that might be handled differently
   - Check if any specific position types are included in one calculation but not the other

3. **Review Recent Changes**:
   - Carefully review all changes made during the SPY simulator implementation
   - Look for any modifications that might have affected how beta-adjusted exposure is calculated

4. **Ensure Consistent Methodology**:
   - Once the source of the discrepancy is identified, update the code to ensure both calculation paths use the same methodology
   - Add comments to clarify the expected behavior

## References

- [SPY Simulator Handoff](docs/devlog/2025-04-25-spy-simulator-handoff.md) - Initial work that led to this issue
- [Options Concepts Documentation](docs/options.md) - Explanation of options concepts and calculations
