# Environment-Specific Logging Configuration

**Date:** 2025-04-17
**Author:** Augment AI Assistant

## Overview

This update enhances the logging configuration in the Folio application to support environment-specific log levels. The application now automatically detects the environment it's running in and applies the appropriate log level from the configuration file.

## Changes Implemented

### 1. Enhanced Configuration File

Updated `src/folio/folio.yaml` to include environment-specific log levels:

```yaml
logging:
  # Default log level if environment is not specified
  level: "INFO"  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  file: "folio.log"
  # Environment-specific log levels
  environments:
    local: "INFO"     # For local development (make folio)
    production: "ERROR"  # For production deployment (including Hugging Face)
```

### 2. Environment Detection

Enhanced `src/folio/logger.py` to detect the current environment:

- **Local**: Default for development environments
- **Production**: When running in Docker or on Hugging Face Spaces

### 3. Log Level Selection

Updated the logger to select the log level based on the detected environment:

1. First, try to use the environment-specific log level from `folio.yaml`
2. If not found, fall back to the default level from `folio.yaml`
3. If specified, the `LOG_LEVEL` environment variable still takes precedence over all configuration file settings

### 4. Makefile Updates

Updated the Makefile to use INFO as the default log level for local development:

```makefile
LOG_LEVEL=$(if $(log),$(log),INFO)
```

### 5. Dockerfile Updates

Removed the hardcoded `LOG_LEVEL=WARNING` from the Dockerfile, as the log level is now determined from the configuration file based on the detected environment.

## Benefits

1. **Environment-Appropriate Logging**: Different log levels for different environments
   - **Local**: More verbose logging (INFO) for development and debugging
   - **Production**: Less verbose logging (ERROR) to reduce log file size and focus on critical issues (applies to both Docker and Hugging Face deployments)

2. **Centralized Configuration**: All log level settings are now in one place (`folio.yaml`)

3. **Flexibility**: Still supports overriding via environment variables when needed

## Usage

### Default Behavior

- When running with `make folio` or `make portfolio`, the application will use the "local" environment log level (INFO)
- When deployed to production (Docker or Hugging Face Spaces), it will use the "production" environment log level (ERROR)

### Overriding Log Levels

You can still override the log level using the `LOG_LEVEL` environment variable:

```bash
LOG_LEVEL=DEBUG make folio
```

This will take precedence over any configuration file settings.

## Future Improvements

1. **Component-Level Log Control**: Allow different log levels for different components
2. **Dynamic Log Level Changes**: Support changing log levels at runtime without restarting the application
3. **Structured Logging**: Implement structured logging for better log analysis
