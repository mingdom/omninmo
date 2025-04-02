# YFinance Implementation Phase 2: Detailed Plan

**Date:** 2025-04-02
**Author:** Auggie
**Status:** Proposed

## Overview

This document provides a detailed plan for Phase 2 of the yfinance implementation, which focuses on creating the yfinance adapter module. This plan builds on the insights gained from completing Phase 1 (comprehensive test suite development) and provides specific implementation details.

## Implementation Checklist

- [ ] Create the yfinance adapter module (`src/yfinance.py`)
- [ ] Implement data format compatibility
- [ ] Test the yfinance adapter in isolation
- [ ] Address performance considerations
- [ ] Document the implementation

## Detailed Implementation Plan

### 1. Create the yfinance Adapter Module

**File Structure:**
```
src/
  yfinance.py  # New module for yfinance adapter
```

**Implementation Details:**
- Create a new `YFinanceDataFetcher` class that implements the same interface as the current `DataFetcher` class
- The class should have the same initialization parameters for compatibility:
  - `cache_dir` parameter (default: "cache")
  - `cache_ttl` parameter (from config or default)
- No need for API key handling since yfinance doesn't require an API key

**Core Methods:**
- `fetch_data(ticker, period="1y", interval="1d")`: Fetch historical data for a specific ticker
- `fetch_market_data(market_index="SPY", period="1y", interval="1d")`: Fetch market index data for beta calculations
- Private helper methods as needed (e.g., `_fetch_from_yfinance`, `_get_cache_path`)

**Caching Implementation:**
- Reuse the same caching structure as the current implementation
- Cache files should be stored in the same format and location
- Implement the same cache TTL logic for consistency

### 2. Implement Data Format Compatibility

**Data Structure Alignment:**
- Based on our analysis of the FMP API data in Phase 1, ensure the yfinance data is transformed to match:
  - Column names must be capitalized: 'Open', 'High', 'Low', 'Close', 'Volume'
  - Date index must be named 'date'
  - Additional columns from yfinance should be preserved but not required
  - Handle any differences in date formatting (yfinance uses timezone-aware timestamps)

**Period Handling:**
- Implement the same period parsing logic as the current implementation
- Map period strings ('1y', '5y', etc.) to yfinance's period format
- Handle any differences in how yfinance interprets time periods

**Error Handling:**
- Implement consistent error handling that matches the current implementation
- Map yfinance-specific errors to the same error types used in the current implementation
- Ensure the same error messages are used for consistency

### 3. Test the yfinance Adapter in Isolation

**Testing Approach:**
- Create a new test file `tests/test_yfinance.py` that mirrors `tests/test_data_fetcher.py`
- Reuse the mock data and test fixtures from Phase 1
- Implement tests for all the same functionality as the current implementation

**Specific Tests:**
- Test initialization and configuration
- Test data fetching and caching
- Test error handling
- Test data format and structure
- Test period handling
- Test beta calculation

**Validation:**
- Compare the output of the yfinance adapter with the output of the current implementation
- Verify that the data structure is consistent
- Check that beta calculations produce similar results
- Ensure caching works correctly

### 4. Performance Considerations

**Benchmarking:**
- Measure the performance of the yfinance adapter compared to the current implementation
- Identify any performance bottlenecks
- Optimize if necessary

**Rate Limiting:**
- Implement rate limiting to avoid hitting yfinance API limits
- Add exponential backoff for retries if needed

### 5. Documentation

**Code Documentation:**
- Add comprehensive docstrings to all methods
- Document any differences between the yfinance adapter and the current implementation
- Include examples of usage

**Implementation Notes:**
- Document any challenges or decisions made during implementation
- Note any limitations of the yfinance API compared to FMP API

## Implementation Details

Based on our analysis in Phase 1, here's a detailed implementation plan for the `YFinanceDataFetcher` class:

```python
import os
import time
import pandas as pd
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class YFinanceDataFetcher:
    """Class to fetch stock data from Yahoo Finance API using yfinance"""

    def __init__(self, cache_dir="cache", cache_ttl=None):
        """
        Initialize the YFinanceDataFetcher.

        Args:
            cache_dir (str): Directory to store cached data
            cache_ttl (int, optional): Cache TTL in seconds. If None, uses config or default.
        """
        self.cache_dir = cache_dir

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        # Get cache TTL from config or use default (1 day)
        if cache_ttl is None:
            try:
                from src.v2.config import config
                self.cache_ttl = config.get("app.cache.ttl", 86400)
            except ImportError:
                self.cache_ttl = 86400
        else:
            self.cache_ttl = cache_ttl

    def fetch_data(self, ticker, period="1y", interval="1d"):
        """
        Fetch stock data for a ticker from Yahoo Finance.

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        # Check cache first
        cache_path = self._get_cache_path(ticker, period, interval)

        if os.path.exists(cache_path):
            # Check if cache is still valid
            cache_age = time.time() - os.path.getmtime(cache_path)
            if cache_age < self.cache_ttl:
                logger.info(f"Loading {ticker} data from cache")
                try:
                    return pd.read_csv(cache_path, index_col=0, parse_dates=True)
                except Exception as e:
                    logger.warning(f"Error reading cache for {ticker}: {e}")
                    # Continue to fetch from API
            else:
                logger.info(f"Cache for {ticker} is expired")

        # Fetch from yfinance
        try:
            logger.info(f"Fetching data for {ticker} from Yahoo Finance")
            df = self._fetch_from_yfinance(ticker, period, interval)

            # Save to cache
            df.to_csv(cache_path)

            return df
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")

            # Try to use expired cache as fallback
            if os.path.exists(cache_path):
                logger.warning(f"Using expired cache for {ticker} as fallback")
                try:
                    return pd.read_csv(cache_path, index_col=0, parse_dates=True)
                except Exception as cache_e:
                    logger.error(f"Error reading cache for {ticker}: {cache_e}")

            # Re-raise the original exception
            raise

    def fetch_market_data(self, market_index="SPY", period="1y", interval="1d"):
        """
        Fetch market index data for beta calculations.

        Args:
            market_index (str): Market index ticker symbol (default: 'SPY' for S&P 500 ETF)
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with market index data
        """
        # Simply call fetch_data with the market index ticker
        return self.fetch_data(market_index, period, interval)

    def _fetch_from_yfinance(self, ticker, period="1y", interval="1d"):
        """
        Fetch data from Yahoo Finance using yfinance.

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        # Map period to yfinance format if needed
        # yfinance already accepts '1y', '5y', etc.

        # Fetch data
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)

        if df.empty:
            raise ValueError(f"No historical data found for {ticker}")

        # Rename columns to match expected format
        df = df.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume',
            'Dividends': 'Dividends',
            'Stock Splits': 'Stock Splits'
        })

        # Ensure index is named 'date'
        df.index.name = 'date'

        # Convert timezone-aware timestamps to naive timestamps
        # This is important for compatibility with the current implementation
        df.index = df.index.tz_localize(None)

        return df

    def _get_cache_path(self, ticker, period, interval):
        """
        Get the path to the cache file for a ticker.

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period
            interval (str): Data interval

        Returns:
            str: Path to cache file
        """
        return os.path.join(self.cache_dir, f"{ticker}_{period}_{interval}.csv")
```

## Potential Challenges and Mitigations

Based on our analysis in Phase 1, here are some potential challenges and mitigations for Phase 2:

1. **Data Format Differences**:
   - **Challenge**: yfinance returns slightly different column names and data types
   - **Mitigation**: Implement a transformation layer to ensure consistent output format

2. **Date Handling**:
   - **Challenge**: yfinance returns timezone-aware timestamps, while FMP API returns naive timestamps
   - **Mitigation**: Convert timezone-aware timestamps to naive timestamps for compatibility

3. **Error Handling**:
   - **Challenge**: yfinance has different error types and messages
   - **Mitigation**: Map yfinance errors to the same error types used in the current implementation

4. **Rate Limiting**:
   - **Challenge**: yfinance may have different rate limits than FMP API
   - **Mitigation**: Implement robust caching and rate limiting to avoid hitting API limits

5. **Additional Data**:
   - **Challenge**: yfinance provides additional data like dividends and stock splits
   - **Mitigation**: Preserve this additional data but don't require it for compatibility

## Testing Strategy

The testing strategy for Phase 2 will leverage the comprehensive test suite created in Phase 1:

1. **Reuse Test Fixtures**: Use the same mock data and test fixtures from Phase 1
2. **Mirror Test Structure**: Create parallel test classes for the yfinance adapter
3. **Compare Results**: Directly compare the output of the yfinance adapter with the FMP API implementation
4. **Validate Beta Calculations**: Ensure beta calculations produce similar results with both implementations
5. **Test Edge Cases**: Test with various tickers, time periods, and error conditions

## Success Criteria

The implementation of Phase 2 will be considered successful when:

1. The yfinance adapter passes all the tests from Phase 1
2. Beta calculations produce results within an acceptable margin of error compared to the FMP API implementation
3. The adapter handles all error conditions gracefully
4. Performance is comparable to or better than the current implementation
5. The code is well-documented and follows project standards

## Conclusion

This detailed plan for Phase 2 builds on the insights gained from Phase 1 and provides a clear roadmap for implementing the yfinance adapter. The implementation will closely mirror the current DataFetcher class while addressing the specific challenges of using yfinance as the data source.

The comprehensive test suite created in Phase 1 will be invaluable for validating the yfinance implementation and ensuring compatibility with the existing codebase.
