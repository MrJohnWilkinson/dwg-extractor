# Chore: Core Module Separation - Extract Geometry and Formatting Utilities

## Chore Description
Split `app/core/extractor.py` (508 lines) and `app/core/excel_writer.py` (449 lines) to improve maintainability by extracting related utilities into focused modules. The goal is to reduce both files to approximately 350 lines each while maintaining clear separation of concerns - geometry calculations vs CAD analysis, and formatting vs data transformation.

This refactoring will create two new modules:
1. `app/core/geometry.py` - Geometric calculation functions for CAD analysis
2. `app/core/excel_formatting.py` - Common Excel formatting logic and utilities

The refactoring must maintain 98% test coverage, follow existing naming conventions, avoid circular dependencies, and ensure zero regressions.

## Relevant Files

**Existing Files to Modify:**

- `app/core/extractor.py` - Contains 4 geometric utility functions to extract (508 lines → ~350 lines)
  - `_get_block_bounding_box()` - Lines 28-112 (85 lines)
  - `_get_intersection_points()` - Lines 115-199 (85 lines)
  - `_calculate_segments()` - Lines 202-233 (32 lines)
  - `_categorize_rotation()` - Lines 236-276 (41 lines)
  - Will retain `ExtractionResult` TypedDict and `extract_blocks()` function
  - Will need import updates to reference new `geometry` module

- `app/core/excel_writer.py` - Contains formatting functions to extract (449 lines → ~350 lines)
  - `_format_block_analysis_sheet()` - Lines 247-261 (15 lines)
  - `_format_layer_analysis_sheet()` - Lines 264-277 (14 lines)
  - `_format_entity_summary_sheet()` - Lines 280-292 (13 lines)
  - `_format_block_geometry_analysis_sheet()` - Lines 396-449 (54 lines)
  - Will retain sheet creation functions and main `write_excel()` function
  - Will need import updates to reference new `excel_formatting` module

- `app/tests/core/test_extractor.py` - Tests that currently import geometry functions
  - Already imports: `_calculate_segments`, `_categorize_rotation`, `_get_block_bounding_box`, `_get_intersection_points`
  - Will need to update imports from `core.extractor` to `core.geometry`

- `app/tests/core/test_excel_writer.py` - Tests for Excel writer functionality
  - May need updates if formatting logic moves to new module
  - Will verify Excel formatting still works correctly

### New Files

- `app/core/geometry.py` - New module for geometric calculation functions
  - Contains: `_get_block_bounding_box()`, `_get_intersection_points()`, `_calculate_segments()`, `_categorize_rotation()`
  - Module docstring explaining geometric analysis purpose
  - Imports: `ezdxf.layouts.BlockLayout` for type hints
  - ~250 lines total (4 functions + docstrings + imports)

- `app/core/excel_formatting.py` - New module for Excel formatting utilities
  - Contains: `_format_block_analysis_sheet()`, `_format_layer_analysis_sheet()`, `_format_entity_summary_sheet()`, `_format_block_geometry_analysis_sheet()`
  - Module docstring explaining Excel formatting purpose
  - Imports: `openpyxl.workbook.workbook.Workbook`, `openpyxl.styles.PatternFill`, constants for sheet names
  - ~120 lines total (4 functions + docstrings + imports + helper for red highlighting)

- `app/tests/core/test_geometry.py` - New test file for geometry module
  - Tests for all 4 geometry functions with edge cases
  - Tests: bounding box calculation, intersection point detection, segment calculation, rotation categorization
  - Edge cases: empty blocks, single points, negative rotations, tolerance boundaries
  - ~150-200 lines following existing test patterns

- `app/tests/core/test_excel_formatting.py` - New test file for Excel formatting module
  - Tests for all 4 formatting functions
  - Tests: auto-filter application, column width settings, red highlighting for mirrored blocks
  - Edge cases: empty worksheets, missing dimensions, negative scales
  - ~100-150 lines following existing test patterns

## Step by Step Tasks

### Step 1: Create app/core/geometry.py module
- Extract the 4 geometric functions from `app/core/extractor.py`:
  - `_get_block_bounding_box()` (lines 28-112)
  - `_get_intersection_points()` (lines 115-199)
  - `_calculate_segments()` (lines 202-233)
  - `_categorize_rotation()` (lines 236-276)
- Add module docstring explaining purpose: "Geometric calculation utilities for CAD block analysis. Provides functions for bounding box calculation, intersection point detection, segment analysis, and rotation categorization."
- Add necessary imports: `from ezdxf.layouts import BlockLayout` for type hints
- Keep all existing docstrings, type hints, and implementation unchanged
- Ensure functions remain private (underscore prefix) as they are internal utilities

### Step 2: Update app/core/extractor.py imports
- Remove the 4 extracted geometric functions from `extractor.py`
- Add import statement at top: `from .geometry import _get_block_bounding_box, _get_intersection_points, _calculate_segments, _categorize_rotation`
- Verify no other changes needed to `extract_blocks()` function - it should work with imported functions
- Verify `ExtractionResult` TypedDict remains in `extractor.py` (not moved)
- Confirm file reduces from 508 to ~350 lines

### Step 3: Create app/core/excel_formatting.py module
- Extract the 4 formatting functions from `app/core/excel_writer.py`:
  - `_format_block_analysis_sheet()` (lines 247-261)
  - `_format_layer_analysis_sheet()` (lines 264-277)
  - `_format_entity_summary_sheet()` (lines 280-292)
  - `_format_block_geometry_analysis_sheet()` (lines 396-449)
- Add module docstring explaining purpose: "Excel worksheet formatting utilities for CAD analysis reports. Provides functions for applying auto-filters, column widths, and conditional formatting to Excel sheets."
- Add necessary imports:
  - `from openpyxl.workbook.workbook import Workbook`
  - `from openpyxl.styles import PatternFill`
  - Sheet name constants from `constants.py`
  - Logger setup from `logger.py`
- Keep all existing docstrings, type hints, and implementation unchanged
- Ensure functions remain private (underscore prefix) as they are internal utilities

### Step 4: Update app/core/excel_writer.py imports
- Remove the 4 extracted formatting functions from `excel_writer.py`
- Add import statement at top: `from .excel_formatting import _format_block_analysis_sheet, _format_layer_analysis_sheet, _format_entity_summary_sheet, _format_block_geometry_analysis_sheet`
- Verify `write_excel()` function works with imported formatting functions (calls at lines 118-121)
- Verify sheet creation functions remain in `excel_writer.py` (not moved)
- Confirm file reduces from 449 to ~350 lines

### Step 5: Create app/tests/core/test_geometry.py
- Create comprehensive test suite for all 4 geometry functions
- Follow existing test patterns from `test_extractor.py` (class structure, docstrings, type hints)
- Test `_get_block_bounding_box()`:
  - Valid blocks with lines, polylines, circles, arcs, points
  - Empty blocks (should return 0,0,0,0)
  - Blocks with single point
  - Mixed entity types
- Test `_get_intersection_points()`:
  - Blocks with various entity types
  - Duplicate point filtering with epsilon tolerance
  - Empty blocks (should return empty lists)
  - Points at tolerance boundary (0.01)
- Test `_calculate_segments()`:
  - Normal list of points (verify distances)
  - Single point (should return empty list)
  - Empty list (should return empty list)
  - Verify rounding to 2 decimal places
- Test `_categorize_rotation()`:
  - Standard angles: 0°, 90°, 180°, 270°
  - Angles within ±1° tolerance: 0.5°, 89.5°, 179.5°, 269.5°
  - Negative angles: -90° (should return '270')
  - Angles > 360°: 450° (should return '90')
  - Non-standard angles: 45°, 135° (should return 'other')
- Use ezdxf to create test block definitions programmatically
- Target 95%+ coverage for the geometry module

### Step 6: Create app/tests/core/test_excel_formatting.py
- Create comprehensive test suite for all 4 formatting functions
- Follow existing test patterns from `test_excel_writer.py` (fixtures, cleanup, assertions)
- Test `_format_block_analysis_sheet()`:
  - Verify auto-filter applied to worksheet
  - Verify column widths set correctly (A=30, B=25, C=25, D=25)
  - Handle empty worksheets gracefully
- Test `_format_layer_analysis_sheet()`:
  - Verify auto-filter applied
  - Verify column widths (A=30, B=25, C=25)
  - Handle missing dimensions attribute
- Test `_format_entity_summary_sheet()`:
  - Verify auto-filter applied
  - Verify column widths (A=25, B=25)
- Test `_format_block_geometry_analysis_sheet()`:
  - Verify auto-filter applied
  - Verify all 13 column widths set correctly
  - Verify red highlighting for negative X scale
  - Verify red highlighting for negative Y scale
  - Verify no highlighting for positive scales
  - Verify highlighting count logged correctly
- Use openpyxl to create test workbooks/worksheets
- Use pandas to populate test data
- Target 95%+ coverage for the excel_formatting module

### Step 7: Update app/tests/core/test_extractor.py imports
- Update import statement from `from core.extractor import _calculate_segments, _categorize_rotation, _get_block_bounding_box, _get_intersection_points, extract_blocks`
- Change to: `from core.geometry import _calculate_segments, _categorize_rotation, _get_block_bounding_box, _get_intersection_points` and `from core.extractor import extract_blocks`
- Verify all existing tests still pass without modification
- No test logic changes needed - only import updates

### Step 8: Run complete validation suite
- Execute all validation commands (see Validation Commands section below)
- Verify zero test failures
- Verify 98%+ code coverage maintained
- Verify no mypy type errors
- Verify no import errors or circular dependencies
- Verify line count targets met (~350 lines for extractor.py and excel_writer.py)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run complete test suite to ensure zero regressions
- `uv run pytest app/tests/ --cov=app/core --cov-report=term-missing` - Verify 98%+ coverage maintained with coverage report
- `uv run pytest app/tests/core/test_geometry.py -v` - Run new geometry tests in verbose mode
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run new Excel formatting tests in verbose mode
- `uv run mypy app/` - Verify no type checking errors introduced
- `wc -l app/core/extractor.py app/core/excel_writer.py app/core/geometry.py app/core/excel_formatting.py` - Verify line count targets met

## Notes

**Refactoring Principles:**
- This is not just moving code to reduce line counts - each new module has a single, cohesive responsibility
- `geometry.py` focuses on geometric calculations (bounding boxes, intersections, segments, rotations)
- `excel_formatting.py` focuses on Excel presentation (auto-filters, column widths, conditional formatting)
- Original modules retain their core responsibilities: `extractor.py` for CAD analysis logic, `excel_writer.py` for data transformation

**Why These Specific Extractions:**
- Geometry functions are pure utilities with no CAD extraction logic - they analyze block definitions independently
- Formatting functions are pure Excel operations with no data transformation - they only modify worksheet appearance
- Both extractions have zero dependencies on the main business logic in their parent modules
- No circular dependency risk - geometry is used by extractor, formatting is used by excel_writer

**Import Strategy:**
- Use relative imports (`.geometry`, `.excel_formatting`) for consistency with existing codebase
- Maintain private function naming convention (underscore prefix) - these are internal utilities
- No changes to public APIs - `extract_blocks()` and `write_excel()` remain the only public functions

**Testing Strategy:**
- New test files follow existing patterns (class-based, docstrings, type hints)
- Focus on edge cases for geometry (empty blocks, tolerance boundaries, angle normalization)
- Focus on Excel corner cases (empty sheets, missing attributes, conditional formatting logic)
- Import updates in existing tests are minimal - only changing import source

**Line Count Verification:**
- `extractor.py`: 508 → ~350 lines (removing ~243 lines of geometry functions, adding 1 import line)
- `excel_writer.py`: 449 → ~350 lines (removing ~96 lines of formatting functions, adding 1 import line)
- `geometry.py`: ~250 lines (4 functions + docstrings + imports)
- `excel_formatting.py`: ~120 lines (4 functions + docstrings + imports)

**Coverage Target:**
- Existing coverage is 98% - must maintain or improve
- Geometry functions already have tests in `test_extractor.py` - moving them ensures same coverage
- Formatting functions may have indirect coverage - new tests make it explicit
- Target 95%+ coverage for both new modules individually
