# ARC Bounding Box Implementation Plan

## Executive Summary

Both statements are **VERIFIED AS ACCURATE**. The Block Suggested Trim Left value of 779 is caused by `_get_block_bounding_box()` using full-circle extents for ARC entities (center ± radius), while content zone detection uses actual flattened arc geometry. This report provides an implementation plan to calculate accurate angular-extent bounding boxes for ARCs.

## Table Summary

| Item | Current Behavior | Proposed Behavior |
|------|------------------|-------------------|
| ARC bbox calculation | `center ± radius` (full circle) | Angular-extent based on start/end angles |
| Example ARC (270°-356°, r=779) | bbox x: [-779, 779] | bbox x: [0, 777] |
| Trim Left for test block | 779 | ~0 (matches content zone) |
| Performance impact | O(1) | O(1) - still constant time |
| Breaking change | N/A | Yes - existing tests need updates |

## Relevant Files

- **`app/core/geometry.py:242-250`** - Current ARC bbox implementation using full circle extents. This is the PRIMARY file to modify.

- **`app/tests/core/test_geometry.py:84-99`** - Tests for `_get_block_bounding_box()` with ARCs that currently expect full-circle extents. These tests will need updates.

- **`app/tests/core/extractor/test_extractor_core.py:571-586`** - Additional ARC bbox tests expecting full-circle behavior.

- **`app/tests/assets/circles_arcs_points.dxf`** - Test asset file containing TEST_ARCS block used in tests.

## Statement Verification

### Statement 1: VERIFIED
> "The Block Suggested Trim Left value of 779...is caused by a discrepancy between two different bounding box calculations: the block bounding box uses full circle extents for ARC entities (simplified approximation), while the content zone detection uses actual flattened arc geometry."

**Evidence:**
- `geometry.py:242-250` shows ARC bbox uses `center.x - radius` and `center.x + radius`
- `geometry.py:577-601` shows `_extract_arc_edges()` uses `entity.flattening()` for actual geometry
- This creates the exact discrepancy described

### Statement 2: VERIFIED
> "The Block Suggested Trim Left value of 779...is caused by an ARC entity centered at x≈0 with radius=779 that extends the block's bounding box to x=-779. The surviving polygons (after min_area_filter=50000) start at x=0, so trim_left = 0 - (-779) = 779. The value 779 equals the ARC radius, not a vertical intersection point."

**Evidence:**
- ARC center at x≈0, radius=779 → block_min_x = 0 - 779 = -779
- Surviving polygons start at x=0 (flattened arc starts at 270° = x=0)
- trim_left = cz_min_x - block_min_x = 0 - (-779) = 779

## Algorithm for Accurate ARC Bounding Box

### Mathematical Foundation

For an arc with center (cx, cy), radius r, start_angle θ₁, and end_angle θ₂:

1. **Start point**: (cx + r·cos(θ₁), cy + r·sin(θ₁))
2. **End point**: (cx + r·cos(θ₂), cy + r·sin(θ₂))
3. **Cardinal extremes** (only if within arc span):
   - Right (0°): (cx + r, cy) → contributes to max_x
   - Top (90°): (cx, cy + r) → contributes to max_y
   - Left (180°): (cx - r, cy) → contributes to min_x
   - Bottom (270°): (cx, cy - r) → contributes to min_y

### Pseudocode

```python
def _get_arc_bounding_box(
    center_x: float,
    center_y: float,
    radius: float,
    start_angle: float,  # in degrees
    end_angle: float,    # in degrees
) -> tuple[float, float, float, float]:
    """Calculate accurate bounding box for an arc.

    Args:
        center_x, center_y: Arc center coordinates
        radius: Arc radius
        start_angle: Start angle in degrees (CCW from +X axis)
        end_angle: End angle in degrees (CCW from +X axis)

    Returns:
        Tuple of (min_x, min_y, max_x, max_y)
    """
    import math

    # Normalize angles to 0-360 range
    start = start_angle % 360
    end = end_angle % 360

    # Handle wrap-around (e.g., 350° to 10°)
    if end <= start:
        end += 360

    # Calculate start and end points
    rad_start = math.radians(start)
    rad_end = math.radians(end_angle % 360)

    start_x = center_x + radius * math.cos(rad_start)
    start_y = center_y + radius * math.sin(rad_start)
    end_x = center_x + radius * math.cos(rad_end)
    end_y = center_y + radius * math.sin(rad_end)

    # Initialize bounds with start and end points
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)

    # Check each cardinal direction (0°, 90°, 180°, 270°)
    def angle_in_arc(angle: float) -> bool:
        """Check if angle is within the arc span."""
        a = angle % 360
        if end <= 360:
            return start <= a <= end
        else:
            # Wrap-around case
            return a >= start or a <= (end % 360)

    # Right (0°) - max_x
    if angle_in_arc(0):
        max_x = center_x + radius

    # Top (90°) - max_y
    if angle_in_arc(90):
        max_y = center_y + radius

    # Left (180°) - min_x
    if angle_in_arc(180):
        min_x = center_x - radius

    # Bottom (270°) - min_y
    if angle_in_arc(270):
        min_y = center_y - radius

    return (min_x, min_y, max_x, max_y)
```

## Implementation Plan

### Step 1: Add Helper Function
Add `_get_arc_bounding_box()` as a new private function in `geometry.py` (insert before `_get_block_bounding_box`).

**Location**: `app/core/geometry.py` around line 178

```python
def _get_arc_bounding_box(
    center_x: float,
    center_y: float,
    radius: float,
    start_angle: float,
    end_angle: float,
) -> tuple[float, float, float, float]:
    """Calculate accurate bounding box for an arc based on angular extent.

    Unlike full-circle extents, this calculates the actual min/max coordinates
    by considering only the arc's start point, end point, and any cardinal
    directions (0°, 90°, 180°, 270°) that fall within the arc span.

    Args:
        center_x: X-coordinate of arc center
        center_y: Y-coordinate of arc center
        radius: Arc radius
        start_angle: Start angle in degrees (counter-clockwise from +X axis)
        end_angle: End angle in degrees (counter-clockwise from +X axis)

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the arc's bounding box.

    Examples:
        >>> _get_arc_bounding_box(0, 0, 100, 270, 356)  # Arc from bottom to near-right
        (0.0, -100.0, 99.76..., 0.0)  # Doesn't include left extent
    """
    # Normalize start angle to [0, 360)
    start = start_angle % 360
    end = end_angle % 360

    # Calculate actual start and end points
    rad_start = math.radians(start)
    rad_end = math.radians(end)

    start_x = center_x + radius * math.cos(rad_start)
    start_y = center_y + radius * math.sin(rad_start)
    end_x = center_x + radius * math.cos(rad_end)
    end_y = center_y + radius * math.sin(rad_end)

    # Initialize bounds with start and end points
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)

    # Determine the arc span, handling wrap-around
    # Arc goes CCW from start to end
    if end < start:
        # Wrap-around case (e.g., 350° to 10° spans 0°)
        span_end = end + 360
    else:
        span_end = end

    def angle_in_span(angle: float) -> bool:
        """Check if a cardinal angle falls within the arc span."""
        # Normalize angle to check
        a = angle % 360
        # Check both the angle and angle+360 for wrap-around
        return start <= a <= span_end or start <= (a + 360) <= span_end

    # Check cardinal directions for extremes
    # 0° (right) - affects max_x
    if angle_in_span(0):
        max_x = max(max_x, center_x + radius)

    # 90° (top) - affects max_y
    if angle_in_span(90):
        max_y = max(max_y, center_y + radius)

    # 180° (left) - affects min_x
    if angle_in_span(180):
        min_x = min(min_x, center_x - radius)

    # 270° (bottom) - affects min_y
    if angle_in_span(270):
        min_y = min(min_y, center_y - radius)

    return (min_x, min_y, max_x, max_y)
```

### Step 2: Update _get_block_bounding_box

Replace the ARC handling in `_get_block_bounding_box()` (lines 242-250):

**Before:**
```python
elif entity_type == "ARC":
    center = entity.dxf.center
    radius = entity.dxf.radius
    # Simplified bounding box for arcs (use full circle extents)
    min_x = min(min_x, center.x - radius)
    max_x = max(max_x, center.x + radius)
    min_y = min(min_y, center.y - radius)
    max_y = max(max_y, center.y + radius)
    has_geometry = True
```

**After:**
```python
elif entity_type == "ARC":
    center = entity.dxf.center
    radius = entity.dxf.radius
    start_angle = entity.dxf.start_angle
    end_angle = entity.dxf.end_angle
    # Calculate accurate bounding box based on angular extent
    arc_min_x, arc_min_y, arc_max_x, arc_max_y = _get_arc_bounding_box(
        center.x, center.y, radius, start_angle, end_angle
    )
    min_x = min(min_x, arc_min_x)
    max_x = max(max_x, arc_max_x)
    min_y = min(min_y, arc_min_y)
    max_y = max(max_y, arc_max_y)
    has_geometry = True
```

### Step 3: Add Unit Tests for _get_arc_bounding_box

Add new test class in `app/tests/core/test_geometry.py`:

```python
class TestArcBoundingBox:
    """Test suite for _get_arc_bounding_box function."""

    def test_quarter_arc_first_quadrant(self) -> None:
        """Arc from 0° to 90° (first quadrant)."""
        bbox = _get_arc_bounding_box(0, 0, 100, 0, 90)
        assert bbox[0] == pytest.approx(0.0, abs=0.01)   # min_x at 90°
        assert bbox[1] == pytest.approx(0.0, abs=0.01)   # min_y at 0°
        assert bbox[2] == pytest.approx(100.0, abs=0.01) # max_x at 0°
        assert bbox[3] == pytest.approx(100.0, abs=0.01) # max_y at 90°

    def test_arc_270_to_356(self) -> None:
        """Arc from 270° to 356° (the problematic case from issue)."""
        bbox = _get_arc_bounding_box(0, -953, 779, 270, 356.1)
        # Should NOT include left extent (-779)
        assert bbox[0] > -100  # min_x should be near 0, not -779
        assert bbox[1] == pytest.approx(-953 - 779, abs=1)  # 270° is at bottom
        assert bbox[2] == pytest.approx(779 * math.cos(math.radians(356.1)), abs=1)
        assert bbox[3] == pytest.approx(-953 + 779 * math.sin(math.radians(356.1)), abs=1)

    def test_semicircle_top(self) -> None:
        """Arc from 0° to 180° (top semicircle)."""
        bbox = _get_arc_bounding_box(50, 50, 25, 0, 180)
        assert bbox[0] == pytest.approx(25.0, abs=0.01)  # min_x at 180°
        assert bbox[1] == pytest.approx(50.0, abs=0.01)  # min_y at 0° and 180°
        assert bbox[2] == pytest.approx(75.0, abs=0.01)  # max_x at 0°
        assert bbox[3] == pytest.approx(75.0, abs=0.01)  # max_y at 90°

    def test_wrap_around_arc(self) -> None:
        """Arc from 350° to 10° (crosses 0°)."""
        bbox = _get_arc_bounding_box(0, 0, 100, 350, 10)
        # Should include the 0° cardinal point (max_x)
        assert bbox[2] == pytest.approx(100.0, abs=0.01)  # max_x at 0°

    def test_full_circle_arc(self) -> None:
        """Arc from 0° to 360° should equal full circle."""
        bbox = _get_arc_bounding_box(100, 100, 50, 0, 360)
        assert bbox == pytest.approx((50.0, 50.0, 150.0, 150.0), abs=0.01)
```

### Step 4: Update Existing Tests

Update `test_bounding_box_with_arcs` in `test_geometry.py` to expect accurate arc bounds:

**Before:**
```python
def test_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (simplified full-circle extents)."""
    # ... expects full-circle extents
    assert bbox[0] == 50.0   # min_x
```

**After:**
```python
def test_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (accurate angular extents)."""
    # ... expects actual arc extents based on angles
    # Need to calculate expected values based on actual arc angles in test file
```

## Test Verification

After implementation, run:
```bash
uv run pytest app/tests/core/test_geometry.py -v -k "arc or Arc"
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/core/extractor/ -v
```

## Recommendations

1. **Implement the helper function first** - Add `_get_arc_bounding_box()` with comprehensive tests before modifying the main function.

2. **Update tests incrementally** - After verifying the helper works correctly, update `_get_block_bounding_box()` and fix failing tests one by one.

3. **Consider backwards compatibility** - If external code depends on current behavior, consider adding a parameter to toggle between full-circle and accurate arc bounds.

4. **Document the change** - Update docstrings to reflect that ARC bounding boxes are now calculated using angular extents rather than full-circle approximation.

## Next Steps

1. Implement `_get_arc_bounding_box()` helper function
2. Add unit tests for the helper function
3. Update `_get_block_bounding_box()` to use the helper
4. Update existing tests with correct expected values
5. Verify the 779 trim issue is resolved with test DXF file
