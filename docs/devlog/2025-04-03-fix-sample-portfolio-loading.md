# Fix for Sample Portfolio Loading Regression

**Date:** 2025-04-03  
**Author:** Dong Ming  
**Issue:** Sample portfolio loading functionality stopped working  
**Error:** `'NoneType' object has no attribute 'lower'`

## Root Cause Analysis

Using `git blame`, I identified that the regression was introduced in commit `dc84de08fc2044b7d5f59553c2bbb793c1823006` from April 3, 2025, titled "Fix import issues and align local development with Hugging Face deployment".

The commit added CSV security measures by implementing a new `validate_csv_upload` function in `src/folio/security.py`. This function was designed to validate and sanitize CSV uploads to protect against CSV injection attacks.

The regression occurred because:

1. The `validate_csv_upload` function required a non-null `filename` parameter and attempted to call `filename.lower()` without checking if `filename` was `None`.

2. The `load_sample_portfolio` function was updated to sanitize the sample portfolio data, but it only set the `contents` property of the upload component and not the `filename` property.

3. When the upload component's `contents` changed, it triggered the `update_portfolio_data` callback, which called `validate_csv_upload(contents, filename)` with `filename=None`, causing the error.

## Fix Implementation

The fix involved two changes:

1. Modified the `validate_csv_upload` function in `security.py` to handle the case when `filename` is `None`:
   ```python
   def validate_csv_upload(contents: str, filename: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[str]]:
       # Validate file extension if filename is provided
       if filename is not None and not filename.lower().endswith('.csv'):
           raise ValueError("Only CSV files are supported")
   ```

2. Updated the `load_sample_portfolio` callback in `app.py` to set both the `contents` and `filename` properties of the upload component:
   ```python
   @app.callback(
       [
           Output("upload-portfolio", "contents"),
           Output("upload-portfolio", "filename"),
       ],
       Input("load-sample", "n_clicks"),
       prevent_initial_call=True,
   )
   def load_sample_portfolio(n_clicks):
       # ...existing code...
       return f"data:{content_type};base64,{content_string}", "sample-portfolio.csv"
   ```

## Lessons Learned

1. **Defensive Programming**: Always check for `None` values before calling methods on parameters that could be `None`.

2. **Complete Component Updates**: When updating a component's state, ensure all relevant properties are set, especially when they depend on each other.

3. **Test Edge Cases**: The regression wasn't caught because the "Load Sample Portfolio" functionality wasn't tested after implementing the CSV security measures.

4. **Comprehensive Testing**: After making security-related changes, test all paths that could be affected, not just the direct use case.

## Prevention Strategies

1. **Add Unit Tests**: Create specific tests for the sample portfolio loading functionality.

2. **Parameter Validation**: Add explicit parameter validation at the beginning of functions.

3. **Documentation**: Document dependencies between component properties to make it clear that both `contents` and `filename` need to be set together.

4. **Code Review**: Ensure code reviews include checking for proper error handling and null checks.

This fix ensures that the "Load Sample Portfolio" functionality works correctly while maintaining the security benefits of the CSV validation and sanitization.
