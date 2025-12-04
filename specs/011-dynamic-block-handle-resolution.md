# Bug: Dynamic Block Handle Resolution Missing

## Bug Description
Dynamic blocks from real AutoCAD DWG-to-DXF conversions are not being extracted because the extractor only looks for the original block name as a direct string (tag code 1000) in XDATA, but AutoCAD actually stores a **handle reference** (tag code 1005) that points to the original block definition. The current implementation works with the test fixtures (which artificially store names directly), but fails with actual AutoCAD-exported DXF files.

**Symptoms:**
- Dynamic blocks (*U blocks) from real AutoCAD DXF files appear as "unresolved" in extraction_issues
- The resolved block name is never found even when AcDbBlockRepBTag XDATA exists
- Test fixtures pass but real-world files fail

**Expected behavior:**
- Dynamic blocks should resolve to their original names by following the handle reference in XDATA tag code 1005
- The extractor should support both direct name storage (tag 1000) and handle reference storage (tag 1005)

**Actual behavior:**
- Only tag code 1000 (direct string) is checked
- Tag code 1005 (handle reference) is ignored
- Real AutoCAD dynamic blocks remain unresolved

## Problem Statement
The `_resolve_dynamic_block_name()` function in `app/core/extractor.py` only checks for tag code 1000 (string data) when looking for the original block name in AcDbBlockRepBTag XDATA. However, AutoCAD stores the original block name as a **handle reference** in tag code 1005, which must be resolved through the document's entity database to retrieve the actual block name.

## Solution Statement
Enhance `_resolve_dynamic_block_name()` to also check for tag code 1005 (database handle) and resolve it through `doc.entitydb[handle]` to get the original block definition's name. This requires passing the document object to the function. The function should:
1. First try tag code 1000 (direct string) for compatibility with current test fixtures
2. Then try tag code 1005 (handle reference) for real AutoCAD files
3. Resolve the handle to get the block record and extract its name

## Steps to Reproduce
1. Export a DWG file with dynamic blocks to DXF format using AutoCAD
2. Run the extractor on the resulting DXF file
3. Observe that dynamic blocks appear in extraction_issues as unresolved
4. The blocks are missing from block_counts under their original names

## Root Cause Analysis
The `_resolve_dynamic_block_name()` function at `app/core/extractor.py:439-530` only checks for group code 1000:

```python
for tag in rep_btag_data:
    # Group code 1000 contains string data (the original block name)
    if hasattr(tag, "code") and tag.code == 1000:  # <-- BUG: Only checks 1000
        original_name = tag.value
```

According to AutoCAD DXF format and ezdxf documentation:
- **Tag code 1000**: ASCII string (used in test fixtures)
- **Tag code 1005**: Database handle - hard-owned handle (used by real AutoCAD)

AutoCAD stores a handle reference in tag 1005 that points to the original block's block_record. To resolve this:
```python
# Pseudocode for correct resolution
handle = tag.value  # e.g., "2F" (hex handle)
original_block_record = doc.entitydb[handle]
original_name = original_block_record.dxf.name
```

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py` - Contains the `_resolve_dynamic_block_name()` function that needs to be enhanced to handle tag code 1005 (handle resolution). Also contains `extract_blocks()` which calls this function and will need to pass the document object.

- `app/tests/core/extractor/test_extractor_dynamic.py` - Contains existing dynamic block tests. New tests needed for handle resolution.

- `app/tests/assets/create_dynamic_block_test.py` - Test fixture generator. May need enhancement to create fixtures with handle-based XDATA (tag 1005) to properly test the fix.

### New Files
- `app/tests/assets/dynamic_block_handle_test.dxf` - New test fixture with handle-based XDATA (tag code 1005) to simulate real AutoCAD exports

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Function Signature to Accept Document
- Modify `_resolve_dynamic_block_name()` signature to accept the ezdxf `Drawing` document as a parameter
- Update the docstring to document the new parameter
- The function signature should change from:
  ```python
  def _resolve_dynamic_block_name(block_record: Any, block_name: str | None = None) -> str | None:
  ```
  to:
  ```python
  def _resolve_dynamic_block_name(block_record: Any, doc: Drawing, block_name: str | None = None) -> str | None:
  ```

### 2. Add Handle Resolution Logic for Tag Code 1005
- In the `_resolve_dynamic_block_name()` function, after checking for tag code 1000, add logic to check for tag code 1005
- When tag code 1005 is found:
  - Get the handle value (hex string or integer)
  - Look up the entity in `doc.entitydb` using the handle
  - Get the name from the resolved entity's `dxf.name` attribute
  - Return the resolved name if valid
- Handle errors gracefully (invalid handle, entity not found, etc.)

### 3. Update All Callers of _resolve_dynamic_block_name
- In `extract_blocks()`, update both calls to `_resolve_dynamic_block_name()` (around lines 709 and 732) to pass the `doc` parameter
- The calls should change from:
  ```python
  resolved_name = _resolve_dynamic_block_name(block_record, block_name)
  ```
  to:
  ```python
  resolved_name = _resolve_dynamic_block_name(block_record, doc, block_name)
  ```

### 4. Create Test Fixture Generator for Handle-Based XDATA
- Create `app/tests/assets/create_dynamic_block_handle_test.py` that:
  - Creates a DXF file with anonymous blocks (*U1, *U2)
  - Creates corresponding original block definitions (e.g., DOOR_HANDLE_TEST)
  - Attaches AcDbBlockRepBTag XDATA with tag code 1005 containing the handle to the original block
  - Creates INSERT entities referencing the anonymous blocks
- Run the script to generate the test fixture

### 5. Add Unit Tests for Handle Resolution
- Add new test class `TestDynamicBlockHandleResolution` in `app/tests/core/extractor/test_extractor_dynamic.py`:
  - `test_handle_resolution_with_tag_1005()` - Verify blocks with handle XDATA are resolved
  - `test_handle_resolution_invalid_handle()` - Verify graceful handling of invalid handles
  - `test_handle_resolution_fallback_to_tag_1000()` - Verify tag 1000 still works (backwards compatibility)

### 6. Run Validation Commands
Execute validation commands to ensure the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_dynamic.py -v` - Run all dynamic block tests including new handle resolution tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests to ensure no regressions
- `uv run pytest app/tests/ -v` - Run complete test suite with zero failures
- `uv run mypy app/` - Run type checking with zero errors
- `uv run ruff check app/` - Run linting with zero errors

## Notes

- **DXF Group Code Reference:**
  - 1000: ASCII string (up to 255 chars)
  - 1005: Database handle (hard-owned handle stored as hex string)

- **ezdxf Handle Resolution:**
  - `doc.entitydb` is a dictionary-like object that maps handles to entities
  - Handles may be stored as hex strings (e.g., "2F") or integers
  - Use `doc.entitydb.get(handle)` for safe access that returns None on missing handles

- **Backwards Compatibility:**
  - The fix must maintain compatibility with existing test fixtures that use tag code 1000
  - Check tag code 1000 first, then fall back to tag code 1005

- **Error Handling:**
  - Invalid handles should be logged at debug level and treated as unresolved
  - Missing entities should not raise exceptions

- **Testing Note:**
  - Creating a realistic test fixture with proper handle references requires understanding ezdxf's internal handle management
  - The fixture generator must ensure the handle in XDATA actually points to a valid block_record
