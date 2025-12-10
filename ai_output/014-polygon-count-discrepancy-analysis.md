# Polygon Count Discrepancy Analysis: SPAR Gulv 900x600 H1860

## Executive Summary
The block `SPAR Gulv 900x600 H1860` reports 5 polygons instead of the expected 7 due to a floating-point precision bug in the coordinate snapping order. The horizontal LINE entities at Y=-535 and Y=535 have endpoint coordinates with nanometer-scale precision errors (~4e-9), and the current code applies `snap()` AFTER `unary_union()`, which means the vertical edges are never split at the correct intersection points.

## Table Summary

| Aspect | Current (5 polygons) | Expected (7 polygons) |
|--------|---------------------|----------------------|
| Upper shelf upper (Y=535-635) | Combined with lower | 900x100 = 90,000 |
| Upper shelf lower (Y=35-535) | 900x600 = 540,000 | 900x500 = 450,000 |
| Middle left | 30x70 = 2,100 | 30x70 = 2,100 |
| Middle center (HATCH) | 870x70 = 60,900 | 870x70 = 60,900 |
| Middle right | 30x70 = 2,100 | 30x70 = 2,100 |
| Lower shelf upper (Y=-535 to -35) | Combined with lower | 900x500 = 450,000 |
| Lower shelf lower (Y=-635 to -535) | 900x600 = 540,000 | 900x100 = 90,000 |

## Relevant Files

- **app/core/geometry.py:515-583** (`_extract_paint_bucket_regions`) - Contains the bug: snap is applied AFTER unary_union instead of before
- **app/core/geometry.py:852-1010** (`_detect_content_zone`) - Calls `_extract_paint_bucket_regions` with tolerance parameters
- **app/core/constants.py** - Defines `PRECISION_SNAP_TOLERANCE` values per unit system
- **specs/032-unit-1-2-circle-arc-hatch-extraction.md** - Implemented HATCH boundary extraction (working correctly)

## Block Structure Analysis

### Entities in Block Definition
| Entity Type | Count | Purpose |
|-------------|-------|---------|
| LWPOLYLINE (CLOSED) | 4 | Two pairs of small rectangles in middle layer (L/R sides, mirrored) |
| LWPOLYLINE (OPEN) | 2 | Upper and lower shelf rectangles (5-point closed-by-repetition) |
| LINE | 2 | Horizontal dividers at Y=-535 and Y=535 |
| HATCH | 1 | Center rectangle in middle layer (EdgePath boundary) |
| MTEXT | 1 | Label text (ignored for geometry) |

### Visual Layers (from user description)
1. **Top layer (1 polygon)**: Upper portion of upper shelf (Y=535 to Y=635)
2. **2nd layer (1 polygon)**: Lower portion of upper shelf (Y=35 to Y=535)
3. **3rd/middle layer (3 polygons)**: Left rectangle + HATCH center + Right rectangle
4. **4th layer (1 polygon)**: Upper portion of lower shelf (Y=-535 to Y=-35)
5. **5th layer (1 polygon)**: Lower portion of lower shelf (Y=-635 to Y=-535)

## Root Cause Analysis

### The Precision Error
The horizontal LINE at Y=-535 has endpoints:
- Start: `(15.0, -535.0)` - exact
- End: `(914.9999999962746, -535.0000000002328)` - floating-point error

The difference from the expected (915.0, -535.0) is approximately **3.7e-9** (3.7 nanometers).

### Why Current Code Fails
The `_extract_paint_bucket_regions()` function does:
```python
# Step 1: Extract edges
edges = _extract_all_edges(block_def)

# Step 2: Merge and split at intersections
merged = unary_union(edges)  # BUG: Precision error prevents proper splitting

# Step 3: Snap coordinates (TOO LATE!)
merged = snap(merged, merged, precision_tolerance)  # Only moves points, doesn't re-split
```

When `unary_union()` runs, the LINE endpoint at (914.999..., -535.000...) does NOT exactly touch the vertical edge at X=915. Therefore:
- The left vertical edge IS split at Y=-535 (exact match at X=15)
- The right vertical edge is NOT split (no exact match at X=914.999...)

The subsequent `snap()` call only adjusts coordinate values but **does not re-compute segment intersections**.

### Proof of Fix
When coordinates are snapped BEFORE `unary_union()`:
```python
# Snap coordinates to grid FIRST
snapped_edges = [snap_coords(e, 0.01) for e in edges]

# THEN merge and split
merged = unary_union(snapped_edges)  # Now intersections are detected correctly
```

Result: **7 polygons** with correct areas matching user expectations.

## HATCH Boundary Extraction (Working Correctly)

The spec 032 implementation for HATCH boundary extraction is **working correctly**. The HATCH in this block has an EdgePath with 4 LineEdge segments forming a 870x70 rectangle in the middle layer. This is properly extracted and forms polygon #2 in both the current (5) and expected (7) counts.

The HATCH boundaries are NOT the cause of the discrepancy.

## Recommendations

### Fix: Snap Coordinates Before Union
Modify `_extract_paint_bucket_regions()` in `app/core/geometry.py` to snap edge coordinates BEFORE calling `unary_union()`:

```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
) -> list[Polygon]:
    edges = _extract_all_edges(block_def)

    if not edges:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Region detection aborted")

    # Stage 1: Snap coordinates BEFORE unary_union
    if precision_tolerance > 0:
        edges = [_snap_linestring_coords(e, precision_tolerance) for e in edges]
        logger.debug(f"Applied Stage 1 precision snap to edges: tolerance={precision_tolerance}")

    # Stage 2: Gap bridging (optional)
    if gap_bridge_tolerance > 0:
        edges = [_snap_linestring_coords(e, gap_bridge_tolerance) for e in edges]
        logger.debug(f"Applied Stage 2 gap bridge to edges: tolerance={gap_bridge_tolerance}")

    # NOW merge and split (intersections will be detected correctly)
    merged = unary_union(edges)

    # ... rest of function
```

### Helper Function Needed
```python
def _snap_linestring_coords(line: LineString, tolerance: float) -> LineString:
    """Snap LineString coordinates to grid based on tolerance."""
    coords = [(round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
              for x, y in line.coords]
    return LineString(coords)
```

## Next Steps

1. Create a spec file for the coordinate snapping fix
2. Update `_extract_paint_bucket_regions()` to snap before union
3. Add unit tests with the SPAR Gulv block to verify 7 polygons
4. Run full regression test suite
5. Re-test sample-blocks.dxf extraction to verify correct polygon counts

## Appendix: Test Verification

```python
# Test showing the fix works
edges = _extract_all_edges(block)
snapped_edges = [snap_coords(e, 0.01) for e in edges]
merged = unary_union(snapped_edges)
segments = list(merged.geoms)
polygons = list(polygonize(segments))

# Result: 7 polygons with areas:
# 450000, 60900, 2100, 450000, 2100, 90000, 90000
```
