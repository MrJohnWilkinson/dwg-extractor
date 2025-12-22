# Attribute Analysis Sheet Implementation Plan

## Executive Summary
The current block attribute implementation stores TAG:VALUE pairs in the All Blocks sheet, creating visual clutter. This plan proposes: (1) simplifying the All Blocks sheet to show only unique attribute tag names, and (2) adding a new "Attribute Analysis" sheet that provides detailed analysis of which blocks contain which attributes with their varying values.

## Table Summary

| Change | Current State | Proposed State | Affected Files |
|--------|--------------|----------------|----------------|
| All Blocks - Attribute Column | `TAG:VALUE` pairs (e.g., `DEPT:30\nPROD1:Garage`) | Tags only (e.g., `DEPT\nPROD1`) | excel_writer.py |
| Column Name | `block_attribute_data` | `block_attribute_tags` | constants.py, excel_writer.py |
| New Sheet | N/A | "Attribute Analysis" | constants.py, excel_writer.py, excel_formatting.py |
| New Sheet Columns | N/A | 5 columns (see below) | types.py, excel_writer.py |

### Proposed Attribute Analysis Sheet Layout

| Position | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| A | `attribute_block_name` | Block containing the attribute | PRODUCT_BLOCK |
| B | `attribute_block_layer_names` | Layers where block is inserted | Layer1, Layer2 |
| C | `attribute_tag` | The attribute tag name | DEPT |
| D | `attribute_values` | Comma-separated unique values | 30, 45 |
| E | `attribute_value_count` | Count of unique values | 2 |

### Sample Attribute Analysis Sheet Data

| Block Name | Layer Names | Tag | Values | Count |
|------------|-------------|-----|--------|-------|
| PRODUCT_BLOCK | TEST_LAYER | BAY# | 12-001, 27-004, 27-005 | 3 |
| PRODUCT_BLOCK | TEST_LAYER | DEPT | 30, 45 | 2 |
| PRODUCT_BLOCK | TEST_LAYER | PROD1 | Garage, Kitchen | 2 |
| PRODUCT_BLOCK | TEST_LAYER | PROD2 | Appliances, Door Openers | 2 |
| SIMPLE_BLOCK | TEST_LAYER | ID | ITEM-001, ITEM-002 | 2 |

## Relevant Files

- **app/core/constants.py** - Add `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant and rename `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`. Add 5 new column constants for the Attribute Analysis sheet.
- **app/core/excel_writer.py** - Modify `_create_all_blocks_sheet` to show tags-only format. Add new `_create_attribute_analysis_sheet` function. Update `write_excel_file` to include new sheet.
- **app/core/excel_formatting.py** - Add `_format_attribute_analysis_sheet` function with column widths and auto-filter.
- **app/core/types.py** - May need `AttributeAnalysisRecord` TypedDict for type safety (optional).
- **app/tests/core/excel_writer/test_excel_writer_all_blocks.py** - Update attribute data tests to check for tags-only format.
- **app/tests/core/excel_writer/conftest.py** - Update fixture data to support new format.
- **New file: app/tests/core/excel_writer/test_excel_writer_attribute_analysis.py** - Tests for new sheet.
- **New file: app/tests/core/excel_formatting/test_formatting_attribute_analysis.py** - Tests for new sheet formatting.

## Implementation Phases

### Phase 1: Constant Updates
1. Rename `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` in constants.py
2. Add `EXCEL_SHEET_ATTRIBUTE_ANALYSIS = "Attribute Analysis"` constant
3. Add new column constants:
   - `EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME`
   - `EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES`
   - `EXCEL_COLUMN_ATTRIBUTE_TAG`
   - `EXCEL_COLUMN_ATTRIBUTE_VALUES`
   - `EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT`

### Phase 2: All Blocks Sheet Modification
1. Update excel_writer.py to import renamed constant
2. Modify attribute formatting in `_create_all_blocks_sheet`:
   ```python
   # OLD: attr_str = "\n".join(f"{tag}:{value}" for tag, value in attrs)
   # NEW: Extract unique tags only
   unique_tags = sorted(set(tag for tag, value in attrs))
   attr_str = "\n".join(unique_tags)
   attr_str = _truncate_segment_string(attr_str)
   ```
3. Update tests expecting TAG:VALUE format to expect tags-only

### Phase 3: Attribute Analysis Sheet Implementation
1. Create `_create_attribute_analysis_sheet` function in excel_writer.py
2. Build data by iterating over `block_attribute_data`:
   - Group by (block_name, tag) to collect all values
   - Look up layer names from `block_layer_pairs`
   - Sort rows by block_name, then tag
3. Create DataFrame with 5 columns
4. Write to Excel

### Phase 4: Formatting
1. Add `_format_attribute_analysis_sheet` in excel_formatting.py
2. Set column widths: A=35, B=35, C=20, D=60, E=12
3. Enable text wrap on columns B and D
4. Apply auto-filter
5. Apply header styling

### Phase 5: Integration and Testing
1. Update `write_excel_file` to call new sheet function
2. Update existing attribute tests for tags-only format
3. Add new test file for Attribute Analysis sheet
4. Run full validation suite

## Step-by-Step Implementation Tasks

### Unit 1: Rename Constant and Update All Blocks Sheet

**1.1 Rename constant in constants.py**
- Change `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`
- Update the comment to reflect the new purpose

**1.2 Update imports in excel_writer.py**
- Replace import of `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` with `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`

**1.3 Modify attribute string formatting**
- Location: `_create_all_blocks_sheet` around line 1237
- Change from TAG:VALUE pairs to unique tags only
- Keep the `attr_count` as the total number of (tag, value) pairs

**1.4 Update column reference in row dict**
- Location: line 1272
- Change `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS`

**1.5 Update empty DataFrame column lists**
- Update both occurrences (empty data case and empty rows case)

**1.6 Run validation**
- `uv run mypy app/core/constants.py app/core/excel_writer.py`
- Fix any import errors

### Unit 2: Add Attribute Analysis Sheet Constants

**2.1 Add sheet constant**
```python
EXCEL_SHEET_ATTRIBUTE_ANALYSIS: str = "Attribute Analysis"
```

**2.2 Add column constants**
```python
# Excel configuration - Attribute Analysis columns
EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME: str = "attribute_block_name"
EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES: str = "attribute_block_layer_names"
EXCEL_COLUMN_ATTRIBUTE_TAG: str = "attribute_tag"
EXCEL_COLUMN_ATTRIBUTE_VALUES: str = "attribute_values"
EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT: str = "attribute_value_count"
```

### Unit 3: Implement Attribute Analysis Sheet

**3.1 Add imports in excel_writer.py**
- Import new sheet and column constants

**3.2 Create `_create_attribute_analysis_sheet` function**
```python
def _create_attribute_analysis_sheet(
    data: ExtractionResult,
    writer: pd.ExcelWriter,
) -> None:
    """Create the Attribute Analysis sheet with block-attribute-value details."""
    block_attribute_data = data.get("block_attribute_data", {})
    block_layer_pairs = data.get("block_layer_pairs", {})

    if not block_attribute_data:
        # Create empty sheet with headers
        df = pd.DataFrame(columns=[...])
        df.to_excel(writer, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS, index=False)
        return

    # Build a lookup for block -> layer names
    block_to_layers: dict[str, set[str]] = {}
    for key in block_layer_pairs.keys():
        if key.block_name not in block_to_layers:
            block_to_layers[key.block_name] = set()
        block_to_layers[key.block_name].add(key.layer_name)

    # Group attributes by (block_name, tag) -> set of values
    block_tag_values: dict[tuple[str, str], set[str]] = {}
    for block_name, attrs in block_attribute_data.items():
        for tag, value in attrs:
            key = (block_name, tag)
            if key not in block_tag_values:
                block_tag_values[key] = set()
            block_tag_values[key].add(value)

    # Build rows
    rows = []
    for (block_name, tag), values in sorted(block_tag_values.items()):
        layer_names = sorted(block_to_layers.get(block_name, set()))
        layer_str = ", ".join(layer_names)
        values_str = ", ".join(sorted(values))
        rows.append({
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_NAME: block_name,
            EXCEL_COLUMN_ATTRIBUTE_BLOCK_LAYER_NAMES: layer_str,
            EXCEL_COLUMN_ATTRIBUTE_TAG: tag,
            EXCEL_COLUMN_ATTRIBUTE_VALUES: values_str,
            EXCEL_COLUMN_ATTRIBUTE_VALUE_COUNT: len(values),
        })

    df = pd.DataFrame(rows)
    # Apply header formatting
    df.columns = [format_header(col) for col in df.columns]
    df.to_excel(writer, sheet_name=EXCEL_SHEET_ATTRIBUTE_ANALYSIS, index=False)
```

**3.3 Update `write_excel_file` to call new function**
- Add call to `_create_attribute_analysis_sheet(data, writer)` after other sheet calls

### Unit 4: Add Formatting

**4.1 Create `_format_attribute_analysis_sheet` in excel_formatting.py**
```python
def _format_attribute_analysis_sheet(wb: Workbook) -> None:
    """Format the Attribute Analysis sheet."""
    if EXCEL_SHEET_ATTRIBUTE_ANALYSIS not in wb.sheetnames:
        return

    ws = wb[EXCEL_SHEET_ATTRIBUTE_ANALYSIS]

    # Apply header styling
    _apply_header_style(ws)

    # Set column widths
    ws.column_dimensions["A"].width = 35  # attribute_block_name
    ws.column_dimensions["B"].width = 35  # attribute_block_layer_names
    ws.column_dimensions["C"].width = 20  # attribute_tag
    ws.column_dimensions["D"].width = 60  # attribute_values
    ws.column_dimensions["E"].width = 12  # attribute_value_count

    # Apply text wrapping for columns with potentially long text
    wrap_columns = [2, 4]  # B and D
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in wrap_columns:
            ws.cell(row=row_idx, column=col_idx).alignment = Alignment(
                wrap_text=True, vertical="top"
            )

    # Apply auto-filter
    if ws.max_row > 0:
        ws.auto_filter.ref = f"A1:E{ws.max_row}"
```

**4.2 Update `format_excel_file` to call new function**

### Unit 5: Update Tests

**5.1 Update test_excel_writer_all_blocks.py**
- Rename tests referencing `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA`
- Update assertions to check for tags-only format
- `test_all_blocks_attribute_data_format` -> Check for tags without values

**5.2 Update conftest.py fixture**
- No structural changes needed (data format unchanged in extraction)

**5.3 Create test_excel_writer_attribute_analysis.py**
- Test sheet exists
- Test column names
- Test data population
- Test empty data handling
- Test value aggregation

**5.4 Create test_formatting_attribute_analysis.py**
- Test column widths
- Test text wrapping
- Test auto-filter

### Unit 6: Full Validation
- Run `uv run mypy app/`
- Run `uv run pytest app/tests/ -v`
- Run `uv run ruff check app/`
- Run `uv run ruff format app/ --check`

## Simple List Summary

- **Step 1**: Rename `block_attribute_data` column to `block_attribute_tags` and show tags-only (no values)
- **Step 2**: Add new "Attribute Analysis" sheet constant and 5 column constants
- **Step 3**: Implement `_create_attribute_analysis_sheet` function with block-tag-values rows
- **Step 4**: Add `_format_attribute_analysis_sheet` with column widths and text wrap
- **Step 5**: Update existing tests for tags-only format in All Blocks sheet
- **Step 6**: Create new test files for Attribute Analysis sheet
- **Step 7**: Run full validation suite (mypy, pytest, ruff)
