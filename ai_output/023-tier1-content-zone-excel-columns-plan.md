# Implementation Plan: Tier 1 Content Zone Excel Columns

## Executive Summary

Add three new columns to the Block Geometry Analysis Excel sheet: `block_content_zone_width`, `block_content_zone_height`, and `block_polygon_count`. These values are already calculated in `_detect_content_zone()` but not persisted. Implementation extends `ContentZoneData` TypedDict and propagates values through to Excel output.

## Table Summary

| Step | File | Change | Depends On |
|------|------|--------|------------|
| 1 | `app/core/types.py` | Add 3 fields to `ContentZoneData` TypedDict | - |
| 2 | `app/core/constants.py` | Add 3 Excel column constants | Step 1 |
| 3 | `app/core/geometry.py` | Update `_empty_content_zone_data()` | Step 1 |
| 4 | `app/core/geometry.py` | Update `_detect_content_zone()` return | Steps 1, 3 |
| 5 | `app/core/excel_writer.py` | Add columns to DataFrame | Steps 1, 2, 4 |
| 6 | `app/tests/core/test_content_zone.py` | Add tests for new fields | Steps 1-5 |
| 7 | Validation | Run full test suite, mypy, ruff | Steps 1-6 |

## Relevant Files

- **`app/core/types.py:195-219`** - `ContentZoneData` TypedDict definition. Add 3 new fields here.
- **`app/core/constants.py:104-111`** - Content zone Excel column constants. Add 3 new constants.
- **`app/core/geometry.py:339-352`** - `_empty_content_zone_data()` returns empty ContentZoneData. Update to include new fields.
- **`app/core/geometry.py:630-740`** - `_detect_content_zone()` calculates all values. Update return to include new fields.
- **`app/core/excel_writer.py:644-680`** - Builds DataFrame rows. Add new columns to row dict.
- **`app/core/excel_writer.py:686-708`** - Empty DataFrame columns. Add new column names.
- **`app/tests/core/test_content_zone.py`** - Content zone tests. Add tests for new fields.

## Step 1: Extend ContentZoneData TypedDict

**File:** `app/core/types.py` (lines 195-219)

Add three new fields to the TypedDict:

```python
class ContentZoneData(TypedDict):
    # Existing fields
    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool

    # NEW: Tier 1 fields
    content_zone_width: float | None
    content_zone_height: float | None
    polygon_count: int
```

Update docstring to document new attributes:
- `content_zone_width`: Width of content zone bounding box (cz_max_x - cz_min_x), or None if not detected
- `content_zone_height`: Height of content zone bounding box (cz_max_y - cz_min_y), or None if not detected
- `polygon_count`: Total number of closed polygons found (LWPOLYLINE + LINE cycles)

## Step 2: Add Excel Column Constants

**File:** `app/core/constants.py` (after line 111)

```python
# Domain: block, Attribute: content_zone (geometry dimensions)
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: str = "block_content_zone_width"
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: str = "block_content_zone_height"
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: str = "block_polygon_count"
```

## Step 3: Update _empty_content_zone_data()

**File:** `app/core/geometry.py` (lines 339-352)

```python
def _empty_content_zone_data() -> ContentZoneData:
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        # NEW fields
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=0,
    )
```

## Step 4: Update _detect_content_zone() Return

**File:** `app/core/geometry.py` (lines 630-740)

At line 678, `polygon_count` is already calculated. Content zone bbox is calculated at lines 712-715.

Add width/height calculation after line 718:

```python
# Calculate content zone dimensions
cz_width = round(cz_max_x - cz_min_x, 2)
cz_height = round(cz_max_y - cz_min_y, 2)
```

Update the return statement (lines 733-739) to include new fields:

```python
return ContentZoneData(
    suggested_trim_left=trim_left,
    suggested_trim_right=trim_right,
    suggested_trim_top=trim_top,
    suggested_trim_bottom=trim_bottom,
    content_zone_detected=True,
    # NEW fields
    content_zone_width=cz_width,
    content_zone_height=cz_height,
    polygon_count=polygon_count,
)
```

**Important:** Also update the early returns (lines 682, 690, 696, 706) to pass `polygon_count` when available:

- Line 682: `polygon_count=0` (no shapes found)
- Line 690: `polygon_count=polygon_count` (exceeds threshold, still report count)
- Line 696: `polygon_count=polygon_count` (no net areas)
- Line 706: `polygon_count=polygon_count` (zero area)

## Step 5: Update Excel Writer

**File:** `app/core/excel_writer.py`

### 5a. Add imports (around line 75)

```python
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
```

### 5b. Update row building (after line 657)

```python
# Get content zone data for this block
content_zone = block_content_zone_data.get(key.block_name)
if content_zone and content_zone["content_zone_detected"]:
    trim_left: float | str = content_zone["suggested_trim_left"] or ""
    trim_right: float | str = content_zone["suggested_trim_right"] or ""
    trim_top: float | str = content_zone["suggested_trim_top"] or ""
    trim_bottom: float | str = content_zone["suggested_trim_bottom"] or ""
    detected = "TRUE"
    # NEW: Extract dimensions
    cz_width: float | str = content_zone["content_zone_width"] or ""
    cz_height: float | str = content_zone["content_zone_height"] or ""
else:
    trim_left = ""
    trim_right = ""
    trim_top = ""
    trim_bottom = ""
    detected = "FALSE" if content_zone else ""
    cz_width = ""
    cz_height = ""

# NEW: Polygon count is always available
poly_count = content_zone["polygon_count"] if content_zone else ""
```

### 5c. Add to row dict (around line 678)

```python
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: cz_width,
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: cz_height,
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: poly_count,
```

### 5d. Update empty DataFrame columns (around line 706)

Add the three new column constants to the empty DataFrame columns list.

## Step 6: Add Tests

**File:** `app/tests/core/test_content_zone.py`

Add tests for the new fields:

```python
def test_content_zone_data_includes_dimensions(self):
    """Verify ContentZoneData includes width, height, and polygon count."""
    # Use existing test block that has a content zone
    block_def = self.doc.blocks.get("SIMPLE_RECTANGLE")
    bbox = (0, 0, 100, 50)
    result = _detect_content_zone(block_def, bbox)

    assert result["content_zone_detected"] is True
    assert result["content_zone_width"] is not None
    assert result["content_zone_height"] is not None
    assert result["polygon_count"] >= 1

def test_empty_content_zone_has_zero_polygon_count(self):
    """Verify empty content zone returns polygon_count=0."""
    block_def = self.doc.blocks.get("EMPTY_BLOCK")  # or create one
    bbox = (0, 0, 100, 50)
    result = _detect_content_zone(block_def, bbox)

    assert result["content_zone_detected"] is False
    assert result["polygon_count"] == 0
    assert result["content_zone_width"] is None
    assert result["content_zone_height"] is None
```

## Step 7: Validation

Run all validation commands:

```bash
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/ -v
uv run mypy app/
uv run ruff check app/
```

## Out of Scope

- **Tier 2 columns** (`block_line_segment_count`, `block_content_zone_area`, `block_skip_reason`) - future enhancement
- **Tier 3 columns** (`block_lwpolyline_count`, `block_line_cycle_count`, `block_largest_polygon_area`) - future enhancement
- **Excel formatting changes** - no new highlighting or column width adjustments
- **Column reordering** - columns added at end, no reorganization of existing columns
- **Performance testing** - changes are data pass-through only, no algorithm changes
