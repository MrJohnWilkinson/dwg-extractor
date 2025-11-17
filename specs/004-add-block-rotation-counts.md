# Feature: Block Rotation Counts

## Feature Description
Enhance the Block Counts sheet to display rotation breakdowns for each block-layer pair. Each row will show not only the block name, total insertion count, entity count, and layer name, but also a breakdown of how many insertions occur at each standard rotation angle (0°, 90°, 180°, 270°, and Other).

This provides users with visibility into the orientation distribution of blocks in their CAD drawings, enabling them to understand:
- How blocks are oriented across the drawing
- Whether blocks follow standard orthogonal rotations or have custom angles
- Rotation patterns for specific blocks on specific layers
- Quality control for drawings that require standard orientations

The rotation columns will display counts for each rotation category, and the sum of all rotation counts will equal the total block_insertion_count for validation.

## User Story
As a CAD file analyst
I want to see how many times each block is inserted at different rotation angles
So that I can understand block orientation patterns, validate consistent rotation usage, and identify blocks with non-standard angles

## Problem Statement
Currently, the Block Counts sheet shows which blocks are inserted and where (by layer), but provides no information about block orientation. Users cannot determine:
- How many blocks are rotated at standard angles (0°, 90°, 180°, 270°)
- Which blocks have non-standard rotation angles
- Whether blocks are consistently oriented or randomly rotated
- Rotation patterns specific to certain layers
- Whether rotation standards are being followed in the drawing

For example, DOOR_SINGLE might appear 45 times on the ARCHITECTURE layer, but users can't see that 12 face one direction (0°), 18 face another (90°), 10 are opposite (180°), and 5 face the fourth direction (270°). This information is critical for understanding door placement patterns and validating architectural standards.

## Solution Statement
Extend the extraction and Excel generation pipeline to track and display rotation counts:

1. **Extraction Layer**: Track rotation angles for each INSERT entity, normalize them to standard angles (0°, 90°, 180°, 270°), categorize non-standard angles as "Other"
2. **Data Structure**: Add a new `block_rotation_counts` dictionary to ExtractionResult: `dict[tuple[str, str, str], int]` mapping (block_name, layer_name, rotation_category) tuples to insertion counts
3. **Excel Generation**: Add five new columns to the Block Counts sheet (0°, 90°, 180°, 270°, Other) showing rotation breakdowns for each block-layer pair
4. **Field Naming**: Follow the established naming convention: `block_rotation_0`, `block_rotation_90`, `block_rotation_180`, `block_rotation_270`, `block_rotation_other`
5. **Validation**: Ensure sum of rotation columns equals block_insertion_count for each row

This approach maintains the existing four-column structure while adding five rotation breakdown columns, for a total of nine columns.

## Relevant Files
Use these files to implement the feature:

**app/core/extractor.py**
- Contains the `extract_blocks()` function that parses DWG/DXF files
- Defines the `ExtractionResult` TypedDict
- Already iterates through INSERT entities and has access to `entity.dxf.rotation` attribute
- Currently tracks block_name and layer_name - needs to also track rotation angles
- Needs function to normalize rotation angles to standard categories

**app/core/excel_writer.py**
- Contains Excel generation logic with sheet creation functions
- `_create_block_counts_sheet()` needs modification to add rotation columns
- `_format_block_counts_sheet()` needs column width settings for five new columns
- Currently creates 4-column Block Counts sheet - will expand to 9 columns

**app/core/constants.py**
- Defines all Excel column name constants following the field naming convention
- Needs new constants for rotation columns:
  - `EXCEL_COLUMN_BLOCK_ROTATION_0`
  - `EXCEL_COLUMN_BLOCK_ROTATION_90`
  - `EXCEL_COLUMN_BLOCK_ROTATION_180`
  - `EXCEL_COLUMN_BLOCK_ROTATION_270`
  - `EXCEL_COLUMN_BLOCK_ROTATION_OTHER`

**app_docs/005-field-naming-convention.md**
- Documents the field naming convention that must be followed
- Provides examples of block domain fields
- Rotation fields should follow pattern: `block_rotation_{category}`

**app/tests/core/test_extractor.py**
- Contains unit tests for the extractor module
- Needs new tests to validate rotation tracking and categorization
- Needs test data with known rotation values

**app/tests/core/test_excel_writer.py**
- Contains Excel generation tests
- Needs updates to test the new rotation columns in the Block Counts sheet

### New Files
**app/tests/assets/test_rotations.dxf**
- New test fixture with blocks at known rotation angles
- Should include blocks at 0°, 90°, 180°, 270°, and non-standard angles
- Will be created during implementation for comprehensive testing

## Implementation Plan

### Phase 1: Foundation
Update the data model and constants to support rotation tracking:
1. Add `block_rotation_counts: dict[tuple[str, str, str], int]` field to `ExtractionResult` TypedDict in extractor.py
2. Add rotation column constants to constants.py following the naming convention
3. Update docstrings in ExtractionResult to document the new field structure
4. Create helper function to normalize rotation angles to categories

### Phase 2: Core Implementation
Modify extraction logic to track rotation angles:
1. Create `_categorize_rotation(angle: float) -> str` helper function to normalize angles to categories
2. Update `extract_blocks()` in extractor.py to populate the `block_rotation_counts` dictionary
3. During INSERT entity iteration, extract rotation angle and categorize it
4. Create composite keys: `(block_name, layer_name, rotation_category)`
5. Increment counts for each unique combination
6. Add logging to report rotation distribution

### Phase 3: Integration
Update Excel generation to display rotation breakdowns:
1. Modify `_create_block_counts_sheet()` to calculate rotation counts for each block-layer pair
2. Add five rotation columns to the DataFrame
3. Ensure sum of rotation columns equals block_insertion_count for validation
4. Update `_format_block_counts_sheet()` to set appropriate column widths for rotation columns
5. Update docstrings to reflect the new nine-column structure

## Step by Step Tasks

### 1. Update Constants
- Add rotation column constants to constants.py:
  - `EXCEL_COLUMN_BLOCK_ROTATION_0: str = 'block_rotation_0'`
  - `EXCEL_COLUMN_BLOCK_ROTATION_90: str = 'block_rotation_90'`
  - `EXCEL_COLUMN_BLOCK_ROTATION_180: str = 'block_rotation_180'`
  - `EXCEL_COLUMN_BLOCK_ROTATION_270: str = 'block_rotation_270'`
  - `EXCEL_COLUMN_BLOCK_ROTATION_OTHER: str = 'block_rotation_other'`
- Add inline comments referencing app_docs/005-field-naming-convention.md
- Group rotation constants together in the Block Counts sheet section

### 2. Update ExtractionResult TypedDict
- Add `block_rotation_counts: dict[tuple[str, str, str], int]` field to ExtractionResult in extractor.py
- Update ExtractionResult docstring to document the block_rotation_counts structure
- Include example in docstring: `{('DOOR', 'WALLS', '0'): 12, ('DOOR', 'WALLS', '90'): 18, ('DOOR', 'WALLS', '180'): 10}`
- Document that rotation categories are strings: '0', '90', '180', '270', 'other'

### 3. Implement Rotation Categorization Helper
- Create `_categorize_rotation(angle: float) -> str` function in extractor.py
- Normalize angles to 0-360 range using modulo: `angle % 360`
- Use tolerance-based comparison (±1 degree) for standard angles to handle floating-point precision
- Return '0', '90', '180', or '270' for standard angles
- Return 'other' for all non-standard angles
- Add comprehensive docstring with examples
- Add unit tests for rotation categorization edge cases

### 4. Implement Block Rotation Tracking
- Initialize `block_rotation_counts: dict[tuple[str, str, str], int] = {}` in extract_blocks()
- During INSERT entity processing:
  - Extract rotation angle: `rotation = entity.dxf.rotation`
  - Categorize rotation: `rotation_category = _categorize_rotation(rotation)`
  - Create composite key: `rotation_key = (block_name, layer_name, rotation_category)`
  - Increment count: `block_rotation_counts[rotation_key] = block_rotation_counts.get(rotation_key, 0) + 1`
- Add block_rotation_counts to the returned ExtractionResult dictionary
- Add logger info statement: `logger.info(f"Tracked rotations for {len(block_rotation_counts)} block-layer-rotation combinations")`
- Update extract_blocks() docstring examples to show block_rotation_counts

### 5. Write Unit Tests for Rotation Categorization
- Add test `test_categorize_rotation_standard_angles()` in test_extractor.py
- Test exact standard angles: 0, 90, 180, 270 → return '0', '90', '180', '270'
- Test angles with tolerance: 0.5, 89.5, 90.5, 179.5, 180.5, 269.5, 270.5 → return correct categories
- Test non-standard angles: 45, 135, 225, 315, 30, 60 → return 'other'
- Test negative angles: -90, -180, -270 → normalize to positive equivalents
- Test angles > 360: 450, 540, 630 → normalize to 90, 180, 270
- Test boundary cases: 359.5 (should normalize to 0), 1.0 (should be 'other')

### 6. Write Unit Tests for Rotation Extraction
- Add test `test_extract_block_rotation_counts()` in test_extractor.py
- Verify block_rotation_counts is present in ExtractionResult
- Verify block_rotation_counts contains tuple keys: (str, str, str)
- Verify counts are positive integers
- Verify rotation categories are valid: '0', '90', '180', '270', 'other'
- Test with fixture file containing known rotation angles

### 7. Create Test Fixture with Rotations
- Create app/tests/assets/test_rotations.dxf using ezdxf
- Insert test blocks at known rotation angles:
  - 5 blocks at 0°
  - 3 blocks at 90°
  - 2 blocks at 180°
  - 1 block at 270°
  - 2 blocks at non-standard angles (45°, 135°)
- Use this fixture in rotation unit tests
- Document the expected counts in test docstrings

### 8. Update Excel Block Counts Sheet Generation
- Modify `_create_block_counts_sheet()` in excel_writer.py to add rotation columns
- Import rotation column constants from constants.py
- For each block-layer pair:
  - Initialize rotation counts: `{0: 0, 90: 0, 180: 0, 270: 0, other: 0}`
  - Iterate through block_rotation_counts to populate rotation breakdown
  - Build row with 9 columns: block_name, insertion_count, entity_count, layer_name, rot_0, rot_90, rot_180, rot_270, rot_other
  - Verify sum of rotation counts equals insertion_count (add assertion or logging)
- Handle empty block_rotation_counts case by creating DataFrame with all 9 column headers
- Update function docstring to reflect nine-column structure

### 9. Update Excel Formatting
- Update `_format_block_counts_sheet()` to set column widths for rotation columns
- Set columns E-I widths to 12 each (compact for numeric counts)
- Columns A-D widths remain: 30, 25, 25, 25
- Update function docstring if needed

### 10. Write Unit Tests for Excel Generation
- Update test_excel_writer.py to validate rotation columns appear in Excel
- Add test to verify Block Counts sheet has nine columns with correct headers
- Verify rotation counts sum to insertion_count for each row
- Verify rotation columns contain only non-negative integers
- Verify sorting by insertion count descending is maintained
- Test empty block_rotation_counts case

### 11. Integration Testing with Real Files
- Create test that generates Excel from fixture with known rotations
- Verify Excel output has correct structure (9 columns)
- Verify rotation counts are accurate for known test data
- Verify sum validation: row['0'] + row['90'] + row['180'] + row['270'] + row['other'] == row['block_insertion_count']
- Test with sample_drawing.dxf (all blocks at 0° rotation)

### 12. Validation - Run All Tests
- Execute `uv run pytest app/tests/core/test_extractor.py -v` to validate extraction tests pass
- Execute `uv run pytest app/tests/core/test_excel_writer.py -v` to validate Excel generation tests pass
- Execute `uv run pytest app/tests/ -v` to run full test suite
- Execute `uv run mypy app/` to verify type checking passes
- Verify zero regressions in existing tests

### 13. End-to-End Validation
- Execute `bash scripts/start.sh` to launch the GUI application
- Select app/tests/assets/test_rotations.dxf
- Click Extract button
- Verify Excel file opens automatically
- Verify Block Counts sheet shows nine columns with rotation breakdown
- Verify rotation counts sum to insertion count for each row
- Verify data is correctly sorted by insertion count descending
- Verify Layer Analysis and Entity Summary sheets remain unchanged
- Test with app/tests/assets/sample_drawing.dxf (should show all counts in 0° column)
- Close application and verify no errors in logs

## Testing Strategy

### Unit Tests

**Rotation Categorization Tests (test_extractor.py)**
- `test_categorize_rotation_standard_angles()`: Verify exact standard angles return correct categories
- `test_categorize_rotation_tolerance()`: Verify angles within ±1° of standard angles are categorized correctly
- `test_categorize_rotation_non_standard()`: Verify non-standard angles return 'other'
- `test_categorize_rotation_normalization()`: Verify negative and >360° angles normalize correctly
- `test_categorize_rotation_boundary_cases()`: Verify edge cases like 359.5°, 1.0°, etc.

**Rotation Extraction Tests (test_extractor.py)**
- `test_extract_block_rotation_counts()`: Verify block_rotation_counts field exists and contains correct data structure
- `test_block_rotation_counts_tuple_keys()`: Verify all keys are (str, str, str) tuples
- `test_block_rotation_counts_valid_categories()`: Verify rotation categories are only '0', '90', '180', '270', 'other'
- `test_block_rotation_counts_conservation()`: Verify sum of rotation counts equals sum of block_layer_pairs
- `test_block_rotation_counts_with_fixture()`: Test with test_rotations.dxf fixture to validate known counts

**Excel Writer Tests (test_excel_writer.py)**
- `test_block_counts_sheet_has_rotation_columns()`: Verify Block Counts sheet has 9 columns including rotation columns
- `test_rotation_counts_sum_to_total()`: Verify rotation columns sum to block_insertion_count for each row
- `test_rotation_counts_are_integers()`: Verify all rotation counts are non-negative integers
- `test_rotation_columns_sorting()`: Verify sorting by insertion count descending is maintained with new columns
- `test_rotation_columns_empty_data()`: Verify empty data creates sheet with all headers including rotation columns

### Integration Tests

**Full Pipeline Test**
- Load test_rotations.dxf → extract → generate Excel → verify rotation breakdown
- Verify rotation counts match expected values from fixture
- Verify sum validation passes for all rows
- Verify Block Counts sheet has correct number of rows and columns

**Real File Test**
- Load sample_drawing.dxf (all blocks at 0°) → extract → generate Excel
- Verify all rotation counts appear in 0° column
- Verify 90°, 180°, 270°, Other columns all show 0

### Edge Cases

**All Standard Rotations**
- File with blocks only at 0°, 90°, 180°, 270° → Other column should show 0 for all rows

**All Non-Standard Rotations**
- File with blocks at 45°, 135°, 225°, 315° → Other column should equal insertion_count, standard columns show 0

**Mixed Rotations**
- Same block-layer pair with multiple rotation angles → verify counts distribute correctly across columns

**Rotation Tolerance**
- Block at 89.8°, 90.0°, 90.2° → all should categorize as '90'
- Block at 0.5° vs 1.5° → 0.5° should be '0', 1.5° should be 'other'

**Negative and Large Angles**
- Block at -90° → should normalize to 270°
- Block at 450° → should normalize to 90°
- Block at -180° → should normalize to 180°

**Empty Data**
- File with no blocks → block_rotation_counts is empty dict → Excel sheet has headers only with 9 columns

**Single Block Multiple Layers**
- DOOR on WALLS at 0°, DOOR on OPENINGS at 90° → should create 2 rows with different rotation distributions

## Acceptance Criteria

1. **Data Model**
   - ExtractionResult includes `block_rotation_counts: dict[tuple[str, str, str], int]` field
   - block_rotation_counts correctly maps (block_name, layer_name, rotation_category) tuples to insertion counts
   - Rotation categories are strings: '0', '90', '180', '270', 'other'
   - Rotation categorization uses ±1° tolerance for standard angles

2. **Excel Output**
   - Block Counts sheet displays nine columns: block_name, block_insertion_count, block_entity_count, block_layer_name, block_rotation_0, block_rotation_90, block_rotation_180, block_rotation_270, block_rotation_other
   - Each row represents a unique block-layer pair with rotation breakdown
   - Rotation columns contain non-negative integers
   - Sum of rotation columns equals block_insertion_count for every row
   - Rows are sorted by block_insertion_count descending
   - Auto-filter is applied to all columns
   - Column widths are appropriate for content

3. **Data Integrity**
   - Sum of all rotation counts across all categories equals total insertions
   - No rotations are lost or double-counted
   - Rotation categorization is deterministic (same angle always produces same category)
   - Empty files produce empty block_rotation_counts and Excel sheet with headers only

4. **Type Safety**
   - All type hints are correct and mypy passes with zero errors
   - Tuple keys in block_rotation_counts are properly typed as tuple[str, str, str]
   - Rotation categorization function has proper type hints

5. **Testing**
   - All new unit tests pass
   - All existing tests pass (zero regressions)
   - Test coverage includes edge cases (tolerance, normalization, non-standard angles)
   - Test fixture with known rotation values validates extraction accuracy

6. **Code Quality**
   - Field naming follows app_docs/005-field-naming-convention.md
   - Constants used for all rotation column names
   - Docstrings updated to reflect new functionality
   - Logging statements added for observability
   - Helper function for rotation categorization is well-documented

7. **User Experience**
   - GUI workflow unchanged (browse → extract → auto-open Excel)
   - Excel file opens successfully with new structure
   - Rotation data is easily readable and properly formatted
   - No breaking changes to existing sheets (Layer Analysis, Entity Summary)
   - Sum validation provides confidence in data accuracy

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_categorize_rotation_standard_angles -v` - Validate rotation categorization for standard angles
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_categorize_rotation_tolerance -v` - Validate rotation tolerance handling
- `uv run pytest app/tests/core/test_extractor.py::TestExtractor::test_extract_block_rotation_counts -v` - Validate rotation extraction logic
- `uv run pytest app/tests/core/test_extractor.py -v` - Validate all extractor tests pass with new rotation logic
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate Excel writer tests pass with new rotation columns
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage includes new rotation code
- `uv run mypy app/` - Verify type checking passes with strict mode
- `bash scripts/start.sh` - Launch GUI and manually test extraction with test_rotations.dxf to verify rotation breakdown in Excel output

## Notes

### Field Naming Convention Compliance
The new rotation fields follow the established convention from app_docs/005-field-naming-convention.md:
- `block_rotation_0`, `block_rotation_90`, etc. - follows {domain}_{attribute}_{qualifier} pattern
- Domain: `block` (rotation is a property of block insertions)
- Attribute: `rotation` (the orientation angle)
- Qualifier: `0`, `90`, `180`, `270`, `other` (specific rotation category)
- Follows the pattern shown in examples: `block_rotation_angles` (collection), but these are individual counts per category

### Rotation Angle Normalization
CAD systems represent rotation angles in degrees, typically in the range 0-360. However, angles can be:
- Negative (e.g., -90° means counterclockwise rotation)
- Greater than 360° (e.g., 450° means 1.25 full rotations)
- Imprecise due to floating-point arithmetic (e.g., 89.999999° instead of exactly 90°)

The implementation uses:
- Modulo operation to normalize to 0-360 range: `angle % 360`
- Tolerance of ±1° for standard angles to handle floating-point precision
- String categories ('0', '90', '180', '270', 'other') for clarity and Excel compatibility

### Rotation Tolerance Rationale
A ±1° tolerance is used for categorizing standard rotations because:
- Floating-point arithmetic in CAD systems can introduce minor precision errors
- Manual rotations in CAD software may not be exactly 90° (e.g., 89.8° or 90.2°)
- The tolerance captures "effectively orthogonal" rotations
- The tolerance is tight enough to avoid false positives (1.5° would clearly be 'other')

### Performance Considerations
- Rotation extraction adds minimal overhead (one additional attribute read per INSERT entity)
- Rotation categorization is O(1) (simple comparisons, no loops)
- Memory impact is small (adds one field per block-layer-rotation combination)
- Excel generation time is similar (same number of rows, just wider columns)

### Future Enhancements
This feature enables additional rotation-based analysis:
- Rotation consistency reports (identify blocks with many non-standard rotations)
- Layer-specific rotation standards validation
- Rotation heatmaps or distribution charts
- Filtering blocks by rotation in the GUI
- Rotation normalization tools (snap all blocks to nearest standard angle)

### Alternative Considered: Single Rotation Histogram Column
An alternative design would add a single column showing rotation distribution as text (e.g., "0°: 12, 90°: 18, 180°: 10"). This was rejected because:
- Not sortable or filterable by specific rotation
- Not usable for Excel formulas or pivot tables
- Less readable for users
- Doesn't follow the structured data principle
- Current approach (separate columns) is more data-centric and analysis-friendly

### Validation Sum Check
The requirement that rotation columns sum to block_insertion_count serves as:
- Data integrity verification (no counts lost during categorization)
- User confidence (visual validation that all insertions are accounted for)
- Debugging aid (mismatches indicate bugs in rotation tracking)
- Documentation of the invariant (clear specification of expected behavior)

### AutoCAD Rotation Convention
AutoCAD uses degrees (not radians) for rotation angles, with:
- 0° = East (positive X-axis direction)
- 90° = North (positive Y-axis direction)
- 180° = West (negative X-axis direction)
- 270° = South (negative Y-axis direction)
- Positive angles = counterclockwise rotation

The ezdxf library preserves this convention in `entity.dxf.rotation`, so no conversion is needed.
