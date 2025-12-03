# Chore: Fix Dynamic Block Extraction from DXF Files

## Chore Description
Dynamic blocks from AutoCAD DWG files are not being extracted when saved as DXF because:

1. **AutoCAD DWG to DXF Conversion Behavior**: When AutoCAD saves a DWG with dynamic blocks to DXF format, it converts dynamic block definitions to anonymous blocks (names starting with `*U`, like `*U1`, `*U2`, etc.)
2. **XDATA Preservation**: The original block name is preserved in XDATA on the block record under the application ID `AcDbBlockRepBTag`
3. **Current Extractor Behavior**: The extractor at `extractor.py:563` skips all blocks starting with `*`, which includes these converted dynamic blocks

**Solution Requirements:**
1. Modify the extractor to check anonymous blocks (`*U*`) for `AcDbBlockRepBTag` XDATA and resolve the original block name
2. Add a new "Extraction Issues" Excel sheet to report unresolved anonymous blocks (anonymous blocks without resolvable original names)

## Relevant Files
Use these files to resolve the chore:

- `app/core/extractor.py` - Contains the main extraction logic
  - Line 560-564: Block definition loop that skips anonymous blocks
  - Line 661-732: INSERT entity processing with XDATA extraction
  - Need to add logic to resolve original names from XDATA

- `app/core/excel_writer.py` - Contains Excel generation logic
  - Need to add new `_create_extraction_issues_sheet()` function
  - Need to update `write_excel()` to include new sheet and formatting

- `app/core/excel_formatting.py` - Contains Excel formatting utilities
  - Need to add `_format_extraction_issues_sheet()` function

- `app/core/constants.py` - Contains Excel column/sheet constants
  - Need to add new sheet name constant
  - Need to add new column constants for Extraction Issues sheet

- `app/core/types.py` - Contains TypedDict definitions
  - Need to add `ExtractionIssue` TypedDict for issue tracking

### New Files
- `app/tests/assets/create_dynamic_block_test.py` - Script to create test DXF with dynamic block simulation
- `app/tests/assets/dynamic_block_test.dxf` - Test fixture with anonymous blocks containing XDATA

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add New Type Definition for Extraction Issues

Update `app/core/types.py`:
- Add `ExtractionIssue` TypedDict with fields:
  - `issue_type: str` - Type of issue (e.g., "Unresolved Anonymous Block")
  - `block_name: str` - The anonymous block name (e.g., `*U1`)
  - `layer_name: str` - Layer where the block was inserted
  - `insertion_count: int` - Number of times this block was inserted
  - `details: str` - Additional context (e.g., "No AcDbBlockRepBTag XDATA found")

### 2. Add Constants for New Excel Sheet

Update `app/core/constants.py`:
- Add `EXCEL_SHEET_EXTRACTION_ISSUES: str = "Extraction Issues"`
- Add column constants:
  - `EXCEL_COLUMN_ISSUE_TYPE: str = "issue_type"`
  - `EXCEL_COLUMN_ISSUE_BLOCK_NAME: str = "issue_block_name"`
  - `EXCEL_COLUMN_ISSUE_LAYER_NAME: str = "issue_layer_name"`
  - `EXCEL_COLUMN_ISSUE_INSERTION_COUNT: str = "issue_insertion_count"`
  - `EXCEL_COLUMN_ISSUE_DETAILS: str = "issue_details"`

### 3. Update ExtractionResult Type

Update `app/core/extractor.py`:
- Add `extraction_issues: list[ExtractionIssue]` to `ExtractionResult` TypedDict
- Import `ExtractionIssue` from types module

### 4. Create Dynamic Block Resolution Function

Add new helper function in `app/core/extractor.py`:
```python
def _resolve_dynamic_block_name(block_def: Any) -> str | None:
    """
    Resolve the original name for a dynamic block from XDATA.

    AutoCAD stores the original block name in XDATA under the
    'AcDbBlockRepBTag' application ID when converting dynamic blocks
    from DWG to DXF format.

    Args:
        block_def: The ezdxf block definition to check

    Returns:
        The original block name if found in XDATA, None otherwise
    """
```
- Access the block record's XDATA looking for `AcDbBlockRepBTag`
- Extract the original block name from the XDATA (typically stored as string in group code 1000)
- Return the resolved name or None if not found

### 5. Modify Block Definition Processing

Update the block definition loop in `extract_blocks()` (around line 560-564):
- Instead of completely skipping `*U` blocks, check for `AcDbBlockRepBTag` XDATA
- If XDATA contains original name, use that name for the block instead
- Track the mapping from anonymous name to resolved name for INSERT processing
- If XDATA is not found or doesn't contain a usable name, track as an extraction issue

### 6. Modify INSERT Entity Processing

Update the INSERT processing section (around line 661-732):
- When processing INSERT entities, check if the block name is an anonymous block (`*U*`)
- If so, look up the resolved name from the mapping created in step 5
- Use the resolved name for all block counting and tracking
- If no resolved name exists, increment the unresolved anonymous block count for the Extraction Issues sheet

### 7. Initialize and Populate Extraction Issues

In `extract_blocks()`:
- Initialize `extraction_issues: list[ExtractionIssue] = []` with other result dictionaries
- After processing, create issue records for each unresolved anonymous block
- Include the issue in the returned `ExtractionResult`

### 8. Create Extraction Issues Sheet Writer

Add new function in `app/core/excel_writer.py`:
```python
def _create_extraction_issues_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Extraction Issues sheet with unresolved anonymous blocks."""
```
- Extract `extraction_issues` from data
- Create DataFrame with columns: Issue Type, Block Name, Layer Name, Insertion Count, Details
- Sort by insertion count descending
- Write to Excel with proper formatting

### 9. Update write_excel Function

Update `write_excel()` in `app/core/excel_writer.py`:
- Add call to `_create_extraction_issues_sheet(extraction_data, writer)` after other sheets
- Add call to `_format_extraction_issues_sheet(wb)` in the formatting section

### 10. Create Extraction Issues Sheet Formatter

Add new function in `app/core/excel_formatting.py`:
```python
def _format_extraction_issues_sheet(wb: Workbook) -> None:
    """Apply formatting to the Extraction Issues sheet."""
```
- Apply auto-filter
- Freeze header row
- Set appropriate column widths (30, 30, 25, 20, 50 for the 5 columns)
- Enable text wrapping on header row
- Apply yellow background fill to all data rows to highlight issues

### 11. Create Test Fixture Generator Script

Create `app/tests/assets/create_dynamic_block_test.py`:
- Create a DXF file that simulates dynamic blocks by:
  - Creating anonymous blocks (`*U1`, `*U2`) with geometry
  - Attaching `AcDbBlockRepBTag` XDATA with original names like "DOOR_DYNAMIC", "WINDOW_DYNAMIC"
  - Creating one anonymous block without XDATA for testing the Extraction Issues sheet
  - Inserting these blocks multiple times on different layers
- Run the script to generate `dynamic_block_test.dxf`

### 12. Add Unit Tests for Dynamic Block Resolution

Add tests in `app/tests/core/test_extractor.py`:
- `test_resolve_dynamic_block_name_with_xdata()` - Verify XDATA resolution works
- `test_resolve_dynamic_block_name_without_xdata()` - Verify None returned when no XDATA
- `test_extract_dynamic_blocks_resolved()` - Verify dynamic blocks are counted under resolved names
- `test_extract_unresolved_anonymous_blocks_reported()` - Verify unresolved blocks appear in extraction_issues

### 13. Add Unit Tests for Extraction Issues Sheet

Add tests in `app/tests/core/test_excel_writer.py`:
- `test_extraction_issues_sheet_created()` - Verify sheet exists in output
- `test_extraction_issues_sheet_contains_unresolved_blocks()` - Verify issues are written
- `test_extraction_issues_sheet_empty_when_no_issues()` - Verify empty sheet when no issues

### 14. Run Validation Commands

Execute validation commands to ensure no regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to validate dynamic block resolution
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests to validate Extraction Issues sheet
- `uv run pytest app/tests/ -v` - Run complete test suite with zero failures
- `uv run mypy app/` - Run type checking with zero errors
- `uv run ruff check app/` - Run linting with zero errors

## Notes

- **XDATA Access Pattern**: The ezdxf library provides XDATA access through `entity.xdata` which is a dictionary-like object mapping application IDs to tag data. For block records, the XDATA is accessed differently - it may be on the block table record, not the block definition itself. Investigation may be needed to determine the exact location.

- **AcDbBlockRepBTag Format**: The XDATA structure typically contains:
  - Application ID: `AcDbBlockRepBTag`
  - Group code 1000: String containing the original block name

- **Anonymous Block Patterns**: AutoCAD uses several anonymous block patterns:
  - `*U<n>` - Dynamic block instances
  - `*D<n>` - Dimension blocks
  - `*X<n>` - Hatch pattern blocks
  - `*Model_Space` and `*Paper_Space` - Space blocks

  This chore focuses on `*U` blocks which represent dynamic block instances.

- **Backward Compatibility**: The new `extraction_issues` field in `ExtractionResult` should default to an empty list, so existing code that doesn't handle it won't break.

- **Excel Sheet Order**: The Extraction Issues sheet should be the last sheet (Sheet 7) since it contains warnings/issues rather than primary data.
