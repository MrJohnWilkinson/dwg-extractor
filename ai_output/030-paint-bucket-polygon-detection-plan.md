# Paint-Bucket Polygon Detection Implementation Plan

## Executive Summary

This plan defines the sequenced implementation steps for upgrading polygon detection from the current "closed CAD entities" approach to a "paint-bucket" algorithm that matches user visual expectations. The work is structured into 3 implementation units, building on the completed Unit 1 (unary_union fix) and Unit 2 (line cycle tests).

## Table Summary

| Unit | Description | Files | Dependencies | Status |
|------|-------------|-------|--------------|--------|
| Unit 1 | Add `unary_union()` preprocessing to LINE cycle detection | `geometry.py:562-568` | None | **COMPLETED** |
| Unit 2 | Add unit tests for T-junctions and crossing intersections | `test_geometry.py` | Unit 1 | **COMPLETED** |
| Unit 3 | Create `_extract_all_edges()` function | `geometry.py` (new function) | Unit 1 | Pending |
| Unit 4 | Create `_extract_paint_bucket_regions()` function | `geometry.py` (new function) | Unit 3 | Pending |
| Unit 5 | Update `_detect_content_zone()` to use paint-bucket | `geometry.py:641-784` | Unit 4 | Pending |
| Unit 6 | Add integration tests with sample blocks | `test_geometry.py` | Unit 5 | Pending |

## Relevant Files

- **`app/core/geometry.py:526-581`** - `_extract_line_cycles()` function (Unit 1 COMPLETED - already has unary_union fix)
- **`app/core/geometry.py:375-404`** - `_extract_closed_lwpolylines()` - only extracts closed LWPOLYLINEs as complete polygons, ignores open ones
- **`app/core/geometry.py:641-784`** - `_detect_content_zone()` main detection logic - combines LWPOLYLINE and LINE shapes separately
- **`app/core/constants.py:140-150`** - Performance thresholds (LINE_SEGMENT_THRESHOLD=5000, POLYGON_COUNT_THRESHOLD=500)
- **`app/tests/core/test_geometry.py`** - Test file for geometry module (Unit 2 COMPLETED - has TestExtractLineCycles)
- **`ai_output/028-polygon-count-discrepancy-analysis.md`** - Analysis showing expected paint-bucket results per block
- **`ai_output/029-polygon-detection-edge-inclusion-analysis.md`** - Technical analysis of required code changes

## In Scope

1. **Unit 3**: Create `_extract_all_edges()` function
   - Extract edges from LWPOLYLINE entities (both open and closed)
   - Extract edges from LINE entities
   - Return list of Shapely LineString objects
   - ~15 lines of code

2. **Unit 4**: Create `_extract_paint_bucket_regions()` function
   - Use `_extract_all_edges()` to get unified edge set
   - Apply `unary_union()` to split at intersections
   - Apply `polygonize()` to find all visual regions
   - Return list of Polygon objects
   - ~20 lines of code

3. **Unit 5**: Update `_detect_content_zone()` to use paint-bucket
   - Replace separate LWPOLYLINE + LINE extraction with unified approach
   - Maintain performance thresholds (now applied to edge count)
   - Preserve existing ContentZoneData return format
   - ~10 lines changed

4. **Unit 6**: Integration tests
   - Test with sample block patterns matching ai_output/028 analysis
   - Verify expected polygon counts: AP #5-4=8, Bread gondola=13, etc.

## Out of Scope

1. **GS900x450HGE_Liquor special handling** - This block has an open U-shape (3 vs 4 expected). Requires separate analysis of whether to:
   - Accept geometric reality (3 is correct)
   - Add endpoint-to-boundary connection logic
   - Document as edge case

2. **Existing test modifications** - All 536+ existing tests must continue to pass

3. **Constants changes** - LINE_SEGMENT_THRESHOLD (5000) and POLYGON_COUNT_THRESHOLD (500) remain unchanged

4. **New dependencies** - All required imports (LineString, unary_union, polygonize) already present

5. **Excel output changes** - polygon_count column behavior unchanged, just more accurate counts

## Implementation Steps (Sequenced)

### Unit 3: Create `_extract_all_edges()` Function

**Prerequisite:** Unit 1 (COMPLETED)

**File:** `app/core/geometry.py`

**Location:** Add after `_count_line_segments()` function (line ~373)

**Code:**
```python
def _extract_all_edges(block_def: BlockLayout) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Extracts edges from:
    - LWPOLYLINE entities (all vertices as edges, closing edge if closed)
    - LINE entities (start to end as single edge)

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of LineString objects representing all edges in the block.
    """
    edges: list[LineString] = []

    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            try:
                points = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                # Convert polyline to edge segments
                for i in range(len(points) - 1):
                    edges.append(LineString([points[i], points[i + 1]]))
                # Add closing edge if closed
                if hasattr(entity, 'closed') and entity.closed and len(points) >= 2:
                    edges.append(LineString([points[-1], points[0]]))
            except (AttributeError, IndexError):
                continue

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges
```

**Validation:**
- `uv run mypy app/core/geometry.py`
- `uv run ruff check app/core/geometry.py`

---

### Unit 4: Create `_extract_paint_bucket_regions()` Function

**Prerequisite:** Unit 3

**File:** `app/core/geometry.py`

**Location:** Add after `_extract_all_edges()` function

**Code:**
```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    """
    Extract all visual regions using paint-bucket algorithm.

    Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
    splits at intersections using unary_union, and finds all closed
    regions using polygonize.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading.Event to signal abort request

    Returns:
        List of Polygon objects representing all visual regions.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    edges = _extract_all_edges(block_def)

    if not edges:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Region detection aborted")

    # Merge and split at all intersections
    merged = unary_union(edges)
    if merged.is_empty:
        return []

    line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
    polygons = list(polygonize(line_segments))

    # Convert to internal format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} paint-bucket regions")
    return result
```

**Validation:**
- `uv run mypy app/core/geometry.py`
- `uv run ruff check app/core/geometry.py`

---

### Unit 5: Update `_detect_content_zone()` to Use Paint-Bucket

**Prerequisite:** Unit 4

**File:** `app/core/geometry.py:641-784`

**Changes Required:**

1. **Replace lines 671-688** (separate LWPOLYLINE and LINE extraction) with:
```python
    # Count edges for threshold check
    edge_count = len(_extract_all_edges(block_def))
    if edge_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping region detection: "
            f"{edge_count} edges exceeds threshold {LINE_SEGMENT_THRESHOLD}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=0,
        )

    # Use paint-bucket algorithm for accurate region detection
    all_shapes = _extract_paint_bucket_regions(block_def, abort_event)
    polygon_count = len(all_shapes)
    logger.debug(f"[{block_name}] Found {polygon_count} paint-bucket regions")
```

2. **Keep remaining logic unchanged** (net area calculation, trim derivation)

**Validation:**
- `uv run pytest app/tests/core/test_geometry.py -v`
- `uv run pytest app/tests/ -v` (all 536+ tests must pass)
- `uv run mypy app/`

---

### Unit 6: Add Integration Tests

**Prerequisite:** Unit 5

**File:** `app/tests/core/test_geometry.py`

**Tests to Add:**

```python
class TestPaintBucketRegions:
    """
    Test suite for paint-bucket region detection.

    Validates that the algorithm correctly detects visual regions
    matching user expectations for various block patterns.
    """

    def test_rectangle_with_vertical_divider(self) -> None:
        """Test rectangle split by vertical divider produces 2 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_DIVIDER")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # LINE divider at midpoint
        block.add_line((50, 0), (50, 50))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 2 regions (left and right)
        assert len(regions) == 2

    def test_rectangle_with_grid_dividers(self) -> None:
        """Test rectangle with cross dividers produces 4 regions."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="RECT_GRID")

        # Closed LWPOLYLINE rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Horizontal divider
        block.add_line((0, 50), (100, 50))
        # Vertical divider
        block.add_line((50, 0), (50, 100))

        regions = _extract_paint_bucket_regions(block)

        # Should produce 4 regions (2x2 grid)
        assert len(regions) == 4
```

**Validation:**
- `uv run pytest app/tests/core/test_geometry.py::TestPaintBucketRegions -v`
- `uv run pytest app/tests/ -v`

---

## Expected Polygon Count Changes

After implementation, polygon counts will change for these block patterns:

| Block Pattern | Current Count | Paint-Bucket Count | Change |
|---------------|---------------|-------------------|--------|
| Rectangle + 1 vertical LINE divider | 1 | 2 | +1 |
| Rectangle + grid (3 horiz + 1 vert) | 1 | 8 | +7 |
| AP #5-4 pattern | 1 | 8 | +7 |
| Bread gondola pattern | 4 | 13 | +9 |
| Bread gondola end pattern | 1 | 4 | +3 |
| Gcase(w1800) pattern | 1 | 2 | +1 |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Edge count exceeds threshold | Low | Medium | Apply threshold to total edge count, not just LINE count |
| `unary_union` performance | Low | Low | Already validated in Unit 1; O(n log n) complexity |
| Nested polygon handling | Medium | Medium | Keep `_calculate_net_areas()` for content zone selection |
| Existing tests fail | Low | High | Run full test suite after each unit |

## Verification Checklist

### Unit 3 (Extract All Edges)
- [ ] `_extract_all_edges()` function added after line 373
- [ ] Function handles LINE entities
- [ ] Function handles LWPOLYLINE entities (open and closed)
- [ ] Type check passes: `uv run mypy app/core/geometry.py`
- [ ] Lint passes: `uv run ruff check app/core/geometry.py`

### Unit 4 (Paint-Bucket Regions)
- [ ] `_extract_paint_bucket_regions()` function added
- [ ] Uses `_extract_all_edges()` for unified edge set
- [ ] Uses `unary_union()` + `polygonize()` pattern
- [ ] Handles abort_event
- [ ] Type check passes

### Unit 5 (Update Detection)
- [ ] `_detect_content_zone()` uses paint-bucket approach
- [ ] Edge count threshold applied correctly
- [ ] All 536+ existing tests pass
- [ ] Type check passes

### Unit 6 (Integration Tests)
- [ ] `TestPaintBucketRegions` class added
- [ ] Rectangle + divider test passes
- [ ] Rectangle + grid test passes
- [ ] All tests pass

## References

- **Analysis 028:** `ai_output/028-polygon-count-discrepancy-analysis.md` - Root cause analysis and expected counts
- **Analysis 029:** `ai_output/029-polygon-detection-edge-inclusion-analysis.md` - Code change requirements
- **Spec 027:** `specs/027-unit-1-unary-union-fix.md` - Completed Unit 1 implementation
- **Spec 028:** `specs/028-unit-2-line-cycle-tests.md` - Completed Unit 2 tests
- **Geometry Module:** `app/core/geometry.py` - Target implementation file
- **Test File:** `app/tests/core/test_geometry.py` - Target test file

## Next Steps

1. Implement Unit 3: `_extract_all_edges()` function
2. Implement Unit 4: `_extract_paint_bucket_regions()` function
3. Implement Unit 5: Update `_detect_content_zone()`
4. Implement Unit 6: Add integration tests
5. Validate with sample-blocks.dxf if available
6. Document any behavior changes in user-facing output
