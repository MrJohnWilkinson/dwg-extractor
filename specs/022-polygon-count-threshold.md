# Chore: Add Polygon Count Threshold

## Chore Description
The `_calculate_net_areas` function in `geometry.py` has O(n³) algorithmic complexity, causing severe performance issues for blocks with many polygons. A block with 102 polygons took 140.7 seconds (2.3 minutes) to process due to 102³ = 1,061,208 iterations with polygon containment checks. Users experience extraction timeouts/aborts on complex blocks.

Most useful blocks have 1-12 polygons; blocks with 30+ polygons are edge cases where content zone detection provides diminishing value. This chore adds an early exit threshold to skip content zone analysis for blocks with excessive polygon counts, returning an empty/default `ContentZoneData` instead of attempting the expensive O(n³) calculation.

## Relevant Files
Use these files to resolve the chore:

- `app/core/constants.py` - Add the new `POLYGON_COUNT_THRESHOLD` constant (value: 30)
- `app/core/geometry.py` - Contains `_detect_content_zone()` function (lines 800-981) that needs the early exit check after polygon extraction
- `app/core/types.py` - Contains `ContentZoneData` TypedDict used for the return type (for reference only, no changes needed)
- `app/tests/core/test_content_zone.py` - Add tests for the polygon threshold behavior

### New Files
None required - only modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add POLYGON_COUNT_THRESHOLD constant
- Open `app/core/constants.py`
- Add a new constant `POLYGON_COUNT_THRESHOLD: int = 30` after the log viewer configuration section (around line 122)
- Add a comment explaining its purpose: threshold for skipping content zone detection on complex blocks

### Step 2: Implement early exit in _detect_content_zone()
- Open `app/core/geometry.py`
- Import `POLYGON_COUNT_THRESHOLD` from `.constants`
- In `_detect_content_zone()` function, after the line that combines shapes:
  ```python
  all_shapes = lwpolyline_shapes + line_cycle_shapes
  ```
  (around line 860)
- Add polygon count threshold check immediately after combining shapes:
  ```python
  # Check polygon count threshold to avoid O(n³) containment analysis
  polygon_count = len(all_shapes)
  if polygon_count > POLYGON_COUNT_THRESHOLD:
      logger.warning(
          f"Skipping content zone detection{block_context}: {polygon_count} polygons "
          f"exceeds threshold of {POLYGON_COUNT_THRESHOLD}"
      )
      return ContentZoneData(
          suggested_trim_left=None,
          suggested_trim_right=None,
          suggested_trim_top=None,
          suggested_trim_bottom=None,
          content_zone_detected=False,
      )
  ```
- This check should be placed BEFORE the existing "Return empty result if no shapes found" check

### Step 3: Add unit tests for polygon threshold
- Open `app/tests/core/test_content_zone.py`
- Add new test class `TestPolygonCountThreshold` with the following tests:
  - `test_threshold_exceeded_returns_empty_result`: Create a block with more than 30 closed polylines and verify `_detect_content_zone` returns `content_zone_detected=False` with all trim values as `None`
  - `test_threshold_exact_processes_normally`: Create a block with exactly 30 polygons and verify content zone detection still runs
  - `test_threshold_below_processes_normally`: Verify blocks with < 30 polygons continue to work normally (can use existing test fixture)
- Import `POLYGON_COUNT_THRESHOLD` from `core.constants` in the test file for threshold value reference

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests including new threshold tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to ensure no regressions
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions across the codebase
- `uv run mypy app/core/geometry.py app/core/constants.py` - Type check modified files
- `uv run ruff check app/core/geometry.py app/core/constants.py` - Lint modified files

## Notes
- The threshold value of 30 is based on analysis showing most useful blocks have 1-12 polygons
- The warning log level is intentional so users can see why content zone data is missing for specific blocks
- This is a graceful degradation - extraction continues, only content zone data is skipped for complex blocks
- The early exit happens AFTER extracting shapes but BEFORE the expensive `_calculate_net_areas()` call
- Future optimization could use spatial indexing or R-trees to reduce complexity below O(n³), but that's out of scope for this chore
