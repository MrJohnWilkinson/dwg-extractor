# Bug: MTEXT Annotation Content Contains Raw Formatting Codes

## Bug Description
When extracting MTEXT entities from DXF files, the annotation content includes raw AutoCAD formatting codes like `\pxqc;`, `\pxt...;`, `\L`, `\O`, `\P`, etc. These codes make the Excel output unreadable and difficult to use. For example, text like `\pxqc;MENS CASUAL\P PANTS` should display as `MENS CASUAL PANTS` but currently shows the raw formatting codes.

**Actual behavior:** MTEXT content includes formatting codes (e.g., `\pxqc;MENS CASUAL\P PANTS`)
**Expected behavior:** MTEXT content shows plain text with formatting codes stripped (e.g., `MENS CASUAL PANTS`)

## Problem Statement
The `extract_blocks()` and `extract_color_analysis()` functions in `app/core/extractor.py` use `entity.text` to retrieve MTEXT content, which returns the raw text including all inline formatting codes. This needs to be changed to use ezdxf's built-in `plain_text()` method which strips formatting codes.

## Solution Statement
Replace `entity.text` with `entity.plain_text()` for MTEXT entities. The `plain_text()` method returns text without formatting codes. By default it replaces `\P` with newlines, but we need spaces instead, so we'll call `plain_text()` and then replace newlines with single spaces.

The solution uses ezdxf's built-in `plain_text(split=False, fast=True)` method which:
- Strips all MTEXT formatting codes (`\pxqc;`, `\pxt...;`, `\L`, `\O`, etc.)
- Replaces paragraph breaks (`\P`) with newlines
- Then we replace newlines with single spaces to match the requirement

## Steps to Reproduce
1. Create a DXF file with MTEXT containing formatting codes (e.g., `\pxqc;MENS CASUAL\P PANTS`)
2. Run `extract_blocks()` on the file
3. Observe that `annotation_data` and `color_analysis_data` contain the raw formatting codes
4. Expected: Plain text `MENS CASUAL PANTS` without formatting codes

## Root Cause Analysis
In `app/core/extractor.py`, there are two locations where MTEXT content is extracted:

1. **Line 467 in `extract_blocks()`**: Uses `entity.text` for MTEXT entities
2. **Line 198 in `extract_color_analysis()`**: Uses `entity.text` for MTEXT entities

Both locations retrieve the raw `.text` property which includes formatting codes. The ezdxf library provides a `plain_text()` method on MTEXT entities specifically designed to strip these codes.

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py` - Contains the two locations where MTEXT text is extracted. Both `extract_blocks()` (line 467) and `extract_color_analysis()` (line 198) need to use `plain_text()` instead of `.text`
- `app/tests/core/test_extractor.py` - Add tests to verify MTEXT formatting codes are stripped correctly
- `app/tests/assets/create_annotation_test.py` - Update to include MTEXT with formatting codes for testing

### New Files
- `app/tests/assets/create_mtext_formatting_test.py` - Script to create a DXF test fixture with various MTEXT formatting codes
- `app/tests/assets/mtext_formatting_test.dxf` - Generated test fixture

## Step by Step Tasks

### Step 1: Create test fixture with MTEXT formatting codes
- Create `app/tests/assets/create_mtext_formatting_test.py` script that generates a DXF file with MTEXT entities containing various formatting codes:
  - Paragraph alignment codes (`\pxqc;`, `\pxql;`, `\pxqr;`, `\pxqj;`)
  - Paragraph breaks (`\P`)
  - Tab characters (`\~`)
  - Underline/overline (`\L`, `\l`, `\O`, `\o`)
  - Font changes (`\f...;`)
  - Color codes (`\C...;`)
  - Text height (`\H...;`)
  - Stacking/fractions (`\S...;`)
  - Tracking/width (`\T...;`, `\W...;`)
  - Complex example: `\pxqc;MENS CASUAL\P PANTS` should become `MENS CASUAL PANTS`
- Run the script to generate `app/tests/assets/mtext_formatting_test.dxf`

### Step 2: Add helper function to clean MTEXT content
- Add a helper function `_clean_mtext_content(entity)` in `app/core/extractor.py` that:
  - Calls `entity.plain_text(split=False, fast=True)` to strip formatting codes
  - Replaces newlines (`\n`) with single spaces
  - Collapses multiple consecutive spaces into single spaces
  - Strips leading/trailing whitespace
  - Returns the cleaned string

### Step 3: Update extract_blocks() to use cleaned MTEXT content
- Modify line 467 in `extract_blocks()` to use `_clean_mtext_content(entity)` instead of `entity.text` for MTEXT entities
- TEXT entities remain unchanged (they already work correctly with `entity.dxf.text`)

### Step 4: Update extract_color_analysis() to use cleaned MTEXT content
- Modify line 198 in `extract_color_analysis()` to use `_clean_mtext_content(entity)` instead of `entity.text` for MTEXT entities
- TEXT entities remain unchanged

### Step 5: Add unit tests for MTEXT formatting cleanup
- Add test class `TestMtextFormatting` in `app/tests/core/test_extractor.py` with tests:
  - `test_mtext_paragraph_codes_stripped` - Verify `\pxqc;`, `\pxql;`, etc. are removed
  - `test_mtext_paragraph_breaks_become_spaces` - Verify `\P` becomes single space, not newline
  - `test_mtext_underline_overline_stripped` - Verify `\L`, `\l`, `\O`, `\o` are removed
  - `test_mtext_color_codes_stripped` - Verify `\C...;` codes are removed
  - `test_mtext_complex_formatting_stripped` - Verify complex example like `\pxqc;MENS CASUAL\P PANTS` becomes `MENS CASUAL PANTS`
  - `test_mtext_plain_text_preserved` - Verify MTEXT without formatting codes is unchanged
  - `test_text_entities_unchanged` - Verify TEXT entities still work correctly

### Step 6: Run validation commands
- Run all tests to ensure no regressions
- Run type checking
- Run linting

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python app/tests/assets/create_mtext_formatting_test.py` - Generate the MTEXT formatting test fixture
- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to validate the bug is fixed
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run mypy app/` - Verify type safety
- `uv run ruff check app/` - Verify no linting issues

## Notes
- The ezdxf library's `plain_text(split=False, fast=True)` method is optimized and handles all common MTEXT formatting codes
- The `fast=True` parameter is appropriate since we're primarily working with DXF files created by modern CAD applications
- Paragraph breaks (`\P`) are converted to newlines by `plain_text()`, but we need spaces for Excel cell readability, hence the post-processing
- TEXT entities use `entity.dxf.text` which already returns plain text - no changes needed
- This fix applies to both `annotation_data` and `color_analysis_data` extraction
