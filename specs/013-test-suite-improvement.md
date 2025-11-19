# Chore: Test Suite Improvement - Coverage, Edge Cases, and Integration Tests

## Chore Description
Systematically improve the test suite to achieve comprehensive coverage, validate recent features (specs 010, 011, 012), test edge cases with real files, ensure fast execution, and verify type safety. This chore focuses on filling coverage gaps, testing failure scenarios, validating constants consistency, removing obsolete tests, and ensuring all tests run headless in WSL without X server dependencies.

Current state:
- Overall coverage: 87% (425 statements, 57 missed)
- Coverage gaps in `app/core/extractor.py`: 77% (51 missed lines in helper functions and error handling)
- Coverage gaps in `app/core/excel_writer.py`: 96% (6 missed lines in edge case handling)
- Missing tests for recent features: specs 010, 011, 012
- No validation that constants match actual DataFrame columns
- Limited edge case testing with real invalid files
- No parametrized tests for block rotation/scale variations

Target state:
- Overall coverage: >90%
- All public functions >80% coverage
- All recent features have corresponding tests
- Constants validated against actual data
- Edge cases tested with real invalid files
- All tests run headless in <5 seconds
- Zero obsolete tests
- mypy passes with no errors

## Relevant Files
Use these files to resolve the chore:

- **app/core/extractor.py** (lines 26-108, 111-196, 232-273, 439-485)
  - Lines 74-102: `_get_block_bounding_box()` - CIRCLE, ARC, POINT entity handling (uncovered)
  - Lines 154-178: `_get_intersection_points()` - CIRCLE, ARC, POINT entity handling (uncovered)
  - Lines 442-445: Scale attribute exception handling in extract_blocks() (uncovered)
  - Lines 483-485: Generic exception handling in extract_blocks() (uncovered)
  - These functions need tests using real DWG/DXF files with various entity types

- **app/core/excel_writer.py** (lines 128-133)
  - Lines 128-133: Exception handling in write_excel() main function (uncovered)
  - Need tests for ValueError and generic exceptions during Excel generation

- **app/core/constants.py** (all lines)
  - All EXCEL_COLUMN_* constants need validation against actual DataFrame columns
  - Need test to ensure constants match what extractor/excel_writer actually produce

- **app/tests/core/test_extractor.py** (entire file)
  - Add tests for CIRCLE, ARC, POINT entities in bounding box calculation
  - Add tests for CIRCLE, ARC, POINT entities in intersection point detection
  - Add parametrized tests for block rotation/scale variations
  - Add tests for missing xscale/yscale attributes
  - Add tests for generic exception handling

- **app/tests/core/test_excel_writer.py** (entire file)
  - Add test validating spec 010 (consolidated geometry sheet)
  - Add test validating spec 011 (open folder button - constants only)
  - Add test validating spec 012 (naming conventions in DataFrame columns)
  - Add test comparing constants.py values against DataFrame columns
  - Add tests for openpyxl.Workbook.save failures
  - Mock file I/O to ensure headless execution

- **app/tests/assets/** (directory)
  - Use existing test files: empty_drawing.dxf, invalid.dxf, test_rotations.dxf
  - Create new test files if needed: corrupted.dxf, circles_arcs.dxf

### New Files
None required - all improvements use existing test files and infrastructure.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Run coverage report and identify gaps
- Execute: `uv run pytest --cov=app/core --cov-report=term-missing app/tests/`
- Document all functions with <80% coverage in this list:
  - `_get_block_bounding_box()`: Missing CIRCLE (77-84), ARC (86-94), POINT (96-102) branches
  - `_get_intersection_points()`: Missing CIRCLE (157-164), ARC (166-173), POINT (175-178) branches
  - `extract_blocks()`: Missing scale attribute exception (442-445) and generic exception (483-485)
  - `write_excel()`: Missing ValueError (128-130) and generic exception (131-133)
- Capture exact line numbers for targeted test coverage

### Step 2: Create test file with CIRCLE, ARC, POINT entities
- Create `app/tests/assets/circles_arcs_points.dxf` using ezdxf
- Include test blocks with:
  - CIRCLE entities (various radii)
  - ARC entities (various angles)
  - POINT entities (various locations)
  - Mixed LINE + CIRCLE combinations
- Use for testing `_get_block_bounding_box()` and `_get_intersection_points()`

### Step 3: Test _get_block_bounding_box with CIRCLE entities
- Add test `test_get_block_bounding_box_with_circles()` in test_extractor.py
- Create test block with 2-3 CIRCLE entities at different positions
- Verify bounding box correctly encompasses all circles
- Target coverage: lines 77-84 in extractor.py

### Step 4: Test _get_block_bounding_box with ARC entities
- Add test `test_get_block_bounding_box_with_arcs()` in test_extractor.py
- Create test block with 2-3 ARC entities at different angles
- Verify bounding box uses simplified full-circle extents
- Target coverage: lines 86-94 in extractor.py

### Step 5: Test _get_block_bounding_box with POINT entities
- Add test `test_get_block_bounding_box_with_points()` in test_extractor.py
- Create test block with multiple POINT entities
- Verify bounding box includes all point locations
- Target coverage: lines 96-102 in extractor.py

### Step 6: Test _get_intersection_points with CIRCLE entities
- Add test `test_get_intersection_points_with_circles()` in test_extractor.py
- Create test block with CIRCLE entities
- Verify intersection points include circle bounding box corners
- Target coverage: lines 157-164 in extractor.py

### Step 7: Test _get_intersection_points with ARC and POINT entities
- Add test `test_get_intersection_points_with_arcs_and_points()` in test_extractor.py
- Create test block with ARC and POINT entities
- Verify intersection points extracted correctly
- Target coverage: lines 166-178 in extractor.py

### Step 8: Test scale attribute exception handling
- Add test `test_extract_blocks_missing_scale_attributes()` in test_extractor.py
- Create mock DXF file or use ezdxf to create INSERT without xscale/yscale
- Verify default scale (1.0, 1.0) is used when attributes missing
- Target coverage: lines 442-445 in extractor.py

### Step 9: Test generic exception handling in extract_blocks
- Add test `test_extract_blocks_generic_exception()` in test_extractor.py
- Mock ezdxf.readfile to raise unexpected exception (e.g., RuntimeError)
- Verify exception is re-raised and logged
- Target coverage: lines 483-485 in extractor.py

### Step 10: Test Excel writer exception handling
- Add test `test_write_excel_value_error()` in test_excel_writer.py
- Pass invalid extraction_data (wrong types, missing keys)
- Verify ValueError is raised appropriately
- Add test `test_write_excel_generic_exception()` for openpyxl failures
- Mock `pd.ExcelWriter` or `Workbook.save` to raise exception
- Target coverage: lines 128-133 in excel_writer.py

### Step 11: Validate constants against DataFrame columns
- Add test `test_constants_match_dataframe_columns()` in test_excel_writer.py
- Extract blocks from sample_drawing.dxf
- Generate Excel and load all sheets
- For each sheet, verify column names exactly match constants.py values:
  - Block Analysis: EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_BLOCK_INSERTION_COUNT, etc.
  - Layer Analysis: EXCEL_COLUMN_LAYER_NAME, EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT, etc.
  - Entity Summary: EXCEL_COLUMN_ENTITY_TYPE_NAME, EXCEL_COLUMN_ENTITY_TYPE_COUNT
  - Block Geometry Analysis: All 13 columns
- Use `assert list(df.columns) == [CONST1, CONST2, ...]` pattern

### Step 12: Test spec 010 - consolidated geometry sheet
- Add test `test_spec_010_consolidated_geometry_sheet()` in test_excel_writer.py
- Verify Block Geometry Analysis sheet has exactly 13 columns
- Verify scale columns (block_scale_x, block_scale_y) present
- Verify rotation columns (0, 90, 180, 270, other) present
- Verify red highlighting for mirrored blocks (negative scales)
- Verify Block Analysis sheet has only 4 columns (no rotations)

### Step 13: Test spec 012 - naming conventions
- Add test `test_spec_012_naming_conventions()` in test_excel_writer.py
- Verify all column names follow {domain}_{attribute}[_{qualifier}] pattern
- Check patterns:
  - block_name (domain_attribute)
  - block_insertion_count (domain_attribute_qualifier)
  - block_scale_x (domain_attribute_qualifier)
  - layer_name, entity_type_name, etc.
- Reference: app_docs/005-field-naming-convention.md

### Step 14: Test edge cases with invalid files
- Add test `test_extract_corrupted_dxf_file()` in test_extractor.py
- Create or use `app/tests/assets/invalid.dxf` (corrupted DXF)
- Verify ValueError raised with "Invalid or corrupted" message
- Add test `test_extract_empty_dwg_file()` in test_extractor.py
- Use `empty_drawing.dxf` and verify empty results (not exception)
- Add test `test_extract_unsupported_extension_raises_error()` (already exists, verify)

### Step 15: Add parametrized test for rotation/scale variations
- Add test `test_block_rotation_scale_variations()` in test_extractor.py
- Use `@pytest.mark.parametrize` with test_rotations.dxf fixture
- Test multiple rotation angles: 0°, 45°, 90°, 135°, 180°, 270°, 359.5°
- Test multiple scale combinations: (1.0, 1.0), (-1.0, 1.0), (1.0, -1.0), (-1.0, -1.0), (2.0, 0.5)
- Verify categorization and extraction for each combination

### Step 16: Mock file I/O for headless execution
- Review all tests for tkinter.filedialog usage (none expected in unit tests)
- Review all tests for openpyxl.Workbook.save that write to disk
- Ensure temp_dir fixture used in test_excel_writer.py cleans up properly
- Verify no X server dependencies in core logic tests
- All GUI tests should be skipped or mocked (per README line 75)

### Step 17: Remove obsolete tests
- Search app/tests/ for function names that no longer exist in app/core/
- Use: `uv run grep -r "test_.*" app/tests/ --include="*.py"`
- Compare with: `uv run grep -r "^def " app/core/ --include="*.py"`
- Remove tests for:
  - Deleted functions (if any found)
  - Refactored code with changed signatures
  - Old sheet names (EXCEL_SHEET_BLOCK_COUNTS should be EXCEL_SHEET_BLOCK_ANALYSIS)
- Verify no broken imports after removal

### Step 18: Optimize slow tests
- Run: `uv run pytest app/tests/ -v --durations=10`
- Identify tests taking >1 second
- If any slow tests found:
  - Split into smaller focused tests
  - Mock expensive operations (file I/O, ezdxf parsing)
  - Use smaller test fixtures
- Target: All tests complete in <5 seconds total

### Step 19: Run full validation suite
- Execute all validation commands listed below
- Verify zero test failures
- Verify coverage >90% for app/core/
- Verify mypy passes with no errors
- Document any remaining coverage gaps with justification

### Step 20: Document coverage improvements
- Capture final coverage report: `uv run pytest --cov=app/core --cov-report=term-missing app/tests/`
- Compare with initial coverage (Step 1)
- Document improvement percentage in test output
- Identify any remaining <80% functions and justify (e.g., GUI code, platform-specific)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest --cov=app/core --cov-report=term-missing app/tests/` - Verify coverage >90% with all gaps documented
- `uv run pytest app/tests/core/test_extractor.py -v` - Run all extractor tests, verify new coverage tests pass
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run all excel writer tests, verify constants validation passes
- `uv run pytest app/tests/ -v` - Run full test suite, verify all tests pass in <5 seconds
- `uv run pytest app/tests/ -v --durations=10` - Verify no slow tests (>1 second)
- `uv run mypy app/` - Verify type checking passes with zero errors
- `uv run pytest app/tests/core/test_excel_writer.py::test_constants_match_dataframe_columns -v` - Verify constants validation
- `uv run pytest app/tests/core/test_excel_writer.py::test_spec_010_consolidated_geometry_sheet -v` - Verify spec 010 validation
- `uv run pytest app/tests/core/test_excel_writer.py::test_spec_012_naming_conventions -v` - Verify spec 012 validation

## Notes

### Coverage Target Justification
- Overall >90% coverage is achievable by testing uncovered branches
- app/core/extractor.py can reach 85-90% by adding entity type tests
- app/core/excel_writer.py can reach 98%+ by adding exception tests
- app/main.py GUI code excluded from coverage requirements (WSL X server issues per README line 75)

### Test Execution Speed
- Current: 2.58 seconds (58 tests)
- Target: <5 seconds (70-80 tests after additions)
- Strategy: Use in-memory test fixtures, avoid large DWG files, mock expensive operations

### Constants Validation Strategy
Test validates that constants.py values exactly match DataFrame columns produced by:
1. Block Analysis sheet: 4 columns from `_create_block_analysis_sheet()`
2. Layer Analysis sheet: 3 columns from `_create_layer_analysis_sheet()`
3. Entity Summary sheet: 2 columns from `_create_entity_summary_sheet()`
4. Block Geometry Analysis sheet: 13 columns from `_create_block_geometry_analysis_sheet()`

This ensures constants stay synchronized with actual implementation.

### Edge Case Testing Philosophy
Use real DWG/DXF files wherever possible instead of mocking ezdxf:
- Valid files: sample_drawing.dxf, test_rotations.dxf (already exist)
- Empty files: empty_drawing.dxf (already exists)
- Invalid files: invalid.dxf (already exists)
- Special entities: Create circles_arcs_points.dxf for geometry tests
- Mock only I/O operations: openpyxl.Workbook.save, tkinter.filedialog

### Parametrized Test Benefits
Using `@pytest.mark.parametrize` for rotation/scale variations:
- Reduces code duplication
- Tests all combinations systematically
- Easy to add new test cases
- Clear failure messages showing which parameters failed

### Obsolete Code Detection
Systematically check for:
1. Tests referencing old constant names (EXCEL_SHEET_BLOCK_COUNTS vs EXCEL_SHEET_BLOCK_ANALYSIS)
2. Tests for deleted helper functions
3. Tests with outdated assertions (e.g., 9 columns vs 4 columns in Block Analysis)
4. Unused test fixtures in app/tests/assets/

### mypy Type Safety
All new tests must maintain type safety:
- Use type hints for test functions (e.g., `-> None`)
- Use type hints for fixtures
- Verify mypy passes after adding tests
- Fix any new type errors introduced
