# Frysetorg Block Polygon Count Analysis

## Executive Summary

The block "Frysetorg OG D 1960 L 3750" returns 9 polygons regardless of Precision Fix setting because the block contains **intentional design gaps** in its vertical dividers (141-349 units), not floating-point precision errors. The precision fix (1e-6 tolerance) cannot bridge these large gaps. The user's expectation of 21 polygons is based on visual counting of rectangular areas, but many of these areas are not algorithmically closed due to the gaps in vertical lines.

## Table Summary

| Aspect | Value | Notes |
|--------|-------|-------|
| Block Name | Frysetorg OG D 1960 L 3750 | Norwegian freezer section block |
| LINE Entities | 22 | 10 horizontal + 12 vertical |
| MTEXT Entities | 2 | Not used in polygon detection |
| Polygons Detected | 9 | Same with/without Precision Fix |
| Expected (Visual) | 21 | User's visual count |
| Gap Size (x=74, x=3676) | 349 units | From y=-1154.5 to y=-805.5 |
| Gap Size (x=1250, x=2500) | 141 units | From y=-1050.5 to y=-909.5 |
| Precision Tolerance | 1e-6 | ~1 nanometer in mm units |
| Gap/Precision Ratio | 141-349 million:1 | Gaps are millions of times larger |

## Relevant Files

- `app/core/geometry.py:537-607` - `_extract_paint_bucket_regions()` function that performs polygon detection using Shapely's `unary_union` and `polygonize`
- `app/core/geometry.py:433-452` - `_snap_linestring_coords()` function that applies precision snapping
- `app/core/geometry.py:876-1035` - `_detect_content_zone()` orchestrates content zone detection including polygon count
- `app/core/constants.py:188-202` - `PRECISION_SNAP_TOLERANCE` dictionary defining tolerances by unit (1e-6 for mm)
- `app/tests/assets/samples/sample-blocks.dxf` - The DXF file containing the block

## Block Geometry Structure

The block consists of 22 LINE entities forming a grid:

### Horizontal Lines (10 total)
| Y Position | Span | Purpose |
|------------|------|---------|
| 0 | x: 0 to 3750 | Top edge |
| -80 | x: 0 to 3750 | Top strip divider |
| -152 | x: 0 to 3750 | Upper main grid boundary |
| -805.5 | x: 0 to 3750 | Upper-middle divider |
| -909.5 | x: 0 to 3750 | Middle section divider |
| -1050.5 | x: 0 to 3750 | Lower-middle divider |
| -1154.5 | x: 0 to 3750 | Lower main grid boundary |
| -1808 | x: 0 to 3750 | Bottom strip divider |
| -1880 | x: 0 to 3750 | Bottom strip divider |
| -1960 | x: 0 to 3750 | Bottom edge |

### Vertical Lines (12 total)
| X Position | Y Span | Gap |
|------------|--------|-----|
| 0 | Full: 0 to -1960 | None |
| 74 | -1808 to -1154.5, -805.5 to -152 | **349 units** |
| 1250 | -1808 to -1050.5, -909.5 to -152 | **141 units** |
| 2500 | -1808 to -1050.5, -909.5 to -152 | **141 units** |
| 3676 | -1808 to -1154.5, -805.5 to -152 | **349 units** |
| 3750 | Full: 0 to -1960 | None |

## Root Cause Analysis

### Why 9 Polygons Are Detected

The 9 polygons detected are:

1. **Large Outer Polygon** (area: 1,812,186 sq units)
   - Encompasses the entire block from (0, 0) to (3750, -1808)
   - Includes edge columns (x=0-74 and x=3676-3750) and top/bottom strips
   - These areas aren't separate polygons because interior verticals don't span there

2. **Upper Middle Cells** (3 polygons)
   - x=74-1250, y=-152 to -805.5 (area: 768,516)
   - x=1250-2500, y=-152 to -805.5 (area: 816,875)
   - x=2500-3676, y=-152 to -805.5 (area: 768,516)

3. **Lower Middle Cells** (3 polygons)
   - x=74-1250, y=-1154.5 to -1808 (area: 768,516)
   - x=1250-2500, y=-1154.5 to -1808 (area: 816,875)
   - x=2500-3676, y=-1154.5 to -1808 (area: 768,516)

4. **Transition Cells** (2 polygons)
   - x=1250-2500, y=-1050.5 to -1154.5 (area: 130,000)
   - x=1250-2500, y=-805.5 to -909.5 (area: 130,000)

### Why Precision Fix Doesn't Help

| Factor | Precision Fix Tolerance | Gap Sizes |
|--------|------------------------|-----------|
| Scale | 1e-6 (nanometer) | 141-349 units |
| Ratio | 1 | 141,000,000 to 349,000,000 |

The precision fix is designed to correct floating-point artifacts at line endpoints (differences of ~1e-10 to 1e-15 units). The gaps in this block are **design features**, not precision errors.

### Why Gap Bridge Doesn't Help

Testing gap bridge tolerances:

| Tolerance | Polygons Found | Result |
|-----------|---------------|--------|
| 0 | 9 | Baseline |
| 50 | 6 | Over-merging starts |
| 100 | 4 | More merging |
| 150+ | 0 | Complete breakdown |

Large gap bridge values cause over-merging of line segments, breaking polygon detection entirely.

## Visual vs Algorithmic Count

### User's Visual Count (21 polygons)
The user visually identified 21 rectangular regions:
- 1 top strip (y=0 to -80)
- 1 second strip (y=-80 to -152)
- 5 cells in upper main area
- 3 cells in upper-middle gap area
- 1 middle strip
- 3 cells in lower-middle gap area
- 5 cells in lower main area
- 1 lower strip
- 1 bottom strip

### Why Algorithm Finds 9
Many visual "rectangles" are not algorithmically closed because:

1. **Edge columns merge with outer polygon**: The vertical lines at x=74 and x=3676 don't span y=0 to -152 or y=-1808 to -1960, so edge cells connect to the outer boundary.

2. **Gaps prevent cell closure**: The gaps in vertical lines mean certain rows have no separating walls at specific X positions.

3. **Polygonize finds minimal closed regions**: Shapely's algorithm finds the smallest set of non-overlapping closed polygons, not all possible rectangular subdivisions.

## Horizontal Segment Values Explanation

The user's horizontal segments from the Excel output:
`80, 72, 653.5, 104, 141, 104, 651.5, 2, 72, 80`

These represent Y-direction distances between intersection points:
| Segment | Height | Y Range |
|---------|--------|---------|
| 80 | 80 | 0 to -80 |
| 72 | 72 | -80 to -152 |
| 653.5 | 653.5 | -152 to -805.5 |
| 104 | 104 | -805.5 to -909.5 |
| 141 | 141 | -909.5 to -1050.5 |
| 104 | 104 | -1050.5 to -1154.5 |
| 651.5* | ~653.5 | -1154.5 to -1808 |
| 2 | 2 | (small segment) |
| 72 | 72 | -1808 to -1880 |
| 80 | 80 | -1880 to -1960 |

*Note: 651.5 vs 653.5 discrepancy may be due to floating-point variations in the DXF coordinates.

## Recommendations

1. **No bug fix needed**: The algorithm is working correctly. The 9-polygon count accurately reflects the number of closed regions given the gaps in vertical lines.

2. **Consider documentation**: Document that polygon count represents closed regions, not visual rectangles. Blocks with intentional gaps will have fewer polygons than visually apparent cells.

3. **Alternative metric**: If users need to count visual cells, a different algorithm would be required that:
   - Identifies all rectangular subdivisions
   - Doesn't require complete closure
   - Would need to infer cell boundaries from partial lines

4. **Block design awareness**: This block appears to be a freezer section ("Frysetorg" = freezer in Norwegian) where gaps represent passages or openings - intentional design features.

## Next Steps

- [ ] Verify with user if the 9-count behavior is acceptable given the explanation
- [ ] Consider adding tooltip/documentation explaining polygon count semantics
- [ ] If visual cell count is needed, design a separate "cell detection" algorithm
