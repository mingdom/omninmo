# Data Fetcher Error Handling Improvement - March 12, 2024

## Issue
The `DataFetcher` class was silently falling back to sample data when:
1. No API key was set
2. API request failed
3. API returned no data

This behavior violated our tenet of never hiding errors and working around them without permission.

## Changes Made
Modified the `fetch_data` method in `DataFetcher` class to:
1. Raise a `ValueError` when no API key is set, with clear instructions on how to fix it
2. Raise errors from API failures instead of silently falling back to sample data
3. Raise a `ValueError` when API returns no data
4. Only use sample data when explicitly requested via `force_sample=True`

## Impact
- Better error visibility: Users will now be immediately aware when there are API issues
- Explicit control: Users must explicitly choose to use sample data
- Easier debugging: Error messages provide clear guidance on how to fix issues

## Example Error Messages
```python
ValueError: No API key found. Please set the FMP_API_KEY environment variable or configure it in the config file. If you want to use sample data instead, explicitly set force_sample=True
```

## Prevention
- Added docstring to clearly document the error cases
- Error messages include actionable steps to resolve the issue 