# Chore: Verify and Fix Spec 010 Refactoring Naming Conventions

## Chore Description
Verify that the refactoring during completion of specs/010-consolidate-geometry-sheet-with-scales.md was completed properly and implemented using naming conventions from app_docs/005-field-naming-convention.md and ai_docs/001-naming-convention-guide.md. Fix any naming inconsistencies found, particularly function names in excel_writer.py that don't match their actual purpose.

The spec 010 renamed sheet constants but didn't rename the corresponding function names, creating a mismatch where:
- `_create_block_counts_sheet()` creates "Block Analysis" sheet (not "Block Counts")
- `_create_block_trimming_analysis_sheet()` creates "Block Geometry Analysis" sheet (not "Block Trimming Analysis")

## Relevant Files
Use these files to resolve the chore:

- **app/core/constants.py** (67 lines) - Contains all Excel column and sheet name constants
  - All column name constants follow the {domain}_{attribute}[_{qualifier}] pattern from app_docs/005-field-naming-convention.md
  - Sheet name constants are correctly updated to EXCEL_SHEET_BLOCK_ANALYSIS and EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
  - New scale constants EXCEL_COLUMN_BLOCK_SCALE_X and EXCEL_COLUMN_BLOCK_SCALE_Y follow naming conventions

- **app/core/excel_writer.py** (396 lines) - Excel file generation module
  - ISSUE: Function `_create_block_counts_sheet()` (line 136) should be renamed to `_create_block_analysis_sheet()`
  - ISSUE: Function `_format_block_counts_sheet()` (line 222) should be renamed to `_format_block_analysis_sheet()`
  - ISSUE: Function `_create_block_trimming_analysis_sheet()` (line 270) should be renamed to `_create_block_geometry_analysis_sheet()`
  - ISSUE: Function `_format_block_trimming_analysis_sheet()` (line 355) should be renamed to `_format_block_geometry_analysis_sheet()`
  - ISSUE: Comment on line 110 says "Sheet 4: Block Trimming Analysis" should say "Sheet 4: Block Geometry Analysis"
  - Function calls in `write_excel()` use the old function names (lines 102, 111, 117, 120)
  - All imports and constants usage are correct

- **app/core/extractor.py** (466 lines) - CAD extraction logic
  - ExtractionResult TypedDict properly includes block_scale_data field with correct typing
  - Scale extraction implementation at lines 440-449 correctly extracts xscale and yscale
  - All field names follow naming conventions

- **app/tests/core/test_excel_writer.py** (~800 lines) - Excel writer unit tests
  - Test names correctly reference "block_analysis" and "block_geometry_analysis"
  - All tests pass (25/25 passing) despite function naming issues
  - Tests use constants, not hardcoded names, which is why they still pass

- **app_docs/005-field-naming-convention.md** (78 lines) - Field naming convention reference
  - Defines {domain}_{attribute}[_{qualifier}] pattern
  - Examples show proper naming: block_name, block_scale_x, block_scale_y, layer_block_insertion_count

- **ai_docs/001-naming-convention-guide.md** (213 lines) - General Python naming conventions
  - Function naming patterns: use descriptive verbs (create_, format_, get_, etc.)
  - Emphasizes self-documenting names that explain purpose without comments

### New Files
None required - all changes are fixes to existing implementation files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Current Column Naming Compliance
- Read app/core/constants.py and verify all EXCEL_COLUMN_* constants follow the {domain}_{attribute}[_{qualifier}] pattern
- Check that block_scale_x and block_scale_y follow conventions (domain=block, attribute=scale, qualifier=x/y)
- Verify all sheet name constants are correctly updated per spec 010
- Document any violations found (expected: zero violations for column names)

### Step 2: Verify Scale Data Extraction Implementation
- Read app/core/extractor.py lines 275-310 to verify ExtractionResult TypedDict includes block_scale_data field
- Read app/core/extractor.py lines 440-461 to verify xscale/yscale extraction implementation
- Verify scale data is stored as {(block_name, layer_name): (x_scale, y_scale)} dictionary structure
- Document any violations found (expected: zero violations for scale extraction)

### Step 3: Identify Function Naming Violations in excel_writer.py
- Read app/core/excel_writer.py and identify all function names that don't match their purpose
- Verify the following mismatches exist:
  - `_create_block_counts_sheet()` creates "Block Analysis" sheet
  - `_format_block_counts_sheet()` formats "Block Analysis" sheet
  - `_create_block_trimming_analysis_sheet()` creates "Block Geometry Analysis" sheet
  - `_format_block_trimming_analysis_sheet()` formats "Block Geometry Analysis" sheet
- Document all function names that need renaming with line numbers

### Step 4: Rename _create_block_counts_sheet to _create_block_analysis_sheet
- Use Edit tool to rename function definition at line 136
- Old: `def _create_block_counts_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:`
- New: `def _create_block_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:`
- Update function call in write_excel() at line 102
- Old: `_create_block_counts_sheet(extraction_data, writer)`
- New: `_create_block_analysis_sheet(extraction_data, writer)`

### Step 5: Rename _format_block_counts_sheet to _format_block_analysis_sheet
- Use Edit tool to rename function definition at line 222
- Old: `def _format_block_counts_sheet(wb: Workbook) -> None:`
- New: `def _format_block_analysis_sheet(wb: Workbook) -> None:`
- Update function call in write_excel() at line 117
- Old: `_format_block_counts_sheet(wb)`
- New: `_format_block_analysis_sheet(wb)`

### Step 6: Rename _create_block_trimming_analysis_sheet to _create_block_geometry_analysis_sheet
- Use Edit tool to rename function definition at line 270
- Old: `def _create_block_trimming_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:`
- New: `def _create_block_geometry_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:`
- Update function call in write_excel() at line 111
- Old: `_create_block_trimming_analysis_sheet(extraction_data, writer)`
- New: `_create_block_geometry_analysis_sheet(extraction_data, writer)`

### Step 7: Rename _format_block_trimming_analysis_sheet to _format_block_geometry_analysis_sheet
- Use Edit tool to rename function definition at line 355
- Old: `def _format_block_trimming_analysis_sheet(wb: Workbook) -> None:`
- New: `def _format_block_geometry_analysis_sheet(wb: Workbook) -> None:`
- Update function call in write_excel() at line 120
- Old: `_format_block_trimming_analysis_sheet(wb)`
- New: `_format_block_geometry_analysis_sheet(wb)`

### Step 8: Fix Misleading Comment on Line 110
- Use Edit tool to update comment at line 110
- Old: `# Sheet 4: Block Trimming Analysis`
- New: `# Sheet 4: Block Geometry Analysis`

### Step 9: Verify All Imports and Constants Usage
- Read app/core/excel_writer.py lines 1-50 to verify imports
- Confirm EXCEL_SHEET_BLOCK_ANALYSIS constant is imported (line 26)
- Confirm EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS constant is imported (line 29)
- Confirm scale column constants are imported (lines 39-40)
- Verify no old constant names (EXCEL_SHEET_BLOCK_COUNTS, EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS) remain

### Step 10: Run All Validation Commands
- Execute all validation commands listed in the "Validation Commands" section
- Verify zero test failures
- Verify zero type errors from mypy
- Verify all 25 excel_writer tests pass
- Verify all extractor tests pass
- Verify no regressions in existing functionality

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_excel_writer.py -v` - Verify all 25 Excel writer tests pass after function renaming
- `uv run pytest app/tests/core/test_extractor.py -v` - Verify scale extraction tests pass
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run mypy app/` - Verify type checking passes with no errors after renaming
- `uv run pytest --cov=app/core app/tests/core/ --cov-report=term-missing` - Verify code coverage remains high

## Notes

**Function Naming Principle:**
According to ai_docs/001-naming-convention-guide.md, function names should be "self-documenting" and "explain purpose without comments". The current function names violate this by using outdated sheet names that don't match what the functions actually create/format.

**Why Tests Still Pass:**
The test suite uses constants (EXCEL_SHEET_BLOCK_ANALYSIS, etc.) rather than hardcoded function names, which is why all 25 tests pass despite the function naming issues. The tests verify the correct sheet names are created, not the function names used to create them.

**Spec 010 Implementation Status:**
- ✅ Sheet name constants renamed correctly
- ✅ Column name constants follow naming conventions
- ✅ Scale extraction implemented correctly
- ✅ Excel sheet structure matches spec (4 columns in Block Analysis, 13 in Block Geometry Analysis)
- ✅ Red highlighting for mirrored blocks implemented
- ❌ Function names not updated to match new sheet names (this chore fixes it)

**Expected Impact:**
- Zero functional changes (functions already work correctly)
- Improved code clarity and maintainability
- Function names will match their actual purpose
- Comments will match actual sheet names
- Future developers won't be confused by outdated naming

**Naming Convention Summary:**
- Column names: {domain}_{attribute}[_{qualifier}] (e.g., block_scale_x, layer_block_insertion_count)
- Function names: {verb}_{descriptive_noun} (e.g., create_block_analysis_sheet, format_block_geometry_analysis_sheet)
- Sheet constants: EXCEL_SHEET_{SHEET_PURPOSE} (e.g., EXCEL_SHEET_BLOCK_ANALYSIS)
