# Feature: Integrate All Blocks Sheet into write_excel Function

## Feature Description
Integrate the existing `_create_all_blocks_sheet()` and `_format_all_blocks_sheet()` functions into the main `write_excel()` function in `excel_writer.py`. This unit wires up the already-implemented All Blocks sheet functionality (from Unit 2) so it becomes part of the generated Excel output. The All Blocks sheet will be positioned as the first sheet (position 1) to serve as the primary view, with the sheet ordering updated to: All Blocks, Block Analysis, Block Geometry, Block Definitions, Layer Analysis, Entity Summary, Annotations, Color, Issues.

## User Story
As a CAD data analyst
I want the All Blocks sheet to be included in the generated Excel workbook as the first sheet
So that I can immediately see the consolidated block-centric view when opening the Excel file without needing to navigate between sheets

## Problem Statement
The `_create_all_blocks_sheet()` function was implemented in Unit 2 (commit 4bd57bb) and is fully tested with 23 tests. The `_format_all_blocks_sheet()` function was also implemented with 14 formatting tests. However, neither function is called from `write_excel()`, so the All Blocks sheet is not actually generated when users export Excel files. The sheet needs to be integrated into the main export workflow and positioned as the first sheet.

## Solution Statement
Update `write_excel()` in `excel_writer.py` to:
1. Import `_format_all_blocks_sheet` from `excel_formatting`
2. Call `_create_all_blocks_sheet()` as the first sheet creation (before Block Analysis)
3. Call `_format_all_blocks_sheet()` in the formatting section (before other formatting calls)
4. Update docstring to reflect the new 9-sheet output with correct ordering

The resulting sheet order will be:
1. All Blocks (new - primary view)
2. Block Analysis
3. Block Geometry Analysis
4. Block Definitions
5. Layer Analysis
6. Entity Summary
7. Annotations Analysis
8. Color Analysis
9. Extraction Issues

## Relevant Files
Use these files to implement the feature:

- `app/core/excel_writer.py` - Main file to modify. Update `write_excel()` function to call `_create_all_blocks_sheet()` and `_format_all_blocks_sheet()`. Update imports to include `_format_all_blocks_sheet`. Update function docstring.
- `app/core/excel_formatting.py` - Reference file. Contains `_format_all_blocks_sheet()` function that needs to be imported.
- `app/tests/core/excel_writer/test_excel_writer_all_blocks.py` - Reference file. Contains 23 existing tests for the All Blocks sheet creation function.
- `app/tests/core/excel_formatting/test_formatting_all_blocks.py` - Reference file. Contains 14 existing tests for the All Blocks sheet formatting function.
- `app/tests/core/excel_writer/test_excel_writer_core.py` - Update to add integration test verifying All Blocks sheet is created in the full write_excel flow.

## Implementation Plan
### Phase 1: Foundation
1. Review current `write_excel()` function structure and sheet creation order
2. Verify `_create_all_blocks_sheet()` function exists and is working (already tested)
3. Verify `_format_all_blocks_sheet()` function exists and is working (already tested)
4. Understand the import structure in excel_writer.py

### Phase 2: Core Implementation
1. Add `_format_all_blocks_sheet` to imports from `excel_formatting`
2. Insert `_create_all_blocks_sheet()` call as first sheet creation in `write_excel()`
3. Insert `_format_all_blocks_sheet()` call as first formatting call
4. Update `write_excel()` docstring to reflect 9-sheet output

### Phase 3: Integration
1. Add integration test to verify All Blocks sheet appears in final Excel output
2. Add test to verify All Blocks is the first sheet (leftmost tab)
3. Run all existing tests to ensure no regressions
4. Verify the 826+ tests still pass

## Step by Step Tasks

### Step 1: Update excel_writer.py Imports
- Open `app/core/excel_writer.py`
- Locate the imports from `excel_formatting` (lines 94-104)
- Add `_format_all_blocks_sheet` to the import list
- Maintain alphabetical ordering of imports

### Step 2: Update write_excel() Sheet Creation Order
- Locate the `write_excel()` function (starts at line 292)
- Find the sheet creation section (lines 338-361)
- Insert call to `_create_all_blocks_sheet(extraction_data, writer)` as the FIRST sheet
- Add appropriate comment (e.g., "# Sheet 1: All Blocks")
- Update existing sheet comments to reflect new numbering (Sheet 2-9)

### Step 3: Update write_excel() Formatting Order
- Locate the formatting section in `write_excel()` (lines 367-383)
- Insert call to `_format_all_blocks_sheet(wb)` as the FIRST formatting call
- Add appropriate debug logging statement
- Update any debug logging that mentions sheet numbers

### Step 4: Update write_excel() Docstring
- Update the docstring at line 293-322 to reflect:
  - 9 sheets instead of 8 (or whatever current count)
  - New sheet ordering with All Blocks as first
  - List All Blocks sheet description

### Step 5: Add Integration Test for All Blocks Sheet
- Open `app/tests/core/excel_writer/test_excel_writer_core.py`
- Add test `test_write_excel_creates_all_blocks_sheet()` that:
  - Calls `write_excel()` with sample extraction data
  - Verifies "All Blocks" sheet exists in workbook
  - Verifies sheet is not empty (has headers at minimum)

### Step 6: Add Sheet Order Integration Test
- Add test `test_write_excel_all_blocks_is_first_sheet()` that:
  - Calls `write_excel()` with sample extraction data
  - Gets `wb.sheetnames` list
  - Asserts first sheet name is "All Blocks"

### Step 7: Run All Validation Commands
- Run type checking: `uv run mypy app/`
- Run linting: `uv run ruff check app/`
- Run all tests: `uv run pytest app/tests/ -v`
- Verify all 826+ tests pass with no regressions

## Testing Strategy
### Unit Tests
- Existing 23 tests in `test_excel_writer_all_blocks.py` cover `_create_all_blocks_sheet()` function
- Existing 14 tests in `test_formatting_all_blocks.py` cover `_format_all_blocks_sheet()` function
- No new unit tests needed for the functions themselves

### Integration Tests
- Add test verifying All Blocks sheet is created in full `write_excel()` flow
- Add test verifying All Blocks is positioned as first sheet
- Add test verifying sheet has expected column count (29 columns)

### Edge Cases
- Empty extraction data should still create All Blocks sheet with headers only
- Extraction data with only system blocks should create empty All Blocks sheet
- All existing edge cases are already covered by Unit 2 tests

### Playwright MCP Tests
Not applicable for this unit - no UI changes. This is backend Excel generation.

## Acceptance Criteria
- [ ] `_format_all_blocks_sheet` is imported in `excel_writer.py`
- [ ] `write_excel()` calls `_create_all_blocks_sheet()` as the first sheet creation
- [ ] `write_excel()` calls `_format_all_blocks_sheet()` in the formatting section
- [ ] `write_excel()` docstring is updated to reflect 9-sheet output
- [ ] All Blocks sheet appears as the first (leftmost) sheet in generated Excel files
- [ ] Sheet order is: All Blocks, Block Analysis, Block Geometry, Block Definitions, Layer Analysis, Entity Summary, Annotations, Color, Issues
- [ ] Integration test verifies All Blocks sheet is created
- [ ] Integration test verifies All Blocks is first sheet
- [ ] All 826+ existing tests pass (no regressions)
- [ ] Type checking passes (`uv run mypy app/`)
- [ ] Linting passes (`uv run ruff check app/`)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks sheet creation tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests
- `uv run pytest app/tests/core/excel_writer/test_excel_writer_core.py -v` - Run core excel_writer tests including new integration tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all excel_formatting tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure no regressions
- `uv run mypy app/` - Run type checking
- `uv run ruff check app/` - Run linting

## Notes
- This is Unit 4 of the All Blocks consolidated sheet feature implementation
- Unit 1 (completed): Added 3 new constants to `constants.py` (commit 7af090b)
- Unit 2 (completed): Created `_create_all_blocks_sheet()` (301 lines) and `_format_all_blocks_sheet()` (157 lines) with comprehensive tests (23 + 14 tests) (commit 4bd57bb)
- Unit 3: Planned for future polish/optimization
- The functions are fully implemented and tested; this unit only wires them into the main export workflow
- Sheet ordering follows the plan recommendation: All Blocks as primary view (first sheet)
- The `_create_all_blocks_sheet()` function already excludes system blocks and handles empty data cases
- The `_format_all_blocks_sheet()` function already handles missing sheet gracefully
- Currently 826 tests are passing; this change should not affect that count
