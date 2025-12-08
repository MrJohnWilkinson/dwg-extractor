# Polygon Count Column Implementation Tasks

## Executive Summary

This report consolidates the conclusions from three polygon detection analysis documents (016, 017, 018) into a prioritized implementation sequence. The goal is to replace the current DFS-based `_extract_line_cycles()` with a planar face detection algorithm that correctly handles T-junctions and crossing intersections, then expose the polygon count in the Block Geometry Analysis Excel sheet.

## Table Summary

| Task # | Task Description | File(s) | Priority | Dependencies |
|--------|------------------|---------|----------|--------------|
| 1 | Add `EXCEL_COLUMN_BLOCK_POLYGON_COUNT` constant | `constants.py` | High | None |
| 2 | Add `polygon_count` field to `ContentZoneData` | `types.py` | High | Task 1 |
| 3 | Implement `_point_on_segment_interior()` for T-junction detection | `geometry.py` | High | None |
| 4 | Implement `_line_segment_intersection()` for crossing detection | `geometry.py` | High | None |
| 5 | Implement `_find_all_split_points()` combining T-junctions + crossings | `geometry.py` | High | Tasks 3, 4 |
| 6 | Implement `_split_edges_at_points()` for edge subdivision | `geometry.py` | High | Task 5 |
| 7 | Implement `_build_angular_sorted_adjacency()` for DCEL structure | `geometry.py` | High | Task 6 |
| 8 | Implement `_trace_planar_faces()` using leftmost turn rule | `geometry.py` | High | Task 7 |
| 9 | Replace `_extract_line_cycles()` with `_detect_planar_faces()` | `geometry.py` | High | Task 8 |
| 10 | Update `_detect_content_zone()` to return polygon count | `geometry.py` | High | Task 9 |
| 11 | Update `_create_block_geometry_analysis_sheet()` for polygon count | `excel_writer.py` | Medium | Tasks 1, 10 |
| 12 | Update `_format_block_geometry_analysis_sheet()` for new column | `excel_formatting.py` | Medium | Task 11 |
| 13 | Add unit tests for T-junction detection | `test_geometry.py` | Medium | Task 3 |
| 14 | Add unit tests for crossing intersection detection | `test_geometry.py` | Medium | Task 4 |
| 15 | Add unit tests with sample blocks (AP #5-4, Bread gondola) | `test_geometry.py` | Medium | Task 9 |
| 16 | Update existing content zone tests for polygon count | `test_content_zone.py` | Low | Task 10 |

## Relevant Files

- `app/core/geometry.py` - Contains current `_extract_line_cycles()` that needs replacement (lines 547-673)
- `app/core/constants.py` - Column name constants; add `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`
- `app/core/types.py` - TypedDict definitions; add `polygon_count` to `ContentZoneData`
- `app/core/excel_writer.py` - Excel generation; add polygon count column to geometry sheet
- `app/core/excel_formatting.py` - Column widths and formatting for geometry sheet
- `app/tests/core/test_geometry.py` - Unit tests for geometry functions
- `app/tests/core/test_content_zone.py` - Integration tests for content zone detection
- `app/tests/assets/samples/sample-blocks.dxf` - Test DXF with 5 validated blocks
- `ai_docs/001-naming-convention-guide.md` - Naming conventions for new constants/functions

## Algorithm Implementation Details

### Current Algorithm Limitations (from Document 016)

The existing `_extract_line_cycles()` uses DFS cycle detection which:
1. Misses T-junctions (endpoint touching another edge's interior)
2. Misses crossing intersections (two edges crossing in their interiors)
3. Limited to path length of 20 vertices
4. Does not implement planar graph face traversal

### Required Algorithm: Planar Face Detection

```
function detect_planar_faces(block):
    edges = extract_edges(block)                    # LINE + LWPOLYLINE
    t_junctions = find_t_junctions(edges)           # Endpoint on edge interior
    crossings = find_crossing_intersections(edges)  # Edge interior crossings
    split_points = t_junctions + crossings

    split_edges = split_edges_at_points(edges, split_points)
    graph = build_angular_sorted_adjacency(split_edges)

    faces = trace_all_faces_ccw(graph)              # Leftmost turn rule
    interior_faces = filter_exterior_face(faces)    # Remove negative signed area

    return len(interior_faces), interior_faces
```

### Critical Finding from Document 017

The AP #5-4 block demonstrated that **both T-junction AND crossing intersection detection are required**:

| Block | T-Junctions Only | T-Junctions + Crossings | Expected |
|-------|------------------|-------------------------|----------|
| AP #5-4 | 3 polygons | 8 polygons | 8 |
| Bread gondola | 13 | 13 | 13 |
| Bread gondola end | 4 | 4 | 4 |
| GS900x450HGE_Liquor | 5 | 5 | 5 |
| Gcase(w1800) | 2 | 2 | 2 |

## Naming Convention Compliance

Following `ai_docs/001-naming-convention-guide.md`:

### Constants (SCREAMING_SNAKE_CASE)
```python
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: str = "block_polygon_count"
```

### Functions (snake_case with verb prefixes)
```python
def _point_on_segment_interior(point, segment_start, segment_end, tolerance=0.02):
def _find_line_segment_intersection(segment_a, segment_b):
def _find_all_split_points(edges):
def _split_edges_at_points(edges, split_points):
def _build_angular_sorted_adjacency(edges):
def _trace_planar_faces(adjacency_graph):
def _detect_planar_faces(block_def, abort_event=None):
```

### Type Annotations
```python
# ContentZoneData TypedDict update
class ContentZoneData(TypedDict):
    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
    polygon_count: int  # NEW: Number of detected interior faces
```

## Implementation Sequence

### Phase 1: Constants and Types (Tasks 1-2)

Add the new constant following the existing naming pattern:

```python
# constants.py - after EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: str = "block_polygon_count"
```

Update `ContentZoneData` in `types.py` to include polygon count.

### Phase 2: Core Algorithm Functions (Tasks 3-8)

Implement helper functions in `geometry.py`:

1. **T-junction detection** - Check if a point lies on a segment's interior:
   ```python
   def _point_on_segment_interior(point, p1, p2, tolerance=0.02):
       d1 = _distance(point, p1)
       d2 = _distance(point, p2)
       d12 = _distance(p1, p2)
       return abs(d1 + d2 - d12) < tolerance and d1 > tolerance and d2 > tolerance
   ```

2. **Crossing intersection** - Find where two line segments cross (not at endpoints):
   ```python
   def _find_line_segment_intersection(seg_a, seg_b):
       # Returns intersection point if segments cross in their interiors
       # Returns None if parallel, collinear, or only touch at endpoints
   ```

3. **Combined split point detection** - Merge T-junctions and crossings:
   ```python
   def _find_all_split_points(edges):
       split_points = set()
       # Add T-junctions: endpoints touching other edge interiors
       # Add crossings: edge pairs that cross in their interiors
       return split_points
   ```

4. **Edge splitting** - Subdivide edges at split points
5. **Angular-sorted adjacency** - Build DCEL-like structure for face traversal
6. **Face traversal** - Use leftmost turn rule to trace minimal faces

### Phase 3: Integration (Tasks 9-10)

Replace `_extract_line_cycles()` with `_detect_planar_faces()` and update `_detect_content_zone()` to return the polygon count along with trim values.

### Phase 4: Excel Output (Tasks 11-12)

Add polygon count column to Block Geometry Analysis sheet after `content_zone_detected`:

```python
# excel_writer.py - in _create_block_geometry_analysis_sheet()
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: polygon_count,
```

### Phase 5: Testing (Tasks 13-16)

Add unit tests using the 5 sample blocks as ground truth:

| Block Name | Expected Polygon Count |
|------------|------------------------|
| AP #5-4 | 8 |
| Bread gondola | 13 |
| Bread gondola end | 4 |
| GS900x450HGE_Liquor | 5 |
| Gcase(w1800) | 2 |

## Alternative Approach: Shapely Library

If rapid implementation is preferred, consider using Shapely's `polygonize()`:

```python
from shapely.ops import polygonize
from shapely.geometry import LineString

def _detect_planar_faces_shapely(block_def):
    lines = []
    for entity in block_def:
        if entity.dxftype() == "LINE":
            lines.append(LineString([(entity.dxf.start.x, entity.dxf.start.y),
                                      (entity.dxf.end.x, entity.dxf.end.y)]))
        elif entity.dxftype() == "LWPOLYLINE" and entity.closed:
            points = [(p[0], p[1]) for p in entity.get_points()]
            points.append(points[0])  # Close the ring
            lines.append(LineString(points))

    polygons = list(polygonize(lines))
    return len(polygons), polygons
```

**Trade-offs:**
- Pros: Production-ready, handles edge cases, well-tested
- Cons: External dependency, less control over algorithm details

## Recommendations

1. **Start with custom implementation** for full control and no new dependencies
2. **Implement T-junction detection first** - covers most blocks correctly
3. **Add crossing detection second** - required for grid-layout blocks like AP #5-4
4. **Validate against all 5 sample blocks** before considering complete
5. **Consider Shapely as fallback** if edge cases prove problematic

## Next Steps

1. Create feature branch: `feature/polygon-count-column`
2. Implement Tasks 1-2 (constants and types)
3. Implement Tasks 3-6 (algorithm helper functions)
4. Implement Tasks 7-9 (face detection and integration)
5. Implement Tasks 10-12 (Excel output)
6. Add tests and validate against sample blocks
7. Performance benchmark on production DXF files with 100+ LINE segments
