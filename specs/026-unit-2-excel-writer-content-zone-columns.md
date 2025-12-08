# Feature: Excel Writer Content Zone Column Updates

## Feature Description
Update the Excel writer to include three new content zone columns (`block_content_zone_width`, `block_content_zone_height`, `block_polygon_count`) in the Block Geometry Analysis sheet output. These columns complement the existing content zone detection fields by providing dimensional data and polygon analysis results that users need to understand the detected content zones.

## User Story
As a CAD analyst
I want to see content zone dimensions and polygon counts in the Excel output
So that I can validate content zone detection results and understand the geometric analysis of each block

## Problem Statement
Unit 1 added three new fields to the `ContentZoneData` TypedDict (`content_zone_width`, `content_zone_height`, `polygon_count`) and corresponding Excel column constants. However, the Excel writer does not yet extract these values from the extraction data or include them in the Block Geometry Analysis sheet output. Users cannot see these important metrics in their Excel reports.

## Solution Statement
Extend the `_create_block_geometry_analysis_sheet` function in `excel_writer.py` to:
1. Import the three new column constants
2. Extract width, height, and polygon count values from `ContentZoneData`
3. Add these values to the row dictionary with proper handling for detected/undetected cases
4. Update the empty DataFrame column list to include the new columns

This maintains the existing pattern of content zone column handling where:
- Width/height display values when content zone is detected, empty string otherwise
- Polygon count is always present (0 for no polygons, actual count otherwise)

## Relevant Files
Use these files to implement the feature:

- **`app/core/excel_writer.py`** - Main file to modify. Contains `_create_block_geometry_analysis_sheet` function that builds Block Geometry Analysis sheet rows. Needs imports for new constants and logic to extract/display new column values.
- **`app/core/constants.py`** - Already contains the three new constants from Unit 1 (`EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH`, `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT`, `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`). No changes needed.
- **`app/core/types.py`** - Already contains updated `ContentZoneData` TypedDict with `content_zone_width`, `content_zone_height`, `polygon_count` fields from Unit 1. No changes needed.
- **`app/tests/core/excel_writer/conftest.py`** - Contains test fixtures with `block_content_zone_data` that already include the new fields from Unit 1. Used by tests.
- **`app/tests/core/excel_writer/test_excel_writer_core.py`** - Contains existing tests for Block Geometry Analysis sheet including `TestContentZoneExcelOutput` class. Tests need updating to verify new columns.

### New Files
None required - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Add the three new column constant imports to `excel_writer.py`. This is a simple import addition that sets up access to the constants needed for the column names.

### Phase 2: Core Implementation
Update the `_create_block_geometry_analysis_sheet` function to:
1. Extract `content_zone_width`, `content_zone_height`, and `polygon_count` from `ContentZoneData`
2. Handle the conditional logic: width/height only when detected, polygon_count always present
3. Add the three new key-value pairs to the row dictionary
4. Update the empty DataFrame columns list for header-only output

### Phase 3: Integration
Add comprehensive tests to verify:
1. New columns appear in DataFrame output with correct headers
2. Values are correctly populated when content zone is detected
3. Empty strings used for width/height when not detected
4. Polygon count displays 0 when no polygons found
5. All existing tests continue to pass (column count increases from 18 to 21)

## Step by Step Tasks

### Step 1: Add New Constant Imports
- Open `app/core/excel_writer.py`
- Locate the import block for constants (around line 22-79)
- Add imports for the three new constants after `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED`:
  ```python
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
  EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
  ```

### Step 2: Update Row Building Logic
- Locate the `_create_block_geometry_analysis_sheet` function (starts around line 527)
- Find the content zone extraction section (after line 645 where `content_zone` is retrieved)
- After the existing trim value extraction (around line 657), add extraction of new fields:
  ```python
  # When content_zone_detected is True:
  cz_width: float | str = content_zone["content_zone_width"] or ""
  cz_height: float | str = content_zone["content_zone_height"] or ""
  poly_count: int | str = content_zone["polygon_count"]

  # When content_zone is None or not detected:
  cz_width = ""
  cz_height = ""
  poly_count = content_zone["polygon_count"] if content_zone else ""
  ```

### Step 3: Add New Columns to Row Dictionary
- Locate the `rows.append()` call that builds the row dictionary (around line 659-679)
- Add the three new key-value pairs after `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED`:
  ```python
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: cz_width,
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: cz_height,
  EXCEL_COLUMN_BLOCK_POLYGON_COUNT: poly_count,
  ```

### Step 4: Update Empty DataFrame Columns
- Locate the empty DataFrame creation for header-only output (around line 686-708)
- Add the three new column constants to the columns list after `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED`:
  ```python
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
  EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
  ```

### Step 5: Update Existing Tests for New Column Count
- Open `app/tests/core/excel_writer/test_excel_writer_core.py`
- Update `test_block_geometry_analysis_sheet_consolidated` to expect 21 columns instead of 18
- Update `test_block_geometry_analysis_empty_data` to expect 21 column headers
- Update `test_content_zone_column_count` to expect 21 columns (13 original + 8 content zone)
- Update `test_constants_match_dataframe_columns` to include the three new formatted headers

### Step 6: Add New Column Header Tests
- Add test `test_new_content_zone_columns_in_headers` to verify all three new columns appear in DataFrame headers with correct Title Case formatting
- Verify column order: width, height, polygon_count appear after content_zone_detected

### Step 7: Add Content Zone Width/Height Value Tests
- Add test `test_content_zone_width_height_populated_when_detected` to verify width/height values are correctly populated when content zone is detected
- Add test `test_content_zone_width_height_empty_when_not_detected` to verify empty string used when content zone not detected

### Step 8: Add Polygon Count Tests
- Add test `test_polygon_count_always_present` to verify polygon_count appears for all rows
- Add test `test_polygon_count_zero_when_no_polygons` to verify 0 displayed when polygon_count is 0
- Add test `test_polygon_count_value_when_polygons_found` to verify actual count displayed

### Step 9: Run Validation Commands
- Run full test suite to ensure all tests pass
- Run type checking to ensure no type errors
- Run linting to ensure code style compliance

## Testing Strategy

### Unit Tests
- **Header Tests**: Verify new columns appear with correct formatted names ("Block Content Zone Width", "Block Content Zone Height", "Block Polygon Count")
- **Value Tests**: Verify values extracted correctly from ContentZoneData
- **Empty State Tests**: Verify proper handling when content zone not detected

### Integration Tests
- **End-to-End Excel Output**: Generate Excel file from real extraction data and verify new columns contain expected values
- **Fixture Integration**: Ensure test fixtures already updated in Unit 1 work correctly with new column output

### Edge Cases
- Content zone detected but width/height are None (should display empty string)
- Content zone not detected (width/height empty, polygon_count from data or empty)
- Empty block_content_zone_data dictionary (all content zone columns empty)
- Polygon count of 0 vs missing polygon_count field

### Playwright MCP Tests
Not applicable - this is backend Excel generation functionality with no UI component.

## Acceptance Criteria
1. Block Geometry Analysis sheet has 21 columns (was 18)
2. Column headers display as "Block Content Zone Width", "Block Content Zone Height", "Block Polygon Count"
3. Width and height show numeric values when content_zone_detected is True
4. Width and height show empty string when content_zone_detected is False
5. Polygon count shows 0 or actual count, always present when content_zone data exists
6. All 486+ existing tests continue to pass
7. No type errors from mypy
8. No linting errors from ruff

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_writer/ -v` - Run Excel writer tests to validate new columns work correctly
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run mypy app/` - Run type checking to ensure no type errors
- `uv run ruff check app/` - Run linting to ensure code style compliance

## Notes
- Unit 1 already added the constants and updated the ContentZoneData TypedDict, so this unit focuses solely on the Excel writer integration
- Test fixtures in `conftest.py` already include the new fields with sample data from Unit 1
- The column order follows the established pattern: trim values, detected flag, then dimensions, then polygon count
- No new libraries required
