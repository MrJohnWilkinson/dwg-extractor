"""
Tests for logger module enhancements.

Tests cover:
- Log level configuration via environment variable
- JSON output format configuration
- Timing decorator for function timing
- Timing context manager for block timing
- JsonFormatter output structure
"""

import json
import logging
import time

import pytest

from core.logger import (
    JsonFormatter,
    _get_log_format_from_env,
    _get_log_level_from_env,
    set_all_logger_levels,
    timed,
    timed_block,
)


class TestLogLevelConfiguration:
    """Tests for log level configuration from environment variable."""

    def test_setup_logger_default_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify default INFO level when env var not set."""
        # Remove env var if set
        monkeypatch.delenv("DXF_EXTRACTOR_LOG_LEVEL", raising=False)

        # Clear any existing loggers to force re-creation
        logging.getLogger("test_default_level").handlers.clear()

        level = _get_log_level_from_env()
        assert level == logging.INFO

    def test_setup_logger_env_debug_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify DEBUG level from env var."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "DEBUG")

        level = _get_log_level_from_env()
        assert level == logging.DEBUG

    def test_setup_logger_env_warning_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify WARNING level from env var."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "WARNING")

        level = _get_log_level_from_env()
        assert level == logging.WARNING

    def test_setup_logger_env_error_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify ERROR level from env var."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "ERROR")

        level = _get_log_level_from_env()
        assert level == logging.ERROR

    def test_setup_logger_env_critical_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify CRITICAL level from env var."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "CRITICAL")

        level = _get_log_level_from_env()
        assert level == logging.CRITICAL

    def test_setup_logger_env_invalid_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify fallback to INFO for invalid env var."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "INVALID")

        level = _get_log_level_from_env()
        assert level == logging.INFO

    def test_setup_logger_env_lowercase_level(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify case-insensitive level parsing."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_LEVEL", "debug")

        level = _get_log_level_from_env()
        assert level == logging.DEBUG


class TestLogFormatConfiguration:
    """Tests for log format configuration from environment variable."""

    def test_setup_logger_text_format_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify text format is default."""
        monkeypatch.delenv("DXF_EXTRACTOR_LOG_FORMAT", raising=False)

        fmt = _get_log_format_from_env()
        assert fmt == "text"

    def test_setup_logger_json_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify JSON output format when env var set."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_FORMAT", "json")

        fmt = _get_log_format_from_env()
        assert fmt == "json"

    def test_setup_logger_json_format_uppercase(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify case-insensitive format parsing."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_FORMAT", "JSON")

        fmt = _get_log_format_from_env()
        assert fmt == "json"

    def test_setup_logger_invalid_format_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify fallback to text for invalid format."""
        monkeypatch.setenv("DXF_EXTRACTOR_LOG_FORMAT", "xml")

        fmt = _get_log_format_from_env()
        assert fmt == "text"


class TestJsonFormatter:
    """Tests for JsonFormatter class."""

    def test_json_formatter_output_structure(self) -> None:
        """Verify JSON has expected keys."""
        formatter = JsonFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Parse JSON
        data = json.loads(output)

        # Verify required keys
        assert "timestamp" in data
        assert "name" in data
        assert "level" in data
        assert "message" in data

        # Verify values
        assert data["name"] == "test_logger"
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"

    def test_json_formatter_with_exception(self) -> None:
        """Verify JSON includes exc_info when exception present."""
        formatter = JsonFormatter()

        # Create a log record with exception info
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exc_info" in data
        assert "ValueError" in data["exc_info"]
        assert "Test error" in data["exc_info"]

    def test_json_formatter_timestamp_format(self) -> None:
        """Verify timestamp uses ISO 8601 format."""
        formatter = JsonFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        # ISO 8601 format check - should contain T separator and timezone
        timestamp = data["timestamp"]
        assert "T" in timestamp
        assert "+" in timestamp or "Z" in timestamp or timestamp.endswith("+00:00")


class TestTimedDecorator:
    """Tests for the @timed decorator."""

    def test_timed_decorator_logs_duration(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify timing decorator logs function duration."""
        # Create a test logger at DEBUG level
        test_logger = logging.getLogger("test_timed")
        test_logger.setLevel(logging.DEBUG)

        @timed(logger=test_logger, level=logging.DEBUG)
        def slow_function() -> str:
            time.sleep(0.05)  # 50ms
            return "done"

        with caplog.at_level(logging.DEBUG, logger="test_timed"):
            result = slow_function()

        assert result == "done"
        assert "[TIMING]" in caplog.text
        assert "slow_function" in caplog.text
        assert "completed in" in caplog.text
        # Verify timing is logged (should be ~0.05s)
        assert "0.0" in caplog.text  # At least starts with 0.0

    def test_timed_decorator_preserves_function_signature(self) -> None:
        """Verify timing decorator preserves function metadata."""

        @timed()
        def documented_function() -> None:
            """This is a documented function."""
            pass

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_timed_decorator_with_arguments(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify timing decorator works with function arguments."""
        test_logger = logging.getLogger("test_timed_args")
        test_logger.setLevel(logging.DEBUG)

        @timed(logger=test_logger, level=logging.DEBUG)
        def add(a: int, b: int) -> int:
            return a + b

        with caplog.at_level(logging.DEBUG, logger="test_timed_args"):
            result = add(2, 3)

        assert result == 5
        assert "[TIMING]" in caplog.text
        assert "add" in caplog.text


class TestTimedBlockContextManager:
    """Tests for the timed_block context manager."""

    def test_timed_block_logs_duration(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify context manager logs block duration."""
        test_logger = logging.getLogger("test_timed_block")
        test_logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG, logger="test_timed_block"):
            with timed_block("test operation", logger=test_logger, level=logging.DEBUG):
                time.sleep(0.05)  # 50ms

        assert "[TIMING]" in caplog.text
        assert "test operation" in caplog.text
        assert "completed in" in caplog.text

    def test_timed_block_logs_on_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify timing is logged even when exception occurs."""
        test_logger = logging.getLogger("test_timed_block_exc")
        test_logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG, logger="test_timed_block_exc"):
            try:
                with timed_block(
                    "failing operation", logger=test_logger, level=logging.DEBUG
                ):
                    raise ValueError("Test error")
            except ValueError:
                pass

        assert "[TIMING]" in caplog.text
        assert "failing operation" in caplog.text
        assert "completed in" in caplog.text

    def test_timed_block_default_level(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify default level is DEBUG."""
        test_logger = logging.getLogger("test_timed_block_default")
        test_logger.setLevel(logging.DEBUG)

        # Should log at DEBUG level by default
        with caplog.at_level(logging.DEBUG, logger="test_timed_block_default"):
            with timed_block("default level", logger=test_logger):
                pass

        assert "[TIMING]" in caplog.text

        # Clear and test at INFO level - should NOT capture DEBUG logs
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="test_timed_block_default"):
            with timed_block("default level", logger=test_logger):
                pass

        # Should be empty since we're only capturing INFO and above
        assert "[TIMING]" not in caplog.text


class TestSetAllLoggerLevels:
    """Tests for set_all_logger_levels function."""

    def test_updates_core_logger_levels(self) -> None:
        """Verify logger levels are updated for core.* loggers."""
        # Create a core.* logger
        core_logger = logging.getLogger("core.test_module")
        core_logger.setLevel(logging.INFO)

        # Update all logger levels to DEBUG
        set_all_logger_levels(logging.DEBUG)

        # Verify level was updated
        assert core_logger.level == logging.DEBUG

        # Cleanup
        core_logger.handlers.clear()

    def test_updates_main_logger_level(self) -> None:
        """Verify logger level is updated for __main__ logger."""
        # Create __main__ logger
        main_logger = logging.getLogger("__main__")
        main_logger.setLevel(logging.WARNING)

        # Update all logger levels to DEBUG
        set_all_logger_levels(logging.DEBUG)

        # Verify level was updated
        assert main_logger.level == logging.DEBUG

        # Cleanup
        main_logger.handlers.clear()

    def test_updates_handler_levels(self) -> None:
        """Verify handler levels are updated for matching loggers."""
        # Create a core.* logger with a handler
        test_logger = logging.getLogger("core.test_handler")
        handler = logging.StreamHandler()
        handler.setLevel(logging.ERROR)
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.ERROR)

        # Update all logger levels to DEBUG
        set_all_logger_levels(logging.DEBUG)

        # Verify both logger and handler levels were updated
        assert test_logger.level == logging.DEBUG
        assert handler.level == logging.DEBUG

        # Cleanup
        test_logger.handlers.clear()

    def test_ignores_non_app_loggers(self) -> None:
        """Verify non-app loggers are not affected."""
        # Create a non-app logger
        external_logger = logging.getLogger("external.module")
        external_logger.setLevel(logging.WARNING)

        # Update all logger levels to DEBUG
        set_all_logger_levels(logging.DEBUG)

        # Verify external logger was NOT updated
        assert external_logger.level == logging.WARNING

        # Cleanup
        external_logger.handlers.clear()

    def test_updates_multiple_core_loggers(self) -> None:
        """Verify multiple core.* loggers are all updated."""
        # Create multiple core.* loggers
        logger1 = logging.getLogger("core.extractor")
        logger2 = logging.getLogger("core.geometry")
        logger3 = logging.getLogger("core.excel_writer")

        logger1.setLevel(logging.INFO)
        logger2.setLevel(logging.WARNING)
        logger3.setLevel(logging.ERROR)

        # Update all logger levels to DEBUG
        set_all_logger_levels(logging.DEBUG)

        # Verify all were updated
        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.DEBUG
        assert logger3.level == logging.DEBUG

        # Cleanup
        for logger in [logger1, logger2, logger3]:
            logger.handlers.clear()
