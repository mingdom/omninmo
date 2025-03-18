# Rule: Focus on the Task

## Description

This rule reminds the AI to focus on the specific task requested by the user and avoid making unrequested changes or additions to the code or configuration. The AI should:

1.  **Address only the user's explicit request.** Do not introduce new features, refactor code beyond the scope of the request, or change configurations without being asked.
2.  **Ask clarifying questions if needed.** If the user's request is ambiguous or could have multiple interpretations, ask for clarification before proceeding.
3.  **Explain any assumptions.** If any assumptions are made to fulfill the request, clearly state them.
4.  **Do not ignore errors without explicit permission.** If an error is encountered, debug it fully and propose a solution. Do not hide errors by swallowing them or adding ignore rules without the user's consent.
5. **Do the minimal change.** When making changes, do the absolute minimum required to fulfill the request.

## Examples

**Bad:** User asks to fix a specific linting error. The AI fixes the error but also refactors unrelated code, adds new features, and changes the linter configuration to ignore similar errors in the future.

**Good:** User asks to fix a specific linting error. The AI fixes only that error and explains the fix.

**Bad:** User asks to add a new function. The AI adds the function and also changes the logging configuration and adds a new dependency without being asked.

**Good:** User asks to add a new function. The AI adds the function and asks if any related configuration changes are needed.

## Glob Pattern

This rule applies to all files. 