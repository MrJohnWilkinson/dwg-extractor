# Feature: Excel Freeze First Row and First Column

## Feature Description
Enhance the Excel output to freeze both the first row (header) and the first column (typically block/entity names) in all sheets. This allows users to scroll through large datasets while keeping the header row and the first column visible for easy reference.

## User Story
As a user analyzing CAD extraction data in Excel
I want the header row and first column to remain visible when scrolling
So that I can easily identify which data I'm viewing in large reports

## Problem Statement
Currently, the Excel output only freezes the header row (`freeze_panes = "A2"`). When users scroll horizontally through sheets with many columns (especially Block Geometry Analysis with 21+ columns), they lose sight of the first column (block name or entity identifier), making it difficult to correlate data with specific blocks.

## Solution Statement
Change `freeze_panes = "A2"` to `freeze_panes = "B2"` in all sheet formatting functions. In openpyxl, `freeze_panes` specifies the first **unfrozen** cell, so `"B2"` freezes everything above row 2 (the header row) AND everything to the left of column B (the first column A).

## Relevant Files
Use these files to implement the feature:

- `app/core/excel_formatting.py` - Contains all sheet formatting functions where `freeze_panes` is set. Each `_format_*_sheet()` function sets `ws.freeze_panes = "A2"` which needs to change to `"B2"`.

- `app/tests/core/excel_formatting/test_formatting_sheets.py` - Contains existing tests for sheet formatting. New tests should verify `freeze_panes = "B2"` on all sheets.

## Implementation Plan
### Phase 1: Foundation
This is a simple change with no foundational work needed. The feature requires only modifying the freeze_panes value from `"A2"` to `"B2"` in existing formatting functions.

### Phase 2: Core Implementation
Update the freeze_panes setting in all eight sheet formatting functions:
1. `_format_block_analysis_sheet`
2. `_format_layer_analysis_sheet`
3. `_format_entity_summary_sheet`
4. `_format_block_geometry_analysis_sheet`
5. `_format_annotations_analysis_sheet`
6. `_format_color_analysis_sheet`
7. `_format_extraction_issues_sheet`
8. `_format_block_definitions_sheet`

### Phase 3: Integration
No integration work needed - the change is self-contained within the formatting module.

## Step by Step Tasks

### Step 1: Update freeze_panes in excel_formatting.py
- Open `app/core/excel_formatting.py`
- Change `ws.freeze_panes = "A2"` to `ws.freeze_panes = "B2"` in all eight `_format_*_sheet` functions:
  - Line 96: `_format_block_analysis_sheet`
  - Line 123: `_format_layer_analysis_sheet`
  - Line 166: `_format_entity_summary_sheet`
  - Line 190: `_format_block_geometry_analysis_sheet`
  - Line 320: `_format_annotations_analysis_sheet`
  - Line 384: `_format_color_analysis_sheet`
  - Line 457: `_format_extraction_issues_sheet`
  - Line 515: `_format_block_definitions_sheet`

### Step 2: Add unit test for freeze_panes verification
- Add a new test class `TestFreezePanes` to `app/tests/core/excel_formatting/test_formatting_sheets.py`
- Add test `test_all_sheets_freeze_first_row_and_column` that verifies `freeze_panes == "B2"` for all sheet types
- Ensure the test creates a mock workbook with each sheet type and verifies the freeze_panes value after formatting

### Step 3: Run validation commands
- Run the test suite to verify all tests pass
- Run type checking with mypy
- Run linting with ruff

## Testing Strategy
### Unit Tests
- Test that each sheet formatting function sets `freeze_panes = "B2"` instead of `"A2"`
- Test that the freeze_panes setting works correctly on empty sheets
- Test that existing formatting functionality remains intact

### Integration Tests
- The existing integration tests in `test_excel_writer_core.py` will implicitly verify freeze_panes is applied when sheets are generated

### Edge Cases
- Empty sheets should still have freeze_panes set to "B2"
- Sheets with only headers (no data rows) should have correct freeze_panes

### Playwright MCP Tests
- Not applicable - this is a backend feature with no UI component

## Acceptance Criteria
- All eight Excel sheets have `freeze_panes = "B2"` applied
- When opening the generated Excel file, scrolling right keeps column A visible
- When opening the generated Excel file, scrolling down keeps row 1 (header) visible
- All existing tests continue to pass
- New test validates the freeze_panes setting for all sheets
- No regressions in mypy type checking or ruff linting

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_formatting/test_formatting_sheets.py -v` - Run sheet formatting tests to verify freeze_panes changes
- `uv run pytest app/tests/ -v` - Run all tests to ensure no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors
- `uv run ruff check app/` - Run linting to ensure code quality

## Notes
- The openpyxl `freeze_panes` property uses the cell reference of the first **unfrozen** cell, not the last frozen cell
- `"B2"` means: freeze row 1 (header) and column A (first column)
- This change affects all 8 sheets in the Excel output uniformly
- No new dependencies required
