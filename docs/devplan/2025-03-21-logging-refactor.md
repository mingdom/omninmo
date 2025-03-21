# Logging Refactor Plan

## Overview
Improve logging and error handling in the codebase to provide cleaner output while maintaining proper error handling principles.

## Current Issues
1. Too many INFO-level logs cluttering output
2. Warnings being used where errors might be more appropriate
3. Some errors being swallowed with just logs instead of proper error handling
4. Inconsistent logging levels across the application

## Logging Principles

### ERROR Level
- Critical failures that prevent operation
- Unrecoverable errors that require user intervention
- Should throw exceptions rather than just log
- Examples:
  - Model not loaded
  - Required data missing
  - Feature calculation failures

### WARNING Level
- Recoverable issues that might affect quality
- Missing optional features/data
- Performance degradation
- Examples:
  - Using fallback data source
  - Missing optional features
  - Performance below threshold

### INFO Level
- Major state changes
- Final results/summaries
- Key configuration changes
- Examples:
  - Model loaded successfully
  - Prediction results summary
  - Configuration changes

### DEBUG Level
- Detailed progress updates
- Feature calculation details
- Data processing steps
- Examples:
  - Processing individual tickers
  - Feature generation progress
  - Data fetching details

## Implementation Plan

### 1. Create Custom Exceptions
Create `src/v2/exceptions.py` with:
```python
class ModelError(Exception):
    """Base class for model-related exceptions"""
    pass

class ModelNotLoadedError(ModelError):
    """Raised when attempting to use an unloaded model"""
    pass

class InsufficientDataError(ModelError):
    """Raised when there is not enough data for prediction"""
    pass

class FeatureGenerationError(ModelError):
    """Raised when feature generation fails"""
    pass
```

### 2. Update Console App
Modify `src/v2/console_app.py`:
- Move progress updates to DEBUG level
- Throw exceptions for critical errors
- Add more context to error messages
- Improve error handling structure

Example changes:
```python
# Before
logger.warning(f"Insufficient data for {ticker}")

# After
logger.debug(f"Checking data sufficiency for {ticker}")
if df is None or len(df) < MIN_DATA_DAYS:
    raise InsufficientDataError(
        f"Insufficient data for {ticker}. "
        f"Required: {MIN_DATA_DAYS} days, Got: {len(df) if df is not None else 0} days"
    )
```

### 3. Update Documentation
- Add error handling section to docs
- Document logging levels and when to use them
- Add examples of proper error handling

### 4. Add Tests
Create tests for:
- Error cases
- Logging level verification
- Exception handling

## Success Criteria
1. Cleaner console output with progress at DEBUG level
2. Clear error messages when things go wrong
3. Proper exception handling instead of swallowed errors
4. Consistent logging levels across the application

## Migration Plan
1. Create exceptions.py
2. Update console_app.py logging
3. Update related modules
4. Add tests
5. Update documentation

## Rollback Plan
Keep old logging approach in a separate branch until new system is verified in production.

## Future Improvements
1. Add structured logging
2. Add log aggregation
3. Add error reporting
4. Add performance monitoring 