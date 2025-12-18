# Chore: Min Side Filter - UI Label Updates and Integration Tests (Unit 2)

## Chore Description

Update the UI labels in the Main Window and Settings Window to clarify that the min side filter only applies to rectangles (4-sided polygons), and add comprehensive integration tests verifying that the rectangles-only filtering behavior works correctly.

This is Unit 2 of the "Min Side Filter: Rectangles-Only" enhancement. Unit 1 (commit ef9b341) already completed the core geometry changes:
- `calculate_shortest_straight_side()` now returns `tuple[float, int]` (shortest_side, side_count) instead of `float`
- Added `passes_min_side_filter()` helper function in `_detect_content_zone()` that checks `side_count == 4`
- Filter now only applies to 4-sided rectangles; complex polygons (>4 sides) pass through
- All existing tests updated to handle tuple return type

Unit 2 focuses on:
1. Updating UI labels to communicate the rectangles-only behavior to users
2. Adding integration tests that verify the filtering logic in `_detect_content_zone()`

## Relevant Files

Use these files to resolve the chore:

- `app/main.py` (lines 483-489) - Contains the main window UI with the min side filter checkbox. The `text` parameter needs to be updated to clarify it only applies to rectangles.
- `app/core/settings_window.py` (lines 698-714) - Contains the settings window with two setting rows for min side filter. Both labels and descriptions need updating to reflect the rectangles-only behavior.
- `app/tests/core/test_geometry.py` - Contains geometry tests. A new test class `TestMinSideFilterRectanglesOnly` should be added to verify the integration of the rectangles-only filter logic in `_detect_content_zone()`.
- `app/core/geometry.py` (lines 1765-1782) - Reference only. Contains the `passes_min_side_filter()` helper and `_detect_content_zone()` function that the tests will exercise.

## Step by Step Tasks

### Step 1: Update Main Window Checkbox Label

**File:** `app/main.py`

Update the min side filter checkbox text to clarify it only applies to rectangles.

**Before (line 485):**
```python
            text="Min Side Filter",
```

**After:**
```python
            text="Min Side (Rectangles Only)",
```

This change makes it immediately clear in the main UI that this filter only affects 4-sided rectangular polygons.

### Step 2: Update Settings Window Min Side Filter Enabled Row

**File:** `app/core/settings_window.py`

Update the first min side filter setting row with a clearer label and description.

**Before (lines 698-705):**
```python
        self._create_setting_row(
            scroll_frame,
            "min_side_filter_enabled",
            "Min Side Filter",
            "Filters out polygons with shortest side below threshold. "
            "Helps remove thin artifacts.",
            readonly=True,
        )
```

**After:**
```python
        self._create_setting_row(
            scroll_frame,
            "min_side_filter_enabled",
            "Min Side Filter (Rectangles Only)",
            "Filters out 4-sided rectangles with shortest side below threshold. "
            "Complex polygons (5+ sides) are not affected by this filter.",
            readonly=True,
        )
```

### Step 3: Update Settings Window Min Side Filter Amount Row

**File:** `app/core/settings_window.py`

Update the second min side filter setting row with a clearer description.

**Before (lines 707-714):**
```python
        self._create_setting_row(
            scroll_frame,
            "min_side_filter_amount",
            "Min Side Filter Amount",
            "Minimum side length in drawing units. "
            "Polygons with shorter sides are excluded.",
            readonly=True,
        )
```

**After:**
```python
        self._create_setting_row(
            scroll_frame,
            "min_side_filter_amount",
            "Min Side Filter Amount",
            "Minimum side length for rectangles in drawing units. "
            "Only applies to 4-sided polygons (rectangles).",
            readonly=True,
        )
```

### Step 4: Add Integration Test Class for Rectangles-Only Filter

**File:** `app/tests/core/test_geometry.py`

Add a new test class `TestMinSideFilterRectanglesOnly` at the end of the file (after line 3148) to verify the integration of the rectangles-only filter logic in `_detect_content_zone()`.

First, add the import for `_detect_content_zone` to the imports section (around line 23-42):

```python
from core.geometry import (
    # ... existing imports ...
    _detect_content_zone,
)
```

Then add the test class at the end of the file:

```python
class TestMinSideFilterRectanglesOnly:
    """Test suite for min_side_filter rectangles-only behavior in _detect_content_zone."""

    def test_rectangle_below_threshold_is_filtered(self) -> None:
        """Test that 4-sided rectangle with short sides gets filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SMALL_RECT")
        # 100x5 rectangle - shortest side is 5 units
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 5), (0, 5)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 5.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Threshold above shortest side (5)
        )

        # Rectangle should be filtered out (shortest side 5 < threshold 10)
        assert result.content_zone_detected is False
        assert result.polygon_count == 1
        assert result.filtered_polygon_count == 0

    def test_rectangle_above_threshold_passes(self) -> None:
        """Test that 4-sided rectangle with sides >= threshold passes."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LARGE_RECT")
        # 100x20 rectangle - shortest side is 20 units
        block.add_lwpolyline(
            [(0, 0), (100, 0), (100, 20), (0, 20)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 20.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Threshold below shortest side (20)
        )

        # Rectangle should pass (shortest side 20 >= threshold 10)
        assert result.content_zone_detected is True
        assert result.filtered_polygon_count == 1

    def test_pentagon_with_short_side_passes(self) -> None:
        """Test that 5-sided polygon with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="PENTAGON")
        # Pentagon with one very short side (5 units)
        # Vertices form a house-like shape
        block.add_lwpolyline(
            [
                (0, 0),      # bottom-left
                (100, 0),    # bottom-right
                (100, 50),   # right
                (50, 70),    # peak
                (0, 50),     # left
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 70.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=30.0,  # High threshold that would filter rectangles
        )

        # Pentagon should pass through (5 sides, not affected by filter)
        assert result.content_zone_detected is True
        assert result.filtered_polygon_count == 1

    def test_hexagon_with_short_side_passes(self) -> None:
        """Test that 6-sided polygon with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HEXAGON")
        # Irregular hexagon with varying side lengths
        block.add_lwpolyline(
            [
                (0, 0),
                (80, 0),     # 80 units
                (100, 20),   # ~28 units
                (100, 80),   # 60 units
                (20, 80),    # 80 units
                (0, 60),     # ~28 units
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 80.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=50.0,  # High threshold that would filter rectangles
        )

        # Hexagon should pass through (6 sides, not affected by filter)
        assert result.content_zone_detected is True
        assert result.filtered_polygon_count == 1

    def test_l_shape_with_short_side_passes(self) -> None:
        """Test that 6-sided L-shape with short side is NOT filtered."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="L_SHAPE")
        # L-shaped polygon with 6 sides, some short (10 units)
        block.add_lwpolyline(
            [
                (0, 0),
                (50, 0),    # 50 units (bottom)
                (50, 30),   # 30 units (right lower)
                (20, 30),   # 30 units (inner horizontal)
                (20, 80),   # 50 units (inner vertical)
                (0, 80),    # 20 units (top)
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 50.0, 80.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=25.0,  # Would filter 20-unit sides if it were a rectangle
        )

        # L-shape should pass through (6 sides, not affected by filter)
        assert result.content_zone_detected is True
        assert result.filtered_polygon_count == 1

    def test_rectangle_and_pentagon_mixed(self) -> None:
        """Test that rectangle is filtered but pentagon in same block passes."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED_SHAPES")

        # Small rectangle (will be filtered)
        block.add_lwpolyline(
            [(0, 0), (20, 0), (20, 5), (0, 5)],
            close=True,
        )

        # Pentagon (will pass through)
        block.add_lwpolyline(
            [
                (50, 0),
                (150, 0),
                (150, 50),
                (100, 70),
                (50, 50),
            ],
            close=True,
        )

        bbox = (0.0, 0.0, 150.0, 70.0)
        result = _detect_content_zone(
            block,
            bbox,
            min_side_filter=10.0,  # Filters rectangle (5 < 10) but not pentagon
        )

        # Rectangle filtered, pentagon passes
        assert result.content_zone_detected is True
        assert result.polygon_count == 2
        assert result.filtered_polygon_count == 1  # Only pentagon survives
```

### Step 5: Run Validation Commands

Execute all validation commands to ensure zero regressions:

```bash
# Run geometry tests specifically (includes new test class)
uv run pytest app/tests/core/test_geometry.py::TestMinSideFilterRectanglesOnly -v

# Run all geometry tests
uv run pytest app/tests/core/test_geometry.py -v

# Run content zone tests
uv run pytest app/tests/core/test_content_zone.py -v

# Run full test suite
uv run pytest app/tests/ -v

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/

# Format check
uv run ruff format app/ --check
```

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# 1. Run the new test class specifically
uv run pytest app/tests/core/test_geometry.py::TestMinSideFilterRectanglesOnly -v

# 2. Run all geometry tests
uv run pytest app/tests/core/test_geometry.py -v

# 3. Run content zone tests (related functionality)
uv run pytest app/tests/core/test_content_zone.py -v

# 4. Run polygon filter tests (related functionality)
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v

# 5. Run full test suite to catch any regressions
uv run pytest app/tests/ -v

# 6. Type checking - verify all types are correct
uv run mypy app/

# 7. Linting - ensure code style is maintained
uv run ruff check app/

# 8. Format check - ensure formatting is consistent
uv run ruff format app/ --check
```

## Notes

- The UI label changes are purely cosmetic and do not affect functionality - they clarify the existing behavior introduced in Unit 1
- The integration tests use `_detect_content_zone()` directly to test the filtering behavior without needing full extraction
- Test shapes use LWPOLYLINE with `close=True` to create proper closed polygons for content zone detection
- The `passes_min_side_filter()` helper function is defined locally inside `_detect_content_zone()`, so we test it through the public interface
- Pentagon, hexagon, and L-shape all have side_count > 4 and should pass through the filter regardless of their shortest side length
- The `test_rectangle_and_pentagon_mixed` test verifies that in a block with multiple shapes, only rectangles are filtered while complex polygons are preserved
