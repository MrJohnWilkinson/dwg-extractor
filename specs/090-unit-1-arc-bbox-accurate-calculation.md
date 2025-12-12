# Feature: Accurate ARC Bounding Box Calculation

## Feature Description

Implement accurate ARC bounding box calculations in `geometry.py` to replace the current simplified full-circle extent approach. Currently, ARC entities use full-circle extents for bounding box calculation, which causes incorrect filtering behavior. For example, an arc spanning only 270-356 degrees incorrectly reports a bounding box that includes the full left extent of the circle (-779), leading to incorrect trim values.

The implementation adds a new `_get_arc_bounding_box()` helper function that calculates the actual bounding box based on the arc's angular extent by considering only:
1. The arc's start point
2. The arc's end point
3. Any cardinal directions (0, 90, 180, 270 degrees) that fall within the arc span

This provides geometrically accurate bounding boxes for ARC entities, improving the precision of block filtering and content zone detection.

## User Story

As a CAD engineer using the DXF Block Extractor
I want accurate bounding box calculations for ARC entities
So that block filtering and trim calculations correctly reflect the actual arc geometry rather than an overestimated full-circle extent

## Problem Statement

The current ARC bounding box implementation in `_get_block_bounding_box()` uses full-circle extents regardless of the arc's actual angular span. This causes several issues:

1. **Incorrect filtering**: Blocks with arcs are incorrectly filtered because their bounding boxes are larger than actual
2. **Wrong trim values**: The `-779 trim left` issue where an arc from 270-356 degrees incorrectly reports left extent as -779 (full circle radius) instead of near 0
3. **Overestimated block sizes**: Block dimensions appear larger than they actually are

Example from the original issue:
- Arc: center=(0, -953), radius=779, angles=270-356
- Current (wrong): min_x = -779 (full circle left extent)
- Correct: min_x should be near 0 (arc doesn't extend to the left)

## Solution Statement

Implement a dedicated `_get_arc_bounding_box()` helper function that:

1. Calculates the exact start and end points of the arc using trigonometry
2. Determines which cardinal directions (0, 90, 180, 270 degrees) fall within the arc span
3. Only includes cardinal point extremes if they're actually part of the arc
4. Returns accurate (min_x, min_y, max_x, max_y) bounds

The algorithm handles wrap-around cases (e.g., arc from 350 to 10 degrees) correctly by treating the arc span as counter-clockwise from start to end angle.

## Relevant Files

Use these files to implement the feature:

- **`app/core/geometry.py`** - Primary implementation file
  - Lines 242-250: Current ARC handling in `_get_block_bounding_box()` that needs updating
  - Insert new `_get_arc_bounding_box()` helper function before `_get_block_bounding_box()` (around line 178)
  - Already imports `math` module needed for trigonometric calculations

- **`app/tests/core/test_geometry.py`** - Unit tests for geometry functions
  - Lines 84-99: `test_bounding_box_with_arcs` test that needs updated expected values
  - Add new `TestArcBoundingBox` test class for comprehensive arc bbox testing
  - Existing test imports and patterns to follow

- **`app/tests/core/extractor/test_extractor_core.py`** - Extractor integration tests
  - Lines 571-586: `test_get_block_bounding_box_with_arcs` test that needs updated expected values
  - Mirrors the geometry test for integration coverage

- **`app/tests/assets/circles_arcs_points.dxf`** - Test asset file containing TEST_ARCS block
  - Arc 1: center=(100, 100), radius=50, 0 to 90 degrees
  - Arc 2: center=(200, 150), radius=40, 45 to 180 degrees
  - Arc 3: center=(150, 50), radius=30, 270 to 360 degrees

- **`ai_output/086-arc-bbox-implementation-plan-v2.md`** - Reference document with implementation details and expected values

## Implementation Plan

### Phase 1: Foundation

Add the `_get_arc_bounding_box()` helper function that implements the core algorithm for calculating accurate arc bounding boxes. This function will be a pure mathematical utility that takes arc parameters and returns bounds.

Key implementation details:
- Normalize angles to [0, 360) range
- Calculate start and end points using cos/sin
- Handle wrap-around arcs (e.g., 350 to 10 degrees) by extending end angle by 360 if needed
- Check each cardinal direction (0, 90, 180, 270) to see if it falls within the arc span

### Phase 2: Core Implementation

Update the ARC entity handling in `_get_block_bounding_box()` to use the new helper function instead of the simplified full-circle approach:

1. Extract `start_angle` and `end_angle` from `entity.dxf`
2. Call `_get_arc_bounding_box()` with center, radius, and angles
3. Merge resulting bounds with accumulated min/max values

### Phase 3: Integration

Update existing tests to expect the new accurate bounding box values, and add comprehensive unit tests for the helper function covering various arc configurations including edge cases like wrap-around arcs and full circles.

## Step by Step Tasks

### Step 1: Add `_get_arc_bounding_box()` Helper Function

Add the new helper function to `app/core/geometry.py`, inserting it before `_get_block_bounding_box()` (around line 178):

- Function signature: `_get_arc_bounding_box(center_x, center_y, radius, start_angle, end_angle) -> tuple[float, float, float, float]`
- Normalize start angle to [0, 360)
- Calculate start point: `(center_x + radius * cos(start), center_y + radius * sin(start))`
- Calculate end point: `(center_x + radius * cos(end), center_y + radius * sin(end))`
- Initialize bounds with start and end points
- Handle wrap-around by setting `span_end = end + 360` if `end <= start`
- Create `angle_in_span()` helper to check if a cardinal angle falls within the arc
- Check each cardinal direction and extend bounds if in span:
  - 0 degrees (right): affects max_x
  - 90 degrees (top): affects max_y
  - 180 degrees (left): affects min_x
  - 270 degrees (bottom): affects min_y
- Return `(min_x, min_y, max_x, max_y)`

### Step 2: Update ARC Handling in `_get_block_bounding_box()`

Modify the ARC handling block at lines 242-250 in `app/core/geometry.py`:

- Keep existing center and radius extraction
- Add extraction of `start_angle` and `end_angle` from `entity.dxf`
- Replace the 4 min/max lines with a call to `_get_arc_bounding_box()`
- Unpack the returned tuple and update accumulated min/max values
- Keep `has_geometry = True`

### Step 3: Add `TestArcBoundingBox` Test Class

Add a new test class to `app/tests/core/test_geometry.py` with the following tests:

- `test_quarter_arc_first_quadrant` - Arc from 0 to 90 degrees at origin with radius 100
  - Expected: min_x=0, min_y=0, max_x=100, max_y=100

- `test_quarter_arc_fourth_quadrant` - Arc from 270 to 360 degrees at origin with radius 100
  - Expected: min_x=0, min_y=-100, max_x=100, max_y=0

- `test_arc_45_to_180` - Arc from 45 to 180 degrees, center=(200, 150), radius=40
  - Expected: min_x=160, min_y=150, max_x~=228.28, max_y=190

- `test_semicircle_top` - Arc from 0 to 180 degrees (top semicircle), center=(50, 50), radius=25
  - Expected: min_x=25, min_y=50, max_x=75, max_y=75

- `test_wrap_around_arc` - Arc from 350 to 10 degrees (crosses 0), origin, radius=100
  - Expected: max_x=100 (includes 0 degree cardinal point)

- `test_full_circle_arc` - Arc from 0 to 360 degrees should equal full circle
  - Expected: equals full circle bbox (50, 50, 150, 150) for center=(100,100), r=50

- `test_arc_270_to_356_problematic_case` - The original issue case
  - Arc: center=(0, -953), radius=779, angles=270 to 356.1
  - Expected: min_x > -100 (NOT -779), min_y = -953 - 779

Add required import: `from core.geometry import _get_arc_bounding_box`

### Step 4: Update `test_bounding_box_with_arcs` in test_geometry.py

Update the test at lines 84-99 in `app/tests/core/test_geometry.py`:

- Update docstring to say "accurate angular extents" instead of "simplified full-circle extents"
- Update comments to reflect new bbox calculations:
  - Arc 1: center=(100, 100), r=50, 0 to 90 degrees -> bbox=(100, 100, 150, 150)
  - Arc 2: center=(200, 150), r=40, 45 to 180 degrees -> bbox=(160, 150, ~228.3, 190)
  - Arc 3: center=(150, 50), r=30, 270 to 360 degrees -> bbox=(150, 20, 180, 50)
  - Overall bbox: (100, 20, ~228.3, 190)
- Change assertions to use `pytest.approx()`:
  - `assert bbox[0] == pytest.approx(100.0, abs=0.01)` - min_x
  - `assert bbox[1] == pytest.approx(20.0, abs=0.01)` - min_y
  - `assert bbox[2] == pytest.approx(228.28, abs=0.1)` - max_x
  - `assert bbox[3] == pytest.approx(190.0, abs=0.01)` - max_y

### Step 5: Update `test_get_block_bounding_box_with_arcs` in test_extractor_core.py

Update the test at lines 571-586 in `app/tests/core/extractor/test_extractor_core.py`:

- Same changes as Step 4 (update docstring, comments, and assertions)
- Update expected values from (50, 20, 240, 190) to (100, 20, ~228.3, 190)
- Use `pytest.approx()` for floating point comparisons

### Step 6: Verify All Tests Pass

Run the validation commands to ensure the implementation is correct and there are no regressions.

## Testing Strategy

### Unit Tests

**New `TestArcBoundingBox` class** - Direct tests for `_get_arc_bounding_box()` function:
- Tests various arc configurations: quarter arcs, semicircles, arbitrary angles
- Tests edge cases: wrap-around arcs, full circles, problematic real-world case
- Uses `pytest.approx()` for floating point comparisons with appropriate tolerances

**Updated existing tests** - Verify integration with `_get_block_bounding_box()`:
- `test_bounding_box_with_arcs` in test_geometry.py
- `test_get_block_bounding_box_with_arcs` in test_extractor_core.py

### Integration Tests

The existing test suite provides integration coverage:
- Tests use real DXF file (`circles_arcs_points.dxf`) with defined arc geometries
- Verifies end-to-end flow from entity parsing through bounding box calculation

### Edge Cases

1. **Quarter arcs in each quadrant** - Test arcs limited to single quadrants
2. **Semicircles** - Test arcs spanning exactly 180 degrees
3. **Wrap-around arcs** - Arcs that cross the 0 degree boundary (e.g., 350 to 10 degrees)
4. **Full circle arcs** - Arc with 0 to 360 degrees should match circle bbox
5. **Near-full arcs** - Arcs like 270 to 356 degrees that almost complete the circle
6. **Small arcs** - Arcs spanning just a few degrees
7. **Arcs at non-origin centers** - Verify center offset is correctly applied

### Playwright MCP Tests

Not applicable - this is a backend geometric calculation with no UI interaction.

## Acceptance Criteria

1. **New helper function exists**: `_get_arc_bounding_box()` is implemented in `geometry.py` with proper docstring and type hints
2. **Accurate arc bounding boxes**: ARC entities return bounding boxes based on actual angular extent, not full-circle extent
3. **Test arc bbox values**: For TEST_ARCS block in `circles_arcs_points.dxf`:
   - Old expected: (50, 20, 240, 190)
   - New expected: (100, 20, ~228.3, 190)
4. **All unit tests pass**: Including new `TestArcBoundingBox` class with 7 test methods
5. **No regressions**: All existing tests continue to pass
6. **Type checking passes**: `mypy app/` runs without errors
7. **Original issue resolved**: Arc from 270-356 degrees no longer reports incorrect -779 left extent

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py::TestArcBoundingBox -v` - Run new arc bounding box unit tests
- `uv run pytest app/tests/core/test_geometry.py::TestBoundingBox::test_bounding_box_with_arcs -v` - Run updated arc test in geometry
- `uv run pytest app/tests/core/extractor/test_extractor_core.py::TestBoundingBox::test_get_block_bounding_box_with_arcs -v` - Run updated arc test in extractor
- `uv run pytest app/tests/core/test_geometry.py -v -k "arc or Arc"` - Run all arc-related geometry tests
- `uv run pytest app/tests/core/extractor/test_extractor_core.py -v -k "arc or Arc"` - Run all arc-related extractor tests
- `uv run pytest app/tests/ -v` - Run complete test suite to verify zero regressions
- `uv run mypy app/` - Run type checking to ensure no type errors

## Notes

1. **Import statement**: The `math` module is already imported in `geometry.py` (line 22), so no additional imports needed for the helper function.

2. **Test import update**: The test file `test_geometry.py` will need to add `_get_arc_bounding_box` to its imports from `core.geometry`.

3. **Angle convention**: DXF uses counter-clockwise angles from the positive X-axis, measured in degrees. This matches standard mathematical convention.

4. **Floating point tolerance**: Use `pytest.approx(value, abs=0.01)` for most comparisons, with `abs=0.1` for values derived from trigonometric calculations (like cos(45) * 40).

5. **Expected value calculations**:
   - Arc 2 max_x: 200 + 40 * cos(45 deg) = 200 + 40 * 0.7071 = 228.28
   - Arc 3 min_y: 50 - 30 = 20 (at 270 degree cardinal point)

6. **Reference document**: Detailed implementation guidance available in `ai_output/086-arc-bbox-implementation-plan-v2.md`

7. **This is Unit 1 of the ARC bbox feature**: First implementation unit with no prior learnings to incorporate.
