# Feature: Add Text/MText Count Column to Layer Analysis Worksheet

## Feature Description
This feature adds a new column to the Layer Analysis worksheet that displays the combined count of TEXT and MTEXT entities per layer. The column will be automatically calculated for all layers found in the DXF/DWG file, maintaining consistency with existing formatting patterns including frozen headers, auto-filtering, and appropriate text alignment.

The feature enhances layer analysis by providing visibility into text annotation density across layers, helping users identify heavily documented layers versus layers with minimal text content.

## User Story
As a CAD analyst
I want to see the number of text entities (TEXT + MTEXT) on each layer
So that I can identify layers with heavy documentation/annotation and understand which layers contain text-based information

## Problem Statement
Currently, the Layer Analysis worksheet provides layer names, block insertion counts, entity counts, and color counts, but does not show text entity distribution. Users cannot easily identify which layers contain text annotations (TEXT and MTEXT entities). This information is valuable for:
- Identifying annotation-heavy layers
- Understanding documentation density across the drawing
- Planning text extraction or migration efforts
- Validating layer organization standards (e.g., text should be on specific layers)
- Analyzing drawing complexity related to annotations

## Solution Statement
Add a `layer_text_mtext_count` column to the Layer Analysis worksheet that:
1. Counts TEXT entities on each layer during extraction
2. Counts MTEXT (multi-line text) entities on each layer during extraction
3. Combines both counts (TEXT + MTEXT) for each layer
4. Displays the total count in a new column after existing layer columns
5. Applies consistent formatting (right-aligned values, left-aligned header, frozen header row, auto-filter)
6. Follows the established field naming convention from `app_docs/005-field-naming-convention.md`

## Relevant Files
Use these files to implement the feature:

**Core Application Files:**
- `app/core/constants.py` - Add `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT` constant definition
  - Follows existing pattern of EXCEL_COLUMN_* constants for layer domain fields
  - Domain: layer, Attribute: text_mtext, Suffix: count

- `app/core/extractor.py` - Extract text entity counts during layer analysis
  - Modify `ExtractionResult` TypedDict to include `layer_text_mtext_counts` field
  - Add logic in `extract_blocks()` to track TEXT and MTEXT entity counts per layer when iterating through entities
  - Check entity type for "TEXT" and "MTEXT" using `entity.dxftype()`
  - Accumulate counts in a dictionary keyed by layer name

- `app/core/excel_writer.py` - Add text/mtext count column to Layer Analysis sheet
  - Modify `_create_layer_analysis_sheet()` to include the new column in DataFrame creation
  - Ensure proper column ordering (after layer_unique_color_count)

- `app/core/excel_formatting.py` - Apply formatting to text/mtext count column
  - Modify `_format_layer_analysis_sheet()` to set column width for new column
  - Apply right-alignment to count values (similar to other numeric columns)

**Test Files:**
- `app/tests/core/test_extractor.py` - Add unit tests for text/mtext counting logic
  - Test counting for layers with only TEXT entities
  - Test counting for layers with only MTEXT entities
  - Test counting for layers with both TEXT and MTEXT entities
  - Test counting for layers with no text entities (should be 0)
  - Verify `layer_text_mtext_counts` key exists in ExtractionResult

- `app/tests/core/test_excel_writer.py` - Add tests for Excel column generation
  - Verify text/mtext count column appears in Layer Analysis sheet
  - Test proper column ordering (5th column)
  - Test header formatting

- `app/tests/core/test_excel_formatting.py` - Add tests for formatting
  - Verify column width is set appropriately
  - Verify right-alignment of count values

**Test Assets:**
- `app/tests/assets/` - Use existing test DXF files or create new ones
  - May need to create a new test asset with TEXT and MTEXT entities on different layers
  - Use generator script pattern similar to other test assets (e.g., `create_text_mtext_test.py`)

### New Files
- `app/tests/assets/create_text_mtext_test.py` - Generator script for test asset (optional)
  - Creates a DXF file with TEXT and MTEXT entities on various layers
  - Provides known entity counts for test validation

- `app/tests/assets/text_mtext_test.dxf` - Test asset with TEXT/MTEXT entities (optional)
  - Contains multiple layers with varying text entity counts
  - Used for unit test validation

## Implementation Plan

### Phase 1: Foundation
1. Review ezdxf documentation for TEXT and MTEXT entity types
2. Understand entity type identification using `entity.dxftype()`
3. Verify TEXT and MTEXT are separate entity types that need individual counting
4. Define the data structure for tracking text/mtext counts per layer
5. Review existing entity counting pattern in `extractor.py` for consistency

### Phase 2: Core Implementation
1. Add constant definition in `constants.py`
2. Modify `ExtractionResult` TypedDict in `extractor.py` to include new field
3. Implement text/mtext counting logic in `extract_blocks()` function
4. Track TEXT and MTEXT entity counts per layer during entity iteration
5. Initialize all layers with 0 text counts (matching layer initialization pattern)
6. Update logging to report text extraction statistics

### Phase 3: Integration
1. Modify `_create_layer_analysis_sheet()` to include text/mtext count column
2. Add column to DataFrame with proper ordering (5th column)
3. Modify `_format_layer_analysis_sheet()` to apply formatting
4. Set column width and alignment for the new column
5. Verify frozen headers and auto-filter include the new column

## Step by Step Tasks

### Step 1: Add Constant Definition
- Open `app/core/constants.py`
- Add `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT: str = "layer_text_mtext_count"` after line 47 (after `EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT`)
- Follow naming convention from `app_docs/005-field-naming-convention.md`
- Add inline comment explaining the field: `# Domain: layer, Attribute: text_mtext (combined TEXT + MTEXT entities), Suffix: count`

### Step 2: Update ExtractionResult TypedDict
- Open `app/core/extractor.py`
- Locate `ExtractionResult` TypedDict (around line 33)
- Add `layer_text_mtext_counts: dict[str, int]` field in the TypedDict definition (after `layer_unique_color_counts`)
- Update the docstring to document the new field:
  ```
  layer_text_mtext_counts: Dictionary mapping layer names to combined TEXT and MTEXT entity counts
                          Counts both TEXT (single-line) and MTEXT (multi-line) entities on each layer
                          Example: {'NOTES': 25, 'TITLE_BLOCK': 8, 'DIMENSIONS': 0}
  ```

### Step 3: Implement Text/MText Counting Logic
- In `app/core/extractor.py`, locate the `extract_blocks()` function
- Initialize `layer_text_mtext_counts: dict[str, int] = {}` after line 151 (with other layer initialization)
- In the layer initialization loop (around line 156), initialize text counts:
  ```python
  layer_text_mtext_counts[layer_name] = 0
  ```
- During entity iteration (around line 198), add text entity counting logic after entity type counting (around line 204):
  ```python
  # Count TEXT and MTEXT entities per layer
  if entity_type in ("TEXT", "MTEXT"):
      layer_text_mtext_counts[layer_name] = layer_text_mtext_counts.get(layer_name, 0) + 1
  ```
- Before returning result (around line 310), add logging:
  ```python
  total_text_entities = sum(layer_text_mtext_counts.values())
  logger.info(f"Found {total_text_entities} TEXT/MTEXT entities across {len(layer_text_mtext_counts)} layers")
  ```
- Add `layer_text_mtext_counts` field to the returned `ExtractionResult` dictionary (around line 320)

### Step 4: Write Unit Tests for Extractor
- Open `app/tests/core/test_extractor.py`
- Add test method `test_extract_layer_text_mtext_counts()`:
  ```python
  def test_extract_layer_text_mtext_counts(self) -> None:
      """Test extraction of TEXT and MTEXT entity counts per layer."""
      result = extract_blocks("app/tests/assets/sample_drawing.dxf")

      # Verify key exists
      assert "layer_text_mtext_counts" in result

      # Verify all values are integers
      for count in result["layer_text_mtext_counts"].values():
          assert isinstance(count, int)
          assert count >= 0

      # Verify all layers have entries (even if 0)
      for layer_name in result["layer_entity_counts"].keys():
          assert layer_name in result["layer_text_mtext_counts"]
  ```
- Add test method `test_extract_layer_text_mtext_counts_empty_file()`:
  ```python
  def test_extract_layer_text_mtext_counts_empty_file(self) -> None:
      """Test text/mtext counts for empty drawing."""
      result = extract_blocks("app/tests/assets/empty_drawing.dxf")

      assert "layer_text_mtext_counts" in result
      assert isinstance(result["layer_text_mtext_counts"], dict)
  ```
- Run tests: `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_extract_layer_text_mtext_counts -v`
- Run tests: `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_extract_layer_text_mtext_counts_empty_file -v`

### Step 5: Create Test Asset with TEXT/MTEXT Entities (Optional)
- Create `app/tests/assets/create_text_mtext_test.py` generator script:
  - Create a DXF with multiple layers
  - Add TEXT entities to specific layers with known counts
  - Add MTEXT entities to specific layers with known counts
  - Mix both on some layers
  - Leave some layers without text entities
  - Save as `app/tests/assets/text_mtext_test.dxf`
- Run generator: `uv run python app/tests/assets/create_text_mtext_test.py`
- Add type annotations to the generator script
- Add specific test using this asset with known counts

### Step 6: Update Excel Writer to Include Text/MText Count Column
- Open `app/core/excel_writer.py`
- Import the new constant at the top (around line 44):
  ```python
  EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT,
  ```
- Locate `_create_layer_analysis_sheet()` function (around line 312)
- Add data extraction (around line 320):
  ```python
  layer_text_mtext_counts = data["layer_text_mtext_counts"]
  ```
- In the row building loop (around line 327), add to the row dictionary:
  ```python
  text_mtext_count = layer_text_mtext_counts.get(layer_name, 0)
  ```
  And add to row dict:
  ```python
  EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT: text_mtext_count,
  ```
- Update the empty DataFrame creation (around line 343) to include the new column:
  ```python
  EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT,
  ```
- Ensure proper column order: layer_name, layer_block_insertion_count, layer_entity_count, layer_unique_color_count, layer_text_mtext_count

### Step 7: Apply Excel Formatting to New Column
- Open `app/core/excel_formatting.py`
- Locate `_format_layer_analysis_sheet()` function (around line 108)
- Update column width setting (add after existing column width settings):
  ```python
  ws.column_dimensions["E"].width = 25  # layer_text_mtext_count
  ```
- Add right-alignment to text/mtext count column values (column E, rows 2+)
- Update the existing alignment loop to include column E:
  ```python
  # Right-align numeric columns (B, C, D, E)
  for row_idx in range(2, ws.max_row + 1):
      for col in ["B", "C", "D", "E"]:
          ws.cell(row=row_idx, column=column_index_from_string(col)).alignment = right_alignment
  ```
- Update logger message to mention text/mtext count column formatting

### Step 8: Write Unit Tests for Excel Writer
- Open `app/tests/core/test_excel_writer.py`
- Add or update test to verify Layer Analysis sheet includes text/mtext count column:
  - Create test with mock ExtractionResult data including `layer_text_mtext_counts`
  - Call `write_excel()` and load resulting workbook
  - Verify Layer Analysis sheet has 5 columns
  - Verify column headers include "Layer Text Mtext Count"
  - Verify data values are present and correct
- Run tests: `uv run pytest app/tests/core/test_excel_writer.py -v`

### Step 9: Write Unit Tests for Excel Formatting
- Open `app/tests/core/test_excel_formatting.py`
- Add or update test to verify Layer Analysis formatting includes new column:
  - Create test workbook with Layer Analysis sheet containing 5 columns
  - Call `_format_layer_analysis_sheet()`
  - Verify column E width is set to 25
  - Verify column E data cells (row 2+) have right-alignment
  - Verify auto-filter includes column E
- Run tests: `uv run pytest app/tests/core/test_excel_formatting.py -v`

### Step 10: Type Checking
- Run mypy to verify type annotations are correct: `uv run mypy app/`
- Fix any type errors that appear
- Ensure all new code has proper type hints

### Step 11: Integration Testing
- Run full test suite: `uv run pytest app/tests/ -v`
- Verify all tests pass with zero failures
- Check for any regressions in existing functionality
- Fix any issues discovered

### Step 12: Manual End-to-End Testing
- Run the application: `bash scripts/start.sh`
- Load a test DXF file with TEXT and MTEXT entities on various layers
- Verify the generated Excel file includes Layer Analysis sheet with 5 columns
- Verify "Layer Text Mtext Count" column appears as the last column
- Verify text/mtext count values are displayed correctly
- Verify right-alignment of count values
- Verify frozen header row includes new column
- Verify auto-filter works on all columns including the new one
- Test sorting by the new column to verify numeric sorting works correctly

### Step 13: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Testing Strategy

### Unit Tests

**Extractor Tests (`test_extractor.py`):**
- `test_extract_layer_text_mtext_counts()` - Verify TEXT and MTEXT counts are extracted for each layer
- `test_extract_layer_text_mtext_counts_empty_file()` - Verify empty file handling
- `test_extract_layer_text_mtext_counts_types()` - Verify return types are integers >= 0
- `test_extract_layer_text_mtext_counts_combined()` - Test layers with both TEXT and MTEXT entities
- `test_extract_layer_text_mtext_counts_zero()` - Test layers with no text entities show 0

**Excel Writer Tests (`test_excel_writer.py`):**
- `test_layer_analysis_includes_text_mtext_count()` - Verify column is added to sheet
- `test_layer_analysis_column_order()` - Verify correct column ordering (5 columns total)
- `test_layer_analysis_text_mtext_count_values()` - Verify data values are correct
- `test_layer_analysis_text_mtext_count_empty_data()` - Test with empty extraction data

**Excel Formatting Tests (`test_excel_formatting.py`):**
- `test_layer_analysis_text_mtext_count_width()` - Verify column width for column E
- `test_layer_analysis_text_mtext_count_alignment()` - Verify right-alignment of values
- `test_layer_analysis_text_mtext_count_header()` - Verify left-alignment of header

### Integration Tests
- Test full workflow: extract blocks → create Excel → apply formatting
- Verify all sheets remain functional after adding new column
- Test with various DXF files (empty, no text entities, mixed text entities)
- Verify counting handles both TEXT and MTEXT entity types correctly
- Verify all layers get initialized with 0 counts

### Edge Cases
1. **Layer with no entities** - Should show 0 text count
2. **Layer with only TEXT entities** - Should show correct TEXT count
3. **Layer with only MTEXT entities** - Should show correct MTEXT count
4. **Layer with both TEXT and MTEXT** - Should show combined count (TEXT + MTEXT)
5. **Layer with entities but no text** - Should show 0 text count
6. **Empty DXF file** - Should not crash, return empty or zero-filled dictionary
7. **All layers have text entities** - Should count all correctly
8. **Layer names with special characters** - Should handle layer names correctly

### Playwright MCP Tests
Not applicable for this feature. The feature involves data extraction and Excel generation, which are better suited for unit and integration tests. GUI testing is not required for this backend functionality.

## Acceptance Criteria
1. ✅ New constant `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT` is defined in `constants.py`
2. ✅ `ExtractionResult` TypedDict includes `layer_text_mtext_counts` field
3. ✅ Text/mtext counting logic correctly counts TEXT entities per layer
4. ✅ Text/mtext counting logic correctly counts MTEXT entities per layer
5. ✅ Counts are combined (TEXT + MTEXT) for each layer
6. ✅ All layers are initialized with 0 counts (consistent with existing pattern)
7. ✅ Layer Analysis worksheet includes new column as 5th column
8. ✅ Column header displays as "Layer Text Mtext Count" (Title Case)
9. ✅ Text/mtext count values are right-aligned
10. ✅ Column header is left-aligned (consistent with other headers)
11. ✅ Frozen header row includes the new column
12. ✅ Auto-filter includes the new column
13. ✅ Column width is set appropriately (25 units)
14. ✅ All unit tests pass
15. ✅ Type checking passes with no errors
16. ✅ Manual testing confirms correct display in Excel
17. ✅ Sorting by the new column works correctly (numeric sort)
18. ✅ Zero regressions in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to validate text/mtext counting logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests to validate column creation
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run formatting tests to validate alignment and width
- `uv run pytest app/tests/ -v` - Run complete test suite to ensure zero regressions
- `uv run pytest --cov=app/core app/tests/` - Run tests with coverage to verify new code is tested
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint code for style issues
- `bash scripts/start.sh` - Launch application for manual testing

## Notes

### Entity Type Identification
- **TEXT**: Single-line text entity, identified by `entity.dxftype() == "TEXT"`
- **MTEXT**: Multi-line text entity, identified by `entity.dxftype() == "MTEXT"`
- Both entity types should be counted separately and summed for the total
- Entity type checking is already implemented in the extractor for entity_type_counts

### Field Naming Rationale
- **Field Name**: `layer_text_mtext_count`
  - Domain: `layer` (follows established pattern)
  - Attribute: `text_mtext` (describes the specific entity types being counted)
  - Suffix: `count` (indicates a numeric count)
- **Constant Name**: `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT`
  - Follows the established EXCEL_COLUMN_{DOMAIN}_{ATTRIBUTE}_{SUFFIX} pattern
- **Excel Display**: "Layer Text Mtext Count"
  - Automatically generated by `format_header()` function
  - Title Case with proper spacing

### Implementation Pattern Consistency
This feature follows the same pattern as the recently implemented `layer_unique_color_count` feature:
1. Add constant to `constants.py`
2. Update `ExtractionResult` TypedDict
3. Add counting logic during entity iteration
4. Initialize all layers with 0 counts
5. Update Excel writer to include column
6. Update Excel formatting for proper display
7. Add comprehensive unit tests

### Performance Considerations
- Text/mtext counting adds minimal overhead as it occurs during existing entity iteration
- No additional file reads or complex operations required
- Simple entity type string comparison for filtering
- Dictionary lookups are O(1) operations

### Future Enhancements
- Separate TEXT and MTEXT into individual columns for more detailed analysis
- Add text content extraction and analysis
- Add text style analysis (font, size, alignment)
- Add text length statistics (min, max, average character count)
- Export text content to separate sheet for review
- Add text location analysis (bounding boxes, spatial distribution)

### Related Features
- `layer_unique_color_count` (spec 025) - Similar layer-based entity analysis pattern
- Entity Summary sheet - Already counts TEXT and MTEXT globally, this adds layer-based breakdown
