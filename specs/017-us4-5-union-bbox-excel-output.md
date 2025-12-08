# Feature: Union Bounding Box and Excel Output Integration (US-4 + US-5)

## Feature Description
This feature combines two related user stories that complete the content zone detection pipeline:

**Part A - Union Bounding Box (US-4):** When multiple shapes tie for the maximum net area during content zone detection, combine all tied shapes into a union bounding box. This ensures trim values represent the full usable area rather than an arbitrary selection of the first shape.

**Part B - Excel Output Integration (US-5):** Export content zone detection results to the Excel output file, adding five new columns to the Block Geometry Analysis sheet: suggested trim values (left, right, top, bottom) and a detection success flag.

## User Story
As a DXF block analyzer
I want tied shapes combined into a union bounding box and results exported to Excel
So that trim values are accurate for complex blocks and users can review detection results in the spreadsheet

## Problem Statement
1. **Tied Areas Problem:** The current `_detect_content_zone()` implementation selects only the first shape when multiple shapes have equal maximum net area. This is arbitrary and may not represent the full usable content area when a block has multiple equal-sized content regions (e.g., 4 equal rectangles in corners).

2. **Output Gap:** Content zone detection results are computed but not visible to users. The detection data exists in `ContentZoneData` but is not integrated into the extraction pipeline or Excel output. Users cannot see suggested trim values or know if detection succeeded.

## Solution Statement
1. **Union Bounding Box:** Add `_get_union_bounding_box()` function that calculates the minimum bounding box encompassing all input polygons. Modify `_detect_content_zone()` to detect tied shapes and use union bbox when multiple shapes have equal maximum net area.

2. **Excel Integration:**
   - Extend `ExtractionResult` TypedDict with `block_content_zone_data` field
   - Call `_detect_content_zone()` during extraction for each block
   - Add 5 new columns to Block Geometry Analysis sheet
   - Format columns with appropriate widths and number formats

## Relevant Files
Use these files to implement the feature:

- `app/core/geometry.py` - Add `_get_union_bounding_box()` function and modify `_detect_content_zone()` to handle tied shapes. Already contains all content zone functions from US-3.
- `app/core/types.py` - Contains `ContentZoneData` TypedDict (already defined in US-3). No changes needed.
- `app/core/constants.py` - Already contains Excel column constants `EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_*` and `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED` from US-1.
- `app/core/extractor.py` - Modify to import `_detect_content_zone()` and call it during block analysis. Add `block_content_zone_data` to `ExtractionResult` TypedDict.
- `app/core/excel_writer.py` - Modify `_create_block_geometry_analysis_sheet()` to include content zone columns. Import new constants.
- `app/core/excel_formatting.py` - Modify `_format_block_geometry_analysis_sheet()` to set column widths for new columns.
- `app/tests/core/test_content_zone.py` - Add tests for union bounding box and tied shape handling.
- `app/tests/core/test_geometry.py` - Existing geometry tests (may add union bbox tests here).
- `app/tests/core/excel_writer/test_excel_writer_core.py` - Add tests for new Excel columns.
- `app/tests/core/excel_formatting/test_formatting_scale.py` - Add tests for new column formatting.

### New Files
- `app/tests/assets/create_equal_area_test.py` - Script to generate test DXF with 4 equal rectangles.
- `app/tests/assets/equal_area_test.dxf` - Test DXF for tied area testing.

## Implementation Plan
### Phase 1: Foundation - Union Bounding Box
Add the union bounding box function to geometry.py:
- Create `_get_union_bounding_box()` that calculates min/max bounds across all input polygons
- Modify `_detect_content_zone()` to detect tied shapes (shapes with equal max net area)
- Use union bbox for trim calculations when ties exist
- Add debug logging for union computation

### Phase 2: Core Implementation - Extraction Integration
Integrate content zone detection into the extraction pipeline:
- Add `block_content_zone_data` field to `ExtractionResult` TypedDict
- Import `_detect_content_zone()` in extractor.py
- Call detection for each block during `extract_blocks()`, using existing block_bbox
- Store results in new field keyed by block name

### Phase 3: Integration - Excel Output
Add content zone columns to Excel output:
- Import content zone column constants in excel_writer.py
- Extend `_create_block_geometry_analysis_sheet()` to include 5 new columns
- Add formatting for new columns in excel_formatting.py
- Handle empty values (None) for blocks where detection was skipped

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Union Bounding Box Function to geometry.py
- Add `_get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]` function
- Place after `_get_polygon_bbox()` function for logical grouping
- Handle empty list input by returning `(0.0, 0.0, 0.0, 0.0)`
- Initialize with first polygon's bbox, then expand for each subsequent polygon
- Add comprehensive docstring with examples

```python
def _get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]:
    """
    Calculate the union bounding box encompassing all input polygons.

    The union bounding box is the minimum axis-aligned rectangle that contains
    all vertices of all input polygons. This is used when multiple shapes tie
    for maximum net area to derive trim values from the combined area.

    Args:
        polygons: List of Polygon objects to calculate union bbox for.

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the union bounding box.
        Returns (0, 0, 0, 0) for empty input.

    Examples:
        >>> poly1 = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> poly2 = [(20, 20), (30, 20), (30, 30), (20, 30)]
        >>> _get_union_bounding_box([poly1, poly2])
        (0.0, 0.0, 30.0, 30.0)
    """
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)

    union_min_x, union_min_y, union_max_x, union_max_y = _get_polygon_bbox(polygons[0])

    for polygon in polygons[1:]:
        min_x, min_y, max_x, max_y = _get_polygon_bbox(polygon)
        union_min_x = min(union_min_x, min_x)
        union_min_y = min(union_min_y, min_y)
        union_max_x = max(union_max_x, max_x)
        union_max_y = max(union_max_y, max_y)

    return (union_min_x, union_min_y, union_max_x, union_max_y)
```

### Step 2: Modify _detect_content_zone() to Handle Tied Shapes
- After finding largest net area, detect all shapes with that exact area
- If single shape, use `_get_polygon_bbox()` (existing behavior)
- If multiple tied shapes, use `_get_union_bounding_box()`
- Add debug log when union is computed: `f"[{block_name}] Content zone: union of {len(tied_shapes)} tied shapes"`
- The modification is near the end of `_detect_content_zone()`, after `net_areas = _calculate_net_areas(...)`

Replace the current content zone selection logic:
```python
# Current (single shape selection):
content_zone_polygon, largest_net_area = net_areas[0]
# ...
cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(content_zone_polygon)
```

With tied shape handling:
```python
# Find maximum net area value
max_net_area = net_areas[0][1]  # Already sorted descending

# Skip if content zone has zero or negative area
if max_net_area <= 0:
    logger.debug(
        f"[{block_name}] Content zone has non-positive area: {max_net_area}"
    )
    return _empty_content_zone_data()

# Find all shapes tied for maximum net area
tied_shapes = [shape for shape, net_area in net_areas if net_area == max_net_area]

# Determine content zone bounding box
if len(tied_shapes) == 1:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(tied_shapes[0])
else:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(tied_shapes)
    logger.debug(
        f"[{block_name}] Content zone: union of {len(tied_shapes)} tied shapes"
    )
```

### Step 3: Add block_content_zone_data to ExtractionResult
- Open `app/core/extractor.py`
- Add import for `ContentZoneData` from `.types`
- Add import for `_detect_content_zone` from `.geometry`
- Add `block_content_zone_data: dict[str, ContentZoneData]` field to `ExtractionResult` TypedDict
- Update docstring to document the new field

```python
# In imports section:
from .geometry import (
    _calculate_segments,
    _categorize_rotation,
    _detect_content_zone,  # NEW
    _get_block_bounding_box,
    _get_intersection_points,
)
from .types import (
    # ... existing imports ...
    ContentZoneData,  # NEW
)

# In ExtractionResult TypedDict:
block_content_zone_data: dict[str, ContentZoneData]
```

### Step 4: Call _detect_content_zone() During Extraction
- In `extract_blocks()`, initialize `block_content_zone_data: dict[str, ContentZoneData] = {}`
- After calculating `block_trimming_data` for each block (inside the block definition loop), call `_detect_content_zone()`
- Use the existing `bbox` variable calculated for trimming
- Store result in `block_content_zone_data[effective_name]`
- Add to the returned `ExtractionResult` dict

```python
# After block_trimming_data[effective_name] = {...} in the block definition loop:
# Detect content zone for trim value suggestions
content_zone_data = _detect_content_zone(block_def, bbox)
block_content_zone_data[effective_name] = content_zone_data

# At the end of extract_blocks(), add to result:
result: ExtractionResult = {
    # ... existing fields ...
    "block_content_zone_data": block_content_zone_data,  # NEW
}
```

### Step 5: Import Content Zone Constants in excel_writer.py
- Add imports for the 5 content zone column constants from `.constants`

```python
from .constants import (
    # ... existing imports ...
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
)
```

### Step 6: Modify _create_block_geometry_analysis_sheet() to Include Content Zone Columns
- Access `block_content_zone_data` from extraction_data
- In the row building loop, look up content zone data for each block
- Add 5 new columns to each row dict
- Handle None values (empty string for trim values, empty for detected flag)
- Update the empty DataFrame columns list to include all 18 columns

```python
def _create_block_geometry_analysis_sheet(
    data: ExtractionResult, writer: pd.ExcelWriter
) -> None:
    """Create the Block Geometry Analysis sheet with consolidated transformations and geometry data."""
    logger.info("Creating Block Geometry Analysis sheet...")

    block_layer_pairs = data["block_layer_pairs"]
    block_trimming_data = data["block_trimming_data"]
    block_rotation_counts = data["block_rotation_counts"]
    block_scale_data = data["block_scale_data"]
    block_content_zone_data = data["block_content_zone_data"]  # NEW

    # ... existing code ...

    # In the row building loop, after horizontal_segments_str:
    # Get content zone data for this block
    content_zone = block_content_zone_data.get(key.block_name)
    if content_zone and content_zone["content_zone_detected"]:
        trim_left = content_zone["suggested_trim_left"]
        trim_right = content_zone["suggested_trim_right"]
        trim_top = content_zone["suggested_trim_top"]
        trim_bottom = content_zone["suggested_trim_bottom"]
        detected = "TRUE"
    else:
        trim_left = ""
        trim_right = ""
        trim_top = ""
        trim_bottom = ""
        detected = "FALSE" if content_zone else ""

    rows.append(
        {
            # ... existing 13 columns ...
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: trim_left,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: trim_right,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: trim_top,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: trim_bottom,
            EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: detected,
        }
    )

    # Update empty DataFrame columns (now 18 columns):
    else:
        df = pd.DataFrame(
            columns=[
                # ... existing 13 columns ...
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
                EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
                EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
            ]
        )
```

### Step 7: Modify _format_block_geometry_analysis_sheet() for New Columns
- Add column width settings for columns N through R (14-18)
- Column widths: 12 for trim values, 15 for detected flag

```python
def _format_block_geometry_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Geometry Analysis sheet with three-tier scale highlighting."""
    ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

    # ... existing code ...

    # Set column widths (18 columns now)
    # ... existing A-M columns ...
    ws.column_dimensions["N"].width = 12  # block_suggested_trim_left
    ws.column_dimensions["O"].width = 12  # block_suggested_trim_right
    ws.column_dimensions["P"].width = 12  # block_suggested_trim_top
    ws.column_dimensions["Q"].width = 12  # block_suggested_trim_bottom
    ws.column_dimensions["R"].width = 15  # block_content_zone_detected
```

### Step 8: Create Equal Area Test DXF Generator Script
- Create `app/tests/assets/create_equal_area_test.py`
- Create block "EQUAL_CORNERS" with 4 equal 10x10 rectangles in corners of 100x100 space
- Each rectangle should have exact same area (100 sq units)
- Rectangles at positions: (0,0)-(10,10), (90,0)-(100,10), (0,90)-(10,100), (90,90)-(100,100)
- Create block "SINGLE_LARGE" with one rectangle for comparison testing
- Save to `app/tests/assets/equal_area_test.dxf`

```python
"""Generate test DXF file with equal-area shapes for union bounding box testing."""
import ezdxf

def create_equal_area_test():
    """Create DXF with blocks having multiple equal-area shapes."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Block 1: Four equal rectangles in corners (for tied area testing)
    # Block bbox is 100x100, each corner has 10x10 rectangle
    block1 = doc.blocks.new("EQUAL_CORNERS")
    # Bottom-left corner
    block1.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10)],
        close=True,
    )
    # Bottom-right corner
    block1.add_lwpolyline(
        [(90, 0), (100, 0), (100, 10), (90, 10)],
        close=True,
    )
    # Top-left corner
    block1.add_lwpolyline(
        [(0, 90), (10, 90), (10, 100), (0, 100)],
        close=True,
    )
    # Top-right corner
    block1.add_lwpolyline(
        [(90, 90), (100, 90), (100, 100), (90, 100)],
        close=True,
    )
    # Add outer frame LINE entities to establish block bbox
    block1.add_line((0, 0), (100, 0))
    block1.add_line((100, 0), (100, 100))
    block1.add_line((100, 100), (0, 100))
    block1.add_line((0, 100), (0, 0))

    # Block 2: Single large rectangle for comparison
    block2 = doc.blocks.new("SINGLE_LARGE")
    block2.add_lwpolyline(
        [(10, 10), (90, 10), (90, 90), (10, 90)],
        close=True,
    )
    # Outer frame
    block2.add_line((0, 0), (100, 0))
    block2.add_line((100, 0), (100, 100))
    block2.add_line((100, 100), (0, 100))
    block2.add_line((0, 100), (0, 0))

    # Add block references to modelspace
    msp.add_blockref("EQUAL_CORNERS", (0, 0))
    msp.add_blockref("SINGLE_LARGE", (150, 0))

    # Save the file
    doc.saveas("app/tests/assets/equal_area_test.dxf")
    print("Created app/tests/assets/equal_area_test.dxf")


if __name__ == "__main__":
    create_equal_area_test()
```

### Step 9: Generate Test DXF File
- Run `uv run python app/tests/assets/create_equal_area_test.py`
- Verify file exists: `test -f app/tests/assets/equal_area_test.dxf`

### Step 10: Add Union Bounding Box Unit Tests to test_content_zone.py
- Add `TestUnionBoundingBox` class with tests for the new function
- Test empty input returns zeros
- Test single polygon returns its bbox
- Test multiple polygons returns correct union
- Test non-overlapping polygons

```python
class TestUnionBoundingBox:
    """Tests for _get_union_bounding_box() function."""

    def test_empty_input(self):
        """Empty list returns zero bbox."""
        result = _get_union_bounding_box([])
        assert result == (0.0, 0.0, 0.0, 0.0)

    def test_single_polygon(self):
        """Single polygon returns its bbox."""
        polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        result = _get_union_bounding_box([polygon])
        assert result == (0.0, 0.0, 10.0, 10.0)

    def test_multiple_non_overlapping(self):
        """Non-overlapping polygons return union bbox."""
        poly1 = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        poly2 = [(90.0, 90.0), (100.0, 90.0), (100.0, 100.0), (90.0, 100.0)]
        result = _get_union_bounding_box([poly1, poly2])
        assert result == (0.0, 0.0, 100.0, 100.0)

    def test_overlapping_polygons(self):
        """Overlapping polygons return correct union bbox."""
        poly1 = [(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (0.0, 50.0)]
        poly2 = [(25.0, 25.0), (75.0, 25.0), (75.0, 75.0), (25.0, 75.0)]
        result = _get_union_bounding_box([poly1, poly2])
        assert result == (0.0, 0.0, 75.0, 75.0)
```

### Step 11: Add Tied Shape Tests to test_content_zone.py
- Add `TestTiedShapeHandling` class
- Test single max area shape uses its bbox
- Test tied shapes use union bbox
- Test with equal_area_test.dxf file

```python
class TestTiedShapeHandling:
    """Tests for tied shape handling in content zone detection."""

    def test_single_max_area_uses_shape_bbox(self):
        """Single shape with max area uses its bounding box."""
        doc = ezdxf.new()
        block = doc.blocks.new("SINGLE_MAX")
        # Large rectangle (80x80 = 6400 sq units)
        block.add_lwpolyline(
            [(10, 10), (90, 10), (90, 90), (10, 90)],
            close=True,
        )
        # Small rectangle (10x10 = 100 sq units)
        block.add_lwpolyline(
            [(0, 0), (10, 0), (10, 10), (0, 10)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 100.0)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Should use large rectangle's bbox for trim values
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0

    def test_tied_shapes_use_union_bbox(self):
        """Multiple tied shapes use union bounding box."""
        doc = ezdxf.readfile("app/tests/assets/equal_area_test.dxf")
        block = doc.blocks.get("EQUAL_CORNERS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Union of 4 corner rectangles should span full block
        # Trim values should be 0 since union covers 0-100 in both dimensions
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0
```

### Step 12: Add Excel Output Tests to excel_writer tests
- Add tests to verify content zone columns appear in output
- Test numeric formatting of trim values
- Test TRUE/FALSE values for detection flag

```python
# In app/tests/core/excel_writer/test_excel_writer_core.py or new file

class TestContentZoneExcelOutput:
    """Tests for content zone columns in Excel output."""

    def test_content_zone_columns_in_output(self, temp_excel_path, sample_extraction_result):
        """Excel output includes all 5 content zone columns."""
        # Add content zone data to sample result
        sample_extraction_result["block_content_zone_data"] = {
            "TEST_BLOCK": {
                "suggested_trim_left": 10.5,
                "suggested_trim_right": 10.5,
                "suggested_trim_top": 5.0,
                "suggested_trim_bottom": 5.0,
                "content_zone_detected": True,
            }
        }

        write_excel(sample_extraction_result, temp_excel_path)
        wb = load_workbook(temp_excel_path)
        ws = wb["Block Geometry Analysis"]

        # Check headers include content zone columns
        headers = [cell.value for cell in ws[1]]
        assert "Block Suggested Trim Left" in headers
        assert "Block Suggested Trim Right" in headers
        assert "Block Suggested Trim Top" in headers
        assert "Block Suggested Trim Bottom" in headers
        assert "Block Content Zone Detected" in headers

    def test_detection_flag_boolean_format(self, temp_excel_path, sample_extraction_result):
        """Content zone detected column shows TRUE/FALSE."""
        sample_extraction_result["block_content_zone_data"] = {
            "TEST_BLOCK": {
                "suggested_trim_left": 10.0,
                "suggested_trim_right": 10.0,
                "suggested_trim_top": 5.0,
                "suggested_trim_bottom": 5.0,
                "content_zone_detected": True,
            }
        }

        write_excel(sample_extraction_result, temp_excel_path)
        wb = load_workbook(temp_excel_path)
        ws = wb["Block Geometry Analysis"]

        # Find the detected column and check value
        headers = [cell.value for cell in ws[1]]
        detected_col = headers.index("Block Content Zone Detected") + 1

        # Get first data row
        detected_value = ws.cell(row=2, column=detected_col).value
        assert detected_value == "TRUE"
```

### Step 13: Add Excel Formatting Tests
- Verify column widths for new columns
- Verify alignment settings

### Step 14: Run Validation Commands
- Generate test DXF: `uv run python app/tests/assets/create_equal_area_test.py`
- Run content zone tests: `uv run pytest app/tests/core/test_content_zone.py -v`
- Run all tests: `uv run pytest app/tests/`
- Type check: `uv run mypy app/`
- Lint: `uv run ruff check app/`
- Format: `uv run ruff format app/`
- Fix: `uv run ruff check app/ --fix`

## Testing Strategy
### Unit Tests
- `_get_union_bounding_box()` - empty input, single polygon, multiple polygons, overlapping polygons
- Tied shape detection - verify shapes with equal max area are all selected
- Content zone selection with ties - verify union bbox is used

### Integration Tests
- Full extraction with content zone data - verify `block_content_zone_data` populated
- Excel output with content zone columns - verify all 5 columns present
- End-to-end with equal_area_test.dxf - verify union bbox calculation

### Edge Cases
- Empty block (no shapes) - content_zone_detected=False, empty trim values
- Single shape - uses shape bbox (not union)
- Two shapes with nearly equal area (floating point) - only exact matches tie
- Block where detection was skipped (threshold exceeded) - empty values in Excel
- All shapes with zero or negative net area - content_zone_detected=False

### Playwright MCP Tests
Not applicable - this feature is backend data processing with Excel output. Unit and integration tests provide complete coverage.

## Acceptance Criteria
1. `_get_union_bounding_box()` function exists in geometry.py
2. `_get_union_bounding_box()` returns (0,0,0,0) for empty input
3. `_get_union_bounding_box()` returns correct union bbox for multiple polygons
4. `_detect_content_zone()` detects tied shapes with equal max net area
5. `_detect_content_zone()` uses union bbox when multiple shapes tie
6. Debug log emitted when union bbox is computed with shape count
7. `ExtractionResult` TypedDict includes `block_content_zone_data` field
8. `extract_blocks()` populates `block_content_zone_data` for each block
9. Block Geometry Analysis sheet includes 5 new columns
10. Trim value columns display numeric values with 2 decimal places
11. Content zone detected column shows "TRUE" or "FALSE"
12. Empty values shown for blocks where detection failed or was skipped
13. Column widths set appropriately (12 for trim, 15 for detected)
14. Test DXF file created: `equal_area_test.dxf`
15. All 451+ existing tests pass
16. All new tests pass (union bbox, tied shapes, Excel output)
17. mypy type checking passes
18. ruff linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Generate test DXF file:
    - `uv run python app/tests/assets/create_equal_area_test.py`
    - `test -f app/tests/assets/equal_area_test.dxf && echo "File created successfully"`
- Run tests to validate the feature works with zero regressions:
    - `uv run pytest app/tests/core/test_content_zone.py -v`
    - `uv run pytest app/tests/core/test_geometry.py -v`
    - `uv run pytest app/tests/core/excel_writer/ -v`
    - `uv run pytest app/tests/`
    - `uv run mypy app/`
    - `uv run ruff check app/`
    - `uv run ruff format app/`
    - `uv run ruff check app/ --fix`

## Notes
- The Excel column constants (`EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_*`, `EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED`) are already defined in `app/core/constants.py` from US-1.
- The `ContentZoneData` TypedDict is already defined in `app/core/types.py` from US-3.
- The content zone detection functions (`_detect_content_zone`, `_get_polygon_bbox`, etc.) are already in `app/core/geometry.py` from US-3.
- The equal area test uses LWPOLYLINE entities (not LINE cycles) because LWPOLYLINE extraction is more reliable and faster.
- Floating-point equality comparison for tied areas should be exact match (not epsilon comparison) to avoid unexpected behavior.
- The Block Geometry Analysis sheet will now have 18 columns (13 existing + 5 new content zone columns).
- Columns N-R in Excel correspond to the 5 new content zone columns after alphabetical order.
- When content zone detection is skipped (threshold exceeded), `content_zone_detected` is False and all trim values are None.
- The "TRUE"/"FALSE" string format is used for Excel readability rather than boolean values.
