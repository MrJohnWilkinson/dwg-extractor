# Shapely `unary_union` Analysis: T-Junctions AND Crossing Intersections

## Executive Summary

**Critical Finding:** Shapely's `unary_union()` handles BOTH T-junctions AND crossing intersections automatically. The current implementation in `geometry.py` is missing the `unary_union()` call before `polygonize()`, which is why polygon detection fails for complex blocks. No custom T-junction or crossing detection code is needed - just add one line: `merged = unary_union(lines)`.

## Table Summary

| Scenario | Without `unary_union` | With `unary_union` | Status |
|----------|----------------------|-------------------|--------|
| Crossing Lines (X pattern) | 0 polygons | Splits into 4 segments | Handled |
| T-Junction (divider in rect) | 1 polygon (wrong) | 2 polygons (correct) | Handled |
| Both (grid pattern) | 1 polygon (wrong) | 6 polygons (correct) | Handled |
| **Current Implementation** | **Missing `unary_union`** | **Needs single-line fix** | **Bug** |

## Relevant Files

- `app/core/geometry.py:526-573` - `_extract_line_cycles()` function that needs the fix. Currently calls `polygonize(lines)` directly without `unary_union()`.
- `ai_output/017-polygon-detection-validation-all-blocks.md` - Validation report showing AP #5-4 failed without crossing detection.
- `ai_output/025-full-paint-bucket-implementation-plan.md` - Previous plan that overcomplicated the solution (custom T-junction detection not needed).

## Test Results

### Test 1: Crossing Lines (X Pattern)

Two diagonal lines crossing in the center:
```
Direct polygonize: 0 polygons
After unary_union: 4 segments (lines split at crossing)
Polygonize after union: 0 polygons (no closed region - expected)
```

**Result:** `unary_union()` correctly splits lines at interior crossing points.

### Test 2: T-Junction (Rectangle with Divider)

Rectangle (4 lines) + vertical divider touching top/bottom at midpoints:
```
Direct polygonize: 1 polygon (WRONG - only finds outer rectangle)
After unary_union: 7 segments (divider endpoints split the rect edges)
Polygonize after union: 2 polygons (CORRECT - left and right halves)
```

**Result:** `unary_union()` correctly handles T-junctions where endpoints touch line interiors.

### Test 3: Both Crossing AND T-Junction (Grid)

Rectangle + 2 horizontal lines + 1 vertical divider (crossing the horizontals):
```
Direct polygonize: 1 polygon (WRONG)
After unary_union: 17 segments (all split points detected)
Polygonize after union: 6 polygons (CORRECT)
```

**Result:** `unary_union()` handles the exact AP #5-4 pattern that report 017 identified as failing.

## Current Implementation Bug

**File:** `app/core/geometry.py` lines 562-563

```python
# CURRENT (INCORRECT):
polygons = list(polygonize(lines))

# SHOULD BE:
merged = unary_union(lines)
line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
polygons = list(polygonize(line_segments))
```

## Why Custom Detection is NOT Needed

| Report 025 Proposed | Actual Solution |
|---------------------|-----------------|
| Custom `_find_t_junctions()` function | Not needed - `unary_union()` handles it |
| Custom `_split_lines_at_points()` function | Not needed - `unary_union()` handles it |
| New `T_JUNCTION_EDGE_THRESHOLD` constant | Not needed - `unary_union()` is O(n log n) |
| O(n^2) custom T-junction detection | Replaced by O(n log n) GEOS operation |

## Performance Comparison

| Approach | Complexity | Implementation Effort |
|----------|------------|----------------------|
| Custom T-junction + crossing detection | O(n^2) | ~100 lines of code |
| Shapely `unary_union()` | O(n log n) | 3 lines of code |

## The Fix

```python
def _extract_line_cycles(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    # Collect all LINE segments as LineStrings
    lines: list[LineString] = []
    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            lines.append(LineString([(start.x, start.y), (end.x, end.y)]))

    if not lines:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Cycle detection aborted")

    # FIX: Use unary_union to split at T-junctions AND crossing points
    merged = unary_union(lines)
    if merged.is_empty:
        return []

    # Handle both single LineString and MultiLineString
    line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]

    # Polygonize now works correctly with split segments
    polygons = list(polygonize(line_segments))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} LINE cycles via polygonize")
    return result
```

## Recommendations

1. **Simplify Report 025**: The custom T-junction detection plan is unnecessary. Replace with `unary_union()` fix.

2. **Immediate Fix**: Add 4 lines to `_extract_line_cycles()` to use `unary_union()` before `polygonize()`.

3. **Keep Existing Thresholds**: `LINE_SEGMENT_THRESHOLD=5000` is still appropriate since `unary_union()` is O(n log n).

4. **Remove Report 025 T-Junction Code**: The proposed custom detection code is not needed.

## Next Steps

1. Update `app/core/geometry.py:_extract_line_cycles()` with the 4-line fix
2. Run validation against sample-blocks.dxf to verify AP #5-4 now detects 8 polygons
3. Run full test suite: `uv run pytest app/tests/`
4. Update report 025 to note this simpler solution

## Conclusion

**Answer to the user's question:** T-junction processing alone is NOT sufficient (as shown in report 017 with AP #5-4). Both T-junction AND crossing intersection detection ARE required. However, **Shapely already handles both** via `unary_union()` - no custom code needed. The current implementation bug is simply that `unary_union()` is not being called before `polygonize()`.
