# QuantLib Integration Design Document

**Date: 2025-04-10**

## 1. Executive Summary

This document outlines a plan to replace our custom options calculations in the Folio application with QuantLib, an industry-standard quantitative finance library. Our proof-of-concept has demonstrated that QuantLib provides accurate results comparable to our current implementation while offering additional capabilities and reducing maintenance burden.

This design document evaluates alternatives to QuantLib, explores additional functionality we could leverage beyond options pricing, and provides a detailed implementation plan for integrating QuantLib into our codebase.

## 2. Alternatives Analysis

### 2.1 Available Options Pricing Libraries

| Library | Language | License | Maturity | Community | Features | Maintenance | Performance |
|---------|----------|---------|----------|-----------|----------|-------------|-------------|
| **QuantLib** | C++ with Python bindings | BSD | High (20+ years) | Large, active | Comprehensive | Active | Excellent |
| **py_vollib** | Python | BSD | Medium | Small | Options only | Limited | Good |
| **FinancePy** | Python | MIT | Medium | Growing | Comprehensive | Active | Good |
| **mibian** | Python | MIT | Low | Small | Options only | Minimal | Good |
| **scipy.stats** | Python | BSD | High | Large | Limited | Active | Excellent |
| **NumPy/SciPy custom** | Python | BSD | N/A | N/A | Custom only | Self-maintained | Variable |

### 2.2 Detailed Comparison

#### 2.2.1 QuantLib
**Pros:**
- Industry standard with 20+ years of development
- Comprehensive coverage of financial instruments and models
- Actively maintained with regular updates
- Extensive documentation and community support
- High performance C++ core with Python bindings
- Used by financial institutions worldwide
- Supports multiple option pricing models beyond Black-Scholes
- Handles complex derivatives and exotic options

**Cons:**
- Larger dependency footprint (C++ library with Python bindings)
- Steeper learning curve due to comprehensive API
- Installation can be more complex than pure Python libraries

#### 2.2.2 py_vollib
**Pros:**
- Pure Python implementation
- Focused specifically on options pricing
- Simple API for basic options calculations
- Easy installation via pip

**Cons:**
- Limited to Black-Scholes and binomial models
- Smaller community and less comprehensive documentation
- Less actively maintained
- Limited to European and American options
- No support for exotic options or complex derivatives

#### 2.2.3 FinancePy
**Pros:**
- Pure Python implementation
- Growing community
- Comprehensive coverage of financial instruments
- Clean, object-oriented API
- Active development

**Cons:**
- Less mature than QuantLib (newer project)
- Smaller community and less battle-tested
- Documentation is still evolving
- Performance may be lower than C++-based solutions

#### 2.2.4 mibian
**Pros:**
- Very lightweight and simple
- Pure Python implementation
- Easy to understand and modify
- Minimal dependencies

**Cons:**
- Very limited functionality (basic Black-Scholes only)
- Not actively maintained
- No support for complex options or models
- Limited documentation and community support

#### 2.2.5 scipy.stats + Custom Implementation
**Pros:**
- Minimal external dependencies
- Complete control over implementation
- Can be tailored exactly to our needs

**Cons:**
- High maintenance burden
- Requires expertise in financial mathematics
- Risk of implementation errors
- Limited to what we implement ourselves
- No community support for financial-specific issues

### 2.3 Recommendation

**QuantLib is the recommended solution** for the following reasons:

1. **Maturity and Reliability**: With over 20 years of development and use in production environments by financial institutions, QuantLib has proven its reliability and accuracy.

2. **Comprehensive Functionality**: QuantLib provides not just options pricing but a wide range of financial calculations that we may leverage in the future.

3. **Active Maintenance**: Regular updates, bug fixes, and improvements ensure the library stays current with financial practices and models.

4. **Performance**: The C++ core provides excellent performance for computationally intensive calculations.

5. **Community Support**: Large community and extensive documentation reduce implementation risks and provide resources for troubleshooting.

6. **Future-Proofing**: The comprehensive nature of QuantLib allows us to expand our financial calculations beyond options without adding new dependencies.

While FinancePy is a promising alternative with a cleaner Python API, QuantLib's maturity, comprehensive feature set, and proven track record make it the safer and more robust choice for production use.

## 3. Additional QuantLib Functionality for Future Use

Beyond options pricing, QuantLib offers numerous capabilities that could enhance our application:

### 3.1 Fixed Income Analysis
- Yield curve construction and interpolation
- Bond pricing and yield calculations
- Duration and convexity calculations
- Interest rate derivatives pricing
- Term structure modeling

**Potential Use Cases:**
- Add bond portfolio analysis
- Calculate portfolio duration and interest rate sensitivity
- Model yield curve scenarios and impact on portfolio

### 3.2 Risk Management
- Value at Risk (VaR) calculations
- Credit risk modeling
- Stress testing frameworks
- Scenario analysis

**Potential Use Cases:**
- Enhanced portfolio risk metrics
- Stress testing portfolio under different market conditions
- Credit risk assessment for fixed income positions

### 3.3 Monte Carlo Simulations
- Path generation for various processes
- Pricing of path-dependent derivatives
- Scenario generation for risk analysis

**Potential Use Cases:**
- Simulate future portfolio performance
- Price complex derivatives
- Generate distribution of potential outcomes

### 3.4 Volatility Modeling
- Local volatility models
- Stochastic volatility models (Heston, SABR)
- Volatility surface construction and interpolation

**Potential Use Cases:**
- More accurate options pricing with sophisticated volatility models
- Volatility surface visualization
- Volatility risk analysis

### 3.5 Calendar and Date Utilities
- Business day conventions
- Holiday calendars for different markets
- Date arithmetic and scheduling

**Potential Use Cases:**
- Accurate handling of settlement dates
- Proper accounting for market holidays
- Scheduling of cash flows and option expiries

### 3.6 Optimization Tools
- Calibration of models to market data
- Portfolio optimization
- Curve fitting

**Potential Use Cases:**
- Calibrate models to market prices
- Optimize portfolio allocations
- Fit yield curves to market data

## 4. Implementation Plan for Options Calculations

### 4.1 Current Architecture

Our current options calculation is implemented in `src/folio/option_utils.py` with the following key functions:
- `calculate_black_scholes_delta`: Calculates option delta
- `calculate_bs_price`: Calculates option price
- `calculate_implied_volatility`: Estimates implied volatility
- `parse_option_description`: Parses option details from description

These functions are used by the `OptionPosition` class in `src/folio/data_model.py` and the portfolio processing logic in `src/folio/portfolio.py`.

### 4.2 Proposed Architecture

We will create a new module `src/folio/quantlib_utils.py` that implements the same interface as our current `option_utils.py` but uses QuantLib internally. This approach allows for:

1. **Parallel Implementation**: Both implementations can coexist during transition
2. **Minimal Disruption**: Existing code using the options API won't need changes
3. **Easy Comparison**: Results from both implementations can be compared
4. **Graceful Fallback**: Can fall back to current implementation if needed

### 4.3 Implementation Phases

#### Phase 1: Core QuantLib Wrapper (1-2 weeks)

1. Create `src/folio/quantlib_utils.py` with the following functions:
   - `calculate_option_delta`: QuantLib implementation of delta calculation
   - `calculate_option_price`: QuantLib implementation of price calculation
   - `calculate_option_implied_volatility`: QuantLib implementation of implied volatility
   - `calculate_option_greeks`: New function to calculate all Greeks (delta, gamma, theta, vega, rho)

2. Add configuration option to select implementation:
   - Add `USE_QUANTLIB` flag in `src/folio/config.py`
   - Modify `option_utils.py` to delegate to QuantLib implementation when flag is enabled

3. Add comprehensive tests:
   - Create `tests/test_quantlib_utils.py`
   - Test with various option parameters
   - Compare results with current implementation
   - Test edge cases (very short expiry, deep ITM/OTM)

#### Phase 2: Enhanced Option Analytics (1-2 weeks)

1. Extend `OptionPosition` class in `data_model.py`:
   - Add properties for additional Greeks (gamma, theta, vega, rho)
   - Add methods to calculate implied volatility surface
   - Ensure backward compatibility

2. Update portfolio calculations in `portfolio.py`:
   - Modify `process_portfolio_data` to use enhanced option analytics
   - Add aggregation of new Greeks at portfolio level
   - Ensure backward compatibility

3. Add tests for enhanced analytics:
   - Test calculation of all Greeks
   - Test aggregation at portfolio level
   - Test with real portfolio data

#### Phase 3: UI Integration (1-2 weeks)

1. Update UI components to display enhanced analytics:
   - Add Greeks to option details view
   - Add implied volatility visualization
   - Add portfolio-level Greeks summary

2. Add user configuration:
   - Allow users to select calculation method
   - Add settings for volatility model parameters

3. Test UI components:
   - Ensure correct display of enhanced analytics
   - Test user configuration options

#### Phase 4: Deprecation of Custom Implementation (1 week)

1. Make QuantLib the default implementation:
   - Set `USE_QUANTLIB=True` as default
   - Add deprecation warnings to custom implementation

2. Update documentation:
   - Document new capabilities
   - Update API references
   - Add examples of using enhanced analytics

3. Final validation:
   - Comprehensive testing with real portfolios
   - Performance benchmarking
   - Edge case validation

### 4.4 Detailed Code Changes

#### 4.4.1 New Module: `src/folio/quantlib_utils.py`

```python
"""
QuantLib implementation of option calculations.
"""

import datetime
from typing import Dict, Any, Optional, Union, Tuple

import QuantLib as ql
import numpy as np

from src.folio.data_model import OptionPosition


def create_option_helper(
    option_type: str,
    strike: float,
    expiry_date: datetime.datetime,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: float = 0.30,
    dividend_yield: float = 0.0,
) -> Tuple[ql.VanillaOption, ql.BlackScholesMertonProcess]:
    """
    Create a QuantLib option and process for calculations.
    
    Returns:
        Tuple of (option, process) for use in calculations
    """
    # Implementation details...


def calculate_option_delta(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> float:
    """
    Calculate option delta using QuantLib.
    
    Compatible with the interface of option_utils.calculate_black_scholes_delta
    """
    # Implementation details...


def calculate_option_price(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> float:
    """
    Calculate option price using QuantLib.
    
    Compatible with the interface of option_utils.calculate_bs_price
    """
    # Implementation details...


def calculate_option_implied_volatility(
    option_position: OptionPosition,
    underlying_price: float,
    option_price: Optional[float] = None,
    risk_free_rate: float = 0.05,
) -> float:
    """
    Calculate implied volatility using QuantLib.
    
    Compatible with the interface of option_utils.calculate_implied_volatility
    """
    # Implementation details...


def calculate_option_greeks(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate all option Greeks using QuantLib.
    
    Returns:
        Dictionary with keys: delta, gamma, theta, vega, rho
    """
    # Implementation details...
```

#### 4.4.2 Modified: `src/folio/option_utils.py`

```python
"""
Option utilities for calculating option metrics.
"""

from typing import Optional

from src.folio.config import USE_QUANTLIB
from src.folio.data_model import OptionPosition

# Import QuantLib implementation if available
try:
    from src.folio.quantlib_utils import (
        calculate_option_delta as ql_calculate_delta,
        calculate_option_price as ql_calculate_price,
        calculate_option_implied_volatility as ql_calculate_iv,
        calculate_option_greeks as ql_calculate_greeks,
    )
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False


def calculate_black_scholes_delta(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> float:
    """
    Calculate option delta using Black-Scholes model.
    
    If USE_QUANTLIB is True and QuantLib is available, uses QuantLib implementation.
    Otherwise falls back to custom implementation.
    """
    if USE_QUANTLIB and QUANTLIB_AVAILABLE:
        return ql_calculate_delta(
            option_position, underlying_price, risk_free_rate, volatility
        )
    
    # Original implementation...


def calculate_bs_price(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> float:
    """
    Calculate option price using Black-Scholes model.
    
    If USE_QUANTLIB is True and QuantLib is available, uses QuantLib implementation.
    Otherwise falls back to custom implementation.
    """
    if USE_QUANTLIB and QUANTLIB_AVAILABLE:
        return ql_calculate_price(
            option_position, underlying_price, risk_free_rate, volatility
        )
    
    # Original implementation...


def calculate_implied_volatility(
    option_position: OptionPosition,
    underlying_price: float,
    option_price: Optional[float] = None,
    risk_free_rate: float = 0.05,
) -> float:
    """
    Calculate implied volatility.
    
    If USE_QUANTLIB is True and QuantLib is available, uses QuantLib implementation.
    Otherwise falls back to custom implementation.
    """
    if USE_QUANTLIB and QUANTLIB_AVAILABLE:
        return ql_calculate_iv(
            option_position, underlying_price, option_price, risk_free_rate
        )
    
    # Original implementation...


def calculate_option_greeks(
    option_position: OptionPosition,
    underlying_price: float,
    risk_free_rate: float = 0.05,
    volatility: Optional[float] = None,
) -> dict:
    """
    Calculate all option Greeks.
    
    If USE_QUANTLIB is True and QuantLib is available, calculates all Greeks.
    Otherwise calculates only delta using custom implementation.
    """
    if USE_QUANTLIB and QUANTLIB_AVAILABLE:
        return ql_calculate_greeks(
            option_position, underlying_price, risk_free_rate, volatility
        )
    
    # Fallback implementation with only delta
    delta = calculate_black_scholes_delta(
        option_position, underlying_price, risk_free_rate, volatility
    )
    return {"delta": delta}
```

#### 4.4.3 New: `src/folio/config.py`

```python
"""
Configuration settings for the Folio application.
"""

# Whether to use QuantLib for option calculations
USE_QUANTLIB = False  # Default to False during transition
```

#### 4.4.4 Modified: `src/folio/data_model.py`

```python
class OptionPosition(Position):
    """
    Represents an option position in a portfolio.
    """
    
    # Existing properties...
    
    @property
    def delta(self) -> float:
        """
        Calculate the delta of the option.
        """
        from src.folio.option_utils import calculate_black_scholes_delta
        return calculate_black_scholes_delta(self, self.underlying_price)
    
    @property
    def greeks(self) -> dict:
        """
        Calculate all Greeks for the option.
        
        Returns a dictionary with keys: delta, gamma, theta, vega, rho
        """
        from src.folio.option_utils import calculate_option_greeks
        return calculate_option_greeks(self, self.underlying_price)
    
    @property
    def gamma(self) -> float:
        """
        Calculate the gamma of the option.
        """
        return self.greeks.get("gamma", 0.0)
    
    @property
    def theta(self) -> float:
        """
        Calculate the theta of the option.
        """
        return self.greeks.get("theta", 0.0)
    
    @property
    def vega(self) -> float:
        """
        Calculate the vega of the option.
        """
        return self.greeks.get("vega", 0.0)
    
    @property
    def rho(self) -> float:
        """
        Calculate the rho of the option.
        """
        return self.greeks.get("rho", 0.0)
```

### 4.5 Testing Strategy

#### 4.5.1 Unit Tests

1. **Core Calculation Tests**:
   - Test each QuantLib function with various parameters
   - Compare results with current implementation
   - Test edge cases (very short expiry, deep ITM/OTM)

2. **Integration Tests**:
   - Test with real portfolio data
   - Verify portfolio-level calculations
   - Test performance with large portfolios

3. **Regression Tests**:
   - Ensure existing functionality continues to work
   - Verify backward compatibility

#### 4.5.2 Test Data

1. **Synthetic Test Cases**:
   - Generate options with various parameters
   - Include edge cases (very short expiry, deep ITM/OTM)
   - Test with different volatility models

2. **Real Portfolio Data**:
   - Use `.tmp/real-portfolio.csv` for testing
   - Include options with various expiries and strikes
   - Test with real market prices

### 4.6 Deployment Considerations

#### 4.6.1 Dependencies

1. **QuantLib Installation**:
   - Add QuantLib to requirements.txt
   - Document installation process
   - Consider containerization to simplify deployment

2. **Fallback Mechanism**:
   - Ensure graceful fallback if QuantLib is not available
   - Add clear error messages and logging

#### 4.6.2 Performance Monitoring

1. **Benchmarking**:
   - Measure performance before and after implementation
   - Monitor calculation times for large portfolios
   - Identify and address any performance bottlenecks

2. **Error Tracking**:
   - Log differences between implementations
   - Monitor for unexpected results or errors
   - Implement alerting for significant discrepancies

## 5. Risks and Mitigations

### 5.1 Implementation Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Calculation differences | High | Medium | Comprehensive testing, parallel implementation, configurable fallback |
| Performance issues | Medium | Low | Benchmarking, optimization, caching |
| Installation complexity | Medium | Medium | Clear documentation, containerization, fallback mechanism |
| API changes in QuantLib | Low | Low | Version pinning, comprehensive tests |
| Learning curve | Medium | Medium | Documentation, examples, training |

### 5.2 Business Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Incorrect risk metrics | High | Low | Extensive validation, comparison with market prices |
| Dependency on external library | Medium | Medium | Fallback implementation, version pinning |
| Increased maintenance complexity | Low | Low | Reduced custom code, improved documentation |
| User resistance to changes | Low | Low | Gradual rollout, user education, configurable options |

## 6. Success Criteria

The integration will be considered successful if:

1. **Accuracy**: QuantLib calculations match or improve upon our current implementation for >99% of options
2. **Performance**: Calculation time is comparable or better than current implementation
3. **Functionality**: All existing features continue to work, with additional Greeks available
4. **Maintenance**: Code complexity is reduced, with fewer lines of custom financial calculations
5. **User Satisfaction**: Users report improved analytics and no regression in existing functionality

## 7. Conclusion

Integrating QuantLib into our Folio application offers significant benefits:

1. **Reduced Maintenance Burden**: Replace complex custom code with industry-standard implementation
2. **Enhanced Capabilities**: Access to additional Greeks and more sophisticated models
3. **Future Expansion**: Foundation for adding more financial calculations beyond options
4. **Improved Accuracy**: More robust handling of edge cases and complex options

The proposed implementation plan minimizes disruption while providing a clear path to fully leveraging QuantLib's capabilities. The parallel implementation approach allows for thorough validation before fully committing to the new implementation.

Given the clear benefits and manageable risks, we recommend proceeding with the QuantLib integration as outlined in this document.

## 8. References

1. QuantLib Documentation: https://www.quantlib.org/docs.shtml
2. QuantLib-Python Documentation: https://quantlib-python-docs.readthedocs.io/
3. Options Pricing Models: https://en.wikipedia.org/wiki/Option_pricing
4. Black-Scholes Model: https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
5. Greeks (Finance): https://en.wikipedia.org/wiki/Greeks_(finance)
