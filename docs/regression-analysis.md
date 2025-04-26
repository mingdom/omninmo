# Regression Analysis Process

This document outlines the standard process for analyzing and addressing regressions in the Folio project. Following these guidelines helps ensure that we not only fix issues but also understand their root causes and prevent similar problems in the future.

## Core Principles

1. **Understand Before Fixing** - Always identify the root cause before implementing a fix
2. **Document Thoroughly** - Record findings and solutions for future reference
3. **Prevent Recurrence** - Implement safeguards to prevent similar issues
4. **Learn and Improve** - Use each regression as an opportunity to improve processes

## Regression Analysis Workflow

### 1. Identify and Reproduce

- **Confirm the Issue**: Verify that the regression exists and can be consistently reproduced
- **Document Symptoms**: Record exact error messages, unexpected behaviors, and affected functionality
- **Determine Scope**: Identify which components, features, or user flows are affected
- **Establish Timeline**: Determine when the issue first appeared

### 2. Investigate Root Cause

- **Use Git Blame**:
  ```bash
  git blame path/to/file | grep -A 10 "relevant_function_or_line"
  ```
  This identifies who last modified the code and in which commit

- **Examine Commit History**:
  ```bash
  git show <commit_hash>
  ```
  Review the full changes in the suspect commit

- **Compare Versions**:
  ```bash
  git diff <old_commit>..<new_commit> -- path/to/file
  ```
  Compare working and non-working versions of the code

- **Check Related Files**: Look for changes in dependencies or related components
  ```bash
  git log -p path/to/related/file
  ```

- **Analyze Data Flow**: Trace the execution path to identify where behavior diverges from expectations

### 3. Develop and Test Fix

- **Minimal Changes**: Make the smallest possible change that addresses the root cause
- **Comprehensive Testing**: Test not only the fixed functionality but also related features
- **Verify Fix**: Ensure the fix resolves the issue without introducing new problems
- **Review Edge Cases**: Check that the fix works in all scenarios, not just the reported case

### 4. Document Findings

- **Create Devlog**: Document the regression and fix in `docs/devlog/` with:
  - Date and issue summary
  - Root cause analysis with references to specific commits
  - Fix implementation details
  - Lessons learned
  - Prevention strategies

- **Example Structure**:
  ```markdown
  # Fix for [Feature] Regression

  **Date:** YYYY-MM-DD
  **Issue:** Brief description of the regression
  **Error:** Exact error message or behavior

  ## Root Cause Analysis
  [Detailed explanation of what caused the regression, referencing specific commits]

  ## Fix Implementation
  [Description of the changes made to fix the issue]

  ## Lessons Learned
  [Insights gained from this regression]

  ## Prevention Strategies
  [Steps to prevent similar issues in the future]
  ```

### 5. Implement Prevention Measures

- **Add Tests**: Create specific tests that would have caught this regression
- **Improve Validation**: Add input validation or assertions that would prevent the issue
- **Update Documentation**: Clarify requirements or dependencies that were misunderstood
- **Enhance Code Reviews**: Identify what could have been caught in code review
- **Refine Processes**: Update development workflows to prevent similar issues

## Common Regression Types and Analysis Strategies

### 1. API/Interface Changes

- **Symptoms**: Function calls fail, unexpected parameter behavior
- **Analysis Strategy**:
  - Compare function signatures before and after changes
  - Check for changes in parameter defaults or types
  - Look for changes in return values or error handling

### 2. Data Flow Disruptions

- **Symptoms**: Incorrect data displayed, processing errors
- **Analysis Strategy**:
  - Trace data from source to display
  - Check for changes in data transformation steps
  - Verify data validation logic

### 3. UI Regressions

- **Symptoms**: Visual glitches, interaction failures
- **Analysis Strategy**:
  - Inspect DOM structure changes
  - Check event handler modifications
  - Review CSS changes affecting layout or visibility

### 4. Performance Regressions

- **Symptoms**: Slowdowns, increased resource usage
- **Analysis Strategy**:
  - Profile before and after the regression
  - Look for added loops, API calls, or expensive operations
  - Check for changes in caching or optimization logic

### 5. Security Regressions

- **Symptoms**: New vulnerabilities, failed security checks
- **Analysis Strategy**:
  - Review input validation changes
  - Check for disabled security features
  - Verify proper sanitization of user inputs

## Tools and Techniques

### Git Commands for Regression Analysis

- **Find when a line changed**:
  ```bash
  git blame -L <start_line>,<end_line> path/to/file
  ```

- **View commit history for a file**:
  ```bash
  git log --follow -p path/to/file
  ```

- **Find commits affecting a specific function**:
  ```bash
  git log -p -S "function_name" path/to/file
  ```

- **Compare file between versions**:
  ```bash
  git diff commit1..commit2 -- path/to/file
  ```

- **Find when a bug was introduced (binary search)**:
  ```bash
  git bisect start
  git bisect bad  # Current version has the bug
  git bisect good <commit_hash>  # Last known good version
  # Git will checkout commits for you to test
  # For each commit, test and mark:
  git bisect good  # If this version works
  git bisect bad   # If this version has the bug
  # When finished:
  git bisect reset
  ```

### Debugging Techniques

- **Logging**: Add strategic log statements to trace execution flow
- **Breakpoints**: Use debugger to step through code execution
- **State Inspection**: Compare variable values between working and non-working versions
- **Isolation**: Create minimal test cases that reproduce the issue

## Integration with Development Workflow

- **Regression Testing**: Run comprehensive tests before and after changes
- **Code Reviews**: Pay special attention to changes that modify existing behavior
- **Continuous Integration**: Set up automated tests to catch regressions early
- **Feature Flags**: Use flags to enable/disable new features for easier isolation of issues

---

Remember: Every regression is an opportunity to improve our codebase and processes. By thoroughly analyzing each issue, we build institutional knowledge and create more robust systems over time.

See also: [BEST_PRACTICES.md](../BEST_PRACTICES.md) for general development guidelines.
