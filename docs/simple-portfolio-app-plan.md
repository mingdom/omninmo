# Simple Portfolio Analysis App Plan

**Date:** 2025-04-10
**Author:** Augment Agent
**Status:** Draft

## 1. Project Overview

### 1.1 Background

The current Folio portfolio analysis application has grown complex with numerous features and maintenance challenges. Key issues include:

- Data fetching inconsistencies leading to calculation errors
- Complex caching mechanisms causing data alignment problems
- Special case handling for certain securities (e.g., SPY beta calculation)
- Overly complex data model with deprecated fields and backward compatibility
- Insufficient testing, particularly for integration scenarios

This plan outlines a green-field approach to create a simpler, more maintainable portfolio analysis application that focuses on the core functionality of exposure and risk analysis.

### 1.2 Core Objectives

1. Create a simplified portfolio analysis tool that focuses on exposure and risk metrics
2. Leverage third-party libraries for financial calculations to improve reliability
3. Provide real-time analysis of portfolio data without caching API calls
4. Maintain a clean, modular codebase with clear separation of concerns
5. Ensure comprehensive testing, particularly for critical calculations

## 2. Current Project Analysis

### 2.1 Core Functionality

The current Folio application provides:

1. **Portfolio Data Loading**: Parses CSV files exported from brokerages
2. **Exposure Analysis**: Calculates market exposure for stocks and options
3. **Risk Metrics**: Computes beta and beta-adjusted exposure
4. **Option Analysis**: Calculates option delta and exposure
5. **Portfolio Visualization**: Displays exposure breakdowns and risk metrics
6. **Price Updates**: Fetches current market prices for portfolio positions

### 2.2 Key Issues

1. **Data Fetching Inconsistencies**: Different cache files for the same ticker when called through different methods
2. **Beta Calculation Issues**: SPY shows a beta of ~0.9 instead of exactly 1.0
3. **Complex Data Model**: Many deprecated fields and backward compatibility layers
4. **Insufficient Testing**: Tests use mocked data that doesn't catch real-world issues
5. **Option Metrics Recalculation**: Issues with delta calculations after price updates
6. **Complex Caching**: Leading to data inconsistencies and alignment problems

## 3. Third-Party Library Analysis

### 3.1 Data Fetching Libraries

#### 3.1.1 yfinance

**Recommendation**: Use as primary data source

- **Pros**: Simple API, good documentation, active maintenance, free
- **Cons**: Rate limits, occasional API changes
- **Usage**: Direct data fetching without caching for consistency

#### 3.1.2 pandas-datareader

**Recommendation**: Secondary option if needed

- **Pros**: Supports multiple data sources, pandas integration
- **Cons**: Limited to data fetching, no financial calculations
- **Usage**: Alternative data source if yfinance has issues

### 3.2 Financial Calculation Libraries

#### 3.2.1 PyPortfolioOpt

**Recommendation**: Primary library for portfolio optimization

- **Pros**: Well-documented, actively maintained, clean API, various optimization methods
- **Cons**: Limited options analysis capabilities
- **Usage**: Portfolio optimization, efficient frontier analysis, risk-based allocation

#### 3.2.2 QuantStats

**Recommendation**: Primary library for performance and risk analytics

- **Pros**: Comprehensive metrics, excellent visualization, easy-to-use API, HTML reports
- **Cons**: Limited portfolio optimization capabilities
- **Usage**: Performance reporting, risk analysis, visualization

#### 3.2.3 empyrical

**Recommendation**: Core library for risk metrics

- **Pros**: Focused on risk metrics, clean API, well-tested, lightweight
- **Cons**: Requires specific data formats, no visualization
- **Usage**: Beta calculations, Sharpe ratio, other risk metrics

#### 3.2.4 Riskfolio-Lib

**Recommendation**: Advanced risk-based portfolio construction

- **Pros**: Comprehensive risk measures (24+), hierarchical risk approaches, excellent documentation
- **Cons**: Steeper learning curve, more complex API
- **Usage**: Advanced portfolio construction, risk parity, hierarchical risk allocation

#### 3.2.5 QuantLib-Python

**Recommendation**: Use for advanced options calculations only

- **Pros**: Industry-standard, comprehensive options models
- **Cons**: Complex API, steep learning curve
- **Usage**: Advanced options pricing and Greeks if needed

### 3.3 Visualization Libraries

#### 3.3.1 Plotly/Dash

**Recommendation**: Continue using for interactive UI

- **Pros**: Interactive, web-based, good documentation
- **Cons**: Can be complex for simple visualizations
- **Usage**: Main UI framework

#### 3.3.2 Matplotlib/Seaborn

**Recommendation**: Use for static visualizations

- **Pros**: Simple API, extensive customization
- **Cons**: Not interactive by default
- **Usage**: Static charts and reports

## 4. MVP Architecture

### 4.1 Core Components

1. **Data Loader**: Parse portfolio CSV files
2. **Market Data Provider**: Fetch real-time market data
3. **Portfolio Analyzer**: Calculate exposure and risk metrics
4. **Option Calculator**: Compute option Greeks and exposure
5. **Visualization Engine**: Display portfolio analysis
6. **Web Interface**: Interactive dashboard

### 4.2 Data Flow

1. User uploads portfolio CSV or loads from file
2. System parses portfolio data into a clean data model
3. System fetches current market data for all positions
4. System calculates exposure and risk metrics
5. System displays analysis in interactive dashboard
6. User can update prices or modify portfolio data

### 4.3 Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: Dash
- **Data Processing**: pandas, numpy
- **Financial Calculations**: PyPortfolioOpt, QuantStats, empyrical, Riskfolio-Lib
- **Data Fetching**: yfinance
- **Visualization**: Plotly
- **Testing**: pytest
- **Deployment**: Docker, Hugging Face Spaces

## 5. Implementation Plan

### 5.1 Phase 1: Core Data Model and Fetching

1. Create simplified data model classes
   - Position (base class)
   - StockPosition
   - OptionPosition
   - Portfolio

2. Implement market data provider using yfinance
   - Direct API calls without caching
   - Error handling and fallbacks
   - Integration with empyrical for beta calculations

3. Create portfolio loader
   - CSV parsing with robust error handling
   - Support for common brokerage formats
   - Validation and data cleaning

### 5.2 Phase 2: Analysis Engine

1. Implement portfolio analyzer
   - Exposure calculations (long, short, net)
   - Risk metrics using empyrical and QuantStats
   - Portfolio optimization using PyPortfolioOpt
   - Advanced risk analysis using Riskfolio-Lib when needed

2. Create option calculator
   - Delta calculations using Black-Scholes
   - Option exposure analysis
   - Integration with portfolio analyzer

3. Develop test suite
   - Unit tests for all components
   - Integration tests with real data
   - Regression tests for known issues

### 5.3 Phase 3: User Interface

1. Create dashboard layout
   - Summary cards
   - Exposure breakdown charts
   - Position details table

2. Implement interactive features
   - Price updates
   - Portfolio filtering
   - Drill-down analysis

3. Add data export functionality
   - CSV export
   - PDF reports
   - Data visualization export

### 5.4 Phase 4: Deployment and Documentation

1. Set up Docker deployment
   - Multi-stage build for efficiency
   - Environment configuration
   - Hugging Face Spaces integration

2. Create comprehensive documentation
   - User guide
   - API documentation
   - Calculation methodology

3. Implement monitoring and logging
   - Error tracking
   - Usage statistics
   - Performance monitoring

## 6. Data Model Design

### 6.1 Position (Base Class)

```python
@dataclass
class Position:
    ticker: str
    quantity: float
    price: float
    position_type: Literal["stock", "option"]

    @property
    def market_exposure(self) -> float:
        """Calculate market exposure (quantity * price)"""
        return self.quantity * self.price
```

### 6.2 StockPosition

```python
@dataclass
class StockPosition(Position):
    beta: float = 1.0

    def __post_init__(self):
        self.position_type = "stock"

    @property
    def beta_adjusted_exposure(self) -> float:
        """Calculate beta-adjusted exposure"""
        return self.market_exposure * self.beta
```

### 6.3 OptionPosition

```python
@dataclass
class OptionPosition(Position):
    underlying: str
    strike: float
    expiry: datetime
    option_type: Literal["CALL", "PUT"]
    delta: float = 0.0
    underlying_price: float = 0.0
    underlying_beta: float = 1.0

    def __post_init__(self):
        self.position_type = "option"

    @property
    def notional_value(self) -> float:
        """Calculate notional value (100 * underlying_price * abs(quantity))"""
        return 100 * self.underlying_price * abs(self.quantity)

    @property
    def delta_exposure(self) -> float:
        """Calculate delta exposure (delta * notional_value * sign(quantity))"""
        return self.delta * self.notional_value * (1 if self.quantity > 0 else -1)

    @property
    def beta_adjusted_exposure(self) -> float:
        """Calculate beta-adjusted exposure"""
        return self.delta_exposure * self.underlying_beta
```

### 6.4 Portfolio

```python
@dataclass
class Portfolio:
    positions: list[Position]
    cash: float = 0.0

    @property
    def stock_positions(self) -> list[StockPosition]:
        """Get all stock positions"""
        return [p for p in self.positions if isinstance(p, StockPosition)]

    @property
    def option_positions(self) -> list[OptionPosition]:
        """Get all option positions"""
        return [p for p in self.positions if isinstance(p, OptionPosition)]

    @property
    def net_exposure(self) -> float:
        """Calculate net market exposure"""
        return sum(p.market_exposure for p in self.positions)

    @property
    def beta_adjusted_exposure(self) -> float:
        """Calculate beta-adjusted exposure"""
        return sum(
            p.beta_adjusted_exposure
            for p in self.positions
            if hasattr(p, "beta_adjusted_exposure")
        )

    @property
    def portfolio_beta(self) -> float:
        """Calculate portfolio beta"""
        if self.net_exposure == 0:
            return 0.0
        return self.beta_adjusted_exposure / self.net_exposure
```

## 7. API Design

### 7.1 Market Data API

```python
class MarketDataProvider:
    """Provider for market data"""

    def get_current_price(self, ticker: str) -> float:
        """Get current price for a ticker"""
        pass

    def get_historical_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data for a ticker"""
        pass

    def get_beta(self, ticker: str, market_index: str = "SPY") -> float:
        """Calculate beta for a ticker against market index"""
        pass

    def get_option_data(self, ticker: str) -> dict:
        """Get option chain data for a ticker"""
        pass
```

### 7.2 Portfolio Loader API

```python
class PortfolioLoader:
    """Loader for portfolio data"""

    def load_from_csv(self, file_path: str) -> Portfolio:
        """Load portfolio from CSV file"""
        pass

    def load_from_dataframe(self, df: pd.DataFrame) -> Portfolio:
        """Load portfolio from pandas DataFrame"""
        pass

    def save_to_csv(self, portfolio: Portfolio, file_path: str) -> None:
        """Save portfolio to CSV file"""
        pass
```

### 7.3 Portfolio Analyzer API

```python
class PortfolioAnalyzer:
    """Analyzer for portfolio data"""

    def calculate_exposure_breakdown(self, portfolio: Portfolio) -> dict:
        """Calculate exposure breakdown"""
        pass

    def calculate_risk_metrics(self, portfolio: Portfolio) -> dict:
        """Calculate risk metrics"""
        pass

    def update_prices(self, portfolio: Portfolio) -> Portfolio:
        """Update prices for all positions"""
        pass

    def calculate_option_metrics(self, portfolio: Portfolio) -> Portfolio:
        """Calculate option metrics"""
        pass
```

## 8. Testing Strategy

### 8.1 Unit Tests

- Test each component in isolation
- Mock external dependencies
- Focus on edge cases and error handling

### 8.2 Integration Tests

- Test components together
- Use real data for critical calculations
- Verify end-to-end workflows

### 8.3 Regression Tests

- Test for known issues from the current application
- Ensure fixes for SPY beta calculation
- Verify option exposure calculations

### 8.4 Performance Tests

- Test with large portfolios
- Measure response times
- Identify bottlenecks

## 9. Deployment Strategy

### 9.1 Local Development

- Docker Compose for local development
- Hot reloading for rapid iteration
- Development-specific configuration

### 9.2 Production Deployment

- Docker container for portability
- Hugging Face Spaces for hosting
- Environment variables for configuration

### 9.3 CI/CD Pipeline

- Automated testing on push
- Build and deploy on merge to main
- Version tagging for releases

## 10. Timeline and Milestones

### 10.1 Phase 1: Core Data Model and Fetching (2 weeks)

- Week 1: Data model and market data provider
- Week 2: Portfolio loader and initial tests

### 10.2 Phase 2: Analysis Engine (3 weeks)

- Week 3: Portfolio analyzer and basic metrics
- Week 4: Option calculator and integration
- Week 5: Comprehensive test suite

### 10.3 Phase 3: User Interface (2 weeks)

- Week 6: Dashboard layout and basic visualizations
- Week 7: Interactive features and data export

### 10.4 Phase 4: Deployment and Documentation (1 week)

- Week 8: Docker setup, documentation, and final testing

## 11. Conclusion

This green-field project plan outlines a path to create a simpler, more maintainable portfolio analysis application that focuses on the core functionality of exposure and risk analysis. By leveraging third-party libraries for financial calculations and adopting a clean, modular architecture, the new application will avoid the issues that have plagued the current implementation.

The MVP will provide the essential features needed for portfolio analysis while establishing a solid foundation for future enhancements. The emphasis on real-time data fetching without caching will ensure consistency in calculations, addressing one of the major pain points in the current application.

With a comprehensive testing strategy and clear documentation, the new application will be more reliable and easier to maintain, providing a better experience for both users and developers.
