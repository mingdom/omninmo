# General Testing Guidelines

This document outlines the general philosophy and best practices for writing tests in this project. The goal is to ensure code correctness, maintainability, and confidence during development and refactoring.

## Core Philosophy

- **Confidence, Not Just Coverage:** The primary goal of testing is to build confidence that the code works as intended, including edge cases and error conditions. High test coverage is a good indicator but not the ultimate goal if the tests themselves aren't meaningful.
- **Test Behavior, Not Implementation:** Tests should verify the *what* (the expected output or behavior for a given input) rather than the *how* (the specific internal steps). This makes tests more resilient to refactoring.
- **Fast Feedback:** Tests should run quickly to encourage frequent execution during development.
- **Maintainability:** Tests are code too. They should be clear, concise, well-organized, and easy to understand and update.

## Testing Pyramid

We generally follow the testing pyramid concept:

1.  **Unit Tests (Foundation):**
    *   **Focus:** Test individual functions, methods, or classes in isolation.
    *   **Characteristics:** Fast, reliable, pinpoint failures accurately.
    *   **Dependencies:** External dependencies (APIs, databases, file system, complex objects) should be mocked or stubbed.
    *   **Goal:** Verify the core logic of the smallest testable parts of the application.
    *   **Location:** Typically reside in the `tests/` directory, mirroring the structure of the `src/` directory.

2.  **Integration Tests (Middle Layer):**
    *   **Focus:** Test the interaction between multiple components or modules.
    *   **Characteristics:** Slower than unit tests, can be less reliable if external systems are involved (though often still mocked).
    *   **Dependencies:** May involve mocking fewer dependencies or using test doubles that mimic real behavior more closely. Can sometimes use test-specific infrastructure (e.g., in-memory database).
    *   **Goal:** Verify that different parts of the system work together as expected (e.g., data flows correctly from a utility function through a callback to a component).
    *   **Usage:** Use more sparingly than unit tests, focusing on critical integration points.

3.  **End-to-End (E2E) / UI Tests (Peak):**
    *   **Focus:** Test the entire application flow from the user's perspective, often through the UI.
    *   **Characteristics:** Slowest, most brittle (prone to breaking with UI changes), hardest to debug.
    *   **Dependencies:** Interact with the fully deployed application or a close replica.
    *   **Goal:** Verify that major user workflows function correctly.
    *   **Usage:** Use very sparingly for the most critical user journeys. In Dash applications, testing callbacks often provides better value and stability than full UI simulation.

## Best Practices

1.  **Unit Tests First:** Prioritize writing comprehensive unit tests for all core logic, utility functions, and data transformations.
2.  **Mock Effectively:** Use mocking libraries (like `unittest.mock` in Python) to isolate the code under test. Mock external APIs (`DataFetcher`), database interactions, file I/O, and potentially complex internal dependencies.
3.  **Test Edge Cases and Errors:** Don't just test the "happy path." Explicitly test:
    *   Boundary conditions (0, -1, empty lists, null/None inputs).
    *   Invalid inputs (wrong types, unexpected values).
    *   Expected error conditions (e.g., ensure specific exceptions are raised when appropriate).
4.  **Keep Tests Independent:** Each test should run independently without relying on the state or outcome of other tests. Use setup/teardown methods or fixtures to ensure a clean state for each test.
5.  **Clear Naming:** Test function names should clearly describe the scenario being tested (e.g., `test_get_beta_returns_zero_for_spaxx`, `test_process_portfolio_data_handles_missing_quantity`).
6.  **Specific Assertions:** Use the most specific assertion methods available (e.g., `assertEqual`, `assertTrue`, `assertRaises`) rather than generic `assert True`. Provide meaningful failure messages where appropriate.
7.  **Use Fixtures:** Leverage testing framework features (like `pytest` fixtures) to create reusable setup code and test data (e.g., mock objects, sample DataFrames).
8.  **Testing Callbacks (Dash):** Instead of simulating UI interactions, test Dash callbacks directly by providing appropriate input data and asserting the expected output data. This is faster and more stable than UI testing.
9.  **Refactor Tests:** As the main codebase evolves, refactor the tests to keep them relevant, clear, and maintainable.

By adhering to these guidelines, we aim to build a robust and reliable application supported by a strong, maintainable test suite. 