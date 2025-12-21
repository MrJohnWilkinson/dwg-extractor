# Chore: Unit 3 - Excel Formatting Updates for Block Attributes

## Chore Description
Update the `_format_all_blocks_sheet` function in `excel_formatting.py` to align with the column order and count changes made in Unit 2. The All Blocks sheet now has 31 columns (was 29) with `block_layer_names` moved to column B (was column V at position 22) and two new columns added at the end: `block_attribute_count` (column AD, position 30) and `block_attribute_data` (column AE, position 31).

This unit updates:
1. Column width assignments to reflect the new column order
2. Adding column widths for the two new attribute columns
3. Text wrap column indices to account for the reordering
4. Scale highlighting column indices (scale_x and scale_y moved from AB/AC to AD/AE)
5. Row highlighting range to cover all 31 columns
6. Test fixtures to reflect the new 31-column structure

## Relevant Files
Use these files to resolve the chore:

### Core Implementation Files
- `app/core/excel_formatting.py` - Main implementation file. Contains `_format_all_blocks_sheet` function that applies formatting to the All Blocks sheet. Key updates needed:
  - Lines 591-620: Column width assignments need updating for new order and new columns
  - Line 630: `wrap_columns` list needs updating for new column positions
  - Lines 676-679: Scale column indices need updating (were 28/29, now 30/31)
  - Line 707: Row highlighting range needs updating (was 30, now 32)

### Test Files
- `app/tests/core/excel_formatting/test_formatting_all_blocks.py` - Contains tests for `_format_all_blocks_sheet`. Key updates needed:
  - Lines 35-67: `_create_test_workbook_with_headers` method - update headers list to 31 columns with new order
  - Lines 76-108: Test data rows need updating to match new column order
  - Lines 113: Auto-filter range assertion needs updating (A1:AC2 -> A1:AE2)
  - Lines 122-132: Column width assertions need updating for new positions
  - Lines 331, 371-374: Row highlighting range assertions need updating (29 -> 31 columns)
  - All test methods with data rows need updating for new column order and count

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Analyze the new column order
The new column order from Unit 2 is:
| Position | Column | Field Name |
|----------|--------|------------|
| 1 | A | block_raw_name |
| 2 | B | block_layer_names (MOVED from position 22) |
| 3 | C | block_resolved_name |
| 4 | D | block_suggested_trim_left |
| 5 | E | block_suggested_trim_right |
| 6 | F | block_suggested_trim_top |
| 7 | G | block_suggested_trim_bottom |
| 8 | H | block_vertical_segments |
| 9 | I | block_horizontal_segments |
| 10 | J | block_native_width |
| 11 | K | block_native_height |
| 12 | L | block_content_zone_detected |
| 13 | M | block_content_zone_width |
| 14 | N | block_content_zone_height |
| 15 | O | block_polygon_count |
| 16 | P | block_filtered_polygon_count |
| 17 | Q | block_insertion_status |
| 18 | R | block_is_nested |
| 19 | S | block_nested_parent_names |
| 20 | T | block_entity_count |
| 21 | U | block_insertion_count |
| 22 | V | block_layer_count |
| 23 | W | block_rotation_0 |
| 24 | X | block_rotation_90 |
| 25 | Y | block_rotation_180 |
| 26 | Z | block_rotation_270 |
| 27 | AA | block_rotation_other |
| 28 | AB | block_scale_x |
| 29 | AC | block_scale_y |
| 30 | AD | block_attribute_count (NEW) |
| 31 | AE | block_attribute_data (NEW) |

### 2. Update column widths in _format_all_blocks_sheet
- Open `app/core/excel_formatting.py`
- Find the column width section in `_format_all_blocks_sheet` (around lines 591-620)
- Update the comment to reflect 31 columns (A-AE)
- Update column width assignments to match new order:
```python
# Set column widths (31 columns: A-AE)
ws.column_dimensions["A"].width = 35  # block_raw_name
ws.column_dimensions["B"].width = 35  # block_layer_names (MOVED here)
ws.column_dimensions["C"].width = 35  # block_resolved_name
ws.column_dimensions["D"].width = 12  # block_suggested_trim_left
ws.column_dimensions["E"].width = 12  # block_suggested_trim_right
ws.column_dimensions["F"].width = 12  # block_suggested_trim_top
ws.column_dimensions["G"].width = 12  # block_suggested_trim_bottom
ws.column_dimensions["H"].width = 50  # block_vertical_segments
ws.column_dimensions["I"].width = 50  # block_horizontal_segments
ws.column_dimensions["J"].width = 15  # block_native_width
ws.column_dimensions["K"].width = 15  # block_native_height
ws.column_dimensions["L"].width = 18  # block_content_zone_detected
ws.column_dimensions["M"].width = 18  # block_content_zone_width
ws.column_dimensions["N"].width = 18  # block_content_zone_height
ws.column_dimensions["O"].width = 15  # block_polygon_count
ws.column_dimensions["P"].width = 18  # block_filtered_polygon_count
ws.column_dimensions["Q"].width = 18  # block_insertion_status
ws.column_dimensions["R"].width = 12  # block_is_nested
ws.column_dimensions["S"].width = 35  # block_nested_parent_names
ws.column_dimensions["T"].width = 15  # block_entity_count
ws.column_dimensions["U"].width = 18  # block_insertion_count
ws.column_dimensions["V"].width = 12  # block_layer_count
ws.column_dimensions["W"].width = 10  # block_rotation_0
ws.column_dimensions["X"].width = 10  # block_rotation_90
ws.column_dimensions["Y"].width = 10  # block_rotation_180
ws.column_dimensions["Z"].width = 10  # block_rotation_270
ws.column_dimensions["AA"].width = 12  # block_rotation_other
ws.column_dimensions["AB"].width = 12  # block_scale_x
ws.column_dimensions["AC"].width = 12  # block_scale_y
ws.column_dimensions["AD"].width = 12  # block_attribute_count (NEW)
ws.column_dimensions["AE"].width = 60  # block_attribute_data (NEW)
```
- Run `uv run mypy app/core/excel_formatting.py` to verify no type errors

### 3. Update wrap_columns list for text wrapping
- Open `app/core/excel_formatting.py`
- Find the `wrap_columns` list (around line 630)
- Update column indices for new positions:
  - A (1): block_raw_name - keep
  - B (2): block_layer_names - ADD (moved here, needs wrap)
  - C (3): block_resolved_name - ADD (was at position 2, now at 3)
  - H (8): block_vertical_segments - keep (was G=7)
  - I (9): block_horizontal_segments - keep (was H=8)
  - S (19): block_nested_parent_names - UPDATE (was R=18)
  - AE (31): block_attribute_data - ADD (new column, needs wrap for newline-separated TAG:VALUE pairs)
- Update the comment and list:
```python
# Apply text wrapping for data rows in columns with potentially long text
# Columns: A (raw_name), B (layer_names), C (resolved_name), H (vert_segments),
#          I (horiz_segments), S (parent_names), AE (attribute_data)
wrap_columns = [1, 2, 3, 8, 9, 19, 31]  # Column indices (1-based)
```
- Run `uv run mypy app/core/excel_formatting.py` to verify no type errors

### 4. Update scale column indices for highlighting
- Open `app/core/excel_formatting.py`
- Find the scale column index section (around lines 676-679)
- The scale columns have NOT moved - they are still at AB (28) and AC (29)
- Update the comment to clarify the column count change:
```python
# Iterate through data rows (skip header at row 1)
# Scale columns are AB (28 = x_scale) and AC (29 = y_scale)
# Note: Column indices unchanged from pre-Unit-2; new columns AD/AE added after
```
- No actual code change needed for scale column indices

### 5. Update row highlighting range
- Open `app/core/excel_formatting.py`
- Find the row highlighting loop (around line 707)
- Update the range from 30 to 32 to cover all 31 columns (A-AE):
```python
# Apply fill to entire row (all 31 columns A-AE) if highlighting is needed
if fill_to_apply is not None:
    for col_idx in range(1, 32):  # Columns A through AE (1-31)
        ws.cell(row=row_idx, column=col_idx).fill = fill_to_apply
```
- Run `uv run mypy app/core/excel_formatting.py` to verify no type errors

### 6. Update test headers in test_formatting_all_blocks.py
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Find `_create_test_workbook_with_headers` method (around lines 29-68)
- Update the comment to reflect 31 columns
- Update the headers list to match new order:
```python
def _create_test_workbook_with_headers(self) -> tuple[Workbook, Worksheet]:
    """Create a test workbook with All Blocks sheet and headers."""
    wb = Workbook()
    ws = cast(Worksheet, wb.active)
    ws.title = EXCEL_SHEET_ALL_BLOCKS

    # Add all 31 column headers (new order from Unit 2)
    headers = [
        "block_raw_name",           # A
        "block_layer_names",        # B (MOVED from position 22)
        "block_resolved_name",      # C
        "block_suggested_trim_left",    # D
        "block_suggested_trim_right",   # E
        "block_suggested_trim_top",     # F
        "block_suggested_trim_bottom",  # G
        "block_vertical_segments",      # H
        "block_horizontal_segments",    # I
        "block_native_width",           # J
        "block_native_height",          # K
        "block_content_zone_detected",  # L
        "block_content_zone_width",     # M
        "block_content_zone_height",    # N
        "block_polygon_count",          # O
        "block_filtered_polygon_count", # P
        "block_insertion_status",       # Q
        "block_is_nested",              # R
        "block_nested_parent_names",    # S
        "block_entity_count",           # T
        "block_insertion_count",        # U
        "block_layer_count",            # V
        "block_rotation_0",             # W
        "block_rotation_90",            # X
        "block_rotation_180",           # Y
        "block_rotation_270",           # Z
        "block_rotation_other",         # AA
        "block_scale_x",                # AB
        "block_scale_y",                # AC
        "block_attribute_count",        # AD (NEW)
        "block_attribute_data",         # AE (NEW)
    ]
    ws.append(headers)
    return wb, ws
```
- Run `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` to see which tests need data row updates

### 7. Create helper function for test data rows
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Add a helper method to create test data rows with the new 31-column structure:
```python
def _create_test_data_row(
    self,
    raw_name: str = "VALVE",
    layer_names: str = "Layer1, Layer2",
    resolved_name: str = "VALVE",
    scale_x: float | str = 1.0,
    scale_y: float | str = 1.0,
    attribute_count: int = 0,
    attribute_data: str = "",
) -> list[object]:
    """Create a test data row with 31 columns in new order."""
    return [
        raw_name,           # A: block_raw_name
        layer_names,        # B: block_layer_names (MOVED)
        resolved_name,      # C: block_resolved_name
        10.0,               # D: trim_left
        10.0,               # E: trim_right
        5.0,                # F: trim_top
        5.0,                # G: trim_bottom
        "10, 80, 10",       # H: vertical_segments
        "5, 40, 5",         # I: horizontal_segments
        100.0,              # J: native_width
        50.0,               # K: native_height
        "TRUE",             # L: content_zone_detected
        80.0,               # M: content_zone_width
        40.0,               # N: content_zone_height
        2,                  # O: polygon_count
        2,                  # P: filtered_polygon_count
        "Inserted",         # Q: insertion_status
        False,              # R: is_nested
        "",                 # S: parent_names
        8,                  # T: entity_count
        10,                 # U: insertion_count
        2,                  # V: layer_count
        5,                  # W: rotation_0
        2,                  # X: rotation_90
        0,                  # Y: rotation_180
        0,                  # Z: rotation_270
        0,                  # AA: rotation_other
        scale_x,            # AB: scale_x
        scale_y,            # AC: scale_y
        attribute_count,    # AD: attribute_count (NEW)
        attribute_data,     # AE: attribute_data (NEW)
    ]
```

### 8. Update test_format_all_blocks_autofilter
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Find `test_format_all_blocks_autofilter` method
- Update the data row to use 31 columns (or use the helper)
- Update the assertion from "A1:AC2" to "A1:AE2":
```python
assert ws.auto_filter.ref == "A1:AE2"
```

### 9. Update test_format_all_blocks_column_widths
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Find `test_format_all_blocks_column_widths` method
- Update assertions to match new column positions:
```python
def test_format_all_blocks_column_widths(self) -> None:
    """Test that column widths are set correctly for all 31 columns."""
    wb, ws = self._create_test_workbook_with_headers()

    _format_all_blocks_sheet(wb)

    # Check key column widths (updated for new column order)
    assert ws.column_dimensions["A"].width == 35  # block_raw_name
    assert ws.column_dimensions["B"].width == 35  # block_layer_names (NEW position)
    assert ws.column_dimensions["C"].width == 35  # block_resolved_name
    assert ws.column_dimensions["AB"].width == 12  # block_scale_x
    assert ws.column_dimensions["AC"].width == 12  # block_scale_y
    assert ws.column_dimensions["AD"].width == 12  # block_attribute_count (NEW)
    assert ws.column_dimensions["AE"].width == 60  # block_attribute_data (NEW)
    assert ws.column_dimensions["H"].width == 50  # block_vertical_segments
    assert ws.column_dimensions["I"].width == 50  # block_horizontal_segments
    assert ws.column_dimensions["P"].width == 18  # block_filtered_polygon_count
```

### 10. Update all test data rows in test methods
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Update each test method that creates data rows:
  - `test_format_all_blocks_autofilter` - update data row
  - `test_format_all_blocks_red_highlighting_varies_negative` - update data row
  - `test_format_all_blocks_orange_highlighting_negative_number` - update data row
  - `test_format_all_blocks_yellow_highlighting_varies` - update data row
  - `test_format_all_blocks_no_highlighting_positive_scales` - update data row
  - `test_format_all_blocks_entire_row_highlighted` - update data row and range assertion
  - `test_format_all_blocks_segment_columns_text_wrap` - update data row and column assertions
  - `test_format_all_blocks_highlighting_priority` - update data row
  - `test_format_all_blocks_y_scale_varies_negative` - update data row
  - `test_format_all_blocks_negative_x_scale` - update data row
- Use the helper method or inline the 31-column data rows
- Run tests after each update to verify

### 11. Update test_format_all_blocks_entire_row_highlighted
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Find `test_format_all_blocks_entire_row_highlighted` method
- Update the docstring to mention 31 columns
- Update the assertion range from 30 to 32:
```python
def test_format_all_blocks_entire_row_highlighted(self) -> None:
    """Test that entire row (all 31 columns) is highlighted for scale issues."""
    # ... create test data with 31 columns ...

    _format_all_blocks_sheet(wb)

    # All 31 columns of row 2 should have red fill
    for col_idx in range(1, 32):
        cell_fill = ws.cell(row=2, column=col_idx).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
        assert cell_fill.fill_type == "solid"
```

### 12. Update test_format_all_blocks_segment_columns_text_wrap
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Find `test_format_all_blocks_segment_columns_text_wrap` method
- Update column assertions for new positions:
  - Column H (8) is now block_vertical_segments (was G=7)
  - Column I (9) is now block_horizontal_segments (was H=8)
```python
def test_format_all_blocks_segment_columns_text_wrap(self) -> None:
    """Test that segment columns (H and I) have text wrapping with top alignment."""
    # ... create test data with 31 columns ...

    _format_all_blocks_sheet(wb)

    # Column H (8 = vertical_segments) should have wrap_text with top vertical alignment
    h_cell = ws.cell(row=2, column=8)
    assert h_cell.alignment.wrap_text is True
    assert h_cell.alignment.vertical == "top"

    # Column I (9 = horizontal_segments) should have wrap_text with top vertical alignment
    i_cell = ws.cell(row=2, column=9)
    assert i_cell.alignment.wrap_text is True
    assert i_cell.alignment.vertical == "top"
```

### 13. Add new test for attribute_data text wrapping
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Add a new test method to verify text wrapping on `block_attribute_data` column:
```python
def test_format_all_blocks_attribute_data_text_wrap(self) -> None:
    """Test that attribute_data column (AE) has text wrapping for multiline content."""
    wb, ws = self._create_test_workbook_with_headers()

    # Add a row with multiline attribute data
    ws.append(self._create_test_data_row(
        attribute_count=3,
        attribute_data="DEPT:30\nPROD1:Garage\nPROD2:Doors",
    ))

    _format_all_blocks_sheet(wb)

    # Column AE (31 = attribute_data) should have wrap_text with top vertical alignment
    ae_cell = ws.cell(row=2, column=31)
    assert ae_cell.alignment.wrap_text is True
    assert ae_cell.alignment.vertical == "top"
```

### 14. Add new test for layer_names text wrapping at position B
- Open `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Add a new test method to verify text wrapping on `block_layer_names` at new position B:
```python
def test_format_all_blocks_layer_names_text_wrap(self) -> None:
    """Test that layer_names column (B) has text wrapping at new position."""
    wb, ws = self._create_test_workbook_with_headers()

    ws.append(self._create_test_data_row(
        layer_names="Layer1, Layer2, Layer3, Layer4",
    ))

    _format_all_blocks_sheet(wb)

    # Column B (2 = layer_names) should have wrap_text with top vertical alignment
    b_cell = ws.cell(row=2, column=2)
    assert b_cell.alignment.wrap_text is True
    assert b_cell.alignment.vertical == "top"
```

### 15. Run all formatting tests
- Run `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v`
- Fix any failing tests
- Ensure all tests pass

### 16. Run full validation
- Run `uv run mypy app/` - Full type checking - must pass with 0 errors
- Run `uv run pytest app/tests/core/excel_formatting/ -v` - Run all formatting tests
- Run `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- Run `uv run ruff check app/` - Run linter - must pass with 0 errors
- Run `uv run ruff format app/ --check` - Verify code formatting - must pass

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/core/excel_formatting.py` - Type check the formatting module
- `uv run mypy app/` - Full type checking - must pass with 0 errors
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run excel_writer tests (integration)
- `uv run pytest app/tests/ -v` - Run full test suite - must pass all 1127+ tests
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The scale columns (block_scale_x and block_scale_y) have NOT moved from their positions at AB (28) and AC (29). The new columns are added AFTER them at AD (30) and AE (31).
- The text wrapping for `block_attribute_data` is important because Unit 2 formats attribute data as newline-separated "TAG:VALUE" pairs (e.g., "DEPT:30\nPROD1:Garage\nPROD2:Doors").
- Column B now contains `block_layer_names` which was previously at position 22 (column V). This column contains comma-separated layer names and benefits from text wrapping.
- The helper method `_create_test_data_row` simplifies test maintenance by providing default values for all 31 columns with only the relevant fields needing override.
- Unit 2 confirmed all 1127 tests are passing before this unit begins.
- The column width for `block_attribute_data` is set to 60 characters to accommodate the TAG:VALUE format with reasonable visibility without scrolling.
