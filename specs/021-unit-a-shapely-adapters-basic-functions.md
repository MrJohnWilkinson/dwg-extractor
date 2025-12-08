# Chore: Unit A - Shapely Adapters and Basic Functions

## Chore Description
Replace basic geometry implementations in `geometry.py` with Shapely library functions. This is the first unit of the Shapely Geometry Refactor (US-8), covering Steps 2-8 from the refactor document. The refactor replaces custom implementations of area calculation, point-in-polygon testing, polygon containment, and bounding box functions with Shapely equivalents.

Key objectives:
- Add Shapely imports and adapter functions for converting between internal `Polygon` type and Shapely objects
- Replace `_shoelace_area()` with `ShapelyPolygon.area`
- Replace `_point_in_polygon()` with `ShapelyPolygon.contains(Point)`
- Replace `_polygon_contains_polygon()` with `ShapelyPolygon.contains()`
- Replace `_get_polygon_bbox()` with `ShapelyPolygon.bounds`
- Replace `_get_union_bounding_box()` with `unary_union().bounds`
- Maintain backwards compatibility - same function signatures, same behavior
- All existing tests must pass after changes

**Context**: Shapely 2.1.2 is already installed (Step 1 completed in prior work).

## Relevant Files
Use these files to resolve the chore:

- `app/core/geometry.py` - **Main refactor target**. Contains the custom geometry functions to replace with Shapely equivalents. Functions affected: `_shoelace_area()` (lines 391-423), `_point_in_polygon()` (lines 426-459), `_polygon_contains_polygon()` (lines 462-484), `_get_polygon_bbox()` (lines 487-506), `_get_union_bounding_box()` (lines 509-544).

- `app/core/types.py` - Defines the `Polygon` type alias as `list[tuple[float, float]]`. Reference for adapter function signatures.

- `app/tests/core/test_geometry.py` - Existing geometry tests that must continue to pass. Tests bounding box, intersection points, segments, and rotation categorization.

- `app/tests/core/test_content_zone.py` - Existing content zone tests that must continue to pass. Tests area calculation, point-in-polygon, containment, net areas, and trim values.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Shapely Imports to geometry.py
- Add the following imports at the top of `app/core/geometry.py` after the existing imports:
  ```python
  from shapely import Polygon as ShapelyPolygon, Point
  from shapely.geometry import LineString
  from shapely.ops import polygonize, unary_union
  ```
- Note: `LineString` and `polygonize` are imported for future use (Unit B), but adding them now avoids duplicate import work later.

### Step 2: Add Adapter Functions
- Add two private adapter functions after the `logger = setup_logger(__name__)` line:
  ```python
  def _to_shapely_polygon(polygon: Polygon) -> ShapelyPolygon:
      """Convert internal Polygon type to Shapely Polygon."""
      return ShapelyPolygon(polygon)


  def _from_shapely_polygon(shapely_poly: ShapelyPolygon) -> Polygon:
      """Convert Shapely Polygon to internal Polygon type."""
      coords = list(shapely_poly.exterior.coords)[:-1]  # Exclude closing point
      return [(float(x), float(y)) for x, y in coords]
  ```

### Step 3: Replace _shoelace_area with Shapely
- Locate the `_shoelace_area()` function (approximately line 391)
- Replace the entire function body while keeping the docstring:
  ```python
  def _shoelace_area(polygon: Polygon) -> float:
      """
      Calculate the area of a polygon using Shapely.

      Args:
          polygon: List of (x, y) vertices forming a closed polygon.

      Returns:
          Absolute area of the polygon. Returns 0.0 for degenerate polygons
          (fewer than 3 vertices or collinear points).

      Examples:
          >>> _shoelace_area([(0, 0), (10, 0), (10, 10), (0, 10)])
          100.0
          >>> _shoelace_area([(0, 0), (3, 0), (3, 4)])
          6.0
      """
      if len(polygon) < 3:
          return 0.0
      shapely_poly = ShapelyPolygon(polygon)
      return abs(shapely_poly.area)
  ```

### Step 4: Replace _point_in_polygon with Shapely
- Locate the `_point_in_polygon()` function (approximately line 426)
- Replace the entire function body while keeping the docstring:
  ```python
  def _point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool:
      """
      Determine if a point is inside a polygon using Shapely.

      Args:
          point: (x, y) coordinates of the point to test.
          polygon: List of (x, y) vertices forming a closed polygon.

      Returns:
          True if the point is inside the polygon, False otherwise.
          Points exactly on the boundary may return either True or False.
      """
      if len(polygon) < 3:
          return False
      shapely_poly = ShapelyPolygon(polygon)
      return shapely_poly.contains(Point(point))
  ```

### Step 5: Replace _polygon_contains_polygon with Shapely
- Locate the `_polygon_contains_polygon()` function (approximately line 462)
- Replace the entire function body while keeping the docstring:
  ```python
  def _polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool:
      """
      Determine if one polygon completely contains another using Shapely.

      A polygon is considered to contain another if ALL vertices of the inner
      polygon are inside the outer polygon.

      Args:
          outer: The potentially containing polygon.
          inner: The potentially contained polygon.

      Returns:
          True if all vertices of inner are inside outer, False otherwise.
      """
      if len(outer) < 3 or len(inner) < 3:
          return False
      outer_shapely = ShapelyPolygon(outer)
      inner_shapely = ShapelyPolygon(inner)
      return outer_shapely.contains(inner_shapely)
  ```

### Step 6: Replace _get_polygon_bbox with Shapely
- Locate the `_get_polygon_bbox()` function (approximately line 487)
- Replace the entire function body while keeping the docstring:
  ```python
  def _get_polygon_bbox(polygon: Polygon) -> tuple[float, float, float, float]:
      """
      Calculate the bounding box of a polygon using Shapely.

      Args:
          polygon: List of (x, y) vertices.

      Returns:
          Tuple of (min_x, min_y, max_x, max_y).
          Returns (0, 0, 0, 0) for empty polygons.
      """
      if not polygon:
          return (0.0, 0.0, 0.0, 0.0)
      shapely_poly = ShapelyPolygon(polygon)
      minx, miny, maxx, maxy = shapely_poly.bounds
      return (minx, miny, maxx, maxy)
  ```

### Step 7: Replace _get_union_bounding_box with Shapely
- Locate the `_get_union_bounding_box()` function (approximately line 509)
- Replace the entire function body while keeping the docstring:
  ```python
  def _get_union_bounding_box(
      polygons: list[Polygon],
  ) -> tuple[float, float, float, float]:
      """
      Calculate the union bounding box encompassing all input polygons using Shapely.

      The union bounding box is the minimum axis-aligned rectangle that contains
      all vertices of all input polygons. This is used when multiple shapes tie
      for maximum net area to derive trim values from the combined area.

      Args:
          polygons: List of Polygon objects to calculate union bbox for.

      Returns:
          Tuple of (min_x, min_y, max_x, max_y) representing the union bounding box.
          Returns (0, 0, 0, 0) for empty input.

      Examples:
          >>> poly1 = [(0, 0), (10, 0), (10, 10), (0, 10)]
          >>> poly2 = [(20, 20), (30, 20), (30, 30), (20, 30)]
          >>> _get_union_bounding_box([poly1, poly2])
          (0.0, 0.0, 30.0, 30.0)
      """
      if not polygons:
          return (0.0, 0.0, 0.0, 0.0)
      shapely_polys = [ShapelyPolygon(p) for p in polygons]
      union = unary_union(shapely_polys)
      minx, miny, maxx, maxy = union.bounds
      return (minx, miny, maxx, maxy)
  ```

### Step 8: Run Geometry Tests
- Execute geometry unit tests to validate basic functions work correctly:
  ```bash
  uv run pytest app/tests/core/test_geometry.py -v
  ```
- All tests must pass before proceeding.

### Step 9: Run Content Zone Tests
- Execute content zone unit tests to validate area calculation, containment, and detection:
  ```bash
  uv run pytest app/tests/core/test_content_zone.py -v
  ```
- All tests must pass before proceeding.

### Step 10: Run Full Validation
- Execute the full validation suite to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate bounding box, intersection, and segment functions.
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests to validate area, containment, and detection functions.
- `uv run pytest app/tests/` - Run all tests to validate zero regressions across the entire test suite.
- `uv run mypy app/` - Run type checker to validate type annotations are correct.
- `uv run ruff check app/` - Run linter to validate code style.
- `uv run ruff format app/` - Run formatter to ensure consistent code formatting.

## Notes
- **Backwards Compatibility**: All function signatures remain unchanged. Only internal implementations are replaced with Shapely equivalents.
- **Edge Cases**: The early return guards for empty/degenerate inputs (`len(polygon) < 3`, `not polygon`) are preserved to maintain existing behavior.
- **Shapely Already Installed**: Shapely 2.1.2 is already in the project dependencies (verified in Step 1 of the main refactor).
- **Future Units**: Steps 9-14 from the main refactor document (cycle detection, net area optimization, threshold adjustments) are handled in subsequent units.
- **Type Hints**: Shapely 2.x has improved type hints, so mypy should pass without additional stubs.
- **Performance**: These basic replacements provide marginal performance improvements. The major gains come in Unit B with `polygonize()` replacing DFS cycle detection.
