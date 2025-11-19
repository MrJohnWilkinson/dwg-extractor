# Feature: Scale Variance Detection

## Feature Description
Enhance the CAD block analysis to detect and display when blocks have been inserted with varying scale values across their insertions. This feature identifies inconsistencies in drawings where the same block appears at different scales, providing visual warnings through "VARIES" indicators and yellow highlighting in Excel reports. The implementation tracks all unique scale combinations per block name (across all layers), determines when variance exists, and displays either actual numeric values (when consistent) or "VARIES" (when inconsistent) with appropriate visual highlighting.

## User Story
As a CAD analyst
I want to see when a block has been inserted with different scale values
So that I can identify inconsistencies in my drawings and understand that the displayed scale values may not represent all insertions

## Problem Statement
Currently, the Block Geometry Analysis sheet displays only the first encountered scale value for each block-layer pair (lines 216-218 in extractor.py). This approach has several limitations:

1. **Incomplete Information**: When a block is inserted multiple times with different scale factors, only the first scale value is shown
2. **Hidden Variance**: Users cannot tell if a block has scale inconsistencies across insertions
3. **Misleading Data**: A single scale value displayed suggests all insertions use that scale, which may not be true
4. **Manual Verification Required**: Users must manually inspect CAD files to discover scale variations

The existing red highlighting for negative scales (mirroring) in excel_formatting.py (lines 169-197) needs to be refactored to work with the new "VARIES" string values and variance-based highlighting logic.

## Solution Statement
Implement comprehensive scale variance detection by:

1. **Enhanced Extraction**: Modify the extractor to track all unique (x_scale, y_scale) combinations per block name across all insertions and layers
2. **Variance Analysis**: Add logic to determine if a block has multiple different scale values for X or Y axes independently
3. **Smart Display Logic**: Show either numeric values (when consistent) or "VARIES" string (when variance detected) per axis
4. **Visual Highlighting**: Apply yellow background color to rows containing "VARIES" to draw immediate attention
5. **Clean Refactoring**: Remove old negative-scale highlighting logic and replace with variance-based highlighting
6. **Clear Separation**: Maintain clean boundaries between extraction logic (data collection) and formatting logic (presentation)

## Relevant Files
Use these files to implement the feature:

**Core Extraction Logic**
- `app/core/extractor.py` (lines 207-218)
  - Currently stores only first scale value per block-layer pair
  - Need to track ALL unique scale combinations per block name
  - Add data structure to store scale sets: `dict[str, set[tuple[float, float]]]`
  - Modified to collect all scales across all insertions

**Excel Generation**
- `app/core/excel_writer.py` (lines 290-294)
  - Currently retrieves single scale tuple from block_scale_data
  - Need to implement variance detection logic
  - Determine if X scale varies, if Y scale varies
  - Display "VARIES" or numeric value per axis

**Excel Formatting**
- `app/core/excel_formatting.py` (lines 169-197)
  - Currently highlights rows with negative scales (red fill)
  - Need to remove negative scale highlighting logic
  - Add new variance highlighting logic (yellow fill for "VARIES")
  - Check for string value "VARIES" in scale columns

**Type Definitions**
- `app/core/extractor.py` (lines 33-70)
  - Update ExtractionResult TypedDict
  - Change block_scale_data from `dict[tuple[str, str], tuple[float, float]]`
  - To: `dict[str, set[tuple[float, float]]]` (block name -> set of unique scale pairs)

**Constants**
- `app/core/constants.py`
  - May need to add color constants for yellow highlighting
  - No new column constants needed (using existing EXCEL_COLUMN_BLOCK_SCALE_X/Y)

### New Files
None required - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
**Update Data Structures**
- Modify ExtractionResult TypedDict to change block_scale_data structure from per-layer to per-block
- Track all unique scale combinations globally per block name (across all layers)
- Ensure backward compatibility during transition

### Phase 2: Core Implementation
**Extraction Logic Enhancement**
- Modify extract_blocks() to collect all scale values per block name
- Use set[tuple[float, float]] to track unique (x_scale, y_scale) combinations
- Remove the "only first occurrence" limitation in current implementation

**Variance Detection Logic**
- Implement helper functions to detect X-axis and Y-axis variance independently
- Extract all X scales from the set of scale pairs
- Extract all Y scales from the set of scale pairs
- Return boolean flags indicating variance for each axis

**Excel Display Logic**
- Add logic to write_excel to determine variance per block
- Display "VARIES" when multiple unique values exist for an axis
- Display numeric value when only one unique value exists for an axis
- Handle edge cases (empty data, missing geometry)

### Phase 3: Integration
**Visual Highlighting**
- Remove old negative-scale red highlighting from _format_block_geometry_analysis_sheet()
- Implement yellow highlighting for rows containing "VARIES" in either scale column
- Iterate through rows checking for string value "VARIES"
- Apply PatternFill with yellow color (FFFFFF00)

**Testing Integration**
- Ensure all existing tests pass
- Add new tests for variance detection scenarios
- Update tests that relied on old highlighting behavior

## Step by Step Tasks

### Step 1: Update Type Definitions
- Modify ExtractionResult TypedDict in app/core/extractor.py (line 65)
- Change block_scale_data type from `dict[tuple[str, str], tuple[float, float]]` to `dict[str, set[tuple[float, float]]]`
- Update docstring to reflect new structure (line 43-45)
- Update examples in docstring (line 55)

### Step 2: Modify Extraction Logic
- Modify extract_blocks() initialization in app/core/extractor.py (line 137)
- Change block_scale_data from dict[tuple, tuple] to dict[str, set[tuple]]
- Modify scale extraction logic (lines 207-218)
- Remove "only first occurrence" check (line 217)
- Track all unique scales per block name: `block_scale_data[block_name].add((x_scale, y_scale))`
- Use defaultdict or explicit set initialization

### Step 3: Add Variance Detection Helpers
- Add helper functions to app/core/excel_writer.py before write_excel()
- Implement `_has_x_scale_variance(scale_set: set[tuple[float, float]]) -> bool`
  - Extract all unique X values from scale tuples
  - Return True if more than one unique X value exists
- Implement `_has_y_scale_variance(scale_set: set[tuple[float, float]]) -> bool`
  - Extract all unique Y values from scale tuples
  - Return True if more than one unique Y value exists
- Implement `_get_single_scale_value(scale_set: set[tuple[float, float]], axis: str) -> float`
  - Extract and return the single scale value for given axis ('x' or 'y')
  - Used when variance is False

### Step 4: Update Excel Writing Logic
- Modify _create_block_geometry_analysis_sheet() in app/core/excel_writer.py (lines 290-294)
- Change scale data retrieval to use block_name instead of (block_name, layer_name)
- Implement variance detection for each block
- Display logic:
  - If X variance detected: set x_scale = "VARIES"
  - If no X variance: set x_scale = numeric value
  - If Y variance detected: set y_scale = "VARIES"
  - If no Y variance: set y_scale = numeric value
- Update row dictionary to use string/numeric values appropriately

### Step 5: Remove Old Highlighting Logic
- Remove negative scale highlighting from app/core/excel_formatting.py (lines 169-197)
- Delete the red_fill PatternFill definition
- Delete the iteration logic checking for negative scales
- Delete the red fill application logic
- Keep the auto-filter and column width logic intact

### Step 6: Implement Variance Highlighting
- Add variance highlighting to _format_block_geometry_analysis_sheet() in app/core/excel_formatting.py
- Create yellow_fill PatternFill with color FFFFFF00
- Iterate through data rows (skip header at row 1)
- Check columns H (x_scale) and I (y_scale) for string value "VARIES"
- If either cell contains "VARIES", apply yellow fill to entire row (columns A-M)
- Track and log number of highlighted rows

### Step 7: Write Unit Tests for Extraction
- Create test fixtures in app/tests/core/test_extractor.py
- Test variance detection with known DXF files
- Test cases:
  - Block with consistent scales across all insertions
  - Block with varying X scales only
  - Block with varying Y scales only
  - Block with varying both X and Y scales
  - Block with single insertion (no variance)
  - Empty file handling
- Verify block_scale_data structure is dict[str, set[tuple]]
- Verify all unique scales are captured

### Step 8: Write Unit Tests for Excel Writer
- Update test fixtures in app/tests/core/test_excel_writer.py
- Modify sample_extraction_data fixture to use new block_scale_data structure
- Add test cases:
  - test_scale_variance_detection_varies_x_only()
  - test_scale_variance_detection_varies_y_only()
  - test_scale_variance_detection_varies_both()
  - test_scale_variance_detection_consistent_scales()
  - test_scale_variance_display_numeric_when_consistent()
  - test_scale_variance_display_varies_string()
- Verify "VARIES" string appears in appropriate cells
- Verify numeric values appear when no variance

### Step 9: Write Unit Tests for Formatting
- Update tests in app/tests/core/test_excel_formatting.py or test_excel_writer.py
- Remove tests that validate red highlighting for negative scales
- Add test cases:
  - test_variance_yellow_highlighting_x_varies()
  - test_variance_yellow_highlighting_y_varies()
  - test_variance_yellow_highlighting_both_vary()
  - test_no_highlighting_when_consistent()
- Verify yellow fill (FFFFFF00) applied to correct rows
- Verify no highlighting on rows without "VARIES"

### Step 10: Create Test Fixtures
- Create new DXF test file: app/tests/assets/scale_variance_test.dxf
- Include blocks with:
  - Same block at scale (1.0, 1.0) and (2.0, 1.0) - X varies
  - Same block at scale (1.0, 1.0) and (1.0, 2.0) - Y varies
  - Same block at scale (1.0, 1.0), (2.0, 2.0), (-1.0, 1.0) - Both vary
  - Same block at consistent scale (1.5, 1.5) across multiple insertions
- Use ezdxf to generate this test file programmatically

### Step 11: Update Integration Tests
- Review existing integration tests in app/tests/core/test_excel_writer.py
- Update tests that verify block_scale_data structure
- Update test_geometry_sheet_red_highlighting() - should now test yellow highlighting
- Ensure test_block_geometry_analysis_has_scales() works with new variance logic
- Update any tests checking exact scale values

### Step 12: Run Validation Commands
- Execute all validation commands listed below
- Fix any test failures
- Verify zero regressions
- Test with real DWG/DXF files to ensure feature works end-to-end

## Testing Strategy

### Unit Tests

**Extraction Tests (app/tests/core/test_extractor.py)**
- test_block_scale_data_structure_is_per_block(): Verify new dict[str, set] structure
- test_block_scale_data_captures_all_unique_scales(): Verify all scales tracked
- test_block_scale_data_with_variance(): Known file with varying scales
- test_block_scale_data_without_variance(): Known file with consistent scales
- test_block_scale_data_single_insertion(): Edge case single insertion
- test_block_scale_data_across_multiple_layers(): Verify cross-layer aggregation
- test_block_scale_data_missing_attributes(): Handle missing xscale/yscale gracefully

**Excel Writer Tests (app/tests/core/test_excel_writer.py)**
- test_variance_detection_helpers(): Test _has_x_scale_variance and _has_y_scale_variance
- test_get_single_scale_value_helper(): Test _get_single_scale_value function
- test_excel_displays_varies_for_x_variance(): Verify "VARIES" in X Scale column
- test_excel_displays_varies_for_y_variance(): Verify "VARIES" in Y Scale column
- test_excel_displays_varies_for_both_variance(): Verify "VARIES" in both columns
- test_excel_displays_numeric_when_consistent(): Verify numeric values shown
- test_scale_columns_accept_mixed_types(): Verify columns accept float and str
- test_empty_scale_data_handling(): Edge case with no scale data

**Formatting Tests (app/tests/core/test_excel_formatting.py or test_excel_writer.py)**
- test_yellow_highlighting_for_varies(): Verify FFFFFF00 fill applied
- test_no_red_highlighting_for_negative_scales(): Verify old logic removed
- test_highlighting_entire_row_on_variance(): Verify all 13 columns highlighted
- test_no_highlighting_without_variance(): Verify no fill when consistent
- test_highlighting_count_matches_varies_rows(): Count highlighted rows

### Integration Tests

**End-to-End Excel Generation**
- test_full_extraction_with_scale_variance(): Extract → Write → Verify complete flow
- test_real_dwg_file_with_known_variance(): Use real DWG with variance
- test_mixed_variance_and_consistent_blocks(): Some blocks vary, some don't
- test_scale_variance_display_matches_extraction(): Verify data consistency

### Edge Cases

**Data Edge Cases**
- Empty scale data (no blocks)
- Single block with single insertion
- Block with missing scale attributes (defaults to 1.0, 1.0)
- Block with zero scales (should still detect variance)
- Block with very small scale differences (floating point precision)

**Display Edge Cases**
- "VARIES" string formatting in Excel cells
- Column width handles "VARIES" text
- Auto-filter works with mixed numeric/string columns
- Sorting works correctly with mixed types
- Yellow highlighting doesn't interfere with other formatting

**Highlighting Edge Cases**
- Rows at top and bottom of sheet
- Empty sheets (headers only)
- Very large sheets (performance)
- Multiple blocks with variance (correct row highlighting)

### Playwright MCP Tests
This feature does not require E2E Playwright tests as it involves:
- Backend data extraction logic (covered by unit tests)
- Excel file generation (covered by integration tests)
- No GUI interaction in the main application

Manual verification:
1. Run the application with a DWG file containing scale variance
2. Open generated Excel file
3. Verify "VARIES" appears in appropriate cells
4. Verify yellow highlighting is visible
5. Verify numeric values shown when scales are consistent

## Acceptance Criteria

1. **Variance Detection**
   - [ ] Extractor tracks ALL unique scale combinations per block name (not per layer)
   - [ ] Variance is detected independently for X and Y axes
   - [ ] Blocks with consistent scales show numeric values
   - [ ] Blocks with varying scales show "VARIES" string

2. **Excel Display**
   - [ ] "VARIES" appears in X Scale column when X scales differ
   - [ ] "VARIES" appears in Y Scale column when Y scales differ
   - [ ] Numeric values displayed when scales are consistent
   - [ ] Mixed numeric and string values work correctly in columns

3. **Visual Highlighting**
   - [ ] Yellow background (FFFFFF00) applied to rows with "VARIES"
   - [ ] Entire row (columns A-M) highlighted, not just scale columns
   - [ ] No highlighting on rows without "VARIES"
   - [ ] Old red highlighting for negative scales completely removed

4. **Code Quality**
   - [ ] Clear separation between extraction and formatting logic
   - [ ] Type definitions updated correctly (ExtractionResult)
   - [ ] No code duplication between variance detection logic
   - [ ] Proper error handling for edge cases

5. **Testing**
   - [ ] All existing tests pass with zero regressions
   - [ ] New unit tests cover variance detection logic
   - [ ] Integration tests verify end-to-end functionality
   - [ ] Edge cases handled gracefully

6. **Documentation**
   - [ ] Docstrings updated for modified functions
   - [ ] Type hints accurate for new data structures
   - [ ] Comments explain variance detection algorithm
   - [ ] Examples in docstrings reflect new behavior

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Validate extraction logic with variance detection
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate Excel generation with "VARIES" display
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Validate yellow highlighting logic
- `uv run pytest app/tests/ -v` - Run complete test suite
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage
- `uv run mypy app/` - Validate type correctness of new data structures
- `uv run ruff check app/` - Ensure code style compliance
- `bash scripts/start.sh` - Manual test: Run application and verify Excel output with real files

## Notes

**Design Decisions**
1. **Per-Block vs Per-Layer Variance**: Track variance at the block level (across all layers) rather than per layer. This gives users a global view of scale inconsistencies for each block.

2. **Independent Axis Detection**: Detect X and Y scale variance independently since blocks can be scaled non-uniformly (e.g., stretched horizontally but not vertically).

3. **"VARIES" String vs Indicator**: Use "VARIES" text rather than symbols or colors alone to ensure accessibility and clarity when printed or viewed in black-and-white.

4. **Yellow vs Other Colors**: Yellow provides good visibility without implying error (red) or success (green). Mirroring (negative scales) is intentional; variance may indicate errors or legitimate design choices.

5. **Remove Old Highlighting**: Clean up legacy red highlighting for negative scales to avoid confusion between mirroring (intentional) and variance (potential issue).

**Implementation Notes**
- Use `set[tuple[float, float]]` for automatic deduplication of scale pairs
- Consider floating-point precision when comparing scales (may need epsilon comparison)
- Ensure "VARIES" string is consistent across codebase (define as constant if used multiple times)
- Keep variance detection helpers private (underscore prefix) as they're internal to excel_writer
- Update ExtractionResult docstring with clear examples of new structure

**Future Enhancements**
- Add column showing the list of unique scale values (e.g., "1.0, 2.0, -1.0")
- Add summary statistics (min/max/avg scale values)
- Filter or sort by variance flag
- Export variance report to separate sheet
- Add rotation variance detection using same pattern
- Configurable variance threshold (ignore tiny differences)

**Performance Considerations**
- Using sets for deduplication is efficient (O(1) insertion, O(n) space)
- Variance detection is O(n) where n is number of unique scales per block (typically small)
- No performance impact on large files as variance check is per-block, not per-insertion

**Breaking Changes**
None - this is an enhancement that adds information without removing existing functionality. The Block Geometry Analysis sheet structure remains the same (13 columns).

**Migration Notes**
No data migration required. This is a code-only change that affects how data is processed and displayed, not how it's stored.
