# Chore: Unit 2 - Reorder All Blocks Sheet Columns (Test Updates)

## Chore Description
This is Unit 2 of the "Reorder All Blocks Sheet Columns" chore. The core implementation (excel_writer.py and excel_formatting.py) was completed in Unit 1 (commit `cd43fbb`). This unit focuses on updating the test files to match the new column order.

The new column order places trim/content zone fields (columns C-O) before metadata fields (columns P-AC):
- Columns A-B: Identity (raw_name, resolved_name)
- Columns C-F: Trim values (left, right, top, bottom)
- Columns G-H: Segments (vertical, horizontal)
- Columns I-J: Native dimensions (width, height)
- Columns K-M: Content zone (detected, width, height)
- Columns N-O: Polygon counts (total, filtered)
- Columns P-R: Block metadata (status, is_nested, parent_names)
- Columns S-T: Counts (entity, insertion)
- Columns U-V: Layer aggregation (count, names)
- Columns W-AA: Rotation counts (0, 90, 180, 270, other)
- Columns AB-AC: Scale data (x, y)

Key column position changes:
- Scale columns moved from O/P (15/16) to AB/AC (28/29)
- Segment columns moved from S/T (19/20) to G/H (7/8)

## Relevant Files
Use these files to resolve the chore:

- **`app/tests/core/excel_writer/test_excel_writer_all_blocks.py`** - Contains `TestAllBlocksSheet` class with `test_all_blocks_sheet_column_names` that validates the expected column order. The `expected_columns` list needs to be reordered to match the new column layout.

- **`app/tests/core/excel_formatting/test_formatting_all_blocks.py`** - Contains `TestAllBlocksFormatting` class with:
  - `_create_test_workbook_with_headers()` helper that creates headers in old order (needs reordering)
  - Multiple test methods with `ws.append()` calls adding 29-value data rows in old order (all need reordering)
  - `test_format_all_blocks_column_widths` with assertions for old column positions (needs updating)
  - `test_format_all_blocks_segment_columns_right_aligned` referencing columns 19/20 (needs to reference 7/8)

- **`app/core/excel_formatting.py`** - Reference file (already updated in Unit 1) - shows the new column widths and positions

- **`app/core/excel_writer.py`** - Reference file (already updated in Unit 1) - shows the new column order in DataFrame construction

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `test_all_blocks_sheet_column_names` Expected Columns

In `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`, update the `expected_columns` list in the `test_all_blocks_sheet_column_names` test method to match the new column order:

```python
expected_columns = [
    format_header(EXCEL_COLUMN_BLOCK_RAW_NAME),
    format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME),
    format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT),
    format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT),
    format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP),
    format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM),
    format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS),
    format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS),
    format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH),
    format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT),
    format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED),
    format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH),
    format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT),
    format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT),
    format_header(EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT),
    format_header(EXCEL_COLUMN_BLOCK_INSERTION_STATUS),
    format_header(EXCEL_COLUMN_BLOCK_IS_NESTED),
    format_header(EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES),
    format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT),
    format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT),
    format_header(EXCEL_COLUMN_BLOCK_LAYER_COUNT),
    format_header(EXCEL_COLUMN_BLOCK_LAYER_NAMES),
    format_header(EXCEL_COLUMN_BLOCK_ROTATION_0),
    format_header(EXCEL_COLUMN_BLOCK_ROTATION_90),
    format_header(EXCEL_COLUMN_BLOCK_ROTATION_180),
    format_header(EXCEL_COLUMN_BLOCK_ROTATION_270),
    format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER),
    format_header(EXCEL_COLUMN_BLOCK_SCALE_X),
    format_header(EXCEL_COLUMN_BLOCK_SCALE_Y),
]
```

### Step 2: Update `_create_test_workbook_with_headers()` Headers List

In `app/tests/core/excel_formatting/test_formatting_all_blocks.py`, update the `headers` list in `_create_test_workbook_with_headers()` method to new column order:

```python
headers = [
    "block_raw_name",
    "block_resolved_name",
    "block_suggested_trim_left",
    "block_suggested_trim_right",
    "block_suggested_trim_top",
    "block_suggested_trim_bottom",
    "block_vertical_segments",
    "block_horizontal_segments",
    "block_native_width",
    "block_native_height",
    "block_content_zone_detected",
    "block_content_zone_width",
    "block_content_zone_height",
    "block_polygon_count",
    "block_filtered_polygon_count",
    "block_insertion_status",
    "block_is_nested",
    "block_nested_parent_names",
    "block_entity_count",
    "block_insertion_count",
    "block_layer_count",
    "block_layer_names",
    "block_rotation_0",
    "block_rotation_90",
    "block_rotation_180",
    "block_rotation_270",
    "block_rotation_other",
    "block_scale_x",
    "block_scale_y",
]
```

### Step 3: Update All `ws.append()` Data Row Calls

In `app/tests/core/excel_formatting/test_formatting_all_blocks.py`, update ALL `ws.append()` calls in test methods to match new 29-column order. The new value order is:

```python
ws.append(
    [
        # A: block_raw_name
        # B: block_resolved_name
        # C: block_suggested_trim_left
        # D: block_suggested_trim_right
        # E: block_suggested_trim_top
        # F: block_suggested_trim_bottom
        # G: block_vertical_segments
        # H: block_horizontal_segments
        # I: block_native_width
        # J: block_native_height
        # K: block_content_zone_detected
        # L: block_content_zone_width
        # M: block_content_zone_height
        # N: block_polygon_count
        # O: block_filtered_polygon_count
        # P: block_insertion_status
        # Q: block_is_nested
        # R: block_nested_parent_names
        # S: block_entity_count
        # T: block_insertion_count
        # U: block_layer_count
        # V: block_layer_names
        # W: block_rotation_0
        # X: block_rotation_90
        # Y: block_rotation_180
        # Z: block_rotation_270
        # AA: block_rotation_other
        # AB: block_scale_x (was column O/15)
        # AC: block_scale_y (was column P/16)
    ]
)
```

The following test methods contain `ws.append()` calls that need updating:
1. `test_format_all_blocks_autofilter` - 1 data row
2. `test_format_all_blocks_red_highlighting_varies_negative` - 1 data row with "VARIES (-)" in x_scale
3. `test_format_all_blocks_orange_highlighting_negative_number` - 1 data row with -1.0 in y_scale
4. `test_format_all_blocks_yellow_highlighting_varies` - 1 data row with "VARIES" in x_scale
5. `test_format_all_blocks_no_highlighting_positive_scales` - 1 data row with positive scales
6. `test_format_all_blocks_entire_row_highlighted` - 1 data row with "VARIES (-)"
7. `test_format_all_blocks_segment_columns_right_aligned` - 1 data row
8. `test_format_all_blocks_highlighting_priority` - 1 data row with "VARIES (-)" and "VARIES"
9. `test_format_all_blocks_y_scale_varies_negative` - 1 data row with "VARIES (-)" in y_scale
10. `test_format_all_blocks_negative_x_scale` - 1 data row with -1.0 in x_scale

For each test, remap values from old order to new order:

**Old column positions -> New column positions:**
| Old Pos | Old Field | New Pos | New Field |
|---------|-----------|---------|-----------|
| 1 (A) | raw_name | 1 (A) | raw_name |
| 2 (B) | resolved_name | 2 (B) | resolved_name |
| 3 (C) | insertion_status | 16 (P) | insertion_status |
| 4 (D) | is_nested | 17 (Q) | is_nested |
| 5 (E) | parent_names | 18 (R) | parent_names |
| 6 (F) | entity_count | 19 (S) | entity_count |
| 7 (G) | insertion_count | 20 (T) | insertion_count |
| 8 (H) | layer_count | 21 (U) | layer_count |
| 9 (I) | layer_names | 22 (V) | layer_names |
| 10 (J) | rotation_0 | 23 (W) | rotation_0 |
| 11 (K) | rotation_90 | 24 (X) | rotation_90 |
| 12 (L) | rotation_180 | 25 (Y) | rotation_180 |
| 13 (M) | rotation_270 | 26 (Z) | rotation_270 |
| 14 (N) | rotation_other | 27 (AA) | rotation_other |
| 15 (O) | scale_x | 28 (AB) | scale_x |
| 16 (P) | scale_y | 29 (AC) | scale_y |
| 17 (Q) | native_width | 9 (I) | native_width |
| 18 (R) | native_height | 10 (J) | native_height |
| 19 (S) | vertical_segments | 7 (G) | vertical_segments |
| 20 (T) | horizontal_segments | 8 (H) | horizontal_segments |
| 21 (U) | trim_left | 3 (C) | trim_left |
| 22 (V) | trim_right | 4 (D) | trim_right |
| 23 (W) | trim_top | 5 (E) | trim_top |
| 24 (X) | trim_bottom | 6 (F) | trim_bottom |
| 25 (Y) | content_zone_detected | 11 (K) | content_zone_detected |
| 26 (Z) | content_zone_width | 12 (L) | content_zone_width |
| 27 (AA) | content_zone_height | 13 (M) | content_zone_height |
| 28 (AB) | polygon_count | 14 (N) | polygon_count |
| 29 (AC) | filtered_polygon_count | 15 (O) | filtered_polygon_count |

Example transformation for a typical data row:

**Old order (29 values):**
```python
["VALVE", "VALVE", "Inserted", False, "", 8, 10, 2, "Layer1, Layer2", 5, 2, 0, 0, 0, 1.0, 1.0, 100.0, 50.0, "10, 80, 10", "5, 40, 5", 10.0, 10.0, 5.0, 5.0, "TRUE", 80.0, 40.0, 2, 2]
```

**New order (29 values):**
```python
["VALVE", "VALVE", 10.0, 10.0, 5.0, 5.0, "10, 80, 10", "5, 40, 5", 100.0, 50.0, "TRUE", 80.0, 40.0, 2, 2, "Inserted", False, "", 8, 10, 2, "Layer1, Layer2", 5, 2, 0, 0, 0, 1.0, 1.0]
```

### Step 4: Update Column Width Test Assertions

In `test_format_all_blocks_column_widths`, update the column width assertions to match new positions:

**Old assertions:**
```python
assert ws.column_dimensions["A"].width == 30  # block_raw_name
assert ws.column_dimensions["B"].width == 30  # block_resolved_name
assert ws.column_dimensions["O"].width == 15  # block_scale_x
assert ws.column_dimensions["P"].width == 15  # block_scale_y
assert ws.column_dimensions["S"].width == 40  # block_vertical_segments
assert ws.column_dimensions["T"].width == 40  # block_horizontal_segments
assert ws.column_dimensions["AC"].width == 20  # block_filtered_polygon_count
```

**New assertions:**
```python
assert ws.column_dimensions["A"].width == 30  # block_raw_name (unchanged)
assert ws.column_dimensions["B"].width == 30  # block_resolved_name (unchanged)
assert ws.column_dimensions["AB"].width == 15  # block_scale_x (was O)
assert ws.column_dimensions["AC"].width == 15  # block_scale_y (was P)
assert ws.column_dimensions["G"].width == 40  # block_vertical_segments (was S)
assert ws.column_dimensions["H"].width == 40  # block_horizontal_segments (was T)
assert ws.column_dimensions["O"].width == 20  # block_filtered_polygon_count (was AC)
```

### Step 5: Update Segment Column Alignment Test

In `test_format_all_blocks_segment_columns_right_aligned`, update the column references:

**Old test:**
```python
# Column S (19 = vertical_segments) should be right-aligned
assert ws.cell(row=2, column=19).alignment.horizontal == "right"
# Column T (20 = horizontal_segments) should be right-aligned
assert ws.cell(row=2, column=20).alignment.horizontal == "right"
```

**New test:**
```python
# Column G (7 = vertical_segments) should be right-aligned
assert ws.cell(row=2, column=7).alignment.horizontal == "right"
# Column H (8 = horizontal_segments) should be right-aligned
assert ws.cell(row=2, column=8).alignment.horizontal == "right"
```

### Step 6: Run All Validation Commands

Execute all validation commands to ensure test updates are complete and pass.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks Excel writer tests to verify column order test passes
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests to verify highlighting and alignment tests pass
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all Excel writer tests to ensure no regressions
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all Excel formatting tests to ensure no regressions
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions across the codebase
- `uv run mypy app/` - Run type checking to ensure no type errors

## Notes
- The column count remains 29 - only the order changes
- All 10 test methods with `ws.append()` calls must be updated to match the new column order
- The scale highlighting tests implicitly test the correct column positions because the formatting code reads from columns AB/AC (28/29)
- The segment alignment test explicitly references column numbers and must be updated
- The column width assertions verify the implementation matches the expected widths at specific column letters
- Implementation learnings from Unit 1:
  - Commit `cd43fbb` updated excel_writer.py (3 places) and excel_formatting.py (3 places)
  - Scale highlighting now reads from columns AB/AC (28/29) instead of O/P (15/16)
  - Segment alignment now applies to columns G/H (7/8) instead of S/T (19/20)
