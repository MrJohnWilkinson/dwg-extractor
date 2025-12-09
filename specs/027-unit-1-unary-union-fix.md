# Chore: Unit 1 - Unary Union Fix for Line Cycle Detection

## Chore Description
Modify the `_extract_line_cycles()` function in the geometry module to use Shapely's `unary_union()` preprocessing before `polygonize()`. This fix ensures that LINE segments are properly split at T-junctions and crossing points, enabling correct polygon detection for complex CAD block geometries where lines intersect but were not originally split at intersection points.

The current implementation passes LINE segments directly to `polygonize()`, which cannot detect closed cycles when lines cross without being explicitly split at intersection points. By first applying `unary_union()`, all lines are merged and automatically split at every intersection point, allowing `polygonize()` to correctly identify all closed polygons.

## Relevant Files
Use these files to resolve the chore:

- `app/core/geometry.py` - Contains the `_extract_line_cycles()` function (lines 526-573) that needs modification. The `unary_union` import already exists at line 29.
- `app/tests/core/test_geometry.py` - Contains existing geometry tests to validate no regressions occur.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify unary_union Import Exists
- File: `app/core/geometry.py`
- Line 29 should contain: `from shapely.ops import polygonize, unary_union`
- This is a read-only verification step - no code change required
- If import is missing, add `unary_union` to the existing import statement

### Step 2: Modify `_extract_line_cycles()` Function
- File: `app/core/geometry.py`
- Location: Lines 562-573 (inside the `_extract_line_cycles()` function)
- Replace the current polygonize code block with unary_union preprocessing

**Current Code to Replace (lines 562-573):**
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

**Key Changes Explained:**
1. **Line 1-3**: Apply `unary_union(lines)` to merge all lines and split them at intersection points. Return early if result is empty.
2. **Line 5-6**: Extract individual line segments from the merged result. `unary_union` returns either a single `LineString` (if all lines form one connected component) or a `MultiLineString` (if multiple disconnected components exist). The `hasattr(merged, 'geoms')` check handles both cases.
3. **Line 8**: Pass the properly split `line_segments` to `polygonize()` instead of the original unsplit `lines`.
4. **Lines 10-18**: Unchanged - conversion to internal Polygon format and logging.

### Step 3: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions
- All tests must pass before considering the chore complete

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate the unary_union changes work correctly with no regressions.
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no side effects in other modules.
- `uv run mypy app/` - Run type checker to ensure no type errors introduced.
- `uv run ruff check app/` - Run linter to ensure code quality standards are maintained.

## Notes
- The `unary_union` import is already present at line 29, so no import changes are needed.
- This change is purely additive preprocessing - the output format remains identical.
- The function signature and return type remain unchanged.
- Performance impact is minimal: `unary_union` is a GEOS-optimized operation that runs in near-linear time for typical CAD geometries.
- Edge cases handled:
  - Empty result from `unary_union`: Returns empty list immediately
  - Single LineString (non-multi geometry): Wraps in list via conditional
  - MultiLineString: Extracts all component geometries via `.geoms`
