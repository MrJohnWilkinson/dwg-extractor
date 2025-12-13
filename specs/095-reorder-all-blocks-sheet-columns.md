# Chore: Reorder All Blocks Sheet Columns

## Chore Description
Reorder the columns in the "All Blocks" Excel sheet so that content zone and geometry-related fields appear before block metadata fields. The current order groups identity fields first, then layer/rotation/scale data, then geometry/content zone. The new order prioritizes content zone trimming data immediately after the block names for easier analysis.

**Current column order (29 columns):**
1. block_raw_name
2. block_resolved_name
3. block_insertion_status
4. block_is_nested
5. block_nested_parent_names
6. block_entity_count
7. block_insertion_count
8. block_layer_count
9. block_layer_names
10. block_rotation_0...rotation_other (5 cols)
15. block_scale_x
16. block_scale_y
17. block_native_width
18. block_native_height
19. block_vertical_segments
20. block_horizontal_segments
21-29. content zone fields

**Requested new column order (29 columns):**
1. block_raw_name
2. block_resolved_name
3. block_suggested_trim_left
4. block_suggested_trim_right
5. block_suggested_trim_top
6. block_suggested_trim_bottom
7. block_vertical_segments
8. block_horizontal_segments
9. block_native_width
10. block_native_height
11. block_content_zone_detected
12. block_content_zone_width
13. block_content_zone_height
14. block_polygon_count
15. block_filtered_polygon_count
16. block_insertion_status
17. block_is_nested
18. block_nested_parent_names
19. block_entity_count
20. block_insertion_count
21. block_layer_count
22. block_layer_names
23. block_rotation_0
24. block_rotation_90
25. block_rotation_180
26. block_rotation_270
27. block_rotation_other
28. block_scale_x
29. block_scale_y

## Relevant Files
Use these files to resolve the chore:

- **`app/core/excel_writer.py`** - Contains `_create_all_blocks_sheet()` function that builds the DataFrame rows with column order. Has 3 places where column order is defined: main row construction (lines 1189-1220), empty data DataFrame (lines 1027-1058), and system-blocks-only DataFrame (lines 1226-1257).

- **`app/core/excel_formatting.py`** - Contains `_format_all_blocks_sheet()` function that sets column widths and applies formatting. Column widths are mapped by Excel letter (A-AC). Scale highlighting uses columns O/P (old) which will become AB/AC (new). Segment right-alignment uses columns S/T (old) which will become G/H (new).

- **`app/tests/core/excel_writer/test_excel_writer_all_blocks.py`** - Contains test `test_all_blocks_sheet_column_names` that verifies exact column order. Must update expected_columns list.

- **`app/tests/core/excel_formatting/test_formatting_all_blocks.py`** - Contains `_create_test_workbook_with_headers()` helper and multiple tests that reference column positions. Header list and all column index references must be updated.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_create_all_blocks_sheet()` in excel_writer.py

- Update the `rows.append()` dictionary in the main data loop (lines 1189-1220) to use the new column order
- Update the empty DataFrame column list for empty `all_block_definitions` (lines 1027-1058) to match new order
- Update the empty DataFrame column list for system-blocks-only case (lines 1226-1257) to match new order
- Ensure all three column order definitions are identical

New column order for all three places:
```python
EXCEL_COLUMN_BLOCK_RAW_NAME,           # A
EXCEL_COLUMN_BLOCK_RESOLVED_NAME,      # B
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,     # C
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,    # D
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,      # E
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,   # F
EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,       # G
EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,     # H
EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,            # I
EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,           # J
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,   # K
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,      # L
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,     # M
EXCEL_COLUMN_BLOCK_POLYGON_COUNT,           # N
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,  # O
EXCEL_COLUMN_BLOCK_INSERTION_STATUS,        # P
EXCEL_COLUMN_BLOCK_IS_NESTED,               # Q
EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,     # R
EXCEL_COLUMN_BLOCK_ENTITY_COUNT,            # S
EXCEL_COLUMN_BLOCK_INSERTION_COUNT,         # T
EXCEL_COLUMN_BLOCK_LAYER_COUNT,             # U
EXCEL_COLUMN_BLOCK_LAYER_NAMES,             # V
EXCEL_COLUMN_BLOCK_ROTATION_0,              # W
EXCEL_COLUMN_BLOCK_ROTATION_90,             # X
EXCEL_COLUMN_BLOCK_ROTATION_180,            # Y
EXCEL_COLUMN_BLOCK_ROTATION_270,            # Z
EXCEL_COLUMN_BLOCK_ROTATION_OTHER,          # AA
EXCEL_COLUMN_BLOCK_SCALE_X,                 # AB
EXCEL_COLUMN_BLOCK_SCALE_Y,                 # AC
```

### Step 2: Update `_format_all_blocks_sheet()` in excel_formatting.py

- Update all column width assignments to match new column positions:
  ```python
  ws.column_dimensions["A"].width = 30   # block_raw_name
  ws.column_dimensions["B"].width = 30   # block_resolved_name
  ws.column_dimensions["C"].width = 15   # block_suggested_trim_left
  ws.column_dimensions["D"].width = 15   # block_suggested_trim_right
  ws.column_dimensions["E"].width = 15   # block_suggested_trim_top
  ws.column_dimensions["F"].width = 15   # block_suggested_trim_bottom
  ws.column_dimensions["G"].width = 40   # block_vertical_segments
  ws.column_dimensions["H"].width = 40   # block_horizontal_segments
  ws.column_dimensions["I"].width = 20   # block_native_width
  ws.column_dimensions["J"].width = 20   # block_native_height
  ws.column_dimensions["K"].width = 20   # block_content_zone_detected
  ws.column_dimensions["L"].width = 20   # block_content_zone_width
  ws.column_dimensions["M"].width = 20   # block_content_zone_height
  ws.column_dimensions["N"].width = 18   # block_polygon_count
  ws.column_dimensions["O"].width = 20   # block_filtered_polygon_count
  ws.column_dimensions["P"].width = 20   # block_insertion_status
  ws.column_dimensions["Q"].width = 15   # block_is_nested
  ws.column_dimensions["R"].width = 40   # block_nested_parent_names
  ws.column_dimensions["S"].width = 20   # block_entity_count
  ws.column_dimensions["T"].width = 25   # block_insertion_count
  ws.column_dimensions["U"].width = 18   # block_layer_count
  ws.column_dimensions["V"].width = 40   # block_layer_names
  ws.column_dimensions["W"].width = 12   # block_rotation_0
  ws.column_dimensions["X"].width = 12   # block_rotation_90
  ws.column_dimensions["Y"].width = 12   # block_rotation_180
  ws.column_dimensions["Z"].width = 12   # block_rotation_270
  ws.column_dimensions["AA"].width = 15  # block_rotation_other
  ws.column_dimensions["AB"].width = 15  # block_scale_x
  ws.column_dimensions["AC"].width = 15  # block_scale_y
  ```

- Update scale highlighting logic:
  - Old: x_scale was column O (15), y_scale was column P (16)
  - New: x_scale is column AB (28), y_scale is column AC (29)
  - Find where `ws.cell(row=row_num, column=15)` and `column=16` are used for reading scale values
  - Change to `column=28` and `column=29`

- Update segment column right-alignment:
  - Old: vertical_segments was column S (19), horizontal_segments was column T (20)
  - New: vertical_segments is column G (7), horizontal_segments is column H (8)
  - Find where alignment is set for columns 19 and 20
  - Change to columns 7 and 8

### Step 3: Update test_excel_writer_all_blocks.py

- Update `test_all_blocks_sheet_column_names` expected_columns list to match new order:
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

### Step 4: Update test_formatting_all_blocks.py

- Update `_create_test_workbook_with_headers()` headers list to new order:
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

- Update all `ws.append()` calls in test methods to match new column order. Each test that appends data rows needs the values reordered:
  - Values 1-2: block_raw_name, block_resolved_name (unchanged position)
  - Values 3-6: suggested_trim_left/right/top/bottom (moved from positions 21-24)
  - Values 7-8: vertical_segments, horizontal_segments (moved from positions 19-20)
  - Values 9-10: native_width, native_height (moved from positions 17-18)
  - Values 11-15: content_zone fields (moved from positions 25-29)
  - Values 16-22: insertion_status through layer_names (moved from positions 3-9)
  - Values 23-27: rotation_0 through rotation_other (moved from positions 10-14)
  - Values 28-29: scale_x, scale_y (moved from positions 15-16)

- Update column width test assertions:
  - `test_format_all_blocks_column_widths`: Update column letters and expected widths
  - Old: S (19) for vertical_segments, T (20) for horizontal_segments
  - New: G (7) for vertical_segments, H (8) for horizontal_segments
  - Old: O (15) for scale_x, P (16) for scale_y
  - New: AB (28) for scale_x, AC (29) for scale_y

- Update scale highlighting tests:
  - Tests check `ws.cell(row=2, column=X)` for scale values
  - Old: column 15 for x_scale, column 16 for y_scale
  - New: column 28 for x_scale, column 29 for y_scale

- Update segment alignment test:
  - `test_format_all_blocks_segment_columns_right_aligned`: Update column references
  - Old: column 19 and column 20
  - New: column 7 and column 8

### Step 5: Run Validation Commands

- Run all tests to ensure the column reordering is complete and correct
- Verify no test failures related to column ordering or formatting

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks sheet Excel writer tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks sheet formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all Excel writer tests to ensure no side effects
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all formatting tests to ensure no side effects
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors introduced

## Notes
- The column count remains 29 - only the order changes
- The formatting logic for scale highlighting and segment alignment must be updated to reference new column positions
- All three empty DataFrame definitions in `_create_all_blocks_sheet()` must be updated to maintain consistency
- Tests that append data rows will need significant reordering of values - be careful to maintain the correct mapping between column names and values
