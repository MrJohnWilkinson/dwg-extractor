# Feature: Three-Tab Excel Output with Comprehensive CAD Analysis

## Feature Description
Enhance the Excel output to provide comprehensive CAD file analysis across three worksheets instead of a single sheet. The feature transforms the current single-sheet "Block Summary" into a multi-dimensional analysis tool that provides:

1. **Block Counts Tab**: Enhanced block analysis showing not only insertion counts but also the complexity of each block definition (entity count within the block)
2. **Layer Analysis Tab**: New layer-based metrics showing block distribution and entity counts across drawing layers
3. **Entity Summary Tab**: New global entity type breakdown showing all entity types (LINE, CIRCLE, ARC, etc.) and their total counts

This feature provides users with a complete understanding of their CAD file structure, enabling better asset management, drawing complexity assessment, and quality control.

## User Story
As a CAD manager or engineer
I want to see comprehensive analysis of blocks, layers, and entities in a single Excel report
So that I can quickly understand drawing complexity, layer organization, and block reusability without manually inspecting the CAD file

## Problem Statement
The current single-tab Excel output only shows block insertion counts, which provides limited insight into the CAD file structure. Users cannot:
- Assess block complexity (how many entities make up each block template)
- Understand layer organization and distribution of objects
- Get a global view of entity types used throughout the drawing
- Identify optimization opportunities (layers with too many entities, overly complex blocks)

This limitation requires users to manually inspect CAD files to gather additional analysis, reducing productivity and making it difficult to quickly assess multiple drawings.

## Solution Statement
Extend the extraction and Excel generation modules to capture and report three dimensions of CAD analysis:

1. **Enhanced Extractor Module**: Modify `extract_blocks()` to return a comprehensive data structure containing:
   - Block insertion counts (existing)
   - Entity counts within each block definition (new)
   - Layer-based block insertion counts (new)
   - Layer-based total entity counts (new)
   - Global entity type counts (new)

2. **Multi-Sheet Excel Writer**: Refactor `write_excel()` to create a workbook with three formatted sheets:
   - "Block Counts" with block_name | insertion_count | entities_in_definition
   - "Layer Analysis" with layer_name | insertions_on_layer | entities_on_layer
   - "Entity Summary" with entity_type | total_count

3. **Maintain Existing Behavior**: Keep all current functionality including timestamped filenames, auto-open behavior, error handling, and GUI workflow.

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** - Core extraction logic that currently only returns block insertion counts. Will be enhanced to extract layer data, entity counts within block definitions, and global entity type counts.

- **app/core/excel_writer.py** - Excel generation module that currently creates a single-sheet workbook. Will be refactored to create a multi-sheet workbook with three tabs, each with proper formatting, auto-filters, and column widths.

- **app/core/constants.py** - Application constants that define Excel column names and worksheet names. Will be extended with new constants for the additional columns and sheet names.

- **app/main.py** - GUI application that orchestrates extraction and Excel generation. May need minor updates to handle the new data structure returned by the extractor.

- **app/tests/core/test_extractor.py** - Unit tests for extractor module. Will need new tests to validate layer analysis, entity counting, and block definition analysis.

- **app/tests/core/test_excel_writer.py** - Unit tests for Excel writer module. Will need new tests to validate multi-sheet creation, data distribution across sheets, and formatting consistency.

### New Files
No new files are required. All changes will be made to existing modules following the established architecture pattern.

## Implementation Plan

### Phase 1: Foundation - Data Structure Design
Design and implement the comprehensive data structure that will be returned by the enhanced extractor module. This is critical as it will be consumed by both the Excel writer and the GUI application.

Define a TypedDict or dataclass structure containing:
- `block_counts: dict[str, int]` - Existing block insertion counts
- `block_entities: dict[str, int]` - Entity count within each block definition
- `layer_insertions: dict[str, int]` - Block insertion count per layer
- `layer_entities: dict[str, int]` - Total entity count per layer
- `entity_types: dict[str, int]` - Global entity type counts

Update constants.py with new Excel configuration constants for all three sheets.

### Phase 2: Core Implementation - Extractor Enhancement
Enhance the extractor module to analyze and extract all required data from DWG/DXF files:

1. Iterate through block definitions to count entities within each block
2. Track layers for each INSERT entity to count insertions per layer
3. Iterate through all entities on each layer to count layer entity totals
4. Track entity types globally across the entire modelspace
5. Return the comprehensive data structure designed in Phase 1

### Phase 3: Integration - Excel Writer Refactoring and Testing
Refactor the Excel writer to create multi-sheet workbooks and integrate with the GUI:

1. Update excel_writer.py to accept the new data structure
2. Create three sheets with appropriate names and formatting
3. Apply auto-filters and column widths to each sheet
4. Sort each sheet by the appropriate column (descending)
5. Update GUI main.py if needed to handle new data structure
6. Create comprehensive unit tests for all new functionality
7. Validate end-to-end workflow with real DWG/DXF files

## Step by Step Tasks

### Step 1: Update constants.py with new Excel configuration
- Add constants for new sheet names: `EXCEL_SHEET_BLOCK_COUNTS`, `EXCEL_SHEET_LAYER_ANALYSIS`, `EXCEL_SHEET_ENTITY_SUMMARY`
- Add constants for Block Counts tab columns: `EXCEL_COLUMN_ENTITIES_IN_DEFINITION`
- Add constants for Layer Analysis tab columns: `EXCEL_COLUMN_LAYER_NAME`, `EXCEL_COLUMN_INSERTIONS_ON_LAYER`, `EXCEL_COLUMN_ENTITIES_ON_LAYER`
- Add constants for Entity Summary tab columns: `EXCEL_COLUMN_ENTITY_TYPE`, `EXCEL_COLUMN_TOTAL_COUNT`
- Maintain backward compatibility by keeping existing constants

### Step 2: Define comprehensive data structure type
- Create a TypedDict in extractor.py named `ExtractionResult` with all required fields:
  - `block_counts: dict[str, int]`
  - `block_entities: dict[str, int]`
  - `layer_insertions: dict[str, int]`
  - `layer_entities: dict[str, int]`
  - `entity_types: dict[str, int]`
- Add comprehensive docstring explaining each field
- Add type hints throughout the module

### Step 3: Enhance extract_blocks() to extract block definition entity counts
- After loading the document, access `doc.blocks` to iterate through block definitions
- For each block definition, count the number of entities it contains
- Store results in `block_entities: dict[str, int]` dictionary
- Handle edge cases: blocks with no entities, anonymous blocks, nested blocks
- Add logging for block definition analysis

### Step 4: Enhance extract_blocks() to extract layer-based metrics
- While iterating through modelspace INSERT entities, track the layer each insertion is on
- Build `layer_insertions: dict[str, int]` dictionary counting insertions per layer
- Iterate through all modelspace entities (not just INSERT) to count entities per layer
- Build `layer_entities: dict[str, int]` dictionary counting total entities per layer
- Add logging for layer analysis

### Step 5: Enhance extract_blocks() to extract global entity type counts
- Iterate through all modelspace entities and track entity types via `entity.dxftype()`
- Build `entity_types: dict[str, int]` dictionary counting each entity type (LINE, CIRCLE, ARC, INSERT, etc.)
- Add logging for entity type analysis
- Return comprehensive `ExtractionResult` dictionary instead of just block_counts

### Step 6: Write unit tests for enhanced extractor
- Create test cases for block definition entity counting
- Create test cases for layer-based insertion counting
- Create test cases for layer-based entity counting
- Create test cases for global entity type counting
- Test edge cases: empty drawings, drawings with no blocks, single-layer drawings
- Validate data structure completeness and type correctness
- Use existing test assets (sample_drawing.dxf, empty_drawing.dxf)

### Step 7: Refactor write_excel() signature and structure
- Update function signature to accept `ExtractionResult` TypedDict instead of `dict[str, int]`
- Create workbook with three sheets instead of one
- Keep timestamped filename generation logic
- Update docstring to reflect new multi-sheet functionality
- Add logging for multi-sheet creation process

### Step 8: Implement "Block Counts" sheet creation
- Create first sheet named per `EXCEL_SHEET_BLOCK_COUNTS` constant
- Merge block_counts and block_entities data into single DataFrame
- Columns: block_name | insertion_count | entities_in_definition
- Sort by insertion_count descending
- Apply auto-filter to headers
- Set column widths: A=30, B=20, C=25
- Add logging for sheet creation

### Step 9: Implement "Layer Analysis" sheet creation
- Create second sheet named per `EXCEL_SHEET_LAYER_ANALYSIS` constant
- Merge layer_insertions and layer_entities data into single DataFrame
- Columns: layer_name | insertions_on_layer | entities_on_layer
- Sort by entities_on_layer descending
- Apply auto-filter to headers
- Set column widths: A=30, B=20, C=20
- Add logging for sheet creation

### Step 10: Implement "Entity Summary" sheet creation
- Create third sheet named per `EXCEL_SHEET_ENTITY_SUMMARY` constant
- Convert entity_types dictionary to DataFrame
- Columns: entity_type | total_count
- Sort by total_count descending
- Apply auto-filter to headers
- Set column widths: A=25, B=20
- Add logging for sheet creation

### Step 11: Write unit tests for multi-sheet Excel writer
- Test that three sheets are created with correct names
- Test each sheet has correct columns and headers
- Test data is correctly distributed across sheets
- Test sorting is correct on each sheet (descending by appropriate column)
- Test auto-filters are applied to all sheets
- Test column widths are set correctly on all sheets
- Test empty data handling (headers only on all sheets)
- Test filename timestamping still works
- Use temp_dir fixture and sample data fixtures

### Step 12: Update main.py GUI integration if needed
- Review if main.py needs updates to handle new data structure
- Update _extraction_worker() to handle ExtractionResult instead of dict[str, int]
- Verify error handling still works correctly
- Verify progress updates work correctly
- Test that auto-open Excel behavior still works with multi-sheet workbook
- Add logging if integration points are modified

### Step 13: Create integration tests for end-to-end workflow
- Test complete workflow: load DXF → extract all data → write multi-sheet Excel → verify output
- Use existing test assets (sample_drawing.dxf, empty_drawing.dxf)
- Validate all three sheets contain expected data
- Validate Excel file can be opened and read correctly
- Test error cases: invalid files, missing files, corrupted files
- Verify error messages are still user-friendly

### Step 14: Run validation commands
- Execute all validation commands listed in "Validation Commands" section
- Fix any failing tests
- Verify zero regressions in existing functionality
- Verify type checking passes with mypy
- Run manual end-to-end test with real DWG/DXF file

## Testing Strategy

### Unit Tests

**Extractor Module Tests (test_extractor.py):**
- `test_extract_block_entities()` - Verify block definition entity counts are accurate
- `test_extract_layer_insertions()` - Verify layer-based insertion counts are correct
- `test_extract_layer_entities()` - Verify layer-based total entity counts are correct
- `test_extract_entity_types()` - Verify global entity type counts are complete
- `test_extract_comprehensive_structure()` - Verify returned data structure has all required fields
- `test_extract_empty_drawing()` - Verify empty drawing returns empty dicts for all fields
- `test_extract_single_layer()` - Verify single-layer drawing is handled correctly

**Excel Writer Module Tests (test_excel_writer.py):**
- `test_write_excel_three_sheets()` - Verify three sheets are created with correct names
- `test_block_counts_sheet_structure()` - Verify Block Counts sheet has correct columns and data
- `test_layer_analysis_sheet_structure()` - Verify Layer Analysis sheet has correct columns and data
- `test_entity_summary_sheet_structure()` - Verify Entity Summary sheet has correct columns and data
- `test_all_sheets_sorted()` - Verify each sheet is sorted correctly by appropriate column
- `test_all_sheets_autofilter()` - Verify auto-filters applied to all sheets
- `test_all_sheets_column_widths()` - Verify column widths set correctly on all sheets
- `test_empty_data_all_sheets()` - Verify empty data creates headers-only sheets
- `test_filename_format_unchanged()` - Verify timestamped filename format is maintained

### Integration Tests
- **End-to-End Workflow Test**: Load sample_drawing.dxf → extract data → write Excel → validate all three sheets have expected data
- **Empty Drawing Test**: Process empty_drawing.dxf → verify all three sheets created with headers only
- **Invalid File Test**: Process invalid.dxf → verify ValueError raised with appropriate message
- **Missing File Test**: Process nonexistent.dxf → verify FileNotFoundError raised

### Edge Cases
- **Drawing with no blocks**: Only INSERT entities missing, but layers and entity types should still be populated
- **Drawing with no layers**: All entities on layer "0" (default layer)
- **Drawing with blocks containing no entities**: Block appears in block_counts but has 0 in entities_in_definition
- **Anonymous blocks**: Blocks with auto-generated names (e.g., "*U123")
- **Nested blocks**: Blocks that contain other blocks (count entities at current level only)
- **Very large drawings**: Drawings with thousands of blocks, layers, or entities (performance test)

### Playwright MCP Tests
Not applicable for this feature as it's a desktop application using customtkinter, not a web application. Manual GUI testing will be performed instead:
- Launch app via `bash scripts/start.sh`
- Browse and select test DWG/DXF file
- Click Extract button
- Verify Excel auto-opens with three tabs
- Verify each tab contains expected data and formatting
- Test with multiple files to verify timestamping prevents overwrites

## Acceptance Criteria
1. ✅ Excel output contains exactly three sheets: "Block Counts", "Layer Analysis", "Entity Summary"
2. ✅ Block Counts sheet displays: block_name | insertion_count | entities_in_definition, sorted by insertion_count descending
3. ✅ Layer Analysis sheet displays: layer_name | insertions_on_layer | entities_on_layer, sorted by entities_on_layer descending
4. ✅ Entity Summary sheet displays: entity_type | total_count, sorted by total_count descending
5. ✅ All sheets have auto-filters applied to header rows
6. ✅ All sheets have properly formatted column widths for readability
7. ✅ Timestamped filename format is maintained (e.g., drawing_blocks_20250117_143022.xlsx)
8. ✅ Auto-open behavior works correctly with multi-sheet workbook
9. ✅ Empty drawings create Excel files with headers only on all three sheets
10. ✅ All existing error handling works correctly (FileNotFoundError, ValueError for invalid files)
11. ✅ GUI workflow remains unchanged (Browse → Extract → Auto-open)
12. ✅ All existing unit tests pass (zero regressions)
13. ✅ All new unit tests pass with 100% coverage on new code
14. ✅ Type checking passes with mypy (strict mode)
15. ✅ Manual end-to-end test succeeds with real DWG/DXF file

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to validate enhanced extraction logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests to validate multi-sheet creation
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage on core modules
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI application for manual end-to-end testing

**Manual Validation Steps:**
1. Launch app: `bash scripts/start.sh`
2. Click "Browse" and select `app/tests/assets/sample_drawing.dxf`
3. Click "Extract"
4. Verify Excel auto-opens with three tabs
5. Verify "Block Counts" tab contains expected data (3 blocks with insertion counts and entity counts)
6. Verify "Layer Analysis" tab contains layer-based metrics
7. Verify "Entity Summary" tab contains entity type breakdown
8. Verify each tab has auto-filter enabled on headers
9. Verify each tab is sorted correctly (descending by appropriate count column)
10. Test with `app/tests/assets/empty_drawing.dxf` to verify headers-only sheets

## Notes

### Implementation Considerations
- **ezdxf API Usage**: The `doc.blocks` collection provides access to block definitions. Each block definition has an `__iter__()` method to iterate through entities within the block.
- **Layer Tracking**: All entities have a `dxf.layer` attribute that identifies which layer they belong to. Default layer is "0".
- **Entity Types**: Use `entity.dxftype()` to get entity type strings like "LINE", "CIRCLE", "ARC", "INSERT", "LWPOLYLINE", etc.
- **Performance**: For large drawings with thousands of entities, consider logging progress at key milestones (e.g., "Analyzed 1000 entities...").

### Future Enhancements
- **Attribute Analysis Tab**: Add fourth tab showing block attributes (if blocks contain attribute definitions)
- **Color/Linetype Analysis**: Add sheet showing color and linetype distribution
- **File Metadata Tab**: Add sheet showing drawing properties (units, limits, creation date from DXF header)
- **Export to CSV**: Add option to export each sheet as separate CSV files
- **Filtering Options**: Add GUI controls to filter by layer or block name before extraction
- **Comparison Mode**: Add ability to compare two drawings side-by-side

### Backward Compatibility
The current implementation returns `dict[str, int]` from `extract_blocks()`. This breaking change means:
- The function signature will change from returning `dict[str, int]` to returning `ExtractionResult` TypedDict
- The `write_excel()` signature will change to accept `ExtractionResult` instead of `dict[str, int]`
- The GUI `_extraction_worker()` will need minor updates to handle the new structure

This is acceptable as this is an internal application with no external API consumers. All integration points (GUI → extractor → excel_writer) are within our control.

### Testing Data Requirements
The existing `app/tests/assets/sample_drawing.dxf` test fixture will need to be verified to ensure it has:
- Multiple layers (for layer analysis testing)
- Various entity types beyond INSERT (LINE, CIRCLE, ARC, etc.)
- Blocks with known entity counts in their definitions

If the current test fixture is insufficient, create a new test fixture DXF file with known, predictable data for all three analysis dimensions.
