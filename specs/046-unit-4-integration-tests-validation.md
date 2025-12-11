# Chore: Unit 4 - Integration Tests and Final Validation for Net Area Filter

## Chore Description

This is Unit 4 of the Net Area Filter Implementation Plan (`ai_output/025-net-area-filter-implementation-plan.md`). It adds integration tests to `app/tests/core/extractor/test_extractor_polygon_filter.py` with a new `TestNetAreaFilterIntegration` class that verifies nested polygon filtering works end-to-end via the `extract_blocks()` function.

The integration tests validate that:
1. Nested polygons are correctly filtered by NET area (not gross area) when using `extract_blocks()`
2. The `block_content_zone_data` dictionary contains correct content zone data after net area filtering
3. Trim values in the content zone data reflect the winning polygon after filtering

Additionally, this unit runs comprehensive final validation commands to ensure zero regressions across all tests (731+), type checking (mypy), and linting (ruff).

**Prior Unit Learnings:**
- **Unit 1**: Core logic restructured - side filter runs BEFORE net area calc, area filter runs AFTER
- **Unit 2**: Test asset `nested_polygon_filter_test.dxf` created with 4 blocks (PICTURE_FRAME, BOX_IN_BOX_IN_BOX, MULTIPLE_SIBLINGS, SINGLE_LARGE)
- **Unit 3**: 9 unit tests added in `TestNetAreaFiltering` class, all 731 tests pass

**Test cases to implement:**

| Test | Purpose | Key Assertion |
|------|---------|---------------|
| `test_nested_polygon_filtered_by_net_area` | Extract blocks filters nested polygons by net area | `content_zone_data` shows correct polygon count |
| `test_content_zone_reflects_net_area_winner` | Content zone data shows correct polygon after filtering | trim values match inner polygon (10,10,10,10) |

## Relevant Files

Use these files to resolve the chore:

- **`app/tests/core/extractor/test_extractor_polygon_filter.py`** - Target file where `TestNetAreaFilterIntegration` class will be added
  - Line 1-18: Imports and module docstring pattern to follow
  - Line 22: `ASSETS_DIR` constant for test asset paths
  - Line 455: End of file where new class will be appended
  - Existing classes provide patterns for test structure and assertions

- **`app/tests/assets/nested_polygon_filter_test.dxf`** - Test DXF file with nested polygon blocks
  - `PICTURE_FRAME`: Outer 100x100 (net=3600), inner 80x80 (net=6400)
  - Block reference inserted at (0,0) in modelspace

- **`app/tests/assets/create_nested_polygon_filter_test.py`** - Generator script documenting exact polygon dimensions and expected net areas (reference only)

- **`app/core/extractor.py`** - Contains `extract_blocks()` function being tested
  - Line 950-962: Function signature with filter parameters
  - Line 1567: Returns `block_content_zone_data` in result dictionary

- **`app/core/types.py`** - Contains `ContentZoneData` TypedDict definition
  - Lines 195-227: ContentZoneData with all field definitions including `polygon_count`, trim values, and `content_zone_detected`

- **`app/tests/core/test_content_zone.py`** - Contains `TestNetAreaFiltering` unit tests (reference for expected values)
  - Lines 999-1100+: Unit tests with documented expected net area calculations

### New Files

None - all changes are additions to the existing `app/tests/core/extractor/test_extractor_polygon_filter.py` file.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Review Existing Test File Structure

Read the existing `app/tests/core/extractor/test_extractor_polygon_filter.py` file to understand:
- Import patterns and module docstring style
- How `ASSETS_DIR` is used for test asset paths
- Test class and method naming conventions
- Assertion patterns for `extract_blocks()` results

### Step 2: Update Module Docstring

Update the module docstring at the top of `app/tests/core/extractor/test_extractor_polygon_filter.py` to include the new test coverage:

Add "- Net area filter integration (nested polygon filtering via extract_blocks)" to the docstring list.

### Step 3: Add TestNetAreaFilterIntegration Class

Append the new test class at the end of `app/tests/core/extractor/test_extractor_polygon_filter.py`:

```python
class TestNetAreaFilterIntegration:
    """Integration tests for net area filtering via extract_blocks().

    These tests verify that the full extraction pipeline correctly applies
    net area filtering to nested polygons. The tests use nested_polygon_filter_test.dxf
    which contains blocks with known nested polygon configurations.

    Test blocks:
    - PICTURE_FRAME: Outer 100x100 (net=3600), inner 80x80 (net=6400)
      With min_area_filter=5000: outer filtered (3600<5000), inner kept (6400>=5000)
    """

    def test_nested_polygon_filtered_by_net_area(self) -> None:
        """Extract blocks filters nested polygons by net area.

        Uses PICTURE_FRAME block which has:
        - Outer rectangle: 100x100 = 10,000 gross, net = 3,600 (after subtracting inner)
        - Inner rectangle: 80x80 = 6,400 gross = 6,400 net (no children)

        With min_area_filter=5000:
        - Outer fails: 3,600 < 5,000
        - Inner passes: 6,400 >= 5,000

        Expected: polygon_count == 1 in content_zone_data for PICTURE_FRAME
        """
        nested_dxf = ASSETS_DIR / "nested_polygon_filter_test.dxf"

        result = extract_blocks(
            str(nested_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=5000.0,
            min_side_filter_enabled=False,
        )

        assert result is not None
        assert "block_content_zone_data" in result

        # PICTURE_FRAME block should have content zone data
        content_zone_data = result["block_content_zone_data"]
        assert "PICTURE_FRAME" in content_zone_data

        # Only inner polygon should remain after net area filtering
        picture_frame_data = content_zone_data["PICTURE_FRAME"]
        assert picture_frame_data["content_zone_detected"] is True
        assert picture_frame_data["polygon_count"] == 1

    def test_content_zone_reflects_net_area_winner(self) -> None:
        """Content zone data shows correct polygon after net area filtering.

        When outer frame is filtered out by net area filter, the inner polygon
        should become the content zone with correct trim values.

        PICTURE_FRAME block:
        - Block bounding box: (0,0) to (100,100)
        - Inner polygon: (10,10) to (90,90)

        Expected trim values (distance from block bbox to content zone):
        - left: 10 (inner starts at x=10)
        - right: 10 (inner ends at x=90, bbox is 100)
        - top: 10 (inner ends at y=90, bbox is 100)
        - bottom: 10 (inner starts at y=10)
        """
        nested_dxf = ASSETS_DIR / "nested_polygon_filter_test.dxf"

        result = extract_blocks(
            str(nested_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=5000.0,
            min_side_filter_enabled=False,
        )

        assert result is not None
        content_zone_data = result["block_content_zone_data"]
        picture_frame_data = content_zone_data["PICTURE_FRAME"]

        # Verify content zone was detected
        assert picture_frame_data["content_zone_detected"] is True

        # Inner rectangle is (10,10) to (90,90), so all trims should be 10
        assert picture_frame_data["suggested_trim_left"] == 10.0
        assert picture_frame_data["suggested_trim_right"] == 10.0
        assert picture_frame_data["suggested_trim_top"] == 10.0
        assert picture_frame_data["suggested_trim_bottom"] == 10.0

        # Content zone dimensions should be 80x80 (inner rectangle)
        assert picture_frame_data["content_zone_width"] == 80.0
        assert picture_frame_data["content_zone_height"] == 80.0
```

### Step 4: Run New Integration Tests

Execute the new integration tests to verify they pass:

```bash
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py::TestNetAreaFilterIntegration -v
```

### Step 5: Run Existing Polygon Filter Tests

Execute all polygon filter tests to ensure no regressions in existing tests:

```bash
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v
```

### Step 6: Run Net Area Filter Unit Tests

Execute the Unit 3 net area filter unit tests to confirm they still pass:

```bash
uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v
```

### Step 7: Run Existing Polygon Filtering Tests

Execute existing polygon filtering tests to verify no regressions:

```bash
uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v
```

### Step 8: Run Full Test Suite

Execute the complete test suite to ensure zero regressions across all 731+ tests:

```bash
uv run pytest app/tests/ -v
```

### Step 9: Run Type Checking

Execute mypy to verify all type annotations are correct:

```bash
uv run mypy app/
```

### Step 10: Run Linting

Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/
```

### Step 11: Verify Test File Formatting

Check that the test file is properly formatted:

```bash
uv run ruff format app/tests/core/extractor/test_extractor_polygon_filter.py --check
```

If formatting issues are found, fix them:

```bash
uv run ruff format app/tests/core/extractor/test_extractor_polygon_filter.py
```

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py::TestNetAreaFilterIntegration -v` - Run new integration tests
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run all extractor polygon filter tests
- `uv run pytest app/tests/core/test_content_zone.py::TestNetAreaFiltering -v` - Run net area filter unit tests
- `uv run pytest app/tests/core/test_content_zone.py::TestPolygonFiltering -v` - Run existing polygon filter tests
- `uv run pytest app/tests/ -v` - Run full test suite (731+ tests expected)
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/tests/core/extractor/test_extractor_polygon_filter.py --check` - Verify test file formatting

## Notes

### Net Area Calculations Reference

From `create_nested_polygon_filter_test.py`:

| Block | Polygon | Gross Area | Net Area | Formula |
|-------|---------|------------|----------|---------|
| PICTURE_FRAME | Outer | 10,000 | 3,600 | 10000 - 6400 |
| PICTURE_FRAME | Inner | 6,400 | 6,400 | No children |

### Unit Relationships

- **Unit 1** (completed): Core logic change in `_detect_content_zone()` - filters by NET area
- **Unit 2** (completed): Test asset creation - `nested_polygon_filter_test.dxf`
- **Unit 3** (completed): Unit tests in `TestNetAreaFiltering` class (9 tests)
- **Unit 4** (this spec): Integration tests via `extract_blocks()` + final validation

### Test Class Location

The new `TestNetAreaFilterIntegration` class should be appended at the end of the file, after line 455 (after `TestExtractBlocksFilterEdgeCases` class).

### ContentZoneData Fields

The `ContentZoneData` TypedDict (from `app/core/types.py`) contains:
- `suggested_trim_left`, `suggested_trim_right`, `suggested_trim_top`, `suggested_trim_bottom`: float | None
- `content_zone_detected`: bool
- `content_zone_width`, `content_zone_height`: float | None
- `polygon_count`: int

### Acceptance Criteria

1. `TestNetAreaFilterIntegration` class added with 2 test methods
2. All new integration tests pass
3. All existing polygon filter tests pass (no regressions)
4. Full test suite passes (731+ tests)
5. Type checking passes: `uv run mypy app/`
6. Linting passes: `uv run ruff check app/`
7. `polygon_count == 1` for PICTURE_FRAME when `min_area_filter=5000`
8. Trim values are all `10.0` for PICTURE_FRAME inner polygon
9. Content zone dimensions are `80x80` for PICTURE_FRAME inner polygon
