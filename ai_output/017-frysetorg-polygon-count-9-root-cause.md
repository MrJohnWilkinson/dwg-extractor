# Frysetorg Block Polygon Count: Root Cause Analysis

## Executive Summary

The block "Frysetorg OG D 1960 L 3750" reports 9 polygons instead of the expected 21 due to **precision errors in the DXF file that exceed the precision fix tolerance**. The horizontal lines do not reach the vertical boundary edges due to coordinate mismatches of ~0.0003 units, while the precision fix only corrects errors smaller than 1e-6 (0.000001) units.

## Table Summary

| Issue | Expected | Actual | Root Cause |
|-------|----------|--------|------------|
| Polygon count | 21 | 9 | Coordinate precision errors ~0.0003 units |
| Precision fix tolerance | 1e-6 (0.000001) | Errors are ~0.0003 | Tolerance 300x too small |
| H-line at y=-80 right endpoint | x=3750.0 | x=3749.9997 | 0.0003 gap to right edge |
| Right vertical edge X | x=3750.0 | x=3749.9998 to 3750.0002 | Varying coordinates |
| Result with 1.0 snap | 21 polygons | 21 polygons | Snap closes the gaps |

## Relevant Files

- **app/core/geometry.py** - Contains `_extract_paint_bucket_regions()` which calls `_snap_linestring_coords()` before `unary_union()`. The snap tolerance is passed from the caller.
- **app/core/extractor.py** - Contains `get_snap_tolerances()` which returns `1e-6` for millimeter units as the precision tolerance.
- **app/core/constants.py** - Defines `PRECISION_SNAP_TOLERANCE` dict with `1e-6` for mm units (code 4).
- **app/tests/assets/samples/sample-blocks.dxf** - The DXF file containing the block with precision errors.

## Detailed Analysis

### Step 1: Raw DXF Coordinates

The block has 22 LINE entities. Key coordinate precision issues found:

```
Left vertical edge:  x = 0.0 (exact)
Right vertical edge: x = 3749.9998 to 3750.0002 (varies by line!)
H-line at y=-80:     x from -0.0 to 3749.9997 (doesn't reach right edge)
```

### Step 2: Y-Coordinate Clustering

Multiple Y values near the same logical coordinate:
```
y = -805.499974999991537  (vertical lines at x=74, x=3676)
y = -805.499974999984147  (horizontal line)
Gap: 7.39e-12 (7.39 picometers) - THIS is fixed by 1e-6 snap
```

### Step 3: X-Coordinate Clustering

The critical gap at the right boundary:
```
H-line y=-80 ends at:  x = 3749.999690
Right edge starts at:  x = 3749.999820
Gap: 0.00013 units - NOT fixed by 1e-6 snap!
```

### Step 4: Why 1e-6 Snap Fails

With precision tolerance = 1e-6:
- `3749.999690 / 1e-6 = 3749999690` rounds to `3749999690` -> `3749.999690`
- `3749.999820 / 1e-6 = 3749999820` rounds to `3749999820` -> `3749.999820`
- **Gap remains 0.00013 - coordinates don't match**

With tolerance = 1.0:
- `3749.999690 / 1.0 = 3749.999690` rounds to `3750` -> `3750.0`
- `3749.999820 / 1.0 = 3749.999820` rounds to `3750` -> `3750.0`
- **Gap closed - coordinates match exactly**

### Step 5: Polygon Formation

**With 1e-6 snap (9 polygons):**
- Horizontal lines at y=-80, -152, -1880, -1960 don't connect to edges
- Results in one huge outer polygon plus 8 internal rectangles

**With 1.0 snap (21 polygons):**
- All lines snap to integer grid, gaps close
- Proper 9-row grid forms with correct subdivisions

## Geometry Structure

The block geometry forms a grid:
```
Y levels: 0, -80, -152, -805, -909, -1050, -1154, -1808, -1880, -1960
X dividers: 0, 74, 1250, 2500, 3676, 3750

Expected structure (21 polygons):
- Row 1 (y=0 to -80): 1 full-width band
- Row 2 (y=-80 to -152): 1 full-width band
- Row 3 (y=-152 to -805): 5 columns (narrow-wide-wide-wide-narrow)
- Row 4 (y=-805 to -909): 3 columns (0-1250, 1250-2500, 2500-3750)
- Row 5 (y=-909 to -1050): 1 full-width band
- Row 6 (y=-1050 to -1154): 3 columns
- Row 7 (y=-1154 to -1808): 5 columns
- Row 8 (y=-1808 to -1880): 1 full-width band
- Row 9 (y=-1880 to -1960): 1 full-width band
```

## Recommendations

1. **Increase precision snap tolerance**: The current 1e-6 tolerance is designed for theoretical floating-point errors. Real DXF files have coordinate errors on the order of 0.0001 to 0.001 units. Consider 1e-3 or 1e-4 for mm units.

2. **Add unit-aware tolerance scaling**: The precision errors in DXF files are often proportional to the coordinate magnitude. A file with coordinates in the 3750 range may have errors of 3750 * 1e-7 = 0.000375.

3. **Consider relative tolerance**: Instead of absolute 1e-6, use a relative tolerance like `max(coord) * 1e-7` to scale with the drawing size.

4. **Document the limitation**: If keeping the conservative 1e-6 tolerance, document that DXF files with larger precision errors may not form complete polygon grids.

## Next Steps

1. Review the rationale for 1e-6 tolerance in `PRECISION_SNAP_TOLERANCE`
2. Test with 1e-4 tolerance to see if it fixes this case without breaking others
3. Consider adding a user-configurable "precision tolerance" slider similar to gap bridge
4. Add regression test with this specific block to track polygon count behavior
