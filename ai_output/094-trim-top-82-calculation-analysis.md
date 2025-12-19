# Block R23-0103 Trim Top 82 Calculation Analysis

## Executive Summary

The "Block Suggested Trim Top" value of `82` differs from the user's expected `155` because the polygon at Y=13424.9365 is detected as having **5 sides instead of 4**. Since the min_side_filter only applies to 4-sided rectangles, this polygon passes the filter despite having a shortest side of 73 (below the 100 threshold). The 5-side count results from collinear edge merging not wrapping around the polygon boundary.

## Table Summary

| Component | Value | Notes |
|-----------|-------|-------|
| Block max_y | 13506.94 | Top of block bounding box |
| Content zone max_y | 13424.94 | Top of surviving polygon union |
| **Trim Top (calculated)** | **82.00** | 13506.94 - 13424.94 |
| **Trim Top (expected)** | **155.00** | If Y=13424.94 polygon was filtered |
| Polygon shortest side | 73.00 | Below min_side_filter of 100 |
| Polygon side count | 5 | Not 4, so min_side_filter skipped |

## Relevant Files

- `app/core/geometry.py:1766-1776` - `passes_min_side_filter()` logic that only applies to 4-sided polygons
- `app/core/geometry.py:87-171` - `calculate_shortest_straight_side()` with collinear edge merging
- `app/core/geometry.py:1876-1879` - Trim calculation formula: `trim_top = block_max_y - cz_max_y`
- `app/core/geometry.py:1862-1869` - Content zone union bounding box calculation

## Step-by-Step Calculation

### Step 1: Extract Polygons

14 polygons detected from block entities using paint-bucket algorithm.

### Step 2: Apply min_side_filter (= 100.0)

The filter logic (`geometry.py:1770-1776`):
```python
def passes_min_side_filter(polygon: Polygon) -> bool:
    shortest_side, side_count = calculate_shortest_straight_side(polygon)
    if side_count != 4:
        return True  # Pass all complex polygons (5+ sides)
    return shortest_side >= min_side_filter
```

Results for polygon at Y=13424.94:
- **Side count: 5** (not 4)
- **Shortest side: 73.00**
- **Filter result: PASS** (because side_count != 4)

### Step 3: Why 5 Sides Instead of 4?

The polygon has 6 vertices:
```
V0: (24953.75, 13351.94)
V1: (24172.75, 13351.94)
V2: (23391.75, 13351.94)
V3: (23391.75, 13424.94)
V4: (25734.75, 13424.94)
V5: (25734.75, 13351.94)
```

Visual representation:
```
           V3                        V4
  Y=13424.94 ●──────────────────────●
             │      top (2343)      │
             │                      │
  Y=13351.94 ●──────●──────●────────●
            V2     V1     V0       V5

Bottom edge: V5→V0 (781) + V0→V1 (781) + V1→V2 (781) = 2343
```

The collinear merging algorithm processes edges sequentially without wrapping:
- **Edges 0+1 (V0→V1→V2)**: Merged into one side (1562 units)
- **Edge 5 (V5→V0)**: Processed separately at the end (781 units)

If the algorithm properly wrapped around, edges 5+0+1 would merge into one 2343-unit side, creating a 4-sided rectangle.

**Merged sides:**
1. V0→V2: 1562 (edges 0+1 merged)
2. V2→V3: 73 (vertical, shortest!)
3. V3→V4: 2343 (top)
4. V4→V5: 73 (vertical, shortest!)
5. V5→V0: 781 (not merged with side 1)

### Step 4: Apply min_area_filter (= 80000)

After min_side_filter, 8 polygons remain. Net area calculation:
- Polygon at Y=13424.94: net_area = 171,039 > 80,000 → **PASS**
- 4 polygons total survive both filters

### Step 5: Calculate Content Zone

Union bounding box of 4 surviving polygons:
```
cz_min_x = 23391.75, cz_min_y = 12446.94
cz_max_x = 25734.75, cz_max_y = 13424.94
```

### Step 6: Calculate Trim Top

```
trim_top = block_max_y - cz_max_y
         = 13506.94 - 13424.94
         = 82.00
```

## Root Cause

**Two contributing factors:**

1. **Collinear merging doesn't wrap around**: The bottom edge (2343 total) is split into two "sides" (1562 + 781) because the algorithm doesn't merge the last edge (V5→V0) with the first edges (V0→V1→V2), even though they're collinear.

2. **min_side_filter only applies to 4-sided shapes**: By design, the filter skips polygons with side_count != 4. This was intentional to avoid filtering complex shapes unfairly, but causes the 5-sided polygon to pass.

## User's Expected Calculation

The user expected:
```
If polygon at Y=13424.94 was filtered:
  cz_max_y = 13351.94 (next highest polygon)
  trim_top = 13506.94 - 13351.94 = 155.00
```

## Potential Solutions

1. **Fix collinear merging to wrap around**: Ensure the last edge is checked against the first merged side for collinearity
2. **Apply min_side_filter to all polygons**: Remove the `side_count != 4` check (may have unintended effects on complex shapes)
3. **Add "strict side filter" option**: Let users choose whether the filter applies to all polygons or just rectangles

## Simple List Summary

- **Calculated trim_top (82)** = block_max_y (13506.94) - content_zone_max_y (13424.94)
- Polygon at Y=13424.94 has **5 sides** (not 4) due to collinear merging not wrapping
- min_side_filter (100) **only applies to 4-sided rectangles**
- The polygon's shortest side (73) is correctly detected but **filter is skipped**
- If this polygon were filtered, trim_top would be 155 as user expected
- Root cause: collinear edge merging algorithm limitation + intentional filter design
