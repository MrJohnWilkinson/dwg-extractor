# Feature: Negative Scale Detection with Color Highlighting

## Feature Description
Extend the existing yellow highlighting system for scale variance to support a three-tier color-coded system that differentiates between positive-only variance, consistent negative scales (mirroring/flipping), and variance with negative values. This enhancement helps CAD analysts quickly identify mirrored or flipped blocks and understand the complexity of scale variance issues by providing visual cues through color-coded row highlighting in the Block Geometry Analysis sheet.

The system analyzes X and Y scale values independently (Z-scale is not tracked) and applies one of three highlight colors based on the underlying scale data:
- **Yellow**: "VARIES" with all positive values (existing behavior)
- **Orange**: Consistent negative number (e.g., -1.0) indicating mirroring/flipping
- **Red**: "VARIES (-)" indicating mixed positive/negative values

## User Story
As a CAD analyst reviewing block geometry
I want negative scale values highlighted with distinct colors in the Block Geometry Analysis sheet
So that I can quickly identify mirrored/flipped blocks and complex scale variance issues

## Problem Statement
Currently, the Block Geometry Analysis sheet uses yellow highlighting to indicate scale variance (when "VARIES" appears in Scale X or Scale Y columns). However, this single-color approach has several limitations:

1. **No Mirroring Detection**: Negative scales (indicating mirrored/flipped blocks) are not visually distinguished from positive scales
2. **Hidden Complexity**: Variance that includes both positive and negative values is not differentiated from positive-only variance
3. **Manual Inspection Required**: Analysts must manually check the underlying CAD file to determine if variance includes negative scales
4. **Missed Design Issues**: Consistent mirroring (all insertions at -1.0) appears as a normal numeric value without highlighting
5. **Incomplete Visual System**: The existing yellow highlighting provides only one level of warning for what can be three distinct scenarios

For example:
- A block inserted at scales {1.0, 2.0, 1.5} shows "VARIES" with yellow highlighting
- A block inserted at scales {1.0, -1.0} also shows "VARIES" with yellow highlighting (same visual treatment despite containing mirroring)
- A block consistently inserted at -1.0 shows "-1.0" without any highlighting (mirroring is invisible)

## Solution Statement
Implement a priority-based three-tier color highlighting system that:

1. **Detects Negative Scales**: Add helper function to detect if any negative values exist in the scale set for X or Y axes
2. **Appends Variance Indicator**: Modify scale text generation to append " (-)" to "VARIES" when negative values are detected
3. **Applies Priority-Based Highlighting**: Refactor the formatting logic to apply the highest-priority color based on:
   - **Priority 1 (Red)**: "VARIES (-)" - variance with negative values present
   - **Priority 2 (Orange)**: Single consistent negative number (e.g., -1.0)
   - **Priority 3 (Yellow)**: "VARIES" - variance with all positive values
   - **Priority 4 (None)**: No highlighting for consistent positive numeric values
4. **Adds Color Constants**: Define three new color constants for the highlighting system
5. **Maintains Row-Level Highlighting**: Apply highlighting across all 13 columns when either Scale X or Scale Y triggers a highlight condition

This approach provides immediate visual feedback about the nature and complexity of scale variations without requiring manual inspection.

## Relevant Files
Use these files to implement the feature:

**Excel Generation Logic**
- `app/core/excel_writer.py` (lines 378-388)
  - Contains scale variance detection and text generation logic
  - Need to add negative scale detection
  - Modify text generation to append " (-)" when negatives exist
  - Currently checks _has_x_scale_variance() and _has_y_scale_variance()
  - Add logic to detect negative scales in the variance set

**Excel Formatting Logic**
- `app/core/excel_formatting.py` (lines 154-221)
  - Contains _format_block_geometry_analysis_sheet() function
  - Currently applies yellow highlighting for "VARIES" (lines 186-206)
  - Need to refactor to support three-tier color system
  - Implement priority-based highlighting logic
  - Check for "VARIES (-)", single negative numbers, and "VARIES"

**Constants**
- `app/core/constants.py`
  - Need to add three color constants for Excel fill colors
  - EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE (yellow - FFFFFF00)
  - EXCEL_FILL_COLOR_SCALE_NEGATIVE (orange - FFA500FF)
  - EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE (red - FFFF0000)

**Type Definitions**
- `app/core/extractor.py` (lines 33-70)
  - No changes required to ExtractionResult TypedDict
  - block_scale_data already tracks (x_scale, y_scale) tuples which include negative values

### New Files
**Test Asset**
- `app/tests/assets/negative_scale_test.dxf`
  - Create test DXF with blocks demonstrating all three highlighting scenarios
  - Scenario 1 (Yellow): Block "VARY_POSITIVE" at scales {(1.0, 1.0), (2.0, 1.0)}
  - Scenario 2 (Orange): Block "MIRROR_CONSISTENT" at scale {(-1.0, 1.0)} across all insertions
  - Scenario 3 (Red): Block "VARY_NEGATIVE" at scales {(1.0, 1.0), (-1.0, 1.0)}
  - Scenario 4 (No highlight): Block "NORMAL" at scale {(1.0, 1.0)} across all insertions

## Implementation Plan

### Phase 1: Foundation
**Add Color Constants**
- Define three new Excel fill color constants in constants.py
- Use descriptive names following SCREAMING_SNAKE_CASE convention
- Document the purpose and color values (yellow, orange, red) in comments

**Create Test Asset**
- Generate negative_scale_test.dxf with ezdxf to cover all highlighting scenarios
- Include blocks with positive-only variance, consistent negative scales, and mixed variance
- Add creation script to assets folder for reproducibility

### Phase 2: Core Implementation
**Negative Scale Detection**
- Add helper function _has_negative_scale_in_set() to detect if any negative values exist in a scale set
- Takes scale_set and axis ('x' or 'y') as parameters
- Returns True if any negative values found for the specified axis
- Use this to determine if " (-)" should be appended to "VARIES"

**Scale Text Generation Enhancement**
- Modify _create_block_geometry_analysis_sheet() in excel_writer.py
- After determining if scale varies, check if negative values exist
- Append " (-)" to "VARIES" string when negative scales detected
- Keep numeric display unchanged for single consistent values (including negative)

### Phase 3: Integration
**Refactor Highlighting Logic**
- Replace single yellow highlighting logic in _format_block_geometry_analysis_sheet()
- Implement priority-based three-tier system
- For each row, determine highest priority highlight condition:
  1. Check for "VARIES (-)" pattern → apply red
  2. Check for single negative numeric value → apply orange
  3. Check for "VARIES" pattern → apply yellow
  4. Otherwise → no highlight
- Apply chosen fill to all 13 columns in the row

**Testing and Validation**
- Write comprehensive unit tests for all highlighting scenarios
- Verify priority system works correctly
- Ensure backward compatibility with existing yellow highlighting
- Test with real DWG/DXF files containing negative scales

## Step by Step Tasks

### Step 1: Add Color Constants
- Open app/core/constants.py
- Add three new constants at the end of the Excel configuration section:
  - `EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE: str = "FFFFFF00"` (yellow)
  - `EXCEL_FILL_COLOR_SCALE_NEGATIVE: str = "FFA500FF"` (orange)
  - `EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE: str = "FFFF0000"` (red)
- Add docstring comments explaining each color's purpose
- Verify naming follows SCREAMING_SNAKE_CASE convention

### Step 2: Create Test Asset Generator Script
- Create app/tests/assets/create_negative_scale_test.py
- Use ezdxf to generate negative_scale_test.dxf programmatically
- Add four blocks demonstrating all scenarios:
  - "VARY_POSITIVE": Insert at (1.0, 1.0) and (2.0, 1.0) - should show "VARIES" with yellow
  - "MIRROR_CONSISTENT": Insert at (-1.0, 1.0) three times - should show -1.0 with orange
  - "VARY_NEGATIVE": Insert at (1.0, 1.0) and (-1.0, 1.0) - should show "VARIES (-)" with red
  - "NORMAL": Insert at (1.0, 1.0) three times - should show 1.0 with no highlight
- Include comments documenting expected behavior
- Run script to generate the DXF file

### Step 3: Add Negative Scale Detection Helper
- Open app/core/excel_writer.py
- Add helper function after _get_single_scale_value() (around line 138):
  ```python
  def _has_negative_scale_in_set(scale_set: set[tuple[float, float]], axis: str) -> bool:
      """
      Check if a block has any negative scale values for the specified axis.

      Args:
          scale_set: Set of unique (x_scale, y_scale) tuples for a block
          axis: Either 'x' or 'y' to specify which axis to check

      Returns:
          True if any negative scale value exists for the specified axis, False otherwise

      Examples:
          >>> _has_negative_scale_in_set({(1.0, 1.0), (-1.0, 1.0)}, 'x')
          True
          >>> _has_negative_scale_in_set({(1.0, 1.0), (2.0, 1.0)}, 'x')
          False
          >>> _has_negative_scale_in_set({(1.0, -1.0), (1.0, -2.0)}, 'y')
          True
      """
  ```
- Implement logic to extract scales for the specified axis and check for negatives
- Add error handling for invalid axis parameter
- Add error handling for empty scale_set

### Step 4: Update Scale Text Generation
- Modify _create_block_geometry_analysis_sheet() in app/core/excel_writer.py (around lines 378-388)
- After variance detection, add negative scale detection
- Update X scale text generation:
  ```python
  if _has_x_scale_variance(scale_set):
      if _has_negative_scale_in_set(scale_set, 'x'):
          x_scale: str | float = "VARIES (-)"
      else:
          x_scale = "VARIES"
  else:
      x_scale = _get_single_scale_value(scale_set, 'x')
  ```
- Apply same logic for Y scale text generation
- Ensure the " (-)" suffix is only added when variance exists AND negatives are present
- Single consistent negative values (e.g., -1.0) should display as numeric without suffix

### Step 5: Import Color Constants in Formatting Module
- Open app/core/excel_formatting.py
- Add imports for new color constants:
  ```python
  from .constants import (
      # ... existing imports ...
      EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
      EXCEL_FILL_COLOR_SCALE_NEGATIVE,
      EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
  )
  ```

### Step 6: Refactor Highlighting Logic to Three-Tier System
- Locate _format_block_geometry_analysis_sheet() in app/core/excel_formatting.py
- Remove existing yellow highlighting logic (lines 186-206)
- Replace with priority-based three-tier system:
  - Define three PatternFill objects using new color constants
  - Iterate through data rows (skip header at row 1)
  - For each row, get scale values from columns H (x_scale) and I (y_scale)
  - Determine highlight priority based on both X and Y scale values:
    - Priority 1: If either contains "VARIES (-)" → use red fill
    - Priority 2: If either is a negative number → use orange fill
    - Priority 3: If either contains "VARIES" → use yellow fill
    - Priority 4: Otherwise → no fill
  - Apply selected fill to all 13 columns (A-M) if highlighting is needed
- Track count of rows highlighted by each color for logging
- Update logger message to report counts by color

### Step 7: Add Helper for Negative Number Detection
- Add helper function within _format_block_geometry_analysis_sheet() to check if a value is negative:
  ```python
  def _is_negative_number(value: str | float | int | None) -> bool:
      """Check if cell value is a negative number."""
      if value is None:
          return False
      if isinstance(value, (int, float)):
          return value < 0
      # String values like "VARIES" or "VARIES (-)" are not negative numbers
      return False
  ```
- Use this helper in the priority-based highlighting logic

### Step 8: Write Unit Tests for Negative Scale Detection Helper
- Open app/tests/core/test_excel_writer.py
- Add test class TestNegativeScaleDetection
- Test cases:
  - test_has_negative_scale_x_with_negatives(): Verify detection of negative X scales
  - test_has_negative_scale_x_without_negatives(): Verify returns False for all positive
  - test_has_negative_scale_y_with_negatives(): Verify detection of negative Y scales
  - test_has_negative_scale_y_without_negatives(): Verify returns False for all positive
  - test_has_negative_scale_mixed_values(): Test set with both positive and negative
  - test_has_negative_scale_empty_set(): Edge case with empty set
  - test_has_negative_scale_invalid_axis(): Verify error handling for invalid axis

### Step 9: Write Unit Tests for Scale Text Generation
- Add to test_excel_writer.py
- Test cases:
  - test_scale_text_varies_with_negatives(): Verify "VARIES (-)" when variance + negatives
  - test_scale_text_varies_without_negatives(): Verify "VARIES" when variance + all positive
  - test_scale_text_single_negative_value(): Verify -1.0 displayed as numeric
  - test_scale_text_single_positive_value(): Verify 1.0 displayed as numeric
  - test_scale_text_x_varies_negative_y_consistent(): Mixed scenario X varies with negatives, Y consistent
  - test_scale_text_both_vary_one_negative(): Both vary but only one has negatives
- Use sample block_scale_data with known scale sets
- Verify correct text appears in Excel DataFrame

### Step 10: Write Unit Tests for Three-Tier Highlighting
- Open app/tests/core/test_excel_formatting.py
- Add test class TestNegativeScaleHighlighting
- Test cases:
  - test_red_highlighting_varies_with_negatives(): Verify red fill for "VARIES (-)"
  - test_orange_highlighting_consistent_negative(): Verify orange fill for -1.0
  - test_yellow_highlighting_varies_positive(): Verify yellow fill for "VARIES"
  - test_no_highlighting_consistent_positive(): Verify no fill for 1.0
  - test_priority_red_over_orange(): Both conditions present, verify red wins
  - test_priority_red_over_yellow(): Both conditions present, verify red wins
  - test_priority_orange_over_yellow(): Both conditions present, verify orange wins
  - test_entire_row_highlighted(): Verify all 13 columns get the same fill
  - test_x_scale_triggers_highlight(): Only X scale has condition, verify row highlighted
  - test_y_scale_triggers_highlight(): Only Y scale has condition, verify row highlighted
- Create test workbooks with appropriate data
- Verify PatternFill objects have correct color codes
- Count highlighted rows by color

### Step 11: Integration Test with Test Asset
- Add integration test to test_excel_writer.py
- Load negative_scale_test.dxf using extract_blocks()
- Verify block_scale_data contains expected scale sets:
  - "VARY_POSITIVE": {(1.0, 1.0), (2.0, 1.0)}
  - "MIRROR_CONSISTENT": {(-1.0, 1.0)}
  - "VARY_NEGATIVE": {(1.0, 1.0), (-1.0, 1.0)}
  - "NORMAL": {(1.0, 1.0)}
- Generate Excel file using write_excel()
- Load workbook and verify highlighting:
  - "VARY_POSITIVE" row has yellow fill
  - "MIRROR_CONSISTENT" row has orange fill
  - "VARY_NEGATIVE" row has red fill
  - "NORMAL" row has no fill
- Verify scale text values:
  - "VARY_POSITIVE": X scale shows "VARIES"
  - "MIRROR_CONSISTENT": X scale shows -1.0
  - "VARY_NEGATIVE": X scale shows "VARIES (-)"
  - "NORMAL": X scale shows 1.0

### Step 12: Update Existing Tests
- Review all tests in test_excel_formatting.py
- Update tests that check for yellow highlighting to use new constant names
- Update test_format_geometry_analysis_yellow_highlighting_varies_x_scale() to import new constant
- Update test_format_geometry_analysis_yellow_highlighting_varies_y_scale() to import new constant
- Update any tests that manually create yellow_fill PatternFill objects
- Ensure backward compatibility: existing yellow highlighting for "VARIES" (positive only) still works

### Step 13: Type Checking and Code Quality
- Run mypy to verify type correctness:
  - Verify _has_negative_scale_in_set() has correct type hints
  - Verify x_scale and y_scale variables accept str | float
  - Verify PatternFill usage is type-safe
- Run ruff to check code style:
  - Verify new functions follow naming conventions
  - Verify imports are properly organized
  - Fix any linting issues
- Run ruff format to ensure consistent formatting

### Step 14: Manual Testing with Real Files
- Run the application with bash scripts/start.sh
- Test with the generated negative_scale_test.dxf
- Verify Excel output shows correct highlighting colors
- Test with real DWG/DXF files if available
- Verify backward compatibility with files that only have positive scales
- Open Excel file and visually confirm:
  - Yellow rows for "VARIES" (positive only)
  - Orange rows for consistent negative values
  - Red rows for "VARIES (-)" (mixed positive/negative)

### Step 15: Run Validation Commands
- Execute all validation commands listed below
- Fix any test failures or type errors
- Verify zero regressions in existing tests
- Confirm all new tests pass
- Verify test coverage meets or exceeds existing coverage

## Testing Strategy

### Unit Tests

**Excel Writer Tests (app/tests/core/test_excel_writer.py)**
- test_has_negative_scale_in_set_x_axis_with_negatives(): Verify negative X scale detection
- test_has_negative_scale_in_set_y_axis_with_negatives(): Verify negative Y scale detection
- test_has_negative_scale_in_set_all_positive(): Verify returns False for all positive
- test_has_negative_scale_in_set_mixed_signs(): Test with both positive and negative values
- test_has_negative_scale_in_set_empty_set(): Edge case with empty set
- test_has_negative_scale_in_set_invalid_axis(): Verify error for invalid axis parameter
- test_scale_text_generation_varies_negative(): Verify "VARIES (-)" appended correctly
- test_scale_text_generation_varies_positive(): Verify "VARIES" without suffix
- test_scale_text_generation_single_negative(): Verify -1.0 displayed as number
- test_scale_text_generation_mixed_axes(): Test X varies with negatives, Y consistent positive

**Excel Formatting Tests (app/tests/core/test_excel_formatting.py)**
- test_three_tier_highlighting_red_priority(): Verify "VARIES (-)" gets red fill
- test_three_tier_highlighting_orange_priority(): Verify -1.0 gets orange fill
- test_three_tier_highlighting_yellow_priority(): Verify "VARIES" gets yellow fill
- test_three_tier_highlighting_no_highlight(): Verify 1.0 gets no fill
- test_three_tier_highlighting_priority_order(): Test priority resolution when multiple conditions exist
- test_three_tier_highlighting_entire_row(): Verify all 13 columns highlighted
- test_three_tier_highlighting_x_scale_triggers(): Only X scale has condition
- test_three_tier_highlighting_y_scale_triggers(): Only Y scale has condition
- test_three_tier_highlighting_counts_by_color(): Verify logging counts match actual highlights
- test_is_negative_number_helper(): Test the negative number detection helper function

### Integration Tests

**End-to-End with Test Asset**
- test_negative_scale_test_dxf_extraction(): Extract data from negative_scale_test.dxf
- test_negative_scale_test_dxf_excel_generation(): Generate Excel from test asset
- test_negative_scale_test_dxf_highlighting_verification(): Verify all four scenarios highlighted correctly
- test_negative_scale_test_dxf_text_verification(): Verify scale text matches expected values
- test_backward_compatibility_existing_files(): Test with existing test assets to ensure no regression

### Edge Cases

**Scale Value Edge Cases**
- Zero scales (0.0) - should be treated as positive (no highlighting for consistent zero)
- Very small negative scales (-0.001) - should trigger orange/red highlighting
- Mixed zero and negative (-0.0 vs 0.0) - floating point comparison
- Large negative scales (-100.0) - should be detected correctly
- Empty scale data (no block insertions) - should not crash

**Text Generation Edge Cases**
- Single scale tuple in set - no variance, display numeric value
- Empty scale set - handle gracefully (shouldn't occur in practice)
- Scale set with only negative values {(-1.0, -1.0), (-2.0, -1.0)} - should show "VARIES (-)"
- All insertions at exactly -1.0 - should show -1.0 with orange highlight

**Highlighting Edge Cases**
- Empty worksheet (headers only) - should not crash
- Very large worksheet (1000+ rows) - performance check
- Mixed highlighting rows (some red, some orange, some yellow) - verify correct colors
- Rows with "VARIES (-)" in one axis and numeric in other - should still highlight entire row
- Header row should never be highlighted (only data rows)

**Priority System Edge Cases**
- Both X and Y have "VARIES (-)" - should use red (highest priority)
- X has -1.0 (orange) and Y has "VARIES" (yellow) - should use orange (higher priority)
- X has "VARIES (-)" (red) and Y has -1.0 (orange) - should use red (highest priority)
- Both axes consistent positive - should have no highlighting

### Playwright MCP Tests
This feature does not require E2E Playwright tests as it involves:
- Backend scale text generation logic (covered by unit tests)
- Excel formatting and highlighting logic (covered by integration tests)
- No GUI interaction in the main application

Manual verification recommended:
1. Run application with negative_scale_test.dxf
2. Open generated Excel file
3. Visually verify three different highlight colors (yellow, orange, red)
4. Verify scale text displays correctly ("VARIES", "VARIES (-)", numeric values)
5. Verify highlighting spans entire rows (all 13 columns)

## Acceptance Criteria

1. **Color Constants**
   - [ ] Three new color constants added to constants.py with descriptive names
   - [ ] Color values correctly defined (yellow: FFFFFF00, orange: FFA500FF, red: FFFF0000)
   - [ ] Constants follow SCREAMING_SNAKE_CASE convention
   - [ ] Docstring comments explain each color's purpose

2. **Negative Scale Detection**
   - [ ] Helper function _has_negative_scale_in_set() correctly detects negative X scales
   - [ ] Helper function correctly detects negative Y scales
   - [ ] Helper handles empty scale sets gracefully
   - [ ] Helper validates axis parameter and raises error for invalid values
   - [ ] Detection works for mixed positive/negative scale sets

3. **Scale Text Generation**
   - [ ] "VARIES (-)" appended when variance exists AND negative values present
   - [ ] "VARIES" displayed when variance exists with all positive values
   - [ ] Numeric values displayed when scales are consistent (both positive and negative)
   - [ ] Single consistent negative value (e.g., -1.0) displays as numeric without suffix
   - [ ] Text generation works independently for X and Y axes

4. **Three-Tier Highlighting System**
   - [ ] Red fill (FFFF0000) applied to rows with "VARIES (-)" in either scale column
   - [ ] Orange fill (FFA500FF) applied to rows with single consistent negative values
   - [ ] Yellow fill (FFFFFF00) applied to rows with "VARIES" (positive only)
   - [ ] No fill applied to rows with consistent positive numeric values
   - [ ] Priority system correctly resolves when multiple conditions exist (red > orange > yellow)
   - [ ] Entire row (columns A-M) highlighted when condition triggered by either X or Y scale
   - [ ] Header row (row 1) never highlighted
   - [ ] Highlighting counts logged correctly by color

5. **Test Coverage**
   - [ ] Test asset negative_scale_test.dxf created with all four scenarios
   - [ ] Unit tests cover all helper functions (_has_negative_scale_in_set, _is_negative_number)
   - [ ] Unit tests cover all scale text generation scenarios
   - [ ] Unit tests cover all three-tier highlighting scenarios
   - [ ] Integration test verifies end-to-end flow with test asset
   - [ ] Edge cases tested (empty sets, zero scales, priority resolution)
   - [ ] All existing tests pass with zero regressions

6. **Code Quality**
   - [ ] Type hints accurate for all new functions
   - [ ] Docstrings provided with examples for all new functions
   - [ ] Functions follow snake_case naming convention
   - [ ] Helper functions marked as private with underscore prefix
   - [ ] No code duplication in highlighting logic
   - [ ] Error handling for edge cases (empty sets, invalid parameters)
   - [ ] mypy passes with no type errors
   - [ ] ruff passes with no style violations

7. **Backward Compatibility**
   - [ ] Existing yellow highlighting for "VARIES" (positive only) still works
   - [ ] Existing test files with positive-only variance display correctly
   - [ ] No breaking changes to ExtractionResult TypedDict
   - [ ] Block Geometry Analysis sheet structure unchanged (13 columns)
   - [ ] Existing tests updated to use new color constants where appropriate

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run python app/tests/assets/create_negative_scale_test.py` - Generate test asset DXF file
- `uv run pytest app/tests/core/test_excel_writer.py::TestNegativeScaleDetection -v` - Test negative scale detection helper
- `uv run pytest app/tests/core/test_excel_formatting.py::TestNegativeScaleHighlighting -v` - Test three-tier highlighting
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate all Excel writer tests
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Validate all formatting tests
- `uv run pytest app/tests/ -v` - Run complete test suite
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify test coverage
- `uv run mypy app/` - Validate type correctness
- `uv run ruff check app/` - Ensure code style compliance
- `uv run ruff format app/` - Format code consistently
- `bash scripts/start.sh` - Manual test: Load negative_scale_test.dxf and verify Excel output

## Notes

**Design Decisions**

1. **Three-Tier vs More Tiers**: Limiting to three highlight colors (yellow, orange, red) plus no-highlight provides sufficient granularity without overwhelming users with too many color codes.

2. **Orange for Consistent Mirroring**: Orange is a middle-ground color between yellow (warning) and red (critical). Consistent mirroring at -1.0 is often intentional design choice, so it warrants highlighting but not the urgent red color.

3. **" (-)" Suffix**: Appending " (-)" to "VARIES" clearly indicates that the variance includes negative values without changing the fundamental "VARIES" pattern users are familiar with.

4. **Priority-Based System**: Using priority order (red > orange > yellow) ensures that the most critical condition is always displayed when a row has multiple highlighting conditions.

5. **Row-Level Highlighting**: Highlighting entire rows (all 13 columns) rather than just scale columns provides better visual scanning and makes it easier to identify problematic blocks.

**Implementation Notes**

- The _has_negative_scale_in_set() helper extracts scales for the specified axis and uses the `any()` function to check for negatives, making it efficient and readable
- The _is_negative_number() helper handles both numeric types and string types, preventing false positives on "VARIES" strings
- Consider floating-point precision when comparing to zero (values like -0.0000001 should be treated as negative)
- Use consistent color constant naming to make the code self-documenting
- Keep helper functions private (underscore prefix) as they're internal implementation details

**Color Choices Rationale**

- **Yellow (FFFFFF00)**: Warning color, indicates attention needed but not critical (variance with all positive values)
- **Orange (FFA500FF)**: Moderate alert, indicates intentional design choice that should be reviewed (consistent mirroring)
- **Red (FFFF0000)**: High priority alert, indicates complex variance with mixed signs (potential design issue)

**Future Enhancements**

- Add configuration option to customize highlight colors
- Add legend/key in Excel sheet explaining color meanings
- Add filter buttons to show only rows with specific highlight colors
- Add column showing scale range (e.g., "-1.0 to 2.0") for variance scenarios
- Support for Z-axis scale variance detection and highlighting
- Add summary count of blocks by highlighting category

**Performance Considerations**

- Negative detection is O(n) where n is the number of unique scales per block (typically 1-5)
- Three-tier highlighting adds minimal overhead as it's a single pass through data rows
- No performance impact expected for large files (1000+ rows)
- PatternFill objects created once and reused across rows

**Breaking Changes**

None - this is an enhancement that extends the existing yellow highlighting system. The Block Geometry Analysis sheet structure and data remain unchanged.

**Migration Notes**

No migration required. Existing Excel files generated with the old system will continue to work. New files will automatically include the enhanced three-tier highlighting.

**Testing Asset Design**

The negative_scale_test.dxf includes four distinct blocks to test all scenarios:
1. **VARY_POSITIVE**: Multiple positive scales → Yellow highlight, "VARIES" text
2. **MIRROR_CONSISTENT**: Consistent negative scale → Orange highlight, -1.0 numeric
3. **VARY_NEGATIVE**: Mixed positive/negative scales → Red highlight, "VARIES (-)" text
4. **NORMAL**: Consistent positive scale → No highlight, 1.0 numeric

This comprehensive test asset enables automated verification of all highlighting paths.
