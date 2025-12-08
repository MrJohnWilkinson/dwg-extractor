# Feature: Content Zone Type Extensions

## Feature Description
This feature extends the `ContentZoneData` TypedDict with three new fields to provide additional geometric information about detected content zones. The new fields include:
- `content_zone_width`: Width of the content zone bounding box
- `content_zone_height`: Height of the content zone bounding box
- `polygon_count`: Total number of closed polygons found during detection

These additions enable downstream consumers (Excel reports, analysis tools) to display content zone dimensions and polygon statistics without requiring additional calculation.

## User Story
As a CAD analyst
I want to see the content zone dimensions and polygon count in the extraction results
So that I can quickly assess the size of detected content zones and complexity of block geometry

## Problem Statement
Currently, `ContentZoneData` only returns trim values and a detection flag. Users and downstream tools cannot determine the actual dimensions of the detected content zone or how many polygons were analyzed without recalculating from the trim values and block bbox. This information is already computed during detection but discarded.

## Solution Statement
Extend `ContentZoneData` TypedDict with three new fields and update all geometry functions that create this data structure to populate the new fields. Add corresponding Excel column constants for future Excel output integration.

## Relevant Files
Use these files to implement the feature:

- **`app/core/types.py`** (lines 195-219): Contains the `ContentZoneData` TypedDict definition that needs three new fields added
- **`app/core/constants.py`** (after line 111): Excel column constants section where new constants for width, height, and polygon count should be added
- **`app/core/geometry.py`** (lines 339-352, 630-740): Contains `_empty_content_zone_data()` helper function and `_detect_content_zone()` main function that need to return the new fields
- **`app/tests/core/test_content_zone.py`**: Contains unit tests for content zone detection that need to be updated to verify new fields
- **`app_docs/005-field-naming-convention.md`**: Reference for field naming conventions (domain: block, attribute: content_zone)

## Implementation Plan
### Phase 1: Foundation (Type Definitions)
1. Extend `ContentZoneData` TypedDict with three new fields following the naming convention
2. Add Excel column constants for the new fields

### Phase 2: Core Implementation (Geometry Functions)
1. Update `_empty_content_zone_data()` to return default values for new fields
2. Update `_detect_content_zone()` to calculate and return width/height/polygon_count
3. Ensure all early return paths include the new fields with appropriate values

### Phase 3: Integration (Testing)
1. Update existing tests to verify new fields are present
2. Add new tests for width/height calculations
3. Verify polygon_count is correctly propagated through all code paths

## Step by Step Tasks

### Step 1: Extend ContentZoneData TypedDict
- Open `app/core/types.py`
- Add three new fields to the `ContentZoneData` TypedDict (after line 219, before the closing):
  ```python
  content_zone_width: float | None
  content_zone_height: float | None
  polygon_count: int
  ```
- Update the docstring to document the new fields:
  - `content_zone_width`: Width of content zone bounding box (cz_max_x - cz_min_x), or None if not detected
  - `content_zone_height`: Height of content zone bounding box (cz_max_y - cz_min_y), or None if not detected
  - `polygon_count`: Total number of closed polygons found (LWPOLYLINE + LINE cycles)

### Step 2: Add Excel Column Constants
- Open `app/core/constants.py`
- Add three new constants after line 111 (after `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED`):
  ```python
  # Domain: block, Attribute: content_zone (geometry dimensions)
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: str = "block_content_zone_width"
  EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: str = "block_content_zone_height"
  EXCEL_COLUMN_BLOCK_POLYGON_COUNT: str = "block_polygon_count"
  ```

### Step 3: Update _empty_content_zone_data()
- Open `app/core/geometry.py`
- Update the `_empty_content_zone_data()` function (lines 339-352) to include the new fields with default values:
  - `content_zone_width=None`
  - `content_zone_height=None`
  - `polygon_count=0`

### Step 4: Update _detect_content_zone() Return
- Open `app/core/geometry.py`
- Locate `_detect_content_zone()` function (lines 630-740)
- At line 678, `polygon_count` is already calculated as `len(all_shapes)`
- Update early return at line 682-683 (no shapes found) to include `polygon_count=0`
- Update early return at line 689-690 (threshold exceeded) to include `polygon_count=polygon_count`
- Update early return at line 695-696 (no net areas) to include `polygon_count=polygon_count`
- Update early return at line 703-706 (non-positive area) to include `polygon_count=polygon_count`
- After line 718 (after content zone bbox is determined), add width/height calculation:
  ```python
  cz_width = round(cz_max_x - cz_min_x, 2)
  cz_height = round(cz_max_y - cz_min_y, 2)
  ```
- Update the final success return statement (lines 733-739) to include:
  - `content_zone_width=cz_width`
  - `content_zone_height=cz_height`
  - `polygon_count=polygon_count`

### Step 5: Update Unit Tests
- Open `app/tests/core/test_content_zone.py`
- Update `TestEdgeCases.test_empty_content_zone_data()` (lines 686-694) to verify new fields:
  ```python
  assert result["content_zone_width"] is None
  assert result["content_zone_height"] is None
  assert result["polygon_count"] == 0
  ```
- Update `TestTypeAnnotations.test_content_zone_data_type()` (lines 730-739) to verify new fields exist:
  ```python
  assert "content_zone_width" in result
  assert "content_zone_height" in result
  assert "polygon_count" in result
  ```
- Add new test for width/height calculation in `TestTrimValueCalculation` class:
  ```python
  def test_content_zone_dimensions_calculated(self) -> None:
      """Verify width and height are calculated correctly."""
      doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
      block = doc.blocks.get("NESTED_RECTANGLES")
      bbox = _get_block_bounding_box(block)

      result = _detect_content_zone(block, bbox)

      assert result["content_zone_detected"] is True
      # Inner rectangle is (10, 10) to (90, 70)
      # Width = 90 - 10 = 80, Height = 70 - 10 = 60
      assert result["content_zone_width"] == 80.0
      assert result["content_zone_height"] == 60.0
  ```
- Add new test for polygon_count in `TestContentZoneDetection` class:
  ```python
  def test_polygon_count_returned(self) -> None:
      """Verify polygon count is returned correctly."""
      doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
      block = doc.blocks.get("NESTED_RECTANGLES")
      bbox = _get_block_bounding_box(block)

      result = _detect_content_zone(block, bbox)

      assert result["polygon_count"] == 2  # Outer and inner rectangle
  ```
- Add test for polygon_count when detection fails:
  ```python
  def test_polygon_count_zero_when_no_shapes(self) -> None:
      """Verify polygon_count is 0 when no shapes found."""
      doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
      block = doc.blocks.get("EMPTY_BLOCK")
      bbox = _get_block_bounding_box(block)

      result = _detect_content_zone(block, bbox)

      assert result["content_zone_detected"] is False
      assert result["polygon_count"] == 0
  ```

### Step 6: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Verify `_empty_content_zone_data()` returns all new fields with correct defaults
- Verify `_detect_content_zone()` populates width/height when detection succeeds
- Verify `polygon_count` is correct for various block configurations
- Verify early returns include `polygon_count` appropriately

### Integration Tests
- Verify existing content zone tests pass with updated assertions
- Verify type checking passes with new TypedDict fields

### Edge Cases
- Empty blocks: `content_zone_width=None`, `content_zone_height=None`, `polygon_count=0`
- Single polygon: `polygon_count=1`, dimensions match polygon bbox
- Multiple nested polygons: `polygon_count` equals total LWPOLYLINE + LINE cycles
- Tied shapes (union bbox): dimensions should reflect union bbox
- Threshold exceeded: `polygon_count` should still be returned

### Playwright MCP Tests
- Not applicable for this feature (backend-only type extension)

## Acceptance Criteria
- [ ] `ContentZoneData` TypedDict includes `content_zone_width: float | None` field
- [ ] `ContentZoneData` TypedDict includes `content_zone_height: float | None` field
- [ ] `ContentZoneData` TypedDict includes `polygon_count: int` field
- [ ] Three new Excel column constants are defined in `constants.py`
- [ ] `_empty_content_zone_data()` returns `content_zone_width=None`, `content_zone_height=None`, `polygon_count=0`
- [ ] `_detect_content_zone()` calculates and returns correct width/height when detection succeeds
- [ ] `_detect_content_zone()` returns `polygon_count` in all return paths
- [ ] All existing tests pass without modification (beyond adding new assertions)
- [ ] New unit tests verify width, height, and polygon_count calculations
- [ ] Type checking passes with `uv run mypy app/`
- [ ] All tests pass with `uv run pytest app/tests/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to ensure TypedDict changes are correct
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests to verify new fields
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run ruff check app/` - Run linting to ensure code quality
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- The `polygon_count` variable is already calculated at line 678 in `_detect_content_zone()` as `len(all_shapes)`, so it just needs to be included in return statements
- Content zone bbox variables (`cz_min_x`, `cz_min_y`, `cz_max_x`, `cz_max_y`) are already calculated at lines 712-715, so width/height can be derived from them
- The early returns at lines 682, 689-690, 695-696, and 703-706 all need to be updated to include `polygon_count`
- Width and height should be `None` when `content_zone_detected=False`, consistent with trim value behavior
- This is Unit 1 of a multi-unit implementation; subsequent units will add Excel output integration
