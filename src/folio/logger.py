import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logger() -> logging.Logger:
    """Set up and configure the logger

    This function configures the logger to:
    1. Write DEBUG and higher messages to a timestamped log file
    2. Write INFO and higher messages to the console
    3. Prevent duplicate messages by disabling propagation

    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine the logs directory based on the environment
    # In Hugging Face Spaces, use /tmp for logs
    # In other environments, use the logs directory in the current working directory
    is_huggingface = os.environ.get('HF_SPACE') == '1' or os.environ.get('SPACE_ID') is not None

    if is_huggingface:
        logs_dir = Path("/tmp")
    else:
        logs_dir = Path("logs")
        # Only create the directory if we're not in Hugging Face
        logs_dir.mkdir(exist_ok=True)

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
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent propagation to avoid duplicate logs

    # Create handlers
    console_handler = logging.StreamHandler()

    # Try to create a file handler, but fall back to console-only logging if it fails
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            logs_dir / f"folio_{timestamp}.log", encoding="utf-8"
        )
        use_file_handler = True
    except (PermissionError, OSError):
        # If we can't create a log file, log to console only
        logger = logging.getLogger("folio")
        logger.setLevel(logging.DEBUG)
        logger.warning("Could not create log file. Logging to console only.")
        use_file_handler = False

    # Set level for console handler
    console_handler.setLevel(logging.INFO)

    # Create formatters
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    # Only set up file handler if we were able to create it
    if use_file_handler:
        # Set level for file handler
        file_handler.setLevel(logging.DEBUG)

        # Create formatter for file handler
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Add file handler to logger
        logger.addHandler(file_handler)

    logger.info("Logger initialized")
    return logger


# Create and configure logger
logger = setup_logger()
