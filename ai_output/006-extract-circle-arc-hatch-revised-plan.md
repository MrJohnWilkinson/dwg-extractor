# Implementation Plan: Extract CIRCLE, ARC, and HATCH Boundary Edges

## Executive Summary

This plan extends `_extract_all_edges()` in `geometry.py` to extract edges from CIRCLE, ARC, and HATCH boundary entities using ezdxf's built-in methods. The approach uses `entity.flattening(sagitta)` for adaptive arc discretization and `ezdxf.path.from_hatch()` for HATCH boundaries, which correctly handles bulge values in PolylinePath segments.

## Table Summary

| Entity Type | Current State | Target State | Implementation Approach | Complexity |
|-------------|---------------|--------------|------------------------|------------|
| LINE | Extracted | Extracted | No change | N/A |
| LWPOLYLINE/POLYLINE | Extracted | Extracted | No change | N/A |
| CIRCLE | Not extracted | Extracted | `entity.flattening(sagitta)` | Low |
| ARC | Not extracted | Extracted | `entity.flattening(sagitta)` | Low |
| HATCH (PolylinePath) | Not extracted | Extracted | `from_hatch()` + `path.flattening()` | Low |
| HATCH (EdgePath - LineEdge) | Not extracted | Extracted | `from_hatch()` + `path.flattening()` | Low |
| HATCH (EdgePath - ArcEdge) | Not extracted | Extracted | `from_hatch()` + `path.flattening()` | Low |

## Relevant Files

- **app/core/geometry.py:375-410** - `_extract_all_edges()` function to modify
- **app/core/constants.py** - Add `ARC_FLATTENING_SAGITTA` constant
- **app/tests/assets/hatch_test.dxf** - Existing HATCH test fixture
- **app/tests/assets/circles_arcs_points.dxf** - Existing CIRCLE/ARC test fixture
- **ai_docs/ezdxf-geometry-reference.md** - ezdxf API reference for flattening methods
- **ai_docs/shapely-geometry-reference.md** - Shapely polygonize patterns
- **ai_docs/logical-rules-for-polygons.md** - Paint-bucket region detection rules

## In-Scope

1. **CIRCLE entity extraction** - Use `entity.flattening(sagitta)` for adaptive discretization
2. **ARC entity extraction** - Use `entity.flattening(sagitta)` for adaptive discretization
3. **HATCH PolylinePath extraction** - Use `from_hatch()` to handle bulge values correctly
4. **HATCH EdgePath - LineEdge** - Handled automatically by `from_hatch()`
5. **HATCH EdgePath - ArcEdge** - Handled automatically by `from_hatch()` + `path.flattening()`
6. **Sagitta-based constant** - `ARC_FLATTENING_SAGITTA = 0.1` instead of fixed segment count
7. **Unit tests** - Tests for each new entity type extraction including bulge scenarios

## Out-of-Scope

1. **ELLIPSE entities** - Not commonly used in target drawings
2. **SPLINE entities** - Complex geometry, rare in target drawings
3. **HATCH EdgePath - EllipseEdge** - Low priority, complex geometry
4. **HATCH EdgePath - SplineEdge** - Low priority, complex geometry
5. **3D entities** - Focus on 2D extraction only
6. **POINT entities** - Points have no edges (zero-dimensional)

## Implementation Steps

### Step 1: Add Sagitta Constant

**File:** `app/core/constants.py`

Add a sagitta constant for adaptive arc flattening:

```python
ARC_FLATTENING_SAGITTA: float = 0.1
"""Maximum distance from arc center to chord center for flattening.
Smaller values = more segments = higher precision. 0.1 is appropriate for
typical CAD drawings with units in mm or inches."""
```

**Rationale:** Sagitta-based flattening adapts to arc size - large arcs get more segments, small arcs fewer. This produces consistent visual quality regardless of scale, unlike a fixed segment count.

---

### Step 2: Add CIRCLE Extraction Helper

**File:** `app/core/geometry.py`

Add helper function using ezdxf's built-in `flattening()`:

```python
from .constants import ARC_FLATTENING_SAGITTA

def _extract_circle_edges(entity: Any) -> list[LineString]:
    """Extract edges from CIRCLE entity using adaptive flattening."""
    points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
    edges: list[LineString] = []
    for i in range(len(points) - 1):
        edges.append(LineString([
            (points[i].x, points[i].y),
            (points[i + 1].x, points[i + 1].y)
        ]))
    return edges
```

**Note:** `flattening()` returns points in WCS. Start vertex equals end vertex for CIRCLE (closed polygon).

---

### Step 3: Add ARC Extraction Helper

**File:** `app/core/geometry.py`

Add helper function for ARC entities:

```python
def _extract_arc_edges(entity: Any) -> list[LineString]:
    """Extract edges from ARC entity using adaptive flattening."""
    points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
    edges: list[LineString] = []
    for i in range(len(points) - 1):
        edges.append(LineString([
            (points[i].x, points[i].y),
            (points[i + 1].x, points[i + 1].y)
        ]))
    return edges
```

---

### Step 4: Add HATCH Boundary Extraction Helper

**File:** `app/core/geometry.py`

Add helper function using `ezdxf.path.from_hatch()`:

```python
from ezdxf.path import from_hatch

def _extract_hatch_boundary_edges(entity: Any) -> list[LineString]:
    """Extract edges from HATCH boundary paths.

    Uses from_hatch() to correctly handle:
    - PolylinePath with bulge values (curved segments)
    - EdgePath with LineEdge, ArcEdge, etc.
    """
    edges: list[LineString] = []
    try:
        for path in from_hatch(entity):
            points = list(path.flattening(distance=ARC_FLATTENING_SAGITTA))
            for i in range(len(points) - 1):
                edges.append(LineString([
                    (points[i].x, points[i].y),
                    (points[i + 1].x, points[i + 1].y)
                ]))
    except (AttributeError, TypeError, ValueError):
        pass
    return edges
```

**Critical:** `from_hatch()` automatically handles bulge values in PolylinePath. Non-zero bulge means a curved segment between vertices.

---

### Step 5: Update `_extract_all_edges()` Function

**File:** `app/core/geometry.py:375-410`

Add CIRCLE, ARC, and HATCH handling to the existing function:

```python
def _extract_all_edges(block_def: BlockLayout) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Extracts edges from:
    - LINE entities (start to end as single edge)
    - LWPOLYLINE/POLYLINE entities (all vertices as edges, closing edge if closed)
    - CIRCLE entities (adaptive flattening to line segments)
    - ARC entities (adaptive flattening to line segments)
    - HATCH boundary paths (PolylinePath and EdgePath variants)

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of LineString objects representing all edges in the block.
    """
    edges: list[LineString] = []

    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                for i in range(len(points) - 1):
                    edges.append(LineString([points[i], points[i + 1]]))
                if hasattr(entity, "closed") and entity.closed and len(points) >= 2:
                    edges.append(LineString([points[-1], points[0]]))
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            edges.extend(_extract_circle_edges(entity))

        elif entity_type == "ARC":
            edges.extend(_extract_arc_edges(entity))

        elif entity_type == "HATCH":
            edges.extend(_extract_hatch_boundary_edges(entity))

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges
```

---

### Step 6: Add Import Statement

**File:** `app/core/geometry.py` (top of file)

Add the required import:

```python
from ezdxf.path import from_hatch
```

---

### Step 7: Create Test DXF Generator Script

**File:** `app/tests/assets/create_circle_arc_hatch_edges_test.py`

Create test fixture with:
- Block with CIRCLE entities forming closed regions
- Block with ARC entities forming closed regions
- Block with HATCH PolylinePath (straight segments only)
- Block with HATCH PolylinePath with bulge values (curved segments)
- Block with HATCH EdgePath containing LineEdge and ArcEdge
- Block mixing all entity types

---

### Step 8: Add Unit Tests for CIRCLE Extraction

**File:** `app/tests/core/test_geometry_circle_arc_hatch.py`

Test cases:
- `_extract_circle_edges()` returns correct edge count (sagitta-dependent)
- Circle edges form closed polygon via `polygonize()`
- Content zone detection works with CIRCLE-only blocks
- Small vs large circles produce different segment counts (adaptive)

---

### Step 9: Add Unit Tests for ARC Extraction

**File:** `app/tests/core/test_geometry_circle_arc_hatch.py`

Test cases:
- `_extract_arc_edges()` returns edges for arc segment
- Multiple arcs forming closed shape detected as polygon
- Arc handles angles > 360 and negative angles correctly
- 180-degree arc produces appropriate segment count

---

### Step 10: Add Unit Tests for HATCH Boundary Extraction

**File:** `app/tests/core/test_geometry_circle_arc_hatch.py`

Test cases:
- PolylinePath with straight segments extracted correctly
- PolylinePath with non-zero bulge values produces curved edges
- EdgePath LineEdge extraction
- EdgePath ArcEdge discretization via `from_hatch()`
- Mixed EdgePath types in single HATCH
- HATCH with multiple boundary paths

---

### Step 11: Integration Tests

**File:** `app/tests/core/test_geometry_circle_arc_hatch.py`

Test cases:
- Content zone detection with CIRCLE boundaries
- Content zone detection with mixed LINE + ARC boundaries
- Content zone detection with HATCH boundary defining outer shape
- Paint-bucket algorithm produces correct regions with new entity types
- Real-world block example (SPAR Gulv 900x600 H1860 or similar)

---

### Step 12: Update Existing Tests

**File:** `app/tests/core/test_content_zone.py`

Verify existing tests still pass after changes. Add regression tests if needed.

---

## Recommendations

1. **Test with real DXF files** - Use blocks like "SPAR Gulv 900x600 H1860" that have HATCH boundaries
2. **Log entity extraction** - Add debug logging for new entity types to aid troubleshooting
3. **Consider `make_path()` for future** - `ezdxf.path.make_path()` provides unified handling for LINE, CIRCLE, ARC, ELLIPSE, SPLINE, LWPOLYLINE - could simplify the code further if ELLIPSE/SPLINE support is needed later

## Next Steps

1. Implement Steps 1-2 (sagitta constant and CIRCLE helper)
2. Implement Steps 3-4 (ARC and HATCH helpers)
3. Run existing tests to verify no regression
4. Implement Step 5-6 (update `_extract_all_edges()`)
5. Create test fixtures (Step 7)
6. Add unit tests (Steps 8-11)
7. Run full test suite with coverage report

## Sources

- [Arc - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/arc.html)
- [Circle - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/circle.html)
- [Path - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/path.html)
- [Hatch - ezdxf documentation](https://ezdxf.readthedocs.io/en/stable/dxfentities/hatch.html)
- [Shapely 2.0 documentation](https://shapely.readthedocs.io/en/stable/)
- ai_docs/ezdxf-geometry-reference.md
- ai_docs/shapely-geometry-reference.md
- ai_docs/logical-rules-for-polygons.md
