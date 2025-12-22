# Feature: Attribute Analysis Sheet Formatting

## Feature Description
This unit implements the `_format_attribute_analysis_sheet` function in `excel_formatting.py` that applies professional formatting to the "Attribute Analysis" sheet. This is Unit 4 of the Attribute Analysis Sheet feature, building upon:
- Unit 1: Renamed `EXCEL_COLUMN_BLOCK_ATTRIBUTE_DATA` to `EXCEL_COLUMN_BLOCK_ATTRIBUTE_TAGS` and updated tags to be comma-separated
- Unit 2: Added `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` sheet constant and 5 column constants
- Unit 3: Implemented `_create_attribute_analysis_sheet` in excel_writer.py (sheet 10 of 10, 1149 tests passing)

The formatting function will apply consistent styling including column widths, auto-filter, frozen panes, header wrapping, and text wrapping for columns with potentially long content.

## User Story
As a CAD data analyst
I want the Attribute Analysis sheet to have professional formatting
So that I can easily read and filter attribute data with proper column widths and text wrapping

## Problem Statement
The Attribute Analysis sheet created in Unit 3 has no formatting applied. Without formatting:
- Column widths default to narrow widths making content hard to read
- No auto-filter prevents easy data filtering
- Long text in layer names and attribute values columns gets truncated
- Headers are not frozen, making navigation of large datasets difficult
- The sheet appears inconsistent with other formatted sheets in the workbook

## Solution Statement
Implement the `_format_attribute_analysis_sheet` function that:
1. Checks if the Attribute Analysis sheet exists (graceful handling if not)
2. Sets appropriate column widths for each of the 5 columns
3. Applies auto-filter to enable data filtering
4. Freezes the header row and first column (B2)
5. Applies text wrapping to header row
6. Applies text wrapping to data rows in columns with potentially long text (B and D)
7. Integrates with `write_excel()` function to apply formatting after sheet creation

## Relevant Files
Use these files to implement the feature:

- **app/core/excel_formatting.py** - Primary file to modify. Add the new `_format_attribute_analysis_sheet` function following the established pattern of other formatting functions. Add import for `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant.
- **app/core/excel_writer.py** - Add import for `_format_attribute_analysis_sheet` and call it in the formatting section of `write_excel()` after `_format_block_definitions_sheet(wb)`.
- **app/core/constants.py** - Reference for `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant (already exists from Unit 2).
- **app/tests/core/excel_formatting/test_formatting_sheets.py** - Add tests for the new formatting function following established patterns.

### New Files
None required for this unit.

## Implementation Plan

### Phase 1: Foundation
1. Review existing formatting functions in `excel_formatting.py` to understand the pattern:
   - Each `_format_*_sheet` function takes a `Workbook` parameter
   - Functions check if sheet exists before formatting
   - Functions apply: auto-filter, freeze panes (B2), column widths, header wrap, and data-specific formatting
   - Functions log their actions using the module logger

2. Review the existing constant in `constants.py` (added in Unit 2):
   - `EXCEL_SHEET_ATTRIBUTE_ANALYSIS = "Attribute Analysis"`

### Phase 2: Core Implementation
1. Add import for `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` to `excel_formatting.py`
2. Implement `_format_attribute_analysis_sheet` function following the provided specification
3. Add import and call to `_format_attribute_analysis_sheet` in `excel_writer.py`

### Phase 3: Integration
1. Add unit tests for the new formatting function
2. Verify formatting is applied correctly to the Attribute Analysis sheet
3. Verify empty sheet case is handled gracefully
4. Run full test suite to ensure zero regressions

## Step by Step Tasks

### Step 1: Add Import to excel_formatting.py
- Open `app/core/excel_formatting.py`
- Add `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` to the existing import block from `.constants`
- The import should be alphabetically ordered with other `EXCEL_SHEET_*` constants

### Step 2: Implement `_format_attribute_analysis_sheet` Function
- Add the function at the end of the file (after `_format_all_blocks_sheet`):
```python
def _format_attribute_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Attribute Analysis sheet.

    This function applies:
    - Auto-filter to the header row
    - Frozen panes (header row and first column)
    - Column widths appropriate for each data type
    - Text wrapping on header row
    - Text wrapping on columns B (layer names) and D (attribute values)

    Args:
        wb: openpyxl Workbook object containing the Attribute Analysis sheet
    """
    if EXCEL_SHEET_ATTRIBUTE_ANALYSIS not in wb.sheetnames:
        logger.info("Attribute Analysis sheet not found, skipping formatting")
        return

    ws = wb[EXCEL_SHEET_ATTRIBUTE_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Attribute Analysis sheet")

    # Set column widths (5 columns: A-E)
    ws.column_dimensions["A"].width = 35  # attribute_block_name
    ws.column_dimensions["B"].width = 35  # attribute_block_layer_names
    ws.column_dimensions["C"].width = 20  # attribute_tag
    ws.column_dimensions["D"].width = 60  # attribute_values
    ws.column_dimensions["E"].width = 12  # attribute_value_count

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Apply text wrapping for columns with potentially long text (B and D)
    wrap_alignment = Alignment(wrap_text=True, vertical="top")
    wrap_columns = [2, 4]  # B (layer_names) and D (attribute_values)
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in wrap_columns:
            ws.cell(row=row_idx, column=col_idx).alignment = wrap_alignment

    logger.info("Attribute Analysis sheet formatted")
```

### Step 3: Update excel_writer.py Imports
- Open `app/core/excel_writer.py`
- Add `_format_attribute_analysis_sheet` to the import block from `.excel_formatting`
- The import should be alphabetically ordered

### Step 4: Update write_excel Function
- Locate the formatting section in `write_excel()` function (around lines 432-450)
- Add formatting call after `_format_block_definitions_sheet(wb)`:
```python
logger.debug("Applying formatting to Attribute Analysis sheet...")
_format_attribute_analysis_sheet(wb)
```

### Step 5: Add Unit Tests
- Add tests to `app/tests/core/excel_formatting/test_formatting_sheets.py`:

```python
class TestAttributeAnalysisFormatting:
    """Test suite for _format_attribute_analysis_sheet function."""

    def test_format_attribute_analysis_autofilter(self, temp_dir: str) -> None:
        """Test that auto-filter is applied to Attribute Analysis sheet."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS

        # Add headers and sample data
        ws.append([
            "attribute_block_name",
            "attribute_block_layer_names",
            "attribute_tag",
            "attribute_values",
            "attribute_value_count",
        ])
        ws.append(["VALVE", "Layer1, Layer2", "DEPT", "Engineering", 1])

        _format_attribute_analysis_sheet(wb)

        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref == "A1:E2"

    def test_format_attribute_analysis_column_widths(self, temp_dir: str) -> None:
        """Test that column widths are set correctly on Attribute Analysis sheet."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        ws.append([
            "attribute_block_name",
            "attribute_block_layer_names",
            "attribute_tag",
            "attribute_values",
            "attribute_value_count",
        ])

        _format_attribute_analysis_sheet(wb)

        assert ws.column_dimensions["A"].width == 35  # attribute_block_name
        assert ws.column_dimensions["B"].width == 35  # attribute_block_layer_names
        assert ws.column_dimensions["C"].width == 20  # attribute_tag
        assert ws.column_dimensions["D"].width == 60  # attribute_values
        assert ws.column_dimensions["E"].width == 12  # attribute_value_count

    def test_format_attribute_analysis_freeze_panes(self, temp_dir: str) -> None:
        """Test that Attribute Analysis sheet freezes first row and first column."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        ws.append(["block_name", "layer_names", "tag", "values", "count"])
        ws.append(["VALVE", "Layer1", "DEPT", "Engineering", 1])

        _format_attribute_analysis_sheet(wb)

        assert ws.freeze_panes == "B2"

    def test_format_attribute_analysis_header_wrap(self, temp_dir: str) -> None:
        """Test that header row has text wrapping enabled."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        ws.append([
            "attribute_block_name",
            "attribute_block_layer_names",
            "attribute_tag",
            "attribute_values",
            "attribute_value_count",
        ])

        _format_attribute_analysis_sheet(wb)

        for col_idx in range(1, 6):
            cell = ws.cell(row=1, column=col_idx)
            assert cell.alignment is not None
            assert cell.alignment.wrap_text is True
            assert cell.alignment.vertical == "top"

    def test_format_attribute_analysis_data_wrap_columns(self, temp_dir: str) -> None:
        """Test that columns B and D have text wrapping in data rows."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        ws.append(["block_name", "layer_names", "tag", "values", "count"])
        ws.append(["VALVE", "Layer1, Layer2, Layer3", "DEPT", "Eng, Maint, Ops", 3])
        ws.append(["PIPE", "Layer1", "ID", "PIPE-001, PIPE-002", 2])

        _format_attribute_analysis_sheet(wb)

        # Verify columns B (2) and D (4) have text wrapping in data rows
        for row_idx in [2, 3]:
            b_cell = ws.cell(row=row_idx, column=2)
            d_cell = ws.cell(row=row_idx, column=4)

            assert b_cell.alignment is not None
            assert b_cell.alignment.wrap_text is True
            assert b_cell.alignment.vertical == "top"

            assert d_cell.alignment is not None
            assert d_cell.alignment.wrap_text is True
            assert d_cell.alignment.vertical == "top"

    def test_format_attribute_analysis_empty_sheet(self, temp_dir: str) -> None:
        """Test that empty Attribute Analysis sheet is handled gracefully."""
        from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS

        # Apply formatting (should not crash on empty sheet)
        _format_attribute_analysis_sheet(wb)

        # Column widths should still be set
        assert ws.column_dimensions["A"].width == 35
        assert ws.column_dimensions["D"].width == 60
        assert ws.freeze_panes == "B2"

    def test_format_attribute_analysis_missing_sheet(self, temp_dir: str) -> None:
        """Test that missing Attribute Analysis sheet is handled gracefully."""
        from core.excel_formatting import _format_attribute_analysis_sheet

        wb = Workbook()
        # Default sheet has different name, so Attribute Analysis doesn't exist

        # Should not raise an exception
        _format_attribute_analysis_sheet(wb)

        # Verify default sheet is unchanged
        assert len(wb.sheetnames) == 1
```

### Step 6: Update TestFreezePanes Class
- Add test for Attribute Analysis freeze panes in the `TestFreezePanes` class:

```python
def test_attribute_analysis_freeze_panes(self, temp_dir: str) -> None:
    """Test that Attribute Analysis sheet freezes first row and first column."""
    from core.constants import EXCEL_SHEET_ATTRIBUTE_ANALYSIS
    from core.excel_formatting import _format_attribute_analysis_sheet

    wb = Workbook()
    ws = cast(Worksheet, wb.active)
    ws.title = EXCEL_SHEET_ATTRIBUTE_ANALYSIS
    ws.append(["block_name", "layer_names", "tag", "values", "count"])
    ws.append(["VALVE", "Layer1", "DEPT", "Engineering", 1])

    _format_attribute_analysis_sheet(wb)

    assert ws.freeze_panes == "B2"
```

### Step 7: Update Test for All Sheets Freeze
- Update the `test_all_sheets_freeze_first_row_and_column` test to include Attribute Analysis sheet (now 9 sheet types instead of 8)

### Step 8: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Test that auto-filter is applied correctly
- Test that all 5 column widths are set correctly
- Test that freeze panes is set to B2
- Test that header row has text wrapping enabled
- Test that columns B and D have text wrapping in data rows
- Test that empty sheet is handled gracefully (no crash, formatting still applied)
- Test that missing sheet is handled gracefully (function returns without error)

### Integration Tests
- Test full Excel generation with sample data
- Verify Attribute Analysis sheet has all formatting applied
- Verify formatting integrates with other 9 sheets

### Edge Cases
- Empty Attribute Analysis sheet (headers only)
- Sheet doesn't exist in workbook
- Very long text in layer names column
- Very long text in attribute values column
- Single row of data
- Many rows of data (100+)

### Playwright MCP Tests
Not applicable for this unit - no GUI or end-to-end functionality added.

## Acceptance Criteria
- [ ] `EXCEL_SHEET_ATTRIBUTE_ANALYSIS` constant imported in excel_formatting.py
- [ ] `_format_attribute_analysis_sheet` function implemented with correct signature
- [ ] Function checks if sheet exists before formatting (graceful handling)
- [ ] Auto-filter applied using `ws.dimensions`
- [ ] Freeze panes set to "B2" (header row and first column)
- [ ] Column widths set correctly: A=35, B=35, C=20, D=60, E=12
- [ ] Header row has text wrapping with vertical="top"
- [ ] Data rows in columns B and D have text wrapping with vertical="top"
- [ ] Function logs actions using module logger
- [ ] `_format_attribute_analysis_sheet` imported in excel_writer.py
- [ ] `write_excel()` calls `_format_attribute_analysis_sheet(wb)` after Block Definitions
- [ ] All unit tests pass for new formatting function
- [ ] `uv run mypy app/` passes with no errors
- [ ] `uv run pytest app/tests/` passes with all tests
- [ ] `uv run ruff check app/` passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/excel_formatting.py` - Type check the modified excel_formatting file
- `uv run mypy app/core/excel_writer.py` - Type check the modified excel_writer file
- `uv run mypy app/` - Run full type checking to ensure no regressions
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run excel_formatting tests to verify new tests pass
- `uv run pytest app/tests/core/excel_writer/ -v` - Run excel_writer tests to verify integration works
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run ruff check app/` - Lint check for code quality
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- This is Unit 4 of the Attribute Analysis Sheet feature:
  - Unit 1 (completed): Renamed constant and updated All Blocks sheet for unique tags
  - Unit 2 (completed): Added sheet and column constants
  - Unit 3 (completed): Implemented `_create_attribute_analysis_sheet` function (1149 tests passing)
  - **Unit 4 (this spec)**: Add formatting function for Attribute Analysis sheet
- The implementation follows the existing pattern for formatting functions in excel_formatting.py
- The function uses the same formatting approach as other sheets: auto-filter, freeze panes, column widths, and text wrapping
- Column widths are chosen to accommodate typical content:
  - A (block_name): 35 - matches other block name columns
  - B (layer_names): 35 - comma-separated list of layer names
  - C (tag): 20 - attribute tag names are typically short
  - D (values): 60 - comma-separated list of values can be long
  - E (count): 12 - single numeric value
- The function gracefully handles missing sheets (returns early with log message) following the pattern in `_format_block_definitions_sheet`
