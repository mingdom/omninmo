# Folio: Portfolio Dashboard

**Date: 2025-04-10**

## Overview

Folio is a web-based dashboard for analyzing and visualizing investment portfolios with a focus on risk metrics and exposure analysis. The application is designed to help investors understand their portfolio's risk profile, particularly through beta and options exposure calculations.

## Key Features

- **Portfolio Analysis**: Comprehensive metrics on portfolio value, beta, and exposure
- **Position Grouping**: Automatic grouping of stocks with their related options
- **Risk Metrics**: Beta and beta-adjusted exposure calculations for all positions
- **Options Analysis**: Delta exposure and other option-specific metrics
- **Interactive UI**: Filtering, sorting, and searching portfolio positions
- **Position Details**: Drill-down into specific positions for detailed analysis
- **CSV Import**: Support for uploading portfolio data from CSV exports (compatible with Fidelity exports)
- **Visualization**: Charts for exposure analysis and position size visualization
- **AI Integration**: AI-powered portfolio analysis and chat functionality

## Technical Architecture

### Core Components

1. **Data Model (`data_model.py`)**: 
   - Core data structures: `Position`, `StockPosition`, `OptionPosition`, `PortfolioGroup`, `PortfolioSummary`, `ExposureBreakdown`
   - Serialization/deserialization for Dash callbacks

2. **Portfolio Processing (`portfolio.py`)**: 
   - CSV data processing and position grouping
   - Portfolio-level metrics calculation
   - Cash-like position identification
   - Price updates for all positions

3. **Option Utilities (`option_utils.py`)**: 
   - Black-Scholes model implementation for delta calculations
   - Option description parsing
   - Option exposure metrics calculation

4. **UI Components**:
   - `charts.py`: Visualization components
   - `portfolio_table.py`: Interactive portfolio table
   - `position_details.py`: Detailed position view
   - `summary_cards.py`: Portfolio summary metrics
   - `premium_chat.py`: AI-powered chat interface

5. **Application Core (`app.py`)**: 
   - Dash application setup
   - Main layout definition
   - Callback registration
   - File upload handling

### Key Metrics

1. **Market Exposure**: 
   - Stocks: quantity * price
   - Options: delta * notional value (100 * underlying price * quantity)

2. **Beta-Adjusted Exposure**:
   - Market exposure * beta
   - Provides a more accurate measure of market risk

3. **Long vs. Short Exposure**:
   - Long exposure: Positive market exposure (long stocks, long calls, short puts)
   - Short exposure: Negative market exposure (short stocks, short calls, long puts)
   - Net exposure: Long exposure + short exposure

4. **Option Delta**:
   - Rate of change of option price relative to underlying price
   - Calculated using Black-Scholes model
   - Determines the effective market exposure of options

## Deployment Options

- Local development server
- Docker container
- Hugging Face Spaces

## Current Limitations

- Custom implementation of financial calculations increases maintenance burden
- Limited test coverage for critical financial calculations
- Complex option handling with potential for edge case issues
- Redundant code in exposure calculations
- Limited portfolio optimization capabilities
- No historical performance tracking

## Future

For planned improvements and development roadmap, see:
- [Third-Party Integration and Simplification Plan](devplan/2025-04-10-third-party-integration-plan.md)

Potential future enhancements include:
- Enhanced options analytics with additional Greeks
- Additional portfolio metrics (Sharpe ratio, VaR)
- Sector allocation analysis
- More sophisticated risk metrics
- Additional visualization components
- Enhanced AI integration
- Support for additional data sources
- Real-time data integration
- Historical performance tracking
