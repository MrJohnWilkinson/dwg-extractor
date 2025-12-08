# Bug: A$C* Anonymous Block Extraction Missing

## Bug Description
A$C* anonymous blocks (AutoCAD's alternate dynamic block naming convention) are completely excluded from extraction results. Users expect these blocks to appear in all Excel output sheets (Block Counts, Block-Layer, Rotations, Scales, Trimming), but currently they are silently filtered out.

**Symptoms:**
- A$C* blocks do not appear in any Excel sheet
- No indication that these blocks exist in the DXF file
- Block counts are artificially lower than actual insertions

**Expected Behavior:**
- A$C* blocks should be processed like *U blocks
- If XDATA resolves the name → use resolved name
- If XDATA does not resolve → use raw A$C* name directly
- Unresolved A$C* blocks should be tracked in extraction_issues for visibility

**Actual Behavior:**
- A$C* blocks are filtered out at line 664 of extractor.py by the `elif block_name.startswith("*"):` condition
- Note: A$C blocks do NOT start with `*`, they start with `A$C`, so they would actually be processed as regular blocks - but the INSERT entities referencing them may have different behavior

## Problem Statement
The extractor currently has no special handling for `A$C*` anonymous blocks. While `*U` blocks are recognized as dynamic blocks and processed with XDATA resolution, `A$C*` blocks are treated as regular blocks. However, they represent the same concept (anonymous dynamic block instances) and should follow the same resolution logic.

Key findings from analysis:
1. `A$C*` blocks exist in real-world DXF files (e.g., `AS-1922_XXXX-SSL-XXX-XX-DR-U-0200.dxf`)
2. Some `A$C*` blocks have `AcDbDynamicBlockTrueName` XDATA but it resolves to itself (not useful)
3. Most `A$C*` blocks have no XDATA or only `AcDbDynamicBlockGUID`
4. Unlike `*U` blocks, `A$C*` blocks do NOT use `AcDbBlockRepBTag` for resolution

## Solution Statement
Extend the anonymous block handling logic in `extractor.py` to:

1. **Block Definition Processing (lines 630-695):**
   - Add handling for `A$C*` blocks alongside `*U` blocks
   - Try to resolve using `AcDbBlockRepBTag` first (for consistency)
   - If not found, try `AcDbDynamicBlockTrueName` as fallback
   - If resolved name is same as anonymous name (self-reference), treat as unresolved
   - Store resolved mappings in `anonymous_to_resolved` dict
   - Process unresolved A$C* blocks for geometry analysis (unlike *U which skips them)

2. **INSERT Processing (lines 766-865):**
   - Add handling for `A$C*` INSERT entities alongside `*U`
   - Use resolved name if available, otherwise use raw A$C* name
   - Track unresolved A$C* blocks in extraction_issues

3. **Key Behavioral Difference from *U:**
   - *U blocks: unresolved → skip processing, only track in issues
   - A$C* blocks: unresolved → use raw name for full processing, AND track in issues

## Steps to Reproduce
1. Open a DXF file containing A$C* blocks (e.g., `app/tests/assets/samples/AS-1922_XXXX-SSL-XXX-XX-DR-U-0200.dxf`)
2. Run extraction: `extract_blocks('app/tests/assets/samples/AS-1922_XXXX-SSL-XXX-XX-DR-U-0200.dxf')`
3. Check `result['block_counts']` - no A$C* blocks appear
4. Check `result['extraction_issues']` - no A$C* blocks are tracked

## Root Cause Analysis
The root cause is that `A$C*` blocks are not recognized as a special anonymous block naming convention. The code only handles:
- `*Model_Space` / `*Paper_Space` - system blocks (skipped)
- `*U*` - dynamic block instances (special handling with XDATA resolution)
- `*` prefix - other anonymous blocks (skipped)

`A$C*` blocks do NOT start with `*`, so they fall through to regular block processing. However, the current code processes them as regular named blocks, which means they should already appear in output. Let me re-verify...

**Updated Analysis:**
After re-reading the code, `A$C*` blocks do NOT start with `*`, so they ARE processed as regular blocks currently. The INSERT entity `A$C0c1c4685` found in the sample file would be processed and counted under that name.

The actual issue is:
1. A$C* blocks ARE being extracted (as regular blocks)
2. But users want them RESOLVED to meaningful names if possible
3. And they want unresolved A$C* blocks tracked in extraction_issues for visibility

So the fix is to add A$C* to the anonymous block handling pipeline alongside *U.

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py` - Main extraction logic
  - `_resolve_dynamic_block_name()` - XDATA resolution function (may need enhancement for AcDbDynamicBlockTrueName)
  - `extract_blocks()` - Block definition processing and INSERT handling

- `app/tests/core/extractor/test_extractor_dynamic.py` - Existing dynamic block tests to extend

- `app/tests/assets/samples/AS-1922_XXXX-SSL-XXX-XX-DR-U-0200.dxf` - Real-world sample containing A$C* blocks

### New Files
- `app/tests/assets/create_a_dollar_c_block_test.py` - Script to create test DXF with A$C* blocks
- `app/tests/assets/a_dollar_c_block_test.dxf` - Generated test fixture

## Step by Step Tasks

### Step 1: Create Test Fixture
- Create `app/tests/assets/create_a_dollar_c_block_test.py` script that generates a DXF file with:
  - A$C block with AcDbBlockRepBTag XDATA (resolvable)
  - A$C block with AcDbDynamicBlockTrueName XDATA (self-referencing, treat as unresolved)
  - A$C block with no XDATA (unresolved)
  - Regular named block for comparison
  - INSERT entities on multiple layers for each block type
- Run the script to generate `app/tests/assets/a_dollar_c_block_test.dxf`

### Step 2: Add Helper Function for A$C Detection
- In `app/core/extractor.py`, add a helper function `_is_anonymous_block(block_name: str) -> bool` that returns True for:
  - Names starting with `*U` (existing pattern)
  - Names starting with `A$C` (new pattern)
- This centralizes the anonymous block detection logic

### Step 3: Enhance XDATA Resolution
- Modify `_resolve_dynamic_block_name()` to also check `AcDbDynamicBlockTrueName` as fallback
- Add logic to detect self-referencing names (e.g., `A$C25B30886` -> `A$C25B30886`) and return None for those
- Update docstring to document the enhanced resolution

### Step 4: Update Block Definition Processing
- In `extract_blocks()`, modify the block definition loop (around line 640):
  - Replace `if block_name.startswith("*U"):` with `if _is_anonymous_block(block_name) and not block_name.startswith("*"):`
  - Handle A$C* blocks: try resolution, if resolved use resolved name, if not use raw A$C* name
  - A$C* blocks with raw names should still have geometry analyzed (unlike *U which skips)
  - Store A$C* mappings in `anonymous_to_resolved` dict (for both resolved and unresolved with identity mapping)

### Step 5: Update INSERT Processing
- In `extract_blocks()`, modify the INSERT handling (around line 770):
  - Add check for A$C* blocks similar to *U handling
  - If name in `anonymous_to_resolved` and not self-mapping, use resolved name
  - If unresolved A$C* block, use raw name AND track in `unresolved_anonymous_blocks`
  - Continue with full processing (unlike *U which uses continue)

### Step 6: Update Extraction Issues Tracking
- Ensure A$C* unresolved blocks are added to extraction_issues with appropriate details
- Use issue_type "Unresolved Anonymous Block" for consistency
- Include details about which XDATA was checked

### Step 7: Add Unit Tests
- Add tests to `app/tests/core/extractor/test_extractor_dynamic.py`:
  - `test_a_dollar_c_block_resolution_with_xdata` - Test A$C blocks with resolvable XDATA
  - `test_a_dollar_c_block_unresolved_uses_raw_name` - Test unresolved A$C blocks appear with raw name
  - `test_a_dollar_c_block_unresolved_in_extraction_issues` - Test unresolved tracking
  - `test_a_dollar_c_block_in_block_layer_pairs` - Test A$C blocks appear in block_layer_pairs
  - `test_a_dollar_c_block_in_rotations` - Test A$C blocks appear in rotation data
  - `test_a_dollar_c_block_in_scales` - Test A$C blocks appear in scale data
  - `test_a_dollar_c_block_in_trimming_data` - Test A$C blocks have geometry data

### Step 8: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_dynamic.py -v` - Run dynamic block tests including new A$C tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run complete test suite
- `uv run mypy app/core/extractor.py` - Type check the modified extractor module
- `uv run ruff check app/core/extractor.py` - Lint check the modified file

## Notes
- The naming `A$C*` uses a dollar sign which is valid in Python strings but should be escaped in regex if needed
- Real-world DXF files show A$C blocks use hexadecimal suffixes (e.g., `A$C7F63364D`, `A$C25B30886`)
- Unlike *U blocks, A$C blocks rarely have useful XDATA for resolution - most will use raw names
- This change maintains backwards compatibility - existing *U handling is unchanged
- Out of scope: *D, *X, and other anonymous patterns remain excluded as per requirements
