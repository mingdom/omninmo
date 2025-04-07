# Development Plan: Price Data Model Refactoring

**Date:** 2025-04-06  
**Author:** Augment Agent  
**Status:** Draft  

## Overview

This development plan addresses critical issues in the portfolio data model related to price handling, which are causing several problems:

1. **Missing Current Price for Stocks**: StockPosition objects don't store current prices, only market exposure (price * quantity)
2. **Duplicate OptionPosition Classes**: Two different OptionPosition classes exist in the codebase, causing confusion
3. **Inaccurate Portfolio Simulations**: The SPY sensitivity chart appears linear because we can't properly calculate non-linear option behavior
4. **Inconsistent Price Updates**: The system doesn't properly update prices using data fetchers

These issues make it impossible to accurately simulate portfolio performance under different market conditions and may lead to incorrect exposure calculations.

## Current Implementation Analysis

### Files and Classes Involved

1. **Data Model Classes**:
   - `src/folio/data_model.py`: Contains the main data model classes used throughout the application
     - `Position`: Base class for all positions
     - `StockPosition`: Stores stock position data (missing current_price)
     - `OptionPosition`: Stores option position data (missing current_price)
     - `PortfolioGroup`: Groups stock and option positions by ticker
     - `PortfolioSummary`: Summarizes portfolio data

2. **Option Utilities**:
   - `src/folio/option_utils.py`: Contains option pricing and calculation utilities
     - `OptionPosition`: A separate class used for option calculations (has current_price)
     - `calculate_bs_price()`: Calculates option price using Black-Scholes
     - `calculate_option_delta()`: Calculates option delta
     - `calculate_implied_volatility()`: Calculates implied volatility

3. **Data Fetchers**:
   - `src/stockdata.py`: Interface and factory for data fetchers
     - `DataFetcherInterface`: Abstract base class for data fetchers
     - `create_data_fetcher()`: Factory function to create data fetchers
   - `src/yfinance.py`: Yahoo Finance data fetcher implementation
     - `YFinanceDataFetcher`: Fetches data from Yahoo Finance
   - `src/v2/data_fetcher.py`: Financial Modeling Prep data fetcher
     - `DataFetcher`: Fetches data from FMP API

4. **Portfolio Processing**:
   - `src/folio/portfolio.py`: Processes portfolio data from CSV
     - Reads "Last Price" from CSV
     - Calculates market_exposure as price * quantity
     - Creates StockPosition and OptionPosition objects
     - Does not store current_price in the objects

5. **Chart Data**:
   - `src/folio/chart_data.py`: Transforms portfolio data for charts
     - `transform_for_spy_sensitivity_chart()`: Attempts to simulate portfolio performance
     - Tries to access stock_position.current_price (which doesn't exist)
     - Falls back to linear approximations when price data is missing

### Key Issues

1. **StockPosition Missing current_price**:
   ```python
   # In src/folio/data_model.py
   @dataclass
   class StockPosition(Position):
       """Details of a stock position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float  # Quantity * Current Price (fetched at runtime)
       beta_adjusted_exposure: float  # Market Exposure * Beta
       # Missing current_price attribute
   ```

2. **Two Different OptionPosition Classes**:
   ```python
   # In src/folio/data_model.py
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float
       beta_adjusted_exposure: float
       strike: float
       expiry: str
       option_type: str
       delta: float
       delta_exposure: float
       notional_value: float
       underlying_beta: float
       # Missing current_price attribute
   ```

   ```python
   # In src/folio/option_utils.py
   class OptionPosition:
       """Option position for pricing calculations"""
       def __init__(
           self,
           underlying,
           expiry,
           strike,
           option_type,
           quantity=1,
           current_price=None,  # Has current_price attribute
           description=None,
       ):
           # ...
   ```

3. **Price Not Used from Data Fetchers**:
   - Data fetchers are initialized in `src/folio/utils.py`
   - They're used to calculate beta values but not to update current prices
   - When processing CSV data, the code uses "Last Price" from the CSV but doesn't store it

4. **SPY Sensitivity Chart Fallback**:
   ```python
   # In src/folio/chart_data.py
   if hasattr(group.stock_position, "current_price"):
       current_underlying_price = group.stock_position.current_price
   else:
       # Fallback to linear approximation
       # ...
   ```

## Proposed Solutions

### Option 1: Minimal Changes (Add current_price to Existing Classes)

1. **Update StockPosition and OptionPosition in data_model.py**:
   ```python
   @dataclass
   class StockPosition(Position):
       """Details of a stock position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float
       beta_adjusted_exposure: float
       current_price: float  # Add current_price attribute
   ```

   ```python
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       # Existing attributes...
       current_price: float  # Add current_price attribute
   ```

2. **Update Portfolio Processing**:
   ```python
   # In src/folio/portfolio.py
   stock_position = StockPosition(
       ticker=symbol,
       quantity=quantity,
       beta=beta,
       market_exposure=value,
       beta_adjusted_exposure=value * beta,
       current_price=price,  # Store the price
   )
   ```

3. **Add Price Update Method**:
   ```python
   # In src/folio/portfolio.py
   def update_prices(portfolio_groups, data_fetcher):
       """Update prices for all positions using the data fetcher"""
       for group in portfolio_groups:
           if group.stock_position:
               try:
                   # Fetch current price
                   stock_data = data_fetcher.fetch_data(group.ticker)
                   current_price = stock_data["Close"].iloc[-1]
                   
                   # Update stock position
                   group.stock_position.current_price = current_price
                   group.stock_position.market_exposure = current_price * group.stock_position.quantity
                   group.stock_position.beta_adjusted_exposure = group.stock_position.market_exposure * group.stock_position.beta
               except Exception as e:
                   logger.error(f"Error updating price for {group.ticker}: {e}")
   ```

### Option 2: Comprehensive Refactoring (Merge OptionPosition Classes)

1. **Create a Single OptionPosition Class**:
   ```python
   # In src/folio/data_model.py
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float
       beta_adjusted_exposure: float
       strike: float
       expiry: str
       option_type: str
       delta: float
       delta_exposure: float
       notional_value: float
       underlying_beta: float
       current_price: float  # Add current_price attribute
       implied_volatility: float = None  # Add IV attribute
       
       # Add methods from option_utils.OptionPosition
       def days_to_expiry(self):
           """Calculate days to expiry"""
           # ...
           
       def is_call(self):
           """Check if option is a call"""
           return self.option_type.upper() == "CALL"
       
       def is_put(self):
           """Check if option is a put"""
           return self.option_type.upper() == "PUT"
   ```

2. **Update Option Utilities**:
   ```python
   # In src/folio/option_utils.py
   # Remove the duplicate OptionPosition class
   # Update all functions to work with data_model.OptionPosition
   ```

3. **Add Price Update System**:
   ```python
   # In src/folio/portfolio.py
   def update_portfolio_prices(portfolio_summary, portfolio_groups, data_fetcher):
       """Update all prices in the portfolio using the data fetcher"""
       # Update stock prices
       for group in portfolio_groups:
           if group.stock_position:
               try:
                   # Fetch current price
                   stock_data = data_fetcher.fetch_data(group.ticker)
                   current_price = stock_data["Close"].iloc[-1]
                   
                   # Update stock position
                   group.stock_position.current_price = current_price
                   group.stock_position.market_exposure = current_price * group.stock_position.quantity
                   group.stock_position.beta_adjusted_exposure = group.stock_position.market_exposure * group.stock_position.beta
                   
                   # Update related option positions with new underlying price
                   for option in group.option_positions:
                       # Recalculate option values based on new underlying price
                       # ...
               except Exception as e:
                   logger.error(f"Error updating price for {group.ticker}: {e}")
       
       # Recalculate portfolio summary
       # ...
   ```

### Option 3: Property-Based Approach (Least Invasive)

1. **Add Properties to StockPosition**:
   ```python
   @dataclass
   class StockPosition(Position):
       """Details of a stock position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float
       beta_adjusted_exposure: float
       
       @property
       def current_price(self):
           """Calculate current price from market_exposure and quantity"""
           if self.quantity != 0:
               return self.market_exposure / self.quantity
           return 0.0
   ```

2. **Add Properties to OptionPosition**:
   ```python
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       # Existing attributes...
       
       @property
       def current_price(self):
           """Calculate current price from market_exposure and quantity"""
           if self.quantity != 0:
               return self.market_exposure / (100 * abs(self.quantity))
           return 0.0
   ```

3. **Update SPY Sensitivity Chart**:
   ```python
   # In src/folio/chart_data.py
   # Now we can always use group.stock_position.current_price
   # and option.current_price
   ```

## Recommended Approach

I recommend **Option 2: Comprehensive Refactoring** for the following reasons:

1. **Solves All Issues**: Addresses all identified problems in a comprehensive way
2. **Eliminates Duplication**: Removes the confusing duplicate OptionPosition class
3. **Improves Maintainability**: Makes the codebase more consistent and easier to understand
4. **Enables Accurate Simulations**: Allows for proper non-linear option behavior in simulations
5. **Supports Real-Time Updates**: Provides a mechanism to update prices using data fetchers

While this approach requires more changes, it provides a more robust and maintainable solution that will prevent similar issues in the future.

## Implementation Plan

### Phase 1: Add current_price to Data Model

1. Update `StockPosition` and `OptionPosition` in `data_model.py` to include current_price
2. Update portfolio processing in `portfolio.py` to store current_price
3. Update tests to reflect the new attributes

### Phase 2: Merge OptionPosition Classes

1. Move methods from `option_utils.OptionPosition` to `data_model.OptionPosition`
2. Update all functions in `option_utils.py` to work with the merged class
3. Remove the duplicate `OptionPosition` class from `option_utils.py`
4. Update tests to use the merged class

### Phase 3: Add Price Update System

1. Implement `update_portfolio_prices()` function in `portfolio.py`
2. Add UI controls to trigger price updates
3. Update the SPY sensitivity chart to use the new price data
4. Add tests for the price update system

### Phase 4: Testing and Documentation

1. Test all changes thoroughly
2. Update documentation to reflect the new data model
3. Create a devlog documenting the changes and their impact

## Risks and Mitigations

1. **Risk**: Breaking existing functionality
   **Mitigation**: Comprehensive test coverage before and after changes

2. **Risk**: Performance impact from frequent price updates
   **Mitigation**: Implement caching and throttling in the data fetchers

3. **Risk**: Increased complexity in the data model
   **Mitigation**: Clear documentation and consistent naming conventions

## Conclusion

The proposed refactoring will address critical issues in the portfolio data model related to price handling. By adding current_price to the data model, merging the duplicate OptionPosition classes, and implementing a price update system, we can enable accurate portfolio simulations and improve the overall reliability of the application.

This is a significant change that touches core components of the system, but the benefits in terms of accuracy, maintainability, and user experience justify the effort.
