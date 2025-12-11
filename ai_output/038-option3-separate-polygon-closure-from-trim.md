# Option 3: Separate Polygon Closure from Trim Calculation - Implementation Guide

## Executive Summary

Option 3 proposes separating coordinate snapping concerns: use snapped coordinates for polygon detection (to close floating-point gaps), then recalculate bounding boxes from original/raw coordinates for accurate trim values. This approach maintains polygon detection robustness while ensuring trim calculations never exceed block bounds. Implementation requires maintaining a coordinate mapping between snapped and original vertices throughout the polygon detection pipeline.

## Table Summary

| Aspect | Current Behavior | Option 3 Behavior |
|--------|------------------|-------------------|
| Edge extraction | Raw coordinates | Raw coordinates (unchanged) |
| Snapping | Applied to edges directly | Applied to create temporary detection geometry |
| Polygon detection | Uses snapped coordinates | Uses snapped coordinates (unchanged) |
| Bounding box source | Snapped polygon vertices | Original raw vertices mapped from detected polygons |
| Trim calculation | `snapped_cz_bounds - raw_block_bounds` | `raw_cz_bounds - raw_block_bounds` |
| Result | Can produce negative trims | Always produces valid (>=0) trims |

## Relevant Files

- `app/core/geometry.py:541-560` - `_snap_linestring_coords()`: Current snapping logic that modifies coordinates in-place
- `app/core/geometry.py:645-715` - `_extract_paint_bucket_regions()`: Paint-bucket algorithm where snapping is applied
- `app/core/geometry.py:984-1181` - `_detect_content_zone()`: Content zone detection that calculates trim values
- `app/core/geometry.py:838-866` - `_get_union_bounding_box()`: Current bbox calculation from polygon vertices
- `app/core/geometry.py:812-836` - `_get_polygon_bbox()`: Single polygon bbox calculation
- `app/core/geometry.py:595-643` - `_extract_all_edges()`: Edge extraction from block entities

## Implementation Strategy

### Core Concept: Coordinate Mapping

The key insight is that **snapping is a bijective transformation** for small tolerances - each original coordinate maps to exactly one snapped coordinate and vice versa. We can maintain this mapping to "reverse lookup" original coordinates after polygon detection.

### Approach A: Snap-Map-Unsnap (Recommended)

Build a lookup table of `snapped_coord -> original_coord` during snapping, then use it to recover original vertices after polygonize.

```python
def _snap_with_mapping(
    edges: list[LineString],
    tolerance: float
) -> tuple[list[LineString], dict[tuple[float, float], tuple[float, float]]]:
    """
    Snap edges and build reverse mapping.

    Returns:
        Tuple of (snapped_edges, snap_map) where snap_map is
        {snapped_coord: original_coord}
    """
    snap_map: dict[tuple[float, float], tuple[float, float]] = {}
    snapped_edges: list[LineString] = []

    for edge in edges:
        snapped_coords = []
        for x, y in edge.coords:
            snapped_x = round(x / tolerance) * tolerance
            snapped_y = round(y / tolerance) * tolerance
            snapped = (snapped_x, snapped_y)
            original = (x, y)

            # Store mapping (may overwrite with similar originals - acceptable)
            snap_map[snapped] = original
            snapped_coords.append(snapped)

        snapped_edges.append(LineString(snapped_coords))

    return snapped_edges, snap_map


def _unsnap_polygon(
    polygon: list[tuple[float, float]],
    snap_map: dict[tuple[float, float], tuple[float, float]]
) -> list[tuple[float, float]]:
    """
    Recover original coordinates for polygon vertices.

    Vertices created by unary_union (intersection points) won't be in
    snap_map - for these, return the snapped coordinate as-is since
    they're derived geometrically.
    """
    return [snap_map.get(coord, coord) for coord in polygon]
```

### Approach B: Entity-Based Bounds Recalculation

Instead of mapping coordinates, recalculate bounds by finding which original DXF entities contributed to each detected polygon.

```python
def _get_bbox_from_contributing_entities(
    polygon: list[tuple[float, float]],
    original_edges: list[LineString],
    snapped_edges: list[LineString]
) -> tuple[float, float, float, float]:
    """
    Find original edges that contributed to polygon and compute bbox.

    This is more complex but handles edge cases where intersection
    points don't map cleanly.
    """
    # For each polygon edge, find matching snapped edge
    # Then look up corresponding original edge
    # Compute bbox from original edge coordinates
    ...
```

### Approach C: Clamp at Polygon Level

After detecting polygons with snapped coordinates, clamp each polygon's bounding box to not exceed block bounds before calculating trim.

```python
def _clamp_polygon_to_block_bounds(
    polygon: list[tuple[float, float]],
    block_bbox: tuple[float, float, float, float]
) -> list[tuple[float, float]]:
    """Clamp polygon vertices to block bounding box."""
    min_x, min_y, max_x, max_y = block_bbox
    return [
        (
            max(min_x, min(max_x, x)),
            max(min_y, min(max_y, y))
        )
        for x, y in polygon
    ]
```

## Recommended Implementation: Approach A

### Step 1: Modify `_extract_paint_bucket_regions()`

```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    return_coordinate_mapping: bool = False,  # NEW PARAMETER
) -> list[Polygon] | tuple[list[Polygon], dict]:
    """
    Extract all visual regions using paint-bucket algorithm.

    When return_coordinate_mapping=True, also returns the snap mapping
    that can be used to recover original coordinates.
    """
    edges = _extract_all_edges(block_def)

    if not edges:
        return ([], {}) if return_coordinate_mapping else []

    # Stage 1: Precision snapping with mapping
    snap_map = {}
    if precision_tolerance > 0:
        edges, snap_map = _snap_with_mapping(edges, precision_tolerance)
        logger.debug(f"Applied Stage 1 precision snap: tolerance={precision_tolerance}")

    # Rest of algorithm unchanged...
    merged = unary_union(edges)
    if merged.is_empty:
        return ([], snap_map) if return_coordinate_mapping else []

    # ... gap bridging, polygonize, etc.

    if return_coordinate_mapping:
        return result, snap_map
    return result
```

### Step 2: Create New Helper Function

```python
def _get_union_bounding_box_unsnapped(
    polygons: list[Polygon],
    snap_map: dict[tuple[float, float], tuple[float, float]]
) -> tuple[float, float, float, float]:
    """
    Calculate union bounding box using original (unsnapped) coordinates.

    For each polygon vertex, looks up the original coordinate in snap_map.
    Vertices not in snap_map (intersection points) are used as-is.
    """
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)

    all_coords = []
    for polygon in polygons:
        for coord in polygon:
            original = snap_map.get(coord, coord)
            all_coords.append(original)

    if not all_coords:
        return (0.0, 0.0, 0.0, 0.0)

    min_x = min(c[0] for c in all_coords)
    min_y = min(c[1] for c in all_coords)
    max_x = max(c[0] for c in all_coords)
    max_y = max(c[1] for c in all_coords)

    return (min_x, min_y, max_x, max_y)
```

### Step 3: Update `_detect_content_zone()`

```python
def _detect_content_zone(...) -> ContentZoneData:
    # ...existing code...

    # Use paint-bucket algorithm WITH coordinate mapping
    all_shapes, snap_map = _extract_paint_bucket_regions(
        block_def, abort_event, precision_tolerance, gap_bridge_tolerance,
        return_coordinate_mapping=True  # NEW
    )

    # ...filtering logic unchanged...

    # Calculate bbox from ORIGINAL coordinates
    if len(survivors) == 1:
        # Unsnap single polygon
        unsnapped_poly = _unsnap_polygon(survivors[0], snap_map)
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(unsnapped_poly)
    else:
        # Unsnap all survivors and compute union bbox
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box_unsnapped(
            survivors, snap_map
        )

    # ...rest unchanged...
```

## Edge Cases and Considerations

### 1. Intersection Point Vertices

When `unary_union()` splits edges at intersections, it creates new vertices that don't exist in the original DXF. These vertices:
- Won't be in `snap_map`
- Should use their snapped coordinate (which is geometrically correct)

**Mitigation**: The `snap_map.get(coord, coord)` pattern handles this gracefully.

### 2. Multiple Originals Mapping to Same Snapped

If two original coordinates snap to the same grid point:
- Original A: `(4876.80000000028, 100.0)` -> snapped `(4878.0, 100.0)`
- Original B: `(4877.2, 100.0)` -> snapped `(4878.0, 100.0)`

The map will only store one original. This is acceptable because:
- For bounding box calculation, using either original gives similar bounds
- The difference is within the snapping tolerance (design choice)

### 3. Gap Bridge Stage

Gap Bridge uses Shapely's `snap()` which may create vertices not in `snap_map`. These are intentional gap-bridging points and using their snapped coordinates is correct.

### 4. Performance Impact

| Operation | Current | With Mapping |
|-----------|---------|--------------|
| Edge extraction | O(n) | O(n) |
| Snap with mapping | O(n) | O(n) + dict insertions |
| Polygon detection | O(n log n) | O(n log n) |
| Bbox unsnapping | O(p) | O(p * v) dict lookups |
| **Memory** | O(n) | O(n) + O(v) for snap_map |

Where n=edges, p=polygons, v=vertices. The overhead is minimal.

## Testing Strategy

### Unit Tests

```python
def test_snap_mapping_preserves_originals():
    """Verify snap map contains original coordinates."""
    edges = [LineString([(4876.80000000028, 0), (4876.80000000028, 100)])]
    snapped, snap_map = _snap_with_mapping(edges, 3.0)

    assert (4878.0, 0.0) in snap_map
    assert snap_map[(4878.0, 0.0)] == (4876.80000000028, 0)


def test_unsnap_polygon_recovers_original_bounds():
    """Verify unsnapped polygon has correct bounds."""
    polygon = [(4878.0, 0.0), (4878.0, 100.0), (0.0, 100.0), (0.0, 0.0)]
    snap_map = {(4878.0, 0.0): (4876.8, 0.0), (4878.0, 100.0): (4876.8, 100.0)}

    unsnapped = _unsnap_polygon(polygon, snap_map)
    bbox = _get_polygon_bbox(unsnapped)

    assert bbox[2] == 4876.8  # max_x from original


def test_content_zone_never_exceeds_block_bounds():
    """Integration test: trim values are never negative."""
    # Test with block AP #5-4 and precision=3.0
    cz_data = _detect_content_zone(block_def, block_bbox, precision_tolerance=3.0)

    assert cz_data['suggested_trim_top'] >= 0
    assert cz_data['suggested_trim_bottom'] >= 0
    assert cz_data['suggested_trim_left'] >= 0
    assert cz_data['suggested_trim_right'] >= 0
```

## Comparison with Other Options

| Criteria | Option 1 (Clamp) | Option 2 (Consistent Coords) | **Option 3 (Separate)** |
|----------|------------------|------------------------------|-------------------------|
| Mathematical correctness | Moderate | High | **Highest** |
| Implementation complexity | Low | Medium | **Medium-High** |
| Native dimension accuracy | Preserved | Modified | **Preserved** |
| Trim value accuracy | Approximate | Exact | **Exact** |
| Backward compatibility | Full | Breaking | **Full** |
| Performance impact | None | Minor | **Minor** |

## Recommendations

1. **Implement Approach A** (snap-map-unsnap) as it provides the cleanest separation of concerns

2. **Add `return_coordinate_mapping` parameter** with default `False` for backward compatibility

3. **Document the coordinate mapping** in function docstrings for future maintainers

4. **Add integration test** specifically for the `AP #5-4` block with precision=3.0

5. **Consider future enhancement**: expose the snap mapping in debug output for troubleshooting

## Next Steps

1. Implement `_snap_with_mapping()` helper function
2. Add `return_coordinate_mapping` parameter to `_extract_paint_bucket_regions()`
3. Create `_get_union_bounding_box_unsnapped()` helper
4. Update `_detect_content_zone()` to use unsnapped coordinates for bbox
5. Write unit tests for new functionality
6. Integration test with problematic block (AP #5-4, precision=3.0)
7. Update documentation to explain the coordinate domain separation
