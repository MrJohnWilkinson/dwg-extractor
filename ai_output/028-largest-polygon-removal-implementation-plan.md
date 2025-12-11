# Largest Polygon Selection Removal: Implementation Plan

## Executive Summary

This plan details the sequential implementation steps to remove the "largest polygon wins" logic from content zone detection. The change shifts from selecting polygons with maximum net area to using ALL surviving polygons equally for content zone bounding box calculation. Four files require modifications, with clear in-scope and out-of-scope boundaries.

## Table Summary

| Step | File | Change | Effort |
|------|------|--------|--------|
| 1 | `app/core/types.py` | Add `filtered_polygon_count` field to `ContentZoneData` | Low |
| 2 | `app/core/constants.py` | Add `EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT` constant | Low |
| 3 | `app/core/geometry.py` | Refactor `_detect_content_zone()` to use all survivors | Medium |
| 4 | `app/core/excel_writer.py` | Add filtered count column to output | Low |
| 5 | `app/tests/` | Update existing tests, add new test cases | Medium |

## Scope Definition

### In Scope

- Add `filtered_polygon_count` field to `ContentZoneData` TypedDict
- Add corresponding Excel column constant
- Modify `_detect_content_zone()` to:
  - Preserve original polygon count before filtering
  - Remove max net area selection logic (lines 1130-1159)
  - Use union bounding box of ALL surviving polygons
  - Return both original and filtered counts
- Update `excel_writer.py` to output both polygon counts
- Update docstrings to reflect new semantics
- Update unit tests for changed behavior

### Out of Scope

- Changes to `_calculate_net_areas()` sorting behavior (keep as-is)
- GUI changes
- Performance optimizations
- Changes to min_area_filter or min_side_filter logic
- Changes to net area calculation algorithm

## Relevant Files

- **`app/core/types.py:195-228`** - `ContentZoneData` TypedDict; add `filtered_polygon_count` field
- **`app/core/constants.py:115`** - Excel column constants; add new constant
- **`app/core/geometry.py:983-1187`** - `_detect_content_zone()` function; main logic changes
- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()`; no changes needed (sorting preserved)
- **`app/core/excel_writer.py:657-722`** - Excel output; add new column
- **`app/tests/core/extractor/test_extractor_polygon_filter.py`** - Update assertions
- **`app/tests/core/test_geometry.py`** - Update geometry test assertions
- **`app_docs/005-field-naming-convention.md`** - Reference for field naming

## Implementation Steps

### Step 1: Update TypedDict (types.py)

**File:** `app/core/types.py`

**Changes:**
1. Add `filtered_polygon_count: int` field to `ContentZoneData` TypedDict
2. Update docstring to clarify semantics:
   - `polygon_count` = Original count BEFORE any filtering
   - `filtered_polygon_count` = Count AFTER all filtering (side + area)

**Code Location:** Lines 195-228

**New Field Definition:**
```python
polygon_count: int  # Original count before filtering
filtered_polygon_count: int  # Count after side and area filters applied
```

### Step 2: Add Excel Column Constant (constants.py)

**File:** `app/core/constants.py`

**Changes:**
1. Add new constant after line 115:
```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: str = "block_filtered_polygon_count"
```

**Naming Convention:** Follows `app_docs/005-field-naming-convention.md`:
- Domain: `block`
- Attribute: `filtered_polygon_count`
- Pattern: `{domain}_{attribute}`

### Step 3: Refactor Content Zone Detection (geometry.py)

**File:** `app/core/geometry.py`

**Function:** `_detect_content_zone()` (lines 983-1187)

**Changes Required:**

#### 3a. Store Original Count (line 1060)
```python
# Current
polygon_count = len(all_shapes)

# Change to
original_polygon_count = len(all_shapes)
```

#### 3b. Update Side Filter Section (lines 1065-1076)
```python
# Current (overwrites polygon_count)
polygon_count = len(all_shapes)

# Change to: Remove this line, don't update original_polygon_count
```

#### 3c. Update Threshold Check (lines 1078-1080)
```python
# Current
if polygon_count == 0:

# Change to
if len(all_shapes) == 0:
```

#### 3d. Update Threshold Warning (lines 1083-1097)
```python
# Current
if polygon_count > POLYGON_COUNT_THRESHOLD:

# Change to
if len(all_shapes) > POLYGON_COUNT_THRESHOLD:
```

And update return to include both counts:
```python
polygon_count=original_polygon_count,
filtered_polygon_count=len(all_shapes),
```

#### 3e. Update Area Filter Section (lines 1104-1116)
```python
# Current (overwrites polygon_count)
polygon_count = len(net_areas)

# Change to: Remove this line
```

#### 3f. Remove Max Net Area Selection (lines 1130-1159)
**DELETE** the following logic:
```python
# Find maximum net area value (already sorted descending)
max_net_area = net_areas[0][1]

# Skip if content zone has zero or negative area
if max_net_area <= 0:
    ...

# Find all shapes tied for maximum net area
tied_shapes = [shape for shape, net_area in net_areas if net_area == max_net_area]

# Determine content zone bounding box
if len(tied_shapes) == 1:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(tied_shapes[0])
else:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(tied_shapes)
```

**REPLACE WITH:**
```python
# Get all surviving polygons (passed both side and area filters)
survivors = [poly for poly, net_area in net_areas]

# Determine content zone bounding box from ALL survivors
if len(survivors) == 1:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(survivors[0])
else:
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(survivors)

filtered_polygon_count = len(survivors)
```

#### 3g. Update All Return Statements
All `ContentZoneData` return statements must include both counts:
```python
polygon_count=original_polygon_count,
filtered_polygon_count=filtered_polygon_count,
```

**Note:** For early returns before filtering begins (threshold exceeded, no shapes found), set:
- `polygon_count` = original count (or 0 if never calculated)
- `filtered_polygon_count` = 0

#### 3h. Update Function Docstring
Update docstring to remove reference to "largest net area" and clarify:
- Content zone is now union bbox of ALL surviving polygons
- `polygon_count` = original count before filtering
- `filtered_polygon_count` = count after all filters

### Step 4: Update Excel Writer (excel_writer.py)

**File:** `app/core/excel_writer.py`

**Changes:**

#### 4a. Add Import (line 41)
Add to imports:
```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
```

#### 4b. Update Data Extraction (lines 657-666)
```python
# Current
poly_count: int | str = content_zone["polygon_count"]

# Add
filtered_poly_count: int | str = content_zone["filtered_polygon_count"]
```

#### 4c. Add Column to Row Dict (line 690)
Add after `EXCEL_COLUMN_BLOCK_POLYGON_COUNT`:
```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: filtered_poly_count,
```

#### 4d. Update Empty DataFrame Columns (line 721)
Add to columns list:
```python
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
```

### Step 5: Update Tests

**Files:** Multiple test files

#### 5a. Update Existing Test Assertions
- `app/tests/core/extractor/test_extractor_polygon_filter.py` - Update assertions for polygon_count semantics
- `app/tests/core/test_geometry.py` - Update geometry test assertions

#### 5b. Add New Test Cases
1. Test that `polygon_count` reflects original count before filtering
2. Test that `filtered_polygon_count` reflects count after filtering
3. Test union bbox calculation with multiple survivors
4. Test edge case: 1 survivor produces same bbox as single polygon
5. Test edge case: 0 survivors after filtering returns appropriate values

## Recommendations Implementation

| Recommendation | Implementation |
|----------------|----------------|
| Preserve current net area calculation | No changes to `_calculate_net_areas()` |
| Simplify `_calculate_net_areas()` | Keep sorting as-is (doesn't hurt, may help debugging) |
| Clear field semantics | Update docstrings in `ContentZoneData` TypedDict |
| Consider edge cases | Already handled: 0 survivors returns `content_zone_detected=False` |

## Edge Cases Handled

| Case | Behavior |
|------|----------|
| 0 polygons extracted | `polygon_count=0`, `filtered_polygon_count=0`, `detected=False` |
| All filtered by side | `polygon_count=original`, `filtered_polygon_count=0`, `detected=False` |
| All filtered by area | `polygon_count=original`, `filtered_polygon_count=0`, `detected=False` |
| 1 survivor | Union bbox = single polygon bbox |
| N survivors | Union bbox of all N polygons |
| Threshold exceeded | `polygon_count=original`, `filtered_polygon_count=0`, `detected=False` |

## Validation Checklist

- [ ] `polygon_count` always reflects original count before filtering
- [ ] `filtered_polygon_count` reflects count after all filters
- [ ] Content zone bbox uses ALL survivors (not just max net area)
- [ ] No reference to "largest polygon" or "max net area selection" in code
- [ ] All tests pass with updated assertions
- [ ] Excel output includes both columns
- [ ] Docstrings accurately describe new behavior

## Next Steps

1. Implement Step 1 (types.py)
2. Implement Step 2 (constants.py)
3. Implement Step 3 (geometry.py) - largest change
4. Implement Step 4 (excel_writer.py)
5. Run existing tests - expect some failures due to semantic changes
6. Update test assertions for new semantics
7. Add new test cases for coverage
8. Run full test suite to verify
