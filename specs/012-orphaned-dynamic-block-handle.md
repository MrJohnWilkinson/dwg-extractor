# Bug: Orphaned Dynamic Block Handle Not Reported Accurately

## Bug Description
When extracting dynamic blocks from certain DXF files, the extractor reports "No AcDbBlockRepBTag XDATA found" for anonymous blocks that actually DO have XDATA, but whose handle reference points to a non-existent entity in the document. This occurs when the original block definition has been purged or deleted from the file, leaving orphaned dynamic block instances.

**Symptoms:**
- Anonymous blocks (e.g., `*U148`) appear in extraction_issues with incorrect detail message
- The error says "No AcDbBlockRepBTag XDATA found" when XDATA actually exists
- The actual problem is that handle reference in XDATA points to missing block definition

**Expected behavior:**
- Extraction issues should report accurate details: "Handle B0DE5 not found in document (orphaned dynamic block reference)"
- Users should understand that the original block definition is missing, not that XDATA is missing

**Actual behavior:**
- Reports "No AcDbBlockRepBTag XDATA found" which is misleading
- The XDATA exists with handle reference, but the referenced block record doesn't exist

## Problem Statement
The `_resolve_dynamic_block_name()` function in `app/core/extractor.py` correctly finds XDATA and attempts handle resolution (tag code 1005), but when `doc.entitydb.get(handle)` returns `None` (orphaned reference), the function silently returns `None`. The caller then incorrectly assumes no XDATA was found and reports the wrong error message.

## Solution Statement
Enhance `_resolve_dynamic_block_name()` to return not just the resolved name (or None), but also the resolution status. This allows callers to distinguish between:
1. No XDATA found
2. XDATA found with tag 1000 (direct name) - resolved successfully
3. XDATA found with tag 1005 (handle reference) - resolved successfully
4. XDATA found with tag 1005 (handle reference) - **handle not found (orphaned)**

The function will return a tuple `(resolved_name, resolution_details)` where `resolution_details` is a string describing what was found/attempted. Callers can use this to provide accurate extraction issue details.

## Steps to Reproduce
1. Extract blocks from `app/tests/assets/samples/05-02 MASTERTEGNING SPAR SUPERMARKED - 670 M2 - 280525.dxf`
2. Observe extraction_issues for `*U148`, `*U151`, `*U161`
3. Note that all report "No AcDbBlockRepBTag XDATA found"
4. But raw DXF analysis shows these blocks DO have `AcDbBlockRepBTag` XDATA with handle `B0DE5`
5. Handle `B0DE5` does not exist in the document's entitydb (block was purged)

## Root Cause Analysis
In `app/core/extractor.py:506-531`, when processing tag code 1005:

```python
elif hasattr(tag, "code") and tag.code == 1005:
    handle = tag.value
    try:
        original_block_record = doc.entitydb.get(handle)
        if original_block_record is not None:  # <-- When None, falls through silently
            # ... resolution logic
        # No else clause - silent failure!
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug(f"Failed to resolve handle {handle} in AcDbBlockRepBTag: {e}")
```

When `doc.entitydb.get(handle)` returns `None`, the code continues to the next tag without recording that a handle WAS found but couldn't be resolved. The function ultimately returns `None`, indistinguishable from "no XDATA found".

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py` - Contains `_resolve_dynamic_block_name()` which needs to return resolution details, and `extract_blocks()` which needs to use those details for accurate issue reporting.

- `app/tests/core/extractor/test_extractor_dynamic.py` - Add tests for orphaned handle scenarios.

### New Files
- `app/tests/assets/create_orphaned_handle_test.py` - Create a test fixture with orphaned handle reference (XDATA pointing to non-existent block)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Test Fixture for Orphaned Handle Scenario
- Create `app/tests/assets/create_orphaned_handle_test.py` that generates a DXF with:
  - An anonymous block `*U999` with `AcDbBlockRepBTag` XDATA
  - The XDATA contains tag code 1005 with a handle that doesn't exist in the document
  - An INSERT entity referencing `*U999`
- Run the script to generate `app/tests/assets/orphaned_handle_test.dxf`

### 2. Modify _resolve_dynamic_block_name Return Type
- Change function signature to return `tuple[str | None, str]`:
  - First element: resolved name (or None if unresolved)
  - Second element: resolution details string describing what was found/attempted
- Update docstring to document new return type
- Return appropriate detail strings for each scenario:
  - `"No XDATA found"` - when block_record has no xdata
  - `"Resolved from AcDbBlockRepBTag tag 1000"` - direct name resolution
  - `"Resolved from AcDbBlockRepBTag handle {handle}"` - handle resolution success
  - `"Handle {handle} not found in document (orphaned dynamic block)"` - handle not in entitydb
  - `"Resolved from AcDbDynamicBlockTrueName"` - fallback resolution
  - `"Self-referencing XDATA"` - when name equals block_name
  - `"AcDbBlockRepBTag XDATA present but no resolvable data"` - XDATA exists but no 1000/1005 tags

### 3. Update extract_blocks() to Use Resolution Details
- Update both call sites of `_resolve_dynamic_block_name()` (around lines 741 and 764) to handle the new return type
- When creating ExtractionIssue entries (around line 1073), use the resolution details instead of hardcoded messages
- Ensure the details accurately reflect what was found/attempted

### 4. Add Unit Tests for Orphaned Handle Resolution
- Add new test class `TestOrphanedHandleResolution` in `app/tests/core/extractor/test_extractor_dynamic.py`:
  - `test_orphaned_handle_reported_accurately()` - Verify correct detail message for orphaned handle
  - `test_orphaned_handle_in_extraction_issues()` - Verify block appears in extraction_issues
  - `test_orphaned_handle_not_in_block_counts()` - Verify orphaned block not counted normally

### 5. Run Validation Commands
Execute validation commands to ensure the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python -c "from app.core.extractor import extract_blocks; r = extract_blocks('app/tests/assets/samples/05-02 MASTERTEGNING SPAR SUPERMARKED - 670 M2 - 280525.dxf'); print([i for i in r['extraction_issues'] if '*U148' in i['block_name']])"` - Verify *U148 now reports orphaned handle, not "No XDATA found"
- `uv run pytest app/tests/core/extractor/test_extractor_dynamic.py -v` - Run all dynamic block tests including new orphaned handle tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests to ensure no regressions
- `uv run pytest app/tests/ -v` - Run complete test suite with zero failures
- `uv run mypy app/` - Run type checking with zero errors
- `uv run ruff check app/` - Run linting with zero errors

## Notes

- **Orphaned Dynamic Blocks**: These occur when the original block definition is purged from a DWG/DXF file but dynamic block instances remain. The instances still have XDATA with handle references, but those handles point to non-existent entities.

- **Backwards Compatibility**: Existing code that uses `_resolve_dynamic_block_name()` expects it to return `str | None`. Changing to a tuple is a breaking change that requires updating all callers. Since this is an internal function, this is acceptable.

- **Resolution Details Format**: The detail strings should be user-friendly and help diagnose issues. They should mention:
  - What was found (XDATA type, tag codes)
  - What was attempted (handle resolution)
  - Why it failed (handle not in document)

- **Test File Considerations**: Creating a test fixture with an orphaned handle requires manually setting XDATA with a non-existent handle. This is tricky with ezdxf but can be done by writing raw XDATA tags.

- **Real-World Impact**: This bug affects any DXF file where blocks have been purged after inserting dynamic block instances. This is a common scenario when drawings are cleaned up to reduce file size.
