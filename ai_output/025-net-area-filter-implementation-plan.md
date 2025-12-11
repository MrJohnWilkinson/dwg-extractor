# Net Area Filter Implementation Plan (Option A)

## Executive Summary

This plan details the implementation of **Option A: Filter After Net Area Calculation** from `ai_output/024-net-area-filter-nested-polygons.md`. The change moves the `min_area_filter` from before `_calculate_net_areas()` to after, filtering polygons by their net area (gross minus contained) rather than gross area. This addresses the "picture frame" scenario where large outer polygons with small net areas (thin frames) should be filtered out.

## Table Summary

| Step | Component | Action | Risk | Files Changed |
|------|-----------|--------|------|---------------|
| 1 | `_detect_content_zone()` | Remove current gross area filter block | Low | geometry.py |
| 2 | `_detect_content_zone()` | Move filter logic after `_calculate_net_areas()` | Low | geometry.py |
| 3 | `_detect_content_zone()` | Update `min_side_filter` to apply after net area filter | Low | geometry.py |
| 4 | Test assets | Create nested polygon test DXF files | None | tests/assets/ |
| 5 | Unit tests | Add net area filter tests | None | test_content_zone.py |
| 6 | Integration tests | Add end-to-end nested polygon tests | None | test_extractor_polygon_filter.py |
| 7 | Documentation | Update docstrings to reflect net area behavior | None | geometry.py |

## Relevant Files

### Core Implementation Files

- **`app/core/geometry.py:1059-1082`** - Current filtering location (BEFORE net area calc) that needs to be moved
- **`app/core/geometry.py:1104-1105`** - `_calculate_net_areas()` call site where filter should move TO
- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()` function that returns `list[tuple[Polygon, float]]`
- **`app/core/geometry.py:57-81`** - `calculate_polygon_area()` for gross area (still used by min_side_filter geometry check)
- **`app/core/geometry.py:83-99`** - `calculate_shortest_straight_side()` for side filter

### Reference Files

- **`ai_output/024-net-area-filter-nested-polygons.md`** - Analysis document with Option A recommendation
- **`app/core/constants.py:258-275`** - `DEFAULT_MIN_AREA_FILTER` unit-specific defaults
- **`app/core/extractor.py:950-962`** - `extract_blocks()` entry point passing filter params
- **`app_docs/005-field-naming-convention.md`** - Field naming conventions

### Test Files

- **`app/tests/core/test_content_zone.py:800-996`** - Existing polygon filtering tests in `TestPolygonFiltering`
- **`app/tests/core/extractor/test_extractor_polygon_filter.py`** - Integration tests for filter parameters
- **`app/tests/assets/`** - Test DXF file location

### Documentation Files

- **`ai_docs/ezdxf-geometry-reference.md`** - ezdxf library reference
- **`ai_docs/shapely-geometry-reference.md`** - Shapely library reference

## In-Scope

1. **Move area filter to use net area** - Relocate the min_area_filter from pre-net-area to post-net-area position
2. **Preserve side filter behavior** - min_side_filter continues to use gross geometry (shortest side length)
3. **Add unit tests for nested scenarios** - Test picture frame, box-in-box, multiple siblings
4. **Update docstrings** - Clarify that min_area_filter uses net area
5. **Maintain backward compatibility** - No change when filters are disabled (default)

## Out-of-Scope

1. **Option C: Containment tree with area propagation** - Future enhancement, not current scope
2. **GUI changes** - No UI changes needed; filter controls remain the same
3. **New filter parameters** - No new parameters added
4. **Performance optimization** - Accept slight performance cost of running net area calc on all polygons
5. **Area propagation when inner removed** - When inner polygon is filtered, outer's net area is NOT recalculated

## Implementation Plan

### Phase 1: Core Logic Change (geometry.py)

#### Step 1: Understand Current Flow

Current implementation at `geometry.py:1059-1082`:
```python
# Current: Filter by GROSS area BEFORE net area calculation
if min_area_filter > 0 or min_side_filter > 0:
    filtered_shapes: list[Polygon] = []
    for shape in all_shapes:
        if min_area_filter > 0:
            area = calculate_polygon_area(shape)  # GROSS area
            if area < min_area_filter:
                continue
        if min_side_filter > 0:
            shortest_side = calculate_shortest_straight_side(shape)
            if shortest_side < min_side_filter:
                continue
        filtered_shapes.append(shape)
    all_shapes = filtered_shapes
```

#### Step 2: Move Area Filter After Net Area Calculation

Modify `_detect_content_zone()` to:

1. **Remove the area filter from the pre-net-area loop** - Keep only min_side_filter in the early filtering
2. **Call `_calculate_net_areas()` on all shapes** (minus side-filtered ones)
3. **Apply min_area_filter to net_areas result** - Filter the `list[tuple[Polygon, float]]` by net area value
4. **Continue with content zone selection** from filtered net_areas

New flow:
```python
# Step 1: Early side filter (uses gross geometry)
if min_side_filter > 0:
    all_shapes = [s for s in all_shapes
                  if calculate_shortest_straight_side(s) >= min_side_filter]

# Step 2: Calculate net areas for remaining shapes
net_areas = _calculate_net_areas(all_shapes, abort_event)

# Step 3: Filter by NET area (post-calculation)
if min_area_filter > 0:
    net_areas = [(poly, net_area) for poly, net_area in net_areas
                 if net_area >= min_area_filter]
```

#### Step 3: Update Polygon Count Tracking

The `polygon_count` returned in `ContentZoneData` should reflect the count AFTER filtering. Ensure logging accurately shows:
- Initial paint-bucket region count
- Count after side filter
- Count after net area filter

#### Step 4: Update Docstring

Update `_detect_content_zone()` docstring to clarify:
```python
"""
Polygon filtering (when enabled):
- min_side_filter: Filters polygons by shortest straight side (gross geometry)
- min_area_filter: Filters polygons by NET area (own area minus contained polygons)
"""
```

### Phase 2: Test Asset Creation

#### Step 5: Create Test DXF File for Nested Polygons

Create `app/tests/assets/nested_polygon_filter_test.dxf` using a Python script at `app/tests/assets/create_nested_polygon_filter_test.py`:

**Blocks to create:**

| Block Name | Description | Expected Behavior |
|------------|-------------|-------------------|
| `PICTURE_FRAME` | Outer 100x100 containing inner 80x80 | Outer net=3600, inner net=6400. Filter=5000 removes outer |
| `BOX_IN_BOX_IN_BOX` | 3 nested boxes with decreasing sizes | Net areas decrease with depth |
| `MULTIPLE_SIBLINGS` | Outer containing 3 non-overlapping inner | Outer net = gross - sum(siblings) |
| `SINGLE_LARGE` | Single rectangle for comparison | Net = gross (no containment) |

### Phase 3: Unit Tests

#### Step 6: Add Net Area Filter Tests

Add new test class `TestNetAreaFiltering` to `app/tests/core/test_content_zone.py`:

```python
class TestNetAreaFiltering:
    """Test suite for net area filtering in _detect_content_zone."""

    def test_picture_frame_filtered_by_net_area(self):
        """Outer polygon with small net area filtered when threshold > net area."""
        # Outer: 100x100=10000 gross, contains 80x80=6400
        # Net areas: outer=3600, inner=6400
        # Filter=5000: outer fails (3600<5000), inner passes (6400>5000)

    def test_picture_frame_inner_selected_as_content_zone(self):
        """Inner polygon becomes content zone when outer filtered."""

    def test_box_in_box_in_box_filtering(self):
        """Multi-level nesting filters correctly by net area."""

    def test_gross_area_filter_would_pass_outer(self):
        """Verify gross area would have passed the outer (regression test)."""

    def test_side_filter_still_uses_gross_geometry(self):
        """min_side_filter continues to check gross shortest side."""

    def test_filter_order_side_then_net_area(self):
        """Side filter applied first, then net area filter."""
```

### Phase 4: Integration Tests

#### Step 7: Add Extractor Integration Tests

Add to `app/tests/core/extractor/test_extractor_polygon_filter.py`:

```python
class TestNetAreaFilterIntegration:
    """Integration tests for net area filtering via extract_blocks()."""

    def test_nested_polygon_filtered_by_net_area(self):
        """Extract blocks filters nested polygons by net area."""

    def test_content_zone_reflects_net_area_winner(self):
        """Content zone data shows correct polygon after net area filtering."""
```

### Phase 5: Validation

#### Step 8: Run All Validation Commands

Execute validation commands to ensure zero regressions:

```bash
# Run new net area filter tests
uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v

# Run existing polygon filter tests
uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v

# Run extractor filter integration tests
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v

# Run full test suite
uv run pytest app/tests/ -v

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/
```

## Acceptance Criteria

1. **Net area filter functional** - `min_area_filter` uses net area (gross - contained) instead of gross area
2. **Picture frame scenario works** - Outer frame polygon (small net area) filtered out, inner kept
3. **Side filter unchanged** - `min_side_filter` continues to use gross polygon geometry
4. **Backward compatible** - No behavior change when filters disabled (default)
5. **All existing tests pass** - No regressions in 700+ existing tests
6. **New tests pass** - All new net area filter tests pass
7. **Type checking passes** - `uv run mypy app/` reports no errors
8. **Linting passes** - `uv run ruff check app/` reports no issues

## Testing Strategy

### Unit Tests (test_content_zone.py)

| Test | Purpose | Key Assertion |
|------|---------|---------------|
| Picture frame filtered | Net area filter removes thin frame | polygon_count == 1 (inner only) |
| Inner becomes content zone | Correct polygon selected | trim values match inner |
| 3-level nesting | Multi-level filtering | Correct net areas calculated |
| Gross vs net comparison | Verify behavior change | Gross would pass, net fails |
| Side filter gross geometry | Side filter unchanged | Uses shortest side, not net |

### Integration Tests (test_extractor_polygon_filter.py)

| Test | Purpose | Key Assertion |
|------|---------|---------------|
| Nested via extract_blocks | End-to-end integration | content_zone_data correct |
| Combined filters | Both filters work together | Correct filtering order |

### Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| No containment | Net area == gross area |
| All filtered | content_zone_detected = False |
| Exactly at threshold | Passes (>= comparison) |
| Multiple equal net areas | Uses union bbox (existing behavior) |

## Code Change Estimate

| Component | Lines Changed | Risk |
|-----------|---------------|------|
| `geometry.py:_detect_content_zone()` | ~25 lines modified | Low |
| New test DXF creator script | ~60 lines new | N/A |
| New unit tests | ~80-100 lines new | N/A |
| New integration tests | ~30 lines new | N/A |
| Docstring updates | ~10 lines modified | N/A |
| **Total** | **~200 lines** | **Low** |

## Notes

### Performance Consideration

The change means `_calculate_net_areas()` runs on ALL shapes (after side filter) before area filtering, instead of running on pre-filtered shapes. This is acceptable because:

1. The polygon count is already bounded by `POLYGON_COUNT_THRESHOLD` (500)
2. Net area calculation is O(n^2) but n is small
3. Correctness is more important than marginal performance for this feature


