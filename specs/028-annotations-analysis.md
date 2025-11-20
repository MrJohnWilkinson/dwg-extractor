# Feature: Annotations Analysis

## Feature Description
Create a new "Annotations Analysis" worksheet that extracts and analyzes all TEXT and MTEXT entities from CAD drawings. The sheet displays annotation contents, type, layer name, resolved RGB colors, and occurrence counts. Additionally, update the Layer Analysis sheet to use the clearer field name `layer_annotation_count` instead of the previous `layer_text_mtext_count`.

This feature provides users with comprehensive visibility into all text annotations in their drawings, grouped by unique combinations of content, type, layer, and color. The color sample column visually displays the actual RGB color of each annotation group.

## User Story
As a CAD drawing analyst
I want to extract and analyze all text annotations (TEXT and MTEXT entities) from DWG/DXF files
So that I can inventory all text content, identify duplicates, understand annotation distribution across layers and colors, and improve drawing consistency

## Problem Statement
Currently, the application only counts TEXT/MTEXT entities per layer in the Layer Analysis sheet but does not extract the actual text contents or provide detailed annotation analysis. Users cannot see what text exists in their drawings, how many times specific annotations appear, which layers contain which text, or what colors are used for annotations. This makes it difficult to:
- Inventory all text content in a drawing
- Identify duplicate or inconsistent annotations
- Analyze annotation distribution by layer
- Understand color usage for text annotations
- Audit text content for quality control

## Solution Statement
Add a new "Annotations Analysis" worksheet that extracts all TEXT and MTEXT entities with their full contents, entity type, layer name, and resolved RGB color values. Group annotations by unique combinations of (contents, type, layer, color) and count occurrences. Display results in a formatted Excel sheet with:
- Full text contents (no truncation, with text wrapping)
- Entity type (TEXT or MTEXT)
- Layer name
- RGB color components (R, G, B)
- Visual color sample cell (background filled with actual RGB color)
- Occurrence count

Additionally, rename the Layer Analysis column from `layer_text_mtext_count` to `layer_annotation_count` for improved clarity and consistency with the new naming conventions.

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Add new column name constants for Annotations Analysis sheet (EXCEL_COLUMN_ANNOTATION_* series) and rename EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT to EXCEL_COLUMN_LAYER_ANNOTATION_COUNT. Add new sheet name constant EXCEL_SHEET_ANNOTATIONS_ANALYSIS.

- **app/core/extractor.py** - Add new extraction logic for TEXT/MTEXT entities with color resolution. Update ExtractionResult TypedDict to include annotation_data dictionary. Rename layer_text_mtext_counts to layer_annotation_counts for consistency. Implement color resolution logic to handle ByLayer, ByBlock, and ACI color indices.

- **app/core/excel_writer.py** - Add new function `_create_annotations_analysis_sheet()` to generate the Annotations Analysis worksheet. Update `_create_layer_analysis_sheet()` to use renamed column constant. Add RGB color fill logic for annotation_color_sample cells. Apply text wrapping to annotation_contents column.

- **app/core/excel_formatting.py** - Add new function `_format_annotations_analysis_sheet()` to apply column widths, text wrapping, auto-filter, frozen panes, and RGB color fills to the annotation_color_sample column. Update format_header() if needed to handle new annotation column names (should work automatically with existing logic).

- **app/tests/core/test_extractor.py** - Add unit tests for annotation extraction logic including TEXT/MTEXT entity detection, color resolution (ByLayer, ByBlock, ACI indices), grouping by unique combinations, and count accuracy.

- **app/tests/core/test_excel_writer.py** - Add unit tests for Annotations Analysis sheet generation including column structure, data accuracy, sorting by annotation_count, and Excel formatting (text wrapping, color fills).

- **app/tests/core/test_excel_formatting.py** - Add unit tests for Annotations Analysis sheet formatting including column widths, auto-filter, frozen panes, and RGB color sample fills.

### New Files
None - all changes are modifications to existing files.

## Implementation Plan
### Phase 1: Foundation
Update core constants and type definitions to support the new Annotations Analysis feature. This includes adding new Excel column constants, sheet name constant, and updating the ExtractionResult TypedDict to include annotation data. Also rename existing layer_text_mtext_count references to layer_annotation_count for consistency.

### Phase 2: Core Implementation
Implement annotation extraction logic in extractor.py to iterate through all TEXT and MTEXT entities, extract their contents, resolve colors to RGB values (handling ByLayer, ByBlock, and ACI color indices), and group by unique combinations of (contents, type, layer, color). Calculate occurrence counts for each unique annotation group.

### Phase 3: Integration
Integrate the annotation data into the Excel generation pipeline by creating the new Annotations Analysis sheet with proper formatting, text wrapping, and RGB color fills. Update the Layer Analysis sheet to use the renamed column constant. Apply comprehensive formatting including column widths, auto-filters, frozen panes, and visual color samples.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Constants and Type Definitions
- Add new sheet name constant to app/core/constants.py: `EXCEL_SHEET_ANNOTATIONS_ANALYSIS`
- Add new column name constants to app/core/constants.py:
  - `EXCEL_COLUMN_ANNOTATION_CONTENTS`
  - `EXCEL_COLUMN_ANNOTATION_TYPE`
  - `EXCEL_COLUMN_ANNOTATION_LAYER_NAME`
  - `EXCEL_COLUMN_ANNOTATION_COLOR_R`
  - `EXCEL_COLUMN_ANNOTATION_COLOR_G`
  - `EXCEL_COLUMN_ANNOTATION_COLOR_B`
  - `EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE`
  - `EXCEL_COLUMN_ANNOTATION_COUNT`
- Rename `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT` to `EXCEL_COLUMN_LAYER_ANNOTATION_COUNT` in app/core/constants.py
- Update ExtractionResult TypedDict in app/core/extractor.py to add `annotation_data: dict[tuple[str, str, str, int, int, int], int]` field (key: (contents, type, layer_name, color_r, color_g, color_b), value: count)
- Rename `layer_text_mtext_counts` to `layer_annotation_counts` in ExtractionResult TypedDict in app/core/extractor.py
- Update all docstring examples in app/core/extractor.py to reflect the renamed field

### 2. Implement Color Resolution Utility Function
- Add helper function `_resolve_entity_color_to_rgb()` to app/core/extractor.py that takes an ezdxf entity and drawing document, and returns tuple[int, int, int] or None
- Implement logic to handle:
  - Direct RGB colors (entity.rgb property)
  - ByLayer colors (resolve to layer's color)
  - ByBlock colors (default to white: (255, 255, 255) as a safe fallback)
  - ACI color index (use ezdxf.colors.aci2rgb() to convert)
  - Handle edge cases: missing colors, invalid indices, None values
- Add comprehensive docstring with examples
- Return None if color cannot be resolved (these entities will be filtered out)

### 3. Implement Annotation Extraction Logic
- In app/core/extractor.py, modify the modelspace entity iteration loop to track annotation data
- Initialize `annotation_data: dict[tuple[str, str, str, int, int, int], int] = {}` at the start of extract_blocks()
- When iterating modelspace entities, for each TEXT or MTEXT entity:
  - Extract text contents using entity.dxf.text (TEXT) or entity.text (MTEXT)
  - Get entity type (TEXT or MTEXT)
  - Get layer name from entity.dxf.layer
  - Resolve color to RGB using `_resolve_entity_color_to_rgb()`
  - Skip entity if color resolution returns None
  - Create key: (contents, entity_type, layer_name, color_r, color_g, color_b)
  - Increment count in annotation_data dictionary
- Add annotation_data to the ExtractionResult return dictionary
- Update logger to report total annotation entities extracted and unique annotation groups

### 4. Update Layer Analysis Extraction to Use Renamed Field
- In app/core/extractor.py, rename `layer_text_mtext_counts` variable to `layer_annotation_counts`
- Update all references to use the new variable name
- Update logger messages to use "annotation" terminology instead of "text_mtext"
- Ensure the dictionary is properly initialized and populated
- Update the ExtractionResult return to use the new field name

### 5. Create Annotations Analysis Sheet Function
- Add function `_create_annotations_analysis_sheet()` to app/core/excel_writer.py
- Extract annotation_data from ExtractionResult
- Build DataFrame rows with columns: annotation_contents, annotation_type, annotation_layer_name, annotation_color_r, annotation_color_g, annotation_color_b, annotation_color_sample, annotation_count
- For empty annotation_data, create DataFrame with column headers only
- Sort by annotation_count descending
- Format column headers using format_header()
- Write to Excel using sheet name EXCEL_SHEET_ANNOTATIONS_ANALYSIS
- Add logger info message with row count

### 6. Integrate Annotations Analysis Sheet into Excel Writer
- In app/core/excel_writer.py, import new constants (sheet name and all annotation column constants)
- In write_excel() function, call `_create_annotations_analysis_sheet(extraction_data, writer)` after creating other sheets
- Add call to `_format_annotations_analysis_sheet(wb)` in the post-processing section (after loading workbook)
- Update logger messages to reflect 5 sheets instead of 4

### 7. Update Layer Analysis Sheet to Use Renamed Column
- In app/core/excel_writer.py, update `_create_layer_analysis_sheet()` to:
  - Import `EXCEL_COLUMN_LAYER_ANNOTATION_COUNT` instead of `EXCEL_COLUMN_LAYER_TEXT_MTEXT_COUNT`
  - Update all references in the function to use the new constant name
  - Update variable names from text_mtext_count to annotation_count
  - Update DataFrame column creation to use new constant
- In app/core/excel_formatting.py, update `_format_layer_analysis_sheet()` docstring and comments to reference "annotation" instead of "text_mtext" (code should use column indices, so no code changes needed)

### 8. Implement Annotations Analysis Sheet Formatting
- Add function `_format_annotations_analysis_sheet()` to app/core/excel_formatting.py
- Apply auto-filter to all columns
- Freeze top row (header row)
- Set column widths:
  - A (annotation_contents): 60 chars with text wrapping enabled
  - B (annotation_type): 15 chars
  - C (annotation_layer_name): 25 chars
  - D (annotation_color_r): 12 chars
  - E (annotation_color_g): 12 chars
  - F (annotation_color_b): 12 chars
  - G (annotation_color_sample): 12 chars
  - H (annotation_count): 20 chars
- Enable text wrapping on annotation_contents column (column A) for all data rows
- For each data row (row 2 onwards):
  - Read RGB values from columns D, E, F
  - Create PatternFill with RGB color
  - Apply fill to annotation_color_sample cell (column G)
  - Validate RGB values are integers 0-255
- Add logger info message with formatting summary

### 9. Write Unit Tests for Color Resolution
- Add test function `test_resolve_entity_color_to_rgb()` to app/tests/core/test_extractor.py
- Create test DXF with TEXT entities having different color types:
  - Direct RGB color
  - ByLayer color (resolve to layer color)
  - ACI color index
  - Missing/None color
- Verify color resolution returns correct RGB tuples
- Verify None is returned for unresolvable colors

### 10. Write Unit Tests for Annotation Extraction
- Add test function `test_extract_annotation_data()` to app/tests/core/test_extractor.py
- Use existing test asset with TEXT/MTEXT entities or create new test DXF
- Verify annotation_data is included in ExtractionResult
- Verify correct grouping by (contents, type, layer, color)
- Verify count accuracy for duplicate annotations
- Verify TEXT and MTEXT are distinguished
- Test edge cases: empty text, special characters, very long text

### 11. Write Unit Tests for Annotations Analysis Sheet Generation
- Add test function `test_create_annotations_analysis_sheet()` to app/tests/core/test_excel_writer.py
- Create mock ExtractionResult with annotation_data
- Generate Excel file and load with openpyxl
- Verify sheet exists with correct name
- Verify column headers are present and formatted correctly
- Verify data rows match input annotation_data
- Verify sorting by annotation_count descending
- Test empty annotation_data case (headers only)

### 12. Write Unit Tests for Annotations Analysis Sheet Formatting
- Add test function `test_format_annotations_analysis_sheet()` to app/tests/core/test_excel_formatting.py
- Create Excel file with Annotations Analysis sheet
- Apply formatting function
- Verify auto-filter is applied
- Verify frozen panes at A2
- Verify column widths are correct
- Verify text wrapping on annotation_contents column
- Verify RGB color fills on annotation_color_sample cells
- Test edge cases: invalid RGB values, missing cells

### 13. Write Unit Tests for Renamed Layer Analysis Column
- Add test function `test_layer_analysis_uses_annotation_count_column()` to app/tests/core/test_excel_writer.py
- Create mock ExtractionResult with layer_annotation_counts
- Generate Excel file and load with openpyxl
- Verify Layer Analysis sheet has column header "Layer Annotation Count" (formatted version of layer_annotation_count)
- Verify data values match layer_annotation_counts from input

### 14. Update Integration Tests
- Run full extraction on test asset files
- Verify Annotations Analysis sheet is created
- Verify Layer Analysis sheet uses new column name
- Verify no regressions in existing sheets (Block Analysis, Entity Summary, Block Geometry Analysis)
- Test with multiple test assets to ensure robustness

### 15. Run Validation Commands
- Execute all validation commands listed in Validation Commands section
- Fix any test failures or type errors
- Verify zero regressions across all test suites
- Verify mypy type checking passes with strict configuration

## Testing Strategy
### Unit Tests
- **Color Resolution**: Test _resolve_entity_color_to_rgb() with direct RGB, ByLayer, ByBlock, ACI index, and edge cases (None, invalid)
- **Annotation Extraction**: Test extract_blocks() returns annotation_data with correct grouping, counts, and field types
- **Sheet Generation**: Test _create_annotations_analysis_sheet() creates correct DataFrame structure, sorting, and column headers
- **Sheet Formatting**: Test _format_annotations_analysis_sheet() applies correct column widths, text wrapping, auto-filter, frozen panes, and RGB color fills
- **Layer Analysis Rename**: Test Layer Analysis sheet uses EXCEL_COLUMN_LAYER_ANNOTATION_COUNT constant and displays correct header

### Integration Tests
- **End-to-End Extraction**: Test complete extraction pipeline from DXF file to Excel output with Annotations Analysis sheet
- **Multi-Sheet Validation**: Verify all 5 sheets are created (Block Analysis, Layer Analysis, Entity Summary, Block Geometry Analysis, Annotations Analysis)
- **Data Consistency**: Verify annotation counts in Annotations Analysis sheet match layer_annotation_counts in Layer Analysis sheet when summed by layer
- **Excel Formatting**: Load generated Excel file with openpyxl and verify all formatting is applied correctly

### Edge Cases
- **Empty Annotations**: Drawing with no TEXT/MTEXT entities (empty sheet with headers only)
- **Duplicate Annotations**: Multiple identical text contents on same layer with same color (verify count > 1)
- **Special Characters**: Text with newlines, tabs, unicode characters, very long strings (>1000 chars)
- **Color Edge Cases**: Entities with no color, ByBlock color, invalid ACI indices
- **Mixed Entity Types**: Same text content as both TEXT and MTEXT (should be separate rows)
- **Layer Variations**: Same text content on different layers (should be separate rows)
- **Color Variations**: Same text content with different colors (should be separate rows)

### Playwright MCP Tests
Not applicable for this feature - this is a backend data extraction and Excel generation feature with no GUI changes. All testing can be done through unit and integration tests using pytest.

## Acceptance Criteria
- [ ] New "Annotations Analysis" worksheet is created in Excel output with correct sheet name
- [ ] Annotations Analysis sheet contains 8 columns in correct order: annotation_contents, annotation_type, annotation_layer_name, annotation_color_r, annotation_color_g, annotation_color_b, annotation_color_sample, annotation_count
- [ ] Column headers are properly formatted (Title Case with proper spacing)
- [ ] All TEXT entities are extracted with full contents (no truncation)
- [ ] All MTEXT entities are extracted with full contents (no truncation)
- [ ] Entity type column correctly distinguishes TEXT vs MTEXT
- [ ] Layer name column shows correct layer for each annotation
- [ ] RGB color values are correctly resolved (ByLayer, ByBlock, ACI index, direct RGB)
- [ ] Color sample column cells are filled with actual RGB background color
- [ ] Annotations are grouped by unique (contents, type, layer, color) combinations
- [ ] Annotation counts are accurate for each unique group
- [ ] Sheet is sorted by annotation_count descending
- [ ] annotation_contents column has text wrapping enabled with ~60 char width
- [ ] annotation_color_sample column has ~12 char width
- [ ] Auto-filter is applied to all column headers
- [ ] Header row is frozen (frozen panes at A2)
- [ ] Layer Analysis sheet column renamed from "Layer Text Mtext Count" to "Layer Annotation Count"
- [ ] All unit tests pass with 100% coverage for new code
- [ ] All integration tests pass with no regressions
- [ ] mypy type checking passes with strict configuration
- [ ] Code follows naming conventions from app_docs/005-field-naming-convention.md
- [ ] Logger messages provide clear progress and summary information

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor unit tests including new annotation extraction tests
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run excel writer unit tests including new Annotations Analysis sheet tests
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run excel formatting unit tests including new sheet formatting tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Run tests with coverage report to ensure new code is tested
- `uv run mypy app/` - Run type checking to verify all type annotations are correct
- `uv run ruff check app/` - Run linter to verify code style compliance
- `uv run python app/main.py` - Manual test: Launch GUI, select test DXF with TEXT/MTEXT entities, verify Annotations Analysis sheet is created with correct data and formatting

## Notes
- **Color Resolution Strategy**: Use entity.rgb property first, then fall back to layer color for ByLayer, then ACI index conversion. ByBlock colors default to white (255, 255, 255) as a safe fallback since block color context is complex.
- **Text Content Extraction**: Use entity.dxf.text for TEXT entities and entity.text for MTEXT entities (MTEXT has a text property that returns the concatenated plain text content)
- **Excel Color Fill Format**: Use openpyxl PatternFill with fill_type="solid" and start_color/end_color in RRGGBB hex format (e.g., "FF0000" for red)
- **Naming Convention Compliance**: All new field names follow the pattern from app_docs/005-field-naming-convention.md using `annotation_` domain prefix
- **Layer Analysis Rename Rationale**: The term "annotation" is clearer and more professional than "text_mtext", and aligns with the new Annotations Analysis feature
- **Performance Consideration**: For very large drawings with thousands of text entities, grouping and counting should be efficient using Python dictionaries. No performance issues expected.
- **Future Enhancements**: Could add text height, rotation angle, font name, or text style in future versions. Current version focuses on core inventory functionality.
