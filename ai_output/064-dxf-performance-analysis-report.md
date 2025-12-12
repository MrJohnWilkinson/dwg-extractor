# DXF Block Extractor Performance Analysis Report

## Executive Summary
Analysis of processing logs for `2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf` reveals that **content zone detection** is the primary performance bottleneck. Specific blocks are taking 35-133+ seconds due to geometric complexity in the `_extract_paint_bucket_regions()` and `_calculate_net_areas()` functions. The **gap bridge feature** (currently enabled) adds significant overhead, and the **polygon count threshold check occurs too late** in the pipeline.

## Table Summary

| Block Name | Duration | Root Cause | Action |
|------------|----------|------------|--------|
| `FrontEnd_Checkout_BeltedTACO_MerchGA` | **133 sec** | Complex geometry, many polygons | Lower thresholds |
| `FreshProduce_ScoopWeighPottles_Wood` | **64 sec** | Complex paint-bucket regions | Lower thresholds |
| `GM_MobileBin` (x4 instances) | **47-54 sec** each | 668-699 polygons, skipped after processing | Check earlier |
| `Stockroom_Hook_SafetyVestRail` | **35 sec** | Complex geometry | Lower thresholds |
| `Grocery_GondolaACO_Combined` | **24 sec** | Large gondola geometry | Expected |
| `Railing - 200mm High Post` (x20+ instances) | **3 sec** each | Small but complex geometry | Consider caching |

**Cumulative Impact:**
- GM_MobileBin variants: ~4 × 50s = **200+ seconds** (then skipped anyway)
- Railing posts: ~20 × 3s = **60+ seconds**
- Major blocks: ~133 + 64 + 35 + 24 = **256 seconds**
- **Total estimated slowdown: 8-10+ minutes** for a file that should process in 1-2 minutes

## Relevant Files

- `app/core/geometry.py:1052-1277` - `_detect_content_zone()` main entry point for content zone detection
- `app/core/geometry.py:707-783` - `_extract_paint_bucket_regions()` expensive region extraction with unary_union and polygonize
- `app/core/geometry.py:995-1049` - `_calculate_net_areas()` O(n²) containment checks
- `app/core/constants.py:169-185` - Performance threshold constants (POLYGON_COUNT_THRESHOLD, LINE_SEGMENT_THRESHOLD, ENTITY_COUNT_THRESHOLD)
- `app/core/settings.py:52-88` - Settings sections including performance thresholds

## Detailed Bottleneck Analysis

### 1. The Gap Bridge Feature (Major Impact)

**Current Settings from Log:**
```
gap_bridge_enabled=True, gap_bridge_amount=3.0
precision_fix_enabled=False
```

When `gap_bridge_enabled=True`, `_extract_paint_bucket_regions()` executes:
```python
# Line 762-765 in geometry.py
if gap_bridge_tolerance > 0:
    all_edges_geom = unary_union(edges)  # EXPENSIVE: unions ALL edges
    edges = [snap(e, all_edges_geom, gap_bridge_tolerance) for e in edges]  # O(n) snaps
```

**Impact:** For a block with 1000 edges, this performs:
- 1 expensive `unary_union()` operation
- 1000 `snap()` operations against the complex union geometry

**Recommendation:** Disable gap bridge (`gap_bridge_enabled=False`) unless specifically needed for drawings with known gaps.

### 2. Polygon Threshold Check Occurs Too Late

**Current Flow in `_detect_content_zone()`:**
```
1. UNIT 1: entity_count check (fast, O(n))           ✓ Line 1128
2. UNIT 2: edge count estimation (fast, O(n))        ✓ Line 1137
3. _extract_paint_bucket_regions()                   ⚠️ EXPENSIVE - Line 1156
4. polygon_count_threshold check                     ❌ TOO LATE - Line 1191
5. _calculate_net_areas()                            ⚠️ O(n²) - Line 1209
```

**Problem:** The GM_MobileBin blocks take ~50 seconds each in `_extract_paint_bucket_regions()`, then get skipped because they have 668-699 polygons (> 500 threshold). The expensive work already ran!

### 3. The `unary_union` + `polygonize` Operations

In `_extract_paint_bucket_regions()` (lines 768-773):
```python
merged = unary_union(edges)  # Splits at all intersections
line_segments = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
polygons = list(polygonize(line_segments))  # Finds all closed regions
```

These Shapely GEOS operations are inherently expensive for complex geometry. The time scales with:
- Number of edges
- Number of intersection points
- Geometric complexity (many small regions)

### 4. O(n²) Net Area Calculation

`_calculate_net_areas()` (lines 1030-1041):
```python
for i, (poly, shapely_poly) in enumerate(zip(polygons, shapely_polys)):
    for j, other in enumerate(shapely_polys):
        if i != j and shapely_poly.contains(other):
            net_poly = net_poly.difference(other)
```

For 500 polygons: **250,000 containment checks**. This is bounded by the threshold but still significant.

## Current Thresholds vs Recommended

| Threshold | Current | Problem | Recommended |
|-----------|---------|---------|-------------|
| `entity_count_threshold` | 1000 | Good, checked early | 1000 (keep) |
| `line_segment_threshold` | 5000 | Good, checked early | 5000 (keep) |
| `polygon_count_threshold` | 500 | Checked too late | **300-400** |

## Settings Already Available

These settings can be adjusted in the Advanced Settings modal or via `settings.json`:

| Setting | Current | Effect | Speed Impact |
|---------|---------|--------|--------------|
| `gap_bridge_enabled` | `True` | Bridges 3mm gaps | **HIGH** - disable for speed |
| `gap_bridge_amount` | `3.0` | Gap size to bridge | Lower = faster |
| `polygon_count_threshold` | `500` | Max polygons | Lower = faster (but less data) |
| `line_segment_threshold` | `5000` | Max edges | Lower = faster |
| `entity_count_threshold` | `1000` | Max entities | Lower = faster |
| `min_area_filter_enabled` | `False` | Filter small polygons | Enable for speed |
| `min_side_filter_enabled` | `False` | Filter by side length | Enable for speed |

## Processing Step Timing Breakdown

Based on log analysis, estimated time per step for complex blocks:

```
Step                              | Fast Block | Complex Block
----------------------------------|------------|---------------
Entity count check                | <1ms       | <1ms
Edge count estimation             | <1ms       | <1ms
_extract_all_edges()              | ~100ms     | ~500ms
gap_bridge snap (if enabled)      | ~500ms     | ~5-30 sec
unary_union()                     | ~100ms     | ~10-60 sec
polygonize()                      | ~100ms     | ~5-30 sec
_calculate_net_areas() O(n²)      | ~100ms     | ~1-10 sec
----------------------------------|------------|---------------
TOTAL                             | ~1 sec     | ~30-130 sec
```

## Root Cause Summary

1. **gap_bridge_enabled=True** adds massive overhead for complex blocks
2. **polygon_count_threshold** check happens after expensive operations
3. **Repeated processing** of identical block definitions (e.g., 20+ Railing posts)
4. **No polygon count estimation** before running `_extract_paint_bucket_regions()`

## Recommendations

### Immediate Actions (No Code Changes)

1. **Disable gap bridge:** Set `gap_bridge_enabled=False` in settings
   - Expected improvement: **50-70% faster** for complex files

2. **Enable filters:** Set `min_side_filter_enabled=True` with `min_side_filter_amount=10`
   - Filters tiny polygons early, reducing O(n²) work

3. **Lower polygon threshold:** Set `polygon_count_threshold=300`
   - Skips complex blocks earlier (still after expensive ops though)

### Code Improvements (Future)

1. **Move polygon count estimation earlier:** Add heuristic before `_extract_paint_bucket_regions()`
   ```python
   # Estimate polygon count from edge count (heuristic: edges/3 ≈ polygons)
   estimated_polygon_count = estimated_edge_count // 3
   if estimated_polygon_count > polygon_count_threshold:
       return _empty_content_zone_data()  # Skip before expensive ops
   ```

2. **Cache content zone results:** Same block definition = same content zone
   - Would eliminate ~60 seconds for the 20+ Railing posts

3. **Spatial indexing for net area:** Use R-tree for O(n log n) containment checks
   - Would reduce 250,000 checks to ~2,500 for 500 polygons

## Next Steps

1. **Test with gap_bridge disabled:** Run the same file with `gap_bridge_enabled=False`
2. **Profile specific blocks:** Add timing instrumentation to identify exact bottlenecks
3. **Consider block definition caching:** Track unique block definitions to avoid reprocessing
4. **Evaluate polygon count estimation:** Add pre-check before expensive operations

## Appendix: Problematic Blocks Timeline

```
Time        Block                                    Duration
12:43:24 -> 12:43:59  Stockroom_Hook_SafetyVestRail         35s
12:44:01 -> 12:45:05  FreshProduce_ScoopWeighPottles_Wood   64s
12:45:26 -> 12:45:50  Grocery_GondolaACO_Combined           24s
12:46:10 -> 12:47:00  GM_MobileBin (1st, skipped)           50s
12:47:22 -> 12:49:35  FrontEnd_Checkout_BeltedTACO_MerchGA  133s ← WORST
12:50:22 -> 12:51:09  GM_MobileBin (2nd, skipped)           47s
12:51:09 -> 12:51:58  GM_MobileBin (3rd, skipped)           49s
12:51:58 -> 12:52:52  GM_MobileBin (4th, skipped)           54s
```

Plus ~20 instances of `Railing - 200mm High Post` at 3 seconds each = 60+ seconds.
