# Bug: Collinear merging wraparound fix

## Bug Description
The `calculate_shortest_straight_side()` function in `geometry.py` incorrectly counts polygon sides when the starting vertex (V0) lies in the middle of a collinear edge sequence. The algorithm processes edges linearly from V0 through all vertices back to V0, merging consecutive collinear edges along the way. However, it never checks if the final merged side is collinear with the first merged side - meaning edges that are geometrically part of the same straight line are counted as separate sides.

**Symptoms:**
- A 4-sided rectangle is incorrectly detected as 5-sided
- The min_side_filter fails to apply to shapes that should be filtered (because 5-sided polygons pass through the filter that only applies to 4-sided rectangles)
- Polygons appear in output that should have been filtered out

**Expected behavior:**
- Rectangle with V0 in middle of bottom edge should return `side_count = 4`
- The first and last sides should be merged if they are collinear

**Actual behavior:**
- Rectangle with V0 in middle of bottom edge returns `side_count = 5`
- First side (partial bottom edge from V0) and last side (partial bottom edge to V0) are counted separately

## Problem Statement
The linear single-pass algorithm at `geometry.py:145-167` only tracks side lengths, not side angles. After the loop completes, there is no way to check if the first and last sides are collinear because the angle information is lost. The algorithm needs to track both length and angle for each side, then perform a post-loop wraparound check.

## Solution Statement
Modify the algorithm to:
1. Store `(length, angle)` tuples in `straight_sides` instead of just lengths
2. After the initial pass completes, check if the first and last sides are collinear using the existing `angles_collinear()` function
3. If collinear, merge them by combining their lengths and removing the last side entry
4. Return the minimum length from the merged list

This is a minimal, surgical fix that:
- Preserves all existing behavior for non-wraparound cases
- Uses the existing `angles_collinear()` function (no new logic needed)
- Only adds ~10 lines of code after the main loop

## Steps to Reproduce
1. Create a polygon with vertices where V0 is in the middle of a collinear edge sequence:
   ```python
   polygon = [
       (24953.75, 13351.94),  # V0 - middle of bottom edge
       (24172.75, 13351.94),  # V1 - collinear with V0
       (23391.75, 13351.94),  # V2 - collinear with V0, V1
       (23391.75, 13424.94),  # V3 - corner (left edge)
       (25734.75, 13424.94),  # V4 - corner (top edge)
       (25734.75, 13351.94),  # V5 - corner (right edge)
   ]
   ```
2. Call `calculate_shortest_straight_side(polygon)`
3. Observe: Returns `(781.0, 5)` - 5 sides detected
4. Expected: Should return `(73.0, 4)` - 4 sides (rectangle)

The bottom edge is split:
- First side: V0 to V2 (leftward portion of bottom)
- Last side: V5 to V0 (rightward portion of bottom)
These are collinear and should be merged into one side.

## Root Cause Analysis
The algorithm at lines 145-167 processes vertices in a single forward pass:

```python
i = 0
while i < len(vertices) - 1:
    # Start a new side
    side_start = vertices[i]
    current_angle = edge_angle(vertices[i], vertices[i + 1])

    # Extend side while consecutive edges are collinear
    j = i + 1
    while j < len(vertices) - 1:
        next_angle = edge_angle(vertices[j], vertices[j + 1])
        if angles_collinear(current_angle, next_angle, angle_tolerance):
            j += 1
        else:
            break

    # Calculate total length of merged side
    side_end = vertices[j]
    side_length = edge_length(side_start, side_end)

    if side_length > 1e-9:  # Ignore degenerate edges
        straight_sides.append(side_length)

    i = j
```

**Root cause:** The algorithm only stores `side_length` (a float), discarding the angle information. After the loop, there's no way to check if the first and last sides should be merged because their angles are unknown.

**Why this matters:** In a closed polygon, the path from V0 through all vertices and back to V0 forms a cycle. If V0 happens to be placed in the middle of what should be a single straight side, the algorithm treats the two "halves" of that side as separate sides.

## Relevant Files
Use these files to fix the bug:

- **`app/core/geometry.py:87-171`** - Contains `calculate_shortest_straight_side()` function
  - Lines 143: `straight_sides: list[float]` needs to become `list[tuple[float, float]]`
  - Lines 164-165: Store `(side_length, current_angle)` instead of just `side_length`
  - Lines 169-171: Add wraparound check and merge logic before returning

- **`app/tests/core/test_geometry.py:1762-1952`** - Contains `TestCalculateShortestStraightSide` test class
  - Add new test methods for wraparound cases
  - Existing tests must continue to pass

### New Files
None required.

## Step by Step Tasks

### Step 1: Modify straight_sides to store (length, angle) tuples

In `app/core/geometry.py`, change the `straight_sides` list to store tuples instead of just lengths:

- Line 143: Change `straight_sides: list[float] = []` to `straight_sides: list[tuple[float, float]] = []`
- Lines 164-165: Change `straight_sides.append(side_length)` to `straight_sides.append((side_length, current_angle))`

### Step 2: Add wraparound collinearity check after the main loop

After the main `while i < len(vertices) - 1:` loop ends (after line 167), add logic to check if the first and last sides are collinear:

- Check if `len(straight_sides) >= 2`
- Extract first side angle: `first_angle = straight_sides[0][1]`
- Extract last side angle: `last_angle = straight_sides[-1][1]`
- Use existing `angles_collinear(first_angle, last_angle, angle_tolerance)` to check
- If collinear:
  - Calculate merged length: `merged_length = straight_sides[0][0] + straight_sides[-1][0]`
  - Update first entry: `straight_sides[0] = (merged_length, first_angle)`
  - Remove last entry: `straight_sides.pop()`

### Step 3: Update return statement to extract lengths from tuples

Modify lines 169-171 to extract just the lengths when returning:

- Change `if not straight_sides:` check to work with the new structure
- Change `return (min(straight_sides), len(straight_sides))` to:
  ```python
  lengths = [side[0] for side in straight_sides]
  return (min(lengths), len(lengths))
  ```

### Step 4: Add test for basic wraparound case

Add test method `test_collinear_edge_merging_wraparound` to `TestCalculateShortestStraightSide` class in `app/tests/core/test_geometry.py`:

```python
def test_collinear_edge_merging_wraparound(self) -> None:
    """Test that first and last sides merge when V0 is mid-edge."""
    # Rectangle with V0 in middle of bottom edge
    # Bottom edge: V5->V0->V1->V2 (all collinear, should merge to one side)
    # Left edge: V2->V3
    # Top edge: V3->V4
    # Right edge: V4->V5
    wraparound_rect: list[tuple[float, float]] = [
        (50.0, 0.0),   # V0 - middle of bottom edge
        (25.0, 0.0),   # V1 - collinear with V0
        (0.0, 0.0),    # V2 - left corner
        (0.0, 30.0),   # V3 - top-left
        (100.0, 30.0), # V4 - top-right
        (100.0, 0.0),  # V5 - right corner, edge to V0 is collinear with V0->V1
    ]
    # Expected: 4 sides (rectangle), shortest side is 30 (left/right edges)
    shortest_side, side_count = calculate_shortest_straight_side(wraparound_rect)
    assert side_count == 4, f"Expected 4 sides, got {side_count}"
    assert shortest_side == pytest.approx(30.0)
```

### Step 5: Add test for real-world failing case

Add test method `test_collinear_merging_real_world_case` to `TestCalculateShortestStraightSide` class:

```python
def test_collinear_merging_real_world_case(self) -> None:
    """Test the exact failing polygon from the bug report."""
    # Real polygon that was incorrectly detected as 5-sided
    real_polygon: list[tuple[float, float]] = [
        (24953.75, 13351.94),  # V0 - middle of bottom edge
        (24172.75, 13351.94),  # V1
        (23391.75, 13351.94),  # V2 - left corner
        (23391.75, 13424.94),  # V3 - top-left
        (25734.75, 13424.94),  # V4 - top-right
        (25734.75, 13351.94),  # V5 - right corner
    ]
    # This is a rectangle:
    # - Bottom: 2343.0 units (25734.75 - 23391.75)
    # - Height: 73.0 units (13424.94 - 13351.94)
    shortest_side, side_count = calculate_shortest_straight_side(real_polygon)
    assert side_count == 4, f"Expected 4 sides (rectangle), got {side_count}"
    assert shortest_side == pytest.approx(73.0, abs=0.1)
```

### Step 6: Run validation commands

Execute all validation commands to ensure the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py::TestCalculateShortestStraightSide -v` - Run all tests in the affected test class to validate fix and ensure no regressions
- `uv run pytest app/tests/core/test_geometry.py -v` - Run full geometry test suite for broader regression check
- `uv run pytest app/tests/ -v --tb=short` - Run complete test suite to ensure no side effects
- `uv run mypy app/core/geometry.py` - Type check the modified file
- `uv run ruff check app/core/geometry.py` - Lint check the modified file

## Notes
- The fix is minimal and surgical - only affects the `calculate_shortest_straight_side()` function
- No new dependencies required
- The existing `angles_collinear()` helper function (lines 137-140) handles angle wraparound correctly and will be reused
- All existing tests in `TestCalculateShortestStraightSide` must continue to pass - they exercise cases where wraparound merging is not needed
- The fix correctly handles edge cases:
  - Fewer than 2 sides: No wraparound check needed
  - First and last sides not collinear: No merge performed
  - First and last sides ARE collinear: Merge and decrement count
