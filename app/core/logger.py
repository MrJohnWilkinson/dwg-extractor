"""
Centralized logging configuration for the DXF Block Extractor application.

This module provides stdout-only logging to enable real-time monitoring by LLM agents
during development and ADW workflow execution. File handlers with immediate flush
are available for debug logging during extraction.

Features:
- Log level configuration via DXF_EXTRACTOR_LOG_LEVEL environment variable
- JSON output format via DXF_EXTRACTOR_LOG_FORMAT environment variable
- Timing decorator and context manager for performance measurement
- FlushingFileHandler for immediate disk writes (tail -f compatible)
- MillisecondFormatter for HH:MM:SS.mmm timestamp format
- create_debug_file_handler() factory for debug log files
"""

import contextlib
import functools
import json
import logging
import os
import sys
import time
from typing import Any, Callable, Generator, ParamSpec, TypeVar


# Environment variable names
LOG_LEVEL_ENV_VAR = "DXF_EXTRACTOR_LOG_LEVEL"
LOG_FORMAT_ENV_VAR = "DXF_EXTRACTOR_LOG_FORMAT"

# Default values
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "text"

# Valid log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Type variables for decorator typing
P = ParamSpec("P")
T = TypeVar("T")


def _get_log_level_from_env() -> int:
    """
    Read log level from environment variable and return corresponding logging constant.

    Reads DXF_EXTRACTOR_LOG_LEVEL environment variable and validates against
    allowed values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    Falls back to logging.INFO if not set or invalid.

    Returns:
        Logging level constant (e.g., logging.DEBUG, logging.INFO)

    Examples:
        >>> os.environ['DXF_EXTRACTOR_LOG_LEVEL'] = 'DEBUG'
        >>> _get_log_level_from_env()
        10  # logging.DEBUG
        >>> os.environ['DXF_EXTRACTOR_LOG_LEVEL'] = 'invalid'
        >>> _get_log_level_from_env()
        20  # logging.INFO (fallback)
    """
    level_str = os.environ.get(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).upper()

    if level_str not in VALID_LOG_LEVELS:
        return logging.INFO

    level: int = getattr(logging, level_str)
    return level


def _get_log_format_from_env() -> str:
    """
    Read log format preference from environment variable.

    Reads DXF_EXTRACTOR_LOG_FORMAT environment variable and returns
    'json' or 'text' (default).

    Returns:
        'json' or 'text'

    Examples:
        >>> os.environ['DXF_EXTRACTOR_LOG_FORMAT'] = 'json'
        >>> _get_log_format_from_env()
        'json'
        >>> os.environ['DXF_EXTRACTOR_LOG_FORMAT'] = 'TEXT'
        >>> _get_log_format_from_env()
        'text'
    """
    format_str = os.environ.get(LOG_FORMAT_ENV_VAR, DEFAULT_LOG_FORMAT).lower()

    if format_str == "json":
        return "json"
    return "text"


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.

    Outputs JSON with keys: timestamp, name, level, message.
    Optionally includes exc_info if an exception is present.
    Uses ISO 8601 format for timestamp.

    Examples:
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(JsonFormatter())
        >>> logger.addHandler(handler)
        >>> logger.info("Test message")
        {"timestamp": "2025-01-17T14:30:22.123456", "name": "mylogger", "level": "INFO", "message": "Test message"}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        from datetime import datetime, timezone

        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class FlushingFileHandler(logging.FileHandler):
    """
    FileHandler that flushes after every emit for immediate visibility.

    Standard FileHandler buffers writes, making `tail -f` unreliable for
    real-time log monitoring. This handler ensures each log message is
    immediately written to disk by calling flush() after every emit().

    Examples:
        >>> handler = FlushingFileHandler("debug.log", mode='w')
        >>> handler.setFormatter(logging.Formatter("%(message)s"))
        >>> logger.addHandler(handler)
        >>> logger.info("Test message")  # Immediately visible in file
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record and immediately flush to disk."""
        super().emit(record)
        self.flush()


class MillisecondFormatter(logging.Formatter):
    """
    Formatter with millisecond precision timestamps.

    Overrides formatTime to produce HH:MM:SS.mmm format for precise
    timing analysis during extraction operations.

    Examples:
        >>> formatter = MillisecondFormatter("%(asctime)s [%(levelname)s] %(message)s")
        >>> # Output: 14:30:22.123 [INFO] Test message
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format timestamp as HH:MM:SS.mmm."""
        ct = self.converter(record.created)
        s = time.strftime("%H:%M:%S", ct)
        return f"{s}.{int(record.msecs):03d}"


def create_debug_file_handler(file_path: str) -> logging.FileHandler:
    """
    Create file handler with DEBUG level and immediate flush.

    Creates a FlushingFileHandler configured for debug logging with
    millisecond-precision timestamps. The handler overwrites any
    existing file and uses UTF-8 encoding.

    Args:
        file_path: Absolute path to log file

    Returns:
        Configured FlushingFileHandler ready to add to logger

    Examples:
        >>> handler = create_debug_file_handler("/path/to/debug.log")
        >>> logging.getLogger().addHandler(handler)
        >>> # Later: handler.close()
    """
    handler = FlushingFileHandler(file_path, mode="w", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        MillisecondFormatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    return handler


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with stdout output only.

    Log level is configurable via DXF_EXTRACTOR_LOG_LEVEL environment variable.
    Output format is configurable via DXF_EXTRACTOR_LOG_FORMAT environment variable.

    Args:
        name: The name for the logger (typically __name__ from the calling module)

    Returns:
        A configured logger instance with stdout handler

    Environment Variables:
        DXF_EXTRACTOR_LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
        DXF_EXTRACTOR_LOG_FORMAT: Set to 'json' for JSON output, defaults to 'text'
    """
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't have one already
    if not logger.handlers:
        # Get configuration from environment
        log_level = _get_log_level_from_env()
        log_format = _get_log_format_from_env()

        # Create stdout handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        # Set formatter based on format preference
        if log_format == "json":
            formatter: logging.Formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(log_level)

    return logger


def timed(
    logger: logging.Logger | None = None, level: int = logging.DEBUG
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator that measures and logs execution time of functions.

    Logs entry with function name and arguments at the specified level,
    and logs exit with function name and elapsed time.

    Args:
        logger: Logger instance to use. If None, uses module-level logger.
        level: Logging level for timing messages (default: DEBUG)

    Returns:
        Decorator function

    Examples:
        >>> @timed()
        ... def slow_function(x):
        ...     time.sleep(1)
        ...     return x * 2

        >>> @timed(logger=my_logger, level=logging.INFO)
        ... def another_function():
        ...     pass

    Output format:
        [TIMING] slow_function completed in 1.234s
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Use provided logger or create one based on function's module
            log = logger or logging.getLogger(func.__module__)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start_time
                log.log(level, f"[TIMING] {func.__name__} completed in {elapsed:.3f}s")

        return wrapper

    return decorator


@contextlib.contextmanager
def timed_block(
    name: str, logger: logging.Logger | None = None, level: int = logging.DEBUG
) -> Generator[None, None, None]:
    """
    Context manager that measures and logs execution time of a code block.

    Args:
        name: Name to identify the block in log messages
        logger: Logger instance to use. If None, uses root logger.
        level: Logging level for timing messages (default: DEBUG)

    Yields:
        None

    Examples:
        >>> with timed_block("color analysis"):
        ...     # expensive operation
        ...     pass

        >>> with timed_block("data processing", logger=my_logger, level=logging.INFO):
        ...     # more expensive operation
        ...     pass

    Output format:
        [TIMING] color analysis completed in 0.456s
    """
    log = logger or logging.getLogger()
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        log.log(level, f"[TIMING] {name} completed in {elapsed:.3f}s")
