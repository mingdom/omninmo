# Logging in Folio

This document describes the logging system in Folio, including configuration options and best practices.

## Overview

Folio uses Python's built-in logging module with environment-specific configuration. The logging system is designed to:

1. Provide appropriate verbosity levels for different environments
2. Support configuration through both environment variables and configuration files
3. Log to both console and file (except in Hugging Face deployments)

## Log Levels

Folio uses standard Python log levels:

| Level | Numeric Value | Description |
|-------|---------------|-------------|
| DEBUG | 10 | Detailed information, typically of interest only when diagnosing problems |
| INFO | 20 | Confirmation that things are working as expected |
| WARNING | 30 | Indication that something unexpected happened, or may happen in the near future |
| ERROR | 40 | Due to a more serious problem, the software has not been able to perform some function |
| CRITICAL | 50 | A serious error, indicating that the program itself may be unable to continue running |

## Configuration

### Environment-Specific Log Levels

Folio automatically detects the environment it's running in and applies the appropriate log level:

```yaml
# From src/folio/folio.yaml
logging:
  # Default log level if environment is not specified
  level: "INFO"  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  file: "folio.log"
  # Environment-specific log levels
  environments:
    local: "INFO"     # For local development (make folio)
    production: "ERROR"  # For production deployment (including Hugging Face)
```

### Environment Detection

The application automatically detects the environment:

- **Local**: Default for development environments
- **Production**: When running in Docker or on Hugging Face Spaces

### Configuration Precedence

Log levels are determined in the following order (highest precedence first):

1. `LOG_LEVEL` environment variable
2. Environment-specific setting from `folio.yaml`
3. Default level from `folio.yaml`
4. Fallback default (INFO for local, ERROR for production)

## Overriding Log Levels

You can override the log level using the `LOG_LEVEL` environment variable:

```bash
# Run with DEBUG level logging
LOG_LEVEL=DEBUG make folio

# Run with WARNING level logging
LOG_LEVEL=WARNING make folio

# Run with ERROR level logging
LOG_LEVEL=ERROR make folio
```

## Log File Location

In local development, logs are written to:

- Console (stderr)
- `logs/folio.log` (or the filename specified in `folio.yaml`)

In production environments (including Hugging Face), logs are written only to the console for privacy reasons.

## Best Practices for Logging

When adding new log statements to the codebase, follow these guidelines:

1. **Use appropriate log levels**:
   - `DEBUG`: Detailed information for troubleshooting
   - `INFO`: Notable events that don't indicate problems
   - `WARNING`: Potential issues that don't prevent operation
   - `ERROR`: Serious problems that prevent some functionality
   - `CRITICAL`: Fatal errors that prevent the application from running

2. **Include context in log messages**:
   - Include relevant identifiers (ticker symbols, file names, etc.)
   - For errors, include the specific operation that failed
   - Use formatted strings for readability

3. **Avoid excessive logging**:
   - Don't log sensitive information
   - Don't log in tight loops without rate limiting
   - Use DEBUG level for detailed operational information

## Example Log Messages

```python
# Good examples of log messages at different levels

# DEBUG: Detailed information for troubleshooting
logger.debug(f"Processing portfolio with {len(df)} rows")
logger.debug(f"Calculated beta of {beta:.2f} for {symbol}")

# INFO: Notable events that don't indicate problems
logger.info(f"Successfully processed {len(groups)} portfolio groups")
logger.info(f"User uploaded portfolio file: {filename}")

# WARNING: Potential issues that don't prevent operation
logger.warning(f"No historical data found for {symbol}, using default beta")
logger.warning("Portfolio contains no stock positions, only cash")

# ERROR: Serious problems that prevent some functionality
logger.error(f"Failed to calculate beta for {symbol}: {e}", exc_info=True)
logger.error(f"Could not process portfolio file: {e}")

# CRITICAL: Fatal errors that prevent the application from running
logger.critical(f"Failed to initialize data fetcher: {e}", exc_info=True)
logger.critical("Database connection failed, application cannot start")
```

## Viewing Logs

### Local Development

In local development, logs are written to both the console and the log file. You can view the log file using:

```bash
cat logs/folio.log
# or
tail -f logs/folio.log  # To follow the log in real-time
```

### Docker Deployment

When running in Docker, you can view logs using:

```bash
make docker-logs
# or
docker logs folio
```

### Hugging Face Deployment

On Hugging Face Spaces, logs can be viewed in the Space's logs tab in the Hugging Face UI.
