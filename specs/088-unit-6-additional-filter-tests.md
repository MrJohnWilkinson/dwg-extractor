# Chore: Unit 6 - Additional Pre-filter and Curved Filter Tests

## Chore Description

This unit reviews existing test coverage and adds any missing tests for the dual-stage filter feature. The goal is to ensure comprehensive test coverage for:

1. **Pre-filters** (in `_extract_all_edges`):
   - `skip_curved_entities`: Skip CIRCLE and ARC entities during edge extraction
   - `min_line_length`: Filter out LINE entities shorter than a threshold

2. **Post-filters** (in `_detect_content_zone`):
   - `curved_filter_enabled`: Filter out polygons containing curved edges

### Existing Test Coverage (from Units 1-5)

**Already covered:**
- `test_constants.py`: TestPreFilterConstants, TestCurvedFilterConstants - constant value tests
- `test_geometry.py`: TestPreFilterLineLengthFilter, TestPreFilterSkipCurvedEntities, TestPolygonHasCurvedEdges - core function tests
- `test_main_settings_sync.py`: TestPreFilterSettingsSync - settings synchronization tests
- `test_extractor_polygon_filter.py`: TestExtractBlocksFilterParameters - min_area/min_side filter integration tests

**Identified Gaps:**
1. **Integration tests for `extract_blocks()` with pre-filter parameters** - No tests verify `skip_curved_entities`, `min_line_length_filter_enabled`, or `curved_filter_enabled` are properly passed through extract_blocks
2. **Tests for `curved_filter_enabled` in `_detect_content_zone()`** - No tests verify this parameter filters curved polygons
3. **End-to-end tests with real DXF files** containing circles/arcs - Need tests using `circles_arcs_points.dxf` and `circle_arc_hatch_edges_test.dxf`

## Relevant Files

Use these files to resolve the chore:

- `app/tests/core/test_geometry.py` - Contains existing pre-filter and curved detection tests; may need additional tests for `_detect_content_zone` with `curved_filter_enabled`
- `app/tests/core/test_content_zone.py` - Contains content zone tests but lacks `curved_filter_enabled` tests
- `app/tests/core/extractor/test_extractor_polygon_filter.py` - Contains filter integration tests but lacks pre-filter and curved-filter parameters
- `app/core/geometry.py` - Source for `_extract_all_edges`, `_detect_content_zone`, `_polygon_has_curved_edges`
- `app/core/extractor.py` - Source for `extract_blocks` with pre-filter and curved-filter parameters
- `app/tests/assets/circles_arcs_points.dxf` - Test file with CIRCLE/ARC blocks
- `app/tests/assets/circle_arc_hatch_edges_test.dxf` - Test file with various circle/arc/hatch configurations

### New Files

- `app/tests/core/extractor/test_extractor_prefilters.py` - Dedicated tests for extract_blocks with pre-filter and curved-filter parameters

## Step by Step Tasks

### Step 1: Add `curved_filter_enabled` Tests to test_content_zone.py

Add a new test class `TestCurvedFilterIntegration` to `app/tests/core/test_content_zone.py`:

- `test_curved_filter_disabled_keeps_all_polygons` - Verify default behavior preserves polygons with curved edges
- `test_curved_filter_enabled_removes_curved_polygons` - Verify curved polygons are filtered when enabled
- `test_curved_filter_keeps_straight_polygons` - Verify rectangles and triangles pass through the filter
- `test_curved_filter_with_circle_approximation` - Use a polygon approximating a circle (many vertices on curved path)
- `test_curved_filter_combined_with_area_filter` - Verify both filters work together
- `test_curved_filter_all_filtered_returns_empty` - Verify behavior when all polygons are filtered

### Step 2: Create test_extractor_prefilters.py

Create new test file `app/tests/core/extractor/test_extractor_prefilters.py` with comprehensive integration tests:

**Class: TestExtractBlocksPreFilterParameters**
- `test_accepts_skip_curved_entities_parameter` - Verify parameter is accepted
- `test_accepts_min_line_length_filter_enabled_parameter` - Verify parameter is accepted
- `test_accepts_min_line_length_filter_amount_parameter` - Verify parameter is accepted
- `test_accepts_curved_filter_enabled_parameter` - Verify parameter is accepted
- `test_accepts_all_prefilter_parameters` - Verify all new parameters work together

**Class: TestExtractBlocksSkipCurvedEntities**
- `test_skip_curved_entities_disabled_by_default` - Verify default behavior extracts circles/arcs
- `test_skip_curved_entities_affects_content_zone` - Verify content zone detection changes when circles skipped (use `circles_arcs_points.dxf`)
- `test_skip_curved_entities_with_mixed_block` - Use TEST_MIXED block from test DXF

**Class: TestExtractBlocksMinLineLengthFilter**
- `test_min_line_length_filter_disabled_by_default` - Verify default behavior
- `test_min_line_length_filter_enabled_filters_short_lines` - Verify short lines excluded

**Class: TestExtractBlocksCurvedFilter**
- `test_curved_filter_disabled_by_default` - Verify default behavior
- `test_curved_filter_enabled_affects_polygon_count` - Verify curved polygons filtered from results

**Class: TestExtractBlocksPreFilterBackwardCompatibility**
- `test_default_prefilters_disabled` - Verify backward compatibility
- `test_results_consistent_with_prefilters_explicitly_disabled` - Compare results

### Step 3: Add Edge Case Tests to test_geometry.py

Add additional edge case tests to existing classes in `app/tests/core/test_geometry.py`:

**Add to TestPolygonHasCurvedEdges:**
- `test_hexagon_not_curved` - Regular hexagon should not be detected as curved
- `test_very_slight_curve_detected` - Edge case with minimal curvature
- `test_single_curved_segment_in_rectangle` - Rectangle with one rounded corner

**Add to TestPreFilterSkipCurvedEntities:**
- `test_skip_curved_with_hatch_containing_arc` - Verify HATCH with ArcEdge is handled

### Step 4: Run All Tests and Verify Zero Regressions

Execute the validation commands to ensure all tests pass.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constant tests to verify pre-filter and curved-filter constant coverage
- `uv run pytest app/tests/core/test_geometry.py -v -k "PreFilter or Curved"` - Run pre-filter and curved edge detection tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests including new curved filter integration tests
- `uv run pytest app/tests/core/extractor/test_extractor_prefilters.py -v` - Run new pre-filter integration tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v -k "PreFilter"` - Run settings sync tests
- `uv run pytest app/tests/ -v` - Run complete test suite to verify zero regressions
- `uv run mypy app/` - Run type checking to ensure no type errors

## Notes

1. **Test File Assets**: The tests should use existing DXF test files:
   - `circles_arcs_points.dxf` - Contains TEST_CIRCLES, TEST_ARCS, TEST_POINTS, TEST_MIXED blocks
   - `circle_arc_hatch_edges_test.dxf` - Contains CIRCLE_REGION, ARC_REGION, HATCH_* blocks

2. **Polygon Curved Detection**: The `_polygon_has_curved_edges()` function detects curves by checking if 4 or more consecutive points lie on an arc (using cross-product deviation analysis). A tolerance parameter controls sensitivity.

3. **Pre-filter Application Point**: Pre-filters (`skip_curved_entities`, `min_line_length`) are applied in `_extract_all_edges()` BEFORE polygonization. The curved post-filter is applied in `_detect_content_zone()` AFTER polygon extraction.

4. **Test Isolation**: Integration tests should verify that parameters flow correctly from `extract_blocks()` through to `_detect_content_zone()`. Unit tests in geometry module already verify the filtering logic itself works correctly.

5. **All 999 tests currently passing**: The implementation from Units 1-5 is complete. This unit adds additional test coverage for completeness but does not change any production code.
