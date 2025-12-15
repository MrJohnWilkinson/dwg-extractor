# Chore: All Blocks Sheet Text Wrapping and Column Width Optimization

## Chore Description
Improve the readability of the "All Blocks" Excel sheet by:
1. Enabling text wrapping for segment columns (G, H) - these contain 500+ character comma-separated values that are currently invisible
2. Enabling text wrapping for name columns (A, B) - long block identifiers are truncated
3. Enabling text wrapping for layer/parent columns (R, V) - variable length lists
4. Reducing widths on rotation columns (W-AA) - single digit values don't need 12-15 width
5. Adding "..." truncation for segment columns if they exceed 200 characters to prevent extreme row heights

The current implementation uses fixed widths without data row wrapping, causing horizontal scroll issues and truncated data in Excel. The analysis in `ai_output/088-all-blocks-column-formatting-analysis.md` shows segment columns can contain 509+ characters with only ~30 visible.

## Relevant Files
Use these files to resolve the chore:

- `app/core/excel_formatting.py` - Contains `_format_all_blocks_sheet()` function (lines 560-713) that applies column widths, text wrapping, and alignment. This is where text wrapping and column width changes will be made.
- `app/core/excel_writer.py` - Contains segment string generation logic at lines 675-684 and 1148-1162. This is where the truncation with "..." suffix needs to be added.
- `app/tests/core/excel_formatting/test_formatting_all_blocks.py` - Contains tests for `_format_all_blocks_sheet()`. Tests must be updated to verify new text wrapping and column widths.
- `app/tests/core/excel_writer/test_excel_writer_all_blocks.py` - Contains tests for All Blocks sheet generation. Tests needed for truncation behavior.
- `ai_output/088-all-blocks-column-formatting-analysis.md` - Reference analysis document with recommended column widths and wrap settings.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Truncation Helper Function to excel_writer.py

Add a helper function to truncate long segment strings:

- Location: `app/core/excel_writer.py` near the top of the file (after imports, before class definitions)
- Add a module-level constant `SEGMENT_MAX_DISPLAY_LENGTH = 200`
- Add helper function `_truncate_segment_string(segment_str: str, max_length: int = SEGMENT_MAX_DISPLAY_LENGTH) -> str`
  - If `len(segment_str) <= max_length`: return unchanged
  - Otherwise: return `segment_str[:max_length - 3] + "..."`

### Step 2: Apply Truncation to Block Geometry Analysis Sheet

Modify the segment string generation in `_create_block_geometry_analysis_sheet()`:

- Location: `app/core/excel_writer.py` lines 675-684
- After creating `vertical_segments_str` and `horizontal_segments_str`, apply truncation:
  ```python
  vertical_segments_str = _truncate_segment_string(vertical_segments_str)
  horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)
  ```

### Step 3: Apply Truncation to All Blocks Sheet

Modify the segment string generation in `_create_all_blocks_sheet()`:

- Location: `app/core/excel_writer.py` lines 1148-1162
- After creating `vertical_segments_str` and `horizontal_segments_str`, apply truncation:
  ```python
  vertical_segments_str = _truncate_segment_string(vertical_segments_str)
  horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)
  ```

### Step 4: Update Column Widths in _format_all_blocks_sheet()

Modify column width settings in `_format_all_blocks_sheet()`:

- Location: `app/core/excel_formatting.py` lines 591-620
- Update widths according to analysis recommendations:
  ```python
  # Identity columns (with wrapping)
  ws.column_dimensions["A"].width = 35   # block_raw_name (was 30)
  ws.column_dimensions["B"].width = 35   # block_resolved_name (was 30)

  # Trim columns (narrower)
  ws.column_dimensions["C"].width = 12   # block_suggested_trim_left (was 15)
  ws.column_dimensions["D"].width = 12   # block_suggested_trim_right (was 15)
  ws.column_dimensions["E"].width = 12   # block_suggested_trim_top (was 15)
  ws.column_dimensions["F"].width = 12   # block_suggested_trim_bottom (was 15)

  # Segment columns (with wrapping)
  ws.column_dimensions["G"].width = 50   # block_vertical_segments (was 40)
  ws.column_dimensions["H"].width = 50   # block_horizontal_segments (was 40)

  # Dimension columns (narrower)
  ws.column_dimensions["I"].width = 15   # block_native_width (was 20)
  ws.column_dimensions["J"].width = 15   # block_native_height (was 20)

  # Content zone columns
  ws.column_dimensions["K"].width = 18   # block_content_zone_detected (was 20)
  ws.column_dimensions["L"].width = 18   # block_content_zone_width (was 20)
  ws.column_dimensions["M"].width = 18   # block_content_zone_height (was 20)

  # Polygon count columns
  ws.column_dimensions["N"].width = 15   # block_polygon_count (was 18)
  ws.column_dimensions["O"].width = 18   # block_filtered_polygon_count (was 20)

  # Metadata columns
  ws.column_dimensions["P"].width = 18   # block_insertion_status (was 20)
  ws.column_dimensions["Q"].width = 12   # block_is_nested (was 15)
  ws.column_dimensions["R"].width = 35   # block_nested_parent_names (was 40)

  # Count columns
  ws.column_dimensions["S"].width = 15   # block_entity_count (was 20)
  ws.column_dimensions["T"].width = 18   # block_insertion_count (was 25)
  ws.column_dimensions["U"].width = 12   # block_layer_count (was 18)
  ws.column_dimensions["V"].width = 35   # block_layer_names (was 40)

  # Rotation columns (much narrower - single digit values)
  ws.column_dimensions["W"].width = 10   # block_rotation_0 (was 12)
  ws.column_dimensions["X"].width = 10   # block_rotation_90 (was 12)
  ws.column_dimensions["Y"].width = 10   # block_rotation_180 (was 12)
  ws.column_dimensions["Z"].width = 10   # block_rotation_270 (was 12)
  ws.column_dimensions["AA"].width = 12  # block_rotation_other (was 15)

  # Scale columns
  ws.column_dimensions["AB"].width = 12  # block_scale_x (was 15)
  ws.column_dimensions["AC"].width = 12  # block_scale_y (was 15)
  ```

### Step 5: Add Text Wrapping for Data Rows

Add text wrapping logic in `_format_all_blocks_sheet()` after the header wrapping code:

- Location: `app/core/excel_formatting.py` after line 625 (after header alignment loop)
- Add data row text wrapping for columns A, B, G, H, R, V:
  ```python
  # Apply text wrapping to data rows for long-content columns
  # Columns: A=1, B=2, G=7, H=8, R=18, V=22
  wrap_columns = [1, 2, 7, 8, 18, 22]
  data_wrap_alignment = Alignment(wrap_text=True, vertical="top")

  for row_idx in range(2, ws.max_row + 1):
      for col_idx in wrap_columns:
          cell = ws.cell(row=row_idx, column=col_idx)
          cell.alignment = data_wrap_alignment
  ```

### Step 6: Update Segment Column Alignment

Change segment columns from right-aligned to left-aligned with wrapping:

- Location: `app/core/excel_formatting.py` lines 701-707
- Remove the existing right-alignment code for segment columns G and H since they will now have wrap_text alignment from Step 5
- The segment columns will inherit left alignment (default) with wrap_text from the data wrapping step

### Step 7: Update Formatting Tests for New Column Widths

Update tests in `app/tests/core/excel_formatting/test_formatting_all_blocks.py`:

- Modify `test_format_all_blocks_column_widths()`:
  - Update assertions for new width values:
    - `A`: 30 → 35
    - `B`: 30 → 35
    - `G`: 40 → 50
    - `H`: 40 → 50
    - `AB`: 15 → 12
    - `AC`: 15 → 12
    - `O`: 20 → 18

### Step 8: Add Text Wrapping Tests

Add new tests in `app/tests/core/excel_formatting/test_formatting_all_blocks.py`:

- Add `test_format_all_blocks_data_rows_text_wrap()`:
  - Create workbook with headers and one data row
  - Call `_format_all_blocks_sheet(wb)`
  - Assert that cells in columns A, B, G, H, R, V (row 2) have `alignment.wrap_text == True`
  - Assert that cells in columns A, B, G, H, R, V (row 2) have `alignment.vertical == "top"`

### Step 9: Update Segment Alignment Test

Update `test_format_all_blocks_segment_columns_right_aligned()`:

- This test needs to be renamed and updated since segment columns will no longer be right-aligned
- Rename to `test_format_all_blocks_segment_columns_text_wrap()`
- Change assertions from `alignment.horizontal == "right"` to `alignment.wrap_text == True`

### Step 10: Add Truncation Tests

Add tests in `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`:

- Add `test_truncate_segment_string_short()`:
  - Test that strings under 200 chars are returned unchanged
- Add `test_truncate_segment_string_exact_limit()`:
  - Test that strings exactly 200 chars are returned unchanged
- Add `test_truncate_segment_string_over_limit()`:
  - Test that strings over 200 chars are truncated to 197 chars + "..."

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests to validate text wrapping and column width changes
- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks writer tests to validate truncation logic
- `uv run pytest app/tests/ -v` - Run complete test suite to ensure no regressions
- `uv run mypy app/` - Type check to ensure no type errors introduced
- `uv run ruff check app/` - Lint check for code quality

## Notes
- The column widths are based on the analysis in `ai_output/088-all-blocks-column-formatting-analysis.md` which examined actual data ranges across real DXF files
- The truncation limit of 200 characters was chosen to balance data visibility with row height management
- Text wrapping combined with truncation ensures users can see meaningful segment data while preventing extremely tall rows
- The segment columns (G, H) change from right-aligned to left-aligned with wrap because wrapped text is more readable left-aligned
- This change affects both the Block Geometry Analysis sheet and All Blocks sheet since both display segment data
