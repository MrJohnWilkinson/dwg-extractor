# Feature: Paint-Bucket Edge Extraction Functions (Units 3+4)

## Feature Description
Create two new functions in the geometry module to support paint-bucket polygon detection. Unit 3 adds `_extract_all_edges()` to extract all edges from LINE and LWPOLYLINE/POLYLINE entities as Shapely LineString objects. Unit 4 adds `_extract_paint_bucket_regions()` to combine edges, split at intersections using `unary_union()`, and find all closed regions using `polygonize()`.

These functions are foundational building blocks for the paint-bucket algorithm that will provide more accurate polygon detection matching user visual expectations.

## User Story
As a CAD drawing analyst
I want polygon detection that finds all visually enclosed regions
So that polygon counts match what users see when using a paint-bucket fill tool in CAD software

## Problem Statement
The current polygon detection only finds:
1. Closed LWPOLYLINE entities (explicitly closed CAD objects)
2. Cycles formed by LINE entities alone

This misses regions formed by combinations of LWPOLYLINE edges and LINE dividers. For example, a closed rectangle LWPOLYLINE with a LINE divider should produce 2 regions, but current detection only finds 1.

## Solution Statement
Implement two new functions that:
1. `_extract_all_edges()`: Extract ALL edges from the block as LineString objects, including both LINE entities and individual segments from LWPOLYLINE/POLYLINE entities (including closing edges for closed polylines)
2. `_extract_paint_bucket_regions()`: Combine all edges, use `unary_union()` to split at intersections, then `polygonize()` to find all enclosed regions

These functions will be used in Unit 5 to replace the separate LWPOLYLINE and LINE extraction in `_detect_content_zone()`.

## Relevant Files
Use these files to implement the feature:

- `app/core/geometry.py` - Target file for new functions. Contains existing edge/polygon extraction functions like `_count_line_segments()` (line 358-372), `_extract_closed_lwpolylines()` (line 375-404), and `_extract_line_cycles()` (line 526-581). New functions follow similar patterns.
- `app/core/types.py` - Contains the `Polygon` type alias used for return values: `list[tuple[float, float]]`
- `app/tests/core/test_geometry.py` - Test file for geometry module. Contains existing test classes like `TestExtractLineCycles` that demonstrate testing patterns.
- `ai_output/030-paint-bucket-polygon-detection-plan.md` - Reference plan with exact function signatures and implementation details.

### New Files
None - all changes are additions to existing files.

## Implementation Plan
### Phase 1: Foundation
No foundation work needed - all required imports (`LineString`, `unary_union`, `polygonize`) are already present in `geometry.py`. The `Polygon` type alias is already defined in `types.py`.

### Phase 2: Core Implementation
1. Add `_extract_all_edges()` function after `_count_line_segments()` (around line 373)
2. Add `_extract_paint_bucket_regions()` function after `_extract_all_edges()`
3. Add unit tests for both functions

### Phase 3: Integration
These functions are standalone utilities that will be integrated in Unit 5. No integration work needed in this unit.

## Step by Step Tasks

### Step 1: Add `_extract_all_edges()` function
Add the following function after `_count_line_segments()` (around line 373) in `app/core/geometry.py`:

```python
def _extract_all_edges(block_def: BlockLayout) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Extracts edges from:
    - LINE entities (start to end as single edge)
    - LWPOLYLINE/POLYLINE entities (all vertices as edges, closing edge if closed)

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of LineString objects representing all edges in the block.
    """
    edges: list[LineString] = []

    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                # Convert polyline to edge segments
                for i in range(len(points) - 1):
                    edges.append(LineString([points[i], points[i + 1]]))
                # Add closing edge if closed
                if hasattr(entity, 'closed') and entity.closed and len(points) >= 2:
                    edges.append(LineString([points[-1], points[0]]))
            except (AttributeError, IndexError):
                continue

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges
```

### Step 2: Add `_extract_paint_bucket_regions()` function
Add the following function after `_extract_all_edges()` in `app/core/geometry.py`:

```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    """
    Extract all visual regions using paint-bucket algorithm.

    Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
    splits at intersections using unary_union, and finds all closed
    regions using polygonize.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading.Event to signal abort request

    Returns:
        List of Polygon objects (coordinate tuples) representing all visual regions.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    edges = _extract_all_edges(block_def)

    if not edges:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Region detection aborted")

    # Merge and split at all intersections
    merged = unary_union(edges)
    if merged.is_empty:
        return []

    line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
    polygons = list(polygonize(line_segments))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} paint-bucket regions")
    return result
```

### Step 3: Add unit tests for `_extract_all_edges()`
Add test class to `app/tests/core/test_geometry.py`:

```python
class TestExtractAllEdges:
    """Test suite for _extract_all_edges function."""

    def test_extracts_line_entities(self) -> None:
        """Test extraction of LINE entities as edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINE_TEST")
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))

        edges = _extract_all_edges(block)

        assert len(edges) == 2

    def test_extracts_closed_lwpolyline_edges(self) -> None:
        """Test extraction of closed LWPOLYLINE as individual edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CLOSED_POLY_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        edges = _extract_all_edges(block)

        # 4 edges: 3 between consecutive points + 1 closing edge
        assert len(edges) == 4

    def test_extracts_open_lwpolyline_edges(self) -> None:
        """Test extraction of open LWPOLYLINE (no closing edge)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="OPEN_POLY_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50)], close=False)

        edges = _extract_all_edges(block)

        # 2 edges between 3 consecutive points, no closing edge
        assert len(edges) == 2

    def test_empty_block_returns_empty_list(self) -> None:
        """Test that empty block returns empty edge list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_TEST")

        edges = _extract_all_edges(block)

        assert edges == []
```

### Step 4: Add unit tests for `_extract_paint_bucket_regions()`
Add test class to `app/tests/core/test_geometry.py`:

```python
class TestExtractPaintBucketRegions:
    """Test suite for _extract_paint_bucket_regions function."""

    def test_rectangle_with_vertical_divider(self) -> None:
        """Test rectangle split by vertical divider produces 2 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_DIVIDER")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # LINE divider at midpoint
        block.add_line((50, 0), (50, 50))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 2 regions (left and right)
        assert len(regions) == 2

    def test_rectangle_with_grid_dividers(self) -> None:
        """Test rectangle with cross dividers produces 4 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_GRID")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Horizontal divider
        block.add_line((0, 50), (100, 50))
        # Vertical divider
        block.add_line((50, 0), (50, 100))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 4 regions (2x2 grid)
        assert len(regions) == 4

    def test_lines_only_rectangle(self) -> None:
        """Test that LINE-only rectangle still works."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINES_RECT")

        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 50))
        block.add_line((100, 50), (0, 50))
        block.add_line((0, 50), (0, 0))

        regions = _extract_paint_bucket_regions(block)

        assert len(regions) == 1

    def test_empty_block_returns_empty_list(self) -> None:
        """Test that empty block returns empty region list."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY_TEST")

        regions = _extract_paint_bucket_regions(block)

        assert regions == []

    def test_abort_event_raises_error(self) -> None:
        """Test that set abort_event raises GeometryAbortedError."""
        import threading
        doc = ezdxf.new()
        block = doc.blocks.new(name="ABORT_TEST")
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)

        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(GeometryAbortedError):
            _extract_paint_bucket_regions(block, abort_event)
```

### Step 5: Update test imports
Update the imports at the top of `app/tests/core/test_geometry.py` to include the new functions:

```python
from core.geometry import (
    _calculate_segments,
    _categorize_rotation,
    _extract_all_edges,
    _extract_line_cycles,
    _extract_paint_bucket_regions,
    _get_block_bounding_box,
    _get_intersection_points,
    GeometryAbortedError,
)
```

### Step 6: Run validation commands
Execute all validation commands to ensure zero regressions.

## Testing Strategy
### Unit Tests
- `TestExtractAllEdges`: Tests for LINE extraction, closed/open LWPOLYLINE extraction, empty block handling
- `TestExtractPaintBucketRegions`: Tests for mixed entity polygonization, LINE-only rectangles, abort event handling

### Integration Tests
Not applicable for this unit - functions are standalone utilities.

### Edge Cases
- Empty blocks (no entities)
- Blocks with only LINE entities
- Blocks with only LWPOLYLINE entities
- Closed vs open LWPOLYLINE handling
- Abort event during processing

### Playwright MCP Tests
Not applicable - these are internal geometry functions with no UI component.

## Acceptance Criteria
- [ ] `_extract_all_edges()` function added after line 373 in geometry.py
- [ ] Function extracts LINE entities as single edges
- [ ] Function extracts LWPOLYLINE/POLYLINE entities as individual segment edges
- [ ] Function adds closing edge for closed polylines
- [ ] `_extract_paint_bucket_regions()` function added after `_extract_all_edges()`
- [ ] Function uses `unary_union()` to split at intersections
- [ ] Function uses `polygonize()` to find closed regions
- [ ] Function handles abort_event parameter correctly
- [ ] Function returns internal Polygon format (not Shapely Polygon)
- [ ] All new tests pass
- [ ] All existing tests pass (536+ tests)
- [ ] mypy type checking passes
- [ ] ruff linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/geometry.py` - Type check the geometry module
- `uv run ruff check app/core/geometry.py` - Lint the geometry module
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- The `Polygon` type used in return values is the internal format: `list[tuple[float, float]]`, not Shapely's `Polygon` class
- All required imports (`LineString`, `unary_union`, `polygonize`) are already present in geometry.py
- The `GeometryAbortedError` exception is already defined in the module
- These functions prepare for Unit 5 which will update `_detect_content_zone()` to use the paint-bucket approach
- Function placement after `_count_line_segments()` maintains logical grouping of edge-related utilities
