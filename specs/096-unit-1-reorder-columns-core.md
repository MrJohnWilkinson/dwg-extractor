# Chore: Unit 1 - Reorder All Blocks Sheet Columns (Core Implementation)

## Chore Description
This is Unit 1 of the "Reorder All Blocks Sheet Columns" chore. This unit focuses on updating the core implementation files (`excel_writer.py` and `excel_formatting.py`) to implement the new column order for the "All Blocks" Excel sheet.

The changes prioritize content zone and geometry-related fields immediately after block names for easier analysis. The column count remains 29 - only the order changes.

**New column order:**
| Column | Field | Notes |
|--------|-------|-------|
| A | block_raw_name | Identity |
| B | block_resolved_name | Identity |
| C | block_suggested_trim_left | Content zone trim |
| D | block_suggested_trim_right | Content zone trim |
| E | block_suggested_trim_top | Content zone trim |
| F | block_suggested_trim_bottom | Content zone trim |
| G | block_vertical_segments | Geometry segments |
| H | block_horizontal_segments | Geometry segments |
| I | block_native_width | Geometry dimensions |
| J | block_native_height | Geometry dimensions |
| K | block_content_zone_detected | Content zone status |
| L | block_content_zone_width | Content zone dimensions |
| M | block_content_zone_height | Content zone dimensions |
| N | block_polygon_count | Polygon metrics |
| O | block_filtered_polygon_count | Polygon metrics |
| P | block_insertion_status | Block metadata |
| Q | block_is_nested | Block metadata |
| R | block_nested_parent_names | Block metadata |
| S | block_entity_count | Block metadata |
| T | block_insertion_count | Block metadata |
| U | block_layer_count | Layer aggregation |
| V | block_layer_names | Layer aggregation |
| W | block_rotation_0 | Rotation counts |
| X | block_rotation_90 | Rotation counts |
| Y | block_rotation_180 | Rotation counts |
| Z | block_rotation_270 | Rotation counts |
| AA | block_rotation_other | Rotation counts |
| AB | block_scale_x | Scale data |
| AC | block_scale_y | Scale data |

## Relevant Files
Use these files to resolve the chore:

- **`app/core/excel_writer.py`** - Contains `_create_all_blocks_sheet()` function that builds DataFrame rows. Has 3 places where column order is defined:
  - Main row construction in `rows.append()` dictionary (lines ~1189-1220)
  - Empty DataFrame for empty `all_block_definitions` (lines ~1027-1058)
  - Empty DataFrame for system-blocks-only case (lines ~1226-1257)

- **`app/core/excel_formatting.py`** - Contains `_format_all_blocks_sheet()` function that applies formatting:
  - Column width assignments (lines ~591-620) - mapped by Excel letter (A-AC)
  - Scale highlighting logic (lines ~666-699) - currently reads columns O/P (15/16)
  - Segment right-alignment (lines ~701-707) - currently uses columns S/T (19/20)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_create_all_blocks_sheet()` Main Row Construction

In `app/core/excel_writer.py`, update the `rows.append()` dictionary (around lines 1189-1220) to use the new column order:

```python
rows.append(
    {
        EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
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
        EXCEL_COLUMN_BLOCK_LAYER_NAMES: block_layer_names,
        EXCEL_COLUMN_BLOCK_ROTATION_0: rot_0,
        EXCEL_COLUMN_BLOCK_ROTATION_90: rot_90,
        EXCEL_COLUMN_BLOCK_ROTATION_180: rot_180,
        EXCEL_COLUMN_BLOCK_ROTATION_270: rot_270,
        EXCEL_COLUMN_BLOCK_ROTATION_OTHER: rot_other,
        EXCEL_COLUMN_BLOCK_SCALE_X: x_scale,
        EXCEL_COLUMN_BLOCK_SCALE_Y: y_scale,
    }
)
```

### Step 2: Update Empty DataFrame for Empty `all_block_definitions`

Update the empty DataFrame column list (around lines 1027-1058) for the case when `all_block_definitions` is empty:

```python
df = pd.DataFrame(
    columns=[
        EXCEL_COLUMN_BLOCK_RAW_NAME,
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
        EXCEL_COLUMN_BLOCK_LAYER_NAMES,
        EXCEL_COLUMN_BLOCK_ROTATION_0,
        EXCEL_COLUMN_BLOCK_ROTATION_90,
        EXCEL_COLUMN_BLOCK_ROTATION_180,
        EXCEL_COLUMN_BLOCK_ROTATION_270,
        EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
        EXCEL_COLUMN_BLOCK_SCALE_X,
        EXCEL_COLUMN_BLOCK_SCALE_Y,
    ]
)
```

### Step 3: Update Empty DataFrame for System-Blocks-Only Case

Update the empty DataFrame column list (around lines 1226-1257) for when all blocks are system blocks:

Use the same column order as Step 2 - the lists must be identical.

### Step 4: Update Column Widths in `_format_all_blocks_sheet()`

In `app/core/excel_formatting.py`, update all column width assignments to match new positions:

```python
# Set column widths (29 columns: A-AC)
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

### Step 5: Update Scale Highlighting Column References

In `_format_all_blocks_sheet()`, update the scale column references for highlighting:

- **Old**: x_scale was column O (15), y_scale was column P (16)
- **New**: x_scale is column AB (28), y_scale is column AC (29)

Find and update these lines (around lines 668-670):
```python
# Old:
x_scale_cell = ws.cell(row=row_idx, column=15)  # Column O
y_scale_cell = ws.cell(row=row_idx, column=16)  # Column P

# New:
x_scale_cell = ws.cell(row=row_idx, column=28)  # Column AB
y_scale_cell = ws.cell(row=row_idx, column=29)  # Column AC
```

Also update the comment that references column letters (around line 667):
```python
# Old: "Scale columns are O (15 = x_scale) and P (16 = y_scale)"
# New: "Scale columns are AB (28 = x_scale) and AC (29 = y_scale)"
```

### Step 6: Update Segment Column Right-Alignment References

In `_format_all_blocks_sheet()`, update segment column alignment references:

- **Old**: vertical_segments was column S (19), horizontal_segments was column T (20)
- **New**: vertical_segments is column G (7), horizontal_segments is column H (8)

Find and update these lines (around lines 701-707):
```python
# Old:
# Apply right-alignment to segment columns (S=19 and T=20)
right_alignment = Alignment(horizontal="right")
for row_idx in range(2, ws.max_row + 1):
    # Column S (19) - block_vertical_segments
    ws.cell(row=row_idx, column=19).alignment = right_alignment
    # Column T (20) - block_horizontal_segments
    ws.cell(row=row_idx, column=20).alignment = right_alignment

# New:
# Apply right-alignment to segment columns (G=7 and H=8)
right_alignment = Alignment(horizontal="right")
for row_idx in range(2, ws.max_row + 1):
    # Column G (7) - block_vertical_segments
    ws.cell(row=row_idx, column=7).alignment = right_alignment
    # Column H (8) - block_horizontal_segments
    ws.cell(row=row_idx, column=8).alignment = right_alignment
```

### Step 7: Run Validation Commands

Execute validation commands to ensure the implementation is complete and correct.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks Excel writer tests (expect failures until tests are updated in Unit 2)
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests (expect failures until tests are updated in Unit 2)
- `uv run mypy app/core/excel_writer.py app/core/excel_formatting.py` - Run type checking on modified files to ensure no type errors introduced

**Note**: Tests are expected to fail after this unit because the test files have not been updated yet. The test updates are scheduled for Unit 2 of this chore.

## Notes
- The column count remains 29 - only the order changes
- All three DataFrame column definitions in `_create_all_blocks_sheet()` must be updated identically to maintain consistency
- The scale highlighting logic reads cell values to determine highlighting tier (red/orange/yellow) - column indices must match new positions
- The segment right-alignment applies text formatting to specific columns - indices must match new positions
- Tests will fail until Unit 2 (test updates) is completed - this is expected
- Implementation learnings from prior units: None (this is the first unit)
