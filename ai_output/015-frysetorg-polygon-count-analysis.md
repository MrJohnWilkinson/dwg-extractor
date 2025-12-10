# Frysetorg Polygon Count Discrepancy Analysis

## Executive Summary

The block `Frysetorg OG D 1960 L 3750` returns only 8 polygons (Precision Fix OFF) or 6 polygons (Precision Fix ON) instead of the expected ~21 visual polygons. **Root cause: Floating-point coordinate errors in the DXF file prevent line intersections, causing Shapely's polygonize() to fail forming closed regions.**

## Table Summary

| Setting | Polygons Found | Expected | Gap |
|---------|---------------|----------|-----|
| Precision Fix OFF (tolerance=0.0) | 8 | ~21 | -13 |
| Precision Fix ON (tolerance=1e-6) | 6 | ~21 | -15 |
| With Coordinate Normalization | 20 | ~21 | -1 |

## Relevant Files

- `app/core/geometry.py:515-583` - `_extract_paint_bucket_regions()` function that performs polygon extraction
- `app/core/geometry.py:465-512` - `_extract_all_edges()` extracts LINE/POLYLINE edges
- `app/core/extractor.py:1091-1098` - Calls `_detect_content_zone()` with precision tolerances
- `app/core/constants.py:188-198` - `PRECISION_SNAP_TOLERANCE` dictionary defining snap values
- `app/tests/assets/samples/sample-blocks.dxf` - The DXF file containing the block

## Block Structure Analysis

The block is a freezer/refrigerator unit layout:
- **Overall dimensions:** 3750mm (width) x 1960mm (height)
- **Entity composition:** 21 LINE entities + 2 MTEXT entities

### Horizontal Lines (10 total, full-width)
```
Y=0        : Top edge
Y=-80      : Top rim boundary
Y=-152     : Second line
Y=-805.5   : Upper shelf area boundary
Y=-909.5   : Middle gap top
Y=-1050.5  : Middle gap center
Y=-1154.5  : Middle gap bottom
Y=-1808    : Lower shelf area boundary
Y=-1880    : Bottom rim boundary
Y=-1960    : Bottom edge
```

### Vertical Lines (partial coverage)
```
X=0        : Left edge (full height: 0 to -1960)
X=74       : Left trim (PARTIAL: -1808 to -1154.5, -805.5 to -152)
X=1250     : First divider (PARTIAL: -1808 to -1050.5, -909.5 to -152)
X=2500     : Second divider (PARTIAL: -1808 to -1050.5, -909.5 to -152)
X=3676     : Right trim (PARTIAL: -1808 to -1154.5, -805.5 to -154)
X=3750     : Right edge (full height: 0 to -1960)
```

## Root Cause: Floating-Point Coordinate Errors

### The Problem

The DXF file contains floating-point precision errors in coordinates:

**Right edge X values (should all be 3750.0):**
| Y Coordinate | Actual X Value | Delta from 3750 |
|--------------|----------------|-----------------|
| Y=0 | 3749.999820 | -0.000180 |
| Y=-80 | 3749.999690 | -0.000310 |
| Y=-805.5 | 3749.999974 | -0.000026 |
| Y=-1808 | 3750.000250 | +0.000250 |

**Range of errors:** -0.00031 to +0.00025 (~0.0005 total spread)

**Left edge X values (should all be 0.0):**
| Y Coordinate | Actual X Value |
|--------------|----------------|
| Y=0 | 0.0 |
| Y=-805.5 | 0.000314 |
| Y=-1154.5 | 0.000364 |
| Y=-1880 | 0.000430 |

### Why Lines Don't Connect

Test case: Horizontal line at Y=-80 vs Right vertical edge
```
Horizontal Y=-80: ends at X=3749.999690
Vertical edge:    at X=3749.999820
Gap: 0.00013mm
Intersection test: FALSE
```

Because the horizontal line ENDS at X=3749.99969 and the vertical line is at X=3749.99982, they DO NOT intersect. Shapely's `unary_union()` only splits segments at actual intersections - near-misses don't count.

## Algorithm Walkthrough

### Step 1: Edge Extraction
`_extract_all_edges()` extracts 21 LINE entities from the block.

### Step 2: Merge and Split with unary_union()
```python
merged = unary_union(edges)  # Splits at actual intersections only
```
Result: 52 line segments (splits occur where lines actually cross)

### Step 3: Precision Snap (Optional)
```python
if precision_tolerance > 0:
    merged = snap(merged, merged, precision_tolerance)
```
- Tolerance 1e-6 is 300-500x smaller than the coordinate errors (~0.0003 to ~0.0005)
- Even with larger tolerances (0.5, 1.0), snap() doesn't CREATE connections
- snap() only moves vertices that are within tolerance of other geometries
- The lines END BEFORE reaching the vertical edges - there's nothing to snap TO

### Step 4: Polygonize
```python
polygons = list(polygonize(segments))
```
Result: 6-8 polygons (only regions with fully closed edges)

## Why Precision Fix ON Finds FEWER Polygons

Counter-intuitively, enabling precision fix reduces the polygon count from 8 to 6.

**Explanation:** When snap() moves some vertices slightly, it can break connections that previously worked by chance. The chaotic nature of floating-point errors means some near-misses happened to align without snapping, but the snap operation perturbed them into non-alignment.

## Polygons Found vs Expected

### Precision Fix OFF (8 polygons)
| # | Bounds | Size | Description |
|---|--------|------|-------------|
| 1 | X=[0,3750] Y=[-1808,0] | 3750x1808 | Outer frame |
| 2 | X=[74,1250] Y=[-805.5,-152] | 1176x653.5 | Top-left shelf cell |
| 3 | X=[1250,2500] Y=[-805.5,-152] | 1250x653.5 | Top-middle cell |
| 4 | X=[1250,2500] Y=[-909.5,-805.5] | 1250x104 | Middle-left strip |
| 5 | X=[1250,2500] Y=[-1154.5,-1050.5] | 1250x104 | Middle-right strip |
| 6 | X=[74,1250] Y=[-1808,-1154.5] | 1176x653.5 | Bottom-left shelf |
| 7 | X=[1250,2500] Y=[-1808,-1154.5] | 1250x653.5 | Bottom-middle |
| 8 | X=[2500,3676] Y=[-1808,-1154.5] | 1176x653.5 | Bottom-right |

### Expected Visual Polygons (~21)
```
Layer 1 (Y=0 to -80):        1 cell  (top rim)
Layer 2 (Y=-80 to -152):     1 cell
Layer 3 (Y=-152 to -805.5):  5 cells (upper shelf area with 4 dividers)
Layer 4 (Y=-805.5 to -909.5): 3 cells (middle section, only 1250/2500 dividers)
Layer 5 (Y=-909.5 to -1050.5): 3 cells (center gap)
Layer 6 (Y=-1050.5 to -1154.5): 3 cells
Layer 7 (Y=-1154.5 to -1808): 5 cells (lower shelf area with 4 dividers)
Layer 8 (Y=-1808 to -1880):  1 cell
Layer 9 (Y=-1880 to -1960):  1 cell
Total: 1+1+5+3+3+3+5+1+1 = 23 cells (similar to user's count of 21)
```

### With Coordinate Normalization (20 polygons)
When coordinates are normalized (horizontal lines extended to exact X=0 and X=3750):
- 62 segments after unary_union (more intersections detected)
- 20 polygons found (close to expected 21)

## Recommendations

### Option 1: Pre-process Coordinate Normalization
Add a coordinate normalization step before polygon extraction:
```python
def normalize_coordinates(edges, tolerance=0.5):
    """Extend lines to reach boundary edges within tolerance."""
    # For each horizontal line ending near X=0 or X=max:
    #   - Extend to exact boundary if within tolerance
    # For each vertical line ending near Y=0 or Y=max:
    #   - Extend to exact boundary if within tolerance
```

### Option 2: Grid-Based Snapping
Snap all coordinates to a regular grid (e.g., 0.1mm or 1mm) before processing:
```python
def snap_to_grid(coord, grid_size=0.1):
    return round(coord / grid_size) * grid_size
```

### Option 3: Tolerance-Based Connection
Use a more aggressive algorithm that creates connections when line endpoints are within tolerance of other lines:
```python
from shapely.ops import nearest_points
# For each line endpoint, find nearest point on other lines
# If distance < tolerance, extend line to connect
```

### Option 4: Buffer-Based Approach
Use buffer/erosion to close small gaps:
```python
merged_buffered = merged.buffer(0.001).buffer(-0.001)  # Close tiny gaps
```

## Next Steps

1. **Decide on approach:** Grid snapping is simplest; coordinate extension is most accurate
2. **Implement fix:** Add pre-processing step in `_extract_paint_bucket_regions()`
3. **Add unit tests:** Create test cases with known polygon counts
4. **Validate:** Test with multiple DXF files to ensure fix doesn't break other cases

## Technical Details

### Shapely Function Behaviors
- `unary_union()`: Splits lines only at actual geometric intersections (not near-misses)
- `snap()`: Moves vertices within tolerance to nearby geometries, but doesn't extend lines
- `polygonize()`: Finds closed polygons from line segments; requires exact connections

### Why Current Tolerances Don't Work
| Tolerance | Purpose | vs Coordinate Errors |
|-----------|---------|---------------------|
| 1e-6 | Fix floating-point artifacts | 300-500x too small |
| 1e-4 | Slightly larger | 3-5x too small |
| 0.001 | Millimeter scale | Still insufficient (errors up to 0.0005) |
| 0.5 | Gap bridging | Doesn't create line extensions |

The fundamental issue is that `snap()` adjusts existing geometry but doesn't CREATE new connections between non-intersecting lines.
