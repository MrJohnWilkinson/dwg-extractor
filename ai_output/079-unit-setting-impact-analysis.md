# Unit Setting Impact on Content Zone Detection

## Executive Summary

The unit selection (Inches vs Feet) affects extraction results because it changes the **default tolerance values** used for coordinate snapping and polygon filtering, NOT the coordinate values themselves. When the DXF file's coordinates are mismatched with the selected unit system, the tolerance ratios become inappropriate, causing significantly different polygon detection and filtering outcomes.

## Table Summary

| Parameter | Inches (code 1) | Feet (code 2) | Ratio (IN/FT) | Impact |
|-----------|-----------------|---------------|---------------|--------|
| Precision Tolerance | 0.125 | 0.0104 | 12:1 | Edge snapping aggressiveness |
| Min Side Filter | 0.394 | 0.0328 | 12:1 | Polygon side length threshold |
| Min Area Filter | 155.0 sq | 1.076 sq | 144:1 | Polygon area threshold |
| Polygon Count (before) | 41 | 37 | - | Different edge merging |
| Filtered Polygon Count | 6 | 31 | - | Different filter pass rate |
| Content Zone Width | 144.5 | 147.5 | - | Different surviving polygons |
| Trim Left/Right | 1.5 | (empty) | - | Different content zone bbox |

## Relevant Files

- **app/core/extractor.py:124-229** - `get_snap_tolerances()` - Calculates precision tolerance based on effective units, using `DEFAULT_GAP_CLOSURE_TOLERANCE` dict lookup
- **app/core/extractor.py:232-314** - `get_filter_values()` - Calculates min_area and min_side filter values based on effective units
- **app/core/constants.py:258-268** - `DEFAULT_GAP_CLOSURE_TOLERANCE` dict - Unit-specific default tolerances (3mm equivalent)
- **app/core/constants.py:288-298** - `DEFAULT_MIN_AREA_FILTER` dict - Unit-specific area thresholds (100,000 sq mm equivalent)
- **app/core/constants.py:308-318** - `DEFAULT_MIN_SIDE_FILTER` dict - Unit-specific side thresholds (10mm equivalent)
- **app/core/geometry.py:1186-1288** - `_extract_paint_bucket_regions()` - Uses precision_tolerance for coordinate snapping
- **app/core/geometry.py:1634-1909** - `_detect_content_zone()` - Applies min_side_filter and min_area_filter to polygons

## Root Cause Analysis

### The Core Problem: Coordinate vs Tolerance Mismatch

The DXF file coordinates remain **constant** regardless of unit selection:
- Block Native Width: 147.5 (raw coordinate units)
- Block Native Height: 60.91 (raw coordinate units)

When you select "Inches" or "Feet", only the **tolerance lookup keys** change, not the coordinates.

### How Tolerances Are Applied

1. **Precision Tolerance** (`_snap_linestring_coords()` in geometry.py:1038-1057):
   - Snaps coordinates to grid: `round(x / tolerance) * tolerance`
   - Larger tolerance = more aggressive snapping = more gaps bridged

2. **With Inches Selected** (tolerance = 0.125):
   - Grid spacing: every 0.125 units
   - For coordinates of ~147.5: tolerance is ~0.085% of coordinate magnitude
   - More gaps get bridged -> slightly different polygon boundaries

3. **With Feet Selected** (tolerance = 0.0104):
   - Grid spacing: every 0.0104 units
   - For coordinates of ~147.5: tolerance is ~0.007% of coordinate magnitude
   - Much tighter snapping -> fewer gaps bridged

### Why Filter Results Differ Dramatically

The min_side_filter shows the most dramatic effect:

**Inches mode** (min_side = 0.394):
- Filters out 4-sided rectangles with shortest side < 0.394 units
- Many small polygons get filtered -> only 6 survive
- Content zone bbox shrinks to 144.5 (surviving polygons are inward)

**Feet mode** (min_side = 0.0328):
- Filters out 4-sided rectangles with shortest side < 0.0328 units
- Very few polygons get filtered -> 31 survive
- Content zone bbox equals block bbox (147.5), so no trim values

### The Mathematical Explanation

If the drawing's coordinates are actually in inches (147.5 = 147.5"), then:

| Filter | Inches Mode | Feet Mode | Physical Equivalent |
|--------|-------------|-----------|---------------------|
| Precision | 0.125 / 147.5 = 0.085% | 0.0104 / 147.5 = 0.007% | 12x tighter in feet |
| Min Side | 0.394 / 147.5 = 0.27% | 0.0328 / 147.5 = 0.022% | 12x tighter in feet |
| Min Area | 155 / 147.5^2 = 0.71% | 1.076 / 147.5^2 = 0.005% | 142x tighter in feet |

## Why This Is Expected Behavior

The default tolerances are designed to be **physically equivalent** across units:
- 0.125" = 0.0104' (both ≈ 3mm)
- 0.394" = 0.0328' (both ≈ 10mm)
- 155 sq in = 1.076 sq ft (both ≈ 100,000 sq mm)

**The issue arises when the coordinate system doesn't match the selected unit.**

If your DXF has coordinates like 147.5, and those are meant to be inches:
- Selecting "Inches" gives appropriate tolerance ratios
- Selecting "Feet" makes tolerances appear 12x smaller relative to coordinates

## Solutions

### Option 1: Auto-Detect Units (Recommended)

Leave unit selection on "DXF/DWG" to use the file's `$INSUNITS` header value. This ensures tolerances match the coordinate system.

### Option 2: Override with Custom Amounts

If auto-detection fails or is incorrect:
1. Enable Precision Fix with a **custom amount** appropriate for your coordinates
2. Enable Min Side Filter with a **custom amount** appropriate for your geometry
3. The custom amounts bypass the unit-specific defaults

### Option 3: Verify DXF Units

Check what units the DXF was created in:
```python
# In Python with ezdxf:
doc = ezdxf.readfile('drawing.dxf')
units = doc.header.get('$INSUNITS', 0)
# 0=Unitless, 1=Inches, 2=Feet, 4=MM, etc.
```

## Simple List Summary

- Unit selection changes default tolerance values, NOT coordinate values
- "Inches" mode uses 12x larger tolerances than "Feet" mode
- Larger tolerances = more aggressive snapping = different polygon detection
- Filter thresholds also scale with units, causing different pass rates
- The DXF coordinates appear to be in inches; selecting "Feet" mismatches the tolerances
- Solution: Use "DXF/DWG" auto-detect or specify custom tolerance amounts
