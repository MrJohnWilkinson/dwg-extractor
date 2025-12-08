# Feature: Shapely Geometry Refactor (US-8)

## Executive Summary

Replace custom geometry implementations in `geometry.py` with Shapely library functions to improve performance, reliability, and code maintainability. The biggest win is replacing the complex DFS cycle detection algorithm with Shapely's `polygonize()` function, eliminating timeout handling and O(n^3) performance bottlenecks.

## Table Summary

| Current Function | Shapely Replacement | Performance Impact |
|-----------------|--------------------|--------------------|
| `_shoelace_area()` | `polygon.area` | Marginal (C-based) |
| `_point_in_polygon()` | `polygon.contains(point)` | Improved (GEOS) |
| `_polygon_contains_polygon()` | `outer.contains(inner)` | Improved (GEOS) |
| `_get_polygon_bbox()` | `polygon.bounds` | Marginal |
| `_get_union_bounding_box()` | `unary_union().bounds` | Improved (native) |
| `_extract_line_cycles()` | `polygonize(lines)` | **Major** (no DFS) |
| `_calculate_net_areas()` | `polygon.difference()` | **Major** (O(n) vs O(n^3)) |

## Relevant Files

- **`app/core/geometry.py`** - Main refactor target. Contains 7 custom geometry functions to replace with Shapely equivalents. Lines 391-848 contain content zone detection logic.

- **`app/core/constants.py`** - Contains `POLYGON_COUNT_THRESHOLD`, `LINE_SEGMENT_THRESHOLD`, `CYCLE_DETECTION_TIMEOUT_SECONDS`. These safeguards may become unnecessary with Shapely's efficient algorithms.

- **`app/core/types.py`** - Defines `Polygon` type alias as `list[tuple[float, float]]`. May need adapter functions for Shapely's `Polygon` objects.

- **`app/tests/core/test_geometry.py`** - Contains existing geometry tests. Tests must pass unchanged (behavior compatibility).

- **`pyproject.toml`** - Add `shapely>=2.0.0` to dependencies.

## Feature Description

Refactor the geometry module to use Shapely, a Python library for manipulation and analysis of planar geometric objects. Shapely uses GEOS (C++ library) under the hood, providing battle-tested algorithms for geometric operations that are significantly faster than pure Python implementations.

**Key Benefits:**
1. **Performance**: GEOS-based algorithms are 10-100x faster than pure Python
2. **Robustness**: Battle-tested algorithms handle edge cases correctly
3. **Simplicity**: Replace 200+ lines of custom code with ~50 lines using Shapely
4. **Remove safeguards**: `POLYGON_COUNT_THRESHOLD` and `LINE_SEGMENT_THRESHOLD` may become unnecessary

## User Story

As a developer
I want to use Shapely for geometric operations
So that content zone detection is faster and more reliable without arbitrary thresholds

## Problem Statement

Current geometry.py has several issues:
1. **DFS cycle detection** (`_extract_line_cycles`) is O(exponential) with 5-second timeout
2. **Net area calculation** (`_calculate_net_areas`) is O(n^3) requiring 30-polygon limit
3. **LINE segment threshold** of 200 prevents analysis of complex blocks
4. **Custom algorithms** lack robustness for edge cases (collinear points, self-intersecting polygons)

## Solution Statement

Replace custom implementations with Shapely equivalents:
1. `shapely.ops.polygonize()` replaces DFS cycle detection - handles thousands of line segments efficiently
2. `polygon.difference()` for hole subtraction replaces O(n^3) containment checking
3. `polygon.area`, `polygon.bounds`, `polygon.contains()` for basic operations
4. Remove or raise thresholds since Shapely handles complex geometry efficiently

## Implementation Plan

### Phase 1: Add Dependency
Add Shapely to project dependencies and create adapter utilities for converting between internal `Polygon` type and Shapely objects.

### Phase 2: Replace Basic Operations
Replace simple functions (`_shoelace_area`, `_point_in_polygon`, `_polygon_contains_polygon`, `_get_polygon_bbox`) with Shapely equivalents. These are low-risk, drop-in replacements.

### Phase 3: Replace Cycle Detection
Replace `_extract_line_cycles()` with `shapely.ops.polygonize()`. This is the highest-impact change, eliminating timeout handling and iteration limits.

### Phase 4: Optimize Net Area Calculation
Replace `_calculate_net_areas()` with Shapely's difference operations. Use `unary_union()` for combining nested polygons efficiently.

### Phase 5: Adjust Thresholds
Evaluate whether `POLYGON_COUNT_THRESHOLD` and `LINE_SEGMENT_THRESHOLD` are still needed. Either remove or significantly raise these limits.

## Step by Step Tasks

### Step 1: Add Shapely dependency to pyproject.toml
- Add `"shapely>=2.0.0"` to `dependencies` list in `[project]` section
- Run `uv sync` to install the dependency
- Verify installation: `uv run python -c "import shapely; print(shapely.__version__)"`

### Step 2: Add Shapely imports and adapter functions to geometry.py
- Add imports at top of file:
  ```python
  from shapely import Polygon as ShapelyPolygon, Point
  from shapely.geometry import LineString
  from shapely.ops import polygonize, unary_union
  ```
- Add adapter function `_to_shapely_polygon(polygon: Polygon) -> ShapelyPolygon`
- Add adapter function `_from_shapely_polygon(shapely_poly: ShapelyPolygon) -> Polygon`

### Step 3: Replace _shoelace_area with Shapely
- Replace function body with:
  ```python
  def _shoelace_area(polygon: Polygon) -> float:
      if len(polygon) < 3:
          return 0.0
      shapely_poly = ShapelyPolygon(polygon)
      return abs(shapely_poly.area)
  ```
- Maintain same function signature for backwards compatibility

### Step 4: Replace _point_in_polygon with Shapely
- Replace function body with:
  ```python
  def _point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool:
      if len(polygon) < 3:
          return False
      shapely_poly = ShapelyPolygon(polygon)
      return shapely_poly.contains(Point(point))
  ```

### Step 5: Replace _polygon_contains_polygon with Shapely
- Replace function body with:
  ```python
  def _polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool:
      if len(outer) < 3 or len(inner) < 3:
          return False
      outer_shapely = ShapelyPolygon(outer)
      inner_shapely = ShapelyPolygon(inner)
      return outer_shapely.contains(inner_shapely)
  ```

### Step 6: Replace _get_polygon_bbox with Shapely
- Replace function body with:
  ```python
  def _get_polygon_bbox(polygon: Polygon) -> tuple[float, float, float, float]:
      if not polygon:
          return (0.0, 0.0, 0.0, 0.0)
      shapely_poly = ShapelyPolygon(polygon)
      minx, miny, maxx, maxy = shapely_poly.bounds
      return (minx, miny, maxx, maxy)
  ```

### Step 7: Replace _get_union_bounding_box with Shapely
- Replace function body with:
  ```python
  def _get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]:
      if not polygons:
          return (0.0, 0.0, 0.0, 0.0)
      shapely_polys = [ShapelyPolygon(p) for p in polygons]
      union = unary_union(shapely_polys)
      minx, miny, maxx, maxy = union.bounds
      return (minx, miny, maxx, maxy)
  ```

### Step 8: Run tests after basic replacements
- Run `uv run pytest app/tests/core/test_geometry.py -v`
- Run `uv run pytest app/tests/core/test_content_zone.py -v`
- Fix any failures before proceeding

### Step 9: Replace _extract_line_cycles with polygonize
- Replace the entire 130-line DFS implementation with:
  ```python
  def _extract_line_cycles(
      block_def: BlockLayout,
      abort_event: threading.Event | None = None,
  ) -> list[Polygon]:
      # Collect all LINE segments as LineStrings
      lines = []
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
- Remove timeout handling - `polygonize()` is fast enough not to need it

### Step 10: Simplify _calculate_net_areas with Shapely difference
- Replace the O(n^3) containment check with geometric difference:
  ```python
  def _calculate_net_areas(
      polygons: list[Polygon],
      abort_event: threading.Event | None = None,
  ) -> list[tuple[Polygon, float]]:
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

### Step 11: Update constants - raise or remove thresholds
- In `constants.py`, increase `LINE_SEGMENT_THRESHOLD` from 200 to 5000
- Increase `POLYGON_COUNT_THRESHOLD` from 30 to 500
- Remove `CYCLE_DETECTION_TIMEOUT_SECONDS` or keep as emergency fallback
- Add comment explaining thresholds are conservative with Shapely

### Step 12: Run full test suite
- Run `uv run pytest app/tests/ -v`
- Run `uv run mypy app/`
- Run `uv run ruff check app/`
- Fix any issues

### Step 13: Add Shapely type stubs (if needed)
- If mypy reports missing type hints, add `types-shapely` to dev dependencies
- Or add `# type: ignore[import]` comments if stubs unavailable

### Step 14: Performance validation
- Test with previously problematic blocks that hit thresholds
- Verify content zone detection now works on blocks that were skipped
- Document performance improvements in commit message

## Testing Strategy

### Unit Tests
- All existing tests in `test_geometry.py` must pass unchanged
- All existing tests in `test_content_zone.py` must pass unchanged
- Behavior must be identical - only implementation changes

### Integration Tests
- Run full extraction on real DXF files with complex blocks
- Verify blocks that previously hit `LINE_SEGMENT_THRESHOLD` now process correctly
- Verify blocks that previously hit `POLYGON_COUNT_THRESHOLD` now process correctly

### Edge Cases
- Empty polygons (< 3 vertices)
- Self-intersecting polygons (Shapely handles gracefully)
- Collinear points (degenerate polygons)
- Very large coordinate values
- Nested polygons (holes within holes)

### Performance Tests
- Compare extraction time before/after on complex DXF files
- Measure memory usage with large polygon counts
- Verify no regressions on simple files

## Acceptance Criteria

1. All 480+ existing tests pass with zero failures
2. Type checking passes with `uv run mypy app/`
3. Linting passes with `uv run ruff check app/`
4. `shapely>=2.0.0` added to dependencies
5. `_extract_line_cycles()` uses `polygonize()` instead of DFS
6. `_calculate_net_areas()` uses Shapely difference operations
7. Basic geometry functions use Shapely equivalents
8. `LINE_SEGMENT_THRESHOLD` increased to 5000 or removed
9. `POLYGON_COUNT_THRESHOLD` increased to 500 or removed
10. No behavioral changes - same trim values for same inputs

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- Run geometry tests specifically:
  - `uv run pytest app/tests/core/test_geometry.py -v`
- Run content zone tests:
  - `uv run pytest app/tests/core/test_content_zone.py -v`
- Run all tests to validate zero regressions:
  - `uv run pytest app/tests/`
- Run type checker:
  - `uv run mypy app/`
- Run linter:
  - `uv run ruff check app/`
- Run formatter:
  - `uv run ruff format app/`
- Verify Shapely installation:
  - `uv run python -c "from shapely.ops import polygonize; print('OK')"`

## Recommendations

1. **Start with basic functions** - Replace `_shoelace_area`, `_point_in_polygon` first as they're low-risk
2. **Test incrementally** - Run tests after each function replacement
3. **Keep old code commented** - For quick rollback during initial testing
4. **Profile before/after** - Document actual performance gains
5. **Consider shapely.prepared** - For repeated containment checks, `prepared.prep()` offers additional speedup

## Next Steps

1. Implement Phase 1-2 (dependency + basic functions) first
2. Validate with existing test suite
3. Implement Phase 3-4 (cycle detection + net areas)
4. Test on real DXF files that previously hit thresholds
5. Adjust thresholds based on performance testing
6. Document performance improvements

## Notes

- **Shapely 2.0+**: Requires Shapely 2.0 or later for best performance and API consistency
- **GEOS dependency**: Shapely requires GEOS C library (usually bundled with wheel)
- **Thread safety**: Shapely operations are thread-safe for read-only operations
- **Memory**: Shapely objects use more memory than simple coordinate lists, but the performance gains outweigh this
- **Invalid geometries**: Shapely can handle invalid geometries gracefully with `make_valid()`
