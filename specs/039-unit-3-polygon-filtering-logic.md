# Feature: Polygon Filtering Logic in Content Zone Detection (Unit 3)

## Feature Description
This feature adds polygon filtering logic to the `_detect_content_zone()` function, allowing small artifact polygons to be filtered out before calculating the content zone bounding box. The function signature is updated to accept two new parameters (`min_area_filter` and `min_side_filter`), and filtering logic is added after polygon extraction to exclude polygons that don't meet the minimum area or minimum side length thresholds.

This is Unit 3 of the Polygon Filter Implementation, building on:
- Unit 1 (commit 0332046): Added filter constants and `PolygonMetrics` TypedDict to constants.py and types.py
- Unit 2 (commit 62af902): Added `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions to geometry.py

## User Story
As a CAD engineer processing DXF files
I want to filter out small artifact polygons from content zone calculations
So that the content zone bounding box accurately reflects the main drawing area without being skewed by dust, debris, construction lines, or annotation elements

## Problem Statement
When calculating content zone bounding boxes, small artifact polygons can skew the results, leading to inaccurate trim values. These artifacts include:
- Dust or debris marks
- Construction lines
- Small annotation elements
- Drawing artifacts

Currently, `_detect_content_zone()` processes all extracted polygons equally, which can result in content zones that don't accurately represent the main drawing area. The calculation functions from Unit 2 (`calculate_polygon_area()` and `calculate_shortest_straight_side()`) exist but are not yet integrated into the content zone detection workflow.

## Solution Statement
Update the `_detect_content_zone()` function to:
1. Accept two new optional parameters: `min_area_filter` (default 0.0) and `min_side_filter` (default 0.0)
2. After extracting polygons with `_extract_paint_bucket_regions()`, filter out polygons that:
   - Have area less than `min_area_filter` (when > 0)
   - Have shortest straight side less than `min_side_filter` (when > 0)
3. Log the filtering results for debugging
4. Continue with net area calculation using only the filtered polygon set

## Relevant Files
Use these files to implement the feature:

- **app/core/geometry.py** - Main implementation file
  - Update `_detect_content_zone()` function signature to add new parameters
  - Add filtering logic after polygon extraction
  - Uses existing `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions

- **app/tests/core/test_content_zone.py** - Content zone test module
  - Add new test class `TestPolygonFiltering` for filter parameter tests
  - Test filtering behavior with various configurations
  - Test edge cases (all polygons filtered, no filtering when disabled)

- **app/core/extractor.py** - Extractor module (reference only)
  - Calls `_detect_content_zone()` - will need updates in Unit 4 to pass filter parameters
  - No changes in this unit - just ensure current call continues to work with default values

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Review the existing `_detect_content_zone()` function signature and the location where filtering should be added (after `_extract_paint_bucket_regions()` call). Confirm that `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions from Unit 2 are available and working correctly.

### Phase 2: Core Implementation
1. Update `_detect_content_zone()` function signature to add `min_area_filter` and `min_side_filter` parameters with default values of 0.0
2. Add filtering logic after the polygon extraction step
3. Update the docstring to document the new parameters

### Phase 3: Integration
Add comprehensive unit tests to verify:
- Filtering is applied correctly when filter values > 0
- No filtering occurs when filter values are 0 (default behavior preserved)
- Both filters can work independently or together
- Edge cases are handled (all polygons filtered, empty input)

## Step by Step Tasks

### Step 1: Update _detect_content_zone() Function Signature
Update the `_detect_content_zone()` function in `app/core/geometry.py` to accept two new parameters:

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,      # NEW
    min_side_filter: float = 0.0,      # NEW
) -> ContentZoneData:
```

Update the function docstring to document the new parameters:
- `min_area_filter`: Minimum polygon area threshold. Polygons with area less than this value are filtered out. Default 0.0 (no filtering).
- `min_side_filter`: Minimum shortest side length threshold. Polygons with shortest straight side less than this value are filtered out. Default 0.0 (no filtering).

### Step 2: Add Polygon Filtering Logic
After the line `all_shapes = _extract_paint_bucket_regions(...)` in `_detect_content_zone()`, add the filtering logic:

```python
# Filter polygons by area and shortest side if filters are enabled
if min_area_filter > 0 or min_side_filter > 0:
    filtered_shapes: list[Polygon] = []
    for shape in all_shapes:
        # Check area filter
        if min_area_filter > 0:
            area = calculate_polygon_area(shape)
            if area < min_area_filter:
                continue
        # Check side filter
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
```

This should be inserted right after the `polygon_count = len(all_shapes)` assignment (around line 1046), before the check for zero polygons.

### Step 3: Update Polygon Count After Filtering
After filtering, update the `polygon_count` variable to reflect the filtered count:

```python
# Update polygon count after filtering
polygon_count = len(all_shapes)
```

The existing debug log `f"[{block_name}] Found {polygon_count} paint-bucket regions"` should remain to show the pre-filtered count, and the new filtering log shows the transition.

### Step 4: Add Unit Tests for Default Behavior Preserved
Add test to `app/tests/core/test_content_zone.py` to verify default behavior is preserved when filters are disabled:

```python
class TestPolygonFiltering:
    """Test suite for polygon filtering in _detect_content_zone."""

    def test_no_filtering_with_zero_values(self) -> None:
        """Verify no filtering occurs when filter values are 0 (default)."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        # Default behavior with zeros
        result = _detect_content_zone(
            block, bbox,
            min_area_filter=0.0,
            min_side_filter=0.0
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2  # Both polygons should be present
```

### Step 5: Add Unit Tests for Area Filtering
Add tests to verify area filtering works correctly:

```python
    def test_area_filter_removes_small_polygons(self) -> None:
        """Verify polygons below min_area threshold are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="AREA_TEST")
        # Large polygon (100x100 = 10000 sq units)
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 100), (0, 100)], close=True
        )
        # Small polygon (5x5 = 25 sq units)
        block.add_lwpolyline(
            [(10, 10), (15, 10), (15, 15), (10, 15)], close=True
        )

        bbox = _get_block_bounding_box(block)

        # Filter out polygons with area < 100
        result = _detect_content_zone(
            block, bbox,
            min_area_filter=100.0,
            min_side_filter=0.0
        )

        assert result["content_zone_detected"] is True
        # Should have filtered out the small polygon, leaving only the large one
        # The large polygon should be the content zone

    def test_area_filter_filters_all_polygons(self) -> None:
        """Verify behavior when all polygons are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_SMALL")
        # Small polygon (10x10 = 100 sq units)
        block.add_lwpolyline(
            [(0, 0), (10, 0), (10, 10), (0, 10)], close=True
        )

        bbox = _get_block_bounding_box(block)

        # Filter threshold higher than all polygon areas
        result = _detect_content_zone(
            block, bbox,
            min_area_filter=500.0,
            min_side_filter=0.0
        )

        # All polygons filtered - should return empty content zone
        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 0
```

### Step 6: Add Unit Tests for Side Filtering
Add tests to verify side filtering works correctly:

```python
    def test_side_filter_removes_narrow_polygons(self) -> None:
        """Verify polygons with short sides are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SIDE_TEST")
        # Wide polygon with sides >= 50 (100x50)
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
        )
        # Narrow polygon with short side = 5 (100x5)
        block.add_lwpolyline(
            [(0, 60), (100, 60), (100, 65), (0, 65)], close=True
        )

        bbox = _get_block_bounding_box(block)

        # Filter out polygons with shortest side < 20
        result = _detect_content_zone(
            block, bbox,
            min_area_filter=0.0,
            min_side_filter=20.0
        )

        assert result["content_zone_detected"] is True
        # Should have filtered out the narrow polygon
```

### Step 7: Add Unit Tests for Combined Filtering
Add tests to verify both filters work together:

```python
    def test_combined_filters(self) -> None:
        """Verify both filters work together."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="COMBINED_TEST")
        # Large polygon with reasonable sides (100x50 = 5000 sq units, shortest side 50)
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 50), (0, 50)], close=True
        )
        # Small polygon but with okay sides (10x10 = 100 sq units, sides 10)
        block.add_lwpolyline(
            [(5, 55), (15, 55), (15, 65), (5, 65)], close=True
        )
        # Large area but narrow (200x2 = 400 sq units, shortest side 2)
        block.add_lwpolyline(
            [(0, 70), (200, 70), (200, 72), (0, 72)], close=True
        )

        bbox = _get_block_bounding_box(block)

        # Filter: area >= 200 AND shortest side >= 5
        result = _detect_content_zone(
            block, bbox,
            min_area_filter=200.0,
            min_side_filter=5.0
        )

        assert result["content_zone_detected"] is True
        # Only the first polygon should pass both filters
```

### Step 8: Add Import Statement for Tests
Ensure the test file imports the `_detect_content_zone` function (should already be imported) and verify test file structure follows existing patterns.

### Step 9: Run Type Checking
Execute mypy to verify type annotations are correct:

```bash
uv run mypy app/core/geometry.py
```

### Step 10: Run Linting
Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/core/geometry.py
uv run ruff format app/ --check
```

### Step 11: Run Geometry Tests
Run the geometry test suite to verify existing functionality is preserved:

```bash
uv run pytest app/tests/core/test_geometry.py -v
```

### Step 12: Run Content Zone Tests
Run the content zone test suite including new tests:

```bash
uv run pytest app/tests/core/test_content_zone.py -v
```

### Step 13: Run All Tests
Execute the full test suite to verify zero regressions:

```bash
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests
1. **TestPolygonFiltering** class in `test_content_zone.py`:
   - `test_no_filtering_with_zero_values` - Verify default behavior preserved
   - `test_area_filter_removes_small_polygons` - Verify area filtering works
   - `test_area_filter_filters_all_polygons` - Verify empty result when all filtered
   - `test_side_filter_removes_narrow_polygons` - Verify side filtering works
   - `test_combined_filters` - Verify both filters work together
   - `test_filter_with_precision_and_gap_bridge` - Verify filters work with other parameters

### Integration Tests
Not required for this unit - extractor integration will be tested in Unit 4. The current `extract_blocks()` call to `_detect_content_zone()` will continue to work with default filter values (0.0).

### Edge Cases
1. Both filters set to 0.0 - no filtering should occur
2. Only area filter enabled - side filter should not affect results
3. Only side filter enabled - area filter should not affect results
4. All polygons filtered out - should return `content_zone_detected=False`
5. Filter values at boundary - polygon exactly at threshold should pass
6. Empty polygon list - filtering should handle gracefully
7. Degenerate polygons - should be handled by underlying calculation functions

### Playwright MCP Tests
Not applicable for this unit - no GUI changes are included.

## Acceptance Criteria
1. `_detect_content_zone()` accepts `min_area_filter` and `min_side_filter` parameters
2. Both parameters default to 0.0 (no filtering)
3. When `min_area_filter > 0`, polygons with area below threshold are excluded
4. When `min_side_filter > 0`, polygons with shortest side below threshold are excluded
5. Both filters can be used together (AND logic - polygon must pass both filters)
6. Filtering is logged at debug level showing before/after polygon counts
7. `polygon_count` in result reflects filtered count when filters are applied
8. Existing tests continue to pass (backward compatibility)
9. All new tests pass
10. Type checking passes with `uv run mypy app/`
11. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/geometry.py` - Type check the modified geometry module
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/core/geometry.py` - Lint the modified geometry module
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v` - Run new filtering tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests for regression
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This is Unit 3 of a multi-unit implementation plan for polygon filtering (source: `ai_output/020-polygon-filter-implementation-plan.md`)
- Unit 1 (commit 0332046) added constants and `PolygonMetrics` TypedDict
- Unit 2 (commit 62af902) added `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions
- Unit 4 will update `extract_blocks()` and `get_snap_tolerances()` to pass filter parameters through to `_detect_content_zone()`
- Unit 5 will add GUI controls (checkboxes and entry fields) for the filter settings
- Filter values are in DXF drawing units (same as precision fix and gap bridge amounts)
- The filtering uses AND logic: a polygon must pass both area AND side filters if both are enabled
- Filtering happens AFTER polygon extraction but BEFORE the polygon count threshold check
- The `polygon_count` in the result will reflect the filtered count, which may affect threshold behavior
