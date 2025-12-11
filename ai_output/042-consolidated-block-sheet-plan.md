# Consolidated Block Sheet Implementation Plan

## Executive Summary

This plan details consolidating all block-related data into a new "All Blocks" Excel sheet. Currently, block data is spread across 3 sheets (Block Analysis, Block Geometry Analysis, Block Definitions) with different row granularities. The recommended approach creates a single comprehensive sheet at the **block definition level** (one row per unique block).

## Table Summary

| Current Sheet | Row Granularity | Key Fields | Consolidation Strategy |
|--------------|-----------------|------------|------------------------|
| Block Analysis | Block-Layer pair | name, insertion_count, entity_count, layer_name, xdata_apps | Aggregate to block level |
| Block Geometry Analysis | Block-Layer pair | rotations, scales, dimensions, segments, trim values, content zone | Aggregate rotations; keep geometry |
| Block Definitions | Block definition | raw_name, resolved_name, status, is_nested, parent_names, entity_count | Include directly |

## Relevant Files

- **app/core/types.py** - TypedDict definitions (BlockTrimmingData, ContentZoneData, BlockDefinitionRecord)
- **app/core/extractor.py** - ExtractionResult structure with all block data fields
- **app/core/excel_writer.py** - Sheet creation functions to modify/extend
- **app/core/constants.py** - Column name constants (add new EXCEL_COLUMN_* entries)
- **app/core/excel_formatting.py** - Formatting functions (add `_format_all_blocks_sheet`)
- **app_docs/005-field-naming-convention.md** - Naming rules for new fields

## In Scope

1. Create new "All Blocks" sheet with one row per block definition
2. Include all existing block fields from:
   - Block identity (raw_name, resolved_name)
   - Block status (insertion_status, is_nested, nested_parent_names)
   - Block counts (total_insertion_count, entity_count)
   - Block geometry (native_width, native_height, vertical_segments, horizontal_segments)
   - Block content zone (trim values, detected flag, dimensions, polygon counts)
   - Block scale summary (x, y or VARIES indicators)
   - Block rotation summary (aggregated counts across all layers)
3. Add new derived fields:
   - `block_layer_count` - count of distinct layers containing this block
   - `block_layer_names` - comma-separated list of layer names
   - `block_total_rotation_count` - sum of all rotation category counts
4. Apply standard Excel formatting (freeze, auto-filter, column widths)
5. Update constants.py with new column definitions
6. Write unit tests for new sheet

## Out of Scope

1. Removing existing sheets (Block Analysis, Block Geometry Analysis, Block Definitions)
2. Per-layer breakdowns in the consolidated sheet
3. Per-insertion detail (individual INSERT entity data)
4. XDATA content extraction (only app IDs are tracked)
5. GUI changes

## Proposed Column Structure (29 columns)

| # | Field Name | Source | Description |
|---|-----------|--------|-------------|
| 1 | block_raw_name | BlockDefinitionRecord | Original name from doc.blocks |
| 2 | block_resolved_name | BlockDefinitionRecord | Resolved name for anonymous blocks |
| 3 | block_insertion_status | BlockDefinitionRecord | Inserted/Nested Only/Unused/System/Unresolved |
| 4 | block_is_nested | BlockDefinitionRecord | True if appears inside another block |
| 5 | block_nested_parent_names | BlockDefinitionRecord | Comma-separated parent names |
| 6 | block_entity_count | BlockDefinitionRecord | Entities in block definition |
| 7 | block_insertion_count | Aggregated | Total insertions across all layers |
| 8 | block_layer_count | NEW | Count of distinct layers |
| 9 | block_layer_names | NEW | Comma-separated layer list |
| 10 | block_rotation_0 | Aggregated | Total 0° insertions |
| 11 | block_rotation_90 | Aggregated | Total 90° insertions |
| 12 | block_rotation_180 | Aggregated | Total 180° insertions |
| 13 | block_rotation_270 | Aggregated | Total 270° insertions |
| 14 | block_rotation_other | Aggregated | Total other rotation insertions |
| 15 | block_scale_x | block_scale_data | X scale or "VARIES" / "VARIES (-)" |
| 16 | block_scale_y | block_scale_data | Y scale or "VARIES" / "VARIES (-)" |
| 17 | block_native_width | BlockTrimmingData | Width at 0° rotation |
| 18 | block_native_height | BlockTrimmingData | Height at 0° rotation |
| 19 | block_vertical_segments | BlockTrimmingData | Comma-separated vertical segments |
| 20 | block_horizontal_segments | BlockTrimmingData | Comma-separated horizontal segments |
| 21 | block_suggested_trim_left | ContentZoneData | Content zone trim suggestion |
| 22 | block_suggested_trim_right | ContentZoneData | Content zone trim suggestion |
| 23 | block_suggested_trim_top | ContentZoneData | Content zone trim suggestion |
| 24 | block_suggested_trim_bottom | ContentZoneData | Content zone trim suggestion |
| 25 | block_content_zone_detected | ContentZoneData | TRUE/FALSE |
| 26 | block_content_zone_width | ContentZoneData | Content zone width |
| 27 | block_content_zone_height | ContentZoneData | Content zone height |
| 28 | block_polygon_count | ContentZoneData | Polygons before filtering |
| 29 | block_filtered_polygon_count | ContentZoneData | Polygons after filtering |

## Implementation Steps

### Step 1: Add Constants (constants.py)

Add new column constants:
```python
EXCEL_SHEET_ALL_BLOCKS: str = "All Blocks"
EXCEL_COLUMN_BLOCK_LAYER_COUNT: str = "block_layer_count"
EXCEL_COLUMN_BLOCK_LAYER_NAMES: str = "block_layer_names"
```

Note: Most columns already exist in constants.py from existing sheets.

### Step 2: Create Sheet Function (excel_writer.py)

Add `_create_all_blocks_sheet()` function:

1. Iterate over `all_block_definitions` (one row per block)
2. For each block definition:
   - Copy identity/status fields from BlockDefinitionRecord
   - Calculate `block_insertion_count` from `block_counts.get(resolved_name, 0)`
   - Calculate `block_layer_count` and `block_layer_names` from `block_layer_pairs`
   - Aggregate rotation counts from `block_rotation_counts`
   - Get scale summary from `block_scale_data`
   - Get geometry from `block_trimming_data`
   - Get content zone from `block_content_zone_data`
3. Sort by insertion_status (Inserted first), then by resolved_name

### Step 3: Add Formatting Function (excel_formatting.py)

Add `_format_all_blocks_sheet()`:
- Apply freeze panes (row 1 + column A)
- Set auto-filter on header row
- Apply column widths (proportional to content type)
- Highlight nested blocks (green fill)
- Highlight scale variance/negative (yellow/red fill)

### Step 4: Update write_excel() (excel_writer.py)

Insert call to `_create_all_blocks_sheet()` after Block Definitions sheet creation.

### Step 5: Write Unit Tests

Add test file: `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`
- Test empty data handling
- Test single block
- Test multiple blocks with various statuses
- Test aggregation logic (rotations, layers)
- Test scale variance indicators
- Test nested block highlighting

### Step 6: Update Formatting Tests

Add test file: `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Test freeze panes
- Test auto-filter
- Test column widths
- Test conditional formatting

## Data Aggregation Logic

### Layer Count and Names
```python
# For block 'DOOR':
layers_for_block = {key.layer_name for key in block_layer_pairs if key.block_name == 'DOOR'}
block_layer_count = len(layers_for_block)
block_layer_names = ", ".join(sorted(layers_for_block))
```

### Rotation Totals
```python
# Sum across all layers for each rotation category
rot_0_total = sum(
    count for key, count in block_rotation_counts.items()
    if key.block_name == 'DOOR' and key.rotation_category == '0'
)
```

### Insertion Count
```python
block_insertion_count = block_counts.get(resolved_name, 0)
```

## Recommendations

1. **Keep existing sheets** - The consolidated sheet provides an overview; existing sheets retain per-layer detail
2. **Position as first sheet** - Move "All Blocks" to position 1 as the primary view
3. **Consider sheet ordering**: All Blocks → Block Analysis → Block Geometry → Block Definitions → Layer Analysis → Entity Summary → Annotations → Color → Issues

## Next Steps

1. Review and approve this plan
2. Create feature branch: `feat/all-blocks-sheet`
3. Implement Step 1-6 sequentially
4. Run full test suite
5. Manual verification with real DXF files
