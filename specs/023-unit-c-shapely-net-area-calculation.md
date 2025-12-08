# Feature: Unit C - Simplify _calculate_net_areas with Shapely Difference

## Feature Description
Replace the O(n^3) containment check and manual area subtraction in `_calculate_net_areas()` with Shapely's geometric difference operations. This is Unit C (Step 10) of the Shapely Geometry Refactor (US-8). The function calculates net areas for polygons by subtracting contained polygon areas, which is used to identify the content zone (the polygon with the largest net area) in CAD block definitions.

Currently the function uses nested loops with custom containment checking and gross area subtraction, resulting in O(n^3) complexity that requires a conservative `POLYGON_COUNT_THRESHOLD` of 30. With Shapely's efficient GEOS-based geometric operations, this threshold can be significantly raised to 500, enabling content zone detection on more complex CAD blocks.

This is Unit C of the Shapely Geometry Refactor. Units A and B have been completed successfully with all 484 tests passing:
- **Unit A**: Added Shapely imports and replaced basic geometry functions (`_shoelace_area`, `_point_in_polygon`, `_polygon_contains_polygon`, `_get_polygon_bbox`, `_get_union_bounding_box`)
- **Unit B**: Replaced DFS cycle detection with `polygonize()` in `_extract_line_cycles()`

## User Story
As a developer
I want to use Shapely's difference operations for net area calculation
So that content zone detection can handle more complex blocks without arbitrary polygon limits

## Problem Statement
The current `_calculate_net_areas()` implementation has several issues:
1. **O(n^3) complexity** - For each polygon (n), checks containment against all other polygons (n), using vertex-based containment check (n vertices)
2. **30-polygon limit required** - `POLYGON_COUNT_THRESHOLD` constraint prevents analysis of complex blocks
3. **Repeated containment checks** - Uses custom `_polygon_contains_polygon()` for each pair which is less efficient than Shapely's native containment
4. **Manual area subtraction** - Subtracts gross areas of contained polygons instead of using geometric difference, which can be inaccurate for overlapping (non-nested) polygons
5. **No invalid polygon handling** - Current implementation doesn't handle invalid/degenerate Shapely polygons gracefully

## Solution Statement
Replace the implementation with Shapely's geometric difference:
1. Convert all polygons to Shapely objects once upfront
2. For each polygon, use `shapely_poly.contains(other)` for efficient GEOS-based containment check
3. Use `net_poly.difference(other)` to geometrically subtract contained polygons
4. Handle invalid polygons by returning 0.0 area
5. Calculate final net area from the resulting geometry using `net_poly.area`
6. Maintain same function signature and return type (sorted by net area descending)
7. Enable raising `POLYGON_COUNT_THRESHOLD` from 30 to 500 in `constants.py`

## Relevant Files
Use these files to implement the feature:

- `app/core/geometry.py` - **Main refactor target**. Contains `_calculate_net_areas()` function (lines 572-630) that will be replaced. Shapely imports (`ShapelyPolygon`) already present from Unit A.

- `app/core/constants.py` - Contains `POLYGON_COUNT_THRESHOLD` (line 136, currently 30) which should be raised to 500 after the Shapely refactor improves performance.

- `app/core/types.py` - Defines `Polygon` type alias as `list[tuple[float, float]]` (line 33). Return type must remain unchanged.

- `app/tests/core/test_content_zone.py` - Contains net area calculation tests in `TestNetAreaCalculation` class (lines 404-482). All tests must continue to pass.

## Implementation Plan

### Phase 1: Preparation
Review the current `_calculate_net_areas()` implementation to understand all edge cases. Verify that Shapely imports (`ShapelyPolygon`) are already in place from Unit A. Confirm all 484 tests pass before making changes.

### Phase 2: Core Implementation
Replace the `_calculate_net_areas()` function body with the Shapely-based implementation:
- Convert all polygons to Shapely objects once
- Add invalid polygon handling (return 0.0 for invalid polygons)
- Use Shapely's `contains()` for containment checks
- Use Shapely's `difference()` for geometric subtraction
- Calculate net area from the resulting geometry

### Phase 3: Integration
Update the `POLYGON_COUNT_THRESHOLD` constant from 30 to 500 to take advantage of Shapely's improved performance. Run full test suite to validate zero regressions.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Prerequisites
- Confirm Shapely imports are present in `app/core/geometry.py` from Unit A:
  - `from shapely import Polygon as ShapelyPolygon`
- Run `uv run pytest app/tests/` to confirm all 484 tests pass before changes

### Step 2: Review Current Implementation
- Read `_calculate_net_areas()` function (lines 572-630 in `app/core/geometry.py`)
- Note the current behavior:
  - Calculates gross areas using `_shoelace_area()` for all polygons
  - Uses `_polygon_contains_polygon()` for containment checks
  - Subtracts gross areas of contained polygons (manual area subtraction)
  - Checks abort event every 10 polygons
  - Returns list sorted by net area descending
- This complexity will be replaced with Shapely's geometric difference

### Step 3: Replace _calculate_net_areas Implementation
- Replace the function body with the following implementation:
  ```python
  def _calculate_net_areas(
      polygons: list[Polygon],
      abort_event: threading.Event | None = None,
  ) -> list[tuple[Polygon, float]]:
      """
      Calculate net area for each polygon using Shapely geometric difference.

      For each polygon, calculates its area after subtracting any contained
      polygons using Shapely's difference() operation. This provides accurate
      net areas even for complex nested polygon arrangements.

      Complexity: O(n^2) with efficient GEOS-based operations
      - n polygons to process
      - n containment checks per polygon (GEOS optimized)
      - difference() operations are efficient for contained polygons

      Args:
          polygons: List of Polygon objects to analyze.
          abort_event: Optional threading.Event to signal abort request.

      Returns:
          List of (polygon, net_area) tuples sorted by net_area descending.

      Raises:
          GeometryAbortedError: If abort_event is set during processing.
      """
      if not polygons:
          return []

      if abort_event and abort_event.is_set():
          raise GeometryAbortedError("Net area calculation aborted")

      shapely_polys = [ShapelyPolygon(p) for p in polygons]
      results: list[tuple[Polygon, float]] = []

      for i, (poly, shapely_poly) in enumerate(zip(polygons, shapely_polys)):
          if not shapely_poly.is_valid:
              results.append((poly, 0.0))
              continue

          # Subtract all contained polygons using difference
          net_poly = shapely_poly
          for j, other in enumerate(shapely_polys):
              if i != j and shapely_poly.contains(other):
                  net_poly = net_poly.difference(other)

          results.append((poly, abs(net_poly.area)))

      results.sort(key=lambda x: x[1], reverse=True)
      return results
  ```
- Keep the function signature unchanged
- Update the docstring to reflect Shapely usage and improved complexity

### Step 4: Run Net Area Calculation Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py::TestNetAreaCalculation -v`
- All tests must pass:
  - `test_net_area_single_polygon`
  - `test_net_area_nested_polygons`
  - `test_net_area_multiple_nested`
  - `test_net_area_disjoint_polygons`
  - `test_net_area_empty_list`
  - `test_net_area_abort_event`

### Step 5: Run Content Zone Detection Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py -v`
- All 52+ content zone tests must pass

### Step 6: Run Geometry Tests
- Execute: `uv run pytest app/tests/core/test_geometry.py -v`
- All geometry tests must continue to pass (unchanged by this refactor)

### Step 7: Update POLYGON_COUNT_THRESHOLD
- In `app/core/constants.py`, update line 136:
  - Change `POLYGON_COUNT_THRESHOLD: int = 30` to `POLYGON_COUNT_THRESHOLD: int = 500`
  - Update the docstring to reflect the new value and Shapely optimization:
    ```python
    POLYGON_COUNT_THRESHOLD: int = 500
    """Maximum polygons for content zone net area calculation.
    Blocks with more polygons skip content zone detection.
    Rationale: With Shapely's efficient GEOS operations, can handle 500 polygons
    in reasonable time (previously 30 with O(n^3) manual calculation)."""
    ```

### Step 8: Run Threshold Tests
- Execute: `uv run pytest app/tests/core/test_content_zone.py::TestThresholdSkips -v`
- Verify threshold behavior still works correctly with new value

### Step 9: Run Full Test Suite
- Execute: `uv run pytest app/tests/`
- All 484 tests must pass with zero failures

### Step 10: Run Type Checker
- Execute: `uv run mypy app/`
- Must pass with no errors
- ShapelyPolygon type should be recognized from existing imports

### Step 11: Run Linter and Formatter
- Execute: `uv run ruff check app/`
- Execute: `uv run ruff format app/`
- Fix any issues reported

### Step 12: Verify Implementation
- Confirm `_calculate_net_areas()` uses Shapely `difference()` operation
- Confirm invalid polygon handling is in place
- Confirm `POLYGON_COUNT_THRESHOLD` is updated to 500
- Confirm docstring accurately describes new implementation

## Testing Strategy

### Unit Tests
- Existing `TestNetAreaCalculation` tests validate core functionality:
  - Single polygon returns gross area as net area
  - Nested polygons correctly subtract contained areas
  - Multiple nesting levels handled correctly
  - Disjoint polygons each get full gross area as net area
  - Empty input returns empty list
  - Abort event handling raises GeometryAbortedError

### Integration Tests
- `TestContentZoneDetection` tests validate end-to-end detection with net areas
- `TestTrimValueCalculation` tests validate trim values derived from content zones
- `TestThresholdSkips` tests validate `POLYGON_COUNT_THRESHOLD` behavior

### Edge Cases
- Empty polygon list - should return empty list
- Single polygon - net area equals gross area
- Nested polygons - outer area minus inner area
- Multiple nesting levels - correct chain of subtractions
- Disjoint polygons - no area subtraction
- Invalid/degenerate polygons - return 0.0 area
- Self-intersecting polygons - Shapely handles gracefully
- Large polygon counts (under new threshold) - should complete efficiently
- Abort event - should raise GeometryAbortedError before processing

### Playwright MCP Tests
Not applicable - this is a core geometry function without UI interaction.

## Acceptance Criteria
1. `_calculate_net_areas()` uses Shapely `difference()` instead of manual area subtraction
2. Function signature unchanged: `(polygons, abort_event) -> list[tuple[Polygon, float]]`
3. Return type unchanged: sorted list of (Polygon, net_area) tuples, descending by area
4. Abort event handling preserved (check at start before processing)
5. Invalid polygon handling added (return 0.0 for invalid Shapely polygons)
6. `POLYGON_COUNT_THRESHOLD` increased from 30 to 500 in `constants.py`
7. All existing tests pass (484 total)
8. Type checking passes (`uv run mypy app/`)
9. Linting passes (`uv run ruff check app/`)
10. Docstring updated to reflect new implementation and complexity

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_content_zone.py::TestNetAreaCalculation -v` - Run net area calculation tests specifically
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests (should be unaffected)
- `uv run pytest app/tests/` - Run full test suite (484 tests expected)
- `uv run mypy app/` - Run type checker
- `uv run ruff check app/` - Run linter
- `uv run ruff format app/` - Run formatter

## Notes
- **Units A and B Completed**: Shapely imports and adapter functions are already in place. `_extract_line_cycles()` already uses `polygonize()`.
- **Backwards Compatibility**: Function signature and return type remain unchanged. Only internal implementation changes.
- **Complexity Improvement**: The new implementation is O(n^2) with GEOS-optimized operations vs the previous O(n^3) with Python loops. The `difference()` operation is efficient because it operates on the actual geometry rather than iterating through vertices.
- **Invalid Polygon Handling**: The new implementation adds explicit handling for invalid Shapely polygons (e.g., self-intersecting, degenerate) by returning 0.0 area. This is more robust than the previous implementation.
- **Threshold Increase**: Raising `POLYGON_COUNT_THRESHOLD` from 30 to 500 enables content zone detection on significantly more complex CAD blocks. The 500 limit is conservative and could potentially be raised further based on performance testing.
- **Test Compatibility**: Existing test DXF files and test cases should produce identical results with the new implementation since the mathematical outcome (net areas) remains the same.
- **Future Optimization**: For very large polygon counts, `shapely.prepared.prep()` could be used to pre-process polygons for faster repeated containment checks. This optimization is not included in this unit but could be added if needed.
