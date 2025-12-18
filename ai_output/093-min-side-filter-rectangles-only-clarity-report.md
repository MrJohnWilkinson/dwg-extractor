# Min Side Filter: Rectangles-Only Solution Clarity Report

## Executive Summary

The user's proposed solution is correct and addresses the root cause: the Min Side Filter should only apply to 4-sided rectangles (after collinear edge merging). This prevents complex polygons with small incidental segments from being incorrectly filtered out. The implementation requires modifying `calculate_shortest_straight_side()` to return both the shortest side and the side count, then conditioning the filter on side_count == 4.

## Table Summary

| Aspect | Current Behavior | Proposed Behavior |
|--------|------------------|-------------------|
| Filter Scope | All polygons | Only 4-sided rectangles |
| Complex Polygons | Filtered if ANY side < threshold | Never filtered by this filter |
| 17-vertex polygon at X=13427 | REJECTED (17-unit segment) | PASSED (not a rectangle) |
| User Expectation | trim_right = 894 | trim_right = 894 (achieved) |
| Purpose Clarity | Ambiguous | "Filters thin rectangles only" |

## Relevant Files

- **app/core/geometry.py:87-164** - `calculate_shortest_straight_side()` function that needs modification to also return side count
- **app/core/geometry.py:1746-1762** - `_detect_content_zone()` where min_side_filter is applied; needs to check side count
- **app/main.py:479-505** - Main window UI for Min Side Filter checkbox and entry
- **app/core/settings_window.py:698-714** - Advanced Settings display of Min Side Filter description
- **app/core/constants.py** - Default filter values

## Why the User's Solution Is Correct

### The Root Cause
The polygon at X=13427 has 17 vertices and 17 straight sides (after collinear merging). One of these sides is only 17 units - a small notch in an otherwise large polygon. This notch causes the Min Side Filter (set to 101) to reject the entire polygon, even though the polygon's "main" dimensions are substantial (914 x 505).

### Why Rectangles-Only Works
1. **True rectangles** have exactly 4 straight sides after collinear merging
2. **Complex polygons** (notches, L-shapes, irregular shapes) have 5+ sides
3. The Min Side Filter's purpose is to remove "thin slivers" - which are always rectangular
4. Applying the filter to complex polygons is semantically incorrect and produces unexpected results

### Alternative Approaches Considered

| Approach | Pros | Cons |
|----------|------|------|
| Rectangle-only filter | Precise, predictable | Requires code changes |
| Lower filter threshold | Quick workaround | May still miss edge cases, catches thin rectangles |
| Disable filter entirely | Simple | Loses ability to filter slivers |
| Top-N sides average | More sophisticated | Complex to explain, unpredictable |

**Rectangle-only is the cleanest solution** - it matches user mental model and has zero ambiguity.

## Implementation Steps (100% Completion)

### Step 1: Modify `calculate_shortest_straight_side()` Return Type

**File:** `app/core/geometry.py:87-164`

Change return type from `float` to `tuple[float, int]` where the tuple is `(shortest_side_length, side_count)`.

```python
# Before
def calculate_shortest_straight_side(polygon: Polygon, ...) -> float:
    ...
    return min(straight_sides) if straight_sides else 0.0

# After
def calculate_shortest_straight_side(polygon: Polygon, ...) -> tuple[float, int]:
    ...
    if not straight_sides:
        return (0.0, 0)
    return (min(straight_sides), len(straight_sides))
```

### Step 2: Update All Call Sites of `calculate_shortest_straight_side()`

**File:** `app/core/geometry.py:1749-1755`

Modify the filter to only apply to 4-sided polygons:

```python
# Before
if min_side_filter > 0:
    all_shapes = [
        s for s in all_shapes
        if calculate_shortest_straight_side(s) >= min_side_filter
    ]

# After
if min_side_filter > 0:
    def passes_min_side_filter(polygon: Polygon) -> bool:
        shortest_side, side_count = calculate_shortest_straight_side(polygon)
        # Only filter 4-sided rectangles; pass all complex polygons
        if side_count != 4:
            return True
        return shortest_side >= min_side_filter

    all_shapes = [s for s in all_shapes if passes_min_side_filter(s)]
```

### Step 3: Search for Other Call Sites

Run: `grep -rn "calculate_shortest_straight_side" app/`

Update any additional call sites to handle the new tuple return type. May need to use `result[0]` or destructure.

### Step 4: Update Main Window UI Description

**File:** `app/main.py:483-489`

Add clarifying tooltip or modify label:

```python
self.min_side_filter_checkbox = ctk.CTkCheckBox(
    min_side_frame,
    text="Min Side (Rectangles Only)",  # Clarified label
    variable=self.min_side_filter_var,
    ...
)
```

### Step 5: Update Settings Window UI Description

**File:** `app/core/settings_window.py:698-714`

Update the description text:

```python
self._create_setting_row(
    scroll_frame,
    "min_side_filter_enabled",
    "Min Side Filter (Rectangles Only)",  # Updated label
    "Filters out 4-sided rectangles with shortest side below threshold. "
    "Complex polygons (5+ sides) are not affected by this filter.",  # Clearer description
    readonly=True,
)

self._create_setting_row(
    scroll_frame,
    "min_side_filter_amount",
    "Min Side Filter Amount",
    "Minimum side length for rectangles in drawing units. "
    "Only applies to 4-sided polygons (rectangles).",  # Clearer description
    readonly=True,
)
```

### Step 6: Update Tests

**File:** `app/tests/core/test_geometry.py` (or appropriate test file)

Add tests for:
1. `calculate_shortest_straight_side()` returns correct tuple
2. Rectangles (4-sided) are filtered when side < threshold
3. Complex polygons (5+ sides) are NOT filtered even if they have short segments

### Step 7: Update Docstrings

Update the docstring for `calculate_shortest_straight_side()`:

```python
def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> tuple[float, int]:
    """
    Calculate the shortest straight side and total side count of a polygon.

    Returns:
        Tuple of (shortest_side_length, side_count) where:
        - shortest_side_length: Length of shortest merged side in DXF units
        - side_count: Total number of straight sides after collinear merging

        For rectangles, side_count will be 4.
        For complex shapes, side_count will be > 4.
    """
```

### Step 8: Run Full Test Suite

```bash
uv run pytest app/tests/ -v
```

### Step 9: Verify with Original Problem Case

Test with the DXF file from the analysis to confirm:
- Polygon at X=13427 now passes filter (17 sides != 4)
- Content zone max_x becomes 13427
- Suggested trim_right becomes 894

## Simple List Summary

- Modify `calculate_shortest_straight_side()` to return `(shortest_side, side_count)` tuple
- Update filter logic to only apply to polygons where `side_count == 4`
- Update all call sites to handle the new return type
- Change UI label to "Min Side (Rectangles Only)"
- Update descriptions to explain "only applies to 4-sided rectangles"
- Add tests for rectangle vs complex polygon filtering
- Verify fix with original problem DXF file
