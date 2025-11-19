# Bug: Layer Analysis Sheet Missing Empty Layers

## Bug Description
The Layer Analysis sheet in the Excel output only displays layers that contain entities in modelspace. Layers that are defined in the DXF/DWG layer table but have no entities are completely omitted from the report.

**Expected behavior:** All layers defined in the drawing's layer table should appear in the Layer Analysis sheet, with 0 counts for layers without entities.

**Actual behavior:** Only layers with at least one entity in modelspace are shown (6 layers instead of 59 layers in the test file).

**Example from test file `251102-WV10-20-1011.dxf`:**
- AutoCAD shows 59 total layers defined in the layer table
- Excel output only shows 6 layers (those with entities)
- Missing layers: Defpoints, Fixture Name, FPAnnotations, FPAnnotationStamp, FPProfileCode, FPJig, and 47 XERF-20-1011-240624|* layers

## Problem Statement
The extractor only counts layers when iterating through modelspace entities (line 186 in `app/core/extractor.py`). Layers defined in the layer table but without entities are never added to `layer_entity_counts`, causing them to be excluded from the Layer Analysis sheet.

## Solution Statement
Modify the extraction logic to:
1. Initialize all layers from the layer table in `layer_entity_counts` with a count of 0
2. Initialize all layers in `layer_block_insertion_counts` with a count of 0
3. Increment counts as entities are encountered (existing behavior)
4. This ensures all defined layers appear in the output, even if they have no entities

## Steps to Reproduce
1. Extract blocks from `app/tests/assets/251102-WV10-20-1011.dxf`
2. Open the generated Excel file
3. Navigate to the "Layer Analysis" sheet
4. Observe only 6 layers are shown instead of the 59 layers defined in AutoCAD

## Root Cause Analysis
**Location:** `app/core/extractor.py:186`

The layer counting logic only increments `layer_entity_counts` when processing entities:
```python
for entity in msp:
    layer_name = entity.dxf.layer
    layer_entity_counts[layer_name] = layer_entity_counts.get(layer_name, 0) + 1
```

Layers without entities are never initialized or added to the dictionary. The code doesn't access the DXF layer table (`doc.layers`) which contains all defined layers regardless of usage.

**Why this matters:**
- Users expect to see all layers defined in their CAD file for comprehensive analysis
- Empty layers may indicate unused layers that could be cleaned up
- Layer structure is important for CAD file organization and auditing

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py:130-186` - Initialize layer dictionaries from layer table before processing entities
- `app/tests/core/test_extractor.py` - Add test to verify all layers from layer table appear in results, including empty layers
- `app/tests/assets/251102-WV10-20-1011.dxf` - Use this file for testing (has 59 layers, only 6 with entities)

## Step by Step Tasks

### 1. Update layer extraction logic to include all layers from layer table
- Modify `extract_blocks()` in `app/core/extractor.py` after line 142 (after initializing empty dicts)
- Add code to iterate through `doc.layers` and initialize all layers in both `layer_entity_counts` and `layer_block_insertion_counts` with count of 0
- Use layer name from `layer.dxf.name`
- Skip system layers that start with "*" (modelspace/paperspace internal layers)
- Existing entity processing logic (lines 176-220) will increment counts for layers with entities

### 2. Add test to verify empty layers are included
- Add new test function `test_extract_blocks_includes_empty_layers()` to `app/tests/core/test_extractor.py`
- Use the test file `app/tests/assets/251102-WV10-20-1011.dxf` which has many empty layers
- Assert that `layer_entity_counts` includes layers with 0 entities
- Assert that all non-system layers from the layer table are present in the result
- Verify specific empty layers like "Defpoints", "Fixture Name", "FPProfileCode" appear with 0 count

### 3. Run validation commands
- Execute all validation commands listed below to ensure the fix works correctly
- Verify no existing tests are broken
- Confirm the bug is resolved with the test file

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python -c "from app.core.extractor import extract_blocks; r = extract_blocks('app/tests/assets/251102-WV10-20-1011.dxf'); print(f'Layers: {len(r[\"layer_entity_counts\"])}'); assert len(r['layer_entity_counts']) > 50, 'Should have 50+ layers'; print('✓ All layers included')"` - Verify extraction includes all layers
- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests (ensure no regressions)
- `uv run pytest app/tests/ -v` - Run all tests to verify zero regressions
- `uv run mypy app/` - Type check to ensure no type errors
- `bash scripts/start.sh` - Manual test: extract the test file and verify Excel shows all 59 layers

## Notes
- The fix should be minimal: just initialize layers from `doc.layers` before processing entities
- Existing increment logic will still work correctly
- Empty layers will naturally have 0 for both `layer_entity_counts` and `layer_block_insertion_counts`
- System layers starting with "*" (like "*Model_Space", "*Paper_Space") should be skipped as they're internal
- This provides better visibility into CAD file structure and helps identify unused layers
