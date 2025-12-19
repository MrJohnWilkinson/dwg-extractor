# Collinear Merging Wraparound Fix Plan

## Executive Summary

The `calculate_shortest_straight_side()` function in `geometry.py` fails to correctly count polygon sides when the starting vertex (V0) lies in the middle of a collinear edge sequence. The algorithm processes edges linearly without checking if the last merged side is collinear with the first. This causes a 4-sided rectangle to be detected as 5-sided, bypassing the min_side_filter.

## Table Summary

| Step | Action | File | Lines |
|------|--------|------|-------|
| 1 | Add wrap-around merge check after initial pass | `geometry.py` | 169 |
| 2 | Merge first and last sides if collinear | `geometry.py` | 169 |
| 3 | Add test for wraparound collinear merging | `test_geometry.py` | new |
| 4 | Add test for real-world case from issue | `test_geometry.py` | new |

## Relevant Files

- `app/core/geometry.py:87-171` - The `calculate_shortest_straight_side()` function containing the collinear merging algorithm that needs fixing
- `app/tests/core/test_geometry.py:1762-1952` - Existing test class `TestCalculateShortestStraightSide` with 12 tests, none covering wraparound

## Problem Analysis

### Current Algorithm Behavior

The algorithm at `geometry.py:145-167`:
1. Starts at vertex 0, builds the first merged side
2. Continues linearly through all edges
3. Never checks if the last side should merge with the first side

### Specific Example (from issue)

Polygon vertices:
```
V0: (24953.75, 13351.94)  ← Algorithm starts here (middle of bottom edge!)
V1: (24172.75, 13351.94)
V2: (23391.75, 13351.94)
V3: (23391.75, 13424.94)
V4: (25734.75, 13424.94)
V5: (25734.75, 13351.94)
```

**Current result**: 5 sides
- Side 1: V0→V2 (1562 units, edges 0+1 merged)
- Side 2: V2→V3 (73 units)
- Side 3: V3→V4 (2343 units)
- Side 4: V4→V5 (73 units)
- Side 5: V5→V0 (781 units) ← NOT merged with Side 1!

**Expected result**: 4 sides
- Bottom: V5→V0→V1→V2 (2343 units total) ← should all merge
- Left: V2→V3 (73 units)
- Top: V3→V4 (2343 units)
- Right: V4→V5 (73 units)

## Implementation Plan

### Step 1: Add Wraparound Merge Logic

After the main while loop at `geometry.py:167`, add logic to check if the first and last sides are collinear and should be merged:

```python
# After line 167, before line 169
# Wraparound check: merge first and last sides if collinear
if len(straight_sides) >= 2:
    # Get endpoints for first and last sides to calculate their angles
    # First side: from vertices[0] to some vertices[j1]
    # Last side: from vertices[k] to vertices[-1] = vertices[0]
    # Need to track side angles during initial pass
```

**Key insight**: The current algorithm discards angle information after computing side lengths. We need to preserve the angle of each merged side to enable the wraparound check.

### Step 2: Modify Algorithm to Track Side Angles

Modify the algorithm to store `(length, angle)` tuples instead of just lengths:

```python
straight_sides: list[tuple[float, float]] = []  # (length, angle)

# In the merging loop, store both:
if side_length > 1e-9:
    straight_sides.append((side_length, current_angle))

# After the loop:
if len(straight_sides) >= 2:
    first_length, first_angle = straight_sides[0]
    last_length, last_angle = straight_sides[-1]
    if angles_collinear(first_angle, last_angle, angle_tolerance):
        # Merge: combine lengths, keep first angle
        merged_length = first_length + last_length
        straight_sides[0] = (merged_length, first_angle)
        straight_sides.pop()

# Extract just lengths for final calculation
side_lengths = [length for length, _ in straight_sides]
if not side_lengths:
    return (0.0, 0)
return (min(side_lengths), len(side_lengths))
```

### Step 3: Add Test - Basic Wraparound

Add test to `TestCalculateShortestStraightSide` class:

```python
def test_collinear_edge_merging_wraparound(self) -> None:
    """Test that first and last edges merge when collinear (wraparound)."""
    # Rectangle where V0 is in middle of bottom edge:
    # V0 and V1 on bottom, V5 also on bottom continuing back to V0
    wraparound_rect: list[tuple[float, float]] = [
        (50.0, 0.0),   # V0 - middle of bottom edge
        (100.0, 0.0),  # V1 - right corner of bottom
        (100.0, 50.0), # V2 - right corner of top
        (0.0, 50.0),   # V3 - left corner of top
        (0.0, 0.0),    # V4 - left corner of bottom
    ]
    # Without wraparound: V0→V1 (50), V1→V2 (50), V2→V3 (100), V3→V4 (50), V4→V0 (50)
    # With wraparound: V4→V0→V1 should merge to 100, giving 4 sides
    shortest_side, side_count = calculate_shortest_straight_side(wraparound_rect)
    assert shortest_side == pytest.approx(50.0)
    assert side_count == 4  # NOT 5
```

### Step 4: Add Test - Real-World Case

Add test using exact values from the issue:

```python
def test_collinear_merging_real_world_case(self) -> None:
    """Test real-world polygon that was detected as 5-sided instead of 4."""
    # From issue: block at Y=13424.94 with bottom edge split across V0
    real_polygon: list[tuple[float, float]] = [
        (24953.75, 13351.94),  # V0 - middle of bottom edge
        (24172.75, 13351.94),  # V1
        (23391.75, 13351.94),  # V2
        (23391.75, 13424.94),  # V3
        (25734.75, 13424.94),  # V4
        (25734.75, 13351.94),  # V5
    ]
    shortest_side, side_count = calculate_shortest_straight_side(real_polygon)
    assert shortest_side == pytest.approx(73.0)  # Vertical sides
    assert side_count == 4  # Rectangle, not 5-sided
```

## Verification Steps

After implementation:

1. **Run existing tests** - ensure no regressions:
   ```bash
   uv run pytest app/tests/core/test_geometry.py::TestCalculateShortestStraightSide -v
   ```

2. **Run new tests** - verify wraparound works:
   ```bash
   uv run pytest app/tests/core/test_geometry.py::TestCalculateShortestStraightSide::test_collinear_edge_merging_wraparound -v
   ```

3. **Integration test** - verify min_side_filter now correctly filters the polygon

## Out of Scope

Per user direction, these options are explicitly NOT being implemented:
- Apply min_side_filter to all polygons (remove side_count != 4 check)
- Add "strict side filter" user option

## Simple List Summary

- **Problem**: Collinear merging doesn't wrap around - last edge not merged with first
- **Root cause**: Linear single-pass algorithm in `calculate_shortest_straight_side()`
- **Fix**: After initial pass, check if first/last sides are collinear and merge them
- **Change location**: `app/core/geometry.py:145-171`
- **Tests needed**: Add 2 new tests for wraparound cases
- **Risk**: Low - isolated change with clear test coverage
