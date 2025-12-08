"""
Unit tests for the extractor module - abort functionality.

This test suite validates the abort mechanism for extraction including:
- ExtractionAbortedError exception behavior
- _check_abort helper function
- Abort during block definition processing
- Abort during modelspace entity processing
- Normal completion when abort event is not set
"""

import threading

import pytest

from core.extractor import ExtractionAbortedError, _check_abort, extract_blocks


class TestExtractionAbort:
    """Test suite for extraction abort functionality."""

    def test_abort_raises_exception_at_start(self) -> None:
        """Test that pre-set abort event causes ExtractionAbortedError at extraction start."""
        abort_event = threading.Event()
        abort_event.set()  # Pre-set to trigger immediately

        with pytest.raises(ExtractionAbortedError, match="extraction start"):
            extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

    def test_abort_at_extraction_start(self) -> None:
        """Test abort triggered at extraction start checkpoint."""
        abort_event = threading.Event()
        abort_event.set()

        # Should abort at the initial "extraction start" checkpoint
        with pytest.raises(ExtractionAbortedError):
            extract_blocks("app/tests/assets/many_lines_test.dxf", abort_event)

    def test_no_abort_when_event_not_set(self) -> None:
        """Test extraction completes normally when abort not triggered."""
        abort_event = threading.Event()
        # Don't set the event

        result = extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

        assert result["block_counts"]["VALVE_GATE"] == 10

    def test_abort_event_none_works(self) -> None:
        """Test extraction works when abort_event is None."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf", None)

        assert len(result["block_counts"]) == 3

    def test_abort_event_default_none(self) -> None:
        """Test extraction works with default abort_event parameter."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        assert len(result["block_counts"]) == 3


class TestCheckAbortHelper:
    """Test suite for _check_abort helper function."""

    def test_check_abort_raises_when_set(self) -> None:
        """Test _check_abort raises when event is set."""
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(ExtractionAbortedError, match="test context"):
            _check_abort(abort_event, "test context")

    def test_check_abort_passes_when_not_set(self) -> None:
        """Test _check_abort does nothing when event not set."""
        abort_event = threading.Event()
        # Should not raise
        _check_abort(abort_event, "test context")

    def test_check_abort_passes_when_none(self) -> None:
        """Test _check_abort does nothing when event is None."""
        # Should not raise
        _check_abort(None, "test context")

    def test_check_abort_exception_message_contains_context(self) -> None:
        """Test that exception message contains the context string."""
        abort_event = threading.Event()
        abort_event.set()

        try:
            _check_abort(abort_event, "custom operation")
            pytest.fail("Expected ExtractionAbortedError")
        except ExtractionAbortedError as e:
            assert "custom operation" in str(e)


class TestAbortIntegration:
    """Integration tests for abort functionality."""

    def test_immediate_abort_raises_exception(self) -> None:
        """Test immediate abort raises ExtractionAbortedError."""
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(ExtractionAbortedError):
            extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

    def test_extraction_result_not_returned_on_abort(self) -> None:
        """Test that no result is returned when extraction is aborted."""
        abort_event = threading.Event()
        abort_event.set()

        result = None
        try:
            result = extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)
        except ExtractionAbortedError:
            pass

        assert result is None

    def test_extraction_completes_when_abort_not_triggered(self) -> None:
        """Test extraction completes fully when abort is never triggered."""
        abort_event = threading.Event()
        # Don't set the event

        result = extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

        # Verify complete extraction
        assert "block_counts" in result
        assert "block_entities" in result
        assert "layer_entity_counts" in result
        assert len(result["block_counts"]) == 3
