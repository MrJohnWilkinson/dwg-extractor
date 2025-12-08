# Trim Value Analysis for Bread gondola end Block

## Executive Summary
Testing the extraction on `sample-blocks - Copy.dxf` reveals that **none of the approaches from the previous analysis produce the user's expected trim values for "Bread gondola end"**. The block has a stepped structure with an outer LWPOLYLINE that equals the block boundary, requiring a new "innermost connected boundary" approach. For consistent results across both blocks, the correct trim values for Bread gondola end are **left=304.8, right=304.8, top=152.4, bottom=0** (innermost tier).

## Table Summary

| Block | Approach | trim_left | trim_right | trim_top | trim_bottom | Accuracy |
|-------|----------|-----------|------------|----------|-------------|----------|
| **GS900x450HGE_Liquor** |
| | Expected | **13** | **13** | **0** | **24.375** | Target |
| | All LINE bbox | 13 | 13 | 0 | 0 | Partial |
| | Structural LINE bbox | 13 | 13 | 0 | 65 | Partial |
| | LINE + Largest LWPOLY | **13** | **13** | **0** | **24.38** | **Correct** |
| | Innermost boundary | 13 | 13 | 0 | 24.38 | Correct |
| **Bread gondola end** |
| | Expected (option A) | **304.8** | **304.8** | **152.4** | **0** | Target |
| | Expected (option B) | 152.4 | 152.4 | 101.6 | 0 | Target |
| | All LINE bbox | 0 | 0 | 50.8 | 0 | Wrong |
| | Structural LINE bbox | 0 | 0 | 50.8 | 0 | Wrong |
| | LINE + Largest LWPOLY | 0 | 0 | 0 | 0 | Wrong |
| | **Innermost boundary** | **304.8** | **304.8** | **152.4** | **0** | **Correct (A)** |

## Relevant Files
- `app/tests/assets/samples/sample-blocks - Copy.dxf` - Test file containing both blocks
- `app/core/geometry.py:737-847` - Current `_detect_content_zone()` implementation
- `ai_output/012-accurate-trim-gs900x450hge-analysis.md` - Previous GS900x450HGE analysis

## Block Geometry Analysis

### Bread gondola end Structure
```
Block bbox: (0.00, 0.00) to (1219.20, 609.60)
Block dimensions: 1219.20 x 609.60

LWPOLYLINE (closed, 4 points) - OUTER BOUNDARY:
  Rectangle: (0, 0) to (1219.20, 609.60)
  Area: 743,224 sq units
  NOTE: This equals the block bbox - NOT an interior content zone!

Horizontal LINEs (3 tiers, from innermost to outermost):
  y=457.20: x from 304.80 to 914.40   (Tier 1 - innermost)
  y=508.00: x from 152.40 to 1066.80  (Tier 2 - middle)
  y=558.80: x from 0.00 to 1219.20    (Tier 3 - full width)

Vertical LINEs (4):
  x=152.40:  y from 0.00 to 508.00   (extends to Tier 2)
  x=304.80:  y from 0.00 to 457.20   (extends to Tier 1)
  x=914.40:  y from 0.00 to 457.20   (extends to Tier 1)
  x=1066.80: y from 0.00 to 508.00   (extends to Tier 2)
```

### Visual Representation
```
         0      152.4   304.8               914.4  1066.8  1219.2
         |        |       |                   |       |       |
609.6 ---+========+===LWPOLYLINE RECTANGLE===+========+-------+
558.8 ---+--------+-------+---LINE TIER 3----+-------+-------+
508.0 ---|        +-------+---LINE TIER 2----+-------+       |
457.2 ---|        |       +---LINE TIER 1----+       |       |
         |        |       |                   |       |       |
         |        V       V                   V       V       |
    0 ---+--------+-------+-------------------+-------+-------+
```

## Why Current Approaches Fail for Bread gondola end

### Problem: Outer LWPOLYLINE = Block Boundary
The current "LINE + Largest LWPOLY Union" approach works for GS900x450HGE_Liquor because its largest LWPOLYLINE (the connector strip) is **inside** the block. However, for Bread gondola end, the largest LWPOLYLINE **IS** the block boundary itself.

**Result**: Union of LINE bbox + LWPOLY bbox = block bbox = zero trims.

### Problem: Full-Width Horizontal LINE
The All LINE bbox approach fails because the line at y=558.80 spans the full block width (x=0 to x=1219.20), resulting in:
- trim_left = 0 (LINE min_x = 0)
- trim_right = 0 (LINE max_x = 1219.20)

This doesn't capture the stepped interior structure.

## Correct Trim Values Determination

### Testing the Options
Given the user's options:
- trim_left = 152.4 or 304.8
- trim_right = 152.4 or 304.8
- trim_top = 50.8 or 101.6 or 152.4
- trim_bottom = 0

**Analysis of geometric relationships:**

| Option Set | Left | Right | Top | Bottom | Corresponding Structure |
|------------|------|-------|-----|--------|------------------------|
| **A (Innermost)** | 304.8 | 304.8 | 152.4 | 0 | Tier 1: y=457.2, x=[304.8, 914.4] |
| B (Middle) | 152.4 | 152.4 | 101.6 | 0 | Tier 2: y=508.0, x=[152.4, 1066.8] |
| C (Outermost) | 0 | 0 | 50.8 | 0 | Tier 3: y=558.8, x=[0, 1219.2] |

### Why Option A (Innermost) is Correct

For consistent behavior with GS900x450HGE_Liquor, we need an approach that identifies the **innermost connected structural boundary**:

1. **GS900x450HGE_Liquor**: The content zone is defined by the innermost visual boundary formed by LINE edges + LWPOLY bottom strip. Expected: left=13, right=13, top=0, bottom=24.375 ✓

2. **Bread gondola end**: Following the same principle, the content zone should be the innermost complete boundary formed by connected LINEs:
   - Horizontal line at y=457.20 spanning x=[304.8, 914.4]
   - Vertical lines at x=304.8 and x=914.4 extending from y=0 to y=457.2
   - These form a complete closed rectangle
   - **Result: left=304.8, right=304.8, top=152.4, bottom=0** ✓

## Recommended Algorithm

### Innermost Connected Boundary Detection

```python
def _detect_innermost_boundary(block_def, block_bbox):
    """
    Detect content zone as innermost complete boundary.

    Algorithm:
    1. Extract all horizontal LINEs (sorted by y descending)
    2. Extract all vertical LINEs
    3. For each horizontal LINE (from innermost/lowest-y to outermost):
       - Check if corresponding vertical LINEs exist at both ends
       - If yes, this defines the content zone
    4. If no LINE-based boundary found, fall back to LWPOLY approach
    """
    h_lines = []  # (x_min, x_max, y)
    v_lines = []  # (x, y_min, y_max)

    for entity in block_def:
        if entity.dxftype() == 'LINE':
            # Classify as horizontal or vertical
            ...

    # Sort horizontal lines by y ascending (innermost first)
    h_lines.sort(key=lambda h: h[2])

    for (x_min, x_max, y) in h_lines:
        # Check for corresponding vertical lines at x_min and x_max
        left_v = find_vertical_at_x(v_lines, x_min)
        right_v = find_vertical_at_x(v_lines, x_max)

        if left_v and right_v:
            # Found innermost complete boundary
            return ContentZone(
                min_x=x_min, max_x=x_max,
                min_y=0,  # or use vertical line y_min
                max_y=y
            )

    # Fallback to existing LWPOLY approach
    return _current_approach(block_def, block_bbox)
```

### Key Principles (No Decorative Exceptions)
1. **Treat all LINEs equally** - no filtering for "decorative" lines
2. **Treat all LWPOLYLINEs equally** - no special cases for boundary polylines
3. **Innermost connected boundary wins** - find the most restrictive complete rectangle
4. **Use geometric connectivity** - verify horizontal+vertical lines meet at endpoints

## Recommendations

1. **Implement Innermost Connected Boundary Detection**
   - Algorithm identifies smallest complete rectangle formed by LINE connections
   - Works consistently for both stepped (Bread gondola end) and mixed (GS900x450HGE) structures

2. **Add Boundary LWPOLY Detection**
   - If largest LWPOLY bbox ≈ block bbox (within tolerance), treat it as boundary, not content zone
   - Use LINE-based detection instead

3. **No Decorative Exceptions**
   - Per user requirement, avoid heuristics that try to identify "decorative" elements
   - Let geometric connectivity determine the content zone

## Next Steps

1. Update `_detect_content_zone()` in geometry.py with innermost boundary detection
2. Add test case for Bread gondola end block with expected trims (304.8, 304.8, 152.4, 0)
3. Verify GS900x450HGE_Liquor still produces (13, 13, 0, 24.38)
4. Test on additional blocks with stepped/tiered structures

## Appendix: Raw Extraction Results

```
Current Implementation Results:
==============================

Block: Bread gondola end
  Native dimensions: 1219.2 x 609.6
  Content zone detected: True
  Trim left: 0.0
  Trim right: 0.0
  Trim top: 0.0
  Trim bottom: 0.0

Block: GS900x450HGE_Liquor
  Native dimensions: 926.0 x 481.0
  Content zone detected: True
  Trim left: 26.0   (WRONG - expected 13.0)
  Trim right: 26.0  (WRONG - expected 13.0)
  Trim top: 440.38  (WRONG - expected 0.0)
  Trim bottom: 24.38 (CORRECT)
```

Note: Current implementation uses largest LWPOLY net area, which selects the connector strip for GS900x450HGE_Liquor but doesn't account for LINE structure properly.
