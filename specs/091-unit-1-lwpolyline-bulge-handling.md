# Bug: LWPOLYLINE Bulge Values Ignored in Edge Extraction

## Bug Description

LWPOLYLINE bulge values are extracted but completely ignored in `_extract_all_edges()`. All polyline segments are treated as straight lines even when they have bulge values indicating arc segments. This causes curved polyline segments to be represented as chords (straight lines between endpoints), resulting in:

- **Incorrect edge geometry**: Curved segments appear as straight chords
- **Incorrect bounding box calculations**: For curved polylines, the actual arc extent is not captured
- **Missing vertices**: Arc segments have no intermediate vertices for polygon detection
- **Incorrect polygon detection**: Paint-bucket regions formed by curved polylines are detected incorrectly

**Expected behavior**: LWPOLYLINE segments with non-zero bulge values should be flattened into multiple line segments that follow the arc path, similar to how HATCH boundaries with bulge are already handled.

**Actual behavior**: The bulge value is explicitly discarded with `_` placeholder, and only the chord (straight line from start to end) is used.

## Problem Statement

In `_extract_all_edges()` at lines 791-799, the LWPOLYLINE handling code extracts points but ignores the bulge values:

```python
elif entity_type in ("LWPOLYLINE", "POLYLINE"):
    try:
        points = [(float(p[0]), float(p[1])) for p in entity.get_points()]  # Bulge IGNORED
        for i in range(len(points) - 1):
            edges.append(LineString([points[i], points[i + 1]]))
        if hasattr(entity, "closed") and entity.closed and len(points) >= 2:
            edges.append(LineString([points[-1], points[0]]))
    except (AttributeError, IndexError):
        continue
```

The code only extracts x,y coordinates and creates straight LineString edges between consecutive points, completely ignoring any bulge values that indicate arc segments.

Similarly, `_get_block_bounding_box()` at lines 304-314 uses `get_points()` without the bulge format, potentially missing the full arc extent for curved segments.

## Solution Statement

Use `ezdxf.path.from_vertices()` to convert LWPOLYLINE points (with bulge) into a proper path that can be flattened. This function correctly interprets bulge values and creates arc segments that can then be flattened to line segments using the existing `ARC_FLATTENING_SAGITTA` constant.

The fix follows the same pattern already used in `_extract_hatch_boundary_edges()` which correctly handles HATCH boundaries with bulge values via `from_hatch()` and `path.flattening()`.

**Key changes:**
1. Add import for `from_vertices` from `ezdxf.path`
2. Update `_extract_all_edges()` to use `from_vertices()` for LWPOLYLINE with bulge handling
3. Update `_get_block_bounding_box()` LWPOLYLINE handling to account for arc extents when bulge is present

## Steps to Reproduce

1. Create a DXF file with an LWPOLYLINE containing a 90-degree arc bulge segment
2. Extract edges using `_extract_all_edges()` on the block containing this LWPOLYLINE
3. Count the edges and observe their geometry
4. **Expected**: Multiple edges following the arc curvature
5. **Actual**: Single straight edge (chord) between arc endpoints

## Root Cause Analysis

The root cause is that the LWPOLYLINE handling code in `_extract_all_edges()` uses `entity.get_points()` without the `format="xyb"` parameter, and even if it did, the bulge value is not being used. The bulge value (a float between -1 and 1) indicates arc curvature:
- `bulge = 0`: Straight line segment
- `bulge = 1`: Semicircle arc (180 degrees)
- `bulge = tan(angle/4)` for any arc angle

The existing `_extract_hatch_boundary_edges()` function demonstrates the correct approach using `from_hatch()` which automatically converts bulge values to arc paths. The equivalent for LWPOLYLINE is `from_vertices()` which accepts `(x, y, bulge)` tuples.

**Contrast with working code** (lines 714-743):
```python
def _extract_hatch_boundary_edges(entity: Any) -> list[LineString]:
    edges: list[LineString] = []
    try:
        for path in from_hatch(entity):  # Correctly handles bulge
            points = list(path.flattening(distance=ARC_FLATTENING_SAGITTA))
            for i in range(len(points) - 1):
                edges.append(LineString(...))
```

## Relevant Files

Use these files to fix the bug:

- **`app/core/geometry.py`** - Primary implementation file
  - Lines 27-28: Import section - add `from_vertices` to existing `from_hatch` import
  - Lines 304-314: `_get_block_bounding_box()` LWPOLYLINE handling - needs bulge-aware bbox calculation
  - Lines 791-799: `_extract_all_edges()` LWPOLYLINE handling - needs `from_vertices()` + flattening

- **`app/tests/core/test_geometry.py`** - Unit tests for geometry functions
  - Add new `TestLwpolylineBulge` test class for bulge handling validation

- **`app/tests/assets/create_circle_arc_hatch_edges_test.py`** - Reference for test asset creation pattern
  - Shows how to create test DXF files with various geometric entities

### New Files

- **`app/tests/assets/create_lwpolyline_bulge_test.py`** - Script to create test DXF file with LWPOLYLINE bulge segments
- **`app/tests/assets/lwpolyline_bulge_test.dxf`** - Test asset file (generated by script above)

## Step by Step Tasks

### Step 1: Create Test Asset Generator Script

Create `app/tests/assets/create_lwpolyline_bulge_test.py` to generate a test DXF file:

- Create block `LWPOLY_90DEG_ARC` with LWPOLYLINE containing 90-degree arc bulge (bulge=1.0 for semicircle)
- Create block `LWPOLY_STRAIGHT` with LWPOLYLINE using only straight segments (bulge=0)
- Create block `LWPOLY_MIXED` with LWPOLYLINE containing both straight and curved segments
- Create block `LWPOLY_CLOSED_ARC` with closed LWPOLYLINE containing arc segment
- Add block references to modelspace
- Save to `app/tests/assets/lwpolyline_bulge_test.dxf`

The 90-degree arc bulge value is `tan(90/4) = tan(22.5) = 0.41421356` (approximately).

### Step 2: Generate Test Asset File

Run the script to generate the test DXF file:

- Execute: `uv run python app/tests/assets/create_lwpolyline_bulge_test.py`
- Verify file created: `app/tests/assets/lwpolyline_bulge_test.dxf`

### Step 3: Update Import in geometry.py

Update the import statement at line 28 in `app/core/geometry.py`:

- Change: `from ezdxf.path import from_hatch`
- To: `from ezdxf.path import from_hatch, from_vertices`

### Step 4: Update `_extract_all_edges()` LWPOLYLINE Handling

Replace the LWPOLYLINE handling block (lines 791-799) in `app/core/geometry.py`:

- Use `entity.get_points(format="xyb")` to get points with bulge values
- Convert to path using `from_vertices(points, close=entity.closed)`
- Flatten the path using `path.flattening(ARC_FLATTENING_SAGITTA)`
- Create LineString edges from flattened vertices
- Handle closed polylines correctly (path closing is handled by `from_vertices` with `close=True`)

The new implementation should:
```python
elif entity_type in ("LWPOLYLINE", "POLYLINE"):
    try:
        # Get points with bulge values: format="xyb" returns (x, y, bulge) tuples
        points_with_bulge = list(entity.get_points(format="xyb"))  # type: ignore[attr-defined]
        if len(points_with_bulge) < 2:
            continue
        # from_vertices() correctly interprets bulge values and creates arc segments
        is_closed = hasattr(entity, "closed") and entity.closed
        path = from_vertices(points_with_bulge, close=is_closed)
        # Flatten path to line segments (handles arcs automatically)
        vertices = list(path.flattening(ARC_FLATTENING_SAGITTA))
        for i in range(len(vertices) - 1):
            edges.append(
                LineString([(vertices[i].x, vertices[i].y), (vertices[i + 1].x, vertices[i + 1].y)])
            )
    except (AttributeError, IndexError, TypeError):
        continue
```

### Step 5: Update `_get_block_bounding_box()` LWPOLYLINE Handling

Update the LWPOLYLINE handling block (lines 304-314) in `app/core/geometry.py`:

- Use `from_vertices()` with bulge format to create path
- Flatten the path to get all vertices including arc approximation points
- Update bounding box from all flattened vertices

The new implementation should:
```python
elif entity_type in ("LWPOLYLINE", "POLYLINE"):
    try:
        # Get points with bulge values for accurate bbox of curved segments
        points_with_bulge = list(entity.get_points(format="xyb"))  # type: ignore[attr-defined]
        if len(points_with_bulge) < 2:
            continue
        is_closed = hasattr(entity, "closed") and entity.closed
        path = from_vertices(points_with_bulge, close=is_closed)
        # Flatten to capture arc extents
        for vertex in path.flattening(ARC_FLATTENING_SAGITTA):
            min_x = min(min_x, vertex.x)
            max_x = max(max_x, vertex.x)
            min_y = min(min_y, vertex.y)
            max_y = max(max_y, vertex.y)
            has_geometry = True
    except (AttributeError, IndexError, TypeError):
        continue
```

### Step 6: Add Unit Tests for LWPOLYLINE Bulge Handling

Add new test class `TestLwpolylineBulge` to `app/tests/core/test_geometry.py`:

- `test_extract_edges_straight_lwpolyline` - Verify straight LWPOLYLINE extracts expected edge count
- `test_extract_edges_arc_lwpolyline` - Verify LWPOLYLINE with 90-degree arc extracts multiple edges (not just 1 chord)
- `test_extract_edges_mixed_lwpolyline` - Verify mixed straight/curved segments handled correctly
- `test_bbox_straight_lwpolyline` - Verify bounding box for straight LWPOLYLINE
- `test_bbox_arc_lwpolyline` - Verify bounding box includes full arc extent (not just chord endpoints)
- `test_closed_lwpolyline_with_bulge` - Verify closed polylines with bulge are handled correctly

Add required import: `from core.geometry import _extract_all_edges, _get_block_bounding_box`

### Step 7: Run Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

- `uv run python app/tests/assets/create_lwpolyline_bulge_test.py` - Generate test asset file
- `uv run pytest app/tests/core/test_geometry.py::TestLwpolylineBulge -v` - Run new LWPOLYLINE bulge unit tests
- `uv run pytest app/tests/core/test_geometry.py::TestBoundingBox::test_bounding_box_with_polyline -v` - Run existing polyline bbox test
- `uv run pytest app/tests/core/test_geometry.py -v` - Run all geometry tests
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests for integration coverage
- `uv run pytest app/tests/ -v` - Run complete test suite to verify zero regressions
- `uv run mypy app/` - Run type checking to ensure no type errors

## Notes

1. **ezdxf `from_vertices()` function**: Available since ezdxf 0.17. Accepts iterable of `(x, y)` or `(x, y, bulge)` tuples and creates a Path object. The `close` parameter controls whether the path should be closed.

2. **Bulge formula**: `bulge = tan(included_angle / 4)`. Common values:
   - 0 = straight line
   - 0.41421356 = 90-degree arc
   - 1.0 = semicircle (180 degrees)
   - -1.0 = semicircle in opposite direction

3. **Flattening sagitta**: Using the existing `ARC_FLATTENING_SAGITTA` constant (0.1) ensures consistent arc approximation quality across all curved entity types.

4. **Pattern consistency**: This fix aligns LWPOLYLINE handling with the existing HATCH boundary handling pattern at lines 714-743, which already correctly uses `from_hatch()` + `flattening()`.

5. **Performance consideration**: Flattening adds computational cost proportional to arc size and sagitta precision. For most CAD drawings, this is negligible. The existing `_estimate_edge_count()` function may need updating to account for potential additional edges from bulge segments.

6. **Reference document**: Detailed analysis in `ai_output/087-geometry-handling-gap-analysis-report.md` Section 1.1.

7. **Prior unit learnings**: ARC bounding box was recently implemented using `_get_arc_bounding_box()` helper. Similar pattern of using accurate geometry calculations instead of simplified approximations applies here.
