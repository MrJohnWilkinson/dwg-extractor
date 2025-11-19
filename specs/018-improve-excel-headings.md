# Chore: Improve Excel Headings with Readable Formatting

## Chore Description
Improve Excel column headings to be more readable for end users by converting snake_case field names (e.g., `block_insertion_count`) to Title Case with proper spacing (e.g., "Block Insertion Count"). This requires:

1. Creating a `format_header()` function in `app/core/excel_formatting.py` that auto-converts snake_case to Title Case with a small override dictionary for acronyms
2. Updating `app/core/excel_writer.py` to apply the formatting to column names when writing DataFrames to Excel
3. Enabling header text wrapping with automatic row height expansion in all sheet formatters
4. Updating the field naming convention documentation to clarify the distinction between code naming (snake_case) and Excel display formatting (Title Case)
5. Adding comprehensive tests for the new `format_header()` function
6. Updating existing Excel writer tests to verify readable headers are present

## Relevant Files
Use these files to resolve the chore:

- **app/core/excel_formatting.py** (line 1-131) - Contains formatting functions for all four Excel sheets. Will add new `format_header()` function and update existing sheet formatters to enable header text wrapping.

- **app/core/excel_writer.py** (line 1-351) - Contains the `write_excel()` function and four sheet creation functions (`_create_block_analysis_sheet`, `_create_layer_analysis_sheet`, `_create_entity_summary_sheet`, `_create_block_geometry_analysis_sheet`). Will need to apply `format_header()` to column names before writing DataFrames.

- **app/core/constants.py** (line 1-69) - Defines all Excel column name constants as snake_case strings. These will remain unchanged as they represent the code-level identifiers, not the display format.

- **app_docs/005-field-naming-convention.md** (line 1-78) - Documents the field naming convention. Currently states in Rule #5 that Python and Excel use identical names. Will update to clarify that code uses snake_case while Excel displays Title Case.

- **app/tests/core/test_excel_formatting.py** (line 1-429) - Contains unit tests for all formatting functions. Will add new test class for `format_header()` function.

- **app/tests/core/test_excel_writer.py** (line 1-917) - Contains comprehensive tests for Excel generation. Will update tests that verify column headers to expect Title Case formatted headers instead of snake_case.

### New Files
None - all changes are to existing files.

## Step by Step Tasks

### Step 1: Create the format_header() function
Add a new public function `format_header()` to `app/core/excel_formatting.py`:
- Accepts a snake_case string (e.g., `"block_insertion_count"`)
- Splits on underscores and converts each word to title case
- Uses a small override dictionary for acronyms that should remain uppercase (e.g., `{"Dwg": "DWG", "Dxf": "DXF", "Cad": "CAD", "Id": "ID"}`)
- Returns a space-separated Title Case string (e.g., `"Block Insertion Count"`)
- Add comprehensive docstring with examples
- Position this function at the top of the module, before the sheet-specific formatting functions

### Step 2: Enable header text wrapping in all sheet formatters
Update all four formatting functions in `app/core/excel_formatting.py`:
- `_format_block_analysis_sheet()`
- `_format_layer_analysis_sheet()`
- `_format_entity_summary_sheet()`
- `_format_block_geometry_analysis_sheet()`

For each function:
- After applying auto-filter and column widths, add code to enable text wrapping on the header row (row 1)
- Set `alignment = Alignment(wrap_text=True, vertical='top')` for all cells in row 1
- Import `Alignment` from `openpyxl.styles` at the top of the file

### Step 3: Update excel_writer.py to format column headers
Update `app/core/excel_writer.py` to apply `format_header()` to DataFrame column names:
- Import the `format_header` function from `excel_formatting`
- In each of the four `_create_*_sheet()` functions, after creating the DataFrame but before calling `df.to_excel()`, rename the columns using: `df.columns = [format_header(col) for col in df.columns]`
- Apply this to all four sheet creation functions:
  - `_create_block_analysis_sheet()` (around line 168 before `df.to_excel()`)
  - `_create_layer_analysis_sheet()` (around line 209 before `df.to_excel()`)
  - `_create_entity_summary_sheet()` (around line 240 before `df.to_excel()`)
  - `_create_block_geometry_analysis_sheet()` (around line 326 before `df.to_excel()`)

### Step 4: Update field naming convention documentation
Update `app_docs/005-field-naming-convention.md`:
- Modify Rule #5 to clarify the distinction between code and Excel display
- Change from: `"5. All snake_case (Python and Excel use identical names)"`
- Change to: `"5. Code uses snake_case, Excel displays Title Case (e.g., code: 'block_insertion_count', Excel: 'Block Insertion Count')"`
- Add a new section after "Constants Pattern" called "Excel Display Format":
  - Explain that `format_header()` converts snake_case to Title Case for Excel
  - Note that constants remain snake_case as they are code identifiers
  - Provide examples showing code vs Excel display

### Step 5: Add tests for format_header() function
Add new test class to `app/tests/core/test_excel_formatting.py`:
- Create `TestFormatHeader` class after the imports
- Add test cases:
  - `test_format_header_basic()` - Test simple snake_case conversion (e.g., `"block_name"` → `"Block Name"`)
  - `test_format_header_multiple_words()` - Test longer field names (e.g., `"layer_block_insertion_count"` → `"Layer Block Insertion Count"`)
  - `test_format_header_single_word()` - Test single word (e.g., `"count"` → `"Count"`)
  - `test_format_header_with_numbers()` - Test with numbers (e.g., `"rotation_0"` → `"Rotation 0"`)
  - `test_format_header_empty_string()` - Test empty string (should return empty string)
  - `test_format_header_no_underscores()` - Test string without underscores (e.g., `"name"` → `"Name"`)
  - If acronym override dictionary is implemented: `test_format_header_acronym_override()` - Test acronyms remain uppercase

### Step 6: Update excel_writer tests to check for readable headers
Update `app/tests/core/test_excel_writer.py`:
- Import the `format_header` function at the top
- Update all test methods that verify column names to expect Title Case formatted headers
- Specifically update these test methods:
  - `test_block_analysis_sheet_simplified()` (line 133-157) - Change assertions to expect formatted headers
  - `test_layer_analysis_sheet_structure()` (line 159-181) - Change assertions to expect formatted headers
  - `test_entity_summary_sheet_structure()` (line 182-200) - Change assertions to expect formatted headers
  - `test_empty_data_all_sheets()` (line 282-316) - Change assertions to expect formatted headers
  - `test_block_geometry_analysis_sheet_consolidated()` (line 388-422) - Change assertions to expect formatted headers
  - `test_block_geometry_analysis_empty_data()` (line 651-690) - Change assertions to expect formatted headers
  - `test_constants_match_dataframe_columns()` (line 754-809) - Change to verify formatted headers, not raw constants
  - Any other tests that check `df.columns` or `list(df.columns)`
- Strategy: For each test, replace raw constant checks with `format_header(CONSTANT)` calls

### Step 7: Run validation commands
Execute all validation commands to ensure zero regressions:
- Run all tests with coverage to verify functionality
- Run type checking to ensure no type errors
- Run linting to ensure code quality

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_excel_formatting.py::TestFormatHeader -v` - Run new format_header tests to verify transformation logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run all excel_writer tests to verify readable headers are present
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run all excel_formatting tests to verify no regressions
- `uv run pytest app/tests/core/ -v` - Run all core tests to ensure no regressions
- `uv run mypy app/core/excel_formatting.py` - Type check the formatting module
- `uv run mypy app/core/excel_writer.py` - Type check the writer module
- `uv run mypy app/` - Type check entire application
- `uv run ruff check app/` - Lint entire application for code quality

## Notes
- The `format_header()` function should be a pure utility function with no side effects
- The acronym override dictionary should be small and focused (initially just DWG, DXF, CAD, ID if needed)
- Header text wrapping ensures long column names (e.g., "Layer Block Insertion Count") display properly in Excel
- The row height will automatically expand to fit wrapped text when users double-click the row separator
- All snake_case constants in `constants.py` remain unchanged - they are code identifiers, not display names
- This change improves user experience without affecting the underlying data structure or code logic
- Tests should verify both the transformation logic and the end-to-end Excel generation with formatted headers
