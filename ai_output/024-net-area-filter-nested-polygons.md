# Net Area Filter for Nested Polygon Scenarios

## Executive Summary

This report investigates options for modifying the `min_area_filter` to use **net area** (gross area minus contained polygon areas) instead of gross area when filtering polygons. The goal is to handle "picture frame" scenarios where a large outer polygon fully contains a smaller inner polygon, and the meaningful area is the frame itself. After analyzing four implementation approaches, **Option A (Filter After Net Area Calculation)** is recommended as the simplest solution that addresses the core requirement with minimal code changes.

## Table Summary

| Option | Approach | Complexity | Accuracy | Recommendation |
|--------|----------|------------|----------|----------------|
| **A** | Filter after net area calc | Low | Good | **Recommended** |
| B | Shapely holes constructor | Medium | High | Over-engineering |
| C | Containment tree propagation | High | Highest | Future enhancement |
| D | Iterative re-filtering | Medium | Medium | Unstable behavior |

## Relevant Files

- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()`: Already calculates net areas by subtracting contained polygons using Shapely's `difference()` operation
- **`app/core/geometry.py:1059-1079`** - Current min_area_filter location in `_detect_content_zone()`: Filters BEFORE net area calculation using gross area
- **`app/core/geometry.py:57-81`** - `calculate_polygon_area()`: Returns gross area (not net)
- **`app/core/geometry.py:790-808`** - `_polygon_contains_polygon()`: Determines containment relationship
- **`app/core/extractor.py:950-962`** - `extract_blocks()`: Entry point passing filter parameters
- **`app/core/constants.py:258-275`** - `DEFAULT_MIN_AREA_FILTER`: Unit-specific default values

## Current Implementation Analysis

### How Filtering Works Today

```
1. _extract_paint_bucket_regions() → returns ALL polygons (including nested)
2. Filter by gross area (calculate_polygon_area) ← CURRENT FILTER LOCATION
3. Filter by shortest side
4. _calculate_net_areas() → subtracts contained polygons
5. Select polygon with largest NET area as content zone
```

### The Problem Illustrated

**Scenario**: Picture frame with outer rectangle (100 sq units) containing inner rectangle (80 sq units)

| Polygon | Gross Area | Net Area | Filter=50 (Current) | Filter=50 (Desired) |
|---------|------------|----------|---------------------|---------------------|
| Outer | 100 | 20 (frame) | PASS (100 > 50) | FAIL (20 < 50) |
| Inner | 80 | 80 | PASS (80 > 50) | PASS (80 > 50) |

**Current**: Both polygons pass because filtering uses gross area.
**Desired**: Outer polygon filtered out because its net area (the frame) is only 20.

## Implementation Options

### Option A: Filter After Net Area Calculation (Recommended)

**Approach**: Move the min_area_filter from before `_calculate_net_areas()` to after, filtering on net area values.

```python
# Current location (geometry.py:1059-1079):
# BEFORE _calculate_net_areas()
if min_area_filter > 0:
    area = calculate_polygon_area(shape)  # GROSS area
    if area < min_area_filter:
        continue

# Proposed location:
# AFTER _calculate_net_areas()
net_areas = _calculate_net_areas(all_shapes, abort_event)
if min_area_filter > 0:
    net_areas = [(poly, net_area) for poly, net_area in net_areas
                 if net_area >= min_area_filter]
```

**Pros**:
- Minimal code changes (move ~15 lines)
- Uses existing `_calculate_net_areas()` function
- Directly addresses the "picture frame" use case
- Maintains backward compatibility when filter is disabled

**Cons**:
- Net area calculation runs on ALL polygons before filtering (slight performance impact)
- Doesn't propagate area changes when outer polygon is removed

**Nested box-in-box behavior**:
```
Box A (outer): gross=1000, contains B → net=1000-500=500
Box B (middle): gross=500, contains C → net=500-100=400
Box C (inner): gross=100, contains nothing → net=100

With filter=150: A passes (500), B passes (400), C fails (100)
```

### Option B: Shapely Polygon with Holes Constructor

**Approach**: Use Shapely's `Polygon(exterior, [holes])` constructor to create polygons with explicit holes, where area is automatically computed as net.

```python
from shapely.geometry import Polygon

# Create polygon with hole
outer_ring = [(0,0), (10,0), (10,10), (0,10)]
inner_ring = [(2,2), (8,2), (8,8), (2,8)]
frame = Polygon(outer_ring, [inner_ring])
print(frame.area)  # 100 - 36 = 64 (net area)
```

**Pros**:
- Semantically correct representation
- Shapely handles complex hole geometries
- Built-in support for multiple holes

**Cons**:
- Requires significant refactoring of `_extract_paint_bucket_regions()`
- Changes the fundamental polygon representation throughout the codebase
- Need to build containment hierarchy first

### Option C: Containment Tree with Area Propagation

**Approach**: Build a tree structure representing containment relationships, calculate net areas from innermost to outermost, and propagate changes when polygons are filtered.

```python
class PolygonNode:
    polygon: Polygon
    children: list[PolygonNode]  # Contained polygons
    gross_area: float
    net_area: float  # gross - sum(children.gross_area)

def build_containment_tree(polygons: list) -> list[PolygonNode]:
    """Build tree where parent contains children."""
    # Sort by area descending (larger likely contains smaller)
    # For each polygon, find smallest polygon that contains it
    ...

def filter_with_propagation(roots: list[PolygonNode], min_area: float):
    """Filter and propagate area changes up the tree."""
    # Post-order traversal: process children before parents
    # When child is removed, add its gross area back to parent's net area
    ...
```

**Pros**:
- Most accurate handling of nested scenarios
- Supports "alternating" containment (solid → hole → solid → hole)
- Correctly handles area propagation when inner polygons are removed

**Cons**:
- Most complex implementation
- Requires new data structures
- Performance overhead for tree construction

**Nested behavior with propagation**:
```
Initial:
A (net=500) contains B (net=400) contains C (net=100)

Filter C (100 < 150):
- Remove C
- B's net area becomes: 400 + 100 = 500 (C's area returned)

Final: A (net=500), B (net=500)
```

### Option D: Iterative Re-filtering

**Approach**: Calculate net areas, filter, recalculate net areas for remaining polygons, repeat until stable.

```python
def iterative_filter(polygons, min_area):
    while True:
        net_areas = _calculate_net_areas(polygons)
        filtered = [p for p, net in net_areas if net >= min_area]
        if len(filtered) == len(polygons):
            break  # Stable
        polygons = filtered
    return polygons
```

**Pros**:
- Self-correcting behavior
- Handles cascading removals

**Cons**:
- May over-filter in edge cases
- Non-deterministic number of iterations
- Performance unpredictable

## Edge Case Analysis

### Case 1: Simple Picture Frame
```
Outer (100 sq) contains Inner (80 sq)
Net areas: Outer=20, Inner=80
Filter=50: Outer removed, Inner kept ✓
```

### Case 2: Box-in-Box-in-Box
```
A (1000) contains B (500) contains C (100)
Net: A=500, B=400, C=100
Filter=150: A kept, B kept, C removed
```

### Case 3: Multiple Siblings
```
Outer (1000) contains [A(200), B(200), C(200)]
Net: Outer=400, A=200, B=200, C=200
Filter=250: Outer kept, A/B/C removed
```

### Case 4: Deeply Nested (5 levels)
```
L1(10000) → L2(5000) → L3(2500) → L4(1000) → L5(100)
Net: L1=5000, L2=2500, L3=1500, L4=900, L5=100
Filter=1000: L1 kept, L2 kept, L3 kept, L4/L5 removed
```

## Recommendations

### Primary Recommendation: Option A

Implement **Option A (Filter After Net Area Calculation)** because:

1. **Simplicity**: Requires moving ~15 lines of code
2. **Correctness**: Addresses the core "picture frame" use case
3. **Backward Compatible**: No change when filter is disabled (default)
4. **Low Risk**: Uses existing, tested `_calculate_net_areas()` function

### Implementation Steps

1. In `_detect_content_zone()`, remove the current filtering loop (lines 1059-1079)
2. Call `_calculate_net_areas()` on all shapes
3. Apply min_area_filter to net_areas list
4. Apply min_side_filter to remaining polygons (uses gross geometry)
5. Continue with content zone selection

### Future Enhancement: Option C

If users need more sophisticated nested polygon handling (area propagation when inner shapes are removed), **Option C** can be implemented as a separate feature flag or advanced mode.

## Next Steps

1. **Implement Option A** as the immediate solution
2. **Add unit tests** for nested polygon scenarios:
   - Simple picture frame
   - Box-in-box-in-box (3+ levels)
   - Multiple siblings at same level
3. **Create test DXF files** with known nested geometries
4. **Document behavior** in user-facing documentation
5. **Consider Option C** for v2 if users report edge cases

## Code Change Estimate

| Component | Lines Changed | Risk |
|-----------|---------------|------|
| `geometry.py:_detect_content_zone()` | ~20 | Low |
| New tests | ~50-100 | N/A |
| Documentation | ~10 | N/A |
| **Total** | **~80-130** | **Low** |
