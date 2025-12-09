# Implementation Plan: Shapely `unary_union` Fix for Polygon Detection

## Executive Summary

This plan implements a 4-line fix to `app/core/geometry.py:_extract_line_cycles()` that enables correct polygon detection for T-junctions and crossing intersections. The fix adds `unary_union()` before `polygonize()` to split lines at intersection points. No new dependencies or constants required - `unary_union` is already imported.

## Table Summary

| Step | Task | File | Lines | Risk | Dependency |
|------|------|------|-------|------|------------|
| 1 | Verify import exists | `geometry.py` | 29 | None | - |
| 2 | Add `unary_union()` call | `geometry.py` | 562-563 | Low | Step 1 |
| 3 | Handle empty result | `geometry.py` | 563 | Low | Step 2 |
| 4 | Extract line segments | `geometry.py` | 564 | Low | Step 3 |
| 5 | Update polygonize call | `geometry.py` | 565 | Low | Step 4 |
| 6 | Add unit tests | `test_geometry.py` | New | None | Step 5 |
| 7 | Run test suite | - | - | None | Step 6 |
| 8 | Validate with real DXF | - | - | None | Step 7 |

## Relevant Files

- **`app/core/geometry.py:526-573`** - Target function `_extract_line_cycles()` containing the bug
- **`app/core/geometry.py:29`** - `unary_union` already imported from `shapely.ops`
- **`app/tests/core/test_geometry.py`** - Test file for geometry module (needs new tests)
- **`app/core/constants.py:146-150`** - `LINE_SEGMENT_THRESHOLD=5000` constant (no change needed)
- **`ai_output/026-shapely-unary-union-analysis.md`** - Analysis proving `unary_union()` handles both T-junctions and crossings

## In Scope

- Modify `_extract_line_cycles()` to use `unary_union()` before `polygonize()`
- Add unit tests for T-junction and crossing intersection scenarios
- Validate fix against existing test suite
- Validate fix against sample DXF files (if available)

## Out of Scope

- Custom T-junction detection code (report 025 - superseded by this fix)
- Custom crossing intersection detection (not needed - `unary_union()` handles it)
- Changes to `LINE_SEGMENT_THRESHOLD` constant (5000 is appropriate)
- Changes to `POLYGON_COUNT_THRESHOLD` constant (500 is appropriate)
- Changes to other geometry functions
- New dependencies (all required imports already present)

## Implementation Steps (Sequenced)

### Step 1: Verify Import Exists

**File:** `app/core/geometry.py:29`

Confirm `unary_union` is already imported:
```python
from shapely.ops import polygonize, unary_union
```

**Action:** Read-only verification. No code change required.

---

### Step 2: Modify `_extract_line_cycles()` Function

**File:** `app/core/geometry.py:562-573`

**Current Code (lines 562-573):**
```python
    # Polygonize finds all closed polygons from line segments
    polygons = list(polygonize(lines))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]  # Exclude closing point
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} LINE cycles via polygonize")
    return result
```

**New Code (replace lines 562-573):**
```python
    # Use unary_union to split lines at T-junctions AND crossing points
    merged = unary_union(lines)
    if merged.is_empty:
        return []

    # Handle both single LineString and MultiLineString
    line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]

    # Polygonize now works correctly with split segments
    polygons = list(polygonize(line_segments))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]  # Exclude closing point
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} LINE cycles via polygonize")
    return result
```

**Key Changes:**
1. Line 562-563: Add `merged = unary_union(lines)`
2. Line 564-565: Add empty check `if merged.is_empty: return []`
3. Line 567-568: Extract segments with `hasattr()` check for GeometryCollection
4. Line 570: Change `polygonize(lines)` to `polygonize(line_segments)`

---

### Step 3: Add Unit Tests

**File:** `app/tests/core/test_geometry.py`

Add new test class `TestExtractLineCycles` with tests for:

```python
class TestExtractLineCycles:
    """Test suite for _extract_line_cycles function."""

    def test_simple_rectangle_from_lines(self) -> None:
        """Test polygon detection from 4 lines forming a rectangle."""
        # 4 lines forming a 100x50 rectangle
        # Expected: 1 polygon

    def test_t_junction_creates_two_polygons(self) -> None:
        """Test T-junction: rectangle split by vertical divider."""
        # Rectangle + vertical divider touching top/bottom midpoints
        # Expected: 2 polygons (left and right halves)

    def test_crossing_lines_no_closed_region(self) -> None:
        """Test crossing lines (X pattern) with no closed region."""
        # Two diagonal lines crossing in center
        # Expected: 0 polygons (no closed region)

    def test_grid_pattern_multiple_polygons(self) -> None:
        """Test grid pattern with T-junctions and crossings."""
        # Rectangle + 2 horizontal lines + 1 vertical divider
        # Expected: 6 polygons
```

**Import to add:**
```python
from core.geometry import _extract_line_cycles
```

---

### Step 4: Run Test Suite

**Command:**
```bash
uv run pytest app/tests/core/test_geometry.py -v
```

**Expected:** All tests pass including new T-junction/crossing tests.

---

### Step 5: Run Full Test Suite

**Command:**
```bash
uv run pytest app/tests/ -v
```

**Expected:** No regressions in existing functionality.

---

### Step 6: Type Check

**Command:**
```bash
uv run mypy app/core/geometry.py
```

**Expected:** No type errors.

---

### Step 7: Validate with Real DXF (Optional)

If `sample-blocks.dxf` or similar test file exists with AP #5-4 pattern:

**Validation:**
- Run extraction on file
- Verify AP #5-4 block now detects expected polygon count (8 polygons per report 017)

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `unary_union` returns unexpected type | Low | Medium | `hasattr()` check handles all cases |
| Performance regression | Low | Low | `unary_union` is O(n log n), faster than O(n^2) custom code |
| Existing tests fail | Low | High | Run full test suite before merging |

## Verification Checklist

- [ ] Import `unary_union` confirmed present at line 29
- [ ] `_extract_line_cycles()` modified with 4 new lines
- [ ] New unit tests added and passing
- [ ] Full test suite passes
- [ ] Type check passes
- [ ] No linting errors

## References

- **Analysis Report:** `ai_output/026-shapely-unary-union-analysis.md`
- **Superseded Plan:** `ai_output/025-full-paint-bucket-implementation-plan.md` (custom T-junction code not needed)
- **Validation Report:** `ai_output/017-polygon-detection-validation-all-blocks.md` (AP #5-4 failure case)
