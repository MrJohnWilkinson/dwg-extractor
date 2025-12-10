# Feature: Core Geometry Functions for Polygon Filtering (Unit 2)

## Feature Description
This feature adds the two core geometry calculation functions needed for polygon filtering in content zone detection:
1. `calculate_polygon_area()` - Calculates the surface area of a polygon using Shapely
2. `calculate_shortest_straight_side()` - Calculates the shortest merged straight side length of a polygon, merging consecutive collinear edges before finding the minimum

This is Unit 2 of the Polygon Filter Implementation, building on the constants and types foundation from Unit 1. It provides the calculation functions that will be used by the filtering logic in Unit 3 (extractor integration) and Unit 4 (GUI controls).

## User Story
As a CAD engineer processing DXF files
I want to calculate polygon area and shortest side length
So that small artifact polygons can be filtered out of content zone calculations, improving the accuracy of detected content zones

## Problem Statement
When calculating content zone bounding boxes, small artifact polygons (dust, debris, construction lines, annotation elements) can skew results. Before filtering can be implemented, the application needs:
1. A function to calculate polygon surface area in DXF drawing units
2. A function to calculate the shortest straight side of a polygon, which correctly merges consecutive collinear edges (handling split LINE segments that represent a single side)

Currently, while `_shoelace_area()` exists as an internal function in geometry.py, there is no public API for area calculation. Additionally, there is no function to calculate shortest straight side with collinear edge merging.

## Solution Statement
1. Add `calculate_polygon_area(polygon: Polygon) -> float` function in `geometry.py`:
   - Uses Shapely's `ShapelyPolygon.area` property
   - Returns absolute value (always positive)
   - Returns 0.0 for degenerate polygons (fewer than 3 vertices)
   - Similar to existing `_shoelace_area()` but without leading underscore (public API)

2. Add `calculate_shortest_straight_side(polygon: Polygon, angle_tolerance: float = 1.0) -> float` function in `geometry.py`:
   - Merges consecutive collinear edges into single sides before finding minimum
   - Uses angle-based collinearity detection with configurable tolerance (default 1 degree)
   - Handles angle wraparound at 180 degrees
   - Returns 0.0 for degenerate polygons
   - Ignores degenerate edges with length < 1e-9

3. Add `math` module import to support trigonometric calculations in shortest side function

## Relevant Files
Use these files to implement the feature:

- **app/core/geometry.py** - Main geometry calculation module
  - Add `math` import at top of file
  - Add `calculate_polygon_area()` function after existing geometry functions
  - Add `calculate_shortest_straight_side()` function after `calculate_polygon_area()`
  - Functions should follow existing patterns (docstrings, type hints, logging)

- **app/core/types.py** - Type definitions (read-only reference)
  - Contains `Polygon` type alias used by the new functions
  - Already imported in geometry.py

- **app/tests/core/test_geometry.py** - Geometry module tests
  - Add `TestCalculatePolygonArea` test class
  - Add `TestCalculateShortestStraightSide` test class
  - Follow existing test patterns in the file

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Add the `math` module import to `geometry.py`. This is required for the `calculate_shortest_straight_side()` function which uses `math.degrees()`, `math.atan2()`, and `math.sqrt()`.

### Phase 2: Core Implementation
Implement the two geometry calculation functions:
1. `calculate_polygon_area()` - straightforward Shapely area calculation
2. `calculate_shortest_straight_side()` - more complex algorithm with collinear edge merging

### Phase 3: Integration
Add comprehensive unit tests for both functions, covering:
- Standard polygon shapes (squares, rectangles, triangles)
- Edge merging behavior for collinear edges
- Degenerate cases (empty, single point, two points)
- Edge cases (very small sides, wraparound angles)

## Step by Step Tasks

### Step 1: Add math Import to geometry.py
Add the `math` module import at the top of `app/core/geometry.py` with the other standard library imports:

```python
import math
import threading
from typing import Any
```

The `math` module is needed for:
- `math.degrees()` - Convert radians to degrees
- `math.atan2()` - Calculate angle from coordinates
- `math.sqrt()` - Calculate edge length

### Step 2: Add calculate_polygon_area() Function
Add the `calculate_polygon_area()` function to `app/core/geometry.py` after the existing `_from_shapely_polygon()` function (around line 54):

```python
def calculate_polygon_area(polygon: Polygon) -> float:
    """
    Calculate the surface area of a polygon.

    Uses Shapely for accurate area calculation. This is the public API
    for area calculation, suitable for use in polygon filtering.

    Args:
        polygon: List of (x, y) vertices from _extract_paint_bucket_regions()

    Returns:
        Area in DXF drawing units squared (always positive).
        Returns 0.0 for degenerate polygons (fewer than 3 vertices).

    Examples:
        >>> calculate_polygon_area([(0, 0), (10, 0), (10, 10), (0, 10)])
        100.0
        >>> calculate_polygon_area([(0, 0), (3, 0), (3, 4)])
        6.0
    """
    if len(polygon) < 3:
        return 0.0
    shapely_poly = ShapelyPolygon(polygon)
    return abs(shapely_poly.area)
```

### Step 3: Add calculate_shortest_straight_side() Function
Add the `calculate_shortest_straight_side()` function to `app/core/geometry.py` immediately after `calculate_polygon_area()`:

```python
def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> float:
    """
    Calculate the shortest straight side of a polygon.

    Merges consecutive collinear edges into single sides before
    finding the minimum. This correctly handles cases where a single
    straight side is represented as multiple LINE segments in the DXF
    (e.g., LINE1 Part1 + LINE1 Part2 being counted as one side).

    Args:
        polygon: List of (x, y) vertices (closed polygon, no repeat of first point)
        angle_tolerance: Maximum angle deviation to consider edges collinear (degrees).
                        Default 1.0 degree handles minor coordinate variations.

    Returns:
        Length of shortest straight side in DXF drawing units.
        Returns 0.0 for degenerate polygons (fewer than 3 vertices).

    Examples:
        >>> calculate_shortest_straight_side([(0, 0), (100, 0), (100, 50), (0, 50)])
        50.0
        >>> # Rectangle with split bottom edge - still finds 50 as shortest
        >>> calculate_shortest_straight_side([(0, 0), (50, 0), (100, 0), (100, 50), (0, 50)])
        50.0
    """
    if len(polygon) < 3:
        return 0.0

    # Close the polygon by appending first vertex
    vertices = polygon + [polygon[0]]

    def edge_angle(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate angle of edge in degrees (0-180 range)."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        return angle % 180

    def edge_length(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def angles_collinear(a1: float, a2: float, tolerance: float) -> bool:
        """Check if two angles are within tolerance (handles wraparound)."""
        diff = abs(a1 - a2)
        return diff <= tolerance or abs(diff - 180) <= tolerance

    # Build list of merged straight sides
    straight_sides: list[float] = []

    i = 0
    while i < len(vertices) - 1:
        # Start a new side
        side_start = vertices[i]
        current_angle = edge_angle(vertices[i], vertices[i + 1])

        # Extend side while consecutive edges are collinear
        j = i + 1
        while j < len(vertices) - 1:
            next_angle = edge_angle(vertices[j], vertices[j + 1])
            if angles_collinear(current_angle, next_angle, angle_tolerance):
                j += 1
            else:
                break

        # Calculate total length of merged side
        side_end = vertices[j]
        side_length = edge_length(side_start, side_end)

        if side_length > 1e-9:  # Ignore degenerate edges
            straight_sides.append(side_length)

        i = j

    return min(straight_sides) if straight_sides else 0.0
```

### Step 4: Add Unit Tests for calculate_polygon_area()
Add the `TestCalculatePolygonArea` test class to `app/tests/core/test_geometry.py`:

- Import the new function: `from core.geometry import calculate_polygon_area`
- Create test class with the following tests:
  - `test_square_area` - Verify 10x10 square returns 100.0
  - `test_rectangle_area` - Verify 20x10 rectangle returns 200.0
  - `test_triangle_area` - Verify right triangle with base 10, height 10 returns 50.0
  - `test_irregular_polygon_area` - Verify irregular quadrilateral area calculation
  - `test_degenerate_polygon_empty` - Verify empty list returns 0.0
  - `test_degenerate_polygon_single_point` - Verify single point returns 0.0
  - `test_degenerate_polygon_two_points` - Verify two points (line) returns 0.0
  - `test_area_always_positive` - Verify area is positive regardless of vertex winding order

### Step 5: Add Unit Tests for calculate_shortest_straight_side()
Add the `TestCalculateShortestStraightSide` test class to `app/tests/core/test_geometry.py`:

- Import the new function: `from core.geometry import calculate_shortest_straight_side`
- Create test class with the following tests:
  - `test_square_shortest_side` - 10x10 square returns 10.0
  - `test_rectangle_shortest_side` - 100x50 rectangle returns 50.0
  - `test_collinear_edge_merging` - Rectangle with split bottom edge still finds correct shortest side
  - `test_collinear_edge_merging_three_segments` - Bottom edge split into 3 parts still merges correctly
  - `test_triangle_shortest_side` - 3-4-5 right triangle returns 3.0
  - `test_degenerate_polygon_empty` - Empty list returns 0.0
  - `test_degenerate_polygon_two_points` - Two points returns 0.0
  - `test_custom_angle_tolerance` - Verify custom tolerance parameter works
  - `test_very_small_edges_ignored` - Verify edges < 1e-9 are ignored
  - `test_angle_wraparound` - Verify collinearity detection handles 180-degree wraparound

### Step 6: Run Validation Commands
Execute all validation commands to ensure zero regressions:

```bash
# Type check all application code
uv run mypy app/

# Lint all application code
uv run ruff check app/

# Format check
uv run ruff format app/ --check

# Run geometry tests specifically
uv run pytest app/tests/core/test_geometry.py -v

# Run all tests to ensure zero regressions
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests
1. **TestCalculatePolygonArea** class:
   - Standard shapes: square, rectangle, triangle
   - Area always positive regardless of vertex winding
   - Degenerate cases: empty, 1 point, 2 points all return 0.0
   - Irregular polygon area calculation

2. **TestCalculateShortestStraightSide** class:
   - Standard shapes: square (all sides equal), rectangle (shorter side)
   - Collinear edge merging: split edges counted as single side
   - Triangle with unequal sides
   - Degenerate cases return 0.0
   - Custom angle tolerance parameter
   - Very small edges (< 1e-9) are ignored
   - Angle wraparound at 180 degrees

### Integration Tests
Not applicable for this unit - these are standalone geometry functions with no integration points yet. Integration tests will be added in Unit 3 when these functions are called from `_detect_content_zone()`.

### Edge Cases
1. Empty polygon returns 0.0
2. Single-point polygon returns 0.0
3. Two-point polygon (line) returns 0.0
4. Self-intersecting polygons (Shapely handles these gracefully)
5. Counter-clockwise vs clockwise winding (area always positive)
6. Very small edges (< 1e-9 length) are ignored in shortest side calculation
7. Collinear edges at exactly 0 and 180 degrees (wraparound handling)
8. Large polygons with many vertices
9. Polygons with all edges equal length (returns that length)

### Playwright MCP Tests
Not applicable for this unit - no GUI changes are included.

## Acceptance Criteria
1. `calculate_polygon_area(polygon)` function exists in `geometry.py` and returns correct area for standard shapes
2. `calculate_polygon_area()` returns 0.0 for degenerate polygons (< 3 vertices)
3. `calculate_polygon_area()` always returns positive values regardless of winding order
4. `calculate_shortest_straight_side(polygon, angle_tolerance)` function exists in `geometry.py`
5. `calculate_shortest_straight_side()` correctly merges collinear edges before finding minimum
6. `calculate_shortest_straight_side()` returns 0.0 for degenerate polygons
7. `calculate_shortest_straight_side()` ignores edges shorter than 1e-9 units
8. `math` module is imported in `geometry.py`
9. All new tests pass
10. All existing tests pass (backward compatibility)
11. Type checking passes with `uv run mypy app/`
12. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/test_geometry.py::TestCalculatePolygonArea -v` - Run area calculation tests
- `uv run pytest app/tests/core/test_geometry.py::TestCalculateShortestStraightSide -v` - Run shortest side tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run all geometry tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This is Unit 2 of a multi-unit implementation plan for polygon filtering (source: `ai_output/020-polygon-filter-implementation-plan.md`)
- Unit 1 (completed - commit 0332046) added constants and `PolygonMetrics` TypedDict
- Unit 3 will add extractor integration to pass filter parameters through `extract_blocks()` and call these functions in `_detect_content_zone()`
- Unit 4 will add GUI controls (checkboxes and entry fields) for the filter settings
- The `calculate_polygon_area()` function is essentially the same as existing `_shoelace_area()` but:
  - Uses public naming convention (no leading underscore)
  - Has more detailed docstring with examples
  - Is designed for external use in filtering logic
- The `calculate_shortest_straight_side()` function uses angle-based collinearity detection (Approach 1 from analysis doc) because:
  - More control over what constitutes "collinear"
  - Handles flattened arcs correctly (they have consistent angles even if not perfectly collinear)
  - Default 1-degree tolerance handles minor coordinate variations
- All measurements are in DXF drawing units (same as Precision Fix and Gap Bridge amounts)
- The `PolygonMetrics` TypedDict from Unit 1 has a `perimeter` field for future extensibility, but perimeter calculation is not implemented in this unit as it's not needed for filtering

### Algorithm Details for calculate_shortest_straight_side()

The algorithm works as follows:
1. Close the polygon by appending the first vertex to the end
2. For each vertex, calculate the angle of the edge to the next vertex (0-180 degree range)
3. Merge consecutive edges that have collinear angles (within tolerance)
4. Calculate the total length from the start of a merged side to its end
5. Return the minimum of all merged side lengths

The angle-based approach handles edge cases like:
- Edges that are exactly horizontal (0 degrees)
- Edges that are exactly vertical (90 degrees)
- Edges near the 180-degree boundary (wraparound handling)
- Split LINE segments that should be counted as one side
