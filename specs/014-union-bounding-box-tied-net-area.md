# Bug: Union Bounding Box for Tied Net Area Content Zones and Improved Extraction Feedback

## Bug Description
Two related issues affecting the DXF Block Extractor:

**Issue 1: Arbitrary Content Zone Selection for Tied Net Areas**
When multiple shapes in a block have equal maximum net area, the system arbitrarily selects the first one (due to Python's `max()` behavior) and uses only that single shape's bounding box to calculate trim values. This produces inaccurate trim values when multiple equally-significant shapes exist in different positions (e.g., 4 equal boxes in corners).

Expected behavior: Combine all tied shapes' bounding boxes into a union bounding box that encompasses all significant shapes, then derive trim values from that union.

**Issue 2: Unresponsive UI During Extraction**
The GUI shows "Analyzing CAD file..." at 50% progress during extraction but provides no further feedback until completion. For large DXF files, the application appears frozen because:
- Progress stays stuck at 0.5 with no updates
- No indication of ongoing processing
- Users cannot tell if the application is working or hung

Expected behavior: Provide more granular progress updates during the extraction phase to indicate ongoing activity.

## Problem Statement
1. Content zone selection uses `max()` which picks only one shape when ties exist, ignoring other equally-significant shapes and producing content zones that don't represent the full usable area
2. Extraction worker provides only 4 progress checkpoints (0.2, 0.5, 0.7, 1.0) with no updates during the longest phase (block analysis)

## Solution Statement
1. **Tied Net Area Fix**: Modify `_detect_content_zone()` to collect ALL shapes with the maximum net area, compute their union bounding box (outer limits), and use that union for trim calculations
2. **Progress Feedback Fix**: Add intermediate progress updates during extraction to provide visual feedback that processing is ongoing

## Steps to Reproduce
**Issue 1 (Tied Net Areas):**
1. Create a DXF file with a block containing 4 equal-sized rectangles in each corner
2. Extract blocks using the application
3. Observe that `suggested_trim_*` values are based on only one rectangle, not the combined extent of all 4

**Issue 2 (Unresponsive UI):**
1. Open a large DXF file with many blocks
2. Click Extract
3. Observe progress bar stuck at 50% with "Analyzing CAD file..." for extended period
4. Application appears frozen/unresponsive

## Root Cause Analysis
**Issue 1:**
In `app/core/geometry.py:738-746`, the `_detect_content_zone()` function uses:
```python
content_zone_shape, max_net_area = max(valid_shapes, key=lambda x: x[1])
```
Python's `max()` returns only the first element when multiple elements share the maximum value. This is correct for single-winner scenarios but incorrect when the design intent is to identify "all significant shapes" as the content zone.

**Issue 2:**
In `app/main.py:169-194`, the `_extraction_worker()` method updates progress at fixed points:
- 0.2 - "Loading file..."
- 0.5 - "Analyzing CAD file..."
- 0.7 - "Generating Excel..."
- 1.0 - "Success"

The `extract_blocks()` call happens between 0.5 and 0.7 with no intermediate updates. For complex files, this phase can take significant time with no user feedback.

## Relevant Files
Use these files to fix the bug:

### Files to Modify
- **app/core/geometry.py** - Fix `_detect_content_zone()` to collect all tied shapes and compute union bounding box. The key change is in lines 738-770 where content zone selection and trim calculation occur.
- **app/main.py** - Add intermediate progress updates during extraction phase to provide user feedback. The key change is in `_extraction_worker()` method (lines 169-219).
- **app/tests/core/test_content_zone.py** - Add test case for 4 equal boxes in corners to validate union bounding box behavior.

### New Files to Create
- **app/tests/assets/create_equal_area_test.py** - Script to create test DXF file with 4 equal-area shapes in corners.
- **app/tests/assets/equal_area_test.dxf** - Test fixture with equal-area shapes for union bounding box validation.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Helper Function for Union Bounding Box
- Add new function `_get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]` to `app/core/geometry.py`
- Implementation:
  ```python
  def _get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]:
      """
      Calculate the union bounding box of multiple polygons.

      Returns (min_x, min_y, max_x, max_y) encompassing all polygons.
      Returns (0.0, 0.0, 0.0, 0.0) for empty list.
      """
      if not polygons:
          return (0.0, 0.0, 0.0, 0.0)

      # Get bounding box of first polygon
      union_min_x, union_min_y, union_max_x, union_max_y = _get_polygon_bounding_box(polygons[0])

      # Expand to include all other polygons
      for polygon in polygons[1:]:
          bbox = _get_polygon_bounding_box(polygon)
          union_min_x = min(union_min_x, bbox[0])
          union_min_y = min(union_min_y, bbox[1])
          union_max_x = max(union_max_x, bbox[2])
          union_max_y = max(union_max_y, bbox[3])

      return (union_min_x, union_min_y, union_max_x, union_max_y)
  ```

### Step 2: Modify Content Zone Selection for Tied Areas
- Update `_detect_content_zone()` in `app/core/geometry.py` to handle tied net areas
- Replace the single-shape selection (lines 738-746) with tie-aware selection:
  ```python
  # Find maximum net area
  if contained_shapes:
      max_net_area = max(net_area for _, net_area in contained_shapes)
      # Collect ALL shapes with maximum net area
      tied_shapes = [shape for shape, net_area in contained_shapes if net_area == max_net_area]
  else:
      max_net_area = max(net_area for _, net_area in valid_shapes)
      # Collect ALL shapes with maximum net area
      tied_shapes = [shape for shape, net_area in valid_shapes if net_area == max_net_area]

  logger.debug(f"Content zone: {len(tied_shapes)} shape(s) with max net area {max_net_area:.2f}")
  ```

### Step 3: Calculate Union Bounding Box for Content Zone
- Update the bounding box calculation in `_detect_content_zone()` to use union of tied shapes:
  ```python
  # Calculate union bounding box of all tied shapes
  if len(tied_shapes) == 1:
      cz_bbox = _get_polygon_bounding_box(tied_shapes[0])
      logger.debug(f"Content zone selected: single shape with net area {max_net_area:.2f}")
  else:
      cz_bbox = _get_union_bounding_box(tied_shapes)
      logger.debug(f"Content zone selected: union of {len(tied_shapes)} shapes with net area {max_net_area:.2f}")
  ```

### Step 4: Create Test Asset Script for Equal Area Shapes
- Create `app/tests/assets/create_equal_area_test.py` with:
  - Block "FOUR_CORNERS" with 4 equal 10x10 rectangles at corners of a 100x100 area:
    - Top-left: (0, 90) to (10, 100)
    - Top-right: (90, 90) to (100, 100)
    - Bottom-left: (0, 0) to (10, 10)
    - Bottom-right: (90, 0) to (100, 10)
  - Block "TWO_EQUAL_HORIZONTAL" with 2 equal 20x10 rectangles side by side
  - Block "SINGLE_SHAPE" with one 50x30 rectangle (regression test)
  - Add INSERT entities for each block in modelspace

### Step 5: Generate Test DXF Fixture
- Run `uv run python app/tests/assets/create_equal_area_test.py`
- Verify `app/tests/assets/equal_area_test.dxf` is created

### Step 6: Add Unit Tests for Union Bounding Box
- Add test class `TestUnionBoundingBox` to `app/tests/core/test_content_zone.py`:
  ```python
  class TestUnionBoundingBox:
      """Test cases for union bounding box calculation."""

      def test_single_polygon(self) -> None:
          """Union of single polygon equals its own bounding box."""
          poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
          bbox = _get_union_bounding_box([poly])
          assert bbox == (0, 0, 10, 10)

      def test_two_disjoint_polygons(self) -> None:
          """Union spans both disjoint polygons."""
          poly_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
          poly_b = [(90, 90), (100, 90), (100, 100), (90, 100)]
          bbox = _get_union_bounding_box([poly_a, poly_b])
          assert bbox == (0, 0, 100, 100)

      def test_four_corner_polygons(self) -> None:
          """Union of 4 corner polygons spans entire area."""
          corners = [
              [(0, 0), (10, 0), (10, 10), (0, 10)],      # bottom-left
              [(90, 0), (100, 0), (100, 10), (90, 10)],  # bottom-right
              [(0, 90), (10, 90), (10, 100), (0, 100)],  # top-left
              [(90, 90), (100, 90), (100, 100), (90, 100)]  # top-right
          ]
          bbox = _get_union_bounding_box(corners)
          assert bbox == (0, 0, 100, 100)

      def test_empty_list(self) -> None:
          """Empty list returns zero bounding box."""
          bbox = _get_union_bounding_box([])
          assert bbox == (0.0, 0.0, 0.0, 0.0)
  ```

### Step 7: Add Integration Test for Four Corners Block
- Add test method to `TestContentZoneDetection` class:
  ```python
  def test_four_equal_corners_block(self) -> None:
      """Test content zone spans all 4 equal corner shapes."""
      test_path = str(Path(__file__).parent.parent / "assets" / "equal_area_test.dxf")
      if not os.path.exists(test_path):
          pytest.skip("Test DXF file not found")

      doc = ezdxf.readfile(test_path)
      block_def = doc.blocks.get("FOUR_CORNERS")
      bbox = (0, 0, 100, 100)  # Block bounding box

      result = _detect_content_zone(block_def, bbox)

      assert result["content_zone_detected"] is True
      # All 4 corners have equal area, union spans 0-100 in both axes
      # Content zone = block bbox, so all trims = 0
      assert result["suggested_trim_left"] == 0.0
      assert result["suggested_trim_right"] == 0.0
      assert result["suggested_trim_top"] == 0.0
      assert result["suggested_trim_bottom"] == 0.0
  ```

### Step 8: Update Import in Test File
- Add `_get_union_bounding_box` to the imports in `app/tests/core/test_content_zone.py`

### Step 9: Add Intermediate Progress Updates to GUI
- Modify `_extraction_worker()` in `app/main.py` to add progress updates:
  ```python
  def _extraction_worker(self) -> None:
      """Background worker thread for extraction process."""
      try:
          # Step 1: Load file
          self._update_progress(0.1, "Loading file...")

          # Validate file path exists
          if not self.selected_file_path:
              self._show_error("No file selected")
              return

          # Step 2: Parse DXF structure
          self._update_progress(0.2, "Parsing DXF structure...")

          # Step 3: Extract comprehensive data
          self._update_progress(0.3, "Analyzing block definitions...")

          extraction_result = extract_blocks(self.selected_file_path)

          # Step 4: Check results
          self._update_progress(0.6, "Processing extraction results...")

          # Check for empty results
          if not extraction_result["block_counts"]:
              self.logger.warning(f"No blocks found in {self.selected_file_path}")
              self._show_error(MSG_ERROR_NO_BLOCKS)
              return

          # Step 5: Generate Excel
          self._update_progress(0.7, "Generating Excel report...")

          excel_path = write_excel(extraction_result, self.selected_file_path)
          self.output_excel_path = excel_path

          # Step 6: Finalize
          self._update_progress(0.9, "Finalizing...")

          # Step 7: Complete
          self._update_progress(1.0, MSG_SUCCESS)

          # Show success and open file
          self._show_success(excel_path)
      # ... rest of error handling unchanged
  ```

### Step 10: Add Progress Callback Support to Extractor (Optional Enhancement)
- This step is optional but recommended for large files
- If implemented, add a progress callback parameter to `extract_blocks()`:
  ```python
  def extract_blocks(
      file_path: str,
      progress_callback: Callable[[float, str], None] | None = None
  ) -> ExtractionResult:
  ```
- Call `progress_callback(0.4, "Analyzing block geometry...")` after block definition analysis
- Call `progress_callback(0.5, "Processing modelspace entities...")` before entity iteration
- This allows real-time feedback during long-running extractions

### Step 11: Run Content Zone Tests
- Execute `xvfb-run uv run pytest app/tests/core/test_content_zone.py -v`
- Verify all tests pass including new union bounding box tests

### Step 12: Run Full Test Suite
- Execute `xvfb-run uv run pytest app/tests/ -v`
- Verify no regressions in existing functionality

### Step 13: Run Type Checking
- Execute `uv run mypy app/`
- Fix any type errors

### Step 14: Run Linting
- Execute `uv run ruff check app/`
- Fix any style issues

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `xvfb-run uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests including new union bounding box tests
- `xvfb-run uv run pytest app/tests/core/test_geometry.py -v` - Verify geometry tests still pass
- `xvfb-run uv run pytest app/tests/core/extractor/ -v` - Verify extractor tests still pass
- `xvfb-run uv run pytest app/tests/ -v` - Run full test suite
- `uv run mypy app/` - Type check entire application
- `uv run ruff check app/` - Lint check entire application

## Notes
- **Epsilon tolerance for tie detection**: Net areas are floating-point values. Consider using `abs(net_area - max_net_area) < epsilon` (e.g., epsilon=0.001) instead of exact equality for robustness against floating-point precision issues.
- **Deterministic behavior preserved**: When a single shape has maximum net area, behavior is unchanged. Only tie scenarios are affected.
- **Progress values recalibrated**: Progress percentages adjusted to 0.1, 0.2, 0.3, 0.6, 0.7, 0.9, 1.0 to provide more frequent updates during the extraction phase.
- **Step 10 is optional**: The progress callback enhancement to `extract_blocks()` provides more granular feedback but requires modifying the extractor signature. The basic fix in Step 9 is sufficient for improved user experience.
- **WSL environment**: GUI tests require `xvfb-run` prefix due to X server limitations in WSL.
