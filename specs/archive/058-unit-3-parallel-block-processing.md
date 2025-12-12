# Feature: Parallel Block Processing (Unit 3)

## Feature Description
Implement concurrent processing of block definitions using Python's ThreadPoolExecutor to significantly improve extraction performance on multi-core systems. This optimization leverages the fact that Shapely/GEOS is thread-safe for read operations and block definitions are independent during analysis, enabling parallel geometry analysis without race conditions.

The implementation splits block analysis into two phases:
1. **Sequential Phase**: Build anonymous block mappings (reads XDATA which requires sequential access)
2. **Parallel Phase**: Concurrent geometry analysis for all block definitions using a thread pool

This is Unit 3 of a performance optimization series, building on Units 1+2 which added early exit paths for complex blocks.

## User Story
As a CAD analyst
I want block definition analysis to process concurrently on multi-core CPUs
So that I can extract data from large DXF files with many blocks in under 1 minute instead of 18+ minutes

## Problem Statement
The current block definition analysis in `extract_blocks()` processes blocks sequentially in a single thread. For DXF files with many blocks (50-100+), each requiring geometry analysis and content zone detection, this results in:
- Medium blocks (100-999 entities): 5-50 seconds each
- Complex blocks (1000+ entities): Already handled by Units 1+2 early exit
- Total extraction time for 100 blocks: 18+ minutes on single thread

Modern CPUs have 4-16+ cores sitting idle during this processing. Since:
- Shapely/GEOS is thread-safe for read-only operations
- Block definitions are independent (no shared mutable state during analysis)
- Each block's geometry analysis is CPU-bound

The sequential approach significantly underutilizes available hardware resources.

## Solution Statement
Refactor block definition analysis to use Python's `ThreadPoolExecutor` for concurrent processing:

1. **Extract per-block analysis into a standalone function** (`_analyze_single_block`) that encapsulates all thread-safe operations for analyzing a single block definition

2. **Split processing into two phases**:
   - Phase 1 (Sequential): Build anonymous block mappings by reading XDATA - this must remain sequential as XDATA reading may have document-level state
   - Phase 2 (Parallel): Submit all block definitions to ThreadPoolExecutor for concurrent geometry analysis

3. **Collect results thread-safely** using `as_completed()` iterator and store in result dictionaries (each key is unique, no concurrent writes to same key)

4. **Cap worker threads at 8** to balance parallelism with memory usage and avoid diminishing returns from context switching

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/core/extractor.py` - Main implementation file. Contains `extract_blocks()` function with the block definition analysis loop (lines 1164-1293) that will be refactored into parallel processing. The `_analyze_single_block` function will be added here since it uses extractor-specific functions like `_get_block_bounding_box`, `_get_intersection_points`, `_calculate_segments`, and `_detect_content_zone`.

### Geometry Functions (Read-Only Reference)
- `app/core/geometry.py` - Contains the geometry analysis functions called during block analysis: `_get_block_bounding_box()`, `_get_intersection_points()`, `_calculate_segments()`, `_detect_content_zone()`. These are already thread-safe for read operations (Shapely/GEOS). No changes needed.

### Type Definitions
- `app/core/types.py` - Contains `BlockTrimmingData` and `ContentZoneData` TypedDicts used in the analysis results. No changes needed.

### Test Files
- `app/tests/core/extractor/test_extractor_core.py` - Contains existing tests for `extract_blocks()`. Add new tests for parallel processing consistency.
- `app/tests/core/extractor/test_extractor_abort.py` - Contains abort functionality tests. Verify abort works with parallel processing.

### New Files
- `app/tests/core/extractor/test_extractor_parallel.py` - New test file for parallel processing specific tests including thread safety, result consistency, and performance verification.

## Implementation Plan

### Phase 1: Foundation
Extract the per-block analysis logic into a standalone thread-safe function that can be called from a ThreadPoolExecutor.

1. Add `concurrent.futures` imports to `extractor.py`
2. Create `_analyze_single_block()` function that encapsulates:
   - Block name handling (system block skipping, anonymous block resolution)
   - Entity counting
   - Nested INSERT scanning
   - Bounding box calculation
   - Intersection point extraction and segment calculation
   - Content zone detection
3. Define proper return type as `tuple[str | None, dict[str, Any] | None]`

### Phase 2: Core Implementation
Refactor the block definition analysis section of `extract_blocks()` to use two-phase processing.

1. Modify the anonymous block mapping loop to be a dedicated Phase 1 (sequential)
2. Replace the sequential geometry analysis loop with ThreadPoolExecutor-based Phase 2 (parallel)
3. Implement result collection using `as_completed()` iterator
4. Handle exceptions gracefully per-block without failing entire extraction
5. Cap max_workers at min(8, block_count) to avoid thread overhead for small files

### Phase 3: Integration
Ensure the parallel implementation integrates correctly with existing functionality.

1. Verify abort_event propagation works correctly with thread pool
2. Ensure logging works correctly from worker threads
3. Validate that all existing tests pass without modification
4. Add new tests specifically for parallel processing behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add concurrent.futures imports
- Open `app/core/extractor.py`
- Add import statement after the existing threading import (around line 15):
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```
- Run `uv run mypy app/core/extractor.py` to verify no import errors

### 2. Create BlockAnalysisResult TypedDict
- Open `app/core/types.py`
- Add new TypedDict after `BlockDefinitionRecord`:
```python
class BlockAnalysisResult(TypedDict):
    """
    Result from analyzing a single block definition for parallel processing.

    Contains all data extracted from a block that will be stored in result dictionaries.

    Attributes:
        entity_count: Number of entities in the block definition
        trimming_data: Block geometry analysis data (native dimensions and segments)
        content_zone_data: Content zone detection results
        nested_inserts: List of block names inserted within this block
    """

    entity_count: int
    trimming_data: BlockTrimmingData
    content_zone_data: ContentZoneData
    nested_inserts: list[str]
```
- Run `uv run mypy app/core/types.py` to verify no type errors

### 3. Add _analyze_single_block function
- Open `app/core/extractor.py`
- Add import for `BlockAnalysisResult` in the types import section
- Add new function after `_resolve_dynamic_block_name()` (around line 875):
```python
def _analyze_single_block(
    block_def: Any,
    doc: Drawing,
    anonymous_to_resolved: dict[str, str],
    abort_event: threading.Event | None,
    precision_tolerance: float,
    gap_bridge_tolerance: float,
    min_area: float,
    min_side: float,
) -> tuple[str | None, BlockAnalysisResult | None]:
    """
    Analyze a single block definition for content zone and geometry.

    Thread-safe function for parallel block processing. Extracts entity count,
    nested INSERT references, trimming geometry, and content zone data.

    Args:
        block_def: ezdxf block definition object
        doc: The ezdxf Drawing document (read-only access)
        anonymous_to_resolved: Pre-built mapping of anonymous block names to resolved names
        abort_event: Optional abort signal for cancellation
        precision_tolerance: Precision snap tolerance for content zone detection
        gap_bridge_tolerance: Gap bridge tolerance for content zone detection
        min_area: Minimum area filter for polygon filtering
        min_side: Minimum side filter for polygon filtering

    Returns:
        Tuple of (effective_name, result_dict) or (None, None) if block should be skipped.
        effective_name is the resolved block name (or raw name for regular blocks).
        result_dict contains entity_count, trimming_data, content_zone_data, nested_inserts.
    """
    block_name = block_def.name

    # Skip modelspace/paperspace blocks
    if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith(
        "*Paper_Space"
    ):
        return (None, None)

    # Handle anonymous blocks starting with *U (dynamic block instances)
    if block_name.startswith("*U"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            return (None, None)  # Skip unresolved *U blocks

    elif block_name.startswith("A$C"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            effective_name = block_name

    elif block_name.startswith("*"):
        return (None, None)  # Skip other system blocks
    else:
        effective_name = block_name

    # Count entities
    entity_count = sum(1 for _ in block_def)

    # Scan for nested INSERTs
    nested_inserts: list[str] = []
    for entity in block_def:
        if entity.dxftype() == "INSERT":
            nested_name = entity.dxf.name
            if nested_name in anonymous_to_resolved:
                nested_name = anonymous_to_resolved[nested_name]
            nested_inserts.append(nested_name)

    # Analyze block geometry
    bbox = _get_block_bounding_box(block_def)
    native_width = round(bbox[2] - bbox[0], 2)
    native_height = round(bbox[3] - bbox[1], 2)

    vertical_points, horizontal_points = _get_intersection_points(block_def)
    vertical_segments = _calculate_segments(vertical_points)
    horizontal_segments = _calculate_segments(horizontal_points)

    block_trimming: BlockTrimmingData = {
        "native_width": native_width,
        "native_height": native_height,
        "vertical_segments": vertical_segments,
        "horizontal_segments": horizontal_segments,
    }

    # Detect content zone
    content_zone = _detect_content_zone(
        block_def,
        bbox,
        abort_event,
        precision_tolerance,
        gap_bridge_tolerance,
        min_area,
        min_side,
    )

    result: BlockAnalysisResult = {
        "entity_count": entity_count,
        "trimming_data": block_trimming,
        "content_zone_data": content_zone,
        "nested_inserts": nested_inserts,
    }

    return (effective_name, result)
```
- Run `uv run mypy app/core/extractor.py` to verify no type errors

### 4. Refactor block analysis loop - Phase 1 (Sequential XDATA resolution)
- In `app/core/extractor.py`, locate the block definition analysis section (lines 1164-1293)
- Replace the existing loop with two-phase processing
- Phase 1: Build anonymous block mappings sequentially:
```python
# Extract block definition entity counts and geometry analysis
logger.info("Analyzing block definitions...")

# PHASE 1: Build anonymous block mappings (must be sequential - reads XDATA)
anonymous_to_resolved: dict[str, str] = {}
anonymous_resolution_details: dict[str, str] = {}

for block_def in doc.blocks:
    block_name = block_def.name

    if block_name.startswith("*U") or block_name.startswith("A$C"):
        try:
            block_record = block_def.block_record
            resolved_name, resolution_details = _resolve_dynamic_block_name(
                block_record, doc, block_name
            )
            anonymous_resolution_details[block_name] = resolution_details
            if resolved_name:
                anonymous_to_resolved[block_name] = resolved_name
            elif block_name.startswith("A$C"):
                anonymous_to_resolved[block_name] = block_name
        except (AttributeError, TypeError) as e:
            anonymous_resolution_details[block_name] = f"Error: {e}"
            if block_name.startswith("A$C"):
                anonymous_to_resolved[block_name] = block_name

logger.info(
    f"Resolved {len(anonymous_to_resolved)} anonymous blocks to original names"
)
```

### 5. Refactor block analysis loop - Phase 2 (Parallel geometry analysis)
- Continue in `app/core/extractor.py` after Phase 1
- Add Phase 2 parallel processing:
```python
# PHASE 2: Parallel block geometry analysis
block_defs_list = list(doc.blocks)
max_workers = min(8, max(1, len(block_defs_list)))  # Cap at 8 threads, minimum 1

logger.info(f"Starting parallel analysis of {len(block_defs_list)} block definitions with {max_workers} workers")

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {
        executor.submit(
            _analyze_single_block,
            block_def,
            doc,
            anonymous_to_resolved,
            abort_event,
            precision_tolerance,
            gap_bridge_tolerance,
            min_area,
            min_side,
        ): block_def.name
        for block_def in block_defs_list
    }

    for future in as_completed(futures):
        block_name = futures[future]
        try:
            effective_name, result = future.result()
            if effective_name is None or result is None:
                continue

            # Store results (thread-safe: each key is unique)
            block_entities[effective_name] = result["entity_count"]
            block_trimming_data[effective_name] = result["trimming_data"]
            block_content_zone_data[effective_name] = result["content_zone_data"]

            # Track nested relationships
            for nested_name in result["nested_inserts"]:
                if nested_name not in nested_block_parents:
                    nested_block_parents[nested_name] = set()
                nested_block_parents[nested_name].add(effective_name)

        except Exception as e:
            logger.warning(f"Error analyzing block {block_name}: {e}")
            continue

logger.info(f"Analyzed {len(block_entities)} block definitions")
logger.info(
    f"Analyzed geometry for {len(block_trimming_data)} block definitions"
)
```
- Run `uv run mypy app/core/extractor.py` to verify no type errors

### 6. Create test file for parallel processing
- Create `app/tests/core/extractor/test_extractor_parallel.py`:
```python
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

        def run_extraction(file_path: str) -> dict:
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
```
- Run `uv run pytest app/tests/core/extractor/test_extractor_parallel.py -v` to verify tests pass

### 7. Update imports in types.py
- Verify `BlockTrimmingData` import is available in extractor.py
- The import should already exist; verify it includes `BlockAnalysisResult`

### 8. Run full validation
- Run `uv run mypy app/` - Full type checking
- Run `uv run pytest app/tests/core/extractor/ -v` - All extractor tests
- Run `uv run pytest app/tests/ -v` - Full test suite
- Run `uv run ruff check app/` - Linting
- Run `uv run ruff format app/ --check` - Format check

## Testing Strategy

### Unit Tests
- **Thread safety tests**: Run same extraction multiple times, verify identical results
- **Result structure tests**: Verify all data structures (block_entities, block_trimming_data, block_content_zone_data, nested_block_parents) are correctly populated
- **Exception handling tests**: Verify per-block exceptions don't crash entire extraction

### Integration Tests
- **Abort integration**: Verify abort_event works correctly with ThreadPoolExecutor
- **Dynamic block resolution**: Verify anonymous blocks are correctly resolved in parallel
- **Nested block tracking**: Verify parent-child relationships are correctly built

### Edge Cases
- Empty DXF file (no blocks)
- DXF with only system blocks (*Model_Space, *Paper_Space)
- DXF with only unresolved anonymous blocks
- DXF with single block (max_workers = 1)
- DXF with 100+ blocks (verify thread pool caps at 8)
- Blocks with exceptions during analysis (verify other blocks still process)

### Playwright MCP Tests
Not applicable - these are backend performance optimizations with no UI changes.

## Acceptance Criteria
1. `_analyze_single_block()` function exists and is thread-safe
2. Block definition analysis uses ThreadPoolExecutor with max_workers capped at 8
3. Phase 1 (XDATA resolution) remains sequential for thread safety
4. Phase 2 (geometry analysis) runs in parallel
5. All existing tests pass without modification
6. New parallel processing tests verify consistent results
7. Abort functionality works correctly with parallel processing
8. No race conditions in result collection (each key written by single thread)
9. Type checking passes with zero errors
10. Performance improvement: 100 blocks should process in under 1 minute (vs 18+ minutes sequential)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/core/extractor/test_extractor_parallel.py -v` - Run parallel processing specific tests
- `uv run pytest app/tests/core/extractor/test_extractor_abort.py -v` - Verify abort functionality still works
- `uv run pytest app/tests/core/extractor/test_extractor_core.py -v` - Verify core extraction still works
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The `_analyze_single_block` function is defined in `extractor.py` (not `geometry.py`) because it uses extractor-specific functions and type definitions
- ThreadPoolExecutor is chosen over ProcessPoolExecutor because:
  - ezdxf document objects are not picklable for process serialization
  - Thread pool has lower overhead for CPU-bound tasks with GIL-releasing libraries (like Shapely/GEOS)
  - Shared memory access is simpler for result collection
- The max_workers cap of 8 is based on typical developer machines and diminishing returns from thread context switching
- Result collection is thread-safe because each block produces a unique effective_name key - no two threads write to the same dictionary key simultaneously
- The abort_event is passed to each worker and checked in `_detect_content_zone()`, allowing mid-analysis cancellation
- Logging from worker threads works correctly in Python's threading model (GIL serializes log writes)
