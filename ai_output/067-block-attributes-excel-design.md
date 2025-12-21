# Block Attributes Excel Implementation Plan

## Overview

Add block attribute data to the Excel output with two new columns at the end of the All Blocks sheet, plus reorder an existing column for improved visibility.

## Column Changes Summary

### All Blocks Sheet - New Column Order

**Reorder:** Move `block_layer_names` to column B:

| Position | Column Name | Notes |
|----------|-------------|-------|
| A | block_raw_name | unchanged |
| B | block_layer_names | reordered |
| C | block_resolved_name | shifted |
| D-AB | (remaining 24 columns) | shifted |
| AC | block_attribute_count | new |
| AD | block_attribute_data | new |

### New Column Specifications

**`block_attribute_count`** (Integer)
- Count of non-empty attributes on the block (across all insertions)
- Value: `0` for blocks with no attributes, `6` for blocks with 6 unique populated attributes
- Enables filtering/sorting by attribute richness

**`block_attribute_data`** (Text)
- Newline-separated TAG:VALUE pairs within a single cell
- Format:
  ```
  BAY#:27-004
  DEPT:30
  PROD1:Garage
  PROD2:Door Openers
  ```
- Skip tags with empty values
- Sort tags alphabetically for consistency
- Truncate using existing `_truncate_segment_string()` function (200 char limit)
- Enable text wrap for readability

## Implementation Steps

### Step 1: Populate Attribute Extraction in Extractor

**File:** `app/core/extractor.py`

The `block_attribute_data` field already exists in `ExtractionResult` (line 973) but is not populated.

1. Initialize `block_attribute_data: dict[str, set[tuple[str, str]]] = {}` near other data structures (~line 1050)

2. In the INSERT entity processing section (~line 1420-1560), extract ATTRIB entities:
   ```python
   # After processing INSERT entity
   if hasattr(entity, 'attribs'):
       for attrib in entity.attribs:
           tag = attrib.dxf.tag
           value = attrib.dxf.text
           if value:  # Skip empty values
               if effective_name not in block_attribute_data:
                   block_attribute_data[effective_name] = set()
               block_attribute_data[effective_name].add((tag, value))
   ```

3. Add `block_attribute_data` to the result dictionary (~line 1731):
   ```python
   "block_attribute_data": {
       k: sorted(list(v)) for k, v in block_attribute_data.items()
   },
   ```

### Step 2: Update All Blocks Sheet Column Order

**File:** `app/core/excel_writer.py`

Modify the column definition lists in `_create_all_blocks_sheet` (appears 3 times: ~lines 1066, 1229, 1268):

1. Move `EXCEL_COLUMN_BLOCK_LAYER_NAMES` from position after `EXCEL_COLUMN_BLOCK_LAYER_COUNT` to position after `EXCEL_COLUMN_BLOCK_RAW_NAME`
2. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` at the end (after `EXCEL_COLUMN_BLOCK_SCALE_Y`)
3. Add `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` at the end

### Step 3: Populate New Columns

**File:** `app/core/excel_writer.py`

In `_create_all_blocks_sheet` data population section (~line 1103):

1. Get attribute data for the block from extraction results:
   ```python
   block_attribute_data = data.get("block_attribute_data", {})
   ```

2. For each block row (~line 1229), calculate and format:
   ```python
   # Get attributes for this block
   attrs = block_attribute_data.get(resolved_name, [])
   attr_count = len(attrs)

   # Format as newline-separated TAG:VALUE pairs (alphabetically sorted)
   attr_str = "\n".join(f"{tag}:{value}" for tag, value in attrs)
   attr_str = _truncate_segment_string(attr_str)
   ```

3. Add to row dict:
   ```python
   EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT: attr_count,
   EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA: attr_str,
   ```

### Step 4: Update Excel Formatting

**File:** `app/core/excel_formatting.py`

In `format_all_blocks_sheet` function:

1. Update column width indices to account for column reorder (block_layer_names moved to B)
2. Add column width for `block_attribute_count` (~12 chars)
3. Add column width for `block_attribute_data` (~60 chars)
4. Enable text wrap for `block_attribute_data` column
5. Update any hardcoded column indices affected by the reorder

### Step 5: Update Tests

**Files:**
- `app/tests/core/extractor/test_extractor_*.py`
- `app/tests/core/excel_writer/test_excel_writer_*.py`
- `app/tests/core/excel_formatting/test_formatting_*.py`

1. Update column order assertions in All Blocks sheet tests
2. Add tests for attribute extraction (may need test DXF with ATTRIB entities)
3. Add tests for new columns in excel_writer
4. Update formatting tests for column width indices

## Files to Modify

| File | Changes |
|------|---------|
| `app/core/extractor.py` | Initialize and populate `block_attribute_data`, add to result dict |
| `app/core/excel_writer.py` | Reorder columns, populate new columns using existing `_truncate_segment_string` |
| `app/core/excel_formatting.py` | Update column widths and wrap settings for reordered/new columns |
| `app/tests/core/extractor/*.py` | Add attribute extraction tests |
| `app/tests/core/excel_writer/*.py` | Update column order tests, add attribute column tests |
| `app/tests/core/excel_formatting/*.py` | Update column index tests |

## Existing Infrastructure

Already in place (no changes needed):
- `EXCEL_COLUMN_BLOCK_ATTRIBUTE_COUNT` constant (`app/core/constants.py:147`)
- `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` constant (`app/core/constants.py:148`)
- `BlockAttributeRecord` TypedDict (`app/core/types.py:274`)
- `block_attribute_data` field in `ExtractionResult` (`app/core/extractor.py:973`)
- `_truncate_segment_string()` function (`app/core/excel_writer.py:120`)
- `SEGMENT_MAX_DISPLAY_LENGTH = 200` constant (`app/core/excel_writer.py:117`)
