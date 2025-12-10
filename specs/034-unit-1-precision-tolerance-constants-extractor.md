# Feature: User-Configurable Precision Fix Tolerance with Increased Defaults

## Feature Description
This feature introduces user-configurable precision fix tolerances with significantly increased default values. Currently, the precision fix tolerances operate at nanometer scale (1e-6 to 1e-4), which only fixes floating-point artifacts. The new tolerances are increased to practical CAD tolerance scale (0.01mm for millimeters, 0.0005in for inches, etc.) to fix both floating-point artifacts AND small coordinate precision errors common in CAD drawings.

This is Unit 1 of the Precision Tolerance GUI Implementation, focusing on the backend constants and extractor logic. It establishes the foundation for future GUI controls that will allow users to specify custom precision fix amounts.

## User Story
As a CAD engineer processing DXF files
I want precision fix tolerances that match practical CAD drawing precision
So that small coordinate precision errors are automatically corrected during polygon detection, resulting in more accurate content zone calculations

## Problem Statement
The current precision snap tolerances (1e-6 for mm, 1e-4 for meters) are set at nanometer scale, which only fixes floating-point arithmetic errors. However, CAD drawings often have small precision errors (e.g., 0.001mm coordinate differences) that are not intentional design gaps but rather CAD system precision limitations. These errors cause polygon detection to fail, resulting in inaccurate content zone calculations and polygon counts.

## Solution Statement
1. Add a new `DEFAULT_PRECISION_FIX_TOLERANCE` dictionary in `constants.py` with practical CAD tolerances:
   - Millimeters: 0.01mm (10 micrometers) - typical CAD precision
   - Inches: 0.0005in (0.5 mils) - half a thousandth
   - Feet: 0.00005ft (~0.5 mils in feet)
   - Centimeters: 0.001cm = 0.01mm
   - Meters: 0.00001m = 0.01mm
   - Unitless: 0.01 (mm-equivalent default)

2. Add input constraint constants `PRECISION_FIX_MIN` and `PRECISION_FIX_MAX` for future GUI validation.

3. Modify `get_snap_tolerances()` in `extractor.py` to accept an optional `precision_fix_amount` parameter, allowing users to specify custom precision tolerance values.

4. Keep existing `PRECISION_SNAP_TOLERANCE` for backward compatibility (optional fallback).

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Contains tolerance dictionaries and constraint constants
  - Add `DEFAULT_PRECISION_FIX_TOLERANCE` dict with new practical CAD tolerances
  - Add `PRECISION_FIX_MIN` and `PRECISION_FIX_MAX` constraint constants
  - Keep existing `PRECISION_SNAP_TOLERANCE` for backward compatibility

- **app/core/extractor.py** - Contains `get_snap_tolerances()` function
  - Add `precision_fix_amount` parameter to function signature
  - Update precision tolerance calculation logic to use new defaults and custom amounts

- **app/tests/core/test_constants.py** - Tests for constants module
  - Add tests for new `DEFAULT_PRECISION_FIX_TOLERANCE` dict
  - Add tests for `PRECISION_FIX_MIN` and `PRECISION_FIX_MAX` constraints

- **app/tests/core/extractor/test_extractor_precision_fix.py** - Tests for precision fix functionality
  - Add tests for `precision_fix_amount` parameter
  - Update existing tests to use new tolerance dict
  - Add tests for custom amount vs default behavior

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Update `constants.py` with new tolerance dictionary and constraint constants. This provides the foundation for the extractor changes and future GUI integration.

### Phase 2: Core Implementation
Modify `get_snap_tolerances()` in `extractor.py` to accept the new `precision_fix_amount` parameter and implement the logic to use custom amounts or fall back to new default tolerances.

### Phase 3: Integration
Update all tests to verify the new behavior, ensure backward compatibility, and validate that existing functionality is preserved.

## Step by Step Tasks

### Step 1: Add New Constants to constants.py
- Add `DEFAULT_PRECISION_FIX_TOLERANCE` dictionary with values from the table:
  ```python
  DEFAULT_PRECISION_FIX_TOLERANCE: dict[int, float] = {
      0: 0.01,     # Unitless: use mm-equivalent default
      1: 0.0005,   # Inches: 0.5 mils (half a thousandth)
      2: 0.00005,  # Feet: ~0.5 mils in feet
      4: 0.01,     # Millimeters: 0.01mm (10 micrometers)
      5: 0.001,    # Centimeters: 0.001cm = 0.01mm
      6: 0.00001,  # Meters: 0.00001m = 0.01mm
  }
  ```
- Add `PRECISION_FIX_MIN: float = 0.0` constant
- Add `PRECISION_FIX_MAX: float = 10.0` constant
- Add appropriate docstrings explaining the purpose and scale of the new tolerances

### Step 2: Update extractor.py get_snap_tolerances() Function
- Add `precision_fix_amount: float | None = None` parameter to function signature
- Update docstring to document the new parameter
- Import `DEFAULT_PRECISION_FIX_TOLERANCE` from constants
- Update precision tolerance calculation logic:
  ```python
  if precision_fix_enabled:
      if precision_fix_amount is not None and precision_fix_amount > 0:
          # Use user-specified amount
          precision_tolerance = precision_fix_amount
      else:
          # Use default for the effective unit from new dict
          precision_tolerance = DEFAULT_PRECISION_FIX_TOLERANCE.get(
              effective_units,
              DEFAULT_PRECISION_FIX_TOLERANCE.get(0, 0.01),  # Fallback
          )
  else:
      precision_tolerance = 0.0
  ```

### Step 3: Add Tests for New Constants
- Add test class `TestPrecisionFixToleranceConstants` to `test_constants.py`
- Test that `DEFAULT_PRECISION_FIX_TOLERANCE` has all supported unit codes (0, 1, 2, 4, 5, 6)
- Test that all tolerance values are in reasonable range (1e-6 to 1.0)
- Test that `PRECISION_FIX_MIN` is less than `PRECISION_FIX_MAX`
- Test that `PRECISION_FIX_MIN` is non-negative (>= 0.0)
- Test that `PRECISION_FIX_MAX` is positive

### Step 4: Add Tests for precision_fix_amount Parameter
- Add test class `TestPrecisionFixAmountParameter` to `test_extractor_precision_fix.py`
- Test custom amount is used when provided and positive
- Test default tolerance is used when amount is None
- Test default tolerance is used when amount is 0 or negative
- Test custom amount works with all unit types
- Test custom amount works with unit override
- Test backward compatibility (existing tests still pass)

### Step 5: Update Existing Tests to Verify New Default Values
- Update `TestPrecisionFixToggle` tests to reference `DEFAULT_PRECISION_FIX_TOLERANCE` instead of `PRECISION_SNAP_TOLERANCE`
- Verify all existing tests pass with the new implementation
- Add comments explaining the change from nanometer to practical CAD tolerances

### Step 6: Run Validation Commands
- Run all tests to ensure zero regressions
- Run type checking to verify type hints are correct
- Run linting to ensure code style compliance

## Testing Strategy

### Unit Tests
1. **Constants Tests (`test_constants.py`)**:
   - `DEFAULT_PRECISION_FIX_TOLERANCE` contains all supported unit codes
   - All tolerance values are within reasonable bounds (1e-6 to 1.0)
   - `PRECISION_FIX_MIN` and `PRECISION_FIX_MAX` constraints are valid

2. **Extractor Tests (`test_extractor_precision_fix.py`)**:
   - `precision_fix_amount` parameter acceptance
   - Custom amount used when provided and > 0
   - Default used when amount is None, 0, or negative
   - Integration with `precision_fix_enabled` flag
   - Integration with unit override

### Integration Tests
1. **extract_blocks() Integration**:
   - Verify `extract_blocks()` still works with new tolerance defaults
   - Verify `extract_blocks()` works when `precision_fix_amount` is passed through tolerance calculation
   - Content zone detection produces consistent results

### Edge Cases
1. `precision_fix_amount = 0.0` should use default tolerance
2. `precision_fix_amount = -1.0` should use default tolerance
3. `precision_fix_amount = None` should use default tolerance
4. Unknown unit codes should fall back to unitless default (0.01)
5. `precision_fix_enabled = False` with custom amount should still return 0.0

### Playwright MCP Tests
Not applicable for this unit - no GUI changes are included.

## Acceptance Criteria
1. `DEFAULT_PRECISION_FIX_TOLERANCE` dict exists in `constants.py` with correct values for all 6 unit codes
2. `PRECISION_FIX_MIN` (0.0) and `PRECISION_FIX_MAX` (10.0) constants exist in `constants.py`
3. `get_snap_tolerances()` accepts `precision_fix_amount` parameter (float | None, default None)
4. When `precision_fix_amount` is provided and > 0, that value is used for precision tolerance
5. When `precision_fix_amount` is None, 0, or negative, the default from `DEFAULT_PRECISION_FIX_TOLERANCE` is used
6. When `precision_fix_enabled` is False, precision tolerance is 0.0 regardless of amount
7. All existing tests pass (backward compatibility)
8. All new tests pass
9. Type checking passes with `uv run mypy app/`
10. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to validate new tolerance dict and constraints
- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run precision fix tests to validate new parameter
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code

## Notes
- The existing `PRECISION_SNAP_TOLERANCE` dict is kept for backward compatibility but will no longer be the primary source of precision tolerances
- The new tolerances are 4-5 orders of magnitude larger than the old ones (e.g., 0.01mm vs 1e-6mm)
- This change may affect polygon detection results for drawings that previously had coordinate precision errors - this is intentional and expected to improve accuracy
- Future units (Unit 2-4) will add GUI controls to expose `precision_fix_amount` to users
- The `PRECISION_FIX_MAX` value of 10.0 is conservative and can be adjusted based on user feedback

### Reference Table (from plan)
| Unit | Code | Old Precision | New Default Precision | Gap Bridge Default |
|------|------|---------------|----------------------|-------------------|
| Millimeters (MM) | 4 | 1e-6 (0.000001) | 0.01 | 0.5 |
| Centimeters (CM) | 5 | 1e-5 (0.00001) | 0.001 | 0.05 |
| Meters (M) | 6 | 1e-4 (0.0001) | 0.00001 | 0.001 |
| Inches (IN) | 1 | 1e-6 (0.000001) | 0.0005 | 0.01 |
| Feet (FT) | 2 | 1e-5 (0.00001) | 0.00005 | 0.1 |
| Unitless | 0 | 1e-6 (0.000001) | 0.01 | 0.1 |
