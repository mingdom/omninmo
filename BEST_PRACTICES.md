# Best Practices for Folio Project

This document is the single source of truth for the Folio project's best practices. Keep it updated as new best practices emerge.

---

# 📋 CORE TENETS

1. **SIMPLICITY** - Prefer simple, focused solutions over complex ones. Question every bit of added complexity.

2. **PRECISION** - Make the smallest necessary changes. Don't modify unrelated code or remove what you don't understand.

3. **RELIABILITY** - Debug thoroughly and test rigorously. Never hide errors or compromise data integrity.

4. **USABILITY** - Prioritize user experience. Design for clarity and ease of use, not technical elegance alone.

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
  - **Commit Messages**: Write commit messages to `.commit-msg.md` in the root directory when asked
  - **Never Commit Directly**: Let the user handle all git operations

### �💻 Implementation
*Supports SIMPLICITY and RELIABILITY*
Write code that is clear, maintainable, and robust against edge cases.

- **Code Style**:
  - **Avoid Hardcoding**: Use pattern-based detection instead of hardcoding specific values
  - **Generic Solutions**: Prefer solutions that work for all cases over special-case handling
  - **Readability**: Prioritize readable code over clever optimizations

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

### 🚨 Testing
*Supports RELIABILITY and PRECISION*
Thorough testing prevents bugs and ensures code behaves as expected in all scenarios.

- **Testing Workflow**:
  - **Always Test Changes**: Run `make test` after ANY change - no exceptions!
  - **Test Application**: Use `make portfolio` to test with sample data
  - **Test Real Data**: Use `src/lab/portfolio.csv` for testing with real portfolio data

- **Testing Strategy**:
  - **Test Behavior**: Focus on functionality, not implementation details
  - **Edge Cases**: Test boundary conditions (empty inputs, maximum values, etc.)
  - **Regression Tests**: Add tests for bugs to prevent recurrence
  - **Test Coverage**: Aim for high coverage of critical paths and business logic

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
