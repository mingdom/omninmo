import logging
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
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        logs_dir / f"folio_{timestamp}.log", encoding="utf-8"
    )
    console_handler = logging.StreamHandler()

    # Set levels
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO)

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Add formatters to handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialized")
    return logger


# Create and configure logger
logger = setup_logger()
