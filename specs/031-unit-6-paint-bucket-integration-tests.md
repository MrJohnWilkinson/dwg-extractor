# Feature: Unit 6 - Paint-Bucket Integration Tests

## Feature Description
Add integration tests to `app/tests/core/test_geometry.py` that validate the paint-bucket region detection algorithm with realistic block patterns. These tests extend the existing `TestExtractPaintBucketRegions` class with more complex scenarios that simulate real-world CAD block patterns.

## User Story
As a developer maintaining the geometry module
I want comprehensive integration tests for paint-bucket region detection
So that I can confidently validate the algorithm works correctly for realistic block patterns

## Problem Statement
The existing `TestExtractPaintBucketRegions` test class has basic tests for simple patterns (rectangle with divider, 2x2 grid). However, Unit 6 of the paint-bucket polygon detection plan requires additional integration tests that validate:
- Multiple horizontal/vertical dividers creating row/column patterns
- Open LWPOLYLINE (U-shape) with closing LINE forming complete regions
- Complex grid patterns matching real-world block counts from analysis

## Solution Statement
Extend the existing `TestExtractPaintBucketRegions` class in `test_geometry.py` with additional integration tests that cover more complex block patterns. These tests will use in-memory ezdxf blocks to create realistic patterns and validate expected region counts.

## Relevant Files
Use these files to implement the feature:

- `app/tests/core/test_geometry.py` - Target test file containing existing `TestExtractPaintBucketRegions` class (lines 587-658). Add new test methods to this class.
- `app/core/geometry.py` - Contains `_extract_paint_bucket_regions()` function being tested (lines 413-458).
- `ai_output/030-paint-bucket-polygon-detection-plan.md` - Reference for expected polygon counts.
- `ai_output/028-polygon-count-discrepancy-analysis.md` - Block analysis with expected paint-bucket results.

## Implementation Plan
### Phase 1: Foundation
No foundational changes needed. The `TestExtractPaintBucketRegions` class already exists with proper imports and structure.

### Phase 2: Core Implementation
Add 5 new test methods to `TestExtractPaintBucketRegions`:
1. `test_multiple_horizontal_dividers` - Rectangle with 3 horizontal dividers = 4 rows
2. `test_multiple_vertical_dividers` - Rectangle with 2 vertical dividers = 3 columns
3. `test_open_lwpolyline_with_closing_line` - U-shape polyline + LINE = 1 closed region
4. `test_nested_rectangles` - Outer rectangle with smaller inner rectangle = 2 regions
5. `test_complex_grid_3x2` - 3 columns x 2 rows = 6 regions (matches plan table)

### Phase 3: Integration
Run full test suite to ensure no regressions and validate all new tests pass.

## Step by Step Tasks

### Step 1: Add test_multiple_horizontal_dividers
Add test to `TestExtractPaintBucketRegions` class:
- Create 100x100 rectangle LWPOLYLINE (closed)
- Add 3 horizontal LINE dividers at y=25, y=50, y=75
- Assert 4 regions detected (4 horizontal rows)

### Step 2: Add test_multiple_vertical_dividers
Add test to `TestExtractPaintBucketRegions` class:
- Create 100x50 rectangle LWPOLYLINE (closed)
- Add 2 vertical LINE dividers at x=33, x=66
- Assert 3 regions detected (3 vertical columns)

### Step 3: Add test_open_lwpolyline_with_closing_line
Add test to `TestExtractPaintBucketRegions` class:
- Create open U-shape LWPOLYLINE: [(0,0), (0,50), (100,50), (100,0)]
- Add closing LINE from (0,0) to (100,0)
- Assert 1 region detected (the closed U becomes a rectangle)

### Step 4: Add test_nested_rectangles
Add test to `TestExtractPaintBucketRegions` class:
- Create outer 100x100 rectangle LWPOLYLINE (closed)
- Create inner 50x50 rectangle LWPOLYLINE (closed) centered at (25,25)
- Assert 2 regions detected (inner rectangle + outer ring)

### Step 5: Add test_complex_grid_3x2
Add test to `TestExtractPaintBucketRegions` class:
- Create 150x100 rectangle LWPOLYLINE (closed)
- Add 2 vertical LINE dividers at x=50, x=100
- Add 1 horizontal LINE divider at y=50
- Assert 6 regions detected (3 columns x 2 rows)

### Step 6: Run validation commands
Execute all validation commands to ensure tests pass with zero regressions.

## Testing Strategy
### Unit Tests
N/A - This feature IS the tests.

### Integration Tests
All 5 new tests are integration tests validating paint-bucket region detection with realistic block patterns.

### Edge Cases
- `test_open_lwpolyline_with_closing_line` tests the edge case of combining an open polyline with a closing line
- `test_nested_rectangles` tests the edge case of overlapping/nested polygons

### Playwright MCP Tests
N/A - No UI changes.

## Acceptance Criteria
- [ ] 5 new test methods added to `TestExtractPaintBucketRegions` class
- [ ] `test_multiple_horizontal_dividers` passes with 4 regions
- [ ] `test_multiple_vertical_dividers` passes with 3 regions
- [ ] `test_open_lwpolyline_with_closing_line` passes with 1 region
- [ ] `test_nested_rectangles` passes with 2 regions
- [ ] `test_complex_grid_3x2` passes with 6 regions
- [ ] All 510+ tests pass (505 baseline + 5 new)
- [ ] mypy type check passes
- [ ] ruff lint check passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py::TestExtractPaintBucketRegions -v` - Run paint-bucket tests
- `uv run pytest app/tests/ -v` - Run all tests to validate zero regressions
- `uv run mypy app/` - Validate type checking passes
- `uv run ruff check app/` - Validate linting passes

## Notes
- The existing `TestExtractPaintBucketRegions` class already has 5 tests. Adding 5 more brings total to 10 tests for this class.
- Expected final test count: 510 (505 baseline + 5 new tests)
- Tests use in-memory ezdxf documents, no file I/O required
- All tests follow existing patterns in `test_geometry.py`
