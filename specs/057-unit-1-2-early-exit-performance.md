# Feature: Early Exit Performance Optimizations (Units 1+2)

## Feature Description
Implement two early exit performance optimizations in the content zone detection pipeline to skip expensive geometry processing for complex blocks. Unit 1 adds a fast entity count pre-check that runs before any geometry extraction. Unit 2 replaces the current expensive edge extraction with a fast edge count estimation that avoids coordinate extraction.

These optimizations target blocks with high entity counts (>1000 entities) that would take 50-90 seconds to process, reducing their processing time to <0.1 seconds by skipping content zone detection entirely.

## User Story
As a CAD analyst
I want the application to quickly skip complex blocks during content zone detection
So that I don't have to wait 50-90 seconds per complex block when processing large DXF files

## Problem Statement
The current `_detect_content_zone()` function in `geometry.py` performs expensive operations before checking if a block should be skipped:

1. **No entity count check**: Blocks with thousands of entities proceed through the entire pipeline even though they will inevitably exceed polygon/edge thresholds
2. **Expensive edge count check**: The current code calls `_extract_all_edges()` to get `len()`, which extracts all coordinates (creating LineString objects, parsing vertices) just to count edges

For complex blocks (1000+ entities), this results in 50-90 second processing times when the block should have been skipped immediately.

## Solution Statement
Implement two sequential early exit gates at the start of `_detect_content_zone()`:

1. **Unit 1 - Entity Count Pre-Check**: Add a fast O(n) entity count check (no coordinate extraction) as the very first gate. Blocks exceeding `ENTITY_COUNT_THRESHOLD` (1000) skip content zone detection immediately.

2. **Unit 2 - Fast Edge Count Estimation**: Replace the expensive `len(_extract_all_edges(block_def))` call with a new `_estimate_edge_count()` function that counts expected edges without creating geometry objects or extracting coordinates.

Both checks are O(n) with minimal overhead - they iterate entities once without coordinate extraction.

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/core/constants.py` - Add `ENTITY_COUNT_THRESHOLD` constant after `LINE_SEGMENT_THRESHOLD` (line ~170). This file defines all content zone detection thresholds.
- `app/core/geometry.py` - Main implementation file. Add `_estimate_edge_count()` function after `_count_line_segments()` (line ~484) and modify `_detect_content_zone()` to add early exit checks at the start.

### Test Files
- `app/tests/core/test_content_zone.py` - Add tests for entity count threshold skip and edge estimation accuracy. This file contains all content zone detection tests.
- `app/tests/assets/many_lines_test.dxf` - Existing test file with blocks designed to test threshold behavior (MANY_LINES, FEW_LINES, EXACTLY_THRESHOLD, JUST_OVER_THRESHOLD blocks)

### New Files
- `app/tests/assets/create_high_entity_count_test.py` - Script to create test DXF with blocks having >1000 entities for Unit 1 testing
- `app/tests/assets/high_entity_count_test.dxf` - Generated test file for entity count threshold tests

## Implementation Plan

### Phase 1: Foundation (Unit 1 - Entity Count Pre-Check)
Add the simplest and fastest check first - counting entities without any coordinate extraction.

1. Add `ENTITY_COUNT_THRESHOLD` constant to `constants.py`
2. Add early exit check at the start of `_detect_content_zone()` that counts entities and returns `_empty_content_zone_data()` if threshold exceeded
3. Create test assets with >1000 entities
4. Add unit tests to verify threshold behavior

### Phase 2: Core Implementation (Unit 2 - Fast Edge Count Estimation)
Replace the expensive edge count with fast estimation.

1. Add `_estimate_edge_count()` function that estimates edge counts by entity type without coordinate extraction
2. Replace the existing `edge_count = len(_extract_all_edges(block_def))` check with `_estimate_edge_count()`
3. Add tests comparing estimation accuracy against actual edge counts
4. Add threshold skip tests using estimation

### Phase 3: Integration
Ensure both early exit gates work together correctly in sequence.

1. Verify Unit 1 check runs before Unit 2 check (entity count first, then edge estimation)
2. Verify logging messages clearly indicate which threshold caused the skip
3. Run full test suite to ensure no regressions
4. Validate performance improvement with complex blocks

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add ENTITY_COUNT_THRESHOLD constant
- Open `app/core/constants.py`
- Add after `LINE_SEGMENT_THRESHOLD` (around line 170):
```python
ENTITY_COUNT_THRESHOLD: int = 1000
"""Maximum entities in block for content zone detection.
Blocks with more entities skip content zone entirely.
Rationale: High entity counts strongly correlate with complex geometry
that will exceed polygon thresholds anyway."""
```
- Run `uv run mypy app/core/constants.py` to verify no type errors

### 2. Create test DXF with high entity count blocks
- Create `app/tests/assets/create_high_entity_count_test.py` script that generates:
  - `HIGH_ENTITY_COUNT` block: 1500 simple LINE entities (exceeds threshold)
  - `LOW_ENTITY_COUNT` block: 500 simple LINE entities (under threshold)
  - `EXACTLY_ENTITY_THRESHOLD` block: Exactly 1000 entities (boundary test)
  - `JUST_OVER_ENTITY_THRESHOLD` block: 1001 entities (first to be skipped)
- Run the script to generate `app/tests/assets/high_entity_count_test.dxf`

### 3. Add Unit 1 early exit to _detect_content_zone()
- Open `app/core/geometry.py`
- Add `ENTITY_COUNT_THRESHOLD` to the imports from `.constants`
- Add entity count check at the very START of `_detect_content_zone()`, before `block_name = block_def.name`:
```python
block_name = block_def.name

# UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
entity_count = sum(1 for _ in block_def)
if entity_count > ENTITY_COUNT_THRESHOLD:
    logger.warning(
        f"[{block_name}] Skipping content zone: "
        f"{entity_count} entities exceeds threshold {ENTITY_COUNT_THRESHOLD}"
    )
    return _empty_content_zone_data()
```
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 4. Add Unit 1 tests
- Open `app/tests/core/test_content_zone.py`
- Add import for `ENTITY_COUNT_THRESHOLD` from `core.constants`
- Add new test class `TestEntityCountThreshold`:
  - `test_entity_count_threshold_skip`: Block with >1000 entities returns empty ContentZoneData
  - `test_entity_count_threshold_not_skip`: Block with <1000 entities proceeds with detection
  - `test_entity_count_exactly_threshold`: Block with exactly 1000 entities is NOT skipped (> not >=)
  - `test_entity_count_just_over_threshold`: Block with 1001 entities IS skipped
- Run `uv run pytest app/tests/core/test_content_zone.py::TestEntityCountThreshold -v` to verify tests pass

### 5. Add _estimate_edge_count() function
- Open `app/core/geometry.py`
- Add new function after `_count_line_segments()` (around line 484):
```python
def _estimate_edge_count(block_def: BlockLayout) -> int:
    """
    Fast O(n) edge count estimation without coordinate extraction.

    Counts the number of edges that would be extracted by _extract_all_edges()
    without actually creating LineString objects or extracting coordinates.
    Used for threshold checks before expensive geometry operations.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Estimated number of edges in the block.
    """
    count = 0
    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            count += 1

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                # Count vertices to estimate edge count
                # Each vertex pair = 1 edge, plus closing edge if closed
                points = list(entity.get_points())
                vertex_count = len(points)
                if vertex_count >= 2:
                    count += vertex_count - 1
                    if hasattr(entity, "closed") and entity.closed:
                        count += 1
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            # Estimate based on typical flattening (full circle ~ 36 segments)
            count += 36

        elif entity_type == "ARC":
            # Estimate based on typical flattening (half circle ~ 18 segments)
            count += 18

        elif entity_type == "HATCH":
            # Conservative estimate per hatch boundary path
            # Actual count varies, but 50 edges per hatch is reasonable average
            count += 50

    return count
```
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 6. Replace edge count check with estimation (Unit 2)
- In `app/core/geometry.py`, locate the existing edge count check in `_detect_content_zone()`:
```python
# Count edges for threshold check
edge_count = len(_extract_all_edges(block_def))
if edge_count > LINE_SEGMENT_THRESHOLD:
```
- Replace with:
```python
# UNIT 2: Fast edge count estimation (no coordinate extraction)
estimated_edge_count = _estimate_edge_count(block_def)
if estimated_edge_count > LINE_SEGMENT_THRESHOLD:
    logger.warning(
        f"[{block_name}] Skipping region detection: "
        f"~{estimated_edge_count} estimated edges exceeds threshold {LINE_SEGMENT_THRESHOLD}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=0,
        filtered_polygon_count=0,
    )
```
- Note: The existing log message format changes slightly to include `~` prefix indicating estimate
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 7. Add Unit 2 tests
- Open `app/tests/core/test_content_zone.py`
- Add new test class `TestEdgeEstimation`:
  - `test_estimate_edge_count_lines_only`: Verify LINE entities counted as 1 edge each
  - `test_estimate_edge_count_polylines`: Verify polyline vertex pairs counted correctly
  - `test_estimate_edge_count_circles`: Verify circles estimated as ~36 edges
  - `test_estimate_edge_count_arcs`: Verify arcs estimated as ~18 edges
  - `test_estimate_edge_count_hatches`: Verify hatches estimated as ~50 edges each
  - `test_estimate_edge_count_mixed`: Verify mixed entities counted correctly
  - `test_estimate_vs_actual_accuracy`: Compare estimation to actual `_extract_all_edges()` count (should be reasonably close)
- Add import for `_estimate_edge_count` from `core.geometry`
- Run `uv run pytest app/tests/core/test_content_zone.py::TestEdgeEstimation -v` to verify tests pass

### 8. Update existing threshold tests
- Review `TestThresholdSkips` class in `test_content_zone.py`
- Update `test_line_threshold_skip` test comment to mention it now uses estimation
- Update `test_line_threshold_not_skip` test comment to mention it now uses estimation
- Ensure tests still pass with new estimation approach (they should, as behavior is the same)
- Run `uv run pytest app/tests/core/test_content_zone.py::TestThresholdSkips -v`

### 9. Run full validation
- Run `uv run mypy app/` - Full type checking
- Run `uv run pytest app/tests/core/test_content_zone.py -v` - All content zone tests
- Run `uv run pytest app/tests/ -v` - Full test suite
- Run `uv run ruff check app/` - Linting
- Run `uv run ruff format app/ --check` - Format check

## Testing Strategy

### Unit Tests
- **Entity count threshold**: Test blocks with entity counts above, below, at, and just over the threshold
- **Edge estimation**: Test estimation accuracy for each entity type (LINE, POLYLINE, CIRCLE, ARC, HATCH)
- **Estimation accuracy**: Compare estimated edge counts to actual `_extract_all_edges()` counts for various blocks

### Integration Tests
- **Check order**: Verify Unit 1 runs before Unit 2 (entity count before edge estimation)
- **Combined behavior**: Verify a block with high entity count skips before edge estimation runs
- **Existing tests pass**: All existing content zone tests must continue to pass

### Edge Cases
- Empty block (0 entities) - should proceed normally
- Block with exactly 1000 entities - should NOT be skipped (threshold is >)
- Block with 1001 entities - should be skipped
- Block with only non-geometric entities (TEXT, MTEXT) - should handle gracefully
- Closed vs open polylines - closed should add +1 edge for closing segment

### Playwright MCP Tests
Not applicable - these are backend geometry processing optimizations with no UI changes.

## Acceptance Criteria
1. Blocks with >1000 entities are skipped immediately with `_empty_content_zone_data()` return
2. Blocks with <=1000 entities proceed to edge estimation check
3. Edge estimation does not create any LineString objects or extract coordinates
4. Edge estimation produces counts reasonably close to actual extraction (within 20% for typical blocks)
5. Log messages clearly indicate which threshold caused the skip (entity count vs edge count)
6. All existing tests pass without modification (except updated comments)
7. New tests cover both threshold behaviors and estimation accuracy
8. Type checking passes with zero errors
9. Complex blocks (1000+ entities) process in <0.1s (skip path)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests including new tests
- `uv run pytest app/tests/core/test_content_zone.py::TestEntityCountThreshold -v` - Run Unit 1 specific tests
- `uv run pytest app/tests/core/test_content_zone.py::TestEdgeEstimation -v` - Run Unit 2 specific tests
- `uv run pytest app/tests/core/test_content_zone.py::TestThresholdSkips -v` - Run existing threshold tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The entity count check uses `sum(1 for _ in block_def)` which is O(n) but does NOT extract any coordinates - it simply iterates the entity collection
- Edge estimation for CIRCLE (36) and ARC (18) are based on typical `sagitta=0.1` flattening results; actual counts vary with radius but estimates are sufficient for threshold decisions
- Edge estimation for HATCH (50) is a conservative average; actual counts vary greatly based on boundary complexity
- The existing `_count_line_segments()` function only counts LINE entities and cannot be reused for this purpose since we need to count all entity types
- Both early exit checks run before any expensive geometry operations (no Shapely objects created)
- Log level is `warning` to match existing threshold skip messages and ensure visibility in normal operation
