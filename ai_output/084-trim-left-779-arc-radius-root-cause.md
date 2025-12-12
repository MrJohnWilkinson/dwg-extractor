# Block Suggested Trim Left 779: ARC Radius Root Cause Analysis

## Executive Summary

The `Block Suggested Trim Left` value of 779 for `Refrigeration_Frozen_Hussmann_PGL_2050H - 5 Door-82274016-GROUND FFL` is caused by an ARC entity centered at x≈0 with radius=779 that extends the block's bounding box to x=-779. The surviving polygons (after min_area_filter=50000) start at x=0, so trim_left = 0 - (-779) = 779. The value 779 equals the ARC radius, not a vertical intersection point.

## Table Summary

| Calculation Step | Value | Source |
|------------------|-------|--------|
| block_min_x | -779 | ARC left extent (center_x - radius = 0 - 779) |
| block_max_x | 3905 | Rightmost geometry |
| cz_min_x | 0 | Leftmost surviving polygon |
| cz_max_x | 3905 | Union of surviving polygons |
| **trim_left** | **779** | cz_min_x - block_min_x = 0 - (-779) |
| trim_right | 0 | block_max_x - cz_max_x = 3905 - 3905 |

### Key Entities Affecting Trim Calculation

| Entity Type | Location | Radius | Effect on Bounding Box |
|-------------|----------|--------|------------------------|
| ARC #1 | center x≈0 | 779 | Extends block_min_x to **-779** |
| ARC #2 | center x=781 | 779 | Contributes x=[2, 1560] |
| ARC #3 | center x=1562 | 779 | Contributes x=[783, 2341] |
| ARC #4 | center x=2343 | 779 | Contributes x=[1564, 3122] |
| ARC #5 | center x=3124 | 779 | Contributes x=[2345, 3903] |
| LINE entities | starts at x=-50 | - | Forms polygon area=48000 (filtered out) |

### Polygon Filtering Impact

| Polygon Location | Area | Min Area Filter | Result |
|------------------|------|-----------------|--------|
| x=-50 to x=0 | 48,000 | 50,000 | **FILTERED OUT** |
| x=0 to x=3905 | 3,466,927 | 50,000 | Survives |
| Other large polygons | >50,000 | 50,000 | Survives (10 total) |

## Relevant Files

- **`app/core/geometry.py:179-266`** (`_get_block_bounding_box`): Uses full circle extents for ARC entities (center ± radius), which extends block bbox to -779.

- **`app/core/geometry.py:1177-1449`** (`_detect_content_zone`): Calculates `trim_left = cz_min_x - block_min_x` at line 1426.

- **`app/core/geometry.py:732-834`** (`_extract_paint_bucket_regions`): Creates polygons from flattened ARCs and LINE entities via `polygonize()`.

- **`app/tests/assets/samples/sample-blocks.dxf`**: Contains the block with 162 LINE entities and 5 ARC entities.

## Step-by-Step Calculation Walkthrough

### Step 1: Block Bounding Box Calculation

The block contains 167 entities (162 LINEs + 5 ARCs). The bounding box is calculated:

```
For each ARC: bbox extends from (center_x - radius) to (center_x + radius)

ARC at center=(0, -953), radius=779:
  bbox_left = 0 - 779 = -779  ← This becomes block_min_x

LINE entities:
  Leftmost LINE endpoint at x = -50
  (But -50 > -779, so doesn't affect block_min_x)

Result: block_min_x = -779, block_max_x = 3905
```

### Step 2: Paint Bucket Region Extraction

With settings `gap_bridge=3.0`, `skip_curved_entities=False`:

```
1. Extract edges from all entities (LINE + ARC)
2. ARCs flattened to line segments (~18 segments each)
3. unary_union() merges edges, splits at intersections
4. polygonize() finds 99 closed regions
```

### Step 3: Min Area Filtering (50,000)

```
Polygon at x=[-50, 0]:
  area = 48,000 < 50,000 → FILTERED OUT

Surviving polygons (10 total):
  - All have min_x >= 0
  - Largest: area = 3,466,927 at x=[0, 3905]
```

### Step 4: Content Zone Calculation

```
survivors = 10 polygons with area >= 50,000
union_bbox = get_union_bounding_box(survivors)

cz_min_x = 0    (leftmost surviving polygon starts at x=0)
cz_max_x = 3905
```

### Step 5: Trim Value Calculation

```
trim_left = cz_min_x - block_min_x
         = 0 - (-779)
         = 779 ← MATCHES THE ARC RADIUS
```

## Why 779 Equals the ARC Radius

The coincidence that trim_left = ARC_radius is NOT random:

1. **ARC centered at x≈0**: The ARC's center is at the same X-coordinate as the content zone's left edge
2. **ARC extends block bbox left**: `block_min_x = center_x - radius = 0 - 779 = -779`
3. **Content zone starts at x=0**: The surviving polygons don't extend left of x=0
4. **Therefore**: `trim_left = 0 - (-779) = 779 = radius`

This is a geometric consequence: when an ARC is centered at the content zone boundary and extends the block bbox by its radius, the trim value equals the radius.

## Why No Intersection at 779

The user correctly observed there's no vertical intersection at x=779. This is because:

- **779 is a DISTANCE, not a coordinate**
- The trim_left value represents the horizontal distance from block_min_x to cz_min_x
- Block_min_x = -779 (ARC left extent)
- cz_min_x = 0 (content zone left edge)
- Distance = 0 - (-779) = 779

## Related Tests

| Test File | Test Class | Relevance |
|-----------|------------|-----------|
| `test_content_zone.py` | `TestTrimValueCalculation` | Tests trim value derivation |
| `test_content_zone.py` | `TestPolygonFiltering` | Tests min_area_filter behavior |
| `test_content_zone.py` | `TestCurvedFilterIntegration` | Tests ARC handling in content zone |
| `test_extractor_prefilters.py` | `TestExtractBlocksSkipCurvedEntities` | Tests excluding ARCs |

## Recommendations

### Option 1: Reduce min_area_filter
Lower to 48000 or below to include the polygon at x=-50. This would change:
- cz_min_x = -50 (instead of 0)
- trim_left = -50 - (-779) = 729

### Option 2: Use "actual" ARC bounding box
Currently ARCs use full-circle extents. Implementing actual angular-extent bbox would reduce false bbox expansion. This is a code change in `_get_block_bounding_box()`.

### Option 3: Skip curved entities
Enable `skip_curved_entities=True` to exclude ARCs from bounding box calculation entirely. This would change block_min_x from -779 to -50.

## Next Steps

1. **Verify expectation**: Determine if trim_left should be 0, 50, 729, or 779 based on user intent.

2. **If expecting smaller trim**: Lower min_area_filter or use skip_curved_entities.

3. **If ARC bbox is problematic**: Consider implementing actual ARC angular-extent bounding box instead of full-circle approximation.
