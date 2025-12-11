# Chore: Update Excel Writer and Fix Failing Tests After Geometry Refactor

## Chore Description

Update the Excel writer to output the new `filtered_polygon_count` column and fix all 18 failing tests after the geometry refactor in Unit 2. The refactor changed the semantic meaning of `polygon_count` (now tracks ORIGINAL count before filtering) and changed content zone bounding box calculation to use ALL surviving polygons instead of just the largest polygon.

**Key Semantic Changes from Unit 2:**
- `polygon_count` = Original count BEFORE any filtering
- `filtered_polygon_count` = Count AFTER all filters applied
- Content zone bbox is now from ALL survivors, not just the polygon with maximum net area

**This is Unit 3 (final unit) of the "Largest Polygon Selection Removal" One Piece Flow.**

## Relevant Files

Use these files to resolve the chore:

- **`app/core/excel_writer.py`** - Excel writer that needs to output the new `filtered_polygon_count` column. Update imports, data extraction, row dict, and empty DataFrame columns.

- **`app/core/constants.py`** - Contains `EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT` constant (already added in Unit 1).

- **`app/tests/core/test_content_zone.py`** - Contains 17 failing tests that need updated assertions for the new semantic meanings:
  - `TestTrimValueCalculation`: 3 tests expecting inner rectangle trim values (now uses ALL survivors)
  - `TestContentZoneDetection`: 1 test expecting inner rectangle as content zone
  - `TestPolygonFiltering`: 5 tests using `polygon_count` to verify filtered counts (should use `filtered_polygon_count`)
  - `TestNetAreaFiltering`: 6 tests using `polygon_count` to verify net area filtering (should use `filtered_polygon_count`)
  - `TestTiedShapeHandling`: 2 tests expecting single shape trim values (now uses ALL survivors)

- **`app/tests/core/extractor/test_extractor_polygon_filter.py`** - Contains 1 failing test `test_nested_polygon_filtered_by_net_area` that uses `polygon_count` instead of `filtered_polygon_count`.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Excel Writer Imports

**File:** `app/core/excel_writer.py` (around line 41)

Add the new constant to the imports from constants:

```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
```

Add it after `EXCEL_COLUMN_BLOCK_POLYGON_COUNT` in the import list.

### Step 2: Update Excel Writer Data Extraction

**File:** `app/core/excel_writer.py` (lines 657-666)

Update the data extraction section to also extract `filtered_polygon_count`.

**After line 657** (`poly_count: int | str = content_zone["polygon_count"]`), add:
```python
filtered_poly_count: int | str = content_zone["filtered_polygon_count"]
```

**After line 666** (`poly_count = content_zone["polygon_count"] if content_zone else ""`), add:
```python
filtered_poly_count = content_zone["filtered_polygon_count"] if content_zone else ""
```

### Step 3: Add Column to Row Dict

**File:** `app/core/excel_writer.py` (around line 690)

Add the new column after `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`:

```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: filtered_poly_count,
```

### Step 4: Update Empty DataFrame Columns

**File:** `app/core/excel_writer.py` (around line 721)

Add the new column to the empty DataFrame columns list after `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`:

```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
```

### Step 5: Update test_content_zone.py - TestTrimValueCalculation

**File:** `app/tests/core/test_content_zone.py`

Update the following tests to use `filtered_polygon_count` and adjust expectations for content zone bbox now encompassing ALL survivors.

#### 5a. test_trim_values_centered_content_zone (lines 493-507)

The `NESTED_RECTANGLES` block has 2 polygons: outer (0,0)-(100,80) and inner (10,10)-(90,70).
With ALL survivors, the content zone bbox is the union: (0,0)-(100,80), so all trims are 0.

**Change the assertions to:**
```python
assert result["content_zone_detected"] is True
# With ALL survivors, bbox encompasses both rectangles = full block
# Outer rectangle is (0, 0) to (100, 80)
# Inner rectangle is (10, 10) to (90, 70)
# Union bbox = (0, 0) to (100, 80) = block bbox
assert result["suggested_trim_left"] == 0.0
assert result["suggested_trim_right"] == 0.0
assert result["suggested_trim_top"] == 0.0
assert result["suggested_trim_bottom"] == 0.0
```

#### 5b. test_trim_values_offset_content_zone (lines 509-526)

This test creates 2 rectangles: outer (0,0)-(100,100) and inner (5,10)-(80,90).
With ALL survivors, the union bbox is (0,0)-(100,100), so all trims are 0.

**Change the assertions to:**
```python
assert result["content_zone_detected"] is True
# With ALL survivors, bbox encompasses both rectangles = full block
# Union of (0,0)-(100,100) and (5,10)-(80,90) = (0,0)-(100,100)
assert result["suggested_trim_left"] == 0.0
assert result["suggested_trim_right"] == 0.0
assert result["suggested_trim_top"] == 0.0
assert result["suggested_trim_bottom"] == 0.0
```

#### 5c. test_content_zone_dimensions_calculated (lines 543-555)

The `NESTED_RECTANGLES` block with ALL survivors has bbox (0,0)-(100,80).
Width = 100, Height = 80.

**Change the assertions to:**
```python
assert result["content_zone_detected"] is True
# With ALL survivors, dimensions are full block bbox
# Block bbox is (0, 0) to (100, 80)
# Width = 100, Height = 80
assert result["content_zone_width"] == 100.0
assert result["content_zone_height"] == 80.0
```

### Step 6: Update test_content_zone.py - TestContentZoneDetection

#### 6a. test_detect_content_zone_nested_rectangles (lines 561-572)

The `NESTED_RECTANGLES` block with ALL survivors has bbox (0,0)-(100,80), so trims are 0.

**Change the assertions to:**
```python
assert result["content_zone_detected"] is True
# With ALL survivors, bbox is union of both rectangles
# Block bbox and content zone bbox are the same
assert result["suggested_trim_left"] == 0.0
assert result["suggested_trim_right"] == 0.0
```

### Step 7: Update test_content_zone.py - TestPolygonFiltering

These tests check filtered counts using `polygon_count`. They should now use `filtered_polygon_count` since `polygon_count` is the ORIGINAL count.

#### 7a. test_area_filter_removes_small_polygons (lines 820-841)

**Change line 841 from:**
```python
assert result["polygon_count"] == 1
```
**To:**
```python
assert result["polygon_count"] == 2  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # After filtering
```

#### 7b. test_area_filter_filters_all_polygons (lines 843-862)

**Change lines 861-862 from:**
```python
assert result["content_zone_detected"] is False
assert result["polygon_count"] == 0
```
**To:**
```python
assert result["content_zone_detected"] is False
assert result["polygon_count"] == 1  # Original count before filtering
assert result["filtered_polygon_count"] == 0  # After filtering
```

#### 7c. test_side_filter_removes_narrow_polygons (lines 864-885)

**Change line 885 from:**
```python
assert result["polygon_count"] == 1
```
**To:**
```python
assert result["polygon_count"] == 2  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # After filtering
```

#### 7d. test_combined_filters (lines 887-910)

**Change line 910 from:**
```python
assert result["polygon_count"] == 1
```
**To:**
```python
assert result["polygon_count"] == 3  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # After filtering
```

#### 7e. test_filter_with_precision_and_gap_bridge (lines 912-934)

**Change line 934 from:**
```python
assert result["polygon_count"] == 1
```
**To:**
```python
assert result["polygon_count"] == 2  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # After filtering
```

### Step 8: Update test_content_zone.py - TestNetAreaFiltering

These tests check net area filtering results using `polygon_count`. They should now use `filtered_polygon_count`.

#### 8a. test_picture_frame_filtered_by_net_area (lines 1013-1040)

**Change line 1040 from:**
```python
assert result["polygon_count"] == 1  # Only inner polygon remains
```
**To:**
```python
assert result["polygon_count"] == 2  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # Only inner polygon remains after net area filter
```

#### 8b. test_box_in_box_in_box_filtering (lines 1077-1105)

**Change lines 1104-1105 from:**
```python
# Innermost filtered out (2500 < 3000), outer and middle remain
assert result["polygon_count"] == 2
```
**To:**
```python
# Innermost filtered out (2500 < 3000), outer and middle remain
assert result["polygon_count"] == 3  # Original count before filtering
assert result["filtered_polygon_count"] == 2  # After net area filter
```

#### 8c. test_gross_area_filter_would_pass_outer (lines 1107-1148)

**Change line 1148 from:**
```python
assert result["polygon_count"] == 1
```
**To:**
```python
assert result["polygon_count"] == 2  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # Only inner remains after net area filter
```

#### 8d. test_filter_order_side_then_net_area (lines 1181-1213)

**Change lines 1212-1213 from:**
```python
# Side filter removed siblings first, only outer remains
assert result["polygon_count"] == 1
```
**To:**
```python
# Side filter removed siblings first (3 siblings with side 20 < 25), only outer remains
assert result["polygon_count"] == 4  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # After side filter (siblings removed)
```

#### 8e. test_all_filtered_by_net_area (lines 1238-1260)

**Change lines 1259-1260 from:**
```python
assert result["content_zone_detected"] is False
assert result["polygon_count"] == 0
```
**To:**
```python
assert result["content_zone_detected"] is False
assert result["polygon_count"] == 3  # Original count before filtering
assert result["filtered_polygon_count"] == 0  # All filtered by net area
```

#### 8f. test_multiple_siblings_outer_kept_siblings_filtered (lines 1262-1287)

**Change line 1287 from:**
```python
assert result["polygon_count"] == 1  # Only outer remains
```
**To:**
```python
assert result["polygon_count"] == 4  # Original count before filtering
assert result["filtered_polygon_count"] == 1  # Only outer remains after net area filter
```

### Step 9: Update test_content_zone.py - TestTiedShapeHandling

These tests expect single shape trim values, but now ALL survivors determine the bbox.

#### 9a. test_single_max_area_uses_shape_bbox (lines 1336-1359)

This test creates 2 polygons: large (10,10)-(90,90) and small (0,0)-(10,10).
With ALL survivors, the union bbox is (0,0)-(90,90).
Block bbox is (0,0)-(100,100).

**Change the assertions to:**
```python
assert result["content_zone_detected"] is True
# With ALL survivors, bbox encompasses both rectangles
# Large: (10,10)-(90,90), Small: (0,0)-(10,10)
# Union bbox = (0,0)-(90,90)
# Block bbox = (0,0)-(100,100)
assert result["suggested_trim_left"] == 0.0  # min_x=0, block_min_x=0
assert result["suggested_trim_right"] == 10.0  # block_max_x=100, max_x=90
assert result["suggested_trim_top"] == 10.0  # block_max_y=100, max_y=90
assert result["suggested_trim_bottom"] == 0.0  # min_y=0, block_min_y=0
```

#### 9b. test_single_large_rectangle_trimming (lines 1377-1390)

This test uses `equal_area_test.dxf` SINGLE_LARGE block. With only 1 polygon, behavior is the same.
The test expects trim values of 10 all around for rectangle (10,10)-(90,90) in block (0,0)-(100,100).

**No change needed if SINGLE_LARGE truly has only 1 polygon.** But the failure indicates there may be multiple polygons. Let's verify the expected behavior based on the test file content.

Looking at the test, SINGLE_LARGE should have a single rectangle (10,10)-(90,90). If it fails with `0.0 == 10.0`, it means the content zone bbox is (0,0)-(100,100) instead of (10,10)-(90,90).

This could mean SINGLE_LARGE block in `equal_area_test.dxf` has additional geometry. We need to verify and update accordingly.

**If SINGLE_LARGE has 1 polygon**: trim values should be 10 all around - NO CHANGE needed.
**If SINGLE_LARGE has multiple polygons**: Update to expect union bbox trims.

Based on the error `assert 0.0 == 10.0`, it appears there are multiple polygons. Check the test file creation script or update the assertion:

```python
# If SINGLE_LARGE contains additional geometry creating multiple polygons,
# the content zone will be the union bbox
# Verify the test expectations match the actual block content
```

Let me check the equal_area_test.dxf creation script to understand the expected structure.

### Step 10: Update test_extractor_polygon_filter.py - TestNetAreaFilterIntegration

#### 10a. test_nested_polygon_filtered_by_net_area (lines 470-502)

**Change line 502 from:**
```python
assert picture_frame_data["polygon_count"] == 1
```
**To:**
```python
assert picture_frame_data["polygon_count"] == 2  # Original count before filtering
assert picture_frame_data["filtered_polygon_count"] == 1  # After net area filter
```

### Step 11: Update TestEdgeCases._empty_content_zone_data Test

**File:** `app/tests/core/test_content_zone.py` (lines 721-732)

The `_empty_content_zone_data()` helper was updated in Unit 2 to include `filtered_polygon_count`. Add assertion:

**Add after line 732** (`assert result["polygon_count"] == 0`):
```python
assert result["filtered_polygon_count"] == 0
```

### Step 12: Update TestTypeAnnotations.test_content_zone_data_type Test

**File:** `app/tests/core/test_content_zone.py` (lines 768-780)

Add verification for the new `filtered_polygon_count` key.

**Add after line 780** (`assert "polygon_count" in result`):
```python
assert "filtered_polygon_count" in result
```

### Step 13: Run Validation Commands

Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run python -c "from app.core.excel_writer import write_excel; print('Import successful')"` - Verify excel_writer compiles without syntax errors
- `uv run mypy app/core/excel_writer.py` - Type check the modified excel_writer file
- `uv run ruff check app/core/excel_writer.py` - Lint the modified excel_writer file
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run polygon filter tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run excel writer tests
- `uv run pytest app/tests/ -v` - Run full test suite to ensure zero regressions

## Notes

- **Unit 1 & Unit 2 Prerequisites:** This spec assumes Units 1 and 2 have been completed:
  - Unit 1 added `filtered_polygon_count: int` to `ContentZoneData` TypedDict and `EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT` constant
  - Unit 2 refactored `_detect_content_zone()` to use ALL surviving polygons for bbox calculation

- **Test Update Strategy:** The test updates focus on:
  1. Changing `polygon_count` assertions to `filtered_polygon_count` for filtered count verification
  2. Updating trim value assertions to reflect union bbox of ALL survivors
  3. Adding original count verification via `polygon_count` where appropriate

- **SINGLE_LARGE Block Investigation:** If `test_single_large_rectangle_trimming` still fails after understanding that it should have 1 polygon, investigate the test asset file to determine if additional geometry was accidentally added.

- **Semantic Summary:**
  - `polygon_count` = ORIGINAL count before ANY filtering
  - `filtered_polygon_count` = count AFTER all filters (side + net area)
  - Content zone bbox = union of ALL surviving polygons (not just max net area)
