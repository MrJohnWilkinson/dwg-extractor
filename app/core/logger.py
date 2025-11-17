"""
Centralized logging configuration for the DWG Block Extractor application.

This module provides stdout-only logging to enable real-time monitoring by LLM agents
during development and ADW workflow execution. No file handlers are used to ensure
immediate visibility of all log messages.
"""

import logging
import sys


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with stdout output only.

    Args:
        name: The name for the logger (typically __name__ from the calling module)

    Returns:
        A configured logger instance with stdout handler
    """
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't have one already
    if not logger.handlers:
        # Create stdout handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Set format
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
