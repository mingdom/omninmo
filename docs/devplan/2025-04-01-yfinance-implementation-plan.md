# YFinance Implementation Plan

**Date:** 2025-04-01
**Author:** Auggie
**Status:** Proposed

## Overview

This document outlines the plan to implement Yahoo Finance (yfinance) as an alternative to the Financial Modeling Prep (FMP) API for fetching financial data in the @src/folio/ project. The implementation will create a new utility module that mirrors the functionality of the existing DataFetcher class while ensuring compatibility with the rest of the codebase.

## Implementation Checklist

- [x] **Phase 1:** Create test suite for data fetching functionality
- [ ] **Phase 2:** Implement the yfinance adapter module
- [ ] **Phase 3:** Integrate with existing code
- [ ] **Phase 4:** Validate implementation with comprehensive tests
- [ ] **Phase 5:** Update documentation and clean up

## Feasibility Assessment

Based on research, this implementation is feasible for the following reasons:

1. **yfinance is already a dependency**: The project already includes yfinance in its requirements.txt and setup.py files, indicating it's already part of the project's dependencies.

2. **Similar API structure**: Both FMP API and yfinance provide historical price data with similar structures (OHLCV data), making the transition relatively straightforward.

3. **Existing data model compatibility**: The current code expects a pandas DataFrame with specific columns, which yfinance can provide with minimal transformation.

4. **Caching mechanism**: The current implementation includes a caching system that can be reused or adapted for yfinance data.

## Detailed Implementation Plan

### Phase 1: Create Test Suite for Data Fetching Functionality

1. **Create a test suite for the current DataFetcher**
   - Implement tests that verify the core functionality of the existing DataFetcher
   - Test the `fetch_data()` and `fetch_market_data()` methods with various inputs
   - Test caching behavior and error handling
   - Document the expected output format and structure

2. **Create a mock data source**
   - Implement a mock data source that can be used for testing both implementations
   - Ensure the mock data is consistent and representative of real-world data
   - Use this mock data to establish baseline behavior

3. **Define test cases for compatibility verification**
   - Create specific test cases that will be used to verify compatibility between implementations
   - Include edge cases like missing data, invalid tickers, and different time periods

### Phase 2: Implement the yfinance Adapter Module

1. **Create a new module: `src/yfinance.py`** (note: we are putting it in a higher level folder as this will likely be shared between projects)
   - Implement a `YFinanceDataFetcher` class that mirrors the interface of the current `DataFetcher` class
   - Ensure it provides the same core methods: `fetch_data()`, `fetch_market_data()`
   - Implement caching similar to the current implementation

2. **Implement data format compatibility**
   - Ensure column names match the expected format (e.g., 'Open', 'High', 'Low', 'Close', 'Volume')
   - Handle any differences in date formatting or index structure
   - Verify compatibility with the test cases defined in Phase 1

3. **Test the yfinance adapter in isolation**
   - Run the test suite created in Phase 1 against the new implementation
   - Verify that the output matches the expected format and structure
   - Fix any issues before proceeding to integration

### Phase 3: Integration with Existing Code

1. **Create an adapter interface**
   - Define a common interface that both data fetchers can implement
   - This will allow for easy switching between data sources and potential future additions

2. **Implement a factory for data fetcher selection**
   - Create a factory function that returns the appropriate data fetcher based on configuration
   - Allow for runtime selection between FMP and yfinance

3. **Create a configuration option for data source selection**
   - Add a configuration option to select the data source (FMP or yfinance)
   - Default to FMP for backward compatibility

### Phase 4: Validate Implementation with Comprehensive Tests

1. **Test beta calculation with yfinance data**
   - Verify that the beta calculation in `get_beta()` works correctly with the data format from yfinance
   - Compare beta values calculated using both data sources for a set of well-known tickers
   - Document any differences and ensure they are within acceptable ranges

2. **Test end-to-end functionality**
   - Test the entire portfolio analysis pipeline using yfinance as the data source
   - Verify that all functionality works as expected
   - Compare results with the FMP implementation to ensure consistency

3. **Performance testing**
   - Measure and compare the performance of both implementations
   - Identify any performance bottlenecks in the yfinance implementation
   - Optimize if necessary

### Phase 5: Documentation and Cleanup

1. **Update documentation**
   - Document the new module and its usage
   - Update any existing documentation that references the FMP API
   - Add examples of how to switch between data sources

2. **Clean up deprecated code**
   - Mark the old FMP API implementation as deprecated
   - Plan for eventual removal in a future release

3. **Create a migration guide**
   - Document the steps required to migrate from FMP to yfinance
   - Include any known differences or limitations

## Detailed Technical Specifications

### 1. YFinanceDataFetcher Class Design

```python
class YFinanceDataFetcher:
    """Class to fetch stock data from Yahoo Finance API using yfinance"""

    def __init__(self, cache_dir="cache"):
        """Initialize with cache directory"""
        self.cache_dir = cache_dir
        self.cache_ttl = 86400  # Default to 1 day if not specified

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_data(self, ticker, period="5y", interval="1d"):
        """
        Fetch stock data for a ticker from Yahoo Finance

        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with stock data
        """
        # Check cache first
        # If cache is valid, return cached data
        # Otherwise, fetch from yfinance
        # Format data to match expected structure
        # Save to cache
        # Return data

    def fetch_market_data(self, market_index="SPY", period="5y", interval="1d"):
        """
        Fetch market index data for beta calculations

        Args:
            market_index (str): Market index ticker symbol (default: 'SPY' for S&P 500 ETF)
            period (str): Time period ('1y', '5y', etc.)
            interval (str): Data interval ('1d', '1wk', etc.)

        Returns:
            pandas.DataFrame: DataFrame with market index data
        """
        # Simply call fetch_data with the market index ticker
        return self.fetch_data(market_index, period, interval)

    def _fetch_from_yfinance(self, ticker, period="5y"):
        """Fetch data from Yahoo Finance using yfinance"""
        # Use yfinance to fetch data
        # Format data to match expected structure
        # Return formatted data
```

### 2. Data Adapter Interface

```python
from abc import ABC, abstractmethod

class DataFetcherInterface(ABC):
    """Interface for data fetchers"""

    @abstractmethod
    def fetch_data(self, ticker, period="5y", interval="1d"):
        """Fetch stock data for a ticker"""
        pass

    @abstractmethod
    def fetch_market_data(self, market_index="SPY", period="5y", interval="1d"):
        """Fetch market index data for beta calculations"""
        pass
```

### 3. Factory for Data Fetcher Selection

```python
def create_data_fetcher(source="yfinance", cache_dir="cache"):
    """Factory function to create the appropriate data fetcher"""
    if source == "yfinance":
        from src.folio.utils.yfinance import YFinanceDataFetcher
        return YFinanceDataFetcher(cache_dir=cache_dir)
    elif source == "fmp":
        from src.v2.data_fetcher import DataFetcher
        return DataFetcher(cache_dir=cache_dir)
    else:
        raise ValueError(f"Unknown data source: {source}")
```

## Potential Challenges and Mitigations

1. **API Rate Limits**:
   - **Challenge**: yfinance may have different rate limits than FMP API
   - **Mitigation**: Implement robust caching and error handling to minimize API calls

2. **Data Format Differences**:
   - **Challenge**: Column names or data types might differ between APIs
   - **Mitigation**: Create adapter methods to transform data into a consistent format

3. **Historical Data Availability**:
   - **Challenge**: yfinance might have different historical data coverage
   - **Mitigation**: Implement fallback mechanisms for missing data

4. **Error Handling**:
   - **Challenge**: Different error types and scenarios from yfinance
   - **Mitigation**: Comprehensive error handling that maps yfinance errors to the expected error types

5. **Performance Considerations**:
   - **Challenge**: yfinance might have different performance characteristics
   - **Mitigation**: Optimize caching and implement performance monitoring

## Implementation Timeline

1. **Phase 1 (Create Test Suite)**: 2-3 days
   - Creating comprehensive tests for the existing DataFetcher
   - Establishing baseline behavior and expected outputs

2. **Phase 2 (Implement yfinance Adapter)**: 2-3 days
   - Implementing the core functionality
   - Ensuring data format compatibility
   - Initial testing against test suite

3. **Phase 3 (Integration)**: 1-2 days
   - Creating the adapter interface
   - Implementing the factory pattern
   - Adding configuration options

4. **Phase 4 (Comprehensive Testing)**: 2-3 days
   - Testing beta calculation with yfinance data
   - End-to-end testing of the portfolio analysis pipeline
   - Performance testing and optimization

5. **Phase 5 (Documentation and Cleanup)**: 1-2 days
   - Updating documentation
   - Creating migration guide
   - Marking deprecated code

Total estimated time: 8-13 days

Note: The timeline is extended compared to the original plan to account for the more thorough testing approach. This investment in testing will ensure a more reliable implementation and smoother transition between data sources.

## Conclusion

This plan outlines a comprehensive, test-driven approach to implementing yfinance as an alternative to the FMP API in the @src/folio/ project. By starting with a robust test suite for the existing functionality, we can ensure that the new implementation maintains compatibility with the existing codebase while providing the benefits of using yfinance for data fetching.

The phased approach allows for incremental testing and validation at each step, reducing the risk of integration issues and ensuring that the final implementation is reliable and performant. The modular design with interfaces and adapters will allow for easy switching between data sources and potential future additions.

By implementing a factory pattern and configuration options, we can provide a smooth transition path for users, allowing them to choose between data sources based on their specific needs. This approach also makes it easier to add additional data sources in the future if needed.
