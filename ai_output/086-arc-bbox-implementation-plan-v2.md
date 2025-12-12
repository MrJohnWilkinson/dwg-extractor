# ARC Bounding Box Implementation Plan v2

## Executive Summary

This plan provides a streamlined, step-by-step implementation for accurate ARC bounding box calculations. Unlike the previous plan, this version assumes full implementation without backwards compatibility concerns, executed in logical sequence as a single cohesive change.

## Table Summary

| Step | Action | File | Lines Affected |
|------|--------|------|----------------|
| 1 | Add `_get_arc_bounding_box()` helper | `geometry.py` | Insert ~45 lines before `_get_block_bounding_box` |
| 2 | Update ARC handling in `_get_block_bounding_box()` | `geometry.py` | Replace lines 242-250 |
| 3 | Add `TestArcBoundingBox` test class | `test_geometry.py` | Add new test class |
| 4 | Update `test_bounding_box_with_arcs` | `test_geometry.py` | Update expected values (lines 84-99) |
| 5 | Update `test_get_block_bounding_box_with_arcs` | `test_extractor_core.py` | Update expected values (lines 571-586) |
| 6 | Run tests and verify | - | - |

## Relevant Files

- **`app/core/geometry.py:242-250`** - Current ARC bbox implementation using full circle extents. Primary file to modify.
- **`app/tests/core/test_geometry.py:84-99`** - `test_bounding_box_with_arcs` expecting full-circle extents.
- **`app/tests/core/extractor/test_extractor_core.py:571-586`** - Duplicate ARC bbox test in extractor tests.
- **`app/tests/assets/circles_arcs_points.dxf`** - Test asset with TEST_ARCS block.
- **`app/tests/assets/create_circles_arcs_points.py`** - Source script showing arc definitions.

## Test Arc Definitions (from circles_arcs_points.dxf)

```python
# Arc 1: center=(100, 100), radius=50, start_angle=0, end_angle=90
# Arc 2: center=(200, 150), radius=40, start_angle=45, end_angle=180
# Arc 3: center=(150, 50), radius=30, start_angle=270, end_angle=360
```

## Expected Bbox Values After Implementation

| Arc | Center | Radius | Angles | Old Bbox (full circle) | New Bbox (accurate) |
|-----|--------|--------|--------|------------------------|---------------------|
| 1 | (100, 100) | 50 | 0°→90° | (50, 50, 150, 150) | (100, 100, 150, 150) |
| 2 | (200, 150) | 40 | 45°→180° | (160, 110, 240, 190) | (160, 150, ~228.3, 190) |
| 3 | (150, 50) | 30 | 270°→360° | (120, 20, 180, 80) | (150, 20, 180, 50) |
| **Combined** | - | - | - | **(50, 20, 240, 190)** | **(100, 20, ~228.3, 190)** |

## Implementation Steps

### Step 1: Add `_get_arc_bounding_box()` Helper Function

**Location:** `app/core/geometry.py` - Insert before `_get_block_bounding_box()` (around line 178)

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

    # Determine the arc span, handling wrap-around (CCW from start to end)
    if end <= start:
        span_end = end + 360
    else:
        span_end = end

    def angle_in_span(angle: float) -> bool:
        """Check if a cardinal angle falls within the arc span."""
        a = angle % 360
        return start <= a <= span_end or start <= (a + 360) <= span_end

    # Check cardinal directions for extremes
    if angle_in_span(0):     # 0° (right) - affects max_x
        max_x = max(max_x, center_x + radius)
    if angle_in_span(90):    # 90° (top) - affects max_y
        max_y = max(max_y, center_y + radius)
    if angle_in_span(180):   # 180° (left) - affects min_x
        min_x = min(min_x, center_x - radius)
    if angle_in_span(270):   # 270° (bottom) - affects min_y
        min_y = min(min_y, center_y - radius)

    return (min_x, min_y, max_x, max_y)
```

### Step 2: Update `_get_block_bounding_box()` ARC Handling

**Location:** `app/core/geometry.py:242-250`

**Replace:**
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

**With:**
```python
elif entity_type == "ARC":
    center = entity.dxf.center
    radius = entity.dxf.radius
    start_angle = entity.dxf.start_angle
    end_angle = entity.dxf.end_angle
    arc_min_x, arc_min_y, arc_max_x, arc_max_y = _get_arc_bounding_box(
        center.x, center.y, radius, start_angle, end_angle
    )
    min_x = min(min_x, arc_min_x)
    max_x = max(max_x, arc_max_x)
    min_y = min(min_y, arc_min_y)
    max_y = max(max_y, arc_max_y)
    has_geometry = True
```

### Step 3: Add `TestArcBoundingBox` Test Class

**Location:** `app/tests/core/test_geometry.py` - Add new test class

```python
class TestArcBoundingBox:
    """Test suite for _get_arc_bounding_box function."""

    def test_quarter_arc_first_quadrant(self) -> None:
        """Arc from 0° to 90° (first quadrant)."""
        bbox = _get_arc_bounding_box(0, 0, 100, 0, 90)
        assert bbox[0] == pytest.approx(0.0, abs=0.01)    # min_x at 90°
        assert bbox[1] == pytest.approx(0.0, abs=0.01)    # min_y at 0°
        assert bbox[2] == pytest.approx(100.0, abs=0.01)  # max_x at 0°
        assert bbox[3] == pytest.approx(100.0, abs=0.01)  # max_y at 90°

    def test_quarter_arc_fourth_quadrant(self) -> None:
        """Arc from 270° to 360° (fourth quadrant)."""
        bbox = _get_arc_bounding_box(0, 0, 100, 270, 360)
        assert bbox[0] == pytest.approx(0.0, abs=0.01)     # min_x at 270°
        assert bbox[1] == pytest.approx(-100.0, abs=0.01)  # min_y at 270°
        assert bbox[2] == pytest.approx(100.0, abs=0.01)   # max_x at 360°
        assert bbox[3] == pytest.approx(0.0, abs=0.01)     # max_y at 360°

    def test_arc_45_to_180(self) -> None:
        """Arc from 45° to 180° (spans second quadrant)."""
        bbox = _get_arc_bounding_box(200, 150, 40, 45, 180)
        # Start: (200 + 40*cos(45°), 150 + 40*sin(45°)) ≈ (228.28, 178.28)
        # End: (200 - 40, 150) = (160, 150)
        # Cardinals in span: 90° → (200, 190), 180° → (160, 150)
        assert bbox[0] == pytest.approx(160.0, abs=0.01)   # min_x at 180°
        assert bbox[1] == pytest.approx(150.0, abs=0.01)   # min_y (end point)
        assert bbox[2] == pytest.approx(228.28, abs=0.1)   # max_x (start point)
        assert bbox[3] == pytest.approx(190.0, abs=0.01)   # max_y at 90°

    def test_semicircle_top(self) -> None:
        """Arc from 0° to 180° (top semicircle)."""
        bbox = _get_arc_bounding_box(50, 50, 25, 0, 180)
        assert bbox[0] == pytest.approx(25.0, abs=0.01)   # min_x at 180°
        assert bbox[1] == pytest.approx(50.0, abs=0.01)   # min_y at 0° and 180°
        assert bbox[2] == pytest.approx(75.0, abs=0.01)   # max_x at 0°
        assert bbox[3] == pytest.approx(75.0, abs=0.01)   # max_y at 90°

    def test_wrap_around_arc(self) -> None:
        """Arc from 350° to 10° (crosses 0°)."""
        bbox = _get_arc_bounding_box(0, 0, 100, 350, 10)
        # Should include the 0° cardinal point (max_x)
        assert bbox[2] == pytest.approx(100.0, abs=0.01)  # max_x at 0°

    def test_full_circle_arc(self) -> None:
        """Arc from 0° to 360° should equal full circle."""
        bbox = _get_arc_bounding_box(100, 100, 50, 0, 360)
        assert bbox == pytest.approx((50.0, 50.0, 150.0, 150.0), abs=0.01)

    def test_arc_270_to_356_problematic_case(self) -> None:
        """Arc from 270° to 356° - the original issue case."""
        # This arc should NOT include left extent (-779)
        bbox = _get_arc_bounding_box(0, -953, 779, 270, 356.1)
        assert bbox[0] > -100  # min_x should be near 0, not -779
        assert bbox[1] == pytest.approx(-953 - 779, abs=1)  # 270° is at bottom
```

### Step 4: Update `test_bounding_box_with_arcs` in test_geometry.py

**Location:** `app/tests/core/test_geometry.py:84-99`

**Replace:**
```python
def test_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (simplified full-circle extents)."""
    doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
    block = doc.blocks.get("TEST_ARCS")

    bbox = _get_block_bounding_box(block)

    # Block contains arcs (simplified to full circle extents):
    # Arc 1: center=(100, 100), radius=50 -> bbox=(50, 50, 150, 150)
    # Arc 2: center=(200, 150), radius=40 -> bbox=(160, 110, 240, 190)
    # Arc 3: center=(150, 50), radius=30 -> bbox=(120, 20, 180, 80)
    # Overall bbox: (50, 20, 240, 190)
    assert bbox[0] == 50.0  # min_x
    assert bbox[1] == 20.0  # min_y
    assert bbox[2] == 240.0  # max_x
    assert bbox[3] == 190.0  # max_y
```

**With:**
```python
def test_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (accurate angular extents)."""
    doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
    block = doc.blocks.get("TEST_ARCS")

    bbox = _get_block_bounding_box(block)

    # Block contains arcs with accurate angular-extent bounding boxes:
    # Arc 1: center=(100, 100), r=50, 0°→90° → bbox=(100, 100, 150, 150)
    # Arc 2: center=(200, 150), r=40, 45°→180° → bbox=(160, 150, ~228.3, 190)
    # Arc 3: center=(150, 50), r=30, 270°→360° → bbox=(150, 20, 180, 50)
    # Overall bbox: (100, 20, ~228.3, 190)
    assert bbox[0] == pytest.approx(100.0, abs=0.01)  # min_x (Arc 1 end point)
    assert bbox[1] == pytest.approx(20.0, abs=0.01)   # min_y (Arc 3 at 270°)
    assert bbox[2] == pytest.approx(228.28, abs=0.1)  # max_x (Arc 2 start point)
    assert bbox[3] == pytest.approx(190.0, abs=0.01)  # max_y (Arc 2 at 90°)
```

### Step 5: Update `test_get_block_bounding_box_with_arcs` in test_extractor_core.py

**Location:** `app/tests/core/extractor/test_extractor_core.py:571-586`

**Replace:**
```python
def test_get_block_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (simplified full-circle extents)."""
    doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
    block = doc.blocks.get("TEST_ARCS")

    bbox = _get_block_bounding_box(block)

    # Block contains arcs (simplified to full circle extents):
    # Arc 1: center=(100, 100), radius=50 -> bbox=(50, 50, 150, 150)
    # Arc 2: center=(200, 150), radius=40 -> bbox=(160, 110, 240, 190)
    # Arc 3: center=(150, 50), radius=30 -> bbox=(120, 20, 180, 80)
    # Overall bbox: (50, 20, 240, 190)
    assert bbox[0] == 50.0  # min_x
    assert bbox[1] == 20.0  # min_y
    assert bbox[2] == 240.0  # max_x
    assert bbox[3] == 190.0  # max_y
```

**With:**
```python
def test_get_block_bounding_box_with_arcs(self) -> None:
    """Test bounding box extraction for blocks with ARC entities (accurate angular extents)."""
    doc = ezdxf.readfile("app/tests/assets/circles_arcs_points.dxf")
    block = doc.blocks.get("TEST_ARCS")

    bbox = _get_block_bounding_box(block)

    # Block contains arcs with accurate angular-extent bounding boxes:
    # Arc 1: center=(100, 100), r=50, 0°→90° → bbox=(100, 100, 150, 150)
    # Arc 2: center=(200, 150), r=40, 45°→180° → bbox=(160, 150, ~228.3, 190)
    # Arc 3: center=(150, 50), r=30, 270°→360° → bbox=(150, 20, 180, 50)
    # Overall bbox: (100, 20, ~228.3, 190)
    assert bbox[0] == pytest.approx(100.0, abs=0.01)  # min_x (Arc 1 end point)
    assert bbox[1] == pytest.approx(20.0, abs=0.01)   # min_y (Arc 3 at 270°)
    assert bbox[2] == pytest.approx(228.28, abs=0.1)  # max_x (Arc 2 start point)
    assert bbox[3] == pytest.approx(190.0, abs=0.01)  # max_y (Arc 2 at 90°)
```

### Step 6: Run Tests and Verify

```bash
# Run ARC-related geometry tests
uv run pytest app/tests/core/test_geometry.py -v -k "arc or Arc"

# Run extractor core tests
uv run pytest app/tests/core/extractor/test_extractor_core.py -v -k "arc or Arc"

# Run full test suite to check for regressions
uv run pytest app/tests/ -v
```

## Recommendations

1. **Export the helper function** - Add `_get_arc_bounding_box` to `__all__` in geometry.py if it needs to be importable for tests.

2. **Add import statement** - Ensure `math` is imported at the top of geometry.py (it likely already is).

3. **Consider adding to test imports** - Update test file imports to include `_get_arc_bounding_box` for direct testing.

## Next Steps

1. Implement Step 1: Add helper function
2. Implement Step 2: Update ARC handling
3. Implement Step 3: Add unit tests for helper
4. Implement Step 4-5: Update existing tests
5. Run Step 6: Verify all tests pass
6. Verify the original 779 trim issue is resolved
