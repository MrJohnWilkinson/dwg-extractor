# Feature: Unit 2 - Core Logic for Pre-filter and Post-filter in Geometry Module

## Feature Description

This unit implements the core filtering logic in the geometry module as part of the dual-stage filter feature. It adds two key capabilities:

1. **Pre-Filter Logic in `_extract_all_edges()`**: Modifies the edge extraction function to accept optional parameters that skip CIRCLE/ARC entities and/or filter out short LINE entities before the expensive `unary_union()` and `polygonize()` operations.

2. **Post-Filter Logic via `_polygon_has_curved_edges()`**: Adds a new function to detect if a polygon contains curved (non-straight) edges by analyzing vertex collinearity. This enables filtering out polygons that originated from curved entities after polygon detection.

These filters reduce processing time for complex DXF drawings and improve polygon detection accuracy by excluding unwanted geometry types.

## User Story

As a DXF Block Extractor user
I want the application to filter out curved entities and short lines during processing
So that content zone detection is faster and only detects relevant rectangular polygons

## Problem Statement

Complex DXF drawings often contain many curved entities (circles, arcs) and short line segments that:
1. Significantly increase processing time in `unary_union()` and `polygonize()` operations
2. Create unwanted polygons that clutter the polygon count
3. Make content zone detection less accurate by including irrelevant geometry

The current `_extract_all_edges()` function extracts all entities unconditionally, and there's no mechanism to identify or filter polygons that originated from curved entities.

## Solution Statement

Implement two complementary filtering mechanisms in the geometry module:

1. **Pre-filtering** by modifying `_extract_all_edges()` to accept `skip_curved_entities` and `min_line_length` parameters that filter entities during edge extraction
2. **Post-filtering** by adding `_polygon_has_curved_edges()` function that detects curved edges in polygons using geometric analysis

Both filters are designed with sensible defaults (disabled) to maintain backward compatibility with existing behavior.

## Relevant Files

Use these files to implement the feature:

- **`app/core/geometry.py`** - Target file for implementation. Contains `_extract_all_edges()` (~line 658) to modify and location after `_extract_paint_bucket_regions()` (~line 801) for new function.
- **`app/core/constants.py`** - Contains constants added in Unit 1: `CURVED_FILTER_TOLERANCE` (0.01), `DEFAULT_SKIP_CURVED_ENTITIES`, `DEFAULT_MIN_LINE_LENGTH_FILTER`, etc. Reference these in the implementation.
- **`app/tests/core/test_geometry.py`** - Existing geometry test file. Add new test classes for pre-filter and post-filter functionality.
- **`app/tests/assets/circle_arc_hatch_edges_test.dxf`** - Existing test asset with circles/arcs for testing pre-filter.

### New Files

No new files required. All implementation is in existing files.

## Implementation Plan

### Phase 1: Foundation

This phase was completed in Unit 1 which added:
- Constants: `DEFAULT_SKIP_CURVED_ENTITIES`, `DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED`, `DEFAULT_MIN_LINE_LENGTH_FILTER`, `MIN_LINE_LENGTH_FILTER_MIN/MAX`, `DEFAULT_CURVED_FILTER_ENABLED`, `CURVED_FILTER_TOLERANCE`
- Types: `skip_curved_entities`, `min_line_length_filter_enabled`, `min_line_length_filter_amount`, `curved_filter_enabled` in AppSettings
- Settings: New filter settings registered in SETTINGS_SECTIONS["filters"]

### Phase 2: Core Implementation (This Unit)

1. Modify `_extract_all_edges()` function signature to accept two new optional parameters
2. Add pre-filter logic for CIRCLE/ARC entities (skip when `skip_curved_entities=True`)
3. Add pre-filter logic for LINE entities (skip when length < `min_line_length`)
4. Add new `_polygon_has_curved_edges()` function after `_extract_paint_bucket_regions()`
5. Add comprehensive unit tests for all new functionality

### Phase 3: Integration (Future Units)

Future units will:
- Wire filter parameters through `_extract_paint_bucket_regions()` and `_detect_content_zone()`
- Add GUI controls in `settings_window.py`
- Connect GUI to extractor pipeline in `main.py`

## Step by Step Tasks

### Step 1: Import math module if not already imported

Verify `math` module is imported in `app/core/geometry.py` for the `math.sqrt()` calculation needed in the pre-filter logic.

- Check existing imports at top of file
- The `math` module should already be imported (used in `calculate_shortest_straight_side`)

### Step 2: Modify `_extract_all_edges()` function signature

Update the function signature at line 658 in `app/core/geometry.py`:

- Add `skip_curved_entities: bool = False` parameter
- Add `min_line_length: float = 0.0` parameter
- Update docstring to document the new pre-filter options

```python
def _extract_all_edges(
    block_def: BlockLayout,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[LineString]:
```

### Step 3: Add LINE pre-filter logic

Modify the LINE entity handler (around line 680-683) to filter short lines:

- Calculate line length using Euclidean distance formula
- Skip LINE entities shorter than `min_line_length` threshold
- Only apply filter when `min_line_length > 0`

```python
if entity_type == "LINE":
    start = entity.dxf.start
    end = entity.dxf.end
    # PRE-FILTER: Skip short LINE entities
    if min_line_length > 0:
        length = math.sqrt(
            (end.x - start.x) ** 2 + (end.y - start.y) ** 2
        )
        if length < min_line_length:
            continue
    edges.append(LineString([(start.x, start.y), (end.x, end.y)]))
```

### Step 4: Add CIRCLE pre-filter logic

Modify the CIRCLE entity handler (around line 695-696) to skip when filtering enabled:

```python
elif entity_type == "CIRCLE":
    # PRE-FILTER: Skip curved entities
    if skip_curved_entities:
        continue
    edges.extend(_extract_circle_edges(entity))
```

### Step 5: Add ARC pre-filter logic

Modify the ARC entity handler (around line 698-699) to skip when filtering enabled:

```python
elif entity_type == "ARC":
    # PRE-FILTER: Skip curved entities
    if skip_curved_entities:
        continue
    edges.extend(_extract_arc_edges(entity))
```

### Step 6: Update `_extract_all_edges()` docstring

Update the docstring to fully document the new functionality:

```python
"""
Extract ALL edges from block as LineStrings for unified polygonize.

Pre-filter options (reduce edge count before union):
- skip_curved_entities: Skip CIRCLE and ARC entities entirely
- min_line_length: Skip LINE entities shorter than threshold

Extracts edges from:
- LINE entities (start to end as single edge)
- LWPOLYLINE/POLYLINE entities (all vertices as edges, closing edge if closed)
- CIRCLE entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
- ARC entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
- HATCH boundary paths (PolylinePath and EdgePath variants)

Args:
    block_def: ezdxf block definition object
    skip_curved_entities: If True, skip CIRCLE and ARC entities. Default False.
    min_line_length: Skip LINE entities shorter than this threshold (drawing units).
                     Default 0.0 (no filtering).

Returns:
    List of LineString objects representing all edges in the block.
"""
```

### Step 7: Add `_polygon_has_curved_edges()` function

Add new function after `_extract_paint_bucket_regions()` (after line 801) in `app/core/geometry.py`:

```python
def _polygon_has_curved_edges(
    polygon: Polygon,
    tolerance: float = 0.01,
) -> bool:
    """
    Detect if a polygon contains curved (non-straight) edges.

    A polygon is considered to have curved edges if any edge has
    intermediate points that deviate from a straight line by more
    than the tolerance. This detects arcs/circles that were flattened
    during edge extraction.

    Args:
        polygon: List of (x, y) coordinate tuples representing polygon vertices.
        tolerance: Maximum deviation from straight line to consider
                   an edge as straight. Default 0.01 drawing units.

    Returns:
        True if polygon contains curved edges, False if all edges
        are straight (within tolerance).
    """
    if len(polygon) < 4:  # Less than 3 unique vertices (need at least 4 for curve detection)
        return False

    # For each triplet of consecutive vertices, check if middle point
    # deviates from the line connecting first and third points
    n = len(polygon)
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        p3 = polygon[(i + 2) % n]

        # Calculate perpendicular distance from p2 to line p1-p3
        ax, ay = p3[0] - p1[0], p3[1] - p1[1]
        bx, by = p2[0] - p1[0], p2[1] - p1[1]

        cross = abs(ax * by - ay * bx)
        line_length = math.sqrt(ax * ax + ay * ay)

        if line_length > 1e-9:
            distance = cross / line_length
            if distance > tolerance:
                return True

    return False
```

### Step 8: Add unit tests for LINE pre-filter

Add new test class `TestPreFilterLineLengthFilter` to `app/tests/core/test_geometry.py`:

- Test that default behavior (min_line_length=0) extracts all LINE entities
- Test that min_line_length filter excludes short lines
- Test that lines exactly at threshold are NOT excluded (< not <=)
- Test that lines above threshold are included
- Test with mixed line lengths
- Test with all lines below threshold returns empty list

```python
class TestPreFilterLineLengthFilter:
    """Test suite for LINE pre-filter in _extract_all_edges function."""

    def test_default_extracts_all_lines(self) -> None:
        """Test that default (min_line_length=0) extracts all lines."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_LINES")
        block.add_line((0, 0), (1, 0))  # Short line
        block.add_line((0, 0), (100, 0))  # Long line

        edges = _extract_all_edges(block, min_line_length=0)

        assert len(edges) == 2

    def test_filters_short_lines(self) -> None:
        """Test that short lines are filtered when min_line_length > 0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="FILTER_SHORT")
        block.add_line((0, 0), (1, 0))  # 1 unit (below threshold)
        block.add_line((0, 0), (100, 0))  # 100 units (above threshold)

        edges = _extract_all_edges(block, min_line_length=5.0)

        assert len(edges) == 1

    def test_line_at_threshold_not_filtered(self) -> None:
        """Test that line exactly at threshold is NOT filtered (< not <=)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="AT_THRESHOLD")
        block.add_line((0, 0), (5, 0))  # Exactly 5 units

        edges = _extract_all_edges(block, min_line_length=5.0)

        # Line is exactly at threshold, should NOT be filtered
        assert len(edges) == 1

    def test_all_lines_below_threshold(self) -> None:
        """Test that all lines below threshold returns empty list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_SHORT")
        block.add_line((0, 0), (1, 0))
        block.add_line((0, 0), (2, 0))
        block.add_line((0, 0), (3, 0))

        edges = _extract_all_edges(block, min_line_length=10.0)

        assert len(edges) == 0
```

### Step 9: Add unit tests for CIRCLE/ARC pre-filter

Add new test class `TestPreFilterSkipCurvedEntities` to `app/tests/core/test_geometry.py`:

- Test that default behavior (skip_curved_entities=False) extracts circles and arcs
- Test that skip_curved_entities=True skips CIRCLE entities
- Test that skip_curved_entities=True skips ARC entities
- Test that LWPOLYLINE and LINE entities are NOT affected
- Test with mixed entity types

```python
class TestPreFilterSkipCurvedEntities:
    """Test suite for skip_curved_entities pre-filter in _extract_all_edges function."""

    def test_default_extracts_circles(self) -> None:
        """Test that default (skip_curved_entities=False) extracts circles."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="WITH_CIRCLE")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block, skip_curved_entities=False)

        assert len(edges) > 10  # Circle produces many segments

    def test_skip_curved_filters_circles(self) -> None:
        """Test that skip_curved_entities=True skips CIRCLE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SKIP_CIRCLE")
        block.add_circle(center=(50, 50), radius=25)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 0

    def test_skip_curved_filters_arcs(self) -> None:
        """Test that skip_curved_entities=True skips ARC entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SKIP_ARC")
        block.add_arc(center=(50, 50), radius=25, start_angle=0, end_angle=90)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 0

    def test_skip_curved_does_not_affect_lines(self) -> None:
        """Test that skip_curved_entities does NOT affect LINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINES_ONLY")
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 2

    def test_skip_curved_does_not_affect_polylines(self) -> None:
        """Test that skip_curved_entities does NOT affect LWPOLYLINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="POLY_ONLY")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        edges = _extract_all_edges(block, skip_curved_entities=True)

        assert len(edges) == 4  # 4 edges of closed rectangle

    def test_mixed_entities_with_skip_curved(self) -> None:
        """Test mixed entities with skip_curved_entities=True."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED")
        block.add_line((0, 0), (100, 0))  # LINE - kept
        block.add_circle(center=(50, 50), radius=25)  # CIRCLE - skipped
        block.add_arc(center=(100, 100), radius=20, start_angle=0, end_angle=90)  # ARC - skipped
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10)], close=False)  # POLY - kept

        edges = _extract_all_edges(block, skip_curved_entities=True)

        # Only LINE (1) + LWPOLYLINE (2 edges, open) = 3 edges
        assert len(edges) == 3
```

### Step 10: Add unit tests for `_polygon_has_curved_edges()`

Add new test class `TestPolygonHasCurvedEdges` to `app/tests/core/test_geometry.py`:

- Test that simple rectangle returns False
- Test that polygon from circle returns True
- Test that triangle returns False
- Test with custom tolerance
- Test degenerate cases (empty, 3 points)

```python
class TestPolygonHasCurvedEdges:
    """Test suite for _polygon_has_curved_edges function."""

    def test_rectangle_returns_false(self) -> None:
        """Test that simple rectangle returns False (all straight edges)."""
        rectangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 50.0),
            (0.0, 50.0),
        ]

        result = _polygon_has_curved_edges(rectangle)

        assert result is False

    def test_triangle_returns_false(self) -> None:
        """Test that simple triangle returns False (all straight edges)."""
        triangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (50.0, 86.6),
        ]

        result = _polygon_has_curved_edges(triangle)

        assert result is False

    def test_circle_approximation_returns_true(self) -> None:
        """Test that circle approximated by many points returns True."""
        import math as m
        # Create circle approximation with 36 points
        circle: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 10)), 50 + 25 * m.sin(m.radians(i * 10)))
            for i in range(36)
        ]

        result = _polygon_has_curved_edges(circle)

        assert result is True

    def test_arc_approximation_returns_true(self) -> None:
        """Test that arc (partial circle) returns True."""
        import math as m
        # Create arc approximation with points every 10 degrees for 90 degrees
        # then straight lines back
        arc_points: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 10)), 50 + 25 * m.sin(m.radians(i * 10)))
            for i in range(10)
        ]
        # Add straight line closing points
        arc_points.extend([(50, 50), (75, 50)])

        result = _polygon_has_curved_edges(arc_points)

        assert result is True

    def test_custom_tolerance_tighter(self) -> None:
        """Test that tighter tolerance detects smaller deviations."""
        # Pentagon-like shape with slight curve (5 points on circle)
        import math as m
        pentagon: list[tuple[float, float]] = [
            (50 + 25 * m.cos(m.radians(i * 72)), 50 + 25 * m.sin(m.radians(i * 72)))
            for i in range(5)
        ]

        # With default tolerance (0.01), might not detect
        result_default = _polygon_has_curved_edges(pentagon, tolerance=0.01)
        # With very tight tolerance, might detect deviation
        result_tight = _polygon_has_curved_edges(pentagon, tolerance=0.001)

        # Pentagon with 5 points is close to straight edges
        # The deviation between consecutive points on a circle is subtle
        assert isinstance(result_default, bool)
        assert isinstance(result_tight, bool)

    def test_degenerate_empty_returns_false(self) -> None:
        """Test that empty list returns False."""
        result = _polygon_has_curved_edges([])

        assert result is False

    def test_degenerate_three_points_returns_false(self) -> None:
        """Test that polygon with 3 points returns False (need 4 for curve detection)."""
        triangle: list[tuple[float, float]] = [
            (0.0, 0.0),
            (100.0, 0.0),
            (50.0, 50.0),
        ]

        result = _polygon_has_curved_edges(triangle)

        assert result is False

    def test_l_shape_returns_false(self) -> None:
        """Test that L-shape polygon returns False (all straight edges)."""
        l_shape: list[tuple[float, float]] = [
            (0.0, 0.0),
            (50.0, 0.0),
            (50.0, 30.0),
            (20.0, 30.0),
            (20.0, 50.0),
            (0.0, 50.0),
        ]

        result = _polygon_has_curved_edges(l_shape)

        assert result is False
```

### Step 11: Add import for new function in test file

Update imports in `app/tests/core/test_geometry.py` to include the new function:

```python
from core.geometry import (
    # ... existing imports ...
    _polygon_has_curved_edges,
)
```

### Step 12: Add combined pre-filter test

Add test verifying both pre-filters work together:

```python
def test_combined_prefilters(self) -> None:
    """Test that both pre-filters work together."""
    doc = ezdxf.new()
    block = doc.blocks.new(name="COMBINED")
    block.add_line((0, 0), (1, 0))  # Short line - filtered by min_line_length
    block.add_line((0, 0), (100, 0))  # Long line - kept
    block.add_circle(center=(50, 50), radius=25)  # Circle - filtered by skip_curved

    edges = _extract_all_edges(block, skip_curved_entities=True, min_line_length=5.0)

    # Only the long line should remain
    assert len(edges) == 1
```

### Step 13: Run validation commands

Execute all validation commands to ensure zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests including new filter tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Testing Strategy

### Unit Tests

- **Pre-filter LINE length tests**: Verify `min_line_length` parameter correctly filters short LINE entities
- **Pre-filter skip curved tests**: Verify `skip_curved_entities` parameter skips CIRCLE and ARC entities
- **Combined pre-filter tests**: Verify both filters work together
- **Post-filter curved edges tests**: Verify `_polygon_has_curved_edges()` correctly detects curved polygons
- **Backward compatibility tests**: Verify default parameters maintain existing behavior

### Integration Tests

- Test that `_extract_all_edges()` still works correctly with `_extract_paint_bucket_regions()` when called with new parameters
- Test with real DXF assets containing circles, arcs, and lines

### Edge Cases

- Empty block returns empty edge list
- Block with only circles/arcs returns empty when skip_curved=True
- Block with all short lines returns empty when min_line_length is set
- Line exactly at threshold is NOT filtered (< not <=)
- Polygon with exactly 3 vertices returns False for curved detection
- Very tight tolerance in curved detection
- Polygon from large circle with many segments

### Playwright MCP Tests

- Not applicable for this unit (no GUI changes)

## Acceptance Criteria

1. `_extract_all_edges()` accepts `skip_curved_entities: bool = False` parameter
2. `_extract_all_edges()` accepts `min_line_length: float = 0.0` parameter
3. When `skip_curved_entities=True`, CIRCLE entities are skipped during edge extraction
4. When `skip_curved_entities=True`, ARC entities are skipped during edge extraction
5. When `min_line_length > 0`, LINE entities shorter than threshold are skipped
6. LWPOLYLINE and HATCH entities are NOT affected by `skip_curved_entities`
7. `_polygon_has_curved_edges()` function exists and correctly detects curved polygons
8. `_polygon_has_curved_edges()` returns False for simple rectangles and triangles
9. `_polygon_has_curved_edges()` returns True for circle/arc approximations
10. Default parameter values maintain backward compatibility
11. All existing geometry tests pass without modification
12. New tests verify all filter behaviors
13. `mypy app/` passes with no errors
14. `ruff check app/` passes with no errors
15. `pytest app/tests/` passes with all tests green

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_geometry.py::TestExtractAllEdges -v` - Run existing edge extraction tests
- `uv run pytest app/tests/core/test_geometry.py::TestPreFilterLineLengthFilter -v` - Run new LINE pre-filter tests
- `uv run pytest app/tests/core/test_geometry.py::TestPreFilterSkipCurvedEntities -v` - Run new curved entity pre-filter tests
- `uv run pytest app/tests/core/test_geometry.py::TestPolygonHasCurvedEdges -v` - Run new post-filter tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run all geometry tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Notes

- **Backward Compatibility**: All new parameters have defaults that preserve existing behavior (`skip_curved_entities=False`, `min_line_length=0.0`)
- **Filter Comparison**: The `min_line_length` filter uses `<` comparison (not `<=`) so lines exactly at the threshold are included
- **Polygon Type**: The `_polygon_has_curved_edges()` function uses the internal `Polygon` type which is `list[tuple[float, float]]`, not Shapely's `Polygon`
- **Curved Detection Algorithm**: Uses perpendicular distance from middle vertex to line connecting adjacent vertices. If distance exceeds tolerance, the edge is considered curved.
- **Constants Reference**: Use `CURVED_FILTER_TOLERANCE` (0.01) from `constants.py` as the default tolerance for `_polygon_has_curved_edges()`
- **Future Integration**: This unit only adds the core functions. Future units will wire these through `_extract_paint_bucket_regions()`, `_detect_content_zone()`, and the GUI.
- **HATCH Entities**: HATCH entities are NOT affected by `skip_curved_entities` since they may contain important boundary information
