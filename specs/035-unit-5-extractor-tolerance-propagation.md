# Feature: Extractor - Pass Tolerances Through extract_blocks

## Feature Description
This feature modifies the `extract_blocks()` function to accept tolerance-related parameters (`unit_override`, `gap_bridge_enabled`, `gap_bridge_amount`) and propagate them through to the geometry module. It uses the existing `_get_drawing_units()` and `get_snap_tolerances()` functions (implemented in Group A, commit `eacc6e0`) to calculate appropriate tolerances, then passes them to `_detect_content_zone()` (modified in Group B, commit `3f359c4`).

This completes the tolerance propagation chain from GUI settings through the extractor to the geometry module, enabling two-stage coordinate snapping based on user-configurable settings and auto-detected drawing units.

This is Unit 5 of the Two-Stage Snapping implementation plan (Group C), building on:
- **Group A (Units 1-2)**: Added constants and functions `_get_drawing_units()`, `get_snap_tolerances()` in extractor.py
- **Group B (Units 3-4)**: Modified `_extract_paint_bucket_regions()` and `_detect_content_zone()` to accept `precision_tolerance` and `gap_bridge_tolerance` parameters

## User Story
As a CAD professional using the DXF Block Extractor
I want to configure unit settings and gap bridging options when extracting blocks
So that the application can automatically apply appropriate coordinate snapping tolerances based on my settings and the drawing's unit system

## Problem Statement
The tolerance calculation infrastructure exists (Group A) and the geometry module can accept tolerance parameters (Group B), but the `extract_blocks()` function does not yet accept user-configurable tolerance parameters or use the unit detection and tolerance calculation functions. This means:

1. Users cannot override the drawing's detected units for tolerance calculation
2. Users cannot enable/disable gap bridging during extraction
3. Users cannot specify custom gap bridging amounts
4. The calculated tolerances are not passed through to `_detect_content_zone()`

Without this integration, the two-stage snapping feature remains incomplete and inaccessible to users.

## Solution Statement
Modify `extract_blocks()` to:
1. Accept three new optional parameters: `unit_override`, `gap_bridge_enabled`, `gap_bridge_amount`
2. Call `_get_drawing_units(doc)` after loading the DXF file to detect units
3. Call `get_snap_tolerances()` with detected/override units and gap bridge settings
4. Log the calculated tolerances for debugging
5. Pass `precision_tolerance` and `gap_bridge_tolerance` to `_detect_content_zone()`

All new parameters have default values that maintain backward compatibility:
- `unit_override: int | None = None` (auto-detect from file)
- `gap_bridge_enabled: bool = False` (Stage 2 disabled by default)
- `gap_bridge_amount: float | None = None` (use unit-appropriate default when enabled)

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** - Main file to modify. Contains `extract_blocks()` function that needs new parameters. Already has `_get_drawing_units()` and `get_snap_tolerances()` functions from Group A. Already imports `_detect_content_zone` from geometry module.
- **app/core/geometry.py** - Contains `_detect_content_zone()` with tolerance parameters (modified by Group B). No changes needed, just reference for understanding the interface.
- **app/core/constants.py** - Contains tolerance constants used by `get_snap_tolerances()`. No changes needed, just reference.
- **app/tests/core/extractor/test_extractor_units.py** - Existing unit tests for `_get_drawing_units()` and `get_snap_tolerances()`. Add new tests for `extract_blocks()` parameter integration here.
- **app/tests/core/extractor/conftest.py** - Contains shared fixtures for extractor tests.

### New Files
None - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
Review the existing infrastructure to understand:
1. The `extract_blocks()` function signature and structure
2. Where `_detect_content_zone()` is called within `extract_blocks()`
3. The parameter signatures of `_get_drawing_units()`, `get_snap_tolerances()`, and `_detect_content_zone()`

### Phase 2: Core Implementation
1. Add three new parameters to `extract_blocks()` with appropriate defaults
2. After loading the DXF file (`doc = ezdxf.readfile(file_path)`), call `_get_drawing_units(doc)`
3. Call `get_snap_tolerances()` with detected units and new parameters
4. Add logging statement showing calculated tolerances
5. Update the `_detect_content_zone()` call to pass tolerance parameters

### Phase 3: Integration
1. Update function docstring with new parameter documentation
2. Ensure backward compatibility by verifying default parameter behavior
3. Add comprehensive tests for new functionality

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update extract_blocks Function Signature
- Add `unit_override: int | None = None` parameter after `abort_event`
- Add `gap_bridge_enabled: bool = False` parameter after `unit_override`
- Add `gap_bridge_amount: float | None = None` parameter after `gap_bridge_enabled`
- Update function signature to:
```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
) -> ExtractionResult:
```

### Step 2: Update extract_blocks Docstring
- Add Args documentation for `unit_override`:
  - "User-selected unit override. -1 for auto-detect, or $INSUNITS value (0=Unitless, 1=IN, 2=FT, 4=MM, 5=CM, 6=M). None = auto."
- Add Args documentation for `gap_bridge_enabled`:
  - "Enable Stage 2 gap bridging. When True, applies gap bridge tolerance to bridge intentional gaps."
- Add Args documentation for `gap_bridge_amount`:
  - "Custom gap bridge tolerance. None = use default for unit."

### Step 3: Add Unit Detection and Tolerance Calculation
- After `doc = ezdxf.readfile(file_path)` line (around line 898)
- Add call to detect drawing units: `detected_units = _get_drawing_units(doc)`
- Add call to calculate tolerances:
```python
precision_tolerance, gap_bridge_tolerance = get_snap_tolerances(
    detected_units,
    unit_override,
    gap_bridge_enabled,
    gap_bridge_amount,
)
```
- Add logging statement:
```python
logger.info(
    f"Using tolerances: precision={precision_tolerance}, "
    f"gap_bridge={gap_bridge_tolerance} "
    f"(units={'auto' if unit_override in (None, -1) else unit_override})"
)
```

### Step 4: Update _detect_content_zone Call
- Find the call to `_detect_content_zone(block_def, bbox, abort_event)` (around line 1046)
- Update to pass tolerance parameters:
```python
content_zone_result = _detect_content_zone(
    block_def,
    bbox,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
)
```

### Step 5: Add Tests for Parameter Passing
- Add new test class `TestExtractBlocksToleranceParameters` to `app/tests/core/extractor/test_extractor_units.py`
- Add test `test_extract_blocks_accepts_unit_override_parameter` - Verify function accepts unit_override parameter
- Add test `test_extract_blocks_accepts_gap_bridge_enabled_parameter` - Verify function accepts gap_bridge_enabled parameter
- Add test `test_extract_blocks_accepts_gap_bridge_amount_parameter` - Verify function accepts gap_bridge_amount parameter
- Add test `test_extract_blocks_default_parameters_work` - Verify function works without new parameters (backward compatibility)

### Step 6: Add Integration Tests
- Add test `test_extract_blocks_with_unit_override` - Call with unit_override=4 (mm), verify no errors
- Add test `test_extract_blocks_with_gap_bridge_enabled` - Call with gap_bridge_enabled=True, verify no errors
- Add test `test_extract_blocks_with_custom_gap_amount` - Call with gap_bridge_amount=1.0, verify no errors
- Add test `test_extract_blocks_with_all_tolerance_params` - Call with all three new params set

### Step 7: Add Edge Case Tests
- Add test `test_extract_blocks_unit_override_minus_one_uses_auto` - Verify -1 behaves like None
- Add test `test_extract_blocks_gap_bridge_disabled_ignores_amount` - Verify amount is ignored when disabled
- Add test `test_extract_blocks_invalid_unit_uses_fallback` - Test with unsupported unit code

### Step 8: Run Validation Commands
- Run all tests to verify implementation is correct with zero regressions
- Run type checker to verify type annotations are correct
- Run linter to verify code style

## Testing Strategy

### Unit Tests
1. **Parameter Acceptance Tests** - Verify `extract_blocks()` accepts new parameters
   - Function accepts `unit_override` parameter of various valid values
   - Function accepts `gap_bridge_enabled` parameter (True/False)
   - Function accepts `gap_bridge_amount` parameter (None, positive float)
   - Function works with default parameters (backward compatibility)

2. **Integration Tests** - Verify tolerance propagation works end-to-end
   - Extraction with unit_override succeeds without errors
   - Extraction with gap_bridge_enabled=True succeeds without errors
   - Extraction with custom gap_bridge_amount succeeds without errors
   - Extraction with all parameters set succeeds without errors

### Integration Tests
- Test `extract_blocks()` with real DXF files from test assets
- Verify content zone detection still works with new tolerance parameters
- Verify extraction results are consistent with and without tolerance parameters (when gap bridging disabled)

### Edge Cases
- `unit_override = -1` (should use auto-detect, same as None)
- `unit_override = None` (default, auto-detect)
- `unit_override = 99` (unsupported unit code, should use fallback)
- `gap_bridge_enabled = False` with `gap_bridge_amount = 100.0` (amount should be ignored)
- `gap_bridge_enabled = True` with `gap_bridge_amount = None` (should use unit default)
- `gap_bridge_enabled = True` with `gap_bridge_amount = 0.0` (should use unit default)
- Empty DXF file with tolerance parameters
- DXF file with no $INSUNITS header (should default to unitless)

### Playwright MCP Tests
Not applicable - no GUI changes in this unit. GUI integration is handled in Units 6-8.

## Acceptance Criteria
1. `extract_blocks()` accepts `unit_override: int | None = None` parameter
2. `extract_blocks()` accepts `gap_bridge_enabled: bool = False` parameter
3. `extract_blocks()` accepts `gap_bridge_amount: float | None = None` parameter
4. `extract_blocks()` calls `_get_drawing_units()` to detect units from loaded document
5. `extract_blocks()` calls `get_snap_tolerances()` with detected/override units and gap bridge settings
6. `extract_blocks()` logs calculated tolerances at INFO level
7. `extract_blocks()` passes `precision_tolerance` and `gap_bridge_tolerance` to `_detect_content_zone()`
8. Default parameter values maintain backward compatibility (existing tests pass without modification)
9. All new tests pass
10. All existing tests pass (zero regressions)
11. Type checker passes with no errors
12. Linter passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run unit detection and new tolerance parameter tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests to verify signature compatibility
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions
- `uv run mypy app/` - Run type checker to verify type annotations
- `uv run ruff check app/` - Run linter to verify code style

## Notes
- **Dependency on Group A (commit `eacc6e0`)**: This spec requires the functions `_get_drawing_units()` and `get_snap_tolerances()` which were added to extractor.py by Group A.

- **Dependency on Group B (commit `3f359c4`)**: This spec requires `_detect_content_zone()` to accept `precision_tolerance` and `gap_bridge_tolerance` parameters, which was implemented by Group B.

- **Forward compatibility**: The parameters added here will be passed from the GUI in Units 6-8. The GUI will construct these parameters based on user selections in dropdown menus and checkboxes.

- **Logging strategy**: An INFO level log is added to show the calculated tolerances for debugging. This helps users understand what tolerances are being applied during extraction.

- **No new libraries needed**: All required functionality uses existing imports and functions.

- **Default behavior**: When called without new parameters, `extract_blocks()` behaves exactly as before:
  - Auto-detects units from DXF file
  - Stage 1 precision snapping is always applied with unit-appropriate tolerance
  - Stage 2 gap bridging is disabled (tolerance = 0.0)
