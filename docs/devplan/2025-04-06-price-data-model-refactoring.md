# Development Plan: Price Data Model Refactoring

**Date:** 2025-04-06
**Author:** Augment Agent
**Status:** In Progress

## Implementation Status

### Current Approach
The implementation is following **Option 1: Minimal Changes** from the proposed solutions, which adds the price attribute to the existing classes. The more comprehensive Option 2 approach with price update mechanism has been implemented in Phase 2 and Phase 3.

### Completed (PR #3)
- [x] Add `price` attribute to `StockPosition` class with default value of 0.0
- [x] Add `price` attribute to `OptionPosition` class with default value of 0.0
- [x] Update constructors to accept `price` parameter
- [x] Update `to_dict()` and `from_dict()` methods to handle the price attribute
- [x] Update portfolio processing in `portfolio.py` to store price when creating positions
- [x] Update tests to include price in test cases
- [x] Add debug mode for Dash app to help with troubleshooting

### Completed (Current Branch)
- [x] Add `price_updated_at` timestamp to `PortfolioSummary`
- [x] Update portfolio loading to set timestamp when prices are initially loaded
- [x] Implement price update mechanism using data fetchers
- [x] Add tests for the price update functionality

### Remaining
- [ ] Add UI components to trigger price updates and display last update time
- [ ] Update documentation to reflect the new data model
- [ ] Create a devlog documenting the changes and their impact

### Not Needed
- [x] Address the two different `OptionPosition` classes issue (they serve different purposes and don't need to be merged)


## Overview

This development plan addresses critical issues in the portfolio data model related to price handling, which are causing several problems:

1. **Missing Price for Positions**: StockPosition and OptionPosition objects don't store prices, only market exposure (price * quantity)
2. **Distinct OptionPosition Classes**: Two different OptionPosition classes exist for different purposes (calculations vs. data storage)
3. **No Price Update Mechanism**: The system doesn't update prices using data fetchers after initial loading

These issues may lead to incorrect exposure calculations when market prices change and make it difficult to implement features that require access to individual position prices.

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

1. **Missing Price Attribute in Data Model**:
   ```python
   # In src/folio/data_model.py
   @dataclass
   class StockPosition(Position):
       """Details of a stock position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float  # Quantity * Price (fetched at runtime)
       beta_adjusted_exposure: float  # Market Exposure * Beta
       # Missing price attribute
   ```

2. **Two Different OptionPosition Classes (Serving Different Purposes)**:
   ```python
   # In src/folio/data_model.py - Used for storing portfolio data
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       ticker: str
       quantity: int
       beta: float
       market_exposure: float  # price * quantity * 100
       beta_adjusted_exposure: float
       strike: float
       expiry: str
       option_type: str
       delta: float
       delta_exposure: float
       notional_value: float
       underlying_beta: float
       # Missing price attribute
   ```

   ```python
   # In src/folio/option_utils.py - Used for option pricing calculations
   @dataclass
   class OptionPosition:
       """Represents a single option position for pricing calculations"""
       underlying: str
       expiry: datetime
       strike: float
       option_type: str  # 'CALL' or 'PUT'
       quantity: int
       current_price: float  # Has current_price attribute
       description: str

       # Used for Black-Scholes calculations, delta calculations, etc.
       # Not used for storing portfolio data
   ```

3. **No Price Update Mechanism**:
   - Data fetchers are initialized in `src/folio/utils.py`
   - They're used to calculate beta values but not to update prices
   - When processing CSV data, the code uses "Last Price" from the CSV but doesn't store it
   - There's no mechanism to update prices after initial loading

## Proposed Solutions

### Option 1: Minimal Changes (Add price to Existing Classes)

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
       price: float  # Add price attribute
   ```

   ```python
   @dataclass
   class OptionPosition(Position):
       """Details of an option position"""
       # Existing attributes...
       price: float  # Add price attribute
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
       price=price,  # Store the price
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
                   new_price = stock_data["Close"].iloc[-1]

                   # Update stock position
                   group.stock_position.price = new_price
                   group.stock_position.market_exposure = new_price * group.stock_position.quantity
                   group.stock_position.beta_adjusted_exposure = group.stock_position.market_exposure * group.stock_position.beta
               except Exception as e:
                   logger.error(f"Error updating price for {group.ticker}: {e}")
   ```

### Option 2: Comprehensive Refactoring (Keep Separate OptionPosition Classes)

1. **Add price to data_model.OptionPosition**:
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
       price: float  # Add price attribute
       implied_volatility: float = None  # Add IV attribute for recalculations
   ```

2. **Keep option_utils.OptionPosition Separate**:
   ```python
   # In src/folio/option_utils.py
   # Keep the existing OptionPosition class for calculations
   # Update portfolio.py to store price in data_model.OptionPosition
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
                   new_price = stock_data["Close"].iloc[-1]

                   # Update stock position
                   group.stock_position.price = new_price
                   group.stock_position.market_exposure = new_price * group.stock_position.quantity
                   group.stock_position.beta_adjusted_exposure = group.stock_position.market_exposure * group.stock_position.beta

                   # Update related option positions with new underlying price
                   for option in group.option_positions:
                       # Create temporary option_utils.OptionPosition for calculations
                       temp_option = option_utils.OptionPosition(
                           underlying=group.ticker,
                           expiry=datetime.strptime(option.expiry, "%Y-%m-%d"),
                           strike=option.strike,
                           option_type=option.option_type,
                           quantity=option.quantity,
                           current_price=option.price,
                           description=f"{group.ticker} {option.expiry} {option.strike} {option.option_type}"
                       )

                       # Calculate new option price using Black-Scholes
                       new_option_price = calculate_bs_price(
                           option=temp_option,
                           underlying_price=new_price,
                           implied_volatility=option.implied_volatility
                       )

                       # Update data model option
                       option.price = new_option_price
                       option.market_exposure = new_option_price * 100 * abs(option.quantity)
                       if option.quantity < 0:  # Short position
                           option.market_exposure = -option.market_exposure

                       # Recalculate delta and delta exposure
                       new_delta = calculate_option_delta(
                           option=temp_option,
                           underlying_price=new_price
                       )
                       option.delta = new_delta
                       option.delta_exposure = new_delta * option.notional_value / 100
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
       def price(self):
           """Calculate price from market_exposure and quantity"""
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
       def price(self):
           """Calculate price from market_exposure and quantity"""
           if self.quantity != 0:
               return self.market_exposure / (100 * abs(self.quantity))
           return 0.0
   ```

3. **Update SPY Sensitivity Chart**:
   ```python
   # In src/folio/chart_data.py
   # Now we can always use group.stock_position.price
   # and option.price
   ```

## Recommended Approach

I recommend **Option 2: Comprehensive Refactoring (Keep Separate OptionPosition Classes)** for the following reasons:

1. **Solves All Issues**: Addresses all identified problems in a comprehensive way
2. **Respects Existing Design**: Maintains the separation between calculation and data storage classes
3. **Improves Maintainability**: Makes the codebase more consistent and easier to understand
4. **Supports Real-Time Updates**: Provides a mechanism to update prices using data fetchers

While this approach requires more changes than Option 3, it provides a more robust and maintainable solution that will prevent similar issues in the future. Option 1 is too minimal and doesn't address the price update mechanism, while Option 3 is a workaround that doesn't properly solve the underlying issue.

## Implementation Plan

### Phase 1: Add price to Data Model (COMPLETED in PR #3)

1. ✅ Update `StockPosition` and `OptionPosition` in `data_model.py` to include price
2. ✅ Update portfolio processing in `portfolio.py` to store price
3. ✅ Update tests to reflect the new attributes
4. ✅ Ensure all tests pass with `make test` and `make lint`


### Phase 2: Add Price Update Timestamp (COMPLETED)

1. ✅ Add `price_updated_at` timestamp to `PortfolioSummary` to track when prices were last updated
2. ✅ Update portfolio loading to set this timestamp when prices are initially loaded
3. ✅ Add tests for the timestamp functionality
4. ✅ Ensure all tests pass with `make test` and `make lint`

### Phase 3: Implement Price Update Mechanism (PARTIALLY COMPLETED)

1. ✅ Create a price update function that uses data fetchers to update prices
2. ❌ Add UI components to trigger price updates
3. ❌ Display last update time in the UI
4. ✅ Implement caching to prevent excessive API calls (using existing data fetcher caching)

### Phase 4: Testing and Documentation (PARTIALLY COMPLETED)

1. ✅ Test all changes thoroughly
2. ❌ Update documentation to reflect the new data model
3. ❌ Create a devlog documenting the changes and their impact

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
