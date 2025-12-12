"""
Tests for logger module enhancements.

Tests cover:
- Log level configuration via environment variable
- JSON output format configuration
- Timing decorator for function timing
- Timing context manager for block timing
- JsonFormatter output structure
- FlushingFileHandler immediate disk writes
- MillisecondFormatter timestamp format
- create_debug_file_handler factory function
- QueueHandler for GUI log viewer
- create_queue_handler factory function
"""

import json
import logging
import queue
import re
import time
from pathlib import Path

import pytest

from core.logger import (
    FlushingFileHandler,
    JsonFormatter,
    MillisecondFormatter,
    QueueHandler,
    _get_log_format_from_env,
    _get_log_level_from_env,
    create_debug_file_handler,
    create_queue_handler,
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


class TestFlushingFileHandler:
    """Tests for FlushingFileHandler class."""

    def test_flushing_file_handler_immediate_write(self, tmp_path: Path) -> None:
        """Verify FlushingFileHandler writes immediately without explicit flush."""
        log_file = tmp_path / "test.log"
        handler = FlushingFileHandler(str(log_file), mode="w")
        handler.setFormatter(logging.Formatter("%(message)s"))

        # Use a unique logger name to avoid conflicts
        logger = logging.getLogger("test_flush_immediate")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("test message")

        # File should contain message immediately (no flush() call needed)
        content = log_file.read_text()
        assert "test message" in content

        handler.close()
        logger.handlers.clear()

    def test_flushing_file_handler_mode_write(self, tmp_path: Path) -> None:
        """Verify handler uses write mode (overwrites existing)."""
        log_file = tmp_path / "test.log"

        # Write initial content
        log_file.write_text("existing content")

        handler = FlushingFileHandler(str(log_file), mode="w")
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_flush_mode")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("new message")
        handler.close()
        logger.handlers.clear()

        # Existing content should be overwritten
        content = log_file.read_text()
        assert "existing content" not in content
        assert "new message" in content

    def test_flushing_file_handler_encoding_utf8(self, tmp_path: Path) -> None:
        """Verify UTF-8 encoding is used for special characters."""
        log_file = tmp_path / "test.log"
        handler = FlushingFileHandler(str(log_file), mode="w", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_flush_utf8")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Log message with special characters
        logger.info("Test with special chars: \u00e9\u00e0\u00fc\u00f1")
        handler.close()
        logger.handlers.clear()

        content = log_file.read_text(encoding="utf-8")
        assert "\u00e9\u00e0\u00fc\u00f1" in content

    def test_flushing_file_handler_multiple_messages(self, tmp_path: Path) -> None:
        """Verify multiple messages are written immediately."""
        log_file = tmp_path / "test.log"
        handler = FlushingFileHandler(str(log_file), mode="w")
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_flush_multi")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("message 1")
        content1 = log_file.read_text()
        assert "message 1" in content1

        logger.info("message 2")
        content2 = log_file.read_text()
        assert "message 1" in content2
        assert "message 2" in content2

        handler.close()
        logger.handlers.clear()


class TestMillisecondFormatter:
    """Tests for MillisecondFormatter class."""

    def test_millisecond_formatter_time_format(self) -> None:
        """Verify timestamp uses HH:MM:SS.mmm format."""
        formatter = MillisecondFormatter("%(asctime)s %(message)s")

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

        # Should match HH:MM:SS.mmm format at start of string
        assert re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}", output)

    def test_millisecond_formatter_valid_time_values(self) -> None:
        """Verify formatted time has valid hour, minute, second values."""
        formatter = MillisecondFormatter("%(asctime)s")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        match = re.match(r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3})", output)

        assert match is not None
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        millis = int(match.group(4))

        assert 0 <= hours <= 23
        assert 0 <= minutes <= 59
        assert 0 <= seconds <= 59
        assert 0 <= millis <= 999

    def test_millisecond_formatter_with_level_and_message(self) -> None:
        """Verify formatter works with full format string."""
        formatter = MillisecondFormatter("%(asctime)s [%(levelname)s] %(message)s")

        record = logging.LogRecord(
            name="test_logger",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Debug message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Verify full format
        assert re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} \[DEBUG\] Debug message$", output)


class TestCreateDebugFileHandler:
    """Tests for create_debug_file_handler factory function."""

    def test_create_debug_file_handler_creates_handler(self, tmp_path: Path) -> None:
        """Verify factory returns FlushingFileHandler."""
        log_file = tmp_path / "debug.log"
        handler = create_debug_file_handler(str(log_file))

        assert isinstance(handler, FlushingFileHandler)
        handler.close()

    def test_create_debug_file_handler_debug_level(self, tmp_path: Path) -> None:
        """Verify handler is set to DEBUG level."""
        log_file = tmp_path / "debug.log"
        handler = create_debug_file_handler(str(log_file))

        assert handler.level == logging.DEBUG
        handler.close()

    def test_create_debug_file_handler_format(self, tmp_path: Path) -> None:
        """Verify handler uses millisecond timestamp format."""
        log_file = tmp_path / "debug.log"
        handler = create_debug_file_handler(str(log_file))

        logger = logging.getLogger("test_debug_format")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug("test message")
        handler.close()
        logger.handlers.clear()

        content = log_file.read_text()
        # Should match HH:MM:SS.mmm [LEVEL] message format
        assert re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} \[DEBUG\] test message", content)

    def test_create_debug_file_handler_creates_file(self, tmp_path: Path) -> None:
        """Verify handler creates log file."""
        log_file = tmp_path / "debug.log"
        assert not log_file.exists()

        handler = create_debug_file_handler(str(log_file))

        logger = logging.getLogger("test_debug_create")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("test")
        handler.close()
        logger.handlers.clear()

        assert log_file.exists()

    def test_create_debug_file_handler_all_levels(self, tmp_path: Path) -> None:
        """Verify handler captures all log levels at DEBUG and above."""
        log_file = tmp_path / "debug.log"
        handler = create_debug_file_handler(str(log_file))

        logger = logging.getLogger("test_debug_levels")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warning msg")
        logger.error("error msg")
        handler.close()
        logger.handlers.clear()

        content = log_file.read_text()
        assert "debug msg" in content
        assert "info msg" in content
        assert "warning msg" in content
        assert "error msg" in content

    def test_create_debug_file_handler_utf8_encoding(self, tmp_path: Path) -> None:
        """Verify handler uses UTF-8 encoding."""
        log_file = tmp_path / "debug.log"
        handler = create_debug_file_handler(str(log_file))

        logger = logging.getLogger("test_debug_utf8")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Unicode: \u4e2d\u6587\u65e5\u672c\u8a9e\ud55c\uad6d\uc5b4")
        handler.close()
        logger.handlers.clear()

        content = log_file.read_text(encoding="utf-8")
        assert "\u4e2d\u6587\u65e5\u672c\u8a9e\ud55c\uad6d\uc5b4" in content


class TestQueueHandler:
    """Tests for QueueHandler class."""

    def test_queue_handler_puts_messages(self) -> None:
        """Verify QueueHandler puts formatted messages into queue."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = QueueHandler(log_queue)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_queue_puts")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("test message")

        # Verify message is in queue
        assert not log_queue.empty()
        level, msg = log_queue.get_nowait()
        assert level == logging.INFO
        assert msg == "test message"

        logger.handlers.clear()

    def test_queue_handler_handles_full_queue(self) -> None:
        """Verify QueueHandler drops messages when queue is full (no exception)."""
        # Create queue with maxsize=1
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue(maxsize=1)
        handler = QueueHandler(log_queue)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_queue_full")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # First message should succeed
        logger.info("message 1")

        # Second message should be dropped silently (no exception)
        logger.info("message 2")  # This should not raise

        # Queue should only have first message
        assert log_queue.qsize() == 1
        level, msg = log_queue.get_nowait()
        assert msg == "message 1"

        logger.handlers.clear()

    def test_queue_handler_message_format(self) -> None:
        """Verify tuple contains (levelno, formatted_string)."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = QueueHandler(log_queue)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )

        logger = logging.getLogger("test_queue_format")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.warning("test warning")

        level, msg = log_queue.get_nowait()
        assert level == logging.WARNING
        assert "[WARNING]" in msg
        assert "test warning" in msg

        logger.handlers.clear()

    def test_queue_handler_all_levels(self) -> None:
        """Verify QueueHandler captures all log levels."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = QueueHandler(log_queue)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_queue_levels")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")

        messages = []
        while not log_queue.empty():
            level, msg = log_queue.get_nowait()
            messages.append((level, msg))

        assert len(messages) == 4
        assert messages[0] == (logging.DEBUG, "debug")
        assert messages[1] == (logging.INFO, "info")
        assert messages[2] == (logging.WARNING, "warning")
        assert messages[3] == (logging.ERROR, "error")

        logger.handlers.clear()


class TestCreateQueueHandler:
    """Tests for create_queue_handler factory function."""

    def test_create_queue_handler_returns_handler(self) -> None:
        """Verify factory returns QueueHandler instance."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        assert isinstance(handler, QueueHandler)

    def test_create_queue_handler_debug_level(self) -> None:
        """Verify handler is set to DEBUG level."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        assert handler.level == logging.DEBUG

    def test_create_queue_handler_format(self) -> None:
        """Verify handler uses HH:MM:SS timestamp format."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        logger = logging.getLogger("test_queue_handler_format")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("test message")

        level, msg = log_queue.get_nowait()
        # Should match HH:MM:SS [LEVEL] message format
        assert re.match(r"^\d{2}:\d{2}:\d{2} \[INFO\] test message$", msg)

        logger.handlers.clear()

    def test_create_queue_handler_captures_all_levels(self) -> None:
        """Verify handler captures DEBUG and above."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        logger = logging.getLogger("test_queue_handler_levels")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warning msg")
        logger.error("error msg")

        messages = []
        while not log_queue.empty():
            level, msg = log_queue.get_nowait()
            messages.append(msg)

        assert len(messages) == 4
        assert "debug msg" in messages[0]
        assert "info msg" in messages[1]
        assert "warning msg" in messages[2]
        assert "error msg" in messages[3]

        logger.handlers.clear()


class TestDynamicLogLevelSetting:
    """Tests for dynamic log level setting pattern used by GUI dropdown."""

    def test_setting_logger_level_dynamically_affects_capture(self) -> None:
        """Verify setting logger level dynamically changes message capture."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        logger = logging.getLogger("test_dynamic_level")
        logger.handlers.clear()
        logger.addHandler(handler)

        # Start at INFO level - DEBUG messages should not be captured
        logger.setLevel(logging.INFO)
        logger.debug("debug should not appear")

        assert log_queue.empty(), "DEBUG message captured at INFO level"

        # Change to DEBUG level - DEBUG messages should now be captured
        logger.setLevel(logging.DEBUG)
        logger.debug("debug should appear")

        assert not log_queue.empty(), "DEBUG message not captured at DEBUG level"
        level, msg = log_queue.get_nowait()
        assert level == logging.DEBUG
        assert "debug should appear" in msg

        logger.handlers.clear()

    def test_setting_debug_level_captures_debug_messages(self) -> None:
        """Verify DEBUG level captures DEBUG messages."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        logger = logging.getLogger("test_debug_capture")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.debug("debug message")
        logger.info("info message")

        messages = []
        while not log_queue.empty():
            level, msg = log_queue.get_nowait()
            messages.append((level, msg))

        assert len(messages) == 2
        assert messages[0][0] == logging.DEBUG
        assert "debug message" in messages[0][1]
        assert messages[1][0] == logging.INFO
        assert "info message" in messages[1][1]

        logger.handlers.clear()

    def test_setting_info_level_filters_debug_messages(self) -> None:
        """Verify INFO level filters out DEBUG messages."""
        log_queue: queue.Queue[tuple[int, str]] = queue.Queue()
        handler = create_queue_handler(log_queue)

        logger = logging.getLogger("test_info_filter")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.debug("debug message")
        logger.info("info message")

        messages = []
        while not log_queue.empty():
            level, msg = log_queue.get_nowait()
            messages.append((level, msg))

        # Only INFO message should be captured
        assert len(messages) == 1
        assert messages[0][0] == logging.INFO
        assert "info message" in messages[0][1]

        logger.handlers.clear()

    def test_getattr_logging_level_conversion(self) -> None:
        """Verify getattr(logging, value) pattern works correctly."""
        # This is the pattern used in _on_log_level_change()
        assert getattr(logging, "DEBUG") == logging.DEBUG
        assert getattr(logging, "INFO") == logging.INFO
        assert getattr(logging, "WARNING") == logging.WARNING
        assert getattr(logging, "ERROR") == logging.ERROR
        assert getattr(logging, "CRITICAL") == logging.CRITICAL
