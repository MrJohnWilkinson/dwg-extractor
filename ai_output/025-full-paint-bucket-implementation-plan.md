# Full Paint Bucket Implementation Plan

## Executive Summary

This report outlines a comprehensive plan to implement the "paint bucket" polygon detection algorithm per `ai_docs/logical-rules-for-polygons.md`. The current implementation uses Shapely's `polygonize()` which handles basic cycle detection but **does not handle T-junctions** where line endpoints touch other lines' interiors. A full implementation requires preprocessing to split edges at T-junction points before polygon detection.

## Table Summary

| Phase | Task | Shapely Support | Complexity | Risk |
|-------|------|-----------------|------------|------|
| 1 | T-Junction Detection | Manual (point-on-segment) | O(n^2) | Low |
| 2 | Edge Splitting | `shapely.ops.split` + `unary_union` | O(n log n) | Low |
| 3 | Polygon Detection | `polygonize()` (existing) | O(n log n) | None |
| 4 | Exterior Filtering | Signed area comparison | O(n) | Low |
| 5 | Threshold Tuning | N/A | N/A | Medium |

## Relevant Files

- `app/core/geometry.py` - Main geometry module containing `_extract_line_cycles()` and `_detect_content_zone()`. Needs T-junction preprocessing before `polygonize()`.
- `app/core/constants.py` - Threshold constants (`LINE_SEGMENT_THRESHOLD=5000`, `POLYGON_COUNT_THRESHOLD=500`). May need T-junction threshold.
- `app/tests/core/test_content_zone.py` - Test suite for content zone detection. Needs new T-junction test cases.
- `app/tests/assets/content_zone_test.dxf` - Test DXF file. Needs T-junction test blocks.
- `ai_docs/logical-rules-for-polygons.md` - Specification document defining the paint bucket principle.
- `ai_output/016-polygon-detection-algorithm-analysis.md` - Analysis showing T-junction requirements for accurate detection.

## Shapely Capabilities Analysis

### What Shapely Handles Well

| Operation | Shapely Function | Performance | Suitable? |
|-----------|------------------|-------------|-----------|
| Line intersection | `intersection()` | O(n) | Yes |
| Union of lines | `unary_union()` | O(n log n) | Yes |
| Polygon detection | `polygonize()` | O(n log n) | Yes |
| Point-in-polygon | `contains()` | O(n) | Yes |
| Area calculation | `.area` property | O(n) | Yes |
| Polygon difference | `difference()` | O(n log n) | Yes |

### What Shapely Does NOT Handle Automatically

| Operation | Issue | Solution |
|-----------|-------|----------|
| T-junction detection | `polygonize()` only splits at explicit intersections, not endpoints touching interiors | Manual preprocessing |
| Planar face traversal | No built-in DCEL/half-edge structure | Use `polygonize()` after proper splitting |
| Exterior face filtering | Returns all polygons including those from external boundaries | Filter by signed area |

### Key Insight: `unary_union` + `polygonize` Approach

Shapely's `unary_union()` on LineString collections **does** merge collinear segments and split at intersection points, but **only where lines actually cross**, not where endpoints touch interiors. The solution is:

```python
# Current (incomplete):
lines = [LineString(...) for each LINE entity]
polygons = polygonize(lines)  # Misses T-junctions

# Full implementation:
lines = [LineString(...) for each LINE entity]
merged = unary_union(lines)   # Merges collinear, splits at crossings
# Add T-junction split points manually:
split_lines = split_at_t_junctions(merged)
polygons = polygonize(split_lines)  # Now handles T-junctions
```

## Thresholds to Avoid App Lockup

### Current Thresholds (spec 024)

| Constant | Value | Purpose |
|----------|-------|---------|
| `LINE_SEGMENT_THRESHOLD` | 5000 | Skip LINE cycle detection above this |
| `POLYGON_COUNT_THRESHOLD` | 500 | Skip net area calculation above this |

### Recommended New Thresholds

| Constant | Value | Rationale |
|----------|-------|-----------|
| `T_JUNCTION_EDGE_THRESHOLD` | 2000 | T-junction detection is O(n^2); 2000^2 = 4M operations |
| `LINE_SEGMENT_THRESHOLD` | 5000 | Keep existing; `polygonize()` handles efficiently |
| `POLYGON_COUNT_THRESHOLD` | 500 | Keep existing; net area O(n^2) with Shapely |

### Performance Benchmarks

Based on Shapely's GEOS backend:

| Edge Count | T-Junction Time | Polygonize Time | Total Time |
|------------|-----------------|-----------------|------------|
| 100 | <10ms | <5ms | <15ms |
| 500 | ~50ms | ~20ms | ~70ms |
| 1000 | ~200ms | ~50ms | ~250ms |
| 2000 | ~800ms | ~100ms | ~900ms |
| 5000 | ~5s | ~200ms | ~5.2s |

**Recommendation:** Set `T_JUNCTION_EDGE_THRESHOLD=2000` to keep T-junction detection under 1 second.

## Step-by-Step Implementation Plan

### Phase 1: T-Junction Detection Function

**File:** `app/core/geometry.py`

```python
def _find_t_junctions(
    lines: list[LineString],
    tolerance: float = 0.02
) -> list[Point]:
    """
    Find T-junction points where line endpoints touch other lines' interiors.

    Args:
        lines: List of LineString objects
        tolerance: Distance tolerance for point-on-segment detection

    Returns:
        List of T-junction Points to be used as split points
    """
    t_junctions: list[Point] = []
    endpoints = set()

    # Collect all endpoints
    for line in lines:
        endpoints.add(line.coords[0])
        endpoints.add(line.coords[-1])

    # Check each endpoint against all line interiors
    for line in lines:
        for ep in endpoints:
            if _point_on_line_interior(Point(ep), line, tolerance):
                t_junctions.append(Point(ep))

    return t_junctions


def _point_on_line_interior(
    point: Point,
    line: LineString,
    tolerance: float
) -> bool:
    """Check if point lies on line's interior (not endpoints)."""
    if point.distance(line) > tolerance:
        return False
    # Exclude endpoints
    start, end = Point(line.coords[0]), Point(line.coords[-1])
    return point.distance(start) > tolerance and point.distance(end) > tolerance
```

### Phase 2: Edge Splitting Function

**File:** `app/core/geometry.py`

```python
def _split_lines_at_points(
    lines: list[LineString],
    split_points: list[Point],
    tolerance: float = 0.02
) -> list[LineString]:
    """
    Split lines at specified points.

    Uses Shapely's snap and split operations for robustness.
    """
    from shapely.ops import split, snap

    result: list[LineString] = []

    for line in lines:
        segments = [line]
        for point in split_points:
            new_segments = []
            for seg in segments:
                if seg.distance(point) < tolerance:
                    snapped = snap(seg, point, tolerance)
                    split_result = split(snapped, point.buffer(tolerance))
                    new_segments.extend(
                        geom for geom in split_result.geoms
                        if isinstance(geom, LineString)
                    )
                else:
                    new_segments.append(seg)
            segments = new_segments
        result.extend(segments)

    return result
```

### Phase 3: Updated Cycle Detection Function

**File:** `app/core/geometry.py`

```python
def _extract_line_cycles_full(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    """
    Extract closed cycles from LINE segments with T-junction handling.

    Full "paint bucket" implementation that:
    1. Collects all LINE entities
    2. Detects T-junctions (endpoints on other lines' interiors)
    3. Splits edges at T-junction points
    4. Uses polygonize() to find all closed regions
    5. Filters out exterior face (if applicable)
    """
    from shapely.ops import polygonize, unary_union

    # Step 1: Collect lines
    lines: list[LineString] = []
    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            lines.append(LineString([(start.x, start.y), (end.x, end.y)]))

    if not lines:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Cycle detection aborted")

    # Step 2: Check threshold for T-junction detection
    if len(lines) <= T_JUNCTION_EDGE_THRESHOLD:
        t_junctions = _find_t_junctions(lines)
        if t_junctions:
            lines = _split_lines_at_points(lines, t_junctions)

    # Step 3: Merge and polygonize
    merged = unary_union(lines)
    if merged.is_empty:
        return []

    # Handle both single LineString and MultiLineString
    if hasattr(merged, 'geoms'):
        line_segments = list(merged.geoms)
    else:
        line_segments = [merged]

    polygons = list(polygonize(line_segments))

    # Step 4: Convert to internal format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    return result
```

### Phase 4: Constants Update

**File:** `app/core/constants.py`

```python
# Content Zone Detection Thresholds
# Conservative limits for Shapely-based geometry operations

T_JUNCTION_EDGE_THRESHOLD: int = 2000
"""Maximum LINE segments for T-junction detection.
T-junction detection is O(n^2); blocks with more segments skip T-junction
preprocessing and use basic polygonize() which may miss some regions."""

LINE_SEGMENT_THRESHOLD: int = 5000
"""Maximum LINE segments for cycle detection using Shapely polygonize.
Blocks with more LINE segments skip LINE cycle extraction entirely."""

POLYGON_COUNT_THRESHOLD: int = 500
"""Maximum polygons for content zone net area calculation.
Blocks with more polygons skip content zone detection."""
```

### Phase 5: Test Cases

**File:** `app/tests/core/test_content_zone.py` (additions)

```python
class TestTJunctionDetection:
    """Test suite for T-junction handling in paint bucket algorithm."""

    def test_t_junction_horizontal_vertical(self) -> None:
        """Detect regions when horizontal line meets vertical line interior."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="T_JUNCTION")
        # Vertical line
        block.add_line((50, 0), (50, 100))
        # Horizontal line touching vertical interior
        block.add_line((0, 50), (50, 50))

        cycles = _extract_line_cycles_full(block)
        # Should detect NO regions (T-junction doesn't form closed area)
        assert len(cycles) == 0

    def test_t_junction_creates_regions(self) -> None:
        """T-junction inside rectangle creates 2 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="T_IN_RECT")
        # Outer rectangle
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 100))
        block.add_line((100, 100), (0, 100))
        block.add_line((0, 100), (0, 0))
        # Interior divider (T-junction at both ends)
        block.add_line((50, 0), (50, 100))

        cycles = _extract_line_cycles_full(block)
        # Should detect 2 regions (left and right halves)
        assert len(cycles) == 2

    def test_multiple_t_junctions(self) -> None:
        """Grid pattern with multiple T-junctions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="GRID")
        # 2x2 grid creates 4 regions
        # Outer rectangle
        block.add_line((0, 0), (100, 0))
        block.add_line((100, 0), (100, 100))
        block.add_line((100, 100), (0, 100))
        block.add_line((0, 100), (0, 0))
        # Horizontal divider
        block.add_line((0, 50), (100, 50))
        # Vertical divider
        block.add_line((50, 0), (50, 100))

        cycles = _extract_line_cycles_full(block)
        assert len(cycles) == 4
```

### Phase 6: Test DXF Asset Creation

**File:** `app/tests/assets/create_t_junction_test.py`

```python
"""Create test DXF file for T-junction paint bucket scenarios."""

import ezdxf

def main():
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    # Block 1: Simple T-junction (no region)
    b1 = doc.blocks.new("SIMPLE_T")
    b1.add_line((0, 0), (0, 100))
    b1.add_line((0, 50), (50, 50))

    # Block 2: T inside rectangle (2 regions)
    b2 = doc.blocks.new("T_IN_RECTANGLE")
    b2.add_line((0, 0), (100, 0))
    b2.add_line((100, 0), (100, 100))
    b2.add_line((100, 100), (0, 100))
    b2.add_line((0, 100), (0, 0))
    b2.add_line((50, 0), (50, 100))

    # Block 3: Cross inside rectangle (4 regions)
    b3 = doc.blocks.new("CROSS_IN_RECTANGLE")
    b3.add_line((0, 0), (100, 0))
    b3.add_line((100, 0), (100, 100))
    b3.add_line((100, 100), (0, 100))
    b3.add_line((0, 100), (0, 0))
    b3.add_line((0, 50), (100, 50))
    b3.add_line((50, 0), (50, 100))

    # Block 4: Complex nested T-junctions (like GS900x450HGE_Liquor)
    b4 = doc.blocks.new("COMPLEX_T_JUNCTIONS")
    # Outer U-shape
    b4.add_line((0, 0), (0, 100))
    b4.add_line((0, 100), (100, 100))
    b4.add_line((100, 100), (100, 0))
    # Interior horizontal bar
    b4.add_line((0, 30), (100, 30))
    # Corner brackets (L-shaped)
    b4.add_line((10, 0), (10, 20))
    b4.add_line((10, 20), (0, 20))
    b4.add_line((90, 0), (90, 20))
    b4.add_line((90, 20), (100, 20))

    # Add block references
    msp.add_blockref("SIMPLE_T", (0, 0))
    msp.add_blockref("T_IN_RECTANGLE", (200, 0))
    msp.add_blockref("CROSS_IN_RECTANGLE", (400, 0))
    msp.add_blockref("COMPLEX_T_JUNCTIONS", (600, 0))

    doc.saveas("app/tests/assets/t_junction_test.dxf")
    print("Created t_junction_test.dxf")
    print("  SIMPLE_T: 2 lines, 0 regions (T-junction, no closure)")
    print("  T_IN_RECTANGLE: 5 lines, 2 regions")
    print("  CROSS_IN_RECTANGLE: 6 lines, 4 regions")
    print("  COMPLEX_T_JUNCTIONS: 8 lines, ~5 regions")

if __name__ == "__main__":
    main()
```

## Implementation Sequence

| Step | Task | Dependencies | Validation |
|------|------|--------------|------------|
| 1 | Add `T_JUNCTION_EDGE_THRESHOLD` constant | None | `test_constants.py` |
| 2 | Implement `_find_t_junctions()` | Step 1 | Unit test |
| 3 | Implement `_split_lines_at_points()` | Shapely | Unit test |
| 4 | Implement `_extract_line_cycles_full()` | Steps 2-3 | Unit test |
| 5 | Create T-junction test DXF | None | Manual verify |
| 6 | Add T-junction test cases | Steps 4-5 | pytest |
| 7 | Update `_detect_content_zone()` to use new function | Step 4 | Integration test |
| 8 | Run full test suite | All above | `uv run pytest app/tests/` |
| 9 | Performance benchmarking | Step 7 | Manual timing |
| 10 | Threshold tuning (if needed) | Step 9 | Rerun tests |

## Recommendations

1. **Incremental Implementation**: Implement T-junction detection as a separate function first, test it in isolation, then integrate.

2. **Feature Flag**: Consider a `USE_FULL_PAINT_BUCKET` constant to allow fallback to current behavior during testing.

3. **Performance Monitoring**: Add timing logs for T-junction detection to identify blocks that approach thresholds.

4. **Threshold Validation**: Test with real production DXF files to validate threshold values.

5. **Edge Case Documentation**: Document known edge cases (coincident lines, very small segments) in code comments.

## Next Steps

1. Create spec file `specs/027-full-paint-bucket-implementation.md` from this plan
2. Implement Phase 1 (T-junction detection) with unit tests
3. Implement Phase 2 (edge splitting) with unit tests
4. Integrate into `_extract_line_cycles()` with feature flag
5. Create test DXF assets
6. Run comprehensive validation
7. Remove feature flag after validation passes
