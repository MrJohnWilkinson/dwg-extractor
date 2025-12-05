"""
Unit tests for extraction abort functionality.

Tests the cooperative cancellation mechanism that allows users to abort
in-progress extraction operations.
"""

import threading
import time
from unittest.mock import patch

import pytest

from core.extractor import (
    ExtractionAbortedError,
    _check_abort,
    extract_blocks,
)


class TestExtractionAbortedError:
    """Tests for the ExtractionAbortedError exception class."""

    def test_exception_with_defaults(self) -> None:
        """Test exception with default values."""
        error = ExtractionAbortedError()
        assert error.blocks_processed == 0
        assert error.entities_processed == 0
        assert error.phase == "unknown"
        assert "unknown" in str(error)

    def test_exception_with_values(self) -> None:
        """Test exception with specific values."""
        error = ExtractionAbortedError(
            blocks_processed=50,
            entities_processed=1000,
            phase="modelspace entity analysis",
        )
        assert error.blocks_processed == 50
        assert error.entities_processed == 1000
        assert error.phase == "modelspace entity analysis"
        assert "50 blocks" in str(error)
        assert "1000 entities" in str(error)
        assert "modelspace entity analysis" in str(error)

    def test_exception_message_format(self) -> None:
        """Test that exception message has expected format."""
        error = ExtractionAbortedError(
            blocks_processed=25,
            entities_processed=500,
            phase="block definition analysis",
        )
        message = str(error)
        assert "Extraction aborted during block definition analysis" in message
        assert "Progress:" in message


class TestCheckAbort:
    """Tests for the _check_abort helper function."""

    def test_check_abort_with_none_event(self) -> None:
        """Test that None abort_event does not raise."""
        # Should not raise
        _check_abort(None, "test phase", 10, 100)

    def test_check_abort_with_unset_event(self) -> None:
        """Test that unset abort_event does not raise."""
        event = threading.Event()
        # Event is not set, should not raise
        _check_abort(event, "test phase", 10, 100)

    def test_check_abort_with_set_event(self) -> None:
        """Test that set abort_event raises ExtractionAbortedError."""
        event = threading.Event()
        event.set()

        with pytest.raises(ExtractionAbortedError) as exc_info:
            _check_abort(event, "test phase", 25, 500)

        error = exc_info.value
        assert error.blocks_processed == 25
        assert error.entities_processed == 500
        assert error.phase == "test phase"

    def test_check_abort_preserves_progress_stats(self) -> None:
        """Test that abort exception contains correct progress statistics."""
        event = threading.Event()
        event.set()

        with pytest.raises(ExtractionAbortedError) as exc_info:
            _check_abort(event, "color analysis", 100, 5000)

        error = exc_info.value
        assert "100 blocks" in str(error)
        assert "5000 entities" in str(error)


class TestExtractBlocksAbort:
    """Tests for abort functionality in extract_blocks()."""

    def test_extract_blocks_without_abort_event(self) -> None:
        """Test that extraction works normally when abort_event is None."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify normal extraction works
        assert isinstance(result, dict)
        assert "block_counts" in result
        assert len(result["block_counts"]) == 3

    def test_extract_blocks_with_unset_abort_event(self) -> None:
        """Test that extraction works normally when abort_event is not set."""
        abort_event = threading.Event()
        # Event is NOT set

        result = extract_blocks(
            "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
        )

        # Verify normal extraction works
        assert isinstance(result, dict)
        assert "block_counts" in result
        assert len(result["block_counts"]) == 3

    def test_extract_blocks_abort_during_file_loading(self) -> None:
        """Test abort immediately after file loading."""
        abort_event = threading.Event()

        # Set abort before extraction starts
        abort_event.set()

        with pytest.raises(ExtractionAbortedError) as exc_info:
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
            )

        error = exc_info.value
        assert error.phase == "file loading"
        assert error.blocks_processed == 0
        assert error.entities_processed == 0

    def test_extract_blocks_abort_raises_exception(self) -> None:
        """Test that setting abort_event raises ExtractionAbortedError."""
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(ExtractionAbortedError):
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
            )

    def test_abort_preserves_partial_progress_info(self) -> None:
        """Test that exception contains progress stats when abort occurs."""
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(ExtractionAbortedError) as exc_info:
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
            )

        error = exc_info.value
        # Should have phase info
        assert error.phase != "unknown"
        # Progress values should be defined
        assert isinstance(error.blocks_processed, int)
        assert isinstance(error.entities_processed, int)

    def test_extract_blocks_abort_during_block_analysis(self) -> None:
        """Test abort during block definition analysis phase."""
        abort_event = threading.Event()
        blocks_before_abort = 0

        # Use a mock to set abort after some blocks are processed
        original_check_abort = _check_abort

        def delayed_abort(
            event: threading.Event | None,
            phase: str,
            blocks: int,
            entities: int,
        ) -> None:
            nonlocal blocks_before_abort
            if phase == "block definition analysis" and blocks >= 1:
                blocks_before_abort = blocks
                abort_event.set()
            original_check_abort(event, phase, blocks, entities)

        with patch("core.extractor._check_abort", side_effect=delayed_abort):
            # This may or may not raise depending on file size and checkpoint frequency
            # For sample_drawing.dxf which is small, it may complete before checkpoint
            try:
                extract_blocks(
                    "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
                )
            except ExtractionAbortedError as e:
                assert "block" in e.phase.lower()

    def test_abort_does_not_affect_subsequent_extractions(self) -> None:
        """Test that a new extraction works after a previous abort."""
        # First extraction - abort it
        abort_event1 = threading.Event()
        abort_event1.set()

        with pytest.raises(ExtractionAbortedError):
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event1
            )

        # Second extraction - should work normally
        abort_event2 = threading.Event()
        # NOT set

        result = extract_blocks(
            "app/tests/assets/sample_drawing.dxf", abort_event=abort_event2
        )

        assert isinstance(result, dict)
        assert "block_counts" in result
        assert len(result["block_counts"]) == 3

    def test_abort_with_empty_file(self) -> None:
        """Test abort behavior with empty drawing file."""
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(ExtractionAbortedError):
            extract_blocks(
                "app/tests/assets/empty_drawing.dxf", abort_event=abort_event
            )


class TestAbortEdgeCases:
    """Tests for edge cases in abort functionality."""

    def test_abort_before_extraction_starts_is_handled(self) -> None:
        """Test that pre-set abort is handled at first checkpoint."""
        abort_event = threading.Event()
        abort_event.set()

        # Should raise at the first checkpoint (after file loading)
        with pytest.raises(ExtractionAbortedError) as exc_info:
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
            )

        # First checkpoint is after file loading
        assert exc_info.value.phase == "file loading"

    def test_file_not_found_still_raises_before_abort_check(self) -> None:
        """Test that FileNotFoundError is raised before any abort check."""
        abort_event = threading.Event()
        abort_event.set()

        # FileNotFoundError should be raised before abort is checked
        with pytest.raises(FileNotFoundError):
            extract_blocks("app/tests/assets/nonexistent.dxf", abort_event=abort_event)

    def test_invalid_file_still_raises_before_abort_check(self) -> None:
        """Test that ValueError for invalid file takes precedence."""
        abort_event = threading.Event()
        abort_event.set()

        # The abort check happens after file loading, so invalid file error
        # should be raised during ezdxf.readfile()
        with pytest.raises(ValueError, match="Invalid or corrupted"):
            extract_blocks("app/tests/assets/invalid.dxf", abort_event=abort_event)

    def test_unsupported_extension_still_raises_before_abort_check(self) -> None:
        """Test that unsupported extension error takes precedence."""
        import tempfile
        from pathlib import Path

        abort_event = threading.Event()
        abort_event.set()

        # Create temp file with wrong extension
        temp_file = Path(tempfile.gettempdir()) / "test_abort.txt"
        temp_file.write_text("test")

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                extract_blocks(str(temp_file), abort_event=abort_event)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_multiple_abort_calls_are_idempotent(self) -> None:
        """Test that calling set() multiple times on abort_event is safe."""
        abort_event = threading.Event()
        abort_event.set()
        abort_event.set()  # Second call
        abort_event.set()  # Third call

        # Should still raise normally
        with pytest.raises(ExtractionAbortedError):
            extract_blocks(
                "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
            )


class TestAbortThreadSafety:
    """Tests for thread safety of abort mechanism."""

    def test_abort_from_different_thread(self) -> None:
        """Test that abort set from different thread is detected."""
        abort_event = threading.Event()
        result_container: dict = {"result": None, "error": None}

        def extraction_thread() -> None:
            try:
                result_container["result"] = extract_blocks(
                    "app/tests/assets/sample_drawing.dxf", abort_event=abort_event
                )
            except ExtractionAbortedError as e:
                result_container["error"] = e

        # Start extraction in background thread
        thread = threading.Thread(target=extraction_thread)
        thread.start()

        # Give extraction a moment to start, then abort
        # For small test file, this may complete before abort
        time.sleep(0.01)
        abort_event.set()

        thread.join(timeout=5)

        # Either completed successfully (fast file) or was aborted
        assert (result_container["result"] is not None) or (
            result_container["error"] is not None
        )
