# Chore: Update _detect_content_zone() to use paint-bucket algorithm

## Chore Description
Update the `_detect_content_zone()` function in `app/core/geometry.py` to use the unified paint-bucket algorithm instead of the current separate LWPOLYLINE + LINE extraction approach.

The current implementation (lines 754-775) extracts closed shapes from two separate sources:
1. Closed LWPOLYLINE entities via `_extract_closed_lwpolylines()`
2. LINE cycles via `_extract_line_cycles()`

This misses regions formed by combinations of LWPOLYLINE edges and LINE dividers. The paint-bucket algorithm (already implemented in `_extract_paint_bucket_regions()`) provides more accurate polygon detection by treating all edges uniformly.

**Key changes:**
1. Replace separate extraction calls with single `_extract_paint_bucket_regions()` call
2. Change threshold check from LINE segment count to total edge count
3. Update logging messages to reflect the new approach

## Relevant Files
Use these files to resolve the chore:

- `app/core/geometry.py` - Target file for modifications. Contains `_detect_content_zone()` (lines 727-870), `_extract_all_edges()` (lines 375-410), and `_extract_paint_bucket_regions()` (lines 413-458). The paint-bucket functions were added in Units 3+4.
- `app/core/constants.py` - Contains `LINE_SEGMENT_THRESHOLD` (5000) and `POLYGON_COUNT_THRESHOLD` (500) constants used for performance safeguards.
- `app/tests/core/test_geometry.py` - Test file for geometry module. Contains existing test classes including `TestDetectContentZone` and `TestExtractPaintBucketRegions`.
- `ai_output/030-paint-bucket-polygon-detection-plan.md` - Reference plan with exact code changes and expected behavior.

### New Files
None - all changes are modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Modify shape extraction logic in `_detect_content_zone()`

Replace lines 755-775 (from `block_name = block_def.name` through `polygon_count = len(all_shapes)`) with the unified paint-bucket approach:

**Current code to replace:**
```python
    block_name = block_def.name

    # Extract LWPOLYLINE shapes (always fast)
    lwpolyline_shapes = _extract_closed_lwpolylines(block_def)
    logger.debug(f"[{block_name}] Found {len(lwpolyline_shapes)} closed LWPOLYLINEs")

    # Check LINE segment count BEFORE extraction
    line_count = _count_line_segments(block_def)
    if line_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping LINE cycle detection: "
            f"{line_count} segments exceeds threshold {LINE_SEGMENT_THRESHOLD}"
        )
        line_cycle_shapes: list[Polygon] = []
    else:
        line_cycle_shapes = _extract_line_cycles(block_def, abort_event)
        logger.debug(f"[{block_name}] Found {len(line_cycle_shapes)} LINE cycles")

    # Combine all shapes
    all_shapes = lwpolyline_shapes + line_cycle_shapes
    polygon_count = len(all_shapes)
```

**New code:**
```python
    block_name = block_def.name

    # Count edges for threshold check
    edge_count = len(_extract_all_edges(block_def))
    if edge_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping region detection: "
            f"{edge_count} edges exceeds threshold {LINE_SEGMENT_THRESHOLD}"
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
        )

    # Use paint-bucket algorithm for accurate region detection
    all_shapes = _extract_paint_bucket_regions(block_def, abort_event)
    polygon_count = len(all_shapes)
    logger.debug(f"[{block_name}] Found {polygon_count} paint-bucket regions")
```

### Step 2: Update function docstring

Update the docstring in `_detect_content_zone()` to reflect the new algorithm. Replace the "Performance safeguards" section:

**Current docstring excerpt:**
```python
    Performance safeguards:
    - Skips LINE cycle detection if > LINE_SEGMENT_THRESHOLD segments (5000)
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons (500)
```

**New docstring excerpt:**
```python
    Performance safeguards:
    - Skips region detection if > LINE_SEGMENT_THRESHOLD edges (5000)
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons (500)
```

### Step 3: Run validation commands

Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Type check the entire app to ensure no type errors
- `uv run ruff check app/core/geometry.py` - Lint the modified geometry module
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate core functionality
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions (expect 505+ tests to pass)

## Notes
- The `_extract_all_edges()` and `_extract_paint_bucket_regions()` functions were added in Unit 3+4 (commit 7c228b5) and are already tested
- The threshold constant `LINE_SEGMENT_THRESHOLD` (5000) is reused but now applies to total edge count rather than just LINE segment count
- The `_extract_closed_lwpolylines()` and `_extract_line_cycles()` functions remain in the codebase for potential future use but are no longer called from `_detect_content_zone()`
- Expected polygon counts will increase for blocks with internal LINE dividers (e.g., rectangle with vertical divider: 1 -> 2 regions)
- The net area calculation, trim derivation, and ContentZoneData return format remain unchanged
