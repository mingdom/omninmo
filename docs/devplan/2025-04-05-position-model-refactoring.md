# Position Model Refactoring: Composition over Inheritance

**Date:** 2025-04-05  
**Author:** Augment AI Assistant  
**Status:** Proposed

## Overview

This development plan outlines a refactoring of the position model classes in the Folio application to follow the "composition over inheritance" principle. The current implementation has some inconsistencies and duplication between `Position` and `StockPosition` classes, and the inheritance relationship between `Position` and `OptionPosition` creates tight coupling that could be problematic for future development.

## Background

### Current Structure

- `Position`: Base class with fields for ticker, position_type, quantity, beta, beta_adjusted_exposure, market_exposure
- `StockPosition`: Standalone class with similar fields but not inheriting from Position
- `OptionPosition`: Inherits from Position and adds option-specific fields

### Issues with Current Structure

1. **Duplication**: Similar fields and methods are duplicated between `Position` and `StockPosition`
2. **Inconsistent Inheritance**: `OptionPosition` inherits from `Position` but `StockPosition` doesn't
3. **Tight Coupling**: Changes to `Position` can unexpectedly affect `OptionPosition`
4. **Type Inconsistencies**: `StockPosition.quantity` is `int` while `Position.quantity` is `float`

## Goals

1. Reduce code duplication while maintaining type safety
2. Apply the "composition over inheritance" principle
3. Make the code more maintainable and easier to evolve
4. Ensure backward compatibility during the transition
5. Improve documentation of the position model

## Non-Goals

1. Changing the public API of the position classes
2. Modifying the business logic or calculations
3. Refactoring other parts of the codebase

## Proposed Solution

### 1. Create a Core Position Component

Create a new `PositionCore` class that contains the common fields shared by all position types:

```python
@dataclass
class PositionCore:
    """Core position data shared by all position types"""
    ticker: str
    quantity: float  # Use float for maximum compatibility
    beta: float
    market_exposure: float
    beta_adjusted_exposure: float
```

### 2. Refactor Position Classes to Use Composition

Modify the existing classes to use the core component:

```python
@dataclass
class Position:
    """Base class for all positions"""
    core: PositionCore
    position_type: Literal["stock", "option"]
    
    @property
    def ticker(self) -> str:
        return self.core.ticker
    
    # Other property delegations...
```

```python
@dataclass
class StockPosition:
    """Stock position with core position data"""
    core: PositionCore
    
    @property
    def ticker(self) -> str:
        return self.core.ticker
    
    # Other property delegations...
    
    @property
    def position_type(self) -> Literal["stock"]:
        return "stock"
```

```python
@dataclass
class OptionPosition:
    """Option position with core position data and option-specific fields"""
    core: PositionCore
    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    delta: float
    delta_exposure: float
    notional_value: float
    underlying_beta: float
    
    @property
    def position_type(self) -> Literal["option"]:
        return "option"
    
    # Other property delegations...
```

### 3. Implement Backward Compatibility

To ensure backward compatibility:

1. Add properties for all core fields that delegate to the core component
2. Keep the existing methods like `to_dict()` and `from_dict()`
3. Add factory methods to create instances from the old format

### 4. Update Type Definitions

Update the type definitions to match the new structure:

```python
class PositionCoreDict(TypedDict):
    """Type definition for position core dictionary"""
    ticker: str
    quantity: float
    beta: float
    market_exposure: float
    beta_adjusted_exposure: float
```

## Implementation Plan

### Phase 1: Preparation (1 day)

1. Add comprehensive tests for the current position classes
2. Document the current behavior and edge cases
3. Create a feature branch for the refactoring

### Phase 2: Core Component Implementation (2 days)

1. Create the `PositionCore` class
2. Add type definitions for the core component
3. Implement serialization methods for the core component
4. Write tests for the core component

### Phase 3: Position Class Refactoring (3 days)

1. Refactor `Position` to use the core component
2. Update `OptionPosition` to work with the refactored `Position`
3. Refactor `StockPosition` to use the core component
4. Ensure all tests pass with the refactored classes

### Phase 4: Integration and Testing (2 days)

1. Update any code that directly creates position instances
2. Run integration tests to ensure everything works together
3. Fix any issues that arise during integration
4. Measure performance impact of the changes

### Phase 5: Documentation and Cleanup (1 day)

1. Update documentation to reflect the new structure
2. Add deprecation warnings for any methods that will change in the future
3. Clean up any temporary code or workarounds
4. Create a pull request with the changes

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Breaking changes to the API | High | Medium | Maintain backward compatibility with properties and factory methods |
| Performance degradation | Medium | Low | Benchmark before and after, optimize if necessary |
| Increased complexity | Medium | Medium | Thorough documentation and clear naming conventions |
| Bugs in refactored code | High | Medium | Comprehensive test coverage before and after refactoring |

## Alternatives Considered

### 1. Unify with Inheritance

Make `StockPosition` inherit from `Position` like `OptionPosition` does. This would reduce duplication but increase coupling and might introduce subtle bugs due to the different field types.

### 2. Keep Separate Classes

Keep the classes separate but extract common functionality into utility functions. This would maintain independence but wouldn't address the duplication as effectively.

### 3. Complete Rewrite

Completely rewrite the position model from scratch. This would allow for a cleaner design but would require much more extensive changes throughout the codebase.

## Conclusion

The proposed refactoring to use composition instead of inheritance will make the position model more maintainable and flexible while reducing duplication. By implementing it in phases with thorough testing, we can ensure a smooth transition with minimal disruption to the rest of the codebase.

This approach aligns with the "composition over inheritance" principle and will make it easier to evolve the position model in the future as requirements change.
