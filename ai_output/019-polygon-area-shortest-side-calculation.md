# Polygon Surface Area and Shortest Side Calculation After Precision Fix

## Executive Summary

This report analyzes the best approaches to calculate surface area and shortest straight side length for each polygon after Precision Fix is applied. The key insight is that `_extract_paint_bucket_regions()` already produces polygons with merged collinear segments and lines trimmed to intersection points - the required calculations can leverage these post-processed polygon vertices directly using Shapely geometry operations.

## Table Summary

| Calculation | Recommended Approach | Implementation Location | Complexity |
|-------------|---------------------|------------------------|------------|
| Surface Area | `ShapelyPolygon(vertices).area` with unit conversion | New function in `geometry.py` | Low |
| Shortest Straight Side | Iterate polygon exterior coords, detect collinear runs, calculate merged lengths | New function in `geometry.py` | Medium |
| Unit Conversion | Use GUI unit settings to convert from DXF units | Pass unit_override to calculation | Low |
| Collinear Merging | Already handled by `unary_union()` + `polygonize()` | Existing in `_extract_paint_bucket_regions()` | Already Done |

## Relevant Files

- **app/core/geometry.py** - Contains `_extract_paint_bucket_regions()` (lines 537-607) which builds polygons with precision fix applied. New area/side functions would be added here.
- **app/core/extractor.py** - Contains `get_snap_tolerances()` (lines 115-220) for unit-aware tolerance calculation. Extract blocks calls content zone detection with tolerances.
- **app/core/constants.py** - Contains `DEFAULT_PRECISION_FIX_TOLERANCE` (lines 230-247) and `DXF_INSUNITS_MAP` (lines 161-168) for unit mappings.
- **app/core/types.py** - Contains `Polygon` type definition (line 33) and `ContentZoneData` (lines 195-228).
- **app/tests/assets/samples/sample-blocks.dxf** - Sample file containing "Frysetorg OG D 1960 L 3750" block.

## How Precision Fix Solves the Collinear Segment Problem

The `_extract_paint_bucket_regions()` function already addresses the LINE1 (Part1) + LINE1 (Part2) merging requirement:

```
Original DXF:
  LINE1 (Part1): (74, -154) → (74, -152)     [length 2]
  LINE1 (Part2): (74, -805.5) → (74, -154)   [length 651.5]

After unary_union() + polygonize():
  Single polygon edge: (74, -805.5) → (74, -152)  [length 653.5]
```

**Why this works:**
1. `_extract_all_edges()` converts both LINE entities to Shapely LineStrings
2. `_snap_linestring_coords()` snaps coordinates to precision grid (fixes floating-point errors)
3. `unary_union()` merges overlapping/touching collinear segments and splits at T-junctions
4. `polygonize()` creates closed polygons from the resulting edge network

The polygon vertices returned represent the **actual corners** of the visual region, not the original DXF entity endpoints.

## Surface Area Calculation

### Approach 1: Direct Shapely Area (Recommended)

```python
from shapely import Polygon as ShapelyPolygon

def calculate_polygon_area(
    polygon: list[tuple[float, float]],
    unit_code: int,
    target_unit: str = "m2"
) -> float:
    """
    Calculate polygon surface area with unit conversion.

    Args:
        polygon: List of (x, y) vertices from _extract_paint_bucket_regions()
        unit_code: DXF $INSUNITS code (4=mm, 1=inches, etc.)
        target_unit: Target unit for output ("m2", "ft2", "mm2")

    Returns:
        Area in target units
    """
    shapely_poly = ShapelyPolygon(polygon)
    raw_area = abs(shapely_poly.area)  # Area in DXF drawing units squared

    # Unit conversion factors to meters
    UNIT_TO_METERS = {
        0: 1.0,      # Unitless - assume meters
        1: 0.0254,   # Inches to meters
        2: 0.3048,   # Feet to meters
        4: 0.001,    # Millimeters to meters
        5: 0.01,     # Centimeters to meters
        6: 1.0,      # Meters to meters
    }

    scale = UNIT_TO_METERS.get(unit_code, 1.0)
    area_m2 = raw_area * (scale ** 2)  # Convert area (square units)

    # Convert to target unit
    if target_unit == "m2":
        return area_m2
    elif target_unit == "ft2":
        return area_m2 * 10.7639
    elif target_unit == "mm2":
        return area_m2 * 1_000_000
    else:
        return area_m2
```

### Integration Point

Add to `ContentZoneData` or create new `PolygonMetrics` TypedDict:

```python
class PolygonMetrics(TypedDict):
    area_raw: float           # Area in DXF units squared
    area_converted: float     # Area in user-selected units
    shortest_side: float      # Shortest straight side length
    perimeter: float          # Total perimeter
```

## Shortest Straight Side Calculation

### The Challenge

After `polygonize()`, polygon vertices represent corners, but:
1. **Arc segments** are flattened to multiple short edges (from `ARC_FLATTENING_SAGITTA = 0.1`)
2. **Collinear points** may still exist if precision snap didn't merge them perfectly
3. We need to distinguish "straight sides" from curved sections

### Approach 1: Angle-Based Collinearity Detection (Recommended)

```python
import math
from shapely import Polygon as ShapelyPolygon

def calculate_shortest_straight_side(
    polygon: list[tuple[float, float]],
    angle_tolerance: float = 1.0  # degrees
) -> float:
    """
    Calculate the shortest straight side of a polygon.

    Merges consecutive collinear edges into single sides before
    finding the minimum. Handles the case where LINE1 (Part1) and
    LINE1 (Part2) should be counted as one side.

    Args:
        polygon: List of (x, y) vertices (closed polygon, no repeat of first point)
        angle_tolerance: Maximum angle deviation to consider edges collinear (degrees)

    Returns:
        Length of shortest straight side
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
        return angle % 180  # Normalize to 0-180 for direction-independent comparison

    def edge_length(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

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

### Approach 2: Using Shapely's simplify() for Collinearity

```python
from shapely import Polygon as ShapelyPolygon

def calculate_shortest_side_simplified(
    polygon: list[tuple[float, float]],
    simplify_tolerance: float = 0.01
) -> float:
    """
    Calculate shortest side using Shapely's simplify to merge collinear segments.

    Args:
        polygon: List of (x, y) vertices
        simplify_tolerance: Douglas-Peucker simplification tolerance

    Returns:
        Length of shortest side after simplification
    """
    shapely_poly = ShapelyPolygon(polygon)

    # Simplify removes collinear points
    simplified = shapely_poly.simplify(simplify_tolerance, preserve_topology=True)

    # Get exterior coordinates (includes closing point)
    coords = list(simplified.exterior.coords)

    # Calculate all side lengths
    side_lengths = []
    for i in range(len(coords) - 1):
        p1, p2 = coords[i], coords[i + 1]
        length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        if length > 1e-9:
            side_lengths.append(length)

    return min(side_lengths) if side_lengths else 0.0
```

### Handling LINE3 Intersection Case

The requirement states LINE3 should be measured "to the intersection at Y=-805.5 rather than the full original LINE3 length."

**This is already handled** by the paint-bucket algorithm:

```
Original LINE3: (1250, -909.5) → (1250, -152)  [full length 757.5]

After unary_union() splits at intersections with horizontal lines:
  Segment 1: (1250, -909.5) → (1250, -805.5)  [length 104]
  Segment 2: (1250, -805.5) → (1250, -152)    [length 653.5]
```

Each polygon will only include the portion of LINE3 that bounds it, not the full original line.

## Complete Integration Example

```python
def extract_polygon_metrics(
    block_def: BlockLayout,
    unit_code: int,
    precision_tolerance: float,
    gap_bridge_tolerance: float = 0.0,
) -> list[dict]:
    """
    Extract metrics for all polygons in a block after precision fix.

    Returns list of dicts with area and shortest_side for each polygon.
    """
    polygons = _extract_paint_bucket_regions(
        block_def,
        precision_tolerance=precision_tolerance,
        gap_bridge_tolerance=gap_bridge_tolerance,
    )

    results = []
    for polygon in polygons:
        shapely_poly = ShapelyPolygon(polygon)

        results.append({
            "vertices": polygon,
            "area_raw": abs(shapely_poly.area),
            "area_m2": calculate_polygon_area(polygon, unit_code, "m2"),
            "shortest_side": calculate_shortest_straight_side(polygon),
            "perimeter": shapely_poly.length,
        })

    return results
```

## Recommendations

1. **Add new functions to geometry.py**:
   - `calculate_polygon_area(polygon, unit_code, target_unit)` - Area with unit conversion
   - `calculate_shortest_straight_side(polygon, angle_tolerance)` - Merged side length calculation

2. **Extend ContentZoneData or create PolygonMetrics TypedDict** to store these values per polygon

3. **Use Approach 1 (angle-based)** for shortest side calculation because:
   - More control over what constitutes "collinear"
   - Handles flattened arcs correctly (they won't be merged due to angle changes)
   - Works with the actual polygon vertices after precision fix

4. **Unit conversion should use GUI settings** by passing `unit_override` parameter through the extraction chain

5. **Test with Frysetorg block** to verify:
   - LINE1 (Part1) + (Part2) merge correctly (expect ~653.5mm combined)
   - LINE3 is measured to intersection (expect segment lengths, not full 757.5)
   - 21 polygons detected with appropriate precision fix amount

## Next Steps

1. Implement `calculate_polygon_area()` function in geometry.py
2. Implement `calculate_shortest_straight_side()` function in geometry.py
3. Add unit tests using Frysetorg block from sample-blocks.dxf
4. Integrate with extraction pipeline to populate new fields
5. Update Excel writer to output new columns
