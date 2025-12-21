# Feature: Excel Column Order and Population for Block Attributes (Unit 2)

## Feature Description
Modify the All Blocks sheet in the Excel output to include block attribute data from the extraction results. This involves reordering the `block_layer_names` column to appear earlier (column B, after `block_raw_name`) and adding two new columns at the end: `block_attribute_count` and `block_attribute_data`. The attribute data column displays newline-separated TAG:VALUE pairs that are alphabetically sorted and truncated for display.

This is Unit 2 of the Block Attributes Excel implementation. Unit 1 completed the extraction of ATTRIB entities from INSERT blocks into the `block_attribute_data` field. This unit focuses on surfacing that data in the Excel output.

## User Story
As a CAD analyst
I want to see block attribute data in the All Blocks sheet
So that I can analyze product codes, department names, and other metadata alongside block information

## Problem Statement
The `block_attribute_data` field is now populated during extraction (Unit 1 complete), but this valuable metadata is not visible in the Excel output. Users need to see:
1. How many unique attribute tag-value pairs exist for each block
2. The actual attribute data in a readable format

Additionally, the current column order places `block_layer_names` at position 22 (after `block_layer_count`), but for usability it should appear earlier in the sheet, immediately after `block_raw_name` in column B.

## Solution Statement
Modify the `_create_all_blocks_sheet` function in `excel_writer.py` to:
1. Reorder columns so `block_layer_names` appears at position B (after `block_raw_name`)
2. Add `block_attribute_count` column at the end (after `block_scale_y`)
3. Add `block_attribute_data` column at the end
4. Populate these columns using data from `data.get("block_attribute_data", {})`
5. Format attribute data as newline-separated "TAG:VALUE" pairs, sorted alphabetically
6. Use existing `_truncate_segment_string()` function for truncation

The solution maintains backward compatibility by keeping all existing columns and data, just reordering and adding columns.

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/core/excel_writer.py` - Main implementation file. Contains `_create_all_blocks_sheet` function that creates the All Blocks sheet. Key locations:
  - Lines ~22-93: Import statements (add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT`, `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA`)
  - Lines ~1062-1093: Empty DataFrame column list (first occurrence - update order and add new columns)
  - Lines ~1227-1259: Row dict construction (second occurrence - update order and add new column values)
  - Lines ~1264-1295: Empty rows DataFrame column list (third occurrence - update order and add new columns)

### Constants (Already Defined)
- `app/core/constants.py` - Contains `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` (line 147) and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` (line 148). These constants are already defined from Unit 1 preparation.

### Test Files
- `app/tests/core/excel_writer/test_excel_writer_all_blocks.py` - Contains existing tests for All Blocks sheet. Add new tests for attribute columns.
- `app/tests/core/excel_writer/conftest.py` - Contains `sample_extraction_data` fixture. Update to include `block_attribute_data` with test values.

### Reference Files
- `app/tests/core/extractor/test_extractor_attributes.py` - Reference for how attribute data structure works (from Unit 1)
- `app/tests/assets/block_attributes_test.dxf` - Test fixture with blocks containing attributes

## Implementation Plan

### Phase 1: Foundation
Update imports and prepare test fixtures with attribute data.

1. Add missing constant imports to `excel_writer.py`
2. Update `sample_extraction_data` fixture in `conftest.py` to include attribute data

### Phase 2: Core Implementation
Modify `_create_all_blocks_sheet` to implement the new column order and population.

1. Update the empty DataFrame column list (~lines 1062-1093) to:
   - Move `EXCEL_COLUMN_BLOCK_LAYER_NAMES` to position after `EXCEL_COLUMN_BLOCK_RAW_NAME`
   - Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` at the end
   - Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` at the end
2. Get `block_attribute_data` from extraction results at function start
3. Update row dict construction (~lines 1227-1259) to:
   - Match new column order
   - Calculate and add `block_attribute_count` value
   - Format and add `block_attribute_data` value
4. Update the empty rows DataFrame column list (~lines 1264-1295) to match new order

### Phase 3: Integration
Ensure tests pass and the feature integrates correctly with existing functionality.

1. Update existing tests that check column count (29 -> 31 columns)
2. Update existing tests that check column order
3. Add new tests for attribute columns

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add constant imports to excel_writer.py
- Open `app/core/excel_writer.py`
- Find the import block from `.constants` (lines 22-93)
- Add imports for `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` in alphabetical order within the block
- Run `uv run mypy app/core/excel_writer.py` to verify no import errors

### 2. Update sample_extraction_data fixture with attribute data
- Open `app/tests/core/excel_writer/conftest.py`
- Find the `sample_extraction_data` fixture
- Update `block_attribute_data` from empty dict to include test data matching the blocks:
```python
"block_attribute_data": {
    "VALVE": [
        ("DEPT", "30"),
        ("PROD1", "Garage"),
        ("PROD2", "Door Openers"),
    ],
    "PIPE": [
        ("ID", "PIPE-001"),
    ],
    # TAG has no attributes
},
```
- Run `uv run pytest app/tests/core/excel_writer/conftest.py -v` to verify fixture loads

### 3. Get block_attribute_data at start of _create_all_blocks_sheet
- Open `app/core/excel_writer.py`
- Find the `_create_all_blocks_sheet` function (around line 1050)
- After the existing data extraction statements (~line 1057), add:
```python
block_attribute_data = data.get("block_attribute_data", {})
```
- Run `uv run mypy app/core/excel_writer.py` to verify no type errors

### 4. Update first column list (empty DataFrame case)
- Open `app/core/excel_writer.py`
- Find the first column list in `_create_all_blocks_sheet` (~lines 1062-1093)
- This is the `df = pd.DataFrame(columns=[...])` for when `all_block_definitions` is empty
- Reorganize the columns:
  1. Keep `EXCEL_COLUMN_BLOCK_RAW_NAME` first
  2. Move `EXCEL_COLUMN_BLOCK_LAYER_NAMES` to second position (was at position ~22)
  3. Keep remaining columns in current relative order (just remove `EXCEL_COLUMN_BLOCK_LAYER_NAMES` from its old position)
  4. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` at the end (after `EXCEL_COLUMN_BLOCK_SCALE_Y`)
  5. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` at the very end
- The new order should be:
```python
columns=[
    EXCEL_COLUMN_BLOCK_RAW_NAME,
    EXCEL_COLUMN_BLOCK_LAYER_NAMES,  # Moved from position 22
    EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
    EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
    EXCEL_COLUMN_BLOCK_IS_NESTED,
    EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_COUNT,
    # EXCEL_COLUMN_BLOCK_LAYER_NAMES removed from here
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT,  # New
    EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA,   # New
]
```
- Run `uv run mypy app/core/excel_writer.py` to verify no type errors

### 5. Update row dict construction with attribute data
- Open `app/core/excel_writer.py`
- Find the `rows.append({...})` section (~lines 1227-1259)
- Before the `rows.append()` call, add attribute calculation:
```python
# Get attributes for this block
attrs = block_attribute_data.get(resolved_name, [])
attr_count = len(attrs)

# Format as newline-separated TAG:VALUE pairs (already sorted from extraction)
attr_str = "\n".join(f"{tag}:{value}" for tag, value in attrs)
attr_str = _truncate_segment_string(attr_str)
```
- Update the row dict to match new column order and include new values:
```python
rows.append(
    {
        EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
        EXCEL_COLUMN_BLOCK_LAYER_NAMES: block_layer_names,  # Moved up
        EXCEL_COLUMN_BLOCK_RESOLVED_NAME: resolved_name,
        EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: trim_left,
        EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: trim_right,
        EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: trim_top,
        EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: trim_bottom,
        EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: vertical_segments_str,
        EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: horizontal_segments_str,
        EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: native_width,
        EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: native_height,
        EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: detected,
        EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: cz_width,
        EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: cz_height,
        EXCEL_COLUMN_BLOCK_POLYGON_COUNT: poly_count,
        EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: filtered_poly_count,
        EXCEL_COLUMN_BLOCK_INSERTION_STATUS: insertion_status,
        EXCEL_COLUMN_BLOCK_IS_NESTED: record["block_is_nested"],
        EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: parent_names_str,
        EXCEL_COLUMN_BLOCK_ENTITY_COUNT: record["block_entity_count"],
        EXCEL_COLUMN_BLOCK_INSERTION_COUNT: block_insertion_count,
        EXCEL_COLUMN_BLOCK_LAYER_COUNT: block_layer_count,
        # EXCEL_COLUMN_BLOCK_LAYER_NAMES removed from here
        EXCEL_COLUMN_BLOCK_ROTATION_0: rot_0,
        EXCEL_COLUMN_BLOCK_ROTATION_90: rot_90,
        EXCEL_COLUMN_BLOCK_ROTATION_180: rot_180,
        EXCEL_COLUMN_BLOCK_ROTATION_270: rot_270,
        EXCEL_COLUMN_BLOCK_ROTATION_OTHER: rot_other,
        EXCEL_COLUMN_BLOCK_SCALE_X: x_scale,
        EXCEL_COLUMN_BLOCK_SCALE_Y: y_scale,
        EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT: attr_count,
        EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA: attr_str,
    }
)
```
- Run `uv run mypy app/core/excel_writer.py` to verify no type errors

### 6. Update third column list (empty rows DataFrame case)
- Open `app/core/excel_writer.py`
- Find the third column list in `_create_all_blocks_sheet` (~lines 1264-1295)
- This is the `df = pd.DataFrame(columns=[...])` for when all blocks are system blocks
- Update to match the same column order as step 4 (exactly the same list)
- Run `uv run mypy app/core/excel_writer.py` to verify no type errors

### 7. Update existing tests for new column count
- Open `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`
- Find tests that check column count (search for "29")
- Update assertions from 29 to 31 columns
- Key tests to update:
  - `test_all_blocks_sheet_has_29_columns` - rename and update assertion
  - `test_all_blocks_empty_data_creates_headers_only` - update assertion
  - `test_all_blocks_only_system_blocks_creates_empty_sheet` - update assertion
- Run tests to verify: `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v`

### 8. Update column order test
- Open `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`
- Find `test_all_blocks_sheet_column_names`
- Update the `expected_columns` list to match new order:
  1. Move `EXCEL_COLUMN_BLOCK_LAYER_NAMES` to position 2 (after raw_name)
  2. Remove it from position ~22
  3. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` at the end
  4. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` at the very end
- Add imports for `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA`
- Run test: `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py::TestAllBlocksSheet::test_all_blocks_sheet_column_names -v`

### 9. Add new tests for attribute columns
- Open `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`
- Add new test methods at the end of `TestAllBlocksSheet` class:

```python
def test_all_blocks_attribute_count(
    self, temp_dir: str, sample_extraction_data: ExtractionResult
) -> None:
    """Test that attribute count is correctly populated."""
    output_path = os.path.join(temp_dir, "test_output.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _create_all_blocks_sheet(sample_extraction_data, writer)

    df = pd.read_excel(output_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

    # VALVE has 3 attributes in fixture
    valve_row = df[df[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "VALVE"]
    assert valve_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT)] == 3

    # PIPE has 1 attribute
    pipe_row = df[df[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "PIPE"]
    assert pipe_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT)] == 1

    # TAG has 0 attributes
    tag_row = df[df[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "TAG"]
    assert tag_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT)] == 0

def test_all_blocks_attribute_data_format(
    self, temp_dir: str, sample_extraction_data: ExtractionResult
) -> None:
    """Test that attribute data is formatted as newline-separated TAG:VALUE pairs."""
    output_path = os.path.join(temp_dir, "test_output.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _create_all_blocks_sheet(sample_extraction_data, writer)

    df = pd.read_excel(output_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

    # VALVE should have formatted attribute data
    valve_row = df[df[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "VALVE"]
    attr_data = valve_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA)]

    # Should contain TAG:VALUE format
    assert "DEPT:30" in attr_data
    assert "PROD1:Garage" in attr_data
    assert "PROD2:Door Openers" in attr_data

    # Should be newline-separated
    assert "\n" in attr_data

def test_all_blocks_attribute_data_empty_block(
    self, temp_dir: str, sample_extraction_data: ExtractionResult
) -> None:
    """Test that blocks without attributes have empty attribute data."""
    output_path = os.path.join(temp_dir, "test_output.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _create_all_blocks_sheet(sample_extraction_data, writer)

    df = pd.read_excel(output_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

    # TAG has no attributes
    tag_row = df[df[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "TAG"]
    attr_data = tag_row.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA)]

    # Should be empty string or NaN
    assert pd.isna(attr_data) or attr_data == ""

def test_all_blocks_layer_names_column_position(
    self, temp_dir: str, sample_extraction_data: ExtractionResult
) -> None:
    """Test that block_layer_names column is at position B (index 1)."""
    output_path = os.path.join(temp_dir, "test_output.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _create_all_blocks_sheet(sample_extraction_data, writer)

    df = pd.read_excel(output_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

    # Column at index 1 should be block_layer_names
    assert df.columns[1] == format_header(EXCEL_COLUMN_BLOCK_LAYER_NAMES)
```
- Run new tests: `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v -k "attribute or layer_names_column"`

### 10. Update other fixtures that use ExtractionResult
- Open `app/tests/core/excel_writer/conftest.py`
- Update the remaining fixtures (`annotation_extraction_data`, `color_analysis_data`, `extraction_issues_data`, `no_issues_data`) to ensure they have `block_attribute_data` key (they already do, but verify the dict value matches expected structure)
- Run all conftest fixtures: `uv run pytest app/tests/core/excel_writer/ -v`

### 11. Run full validation
- Run `uv run mypy app/` - Full type checking - must pass with 0 errors
- Run `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run all All Blocks sheet tests
- Run `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- Run `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- Run `uv run ruff check app/` - Run linter - must pass with 0 errors
- Run `uv run ruff format app/ --check` - Verify code formatting - must pass

## Testing Strategy

### Unit Tests
- **Column count test**: Verify All Blocks sheet has exactly 31 columns (updated from 29)
- **Column order test**: Verify columns appear in correct order with `block_layer_names` at position B
- **Attribute count test**: Verify `block_attribute_count` correctly reflects number of unique tag-value pairs
- **Attribute data format test**: Verify data is formatted as "TAG:VALUE" pairs separated by newlines
- **Empty attribute test**: Verify blocks without attributes have 0 count and empty data field
- **Truncation test**: Verify long attribute strings are truncated using `_truncate_segment_string()`

### Integration Tests
- **End-to-end extraction and export**: Extract from `block_attributes_test.dxf` and verify attribute data appears in Excel
- **Empty file handling**: Verify empty DXF files produce sheet with correct 31 column headers

### Edge Cases
- Block with no attributes (count=0, data="")
- Block with single attribute
- Block with many attributes (truncation scenario)
- Block with attribute values containing special characters
- All blocks are system blocks (empty sheet with headers)
- No block definitions at all (empty sheet with headers)

### Playwright MCP Tests
Not applicable - this is a backend Excel generation feature with no UI changes.

## Acceptance Criteria
1. All Blocks sheet has exactly 31 columns (was 29)
2. `block_layer_names` column appears at position B (after `block_raw_name`)
3. `block_attribute_count` column appears at position 30 (after `block_scale_y`)
4. `block_attribute_data` column appears at position 31 (last column)
5. `block_attribute_count` shows the number of unique (tag, value) pairs for each block
6. `block_attribute_data` shows newline-separated "TAG:VALUE" pairs, sorted alphabetically
7. Long attribute data strings are truncated using existing `_truncate_segment_string()` function
8. Blocks without attributes show 0 count and empty data field
9. All existing tests pass without modification (after updating column count/order assertions)
10. Type checking passes with zero errors
11. Code follows existing patterns in excel_writer.py

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/excel_writer.py` - Type check excel_writer module
- `uv run mypy app/` - Full type checking - must pass with 0 errors
- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks sheet tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- `uv run pytest app/tests/core/extractor/test_extractor_attributes.py -v` - Verify attribute extraction tests still pass
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The constants `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` and `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` already exist in `constants.py` (lines 147-148) from Unit 1 preparation
- The `block_attribute_data` field in `ExtractionResult` is populated as `dict[str, list[tuple[str, str]]]` where the list is already sorted alphabetically by (tag, value)
- The `_truncate_segment_string()` function (lines 118-143) handles truncation with "..." suffix when exceeding `SEGMENT_MAX_DISPLAY_LENGTH` (200 chars)
- Column reordering requires updating all three occurrences of the column list in `_create_all_blocks_sheet`:
  1. Empty `all_block_definitions` case (~line 1062)
  2. Row dict construction (~line 1227)
  3. Empty rows (all system blocks) case (~line 1264)
- Unit 1 confirmed all 1123 tests are passing before this unit begins
- This is Unit 2 of a multi-unit implementation; Unit 3 may add formatting or additional features
