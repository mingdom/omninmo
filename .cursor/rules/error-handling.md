# Best Practices for Error Handling
- Fail Fast: Errors should surface quickly rather than creating silent failures that cause problems downstream.
- Only Catch What You Can Handle: Don't catch exceptions unless you can take meaningful action to recover.
- Preserve the Stack Trace: When re-throwing, use raise from or similar mechanisms to maintain the causal chain.
- Error Granularity: Provide specific error types that callers can distinguish between.
- Don't Hide Critical Errors: Logging an error and continuing is appropriate only for non-critical paths.