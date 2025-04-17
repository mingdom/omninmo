import logging
import os
import sys
from pathlib import Path

import yaml


def setup_logger() -> logging.Logger:
    """Set up and configure the logger

    This function configures the logger to:
    1. Write DEBUG and higher messages to a log file (except on Hugging Face)
    2. Write messages to the console at the specified log level
    3. Prevent duplicate messages by disabling propagation

    Configuration sources (in order of precedence):
    1. Environment variables:
        LOG_LEVEL: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Takes precedence over configuration file settings

    2. Configuration file (src/folio/folio.yaml):
        app.logging.level: The logging level to use
        app.logging.file: The name of the log file

    3. Default values:
        Level: INFO for normal environments, WARNING for Hugging Face
        File: folio_latest.log

    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine the logs directory based on the environment
    # In Hugging Face Spaces, use /tmp for logs
    # In other environments, use the logs directory in the current working directory
    is_huggingface = (
        os.environ.get("HF_SPACE") == "1" or os.environ.get("SPACE_ID") is not None
    )

    # Determine the environment
    is_docker = os.path.exists("/.dockerenv")
    is_debug = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")

    # Determine environment for logging configuration
    if is_huggingface or is_docker:
        # Consider both Hugging Face and Docker as production environments
        environment = "production"
    else:
        environment = "local"

    # Try to load log level from configuration file
    config_log_level = None
    try:
        config_path = os.path.join(os.path.dirname(__file__), "folio.yaml")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
                logging_config = config.get("app", {}).get("logging", {})

                # Try to get environment-specific log level first
                env_log_level_str = logging_config.get("environments", {}).get(
                    environment
                )
                if env_log_level_str:
                    config_log_level = getattr(logging, env_log_level_str.upper(), None)
                    if config_log_level is not None:
                        print(
                            f"Using {environment} environment log level: {env_log_level_str}"
                        )

                # Fall back to default level if environment-specific not found or invalid
                if config_log_level is None:
                    default_log_level_str = logging_config.get("level")
                    if default_log_level_str:
                        config_log_level = getattr(
                            logging, default_log_level_str.upper(), None
                        )
                        if config_log_level is not None:
                            print(f"Using default log level: {default_log_level_str}")
    except Exception as e:
        # If there's an error loading the config, just continue with defaults
        print(f"Error loading config: {e}")

    # Get log level from environment variable (takes precedence over config file)
    # Default to WARNING for Hugging Face, INFO for other environments
    log_level_str = os.environ.get("LOG_LEVEL")
    if log_level_str:
        # Use the provided log level from environment variable
        log_level_str = log_level_str.upper()
        log_level = getattr(logging, log_level_str, None)
        if log_level is None:
            log_level = logging.WARNING if is_huggingface else logging.INFO
    elif config_log_level is not None:
        # Use the log level from the config file
        log_level = config_log_level
    else:
        # Use default log level based on environment
        log_level = logging.WARNING if is_huggingface else logging.INFO

    # Configure root logger to prevent duplicate logs
    root_logger = logging.getLogger()
    root_logger.setLevel(
        logging.WARNING
    )  # Only show warnings and errors from other libraries

    # Clear any existing handlers on the root logger
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add a basic handler to the root logger
    root_handler = logging.StreamHandler(sys.stderr)
    root_handler.setFormatter(logging.Formatter("ROOT: %(levelname)s - %(message)s"))
    root_logger.addHandler(root_handler)

    # Create our application logger
    logger = logging.getLogger("folio")
    logger.setLevel(
        logging.DEBUG
    )  # Set to DEBUG to allow all levels to be logged based on handlers
    logger.propagate = False  # Prevent propagation to avoid duplicate logs

    # Create handlers
    console_handler = logging.StreamHandler()

    # Set level for console handler based on environment variable
    console_handler.setLevel(log_level)

    # Create formatters
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    # Only create file handler if not on Hugging Face (for privacy reasons)
    if not is_huggingface:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Try to get log file name from config
        log_file_name = "folio_latest.log"  # Default name
        try:
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    config_log_file = (
                        config.get("app", {}).get("logging", {}).get("file")
                    )
                    if config_log_file:
                        log_file_name = config_log_file
        except Exception:
            # If there's an error, just use the default name
            pass

        # Try to create a file handler with the configured name (overwriting previous logs)
        # This ensures we only keep the latest log file
        try:
            file_handler = logging.FileHandler(
                logs_dir / log_file_name, mode="w", encoding="utf-8"
            )

            # Set level for file handler
            file_handler.setLevel(logging.DEBUG)

            # Create formatter for file handler
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)

            # Add file handler to logger
            logger.addHandler(file_handler)
        except (PermissionError, OSError):
            # If we can't create a log file, log to console only
            logger.warning("Could not create log file. Logging to console only.")

    # Log the initialization with the configured level
    level_name = logging.getLevelName(log_level)
    logger.info(
        f"Logger initialized with level {level_name} for {environment} environment"
    )
    return logger


# Create and configure logger
logger = setup_logger()
