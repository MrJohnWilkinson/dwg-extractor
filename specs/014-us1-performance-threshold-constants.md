# Chore: Performance Threshold Constants (US-1)

## Chore Description
As a DXF block analyzer, I want performance threshold constants defined upfront so that all subsequent algorithms have safeguards against exponential complexity from day one.

This chore establishes the foundational constants that will be used by content zone detection algorithms to prevent performance degradation when processing complex DXF blocks. The constants include:

1. **POLYGON_COUNT_THRESHOLD (30)** - Maximum polygons for content zone net area calculation. Blocks with more polygons skip content zone detection because `_calculate_net_areas()` is O(n^3) - 102 polygons resulted in 140+ seconds processing time.

2. **LINE_SEGMENT_THRESHOLD (200)** - Maximum LINE segments for cycle detection DFS. Blocks with more LINE segments skip LINE cycle extraction because DFS on 967 segments (504 vertices) caused 6+ minute hangs.

3. **CYCLE_DETECTION_TIMEOUT_SECONDS (5.0)** - Safety timeout for cycle detection algorithm. Prevents indefinite hang even if threshold check is bypassed.

4. **Excel column constants** for content zone fields that will be used in reporting.

## Relevant Files
Use these files to resolve the chore:

- `app/core/constants.py` - Main constants file where all new constants will be added. This file already contains Excel column constants and follows a consistent pattern of typed constants with documentation.
- `app/tests/core/test_logger.py` - Reference for test file structure and patterns used in this codebase.
- `app_docs/005-field-naming-convention.md` - Field naming convention guide for Excel columns (referenced in constants.py comments).

### New Files
- `app/tests/core/test_constants.py` - New test file to validate that threshold constants are within reasonable bounds.

## Step by Step Tasks

### Step 1: Add Content Zone Detection Threshold Constants to constants.py

Add the following constants to `app/core/constants.py` after the existing UI messages section:

- Add a section comment `# Content Zone Detection Thresholds`
- Add `POLYGON_COUNT_THRESHOLD: int = 30` with docstring explaining the O(n^3) rationale
- Add `LINE_SEGMENT_THRESHOLD: int = 200` with docstring explaining the DFS hang rationale
- Add `CYCLE_DETECTION_TIMEOUT_SECONDS: float = 5.0` with docstring explaining its purpose as a safety timeout

### Step 2: Add Content Zone Excel Column Constants to constants.py

Add the following Excel column constants to `app/core/constants.py` in a new section after the existing Excel column sections:

- Add a section comment `# Excel configuration - Content Zone columns`
- Add reference comment to `app_docs/005-field-naming-convention.md`
- Add `EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: str = "block_suggested_trim_left"`
- Add `EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: str = "block_suggested_trim_right"`
- Add `EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: str = "block_suggested_trim_top"`
- Add `EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: str = "block_suggested_trim_bottom"`
- Add `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: str = "block_content_zone_detected"`

### Step 3: Create Test File for Constants Validation

Create `app/tests/core/test_constants.py` with the following tests:

- Import the new constants from `core.constants`
- Add `test_polygon_threshold_reasonable()` - Assert threshold is between 10 and 100
- Add `test_line_threshold_reasonable()` - Assert threshold is between 50 and 500
- Add `test_timeout_reasonable()` - Assert timeout is between 1.0 and 30.0 seconds
- Add `test_content_zone_excel_columns_follow_naming_convention()` - Assert all content zone columns start with "block_" prefix

### Step 4: Run Validation Commands

Execute every command to validate the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- Run tests to validate the chore is complete with zero regressions
    - `uv run pytest app/tests/`
    - `uv run mypy app/`
    - `uv run ruff check app/`
    - `uv run ruff format app/`
    - `uv run ruff check app/ --fix`

## Notes

- The threshold values (30, 200, 5.0) are derived from empirical performance analysis documented in the content zone optimization retrospective. These values represent a balance between detecting content zones in typical blocks while avoiding exponential slowdowns on complex blocks.
- The Excel column names follow the established naming convention in `app_docs/005-field-naming-convention.md` using the pattern: `{domain}_{attribute}` where domain is "block" and attributes describe the suggested trim values and detection status.
- These constants lay the groundwork for subsequent user stories that will implement the actual content zone detection algorithms.
