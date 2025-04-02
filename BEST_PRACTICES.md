# Best Practices for Folio Project

This document is the single source of truth for the Folio project's best practices. Keep it updated as new best practices emerge.

## Core Tenets

1. **Minimal Edits**: Always make the smallest necessary change. Don't modify unrelated code or indiscriminately remove old code.

2. **Simplicity Over Complexity**: Prefer simple solutions. Question whether added complexity is truly necessary.

3. **Avoid Code Bloat**: Keep the codebase lean and focused. Don't add unnecessary code.

4. **Debug Thoroughly**: Understand errors before fixing them. Use logging extensively and never hide errors without permission.

## Key Principles

### Code Organization
- **Module Structure**: Use `__init__.py` files for imports; maintain clean, hierarchical structure
- **Refactoring**: Copy implementations 1:1; preserve function signatures; test thoroughly
- **File Naming**: Use hyphens instead of underscores; include timestamps when appropriate

### Implementation
- **Avoid Hardcoding**: Use pattern-based detection instead of hardcoding specific values
- **Generic Solutions**: Prefer solutions that work for all cases over special-case handling
- **Error Handling**: Understand errors before fixing; log with context; only handle expected errors
- **Logging**: Use INFO for information, WARNING only for actionable issues

### Testing
- **Always Test Changes**: Run tests after any change with `make test`
- **Test Behavior**: Focus on functionality, not implementation details
- **Edge Cases**: Test boundary conditions and error scenarios
- **Regression Tests**: Add tests for bugs to prevent recurrence

### Development Workflow
- **Incremental Changes**: Make small, focused changes rather than large rewrites
- **Documentation**: Keep documentation updated with changes
- **Performance**: Optimize only after identifying actual bottlenecks
