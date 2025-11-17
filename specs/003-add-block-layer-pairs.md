# Feature: Block-Layer Pair Extraction

## Feature Description
Enhance the Block Counts sheet to display block-layer pairs instead of aggregated block counts. Each unique combination of block name and layer will appear as a separate row, showing how many times that specific block was inserted on that specific layer. This provides granular visibility into block placement across different CAD layers, enabling users to understand the spatial organization and layer-based distribution of blocks in their drawings.

The current implementation aggregates all insertions of a block across all layers into a single count. This feature will break down those aggregated counts by layer, creating separate rows for each block-layer combination.

## User Story
As a CAD file analyst
I want to see block insertion counts broken down by layer
So that I can understand which layers contain specific blocks and identify layer-based patterns in block placement

## Problem Statement
Currently, the Block Counts sheet aggregates all block insertions across all layers, showing only the total count for each block name. Users cannot determine:
- Which layers contain which blocks
- How many times a specific block appears on a specific layer
- Whether blocks are distributed across multiple layers or concentrated on one layer
- Layer-based organization patterns in the drawing

For example, a DOOR block might appear 8 times total, but users can't see that 5 are on the WALLS layer and 3 are on the OPENINGS layer without manually inspecting the CAD file.

## Solution Statement
Modify the extraction and Excel generation pipeline to create block-layer pairs:

1. **Extraction Layer**: Track block name and layer name together during extraction, creating a composite key (block_name, layer_name) with associated counts
2. **Data Structure**: Add a new `block_layer_pairs` dictionary to ExtractionResult: `dict[tuple[str, str], int]` mapping (block_name, layer_name) tuples to insertion counts
3. **Excel Generation**: Update the Block Counts sheet to display three columns (block_name, block_insertion_count, block_layer_name) with one row per block-layer pair, sorted by count descending
4. **Field Naming**: Follow the established naming convention: `block_layer_name` for the layer identifier

This approach maintains backwards compatibility by preserving the existing `block_counts` aggregated data while adding the new granular data.

## Relevant Files
Use these files to implement the feature:

**app/core/extractor.py**
- Contains the `extract_blocks()` function that parses DWG/DXF files
- Defines the `ExtractionResult` TypedDict
- Already iterates through INSERT entities and has access to both `block_name` and `layer_name` (entity.dxf.layer)
- Currently aggregates counts by block_name only - needs to track (block_name, layer_name) pairs

**app/core/excel_writer.py**
- Contains Excel generation logic with sheet creation functions
- `_create_block_counts_sheet()` needs modification to use block-layer pairs instead of aggregated counts
- `_format_block_counts_sheet()` may need column width adjustments for the new layer column
- Already has patterns for creating multi-column sheets with sorting and filtering

**app/core/constants.py**
- Defines all Excel column name constants following the field naming convention
- Needs new constant: `EXCEL_COLUMN_BLOCK_LAYER_NAME`
- Already has the pattern: domain_attribute format (block_name, block_insertion_count, etc.)

**app_docs/005-field-naming-convention.md**
- Documents the field naming convention that must be followed
- Confirms `block_layer_name` follows the pattern (singular for single value, not a collection)
- Provides examples of block domain fields

**app/tests/core/test_extractor.py**
- Contains unit tests for the extractor module
- Needs new tests to validate block-layer pair extraction
- Already has test fixtures (sample_drawing.dxf) that can be used

### New Files
**app/tests/core/test_excel_writer.py**
- Currently exists and contains Excel generation tests
- Will need updates to test the new block-layer pair functionality in the Block Counts sheet

## Implementation Plan

### Phase 1: Foundation
Update the data model and constants to support block-layer pairs:
1. Add `block_layer_pairs: dict[tuple[str, str], int]` field to `ExtractionResult` TypedDict in extractor.py
2. Add `EXCEL_COLUMN_BLOCK_LAYER_NAME` constant to constants.py following the naming convention
3. Update docstrings in ExtractionResult to document the new field structure

### Phase 2: Core Implementation
Modify extraction logic to collect block-layer pairs:
1. Update `extract_blocks()` in extractor.py to populate the `block_layer_pairs` dictionary
2. During INSERT entity iteration, create composite keys: `(block_name, layer_name)`
3. Increment counts for each unique block-layer pair
4. Keep the existing `block_counts` aggregation for backwards compatibility
5. Add logging to report unique block-layer pair counts

### Phase 3: Integration
Update Excel generation to display block-layer pairs:
1. Modify `_create_block_counts_sheet()` to iterate over block_layer_pairs instead of block_counts
2. Create three-column rows: block_name, block_insertion_count, block_layer_name
3. Sort by block_insertion_count descending (maintain existing sort behavior)
4. Update `_format_block_counts_sheet()` to set appropriate column width for the layer column
5. Update docstrings to reflect the new three-column structure

## Step by Step Tasks

### 1. Update Constants
- Add `EXCEL_COLUMN_BLOCK_LAYER_NAME: str = 'block_layer_name'` to constants.py following the field naming convention
- Add inline comment referencing app_docs/005-field-naming-convention.md

### 2. Update ExtractionResult TypedDict
- Add `block_layer_pairs: dict[tuple[str, str], int]` field to ExtractionResult in extractor.py
- Update ExtractionResult docstring to document the block_layer_pairs structure
- Include example in docstring: `{('DOOR', 'WALLS'): 5, ('DOOR', 'OPENINGS'): 3}`

### 3. Implement Block-Layer Pair Extraction
- Initialize `block_layer_pairs: dict[tuple[str, str], int] = {}` in extract_blocks()
- During INSERT entity processing, create composite key: `pair_key = (block_name, layer_name)`
- Increment block_layer_pairs count: `block_layer_pairs[pair_key] = block_layer_pairs.get(pair_key, 0) + 1`
- Add block_layer_pairs to the returned ExtractionResult dictionary
- Add logger info statement: `logger.info(f"Found {len(block_layer_pairs)} unique block-layer pairs")`
- Update extract_blocks() docstring examples to show block_layer_pairs

### 4. Write Unit Tests for Extraction
- Add test `test_extract_block_layer_pairs()` in test_extractor.py
- Verify block_layer_pairs is present in ExtractionResult
- Verify block_layer_pairs contains tuple keys: (str, str)
- Verify counts are positive integers
- Verify sum of block_layer_pairs values equals sum of block_counts values (conservation of insertions)
- Test with sample_drawing.dxf to validate real data extraction

### 5. Update Excel Block Counts Sheet Generation
- Modify `_create_block_counts_sheet()` in excel_writer.py to use block_layer_pairs
- Unpack tuple keys: `for (block_name, layer_name), insertion_count in data['block_layer_pairs'].items()`
- Fetch entity count from block_entities: `entity_count = block_entities.get(block_name, 0)`
- Build rows with three data columns plus entity count: block_name, insertion_count, entity_count, layer_name
- Sort by block_insertion_count descending (maintain existing behavior)
- Handle empty block_layer_pairs case by creating empty DataFrame with all four column headers
- Update function docstring to reflect block-layer pair structure

### 6. Update Excel Formatting
- Import `EXCEL_COLUMN_BLOCK_LAYER_NAME` in excel_writer.py
- Update `_format_block_counts_sheet()` to set column width for layer column
- Set column D width to 25 for block_layer_name (matching layer_name in Layer Analysis sheet)
- Update function docstring if needed

### 7. Write Unit Tests for Excel Generation
- Update test_excel_writer.py to validate block-layer pairs appear in Excel
- Add test to verify Block Counts sheet has four columns: block_name, block_insertion_count, block_entity_count, block_layer_name
- Verify rows contain unpacked block-layer pair data
- Verify sorting by insertion count descending is maintained
- Verify auto-filter is applied correctly
- Test empty block_layer_pairs case

### 8. Integration Testing with Real Files
- Run extraction on app/tests/assets/sample_drawing.dxf
- Manually verify Excel output has correct structure
- Verify block-layer pairs are correctly unpacked into separate columns
- Verify same block on different layers appears as separate rows
- Verify counts are accurate and sum correctly

### 9. Validation - Run All Tests
- Execute `uv run pytest app/tests/core/test_extractor.py -v` to validate extraction tests pass
- Execute `uv run pytest app/tests/core/test_excel_writer.py -v` to validate Excel generation tests pass
- Execute `uv run pytest app/tests/ -v` to run full test suite
- Execute `uv run mypy app/` to verify type checking passes
- Verify zero regressions in existing tests

### 10. End-to-End Validation
- Execute `bash scripts/start.sh` to launch the GUI application
- Select app/tests/assets/sample_drawing.dxf
- Click Extract button
- Verify Excel file opens automatically
- Verify Block Counts sheet shows block-layer pairs with four columns
- Verify data is correctly sorted by insertion count descending
- Verify Layer Analysis and Entity Summary sheets remain unchanged
- Close application and verify no errors in logs

## Testing Strategy

### Unit Tests

**Extractor Tests (test_extractor.py)**
- `test_extract_block_layer_pairs()`: Verify block_layer_pairs field exists and contains correct data structure
- `test_block_layer_pairs_tuple_keys()`: Verify all keys are (str, str) tuples
- `test_block_layer_pairs_conservation()`: Verify sum of block_layer_pairs equals sum of block_counts
- `test_block_layer_pairs_empty_file()`: Verify empty file returns empty block_layer_pairs dict
- `test_block_layer_pairs_single_layer()`: Verify blocks on single layer create correct pairs

**Excel Writer Tests (test_excel_writer.py)**
- `test_block_counts_sheet_has_layer_column()`: Verify Block Counts sheet has block_layer_name column
- `test_block_layer_pairs_unpacked_correctly()`: Verify tuple keys are unpacked into separate columns
- `test_block_layer_pairs_sorting()`: Verify rows sorted by insertion count descending
- `test_block_layer_pairs_empty_data()`: Verify empty block_layer_pairs creates sheet with headers only
- `test_block_layer_pairs_column_widths()`: Verify layer column has appropriate width

### Integration Tests

**Full Pipeline Test**
- Load sample_drawing.dxf → extract → generate Excel → verify all sheets
- Verify Block Counts sheet has correct number of rows (one per unique block-layer pair)
- Verify same block on multiple layers appears as multiple rows
- Verify counts aggregate correctly when grouped by block_name

### Edge Cases

**Empty Data**
- File with no blocks → block_layer_pairs is empty dict → Excel sheet has headers only

**Single Layer**
- All blocks on layer "0" → block_layer_pairs maps to single layer for all blocks → verify layer column shows "0"

**Multiple Layers per Block**
- DOOR on WALLS (5), DOOR on OPENINGS (3) → should create 2 rows → verify both rows exist with correct counts

**Special Characters in Layer Names**
- Layer names with spaces, hyphens, underscores → verify proper handling in tuple keys and Excel

**Block Not in Definitions**
- INSERT references block not in doc.blocks → entity_count should be 0 → verify block_entities.get() handles gracefully

### Playwright MCP Tests

**GUI Workflow Test**
- Launch app → select file → extract → verify Excel columns in Block Counts sheet
- Verify block_layer_name column appears in correct position (4th column)
- Verify data is readable and properly formatted
- Verify auto-filter works on all four columns

**Multi-Sheet Validation**
- Verify Layer Analysis and Entity Summary sheets are unaffected
- Verify all three sheets are present in output workbook
- Verify sheet names remain consistent

## Acceptance Criteria

1. **Data Model**
   - ExtractionResult includes `block_layer_pairs: dict[tuple[str, str], int]` field
   - block_layer_pairs correctly maps (block_name, layer_name) tuples to insertion counts
   - Existing block_counts field remains unchanged for backwards compatibility

2. **Excel Output**
   - Block Counts sheet displays four columns: block_name, block_insertion_count, block_entity_count, block_layer_name
   - Each row represents a unique block-layer pair
   - Rows are sorted by block_insertion_count descending
   - Auto-filter is applied to all columns
   - Column widths are appropriate for content

3. **Data Integrity**
   - Sum of block_layer_pairs insertion counts equals sum of block_counts (no insertions lost)
   - Same block on different layers appears as separate rows
   - Empty files produce empty block_layer_pairs and Excel sheet with headers only

4. **Type Safety**
   - All type hints are correct and mypy passes with zero errors
   - Tuple keys in block_layer_pairs are properly typed as tuple[str, str]

5. **Testing**
   - All new unit tests pass
   - All existing tests pass (zero regressions)
   - Test coverage includes edge cases (empty data, single layer, multiple layers)

6. **Code Quality**
   - Field naming follows app_docs/005-field-naming-convention.md
   - Docstrings updated to reflect new functionality
   - Logging statements added for observability
   - Constants used instead of magic strings

7. **User Experience**
   - GUI workflow unchanged (browse → extract → auto-open Excel)
   - Excel file opens successfully with new structure
   - Data is easily readable and properly formatted
   - No breaking changes to existing sheets (Layer Analysis, Entity Summary)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Validate extractor tests pass with new block-layer pair logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate Excel writer tests pass with new sheet structure
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage includes new code
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI and manually test extraction with sample_drawing.dxf to verify Excel output

## Notes

### Field Naming Convention Compliance
The new field follows the established convention from app_docs/005-field-naming-convention.md:
- `block_layer_name` - follows {domain}_{attribute} pattern
- Domain: `block` (the block-layer pair is part of the block domain)
- Attribute: `layer_name` (the identifier of the layer)
- Singular form because it represents a single layer per row (not a collection)

### Backwards Compatibility
The existing `block_counts` field will remain in ExtractionResult. This ensures:
- Existing code that relies on aggregated counts continues to work
- Future features can use either aggregated or granular data
- Migration path is smooth if we want to deprecate block_counts later

### Performance Considerations
- Block-layer pair extraction adds minimal overhead (same single iteration through INSERT entities)
- Memory impact is negligible (typical drawings have hundreds to thousands of pairs, not millions)
- Excel generation time is similar (same number of total rows across all blocks)

### Future Enhancements
This feature sets the foundation for additional block-layer analysis:
- Filtering blocks by layer in the GUI
- Layer-based block statistics (most common block per layer)
- Cross-referencing block-layer pairs with layer properties (color, frozen/thawed state)
- Pivot table generation (blocks as rows, layers as columns)

### Alternative Considered: Separate Sheet
An alternative design would create a new "Block-Layer Pairs" sheet instead of modifying Block Counts. This was rejected because:
- Adds complexity (additional sheet to maintain)
- Splits related data across sheets
- Block Counts sheet would become less useful if it only shows aggregates
- Current approach is more intuitive (one sheet for block insertions, now with layer detail)
