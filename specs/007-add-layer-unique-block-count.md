# Feature: Layer Unique Block Count

## Feature Description
Add a new column to the Layer Analysis sheet that displays the count of unique block types on each layer. This provides visibility into the diversity of blocks used on each layer, helping users understand the complexity and composition of their layer organization. The field will follow the naming convention from app_docs/005-field-naming-convention.md: `layer_unique_block_count` representing the count of distinct block types per layer.

## User Story
As a CAD file analyst
I want to see how many different block types exist on each layer
So that I can understand the diversity and complexity of block usage across layers and identify layers with high block variety

## Problem Statement
Currently, the Layer Analysis sheet shows:
- `layer_name`: The layer identifier
- `layer_block_insertion_count`: Total number of block insertions on the layer
- `layer_entity_count`: Total number of entities on the layer

However, users cannot determine:
- How many different block types are used on each layer
- Whether a layer has many insertions of few block types (repetitive) or few insertions of many block types (diverse)
- Which layers have the highest block diversity for complexity analysis

For example, a layer might have 100 block insertions (`layer_block_insertion_count = 100`), but this could be 100 insertions of 1 block type, or 10 insertions each of 10 different block types. The unique block count provides this critical distinction.

## Solution Statement
Add a new column `layer_unique_block_count` to the Layer Analysis sheet by:

1. **Extraction Layer**: Calculate unique block types per layer during the extraction phase by analyzing the existing `block_layer_pairs` data structure
2. **Data Structure**: Add `layer_unique_block_counts: dict[str, int]` to ExtractionResult, mapping layer names to their count of distinct block types
3. **Excel Generation**: Add the new column to the Layer Analysis sheet as the fourth column (after layer_entity_count)
4. **Field Naming**: Follow the naming convention: `layer_unique_block_count` (domain: layer, qualifier: unique, attribute: block, type: count)

This approach leverages the existing block_layer_pairs data without requiring additional file parsing, ensuring efficient computation.

## Relevant Files
Use these files to implement the feature:

**app/core/extractor.py**
- Contains the `extract_blocks()` function and `ExtractionResult` TypedDict
- Already generates `block_layer_pairs: dict[tuple[str, str], int]` which contains all the data needed to calculate unique blocks per layer
- Needs to add logic to calculate `layer_unique_block_counts` from `block_layer_pairs` before returning the result
- Pattern: Iterate through block_layer_pairs keys, count unique block names per layer

**app/core/excel_writer.py**
- Contains `_create_layer_analysis_sheet()` function that generates the Layer Analysis sheet
- Currently displays 3 columns: layer_name, layer_block_insertion_count, layer_entity_count
- Needs to add the fourth column: layer_unique_block_count
- The new column should appear after layer_entity_count for logical flow
- `_format_layer_analysis_sheet()` needs column width setting for the new column D

**app/core/constants.py**
- Defines all Excel column name constants
- Needs new constant: `EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT: str = 'layer_unique_block_count'`
- Must include inline comment referencing the naming convention guide

**app_docs/005-field-naming-convention.md**
- Documents the field naming convention (read-only reference)
- Confirms the pattern: layer_unique_block_count follows layer domain examples
- Pattern: `layer_{attribute}_{qualifier}` → `layer_block_count` with `unique` qualifier → `layer_unique_block_count`

**app/tests/core/test_extractor.py**
- Contains unit tests for extractor module
- Needs new tests to validate layer_unique_block_counts calculation
- Should verify counts are accurate for various scenarios (single block type, multiple block types, no blocks)

**app/tests/core/test_excel_writer.py**
- Contains unit tests for Excel generation
- Needs updates to verify the new column appears in Layer Analysis sheet
- Should test correct positioning, sorting behavior, and data accuracy

## Implementation Plan

### Phase 1: Foundation
Update the data model and constants to support layer unique block counts:
1. Add `EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT` constant to constants.py
2. Add `layer_unique_block_counts: dict[str, int]` field to `ExtractionResult` TypedDict
3. Update ExtractionResult docstring to document the new field structure and purpose

### Phase 2: Core Implementation
Implement the calculation of unique blocks per layer:
1. In `extract_blocks()`, after populating `block_layer_pairs`, calculate `layer_unique_block_counts`
2. Iterate through block_layer_pairs keys (which are tuples of (block_name, layer_name))
3. For each layer, count the number of unique block names that appear in the pairs
4. Add the result to the ExtractionResult dictionary
5. Add logging to report unique block count metrics

### Phase 3: Integration
Update Excel generation to display the new column:
1. Modify `_create_layer_analysis_sheet()` to include layer_unique_block_count column
2. Ensure the column appears as the fourth column (after layer_entity_count)
3. Maintain the existing sort order (by layer_entity_count descending)
4. Update `_format_layer_analysis_sheet()` to set appropriate column width for column D
5. Handle empty data case (headers only)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Constant for New Column
- Open `app/core/constants.py`
- Add `EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT: str = 'layer_unique_block_count'` after line 41 (after EXCEL_COLUMN_LAYER_ENTITY_COUNT)
- Add inline comment: `# See app_docs/005-field-naming-convention.md for naming conventions`
- Verify constant follows snake_case pattern

### 2. Update ExtractionResult TypedDict
- Open `app/core/extractor.py`
- Add `layer_unique_block_counts: dict[str, int]` field to ExtractionResult TypedDict (around line 305)
- Add it after `layer_entity_counts` and before `entity_type_counts`
- Update ExtractionResult docstring to document the new field:
  - "layer_unique_block_counts: Dictionary mapping layer names to count of distinct block types on that layer"
  - Include example: `{'Piping': 15, 'Equipment': 8}` (meaning Piping layer has 15 different block types)

### 3. Implement Layer Unique Block Count Calculation
- In `extract_blocks()` function, after the block_layer_pairs is fully populated (around line 432)
- Add calculation logic:
  ```python
  # Calculate unique blocks per layer
  layer_unique_block_counts: dict[str, int] = {}
  for (block_name, layer_name) in block_layer_pairs.keys():
      if layer_name not in layer_unique_block_counts:
          layer_unique_block_counts[layer_name] = 0
      # This counts unique blocks by iterating through all pairs

  # Properly count unique blocks per layer
  for layer_name in layer_entity_counts.keys():
      unique_blocks = set(
          block_name for (block_name, layer) in block_layer_pairs.keys()
          if layer == layer_name
      )
      layer_unique_block_counts[layer_name] = len(unique_blocks)
  ```
- Add to the logger info section (around line 444): `logger.info(f"Calculated unique block counts for {len(layer_unique_block_counts)} layers")`
- Add `layer_unique_block_counts` to the returned ExtractionResult dictionary (around line 456)
- Update extract_blocks() docstring examples to include layer_unique_block_counts

### 4. Write Unit Tests for Extraction
- Open `app/tests/core/test_extractor.py`
- Add test `test_extract_layer_unique_block_counts()`:
  - Verify layer_unique_block_counts is present in ExtractionResult
  - Verify all values are non-negative integers
  - Verify keys match layer_entity_counts keys (all layers present)
- Add test `test_layer_unique_block_counts_accuracy()`:
  - Create sample data with known block-layer relationships
  - Verify count calculation is accurate
  - Example: Layer1 has DOOR and WINDOW → unique count should be 2
- Add test `test_layer_unique_block_counts_empty()`:
  - Test with empty file
  - Verify layer_unique_block_counts is empty dict
- Add test `test_layer_unique_block_counts_single_block_type()`:
  - Layer with multiple insertions of single block type → unique count = 1
  - Verify edge case handling

### 5. Update Layer Analysis Sheet Column Structure
- Open `app/core/excel_writer.py`
- Import the new constant at the top: Add `EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT` to the import from constants (around line 44)
- In `_create_layer_analysis_sheet()` function (around line 186):
  - Add layer_unique_block_counts extraction: `layer_unique_block_counts = data['layer_unique_block_counts']`
  - In the row building loop (around line 196), add:
    ```python
    unique_block_count = layer_unique_block_counts.get(layer_name, 0)
    ```
  - Add to the rows.append() dict (around line 198):
    ```python
    EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT: unique_block_count
    ```
  - Update empty DataFrame columns list (around line 208) to include EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT as the 4th column
- Update function docstring to mention the 4-column structure
- Verify column order: layer_name, layer_block_insertion_count, layer_entity_count, layer_unique_block_count

### 6. Update Layer Analysis Sheet Formatting
- In `_format_layer_analysis_sheet()` function (around line 259):
  - Add column width for column D: `ws.column_dimensions['D'].width = 25  # layer_unique_block_count`
  - Match the width of other count columns (25) for consistency

### 7. Write Unit Tests for Excel Generation
- Open `app/tests/core/test_excel_writer.py`
- Update `test_layer_analysis_sheet_structure()` (around line 151):
  - Add EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT to the import at top of file
  - Update expected columns list to include 4 columns
  - Verify layer_unique_block_count column exists and has correct data
- Add test `test_layer_analysis_unique_block_count_accuracy()`:
  - Use sample_extraction_data fixture
  - Verify Layer1 has correct unique block count (should be 3: VALVE, PIPE, TAG)
  - Verify Layer2 has correct unique block count (should be 1: VALVE only)
- Update `test_all_sheets_column_widths()` (around line 233):
  - Add assertion for column D width: `assert ws_layers.column_dimensions['D'].width == 25  # layer_unique_block_count`
- Update `test_empty_data_all_sheets()` (around line 263):
  - Update layer_entity_counts assertion to verify 4 columns
  - Add EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT to expected columns
- Update `sample_extraction_data` fixture (around line 62):
  - Add `layer_unique_block_counts` field:
    ```python
    'layer_unique_block_counts': {'Layer1': 3, 'Layer2': 1}
    ```
  - Layer1 has VALVE, PIPE, TAG → 3 unique blocks
  - Layer2 has VALVE only → 1 unique block

### 8. Update Empty Data Test Fixture
- Ensure all tests that use empty ExtractionResult data include the new field
- Search for `ExtractionResult` dictionaries in test files and add `'layer_unique_block_counts': {}`

### 9. Validation - Run All Tests
- Execute `uv run pytest app/tests/core/test_extractor.py -v` to validate extraction tests pass
- Execute `uv run pytest app/tests/core/test_excel_writer.py -v` to validate Excel writer tests pass
- Execute `uv run pytest app/tests/ -v` to run full test suite and ensure zero regressions
- Execute `uv run mypy app/` to verify type checking passes with strict mode
- Verify all tests pass without errors

### 10. Integration Testing with Real Files
- Execute `bash scripts/start.sh` to launch the GUI application
- Select `app/tests/assets/sample_drawing.dxf`
- Click Extract button and verify Excel opens automatically
- Verify Layer Analysis sheet has 4 columns with correct headers
- Manually verify layer_unique_block_count values are accurate by cross-referencing with Block Counts sheet
- Verify sorting by layer_entity_count descending is maintained
- Verify auto-filter works on all 4 columns
- Close application and verify no errors in logs

## Testing Strategy

### Unit Tests

**Extractor Tests (test_extractor.py)**
- `test_extract_layer_unique_block_counts()`: Verify layer_unique_block_counts field exists in ExtractionResult
- `test_layer_unique_block_counts_types()`: Verify all values are non-negative integers
- `test_layer_unique_block_counts_keys()`: Verify keys match layers from layer_entity_counts
- `test_layer_unique_block_counts_accuracy()`: Verify count calculation correctness with known data
- `test_layer_unique_block_counts_empty()`: Verify empty file returns empty dict
- `test_layer_unique_block_counts_single_block()`: Verify layer with single block type returns count of 1
- `test_layer_unique_block_counts_multiple_insertions()`: Verify multiple insertions of same block count as 1 unique

**Excel Writer Tests (test_excel_writer.py)**
- `test_layer_analysis_has_unique_block_count_column()`: Verify Layer Analysis has 4 columns with layer_unique_block_count
- `test_layer_unique_block_count_values()`: Verify counts are accurate in Excel output
- `test_layer_unique_block_count_column_width()`: Verify column D has width of 25
- `test_layer_unique_block_count_empty_data()`: Verify empty data creates 4-column headers
- `test_layer_unique_block_count_sorting_preserved()`: Verify adding column doesn't break descending sort

### Integration Tests

**Full Pipeline Test**
- Load sample_drawing.dxf → extract → generate Excel → verify Layer Analysis sheet
- Count unique blocks manually from Block Counts sheet, compare to layer_unique_block_count column
- Verify layer with 10 insertions of 1 block type shows unique count = 1
- Verify layer with 10 insertions of 5 block types shows unique count = 5

### Edge Cases

**Empty Layer**
- Layer with no block insertions (only non-block entities) → layer_unique_block_count = 0

**Single Block Type**
- Layer with 100 insertions of DOOR block only → layer_unique_block_count = 1

**High Diversity Layer**
- Layer with 100 insertions of 50 different block types → layer_unique_block_count = 50

**Layer with No Blocks**
- Layer with only LINE, CIRCLE entities (no INSERT entities) → layer_unique_block_count = 0

**Empty File**
- File with no entities → layer_unique_block_counts = {} → Excel sheet with headers only

### Playwright MCP Tests

**GUI Workflow Test**
- Launch app → select file → extract → verify Layer Analysis sheet has 4 columns
- Verify layer_unique_block_count column is readable and properly formatted
- Verify auto-filter works on all 4 columns including the new one
- Test with multiple DWG/DXF files to ensure consistency

**Data Validation Test**
- Open Excel file → sort by layer_unique_block_count descending
- Verify layers with highest block diversity appear first
- Filter layer_unique_block_count > 10 → verify only complex layers shown

## Acceptance Criteria

1. **Data Model**
   - ExtractionResult includes `layer_unique_block_counts: dict[str, int]` field
   - layer_unique_block_counts correctly maps layer names to count of distinct block types
   - Keys in layer_unique_block_counts match keys in layer_entity_counts (all layers present)

2. **Calculation Accuracy**
   - Unique block count accurately reflects distinct block types per layer
   - Multiple insertions of same block type count as 1 unique block
   - Layers with no blocks have unique count of 0
   - Empty files produce empty layer_unique_block_counts dict

3. **Excel Output**
   - Layer Analysis sheet displays 4 columns: layer_name, layer_block_insertion_count, layer_entity_count, layer_unique_block_count
   - New column appears as 4th column (after layer_entity_count)
   - Rows remain sorted by layer_entity_count descending
   - Auto-filter applies to all 4 columns
   - Column D has width of 25 for consistency

4. **Type Safety**
   - All type hints are correct and mypy passes with zero errors
   - layer_unique_block_counts is properly typed as dict[str, int]

5. **Testing**
   - All new unit tests pass
   - All existing tests pass (zero regressions)
   - Test coverage includes edge cases (empty data, single block type, high diversity)

6. **Code Quality**
   - Field naming follows app_docs/005-field-naming-convention.md
   - Constant EXCEL_COLUMN_LAYER_UNIQUE_BLOCK_COUNT follows established pattern
   - Docstrings updated to reflect new functionality
   - Logging statements added for observability

7. **User Experience**
   - GUI workflow unchanged (browse → extract → auto-open Excel)
   - Excel file opens successfully with new column
   - Data is easily readable and properly formatted
   - No breaking changes to existing sheets (Block Counts, Entity Summary, Block Trimming Analysis)

8. **Performance**
   - Calculation adds negligible overhead (single iteration through existing block_layer_pairs)
   - No impact on extraction or Excel generation time

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Validate extractor tests pass with new layer unique block count logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate Excel writer tests pass with new column
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage includes new code
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI and manually test extraction with sample_drawing.dxf to verify Layer Analysis sheet has 4 columns with accurate data

## Notes

### Field Naming Convention Compliance
The new field follows the established convention from app_docs/005-field-naming-convention.md:
- `layer_unique_block_count` - follows {domain}_{qualifier}_{attribute}_{type} pattern
- Domain: `layer` (layer-based metric)
- Qualifier: `unique` (distinct/non-duplicate)
- Attribute: `block` (block type)
- Type: `count` (count of unique blocks)
- Matches the pattern from the convention guide: `layer_unique_block_count` (distinct block count per layer)

### Calculation Efficiency
The calculation is performed using existing data structures:
- No additional file parsing required
- Single pass through block_layer_pairs dictionary keys
- Time complexity: O(n) where n = number of block-layer pairs
- Memory complexity: O(m) where m = number of layers
- Typical performance impact: < 1ms for drawings with hundreds of layers

### Business Value
This metric provides actionable insights:
- **Complexity Analysis**: High unique block count indicates complex layer organization
- **Standardization**: Low unique block count on multiple layers suggests good standardization
- **Quality Control**: Unexpected unique block counts can reveal drafting errors
- **Planning**: Helps estimate effort for layer-specific modifications

### Alternative Considered: Inline Calculation
An alternative approach would calculate unique block counts inline during the Excel generation phase. This was rejected because:
- Violates separation of concerns (extraction vs. presentation)
- Would require recalculating if multiple export formats are added
- Makes testing more complex (can't test extraction independently)
- Current approach follows established pattern (calculate during extraction, use during export)

### Future Enhancements
This feature enables additional layer analysis capabilities:
- Add `layer_dominant_block` column (most common block on layer)
- Add `layer_block_names` column (comma-separated list of block types)
- Pivot table: layers as rows, block types as columns, insertion counts as values
- Filtering: "Show only layers with > 10 unique block types"
- Correlation analysis: layer_unique_block_count vs layer_block_insertion_count (diversity ratio)
