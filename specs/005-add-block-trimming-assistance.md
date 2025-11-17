# Feature: Block Trimming Assistance

## Feature Description
Add block geometry analysis to help users determine correct trim values for retail shelving fixtures in CAD drawings. This feature extracts native block dimensions (width and height at 0° rotation) and identifies intersection points within block geometry, presenting segment measurements that reveal structural boundaries versus merchandisable space.

Users will receive an additional Excel sheet showing block dimensions and geometric segments, enabling them to identify which portions of fixtures represent non-sellable structural elements (feet, frames, doors, vents) versus actual merchandisable shelf space. This eliminates the guesswork when trimming oversized fixture blocks down to their true product placement areas.

## User Story
As a retail space planner
I want to see geometric segment measurements for each fixture block at 0° rotation
So that I can identify structural boundaries and determine correct trim values to isolate merchandisable space

## Problem Statement
Retail fixture blocks in CAD drawings represent shelving units that are typically drawn larger than their actual merchandisable space. These blocks include non-sellable structural elements:
- Extended support feet that protrude beyond the shelf area
- Frame borders and edge trim
- Compressor housings and cooling vents (for refrigerated cases)
- Open door swings and hinges
- Support columns and vertical dividers

Users need to trim these blocks to their true merchandisable dimensions using a separate application that accepts four trim parameters: Trim Left, Trim Right, Trim Top, Trim Bottom. These parameters work in **block-local coordinates at 0° rotation**.

**The Challenge:**
- Blocks are placed at various rotations (90°, 180°, 270°) in actual CAD drawings
- Users see rotated blocks on screen but trim parameters reference the block's native 0° orientation
- Users must mentally rotate blocks back to 0° to measure trim distances correctly
- Complex fixtures (like refrigerated display cases) have asymmetric structures with multiple geometric boundaries
- Users may not know the target merchandisable dimensions beforehand and need to identify them from the geometry

**Current Pain Points:**
- Users manually set each block to 0° rotation in CAD, measure trim distances, then restore rotation
- No visibility into internal geometric structure (where frames end and shelves begin)
- Trial-and-error process to find correct trim values
- Confusion about which visual side corresponds to which trim parameter
- Time-consuming workflow for drawings with dozens of unique fixture types

## Solution Statement
Extract and analyze block geometry at the native 0° orientation to provide actionable trimming guidance:

1. **Native Dimension Extraction**: For each unique block, extract width and height at 0° rotation (before any placement rotation is applied)
2. **Geometric Intersection Analysis**: Identify all horizontal and vertical intersection points within the block's geometry
3. **Segment Calculation**: Calculate distances between consecutive intersection points to reveal structural layers
4. **Excel Presentation**: Display results in a new "Block Trimming Analysis" sheet with:
   - `block_name`: Block identifier
   - `block_native_width`: Width at 0° rotation
   - `block_native_height`: Height at 0° rotation
   - `block_vertical_segments`: Comma-separated list of segment widths from left to right (e.g., "50, 1100, 50")
   - `block_horizontal_segments`: Comma-separated list of segment heights from bottom to top (e.g., "25, 550, 25")

**User Workflow:**
1. Open generated Excel file and navigate to "Block Trimming Analysis" sheet
2. Find their fixture block by name
3. Review native dimensions to understand the block's unrotated size
4. Examine vertical segments (left-to-right measurements) to identify left/right trim boundaries
5. Examine horizontal segments (bottom-to-top measurements) to identify bottom/top trim boundaries
6. Recognize patterns: small symmetric edge segments = structural, large center segment = merchandisable
7. Calculate trim values: edge segment sizes = trim amounts, or measure to reach known merchandisable size

**Example Interpretation:**
```
Block: SHELF_4FT
Native Width: 1200mm
Native Height: 600mm
Vertical Segments: 50, 1100, 50
Horizontal Segments: 25, 550, 25

User sees: 50mm edges on left/right → Trim Left: 50, Trim Right: 50
           25mm edges on top/bottom → Trim Bottom: 25, Trim Top: 25
Result: Merchandisable space = 1100mm × 550mm
```

## Relevant Files
Use these files to implement the feature:

**app/core/extractor.py**
- Contains `extract_blocks()` function that parses DWG/DXF files using ezdxf
- Defines `ExtractionResult` TypedDict for extraction results
- Needs new function `_analyze_block_geometry()` to extract block dimensions and intersections
- Access to `doc.blocks` for block definitions
- Access to block entities for geometric analysis

**app/core/excel_writer.py**
- Contains Excel generation logic with multi-sheet creation
- Currently creates three sheets: Block Counts, Layer Analysis, Entity Summary
- Needs new function `_create_block_trimming_analysis_sheet()` to create the fourth sheet
- Needs new function `_format_block_trimming_analysis_sheet()` for formatting
- Main `write_excel()` function needs to call the new sheet creation function

**app/core/constants.py**
- Defines all Excel column name constants and sheet names
- Needs new constant `EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS: str = 'Block Trimming Analysis'`
- Needs new column constants following naming convention:
  - `EXCEL_COLUMN_BLOCK_NAME` (already exists)
  - `EXCEL_COLUMN_BLOCK_NATIVE_WIDTH`
  - `EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT`
  - `EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS`
  - `EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS`

**app_docs/005-field-naming-convention.md**
- Documents the field naming convention: `{domain}_{attribute}[_{qualifier}]`
- Block domain fields follow `block_` prefix
- Collections use plural suffix (e.g., `_segments`)

**app/tests/core/test_extractor.py**
- Contains unit tests for extraction logic
- Needs new tests for block geometry analysis:
  - Test native dimension extraction
  - Test intersection point identification
  - Test segment calculation
  - Test with simple rectangular blocks
  - Test with complex multi-component blocks

**app/tests/core/test_excel_writer.py**
- Contains Excel generation tests
- Needs tests for the new Block Trimming Analysis sheet:
  - Verify sheet exists
  - Verify column headers are correct
  - Verify data types (widths/heights are numeric, segments are strings)
  - Verify segment formatting (comma-separated values)

### New Files
**app/tests/assets/simple_fixture.dxf**
- Test fixture with simple rectangular block with known dimensions
- Used to validate basic dimension extraction and segment calculation

**app/tests/assets/complex_fixture.dxf**
- Test fixture with complex multi-component block (simulating refrigerated case)
- Contains multiple geometric boundaries (housing, frames, shelves, vents)
- Used to validate intersection point identification and segment calculation

## Implementation Plan

### Phase 1: Foundation
Establish data structures, constants, and helper functions:
1. Add block geometry analysis fields to `ExtractionResult` TypedDict
2. Add Excel sheet and column constants to constants.py
3. Design data structure for storing block dimensions and segments
4. Create helper functions for geometric analysis (bounding box, intersection detection)

### Phase 2: Core Implementation
Implement block geometry extraction and analysis:
1. Create `_analyze_block_geometry()` function to extract block definitions
2. Calculate native bounding box (min/max extents at 0° rotation)
3. Identify vertical intersection points (unique X-coordinates of geometry boundaries)
4. Identify horizontal intersection points (unique Y-coordinates of geometry boundaries)
5. Calculate segment sizes (distances between consecutive intersection points)
6. Store results in new ExtractionResult fields

### Phase 3: Integration
Update Excel generation to display trimming analysis:
1. Create `_create_block_trimming_analysis_sheet()` to generate the new sheet
2. Format segments as comma-separated values
3. Apply proper column widths and auto-filtering
4. Integrate new sheet into main `write_excel()` function
5. Ensure sheet ordering and formatting consistency

## Step by Step Tasks

### 1. Update Constants
- Add sheet name constant: `EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS: str = 'Block Trimming Analysis'`
- Add column constants following naming convention:
  - `EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: str = 'block_native_width'`
  - `EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: str = 'block_native_height'`
  - `EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: str = 'block_vertical_segments'`
  - `EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: str = 'block_horizontal_segments'`
- Add inline comments referencing app_docs/005-field-naming-convention.md
- Group all Block Trimming Analysis constants together

### 2. Update ExtractionResult TypedDict
- Add new field: `block_trimming_data: dict[str, dict[str, Any]]` to ExtractionResult
- Structure: `{block_name: {native_width: float, native_height: float, vertical_segments: list[float], horizontal_segments: list[float]}}`
- Update ExtractionResult docstring with examples
- Document that segments are ordered left-to-right (vertical) and bottom-to-top (horizontal)
- Import Any from typing if not already imported

### 3. Implement Block Bounding Box Extraction
- Create helper function `_get_block_bounding_box(block_def) -> tuple[float, float, float, float]`
- Iterate through all entities in block definition
- Extract min/max X and Y coordinates using ezdxf geometry utilities
- Return (min_x, min_y, max_x, max_y) tuple
- Handle empty blocks gracefully (return (0, 0, 0, 0))
- Add comprehensive docstring with examples

### 4. Implement Intersection Point Identification
- Create helper function `_get_intersection_points(block_def) -> tuple[list[float], list[float]]`
- Iterate through block entities and extract geometric vertices/boundaries
- Collect unique X-coordinates for vertical intersections
- Collect unique Y-coordinates for horizontal intersections
- Sort intersection points in ascending order
- Filter out duplicate points (use small epsilon for floating-point comparison)
- Return (sorted_vertical_points, sorted_horizontal_points)
- Add comprehensive docstring

### 5. Implement Segment Calculation
- Create helper function `_calculate_segments(intersection_points: list[float]) -> list[float]`
- Take sorted list of intersection points
- Calculate distances between consecutive points
- Return list of segment sizes
- Handle edge cases: empty list, single point
- Round segment sizes to reasonable precision (2 decimal places)
- Add comprehensive docstring with examples

### 6. Integrate Block Geometry Analysis into extract_blocks()
- Initialize `block_trimming_data: dict[str, dict[str, Any]] = {}` in extract_blocks()
- After extracting block_entities, iterate through block definitions again
- For each block (skip anonymous blocks):
  - Get bounding box to calculate native width and height
  - Get intersection points (vertical and horizontal)
  - Calculate segments from intersection points
  - Store in block_trimming_data dictionary
- Add block_trimming_data to returned ExtractionResult
- Add logger statement: `logger.info(f"Analyzed geometry for {len(block_trimming_data)} block definitions")`
- Update extract_blocks() docstring to mention trimming analysis

### 7. Write Unit Tests for Bounding Box Extraction
- Add test `test_get_block_bounding_box_simple()` in test_extractor.py
- Create simple test block with known extents
- Verify bounding box matches expected values
- Test with rectangular block: verify width and height calculation
- Test with empty block: verify returns (0, 0, 0, 0)

### 8. Write Unit Tests for Intersection Point Identification
- Add test `test_get_intersection_points_simple()` in test_extractor.py
- Create test block with known geometry vertices
- Verify vertical intersection points are identified correctly
- Verify horizontal intersection points are identified correctly
- Verify points are sorted in ascending order
- Verify duplicate points are filtered

### 9. Write Unit Tests for Segment Calculation
- Add test `test_calculate_segments()` in test_extractor.py
- Test with simple list: [0, 50, 1150, 1200] → [50, 1100, 50]
- Test with single point: [0] → []
- Test with empty list: [] → []
- Test with two points: [0, 100] → [100]
- Verify segments are rounded appropriately

### 10. Write Integration Tests for Block Geometry Analysis
- Add test `test_extract_block_trimming_data()` in test_extractor.py
- Use sample_drawing.dxf or create simple_fixture.dxf
- Verify block_trimming_data is present in ExtractionResult
- Verify structure: each block has native_width, native_height, vertical_segments, horizontal_segments
- Verify all values are correct types (floats for dimensions, list[float] for segments)
- Verify at least one block has non-empty segment lists

### 11. Create Test Fixtures
- Create app/tests/assets/simple_fixture.dxf using ezdxf:
  - Single block with rectangular geometry: 1200mm × 600mm
  - Simple structure: 50mm borders on all sides, 1100mm × 500mm center
  - Expected vertical segments: [50, 1100, 50]
  - Expected horizontal segments: [50, 500, 50]
- Create app/tests/assets/complex_fixture.dxf:
  - Block simulating refrigerated display case
  - Asymmetric structure with multiple components
  - Expected vertical segments: [200, 50, 1100, 50, 1100, 50, 450] (7 segments)
  - Expected horizontal segments: [150, 1200, 150] (3 segments)

### 12. Create Block Trimming Analysis Sheet Function
- Create `_create_block_trimming_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None`
- Extract block_trimming_data from ExtractionResult
- Build DataFrame rows:
  - block_name: str
  - native_width: float
  - native_height: float
  - vertical_segments: str (comma-separated values, e.g., "50, 1100, 50")
  - horizontal_segments: str (comma-separated values)
- Convert segment lists to comma-separated strings: `", ".join(map(str, segments))`
- Sort DataFrame by block_name alphabetically
- Handle empty block_trimming_data: create DataFrame with headers only
- Write to Excel with sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS
- Add logger statement: `logger.info(f"Block Trimming Analysis sheet created with {len(df)} rows")`

### 13. Create Formatting Function
- Create `_format_block_trimming_analysis_sheet(wb: Workbook) -> None`
- Apply auto-filter to all columns
- Set column widths:
  - Column A (block_name): 30
  - Column B (block_native_width): 20
  - Column C (block_native_height): 20
  - Column D (block_vertical_segments): 40
  - Column E (block_horizontal_segments): 40
- Add logger statement: `logger.info("Block Trimming Analysis sheet formatted")`

### 14. Integrate New Sheet into write_excel()
- Import new constants and functions
- Add call to `_create_block_trimming_analysis_sheet(extraction_data, writer)` in write_excel()
- Add call to `_format_block_trimming_analysis_sheet(wb)` after loading workbook
- Update write_excel() docstring to mention four sheets instead of three
- Ensure sheet ordering: Block Counts, Layer Analysis, Entity Summary, Block Trimming Analysis

### 15. Write Unit Tests for Excel Sheet Creation
- Update test_excel_writer.py with new tests:
  - `test_excel_has_block_trimming_analysis_sheet()`: Verify sheet exists
  - `test_block_trimming_analysis_sheet_headers()`: Verify column headers match constants
  - `test_block_trimming_analysis_sheet_data_types()`: Verify widths/heights are numeric
  - `test_block_trimming_analysis_segment_formatting()`: Verify segments are comma-separated strings
  - `test_block_trimming_analysis_empty_data()`: Verify empty data creates sheet with headers only

### 16. Write Integration Tests for Full Pipeline
- Create test that runs full pipeline: extract → write Excel → verify trimming sheet
- Use simple_fixture.dxf: verify segment values match expected
- Use complex_fixture.dxf: verify complex geometry is analyzed correctly
- Verify all four sheets exist in generated Excel file
- Verify Block Trimming Analysis sheet is properly formatted

### 17. Validation - Run All Tests
- Execute `uv run pytest app/tests/core/test_extractor.py -v` to validate extraction tests pass
- Execute `uv run pytest app/tests/core/test_excel_writer.py -v` to validate Excel tests pass
- Execute `uv run pytest app/tests/ -v` to run full test suite
- Execute `uv run mypy app/` to verify type checking passes
- Verify zero regressions in existing tests

### 18. End-to-End Validation
- Execute `bash scripts/start.sh` to launch GUI
- Test with app/tests/assets/sample_drawing.dxf
- Verify Excel opens with four sheets
- Verify Block Trimming Analysis sheet shows block dimensions and segments
- Verify segment formatting is readable (comma-separated values)
- Test with simple_fixture.dxf: verify segment values are correct
- Test with complex_fixture.dxf: verify complex geometry analysis
- Verify existing sheets (Block Counts, Layer Analysis, Entity Summary) remain unchanged

## Testing Strategy

### Unit Tests

**Bounding Box Extraction (test_extractor.py)**
- `test_get_block_bounding_box_simple()`: Verify bounding box calculation for simple rectangular block
- `test_get_block_bounding_box_empty()`: Verify empty block returns (0, 0, 0, 0)
- `test_get_block_bounding_box_negative_coords()`: Verify blocks with negative coordinates work correctly

**Intersection Point Identification (test_extractor.py)**
- `test_get_intersection_points_simple()`: Verify intersection points identified correctly
- `test_get_intersection_points_sorting()`: Verify points are sorted in ascending order
- `test_get_intersection_points_deduplication()`: Verify duplicate points are filtered
- `test_get_intersection_points_empty_block()`: Verify empty block returns empty lists

**Segment Calculation (test_extractor.py)**
- `test_calculate_segments_normal()`: Test with typical intersection point list
- `test_calculate_segments_edge_cases()`: Test with empty, single point, two points
- `test_calculate_segments_precision()`: Verify rounding to appropriate precision

**Block Geometry Analysis Integration (test_extractor.py)**
- `test_extract_block_trimming_data()`: Verify block_trimming_data field exists and has correct structure
- `test_block_trimming_data_types()`: Verify all values are correct types
- `test_block_trimming_data_simple_fixture()`: Test with simple_fixture.dxf with known values
- `test_block_trimming_data_complex_fixture()`: Test with complex_fixture.dxf

**Excel Sheet Creation (test_excel_writer.py)**
- `test_excel_has_block_trimming_analysis_sheet()`: Verify fourth sheet exists
- `test_block_trimming_analysis_sheet_headers()`: Verify column headers
- `test_block_trimming_analysis_sheet_data_types()`: Verify data types
- `test_block_trimming_analysis_segment_formatting()`: Verify comma-separated formatting
- `test_block_trimming_analysis_sorting()`: Verify blocks sorted alphabetically
- `test_block_trimming_analysis_empty_data()`: Verify empty data handling

### Integration Tests

**Full Pipeline Test**
- Load simple_fixture.dxf → extract → generate Excel → verify trimming analysis sheet
- Verify segment values match expected values from fixture
- Verify all four sheets exist and are properly formatted

**Complex Geometry Test**
- Load complex_fixture.dxf → extract → verify complex intersection detection
- Verify asymmetric segment patterns are captured correctly

**Real File Test**
- Load sample_drawing.dxf → extract → verify real block geometry analysis
- Verify existing blocks have trimming analysis data

### Edge Cases

**Empty Drawing**
- File with no blocks → block_trimming_data is empty → sheet has headers only

**Simple Rectangular Blocks**
- Block with no internal structure → should show two intersection points (min/max X/Y)
- Segments list will have single value (total width/height)

**Complex Multi-Component Blocks**
- Refrigerated case with 7 vertical segments → verify all boundaries captured
- Asymmetric structures → verify left/right and top/bottom analyzed independently

**Blocks with Circular or Arc Geometry**
- Blocks containing arcs/circles → verify bounding box calculation works
- Intersection detection may need to handle non-linear geometry

**Very Small Blocks**
- Blocks with dimensions < 1mm → verify precision handling
- Avoid floating-point precision issues in segment calculation

**Overlapping Geometry**
- Block with overlapping entities → verify intersection deduplication works

## Acceptance Criteria

1. **Data Model**
   - ExtractionResult includes `block_trimming_data: dict[str, dict[str, Any]]` field
   - Each block entry contains: native_width, native_height, vertical_segments, horizontal_segments
   - Segments are lists of floats representing distances between intersection points
   - All dimensions use CAD file units (mm or inches, depending on drawing)

2. **Excel Output**
   - New "Block Trimming Analysis" sheet added as fourth sheet
   - Five columns: block_name, block_native_width, block_native_height, block_vertical_segments, block_horizontal_segments
   - Segments formatted as comma-separated values for readability
   - Rows sorted alphabetically by block_name
   - Auto-filter applied to all columns
   - Column widths appropriate for content

3. **Data Accuracy**
   - Native dimensions match block bounding box at 0° rotation
   - Intersection points correctly identified from block geometry
   - Segment calculations are accurate (distances between consecutive points)
   - Segments ordered correctly: vertical (left-to-right), horizontal (bottom-to-top)

4. **Type Safety**
   - All type hints correct and mypy passes with zero errors
   - Proper handling of floats for dimensions and segments
   - String formatting for comma-separated segment values

5. **Testing**
   - All new unit tests pass
   - All existing tests pass (zero regressions)
   - Test coverage includes edge cases (empty blocks, complex geometry)
   - Test fixtures with known geometry validate extraction accuracy

6. **Code Quality**
   - Field naming follows app_docs/005-field-naming-convention.md
   - Constants used for all sheet and column names
   - Docstrings comprehensive and accurate
   - Logging statements for observability
   - Helper functions well-documented

7. **User Experience**
   - GUI workflow unchanged (browse → extract → auto-open Excel)
   - Excel opens successfully with four sheets
   - Trimming analysis data is readable and actionable
   - No breaking changes to existing sheets
   - Users can identify structural boundaries from segment patterns

8. **Documentation**
   - Spec document clearly explains the feature and user workflow
   - Code comments explain geometric analysis logic
   - Test fixtures document expected values

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_get_block_bounding_box_simple -v` - Validate bounding box extraction
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_get_intersection_points_simple -v` - Validate intersection point identification
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_calculate_segments -v` - Validate segment calculation
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_extract_block_trimming_data -v` - Validate block geometry analysis
- `uv run pytest app/tests/core/test_extractor.py -v` - Validate all extractor tests pass
- `uv run pytest app/tests/core/test_excel_writer.py::TestExcelWriter::test_excel_has_block_trimming_analysis_sheet -v` - Validate new sheet exists
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate all Excel writer tests pass
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage includes new trimming analysis code
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI and manually test extraction to verify Block Trimming Analysis sheet appears with correct data

## Notes

### Field Naming Convention Compliance
The new trimming analysis fields follow the established convention from app_docs/005-field-naming-convention.md:
- `block_native_width`, `block_native_height` - follows {domain}_{qualifier}_{attribute} pattern
  - Domain: `block` (dimensions of block definition)
  - Qualifier: `native` (at 0° rotation, unrotated state)
  - Attribute: `width`, `height` (dimensional measurements)
- `block_vertical_segments`, `block_horizontal_segments` - follows {domain}_{attribute}_{qualifier} pattern
  - Domain: `block` (segments within block geometry)
  - Attribute: `vertical`, `horizontal` (orientation of segment measurements)
  - Qualifier: `segments` (plural for collection of measurements)

### Geometric Coordinate System
CAD coordinate systems use:
- X-axis: horizontal (left-to-right is positive X)
- Y-axis: vertical (bottom-to-top is positive Y)
- Origin (0, 0): typically bottom-left corner of block bounding box

Segments are ordered to match user mental model:
- Vertical segments: left-to-right (increasing X)
- Horizontal segments: bottom-to-top (increasing Y)

This matches the trim parameter convention:
- Trim Left affects minimum X boundary
- Trim Right affects maximum X boundary
- Trim Bottom affects minimum Y boundary
- Trim Top affects maximum Y boundary

### Intersection Point Detection Strategy
The implementation identifies intersection points by:
1. Iterating through all entities in block definition
2. Extracting vertex coordinates (for lines, polylines, etc.)
3. Collecting unique X-coordinates and unique Y-coordinates
4. Sorting and deduplicating with floating-point tolerance (epsilon = 0.01mm)
5. Representing structural boundaries where geometry changes

This approach works for:
- Rectangular geometry (4 intersection points: min/max X and Y)
- Multi-component structures (many intersection points revealing layers)
- Complex fixtures with asymmetric designs

### Segment Interpretation for Users
Users interpret segment patterns to identify trim values:

**Symmetric Pattern (simple fixture):**
- Vertical: [50, 1100, 50] → 50mm trim left/right
- Horizontal: [25, 550, 25] → 25mm trim top/bottom
- Center segment = merchandisable space

**Asymmetric Pattern (complex fixture):**
- Vertical: [200, 50, 1100, 50, 1100, 50, 450] → 200mm trim left, 450mm trim right
- Multiple center segments = multiple merchandisable zones (e.g., double-door fridge)

**Single Segment (no internal structure):**
- Vertical: [1200] → no internal boundaries, entire width is block extent
- May need external specifications to determine trim values

### Performance Considerations
- Geometry analysis happens once per unique block definition (not per insertion)
- For a drawing with 100 unique blocks, analysis runs 100 times
- Intersection detection is O(n) where n = number of entities in block definition
- Typical blocks have 10-50 entities, so analysis is fast
- Memory impact is minimal (stores 4-8 values per block)

### Future Enhancements
This feature enables additional capabilities:
- Visual trimming guide overlays in GUI
- Automatic trim value suggestions based on segment patterns
- Validation warnings for unusual segment distributions
- Export trim values directly to the other application's Excel format
- Integration with the rotation analysis feature to show how rotations affect visual trim sides

### Alternative Considered: Detailed Intersection Coordinates
An alternative design would show exact X/Y coordinates of intersection points instead of segment sizes. This was rejected because:
- Users need distances (trim amounts), not absolute coordinates
- Coordinate values are less intuitive (require mental subtraction)
- Segment sizes directly answer "how much to trim"
- Current approach is more actionable

### Relationship to Block Rotation Feature
This feature complements the existing block rotation analysis (specs/004-add-block-rotation-counts.md):
- Rotation feature shows how blocks are oriented when placed
- Trimming feature shows block geometry at native 0° orientation
- Together, they help users understand: "This block is rotated 90° in the drawing, but its trim values are based on the 0° orientation shown in the trimming analysis"

### ezdxf Geometry Utilities
The implementation uses ezdxf's built-in geometry utilities:
- `entity.dxf.insert` for block insertion points
- Entity bounding box methods for extent calculation
- Vertex extraction from LINE, LWPOLYLINE, POLYLINE, ARC, CIRCLE entities
- Block definition entity iteration via `block_def` object

### Handling Non-Rectangular Geometry
Blocks with arcs, circles, and curves:
- Bounding box still captures overall extents (min/max X/Y)
- Intersection detection may miss curved boundaries (only captures vertices)
- Future enhancement: sample points along curves to improve intersection detection
- Current implementation provides baseline analysis sufficient for most retail fixtures

### Precision and Rounding
- CAD drawings use high precision (many decimal places)
- Segment values rounded to 2 decimal places for readability
- Epsilon tolerance (0.01mm) used for deduplicating intersection points
- Prevents floating-point precision errors from creating spurious segments

### User Documentation Recommendation
When deploying this feature, provide users with:
- Explanation of "native orientation" (0° rotation)
- Guide to interpreting segment patterns
- Examples of common fixture types with their typical segment structures
- Relationship between segment positions and trim parameters
