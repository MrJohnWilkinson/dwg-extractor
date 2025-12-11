# Gap Bridge Alternative Approach Implementation Plan

## Executive Summary

This plan implements the Alternative Approach for gap bridging from `ai_output/040-alternative-approach-gap-bridge-analysis.md` with a critical modification: **Precision Fix and Gap Bridge are mutually exclusive options**. Both options solve the same problem (closing small gaps in polygon edges for accurate polygon counts) using different snapping strategies. Mutual exclusivity is enforced at the GUI level (single source of truth) with the backend trusting the inputs.

## Table Summary

| Step | File | Change Type | Description |
|------|------|-------------|-------------|
| 0 | `app/main.py` | Modify | GUI checkbox callbacks enforce mutual exclusivity |
| 1 | `app/core/geometry.py` | Modify | Implement pre-union snapping for gap bridge (Alternative Approach) |
| 2 | `app/core/geometry.py` | Update | Update docstrings to reflect mutual exclusivity and unified purpose |
| 3 | `app/tests/core/test_geometry.py` | Modify | Update geometry tests for new gap bridge implementation |
| 4 | `app/core/constants.py` | Update | Update docstring comments about gap bridge purpose |
| 5 | Run | Test | Execute full test suite to verify no regressions |

## In-Scope

- **GUI mutual exclusivity**: Modify checkbox callbacks so checking one unchecks the other
- Implement Alternative Approach in `_extract_paint_bucket_regions()` for gap bridge
- Update docstrings to reflect:
  - Mutual exclusivity of precision fix and gap bridge
  - Both options solve the same problem: closing small gaps for accurate polygon counts
- Update existing tests to work with new gap bridge implementation
- Run and pass all existing tests

## Out-of-Scope

- Changes to GUI layout or visual appearance (checkboxes stay as checkboxes)
- Changes to `get_snap_tolerances()` logic (GUI enforces exclusivity, backend trusts inputs)
- Changes to default tolerance values
- Changes to unit detection logic
- Changes to polygon filtering logic
- Adding new test files
- Performance optimizations
- Changes to Excel output

## Relevant Files

- **`app/main.py:676-705`** - `_on_precision_fix_toggle()` and `_on_gap_bridge_toggle()` callbacks to modify for mutual exclusivity.
- **`app/main.py:87-90`** - BooleanVar definitions for `precision_fix_var` and `gap_bridge_var`.
- **`app/core/geometry.py:645-715`** - `_extract_paint_bucket_regions()` function containing the two-stage snapping. Gap bridge implementation changes here.
- **`app/core/geometry.py:541-560`** - `_snap_linestring_coords()` function showing the precision fix pattern to follow for gap bridge.
- **`app/core/constants.py:217-237`** - `DEFAULT_GAP_BRIDGE_TOLERANCE` docstring incorrectly describes purpose as "intentional design gaps".
- **`app/tests/core/test_geometry.py:1110-1185`** - Tests for Stage 2 gap bridge tolerance functionality.

## Implementation Steps (Sequential Order)

### Step 0: Enforce Mutual Exclusivity in GUI Callbacks

**File:** `app/main.py`

**Modify `_on_precision_fix_toggle()` (line 676):**
```python
def _on_precision_fix_toggle(self) -> None:
    """Handle precision fix checkbox toggle."""
    enabled = self.precision_fix_var.get()
    self.logger.debug(f"Precision fix toggled: {enabled}")

    if enabled:
        # Mutual exclusivity: uncheck gap bridge when precision fix is enabled
        if self.gap_bridge_var.get():
            self.gap_bridge_var.set(False)
            self.gap_bridge_entry.configure(state="disabled")
            self.logger.debug("Gap bridge disabled (mutual exclusivity)")
        self.precision_fix_entry.configure(state="normal")
        self._update_precision_fix_default()
    else:
        self.precision_fix_entry.configure(state="disabled")
```

**Modify `_on_gap_bridge_toggle()` (line 696):**
```python
def _on_gap_bridge_toggle(self) -> None:
    """Handle gap bridge checkbox toggle."""
    enabled = self.gap_bridge_var.get()
    self.logger.debug(f"Gap bridge toggled: {enabled}")

    if enabled:
        # Mutual exclusivity: uncheck precision fix when gap bridge is enabled
        if self.precision_fix_var.get():
            self.precision_fix_var.set(False)
            self.precision_fix_entry.configure(state="disabled")
            self.logger.debug("Precision fix disabled (mutual exclusivity)")
        self.gap_bridge_entry.configure(state="normal")
        self._update_gap_bridge_default()
    else:
        self.gap_bridge_entry.configure(state="disabled")
```

**Rationale:**
- Single source of truth at the GUI level
- User immediately sees visual feedback (other checkbox unchecks)
- Backend code (`get_snap_tolerances()`) remains unchanged - trusts that inputs are already mutually exclusive
- No hidden logic surprises - what user sees is what gets processed

### Step 1: Implement Alternative Approach in `_extract_paint_bucket_regions()`

**File:** `app/core/geometry.py`

**Current code (lines 687-702):**
```python
# Stage 1: Precision snapping BEFORE union to fix floating-point artifacts
if precision_tolerance > 0:
    edges = [_snap_linestring_coords(e, precision_tolerance) for e in edges]
    logger.debug(f"Applied Stage 1 precision snap: tolerance={precision_tolerance}")

# Merge and split at all intersections (now with snapped coordinates)
merged = unary_union(edges)
if merged.is_empty:
    return []

# Stage 2: Gap bridging for intentional design gaps (when enabled)
if gap_bridge_tolerance > 0:
    merged = snap(merged, merged, gap_bridge_tolerance)
    logger.debug(f"Applied Stage 2 gap bridge: tolerance={gap_bridge_tolerance}")
```

**Replace with:**
```python
# Precision Fix: snap individual edge coordinates to grid BEFORE union
# Fixes floating-point artifacts at line endpoints
if precision_tolerance > 0:
    edges = [_snap_linestring_coords(e, precision_tolerance) for e in edges]
    logger.debug(f"Applied precision fix snap: tolerance={precision_tolerance}")

# Gap Bridge: snap individual edges to reference geometry BEFORE union
# Alternative method for closing gaps using Shapely's snap() function
# Note: Mutually exclusive with precision fix (GUI enforces this)
if gap_bridge_tolerance > 0:
    all_edges_geom = unary_union(edges)
    edges = [snap(e, all_edges_geom, gap_bridge_tolerance) for e in edges]
    logger.debug(f"Applied gap bridge snap: tolerance={gap_bridge_tolerance}")

# Merge and split at all intersections
merged = unary_union(edges)
if merged.is_empty:
    return []
```

**Key changes:**
- Gap bridge now uses pre-union snapping (same pattern as precision fix)
- Creates reference geometry with `unary_union(edges)`, then snaps each edge to it
- Removed "Stage 1/Stage 2" terminology - now just two alternative methods
- Final `unary_union(edges)` is the single authoritative intersection computation

### Step 2: Update Docstrings in `geometry.py`

**File:** `app/core/geometry.py`

**Update function docstring (lines 651-677):**

**Current:**
```python
"""
Extract all visual regions using paint-bucket algorithm.

Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
splits at intersections using unary_union, applies two-stage
coordinate snapping, and finds all closed regions using polygonize.

Two-stage snapping:
- Stage 1 (Precision): Automatically fixes floating-point artifacts at
  line endpoints using a very small tolerance (nanometer scale).
- Stage 2 (Gap Bridge): Optionally bridges intentional design gaps when
  gap_bridge_tolerance > 0.
...
"""
```

**Replace with:**
```python
"""
Extract all visual regions using paint-bucket algorithm.

Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
splits at intersections using unary_union, and finds all closed
regions using polygonize.

Gap Closure Methods (mutually exclusive - only one should be enabled):
- Precision Fix: Snaps individual edge coordinates to a grid to fix
  floating-point artifacts. Uses small tolerances (e.g., 0.01mm).
- Gap Bridge: Snaps individual edges to nearby geometry using Shapely's
  snap() function. Uses larger tolerances for visible coordinate gaps.

Both methods apply BEFORE the union operation to ensure clean
intersection detection. The GUI enforces mutual exclusivity.

Args:
    block_def: ezdxf block definition object
    abort_event: Optional threading.Event to signal abort request
    precision_tolerance: Precision fix tolerance for coordinate grid snapping.
        Set to 0 to disable. Mutually exclusive with gap_bridge_tolerance.
    gap_bridge_tolerance: Gap bridge tolerance for snapping edges to nearby
        geometry. Set to 0 to disable. Mutually exclusive with precision_tolerance.

Returns:
    List of Polygon objects (coordinate tuples) representing all visual regions.

Raises:
    GeometryAbortedError: If abort_event is set during processing.
"""
```

### Step 3: Update Tests in `test_geometry.py`

**File:** `app/tests/core/test_geometry.py`

**Update `TestGapBridgeTolerance` class (lines 1110-1185):**

Since gap bridge now uses pre-union snapping, tests need to:
1. Pass `precision_tolerance=0` when testing gap bridge (mutual exclusivity)
2. Verify the new implementation produces valid polygons
3. Update `test_both_tolerances_combined()` to `test_gap_bridge_standalone()` or remove it

**Specific changes:**

```python
# Update test_stage2_disabled_by_default - now just tests default behavior
def test_gap_bridge_disabled_by_default(self) -> None:
    """Test that default gap_bridge_tolerance=0.0 doesn't modify geometry."""
    # ... keep existing test, rename from stage2 terminology

# Update test_stage2_tolerance_parameter_accepted
def test_gap_bridge_tolerance_parameter_accepted(self) -> None:
    """Test that gap_bridge_tolerance parameter is accepted."""
    # Change: use precision_tolerance=0 since they're mutually exclusive
    regions_zero = _extract_paint_bucket_regions(
        block, precision_tolerance=0, gap_bridge_tolerance=0.0
    )
    regions_small = _extract_paint_bucket_regions(
        block, precision_tolerance=0, gap_bridge_tolerance=0.5
    )
    # ...

# Remove or rename test_both_tolerances_combined
def test_gap_bridge_standalone(self) -> None:
    """Test gap bridge with precision fix disabled (mutual exclusivity)."""
    # Test gap bridge in isolation
    regions = _extract_paint_bucket_regions(
        block, precision_tolerance=0, gap_bridge_tolerance=0.5
    )
    assert len(regions) == 1
```

### Step 4: Update Docstring in `constants.py`

**File:** `app/core/constants.py`

**Update comment at lines 217-218:**

**Current:**
```python
# Stage 2: Default gap bridge tolerances for intentional gap bridging
# These represent typical small gaps in CAD drawings that users may want to bridge
DEFAULT_GAP_BRIDGE_TOLERANCE: dict[int, float] = {
```

**Replace with:**
```python
# Default gap bridge tolerances for closing small gaps in polygon edges.
# Gap Bridge is an alternative to Precision Fix - both close gaps for accurate
# polygon counts. Gap Bridge uses larger tolerances suitable for visible
# coordinate discrepancies in CAD drawings. Mutually exclusive with Precision Fix.
DEFAULT_GAP_BRIDGE_TOLERANCE: dict[int, float] = {
```

### Step 5: Run Full Test Suite

**Commands:**
```bash
uv run pytest app/tests/ -v
uv run mypy app/
uv run ruff check app/
```

**Expected:** All tests pass, no type errors, no lint warnings.

## Verification Checklist

- [ ] GUI: Checking Precision Fix unchecks Gap Bridge (and vice versa)
- [ ] GUI: Entry fields enable/disable correctly with mutual exclusivity
- [ ] Gap bridge uses pre-union snapping (Alternative Approach pattern)
- [ ] Docstrings document mutual exclusivity and unified purpose
- [ ] Tests updated to use `precision_tolerance=0` when testing gap bridge
- [ ] Full test suite passes
- [ ] Type checking passes
- [ ] Linting passes

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| User confusion about mutual exclusivity | Visual feedback immediate - unchecking happens on click |
| Breaking existing CLI/API usage | Backend unchanged - only GUI enforces exclusivity |
| Performance regression | Alternative Approach has similar performance (same number of union ops) |
| Test coverage gaps | Update existing tests rather than removing them |

## Design Decision: GUI Enforcement vs Backend Enforcement

**Chosen: GUI Enforcement (Single Source of Truth)**

| Aspect | GUI Enforcement | Backend Enforcement |
|--------|-----------------|---------------------|
| User feedback | Immediate visual | Silent (user may not know one was ignored) |
| Code complexity | Simple callback change | Logic in `get_snap_tolerances()` |
| API compatibility | CLI/API still accepts both | CLI/API gets one zeroed out |
| Debugging | Clear state visible | Hidden transformation |

GUI enforcement is cleaner because:
1. User sees exactly what will be processed
2. No hidden logic that silently modifies inputs
3. Backend code stays simple and trusts its inputs
4. Easier to test (just test the callbacks)

## Next Steps

After implementation:
1. Manual testing with sample DXF files to verify polygon counts with each method
2. Verify GUI behavior feels natural (no jarring checkbox changes)
3. Consider adding tooltip explaining mutual exclusivity if users are confused
