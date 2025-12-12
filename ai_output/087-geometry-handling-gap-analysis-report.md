# Geometry Handling Gap Analysis Report

**Generated:** 2025-12-12
**Scope:** Investigate current handling of specific geometry scenarios in DXF Block Extractor

---

## Executive Summary

This report examines how the DXF Block Extractor currently handles six priority geometry scenarios. Analysis reveals that **most scenarios are NOT properly handled**, with significant gaps in curved geometry support and nested block expansion.

| Priority | Scenario | Status | Impact |
|----------|----------|--------|--------|
| 1 (High) | LWPOLYLINE bulge handling | **NOT HANDLED** | Curved polyline segments treated as straight lines |
| 1 (High) | Nested INSERT geometry | **NOT HANDLED** | Nested blocks excluded from bounding box |
| 2 (Medium) | ELLIPSE support | **NOT HANDLED** | Entity type completely ignored |
| 2 (Medium) | SPLINE support | **NOT HANDLED** | Entity type completely ignored |
| 2 (Medium) | ARC bounding box fix | **PARTIALLY** | Uses full circle approximation (plan exists: 086) |
| 3 (Low) | Edge count estimation | **NOT HANDLED** | Uses fixed values instead of formula |

---

## Priority 1: High Impact Issues

### 1.1 LWPOLYLINE Bulge Handling

**Current Status: NOT HANDLED**

**Location:** `app/core/geometry.py` lines 703-709

**Current Implementation:**
```python
elif entity.dxftype() == "LWPOLYLINE":
    with_points = entity.get_points(format="xyb")
    for i in range(len(with_points) - 1):
        x1, y1, _ = with_points[i]  # Bulge value DISCARDED
        x2, y2, _ = with_points[i + 1]
        edges.append(((x1, y1), (x2, y2)))
```

**Problem:** The bulge value (third element in tuple) is extracted but completely ignored. All polyline segments are treated as straight lines, causing:
- Curved segments to be represented as chords
- Incorrect bounding box calculations for curved polylines
- Missing vertices for arc segments in polygon detection

**Evidence:** The code explicitly discards bulge with `_` placeholder.

**Contrast with HATCH Handling:**
In `_extract_hatch_boundary_edges()` (lines 626-655), the code correctly uses `ezdxf.path.from_hatch()` which automatically handles bulge values:
```python
paths = ezdxf.path.from_hatch(entity)
for path in paths:
    vertices = list(path.flattening(sagitta))
```

**Best Practice Solution:**
Use `ezdxf.path.from_vertices()` to convert LWPOLYLINE with bulge to a proper path:

```python
from ezdxf.path import from_vertices

elif entity.dxftype() == "LWPOLYLINE":
    # from_vertices() handles bulge values and creates arc segments
    path = from_vertices(entity.get_points(format="xyb"), close=entity.closed)
    vertices = list(path.flattening(sagitta))
    for i in range(len(vertices) - 1):
        edges.append((vertices[i], vertices[i + 1]))
```

**References:**
- ezdxf docs: `from_vertices()` accepts `(x, y, bulge)` tuples and creates proper arc paths
- Already used pattern: `from_hatch()` in same file

---

### 1.2 Nested INSERT Geometry Expansion

**Current Status: NOT HANDLED**

**Location:**
- `app/core/geometry.py` `_get_block_bounding_box()` lines 179-266
- `app/core/extractor.py` nested block tracking lines ~1197

**Current Implementation:**
```python
# In _get_block_bounding_box() - INSERT entities are NOT processed
# Only direct entities: LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, POINT
```

In `extractor.py`, nested blocks are tracked for reporting purposes:
```python
nested_block_parents: dict[str, list[str]] = {}
# Tracks parent-child relationships but does NOT expand geometry
```

**Problem:** When block A contains an INSERT reference to block B:
- Block A's bounding box only includes block A's direct entities
- Block B's geometry is NOT recursively included
- Result: Undersized bounding boxes and incorrect content zone detection

**Best Practice Solution:**
Recursively expand nested INSERT geometry with transformation:

```python
def _get_block_bounding_box(
    block: BlockLayout,
    doc: Drawing,
    processed_blocks: set[str] | None = None,  # Prevent infinite recursion
) -> tuple[float, float, float, float] | None:
    if processed_blocks is None:
        processed_blocks = set()

    block_name = block.name
    if block_name in processed_blocks:
        return None  # Circular reference protection
    processed_blocks.add(block_name)

    all_points: list[tuple[float, float]] = []

    for entity in block:
        if entity.dxftype() == "INSERT":
            # Get nested block definition
            nested_block_name = entity.dxf.name
            if nested_block_name in doc.blocks:
                nested_block = doc.blocks[nested_block_name]
                nested_bbox = _get_block_bounding_box(
                    nested_block, doc, processed_blocks.copy()
                )
                if nested_bbox:
                    # Apply INSERT transformation (scale, rotation, position)
                    transformed_points = _transform_bbox_points(
                        nested_bbox, entity
                    )
                    all_points.extend(transformed_points)
        # ... existing entity handling ...
```

**Transformation Helper:**
```python
def _transform_bbox_points(
    bbox: tuple[float, float, float, float],
    insert: Insert,
) -> list[tuple[float, float]]:
    """Transform nested block bbox corners by INSERT properties."""
    min_x, min_y, max_x, max_y = bbox
    corners = [
        (min_x, min_y), (max_x, min_y),
        (max_x, max_y), (min_x, max_y)
    ]

    # Get INSERT transformation
    insert_point = (insert.dxf.insert.x, insert.dxf.insert.y)
    scale_x = insert.dxf.xscale
    scale_y = insert.dxf.yscale
    rotation_rad = math.radians(insert.dxf.rotation)

    transformed = []
    for x, y in corners:
        # Apply scale
        x *= scale_x
        y *= scale_y
        # Apply rotation
        cos_r, sin_r = math.cos(rotation_rad), math.sin(rotation_rad)
        x_rot = x * cos_r - y * sin_r
        y_rot = x * sin_r + y * cos_r
        # Apply translation
        transformed.append((x_rot + insert_point[0], y_rot + insert_point[1]))

    return transformed
```

---

## Priority 2: Medium Impact Issues

### 2.1 ELLIPSE Support

**Current Status: NOT HANDLED**

**Evidence:**
```bash
# Grep search found ELLIPSE in sample DXF files but NOT in code handlers
# No "ELLIPSE" string in geometry.py entity type checks
```

**Problem:** ELLIPSE entities are completely ignored in:
- `_get_block_bounding_box()` - not in entity type list
- `_extract_all_edges()` - not in entity type list
- `_estimate_edge_count()` - not in entity type list

**Best Practice Solution:**
ELLIPSE entities support the same `flattening()` method as other curves:

```python
elif entity.dxftype() == "ELLIPSE":
    vertices = list(entity.flattening(sagitta))
    # Add to bounding box
    for x, y, *_ in vertices:
        all_points.append((x, y))

    # For edge extraction
    for i in range(len(vertices) - 1):
        edges.append((vertices[i][:2], vertices[i + 1][:2]))
```

**Edge Count Estimation:**
```python
# Approximate based on ellipse circumference and sagitta
# Ramanujan approximation for ellipse perimeter
a = entity.dxf.major_axis.magnitude
b = entity.minor_axis.magnitude  # Calculated property
h = ((a - b) ** 2) / ((a + b) ** 2)
perimeter = math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
estimated_edges = int(perimeter / (2 * math.sqrt(2 * radius * sagitta)))
```

---

### 2.2 SPLINE Support

**Current Status: NOT HANDLED**

**Evidence:**
```bash
# Grep search found SPLINE in sample DXF files but NOT in code handlers
# No "SPLINE" string in geometry.py entity type checks
```

**Problem:** SPLINE entities are completely ignored in all geometry functions.

**Best Practice Solution:**
SPLINE entities also support `flattening()`:

```python
elif entity.dxftype() == "SPLINE":
    try:
        vertices = list(entity.flattening(sagitta))
        # Add to bounding box
        for x, y, *_ in vertices:
            all_points.append((x, y))

        # For edge extraction
        for i in range(len(vertices) - 1):
            edges.append((vertices[i][:2], vertices[i + 1][:2]))
    except Exception:
        # SPLINE flattening can fail for degenerate splines
        # Fall back to control points
        for point in entity.control_points:
            all_points.append((point.x, point.y))
```

**Note:** SPLINE flattening is more computationally expensive than other curve types. Consider:
- Adding a complexity check before flattening
- Using control point bbox as fast approximation for early-exit checks

---

### 2.3 ARC Bounding Box Fix

**Current Status: PARTIALLY HANDLED - Plan Exists**

**Location:** `app/core/geometry.py` lines 242-250

**Current Implementation:**
```python
elif entity.dxftype() == "ARC":
    center = entity.dxf.center
    radius = entity.dxf.radius
    # SIMPLIFIED: Uses full circle extents, not actual angular extent
    all_points.extend([
        (center.x - radius, center.y - radius),
        (center.x + radius, center.y + radius),
    ])
```

**Problem:** A 10-degree arc reports the same bounding box as a full circle.

**Existing Plan:** See `ai_output/086-arc-bbox-implementation-plan-v2.md` for detailed implementation.

**Correct Implementation:**
```python
elif entity.dxftype() == "ARC":
    # Use flattening to get accurate arc points
    vertices = list(entity.flattening(sagitta))
    for x, y, *_ in vertices:
        all_points.append((x, y))
```

---

## Priority 3: Low Impact Issues

### 3.1 Edge Count Estimation Formula

**Current Status: NOT HANDLED**

**Location:** `app/core/geometry.py` lines 499-546

**Current Implementation:**
```python
elif entity.dxftype() == "CIRCLE":
    count += 36  # Fixed value
elif entity.dxftype() == "ARC":
    count += 18  # Fixed value
elif entity.dxftype() == "HATCH":
    count += 50  # Fixed value
```

**Problem:** Fixed estimates don't account for:
- Entity size (larger circles need more segments)
- Configured sagitta value (higher precision = more segments)
- Actual arc angular extent

**Best Practice Solution:**
Use sagitta-based formula for arc segment count:

```python
def _estimate_arc_segments(radius: float, angle_rad: float, sagitta: float) -> int:
    """
    Calculate segments needed to approximate arc within sagitta tolerance.

    Formula derived from: sagitta = radius * (1 - cos(theta/2))
    where theta is the angle per segment.
    Solving for segments: n = angle / (2 * arccos(1 - sagitta/radius))
    """
    if radius <= 0 or sagitta <= 0:
        return 1

    ratio = sagitta / radius
    if ratio >= 1:
        return 1  # Sagitta larger than radius - use minimum

    # Angle per segment that achieves target sagitta
    theta_per_segment = 2 * math.acos(1 - ratio)

    # Number of segments for the arc
    segments = int(math.ceil(angle_rad / theta_per_segment))
    return max(1, segments)

# Usage in _estimate_edge_count():
elif entity.dxftype() == "CIRCLE":
    radius = entity.dxf.radius
    count += _estimate_arc_segments(radius, 2 * math.pi, sagitta)

elif entity.dxftype() == "ARC":
    radius = entity.dxf.radius
    start = math.radians(entity.dxf.start_angle)
    end = math.radians(entity.dxf.end_angle)
    angle = (end - start) % (2 * math.pi)
    if angle == 0:
        angle = 2 * math.pi  # Full circle case
    count += _estimate_arc_segments(radius, angle, sagitta)
```

---

## Implementation Plan

### Phase 1: Critical Fixes (Priority 1)

**1.1 LWPOLYLINE Bulge Handling**
- Modify `_extract_all_edges()` in geometry.py
- Use `ezdxf.path.from_vertices()` for bulge conversion
- Add unit tests with curved polyline fixtures
- Estimated changes: ~20 lines in geometry.py

**1.2 Nested INSERT Expansion**
- Add `_transform_bbox_points()` helper function
- Modify `_get_block_bounding_box()` to recursively process INSERTs
- Add circular reference protection
- Add unit tests with nested block fixtures
- Estimated changes: ~60 lines in geometry.py

### Phase 2: Entity Support (Priority 2)

**2.1 ELLIPSE Support**
- Add ELLIPSE handler to `_get_block_bounding_box()`
- Add ELLIPSE handler to `_extract_all_edges()`
- Add ELLIPSE handler to `_estimate_edge_count()`
- Add unit tests
- Estimated changes: ~30 lines

**2.2 SPLINE Support**
- Add SPLINE handler to `_get_block_bounding_box()`
- Add SPLINE handler to `_extract_all_edges()`
- Add SPLINE handler to `_estimate_edge_count()`
- Add error handling for degenerate splines
- Add unit tests
- Estimated changes: ~40 lines

**2.3 ARC Bounding Box**
- Follow existing plan in `086-arc-bbox-implementation-plan-v2.md`
- Replace full-circle approximation with flattening-based bbox
- Estimated changes: ~10 lines

### Phase 3: Optimization (Priority 3)

**3.1 Edge Count Estimation**
- Add `_estimate_arc_segments()` helper function
- Replace fixed values with formula-based estimates
- Apply to CIRCLE, ARC, ELLIPSE
- Estimated changes: ~30 lines

---

## Dependencies and Considerations

### ezdxf Version Requirements
- `from_vertices()` available since ezdxf 0.17
- `flattening()` method stable across versions
- Current project uses ezdxf (version should be checked)

### Performance Impact
- SPLINE flattening is expensive for complex splines
- Nested INSERT recursion could be deep for complex drawings
- Consider caching nested block bboxes

### Backward Compatibility
- Changes affect `ContentZoneData` values (suggested trims may change)
- Block bounding boxes will be more accurate (potentially larger with nested blocks)
- Users may need to re-tune threshold settings

---

## Testing Strategy

### Unit Tests Required

1. **LWPOLYLINE with Bulge**
   - Create polyline with 90-degree arc bulge
   - Verify flattened vertices follow arc path
   - Compare edge count with straight-line version

2. **Nested INSERT**
   - Block A contains INSERT of Block B
   - Verify Block A bbox includes Block B geometry
   - Test with scale, rotation, and translation
   - Test circular reference protection

3. **ELLIPSE**
   - Verify bounding box matches ellipse extents
   - Verify edge extraction produces valid polygon
   - Test various eccentricities

4. **SPLINE**
   - Verify bounding box captures spline extent
   - Test control point fallback for degenerate splines

5. **ARC Bounding Box**
   - Compare old (full circle) vs new (actual extent)
   - Test arcs at various angles (0-90, 90-180, crossing 0)

6. **Edge Count Formula**
   - Verify formula matches actual flattening output
   - Test with various radius/sagitta combinations

---

## Appendix: Code Location Reference

| Function | File | Lines | Purpose |
|----------|------|-------|---------|
| `_get_block_bounding_box()` | geometry.py | 179-266 | Block bbox calculation |
| `_extract_all_edges()` | geometry.py | 658-729 | Edge extraction for polygon detection |
| `_extract_hatch_boundary_edges()` | geometry.py | 626-655 | Hatch edge extraction (has bulge handling) |
| `_estimate_edge_count()` | geometry.py | 499-546 | Early-exit complexity estimation |
| `_extract_circle_edges()` | geometry.py | 574-588 | Circle to edges via flattening |
| `_extract_arc_edges()` | geometry.py | 591-623 | Arc to edges via flattening |
| Nested block tracking | extractor.py | ~1197 | Parent-child relationship tracking |
