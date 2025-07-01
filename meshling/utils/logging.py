"""Logging configuration for Meshling."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging for the application.

    Args:
        debug: Enable debug level logging
        log_file: Path to log file, if None logs only to console
    """
    # Set log level
    level = logging.DEBUG if debug else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for file
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from external libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("serial").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
