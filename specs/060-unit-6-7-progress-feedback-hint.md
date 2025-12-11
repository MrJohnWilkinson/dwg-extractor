# Feature: Progress Feedback and Hint Text Update (Units 6+7)

## Feature Description
Implement two related enhancements that improve user experience during DXF extraction:

1. **Unit 6 - Progress Feedback During Long Operations**: Add INFO-level logging at the start and end of content zone detection for each block. This provides users with visibility into what's happening during long operations (3+ minutes) to distinguish progress from application freezes.

2. **Unit 7 - Units Hint Text Update**: Update the hint text below the Units dropdown to accurately reflect that the selected unit applies to all numeric filters (precision fix, gap bridge, area filter, and side filter), not just precision fix and gap bridge.

## User Story
As a CAD analyst
I want to see progress messages during long extraction operations and accurate descriptions of UI controls
So that I can distinguish active processing from application freezes and understand which settings are affected by my unit selection

## Problem Statement
Two usability issues exist in the current implementation:

1. **Silent Long Operations**: During content zone detection for complex blocks, the application can appear frozen for 3+ minutes with no visible feedback. Users cannot distinguish between:
   - Active processing that's making progress
   - An application hang or freeze
   - This causes users to prematurely cancel extractions or lose confidence in the application.

2. **Inaccurate Hint Text**: The Units dropdown hint text states "(applies to precision fix and gap bridge)" but the unit selection actually affects four numeric filters:
   - Precision Fix tolerance
   - Gap Bridge tolerance
   - Min Area Filter
   - Min Side Filter
   - This misleads users about the scope of the unit setting.

## Solution Statement
1. **Unit 6**: Add INFO-level logging at two points in `_detect_content_zone()`:
   - At function start: `logger.info(f"[{block_name}] Detecting content zone...")`
   - At successful completion: `logger.info(f"[{block_name}] Content zone detected: {width:.2f} x {height:.2f}")`
   - For non-detection paths: `logger.debug(f"[{block_name}] No content zone detected")`

   INFO level is used for start/success messages so they appear at default log levels, while non-detection uses DEBUG to avoid noise for blocks that legitimately have no content zone.

2. **Unit 7**: Update the hint text from "(applies to precision fix and gap bridge)" to "(applies to all numeric filters)" to accurately describe the scope.

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/core/geometry.py` - Contains `_detect_content_zone()` function (lines 1041-1250). Add progress logging:
  - After line 1097 (block_name assignment): Add start logging
  - Before line 1240 (successful return): Add completion logging with dimensions
  - Before lines 1106, 1150, 1197 (empty returns): Add debug logging for non-detection

- `app/main.py` - Contains the units hint label (lines 196-202). Update text value.

### Reference Files (Read-Only)
- `app/core/logger.py` - Contains logging configuration. The `logger` module variable is already imported in geometry.py.
- `app/tests/core/test_content_zone.py` - Existing content zone tests. May be used to verify logging doesn't break functionality.
- `app/tests/core/test_geometry.py` - Existing geometry tests. May be used to verify logging doesn't break functionality.

## Implementation Plan

### Phase 1: Foundation (Unit 6 - Start Logging)
Add progress feedback logging at the start of content zone detection to indicate processing has begun for each block.

1. Add INFO-level log message immediately after `block_name = block_def.name` in `_detect_content_zone()`
2. Use consistent format: `[{block_name}] Detecting content zone...`

### Phase 2: Core Implementation (Unit 6 - Completion Logging)
Add completion logging at all return points to indicate processing has finished for each block.

1. Add INFO-level log message before the successful return (line 1240) with dimensions
2. Add DEBUG-level log messages before empty returns for non-detection cases
3. Ensure all return paths have appropriate logging

### Phase 3: Integration (Unit 7 - Hint Text)
Update the UI hint text to accurately describe the unit selection scope.

1. Locate the `units_hint` CTkLabel in `main.py`
2. Change text from "(applies to precision fix and gap bridge)" to "(applies to all numeric filters)"

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add start logging to _detect_content_zone
- Open `app/core/geometry.py`
- Locate line 1097 (after `block_name = block_def.name`)
- Add the progress start log message:
```python
block_name = block_def.name

# UNIT 6: Progress feedback - log block processing start
logger.info(f"[{block_name}] Detecting content zone...")

# UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
```
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 2. Add completion logging before successful return
- Open `app/core/geometry.py`
- Locate the successful return at line 1240 (the `return ContentZoneData(...)` with `content_zone_detected=True`)
- Modify the existing debug log (line 1234-1238) to be INFO level and include dimensions:
```python
# Change from:
logger.debug(
    f"[{block_name}] Content zone detected: "
    f"trim_left={trim_left}, trim_right={trim_right}, "
    f"trim_top={trim_top}, trim_bottom={trim_bottom}"
)

# Change to:
logger.info(
    f"[{block_name}] Content zone detected: "
    f"{cz_width:.2f} x {cz_height:.2f}"
)
```
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 3. Add debug logging for empty return after entity count check
- Open `app/core/geometry.py`
- Locate line 1106 (`return _empty_content_zone_data()`)
- The warning log already exists (lines 1102-1105), so no additional logging needed here
- The warning message provides sufficient feedback for this early exit case

### 4. Add debug logging for empty return after edge count check
- Open `app/core/geometry.py`
- Locate line 1115-1125 (the return after edge count estimation)
- The warning log already exists (lines 1111-1114), so no additional logging needed here
- The warning message provides sufficient feedback for this early exit case

### 5. Add debug logging for empty return after no shapes found
- Open `app/core/geometry.py`
- Locate line 1148-1160 (the return when `len(all_shapes) == 0`)
- A debug log already exists at line 1149 (`logger.debug(f"[{block_name}] No closed shapes found")`)
- No additional logging needed here

### 6. Add debug logging for empty return after polygon count threshold
- Open `app/core/geometry.py`
- Locate line 1163-1178 (the return after polygon count threshold check)
- The warning log already exists (lines 1164-1167), so no additional logging needed here
- The warning message provides sufficient feedback for this early exit case

### 7. Add debug logging for empty return after net area filter
- Open `app/core/geometry.py`
- Locate line 1197-1208 (the return when `not net_areas`)
- Add debug logging before the return:
```python
if not net_areas:
    logger.debug(f"[{block_name}] No content zone detected (all polygons filtered)")
    return ContentZoneData(
```
- Run `uv run mypy app/core/geometry.py` to verify no type errors

### 8. Update units hint text in main.py
- Open `app/main.py`
- Locate lines 196-202 (the `units_hint` CTkLabel)
- Change the text parameter:
```python
# OLD:
units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to precision fix and gap bridge)",
    font=ctk.CTkFont(size=10),
    text_color="gray",
)

# NEW:
units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to all numeric filters)",
    font=ctk.CTkFont(size=10),
    text_color="gray",
)
```
- Run `uv run mypy app/main.py` to verify no type errors

### 9. Run type checking
- Run `uv run mypy app/` - Full type checking on all application code
- Verify zero type errors

### 10. Run existing tests
- Run `uv run pytest app/tests/core/test_geometry.py -v` - Verify geometry tests pass
- Run `uv run pytest app/tests/core/test_content_zone.py -v` - Verify content zone tests pass
- Run `uv run pytest app/tests/ -v` - Run full test suite
- Verify all tests pass with zero failures

### 11. Run linting and formatting
- Run `uv run ruff check app/` - Linting
- Run `uv run ruff format app/ --check` - Format check
- Verify both pass with zero errors

### 12. Run final validation
- Execute all validation commands to ensure the feature works correctly with zero regressions

## Testing Strategy

### Unit Tests
- Existing tests in `test_geometry.py` and `test_content_zone.py` cover the `_detect_content_zone()` function behavior
- No new unit tests required as the changes are logging-only and UI text changes
- The logging changes don't affect function return values or behavior, only side effects (log output)

### Integration Tests
- Manual testing recommended for:
  - Verify INFO log messages appear during extraction in the GUI log viewer
  - Verify the updated hint text displays correctly in the GUI
  - Run extraction on a multi-block DXF to confirm per-block progress messages appear

### Edge Cases
- Blocks that trigger early exits (entity count threshold, edge count threshold)
- Blocks with no closed shapes
- Blocks that exceed polygon count threshold
- Blocks where all polygons are filtered out
- Blocks with successful content zone detection

### Playwright MCP Tests
Not applicable - these are logging additions and text label changes. Manual visual inspection and functional testing is appropriate for:
- Verifying log messages appear at expected times during extraction
- Verifying hint text displays correctly

## Acceptance Criteria
1. INFO log message `[{block_name}] Detecting content zone...` appears at start of content zone detection for each block
2. INFO log message `[{block_name}] Content zone detected: {width:.2f} x {height:.2f}` appears on successful detection
3. DEBUG log message appears for non-detection cases (except where WARNING already exists)
4. Units hint text reads "(applies to all numeric filters)" instead of "(applies to precision fix and gap bridge)"
5. All existing tests pass without modification
6. Type checking passes with zero errors
7. Linting passes with zero errors
8. Log messages use consistent `[{block_name}]` prefix format matching existing patterns

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The existing logging in `_detect_content_zone()` uses a consistent `[{block_name}]` prefix format. The new logging follows this pattern.
- The change from DEBUG to INFO for the completion message is intentional - this makes the progress feedback visible at the default INFO log level in the GUI.
- Early exit paths (entity count, edge count, polygon count thresholds) already have WARNING-level logs, so no additional logging is needed there.
- The "No closed shapes found" case already has DEBUG logging at line 1149.
- Only the "all polygons filtered" case (line 1197) needs new DEBUG logging.
- The hint text change is a simple string replacement with no functional impact.
