# Chore: Implement Truncation Helper and Formatting Changes for All Blocks Sheet

## Chore Description

Implement a truncation helper function for segment strings and update column formatting in the All Blocks sheet to optimize text wrapping and readability. This involves:

1. Adding a reusable truncation helper function to limit segment string length
2. Applying truncation to segment strings in both Block Geometry Analysis and All Blocks sheets
3. Updating column widths for better visual balance
4. Adding text wrapping with vertical top alignment for specific text-heavy columns
5. Removing existing right-alignment from segment columns (they will inherit left alignment with wrap_text)

This is Unit 1 of the All Blocks text wrap formatting optimization effort (Steps 1-6).

## Relevant Files

Use these files to resolve the chore:

- **`app/core/excel_writer.py`** - Contains segment string generation logic in `_create_block_geometry_analysis_sheet()` and `_create_all_blocks_sheet()`. This is where the truncation helper will be added and applied.
  - Lines 569-774: `_create_block_geometry_analysis_sheet()` function with segment string generation at lines 671-684
  - Lines 989-1285: `_create_all_blocks_sheet()` function with segment string generation at lines 1144-1156

- **`app/core/excel_formatting.py`** - Contains `_format_all_blocks_sheet()` function where column widths and alignment settings are configured.
  - Lines 560-713: `_format_all_blocks_sheet()` function with column widths at lines 591-620, header alignment at lines 622-625, and segment column right-alignment at lines 701-707

- **`app/tests/core/excel_formatting/test_formatting_all_blocks.py`** - Existing tests for All Blocks sheet formatting that may need updates for new text wrapping behavior.

## Step by Step Tasks

### Step 1: Add Truncation Helper Constant and Function to excel_writer.py

**Location:** `app/core/excel_writer.py` near the top of the file (after imports, around line 111, before `_ACI_NAMED_COLORS`)

- Add module-level constant:
  ```python
  # Maximum display length for segment strings in Excel cells
  SEGMENT_MAX_DISPLAY_LENGTH = 200
  ```

- Add helper function immediately after the constant:
  ```python
  def _truncate_segment_string(segment_str: str, max_length: int = SEGMENT_MAX_DISPLAY_LENGTH) -> str:
      """
      Truncate a segment string to a maximum length for Excel display.

      When segment lists are very long, they can cause Excel cells to become
      unwieldy. This function truncates the string and adds an ellipsis to
      indicate truncation occurred.

      Args:
          segment_str: The comma-separated segment string to truncate
          max_length: Maximum allowed length (default: SEGMENT_MAX_DISPLAY_LENGTH)

      Returns:
          Original string if within max_length, otherwise truncated with "..."

      Examples:
          >>> _truncate_segment_string("10, 20, 30", 200)
          '10, 20, 30'
          >>> _truncate_segment_string("a" * 250, 200)
          'aaaa...aaa...'  # 197 chars + "..."
      """
      if len(segment_str) <= max_length:
          return segment_str
      return segment_str[:max_length - 3] + "..."
  ```

### Step 2: Apply Truncation in _create_block_geometry_analysis_sheet()

**Location:** `app/core/excel_writer.py` in `_create_block_geometry_analysis_sheet()` function

- Find the segment string creation code around lines 675-684:
  ```python
  vertical_segments_str = (
      ", ".join(map(format_number, vertical_segments))
      if vertical_segments
      else ""
  )
  horizontal_segments_str = (
      ", ".join(map(format_number, horizontal_segments))
      if horizontal_segments
      else ""
  )
  ```

- Apply truncation after each string is created:
  ```python
  vertical_segments_str = (
      ", ".join(map(format_number, vertical_segments))
      if vertical_segments
      else ""
  )
  vertical_segments_str = _truncate_segment_string(vertical_segments_str)

  horizontal_segments_str = (
      ", ".join(map(format_number, horizontal_segments))
      if horizontal_segments
      else ""
  )
  horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)
  ```

### Step 3: Apply Truncation in _create_all_blocks_sheet()

**Location:** `app/core/excel_writer.py` in `_create_all_blocks_sheet()` function

- Find the segment string creation code around lines 1148-1156:
  ```python
  vertical_segments_str = (
      ", ".join(map(format_number, vertical_segments))
      if vertical_segments
      else ""
  )
  horizontal_segments_str = (
      ", ".join(map(format_number, horizontal_segments))
      if horizontal_segments
      else ""
  )
  ```

- Apply truncation after each string is created:
  ```python
  vertical_segments_str = (
      ", ".join(map(format_number, vertical_segments))
      if vertical_segments
      else ""
  )
  vertical_segments_str = _truncate_segment_string(vertical_segments_str)

  horizontal_segments_str = (
      ", ".join(map(format_number, horizontal_segments))
      if horizontal_segments
      else ""
  )
  horizontal_segments_str = _truncate_segment_string(horizontal_segments_str)
  ```

### Step 4: Update Column Widths in _format_all_blocks_sheet()

**Location:** `app/core/excel_formatting.py` in `_format_all_blocks_sheet()` function, lines 591-620

Replace the existing column width assignments with these new values:

```python
# Set column widths (29 columns: A-AC)
ws.column_dimensions["A"].width = 35   # block_raw_name
ws.column_dimensions["B"].width = 35   # block_resolved_name
ws.column_dimensions["C"].width = 12   # block_suggested_trim_left
ws.column_dimensions["D"].width = 12   # block_suggested_trim_right
ws.column_dimensions["E"].width = 12   # block_suggested_trim_top
ws.column_dimensions["F"].width = 12   # block_suggested_trim_bottom
ws.column_dimensions["G"].width = 50   # block_vertical_segments
ws.column_dimensions["H"].width = 50   # block_horizontal_segments
ws.column_dimensions["I"].width = 15   # block_native_width
ws.column_dimensions["J"].width = 15   # block_native_height
ws.column_dimensions["K"].width = 18   # block_content_zone_detected
ws.column_dimensions["L"].width = 18   # block_content_zone_width
ws.column_dimensions["M"].width = 18   # block_content_zone_height
ws.column_dimensions["N"].width = 15   # block_polygon_count
ws.column_dimensions["O"].width = 18   # block_filtered_polygon_count
ws.column_dimensions["P"].width = 18   # block_insertion_status
ws.column_dimensions["Q"].width = 12   # block_is_nested
ws.column_dimensions["R"].width = 35   # block_nested_parent_names
ws.column_dimensions["S"].width = 15   # block_entity_count
ws.column_dimensions["T"].width = 18   # block_insertion_count
ws.column_dimensions["U"].width = 12   # block_layer_count
ws.column_dimensions["V"].width = 35   # block_layer_names
ws.column_dimensions["W"].width = 10   # block_rotation_0
ws.column_dimensions["X"].width = 10   # block_rotation_90
ws.column_dimensions["Y"].width = 10   # block_rotation_180
ws.column_dimensions["Z"].width = 10   # block_rotation_270
ws.column_dimensions["AA"].width = 12  # block_rotation_other
ws.column_dimensions["AB"].width = 12  # block_scale_x
ws.column_dimensions["AC"].width = 12  # block_scale_y
```

**Width changes summary:**
- A, B: 30 -> 35 (block names)
- C-F: 15 -> 12 (trim values)
- G, H: 40 -> 50 (segment strings - more room for wrapped text)
- I, J: 20 -> 15 (native dimensions)
- K-M: 20 -> 18 (content zone)
- N: 18 -> 15 (polygon_count)
- O: 20 -> 18 (filtered_polygon_count)
- P: 20 -> 18 (insertion_status)
- Q: 15 -> 12 (is_nested)
- R: 40 -> 35 (parent_names)
- S: 20 -> 15 (entity_count)
- T: 25 -> 18 (insertion_count)
- U: 18 -> 12 (layer_count)
- V: 40 -> 35 (layer_names)
- W-Z: 12 -> 10 (rotation counts)
- AA: 15 -> 12 (rotation_other)
- AB, AC: 15 -> 12 (scale)

### Step 5: Add Text Wrapping for Data Rows

**Location:** `app/core/excel_formatting.py` in `_format_all_blocks_sheet()`, after the header alignment code (after line 625)

Add text wrapping for columns that contain potentially long text content:
- Column A (1) - block_raw_name
- Column B (2) - block_resolved_name
- Column G (7) - block_vertical_segments
- Column H (8) - block_horizontal_segments
- Column R (18) - block_nested_parent_names
- Column V (22) - block_layer_names

Insert the following code after the header alignment loop:

```python
# Apply text wrapping for data rows in columns with potentially long text
# Columns: A (raw_name), B (resolved_name), G (vert_segments), H (horiz_segments),
#          R (parent_names), V (layer_names)
wrap_columns = [1, 2, 7, 8, 18, 22]  # Column indices (1-based)
wrap_alignment = Alignment(wrap_text=True, vertical="top")
for row_idx in range(2, ws.max_row + 1):
    for col_idx in wrap_columns:
        ws.cell(row=row_idx, column=col_idx).alignment = wrap_alignment
```

### Step 6: Remove Segment Column Right-Alignment

**Location:** `app/core/excel_formatting.py` in `_format_all_blocks_sheet()`, lines 701-707

Remove the existing right-alignment code for segment columns G and H:

```python
# Apply right-alignment to segment columns (G=7 and H=8)
right_alignment = Alignment(horizontal="right")
for row_idx in range(2, ws.max_row + 1):
    # Column G (7) - block_vertical_segments
    ws.cell(row=row_idx, column=7).alignment = right_alignment
    # Column H (8) - block_horizontal_segments
    ws.cell(row=row_idx, column=8).alignment = right_alignment
```

This code block should be deleted entirely. The segment columns will now inherit the wrap_text alignment from Step 5, which uses left alignment (the default) with vertical top alignment.

**Note:** Also update the logger.info message at the end of the function to remove reference to "segment columns right-aligned" since they will no longer be right-aligned.

Change from:
```python
logger.info(
    f"All Blocks sheet formatted with {total_highlighted} rows highlighted "
    f"(red: {red_highlighted}, orange: {orange_highlighted}, yellow: {yellow_highlighted})"
)
```

To:
```python
logger.info(
    f"All Blocks sheet formatted with {total_highlighted} rows highlighted "
    f"(red: {red_highlighted}, orange: {orange_highlighted}, yellow: {yellow_highlighted}) "
    f"and text wrapping applied to name/segment columns"
)
```

### Step 7: Update Tests for Segment Column Alignment

**Location:** `app/tests/core/excel_formatting/test_formatting_all_blocks.py`

Update `test_format_all_blocks_segment_columns_right_aligned` to reflect the new behavior:

```python
def test_format_all_blocks_segment_columns_text_wrap(self) -> None:
    """Test that segment columns (G and H) have text wrapping with top alignment."""
    wb, ws = self._create_test_workbook_with_headers()

    ws.append(
        [
            "VALVE",  # A: raw_name
            "VALVE",  # B: resolved_name
            10.0,  # C: trim_left
            10.0,  # D: trim_right
            5.0,  # E: trim_top
            5.0,  # F: trim_bottom
            "10, 80, 10",  # G: vertical_segments
            "5, 40, 5",  # H: horizontal_segments
            100.0,  # I: native_width
            50.0,  # J: native_height
            "TRUE",  # K: content_zone_detected
            80.0,  # L: content_zone_width
            40.0,  # M: content_zone_height
            2,  # N: polygon_count
            2,  # O: filtered_polygon_count
            "Inserted",  # P: insertion_status
            False,  # Q: is_nested
            "",  # R: parent_names
            8,  # S: entity_count
            10,  # T: insertion_count
            2,  # U: layer_count
            "Layer1, Layer2",  # V: layer_names
            5,  # W: rotation_0
            2,  # X: rotation_90
            0,  # Y: rotation_180
            0,  # Z: rotation_270
            0,  # AA: rotation_other
            1.0,  # AB: scale_x
            1.0,  # AC: scale_y
        ]
    )

    _format_all_blocks_sheet(wb)

    # Column G (7 = vertical_segments) should have wrap_text with top vertical alignment
    g_cell = ws.cell(row=2, column=7)
    assert g_cell.alignment.wrap_text is True
    assert g_cell.alignment.vertical == "top"

    # Column H (8 = horizontal_segments) should have wrap_text with top vertical alignment
    h_cell = ws.cell(row=2, column=8)
    assert h_cell.alignment.wrap_text is True
    assert h_cell.alignment.vertical == "top"
```

### Step 8: Add Test for Truncation Helper Function

**Location:** `app/tests/core/excel_writer/test_excel_writer_core.py` (or create new test file if needed)

Add tests for the truncation helper:

```python
from core.excel_writer import _truncate_segment_string, SEGMENT_MAX_DISPLAY_LENGTH


class TestTruncateSegmentString:
    """Tests for _truncate_segment_string helper function."""

    def test_short_string_unchanged(self) -> None:
        """Test that strings under max length are returned unchanged."""
        result = _truncate_segment_string("10, 20, 30")
        assert result == "10, 20, 30"

    def test_exact_length_unchanged(self) -> None:
        """Test that strings exactly at max length are returned unchanged."""
        exact_string = "a" * SEGMENT_MAX_DISPLAY_LENGTH
        result = _truncate_segment_string(exact_string)
        assert result == exact_string
        assert len(result) == SEGMENT_MAX_DISPLAY_LENGTH

    def test_long_string_truncated(self) -> None:
        """Test that strings over max length are truncated with ellipsis."""
        long_string = "a" * 250
        result = _truncate_segment_string(long_string)
        assert len(result) == SEGMENT_MAX_DISPLAY_LENGTH
        assert result.endswith("...")
        assert result == "a" * 197 + "..."

    def test_empty_string(self) -> None:
        """Test that empty string is returned unchanged."""
        result = _truncate_segment_string("")
        assert result == ""

    def test_custom_max_length(self) -> None:
        """Test truncation with custom max length."""
        result = _truncate_segment_string("0123456789", max_length=8)
        assert result == "01234..."
        assert len(result) == 8

    def test_default_max_length_constant(self) -> None:
        """Test that default max length constant is set correctly."""
        assert SEGMENT_MAX_DISPLAY_LENGTH == 200
```

### Step 9: Update Column Width Test Assertions

**Location:** `app/tests/core/excel_formatting/test_formatting_all_blocks.py`

Update `test_format_all_blocks_column_widths` to reflect new column widths:

```python
def test_format_all_blocks_column_widths(self) -> None:
    """Test that column widths are set correctly for all 29 columns."""
    wb, ws = self._create_test_workbook_with_headers()

    _format_all_blocks_sheet(wb)

    # Check key column widths (updated for new widths)
    assert ws.column_dimensions["A"].width == 35  # block_raw_name (was 30)
    assert ws.column_dimensions["B"].width == 35  # block_resolved_name (was 30)
    assert ws.column_dimensions["AB"].width == 12  # block_scale_x (was 15)
    assert ws.column_dimensions["AC"].width == 12  # block_scale_y (was 15)
    assert ws.column_dimensions["G"].width == 50  # block_vertical_segments (was 40)
    assert ws.column_dimensions["H"].width == 50  # block_horizontal_segments (was 40)
    assert ws.column_dimensions["O"].width == 18  # block_filtered_polygon_count (was 20)
```

### Step 10: Run Validation Commands

Execute the validation commands to ensure zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests to validate formatting changes.
- `uv run pytest app/tests/core/excel_writer/ -v` - Run Excel writer tests to validate truncation helper and segment string generation.
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions.
- `uv run mypy app/core/excel_writer.py app/core/excel_formatting.py` - Type check the modified files.
- `uv run ruff check app/core/excel_writer.py app/core/excel_formatting.py` - Lint check the modified files.

## Notes

1. **Truncation threshold of 200 characters**: This value was chosen to balance readability with information density. Segment strings with more than 200 characters typically represent blocks with many complex geometry segments, and truncation helps Excel cells remain manageable.

2. **Text wrapping vs right-alignment trade-off**: The previous right-alignment for segment columns was intended to provide visual consistency for numeric lists. However, with the new text wrapping approach, left-alignment (default) works better because:
   - Wrapped text reads more naturally from left to right
   - The ellipsis truncation indicator ("...") is more visible at the end
   - Vertical top alignment keeps content aligned at the top when rows expand

3. **Column width optimization**: The new widths were carefully chosen based on the analysis document (`ai_output/088-all-blocks-column-formatting-analysis.md`) to:
   - Give more space to text-heavy columns that will wrap (A, B, G, H, R, V)
   - Reduce space for numeric columns that don't need as much width
   - Maintain overall sheet readability

4. **Existing highlighting behavior**: The three-tier scale highlighting (red/orange/yellow) remains unchanged. The new text wrapping alignment is applied separately from the fill highlighting.

5. **Test updates required**: The test `test_format_all_blocks_segment_columns_right_aligned` needs to be renamed and updated to test for wrap_text instead of right alignment. The column width test assertions also need updating.
