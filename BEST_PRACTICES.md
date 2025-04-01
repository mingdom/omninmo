# Project Best Practices

## Core Tenets

0. **Minimal Edits**: Above all else, always do the MINIMAL edit when introducing a change. Do not go around changing things not related to your current task. Do not indiscriminately remove old code.

1. **Simplicity Over Complexity**: Prefer simplicity over complexity. Think hard before introducing unnecessary complexity, is it really worth it?

2. **Avoid Code Bloat**: Do not add unnecessary code or file bloat. KEEP IT SIMPLE STUPID!

3. **Debug Thoroughly**: Debug errors fully! Use logging to understand the error before fixing it. Never, never, NEVER hide an error by swallowing it or working around it without asking for permission.

## Development Practices

### Code Quality
- Use `make lint` to automatically fix style issues with ruff

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

## Implementation Guidelines

### Dash Callbacks
- Keep callbacks focused on a single responsibility
- Document complex callback logic with comments

### Data Processing
- Validate input data before processing
- Handle edge cases (empty data, missing values, etc.)

### Testing
- Test edge cases and error conditions
- Verify calculations with known examples

### Performance
- Optimize only after identifying actual bottlenecks
- Profile slow operations before optimizing
