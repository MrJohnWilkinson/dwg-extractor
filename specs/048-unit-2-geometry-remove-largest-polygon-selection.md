# Chore: Remove Largest Polygon Selection Logic in _detect_content_zone()

## Chore Description

Refactor `_detect_content_zone()` in `geometry.py` to remove the "largest polygon wins" logic and instead use ALL surviving polygons (those that passed both side and area filters) for content zone bounding box calculation.

This is Unit 2 of the "Largest Polygon Selection Removal" One Piece Flow. Unit 1 added the `filtered_polygon_count` field to `ContentZoneData` TypedDict. This unit modifies the core algorithm to:

1. Track `original_polygon_count` separately from the count after filtering
2. Remove the logic that selects only the polygon(s) with maximum net area
3. Use ALL surviving polygons to determine the content zone bounding box
4. Populate both `polygon_count` (original) and `filtered_polygon_count` (after filtering) in all returns

## Relevant Files

Use these files to resolve the chore:

- **`app/core/geometry.py`** - Contains `_detect_content_zone()` function (lines 983-1187) that needs modification, and `_empty_content_zone_data()` helper (lines 449-465) that needs to include `filtered_polygon_count`
- **`app/core/types.py`** - Contains `ContentZoneData` TypedDict definition (already updated in Unit 1 with `filtered_polygon_count` field)

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_empty_content_zone_data()` Helper Function

**File:** `app/core/geometry.py` (lines 449-465)

Update the helper to include the new `filtered_polygon_count` field:

```python
def _empty_content_zone_data() -> ContentZoneData:
    """
    Return an empty ContentZoneData with all trim values as None.

    Returns:
        ContentZoneData with content_zone_detected=False and all trim values as None.
    """
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=0,
        filtered_polygon_count=0,
    )
```

### Step 2: Update Function Docstring

**File:** `app/core/geometry.py` (lines 992-1035)

Update the docstring to remove reference to "largest net area" and clarify the new semantics:

- Change line 995-997 from:
  ```
  The content zone is the closed polygon with the largest net area (own area
  minus areas of contained polygons). Trim values are derived from the
  content zone bounding box relative to the block bounding box.
  ```
- To:
  ```
  The content zone is the bounding box encompassing ALL polygons that survive
  both side and area filtering. Trim values are derived from this combined
  bounding box relative to the block bounding box.
  ```

### Step 3a: Store Original Count

**File:** `app/core/geometry.py` (around line 1060)

Change:
```python
polygon_count = len(all_shapes)
logger.debug(f"[{block_name}] Found {polygon_count} paint-bucket regions")
```

To:
```python
original_polygon_count = len(all_shapes)
logger.debug(f"[{block_name}] Found {original_polygon_count} paint-bucket regions")
```

### Step 3b: Update Side Filter Section

**File:** `app/core/geometry.py` (lines 1065-1076)

Remove the line `polygon_count = len(all_shapes)` at the end of the side filter section.

Change:
```python
if min_side_filter > 0:
    pre_side_count = len(all_shapes)
    all_shapes = [
        s
        for s in all_shapes
        if calculate_shortest_straight_side(s) >= min_side_filter
    ]
    logger.debug(
        f"[{block_name}] Side filter: {pre_side_count} -> {len(all_shapes)} polygons "
        f"(min_side={min_side_filter})"
    )
    polygon_count = len(all_shapes)
```

To:
```python
if min_side_filter > 0:
    pre_side_count = len(all_shapes)
    all_shapes = [
        s
        for s in all_shapes
        if calculate_shortest_straight_side(s) >= min_side_filter
    ]
    logger.debug(
        f"[{block_name}] Side filter: {pre_side_count} -> {len(all_shapes)} polygons "
        f"(min_side={min_side_filter})"
    )
```

### Step 3c: Update Threshold Check (Empty Shapes)

**File:** `app/core/geometry.py` (lines 1078-1080)

Change:
```python
if polygon_count == 0:
    logger.debug(f"[{block_name}] No closed shapes found")
    return _empty_content_zone_data()
```

To:
```python
if len(all_shapes) == 0:
    logger.debug(f"[{block_name}] No closed shapes found")
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=original_polygon_count,
        filtered_polygon_count=0,
    )
```

### Step 3d: Update Polygon Threshold Warning Return

**File:** `app/core/geometry.py` (lines 1082-1097)

Change:
```python
# Check polygon count BEFORE net area calculation
if polygon_count > POLYGON_COUNT_THRESHOLD:
    logger.warning(
        f"[{block_name}] Skipping content zone: "
        f"{polygon_count} polygons exceeds threshold {POLYGON_COUNT_THRESHOLD}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=polygon_count,
    )
```

To:
```python
# Check polygon count BEFORE net area calculation
if len(all_shapes) > POLYGON_COUNT_THRESHOLD:
    logger.warning(
        f"[{block_name}] Skipping content zone: "
        f"{len(all_shapes)} polygons exceeds threshold {POLYGON_COUNT_THRESHOLD}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=original_polygon_count,
        filtered_polygon_count=len(all_shapes),
    )
```

### Step 3e: Update Area Filter Section

**File:** `app/core/geometry.py` (lines 1104-1116)

Remove the line `polygon_count = len(net_areas)` at the end of the area filter section.

Change:
```python
if min_area_filter > 0:
    pre_area_count = len(net_areas)
    net_areas = [
        (poly, net_area)
        for poly, net_area in net_areas
        if net_area >= min_area_filter
    ]
    logger.debug(
        f"[{block_name}] Net area filter: {pre_area_count} -> {len(net_areas)} polygons "
        f"(min_area={min_area_filter})"
    )
    # Update polygon count after all filtering
    polygon_count = len(net_areas)
```

To:
```python
if min_area_filter > 0:
    pre_area_count = len(net_areas)
    net_areas = [
        (poly, net_area)
        for poly, net_area in net_areas
        if net_area >= min_area_filter
    ]
    logger.debug(
        f"[{block_name}] Net area filter: {pre_area_count} -> {len(net_areas)} polygons "
        f"(min_area={min_area_filter})"
    )
```

### Step 3f: Update Empty net_areas Return

**File:** `app/core/geometry.py` (lines 1118-1128)

Change:
```python
if not net_areas:
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=polygon_count,
    )
```

To:
```python
if not net_areas:
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=original_polygon_count,
        filtered_polygon_count=0,
    )
```

### Step 3g: Remove Max Net Area Selection and Replace with ALL Survivors Logic

**File:** `app/core/geometry.py` (lines 1130-1159)

DELETE the "largest polygon wins" logic:
```python
# Find maximum net area value (already sorted descending)
max_net_area = net_areas[0][1]

# Skip if content zone has zero or negative area
if max_net_area <= 0:
    logger.debug(
        f"[{block_name}] Content zone has non-positive area: {max_net_area}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=polygon_count,
    )

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

REPLACE WITH:
```python
# Get all surviving polygons (passed both side and area filters)
survivors = [poly for poly, net_area in net_areas]
filtered_polygon_count = len(survivors)

# Determine content zone bounding box from ALL survivors
if len(survivors) == 1:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(survivors[0])
else:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(survivors)
    logger.debug(
        f"[{block_name}] Content zone: union of {len(survivors)} surviving polygons"
    )
```

### Step 3h: Update Final Return Statement

**File:** `app/core/geometry.py` (lines 1178-1187)

Change:
```python
return ContentZoneData(
    suggested_trim_left=trim_left,
    suggested_trim_right=trim_right,
    suggested_trim_top=trim_top,
    suggested_trim_bottom=trim_bottom,
    content_zone_detected=True,
    content_zone_width=cz_width,
    content_zone_height=cz_height,
    polygon_count=polygon_count,
)
```

To:
```python
return ContentZoneData(
    suggested_trim_left=trim_left,
    suggested_trim_right=trim_right,
    suggested_trim_top=trim_top,
    suggested_trim_bottom=trim_bottom,
    content_zone_detected=True,
    content_zone_width=cz_width,
    content_zone_height=cz_height,
    polygon_count=original_polygon_count,
    filtered_polygon_count=filtered_polygon_count,
)
```

### Step 4: Update Edge Count Threshold Return

**File:** `app/core/geometry.py` (lines 1045-1054)

Update the early return for edge count threshold to include `filtered_polygon_count`:

Change:
```python
return ContentZoneData(
    suggested_trim_left=None,
    suggested_trim_right=None,
    suggested_trim_top=None,
    suggested_trim_bottom=None,
    content_zone_detected=False,
    content_zone_width=None,
    content_zone_height=None,
    polygon_count=0,
)
```

To:
```python
return ContentZoneData(
    suggested_trim_left=None,
    suggested_trim_right=None,
    suggested_trim_top=None,
    suggested_trim_bottom=None,
    content_zone_detected=False,
    content_zone_width=None,
    content_zone_height=None,
    polygon_count=0,
    filtered_polygon_count=0,
)
```

### Step 5: Run Validation Commands

Execute the validation commands to verify changes compile and identify expected test failures.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run python -c "from app.core.geometry import _detect_content_zone; print('Import successful')"` - Verify the module compiles without syntax errors
- `uv run mypy app/core/geometry.py` - Type check the modified file
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests (some may fail due to semantic changes)
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests (some may fail due to semantic changes)
- `uv run pytest app/tests/ -v` - Run full test suite to identify all affected tests

## Notes

- **Expected Test Failures:** Some tests may fail because they expect the old "largest polygon wins" behavior. These failures are expected and will be addressed in Unit 3 (test updates).
- **Semantic Change:** This is a semantic change to the algorithm. Previously, only the polygon(s) with the maximum net area determined the content zone. Now, ALL polygons that survive filtering determine the content zone bounding box.
- **Unit 1 Prerequisite:** This spec assumes Unit 1 has been completed, which added `filtered_polygon_count: int` to the `ContentZoneData` TypedDict in `app/core/types.py`.
- **No Test Updates in This Unit:** Test updates belong in Unit 3. This unit focuses solely on the geometry.py code changes.
