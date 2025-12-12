# Chore: Update Threshold Valid Ranges and Defaults

## Chore Description
Update the valid ranges and default values for three performance threshold settings in the DXF Block Extractor application:

| Setting | Current Range | New Range | Current Default | New Default |
|---------|---------------|-----------|-----------------|-------------|
| Polygon Count Threshold | 100-10000 | **1-10000** | 500 | **30** |
| Line Segment Threshold | 1000-50000 | **1-10000** | 5000 | **30** |
| Entity Count Threshold | 100-10000 | **1-10000** | 1000 | **30** |

These thresholds control early-exit behavior for content zone detection. Lower values improve performance by skipping complex blocks earlier in processing.

## Relevant Files
Use these files to resolve the chore:

- **`app/core/constants.py`** - Contains all threshold constants that need modification:
  - `DEFAULT_POLYGON_COUNT_THRESHOLD` (line 352) - default value to change to 30
  - `DEFAULT_LINE_SEGMENT_THRESHOLD` (line 353) - default value to change to 30
  - `DEFAULT_ENTITY_COUNT_THRESHOLD` (line 354) - default value to change to 30
  - `POLYGON_COUNT_THRESHOLD_MIN` (line 356) - change from 100 to 1
  - `POLYGON_COUNT_THRESHOLD_MAX` (line 357) - already 10000 (no change)
  - `LINE_SEGMENT_THRESHOLD_MIN` (line 358) - change from 1000 to 1
  - `LINE_SEGMENT_THRESHOLD_MAX` (line 359) - change from 50000 to 10000
  - `ENTITY_COUNT_THRESHOLD_MIN` (line 360) - change from 100 to 1
  - `ENTITY_COUNT_THRESHOLD_MAX` (line 361) - already 10000 (no change)
  - `POLYGON_COUNT_THRESHOLD` (line 169) - hardcoded early-exit threshold, update to 30
  - `LINE_SEGMENT_THRESHOLD` (line 175) - hardcoded early-exit threshold, update to 30
  - `ENTITY_COUNT_THRESHOLD` (line 181) - hardcoded early-exit threshold, update to 30

- **`app/tests/core/test_constants.py`** - Contains tests that validate threshold ranges and defaults:
  - `test_polygon_threshold_reasonable()` (line 49-55) - assertion bounds need updating
  - `test_line_threshold_reasonable()` (line 57-63) - assertion bounds need updating
  - `test_performance_threshold_defaults()` (line 582-592) - expected values need updating

- **`app/tests/core/test_settings.py`** - Contains tests that rely on specific min/max values:
  - `test_set_invalid_value_returns_false()` (line 84-87) - uses value 10 which will now be valid
  - `test_set_invalid_value_does_not_change_setting()` (line 89-95) - uses value 10 which will now be valid
  - `test_validate_value_below_min()` (line 129-133) - uses value 50 which will now be valid

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Default Values in constants.py
Update the DEFAULT_* constants for the three performance thresholds:

- Change `DEFAULT_POLYGON_COUNT_THRESHOLD` from `500` to `30`
- Change `DEFAULT_LINE_SEGMENT_THRESHOLD` from `5000` to `30`
- Change `DEFAULT_ENTITY_COUNT_THRESHOLD` from `1000` to `30`

### Step 2: Update Min/Max Range Constants in constants.py
Update the min/max validation range constants:

- Change `POLYGON_COUNT_THRESHOLD_MIN` from `100` to `1`
- Keep `POLYGON_COUNT_THRESHOLD_MAX` at `10000` (no change)
- Change `LINE_SEGMENT_THRESHOLD_MIN` from `1000` to `1`
- Change `LINE_SEGMENT_THRESHOLD_MAX` from `50000` to `10000`
- Change `ENTITY_COUNT_THRESHOLD_MIN` from `100` to `1`
- Keep `ENTITY_COUNT_THRESHOLD_MAX` at `10000` (no change)

### Step 3: Update Hardcoded Threshold Constants in constants.py
Update the hardcoded threshold values used for early-exit logic:

- Change `POLYGON_COUNT_THRESHOLD` from `500` to `30`
- Change `LINE_SEGMENT_THRESHOLD` from `5000` to `30`
- Change `ENTITY_COUNT_THRESHOLD` from `1000` to `30`

Also update the docstrings for these constants to reflect the new values.

### Step 4: Update test_constants.py Tests
Update the test assertions to match new ranges and defaults:

- **`test_polygon_threshold_reasonable()`**: Change assertion from `assert 10 <= POLYGON_COUNT_THRESHOLD <= 1000` to `assert 1 <= POLYGON_COUNT_THRESHOLD <= 10000`
- **`test_line_threshold_reasonable()`**: Change assertion from `assert 1000 <= LINE_SEGMENT_THRESHOLD <= 10000` to `assert 1 <= LINE_SEGMENT_THRESHOLD <= 10000`
- **`test_performance_threshold_defaults()`**: Update expected values:
  - `DEFAULT_POLYGON_COUNT_THRESHOLD == 30`
  - `DEFAULT_LINE_SEGMENT_THRESHOLD == 30`
  - `DEFAULT_ENTITY_COUNT_THRESHOLD == 30`

### Step 5: Update test_settings.py Tests
Fix tests that use values that are now valid under the new ranges:

- **`test_set_invalid_value_returns_false()`**: Change test value from `10` to `0` (now below new min of 1)
- **`test_set_invalid_value_does_not_change_setting()`**: Change test value from `10` to `0` (now below new min of 1)
- **`test_validate_value_below_min()`**: Change test value from `50` to `0` (now below new min of 1)

### Step 6: Run Validation Commands
Execute all validation commands to confirm zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_constants.py -v` - Run constant tests to validate threshold range and default value changes
- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests to validate validation range changes
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors introduced
- `uv run ruff check app/` - Run linting to ensure code quality

## Notes
- The hardcoded threshold constants (`POLYGON_COUNT_THRESHOLD`, `LINE_SEGMENT_THRESHOLD`, `ENTITY_COUNT_THRESHOLD`) at lines 169-185 are used directly in `extractor.py` and `geometry.py` for early-exit checks. These should match the new DEFAULT_* values.
- The `settings_window.py` displays range hints like `(100 - 10000)` dynamically using the `SETTINGS_VALIDATION_REGISTRY` from `constants.py`, so no GUI code changes are needed - the hints will auto-update.
- The docstrings for the hardcoded threshold constants should be updated to explain the new default value of 30.
