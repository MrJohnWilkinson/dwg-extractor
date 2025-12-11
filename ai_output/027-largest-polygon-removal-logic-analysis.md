# Largest Polygon Selection Removal: Logic Analysis

## Executive Summary

This report analyzes the proposed changes to remove the "largest polygon wins" logic from content zone detection. The analysis confirms the user's understanding is correct: the current implementation still selects polygons with maximum net area, while the proposal shifts to using ALL surviving polygons equally. Three code changes are required, plus one new field addition.

## Table Summary

| Item | Current Behavior | Proposed Behavior | Change Required? |
|------|-----------------|-------------------|------------------|
| Net area calculation | Used for min_area_filter | Used ONLY for min_area_filter | No (already correct) |
| Content zone bbox | Bbox of max net area polygon(s) | Union of ALL survivors | **Yes** |
| Bounding box source | Gross geometry of winner(s) | Gross geometry of all survivors | **Yes** |
| Polygon count field | Count AFTER all filtering | ORIGINAL count before filtering | **Yes** |
| Filtered count field | Not present | New field needed | **Yes - Add field** |
| min_area_filter | Uses net area | Uses net area | No (already correct) |
| min_side_filter | Uses gross geometry | Uses gross geometry | No (already correct) |
| Trim values | From block bbox to winner bbox | From block bbox to union bbox | **Yes** |
| Largest polygon logic | Max net area wins | Remove entirely | **Yes** |
| Area sorting | Sorted descending by net area | Not needed | **Yes - Remove** |
| Tie-breaking | Union bbox of tied shapes | Not applicable | **Yes - Remove** |

## Relevant Files

- **`app/core/geometry.py:1099-1186`** - `_detect_content_zone()` function contains the largest polygon selection logic at lines 1130-1159, polygon count assignment at line 1116
- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()` returns polygons sorted by net area; this sorting would become optional
- **`app/core/types.py:195-228`** - `ContentZoneData` TypedDict defines `polygon_count` field; needs new `filtered_polygon_count` field
- **`app/core/constants.py:115`** - `EXCEL_COLUMN_BLOCK_POLYGON_COUNT` column constant; need new constant for filtered count
- **`app/core/excel_writer.py:657-690`** - Excel output uses `polygon_count`; needs to output both counts

## Current vs Proposed Logic Flow

### Current Flow (geometry.py:1099-1186)
```
1. Extract regions → polygon_count = len(all_shapes)
2. Apply side filter → polygon_count = len(all_shapes)
3. Check threshold
4. Calculate net areas → sorted by net area descending
5. Apply area filter → polygon_count = len(net_areas)  ← FINAL COUNT
6. Find max_net_area = net_areas[0][1]
7. Collect tied_shapes = [all with max net area]
8. Content zone bbox = bbox of tied_shapes (single or union)
9. Return polygon_count (filtered count)
```

### Proposed Flow
```
1. Extract regions → original_polygon_count = len(all_shapes)  ← PRESERVE
2. Apply side filter (no count update)
3. Check threshold
4. Calculate net areas (sorting optional)
5. Apply area filter
6. survivors = [all polygons that pass filters]
7. filtered_polygon_count = len(survivors)  ← NEW FIELD
8. Content zone bbox = union bbox of ALL survivors
9. Return both counts
```

## Logic Validation

| User Statement | Assessment | Evidence |
|----------------|------------|----------|
| "largest polygon filter is no longer required" | **Correct** | Current code at line 1131-1150 selects max net area |
| "ONLY filters are min_area and min_side" | **Correct** | No other filtering exists after these two |
| "min_area uses net area calculation" | **Correct** | Line 1109: `if net_area >= min_area_filter` |
| "Excel shows polygon count after filter" | **Correct** | Line 1116: `polygon_count = len(net_areas)` after filtering |
| "Field is for original count" | **Needs change** | Current behavior contradicts this intent |
| "Add Filtered Block Polygon Count" | **Recommended** | New field `block_filtered_polygon_count` |

## Semantic Clarification

The current `polygon_count` field has ambiguous meaning:
- **Current behavior**: Count after ALL filtering (side + area)
- **User's intent**: Original count BEFORE any filtering

Recommended field naming:
- `block_polygon_count` → Original paint-bucket region count (before any filtering)
- `block_filtered_polygon_count` → Surviving polygon count (after all filtering)

## Implementation Summary

### Changes Required

1. **geometry.py** - `_detect_content_zone()`:
   - Store `original_polygon_count` before filtering
   - After filtering, use ALL survivors for union bbox (remove max_net_area selection)
   - Return both `polygon_count` (original) and new `filtered_polygon_count`

2. **types.py** - `ContentZoneData`:
   - Add `filtered_polygon_count: int` field

3. **constants.py**:
   - Add `EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: str = "block_filtered_polygon_count"`

4. **excel_writer.py**:
   - Add new column for filtered count

## Recommendations

1. **Preserve current net area calculation** - Still needed for min_area_filter comparison
2. **Simplify `_calculate_net_areas()`** - Sorting becomes optional since we don't need max; however, keeping it sorted doesn't hurt
3. **Clear field semantics** - Document that `polygon_count` = original, `filtered_polygon_count` = after filters
4. **Consider edge cases** - When 0 survivors after filtering, content zone detection fails (already handled)

## Next Steps

1. Add `filtered_polygon_count` field to `ContentZoneData` TypedDict
2. Add corresponding Excel column constant
3. Modify `_detect_content_zone()` to:
   - Capture original count before any filtering
   - Use union bbox of all survivors (not just max net area ones)
   - Return both original and filtered counts
4. Update `excel_writer.py` to output both fields
5. Update tests to verify new behavior
