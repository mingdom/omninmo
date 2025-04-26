# Options Module Refactoring

## Overview

This document summarizes the refactoring of options-related functionality from `quantlib_utils.py` into a new dedicated `options.py` module. This refactoring was done to improve separation of concerns and make it easier to potentially swap out the underlying implementation in the future.

## Changes Made

1. Created a new `src/folio/options.py` module with all the options-related functionality from `quantlib_utils.py`:
   - `OptionContract` dataclass
   - Black-Scholes calculation functions
   - Option parsing and processing functions
   - Volatility estimation functions

2. Completely removed `quantlib_utils.py` to keep the codebase clean (backward compatibility was not a concern)

3. Created a new test file `tests/test_options.py` for the new module

4. Updated `tests/test_option_exposure.py` to import from the new module

5. Verified that all tests pass and there are no linting issues

## Benefits

- Better separation of concerns
- Easier to swap out the underlying implementation in the future
- More maintainable codebase
- Clearer module structure

## Future Work

- Consider creating an abstract interface for option calculations to make it even easier to swap implementations
- Add more sophisticated volatility models
- Support additional option types beyond vanilla calls and puts
