# Feature: Instructions Sheet for Excel Output

## Feature Description
Add a static "Instructions" sheet to the Excel output that explains the color coding used throughout the workbook and describes what each sheet contains. This sheet will be positioned as the first (leftmost) tab, making it immediately visible when users open the file. The sheet provides a clear reference for understanding the visual indicators and navigating the multi-sheet workbook.

## User Story
As a user reviewing the Excel output
I want an Instructions sheet that explains the color coding and sheet contents
So that I can quickly understand the visual indicators and find the data I need

## Problem Statement
The Excel output contains 10 sheets with various color highlights (yellow for scale variance, orange for negative scale, red for variance with negatives, green for nested blocks) but users have no in-document reference to understand what these colors mean. Users also need to explore multiple tabs to understand what each sheet contains.

## Solution Statement
Add a new "Instructions" sheet as the first tab in the Excel workbook containing:
1. A Color Coding section explaining the four highlight colors and their meanings
2. A Sheet Descriptions section listing all 10 analysis sheets with brief descriptions

The sheet will use simple formatting (bold headers, appropriate column widths, text wrapping) without auto-filter or freeze panes since it contains static reference content.

## Relevant Files
Use these files to implement the feature:

### Existing Files to Modify

- `app/core/constants.py`
  - Add `EXCEL_SHEET_INSTRUCTIONS` constant for the new sheet name
  - This follows the existing pattern of `EXCEL_SHEET_*` constants

- `app/core/excel_writer.py`
  - Add `_create_instructions_sheet()` function to generate the static content
  - Update `write_excel()` to call the new sheet creation function first
  - Import the new sheet name constant and formatting function

- `app/core/excel_formatting.py`
  - Add `_format_instructions_sheet()` function for column widths, bold headers, and text wrapping
  - Import the new sheet name constant
  - Note: This function will NOT apply auto-filter or freeze panes (differs from other sheets)

### New Files to Create

- `app/tests/core/excel_writer/test_excel_writer_instructions.py`
  - Test `_create_instructions_sheet()` creates proper static content
  - Test sheet position (first/leftmost)
  - Test color coding rows are present
  - Test sheet descriptions are present

- `app/tests/core/excel_formatting/test_formatting_instructions.py`
  - Test column widths are set correctly
  - Test bold headers are applied
  - Test text wrapping is enabled
  - Test NO auto-filter is applied
  - Test NO freeze panes are applied
  - Test empty sheet handling

## Implementation Plan
### Phase 1: Foundation
Add the sheet name constant to `constants.py` following the existing `EXCEL_SHEET_*` naming pattern. This establishes the sheet identifier used throughout the codebase.

### Phase 2: Core Implementation
1. Create `_create_instructions_sheet()` in `excel_writer.py` that builds a DataFrame with:
   - Color Coding section header and 4 color rows (Yellow, Orange, Red, Light Green)
   - Sheet Descriptions section header and 10 sheet description rows
   - Write to Excel using pandas ExcelWriter

2. Create `_format_instructions_sheet()` in `excel_formatting.py` that applies:
   - Column widths (Column A: 20 for Color/Sheet names, Column B: 60 for descriptions)
   - Bold font on section headers ("Color Coding" and "Sheet Descriptions")
   - Text wrapping on Column B
   - NO auto-filter (static content)
   - NO freeze panes (short, static content)

### Phase 3: Integration
1. Update `write_excel()` to call `_create_instructions_sheet()` BEFORE all other sheets
2. Update `write_excel()` to call `_format_instructions_sheet()` after workbook load
3. Move the Instructions sheet to position 0 (leftmost) after all sheets are created
4. Add comprehensive unit tests

## Step by Step Tasks

### Step 1: Add Sheet Name Constant
- Open `app/core/constants.py`
- Add `EXCEL_SHEET_INSTRUCTIONS: str = "Instructions"` in the Excel configuration sheet names section (around line 24)

### Step 2: Create Instructions Sheet Writer Function
- Open `app/core/excel_writer.py`
- Add import for `EXCEL_SHEET_INSTRUCTIONS` from constants
- Add import for `_format_instructions_sheet` from excel_formatting
- Create `_create_instructions_sheet(writer: pd.ExcelWriter) -> None` function:
  ```python
  def _create_instructions_sheet(writer: pd.ExcelWriter) -> None:
      """Create the Instructions sheet with color coding and sheet descriptions."""
      # Build rows for Color Coding section
      # Build rows for Sheet Descriptions section
      # Create DataFrame and write to Excel
  ```

### Step 3: Create Instructions Sheet Formatting Function
- Open `app/core/excel_formatting.py`
- Add import for `EXCEL_SHEET_INSTRUCTIONS` from constants
- Create `_format_instructions_sheet(wb: Workbook) -> None` function:
  ```python
  def _format_instructions_sheet(wb: Workbook) -> None:
      """Apply formatting to the Instructions sheet."""
      # Set column widths
      # Apply bold to section headers
      # Apply text wrapping to description column
      # Apply color fills to sample cells in Color Coding section
      # NO auto-filter
      # NO freeze panes
  ```

### Step 4: Integrate into write_excel Function
- In `app/core/excel_writer.py`, update `write_excel()`:
  - Add `_create_instructions_sheet(writer)` as the FIRST sheet creation call
  - Add `_format_instructions_sheet(wb)` as the FIRST formatting call after `wb = load_workbook()`

### Step 5: Ensure Sheet Position is Leftmost
- After all sheets are created, move Instructions sheet to index 0:
  ```python
  wb.move_sheet(EXCEL_SHEET_INSTRUCTIONS, offset=-wb.index(wb[EXCEL_SHEET_INSTRUCTIONS]))
  ```
- OR create Instructions sheet first in the writer context (sheets are ordered by creation)

### Step 6: Create Writer Unit Tests
- Create `app/tests/core/excel_writer/test_excel_writer_instructions.py`
- Test cases:
  - `test_instructions_sheet_created`: Sheet exists in output
  - `test_instructions_sheet_is_first`: Sheet is at index 0 (leftmost)
  - `test_instructions_sheet_color_coding_content`: Color coding rows present with correct colors
  - `test_instructions_sheet_sheet_descriptions_content`: All 10 sheet descriptions present
  - `test_instructions_sheet_section_headers`: "Color Coding" and "Sheet Descriptions" headers exist

### Step 7: Create Formatting Unit Tests
- Create `app/tests/core/excel_formatting/test_formatting_instructions.py`
- Test cases:
  - `test_format_instructions_column_widths`: Column A=20, Column B=60
  - `test_format_instructions_bold_headers`: Section headers are bold
  - `test_format_instructions_text_wrapping`: Column B has text wrapping
  - `test_format_instructions_no_autofilter`: auto_filter.ref is None
  - `test_format_instructions_no_freeze_panes`: freeze_panes is None
  - `test_format_instructions_color_sample_fills`: Color sample cells have correct fill colors
  - `test_format_instructions_empty_sheet`: Handles empty sheet gracefully
  - `test_format_instructions_missing_sheet`: Handles missing sheet gracefully

### Step 8: Run Validation Commands
- Run all tests to ensure no regressions
- Run type checker
- Run linter

## Testing Strategy
### Unit Tests
- Test `_create_instructions_sheet()` generates correct static content
- Test `_format_instructions_sheet()` applies correct formatting without auto-filter/freeze
- Test sheet positioning in workbook
- Test content accuracy (all colors, all sheets described)

### Integration Tests
- Test `write_excel()` produces workbook with Instructions sheet as first tab
- Test Instructions sheet is visible and properly formatted in generated Excel file

### Edge Cases
- Empty workbook: Instructions sheet should still be created and formatted
- Missing sheet: `_format_instructions_sheet()` should handle gracefully (log and skip)
- Very long sheet descriptions: Text wrapping should handle properly

### Playwright MCP Tests
Not applicable - this is an Excel output feature, not a UI feature.

## Acceptance Criteria
- [ ] Instructions sheet appears as the first (leftmost) tab when opening the Excel file
- [ ] Color Coding section displays all four colors (Yellow, Orange, Red, Light Green) with correct meanings
- [ ] Sheet Descriptions section lists all 10 sheets with accurate descriptions
- [ ] Column A has width 20, Column B has width 60
- [ ] Section headers ("Color Coding", "Sheet Descriptions") are bold
- [ ] Column B (descriptions) has text wrapping enabled
- [ ] No auto-filter is applied to the Instructions sheet
- [ ] No freeze panes are applied to the Instructions sheet
- [ ] Color sample cells in the Color Coding section display the actual colors
- [ ] All existing tests pass (no regressions)
- [ ] Type checking passes
- [ ] Linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_instructions.py -v` - Run new Instructions sheet writer tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_instructions.py -v` - Run new Instructions sheet formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all excel_formatting tests
- `uv run pytest app/tests/ -v` - Run full test suite
- `uv run mypy app/` - Type check
- `uv run ruff check app/` - Lint check

## Notes
- The Instructions sheet differs from other sheets in that it does NOT use auto-filter or freeze panes since it contains static reference content rather than filterable data
- The sheet uses a two-column layout: Column A for identifiers (color names, sheet names), Column B for descriptions
- Color sample cells should display the actual fill colors so users can visually match them to highlights in other sheets
- The four highlight colors are already defined in constants.py: `EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE` (Yellow), `EXCEL_FILL_COLOR_SCALE_NEGATIVE` (Orange), `EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE` (Red), `EXCEL_FILL_COLOR_NESTED_BLOCK` (Light Green)
