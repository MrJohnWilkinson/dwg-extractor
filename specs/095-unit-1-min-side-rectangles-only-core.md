# Chore: Min Side Filter - Rectangles-Only Core Geometry Change

## Chore Description

Modify `calculate_shortest_straight_side()` to return both the shortest side length and the side count as a tuple, then update the filter logic in `_detect_content_zone()` to only apply the min_side_filter to 4-sided rectangles. Complex polygons with more than 4 sides should pass through the filter unaffected.

This change ensures that the min_side_filter setting only rejects small rectangles (like hatches and detail boxes) while preserving complex polygons that may have short sides as part of their legitimate geometry.

## Relevant Files

Use these files to resolve the chore:

- `app/core/geometry.py` - Contains `calculate_shortest_straight_side()` function (lines 87-164) and `_detect_content_zone()` function (lines 1746-1762) that need modification
- `app/tests/core/test_geometry.py` - Contains `TestCalculateShortestStraightSide` test class (lines 1762-1896) that needs updating to handle the new tuple return type
- `app/core/types.py` - Contains `Polygon` type alias used by the geometry functions (no changes needed, reference only)

## Step by Step Tasks

### Step 1: Update `calculate_shortest_straight_side()` Return Type and Docstring

**File:** `app/core/geometry.py`

- Change function signature return type from `float` to `tuple[float, int]`
- Update the docstring to document the new return type semantics:
  - `shortest_side_length`: Length of shortest merged side in DXF units
  - `side_count`: Total number of straight sides after collinear merging
- Update return statements:
  - Change `return 0.0` to `return (0.0, 0)` for degenerate polygons
  - Change `return min(straight_sides) if straight_sides else 0.0` to `return (min(straight_sides), len(straight_sides))` with proper handling for empty list

**Before (line 90):**
```python
def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> float:
```

**After:**
```python
def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> tuple[float, int]:
```

**Before (lines 115-116):**
```python
    if len(polygon) < 3:
        return 0.0
```

**After:**
```python
    if len(polygon) < 3:
        return (0.0, 0)
```

**Before (line 164):**
```python
    return min(straight_sides) if straight_sides else 0.0
```

**After:**
```python
    if not straight_sides:
        return (0.0, 0)
    return (min(straight_sides), len(straight_sides))
```

### Step 2: Update Docstring Content

**File:** `app/core/geometry.py` (lines 91-106)

Replace the existing docstring with comprehensive documentation for the new return type:

```python
    """
    Calculate the shortest straight side and total side count of a polygon.

    Merges consecutive collinear edges into single sides before
    finding the minimum. This correctly handles cases where a single
    straight side is represented as multiple LINE segments in the DXF
    (e.g., LINE1 Part1 + LINE1 Part2 being counted as one side).

    Args:
        polygon: List of (x, y) vertices (closed polygon, no repeat of first point)
        angle_tolerance: Maximum angle deviation to consider edges collinear (degrees).
                        Default 1.0 degree handles minor coordinate variations.

    Returns:
        Tuple of (shortest_side_length, side_count) where:
        - shortest_side_length: Length of shortest merged side in DXF units
        - side_count: Total number of straight sides after collinear merging

        For rectangles, side_count will be 4.
        For complex shapes, side_count will be > 4.
        Returns (0.0, 0) for degenerate polygons (fewer than 3 vertices).

    Examples:
        >>> calculate_shortest_straight_side([(0, 0), (100, 0), (100, 50), (0, 50)])
        (50.0, 4)
        >>> # Rectangle with split bottom edge - still finds 50 as shortest, 4 sides
        >>> calculate_shortest_straight_side([(0, 0), (50, 0), (100, 0), (100, 50), (0, 50)])
        (50.0, 4)
    """
```

### Step 3: Update Filter Logic in `_detect_content_zone()`

**File:** `app/core/geometry.py` (lines 1749-1755)

Replace the simple list comprehension with a helper function that implements rectangles-only filtering:

**Before:**
```python
    if min_side_filter > 0:
        pre_side_count = len(all_shapes)
        all_shapes = [
            s
            for s in all_shapes
            if calculate_shortest_straight_side(s) >= min_side_filter
        ]
```

**After:**
```python
    if min_side_filter > 0:
        pre_side_count = len(all_shapes)

        def passes_min_side_filter(polygon: Polygon) -> bool:
            """Check if polygon passes min side filter (only applies to 4-sided rectangles)."""
            shortest_side, side_count = calculate_shortest_straight_side(polygon)
            # Only filter 4-sided rectangles; pass all complex polygons
            if side_count != 4:
                return True
            return shortest_side >= min_side_filter

        all_shapes = [s for s in all_shapes if passes_min_side_filter(s)]
```

### Step 4: Update Tests for New Return Type

**File:** `app/tests/core/test_geometry.py`

Update all assertions in `TestCalculateShortestStraightSide` class to handle tuple returns. Each test needs to:
1. Destructure the tuple or access elements by index
2. Verify both the shortest side length AND the side count

**Test updates required:**

- `test_square_shortest_side`: Expect `(10.0, 4)` - square has 4 equal sides
- `test_rectangle_shortest_side`: Expect `(50.0, 4)` - rectangle has 4 sides
- `test_collinear_edge_merging`: Expect `(50.0, 4)` - merged rectangle has 4 sides
- `test_collinear_edge_merging_three_segments`: Expect `(50.0, 4)` - still 4 sides after merging
- `test_triangle_shortest_side`: Expect `(3.0, 3)` - triangle has 3 sides
- `test_degenerate_polygon_empty`: Expect `(0.0, 0)` - empty polygon
- `test_degenerate_polygon_two_points`: Expect `(0.0, 0)` - insufficient points
- `test_custom_angle_tolerance`: Update to check tuple[0] for shortest side
- `test_very_small_edges_ignored`: Expect `(50.0, 4)` - rectangle after ignoring degenerate edge
- `test_angle_wraparound`: Expect `(10.0, 4)` - horizontal rectangle
- `test_all_edges_equal`: Expect `(10.0, 4)` - square

**Example test update:**

```python
def test_square_shortest_side(self) -> None:
    """Test that 10x10 square returns (10.0, 4) for all equal sides."""
    square: list[tuple[float, float]] = [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
        (0.0, 10.0),
    ]
    shortest_side, side_count = calculate_shortest_straight_side(square)
    assert shortest_side == pytest.approx(10.0)
    assert side_count == 4
```

### Step 5: Add New Test for Complex Polygon Side Count

**File:** `app/tests/core/test_geometry.py`

Add a new test to verify that complex polygons (>4 sides) return the correct side count:

```python
def test_hexagon_side_count(self) -> None:
    """Test that hexagon returns correct side count of 6."""
    # Regular hexagon-like shape
    hexagon: list[tuple[float, float]] = [
        (10.0, 0.0),
        (20.0, 0.0),
        (25.0, 8.66),
        (20.0, 17.32),
        (10.0, 17.32),
        (5.0, 8.66),
    ]
    shortest_side, side_count = calculate_shortest_straight_side(hexagon)
    assert side_count == 6
    assert shortest_side > 0.0

def test_l_shaped_polygon_side_count(self) -> None:
    """Test that L-shaped polygon returns 6 sides."""
    # L-shape: 6 vertices, 6 sides
    l_shape: list[tuple[float, float]] = [
        (0.0, 0.0),
        (20.0, 0.0),
        (20.0, 10.0),
        (10.0, 10.0),
        (10.0, 30.0),
        (0.0, 30.0),
    ]
    shortest_side, side_count = calculate_shortest_straight_side(l_shape)
    assert side_count == 6
    assert shortest_side == pytest.approx(10.0)  # Shortest is the 10-unit sides
```

### Step 6: Run Validation Commands

Execute all validation commands to ensure zero regressions:

```bash
# Run geometry tests specifically
uv run pytest app/tests/core/test_geometry.py -v

# Run full test suite
uv run pytest app/tests/ -v

# Run type checking
uv run mypy app/

# Run linting
uv run ruff check app/

# Run formatting check
uv run ruff format app/ --check
```

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# 1. Run geometry-specific tests (includes TestCalculateShortestStraightSide)
uv run pytest app/tests/core/test_geometry.py -v

# 2. Run content zone tests (uses the filter logic)
uv run pytest app/tests/core/test_content_zone.py -v

# 3. Run polygon filter tests (may use shortest side calculation)
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v

# 4. Run full test suite to catch any regressions
uv run pytest app/tests/ -v

# 5. Type checking - verify tuple return type is correctly handled everywhere
uv run mypy app/

# 6. Linting - ensure code style is maintained
uv run ruff check app/

# 7. Format check - ensure formatting is consistent
uv run ruff format app/ --check
```

## Notes

- The `Polygon` type alias is defined in `app/core/types.py` as `list[tuple[float, float]]`
- The function currently returns `float` and needs to return `tuple[float, int]`
- There is only ONE non-test call site in `_detect_content_zone()` that needs updating
- The test file has 11 test methods that all need their assertions updated
- The collinear edge merging logic means that a polygon with 5 vertices can still be a 4-sided rectangle (if one side is split into segments)
- Complex polygons (L-shapes, T-shapes, etc.) will have side_count > 4 and should pass through the min_side_filter unchanged
