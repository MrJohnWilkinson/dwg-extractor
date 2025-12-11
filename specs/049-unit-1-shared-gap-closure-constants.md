# Chore: Shared Gap Closure Tolerance and Filter Defaults

## Chore Description

This is a refactoring/maintenance task to consolidate and update default tolerance constants in `constants.py`. The goal is to:

1. **Consolidate gap closure tolerances**: Replace the separate `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE` dictionaries with a single `DEFAULT_GAP_CLOSURE_TOLERANCE` shared dictionary. Both Precision Fix and Gap Bridge solve the same problem (closing small gaps for accurate polygon counts) using different algorithms, so they should share the same default tolerance values.

2. **Update tolerance values to 3mm base**: The new shared tolerance uses 3mm as the base value - this is a typical visible CAD gap that is large enough to bridge design gaps but small enough to not merge distinct geometry. The imperial equivalent is 1/8 inch (0.125"), which is the closest standard imperial fraction to 3mm.

3. **Update minimum area filter values to 100,000 sq mm base**: The current 100 sq mm base is too small. 100,000 sq mm filters out small artifact polygons while preserving meaningful geometry (approximately a 10" x 10" square or 316mm x 316mm square).

4. **Update minimum side filter imperial values for 10mm base**: Update the imperial unit values to properly convert from the 10mm base value.

## Relevant Files

Use these files to resolve the chore:

- **`app/core/constants.py`** (lines 198-309): Contains the tolerance and filter constant dictionaries that need to be modified:
  - `DEFAULT_PRECISION_FIX_TOLERANCE` - to be removed and replaced
  - `DEFAULT_GAP_BRIDGE_TOLERANCE` - to be removed and replaced
  - `DEFAULT_MIN_AREA_FILTER` - values to be updated
  - `DEFAULT_MIN_SIDE_FILTER` - imperial values to be updated

- **`app/tests/core/test_constants.py`** (lines 148-351): Contains tests for the tolerance and filter constants that need to be updated to validate new values

- **`app/main.py`** (lines 26-29, 697, 723): Imports and uses `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE` - imports and usages must be updated to use `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **`app/core/extractor.py`** (lines 25-28, 143-216, 293-303): Imports and uses the tolerance constants - imports and usages must be updated to use `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **`app/tests/core/extractor/test_extractor_units.py`**: Tests that reference `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE` - must be updated

- **`app/tests/core/extractor/test_extractor_precision_fix.py`**: Tests that reference `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE` - must be updated

- **`app/tests/core/extractor/test_extractor_polygon_filter.py`**: Tests that reference `DEFAULT_MIN_AREA_FILTER` and `DEFAULT_MIN_SIDE_FILTER` - may need updates if value assertions change

- **`app/tests/core/test_geometry.py`** (line 1339-1344): Tests that assert specific `DEFAULT_GAP_BRIDGE_TOLERANCE` values - must be updated

## Step by Step Tasks

### Step 1: Update constants.py - Add shared tolerance and update filters

Update `/workspace/app/core/constants.py`:

- **Add `DEFAULT_GAP_CLOSURE_TOLERANCE` dictionary** (replaces both `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE`):
  ```python
  # Shared gap closure tolerance for both Precision Fix and Gap Bridge algorithms.
  # Both solve the same problem (closing small gaps for accurate polygon counts)
  # using different algorithms, so they share the same default tolerance.
  # Base: 3mm - typical visible CAD gap, large enough to bridge design gaps
  # but small enough to not merge distinct geometry.
  DEFAULT_GAP_CLOSURE_TOLERANCE: dict[int, float] = {
      0: 3.0,      # Unitless: assume mm-equivalent (3mm)
      1: 0.125,    # Inches: 1/8 inch (closest standard fraction to 3mm)
      2: 0.0104,   # Feet: 1/8 inch in feet (0.125/12)
      4: 3.0,      # Millimeters: 3mm
      5: 0.3,      # Centimeters: 0.3cm = 3mm
      6: 0.003,    # Meters: 0.003m = 3mm
  }
  ```

- **Remove `DEFAULT_PRECISION_FIX_TOLERANCE` dictionary** (lines 245-262)

- **Remove `DEFAULT_GAP_BRIDGE_TOLERANCE` dictionary** (lines 221-231) and its docstring

- **Update `DEFAULT_MIN_AREA_FILTER`** to use 100,000 sq mm base:
  ```python
  DEFAULT_MIN_AREA_FILTER: dict[int, float] = {
      0: 100000.0,   # Unitless: assume mm-equivalent (100,000 sq mm)
      1: 155.0,      # Inches: 155 sq inches (~100,000 sq mm)
      2: 1.076,      # Feet: 1.076 sq feet (~100,000 sq mm)
      4: 100000.0,   # Millimeters: 100,000 sq mm
      5: 1000.0,     # Centimeters: 1,000 sq cm = 100,000 sq mm
      6: 0.1,        # Meters: 0.1 sq m = 100,000 sq mm
  }
  ```

- **Update `DEFAULT_MIN_SIDE_FILTER`** imperial values for 10mm base:
  ```python
  DEFAULT_MIN_SIDE_FILTER: dict[int, float] = {
      0: 10.0,     # Unitless: assume mm-equivalent (10mm)
      1: 0.394,    # Inches: 0.394 inches (~10mm)
      2: 0.0328,   # Feet: 0.0328 feet (~10mm)
      4: 10.0,     # Millimeters: 10mm
      5: 1.0,      # Centimeters: 1cm = 10mm
      6: 0.01,     # Meters: 0.01m = 10mm
  }
  ```

### Step 2: Update main.py imports and usages

Update `/workspace/app/main.py`:

- **Update imports** (lines 25-29): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update precision fix default lookup** (around line 697):
  ```python
  # Before:
  default_amount = DEFAULT_PRECISION_FIX_TOLERANCE.get(effective_units, 0.01)
  # After:
  default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
  ```

- **Update gap bridge default lookup** (around line 723):
  ```python
  # Before:
  default_amount = DEFAULT_GAP_BRIDGE_TOLERANCE.get(effective_units, 100.0)
  # After:
  default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
  ```

### Step 3: Update extractor.py imports and usages

Update `/workspace/app/core/extractor.py`:

- **Update imports** (lines 25-28): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update docstrings** that reference the old constant names (lines 143-161)

- **Update precision tolerance lookup** (around lines 195-198):
  ```python
  # Before:
  precision_tolerance = DEFAULT_PRECISION_FIX_TOLERANCE.get(
      effective_units,
      DEFAULT_PRECISION_FIX_TOLERANCE.get(0, 0.01),
  )
  # After:
  precision_tolerance = DEFAULT_GAP_CLOSURE_TOLERANCE.get(
      effective_units,
      DEFAULT_GAP_CLOSURE_TOLERANCE.get(0, 3.0),
  )
  ```

- **Update gap bridge tolerance lookup** (around lines 214-216):
  ```python
  # Before:
  gap_bridge_tolerance = DEFAULT_GAP_BRIDGE_TOLERANCE.get(
      effective_units,
      DEFAULT_GAP_BRIDGE_TOLERANCE.get(0, 0.1),
  )
  # After:
  gap_bridge_tolerance = DEFAULT_GAP_CLOSURE_TOLERANCE.get(
      effective_units,
      DEFAULT_GAP_CLOSURE_TOLERANCE.get(0, 3.0),
  )
  ```

- **Update docstrings** for `_calculate_filter_defaults` (around lines 253-264, 293-303) that reference the old constant names

### Step 4: Update test_constants.py

Update `/workspace/app/tests/core/test_constants.py`:

- **Update imports** (lines 11-14): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update `TestDrawingUnitConstants.test_gap_bridge_tolerances_in_reasonable_range`** (lines 128-137): Update to test `DEFAULT_GAP_CLOSURE_TOLERANCE` with new value range (0.001 to 10.0)

- **Replace entire `TestPrecisionFixToleranceConstants` class** (lines 148-245) with new `TestGapClosureToleranceConstants` class that tests:
  - All supported unit codes present
  - Values in reasonable range (0.001 to 10.0)
  - Specific values: MM=3.0, Inches=0.125, Feet=0.0104, CM=0.3, M=0.003, Unitless=3.0

- **Update `TestMinAreaFilterConstants`** (lines 247-298):
  - Update `test_default_min_area_filter_mm_value` to expect 100000.0
  - Update `test_default_min_area_filter_inch_value` to expect 155.0

- **Update `TestMinSideFilterConstants`** (lines 300-351):
  - Update `test_default_min_side_filter_inch_value` to expect 0.394

### Step 5: Update test_extractor_units.py

Update `/workspace/app/tests/core/extractor/test_extractor_units.py`:

- **Update imports** (lines 14-15): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update all assertions** that reference the old constants to use `DEFAULT_GAP_CLOSURE_TOLERANCE`:
  - Lines 137-138, 152-153, 167-168, 196, 210, 237, 253-256, 274-275, 288-289, 497, 519, 537

- **Update docstrings and comments** that reference the old constant names

### Step 6: Update test_extractor_precision_fix.py

Update `/workspace/app/tests/core/extractor/test_extractor_precision_fix.py`:

- **Update imports** (lines 15-16): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update all assertions** that reference the old constants to use `DEFAULT_GAP_CLOSURE_TOLERANCE`:
  - Lines 53, 94, 123, 169, 188, 209, 211, 258, 303-304, 365, 495, 511, 527, 543, 582, 663

- **Update docstrings, comments, and class docstrings** that reference the old constant names

### Step 7: Update test_geometry.py

Update `/workspace/app/tests/core/test_geometry.py`:

- **Update imports** (line 18): Replace `DEFAULT_GAP_BRIDGE_TOLERANCE` with `DEFAULT_GAP_CLOSURE_TOLERANCE`

- **Update tolerance value assertions** (lines 1339-1344):
  ```python
  # Before:
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[4] == 0.5  # MM: 0.5mm
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[6] == 0.001  # M: 1mm in meters
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[1] == 0.01  # IN: 0.01 inches
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[2] == 0.1  # FT: 0.1 feet
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[5] == 0.05  # CM: 0.05 cm
  assert DEFAULT_GAP_BRIDGE_TOLERANCE[0] == 0.1  # Unitless

  # After:
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[4] == 3.0  # MM: 3mm
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[6] == 0.003  # M: 3mm in meters
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[1] == 0.125  # IN: 1/8 inch
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[2] == 0.0104  # FT: 1/8 inch in feet
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[5] == 0.3  # CM: 0.3 cm
  assert DEFAULT_GAP_CLOSURE_TOLERANCE[0] == 3.0  # Unitless
  ```

### Step 8: Update test_extractor_polygon_filter.py

Update `/workspace/app/tests/core/extractor/test_extractor_polygon_filter.py`:

- Review tests that assert specific `DEFAULT_MIN_AREA_FILTER` and `DEFAULT_MIN_SIDE_FILTER` values
- Since the MM values for `DEFAULT_MIN_SIDE_FILTER` (10.0) remain unchanged, tests using MM should still pass
- Tests asserting specific inch values will need updates if they check exact values:
  - Area filter inch: 0.01 -> 155.0
  - Side filter inch: 0.5 -> 0.394

### Step 9: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to validate new constant values
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate gap closure tolerance updates
- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run extractor units tests
- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run precision fix tests
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run polygon filter tests
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check to ensure no type errors after refactoring
- `uv run ruff check app/` - Lint check for code quality

## Notes

- **Conversion Reference for 3mm base tolerance**:
  - 3mm = 0.1181 inches, rounded to 0.125" (1/8 inch) for standard imperial fraction
  - 1/8 inch = 0.0104 feet (0.125/12)
  - 3mm = 0.3 cm = 0.003 m

- **Conversion Reference for 100,000 sq mm base area filter**:
  - 100,000 sq mm = 155.0 sq inches (100000 / 645.16)
  - 100,000 sq mm = 1.076 sq feet (155.0 / 144)
  - 100,000 sq mm = 1,000 sq cm = 0.1 sq m

- **Conversion Reference for 10mm base side filter**:
  - 10mm = 0.394 inches (10 / 25.4)
  - 10mm = 0.0328 feet (0.394 / 12)
  - 10mm = 1.0 cm = 0.01 m

- **Rationale for shared tolerance**: Both Precision Fix and Gap Bridge algorithms serve the same purpose - closing small gaps between line segments to enable accurate polygon detection. They use different approaches (coordinate snapping vs. adding bridge segments) but the appropriate gap size to close is the same regardless of algorithm.

- **Rationale for 3mm default**: This is a typical visible gap in CAD drawings - large enough to bridge common design gaps and coordinate precision issues, but small enough to not accidentally merge geometry that should remain separate.

- **Import updates must be synchronized**: When updating imports in each file, ensure both the old constant names are removed and the new `DEFAULT_GAP_CLOSURE_TOLERANCE` is added. Running tests after each file update will catch any missed references.
