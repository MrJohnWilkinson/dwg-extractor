# Feature: Add Block-Layer Pairs to Block Trimming Analysis Sheet

## Feature Description
Enhance the Block Trimming Analysis sheet to display block-layer pairs instead of unique blocks only. Each unique combination of block name and layer will appear as a separate row with the block's geometry analysis (native dimensions and segments). This enables users to filter block geometry data by layer, making it easier to analyze trimming requirements for blocks on specific layers.

Currently, the Block Trimming Analysis sheet shows one row per unique block with geometry data (native_width, native_height, vertical_segments, horizontal_segments). This feature will expand each block into multiple rows—one for each layer the block appears on—while repeating the same geometry data for filtering purposes.

## User Story
As a CAD file analyst
I want to see block trimming geometry data broken down by layer
So that I can filter and analyze trimming requirements for blocks on specific layers

## Problem Statement
Currently, the Block Trimming Analysis sheet aggregates geometry data at the block level, showing one row per unique block. Users cannot:
- Filter geometry data by specific layers
- Identify which layers contain blocks that need trimming assistance
- Analyze trimming patterns by layer (e.g., "show me all blocks on the FIXTURES layer")
- Cross-reference block-layer pairs between Block Counts and Block Trimming Analysis sheets

For example, a SHELF_4FT block might appear on both FIXTURES and EQUIPMENT layers. The current sheet only shows one row with geometry, but users cannot filter to see "only FIXTURES blocks" or "only EQUIPMENT blocks" for their trimming analysis.

## Solution Statement
Modify the Excel generation logic to create block-layer pairs in the Block Trimming Analysis sheet:

1. **Data Source**: Use the existing `block_layer_pairs` dictionary (already available in ExtractionResult) to iterate through all block-layer combinations
2. **Geometry Data**: For each block-layer pair, look up the block's geometry from `block_trimming_data` (which remains block-level since geometry is defined at the block definition level, not per insertion)
3. **Excel Structure**: Add `block_layer_name` column to the Block Trimming Analysis sheet, creating one row per block-layer pair
4. **Data Repetition**: The same geometry data (width, height, segments) repeats for each layer a block appears on—this is intentional to enable layer-based filtering
5. **Column Order**: block_name, block_layer_name, block_native_width, block_native_height, block_vertical_segments, block_horizontal_segments

This approach mirrors the Block Counts sheet pattern (lines 141-164 in excel_writer.py) and requires no changes to the extraction logic.

## Relevant Files
Use these files to implement the feature:

**app/core/excel_writer.py**
- Contains `_create_block_trimming_analysis_sheet()` function (lines 290-332) that currently creates one row per block
- Needs modification to iterate through `block_layer_pairs` instead of `block_trimming_data`
- For each (block_name, layer_name) pair, lookup geometry from `block_trimming_data[block_name]`
- Add `block_layer_name` column between `block_name` and geometry columns
- `_format_block_trimming_analysis_sheet()` (lines 334-349) needs column width adjustment for the new layer column

**app/core/constants.py**
- Already defines `EXCEL_COLUMN_BLOCK_LAYER_NAME` (line 27) - can reuse this constant
- No new constants needed since the layer column name already exists from Block Counts sheet

**app/core/extractor.py**
- No changes needed - `block_layer_pairs` already exists in ExtractionResult (line 301)
- `block_trimming_data` already exists in ExtractionResult (line 306)
- Both data structures are already populated during extraction

**app_docs/005-field-naming-convention.md**
- Documents the field naming convention
- `block_layer_name` already follows the established pattern (domain: block, attribute: layer_name)

**app/tests/core/test_excel_writer.py**
- Contains Excel generation tests
- Needs new tests to validate block-layer pairs in Block Trimming Analysis sheet
- Already has patterns for testing multi-column sheets with sorting and filtering

### New Files
No new files needed. All changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
No foundational changes needed. All required data structures (`block_layer_pairs` and `block_trimming_data`) and constants (`EXCEL_COLUMN_BLOCK_LAYER_NAME`) already exist from previous features.

### Phase 2: Core Implementation
Modify `_create_block_trimming_analysis_sheet()` to iterate through block-layer pairs and look up geometry data for each pair:
1. Change iteration source from `block_trimming_data` to `block_layer_pairs`
2. For each (block_name, layer_name) pair, fetch geometry from `block_trimming_data[block_name]`
3. Add `block_layer_name` column to the DataFrame
4. Handle edge case: blocks in `block_layer_pairs` but not in `block_trimming_data` (anonymous blocks, modelspace, etc.)

### Phase 3: Integration
Update Excel formatting and column structure:
1. Import `EXCEL_COLUMN_BLOCK_LAYER_NAME` constant in excel_writer.py
2. Update column order: block_name, block_layer_name, geometry columns
3. Adjust column widths in `_format_block_trimming_analysis_sheet()` for the new 6-column layout
4. Update docstrings to reflect block-layer pair structure
5. Maintain alphabetical sorting by block_name (existing behavior)

## Step by Step Tasks

### 1. Update Excel Sheet Creation Logic
- Modify `_create_block_trimming_analysis_sheet()` in excel_writer.py to use `block_layer_pairs` as iteration source
- Import `EXCEL_COLUMN_BLOCK_LAYER_NAME` at the top of excel_writer.py (add to existing imports from constants)
- Change iteration: `for (block_name, layer_name), _insertion_count in data['block_layer_pairs'].items()`
- Look up geometry: `geometry_data = block_trimming_data.get(block_name)` (use .get() to handle missing blocks gracefully)
- Skip pairs where block has no geometry data (anonymous blocks, etc.): `if geometry_data is None: continue`
- Build rows with 6 columns: block_name, block_layer_name, native_width, native_height, vertical_segments, horizontal_segments
- Update empty DataFrame case to include block_layer_name column header
- Update function docstring to reflect block-layer pair structure

### 2. Update Excel Formatting
- Modify `_format_block_trimming_analysis_sheet()` to adjust column widths for 6 columns instead of 5
- Set column widths: A=30 (block_name), B=25 (block_layer_name), C=20 (native_width), D=20 (native_height), E=40 (vertical_segments), F=40 (horizontal_segments)
- Column B width matches the layer column width from Block Counts sheet (25 characters)
- Update function docstring if needed

### 3. Write Unit Tests for Excel Generation
- Add test `test_block_trimming_analysis_has_layer_column()` in test_excel_writer.py
- Verify Block Trimming Analysis sheet has block_layer_name column in position 2 (B column)
- Add test `test_block_trimming_analysis_block_layer_pairs()` to verify:
  - Rows contain block-layer pairs (not just unique blocks)
  - Same block on multiple layers appears as multiple rows
  - Geometry data is correctly repeated for each layer
  - Blocks without geometry data are skipped gracefully
- Add test `test_block_trimming_analysis_empty_data()` to verify empty block_layer_pairs creates sheet with 6 column headers
- Add test `test_block_trimming_analysis_column_widths()` to verify all 6 columns have appropriate widths

### 4. Integration Testing with Real Files
- Run extraction on app/tests/assets/sample_drawing.dxf
- Manually inspect Excel output Block Trimming Analysis sheet
- Verify block_layer_name column appears between block_name and geometry columns
- Verify same block on different layers appears as separate rows with identical geometry
- Verify sorting by block_name is maintained
- Verify auto-filter works on all 6 columns

### 5. Validation - Run All Tests
- Execute `uv run pytest app/tests/core/test_excel_writer.py::test_block_trimming_analysis_has_layer_column -v` to validate new test
- Execute `uv run pytest app/tests/core/test_excel_writer.py::test_block_trimming_analysis_block_layer_pairs -v` to validate block-layer pair logic
- Execute `uv run pytest app/tests/core/test_excel_writer.py -v` to validate all Excel writer tests pass
- Execute `uv run pytest app/tests/ -v` to run full test suite and ensure zero regressions
- Execute `uv run mypy app/` to verify type checking passes
- Verify all existing tests pass without modification

### 6. End-to-End Validation
- Execute `bash scripts/start.sh` to launch the GUI application
- Select app/tests/assets/Supermarket-2020.dwg (or another test file with multiple layers)
- Click Extract button
- Verify Excel file opens automatically
- Verify Block Trimming Analysis sheet shows block-layer pairs with 6 columns
- Verify data is correctly sorted by block_name alphabetically
- Verify auto-filter allows filtering by layer name
- Verify Block Counts, Layer Analysis, and Entity Summary sheets remain unchanged
- Close application and verify no errors in logs

## Testing Strategy

### Unit Tests

**Excel Writer Tests (test_excel_writer.py)**
- `test_block_trimming_analysis_has_layer_column()`: Verify Block Trimming Analysis sheet has block_layer_name column in correct position
- `test_block_trimming_analysis_block_layer_pairs()`: Verify rows expand to block-layer pairs with geometry data repeated
- `test_block_trimming_analysis_same_block_multiple_layers()`: Verify same block on 3 layers creates 3 rows with identical geometry
- `test_block_trimming_analysis_empty_data()`: Verify empty block_layer_pairs creates sheet with 6 column headers only
- `test_block_trimming_analysis_column_widths()`: Verify all 6 columns have appropriate widths (A=30, B=25, C=20, D=20, E=40, F=40)
- `test_block_trimming_analysis_missing_geometry()`: Verify blocks in block_layer_pairs but not in block_trimming_data are skipped gracefully

### Integration Tests

**Full Pipeline Test**
- Load Supermarket-2020.dwg → extract → generate Excel → verify Block Trimming Analysis sheet
- Verify sheet has correct number of rows (sum of all block-layer pairs that have geometry data)
- Verify same block on multiple layers appears as multiple rows with identical geometry
- Verify blocks without geometry (anonymous blocks) are excluded

**Cross-Sheet Validation**
- Verify Block Counts and Block Trimming Analysis sheets have matching block-layer pairs
- Verify every block-layer pair in Block Trimming Analysis also appears in Block Counts (subset relationship)
- Verify blocks in Block Counts without geometry don't appear in Block Trimming Analysis

### Edge Cases

**Empty Data**
- File with no blocks → block_layer_pairs is empty → Block Trimming Analysis sheet has 6 column headers only

**Single Layer**
- All blocks on layer "0" → verify block_layer_name column shows "0" for all rows

**Multiple Layers per Block**
- SHELF_4FT on FIXTURES (5 insertions), SHELF_4FT on EQUIPMENT (3 insertions) → should create 2 rows with identical geometry → verify both rows exist with correct layer names

**Anonymous Blocks**
- Anonymous blocks (*U123, *D45) in block_layer_pairs but not in block_trimming_data → verify skipped gracefully with no errors

**Blocks Without Geometry**
- Block definition exists but has no geometric entities → bounding box is (0,0,0,0) → verify row appears with zeros for dimensions

**Special Characters in Layer Names**
- Layer names with spaces, hyphens, underscores → verify proper handling in Excel cells

### Playwright MCP Tests

**GUI Workflow Test**
- Launch app → select Supermarket-2020.dwg → extract → verify Block Trimming Analysis sheet has 6 columns
- Verify block_layer_name column appears in correct position (B column, between block_name and geometry)
- Verify data is readable and properly formatted
- Verify auto-filter works on all 6 columns, especially filtering by layer_name

**Multi-Sheet Validation**
- Verify Block Counts, Layer Analysis, and Entity Summary sheets are unaffected by changes
- Verify all 4 sheets are present in output workbook
- Verify sheet names remain consistent

**Filter Functionality**
- Open Excel → navigate to Block Trimming Analysis → apply filter on block_layer_name column
- Verify filtering by layer name (e.g., "FIXTURES") shows only rows for that layer
- Verify geometry data is correctly displayed for filtered rows

## Acceptance Criteria

1. **Excel Output Structure**
   - Block Trimming Analysis sheet displays 6 columns: block_name, block_layer_name, block_native_width, block_native_height, block_vertical_segments, block_horizontal_segments
   - Column order: block_name (A), block_layer_name (B), geometry columns (C-F)
   - Each row represents a unique block-layer pair with geometry data

2. **Data Expansion**
   - Same block on N layers appears as N separate rows
   - Geometry data (width, height, segments) repeats identically for each layer a block appears on
   - Blocks without geometry data (anonymous blocks, no entities) are excluded gracefully

3. **Formatting**
   - Rows are sorted by block_name alphabetically (maintain existing sort behavior)
   - Auto-filter is applied to all 6 columns
   - Column widths are appropriate: A=30, B=25, C=20, D=20, E=40, F=40

4. **Data Integrity**
   - Block-layer pairs in Block Trimming Analysis are a subset of Block Counts (only pairs with geometry)
   - Geometry data matches the block definition (no per-layer variation since geometry is defined at block level)
   - Empty files produce empty block_layer_pairs and Excel sheet with 6 column headers only

5. **Filtering Capability**
   - Users can filter by block_layer_name to see geometry for blocks on specific layers
   - Auto-filter dropdown works correctly on all columns
   - Filter results show correct geometry data for selected layer

6. **Type Safety**
   - No new type definitions needed (reusing existing constants and structures)
   - mypy passes with zero errors

7. **Testing**
   - All new unit tests pass
   - All existing tests pass (zero regressions)
   - Test coverage includes edge cases (empty data, single layer, multiple layers, missing geometry)

8. **Code Quality**
   - Field naming follows app_docs/005-field-naming-convention.md (reusing EXCEL_COLUMN_BLOCK_LAYER_NAME)
   - Docstrings updated to reflect block-layer pair structure
   - Constants used instead of magic strings
   - Code mirrors Block Counts sheet pattern for consistency

9. **User Experience**
   - GUI workflow unchanged (browse → extract → auto-open Excel)
   - Excel file opens successfully with updated Block Trimming Analysis structure
   - Data is easily readable and filterable by layer
   - No breaking changes to existing sheets (Block Counts, Layer Analysis, Entity Summary)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate Excel writer tests pass with new Block Trimming Analysis structure
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage includes new code
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI and manually test extraction with Supermarket-2020.dwg to verify Excel output has block-layer pairs in Block Trimming Analysis sheet

## Notes

### Field Naming Convention Compliance
The feature reuses the existing `block_layer_name` constant from Block Counts sheet, ensuring consistency:
- `block_layer_name` - follows {domain}_{attribute} pattern from app_docs/005-field-naming-convention.md
- Domain: `block` (the block-layer pair is part of the block domain)
- Attribute: `layer_name` (the identifier of the layer)
- Singular form because it represents a single layer per row (not a collection)

### Design Rationale: Geometry Data Repetition
The same geometry data repeats for each layer a block appears on. This is intentional:
- **Filtering**: Users can filter by layer to see geometry for blocks on specific layers
- **Cross-referencing**: Block-layer pairs match between Block Counts and Block Trimming Analysis sheets
- **Excel UX**: Users expect to see complete information in each row after filtering (not missing data)
- **Simplicity**: No need for VLOOKUP formulas or pivot tables to cross-reference data

### No Extraction Changes
This feature requires ZERO changes to extractor.py because:
- `block_layer_pairs` already exists (added in feature 003)
- `block_trimming_data` already exists (added in feature 005)
- Both are already populated during extraction
- Changes are Excel generation only (excel_writer.py)

### Pattern Consistency
This implementation mirrors the Block Counts sheet pattern:
- Block Counts: iterates through `block_layer_pairs`, looks up `block_entities[block_name]` for each pair
- Block Trimming Analysis (new): iterates through `block_layer_pairs`, looks up `block_trimming_data[block_name]` for each pair
- Same structure, same logic, different data lookups

### Performance Considerations
- No performance impact on extraction (no changes to extractor.py)
- Minimal Excel generation impact (same iteration pattern as Block Counts sheet)
- Memory impact negligible (geometry data is small: 4 numbers + 2 lists per block)
- Excel file size increases slightly (more rows in Block Trimming Analysis) but remains manageable

### Future Enhancements
This feature enables additional layer-based analysis:
- Layer-specific trimming reports (e.g., "all FIXTURES blocks need trimming at 50mm intervals")
- Cross-layer geometry comparison (same block, different layers, verify geometry matches)
- Layer-based pivot tables showing block distribution with geometry constraints

### Alternative Considered: Keep Current Structure
An alternative would be to keep Block Trimming Analysis as-is (one row per block) and add a separate "Block-Layer Geometry" sheet. This was rejected because:
- Data duplication (geometry repeated across sheets)
- User confusion (which sheet to use for trimming analysis?)
- Inconsistency (Block Counts has layer breakdown but Block Trimming Analysis doesn't)
- Current approach enables filtering which is the primary user benefit
