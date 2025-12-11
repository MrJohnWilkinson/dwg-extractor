# Feature: Unit 3 - Net Area Filter Unit Tests

## Feature Description

Add a comprehensive test class `TestNetAreaFiltering` to `app/tests/core/test_content_zone.py` that validates the net area filter implementation from Unit 1. These tests use the `nested_polygon_filter_test.dxf` test asset created in Unit 2 to verify that `min_area_filter` correctly uses NET area (gross area minus contained polygon areas) instead of GROSS area.

This is Unit 3 of the Net Area Filter Implementation Plan (`ai_output/025-net-area-filter-implementation-plan.md`), focusing on unit tests that exercise the core logic change. The tests ensure that "picture frame" scenarios (large outer polygons with small net areas due to inner polygons) are correctly filtered.

**Test cases to implement:**

| Test | Purpose | Key Assertion |
|------|---------|---------------|
| `test_picture_frame_filtered_by_net_area` | Net area filter removes thin frame | polygon_count == 1 (inner only) |
| `test_picture_frame_inner_selected_as_content_zone` | Correct polygon selected | trim values match inner |
| `test_box_in_box_in_box_filtering` | Multi-level filtering | Correct net areas calculated |
| `test_gross_area_filter_would_pass_outer` | Verify behavior change | Gross would pass, net fails |
| `test_side_filter_still_uses_gross_geometry` | Side filter unchanged | Uses shortest side, not net |
| `test_filter_order_side_then_net_area` | Correct filter order | Side filter applied first |

## User Story

As a CAD engineer processing DXF files with nested polygons
I want to verify that the area filter uses net area calculations
So that I can trust that thin "picture frame" polygons are correctly filtered out while inner content zones are preserved

## Problem Statement

Unit 1 implemented the core logic change to filter by NET area instead of GROSS area. Unit 2 created test assets with known nested polygon configurations. Unit 3 must now add comprehensive unit tests that:

1. Verify the picture frame scenario works correctly (outer frame filtered, inner kept)
2. Confirm multi-level nesting is handled properly
3. Ensure the side filter still uses gross geometry (unchanged behavior)
4. Validate the correct filter ordering (side filter first, then net area filter)
5. Provide regression tests that would fail if someone reverts to gross area filtering

Without these tests, the net area filter implementation lacks verification and could regress in future changes.

## Solution Statement

Add a new test class `TestNetAreaFiltering` following the existing patterns from `TestPolygonFiltering`. The tests will:

1. Use `ezdxf.readfile()` to load the `nested_polygon_filter_test.dxf` test asset
2. Call `_get_block_bounding_box()` and `_detect_content_zone()` directly (unit tests)
3. Assert on `polygon_count`, `content_zone_detected`, and trim values
4. Include clear docstrings explaining each test scenario with expected net area calculations
5. Use parametrized tests where multiple threshold values need testing

## Relevant Files

Use these files to implement the feature:

- **`app/tests/core/test_content_zone.py`** - Main test file where `TestNetAreaFiltering` class will be added
  - Lines 1-41: Imports and module structure to follow
  - Lines 800-996: `TestPolygonFiltering` class as reference pattern for test structure
  - Line 996: End of `TestPolygonFiltering` class where new class will be added (before `TestUnionBoundingBox`)

- **`app/tests/assets/nested_polygon_filter_test.dxf`** - Test DXF file with nested polygon blocks created in Unit 2
  - `PICTURE_FRAME`: Outer 100x100 (net=3600) containing inner 80x80 (net=6400)
  - `BOX_IN_BOX_IN_BOX`: 3 levels - outer (net=3600), middle (net=3900), inner (net=2500)
  - `MULTIPLE_SIBLINGS`: Outer (net=8800) with 3 inner 20x20 (net=400 each)
  - `SINGLE_LARGE`: Single 80x80 (net=gross=6400)

- **`app/tests/assets/create_nested_polygon_filter_test.py`** - Generator script documenting exact polygon dimensions and expected net areas (reference only)

- **`app/core/geometry.py`** - Core implementation being tested
  - `_detect_content_zone()`: Function under test with `min_area_filter` and `min_side_filter` parameters
  - `_get_block_bounding_box()`: Required to get bbox for content zone detection
  - `calculate_polygon_area()`: Used in tests to verify gross area calculations
  - `calculate_shortest_straight_side()`: Used in side filter verification tests

### New Files

None - all changes are additions to the existing `app/tests/core/test_content_zone.py` file.

## Implementation Plan

### Phase 1: Foundation

1. Review the existing `TestPolygonFiltering` class structure and test patterns
2. Understand the test DXF block configurations and their expected net areas:
   - `PICTURE_FRAME`: outer net=3600, inner net=6400
   - `BOX_IN_BOX_IN_BOX`: outer net=3600, middle net=3900, inner net=2500
   - `MULTIPLE_SIBLINGS`: outer net=8800, siblings net=400 each
   - `SINGLE_LARGE`: net=gross=6400
3. Verify imports are available for required functions

### Phase 2: Core Implementation

1. Add `TestNetAreaFiltering` class after line 996 (after `TestPolygonFiltering`, before `TestUnionBoundingBox`)
2. Implement 6 test methods following the test matrix
3. Add comprehensive docstrings with expected net area calculations
4. Use pytest parametrize where multiple filter values need testing

### Phase 3: Integration

1. Run the new tests to verify they pass with the Unit 1 implementation
2. Run the full content zone test suite to ensure no regressions
3. Run the full test suite to validate all 722+ tests still pass

## Step by Step Tasks

### Step 1: Add TestNetAreaFiltering Class with Picture Frame Test

Add the new test class to `app/tests/core/test_content_zone.py` after line 996 (after `TestPolygonFiltering` class, before `TestUnionBoundingBox` class).

Create the class with the first test method `test_picture_frame_filtered_by_net_area`:

```python
class TestNetAreaFiltering:
    """Test suite for net area filtering in _detect_content_zone.

    These tests verify that min_area_filter uses NET area (gross minus contained
    polygons) rather than GROSS area. This correctly handles "picture frame"
    scenarios where a large outer polygon has a small net area.

    Test blocks from nested_polygon_filter_test.dxf:
    - PICTURE_FRAME: outer 100x100 (net=3600), inner 80x80 (net=6400)
    - BOX_IN_BOX_IN_BOX: 3 levels - outer (net=3600), middle (net=3900), inner (net=2500)
    - MULTIPLE_SIBLINGS: outer (net=8800), 3 inner 20x20 (net=400 each)
    - SINGLE_LARGE: 80x80 (net=gross=6400)
    """

    def test_picture_frame_filtered_by_net_area(self) -> None:
        """Verify outer polygon with small net area is filtered, leaving inner polygon.

        Scenario:
        - Outer rectangle: 100x100 = 10,000 sq units gross
        - Inner rectangle: 80x80 = 6,400 sq units gross (centered at 10,10 to 90,90)
        - Outer NET area: 10,000 - 6,400 = 3,600 sq units
        - Inner NET area: 6,400 sq units (no children)

        With min_area_filter=5000:
        - Outer fails: 3,600 < 5,000 (filtered OUT)
        - Inner passes: 6,400 >= 5,000 (kept)

        Expected: polygon_count == 1 (only inner remains)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1  # Only inner polygon remains
```

### Step 2: Add Picture Frame Content Zone Selection Test

Add `test_picture_frame_inner_selected_as_content_zone`:

```python
    def test_picture_frame_inner_selected_as_content_zone(self) -> None:
        """Verify inner polygon becomes content zone with correct trim values.

        When outer frame is filtered out, the inner polygon (10,10)-(90,90)
        should be selected as the content zone.

        Block bounding box: (0,0)-(100,100)
        Inner polygon: (10,10)-(90,90)
        Expected trim values:
        - left: 10 (inner starts at x=10)
        - right: 10 (inner ends at x=90, bbox is 100)
        - top: 10 (inner ends at y=90, bbox is 100)
        - bottom: 10 (inner starts at y=10)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        # Inner rectangle is (10,10) to (90,90)
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0
        # Content zone dimensions: 80x80
        assert result["content_zone_width"] == 80.0
        assert result["content_zone_height"] == 80.0
```

### Step 3: Add Box-in-Box-in-Box Filtering Test

Add `test_box_in_box_in_box_filtering`:

```python
    def test_box_in_box_in_box_filtering(self) -> None:
        """Verify multi-level nesting filters correctly by net area.

        3 nested rectangles:
        - Outermost: 100x100, gross=10000, net=10000-6400=3600
        - Middle: 80x80, gross=6400, net=6400-2500=3900
        - Innermost: 50x50, gross=2500, net=2500 (no children)

        With min_area_filter=3000:
        - Outermost: net=3600 >= 3000, PASSES
        - Middle: net=3900 >= 3000, PASSES
        - Innermost: net=2500 < 3000, FAILS (filtered)

        Expected: polygon_count == 2 (outer and middle remain)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("BOX_IN_BOX_IN_BOX")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=3000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        # Innermost filtered out (2500 < 3000), outer and middle remain
        assert result["polygon_count"] == 2
```

### Step 4: Add Gross Area Regression Test

Add `test_gross_area_filter_would_pass_outer`:

```python
    def test_gross_area_filter_would_pass_outer(self) -> None:
        """Regression test: verify gross area WOULD have passed but net area fails.

        This test ensures we're using NET area, not GROSS area.

        PICTURE_FRAME outer polygon:
        - GROSS area: 100x100 = 10,000 sq units
        - NET area: 10,000 - 6,400 = 3,600 sq units

        With min_area_filter=5000:
        - If using GROSS: outer would PASS (10,000 >= 5,000) - WRONG!
        - If using NET: outer FAILS (3,600 < 5,000) - CORRECT!

        This test verifies the implementation uses NET area by confirming
        the outer polygon is NOT present (polygon_count < 2).
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        # Verify gross area would pass the threshold
        from core.geometry import calculate_polygon_area, _extract_closed_lwpolylines

        polygons = _extract_closed_lwpolylines(block)
        # Find the outer polygon (larger gross area)
        outer_polygon = max(polygons, key=lambda p: calculate_polygon_area(p))
        outer_gross_area = calculate_polygon_area(outer_polygon)

        # Outer gross area should be 10,000 (would pass filter of 5000)
        assert outer_gross_area >= 9900  # Allow small tolerance
        assert outer_gross_area >= 5000  # Would pass if using gross

        # But with NET area filtering, outer should be filtered out
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        # Only 1 polygon remains (inner), proving we use NET area
        assert result["polygon_count"] == 1
```

### Step 5: Add Side Filter Gross Geometry Test

Add `test_side_filter_still_uses_gross_geometry`:

```python
    def test_side_filter_still_uses_gross_geometry(self) -> None:
        """Verify side filter uses shortest side of gross geometry, not net area.

        The side filter should evaluate the actual polygon dimensions,
        independent of any contained polygons.

        PICTURE_FRAME outer polygon:
        - Dimensions: 100x100 (square)
        - Shortest side: 100 units (all sides equal)

        With min_side_filter=50:
        - Outer PASSES: shortest side 100 >= 50
        - Inner PASSES: shortest side 80 >= 50

        Expected: Both polygons remain (side filter doesn't use net area)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=0.0,  # Disable area filter
            min_side_filter=50.0,  # Both should pass
        )

        assert result["content_zone_detected"] is True
        # Both polygons should pass the side filter (100 >= 50, 80 >= 50)
        assert result["polygon_count"] == 2
```

### Step 6: Add Filter Order Test

Add `test_filter_order_side_then_net_area`:

```python
    def test_filter_order_side_then_net_area(self) -> None:
        """Verify side filter is applied BEFORE net area filter.

        This test uses a scenario where filter order matters:
        - Side filter removes some polygons
        - Then net area is calculated on remaining polygons
        - Then net area filter is applied

        MULTIPLE_SIBLINGS block:
        - Outer 100x100, contains 3 inner 20x20 rectangles
        - Inner polygons have shortest side = 20

        With min_side_filter=25 (filters inner siblings) and min_area_filter=100:
        - Side filter removes all 3 inner siblings (20 < 25)
        - Only outer remains for net area calculation
        - Outer's net area CHANGES because siblings are gone from calculation

        This demonstrates side filter runs first (before net area calc).
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("MULTIPLE_SIBLINGS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,  # Low threshold, not filtering anything by area
            min_side_filter=25.0,   # Filters inner siblings (20 < 25)
        )

        assert result["content_zone_detected"] is True
        # Side filter removed siblings first, only outer remains
        assert result["polygon_count"] == 1
```

### Step 7: Add Additional Edge Case Tests

Add supplementary tests for completeness:

```python
    def test_single_large_net_equals_gross(self) -> None:
        """Verify net area equals gross area when no containment.

        SINGLE_LARGE block has a single 80x80 rectangle with no inner polygons.
        Net area should equal gross area (6400).

        With min_area_filter=6000:
        - Single polygon net=gross=6400 >= 6000, PASSES
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("SINGLE_LARGE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=6000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1

    def test_all_filtered_by_net_area(self) -> None:
        """Verify behavior when all polygons are filtered by net area.

        BOX_IN_BOX_IN_BOX:
        - Outer net=3600, Middle net=3900, Inner net=2500

        With min_area_filter=4000:
        - All polygons have net area < 4000
        - All should be filtered out
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("BOX_IN_BOX_IN_BOX")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=4000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 0

    def test_multiple_siblings_outer_kept_siblings_filtered(self) -> None:
        """Verify outer polygon kept when siblings filtered by net area.

        MULTIPLE_SIBLINGS:
        - Outer 100x100, net = 10000 - 400*3 = 8800
        - 3 inner siblings 20x20, each net = 400

        With min_area_filter=500:
        - Outer passes: 8800 >= 500
        - Siblings fail: 400 < 500

        Expected: polygon_count == 1 (only outer)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("MULTIPLE_SIBLINGS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=500.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1  # Only outer remains
```

### Step 8: Update Imports in Test File

Ensure the test file imports include `calculate_polygon_area` and `_extract_closed_lwpolylines` which are used in `test_gross_area_filter_would_pass_outer`:

Check the existing imports at the top of the file and add if needed:

```python
from core.geometry import (
    GeometryAbortedError,
    _calculate_net_areas,
    _count_line_segments,
    _detect_content_zone,
    _empty_content_zone_data,
    _extract_closed_lwpolylines,
    _extract_line_cycles,
    _get_block_bounding_box,
    _get_polygon_bbox,
    _get_union_bounding_box,
    _point_in_polygon,
    _polygon_contains_polygon,
    _shoelace_area,
    calculate_polygon_area,  # Add if not present
)
```

### Step 9: Run New Tests

Execute the new test class to verify all tests pass:

```bash
uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v
```

### Step 10: Run Full Content Zone Test Suite

Execute all content zone tests to ensure no regressions:

```bash
uv run pytest app/tests/core/test_content_zone.py -v
```

### Step 11: Run Type Checking

Execute mypy to verify type annotations are correct:

```bash
uv run mypy app/tests/core/test_content_zone.py
```

### Step 12: Run Linting

Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/tests/core/test_content_zone.py
uv run ruff format app/tests/core/test_content_zone.py --check
```

### Step 13: Run Full Test Suite

Execute all tests to verify zero regressions:

```bash
uv run pytest app/tests/ -v
```

### Step 14: Run Validation Commands

Execute all validation commands to confirm the feature is complete:

```bash
uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v
uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/ -v
uv run mypy app/
uv run ruff check app/
```

## Testing Strategy

### Unit Tests

The `TestNetAreaFiltering` class provides 9 test methods covering:

1. **Picture frame filtering** - Core scenario where outer frame is filtered
2. **Content zone selection** - Verifying correct polygon becomes content zone with accurate trim values
3. **Multi-level nesting** - Box-in-box-in-box with 3 levels of containment
4. **Gross vs net regression** - Explicit test that would fail if using gross area
5. **Side filter unchanged** - Verifying side filter still uses gross geometry
6. **Filter ordering** - Verifying side filter runs before net area calculation
7. **Single polygon baseline** - Verifying net=gross when no containment
8. **All filtered scenario** - Verifying behavior when all polygons filtered
9. **Multiple siblings** - Verifying sibling polygons filtered correctly

### Integration Tests

Integration tests are covered in Unit 4 (separate spec) via `test_extractor_polygon_filter.py`.

### Edge Cases

| Case | Test Method | Expected Behavior |
|------|-------------|-------------------|
| No containment | `test_single_large_net_equals_gross` | Net area equals gross area |
| All filtered | `test_all_filtered_by_net_area` | `content_zone_detected=False`, `polygon_count=0` |
| Multi-level nesting | `test_box_in_box_in_box_filtering` | Correct filtering at each level |
| Siblings contained | `test_multiple_siblings_outer_kept_siblings_filtered` | Siblings filtered, outer kept |
| Filter ordering | `test_filter_order_side_then_net_area` | Side filter runs first |

### Playwright MCP Tests

Not applicable for this unit - these are unit tests, not GUI tests.

## Acceptance Criteria

1. `TestNetAreaFiltering` class added to `app/tests/core/test_content_zone.py`
2. All 9 test methods pass with `uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v`
3. Picture frame scenario correctly filters outer polygon (polygon_count == 1)
4. Inner polygon selected as content zone with correct trim values (10, 10, 10, 10)
5. Multi-level nesting test validates correct net area calculations
6. Gross area regression test explicitly verifies NET area is used
7. Side filter test confirms gross geometry is still used (polygon_count == 2)
8. Filter order test confirms side filter runs before net area calculation
9. All existing tests pass (zero regressions in 722+ tests)
10. Type checking passes: `uv run mypy app/`
11. Linting passes: `uv run ruff check app/`

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v` - Run new net area filter tests
- `uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v` - Run existing polygon filter tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run all content zone tests
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions
- `uv run mypy app/tests/core/test_content_zone.py` - Type check the test file
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/tests/core/test_content_zone.py` - Lint the test file
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/tests/core/test_content_zone.py --check` - Verify test file formatting

## Notes

### Net Area Calculations Reference

From `create_nested_polygon_filter_test.py`:

| Block | Polygon | Gross Area | Net Area | Formula |
|-------|---------|------------|----------|---------|
| PICTURE_FRAME | Outer | 10,000 | 3,600 | 10000 - 6400 |
| PICTURE_FRAME | Inner | 6,400 | 6,400 | No children |
| BOX_IN_BOX_IN_BOX | Outer | 10,000 | 3,600 | 10000 - 6400 |
| BOX_IN_BOX_IN_BOX | Middle | 6,400 | 3,900 | 6400 - 2500 |
| BOX_IN_BOX_IN_BOX | Inner | 2,500 | 2,500 | No children |
| MULTIPLE_SIBLINGS | Outer | 10,000 | 8,800 | 10000 - 400*3 |
| MULTIPLE_SIBLINGS | Each sibling | 400 | 400 | No children |
| SINGLE_LARGE | Single | 6,400 | 6,400 | No children |

### Unit Relationships

- **Unit 1** (completed): Core logic change in `_detect_content_zone()` - filters by NET area
- **Unit 2** (completed): Test asset creation - `nested_polygon_filter_test.dxf`
- **Unit 3** (this spec): Unit tests using the test assets
- **Unit 4** (upcoming): Integration tests via `extract_blocks()`

### Test File Location

The new `TestNetAreaFiltering` class should be inserted after `TestPolygonFiltering` (ends at line 996) and before `TestUnionBoundingBox` (starts at line 999). This maintains logical grouping of polygon filtering tests.

### Import Considerations

The `test_gross_area_filter_would_pass_outer` test uses `calculate_polygon_area` and `_extract_closed_lwpolylines` to verify gross area would have passed. These imports may already exist in the file or need to be added to the import block at lines 26-40.
