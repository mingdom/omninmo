import logging
import os
import sys
from pathlib import Path


def setup_logger() -> logging.Logger:
    """Set up and configure the logger

    This function configures the logger to:
    1. Write DEBUG and higher messages to a timestamped log file (except on Hugging Face)
    2. Write messages to the console at the level specified by LOG_LEVEL env var (default: INFO)
    3. Prevent duplicate messages by disabling propagation

    Environment variables:
        LOG_LEVEL: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Default is INFO for normal environments, WARNING for Hugging Face

    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine the logs directory based on the environment
    # In Hugging Face Spaces, use /tmp for logs
    # In other environments, use the logs directory in the current working directory
    is_huggingface = os.environ.get('HF_SPACE') == '1' or os.environ.get('SPACE_ID') is not None

    # Get log level from environment variable
    # Default to WARNING for Hugging Face, INFO for other environments
    log_level_str = os.environ.get('LOG_LEVEL')
    if log_level_str:
        # Use the provided log level
        log_level_str = log_level_str.upper()
        log_level = getattr(logging, log_level_str, None)
        if log_level is None:
            log_level = logging.WARNING if is_huggingface else logging.INFO
    else:
        # Use default log level based on environment
        log_level = logging.WARNING if is_huggingface else logging.INFO

    # Configure root logger to prevent duplicate logs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Only show warnings and errors from other libraries

    # Clear any existing handlers on the root logger
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add a basic handler to the root logger
    root_handler = logging.StreamHandler(sys.stderr)
    root_handler.setFormatter(logging.Formatter("ROOT: %(levelname)s - %(message)s"))
    root_logger.addHandler(root_handler)

    # Create our application logger
    logger = logging.getLogger("folio")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to allow all levels to be logged based on handlers
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

        # Try to create a file handler with a fixed name (overwriting previous logs)
        # This ensures we only keep the latest log file
        try:
            file_handler = logging.FileHandler(
                logs_dir / "folio_latest.log", mode="w", encoding="utf-8"
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

    logger.info("Logger initialized")
    return logger


# Create and configure logger
logger = setup_logger()
