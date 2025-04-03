# Logging Configuration Improvements

Date: 2025-04-05

## Overview

This update improves the logging configuration in the Folio application to:

1. Make the logging level configurable via environment variable
2. Disable log file creation when running on Hugging Face (for privacy reasons)
3. Set a default log level of WARNING for Hugging Face deployments

## Changes

### 1. Updated Logger Configuration

Modified `src/folio/logger.py` to:

- Read the `LOG_LEVEL` environment variable to determine the logging level
- Default to WARNING level for Hugging Face, INFO for other environments
- Completely disable file logging when running on Hugging Face
- Improve documentation of the logging configuration

Key changes:

```python
# Get log level from environment variable
# Default to WARNING for Hugging Face, INFO for other environments
log_level_str = os.environ.get('LOG_LEVEL')
if log_level_str:
    # Use the provided log level
    log_level_str = log_level_str.upper()
    log_level = getattr(logging, log_level_str, None)
    if log_level is None:
        print(f"Invalid LOG_LEVEL: {log_level_str}. Using default.")
        log_level = logging.WARNING if is_huggingface else logging.INFO
else:
    # Use default log level based on environment
    log_level = logging.WARNING if is_huggingface else logging.INFO

# Set level for console handler based on environment variable
console_handler.setLevel(log_level)

# Only create file handler if not on Hugging Face (for privacy reasons)
if not is_huggingface:
    # File handler setup code...
```

### 2. Updated Docker Configuration

Updated Docker configuration files to set appropriate default log levels:

- `Dockerfile`: Added `ENV LOG_LEVEL=WARNING` for Hugging Face deployment
- `docker-compose.yml` and `docker-compose.test.yml`: Added `LOG_LEVEL=INFO` for local deployments

### 3. Usage

The logging level can now be configured using the `LOG_LEVEL` environment variable:

```bash
# Run with DEBUG level logging
LOG_LEVEL=DEBUG python -m src.folio.app

# Run with WARNING level logging
LOG_LEVEL=WARNING python -m src.folio.app

# Run with ERROR level logging
LOG_LEVEL=ERROR python -m src.folio.app
```

Valid log levels are:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

### 4. Default Behavior

- In Hugging Face environment: 
  - Log level: WARNING (only warnings and errors)
  - No log files are created (console logging only)
  
- In other environments:
  - Log level: INFO (informational messages and above)
  - Log files are created in the `logs/` directory

## Rationale

These changes were made to:

1. Improve privacy by not writing log files in the Hugging Face environment
2. Reduce noise in production logs by defaulting to WARNING level
3. Provide flexibility for developers to adjust logging verbosity as needed
4. Follow best practices for configurable logging in production applications
