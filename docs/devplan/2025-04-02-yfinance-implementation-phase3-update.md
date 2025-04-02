# YFinance Implementation Phase 3: Updated Plan

**Date:** 2025-04-02
**Author:** Auggie
**Status:** Proposed

## Overview

This document provides an updated plan for Phase 3 of the yfinance implementation, based on the insights gained from Phase 2. The main focus of Phase 3 is to integrate the YFinanceDataFetcher with the existing codebase, ensuring consistent behavior regardless of the data source.

## Key Findings from Phase 2

Our detailed analysis of the YFinanceDataFetcher implementation revealed several important insights:

1. **Date Range Differences**:
   - FMP data covers a much longer period (5 years) by default
   - YFinance data covers only 1 year by default
   - This leads to different beta values when using the full dataset

2. **Beta Calculation with Common Dates**:
   - When using the same date range, the beta values are very similar
   - The differences are less than 4% when using the same date range

3. **Price Differences**:
   - The price differences between the two data sources are minimal
   - Average differences are less than 1% for most tickers

4. **Benefits of Shorter Time Periods for Beta**:
   - Using a 6-month period for beta calculations provides a more current view of a stock's behavior
   - Market sentiment and cycles change over time, making recent data more relevant
   - For volatile stocks, the difference between 1-year and 6-month betas can be significant

## Updated Implementation Plan for Phase 3

### 1. Create a Common Data Fetcher Interface

```python
from abc import ABC, abstractmethod

class DataFetcherInterface(ABC):
    """Interface for data fetchers"""

    # Default period for beta calculations
    beta_period = "6m"

    @abstractmethod
    def fetch_data(self, ticker, period="1y", interval="1d"):
        """Fetch stock data for a ticker"""
        pass

    @abstractmethod
    def fetch_market_data(self, market_index="SPY", period=None, interval="1d"):
        """Fetch market index data for beta calculations

        If period is None, uses the class beta_period (6m by default).
        """
        pass
```

### 2. Update the Existing Data Fetchers to Implement the Interface

#### Update FMP DataFetcher

```python
from src.data_fetcher_interface import DataFetcherInterface

class DataFetcher(DataFetcherInterface):
    """Class to fetch stock data from Financial Modeling Prep API"""

    # Default period for beta calculations
    beta_period = "6m"

    # Existing initialization and fetch_data methods...

    def fetch_market_data(self, market_index="SPY", period=None, interval="1d"):
        """Fetch market index data for beta calculations"""
        # Use the class beta_period if period is None
        if period is None:
            period = self.beta_period
            logger.info(f"Using default beta period: {period}")

        # Call fetch_data with the market index ticker
        return self.fetch_data(market_index, period, interval)
```

#### Update YFinance DataFetcher

```python
from src.data_fetcher_interface import DataFetcherInterface

class YFinanceDataFetcher(DataFetcherInterface):
    """Class to fetch stock data from Yahoo Finance API using yfinance"""

    # Default period for beta calculations
    beta_period = "6m"

    # Existing initialization and fetch_data methods...

    def fetch_market_data(self, market_index="SPY", period=None, interval="1d"):
        """Fetch market index data for beta calculations"""
        # Use the class beta_period if period is None
        if period is None:
            period = self.beta_period
            logger.info(f"Using default beta period: {period}")

        # Call fetch_data with the market index ticker
        return self.fetch_data(market_index, period, interval)

    def _map_period_to_yfinance(self, period):
        """
        Map period string to yfinance format.

        Args:
            period (str): Period string ('1y', '5y', etc.)

        Returns:
            str: Period string in yfinance format
        """
        # yfinance accepts these period formats:
        # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

        # Check if period is already in yfinance format
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        if period in valid_periods:
            return period

        # Try to parse period
        if period.endswith('y'):
            try:
                years = int(period[:-1])
                if years == 1:
                    return '1y'
                elif years == 2:
                    return '2y'
                elif years <= 5:
                    return '5y'
                else:
                    return '10y'
            except ValueError:
                pass
        elif period.endswith('m'):
            try:
                months = int(period[:-1])
                if months <= 1:
                    return '1mo'
                elif months <= 3:
                    return '3mo'
                elif months <= 6:
                    return '6mo'
                else:
                    return '1y'
            except ValueError:
                pass

        # Default to 1y if period format is not recognized
        logger.warning(f"Unrecognized period format: {period}, defaulting to '1y'")
        return '1y'
```

### 3. Create a Factory for Data Fetcher Selection

```python
def create_data_fetcher(source="yfinance", cache_dir=None):
    """Factory function to create the appropriate data fetcher"""
    # Set default cache directories based on data source
    if cache_dir is None:
        cache_dir = ".cache_yf" if source == "yfinance" else ".cache_fmp"

    if source == "yfinance":
        from src.yfinance import YFinanceDataFetcher
        return YFinanceDataFetcher(cache_dir=cache_dir)
    elif source == "fmp":
        from src.v2.data_fetcher import DataFetcher
        return DataFetcher(cache_dir=cache_dir)
    else:
        raise ValueError(f"Unknown data source: {source}")
```

### 4. Update the Utils Module to Use the Factory

```python
import os
import yaml
from src.data_fetcher_factory import create_data_fetcher

# Load configuration from folio.yaml
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'folio.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

# Get configuration
config = load_config()

# Get data source from config (default to "yfinance" if not specified)
data_source = config.get("app", {}).get("data_source", "yfinance")

# Create data fetcher using factory
data_fetcher = create_data_fetcher(source=data_source)
```

### 5. Use a 6-Month Period for Beta Calculations

Based on our analysis, we've determined that a 6-month period is more appropriate for beta calculations as it better reflects current market conditions. We've already implemented this change in the YFinanceDataFetcher:

1. Added a class variable `beta_period = "6m"` to the YFinanceDataFetcher class
2. Modified the `fetch_market_data` method to use this period by default
3. Updated tests to verify this behavior

For Phase 3, we need to ensure this approach is consistently applied:

1. Update the DataFetcherInterface to specify a 6-month default period for beta calculations
2. Ensure both implementations use this default period
3. Add documentation explaining the rationale for using a shorter time period

### 6. Add Configuration Options

We've created a folio.yaml file in the src/folio directory with yfinance as the default data source:

```yaml
# Folio Application Configuration

app:
  # Data source configuration
  data_source: "yfinance"  # Options: "fmp", "yfinance"

  # Cache configuration
  cache:
    ttl: 86400  # Cache time-to-live in seconds (1 day)

  # Beta calculation configuration
  beta:
    period: "6m"  # Default period for beta calculations (6 months)

  # UI configuration
  ui:
    theme: "default"
    table_rows_per_page: 20

  # Logging configuration
  logging:
    level: "INFO"  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    file: "folio.log"
```

This configuration file will be loaded by the utils module and used to determine which data source to use. By default, yfinance will be used as the data source.

### 7. Update Documentation

Update the documentation to reflect the changes:

1. Add information about the data source configuration option
2. Document the differences between the two data sources
3. Provide guidance on when to use each data source

## Testing Strategy

The testing strategy for Phase 3 will focus on ensuring consistent behavior regardless of the data source:

1. **Interface Compliance**: Verify that both data fetchers implement the interface correctly
2. **Factory Tests**: Test the factory function with different data source options
3. **Integration Tests**: Test the integration with the existing codebase
4. **Beta Calculation Tests**: Verify that beta calculations produce consistent results with both data sources
5. **Configuration Tests**: Test the configuration options for selecting the data source

## Success Criteria

The implementation of Phase 3 will be considered successful when:

1. Both data fetchers implement the common interface
2. The factory function correctly creates the appropriate data fetcher
3. The utils module uses the factory to create the data fetcher based on config.yaml
4. YFinance is used as the default data source
5. Beta calculations use the 6-month period and produce consistent results
6. The configuration options in config.yaml work correctly
7. All tests pass with the new implementation

## Conclusion

This updated plan for Phase 3 addresses the key findings from Phase 2, ensuring consistent behavior regardless of the data source. By implementing a common interface, a factory function, and using a 6-month period for beta calculations, we can provide a seamless experience for users regardless of which data source they choose to use.

The decision to use a 6-month period for beta calculations is based on our analysis showing that market sentiment and cycles change over time, making recent data more relevant for assessing a stock's current relationship with the market. This approach provides more accurate and actionable beta values, especially for volatile stocks.

With the creation of config.yaml and setting yfinance as the default data source, we're making a significant improvement to the application. YFinance offers several advantages over the FMP API, including:

1. No API key required, making it easier for new users to get started
2. More reliable data availability
3. Additional data like dividends and stock splits

While maintaining the option to use FMP API through configuration, making yfinance the default ensures that users get the best experience out of the box.
