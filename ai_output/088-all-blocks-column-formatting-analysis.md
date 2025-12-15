# All Blocks Sheet Column Formatting Analysis

## Executive Summary

Analysis of the "All Blocks" sheet reveals that 29 columns have vastly different content patterns requiring targeted formatting. The segment columns (G, H) can contain extremely long comma-separated lists (500+ characters), while name columns (A, B, R, V) vary widely. The current implementation uses fixed widths without data row wrapping, causing horizontal scroll issues and truncated data in Excel.

## Table Summary

| Column | Header | Current Width | Observed Data Range | Recommended Width | Wrap Data? | Priority |
|--------|--------|---------------|---------------------|-------------------|------------|----------|
| A | Block Raw Name | 30 | 8-72 chars | 35 | Yes | High |
| B | Block Resolved Name | 30 | 8-72 chars | 35 | Yes | High |
| C | Block Suggested Trim Left | 15 | 0-4 chars | 12 | No | Low |
| D | Block Suggested Trim Right | 15 | 0-6 chars | 12 | No | Low |
| E | Block Suggested Trim Top | 15 | 0-6 chars | 12 | No | Low |
| F | Block Suggested Trim Bottom | 15 | 0-6 chars | 12 | No | Low |
| G | Block Vertical Segments | 40 | 0-509 chars | 50 | **Yes** | Critical |
| H | Block Horizontal Segments | 40 | 0-186 chars | 50 | **Yes** | Critical |
| I | Block Native Width | 20 | 1-5 chars | 15 | No | Low |
| J | Block Native Height | 20 | 1-7 chars | 15 | No | Low |
| K | Block Content Zone Detected | 20 | 4-5 chars | 18 | No | Low |
| L | Block Content Zone Width | 20 | 0-5 chars | 18 | No | Low |
| M | Block Content Zone Height | 20 | 0-7 chars | 18 | No | Low |
| N | Block Polygon Count | 18 | 0-3 chars | 15 | No | Low |
| O | Block Filtered Polygon Count | 20 | 0-2 chars | 18 | No | Low |
| P | Block Insertion Status | 20 | 8 chars max | 18 | No | Low |
| Q | Block Is Nested | 15 | 5 chars max | 12 | No | Low |
| R | Block Nested Parent Names | 40 | 0-50+ chars | 35 | Yes | Medium |
| S | Block Entity Count | 20 | 1-3 chars | 15 | No | Low |
| T | Block Insertion Count | 25 | 1-3 chars | 18 | No | Low |
| U | Block Layer Count | 18 | 1 char | 12 | No | Low |
| V | Block Layer Names | 40 | 1-30 chars | 35 | Yes | Medium |
| W | Block Rotation 0 | 12 | 1 char | 10 | No | Low |
| X | Block Rotation 90 | 12 | 1 char | 10 | No | Low |
| Y | Block Rotation 180 | 12 | 1 char | 10 | No | Low |
| Z | Block Rotation 270 | 12 | 1 char | 10 | No | Low |
| AA | Block Rotation Other | 15 | 1 char | 12 | No | Low |
| AB | Block Scale X | 15 | 1-12 chars | 12 | No | Low |
| AC | Block Scale Y | 15 | 1-12 chars | 12 | No | Low |

## Relevant Files

- `app/core/excel_formatting.py:560-713` - `_format_all_blocks_sheet()` function containing current column width definitions and formatting logic
- `app/core/excel_writer.py:989-1285` - `_create_all_blocks_sheet()` function that generates the data
- `app/core/constants.py:32` - `EXCEL_SHEET_ALL_BLOCKS` constant and column name definitions

## Sample Data Analysis

### Critical Width Issues Identified

**Vertical Segments Column (G)** - Most extreme case observed:
```
0.5, 873, 0.5, 3, 17, 17, 3, 0.5, 873, 0.5, 3, 17, 17, 3, 0.5, 873, 0.5, 3, 17, 17, 3, ...
```
- Character count: **509 characters** (Grocery_Gondola_Combined block)
- Current width (40) displays ~30 characters
- Without wrapping: 93% of data is hidden

**Horizontal Segments Column (H)** - High variance observed:
```
657.69, 0.31, 24.69, 6.73, 4.82, 10.77, 4.81, 13.65, 0.1, 2.05, 0.49, 71.9, 760, 126.81, ...
```
- Character count: **up to 186 characters**
- Current width (40) displays ~30 characters
- Without wrapping: 84% of data is hidden

**Block Name Columns (A, B)** - Long identifiers:
```
Grocery_Gondola_Combined - 2000H  - 1240W _505_505_-80724766-GROUND FFL
Refrigeration_Frozen_Hussmann_PGL_2050H - 5 Door-82274016-GROUND FFL
```
- Character count: **up to 72 characters**
- Current width (30) displays ~25 characters
- Without wrapping: 65% of data is hidden

### Data Type Classification

| Category | Columns | Characteristics | Formatting Strategy |
|----------|---------|-----------------|---------------------|
| **Long Text** | A, B, G, H, R, V | Variable length, high variance | Wrap text, moderate width |
| **Short Numeric** | C, D, E, F, I, J, L, M, N, O, S, T, U | 1-7 chars typically | Fixed width, right-align |
| **Boolean/Enum** | K, P, Q | Fixed vocabulary | Fixed width, no wrap |
| **Rotation Counts** | W, X, Y, Z, AA | 0-4 digit integers | Narrow fixed width |
| **Scale Values** | AB, AC | "VARIES", "VARIES (-)", or float | Moderate fixed width |

## Recommended Formatting Configuration

### Column Width Configuration (Excel units)

```python
# Group 1: Text columns requiring wrapping
TEXT_WRAP_COLUMNS = {
    "A": 35,   # block_raw_name - long identifiers
    "B": 35,   # block_resolved_name - long identifiers
    "G": 50,   # block_vertical_segments - CSV lists, CRITICAL
    "H": 50,   # block_horizontal_segments - CSV lists, CRITICAL
    "R": 35,   # block_nested_parent_names - parent block names
    "V": 35,   # block_layer_names - layer name lists
}

# Group 2: Narrow numeric columns (right-aligned)
NUMERIC_NARROW_COLUMNS = {
    "C": 12,   # block_suggested_trim_left
    "D": 12,   # block_suggested_trim_right
    "E": 12,   # block_suggested_trim_top
    "F": 12,   # block_suggested_trim_bottom
    "I": 15,   # block_native_width
    "J": 15,   # block_native_height
    "L": 18,   # block_content_zone_width
    "M": 18,   # block_content_zone_height
    "N": 15,   # block_polygon_count
    "O": 18,   # block_filtered_polygon_count
    "S": 15,   # block_entity_count
    "T": 18,   # block_insertion_count
    "U": 12,   # block_layer_count
}

# Group 3: Rotation count columns (very narrow)
ROTATION_COLUMNS = {
    "W": 10,   # block_rotation_0
    "X": 10,   # block_rotation_90
    "Y": 10,   # block_rotation_180
    "Z": 10,   # block_rotation_270
    "AA": 12,  # block_rotation_other
}

# Group 4: Status/boolean/scale columns
STATUS_COLUMNS = {
    "K": 18,   # block_content_zone_detected
    "P": 18,   # block_insertion_status
    "Q": 12,   # block_is_nested
    "AB": 12,  # block_scale_x
    "AC": 12,  # block_scale_y
}
```

### Row Height Considerations

For wrapped columns, Excel auto-adjusts row height. However, with extremely long segment lists:
- **Maximum recommended row height**: 75 points (~5 lines of wrapped text)
- **Alternative**: Truncate segment display at 100 characters with "..." suffix

### Alignment Configuration

| Column Type | Horizontal | Vertical | Wrap |
|-------------|------------|----------|------|
| Text columns (A, B, R, V) | Left | Top | Yes |
| Segment columns (G, H) | Left | Top | Yes |
| Numeric columns | Right | Center | No |
| Boolean columns (K, Q) | Center | Center | No |
| Status column (P) | Left | Center | No |

## Implementation Code Changes

### Proposed `_format_all_blocks_sheet()` Modifications

```python
def _format_all_blocks_sheet(wb: Workbook) -> None:
    """Apply formatting to the All Blocks sheet with text wrapping for long columns."""
    # ... existing header code ...

    # Set column widths with optimized values
    # Group 1: Text columns with wrapping
    ws.column_dimensions["A"].width = 35   # block_raw_name
    ws.column_dimensions["B"].width = 35   # block_resolved_name
    ws.column_dimensions["G"].width = 50   # block_vertical_segments (CRITICAL)
    ws.column_dimensions["H"].width = 50   # block_horizontal_segments (CRITICAL)
    ws.column_dimensions["R"].width = 35   # block_nested_parent_names
    ws.column_dimensions["V"].width = 35   # block_layer_names

    # Group 2: Trim columns (narrow)
    for col in ["C", "D", "E", "F"]:
        ws.column_dimensions[col].width = 12

    # Group 3: Dimension columns
    ws.column_dimensions["I"].width = 15   # block_native_width
    ws.column_dimensions["J"].width = 15   # block_native_height

    # Group 4: Content zone columns
    ws.column_dimensions["K"].width = 18   # block_content_zone_detected
    ws.column_dimensions["L"].width = 18   # block_content_zone_width
    ws.column_dimensions["M"].width = 18   # block_content_zone_height
    ws.column_dimensions["N"].width = 15   # block_polygon_count
    ws.column_dimensions["O"].width = 18   # block_filtered_polygon_count

    # Group 5: Status columns
    ws.column_dimensions["P"].width = 18   # block_insertion_status
    ws.column_dimensions["Q"].width = 12   # block_is_nested

    # Group 6: Count columns
    ws.column_dimensions["S"].width = 15   # block_entity_count
    ws.column_dimensions["T"].width = 18   # block_insertion_count
    ws.column_dimensions["U"].width = 12   # block_layer_count

    # Group 7: Rotation columns (very narrow)
    for col in ["W", "X", "Y", "Z"]:
        ws.column_dimensions[col].width = 10
    ws.column_dimensions["AA"].width = 12  # block_rotation_other

    # Group 8: Scale columns
    ws.column_dimensions["AB"].width = 12  # block_scale_x
    ws.column_dimensions["AC"].width = 12  # block_scale_y

    # Apply text wrapping to data rows for long-content columns
    wrap_alignment = Alignment(wrap_text=True, vertical="top")
    wrap_columns = [1, 2, 7, 8, 18, 22]  # A, B, G, H, R, V (1-indexed)

    for row_idx in range(2, ws.max_row + 1):
        for col_idx in wrap_columns:
            ws.cell(row=row_idx, column=col_idx).alignment = wrap_alignment

    # Apply right-alignment to numeric columns
    right_alignment = Alignment(horizontal="right", vertical="center")
    numeric_columns = [3, 4, 5, 6, 9, 10, 12, 13, 14, 15, 19, 20, 21, 23, 24, 25, 26, 27, 28, 29]

    for row_idx in range(2, ws.max_row + 1):
        for col_idx in numeric_columns:
            current = ws.cell(row=row_idx, column=col_idx)
            current.alignment = right_alignment
```

## Width Savings Analysis

| Column | Current | Recommended | Savings |
|--------|---------|-------------|---------|
| A | 30 | 35 | -5 (needed for readability) |
| B | 30 | 35 | -5 (needed for readability) |
| C-F | 60 (4x15) | 48 (4x12) | +12 |
| G | 40 | 50 | -10 (critical for data) |
| H | 40 | 50 | -10 (critical for data) |
| I-J | 40 (2x20) | 30 (2x15) | +10 |
| K-O | 98 | 87 | +11 |
| P-Q | 35 | 30 | +5 |
| R | 40 | 35 | +5 |
| S-U | 63 | 45 | +18 |
| V | 40 | 35 | +5 |
| W-AA | 63 | 52 | +11 |
| AB-AC | 30 | 24 | +6 |
| **Total** | 629 | 616 | **+13 (2% narrower)** |

Net effect: Sheet becomes 2% narrower while displaying data more effectively through text wrapping.

## Recommendations

1. **Critical Priority**: Enable text wrapping for segment columns (G, H) - these have 500+ character values that are currently invisible
2. **High Priority**: Enable text wrapping for name columns (A, B) - long block identifiers are truncated
3. **Medium Priority**: Enable text wrapping for layer/parent columns (R, V) - variable length lists
4. **Low Priority**: Reduce widths on rotation columns (W-AA) - single digit values don't need 12-15 width
5. **Consider**: Adding "..." truncation for segment columns if they exceed 200 characters to prevent extreme row heights

## Next Steps

1. Update `_format_all_blocks_sheet()` in `app/core/excel_formatting.py` with:
   - Revised column widths per the table above
   - Text wrapping for columns A, B, G, H, R, V on data rows
   - Right-alignment for numeric columns
2. Add unit tests verifying text wrap alignment is applied correctly
3. Consider adding a configurable "max segment display length" constant for extremely long segment lists
