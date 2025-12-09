# Block Polygon Count Discrepancy Analysis

## Executive Summary

The polygon count discrepancy between Excel output and user expectations stems from a fundamental difference in detection methodology. The current algorithm counts **closed CAD entities** (closed LWPOLYLINEs + LINE cycles), while users expect **visual paint-bucket regions** (all fillable areas bounded by any combination of lines and boundaries). A paint-bucket style algorithm that includes the outer boundary in edge detection matches user expectations for 4 of 5 blocks.

## Table Summary

| Block Name | Excel Count | User Count | Root Cause | Paint-Bucket Result |
|------------|-------------|------------|------------|---------------------|
| AP #5-4 | 1 | 8 | LINEs don't form closed loops without boundary | 8 ✓ |
| Bread gondola | 4 | 13 | Most LINEs are internal dividers, not closed loops | 13 ✓ |
| Bread gondola end | 1 | 4 | LINEs are T-junctions, no closed loops | 4 ✓ |
| GS900x450HGE_Liquor | 3 | 4 | U-shape is open at bottom, not a polygon | 3 ✗ (see note) |
| Gcase(w1800) | 1 | 2 | Single LINE divides rectangle, not closed loop | 2 ✓ |

**Note on GS900x450HGE_Liquor**: User counts the U-shaped interior as a region, but it's geometrically open at y=65. The 3 LINEs don't connect to form a closed polygon.

## Relevant Files

- `app/core/geometry.py:526-581` - `_extract_line_cycles()` function using Shapely polygonize
- `app/core/geometry.py:641-784` - `_detect_content_zone()` main detection logic
- `app/core/geometry.py:375-404` - `_extract_closed_lwpolylines()` for closed polyline extraction
- `app/core/constants.py:140-150` - Threshold constants (LINE_SEGMENT_THRESHOLD, POLYGON_COUNT_THRESHOLD)
- `app/tests/assets/samples/sample-blocks.dxf` - Test file containing the 5 blocks

## Current Algorithm Flow

```
For each block:
1. Extract closed LWPOLYLINEs (polylines with closed=True flag)
2. Extract LINE segments from block
3. Apply unary_union() to split lines at intersections
4. Run polygonize() to find closed LINE cycles
5. polygon_count = len(closed_LWPOLYLINEs) + len(LINE_cycles)
```

## Block-by-Block Analysis

### AP #5-4 (Excel: 1, User: 8)

**Entity Composition:**
- 1 closed LWPOLYLINE (outer rectangle: 762 × 4876.8)
- 4 LINE segments (1 vertical + 3 horizontal creating grid)

**Algorithm Trace:**
```
Step 1: Closed LWPOLYs = 1 (the outer rectangle)
Step 2: LINE segments = 4
  - Vertical: (381,0) → (381,4876.8) - full height
  - Horizontal: (0,1219.2) → (762,1219.2) - full width
  - Horizontal: (0,2438.4) → (762,2438.4) - full width
  - Horizontal: (0,3657.6) → (762,3657.6) - full width
Step 3: unary_union splits at intersections → 10 segments
Step 4: polygonize finds 0 cycles (lines don't close on their own)
Result: 1 polygon
```

**Why No LINE Cycles:**
The 4 LINEs form a cross/grid pattern but require the outer boundary to create closed regions. Without the boundary, the vertical line has no left/right edges to close against.

**Paint-Bucket Fix:**
When boundary edges are included in polygonize: **8 regions** (matches user)

---

### Bread gondola (Excel: 4, User: 13)

**Entity Composition:**
- 1 closed LWPOLYLINE (outer rectangle: 1219.2 × 1219.2)
- 13 LINE segments (vertical dividers + small horizontal bars)

**Algorithm Trace:**
```
Step 1: Closed LWPOLYs = 1
Step 2: LINE segments = 13
Step 3: unary_union → 21 segments
Step 4: polygonize finds 3 cycles (small rectangles from LINE intersections)
Result: 4 polygons
```

**Why Only 3 LINE Cycles:**
Most vertical LINEs span full height (0 to 1219.2) but don't intersect each other horizontally. Only 2 small rectangle regions are formed by LINE-to-LINE intersections.

**Paint-Bucket Fix:**
Including boundary: **13 regions** (matches user)

---

### Bread gondola end (Excel: 1, User: 4)

**Entity Composition:**
- 1 closed LWPOLYLINE (outer rectangle)
- 7 LINE segments (vertical + horizontal creating T-junctions)

**Algorithm Trace:**
```
Step 1: Closed LWPOLYs = 1
Step 2: LINE segments = 7
  - 4 vertical lines at different x positions
  - 3 horizontal lines at different y positions
Step 3: unary_union → 7 segments (no additional splits)
Step 4: polygonize finds 0 cycles
Result: 1 polygon
```

**Why No LINE Cycles:**
The LINEs form T-junctions (lines end at other lines) but don't fully enclose any area. They're structural dividers, not closed shapes.

**Paint-Bucket Fix:**
Including boundary: **4 regions** (matches user)

---

### GS900x450HGE_Liquor (Excel: 3, User: 4-5)

**Entity Composition:**
- 3 closed LWPOLYLINEs:
  - Left square: 26 × 65 (area 1690)
  - Right square: 26 × 65 (area 1690)
  - Thin rectangle: 874 × 16.25 (area 14202.5)
- 4 LINE segments (U-shape top + decorative bottom)

**Algorithm Trace:**
```
Step 1: Closed LWPOLYs = 3
Step 2: LINE segments = 4
  - Horizontal top: (13,481) → (913,481)
  - Left vertical: (13,481) → (13,65)
  - Right vertical: (913,65) → (913,481)
  - Decorative bottom: (26,0) → (900,0)
Step 3: unary_union → 5 segments
Step 4: polygonize finds 0 cycles (U-shape is open at y=65)
Result: 3 polygons
```

**Why Only 3:**
The 3 LINEs form an inverted U-shape open at the bottom (y=65). There's no LINE connecting x=13 to x=913 at y=65, so it's not a closed polygon. The decorative LINE at y=0 is disconnected.

**Paint-Bucket Issue:**
Even with boundary included, the U-shape interior doesn't close. User visually perceives the interior as a "fillable" region, but geometrically it's open. The 4th LINE (decorative) is at a different y-level and doesn't help close the U.

---

### Gcase(w1800) (Excel: 1, User: 2)

**Entity Composition:**
- 1 closed LWPOLYLINE (rectangle 600 × 1800)
- 1 LINE segment (vertical divider at x=400)

**Algorithm Trace:**
```
Step 1: Closed LWPOLYs = 1
Step 2: LINE segments = 1
  - Vertical: (400,0) → (400,1800) - full height
Step 3: unary_union → 1 segment
Step 4: polygonize finds 0 cycles (single line can't form polygon)
Result: 1 polygon
```

**Why Only 1:**
A single LINE cannot form a closed polygon. It simply divides the outer rectangle visually.

**Paint-Bucket Fix:**
Including boundary: **2 regions** (matches user)

---

## Algorithm Comparison

| Approach | Description | Limitations |
|----------|-------------|-------------|
| **Current** | Closed LWPOLYs + LINE cycles only | Misses regions bounded by outer boundary + internal lines |
| **Paint-Bucket** | Include outer boundary in edge set before polygonize | Matches visual expectations; requires identifying "outer" boundary |
| **Full Planar Graph** | Build complete planar subdivision from all edges | Most accurate but complex; handles nested boundaries |

## Recommendations

1. **Short-term**: Document current behavior in user-facing output (polygon_count represents "closed CAD entities" not "visual regions")

2. **Medium-term**: Implement paint-bucket algorithm:
   ```python
   def _extract_paint_bucket_regions(block_def, outer_boundary):
       all_edges = extract_lines(block_def)
       all_edges += boundary_to_linestrings(outer_boundary)
       merged = unary_union(all_edges)
       return list(polygonize(merged.geoms))
   ```

3. **Long-term**: Add configurable detection mode:
   - `polygon_count_closed_entities` (current)
   - `polygon_count_visual_regions` (paint-bucket)

## Next Steps

1. Decide whether to change algorithm behavior or add a new column
2. If changing: implement paint-bucket approach using block bounding box or largest LWPOLY as boundary
3. Handle edge case of GS900x450HGE_Liquor (open U-shape) - may need to connect line endpoints at boundary
4. Add unit tests for paint-bucket detection with known expected counts
