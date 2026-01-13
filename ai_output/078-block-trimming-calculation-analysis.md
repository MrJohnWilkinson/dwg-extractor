# Block Trimming Calculation Analysis: *U22 (DD5X-12ULEP)

## Executive Summary

This report traces the complete calculation process for trimming suggestions on block *U22 (resolved to DD5X-12ULEP) extracted from `app/tests/assets/samples/sample-blocks.dxf`. The trim values are derived from content zone detection, which identifies the largest rectangular regions within the block and calculates the offset from the block's bounding box to the content zone bounding box.

## Table Summary

| Metric | Value | Calculation |
|--------|-------|-------------|
| Block Bounding Box Width | 147.5 | `max_x - min_x` from `_get_block_bounding_box()` |
| Block Bounding Box Height | 60.91 | `max_y - min_y` from `_get_block_bounding_box()` |
| Content Zone Width | 144.5 | `cz_max_x - cz_min_x` (union of 6 surviving polygons) |
| Content Zone Height | 45 | `cz_max_y - cz_min_y` (union of 6 surviving polygons) |
| Suggested Trim Left | 1.5 | `cz_min_x - block_min_x` |
| Suggested Trim Right | 1.5 | `block_max_x - cz_max_x` |
| Suggested Trim Top | 0.0 (empty) | `block_max_y - cz_max_y` = 60.91 - 45 - 15.91 = 0 |
| Suggested Trim Bottom | 15.91 | `cz_min_y - block_min_y` |
| Initial Polygon Count | 41 | From `_extract_paint_bucket_regions()` |
| Filtered Polygon Count | 6 | After side and area filtering |

**Verification**:
- Width: 1.5 + 144.5 + 1.5 = 147.5 ✓
- Height: 0 + 45 + 15.91 = 60.91 ✓

## Relevant Files

- **app/core/geometry.py:1634-1909** - `_detect_content_zone()` function - Main entry point for content zone detection and trim calculation
- **app/core/geometry.py:1186-1288** - `_extract_paint_bucket_regions()` - Extracts closed polygons using Shapely polygonize
- **app/core/geometry.py:349-538** - `_get_block_bounding_box()` - Calculates block extents including nested INSERTs
- **app/core/geometry.py:1577-1631** - `_calculate_net_areas()` - Computes net area (own area minus contained polygons)
- **app/core/extractor.py:1287-1336** - Block geometry analysis phase in `extract_blocks()`
- **app/core/types.py:195-231** - `ContentZoneData` TypedDict definition

## Sequence of Events

### Phase 1: Block Identification and Bounding Box

1. **Anonymous Block Resolution** (`extractor.py:1218-1236`)
   - Block `*U22` is identified as an anonymous dynamic block
   - XDATA is checked for `AcDbBlockRepBTag` application ID
   - Resolved to original name `DD5X-12ULEP`

2. **Bounding Box Calculation** (`geometry.py:349-538`)
   - Iterates through all entities in block definition
   - Processes LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, ELLIPSE, SPLINE, POINT entities
   - For nested INSERT entities, recursively calculates and transforms bounding boxes
   - Result: `(min_x, min_y, max_x, max_y)` where width=147.5, height=60.91

### Phase 2: Content Zone Detection

3. **Entity Count Pre-Check** (`geometry.py:1718-1725`)
   - Counts entities in block: 59 entities
   - Compares against `ENTITY_COUNT_THRESHOLD` (default: 30)
   - If exceeded, would skip content zone entirely

4. **Edge Count Estimation** (`geometry.py:1728-1744`)
   - Fast O(n) estimation via `_estimate_edge_count()`
   - Compares against `LINE_SEGMENT_THRESHOLD` (default: 30)
   - If exceeded, would skip region detection

5. **Paint Bucket Region Extraction** (`geometry.py:1186-1288`)
   - `_extract_all_edges()` collects all edges from:
     - LINE entities (direct)
     - LWPOLYLINE/POLYLINE (via `make_path()` + flattening)
     - CIRCLE, ARC, ELLIPSE, SPLINE (adaptive flattening)
     - HATCH boundary paths
   - **Precision Fix Snapping**: Coordinates snapped to grid using `precision_tolerance`
   - **Unary Union**: All edges merged via `unary_union()` to split at intersections
   - **Polygonize**: `polygonize()` finds all closed regions
   - Result: 41 polygons

### Phase 3: Polygon Filtering

6. **Curved Edge Filter** (`geometry.py:1766-1771`)
   - If `curved_filter_enabled`, removes polygons with detected curved edges
   - Uses `_polygon_has_curved_edges()` - detects 3+ consecutive small angular deviations

7. **Minimum Side Filter** (`geometry.py:1777-1795`)
   - Filters polygons by shortest straight side length
   - Only applies to 4-sided rectangles (complex polygons pass through)
   - Uses `calculate_shortest_straight_side()` which merges collinear edges

8. **Polygon Count Threshold** (`geometry.py:1812-1827`)
   - If remaining polygons > `POLYGON_COUNT_THRESHOLD` (default: 30), skip content zone

9. **Net Area Calculation** (`geometry.py:1577-1631`)
   - For each polygon, calculates net area = own area - contained polygons' areas
   - Uses Shapely `difference()` for accurate geometric subtraction
   - Handles "picture frame" scenarios (outer rectangle with inner cutout)

10. **Minimum Area Filter** (`geometry.py:1842-1856`)
    - Filters by NET area (not gross area)
    - Polygons below `min_area_filter` threshold removed

### Phase 4: Trim Value Calculation

11. **Content Zone Bounding Box** (`geometry.py:1876-1882`)
    - If single survivor: uses `_get_polygon_bbox()`
    - If multiple survivors (this case: 6): uses `_get_union_bounding_box()`
    - Calculates union bbox of all 6 surviving polygons

12. **Trim Value Computation** (`geometry.py:1884-1893`)
    ```python
    trim_left   = round(cz_min_x - block_min_x, 2)   # 1.5
    trim_right  = round(block_max_x - cz_max_x, 2)   # 1.5
    trim_top    = round(block_max_y - cz_max_y, 2)   # 0.0
    trim_bottom = round(cz_min_y - block_min_y, 2)   # 15.91
    ```

## Why Trim Top is Empty

The `trim_top` value of 0.0 indicates the content zone's top edge aligns exactly with the block's top edge. In Excel output, 0.0 values may display as empty cells depending on formatting rules. The calculation verifies:

- `block_max_y - cz_max_y = 0` means `cz_max_y = block_max_y`
- Content zone extends to the top of the block bounding box
- No trimming needed at the top

## Simple List Summary

- Block *U22 resolves to DD5X-12ULEP via XDATA lookup
- Block bounding box calculated: 147.5 x 60.91 units
- Paint bucket algorithm extracts 41 closed polygons from edges
- Side and area filters reduce to 6 qualifying polygons
- Content zone = union bounding box of 6 survivors: 144.5 x 45 units
- Trim values = offset from block bbox to content zone bbox
- Trim top = 0 because content zone touches block's top edge
