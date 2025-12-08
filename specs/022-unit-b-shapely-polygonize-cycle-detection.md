# Feature: Unit B - Replace _extract_line_cycles with Shapely polygonize

## Feature Description
Replace the 130-line DFS (Depth-First Search) cycle detection algorithm in `_extract_line_cycles()` with Shapely's `polygonize()` function. This is the highest-impact change in the Shapely Geometry Refactor (US-8), eliminating O(exponential) complexity and the need for timeout handling. The function finds closed polygons formed by LINE segments in CAD block definitions.

This is Unit B of the Shapely Geometry Refactor. Unit A has been completed successfully with all 484 tests passing. The Shapely imports (`LineString`, `polygonize`) and adapter functions are already in place.

## User Story
As a developer
I want to use Shapely's polygonize for cycle detection
So that content zone detection is faster, more reliable, and doesn't require timeout safeguards

## Problem Statement
The current `_extract_line_cycles()` implementation has several issues:
1. **O(exponential) complexity** - The iterative DFS algorithm has exponential worst-case time complexity
2. **5-second timeout required** - `CYCLE_DETECTION_TIMEOUT_SECONDS` safeguard needed to prevent hangs
3. **130 lines of complex code** - Nested loops, stack management, and iteration counting
4. **Edge case vulnerabilities** - Custom algorithm may not handle all geometric edge cases correctly
5. **Arbitrary iteration limits** - Timeout checks every 1000 iterations and 20-vertex path limit

## Solution Statement
Replace the entire DFS implementation with Shapely's `polygonize()` function which:
1. Uses GEOS (C++ library) for fast, battle-tested cycle detection
2. Handles thousands of line segments efficiently without timeout
3. Reduces 130 lines to ~25 lines of code
4. Eliminates need for timeout handling within the function
5. Provides robust handling of edge cases (collinear points, degenerate segments)

## Relevant Files
Use these files to implement the feature:

- `app/core/geometry.py` - **Main refactor target**. Contains `_extract_line_cycles()` function (lines 528-654) that will be replaced. Shapely imports (`LineString`, `polygonize`) already present from Unit A.

- `app/core/constants.py` - Contains `CYCLE_DETECTION_TIMEOUT_SECONDS` (line 146) which may become unnecessary after this refactor. Also contains `LINE_SEGMENT_THRESHOLD` (line 141) which is evaluated in `_detect_content_zone()` before calling `_extract_line_cycles()`.

- `app/core/types.py` - Defines `Polygon` type alias as `list[tuple[float, float]]` (line 33). Return type must remain unchanged.

- `app/tests/core/test_content_zone.py` - Contains tests for cycle detection in `TestLineCycleDetection` class (lines 99-181). Tests must continue to pass.

- `app/tests/assets/content_zone_test.dxf` - Test fixture with LINE-based shapes (`LINE_RECTANGLE`, `CHAMFERED_SHAPE`)

- `app/tests/assets/many_lines_test.dxf` - Test fixture with threshold edge cases (`MANY_LINES`, `FEW_LINES`, `EXACTLY_THRESHOLD`, `JUST_OVER_THRESHOLD`)

## Implementation Plan

### Phase 1: Preparation
Review the current implementation to understand all edge cases and ensure the new implementation handles them correctly. Verify that Shapely imports are in place from Unit A.

### Phase 2: Core Implementation
Replace the `_extract_line_cycles()` function body with the Shapely-based implementation while maintaining the same function signature and return type.

### Phase 3: Cleanup and Validation
Remove unused imports (time module if no longer needed), update docstring to reflect new implementation, and run full test suite to validate zero regressions.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Shapely Imports Already Present
- Open `app/core/geometry.py`
- Confirm `LineString` is imported from `shapely.geometry`
- Confirm `polygonize` is imported from `shapely.ops`
- These were added in Unit A and should already be present

### Step 2: Review Current Implementation
- Read `_extract_line_cycles()` function (lines 528-654)
- Note the current behavior:
  - Builds adjacency graph from LINE segments
  - Uses iterative DFS with stack
  - Has timeout protection via `CYCLE_DETECTION_TIMEOUT_SECONDS`
  - Has abort event checkpoints every 1000 iterations
  - Limits path length to 20 vertices
  - Rounds coordinates to 2 decimal places for tolerance matching
- All this complexity will be replaced

### Step 3: Replace _extract_line_cycles Implementation
- Replace the entire function body (keep the signature and docstring structure)
- New implementation:
  ```python
  def _extract_line_cycles(
      block_def: BlockLayout,
      abort_event: threading.Event | None = None,
  ) -> list[Polygon]:
      """
      Extract closed cycles from LINE segments using Shapely polygonize.

      Collects all LINE entities from the block definition, converts them to
      Shapely LineString objects, and uses polygonize() to find all closed
      polygons formed by the line segments.

      Args:
          block_def: ezdxf block definition object
          abort_event: Optional threading.Event to signal abort request

      Returns:
          List of Polygon objects representing detected cycles.

      Raises:
          GeometryAbortedError: If abort_event is set during processing.
      """
      # Collect all LINE segments as LineStrings
      lines: list[LineString] = []
      for entity in block_def:
          if entity.dxftype() == "LINE":
              start = entity.dxf.start
              end = entity.dxf.end
              lines.append(LineString([(start.x, start.y), (end.x, end.y)]))

      if not lines:
          return []

      # Check abort before expensive operation
      if abort_event and abort_event.is_set():
          raise GeometryAbortedError("Cycle detection aborted")

      # Polygonize finds all closed polygons from line segments
      polygons = list(polygonize(lines))

      # Convert to internal Polygon format
      result: list[Polygon] = []
      for poly in polygons:
          if poly.is_valid and not poly.is_empty:
              coords = list(poly.exterior.coords)[:-1]  # Exclude closing point
              result.append([(float(x), float(y)) for x, y in coords])

      logger.debug(f"Found {len(result)} LINE cycles via polygonize")
      return result
  ```

### Step 4: Remove Unused Imports
- Check if `time` module import is still needed in geometry.py
- The `time` import was used for `time.perf_counter()` in the timeout logic
- If no other code uses `time`, remove the import
- Keep `from collections import defaultdict` only if used elsewhere in the file

### Step 5: Update Function Docstring
- Update the docstring to reflect that Shapely polygonize is now used
- Remove references to DFS, timeout, and iteration limits
- Keep the Args, Returns, and Raises sections accurate

### Step 6: Run Cycle Detection Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py::TestLineCycleDetection -v`
- All tests must pass:
  - `test_extract_line_cycle_simple_rectangle`
  - `test_extract_line_cycle_no_cycles`
  - `test_extract_line_cycle_chamfered`
  - `test_line_cycle_timeout_protection`
  - `test_line_cycle_abort_event`

### Step 7: Run Threshold Skip Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py::TestThresholdSkips -v`
- All tests must pass (these verify LINE_SEGMENT_THRESHOLD behavior in `_detect_content_zone`)

### Step 8: Run Content Zone Detection Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py -v`
- All 52+ content zone tests must pass

### Step 9: Run Geometry Tests
- Execute: `uv run pytest app/tests/core/test_geometry.py -v`
- All geometry tests must continue to pass (unchanged by this refactor)

### Step 10: Run Full Test Suite
- Execute: `uv run pytest app/tests/`
- All 484 tests must pass with zero failures

### Step 11: Run Type Checker
- Execute: `uv run mypy app/`
- Must pass with no errors
- LineString type from shapely.geometry should be recognized

### Step 12: Run Linter and Formatter
- Execute: `uv run ruff check app/`
- Execute: `uv run ruff format app/`
- Fix any issues reported

### Step 13: Verify Import Cleanup
- Confirm unused imports removed:
  - `time` (if no longer used)
  - `defaultdict` (if no longer used - was used for graph building)
- Confirm noqa comment on LineString import can be removed (now actively used)

## Testing Strategy

### Unit Tests
- Existing `TestLineCycleDetection` tests validate core functionality:
  - Simple rectangle from 4 LINE segments
  - Open line chains (no cycles expected)
  - Chamfered shapes (8-vertex cycles)
  - Timeout protection (should complete quickly with polygonize)
  - Abort event handling

### Integration Tests
- `TestContentZoneDetection` tests validate end-to-end detection with LINE cycles
- `TestThresholdSkips` tests validate LINE_SEGMENT_THRESHOLD behavior

### Edge Cases
- Empty block (no LINE entities) - should return empty list
- Open line chains (no closed cycles) - should return empty list
- Single closed rectangle - should find one 4-vertex cycle
- Complex shapes (chamfered rectangle) - should find 8-vertex cycle
- Large number of lines (under threshold) - should complete quickly
- Degenerate lines (start == end) - polygonize handles gracefully
- Collinear segments - polygonize handles correctly
- Self-intersecting line arrangements - polygonize finds all valid cycles

### Playwright MCP Tests
Not applicable - this is a core geometry function without UI interaction.

## Acceptance Criteria
1. `_extract_line_cycles()` uses Shapely `polygonize()` instead of DFS
2. Function signature unchanged: `(block_def, abort_event) -> list[Polygon]`
3. Return type unchanged: `list[Polygon]` where `Polygon = list[tuple[float, float]]`
4. Abort event handling preserved (check before polygonize call)
5. Timeout handling removed (no longer needed with polygonize)
6. All existing tests pass (484 total)
7. Type checking passes (`uv run mypy app/`)
8. Linting passes (`uv run ruff check app/`)
9. Unused imports removed (`time`, `defaultdict` if applicable)
10. Docstring updated to reflect new implementation

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_content_zone.py::TestLineCycleDetection -v` - Run cycle detection tests specifically
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests (should be unaffected)
- `uv run pytest app/tests/` - Run full test suite (484 tests expected)
- `uv run mypy app/` - Run type checker
- `uv run ruff check app/` - Run linter
- `uv run ruff format app/` - Run formatter

## Notes
- **Unit A Completed**: Shapely imports and adapter functions are already in place from Unit A
- **Backwards Compatibility**: Function signature and return type remain unchanged
- **CYCLE_DETECTION_TIMEOUT_SECONDS**: The constant in `constants.py` is no longer used by `_extract_line_cycles()` after this change, but it remains in the codebase. A future cleanup task may remove it if no other code references it.
- **LINE_SEGMENT_THRESHOLD**: This threshold check happens in `_detect_content_zone()` BEFORE calling `_extract_line_cycles()`. The threshold may be raised or removed in a future Unit since polygonize handles large inputs efficiently.
- **Coordinate Tolerance**: The old DFS implementation rounded coordinates to 2 decimal places. Shapely's polygonize uses floating-point comparison with its own tolerance handling. This should be equivalent or better for most cases.
- **Performance**: Shapely's polygonize uses GEOS noding algorithm which is O(n log n) compared to the old DFS which was O(exponential) in worst case.
- **Test Asset Compatibility**: Existing test DXF files were created for the DFS algorithm. The new implementation should produce equivalent results for the same inputs.
