# Price Update Issues Report

This document summarizes issues identified during the investigation of price update functionality and beta calculation in the Folio application.

## Issues Identified

### 1. SPY Beta Calculation Issue

**Problem**: SPY (the S&P 500 ETF) shows a beta of approximately 0.9 in the application, when it should be exactly 1.0 since it's the benchmark against which other securities' betas are calculated.

**Root Cause Analysis**:
- When calculating SPY's beta, we call `fetch_data("SPY")` for the stock data and `fetch_market_data()` (which also fetches SPY) for the market data
- These two calls create separate cache files and can result in slightly different data
- The correlation between SPY and the market index was very high (0.9906) but not exactly 1.0
- There were small differences in the data, particularly on 2025-04-09
- This resulted in a calculated beta of 0.8962 instead of 1.0

**Potential Solutions**:
- Investigate why the data fetched for SPY as a stock and SPY as the market index are different
- Ensure that the same data source and time period are used for both calculations
- Consider using a third-party library for beta calculations (see recommendations below)

**Status**: Identified but not properly fixed. Current implementation uses a correlation check to set SPY's beta to 1.0 when the correlation is high, which is a workaround rather than addressing the root cause.

### 2. Data Fetching Inconsistencies

**Problem**: The data fetcher creates separate cache files for the same ticker when called through different methods (`fetch_data` vs `fetch_market_data`).

**Root Cause Analysis**:
- The `fetch_market_data` method simply calls `fetch_data` with the market index ticker
- However, each call creates its own cache file, which can lead to inconsistencies
- API responses might differ slightly at different times
- Data alignment issues can occur when joining the datasets

**Potential Solutions**:
- Modify the data fetcher to use a consistent caching mechanism
- Ensure that when calculating beta for a ticker against itself, the exact same data is used
- Implement a more robust data alignment strategy

**Status**: Identified but not properly fixed.

### 3. Beta Calculation Precision Issues

**Problem**: Beta calculations are sensitive to small differences in data, leading to unexpected results.

**Root Cause Analysis**:
- The beta calculation formula (covariance / variance) is sensitive to small differences in the input data
- Numerical precision issues can affect the calculation
- Different data alignment strategies can lead to different results

**Potential Solutions**:
- Implement more robust data alignment and preprocessing
- Use a third-party library for beta calculations
- Add more comprehensive tests with real data

**Status**: Identified but not properly fixed.

### 4. Insufficient Integration Testing

**Problem**: The existing tests for beta calculation use mocked data that guarantees the expected result, which doesn't catch real-world issues.

**Root Cause Analysis**:
- The test `test_market_benchmark` in `tests/test_beta.py` uses identical data for both the stock and the market
- This ensures that the beta calculation will result in a value very close to 1.0
- However, it doesn't test the actual data fetching and alignment logic

**Potential Solutions**:
- Create more comprehensive integration tests that use real data
- Test edge cases and potential failure modes
- Implement a test data cache to ensure consistent test results

**Status**: Partially addressed with the creation of integration tests, but more comprehensive testing is needed.

### 5. Option Metrics Recalculation Issues

**Problem**: Option exposures weren't being recalculated correctly after price updates.

**Root Cause Analysis**:
- The `recalculate_option_metrics` function in `option_utils.py` had issues with how it handled delta calculations
- Option exposure calculations need to be consistent with the rest of the application

**Potential Solutions**:
- Ensure consistent delta calculation methodology
- Improve error handling and logging
- Add more comprehensive tests

**Status**: Fixed in recent commits (f5b9193).

### 6. Portfolio Estimate Value Calculation

**Problem**: Portfolio estimate value was calculated incorrectly, not including cash-like positions.

**Root Cause Analysis**:
- The portfolio summary calculation didn't properly account for cash-like positions
- This led to inaccurate portfolio metrics after price updates

**Potential Solutions**:
- Ensure all position types are properly included in portfolio calculations
- Improve documentation of calculation methodologies
- Add more comprehensive tests

**Status**: Fixed in recent commits (f5b9193).

### 7. Option Symbol Parsing

**Problem**: Option symbols in format '-AMAT250516P130' weren't being parsed correctly.

**Root Cause Analysis**:
- The option symbol parsing logic didn't handle all possible formats
- This led to issues with option position identification and metrics calculation

**Potential Solutions**:
- Implement more robust option symbol parsing
- Add support for different option symbol formats
- Improve error handling and logging

**Status**: Fixed in recent commits (f5b9193).

## Third-Party Libraries for Financial Calculations

### 1. pandas-datareader

**Description**: A library that provides data extraction from various Internet sources into pandas DataFrames.

**Advantages**:
- Built-in support for fetching data from Yahoo Finance, Google Finance, etc.
- Integrates well with pandas for data manipulation
- Active maintenance and community support

**Disadvantages**:
- Limited to data fetching, doesn't provide financial calculations
- Can be affected by changes in the underlying APIs

**Recommendation**: Could be used to replace our custom data fetching logic, but would still require custom calculation code.

### 2. pyfolio

**Description**: A Python library for performance and risk analysis of financial portfolios.

**Advantages**:
- Comprehensive portfolio analysis tools
- Built-in beta calculation and risk metrics
- Developed by Quantopian (now part of Robinhood)
- Well-documented and tested

**Disadvantages**:
- May be more complex than needed for our use case
- Requires specific data formats

**Recommendation**: Strong candidate for replacing our custom portfolio analysis code, especially for risk metrics like beta.

### 3. QuantLib-Python

**Description**: Python bindings for QuantLib, a comprehensive quantitative finance library.

**Advantages**:
- Industry-standard library for quantitative finance
- Comprehensive options pricing and risk models
- Highly accurate and well-tested

**Disadvantages**:
- Complex API with a steep learning curve
- May be overkill for simple calculations
- Installation can be challenging

**Recommendation**: Good option for advanced options calculations, but may be too complex for basic beta calculations.

### 4. ffn (Financial Functions for Python)

**Description**: A financial function library for Python.

**Advantages**:
- Simple API for common financial calculations
- Built-in beta calculation and other risk metrics
- Good integration with pandas

**Disadvantages**:
- Less comprehensive than some alternatives
- Not as actively maintained as some other libraries

**Recommendation**: Good lightweight option for replacing our beta calculation code.

### 5. empyrical

**Description**: Common financial risk and performance metrics.

**Advantages**:
- Focused specifically on risk and performance metrics
- Clean API and good documentation
- Used by pyfolio and other financial libraries

**Disadvantages**:
- Limited to risk and performance metrics
- Requires specific data formats

**Recommendation**: Excellent option for replacing our beta calculation code with a well-tested implementation.

## Conclusion

The price update functionality in the Folio application has several issues that need to be addressed. The most critical issue is the SPY beta calculation, which should be exactly 1.0 but is currently showing as approximately 0.9. This issue stems from inconsistencies in data fetching and alignment, rather than a fundamental problem with the beta calculation formula.

Rather than implementing workarounds, we should focus on addressing the root causes of these issues. This may involve refactoring the data fetching logic, improving data alignment strategies, and potentially leveraging third-party libraries for financial calculations.

Of the third-party libraries evaluated, empyrical and pyfolio stand out as strong candidates for replacing our custom beta calculation code. These libraries provide well-tested implementations of financial risk metrics and would likely resolve the issues we're experiencing with beta calculations.

Next steps should include:
1. Conducting a more thorough investigation of the data fetching inconsistencies
2. Evaluating empyrical and pyfolio for integration into the application
3. Implementing more comprehensive integration tests
4. Refactoring the data model to ensure consistent handling of all position types
