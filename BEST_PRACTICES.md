# Best Practices for Folio Project

This document is the single source of truth for the Folio project's best practices. Keep it updated as new best practices emerge.

---

# 📋 CORE TENETS

1. **SIMPLICITY** - Prefer simple, focused solutions over complex ones. Question every bit of added complexity.

2. **PRECISION** - Make the smallest necessary changes. Don't modify unrelated code or remove what you don't understand.

3. **RELIABILITY** - Debug thoroughly and test rigorously. Never hide errors or compromise data integrity.

4. **USABILITY** - Prioritize user experience. Design for clarity and ease of use, not technical elegance alone.

5. **SAFETY** - Never modify Git history or hide Git commands in scripts. All version control operations must be explicit, visible, and performed manually by the user.

---

## Key Principles
*When in doubt, follow the CORE TENETS above.*
This section adds specific guidelines for various aspects of the project.

### 📂 Code Organization
*Supports SIMPLICITY and PRECISION*
Organize code to maximize readability and minimize maintenance overhead.

- **Structure**:
  - **Module Structure**: Use `__init__.py` files for clean imports and hierarchical organization
  - **File Naming**: Use hyphens instead of underscores; include timestamps when appropriate
  - **Dependencies**: Minimize dependencies between modules; use interfaces when needed

- **Refactoring**:
  - **Preserve Interfaces**: Maintain function signatures when refactoring
  - **Copy Carefully**: Copy implementations 1:1 when moving code; avoid subtle changes
  - **Test Thoroughly**: Always test refactored code extensively

### � Development Workflow
*Supports PRECISION and SIMPLICITY*
Follow consistent development practices to maintain code quality and developer productivity.

- **Code Changes**:
  - **Incremental Changes**: Make small, focused changes rather than large rewrites
  - **Performance**: Optimize only after identifying actual bottlenecks
  - **Testing Changes**: Always verify UI changes by running and interacting with the app

- **Application Testing**:
  - **Running the App**: Use `make portfolio` with sample data or `make folio` for a clean start
  - **Manual Testing**: Test critical user flows after any UI or logic changes

- **File Management**:
  - **Version Control**: Update .gitignore for new temporary files or directories
  - **Temporary Files**: Store temporary files in the `.tmp` directory
  - **Cache Files**: Use hidden directories (`.cache_*`) for cache files

- **Version Control**:
  - **Never Commit Directly**: Let the user handle all git operations
  - **⚠️ NEVER USE GIT IN SCRIPTS**: Do not write scripts that use git commands - this can lead to catastrophic data loss and irreversible history modification
  - **Manual Git Operations**: All git operations must be performed manually by the user, never automated
  - **NEVER CREATE PRs WITHOUT BEING ASKED**: Do not create pull requests unless explicitly requested by the user
  - **Preserve Git History**: Never modify Git history without explicit user consent and understanding of the consequences
  - **Transparent Operations**: All version control suggestions must be explicit, visible, and explained clearly

- **Commit Messages**:
  - **Delivery Format**: When asked to write a commit message, provide it directly as a markdown code block (```...```) in the chat, not as a separate file
  - **Conventional Format**: Follow the conventional commits format with a type prefix
  - **Message Structure**: Use a concise title (50 chars max) followed by a blank line and then a detailed body
  - **Title Format**: `<type>: <concise description in imperative mood>`
    - **Types in Priority Order**: Always use the highest impact prefix when multiple types apply
      1. `feat`: New features or significant enhancements (highest priority)
      2. `fix`: Bug fixes or correcting errors
      3. `security`: Security-related changes
      4. `perf`: Performance improvements
      5. `refactor`: Code restructuring without changing functionality
      6. `test`: Adding or modifying tests
      7. `docs`: Documentation updates only
      8. `style`: Formatting, white-space, etc. (no code change)
      9. `build`: Build system or external dependency changes
      10. `ci`: CI configuration changes
      11. `chore`: Maintenance tasks, no production code change (lowest priority)
    - **Examples**:
      - `feat: add user authentication system`
      - `fix: resolve database connection timeout issue`
      - `docs: update deployment instructions`
  - **Title Guidelines**:
    - Use imperative mood ("Add feature" not "Added feature")
    - Capitalize the first word after the type prefix
    - Don't end with a period
    - Keep under 50 characters
    - Be specific about what changed
  - **Body Guidelines**:
    - Explain the "what" and "why" of the change, not the "how"
    - Wrap text at 72 characters
    - Use bullet points for multiple points
    - Reference issues or tickets where applicable
    - Don't use phrases like "This commit..."

### �💻 Implementation
*Supports SIMPLICITY and RELIABILITY*
Write code that is clear, maintainable, and robust against edge cases.

- **Code Style**:
  - **Avoid Hardcoding**: Use pattern-based detection instead of hardcoding specific values
  - **Generic Solutions**: Prefer solutions that work for all cases over special-case handling
  - **Readability**: Prioritize readable code over clever optimizations
  - **Code Quality**: Run `make lint` regularly to identify and fix code quality issues
  - **Unused Code**: Avoid unused imports, functions, and variables; prefix intentionally unused variables with underscore
  - **Clean Code**: Remove commented-out code and fix exception handling issues

- **Configuration**:
  - **External Config**: Use configuration files for values that might change
  - **Sensible Defaults**: Provide reasonable defaults for all configurable options
  - **Validate Inputs**: Check and validate all external inputs and configuration

### 🛡️ Error Handling and Logging
*Supports RELIABILITY and PRECISION*
Handle errors gracefully and log information that helps diagnose issues quickly.

- **Exception Handling**:
  - **Use Custom Exceptions**: Use application-specific exceptions from `src/folio/exceptions.py`
  - **Don't Swallow Exceptions**: Never catch exceptions without proper handling or re-raising
  - **Use Error Utilities**: Leverage decorators and utilities in `src/folio/error_utils.py`

- **Logging Best Practices**:
  - **Structured Messages**: Include context (e.g., "Failed to process AAPL: missing price data")
  - **Include Stack Traces**: For unexpected errors, use `exc_info=True`
  - **Distinguish States vs. Errors**: Log normal states as DEBUG/INFO, not as errors

- **Log Levels**:
  - **DEBUG**: Detailed flow information ("Processing portfolio entry 5 of 20")
  - **INFO**: Normal application events ("Portfolio loaded successfully")
  - **WARNING**: Potential issues requiring attention ("Using cached data: API unavailable")
  - **ERROR**: Actual errors affecting functionality ("Failed to calculate beta for AAPL")
  - **CRITICAL**: Severe errors preventing operation ("Database connection failed")

- **Log Monitoring**:
  - **Check Latest Logs**: Always check the latest logs in the `logs/` directory after running tests or the application
  - **Application Logs**: Review `logs/folio_latest.log` after running the application to identify errors
  - **Test Logs**: Check `logs/test_latest.log` after running tests to catch test failures and errors
  - **Error Investigation**: When errors occur, examine the logs first for detailed error messages and stack traces

- **Regression Analysis**:
  - **Root Cause Investigation**: Always use `git blame` to understand what caused a regression
  - **Document Findings**: Record regression analysis in devlogs to prevent repeating mistakes
  - **Follow Process**: See [regression-analysis.md](docs/regression-analysis.md) for the complete process

### 🚨 Testing
*Supports RELIABILITY and PRECISION*
Thorough testing prevents bugs and ensures code behaves as expected in all scenarios.

- **Testing Workflow**:
  - **Always Test Changes**: Run `make test` after ANY change - no exceptions!
  - **Check Test Logs**: Always review `logs/test_latest.log` after running tests to identify failures
  - **Run Linter Regularly**: Run `make lint` to check for code quality issues, unused imports/functions, and other potential problems
  - **Fix Linting Issues**: Address linting errors before committing code to maintain code quality
  - **Automated vs. Manual Testing**:
    - For AI assistants: Only run `make test` and `make lint` to verify changes
    - NEVER launch the application with `make folio` or `make portfolio` - leave UI testing to human users
    - Instead, provide detailed instructions on what UI changes to test and how to verify them
    - Add unit tests for new functionality instead of manual testing when possible
  - **Testing Instructions**:
    - Provide clear, step-by-step instructions for the user to test changes
    - Include specific UI elements to check and expected behavior
    - Describe what success looks like and potential issues to watch for
    - Format as a checklist that the user can follow easily
  - **Review App Logs**: Check `logs/test_latest.log` after running tests to catch errors
  - **Test Real Data**: Use `src/lab/portfolio.csv` for testing with real portfolio data

- **Testing Strategy**:
  - **Test Behavior**: Focus on functionality, not implementation details
  - **Edge Cases**: Test boundary conditions (empty inputs, maximum values, etc.)
  - **Regression Tests**: Add tests for bugs to prevent recurrence
  - **Test Coverage**: Aim for high coverage of critical paths and business logic
  - **Test New Functionality**: Always write tests for new features and components
  - **Test Naming**: Name tests specifically to the method/module being tested
  - **Test Public API**: Test only public functions to avoid coupling tests to implementation details
  - **Test Independence**: Each test should be independent and not rely on other tests

- **Writing Tests**:
  - **Test Structure**: Follow the Arrange-Act-Assert pattern
  - **Mock External Dependencies**: Use mocks for external services, APIs, and databases
  - **Test Edge Cases**: Include tests for error conditions and boundary cases
  - **Parameterized Tests**: Use pytest's parameterize for testing multiple inputs
  - **Fixtures**: Create fixtures for common test setup
  - **Test Isolation**: Reset state between tests to prevent test interdependence
  - **Never Change Test Logic**: Fix implementation to make tests pass, not the other way around

### 📝 Documentation
*Supports USABILITY and RELIABILITY*
Clear, accurate documentation helps onboard new developers and maintain institutional knowledge.

- **Documentation Standards**:
  - **Date Accuracy**: Always use the `date` command for current dates in documents
  - **Consistent Format**: Follow existing formats and naming conventions
  - **Single Source of Truth**: Maintain one authoritative source for each type of documentation

- **Documentation Maintenance**:
  - **Keep Updated**: Update documentation when code changes
  - **Code Comments**: Document complex logic and "why" decisions, not obvious code
  - **README Files**: Ensure each major component has a clear, concise README

- **Development Planning**:
  - **Create Devplans**: Document detailed plans in `docs/devplan/` for significant features, design changes, or deployments
  - **Plan Structure**: Include overview, implementation steps, timeline, and considerations
  - **Phased Approach**: Break complex changes into manageable phases with testing checkpoints
  - **Deployment Plans**: For deployment-related changes, include hosting options, infrastructure requirements, and security considerations

- **Development Logging**:
  - **Update Devlogs**: Document completed changes in `docs/devlog/` after implementing major features or changes
  - **Devlog Format**: Include date, summary, implementation details, and lessons learned
  - **Technical Details**: Document key technical decisions, challenges overcome, and solutions implemented
  - **Future Considerations**: Note any follow-up tasks or potential improvements identified during implementation
