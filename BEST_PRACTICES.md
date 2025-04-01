# Best Practices for Folio Project

This document outlines the best practices for the Folio project to ensure code quality, maintainability, and consistency.

## Core Tenets

1. **Minimal Edits**: Above all else, always do the MINIMAL edit when introducing a change. Do not go around changing things not related to your current task. Do not indiscriminately remove old code.

2. **Simplicity Over Complexity**: Prefer simplicity over complexity. Think hard before introducing unnecessary complexity, is it really worth it?

3. **Avoid Code Bloat**: Do not add unnecessary code or file bloat. Keep the codebase lean and focused.

4. **Debug Thoroughly**: Debug errors fully! Use logging to understand the error before fixing it. Never hide an error by swallowing it or working around it without asking for permission.

## Code Style

- Style enforcement is handled by linting tools. Use `make lint` to automatically fix style issues with ruff.
- Use descriptive variable and function names that clearly communicate their purpose.
- Add comments for complex logic, but prefer self-documenting code when possible.

## Development Practices

### File Organization
- When creating new files, prefer hyphen (`-`) instead of underscore (`_`)
- Use the `datetime` command when creating files with timestamp to get the latest date

### Documentation
- Document progress of your changes in the `docs/devlog/` directory, create new file with timestamp as name
- When asked to write a plan, write it in `docs/devplan/` directory
- Keep README.md up to date with current functionality

### Error Handling
- Never hide or work around errors without understanding them first
- Log errors with detailed context before handling them
- Don't swallow exceptions silently

### Logging
- Use logging extensively to debug issues
- Log important state changes and decision points
- Include enough context in log messages to understand the system state
- Use INFO level for informational messages and WARNING level only for actionable issues

## Implementation Guidelines

### Dash Callbacks
- Keep callbacks focused on a single responsibility
- Document complex callback logic with comments

### Data Processing
- Validate input data before processing
- Handle edge cases (empty data, missing values, etc.)
- **Avoid Hardcoding**: Don't hardcode specific values like ticker symbols. Use pattern-based detection or configuration files instead.
- **Avoid Special-Casing**: Prefer generic solutions that work for all cases rather than special handling for specific scenarios.
- **Cash-Like Positions**: Detect based on characteristics (beta, description patterns) rather than account type.

## Testing Best Practices

1. **Test Behavior, Not Implementation**: Tests should verify that the code behaves correctly, not how it's implemented. This allows refactoring without breaking tests.

2. **High ROI Tests**: Focus on testing core functionality and edge cases that are likely to break. Not every line needs a test.

3. **Test Independence**: Each test should be independent and not rely on the state from other tests.

4. **Descriptive Test Names**: Name tests to describe what they're testing, not just the function name.

5. **Test Data**: Use realistic but minimal test data. Avoid using production data in tests.

6. **Mocking External Dependencies**: Use mocks for external dependencies like APIs to make tests faster and more reliable.

7. **Test for Regressions**: When fixing a bug, add a test that would have caught it.

8. **Test Error Handling**: Test that the code handles errors gracefully, not just the happy path.

9. **Edge Cases**: Test edge cases and error conditions.

10. **Verify Calculations**: Verify calculations with known examples.

## Development Workflow

- Use `make test` to run tests before committing changes.
- Use `make portfolio` to test the application with a sample portfolio.
- Document significant changes in the codebase.

## Performance

- Optimize only after identifying actual bottlenecks
- Profile slow operations before optimizing
