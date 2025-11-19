# Feature: Consolidate Geometry Sheet with X/Y Scale Columns and Mirrored Block Highlighting

## Feature Description
Redesign the Excel output to consolidate all geometric data into a single "Block Geometry Analysis" sheet while maintaining a simplified "Block Analysis" sheet for inventory counting. Add X and Y scale columns to track block transformations, and implement red row highlighting for blocks with negative scales (mirrored blocks). This reorganization provides clearer separation between inventory analysis and geometric/transformation properties.

The feature transforms the current 4-sheet structure where rotation, trimming, and dimension data are spread across sheets into a more logical structure:
- Sheet 1 "Block Analysis": Simplified to core metrics (block_name, block_insertion_count, block_entity_count, block_layer_name)
- Sheet 2 "Block Geometry Analysis": All geometry data (rotations, scales, dimensions, segments) - renamed from "Block Trimming Analysis"
- Sheet 3 "Layer Analysis": Unchanged (layer stats)
- Sheet 4 "Entity Summary": Unchanged (entity type counts)

### ASCII Mockups

**Sheet 1: "Block Analysis" (simplified - counts only)**

```
┌──────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Block Name       │ Insertion Count │ Entity Count    │ Layer Name      │
├──────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ DESK-STD         │ 45              │ 12              │ FURN            │
│ CHAIR-OFF        │ 38              │ 8               │ FURN            │
│ DOOR-SINGLE      │ 12              │ 6               │ DOORS           │
│ DOOR-SINGLE      │ 8               │ 6               │ WALLS           │
│ WINDOW-DBL       │ 8               │ 4               │ WINDOWS         │
│ TABLE-CONF       │ 3               │ 15              │ FURN            │
└──────────────────┴─────────────────┴─────────────────┴─────────────────┘

Focus: Inventory and counting
Use case: "How many of each block are inserted?"
Sorted by: Insertion count (descending)
```

**Sheet 2: "Block Geometry Analysis" (consolidated geometry)**

```
┌────────────┬─────────┬────┬────┬─────┬─────┬───────┬──────┬──────┬───────┬────────┬──────────┬────────────┐
│ Block Name │ Layer   │ 0° │ 90°│ 180°│ 270°│ Other │ X    │ Y    │ Width │ Height │ Vertical │ Horizontal │
│            │         │    │    │     │     │       │ Scale│ Scale│       │        │ Segments │ Segments   │
├────────────┼─────────┼────┼────┼─────┼─────┼───────┼──────┼──────┼───────┼────────┼──────────┼────────────┤
│ CHAIR-OFF  │ FURN    │ 38 │ 0  │ 0   │ 0   │ 0     │ 1.0  │ 1.0  │ 24    │ 18     │ 6,12,18  │ 9          │
│ DESK-STD   │ FURN    │ 30 │ 10 │ 5   │ 0   │ 0     │ 1.0  │ 1.0  │ 60    │ 30     │ 15,30,45 │ 10,20      │
│ DOOR-SINGLE│ DOORS   │ 6  │ 6  │ 0   │ 0   │ 0     │ -1.0 │ 1.0  │ 36    │ 84     │ 18,36,54 │ 21,42,63   │ ◄ RED
│ DOOR-SINGLE│ WALLS   │ 4  │ 4  │ 0   │ 0   │ 0     │ 1.0  │ 1.0  │ 36    │ 84     │ 18,36,54 │ 21,42,63   │
│ WINDOW-DBL │ WINDOWS │ 4  │ 4  │ 0   │ 0   │ 0     │ 1.0  │ -1.0 │ 48    │ 36     │ 12,24,36 │ 18         │ ◄ RED
│ TABLE-CONF │ FURN    │ 2  │ 1  │ 0   │ 0   │ 0     │ -1.0 │ -1.0 │ 96    │ 48     │ 24,48,72 │ 16,32      │ ◄ RED
└────────────┴─────────┴────┴────┴─────┴─────┴───────┴──────┴──────┴───────┴────────┴──────────┴────────────┘
                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                        TRANSFORMATIONS + PHYSICAL GEOMETRY COMBINED

Focus: All geometric properties (transformations + dimensions)
Use case: "Show geometry for mirrored blocks" or "Find blocks with specific dimensions"
Sorted by: Block name (alphabetical)
Red rows: Any scale < 0 (mirrored blocks)
```

**Sheet 3: "Layer Analysis" (unchanged)**

```
┌─────────────────┬───────────────────────┬─────────────────┐
│ Layer Name      │ Block Insertion Count │ Entity Count    │
├─────────────────┼───────────────────────┼─────────────────┤
│ FURN            │ 86                    │ 245             │
│ WALLS           │ 165                   │ 892             │
│ DOORS           │ 12                    │ 72              │
└─────────────────┴───────────────────────┴─────────────────┘

Focus: Layer-level statistics
Use case: "Which layers have the most content?"
Sorted by: Entity count (descending)
```

**Sheet 4: "Entity Summary" (unchanged)**

```
┌──────────────────┬─────────┐
│ Entity Type      │ Count   │
├──────────────────┼─────────┤
│ LINE             │ 1245    │
│ LWPOLYLINE       │ 856     │
│ INSERT           │ 103     │
└──────────────────┴─────────┘

Focus: Global entity distribution
Use case: "What types of CAD entities are in this drawing?"
Sorted by: Count (descending)
```

## User Story
As a CAD analyst reviewing block transformations
I want to see all geometric properties (rotations, scales, dimensions, segments) on a single sheet with visual highlighting for mirrored blocks
So that I can quickly identify transformation patterns and mirrored blocks without switching between multiple sheets

## Problem Statement
The current Excel structure spreads geometric data across multiple sheets:
- "Block Counts" sheet contains rotations alongside inventory counts (mixed concerns)
- "Block Trimming Analysis" sheet contains only dimensions/segments (incomplete geometric view)
- No scale information is captured, making it impossible to identify mirrored or scaled blocks
- Users must cross-reference multiple sheets to understand a block's complete geometric properties
- Mirrored blocks (negative scales) have no visual indication, making them hard to spot

## Solution Statement
Reorganize the Excel output into two focused sheets for block data:

1. **Sheet 1 "Block Analysis"** (simplified inventory):
   - Contains only: block_name, block_insertion_count, block_entity_count, block_layer_name
   - Sorted by block_insertion_count (descending) for quick inventory assessment
   - Use case: "How many of each block are inserted?"

2. **Sheet 2 "Block Geometry Analysis"** (consolidated transformations + geometry):
   - Contains: block_name, block_layer_name, all 5 rotation columns, block_scale_x, block_scale_y, native dimensions, segments
   - Sorted by block_name (alphabetical) for easy lookup
   - Red row highlighting for any block-layer pair with negative X or Y scale
   - Use case: "Show me all geometric properties and transformations for blocks"

This approach:
- Separates concerns: inventory counting vs. geometric analysis
- Consolidates all transformation data (rotations + scales) with physical geometry (dimensions + segments)
- Provides visual feedback for mirrored blocks via red highlighting
- Maintains existing Layer Analysis and Entity Summary sheets unchanged

## Relevant Files
Use these files to implement the feature:

- **app/core/excel_writer.py** (lines 1-365): Main Excel generation module
  - Contains all sheet creation and formatting functions
  - `_create_block_counts_sheet()`: Currently creates Sheet 1 with 9 columns including rotations - needs to be simplified to 4 columns
  - `_create_block_trimming_analysis_sheet()`: Currently creates Sheet 4 with dimensions/segments - needs to be renamed and expanded
  - `_format_block_counts_sheet()`: Format function for Sheet 1 - needs updated column widths
  - `_format_block_trimming_analysis_sheet()`: Format function for Sheet 4 - needs red highlighting logic added
  - All column constants imported from constants.py

- **app/core/extractor.py** (lines 1-466): CAD extraction logic
  - `ExtractionResult` TypedDict (lines 275-307): Needs new fields for scale data
  - `extract_blocks()` function (lines 309-465): Main extraction function
  - Currently extracts rotation data (line 427-431) but not scale data
  - Block insertion loop (lines 417-431): Needs to capture X and Y scale from INSERT entities
  - Already provides `block_rotation_counts` and `block_trimming_data` dictionaries

- **app/core/constants.py** (lines 1-64): Application constants
  - Sheet name constants (lines 16-20): Need to rename EXCEL_SHEET_BLOCK_COUNTS to EXCEL_SHEET_BLOCK_ANALYSIS (value: 'Block Analysis') and EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS to EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS (value: 'Block Geometry Analysis')
  - Column constants (lines 22-55): Need to add EXCEL_COLUMN_BLOCK_SCALE_X and EXCEL_COLUMN_BLOCK_SCALE_Y
  - These constants are used throughout excel_writer.py for consistency

- **app_docs/005-field-naming-convention.md**: Field naming guidelines
  - Defines the {domain}_{attribute}[_{qualifier}] pattern
  - Scale fields should follow: block_scale_x and block_scale_y (domain=block, attribute=scale, qualifier=x/y)
  - Ensures consistency with existing naming conventions

### New Files
None required - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation - Data Collection
Add scale extraction to the CAD parsing logic:
- Modify `ExtractionResult` TypedDict to include `block_scale_data` dictionary
- Extract X and Y scale factors from INSERT entities in `extract_blocks()`
- Store scale data as `{(block_name, layer_name): (x_scale, y_scale)}` dictionary
- Use ezdxf's `entity.dxf.xscale` and `entity.dxf.yscale` attributes

### Phase 2: Core Implementation - Excel Structure
Redesign the Excel sheet creation functions:
1. Simplify Sheet 1 "Block Analysis" to 4 columns (remove rotations)
2. Rename and expand Sheet 4 to "Block Geometry Analysis" with 13 columns
3. Add scale column constants to constants.py
4. Update sheet name constant for geometry sheet
5. Modify column width formatting for both sheets

### Phase 3: Integration - Visual Highlighting
Add conditional formatting for mirrored blocks:
- Implement red background highlighting in `_format_block_trimming_analysis_sheet()` (rename to `_format_block_geometry_analysis_sheet()`)
- Apply red fill to entire row if X scale < 0 OR Y scale < 0
- Use openpyxl's PatternFill with color 'FFFF0000' (red) and fill_type 'solid'
- Iterate through data rows (skip header) and check scale column values

## Step by Step Tasks

### Step 1: Update Sheet Name Constants and Add Scale Column Constants
- Rename `EXCEL_SHEET_BLOCK_COUNTS` to `EXCEL_SHEET_BLOCK_ANALYSIS` with value 'Block Analysis' in constants.py
- Rename `EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS` to `EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS` with value 'Block Geometry Analysis' in constants.py
- Add `EXCEL_COLUMN_BLOCK_SCALE_X: str = 'block_scale_x'` to constants.py
- Add `EXCEL_COLUMN_BLOCK_SCALE_Y: str = 'block_scale_y'` to constants.py
- Follow field naming convention: block (domain), scale (attribute), x/y (qualifier)
- Update docstring to reflect new sheet names

### Step 2: Update ExtractionResult TypedDict
- Add `block_scale_data: dict[tuple[str, str], tuple[float, float]]` to ExtractionResult in extractor.py
- Key format: `(block_name, layer_name)`, Value format: `(x_scale, y_scale)`
- Document in TypedDict docstring with example: `{('DOOR', 'WALLS'): (1.0, 1.0), ('WINDOW', 'WALLS'): (-1.0, 1.0)}`
- This matches the existing block_layer_pairs structure for consistency

### Step 3: Extract Scale Data from INSERT Entities
- In `extract_blocks()`, initialize `block_scale_data: dict[tuple[str, str], tuple[float, float]] = {}` (around line 373)
- In the INSERT entity processing loop (around line 418-431), capture scale factors:
  - Extract `x_scale = entity.dxf.xscale` and `y_scale = entity.dxf.yscale`
  - Store as `block_scale_data[(block_name, layer_name)] = (x_scale, y_scale)`
  - Handle missing scale attributes with default (1.0, 1.0)
- Add `block_scale_data` to the returned ExtractionResult dictionary
- Write unit test `test_extract_blocks_with_scales()` in test_extractor.py
- Test case should verify scale extraction for positive, negative, and default values

### Step 4: Simplify Block Analysis Sheet (Sheet 1)
- Modify `_create_block_counts_sheet()` to remove all 5 rotation columns (0°, 90°, 180°, 270°, Other)
- Update sheet_name parameter from EXCEL_SHEET_BLOCK_COUNTS to EXCEL_SHEET_BLOCK_ANALYSIS
- Keep only 4 columns: block_name, block_insertion_count, block_entity_count, block_layer_name
- Update empty DataFrame creation to match 4 columns
- Remove rotation data lookups from the row building loop
- Keep block_insertion_count descending sort
- Update function docstring to reflect "simplified inventory sheet"

### Step 5: Update Block Analysis Sheet Formatting
- Modify `_format_block_counts_sheet()` to remove rotation column width settings (lines 250-254)
- Update sheet reference from EXCEL_SHEET_BLOCK_COUNTS to EXCEL_SHEET_BLOCK_ANALYSIS
- Keep only column widths for A-D (block_name, block_insertion_count, block_entity_count, block_layer_name)
- Set widths: A=30, B=25, C=25, D=25
- Update function docstring

### Step 6: Create Consolidated Block Geometry Analysis Sheet
- Rename `_create_block_trimming_analysis_sheet()` to `_create_block_geometry_analysis_sheet()`
- Change sheet_name parameter from EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS to EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
- Restructure to create 13 columns in this order:
  1. block_name
  2. block_layer_name
  3. block_rotation_0
  4. block_rotation_90
  5. block_rotation_180
  6. block_rotation_270
  7. block_rotation_other
  8. block_scale_x
  9. block_scale_y
  10. block_native_width
  11. block_native_height
  12. block_vertical_segments
  13. block_horizontal_segments
- Extract scale data: `x_scale, y_scale = data['block_scale_data'].get((block_name, layer_name), (1.0, 1.0))`
- Add rotation counts to each row (move from old Block Counts sheet)
- Sort by block_name alphabetically (ascending)
- Update empty DataFrame column list to include all 13 columns
- Update function docstring to describe consolidated geometry sheet

### Step 7: Format Block Geometry Analysis Sheet with Column Widths
- Rename `_format_block_trimming_analysis_sheet()` to `_format_block_geometry_analysis_sheet()`
- Update sheet reference from EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS to EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
- Set column widths for 13 columns:
  - A (block_name): 30
  - B (block_layer_name): 25
  - C-G (block_rotation_0/90/180/270/other): 12 each
  - H (block_scale_x): 15
  - I (block_scale_y): 15
  - J (block_native_width): 20
  - K (block_native_height): 20
  - L (block_vertical_segments): 40
  - M (block_horizontal_segments): 40
- Update function docstring

### Step 8: Implement Red Highlighting for Mirrored Blocks
- In `_format_block_geometry_analysis_sheet()`, import PatternFill from openpyxl.styles
- After setting column widths, add red highlighting logic:
  - Create red fill: `red_fill = PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')`
  - Iterate through data rows starting at row 2 (skip header)
  - For each row, check cells in columns H (x_scale) and I (y_scale)
  - If `cell.value < 0` for either scale column, apply red_fill to entire row (columns A-M)
  - Use `ws.cell(row=row_idx, column=col_idx).fill = red_fill`
- Handle empty cells and None values safely
- Add logging: "Applied red highlighting to N rows with negative scales"

### Step 9: Update Excel Writer Main Function
- In `write_excel()`, update comment on line 107 from "Sheet 4: Block Trimming Analysis" to "Sheet 4: Block Geometry Analysis"
- Update function call on line 108 from `_create_block_trimming_analysis_sheet()` to `_create_block_geometry_analysis_sheet()`
- Update formatting call on line 117 from `_format_block_trimming_analysis_sheet()` to `_format_block_geometry_analysis_sheet()`
- Update docstring to reflect new sheet structure: "Block Analysis, Block Geometry Analysis, Layer Analysis, Entity Summary"

### Step 10: Update Import Statements
- In excel_writer.py, update imports from constants.py to include:
  - EXCEL_SHEET_BLOCK_ANALYSIS (renamed from EXCEL_SHEET_BLOCK_COUNTS)
  - EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS (renamed from EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)
  - EXCEL_COLUMN_BLOCK_SCALE_X (new)
  - EXCEL_COLUMN_BLOCK_SCALE_Y (new)
- Remove imports of old constants: EXCEL_SHEET_BLOCK_COUNTS and EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS
- Add PatternFill import: `from openpyxl.styles import PatternFill`

### Step 11: Write Unit Tests for Scale Extraction
- Create test in app/tests/core/test_extractor.py: `test_extract_blocks_with_scales()`
- Test positive scales (1.0, 1.5)
- Test negative scales (-1.0, -1.0) for mirrored blocks
- Test mixed scales (-1.0, 1.0) for single-axis mirrors
- Test default scales when xscale/yscale attributes are missing
- Verify block_scale_data dictionary structure and values
- Run: `uv run pytest app/tests/core/test_extractor.py::test_extract_blocks_with_scales -v`

### Step 12: Write Unit Tests for Simplified Block Analysis Sheet
- Create test in app/tests/core/test_excel_writer.py: `test_block_analysis_sheet_simplified()`
- Verify Sheet 1 has exactly 4 columns: block_name, block_insertion_count, block_entity_count, block_layer_name
- Verify no rotation columns present
- Verify sort order is block_insertion_count descending
- Run: `uv run pytest app/tests/core/test_excel_writer.py::test_block_analysis_sheet_simplified -v`

### Step 13: Write Unit Tests for Consolidated Geometry Sheet
- Create test in app/tests/core/test_excel_writer.py: `test_block_geometry_analysis_sheet_consolidated()`
- Verify Sheet 2 name is "Block Geometry Analysis"
- Verify all 13 columns present in correct order
- Verify rotation data is included
- Verify scale data (X and Y) is included
- Verify dimension and segment data is included
- Verify sort order is block_name alphabetical
- Run: `uv run pytest app/tests/core/test_excel_writer.py::test_block_geometry_analysis_sheet_consolidated -v`

### Step 14: Write Unit Tests for Red Highlighting
- Create test in app/tests/core/test_excel_writer.py: `test_geometry_sheet_red_highlighting()`
- Create mock extraction data with:
  - Block with negative X scale (-1.0, 1.0)
  - Block with negative Y scale (1.0, -1.0)
  - Block with both negative (-1.0, -1.0)
  - Block with positive scales (1.0, 1.0)
- Generate Excel file and load with openpyxl
- Verify rows with negative scales have red fill (PatternFill with 'FFFF0000')
- Verify rows with positive scales have no fill
- Run: `uv run pytest app/tests/core/test_excel_writer.py::test_geometry_sheet_red_highlighting -v`

### Step 15: Run All Validation Commands
- Execute all validation commands listed in the "Validation Commands" section
- Verify zero test failures
- Verify zero type errors
- Verify zero regressions in existing functionality
- Verify Excel output matches ASCII mockups from feature description
- Test with real DWG files to ensure scales are extracted correctly

## Testing Strategy

### Unit Tests

**Extractor Tests (test_extractor.py):**
- `test_extract_blocks_with_scales()`: Verify scale extraction from INSERT entities
  - Test positive scales (standard blocks)
  - Test negative X scale (X-axis mirror)
  - Test negative Y scale (Y-axis mirror)
  - Test both negative (180° mirror)
  - Test default values (1.0, 1.0) when scale attributes missing
  - Verify block_scale_data dictionary structure matches `{(block_name, layer_name): (x_scale, y_scale)}`

**Excel Writer Tests (test_excel_writer.py):**
- `test_block_analysis_sheet_simplified()`: Verify Sheet 1 has only 4 inventory columns
  - Assert columns: block_name, block_insertion_count, block_entity_count, block_layer_name
  - Assert no rotation columns
  - Assert sort by block_insertion_count descending

- `test_block_geometry_analysis_sheet_consolidated()`: Verify Sheet 2 consolidation
  - Assert sheet name is "Block Geometry Analysis"
  - Assert 13 columns in correct order
  - Assert rotation columns included (5 columns)
  - Assert scale columns included (2 columns)
  - Assert dimension columns included (2 columns)
  - Assert segment columns included (2 columns)
  - Assert sort by block_name alphabetical

- `test_geometry_sheet_red_highlighting()`: Verify visual highlighting
  - Create blocks with various scale combinations
  - Assert rows with X scale < 0 have red fill
  - Assert rows with Y scale < 0 have red fill
  - Assert rows with both scales < 0 have red fill
  - Assert rows with positive scales have no fill
  - Verify fill color is 'FFFF0000' (red)

### Integration Tests

**End-to-End Excel Generation:**
- Test with real DWG file containing mirrored blocks
- Verify Sheet 1 "Block Analysis" contains only inventory data
- Verify Sheet 2 "Block Geometry Analysis" contains all geometric properties
- Verify Sheets 3 and 4 remain unchanged
- Manually inspect Excel file to confirm red highlighting appears correctly
- Test with empty drawings (verify empty DataFrames with headers)
- Test with drawings containing no mirrored blocks (verify no red highlighting)

### Edge Cases

1. **Missing Scale Attributes:**
   - Some INSERT entities may not have xscale/yscale attributes
   - Handle with try/except and default to (1.0, 1.0)
   - Test with legacy DWG files

2. **Zero Scales:**
   - Blocks with zero scale should not crash highlighting logic
   - Treat zero as non-negative (no red highlighting)
   - Test scale = 0.0 scenarios

3. **Anonymous Blocks:**
   - Anonymous blocks (names starting with '*') are already filtered in extractor
   - Verify they don't appear in geometry sheet
   - No scale data collected for anonymous blocks

4. **Empty Drawings:**
   - Verify empty DataFrames create correctly with all 13 columns
   - Verify no errors when highlighting logic runs on empty sheet
   - No red highlighting applied (no data rows)

5. **Large Scale Factors:**
   - Test blocks with very large positive scales (e.g., 100.0)
   - Test blocks with very small negative scales (e.g., -0.01)
   - Ensure highlighting works for all negative values regardless of magnitude

### Playwright MCP Tests

Not applicable for this feature - Excel file generation is tested via unit and integration tests. The feature does not involve GUI changes or user interaction flows that require end-to-end browser testing.

## Acceptance Criteria

1. **Scale Data Extraction:**
   - [ ] X and Y scale factors are extracted from all INSERT entities
   - [ ] Scale data is stored as `{(block_name, layer_name): (x_scale, y_scale)}` dictionary
   - [ ] Missing scale attributes default to (1.0, 1.0)
   - [ ] All scale data is included in ExtractionResult

2. **Sheet 1 "Block Analysis" Simplification:**
   - [ ] Contains exactly 4 columns: block_name, block_insertion_count, block_entity_count, block_layer_name
   - [ ] No rotation columns present
   - [ ] Sorted by block_insertion_count descending
   - [ ] Auto-filter enabled on all columns
   - [ ] Column widths set appropriately (30, 25, 25, 25)

3. **Sheet 2 "Block Geometry Analysis" Consolidation:**
   - [ ] Sheet renamed from "Block Trimming Analysis" to "Block Geometry Analysis"
   - [ ] Contains all 13 columns in correct order
   - [ ] Rotation data (5 columns) included for each block-layer pair
   - [ ] Scale data (2 columns) included: block_scale_x, block_scale_y
   - [ ] Dimension data (2 columns) included: block_native_width, block_native_height
   - [ ] Segment data (2 columns) included: block_vertical_segments, block_horizontal_segments
   - [ ] Sorted by block_name alphabetically
   - [ ] Auto-filter enabled on all columns
   - [ ] Column widths set appropriately for all 13 columns

4. **Red Highlighting for Mirrored Blocks:**
   - [ ] Entire row highlighted red if X scale < 0
   - [ ] Entire row highlighted red if Y scale < 0
   - [ ] Entire row highlighted red if both scales < 0
   - [ ] No highlighting for rows with positive scales
   - [ ] Red color is 'FFFF0000' (solid red)
   - [ ] Highlighting applies to all 13 columns in the row

5. **Sheets 3 and 4 Unchanged:**
   - [ ] "Layer Analysis" sheet structure and data unchanged
   - [ ] "Entity Summary" sheet structure and data unchanged

6. **Constants and Naming:**
   - [ ] New constants follow field naming convention (block_scale_x, block_scale_y)
   - [ ] Sheet name constant EXCEL_SHEET_BLOCK_COUNTS renamed to EXCEL_SHEET_BLOCK_ANALYSIS
   - [ ] Sheet name constant EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS renamed to EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
   - [ ] All constants defined in constants.py
   - [ ] All imports updated in excel_writer.py

7. **Testing:**
   - [ ] All unit tests pass
   - [ ] Scale extraction tested with positive, negative, and default values
   - [ ] Sheet structure tests verify column counts and order
   - [ ] Red highlighting tests verify correct application
   - [ ] Integration tests with real DWG files succeed
   - [ ] Zero regressions in existing functionality

8. **Code Quality:**
   - [ ] Type hints correct for all new/modified functions
   - [ ] Docstrings updated to reflect changes
   - [ ] Logging statements added for scale extraction and highlighting
   - [ ] No mypy errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Verify scale extraction logic works correctly
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Verify all Excel sheet changes work correctly
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run pytest --cov=app/core app/tests/core/ --cov-report=term-missing` - Verify code coverage for core modules
- `uv run mypy app/` - Verify type checking passes with no errors
- `bash scripts/start.sh` - Launch application and test with real DWG file containing mirrored blocks, verify Excel output matches specifications

## Notes

**Scale Extraction Implementation Details:**
- ezdxf INSERT entities have `xscale` and `yscale` attributes that represent scale factors
- Positive scales indicate normal orientation
- Negative scales indicate mirroring along that axis
- Scale = -1.0 means 100% mirror (most common)
- Scale = 1.0 means no transformation (default)
- Scales can be any float value (e.g., 2.0 = 200% scale, -0.5 = 50% mirror)

**Red Highlighting Implementation:**
- Use openpyxl's PatternFill: `PatternFill(start_color='FFFF0000', end_color='FFFF0000', fill_type='solid')`
- Apply to all cells in row (columns A-M) when condition met
- Iterate through rows using `ws.iter_rows(min_row=2, max_row=ws.max_row)`
- Check scale column values (columns H and I) for negative values
- Safe handling: `if cell.value is not None and cell.value < 0`

**Future Enhancements:**
- Add filter/search functionality for mirrored blocks in GUI
- Export mirrored block report as separate sheet
- Add rotation + scale combination analysis (e.g., "90° + X-mirror")
- Add scale factor statistics (min/max/average per block)
- Support Z-axis scale (currently only X and Y)

**Migration Notes:**
- Existing Excel files from previous versions will not be affected
- Users will see new structure immediately after updating
- No data migration required (fresh extraction from DWG files)
- Consider adding version number to Excel file metadata in future
