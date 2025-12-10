# Feature: Two-Stage Coordinate Snapping in Geometry Module

## Feature Description
This feature modifies the geometry module to apply two-stage coordinate snapping during region detection. Stage 1 (precision snapping) automatically fixes floating-point artifacts at line endpoints that prevent proper polygon detection. Stage 2 (gap bridging) optionally bridges intentional design gaps when enabled by the user.

The implementation uses Shapely's `snap()` function to efficiently snap coordinates within specified tolerances. Stage 1 uses extremely small tolerances (nanometer scale) appropriate for the drawing's unit system, while Stage 2 uses larger tolerances (millimeter to inch scale) for bridging intentional gaps.

This is Group B of the Two-Stage Snapping implementation plan, combining Units 3 and 4. It depends on Group A (Units 1-2) which added the constants and unit detection functions in commit `eacc6e0`.

## User Story
As a CAD professional using the DXF Block Extractor
I want floating-point precision errors to be automatically fixed during region detection
So that blocks with near-touching line endpoints correctly detect all enclosed regions without manual geometry cleanup

## Problem Statement
DXF drawings created in different CAD applications often have floating-point precision errors at line endpoints. A line that should connect at coordinate (10.0, 5.0) might actually end at (9.9999999962746, 5.0) due to floating-point arithmetic. These nanometer-scale gaps prevent the `polygonize()` function from detecting closed regions, resulting in fewer polygons being detected than visually expected.

For example, a block with a rectangle divided by a horizontal line should produce 2 regions, but a 3.7nm gap at the line endpoint causes only 1 region to be detected.

Additionally, some drawings have intentional small gaps that users may want to bridge for region detection purposes.

## Solution Statement
Modify `_extract_paint_bucket_regions()` to apply two-stage coordinate snapping after `unary_union()` and before `polygonize()`:

1. **Stage 1 (Precision Snapping)**: Always apply a very small snap tolerance (1e-6 for mm units) to fix floating-point artifacts without affecting intentional geometry. This runs automatically with no user intervention.

2. **Stage 2 (Gap Bridging)**: Optionally apply a larger snap tolerance (user-configurable or unit-appropriate default) to bridge intentional small gaps. This is disabled by default (tolerance = 0.0) and only runs when enabled by the user.

Update `_detect_content_zone()` signature to accept and propagate the tolerance parameters to `_extract_paint_bucket_regions()`.

## Relevant Files
Use these files to implement the feature:

- **app/core/geometry.py** - Contains `_extract_paint_bucket_regions()` and `_detect_content_zone()` functions that need modification. The main implementation work happens here.
- **app/core/constants.py** - Contains tolerance constants added by Group A: `PRECISION_SNAP_TOLERANCE`, `DEFAULT_PRECISION_SNAP_TOLERANCE`, `DEFAULT_GAP_BRIDGE_TOLERANCE`. Import these for default values.
- **app/tests/core/test_geometry.py** - Contains existing geometry tests. Add new test classes for snapping behavior here.
- **app/tests/core/test_content_zone.py** - Contains content zone detection tests. May need updates if signature changes affect existing tests.

### New Files
None - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
Add the `snap` import from `shapely.ops` to the geometry module. This is a one-line addition to the existing imports.

### Phase 2: Core Implementation
1. Modify `_extract_paint_bucket_regions()` to:
   - Accept two new parameters: `precision_tolerance` and `gap_bridge_tolerance`
   - Apply Stage 1 snap after `unary_union()` using `snap(merged, merged, precision_tolerance)`
   - Apply Stage 2 snap after Stage 1 if `gap_bridge_tolerance > 0`
   - Update docstring to document new parameters

2. Modify `_detect_content_zone()` to:
   - Accept two new parameters: `precision_tolerance` and `gap_bridge_tolerance`
   - Pass these parameters through to `_extract_paint_bucket_regions()`
   - Update docstring to document new parameters

### Phase 3: Integration
The modified functions maintain backward compatibility through default parameter values:
- `precision_tolerance: float = 1e-6` (sensible default for most drawings)
- `gap_bridge_tolerance: float = 0.0` (disabled by default)

Existing callers that don't pass these parameters will get the default behavior, which is Stage 1 always on and Stage 2 disabled.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add snap Import to geometry.py
- Locate the existing `from shapely.ops import polygonize, unary_union` line
- Add `snap` to the import: `from shapely.ops import polygonize, snap, unary_union`

### Step 2: Modify _extract_paint_bucket_regions Signature
- Add `precision_tolerance: float = 1e-6` parameter after `abort_event`
- Add `gap_bridge_tolerance: float = 0.0` parameter after `precision_tolerance`
- Update function docstring with new Args documentation

### Step 3: Implement Stage 1 Precision Snapping
- After `merged = unary_union(edges)` and the empty check
- Add condition: `if precision_tolerance > 0:`
- Apply snap: `merged = snap(merged, merged, precision_tolerance)`
- Add debug log: `logger.debug(f"Applied Stage 1 precision snap: tolerance={precision_tolerance}")`

### Step 4: Implement Stage 2 Gap Bridging
- After Stage 1 snap block
- Add condition: `if gap_bridge_tolerance > 0:`
- Apply snap: `merged = snap(merged, merged, gap_bridge_tolerance)`
- Add debug log: `logger.debug(f"Applied Stage 2 gap bridge: tolerance={gap_bridge_tolerance}")`

### Step 5: Modify _detect_content_zone Signature
- Add `precision_tolerance: float = 1e-6` parameter after `abort_event`
- Add `gap_bridge_tolerance: float = 0.0` parameter after `precision_tolerance`
- Update function docstring with new Args documentation

### Step 6: Update _detect_content_zone to Pass Tolerances
- Find the call to `_extract_paint_bucket_regions(block_def, abort_event)`
- Update to: `_extract_paint_bucket_regions(block_def, abort_event, precision_tolerance, gap_bridge_tolerance)`

### Step 7: Add Test Class for Precision Snapping
- Add new test class `TestPrecisionSnapping` to `app/tests/core/test_geometry.py`
- Add test `test_stage1_fixes_nanometer_gap` - Create edges with ~3.7nm gap, verify snap fixes it
- Add test `test_stage1_no_effect_on_clean_geometry` - Verify clean geometry unchanged

### Step 8: Add Test Class for Gap Bridging
- Add new test class `TestGapBridging` to `app/tests/core/test_geometry.py`
- Add test `test_stage2_disabled_by_default` - Verify tolerance=0.0 has no effect
- Add test `test_stage2_bridges_large_gaps` - Verify large tolerance bridges gaps

### Step 9: Add Tests for Tolerance Propagation
- Add test `test_tolerances_propagate_to_paint_bucket` - Verify parameters passed correctly
- Add integration test with different tolerance combinations

### Step 10: Run Validation Commands
- Run all geometry tests to verify snapping behavior
- Run full test suite to verify zero regressions
- Run type checker to verify type annotations
- Run linter to verify code style

## Testing Strategy

### Unit Tests
1. **TestPrecisionSnapping** - Tests for Stage 1 precision snapping behavior
   - `test_stage1_fixes_nanometer_gap`: Create edges with ~3.7nm gap (like SPAR Gulv issue), verify snapping produces expected polygon count
   - `test_stage1_no_effect_on_clean_geometry`: Verify clean geometry without precision errors produces same results with or without Stage 1
   - `test_stage1_uses_provided_tolerance`: Verify custom precision tolerance is applied

2. **TestGapBridging** - Tests for Stage 2 gap bridging behavior
   - `test_stage2_disabled_by_default`: Verify gap_bridge_tolerance=0.0 has no effect
   - `test_stage2_bridges_large_gaps`: Verify large tolerance bridges intentional gaps
   - `test_stage2_uses_provided_tolerance`: Verify custom gap tolerance is applied

3. **TestTolerancePropagation** - Tests for parameter passing
   - `test_detect_content_zone_passes_tolerances`: Verify tolerances propagate through call chain
   - `test_default_parameters_backward_compatible`: Verify existing tests pass without changes

### Integration Tests
- Test `_extract_paint_bucket_regions` with both tolerances set
- Test `_detect_content_zone` with tolerance parameters
- Verify existing content zone tests still pass

### Edge Cases
- `precision_tolerance = 0`: Stage 1 should be skipped
- `gap_bridge_tolerance = 0`: Stage 2 should be skipped (default behavior)
- Very large `gap_bridge_tolerance`: Should not break geometry (Shapely handles gracefully)
- Empty edge list: Should return empty list without errors
- Abort event set: Should raise GeometryAbortedError before snapping

### Playwright MCP Tests
Not applicable - no GUI changes in this unit. GUI integration is handled in Units 6-8.

## Acceptance Criteria
1. `_extract_paint_bucket_regions()` accepts `precision_tolerance` and `gap_bridge_tolerance` parameters
2. Stage 1 precision snap is applied when `precision_tolerance > 0`
3. Stage 2 gap bridge snap is applied when `gap_bridge_tolerance > 0`
4. Stage 2 has no effect when `gap_bridge_tolerance = 0.0` (default)
5. `_detect_content_zone()` accepts and passes tolerance parameters to `_extract_paint_bucket_regions()`
6. Default parameter values maintain backward compatibility with existing callers
7. Debug logging shows when each snap stage is applied
8. All new tests pass
9. All existing tests pass (zero regressions)
10. Type checker passes with no errors
11. Linter passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests including new snapping tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests to verify signature changes work
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions
- `uv run mypy app/` - Run type checker to verify type annotations
- `uv run ruff check app/` - Run linter to verify code style

## Notes
- **Dependency on Group A**: This spec requires commit `eacc6e0` from Group A which added:
  - `DXF_INSUNITS_MAP` - Maps unit codes to names
  - `PRECISION_SNAP_TOLERANCE` - Unit-specific precision tolerances
  - `DEFAULT_GAP_BRIDGE_TOLERANCE` - Unit-specific gap bridge defaults
  - `_get_drawing_units()` - Reads $INSUNITS from DXF header
  - `get_snap_tolerances()` - Calculates tolerances based on units and settings

- **Forward compatibility**: The tolerance parameters will be used by Unit 5 (extractor integration) which passes calculated tolerances from `get_snap_tolerances()` through to these geometry functions.

- **Shapely snap() behavior**: The `snap()` function snaps vertices of the first geometry to the second geometry within the specified tolerance. By using `snap(merged, merged, tolerance)`, we snap the geometry to itself, effectively snapping nearby endpoints together.

- **Performance consideration**: The `snap()` function is efficient O(n) and adds minimal overhead to the existing `unary_union()` and `polygonize()` operations.

- **No new libraries needed**: Shapely's `snap` function is already available in the installed version.
