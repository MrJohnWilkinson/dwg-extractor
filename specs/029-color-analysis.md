# Feature: Color Analysis

## Feature Description
Create a new "Color Analysis" worksheet that provides a comprehensive view of all drawing entities grouped by color, layer, and entity type. The feature extracts Lines, Polylines, TEXT, and MTEXT entities from CAD drawings and groups them by their unique RGB color, layer name, and entity type combination. For geometric entities (Lines/Polylines), the worksheet displays aggregate counts. For text entities (TEXT/MTEXT), each annotation appears as a separate row with its full content displayed. The worksheet includes visual color samples showing the actual RGB color of each group.

This feature enables users to analyze color usage patterns across their drawings, understand which colors appear on which layers, identify annotation content by color, and audit color consistency across different entity types and layers.

## User Story
As a CAD drawing analyst
I want to see all drawing entities grouped by their color, layer name, and entity type with annotation contents
So that I can understand color usage patterns, identify which colors are used for specific purposes across different layers, audit text annotations by color, and ensure drawing consistency

## Problem Statement
Currently, the application tracks unique color counts per layer in the Layer Analysis sheet but does not provide detailed visibility into which specific colors are used, what entity types use those colors, or what annotations exist for each color. Users cannot:
- See which specific RGB colors are used throughout the drawing
- Understand how the same color is used across different layers (e.g., RED on "FIRE-SAFETY" vs "ELECTRICAL")
- Identify all text annotations that use a specific color
- Analyze geometric entity distribution by color and layer
- Audit color consistency across entity types
- View visual color samples for quick recognition
- Understand the relationship between colors, layers, and entity types

This makes it difficult to perform color-based quality control, standardize color usage, identify drawing inconsistencies, or understand how colors are applied across different drawing elements.

## Solution Statement
Add a new "Color Analysis" worksheet that extracts all LINE, LWPOLYLINE, POLYLINE, TEXT, and MTEXT entities from the drawing. Resolve each entity's color to RGB values (handling ByLayer, ByBlock, and ACI color indices). Group entities by unique (RGB color, layer name, entity type) combinations.

For geometric entities (Lines/Polylines), display aggregate counts with blank annotation contents. For text entities (TEXT/MTEXT), display each annotation individually with full text content. Sort results by RGB values (R, G, B ascending), then by layer name alphabetically, then by entity type alphabetically.

Display results in a formatted Excel sheet with:
- Annotation contents (wrapped text, blank for geometric entities)
- Layer name
- RGB color components (R, G, B as 0-255 integers)
- Visual color sample cell (background filled with actual RGB color)
- Entity type (Lines, Polylines, TEXT, MTEXT)
- Entity count

The worksheet provides both quantitative analysis (counts of geometric entities) and qualitative analysis (actual text content) organized by color usage patterns.

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Add new column name constants for Color Analysis sheet (EXCEL_COLUMN_COLOR_* series) following the `color_` domain naming convention. Add new sheet name constant EXCEL_SHEET_COLOR_ANALYSIS. These constants define the data structure and column identifiers for the new worksheet.

- **app/core/extractor.py** - Add new extraction method `extract_color_analysis()` to analyze all LINE, LWPOLYLINE, POLYLINE, TEXT, and MTEXT entities. Resolve entity colors to RGB using existing `_resolve_entity_color_to_rgb()` helper. Group Lines/Polylines by (RGB, layer, type) with aggregate counts. Extract TEXT/MTEXT individually with full content. Return sorted results by (R, G, B, layer, entity_type). Update ExtractionResult TypedDict to include color_analysis_data field.

- **app/core/excel_writer.py** - Add new function `_write_color_analysis_sheet()` to generate the Color Analysis worksheet. Create DataFrame from color analysis data with proper column structure. Handle both aggregate rows (Lines/Polylines with counts) and individual rows (TEXT/MTEXT with contents). Apply sorting by RGB then layer then entity type. Format column headers and write to Excel with sheet name EXCEL_SHEET_COLOR_ANALYSIS.

- **app/core/excel_formatting.py** - Add new function `_format_color_analysis_sheet()` to apply visual formatting. Set column widths optimized for content display. Enable text wrapping on annotation contents column with top vertical alignment. Apply auto-filter and freeze header row. Apply RGB color fills to color_sample column cells by reading RGB values from color_r/color_g/color_b columns and converting to hex format for PatternFill.

- **app/tests/core/test_extractor.py** - Add comprehensive unit tests for `extract_color_analysis()` method. Test Line/Polyline extraction and grouping by (RGB, layer, type). Test TEXT/MTEXT extraction with text content. Test color resolution (direct RGB, ByLayer, ByBlock, ACI). Test grouping logic (same color on different layers = separate rows). Test sorting by RGB values, layer name, and entity type. Test empty drawings and edge cases.

- **app/tests/core/test_excel_writer.py** - Add unit tests for Color Analysis sheet generation. Test `_write_color_analysis_sheet()` creates correct DataFrame structure. Verify column headers and data accuracy. Test sorting is applied correctly. Test empty color analysis data creates headers-only sheet. Verify integration into multi-sheet workbook generation.

- **app/tests/core/test_excel_formatting.py** - Add unit tests for Color Analysis sheet formatting. Test `_format_color_analysis_sheet()` applies correct column widths. Verify text wrapping on annotation contents column. Test auto-filter and frozen panes. Verify RGB color fills on color_sample cells. Test edge cases (invalid RGB values, empty cells).

### New Files
None - all changes are modifications to existing files following established patterns.

## Implementation Plan
### Phase 1: Foundation
Update core constants and type definitions to support the new Color Analysis feature. Add all required Excel column constants following the `color_` domain naming convention from app_docs/005-field-naming-convention.md. Add sheet name constant. Update ExtractionResult TypedDict to include the new color_analysis_data field which will store the extracted color analysis results.

### Phase 2: Core Implementation
Implement the color analysis extraction logic in extractor.py. Create `extract_color_analysis()` method that iterates through all modelspace entities, filters for LINE, LWPOLYLINE, POLYLINE, TEXT, and MTEXT types, resolves colors to RGB using the existing `_resolve_entity_color_to_rgb()` helper, and groups results appropriately. Lines and Polylines are aggregated by (RGB, layer, entity_type) with counts. TEXT and MTEXT are extracted individually with full text content. Results are sorted by (R, G, B, layer, entity_type) for consistent presentation.

### Phase 3: Integration
Integrate the color analysis data into the Excel generation pipeline. Add `_write_color_analysis_sheet()` to excel_writer.py to create the worksheet from extracted data. Add `_format_color_analysis_sheet()` to excel_formatting.py to apply visual formatting including text wrapping, column widths, auto-filters, frozen panes, and RGB color fills. Update the main `write_excel()` function to call both the sheet creation and formatting functions. The Color Analysis sheet will be the 6th sheet in the workbook.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add Constants for Color Analysis Sheet
- Add new sheet name constant to app/core/constants.py: `EXCEL_SHEET_COLOR_ANALYSIS: str = "Color Analysis"`
- Add new column name constants to app/core/constants.py following the `color_` domain prefix from naming conventions:
  - `EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS: str = "color_annotation_contents"`
  - `EXCEL_COLUMN_COLOR_LAYER_NAME: str = "color_layer_name"`
  - `EXCEL_COLUMN_COLOR_RED: str = "color_red"`
  - `EXCEL_COLUMN_COLOR_GREEN: str = "color_green"`
  - `EXCEL_COLUMN_COLOR_BLUE: str = "color_blue"`
  - `EXCEL_COLUMN_COLOR_SAMPLE: str = "color_sample"`
  - `EXCEL_COLUMN_COLOR_ENTITY_TYPE: str = "color_entity_type"`
  - `EXCEL_COLUMN_COLOR_ENTITY_COUNT: str = "color_entity_count"`
- Place constants after the Annotations Analysis section with clear comment header: "# Excel configuration - Color Analysis sheet columns"
- Add comments following existing patterns (e.g., "# See app_docs/005-field-naming-convention.md for naming conventions")

### 2. Update ExtractionResult TypedDict
- In app/core/extractor.py, add new field to ExtractionResult TypedDict: `color_analysis_data: list[dict[str, Any]]`
- Add docstring explanation: "color_analysis_data: List of color analysis records. Each record contains: annotation_contents (str, blank for Lines/Polylines), layer_name (str), color_r (int 0-255), color_g (int 0-255), color_b (int 0-255), entity_type (str: 'Lines', 'Polylines', 'TEXT', 'MTEXT'), entity_count (int)"
- Add example in docstring: `color_analysis_data: [{'annotation_contents': '', 'layer_name': 'WALLS', 'color_r': 255, 'color_g': 0, 'color_b': 0, 'entity_type': 'Lines', 'entity_count': 45}, ...]`
- Place field at the end of the TypedDict definition

### 3. Implement extract_color_analysis() Method
- Add new method `extract_color_analysis()` to app/core/extractor.py
- Method signature: `def extract_color_analysis(doc: Drawing) -> list[dict[str, Any]]:`
- Add comprehensive docstring explaining purpose, arguments, return value, and examples
- Implementation logic:
  - Initialize result list and tracking dictionaries for geometric entities: `geometric_entities: dict[tuple[int, int, int, str, str], int] = {}`
  - Initialize list for text annotations: `text_annotations: list[dict[str, Any]] = []`
  - Iterate through all modelspace entities
  - Filter for entity types: LINE, LWPOLYLINE, POLYLINE, TEXT, MTEXT
  - For each entity, resolve color using `_resolve_entity_color_to_rgb(entity, doc)`
  - Skip entities where color resolution returns None
  - Get layer_name from entity.dxf.layer
  - For LINE entities: group by (R, G, B, layer_name, "Lines"), increment count
  - For LWPOLYLINE and POLYLINE entities: group by (R, G, B, layer_name, "Polylines"), increment count
  - For TEXT entities: extract text using entity.dxf.text, create individual record with entity_type="TEXT", entity_count=1
  - For MTEXT entities: extract text using entity.text, create individual record with entity_type="MTEXT", entity_count=1
  - Convert geometric_entities dict to list of records with annotation_contents=""
  - Combine geometric records and text_annotations into single result list
  - Sort result by (color_r, color_g, color_b, layer_name, entity_type) - all ascending
  - Return sorted list
- Add error handling with try/except blocks
- Add logger info messages for tracking progress

### 4. Integrate extract_color_analysis() into extract_blocks()
- In app/core/extractor.py, call `extract_color_analysis(doc)` within the try block of extract_blocks() function
- Store result: `color_analysis_data = extract_color_analysis(doc)`
- Add to ExtractionResult return dictionary: `"color_analysis_data": color_analysis_data`
- Add logger summary: `logger.info(f"Extracted {len(color_analysis_data)} color analysis records")`
- Update docstring examples in extract_blocks() to include color_analysis_data field

### 5. Create _write_color_analysis_sheet() Function
- Add new function `_write_color_analysis_sheet()` to app/core/excel_writer.py
- Function signature: `def _write_color_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:`
- Add comprehensive docstring explaining purpose and behavior
- Implementation logic:
  - Extract color_analysis_data from ExtractionResult
  - Import all required column constants from constants.py
  - If color_analysis_data is not empty:
    - Create DataFrame directly from the list of dictionaries using appropriate column names
    - Map dictionary keys to Excel column constants
    - Ensure proper data types (str for contents/layer/type, int for RGB/count)
  - If color_analysis_data is empty:
    - Create empty DataFrame with all 8 column headers
  - Apply format_header() to all column names for Excel display
  - Write to Excel using sheet name EXCEL_SHEET_COLOR_ANALYSIS
  - Add logger info message: `logger.info(f"Color Analysis sheet created with {len(df)} rows")`
- Follow existing patterns from _create_annotations_analysis_sheet() for consistency

### 6. Create _format_color_analysis_sheet() Function
- Add new function `_format_color_analysis_sheet()` to app/core/excel_formatting.py
- Function signature: `def _format_color_analysis_sheet(wb: Workbook) -> None:`
- Add comprehensive docstring explaining formatting applied
- Implementation logic:
  - Get worksheet: `ws = wb[EXCEL_SHEET_COLOR_ANALYSIS]`
  - Apply auto-filter: `ws.auto_filter.ref = ws.dimensions` (if dimensions exist)
  - Freeze header row: `ws.freeze_panes = "A2"`
  - Set column widths following mockup specifications:
    - A (color_annotation_contents): 50 chars
    - B (color_layer_name): 20 chars
    - C (color_red): 10 chars
    - D (color_green): 10 chars
    - E (color_blue): 10 chars
    - F (color_sample): 12 chars
    - G (color_entity_type): 20 chars
    - H (color_entity_count): 15 chars
  - Enable text wrapping on header row with vertical="top"
  - Enable text wrapping on column A (annotation contents) for all data rows with vertical="top"
  - Apply right-alignment to columns C, D, E, H (numeric columns)
  - Apply RGB color fills to color_sample column (column F):
    - Iterate through data rows (row 2 onwards)
    - Read RGB values from columns C, D, E
    - Validate integers 0-255
    - Convert to hex format: `hex_color = f"{r:02X}{g:02X}{b:02X}"`
    - Create PatternFill with hex_color
    - Apply to cell in column F
    - Track count of fills applied
  - Add logger info message with formatting summary including color fills count
- Follow existing patterns from _format_annotations_analysis_sheet() for consistency

### 7. Integrate Color Analysis Sheet into Excel Writer Pipeline
- In app/core/excel_writer.py, import new constants:
  - Add EXCEL_SHEET_COLOR_ANALYSIS to sheet name imports
  - Add all EXCEL_COLUMN_COLOR_* constants to column name imports
- In write_excel() function:
  - Add call to `_create_color_analysis_sheet(extraction_data, writer)` after Annotations Analysis sheet creation
  - Add call to `_format_color_analysis_sheet(wb)` in post-processing section after loading workbook
  - Update docstring to mention 6 sheets instead of 5
  - Update logger messages to reflect 6 sheets
- In app/core/excel_formatting.py, import EXCEL_SHEET_COLOR_ANALYSIS constant

### 8. Write Unit Tests for extract_color_analysis()
- Add test class `TestColorAnalysis` to app/tests/core/test_extractor.py
- Test function `test_extract_color_analysis_lines_polylines()`:
  - Create test DXF with Lines and Polylines of different colors on different layers
  - Call extract_blocks() and verify color_analysis_data in result
  - Verify Lines and Polylines are grouped correctly by (RGB, layer, entity_type)
  - Verify entity_count is aggregated correctly
  - Verify annotation_contents is empty string for geometric entities
- Test function `test_extract_color_analysis_text_annotations()`:
  - Create test DXF with TEXT and MTEXT entities of different colors
  - Verify each text annotation appears as individual row
  - Verify annotation_contents matches entity text
  - Verify entity_type is "TEXT" or "MTEXT"
  - Verify entity_count is 1 for each annotation
- Test function `test_extract_color_analysis_color_resolution()`:
  - Test entities with direct RGB colors
  - Test entities with ByLayer colors (resolve to layer color)
  - Test entities with ACI color indices
  - Verify colors are resolved correctly to RGB tuples
  - Test entities with unresolvable colors are skipped
- Test function `test_extract_color_analysis_grouping()`:
  - Verify same color on different layers creates separate records
  - Verify same color with different entity types creates separate records
  - Verify Lines and Polylines are distinct entity types
  - Example: RED on "FIRE-SAFETY" and RED on "ELECTRICAL" = 2 separate records
- Test function `test_extract_color_analysis_sorting()`:
  - Create test data with various RGB values, layers, and entity types
  - Verify sorting is by (color_r, color_g, color_b, layer_name, entity_type) ascending
  - Verify lower R values appear first, then G, then B
  - Verify alphabetical layer sorting within same color
  - Verify alphabetical entity type sorting within same color and layer
- Test function `test_extract_color_analysis_empty_drawing()`:
  - Test DXF with no relevant entities (or only blocks)
  - Verify color_analysis_data is empty list
  - Verify no errors raised

### 9. Write Unit Tests for Color Analysis Sheet Generation
- Add test function `test_create_color_analysis_sheet()` to app/tests/core/test_excel_writer.py
- Create mock ExtractionResult with sample color_analysis_data containing:
  - Geometric entity rows (Lines/Polylines with counts, blank annotation_contents)
  - Text annotation rows (TEXT/MTEXT with contents, count=1)
  - Various colors, layers, and entity types
- Generate Excel file using write_excel()
- Load with openpyxl and verify:
  - Sheet "Color Analysis" exists
  - Has 8 columns with correct headers (formatted with Title Case)
  - Data rows match input color_analysis_data
  - Sorting is preserved (RGB values ascending)
  - Annotation contents are present for text entities, blank for geometric
  - Entity counts are correct
- Test function `test_create_color_analysis_sheet_empty()`:
  - Create ExtractionResult with empty color_analysis_data
  - Generate Excel and verify Color Analysis sheet has headers only, no data rows

### 10. Write Unit Tests for Color Analysis Sheet Formatting
- Add test function `test_format_color_analysis_sheet()` to app/tests/core/test_excel_formatting.py
- Create test Excel file with Color Analysis sheet containing sample data
- Apply _format_color_analysis_sheet(wb)
- Verify:
  - Auto-filter is applied to all columns
  - Frozen panes at A2 (header row frozen)
  - Column widths match specifications (A=50, B=20, C-E=10, F=12, G=20, H=15)
  - Text wrapping enabled on column A for data rows with vertical="top"
  - Numeric columns (C, D, E, H) are right-aligned
  - Color sample column (F) has RGB fills matching RGB values from columns C, D, E
- Test function `test_format_color_analysis_sheet_color_fills()`:
  - Create test data with various RGB values
  - Apply formatting
  - Verify each color_sample cell has correct RGB background color
  - Verify hex conversion is correct (e.g., RGB(255, 0, 0) → "FF0000")
  - Test edge cases: RGB(0, 0, 0), RGB(255, 255, 255), RGB(127, 127, 127)
- Test function `test_format_color_analysis_sheet_invalid_rgb()`:
  - Create test data with invalid RGB values (negative, >255, non-integer)
  - Verify formatting doesn't crash
  - Verify no color fill applied for invalid values

### 11. Write Integration Tests
- Add test function `test_full_extraction_with_color_analysis()` to app/tests/core/test_extractor.py
- Use existing comprehensive test asset (e.g., app/tests/assets/comprehensive_scale_test.dxf)
- Run full extract_blocks() and verify:
  - color_analysis_data is included in result
  - Contains expected entity types (Lines, Polylines, TEXT, MTEXT)
  - Colors are resolved correctly
  - Grouping logic works across real drawing data
- Add test function `test_excel_generation_includes_color_analysis()` to app/tests/core/test_excel_writer.py
- Generate complete Excel file from real test asset
- Load with openpyxl and verify:
  - 6 sheets exist: Block Analysis, Layer Analysis, Entity Summary, Block Geometry Analysis, Annotations Analysis, Color Analysis
  - Color Analysis sheet is properly formatted
  - No regressions in other sheets
  - All data is consistent across sheets

### 12. Test with Real Drawing Assets
- Run extraction on app/tests/assets/sample_drawing.dxf
- Run extraction on app/tests/assets/Supermarket-2020.dwg
- Run extraction on app/tests/assets/comprehensive_scale_test.dxf
- Verify Color Analysis sheet is generated for each
- Manually inspect Excel output to verify:
  - Color samples display correctly
  - Text wrapping works properly
  - Sorting is correct
  - Grouping logic is accurate
  - No data loss or corruption

### 13. Run Validation Commands
- Execute all validation commands listed in Validation Commands section
- Fix any test failures, type errors, or linting issues
- Verify zero regressions across all test suites
- Verify mypy type checking passes with strict configuration
- Verify ruff linting passes with no warnings
- Ensure 100% test coverage for new code

## Testing Strategy
### Unit Tests
- **Color Analysis Extraction**: Test extract_color_analysis() extracts correct entities (Lines, Polylines, TEXT, MTEXT), resolves colors correctly (direct RGB, ByLayer, ACI), groups geometric entities by (RGB, layer, type), extracts text annotations individually, sorts results correctly by (R, G, B, layer, entity_type)
- **Sheet Generation**: Test _write_color_analysis_sheet() creates correct DataFrame structure with 8 columns, handles empty data (headers only), preserves sorting, maps data correctly from extraction result
- **Sheet Formatting**: Test _format_color_analysis_sheet() applies correct column widths, enables text wrapping on annotation contents, applies RGB color fills to color_sample column, applies auto-filter and frozen panes, handles edge cases (invalid RGB values)
- **Integration**: Test Color Analysis sheet integrates correctly into 6-sheet workbook, no regressions in existing sheets, data consistency across sheets

### Integration Tests
- **End-to-End Extraction**: Test complete extraction pipeline from DXF/DWG file to Excel output with Color Analysis sheet
- **Multi-Sheet Validation**: Verify all 6 sheets are created correctly (Block Analysis, Layer Analysis, Entity Summary, Block Geometry Analysis, Annotations Analysis, Color Analysis)
- **Real Asset Testing**: Run extraction on multiple real test assets to verify robustness across different drawing types and complexities
- **Excel Formatting Validation**: Load generated Excel files with openpyxl and verify all formatting is applied correctly (text wrapping, color fills, column widths, auto-filters, frozen panes)

### Edge Cases
- **Empty Drawings**: Drawing with no Lines/Polylines/TEXT/MTEXT entities (empty sheet with headers only)
- **Single Color**: All entities use the same color on the same layer (single row)
- **Same Color, Different Layers**: Same RGB color used on multiple layers (separate rows per layer)
- **Same Color, Different Entity Types**: Same RGB color used for Lines, Polylines, TEXT, MTEXT on same layer (separate rows per entity type)
- **Color Resolution Edge Cases**: Entities with no color, ByBlock color, invalid ACI indices, ByLayer with layer color unresolved
- **Text Content Edge Cases**: Empty text, very long text (>1000 chars), text with newlines/tabs/special characters, unicode content
- **Polyline Variations**: Both LWPOLYLINE and POLYLINE entities (both should map to "Polylines" entity type)
- **RGB Extremes**: RGB(0,0,0) black, RGB(255,255,255) white, mid-range grays
- **Large Datasets**: Drawing with thousands of entities across hundreds of color/layer/type combinations

### Playwright MCP Tests
Not applicable for this feature - this is a backend data extraction and Excel generation feature with no GUI changes. All testing can be done through unit and integration tests using pytest.

## Acceptance Criteria
- [ ] New "Color Analysis" worksheet is created in Excel output with correct sheet name
- [ ] Color Analysis sheet contains 8 columns in correct order: color_annotation_contents, color_layer_name, color_red, color_green, color_blue, color_sample, color_entity_type, color_entity_count
- [ ] Column headers are properly formatted (Title Case with proper spacing)
- [ ] LINE entities are extracted and grouped by (RGB, layer, "Lines") with aggregate counts
- [ ] LWPOLYLINE and POLYLINE entities are extracted and grouped by (RGB, layer, "Polylines") with aggregate counts
- [ ] TEXT entities are extracted individually with full text content and entity_type="TEXT"
- [ ] MTEXT entities are extracted individually with full text content and entity_type="MTEXT"
- [ ] Geometric entities (Lines/Polylines) have blank annotation_contents column
- [ ] Text entities (TEXT/MTEXT) have full text content in annotation_contents column
- [ ] RGB color values are correctly resolved (ByLayer, ByBlock, ACI index, direct RGB)
- [ ] Same color on different layers creates separate rows (e.g., RED on "FIRE-SAFETY" and RED on "ELECTRICAL")
- [ ] Same color with different entity types creates separate rows (e.g., Lines and Polylines with same color/layer)
- [ ] Results are sorted by color_red (asc), color_green (asc), color_blue (asc), layer_name (asc), entity_type (asc)
- [ ] Color sample column (F) cells are filled with actual RGB background color
- [ ] Column A (annotation_contents) has text wrapping enabled with vertical align top, width ~50 chars
- [ ] Column B (layer_name) has width ~20 chars
- [ ] Columns C, D, E (RGB values) have width ~10 chars and right-aligned
- [ ] Column F (color_sample) has width ~12 chars
- [ ] Column G (entity_type) has width ~20 chars
- [ ] Column H (entity_count) has width ~15 chars and right-aligned
- [ ] Auto-filter is applied to all column headers
- [ ] Header row is frozen (frozen panes at A2)
- [ ] Excel workbook now contains 6 sheets (added Color Analysis as 6th sheet)
- [ ] No regressions in existing 5 sheets (Block Analysis, Layer Analysis, Entity Summary, Block Geometry Analysis, Annotations Analysis)
- [ ] All unit tests pass with 100% coverage for new code
- [ ] All integration tests pass with no regressions
- [ ] mypy type checking passes with strict configuration
- [ ] ruff linting passes with no warnings
- [ ] Code follows naming conventions from app_docs/005-field-naming-convention.md (color_ domain prefix)
- [ ] Logger messages provide clear progress and summary information
- [ ] Works correctly on empty drawings (headers-only sheet)
- [ ] Works correctly on large drawings with thousands of entities

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py::TestColorAnalysis -v` - Run color analysis extraction unit tests
- `uv run pytest app/tests/core/test_excel_writer.py -k color_analysis -v` - Run color analysis sheet generation tests
- `uv run pytest app/tests/core/test_excel_formatting.py -k color_analysis -v` - Run color analysis sheet formatting tests
- `uv run pytest app/tests/core/test_extractor.py -v` - Run all extractor tests to verify no regressions
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run all excel writer tests to verify no regressions
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run all excel formatting tests to verify no regressions
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions across entire codebase
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Run tests with coverage report to ensure new code is fully tested
- `uv run mypy app/` - Run type checking to verify all type annotations are correct
- `uv run ruff check app/` - Run linter to verify code style compliance
- `uv run ruff format app/ --check` - Verify code formatting compliance
- `bash scripts/start.sh` - Manual test: Launch GUI, select test DXF with various entities, verify Color Analysis sheet is created with correct data and formatting

## Notes
- **Entity Type Mapping**: LINE entities map to "Lines", LWPOLYLINE and POLYLINE entities both map to "Polylines", TEXT maps to "TEXT", MTEXT maps to "MTEXT"
- **Color Resolution Strategy**: Use existing `_resolve_entity_color_to_rgb()` helper function which handles direct RGB, ByLayer, ByBlock, and ACI color indices. Entities with unresolvable colors (returns None) are skipped from analysis.
- **Grouping Strategy**: Geometric entities (Lines/Polylines) are aggregated by unique (RGB, layer, entity_type) combinations with counts. Text annotations (TEXT/MTEXT) are extracted individually with full content and count=1. This provides both quantitative analysis (geometric counts) and qualitative analysis (text content).
- **Same Color, Different Layers**: A key requirement is that the same RGB color on different layers must create separate rows. For example, RED (255,0,0) on "FIRE-SAFETY" layer and RED (255,0,0) on "ELECTRICAL" layer should be two distinct rows in the output.
- **Sorting Rationale**: Sorting by RGB values (R, G, B) groups similar colors together visually. Secondary sorting by layer name and entity type provides consistent ordering within color groups.
- **Excel Color Fill Format**: Use openpyxl PatternFill with fill_type="solid" and start_color/end_color in RRGGBB hex format (e.g., "FF0000" for red). Convert RGB integers (0-255) to 2-digit hex using f"{r:02X}{g:02X}{b:02X}".
- **Text Wrapping**: Column A (annotation_contents) requires text wrapping with vertical="top" alignment for proper display of multi-line text from MTEXT entities and long TEXT content.
- **Naming Convention Compliance**: All new field names follow the pattern from app_docs/005-field-naming-convention.md using `color_` domain prefix (e.g., color_annotation_contents, color_layer_name, color_red, color_entity_type, color_entity_count)
- **Performance Consideration**: For very large drawings with thousands of entities, using dictionary-based grouping for geometric entities ensures efficient aggregation. Text annotations are not aggregated to preserve full content visibility.
- **Future Enhancements**: Could add entity coordinates, text height/rotation, line thickness, or statistical summaries in future versions. Current version focuses on core color usage analysis and annotation content visibility.
- **Existing Helper Usage**: The feature leverages the existing `_resolve_entity_color_to_rgb()` helper function which was added for Annotations Analysis, demonstrating good code reuse and consistency.
