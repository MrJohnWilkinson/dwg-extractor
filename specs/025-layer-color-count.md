# Feature: Add Color Count Column to Layer Analysis

## Feature Description
This feature adds a new column to the Layer Analysis worksheet that displays the count of unique RGB color values for all entities on each layer. The column will be automatically calculated for all layers found in the DXF file, maintaining consistency with existing formatting patterns including frozen headers, auto-filtering, and appropriate text alignment.

The feature enhances layer analysis by providing visibility into color diversity per layer, helping users identify layers with varying color schemes versus uniform coloring.

## User Story
As a CAD analyst
I want to see the number of unique colors used on each layer
So that I can identify layers with complex color schemes and understand layer color standardization

## Problem Statement
Currently, the Layer Analysis worksheet provides layer names, block insertion counts, and entity counts, but does not show color diversity information. Users cannot easily identify which layers use multiple colors versus layers with uniform coloring. This information is valuable for:
- Identifying non-standard color usage
- Understanding layer complexity
- Validating CAD standards compliance
- Planning layer cleanup or standardization efforts

## Solution Statement
Add a `layer_unique_color_count` column to the Layer Analysis worksheet that:
1. Extracts RGB color values from all entities on each layer
2. Counts distinct color values per layer
3. Displays the count in a new column after existing layer columns
4. Applies consistent formatting (right-aligned values, left-aligned header, frozen header row, auto-filter)
5. Follows the established field naming convention from `app_docs/005-field-naming-convention.md`

## Relevant Files
Use these files to implement the feature:

**Core Application Files:**
- `app/core/constants.py` - Add `EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT` constant definition
  - Follows existing pattern of EXCEL_COLUMN_* constants for layer domain fields

- `app/core/extractor.py` - Extract color data during layer entity analysis
  - Modify `ExtractionResult` TypedDict to include `layer_unique_color_counts` field
  - Add logic in `extract_blocks()` to track unique RGB colors per layer when iterating through entities
  - Access entity color information from ezdxf entity objects

- `app/core/excel_writer.py` - Add color count column to Layer Analysis sheet
  - Modify `_create_layer_analysis_sheet()` to include the new column in DataFrame creation
  - Ensure proper column ordering (after layer_entity_count)

- `app/core/excel_formatting.py` - Apply formatting to color count column
  - Modify `_format_layer_analysis_sheet()` to set column width for new column
  - Apply right-alignment to color count values (similar to other numeric columns)

**Test Files:**
- `app/tests/core/test_extractor.py` - Add unit tests for color extraction logic
  - Test color counting for layers with single color
  - Test color counting for layers with multiple colors
  - Test color counting for layers with no entities
  - Verify `layer_unique_color_counts` key exists in ExtractionResult

- `app/tests/core/test_excel_writer.py` - Add tests for Excel column generation
  - Verify color count column appears in Layer Analysis sheet
  - Test proper column ordering
  - Test header formatting

- `app/tests/core/test_excel_formatting.py` - Add tests for formatting
  - Verify column width is set appropriately
  - Verify right-alignment of color count values

**Test Assets:**
- `app/tests/assets/` - Use existing test DXF files that contain layers with entities
  - `sample_drawing.dxf` - Existing test file with multiple layers
  - May need to create additional test asset if color diversity testing is needed

### New Files
No new files are required. All changes will be made to existing files.

## Implementation Plan

### Phase 1: Foundation
1. Review ezdxf documentation for entity color access patterns
2. Understand how ezdxf represents colors (RGB, ACI color index, true color)
3. Determine color normalization approach (handle both RGB and ACI colors)
4. Define the data structure for tracking color counts per layer

### Phase 2: Core Implementation
1. Add constant definition in `constants.py`
2. Modify `ExtractionResult` TypedDict in `extractor.py` to include new field
3. Implement color extraction logic in `extract_blocks()` function
4. Extract and normalize color values from entities during layer iteration
5. Track unique colors per layer in a dictionary

### Phase 3: Integration
1. Modify `_create_layer_analysis_sheet()` to include color count column
2. Add column to DataFrame with proper ordering
3. Modify `_format_layer_analysis_sheet()` to apply formatting
4. Set column width and alignment for the new column
5. Verify frozen headers and auto-filter include the new column

## Step by Step Tasks

### Step 1: Add Constant Definition
- Open `app/core/constants.py`
- Add `EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT: str = "layer_unique_color_count"` after line 45 (after `EXCEL_COLUMN_LAYER_ENTITY_COUNT`)
- Follow naming convention from `app_docs/005-field-naming-convention.md` (domain: layer, attribute: unique, qualifier: color, suffix: count)

### Step 2: Update ExtractionResult TypedDict
- Open `app/core/extractor.py`
- Locate `ExtractionResult` TypedDict (around line 33)
- Add `layer_unique_color_counts: dict[str, int]` field in the TypedDict definition
- Update docstring to document the new field with examples
- Follow the existing pattern for layer-based dictionaries

### Step 3: Implement Color Extraction Logic
- In `app/core/extractor.py`, locate the `extract_blocks()` function
- Initialize `layer_unique_color_counts: dict[str, set[tuple[int, int, int]]] = {}` to track unique RGB colors per layer
- During entity iteration (around line 194), extract entity color information:
  - Access `entity.dxf.color` for ACI color index
  - Access `entity.rgb` or `entity.dxf.true_color` for RGB values if available
  - Handle both ACI colors (convert to RGB) and true color (direct RGB)
  - Store colors as RGB tuples `(r, g, b)` for consistency
- Add colors to the set for the corresponding layer
- Before returning result, convert sets to counts: `layer_unique_color_counts_final: dict[str, int] = {layer: len(colors) for layer, colors in layer_unique_color_counts.items()}`
- Add field to returned `ExtractionResult` dictionary
- Update logging to report color extraction statistics

### Step 4: Write Unit Tests for Extractor
- Open `app/tests/core/test_extractor.py`
- Add test method `test_extract_layer_color_counts()`:
  - Extract from `sample_drawing.dxf`
  - Verify `layer_unique_color_counts` key exists in result
  - Verify values are integers
  - Verify all layers have color count entries (including 0 for empty layers)
- Add test method `test_extract_layer_color_counts_empty_file()`:
  - Extract from `empty_drawing.dxf`
  - Verify `layer_unique_color_counts` is an empty or zero-filled dictionary
- Run tests: `uv run pytest app/tests/core/test_extractor.py -v`

### Step 5: Update Excel Writer to Include Color Count Column
- Open `app/core/excel_writer.py`
- Import the new constant at the top
- Locate `_create_layer_analysis_sheet()` function (around line 311)
- Add `layer_unique_color_counts = data["layer_unique_color_counts"]` to extract the data
- In the row building loop (around line 323), add:
  - `color_count = layer_unique_color_counts.get(layer_name, 0)`
  - Add `EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT: color_count` to the row dictionary
- Update the empty DataFrame creation (around line 340) to include the new column in the columns list
- Ensure proper column order: layer_name, layer_block_insertion_count, layer_entity_count, layer_unique_color_count
- Update logging statement if needed

### Step 6: Apply Excel Formatting to New Column
- Open `app/core/excel_formatting.py`
- Locate `_format_layer_analysis_sheet()` function (around line 108)
- Add column width setting: `ws.column_dimensions["D"].width = 25  # layer_unique_color_count`
- Add right-alignment to color count column values (rows 2 onwards, column D)
- Create alignment object: `right_alignment = Alignment(horizontal="right")`
- Apply to column D data rows:
  ```python
  for row_idx in range(2, ws.max_row + 1):
      ws.cell(row=row_idx, column=4).alignment = right_alignment
  ```
- Headers remain left-aligned (already handled by existing header formatting)
- Update logger message to mention color count column formatting

### Step 7: Write Unit Tests for Excel Writer
- Open `app/tests/core/test_excel_writer.py`
- Add test to verify Layer Analysis sheet includes color count column:
  - Create test with mock ExtractionResult data including `layer_unique_color_counts`
  - Call `write_excel()` and load resulting workbook
  - Verify Layer Analysis sheet has 4 columns
  - Verify column headers include "Layer Unique Color Count"
  - Verify data values are present
- Run tests: `uv run pytest app/tests/core/test_excel_writer.py -v`

### Step 8: Write Unit Tests for Excel Formatting
- Open `app/tests/core/test_excel_formatting.py`
- Add test to verify Layer Analysis formatting includes new column:
  - Create test workbook with Layer Analysis sheet containing 4 columns
  - Call `_format_layer_analysis_sheet()`
  - Verify column D width is set to 25
  - Verify column D data cells (row 2+) have right-alignment
  - Verify auto-filter includes column D
- Run tests: `uv run pytest app/tests/core/test_excel_formatting.py -v`

### Step 9: Integration Testing
- Run full test suite: `uv run pytest app/tests/`
- Verify all tests pass with zero failures
- Check for any type checking errors: `uv run mypy app/`
- Fix any issues discovered

### Step 10: Manual End-to-End Testing
- Run the application: `bash scripts/start.sh`
- Load a test DXF file with multiple layers and varying colors
- Verify the generated Excel file includes Layer Analysis sheet with 4 columns
- Verify "Layer Unique Color Count" column appears after "Layer Entity Count"
- Verify color count values are displayed correctly
- Verify right-alignment of color count values
- Verify frozen header row includes new column
- Verify auto-filter works on all columns including the new one

### Step 11: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Testing Strategy

### Unit Tests

**Extractor Tests (`test_extractor.py`):**
- `test_extract_layer_color_counts()` - Verify color counts are extracted for each layer
- `test_extract_layer_color_counts_empty_file()` - Verify empty file handling
- `test_extract_layer_color_counts_types()` - Verify return types are correct
- `test_extract_layer_color_counts_multi_color()` - Test layers with multiple colors

**Excel Writer Tests (`test_excel_writer.py`):**
- `test_layer_analysis_includes_color_count()` - Verify column is added to sheet
- `test_layer_analysis_column_order()` - Verify correct column ordering
- `test_layer_analysis_color_count_values()` - Verify data values are correct
- `test_layer_analysis_empty_data()` - Test with empty extraction data

**Excel Formatting Tests (`test_excel_formatting.py`):**
- `test_layer_analysis_color_count_width()` - Verify column width
- `test_layer_analysis_color_count_alignment()` - Verify right-alignment of values
- `test_layer_analysis_header_alignment()` - Verify left-alignment of header

### Integration Tests
- Test full workflow: extract blocks → create Excel → apply formatting
- Verify all sheets remain functional after adding new column
- Test with various DXF files (empty, single layer, multiple layers)
- Verify color extraction handles different color types (ACI, RGB, true color)

### Edge Cases
1. **Layer with no entities** - Should show 0 color count
2. **Layer with all entities same color** - Should show 1 color count
3. **Layer with entities using ACI colors** - Should properly convert and count
4. **Layer with entities using RGB true colors** - Should properly extract and count
5. **Layer with mixed color types** - Should normalize and count correctly
6. **Empty DXF file** - Should not crash, return empty or zero-filled dictionary
7. **Layer with ByLayer color** - Should handle gracefully
8. **Layer with ByBlock color** - Should handle gracefully

### Playwright MCP Tests
Not applicable for this feature. The feature involves data extraction and Excel generation, which are better suited for unit and integration tests. GUI testing is not required for this backend functionality.

## Acceptance Criteria
1. ✅ New constant `EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT` is defined in `constants.py`
2. ✅ `ExtractionResult` TypedDict includes `layer_unique_color_counts` field
3. ✅ Color extraction logic correctly counts unique colors per layer
4. ✅ Color extraction handles both ACI and RGB color formats
5. ✅ Layer Analysis worksheet includes new column after existing columns
6. ✅ Column header displays as "Layer Unique Color Count" (Title Case)
7. ✅ Color count values are right-aligned
8. ✅ Column header is left-aligned (consistent with other headers)
9. ✅ Frozen header row includes the new column
10. ✅ Auto-filter includes the new column
11. ✅ Column width is set appropriately (25 units)
12. ✅ All unit tests pass
13. ✅ Type checking passes with no errors
14. ✅ Manual testing confirms correct display in Excel
15. ✅ Zero regressions in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests to validate color extraction logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests to validate column creation
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run formatting tests to validate alignment and width
- `uv run pytest app/tests/ -v` - Run complete test suite to ensure zero regressions
- `uv run pytest --cov=app/core app/tests/` - Run tests with coverage to verify new code is tested
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint code for style issues
- `bash scripts/start.sh` - Launch application for manual testing

## Notes

### Color Extraction Considerations
- **ACI Colors**: AutoCAD Color Index (0-256) colors need to be converted to RGB for consistency
- **True Color**: Direct RGB values should be used as-is
- **ByLayer/ByBlock**: These special color values indicate inheritance and should be handled appropriately
- **Color Normalization**: All colors should be stored as RGB tuples (r, g, b) for consistent comparison

### ezdxf Color API
Based on ezdxf documentation, entity colors can be accessed via:
- `entity.dxf.color` - ACI color index (integer 0-256)
- `entity.rgb` - RGB tuple if available
- `entity.dxf.true_color` - 24-bit true color value

Need to research exact API and determine best approach for color extraction and normalization.

### Future Enhancements
- Display color palette visualization in Excel (conditional formatting by color)
- Add layer color mode analysis (dominant color per layer)
- Export color usage statistics to separate sheet
- Add color standardization recommendations

### Performance Considerations
- Color extraction adds minimal overhead as it occurs during existing entity iteration
- Using sets for unique color tracking is memory-efficient
- No additional file reads or complex operations required
