# Feature: Add _create_all_blocks_sheet Function to excel_writer.py

## Feature Description
Add a new `_create_all_blocks_sheet()` function to `app/core/excel_writer.py` that creates a consolidated "All Blocks" Excel sheet with 29 columns. This sheet provides a comprehensive block-centric view by iterating over `all_block_definitions` and aggregating data from multiple sources including `block_counts`, `block_layer_pairs`, `block_rotation_counts`, `block_scale_data`, `block_trimming_data`, and `block_content_zone_data`. Each row represents a single block definition with its complete metadata, insertion statistics, transformation data, geometry, and content zone information.

## User Story
As a CAD data analyst
I want a single consolidated "All Blocks" sheet that shows all block definitions with their complete analysis data
So that I can quickly review block metadata, insertion counts, layer distribution, rotations, scales, geometry, and content zone data in one place without switching between multiple sheets

## Problem Statement
Currently, block data is spread across multiple sheets:
- Block Definitions: Identity/status fields only
- Block Analysis: Block-layer pairs with insertion counts
- Block Geometry Analysis: Transformations and geometry per block-layer pair

Users need to cross-reference multiple sheets to get a complete picture of a single block. The new "All Blocks" sheet consolidates all block data into a single view where each row represents one block definition with aggregated statistics across all layers.

## Solution Statement
Create a new `_create_all_blocks_sheet()` function that:
1. Iterates over `all_block_definitions` (one row per block)
2. Copies identity/status fields from `BlockDefinitionRecord`
3. Calculates aggregated insertion count from `block_counts`
4. Derives layer count and layer names from `block_layer_pairs`
5. Sums rotation counts across all layers from `block_rotation_counts`
6. Gets scale summary from `block_scale_data`
7. Gets geometry from `block_trimming_data`
8. Gets content zone data from `block_content_zone_data`
9. Sorts by insertion_status (Inserted first), then by resolved_name
10. Outputs to sheet named "All Blocks" with 29 columns

## Relevant Files
Use these files to implement the feature:

- `app/core/excel_writer.py` - Main file to modify. Add the new `_create_all_blocks_sheet()` function following the pattern of existing sheet creation functions like `_create_block_definitions_sheet()` and `_create_block_geometry_analysis_sheet()`. Also update `write_excel()` to call the new function and add formatting.
- `app/core/excel_formatting.py` - Add `_format_all_blocks_sheet()` function for sheet formatting (auto-filter, column widths, scale highlighting).
- `app/core/constants.py` - Reference file. Contains `EXCEL_SHEET_ALL_BLOCKS`, `EXCEL_COLUMN_BLOCK_LAYER_COUNT`, `EXCEL_COLUMN_BLOCK_LAYER_NAMES` and all other column constants needed.
- `app/core/types.py` - Reference file. Contains `BlockDefinitionRecord`, `BlockLayerKey`, `BlockRotationKey`, and `ExtractionResult` type definitions.
- `app/core/extractor.py` - Reference file. Contains `ExtractionResult` TypedDict defining all available data fields.
- `app/tests/core/excel_writer/conftest.py` - Update to add fixture data for All Blocks sheet testing.
- `app/tests/core/excel_writer/test_excel_writer_block_definitions.py` - Reference for testing patterns.

### New Files
- `app/tests/core/excel_writer/test_excel_writer_all_blocks.py` - New test file for All Blocks sheet functionality.
- `app/tests/core/excel_formatting/test_formatting_all_blocks.py` - New test file for All Blocks sheet formatting.

## Implementation Plan
### Phase 1: Foundation
1. Review existing sheet creation functions in `excel_writer.py` to understand patterns
2. Review `_create_block_definitions_sheet()` for row iteration over `all_block_definitions`
3. Review `_create_block_geometry_analysis_sheet()` for data aggregation patterns
4. Verify all 29 column constants exist in `constants.py`
5. Understand the data structures in `ExtractionResult` and how to aggregate them

### Phase 2: Core Implementation
1. Add `_create_all_blocks_sheet()` function to `excel_writer.py`
2. Implement row-by-row iteration over `all_block_definitions`
3. Implement aggregation logic for:
   - Layer count and names from `block_layer_pairs`
   - Total rotation counts across all layers
   - Scale data using existing `_has_x_scale_variance()`, `_has_y_scale_variance()`, etc.
   - Geometry from `block_trimming_data`
   - Content zone from `block_content_zone_data`
4. Implement sorting by insertion_status then resolved_name
5. Add `_format_all_blocks_sheet()` to `excel_formatting.py`
6. Update `write_excel()` to call new function and formatting

### Phase 3: Integration
1. Add comprehensive unit tests for sheet creation
2. Add formatting tests
3. Update conftest.py with appropriate test fixtures
4. Validate all existing tests pass (no regressions)

## Step by Step Tasks

### Step 1: Update excel_writer.py Imports
- Open `app/core/excel_writer.py`
- Add import for `EXCEL_SHEET_ALL_BLOCKS` constant
- Add import for `EXCEL_COLUMN_BLOCK_LAYER_COUNT` constant
- Add import for `EXCEL_COLUMN_BLOCK_LAYER_NAMES` constant
- Verify all other needed constants are already imported

### Step 2: Create _create_all_blocks_sheet Function
- Add new function `_create_all_blocks_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None`
- Add docstring following existing function patterns
- Add logging at start and end of function
- Extract needed data from ExtractionResult:
  - `all_block_definitions`
  - `block_counts`
  - `block_layer_pairs`
  - `block_rotation_counts`
  - `block_scale_data`
  - `block_trimming_data`
  - `block_content_zone_data`

### Step 3: Implement Row Iteration Logic
- Skip System blocks (insertion_status starting with "System")
- For each block definition in `all_block_definitions`:
  - Get resolved_name for lookups
  - Copy identity fields: raw_name, resolved_name, insertion_status, is_nested, nested_parent_names, entity_count
  - Calculate `block_insertion_count` from `block_counts.get(resolved_name, 0)`

### Step 4: Implement Layer Aggregation
- Calculate layers_for_block: `{key.layer_name for key in block_layer_pairs if key.block_name == resolved_name}`
- Set `block_layer_count = len(layers_for_block)`
- Set `block_layer_names = ", ".join(sorted(layers_for_block))`

### Step 5: Implement Rotation Aggregation
- For each rotation category ('0', '90', '180', '270', 'other'):
  - Sum counts across all layers: `sum(count for key, count in block_rotation_counts.items() if key.block_name == resolved_name and key.rotation_category == category)`

### Step 6: Implement Scale Data Extraction
- Get scale_set from `block_scale_data.get(resolved_name, {(1.0, 1.0)})`
- Use existing helper functions:
  - `_has_x_scale_variance(scale_set)` for x_variance
  - `_has_y_scale_variance(scale_set)` for y_variance
  - `_has_negative_scale_in_set(scale_set, axis)` for negative detection
  - `_get_single_scale_value(scale_set, axis)` for single values
- Set x_scale: "VARIES (-)", "VARIES", or numeric value
- Set y_scale: "VARIES (-)", "VARIES", or numeric value

### Step 7: Implement Geometry Data Extraction
- Get geometry_data from `block_trimming_data.get(resolved_name)`
- If exists: extract native_width, native_height, vertical_segments, horizontal_segments
- If not exists: use empty/default values
- Format segment lists as comma-separated strings using format_number helper

### Step 8: Implement Content Zone Data Extraction
- Get content_zone from `block_content_zone_data.get(resolved_name)`
- If content_zone and content_zone_detected:
  - Extract trim values, detected flag, dimensions, polygon counts
- Else:
  - Use empty/default values

### Step 9: Build DataFrame Row
- Create row dict with all 29 columns using constant column names
- Append to rows list

### Step 10: Implement Sorting Logic
- Define status_order dict matching `_create_block_definitions_sheet()`
- Sort rows by (status_order[insertion_status], resolved_name.lower())

### Step 11: Create DataFrame and Write Sheet
- Create DataFrame from rows
- Handle empty data case (empty DataFrame with all 29 column headers)
- Format column headers using `format_header()`
- Write to sheet using `df.to_excel(writer, sheet_name=EXCEL_SHEET_ALL_BLOCKS, index=False)`
- Log completion

### Step 12: Add _format_all_blocks_sheet Function
- Open `app/core/excel_formatting.py`
- Add import for `EXCEL_SHEET_ALL_BLOCKS`
- Create `_format_all_blocks_sheet(wb: Workbook) -> None` function
- Apply auto-filter to header row
- Set appropriate column widths (wider for names, narrower for counts)
- Add scale highlighting (yellow for VARIES, orange for negative, red for VARIES(-)) using existing fill colors
- Handle case where sheet doesn't exist (return early)

### Step 13: Update write_excel Function
- Add call to `_create_all_blocks_sheet(extraction_data, writer)` after Sheet 8
- Add call to `_format_all_blocks_sheet(wb)` in formatting section
- Add logging debug statements

### Step 14: Create Test File for All Blocks Sheet
- Create `app/tests/core/excel_writer/test_excel_writer_all_blocks.py`
- Add imports for constants, types, fixtures
- Create `TestAllBlocksSheet` test class

### Step 15: Add Sheet Existence Test
- Test that "All Blocks" sheet is created when `all_block_definitions` has non-system blocks
- Use `sample_extraction_data` fixture

### Step 16: Add Column Count Test
- Test that sheet has exactly 29 columns
- Verify column names match expected constants

### Step 17: Add Row Count Test
- Test correct number of rows (non-system blocks only)
- Verify system blocks are excluded

### Step 18: Add Sorting Test
- Test that rows are sorted by insertion_status then resolved_name
- Inserted blocks should appear before Nested Only

### Step 19: Add Layer Aggregation Test
- Test that block_layer_count is calculated correctly
- Test that block_layer_names is comma-separated and sorted

### Step 20: Add Rotation Aggregation Test
- Test that rotation counts are summed across all layers
- Test block with multiple layers has aggregated totals

### Step 21: Add Scale Data Test
- Test blocks with uniform scale show numeric values
- Test blocks with varying scale show "VARIES"
- Test blocks with negative scale show appropriate values

### Step 22: Add Geometry Data Test
- Test that native_width, native_height are populated
- Test that segments are formatted as comma-separated strings

### Step 23: Add Content Zone Data Test
- Test blocks with detected content zone have trim values
- Test blocks without content zone have empty values

### Step 24: Add Empty Data Test
- Test that empty `all_block_definitions` creates empty sheet with headers only

### Step 25: Add Formatting Test File
- Create `app/tests/core/excel_formatting/test_formatting_all_blocks.py`
- Test auto-filter is applied
- Test column widths are set
- Test scale highlighting (requires fixture with VARIES values)

### Step 26: Update conftest.py for All Blocks Testing
- Update `sample_extraction_data` fixture if needed to support All Blocks tests
- Ensure fixture has:
  - Multiple blocks with different insertion statuses
  - Blocks on multiple layers for aggregation testing
  - Blocks with varying scales
  - Blocks with and without content zone detection

### Step 27: Run Validation Commands
- Run all tests to ensure no regressions
- Run type checking
- Run linting

## Testing Strategy
### Unit Tests
- Test sheet creation with sample data
- Test all 29 columns are present with correct headers
- Test row count excludes system blocks
- Test sorting by insertion_status and resolved_name
- Test layer count/names aggregation
- Test rotation count aggregation across layers
- Test scale variance detection and display
- Test geometry data population
- Test content zone data population
- Test empty data handling
- Test formatting function applies auto-filter
- Test formatting function applies column widths
- Test formatting function applies scale highlighting

### Integration Tests
- Test `write_excel()` produces Excel file with All Blocks sheet
- Test All Blocks sheet alongside other sheets (no conflicts)
- Test with real extraction data from DXF file

### Edge Cases
- Block with no insertions (insertion_count = 0)
- Block on zero layers (layer_count = 0)
- Block with no rotation data (all rotation counts = 0)
- Block with no scale data (use default 1.0, 1.0)
- Block with no geometry data (empty values)
- Block with no content zone data (empty values)
- All blocks are system blocks (sheet has headers only)
- Single block with single layer (no aggregation needed)
- Block with many layers (test comma-separated names)

### Playwright MCP Tests
Not applicable for this unit - no UI changes. This is backend Excel generation.

## Acceptance Criteria
- [ ] `_create_all_blocks_sheet()` function exists in `excel_writer.py`
- [ ] Function iterates over `all_block_definitions` and creates one row per non-system block
- [ ] Sheet has exactly 29 columns with correct headers
- [ ] `block_insertion_count` is correctly calculated from `block_counts`
- [ ] `block_layer_count` and `block_layer_names` are correctly aggregated from `block_layer_pairs`
- [ ] Rotation counts are correctly summed across all layers
- [ ] Scale data correctly shows "VARIES", "VARIES (-)", or numeric values
- [ ] Geometry data is correctly populated from `block_trimming_data`
- [ ] Content zone data is correctly populated from `block_content_zone_data`
- [ ] Rows are sorted by insertion_status (Inserted first), then by resolved_name
- [ ] `_format_all_blocks_sheet()` function exists and applies auto-filter, column widths, and scale highlighting
- [ ] `write_excel()` calls new functions to create and format the sheet
- [ ] All unit tests pass
- [ ] All existing tests pass (no regressions)
- [ ] Type checking passes (`uv run mypy app/`)
- [ ] Linting passes (`uv run ruff check app/`)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_all_blocks.py -v` - Run All Blocks sheet tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_all_blocks.py -v` - Run All Blocks formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all excel_formatting tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure no regressions
- `uv run mypy app/` - Run type checking
- `uv run ruff check app/` - Run linting

## Notes
- This is Unit 2 of a larger implementation plan for the "All Blocks" consolidated sheet feature
- Unit 1 (completed in commit 7af090b) added the three new constants to `constants.py`: `EXCEL_SHEET_ALL_BLOCKS`, `EXCEL_COLUMN_BLOCK_LAYER_COUNT`, `EXCEL_COLUMN_BLOCK_LAYER_NAMES`
- The 29 columns are defined in the unit content table above - most constants already exist from other sheets
- System blocks (insertion_status starting with "System") are excluded from the All Blocks sheet
- The sorting logic matches `_create_block_definitions_sheet()` for consistency
- Scale helper functions (`_has_x_scale_variance`, `_has_y_scale_variance`, `_get_single_scale_value`, `_has_negative_scale_in_set`) already exist and should be reused
- The `format_number` helper function for segment formatting already exists in `_create_block_geometry_analysis_sheet()` and may need to be extracted or duplicated
- Future Unit 3 will add integration with the main application and any final polish
