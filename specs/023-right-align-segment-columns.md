# Feature: Right-Align Segment Columns in Block Geometry Analysis Sheet

## Feature Description
Apply right-alignment formatting to the "Block Vertical Segments" and "Block Horizontal Segments" columns in the Block Geometry Analysis Excel worksheet. These columns contain comma-separated numeric values (e.g., "10, 80, 10") which are currently left-aligned by default. Right-alignment will improve readability by aligning the numeric values for easier visual comparison across rows.

## User Story
As a CAD analyst reviewing block geometry data
I want the vertical and horizontal segment columns to be right-aligned
So that I can more easily compare numeric segment values across different blocks

## Problem Statement
The "Block Vertical Segments" and "Block Horizontal Segments" columns in the Block Geometry Analysis sheet contain comma-separated numeric values that represent geometric measurements. By default, Excel left-aligns text content, which makes it harder to visually scan and compare numeric values across rows. Right-alignment would improve the visual presentation and make these numeric lists easier to read and compare.

## Solution Statement
Add right-alignment formatting to the "Block Vertical Segments" (column L) and "Block Horizontal Segments" (column M) in the `_format_block_geometry_analysis_sheet()` function. This will be implemented using openpyxl's `Alignment` class with `horizontal='right'` applied to all cells in these two columns (excluding the header row which maintains its existing wrap_text formatting).

## Relevant Files
Use these files to implement the feature:

- **app/core/excel_formatting.py** - Contains the `_format_block_geometry_analysis_sheet()` function that applies formatting to the Block Geometry Analysis worksheet. This is where we'll add the right-alignment logic for columns L and M.
  - Lines 154-211 contain the function that handles all formatting for this sheet
  - Lines 166-179 set column widths including L (block_vertical_segments) and M (block_horizontal_segments)
  - Lines 186-210 apply yellow highlighting for scale variance rows
  - We'll add new code after the yellow highlighting logic to apply right-alignment to columns L and M

- **app/tests/core/test_excel_formatting.py** - Contains the test suite for Excel formatting functions. We'll add new test cases to verify right-alignment is applied correctly to the segment columns.
  - Lines 265-487 contain the `TestBlockGeometryAnalysisFormatting` test class
  - We'll add a new test method to verify right-alignment on columns L and M

### New Files
No new files are needed. All changes will be made to existing files.

## Implementation Plan

### Phase 1: Foundation
Review the existing formatting code in `_format_block_geometry_analysis_sheet()` to understand the current structure and identify where to add the right-alignment logic. The function already applies column widths, header formatting, frozen panes, auto-filters, and yellow highlighting for scale variance.

### Phase 2: Core Implementation
Add right-alignment formatting to columns L (block_vertical_segments) and M (block_horizontal_segments) in the `_format_block_geometry_analysis_sheet()` function. This will involve iterating through all data rows (excluding the header) and applying the `Alignment(horizontal='right')` style to cells in these columns.

### Phase 3: Integration
Ensure the right-alignment formatting integrates seamlessly with existing formatting features (yellow highlighting, frozen headers, column widths) and does not interfere with any existing functionality. Verify that the alignment is preserved when the Excel file is saved and opened.

## Step by Step Tasks

### 1. Add Right-Alignment Logic to Block Geometry Analysis Sheet Formatting
- Open `app/core/excel_formatting.py`
- Locate the `_format_block_geometry_analysis_sheet()` function (lines 154-211)
- After the yellow highlighting logic (around line 210), add new code to:
  - Create a right-alignment style using `Alignment(horizontal='right')`
  - Iterate through all data rows (from row 2 to `ws.max_row`)
  - Apply the right-alignment to column L (column index 12) and column M (column index 13)
  - Preserve any existing fill formatting (yellow highlighting) while adding alignment
- Update the logger message to mention alignment formatting was applied
- Ensure the code handles empty sheets gracefully (similar to existing patterns)

### 2. Create Unit Tests for Right-Alignment
- Open `app/tests/core/test_excel_formatting.py`
- In the `TestBlockGeometryAnalysisFormatting` class, add a new test method:
  - `test_format_geometry_analysis_segment_columns_right_aligned()`
    - Create a test workbook with the Block Geometry Analysis sheet
    - Add headers and sample data rows with segment values
    - Apply formatting using `_format_block_geometry_analysis_sheet()`
    - Verify that columns L and M have right-alignment applied to data rows
    - Verify that the header row maintains its wrap_text alignment
    - Verify that other columns (A-K) do not have right-alignment
- Add another test for edge case:
  - `test_format_geometry_analysis_segment_alignment_with_highlighting()`
    - Create test data with rows that have "VARIES" in scale columns (yellow highlighting)
    - Verify that right-alignment is applied to columns L and M even when rows are highlighted
    - Ensure both the yellow fill and right-alignment coexist on the same cells

### 3. Run Validation Commands
- Execute all validation commands listed below to ensure the feature works correctly with zero regressions
- Fix any test failures or type checking issues that arise
- Verify the feature works end-to-end by running the application and inspecting the generated Excel file

## Testing Strategy

### Unit Tests
- **test_format_geometry_analysis_segment_columns_right_aligned**: Verify that columns L and M have `horizontal='right'` alignment applied to all data rows (excluding header)
- **test_format_geometry_analysis_segment_alignment_with_highlighting**: Verify that right-alignment works correctly on highlighted rows (yellow fill for VARIES scale values)
- **test_format_geometry_analysis_empty_sheet**: Existing test should continue to pass, confirming empty sheets are handled gracefully

### Integration Tests
The existing integration tests in `test_excel_writer.py` should continue to pass without modification, demonstrating that the new alignment feature integrates seamlessly with the existing Excel generation workflow.

### Edge Cases
- Empty worksheet (no data rows, only headers) - should not crash
- Single data row - alignment should be applied correctly
- Multiple data rows with varying content (empty strings, short values, long comma-separated lists) - all should be right-aligned
- Rows with yellow highlighting (VARIES scale values) - alignment should coexist with fill formatting
- Very long segment lists - right-alignment should still be applied correctly

### Playwright MCP Tests
No Playwright tests are needed for this feature as it only affects Excel file formatting, which is validated through unit tests. The feature does not involve GUI interaction.

## Acceptance Criteria
1. The "Block Vertical Segments" column (L) in the Block Geometry Analysis sheet has right-alignment applied to all data rows
2. The "Block Horizontal Segments" column (M) in the Block Geometry Analysis sheet has right-alignment applied to all data rows
3. The header row (row 1) maintains its existing wrap_text formatting and is not affected by the right-alignment change
4. Right-alignment coexists correctly with existing yellow highlighting for scale variance rows
5. All other columns (A-K) maintain their default left-alignment
6. All existing unit tests continue to pass without modification
7. New unit tests verify the right-alignment behavior for columns L and M
8. Type checking with mypy passes with no errors
9. The application runs successfully and generates Excel files with correctly aligned segment columns
10. Empty worksheets are handled gracefully without errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_excel_formatting.py::TestBlockGeometryAnalysisFormatting -v` - Run Block Geometry Analysis formatting tests to verify right-alignment
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run all Excel formatting tests to ensure no regressions
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests to ensure integration works correctly
- `uv run pytest app/tests/ -v` - Run full test suite to validate zero regressions across entire codebase
- `uv run mypy app/` - Verify type checking passes with no errors
- `uv run ruff check app/` - Verify linting passes with no issues
- `bash scripts/start.sh` - Launch application to manually verify Excel output has right-aligned segment columns (visual inspection of generated Excel file)

## Notes
- The right-alignment will only affect the visual presentation in Excel and does not change the underlying data values
- The `Alignment` class from openpyxl supports `horizontal='right'` which is the standard way to right-align content in Excel cells
- The implementation should iterate through data rows dynamically (using `ws.max_row`) rather than hardcoding row counts, ensuring it works correctly regardless of the number of data rows
- When applying alignment to cells that already have yellow fill formatting (scale variance highlighting), we need to preserve the existing fill while adding the alignment property
- The column indices for openpyxl are 1-based: column L is index 12, column M is index 13
- This is a purely cosmetic enhancement that improves readability without changing any business logic or data extraction functionality
