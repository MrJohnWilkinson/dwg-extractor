# Unified Trim Algorithm Analysis

## Executive Summary
Testing the proposed approaches from ai_output/012 and ai_output/013 against all blocks in sample-blocks.dxf reveals that **no single approach produces correct trim values for all blocks**. The "Innermost Connected LINE Boundary" approach (from 013) works for Bread gondola end, but GS900x450HGE_Liquor requires a hybrid approach. Polygon area calculations via the shoelace formula are already implemented and could be integrated into Step 4/5 of the current algorithm to filter boundary polygons and rank candidates.

## Table Summary

| Block | Expected L/R/T/B | Approach 1 (Largest LWPOLY) | Approach 2 (LINE+LWPOLY) | Approach 3 (Innermost LINE) | Approach 4 (Structural LINE) | Result |
|-------|------------------|------------------------------|---------------------------|------------------------------|-------------------------------|--------|
| GS900x450HGE_Liquor | 13/13/0/24.38 | 26/26/440/24 | 13/13/0/**0** | 13/13/0/**65** | 13/13/0/**65** | Partial |
| Bread gondola end | 304.8/304.8/152.4/0 | 0/0/0/0 | 0/0/0/0 | **304.8/304.8/152.4/0** | 0/0/50.8/0 | **Approach 3** |
| Bread gondola | 25.4-127/same/0/0 | 0/0/0/0 | 0/0/0/0 | 584/584/965/0 | 0/**25.4**/0/0 | None |
| AP #5-4 | 0/0/0/0 | **0/0/0/0** | **0/0/0/0** | N/A | **0/0/0/0** | All |
| Gcase(w1800) | 0/0-200/0/0 | 0/0/0/0 | 0/0/0/0 | N/A | 400/**200**/0/0 | Partial |

## Relevant Files
- `app/core/geometry.py:391-423` - `_shoelace_area()` - already implements polygon area calculation
- `app/core/geometry.py:487-499` - `_get_polygon_bbox()` - bounding box calculation
- `app/core/geometry.py:359-388` - `_extract_closed_lwpolylines()` - extracts closed LWPOLYLINEs
- `app/core/geometry.py:737-847` - `_detect_content_zone()` - current content zone detection
- `app/tests/assets/samples/sample-blocks.dxf` - test file with all blocks
- `app/tests/assets/samples/sample-blocks-actual-trim-values.xlsx` - expected trim values

## Block Geometry Summary

### Block Entity Analysis

| Block | LWPOLYs | LINEs | LWPOLY = Block? | Has LINE Rectangles |
|-------|---------|-------|-----------------|---------------------|
| GS900x450HGE_Liquor | 3 interior | 4 (3 structural + 1 baseline) | No | Partial (no bottom) |
| Bread gondola end | 1 boundary | 7 (tiered structure) | Yes | Yes (2 tiers) |
| Bread gondola | 1 boundary | 13 (section dividers) | Yes | No (H-LINEs too narrow) |
| AP #5-4 | 1 boundary | 4 (partition lines) | Yes | No |
| Gcase(w1800) | 1 boundary | 1 (vertical divider) | Yes | No |

### Key Observations

1. **GS900x450HGE_Liquor**: Unique structure with 3 interior LWPOLYs and structural LINEs that don't form a complete rectangle. Content zone requires combining LINE bounds (left/right/top) with LWPOLY bottom edge.

2. **Bread gondola end**: Tiered stepped structure with 3 horizontal LINE levels. Vertical LINEs at tier boundaries form complete rectangles. Innermost rectangle = smallest area.

3. **Bread gondola**: Vertical section dividers that span full block height. No enclosed rectangles. Expected trims (25.4, 76.2, 127) represent panel widths from the left edge.

4. **AP #5-4 & Gcase(w1800)**: Simple blocks where LWPOLY fills the entire block. LINEs are internal partitions, not boundaries.

## Approach Testing Results

### Approach 1: Largest LWPOLY Area (Current Implementation)

**Algorithm**: Select LWPOLY with largest net area as content zone.

| Block | Content Zone | Trims | Correct? |
|-------|--------------|-------|----------|
| GS900x450HGE_Liquor | (26, 24.38, 900, 40.62) | 26/26/440/24 | No - wrong left/right |
| Bread gondola end | (0, 0, 1219.2, 609.6) | 0/0/0/0 | No - selects boundary |
| Bread gondola | (0, 0, 1219.2, 1219.2) | 0/0/0/0 | No - selects boundary |
| AP #5-4 | (0, 0, 762, 4876.8) | 0/0/0/0 | Yes |
| Gcase(w1800) | (0, 0, 600, 1800) | 0/0/0/0 | Yes (one option) |

**Verdict**: Only works when LWPOLY defines actual content zone, not when it equals block boundary.

### Approach 2: LINE + Largest LWPOLY Union (From 012)

**Algorithm**: Union of all LINE bounding box with largest LWPOLY bounding box.

| Block | LINE bbox | Union Result | Trims | Correct? |
|-------|-----------|--------------|-------|----------|
| GS900x450HGE_Liquor | (13, 0, 913, 481) | (13, 0, 913, 481) | 13/13/0/0 | Partial - wrong bottom |
| Bread gondola end | (0, 0, 1219.2, 558.8) | = block | 0/0/0/0 | No |
| Bread gondola | (0, 0, 1193.8, 1219.2) | = block | 0/0/0/0 | No |

**Verdict**: Fails when LWPOLY equals block bbox. Needs boundary LWPOLY filtering.

### Approach 3: Innermost Connected LINE Boundary (From 013)

**Algorithm**: Find smallest complete rectangle formed by horizontal + vertical LINEs.

| Block | Rectangles Found | Innermost | Trims | Correct? |
|-------|------------------|-----------|-------|----------|
| GS900x450HGE_Liquor | 1 (incomplete bottom) | (13, 65, 913, 481) | 13/13/0/65 | Partial |
| Bread gondola end | 2 tiers | (304.8, 0, 914.4, 457.2) | 304.8/304.8/152.4/0 | **Yes** |
| Bread gondola | 4 (small internal) | (584.2, 0, 635, 254) | 584/584/965/0 | No |

**Verdict**: Works best for tiered structures with complete LINE rectangles.

### Approach 4: Structural LINE bbox Only

**Algorithm**: Bounding box of non-baseline LINEs (excluding y=0 LINEs).

| Block | Structural LINE bbox | Trims | Correct? |
|-------|---------------------|-------|----------|
| GS900x450HGE_Liquor | (13, 65, 913, 481) | 13/13/0/65 | Partial |
| Bread gondola end | (0, 0, 1219.2, 558.8) | 0/0/50.8/0 | Partial (top=50.8 valid) |
| Bread gondola | (0, 0, 1193.8, 1219.2) | 0/25.4/0/0 | Partial (right=25.4 valid) |

**Verdict**: Provides some correct values but not complete solution.

## Polygon Area Integration

### Current Implementation

The shoelace formula is already implemented in `app/core/geometry.py:391-423`:

```python
def _shoelace_area(polygon: Polygon) -> float:
    """Calculate the area of a polygon using the shoelace formula."""
    n = len(polygon)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += polygon[i][0] * polygon[j][1]
        area -= polygon[j][0] * polygon[i][1]
    return abs(area) / 2.0
```

### Where Area Fits in Algorithm (From 010)

| Step | Current Use | Proposed Enhancement |
|------|-------------|---------------------|
| Step 2: Extract LWPOLYLINEs | None | Calculate area, flag boundary (area ≈ block area) |
| Step 3: Extract LINE Cycles | None | Calculate rectangle areas |
| Step 4: Calculate Net Areas | Rank by largest | Filter boundary LWPOLYs, rank LINE rectangles by smallest |
| Step 5: Identify Content Zone | Select largest net area | Select based on block type detection |

### Area-Based Filtering Logic

```python
def _is_boundary_polygon(polygon_bbox, block_bbox, tolerance=0.01):
    """Check if polygon fills entire block (boundary, not content)."""
    poly_area = (polygon_bbox[2] - polygon_bbox[0]) * (polygon_bbox[3] - polygon_bbox[1])
    block_area = (block_bbox[2] - block_bbox[0]) * (block_bbox[3] - block_bbox[1])
    return abs(poly_area - block_area) / block_area < tolerance

def _detect_content_zone_v2(block_def, block_bbox):
    # Step 1: Extract and classify LWPOLYs
    lwpolys = _extract_closed_lwpolylines(block_def)
    interior_lwpolys = [p for p in lwpolys
                        if not _is_boundary_polygon(_get_polygon_bbox(p), block_bbox)]

    # Step 2: Extract LINE rectangles
    line_rectangles = _find_line_rectangles(block_def)  # Returns sorted by area

    # Step 3: Selection logic
    if line_rectangles:
        # Prefer innermost LINE rectangle
        return line_rectangles[0]  # Smallest area
    elif interior_lwpolys:
        # Fall back to largest interior LWPOLY
        return max(interior_lwpolys, key=_shoelace_area)
    else:
        # No content zone detected
        return block_bbox
```

### Area Calculations for Test Blocks

| Block | Block Area | Content Zone Area | Ratio | Interpretation |
|-------|------------|-------------------|-------|----------------|
| GS900x450HGE_Liquor | 445,406 | 410,963 (expected) | 92.3% | Nearly full block |
| Bread gondola end (tier 1) | 743,224 | 278,668 | 37.5% | Innermost tier |
| Bread gondola end (tier 2) | 743,224 | 464,515 | 62.5% | Middle tier |
| Bread gondola | 1,486,449 | Varies | Varies | Section-based |
| AP #5-4 | 3,716,122 | Same | 100% | Full block |
| Gcase(w1800) | 1,080,000 | Same | 100% | Full block |

## Recommendations

### 1. Implement Block Type Detection

Different block structures require different algorithms:

| Block Type | Detection Criteria | Algorithm |
|------------|---------------------|-----------|
| **Type A: Interior LWPOLYs** | Multiple LWPOLYs, none at boundary | Hybrid: LINE bbox + LWPOLY edges |
| **Type B: Tiered Structure** | LWPOLY at boundary + LINE rectangles | Innermost LINE rectangle |
| **Type C: Section Dividers** | LWPOLY at boundary + vertical LINEs only | V-LINE positions from edges |
| **Type D: Full Boundary** | Single LWPOLY = block bbox | No trimming (0/0/0/0) |

### 2. Hybrid Algorithm for GS900x450HGE_Liquor (Type A)

```python
def _detect_content_zone_type_a(block_def, block_bbox):
    """For blocks with interior LWPOLYs and structural LINEs."""
    # Get structural LINE bbox (left/right/top)
    line_bbox = _get_structural_line_bbox(block_def, block_bbox)

    # Get bottom from largest interior LWPOLY
    interior_lwpolys = [p for p in lwpolys if not _is_boundary(p)]
    if interior_lwpolys:
        largest = max(interior_lwpolys, key=_shoelace_area)
        lwpoly_bbox = _get_polygon_bbox(largest)

        # Combine: LINE for left/right/top, LWPOLY for bottom
        return (
            line_bbox[0],      # left from LINE
            lwpoly_bbox[1],    # bottom from LWPOLY
            line_bbox[2],      # right from LINE
            line_bbox[3]       # top from LINE
        )
```

### 3. Innermost Rectangle Selection (Type B)

For Bread gondola end, the current approach 3 works. Ensure selection of smallest area rectangle:

```python
def _select_content_zone_type_b(line_rectangles):
    """For blocks with tiered LINE structures."""
    if not line_rectangles:
        return None
    # Sort by area ascending, select smallest (innermost)
    line_rectangles.sort(key=lambda r: _rectangle_area(r))
    return line_rectangles[0]
```

### 4. Section Divider Detection (Type C)

For Bread gondola, detect vertical section lines:

```python
def _detect_section_trims(v_lines, block_bbox):
    """For blocks with vertical section dividers."""
    left_x = block_bbox[0]
    right_x = block_bbox[2]

    # Find V-LINEs near left/right edges
    left_dividers = sorted([v[0] for v in v_lines if v[0] < (right_x + left_x) / 2])
    right_dividers = sorted([v[0] for v in v_lines if v[0] > (right_x + left_x) / 2], reverse=True)

    # Expected trims are distances from edges to first dividers
    trim_left = left_dividers[0] - left_x if left_dividers else 0
    trim_right = right_x - right_dividers[0] if right_dividers else 0

    return (trim_left, trim_right, 0, 0)
```

## Next Steps

1. **Implement block type detection** - Classify blocks by geometry pattern before applying trim algorithm
2. **Add boundary polygon filtering** - Use area comparison to exclude LWPOLYs that equal block bbox
3. **Integrate LINE rectangle detection** - Use approach 3 logic for tiered structures
4. **Create hybrid algorithm for Type A blocks** - Combine LINE bbox with LWPOLY edges
5. **Add configuration option** - Allow user to select trim calculation strategy per block type
6. **Extend test coverage** - Add unit tests for each block type with expected trim values

## Appendix: Raw Test Results

### GS900x450HGE_Liquor
```
Block bbox: (0.0, 0.0, 926.0, 481.0)
Expected: left=13, right=13, top=0, bottom=24.375

Best partial match: Approach 2/3/4 get left=13, right=13, top=0
Missing: bottom=24.38 requires LWPOLY edge data
Required approach: Hybrid (LINE bbox + LWPOLY min_y)
```

### Bread gondola end
```
Block bbox: (0.0, 0.0, 1219.2, 609.6)
Expected (option A): left=304.8, right=304.8, top=152.4, bottom=0

Approach 3 result: 304.8/304.8/152.4/0 - EXACT MATCH
Found 2 LINE rectangles:
  - Tier 1: (304.8, 0, 914.4, 457.2) area=278,668 - SELECTED (smallest)
  - Tier 2: (152.4, 0, 1066.8, 508) area=464,515
```

### Bread gondola
```
Block bbox: (0.0, 0.0, 1219.2, 1219.2)
Expected: left=25.4/76.2/127, right=same, top=0, bottom=0

No approach works. V-LINE positions from left edge:
  0, 25.4, 76.2, 127 (expected trim values)

Requires section-divider detection algorithm.
```

### AP #5-4 and Gcase(w1800)
```
Both: LWPOLY fills entire block bbox
Expected: 0/0/0/0 (or right=200 for Gcase)
All approaches return 0/0/0/0 - CORRECT for baseline
```
