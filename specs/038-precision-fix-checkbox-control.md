# Feature: Precision Fix Checkbox Control

## Feature Description
Add a checkbox control that allows users to toggle the precision fix (Stage 1 snapping) on or off. Currently, precision snapping is always applied automatically during content zone detection. This feature gives users explicit control over both snapping stages:

1. **Precision Fix** (Stage 1) - Fixes floating-point artifacts at line endpoints using nanometer-scale tolerances
2. **Gap Bridge** (Stage 2) - Bridges intentional design gaps using user-configurable tolerances (already exists as a checkbox)

Both controls will be independent checkboxes, allowing users to enable/disable each stage separately based on their specific DXF file requirements.

## User Story
As a CAD technician
I want to toggle the precision fix feature on or off independently
So that I can control how the extractor handles floating-point precision issues in my drawings without affecting intentional gap bridging behavior

## Problem Statement
The precision fix (Stage 1 snapping) is currently always applied automatically with no user control. Some users may want to disable this feature for specific drawings where the precision snapping causes unintended side effects, or to compare extraction results with and without precision correction.

## Solution Statement
Add a "Precision Fix" checkbox to the GUI options frame, positioned before the existing "Gap Bridge" checkbox. When unchecked, the precision_tolerance parameter passed to geometry functions will be 0.0, effectively disabling Stage 1 snapping while preserving all other functionality. The checkbox will default to checked (enabled) to maintain backward compatibility.

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application. Contains the options frame with unit dropdown and gap bridge checkbox. Need to add precision fix checkbox variable and widget.
- **app/core/extractor.py** - Extraction logic. Contains `extract_blocks()` and `get_snap_tolerances()` functions that calculate and use tolerance values. Need to add `precision_fix_enabled` parameter.
- **app/core/geometry.py** - Geometry calculations. Already accepts `precision_tolerance` parameter - no changes needed as it will receive 0.0 when disabled.
- **app/core/constants.py** - Contains tolerance constants. No changes needed - constants remain available for when precision fix is enabled.
- **app/tests/core/extractor/conftest.py** - Test fixtures for extractor tests.
- **app/tests/core/extractor/test_extractor_units.py** - Existing tests for unit detection and tolerance calculation.

### New Files
- **app/tests/core/extractor/test_extractor_precision_fix.py** - New test file for precision fix toggle functionality.

## Implementation Plan
### Phase 1: Foundation
1. Update `get_snap_tolerances()` in extractor.py to accept a `precision_fix_enabled` parameter
2. When `precision_fix_enabled=False`, return 0.0 for precision_tolerance instead of the calculated value
3. Update `extract_blocks()` to accept and pass through the `precision_fix_enabled` parameter

### Phase 2: Core Implementation
1. Add `precision_fix_var` BooleanVar to main.py (default True)
2. Create "Precision Fix" checkbox widget in options frame
3. Position checkbox before the "Gap Bridge" checkbox
4. Wire checkbox to extraction call with the new parameter

### Phase 3: Integration
1. Update extraction worker to read precision fix setting
2. Add logging for precision fix state
3. Ensure backward compatibility (defaults to enabled)
4. Create comprehensive unit tests

## Step by Step Tasks

### Step 1: Update get_snap_tolerances Function
- Modify `get_snap_tolerances()` in `app/core/extractor.py` to accept new `precision_fix_enabled: bool` parameter
- Add parameter with default value `True` for backward compatibility
- When `precision_fix_enabled=False`, set `precision_tolerance = 0.0` instead of calculating it
- Update function docstring with new parameter documentation
- Update type hints for return value documentation

### Step 2: Update extract_blocks Function Signature
- Add `precision_fix_enabled: bool = True` parameter to `extract_blocks()` in `app/core/extractor.py`
- Pass the new parameter to `get_snap_tolerances()` call
- Update function docstring with new parameter documentation
- Update logging to include precision fix state

### Step 3: Add GUI Variables in main.py
- Add `self.precision_fix_var = ctk.BooleanVar(value=True)` in `DXFExtractorApp.__init__()` (after line 78)
- Position new variable declaration near the existing `gap_bridge_var` for logical grouping

### Step 4: Add Precision Fix Checkbox Widget
- Add "Precision Fix:" checkbox in `_create_widgets()` method
- Position BEFORE the existing "Gap Bridge:" checkbox in the options_frame
- Use consistent styling: `font=ctk.CTkFont(size=12)`
- Checkbox should use `self.precision_fix_var` as its variable
- Add callback method `_on_precision_fix_toggle()` for logging (optional but recommended)

### Step 5: Update Extraction Worker
- Modify `_extraction_worker()` method to read `self.precision_fix_var.get()`
- Pass value to `extract_blocks()` as `precision_fix_enabled` parameter
- Add precision fix state to the existing extraction settings log message

### Step 6: Create Unit Tests for Precision Fix Toggle
- Create new test file `app/tests/core/extractor/test_extractor_precision_fix.py`
- Test `get_snap_tolerances()` returns 0.0 precision tolerance when disabled
- Test `get_snap_tolerances()` returns calculated tolerance when enabled
- Test backward compatibility (default enabled)
- Test interaction with gap bridge settings (both independent)

### Step 7: Update Existing Tolerance Tests
- Review `app/tests/core/extractor/test_extractor_units.py` for any tests that need updating
- Ensure existing tests pass with default `precision_fix_enabled=True`
- Add test cases that verify both parameters work independently

### Step 8: Run Validation Commands
- Execute all validation commands to verify zero regressions
- Run type checking with mypy
- Run linting with ruff
- Execute full test suite with coverage

## Testing Strategy
### Unit Tests
- Test `get_snap_tolerances()` with `precision_fix_enabled=True` returns calculated tolerance
- Test `get_snap_tolerances()` with `precision_fix_enabled=False` returns 0.0
- Test `get_snap_tolerances()` maintains gap_bridge behavior regardless of precision_fix setting
- Test `extract_blocks()` propagates precision_fix_enabled to tolerance calculation

### Integration Tests
- Test full extraction flow with precision fix enabled (default behavior)
- Test full extraction flow with precision fix disabled
- Test that content zone detection behavior differs appropriately based on setting

### Edge Cases
- Both precision fix and gap bridge disabled (precision_tolerance=0.0, gap_bridge_tolerance=0.0)
- Precision fix disabled, gap bridge enabled (precision_tolerance=0.0, gap_bridge_tolerance>0)
- Precision fix enabled, gap bridge disabled (precision_tolerance>0, gap_bridge_tolerance=0.0)
- Both enabled (default case, should match current behavior)

### Playwright MCP Tests
- GUI tests skipped per README.md due to WSL X server issues
- Focus on unit/integration tests for this feature

## Acceptance Criteria
1. New "Precision Fix" checkbox appears in the GUI options frame before "Gap Bridge" checkbox
2. Checkbox defaults to checked (enabled) to maintain backward compatibility
3. When unchecked, precision_tolerance passed to geometry functions is 0.0
4. When checked, precision_tolerance is calculated based on detected/selected units
5. Precision fix and gap bridge checkboxes operate independently
6. All existing tests pass without modification (backward compatible)
7. New tests cover all precision fix toggle scenarios
8. Type checking passes with no errors
9. Linting passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run new precision fix tests
- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run existing unit/tolerance tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run complete test suite
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run pytest --cov=app/core app/tests/` - Run tests with coverage report

## Notes
- The precision fix checkbox will be labeled "Precision Fix:" to match the style of "Gap Bridge:" label
- Default value is True to ensure backward compatibility with existing behavior
- No new dependencies required
- The geometry.py module already accepts precision_tolerance as a parameter, so no changes needed there
- Consider adding a tooltip or help text in future iterations to explain what precision fix does
