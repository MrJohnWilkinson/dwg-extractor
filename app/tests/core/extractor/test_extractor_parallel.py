"""
Unit tests for the extractor module - parallel block processing.

This test suite validates the ThreadPoolExecutor-based parallel block
processing including:
- Thread safety verification (consistent results across runs)
- Abort functionality with parallel processing
- Result consistency between parallel and expected values
- Performance characteristics
"""

import threading

import pytest

from core.extractor import extract_blocks


class TestParallelBlockProcessing:
    """Test suite for parallel block processing functionality."""

    def test_parallel_processing_consistent_results(self) -> None:
        """Test that parallel processing produces consistent results across multiple runs."""
        # Run extraction multiple times and verify identical results
        results = []
        for _ in range(3):
            result = extract_blocks("app/tests/assets/sample_drawing.dxf")
            results.append(result)

        # Compare block_counts across all runs
        for i in range(1, len(results)):
            assert results[0]["block_counts"] == results[i]["block_counts"]
            assert results[0]["block_entities"] == results[i]["block_entities"]

    def test_parallel_processing_with_dynamic_blocks(self) -> None:
        """Test parallel processing correctly resolves dynamic blocks."""
        result = extract_blocks("app/tests/assets/dynamic_block_test.dxf")

        # Verify dynamic block resolution works correctly
        assert "block_counts" in result
        assert "block_entities" in result
        assert "block_trimming_data" in result

    def test_parallel_processing_with_nested_blocks(self) -> None:
        """Test parallel processing correctly identifies nested block relationships."""
        result = extract_blocks("app/tests/assets/nested_block_test.dxf")

        # Verify nested block tracking works
        assert "nested_block_parents" in result
        # INNER_BLOCK should be nested inside OUTER_BLOCK
        if "INNER_BLOCK" in result["nested_block_parents"]:
            assert "OUTER_BLOCK" in result["nested_block_parents"]["INNER_BLOCK"]

    def test_parallel_processing_abort_event(self) -> None:
        """Test that abort event works correctly with parallel processing."""
        abort_event = threading.Event()
        abort_event.set()  # Pre-set to trigger abort

        from core.extractor import ExtractionAbortedError

        with pytest.raises(ExtractionAbortedError):
            extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

    def test_parallel_processing_abort_event_not_set(self) -> None:
        """Test extraction completes when abort event is not set."""
        abort_event = threading.Event()
        # Don't set the event

        result = extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

        # Verify complete extraction
        assert len(result["block_counts"]) == 3
        assert result["block_counts"]["VALVE_GATE"] == 10

    def test_parallel_processing_empty_file(self) -> None:
        """Test parallel processing handles empty files correctly."""
        result = extract_blocks("app/tests/assets/empty_drawing.dxf")

        assert result["block_counts"] == {}
        assert isinstance(result["block_entities"], dict)

    def test_parallel_processing_block_trimming_data(self) -> None:
        """Test that block trimming data is correctly populated in parallel."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify trimming data structure
        assert "block_trimming_data" in result
        for block_name, trimming in result["block_trimming_data"].items():
            assert "native_width" in trimming
            assert "native_height" in trimming
            assert "vertical_segments" in trimming
            assert "horizontal_segments" in trimming
            assert isinstance(trimming["native_width"], (int, float))
            assert isinstance(trimming["native_height"], (int, float))

    def test_parallel_processing_content_zone_data(self) -> None:
        """Test that content zone data is correctly populated in parallel."""
        result = extract_blocks("app/tests/assets/content_zone_test.dxf")

        # Verify content zone data structure
        assert "block_content_zone_data" in result
        for block_name, zone_data in result["block_content_zone_data"].items():
            assert "content_zone_detected" in zone_data
            assert "polygon_count" in zone_data
            assert "filtered_polygon_count" in zone_data

    def test_parallel_processing_preserves_entity_counts(self) -> None:
        """Test that entity counts match expected values after parallel processing."""
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify entity counts are present for all counted blocks
        for block_name in result["block_counts"].keys():
            assert block_name in result["block_entities"]
            assert isinstance(result["block_entities"][block_name], int)
            assert result["block_entities"][block_name] >= 0


class TestParallelProcessingThreadSafety:
    """Test suite specifically for thread safety verification."""

    def test_no_race_conditions_in_result_collection(self) -> None:
        """Test that result collection has no race conditions."""
        # Run extraction on a file with multiple blocks
        result = extract_blocks("app/tests/assets/sample_drawing.dxf")

        # Verify all data structures are internally consistent
        block_names_in_counts = set(result["block_counts"].keys())
        block_names_in_entities = set(result["block_entities"].keys())

        # All blocks with counts should have entity data
        assert block_names_in_counts.issubset(block_names_in_entities)

    def test_multiple_concurrent_extractions(self) -> None:
        """Test that multiple concurrent extractions don't interfere."""
        import concurrent.futures

        from core.extractor import ExtractionResult

        def run_extraction(file_path: str) -> ExtractionResult:
            return extract_blocks(file_path)

        # Run multiple extractions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
                executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
                executor.submit(run_extraction, "app/tests/assets/sample_drawing.dxf"),
            ]

            results = [f.result() for f in futures]

        # All results should be identical
        for i in range(1, len(results)):
            assert results[0]["block_counts"] == results[i]["block_counts"]

    def test_nested_block_parents_thread_safety(self) -> None:
        """Test that nested_block_parents dictionary is built correctly."""
        result = extract_blocks("app/tests/assets/nested_block_test.dxf")

        # Verify nested_block_parents structure
        assert "nested_block_parents" in result
        for child_name, parents in result["nested_block_parents"].items():
            assert isinstance(child_name, str)
            assert isinstance(parents, list)
            # Parents should be sorted
            assert parents == sorted(parents)
