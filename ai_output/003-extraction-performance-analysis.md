# DXF Extraction Performance Analysis

## Executive Summary

The extraction process is extremely slow due to O(n³) algorithmic complexity in the content zone detection phase. A single block with 102 polygons consumed **140.7 seconds** (2.3 minutes), while the entire extraction was aborted after 18 minutes. The primary bottlenecks are the `_calculate_net_areas` and `_extract_line_cycles` functions in `geometry.py`.

## Table Summary

| Block Name | Polygons | LINE Segments | Time (s) | Issue |
|------------|----------|---------------|----------|-------|
| GUB-460.fotocelle | 102 | 5 | **140.7** | O(n³) containment analysis |
| MARLIN52 2D.plan | 31+ | 967 | Aborted | O(n²) adjacency graph + O(n³) cycle detection |
| BIS 1065 m.vaskeprogram 2D | ~2 | 849 | 0.075 | Fast due to few closed cycles |
| Typical blocks | 1-12 | <100 | 0.001-0.044 | Acceptable |

**Time breakdown from logs:**
- DXF file loading: 1.645s (acceptable)
- Block analysis (to abort): ~15-18 minutes (unacceptable)
- User aborted at: 13:41:38 after starting at 13:23:33

## Relevant Files

- **app/core/geometry.py** - Contains the O(n³) algorithms:
  - `_calculate_net_areas()` - lines 701-797 - Primary bottleneck
  - `_extract_line_cycles()` - lines 554-698 - Secondary bottleneck
  - `_polygon_contains_polygon()` - lines 403-426 - Called O(n²) times
  - `_detect_content_zone()` - lines 800-981 - Orchestrates the slow functions

- **app/core/extractor.py** - Main extraction loop, calls geometry functions per block definition

- **Log files analyzed:**
  - `app/tests/assets/samples/05-02 MASTERTEGNING SPAR SUPERMARKED - 670 M2 - 280525_debug_20251205_132333.log` (11,976 lines)
  - `app/tests/assets/samples/sample.log` (1,297 lines)

## Root Cause Analysis

### 1. O(n³) Net Area Calculation (Primary Bottleneck)

The `_calculate_net_areas` function has three nested loops for containment analysis:

```python
# geometry.py:763-787 - O(n³) complexity
for i in range(n):  # O(n)
    for j in range(n):  # O(n)
        if _polygon_contains_polygon(polygons[i], polygons[j]):  # O(vertices)
            for k in range(n):  # O(n) - check for intermediate containers
                if _polygon_contains_polygon(polygons[i], polygons[k]) and
                   _polygon_contains_polygon(polygons[k], polygons[j]):
```

For 102 polygons: **102³ = 1,061,208 iterations** with polygon containment checks.

### 2. O(n²) Line Cycle Adjacency Building

The `_extract_line_cycles` function builds an adjacency graph with tolerance-based vertex merging:

```python
# geometry.py:600-609 - O(n²) for vertex canonicalization
def get_canonical(point):
    for existing in canonical:  # O(n) per call
        if abs(existing[0] - point[0]) <= epsilon...
```

For 967 LINE segments (1,934 points): **~3.7 million comparisons** just for canonicalization.

### 3. Excessive Logging Overhead

Every entity processed generates DEBUG log entries:
```
13:23:36.597 [DEBUG] Bounding box: processing entity type LINE
```

The sample block `GUB-460.fotocelle` alone generates 100+ log lines for bounding box processing.

## Recommendations

### High Impact (Recommended)

| Priority | Optimization | Expected Speedup | Effort |
|----------|-------------|------------------|--------|
| 1 | Add polygon count threshold (skip if > 30) | 100x+ for complex blocks | Low |
| 2 | Use spatial indexing (R-tree) for containment | 10-100x for large n | Medium |
| 3 | Cache bounding boxes for early rejection | 5-10x | Low |
| 4 | Make content zone detection optional | N/A (skip entirely) | Low |

### Medium Impact

| Priority | Optimization | Expected Speedup | Effort |
|----------|-------------|------------------|--------|
| 5 | Use hashable grid for vertex canonicalization | 10x for line cycles | Low |
| 6 | Limit line cycle detection to reasonable bounds | Variable | Low |
| 7 | Reduce DEBUG logging granularity | 2-5% overall | Low |

### Low Impact

| Priority | Optimization | Expected Speedup | Effort |
|----------|-------------|------------------|--------|
| 8 | Parallelize block analysis | Linear with cores | Medium |
| 9 | Use numpy for polygon operations | 2-3x | High |

## Next Steps

### Immediate (Quick Wins)

1. **Add threshold to skip complex blocks**:
   ```python
   # In _detect_content_zone
   if len(all_shapes) > 30:
       logger.warning(f"Skipping content zone: {len(all_shapes)} shapes exceeds threshold")
       return ContentZoneData(...)  # empty result
   ```

2. **Use bounding box pre-filtering**:
   ```python
   def _polygon_contains_polygon_fast(outer, inner):
       outer_bbox = _get_polygon_bounding_box(outer)
       inner_bbox = _get_polygon_bounding_box(inner)
       # Quick rejection if bounding boxes don't contain
       if not _bbox_contains_bbox(outer_bbox, inner_bbox):
           return False
       return _polygon_contains_polygon(outer, inner)  # Full check
   ```

3. **Add configuration option to disable content zone detection**:
   ```python
   # In extract_blocks()
   if not config.enable_content_zone_detection:
       block_trimming_data[effective_name] = {..., 'content_zone_detected': False}
   ```

### Short-term

4. **Replace O(n²) vertex canonicalization with spatial hashing**:
   ```python
   def get_canonical(point, grid_size=0.01):
       grid_key = (round(point[0] / grid_size), round(point[1] / grid_size))
       return canonical_grid.setdefault(grid_key, point)
   ```

### Long-term

5. **Implement R-tree spatial indexing** using `rtree` or `shapely` for polygon containment queries
6. **Consider Numba/Cython** for hot loops in polygon operations
