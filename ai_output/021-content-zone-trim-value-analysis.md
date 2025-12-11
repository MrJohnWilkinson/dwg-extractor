# Content Zone and Trim Value Analysis Report

## Executive Summary

The extracted trim values and content zone dimensions do NOT solely depend on the Min Area Filter and Min Side Filter. The content zone detection algorithm uses **net area calculation** as the primary selection criterion, meaning the polygon with the largest area **after subtracting any contained polygons** is chosen as the content zone. With filters disabled (OFF), ALL detected polygons are candidates, and the algorithm selects whichever polygon has the maximum net area - which is often an inner polygon rather than the outer boundary.

## Table Summary

| Block Name | Native W×H | Content Zone W×H | Trim L/R/T/B | Polygon Count | Key Observation |
|------------|------------|------------------|--------------|---------------|-----------------|
| AP #5-4 | 762×4876.8 | 762×3660 | 0/0/-1.2/1218 | 8 | Content zone spans full width |
| Bread gondola | 1219.2×1219.2 | 459×1218 | 126/634.2/1.2/0 | 13 | Inner shelf area selected |
| Bread gondola end | 1219.2×609.6 | 609×456 | 306/304.2/153.6/0 | 4 | Central region selected |
| Frysetorg D 1960 L 3750 | 3750×1960 | 1248×654 | 1251/1251/1155/151 | 21 | Small internal region selected |
| Frysetorg OG D 1960 L 3750 | 3750×1960 | 1248×654 | 1251/1251/1155/151 | 21 | Identical to above (same block geometry) |
| GS900x450HGE_Liquor | 926×481 | 900×438 | 12/14/1/42 | 5 | Main display area selected |
| Gcase(w1800) | 600×1800 | 399×1800 | 0/201/0/0 | 2 | Full height, partial width |
| SPAR Gulv 900x600 H1860 | 930×1270 | 900×1068 | 15/15/101/101 | 7 | Central floor area selected |

## Relevant Files

- **`app/core/geometry.py:983-1176`** - `_detect_content_zone()` function - the main content zone detection algorithm
- **`app/core/geometry.py:644-714`** - `_extract_paint_bucket_regions()` - polygon extraction using paint-bucket algorithm
- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()` - net area calculation with containment subtraction
- **`app/core/extractor.py:950-1046`** - `extract_blocks()` - main extraction function with filter parameter handling
- **`app/core/constants.py:230-247`** - `DEFAULT_PRECISION_FIX_TOLERANCE` - precision fix default values

## Content Zone Detection Algorithm

### Step-by-Step Process

The content zone detection follows this exact sequence:

```
1. Extract ALL edges from block (LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, HATCH)
   ↓
2. Stage 1: Precision Fix (if enabled)
   - Snap all edge coordinates to a grid based on precision_tolerance
   - With "Precision Fix ON: 3", coordinates snap to 3-unit grid
   ↓
3. Stage 2: Gap Bridge (if enabled, OFF in your case)
   - Bridge small gaps between nearby endpoints
   ↓
4. Merge edges with unary_union() - splits at ALL intersections
   ↓
5. Find ALL closed regions with polygonize()
   ↓
6. Apply filters (if enabled)
   - Min Area Filter: Remove polygons with area < threshold
   - Min Side Filter: Remove polygons with shortest side < threshold
   - BOTH FILTERS ARE OFF in your settings
   ↓
7. Calculate NET AREA for EACH polygon
   - net_area = polygon_area - sum(areas of contained polygons)
   ↓
8. Select polygon(s) with LARGEST net area as content zone
   ↓
9. Calculate trim values from content zone bbox relative to block bbox
```

### The Critical Factor: Net Area Selection

**This is the root cause of unexpected values.** The algorithm does NOT select the outer boundary or the largest polygon. It selects the polygon with the **largest NET area**.

For nested shapes:
```
Outer polygon: Area = 10000, Contains inner polygon (6400)
Inner polygon: Area = 6400, Contains nothing

Net areas:
- Outer: 10000 - 6400 = 3600
- Inner: 6400 - 0 = 6400  ← LARGER NET AREA

Content zone = Inner polygon (not the outer boundary!)
```

## Detailed Block Analysis

### Frysetorg D 1960 L 3750 (Example Deep-Dive)

**Given:**
- Native Width: 3750, Native Height: 1960
- Content Zone: 1248×654
- Trim: Left=1251, Right=1251, Top=1155, Bottom=151
- Polygon Count: 21

**Verification of trim calculation:**
```
Width check:  1251 + 1248 + 1251 = 3750 ✓
Height check: 151 + 654 + 1155 = 1960 ✓
```

**Why this content zone was selected:**

With 21 polygons detected, the algorithm calculated net area for each. The selected content zone (1248×654 = 816,192 sq units) had the largest net area after subtracting any polygons it contained.

The content zone position (centered horizontally at 1251 from each side, offset vertically with 151 from bottom and 1155 from top) suggests this is likely an internal display shelf or usable floor area within the freezer unit - NOT the outer freezer boundary.

### AP #5-4

**Given:**
- Native Width: 762, Native Height: 4876.8
- Content Zone: 762×3660
- Trim: Left=0, Right=0, Top=-1.2 (negative!), Bottom=1218

**Analysis:**
The negative top trim (-1.2) indicates the content zone extends BEYOND the block bounding box at the top by 1.2 units. This can occur due to:
1. Floating-point precision artifacts
2. The precision fix (3 units) rounding coordinates
3. A polygon vertex that extends slightly past the nominal block boundary

### Bread gondola

**Given:**
- Native Width: 1219.2, Native Height: 1219.2
- Content Zone: 459×1218
- Trim: Left=126, Right=634.2, Top=1.2, Bottom=0

**Analysis:**
The asymmetric horizontal trim (126 left vs 634.2 right) shows the content zone is positioned toward the left side of the block. This is likely a shelf or display area that the net area calculation identified as the primary usable space.

## Why Min Area/Min Side Filters Don't Affect These Results

With both filters **OFF** (disabled):
- `min_area_filter = 0.0` → No polygons filtered by area
- `min_side_filter = 0.0` → No polygons filtered by side length

The code in `_detect_content_zone()` (lines 1060-1081):
```python
# Filter polygons by area and shortest side if filters are enabled
if min_area_filter > 0 or min_side_filter > 0:
    # ... filtering logic ...
```

Since both are 0, this block is skipped entirely. **ALL 21 polygons in Frysetorg remain candidates.**

The content zone selection is then purely based on which polygon has the maximum net area (line 1139):
```python
tied_shapes = [shape for shape, net_area in net_areas if net_area == max_net_area]
```

## The Precision Fix Factor

With "Precision Fix ON: 3", the precision tolerance is set to **3.0 drawing units**. This is passed to `_extract_paint_bucket_regions()`:

```python
# Stage 1: Precision snapping BEFORE union
if precision_tolerance > 0:
    edges = [_snap_linestring_coords(e, precision_tolerance) for e in edges]
```

The snapping function rounds coordinates to the nearest multiple of the tolerance:
```python
coords = [
    (round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
    for x, y in line.coords
]
```

With tolerance=3:
- Coordinate 1251.4 → rounds to 1251 (1251/3 = 417.13... → 417 × 3 = 1251)
- Coordinate 1249.8 → rounds to 1251 (1249.8/3 = 416.6 → 417 × 3 = 1251)

This 3-unit precision can merge vertices that are close together, potentially affecting polygon formation.

## Summary of All Factors Affecting Content Zone

| Factor | Your Setting | Effect |
|--------|-------------|--------|
| **Net Area Selection** | Always active | Primary selection criterion - polygon with largest (area - contained areas) wins |
| **Precision Fix** | ON: 3 | Snaps coordinates to 3-unit grid before polygon formation |
| **Gap Bridge** | OFF | No effect |
| **Min Area Filter** | OFF | No effect |
| **Min Side Filter** | OFF | No effect |
| **Polygon Count Threshold** | 500 | Skips detection if >500 polygons (not triggered here) |
| **Edge Count Threshold** | 5000 | Skips detection if >5000 edges (not triggered here) |

## Recommendations

### Option A: Use Filters to Exclude Small Interior Polygons
Enable filters to remove small internal shapes, forcing selection of larger boundary polygons:
```
Min Area Filter ON: Set to exclude internal shelf/component polygons
Min Side Filter ON: Set to exclude narrow structural elements
```

### Option B: Accept Algorithm Behavior
The current algorithm identifies the "usable area" within fixtures, which may actually be valuable for space planning (display shelving rather than overall fixture footprint).

### Option C: Algorithm Modification (Code Change)
If the outer boundary is always desired, the algorithm could be modified to:
1. Select polygon with largest GROSS area (not net)
2. Or select the polygon whose bounding box matches the block bounding box
3. Or provide a "select outer boundary" option

## Next Steps

1. **Test with filters enabled**: Try extraction with Min Area Filter set to filter out polygons smaller than expected content zone
2. **Verify expected behavior**: Clarify whether "content zone" should mean outer boundary or largest usable internal area
3. **Consider precision fix value**: A value of 3 units may be too aggressive for millimeter-scale drawings - consider 0.1 or 0.01

---
*Report generated from analysis of `app/tests/assets/samples/sample-blocks.dxf` with settings: Units=dxf/dwg, Precision Fix ON=3, Gap Bridge OFF, Min Area Filter OFF, Min Side Filter OFF*
