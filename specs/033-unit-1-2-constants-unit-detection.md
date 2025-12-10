# Feature: Drawing Unit Constants and Unit Detection Functions

## Feature Description
This feature adds drawing unit configuration constants and unit detection functions to support two-stage coordinate snapping. It includes:

1. **DXF $INSUNITS Mappings** - Maps DXF header unit codes to human-readable names
2. **GUI Unit Selection Options** - Provides dropdown options for user unit override
3. **Stage 1 Precision Snap Tolerances** - Unit-appropriate tolerances to fix floating-point artifacts
4. **Stage 2 Gap Bridge Tolerances** - Default tolerances for intentional gap bridging per unit system
5. **Unit Detection Function** - Reads $INSUNITS from DXF header to auto-detect drawing units
6. **Tolerance Calculation Function** - Computes appropriate snap tolerances based on units and user settings

This is the foundational work (Units 1-2 of the Two-Stage Snapping implementation plan) that establishes the constants and core functions needed by subsequent units.

## User Story
As a CAD professional using the DXF Block Extractor
I want the application to automatically detect drawing units and apply appropriate coordinate snapping tolerances
So that floating-point precision artifacts are fixed automatically and I can optionally bridge intentional design gaps with unit-appropriate defaults

## Problem Statement
DXF drawings created in different CAD applications often have floating-point precision errors at line endpoints. A line that should connect at coordinate (10.0, 5.0) might actually end at (9.9999999962746, 5.0) due to floating-point arithmetic. These nanometer-scale gaps prevent proper polygon detection.

Additionally, different drawings use different unit systems (millimeters, inches, meters, etc.), and snap tolerances must be appropriate for each unit system - a 1e-6 tolerance is appropriate for millimeters but too coarse for meters.

## Solution Statement
Implement a constants module with:
- Unit code mappings for DXF $INSUNITS header values
- Precision snap tolerances scaled appropriately for each unit system
- Gap bridge default tolerances representing typical CAD drafting gaps in each unit
- GUI dropdown options for manual unit override

Implement extractor functions to:
- Auto-detect drawing units from the $INSUNITS header variable
- Calculate appropriate tolerances based on detected/override units and user gap bridge settings

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Contains application-wide constants. Add new unit mapping and tolerance constants here following the existing pattern of grouped constants with docstrings.
- **app/core/extractor.py** - Contains DXF extraction logic. Add unit detection function `_get_drawing_units()` and tolerance calculation function `get_snap_tolerances()` here. The file already imports from ezdxf and has access to Drawing objects.
- **app/tests/core/test_constants.py** - Contains tests for constants module. Add new tests for unit constants here following the existing test pattern.

### New Files
- **app/tests/core/extractor/test_extractor_units.py** - New test file for unit detection and tolerance calculation tests, following the existing test file organization in the extractor test directory.

## Implementation Plan

### Phase 1: Foundation
Add all unit-related constants to the constants module:
- DXF_INSUNITS_MAP dictionary mapping $INSUNITS codes to unit names
- UNIT_SELECTION_OPTIONS dictionary for GUI dropdown values
- PRECISION_SNAP_TOLERANCE dictionary with unit-appropriate Stage 1 tolerances
- DEFAULT_PRECISION_SNAP_TOLERANCE fallback constant
- DEFAULT_GAP_BRIDGE_TOLERANCE dictionary with unit-appropriate Stage 2 defaults
- GAP_BRIDGE_MIN and GAP_BRIDGE_MAX input constraints

### Phase 2: Core Implementation
Add unit detection and tolerance calculation functions to extractor module:
- `_get_drawing_units(doc: Drawing) -> int` - Reads $INSUNITS from DXF header
- `get_snap_tolerances(detected_units, override_units, gap_bridge_enabled, gap_bridge_amount) -> tuple[float, float]` - Calculates both tolerance values

### Phase 3: Integration
These functions will be called by `extract_blocks()` in future units. For now, they are standalone utilities that can be tested independently. The constants are exported for use by both the extractor and GUI modules.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Unit Constants to constants.py
- Add section header comment "# Drawing Unit Configuration"
- Add `DXF_INSUNITS_MAP: dict[int, str]` mapping codes 0, 1, 2, 4, 5, 6 to unit names
- Add `UNIT_SELECTION_OPTIONS: dict[str, int]` with "DXF/DWG" (-1), "MM" (4), "CM" (5), "M" (6), "IN" (1), "FT" (2)
- Add `PRECISION_SNAP_TOLERANCE: dict[int, float]` with tolerances for each unit code
- Add `DEFAULT_PRECISION_SNAP_TOLERANCE: float = 1e-6` with docstring
- Add `DEFAULT_GAP_BRIDGE_TOLERANCE: dict[int, float]` with default gap amounts per unit
- Add `GAP_BRIDGE_MIN: float = 0.0` and `GAP_BRIDGE_MAX: float = 10000.0` with docstring

### Step 2: Add Constants Tests to test_constants.py
- Add new test class `TestDrawingUnitConstants`
- Add test `test_dxf_insunits_map_has_all_supported_units` - verify keys 0, 1, 2, 4, 5, 6 exist
- Add test `test_unit_selection_options_keys_match_display_labels` - verify GUI labels are strings
- Add test `test_precision_snap_tolerances_in_reasonable_range` - verify all values between 1e-9 and 1e-3
- Add test `test_gap_bridge_tolerances_in_reasonable_range` - verify all values between 0.01 and 1000
- Add test `test_gap_bridge_constraints_valid` - verify MIN < MAX

### Step 3: Add Unit Detection Function to extractor.py
- Add imports: `DXF_INSUNITS_MAP`, `PRECISION_SNAP_TOLERANCE`, `DEFAULT_PRECISION_SNAP_TOLERANCE`, `DEFAULT_GAP_BRIDGE_TOLERANCE`
- Add function `_get_drawing_units(doc: Drawing) -> int`
- Implement: read `doc.header.get("$INSUNITS", 0)`
- Log detected unit name using DXF_INSUNITS_MAP
- Handle AttributeError/KeyError exceptions, return 0 as fallback

### Step 4: Add Tolerance Calculation Function to extractor.py
- Add function `get_snap_tolerances(detected_units: int, override_units: int | None, gap_bridge_enabled: bool, gap_bridge_amount: float | None) -> tuple[float, float]`
- Determine effective units: use override if provided and not -1, else use detected
- Calculate precision_tolerance from PRECISION_SNAP_TOLERANCE dict with fallback
- Calculate gap_bridge_tolerance: 0.0 if disabled, user amount if provided, else default for unit
- Log calculated tolerances
- Return tuple of (precision_tolerance, gap_bridge_tolerance)

### Step 5: Create Unit Detection Tests
- Create new file `app/tests/core/extractor/test_extractor_units.py`
- Add test class `TestGetDrawingUnits`
- Add test `test_detects_mm_units` - mock doc with $INSUNITS=4, verify returns 4
- Add test `test_detects_inch_units` - mock doc with $INSUNITS=1, verify returns 1
- Add test `test_detects_meter_units` - mock doc with $INSUNITS=6, verify returns 6
- Add test `test_missing_insunits_returns_zero` - mock KeyError, verify returns 0
- Add test `test_invalid_header_returns_zero` - mock AttributeError, verify returns 0

### Step 6: Create Tolerance Calculation Tests
- Add test class `TestGetSnapTolerances` in same file
- Add test `test_auto_detect_uses_detected_units` - override=None uses detected
- Add test `test_override_minus_one_uses_detected_units` - override=-1 uses detected
- Add test `test_override_replaces_detected_units` - override=6 uses meter tolerance
- Add test `test_gap_bridge_disabled_returns_zero` - gap_bridge_enabled=False returns 0.0
- Add test `test_gap_bridge_enabled_uses_default` - enabled with amount=None uses default
- Add test `test_gap_bridge_custom_amount_used` - enabled with amount=50.0 uses 50.0
- Add test `test_unknown_unit_uses_fallback_tolerance` - unknown unit uses DEFAULT

### Step 7: Run Validation Commands
- Run all tests to verify implementation is correct with zero regressions
- Run type checker to verify type annotations are correct
- Run linter to verify code style

## Testing Strategy

### Unit Tests
1. **Constants Tests** - Verify all constants exist and have reasonable values
   - All unit codes in DXF_INSUNITS_MAP
   - All tolerance values in expected ranges
   - Constraints are valid (MIN < MAX)

2. **Unit Detection Tests** - Verify _get_drawing_units behavior
   - Returns correct value for each supported $INSUNITS code
   - Returns 0 for missing header
   - Returns 0 for invalid/corrupt header

3. **Tolerance Calculation Tests** - Verify get_snap_tolerances behavior
   - Correct tolerance for each unit
   - Override behavior works correctly
   - Gap bridge enable/disable works correctly
   - Custom gap amount overrides default

### Integration Tests
No integration tests needed for this unit - these are standalone functions that will be integrated in Unit 5.

### Edge Cases
- $INSUNITS header missing entirely
- $INSUNITS value not in supported list (e.g., 3 = miles)
- override_units = -1 (should use detected)
- override_units = None (should use detected)
- gap_bridge_amount = 0 (should use default)
- gap_bridge_amount = negative (should use default)

### Playwright MCP Tests
Not applicable - no GUI changes in this unit.

## Acceptance Criteria
1. All constants are defined in constants.py with correct values matching the implementation plan
2. `_get_drawing_units()` correctly reads $INSUNITS from any valid DXF document
3. `_get_drawing_units()` returns 0 for missing or invalid $INSUNITS
4. `get_snap_tolerances()` returns correct precision tolerance for each unit system
5. `get_snap_tolerances()` respects unit override when provided
6. `get_snap_tolerances()` returns 0.0 gap tolerance when gap bridging is disabled
7. `get_snap_tolerances()` returns unit-appropriate default when gap bridging is enabled without custom amount
8. `get_snap_tolerances()` uses custom amount when provided
9. All new tests pass
10. All existing tests continue to pass (zero regressions)
11. Type checker passes with no errors
12. Linter passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests
- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run new unit detection tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions
- `uv run mypy app/` - Run type checker to verify type annotations
- `uv run ruff check app/` - Run linter to verify code style

## Notes
- This is Unit 1-2 of the Two-Stage Snapping implementation plan (Group A)
- No prior unit learnings to incorporate (this is the first unit)
- The functions added here will be used by Unit 5 (extract_blocks parameter propagation) and Unit 6-8 (GUI integration)
- The $INSUNITS code 3 (miles) is intentionally not supported as it's not used in typical CAD workflows
- Stage 1 tolerances are extremely small (nanometer scale) to only fix floating-point artifacts
- Stage 2 tolerances are much larger (millimeter to inch scale) for intentional gap bridging
