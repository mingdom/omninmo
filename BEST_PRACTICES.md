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

### Error Handling and Logging
- **Use Custom Exceptions**: Use the application's custom exception classes in `src/folio/exceptions.py` for better context
- **Distinguish States vs. Errors**: Log expected states (like initialization) as DEBUG, not as errors
- **Use Error Handling Utilities**: Use the decorators and utilities in `src/folio/error_utils.py` for consistent handling
- **Include Stack Traces**: Always include stack traces for unexpected errors using `exc_info=True`
- **Appropriate Log Levels**:
  - DEBUG: Detailed flow information
  - INFO: Normal application events
  - WARNING: Potential issues that don't prevent operation
  - ERROR: Actual errors that affect functionality
  - CRITICAL: Severe errors that prevent the application from functioning
- **Actionable Warnings**: Only use WARNING level for issues that require attention
- **Structured Error Messages**: Include context in error messages (what operation was being performed, what data was involved)
- **Don't Swallow Exceptions**: Never catch exceptions without proper handling or re-raising

### Testing
- **Always Test Changes**: Run tests after ANY change with `make test` - no exceptions!
- **Test Application**: Use `make portfolio` to launch and test the application with sample data
- **Test Portfolio**: Use `src/lab/portfolio.csv` for testing with real portfolio data (note: this file is gitignored for privacy reasons but available locally)
- **Test Behavior**: Focus on functionality, not implementation details
- **Edge Cases**: Test boundary conditions and error scenarios
- **Regression Tests**: Add tests for bugs to prevent recurrence

### Documentation
- **Date Accuracy**: Always use the `date` command to get the current date when creating dated documents
- **Consistent Format**: Follow existing document formats and naming conventions
- **Keep Updated**: Update documentation when code changes
- **Single Source of Truth**: Maintain one authoritative source for each type of documentation

### Development Workflow
- **Incremental Changes**: Make small, focused changes rather than large rewrites
- **Documentation**: Keep documentation updated with changes
- **Performance**: Optimize only after identifying actual bottlenecks
- **Running the Application**: Use `make portfolio` to test with sample data or `make folio` for a clean start
- **Testing Changes**: Always verify UI changes by running the application and interacting with it
- **Version Control**: Update .gitignore when adding new temporary files or directories
- **Temporary Files**: Store temporary files in the .tmp directory
- **Cache Files**: Use hidden directories (.cache_*) for cache files
