# Polygon Area Calculation for Block Trimming Analysis

## Executive Summary
The codebase already implements polygon area calculation using the shoelace formula (`_shoelace_area()` in geometry.py). However, the current content zone detection algorithm cannot produce accurate trim values for the three target blocks because: (1) composite shapes formed by mixed LINE + LWPOLYLINE entities aren't detected, (2) boundary LWPOLYLINEs filling entire blocks aren't filtered, and (3) LINE entities don't form closed cycles by themselves in these blocks.

## Table Summary

| Block | Expected Trims (L/R/T/B) | Current Result | Issue | Root Cause |
|-------|--------------------------|----------------|-------|------------|
| GS900x450HGE_Liquor | 13/13/0/24.375 | 26/26/440/24 | Wrong L/R/T | 8-sided shape is composite (3 LINEs + 1 LWPOLY) |
| Gcase(w1800) | 0/200/0/0 | 0/0/0/0 | Missing R trim | LINE divider not used to calculate regions |
| Bread gondola end | 304.8/304.8/152.4/0 | 0/0/0/0 | All wrong | LINEs form tiered rectangles, not detected |

## Relevant Files
- `app/core/geometry.py:391-423` - `_shoelace_area()` implements polygon area calculation using shoelace formula
- `app/core/geometry.py:462-484` - `_polygon_contains_polygon()` checks polygon containment for net area
- `app/core/geometry.py:676-734` - `_calculate_net_areas()` calculates net areas (gross minus contained)
- `app/core/geometry.py:737-847` - `_detect_content_zone()` current content zone detection algorithm
- `app/core/geometry.py:547-673` - `_extract_line_cycles()` attempts to find closed LINE cycles
- `app/tests/assets/samples/sample-blocks.dxf` - Test file with target blocks
- `app/tests/assets/samples/sample-blocks-actual-trim-values.xlsx` - Expected trim values

## Current Algorithm Capabilities

### What Works
| Capability | Implementation | Status |
|------------|----------------|--------|
| Polygon area (shoelace) | `_shoelace_area()` | Implemented |
| Point-in-polygon test | `_point_in_polygon()` | Implemented |
| Polygon containment | `_polygon_contains_polygon()` | Implemented |
| Net area calculation | `_calculate_net_areas()` | Implemented |
| LWPOLYLINE extraction | `_extract_closed_lwpolylines()` | Implemented |
| LINE cycle detection | `_extract_line_cycles()` | Implemented (DFS-based) |

### What's Missing
| Capability | Required For | Status |
|------------|--------------|--------|
| Mixed entity cycle detection | GS900x450HGE_Liquor | Not implemented |
| Boundary LWPOLY filtering | Gcase, Bread gondola | Not implemented |
| LINE-based region splitting | Gcase(w1800) | Not implemented |
| Innermost LINE rectangle detection | Bread gondola end | Not implemented |

## Block-by-Block Analysis

### GS900x450HGE_Liquor

**Geometry:**
```
Block: 926 x 481
LINEs (4):
  - Top: (13, 481) -> (913, 481)      # Structural
  - Left: (13, 481) -> (13, 65)       # Structural
  - Right: (913, 65) -> (913, 481)    # Structural
  - Baseline: (26, 0) -> (900, 0)     # Decorative

LWPOLYLINEs (3):
  - Bottom-left corner: area=1,690
  - Bottom-right corner: area=1,690
  - Connector strip: area=14,203 (SELECTED by current algorithm)
```

**User's 8-Sided Polygon:** The large 8-sided polygon is NOT a single entity. It's a composite boundary formed by:
- 3 LINE edges (left, top, right at x=13, y=481, x=913)
- Stepping down through corner rectangles
- Using connector strip LWPOLY bottom edge at y=24.375

**Why Current Algorithm Fails:**
- LINE cycle detection finds 0 cycles (LINEs don't form closed shape alone)
- Algorithm selects connector strip LWPOLY (largest net area = 14,203)
- Connector strip bbox is (26, 24, 900, 41) -> trims 26/26/440/24
- Expected content zone is (13, 24.375, 913, 481) -> trims 13/13/0/24

**Solution Required:** Hybrid approach combining:
- LINE bounding box for left/right/top edges
- LWPOLY min_y for bottom edge

### Gcase(w1800)

**Geometry:**
```
Block: 600 x 1800
LWPOLYLINE (1): Fills entire block (0,0) to (600,1800), area=1,080,000
LINE (1): Vertical divider at x=400, full height
```

**User's Interpretation:** The vertical LINE creates two regions:
- Left region: x=[0, 400], area = 400 * 1800 = 720,000
- Right region: x=[400, 600], area = 200 * 1800 = 360,000

Since left region is larger, content zone should be left side -> trim_right = 200.

**Why Current Algorithm Fails:**
- Single LWPOLY fills entire block -> content zone = block bbox -> all trims = 0
- LINE cycle detection finds 0 cycles (single LINE can't form cycle)
- No mechanism to use LINE as region divider

**Solution Required:** Region-splitting algorithm:
1. Detect full-block LWPOLY (boundary, not content)
2. Use internal LINEs to divide block into regions
3. Select largest region as content zone

### Bread gondola end

**Geometry:**
```
Block: 1219.2 x 609.6
LWPOLYLINE (1): Fills entire block (boundary), area=743,224
LINEs (7): Form tiered stepped structure

Tiers (innermost to outermost):
- Tier 1: H-LINE y=457.2, V-LINEs x=304.8 & x=914.4
  Rectangle: (304.8, 0) to (914.4, 457.2), area=278,668

- Tier 2: H-LINE y=508.0, V-LINEs x=152.4 & x=1066.8
  Rectangle: (152.4, 0) to (1066.8, 508.0), area=464,515

- Tier 3: H-LINE y=558.8, full width
  Not a complete rectangle (no V-LINEs at edges)
```

**Net Area Calculation (User's Request):**
The user correctly identifies that nested tiers should use NET area:
- Tier 1 (innermost): 278,668 (full area - nothing inside)
- Tier 2: 464,515 - 278,668 = 185,847 (minus Tier 1)
- Tier 3: (incomplete, but would subtract Tier 2)

**Largest Net Area = Tier 1 = 278,668** -> content zone should be Tier 1

**Why Current Algorithm Fails:**
- LINE cycle detection finds 0 cycles (LINEs don't connect at corners)
- Single LWPOLY fills block -> detected as content zone -> trims = 0
- No mechanism to find LINE-formed rectangles

**Expected Result:**
```
Content zone: (304.8, 0, 914.4, 457.2)
trim_left = 304.8 - 0 = 304.8
trim_right = 1219.2 - 914.4 = 304.8
trim_top = 609.6 - 457.2 = 152.4
trim_bottom = 0 - 0 = 0
```

## Why LINE Cycles Aren't Detected

The `_extract_line_cycles()` function builds an adjacency graph from LINE endpoints and uses DFS to find cycles. However, it only finds cycles where LINE endpoints EXACTLY connect (within 0.01 tolerance).

**GS900x450HGE_Liquor:** LINEs don't form closed shape:
```
LINE 1: (13, 481) -> (913, 481)
LINE 2: (13, 481) -> (13, 65)    # Connects to LINE 1 at (13, 481)
LINE 3: (913, 65) -> (913, 481)  # Connects to LINE 1 at (913, 481)
LINE 4: (26, 0) -> (900, 0)      # No connection to others
```
3 structural LINEs form an incomplete "U" shape - no cycle.

**Bread gondola end:** LINEs form stepped structure but not at same coordinates:
```
H-LINE: y=457.2, x=[304.8, 914.4]
V-LINEs: x=304.8 y=[0, 457.2], x=914.4 y=[0, 457.2]
```
The V-LINEs connect to H-LINE at (304.8, 457.2) and (914.4, 457.2), but there's no bottom H-LINE at y=0 to complete the rectangle.

## Recommendations

### 1. Add Boundary LWPOLY Detection
```python
def _is_boundary_lwpoly(poly_bbox, block_bbox, tolerance=1.0):
    """Check if LWPOLY fills entire block (boundary, not content)."""
    return (abs(poly_bbox[0] - block_bbox[0]) < tolerance and
            abs(poly_bbox[1] - block_bbox[1]) < tolerance and
            abs(poly_bbox[2] - block_bbox[2]) < tolerance and
            abs(poly_bbox[3] - block_bbox[3]) < tolerance)
```

### 2. Add LINE Rectangle Detection
```python
def _find_line_rectangles(block_def):
    """Find rectangles formed by H-LINEs + V-LINEs with implicit bottom at y=0."""
    h_lines = []  # (x_min, x_max, y)
    v_lines = []  # (x, y_min, y_max)

    # Extract and classify LINEs...

    rectangles = []
    for (x_min, x_max, y) in h_lines:
        # Check if V-LINEs exist at both x coordinates
        left_v = find_vline_at_x(v_lines, x_min, tolerance=1.0)
        right_v = find_vline_at_x(v_lines, x_max, tolerance=1.0)
        if left_v and right_v:
            # Rectangle with implicit bottom at y=0
            rectangles.append((x_min, 0, x_max, y))

    return sorted(rectangles, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))  # By area
```

### 3. Add Region Splitting for Divider LINEs
```python
def _split_regions_by_lines(block_bbox, v_lines):
    """Split block into regions using vertical divider LINEs."""
    x_coords = [block_bbox[0]] + sorted([v[0] for v in v_lines]) + [block_bbox[2]]

    regions = []
    for i in range(len(x_coords) - 1):
        width = x_coords[i+1] - x_coords[i]
        height = block_bbox[3] - block_bbox[1]
        area = width * height
        regions.append((x_coords[i], block_bbox[1], x_coords[i+1], block_bbox[3], area))

    return max(regions, key=lambda r: r[4])  # Return largest region
```

### 4. Block Type Classification
Different blocks require different algorithms:

| Type | Detection | Algorithm |
|------|-----------|-----------|
| Interior LWPOLYs | Multiple LWPOLYs, none fill block | Current (largest net area) |
| Composite Boundary | LINEs + interior LWPOLYs | Hybrid (LINE bbox + LWPOLY edges) |
| Tiered Structure | Full-block LWPOLY + LINE rectangles | Innermost LINE rectangle |
| Section Dividers | Full-block LWPOLY + vertical LINEs | Region splitting |

## Next Steps

1. **Implement boundary LWPOLY detection** - Filter LWPOLYs that fill entire block before net area calculation
2. **Implement LINE rectangle detection** - Find closed rectangles from H-LINE + V-LINE combinations with implicit bottom
3. **Implement region splitting** - Use vertical divider LINEs to split blocks into regions
4. **Add block type classification** - Auto-detect block structure type and apply appropriate algorithm
5. **Create test cases** - Add unit tests for each block with expected trim values

## Conclusion

**Can we calculate polygon areas?** Yes - shoelace formula is implemented and working.

**Do we get accurate trimming?** No - the current algorithm cannot handle:
- Composite shapes (GS900x450HGE_Liquor's 8-sided boundary)
- Region-splitting divider lines (Gcase's vertical divider)
- LINE-formed tiered rectangles (Bread gondola end's stepped structure)

The net area calculation logic is correct (subtracting contained polygon areas), but the polygon DETECTION is incomplete. The algorithm needs to be extended to recognize these geometric patterns.
