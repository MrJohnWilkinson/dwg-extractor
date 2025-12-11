# Feature: Unit 1 - Net Area Filter Core Logic Change

## Feature Description

This feature modifies the `_detect_content_zone()` function in `geometry.py` to filter polygons by NET area (gross area minus contained polygon areas) instead of GROSS area. The current implementation filters polygons by gross area BEFORE calling `_calculate_net_areas()`, which incorrectly keeps large "picture frame" polygons that have small actual (net) areas after subtracting inner polygons.

This is Unit 1 of the Net Area Filter Implementation Plan (`ai_output/025-net-area-filter-implementation-plan.md`), focusing on the core logic change. This unit does not add new tests or test assets - those will be covered in subsequent units.

## User Story

As a CAD engineer processing DXF files with nested polygons
I want the area filter to use net area (gross minus contained) instead of gross area
So that thin "picture frame" polygons with large gross areas but small net areas are correctly filtered out, leaving the actual content zone intact

## Problem Statement

The current implementation at `geometry.py:1059-1082` filters polygons by their GROSS area before calculating net areas:

```python
# Current: Filter by GROSS area BEFORE net area calculation
if min_area_filter > 0:
    area = calculate_polygon_area(shape)  # GROSS area
    if area < min_area_filter:
        continue
```

This causes incorrect behavior in the "picture frame" scenario:
- Outer rectangle: 100x100 = 10,000 sq units gross area
- Inner rectangle: 80x80 = 6,400 sq units
- Outer's NET area: 10,000 - 6,400 = 3,600 sq units (thin frame only)
- Inner's NET area: 6,400 sq units (solid)

With `min_area_filter=5000`:
- **Current (gross)**: Outer passes (10,000 > 5,000), inner passes (6,400 > 5,000) - outer wins as content zone
- **Desired (net)**: Outer fails (3,600 < 5,000), inner passes (6,400 > 5,000) - inner correctly wins

## Solution Statement

Restructure `_detect_content_zone()` to apply the area filter AFTER net area calculation:

1. **Early side filter**: Apply `min_side_filter` before net area calculation (uses gross geometry - unchanged)
2. **Calculate net areas**: Call `_calculate_net_areas()` on all remaining shapes
3. **Post-calculation area filter**: Apply `min_area_filter` to the net_areas result, filtering by NET area
4. **Update tracking**: Ensure `polygon_count` and logging reflect the correct filtered state
5. **Update docstring**: Clarify that `min_area_filter` uses net area while `min_side_filter` uses gross geometry

## Relevant Files

Use these files to implement the feature:

- **app/core/geometry.py** - Main implementation file
  - Lines 1059-1082: Current filtering location (BEFORE net area calc) - needs restructuring
  - Lines 1104-1105: `_calculate_net_areas()` call site where area filter should move TO
  - Lines 926-980: `_calculate_net_areas()` function that returns `list[tuple[Polygon, float]]`
  - Lines 983-1031: `_detect_content_zone()` docstring that needs updating

- **app/tests/core/test_content_zone.py** - Content zone test module
  - Lines 800-996: Existing `TestPolygonFiltering` class - existing tests should continue to pass
  - Some existing tests may need assertion updates if they rely on gross area filtering behavior

### New Files

None - all changes are to existing files.

## Implementation Plan

### Phase 1: Foundation

Understand the current flow in `_detect_content_zone()`:
1. Extract paint-bucket regions -> `all_shapes`
2. Filter by gross area AND side (lines 1059-1082)
3. Check polygon count threshold
4. Calculate net areas with `_calculate_net_areas()` (line 1105)
5. Find largest net area polygon(s) for content zone

Review the `_calculate_net_areas()` return type: `list[tuple[Polygon, float]]` sorted by net area descending.

### Phase 2: Core Implementation

Restructure the filtering logic:
1. Remove area filter from the pre-net-area loop (keep only side filter early)
2. Move area filter to after `_calculate_net_areas()` call
3. Filter the `list[tuple[Polygon, float]]` result by net area value
4. Update polygon count tracking to reflect post-filter state
5. Update docstring to clarify net vs gross area usage

### Phase 3: Integration

Verify backward compatibility:
- Default filter values (0.0) produce identical behavior
- Side filter continues to use gross geometry
- Existing tests pass without modification (or with minimal assertion updates)

## Step by Step Tasks

### Step 1: Understand Current Implementation

Review the current filtering code at `geometry.py:1059-1082`:

```python
# Current: Filter by GROSS area BEFORE net area calculation
if min_area_filter > 0 or min_side_filter > 0:
    filtered_shapes: list[Polygon] = []
    for shape in all_shapes:
        if min_area_filter > 0:
            area = calculate_polygon_area(shape)
            if area < min_area_filter:
                continue
        if min_side_filter > 0:
            shortest_side = calculate_shortest_straight_side(shape)
            if shortest_side < min_side_filter:
                continue
        filtered_shapes.append(shape)

    logger.debug(
        f"[{block_name}] Filtered {len(all_shapes)} -> {len(filtered_shapes)} polygons "
        f"(min_area={min_area_filter}, min_side={min_side_filter})"
    )
    all_shapes = filtered_shapes
    polygon_count = len(all_shapes)
```

### Step 2: Restructure Early Filtering (Side Filter Only)

Replace the combined filter block with side-only early filtering:

```python
# Step 1: Early side filter (uses gross geometry)
if min_side_filter > 0:
    pre_side_count = len(all_shapes)
    all_shapes = [
        s for s in all_shapes
        if calculate_shortest_straight_side(s) >= min_side_filter
    ]
    logger.debug(
        f"[{block_name}] Side filter: {pre_side_count} -> {len(all_shapes)} polygons "
        f"(min_side={min_side_filter})"
    )
    polygon_count = len(all_shapes)
```

This replaces lines 1059-1082 with a simpler side-only filter.

### Step 3: Add Net Area Filter After Calculation

After the existing `_calculate_net_areas()` call at line 1105, add the net area filter:

```python
# Calculate net areas (O(n^2) but bounded by threshold)
net_areas = _calculate_net_areas(all_shapes, abort_event)

# Step 3: Filter by NET area (post-calculation)
if min_area_filter > 0:
    pre_area_count = len(net_areas)
    net_areas = [
        (poly, net_area) for poly, net_area in net_areas
        if net_area >= min_area_filter
    ]
    logger.debug(
        f"[{block_name}] Net area filter: {pre_area_count} -> {len(net_areas)} polygons "
        f"(min_area={min_area_filter})"
    )
```

### Step 4: Update Polygon Count After Net Area Filter

Update the polygon_count to reflect the final filtered state. Add after the net area filter:

```python
# Update polygon count after all filtering
polygon_count = len(net_areas)
```

This ensures the `polygon_count` in `ContentZoneData` reflects the true count after both filters.

### Step 5: Handle Empty Result After Net Area Filter

After the net area filter, add a check for empty result:

```python
if not net_areas:
    logger.debug(f"[{block_name}] No polygons remain after net area filtering")
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
```

Note: There's already a check for empty `net_areas` after the call, but the log message should be updated to clarify it could be due to filtering.

### Step 6: Update Function Docstring

Update the `_detect_content_zone()` docstring (lines 993-1028) to clarify filter behavior:

Change from:
```python
    Polygon filtering (when enabled):
    - Filters out small artifact polygons before calculating content zone
    - Uses area and/or shortest side thresholds to exclude noise polygons
```

To:
```python
    Polygon filtering (when enabled):
    - min_side_filter: Filters polygons by shortest straight side (gross geometry).
      Applied BEFORE net area calculation for efficiency.
    - min_area_filter: Filters polygons by NET area (own area minus contained
      polygons). Applied AFTER net area calculation to correctly handle nested
      polygons like "picture frames".
```

Also update the Args section:
```python
        min_area_filter: Minimum polygon NET area threshold. Polygons with net
            area (gross minus contained) less than this value are filtered out.
            Default 0.0 (no filtering).
```

### Step 7: Review and Update Existing Tests

Review existing tests in `TestPolygonFiltering` class to ensure they still pass:

1. `test_no_filtering_with_zero_values` - Should pass unchanged
2. `test_area_filter_removes_small_polygons` - Uses non-nested polygons, net area == gross area, should pass
3. `test_area_filter_filters_all_polygons` - Single polygon, net == gross, should pass
4. `test_side_filter_removes_narrow_polygons` - Tests side filter only, should pass unchanged
5. `test_combined_filters` - Uses non-overlapping polygons, net == gross, should pass
6. `test_filter_with_precision_and_gap_bridge` - Non-nested, should pass
7. `test_filter_boundary_value_included` - Single polygon, should pass
8. `test_only_area_filter_enabled` - Single polygon, should pass
9. `test_only_side_filter_enabled` - Single polygon, should pass

All existing tests use non-nested polygons where net area equals gross area, so they should pass without modification.

### Step 8: Run Type Checking

Execute mypy to verify type annotations are correct:

```bash
uv run mypy app/core/geometry.py
```

### Step 9: Run Linting

Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/core/geometry.py
uv run ruff format app/ --check
```

### Step 10: Run Content Zone Tests

Run the content zone test suite to verify existing tests pass:

```bash
uv run pytest app/tests/core/test_content_zone.py -v
```

### Step 11: Run Polygon Filter Tests

Run the specific polygon filtering tests:

```bash
uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v
```

### Step 12: Run All Tests

Execute the full test suite to verify zero regressions:

```bash
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests

Existing tests in `TestPolygonFiltering` class should continue to pass:
- All existing tests use non-nested polygons where net area == gross area
- No test assertion changes expected

New tests for nested polygon scenarios will be added in a subsequent unit (Unit 2).

### Integration Tests

The extractor integration tests in `test_extractor_polygon_filter.py` should continue to pass:
- These tests use the filter parameters through `extract_blocks()`
- Non-nested test scenarios should behave identically

### Edge Cases

Covered by existing tests:
1. Both filters set to 0.0 - no filtering occurs
2. Only area filter enabled - side filter does not affect results
3. Only side filter enabled - area filter does not affect results
4. All polygons filtered out - returns `content_zone_detected=False`
5. Filter values at boundary - polygon exactly at threshold passes

To be tested in subsequent units:
1. Nested polygons (picture frame scenario)
2. Multi-level nesting (box-in-box-in-box)
3. Multiple siblings within parent
4. Gross area would pass but net area fails

### Playwright MCP Tests

Not applicable for this unit - no GUI changes are included.

## Acceptance Criteria

1. `min_area_filter` uses net area (gross - contained) instead of gross area
2. `min_side_filter` continues to use gross polygon geometry (unchanged behavior)
3. No behavior change when filters are disabled (both default to 0.0)
4. All existing tests pass without modification (zero regressions)
5. `polygon_count` in result reflects count AFTER all filtering
6. Debug logging shows both side filter and net area filter results when enabled
7. Docstring clearly documents that area filter uses net area, side filter uses gross geometry
8. Type checking passes with `uv run mypy app/`
9. Linting passes with `uv run ruff check app/`

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/geometry.py` - Type check the modified geometry module
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/core/geometry.py` - Lint the modified geometry module
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v` - Run polygon filtering tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run extractor filter integration tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes

### Implementation Order

This is Unit 1 of the Net Area Filter Implementation Plan. The full plan includes:
- **Unit 1** (this spec): Core logic change in `_detect_content_zone()`
- **Unit 2**: Test asset creation (nested polygon DXF files)
- **Unit 3**: Unit tests for net area filtering scenarios
- **Unit 4**: Integration tests via `extract_blocks()`

### Performance Consideration

The change means `_calculate_net_areas()` runs on ALL shapes (after side filter) before area filtering, instead of running on pre-filtered shapes. This is acceptable because:
1. The polygon count is already bounded by `POLYGON_COUNT_THRESHOLD` (500)
2. Net area calculation is O(n^2) but n is small after threshold check
3. Correctness is more important than marginal performance for this feature

### Why Side Filter Stays Early

The side filter continues to use gross geometry and applies BEFORE net area calculation because:
1. Shortest side length is an intrinsic property that doesn't change with containment
2. Early filtering reduces the number of polygons for the O(n^2) net area calculation
3. A thin sliver polygon is a thin sliver regardless of what it contains

### Backward Compatibility

When both filters are 0.0 (default), the behavior is identical to before:
- No early side filtering occurs
- Net areas are calculated for all shapes
- No post-calculation area filtering occurs
- Largest net area polygon(s) become content zone

### Related Files

- `ai_output/025-net-area-filter-implementation-plan.md` - Full implementation plan
- `ai_output/024-net-area-filter-nested-polygons.md` - Analysis document with Option A recommendation
- `specs/039-unit-3-polygon-filtering-logic.md` - Original polygon filter implementation (now being enhanced)
