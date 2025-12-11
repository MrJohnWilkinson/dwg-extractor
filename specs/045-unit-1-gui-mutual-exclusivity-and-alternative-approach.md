# Feature: GUI Mutual Exclusivity and Alternative Approach for Gap Bridge

## Feature Description
Implement mutual exclusivity between Precision Fix and Gap Bridge checkboxes in the GUI, and change the Gap Bridge algorithm from post-union snapping to pre-union snapping (matching the pattern used by Precision Fix). This ensures users can only select one approach at a time while making both approaches consistent in their implementation strategy.

## User Story
As a CAD technician extracting block data from DXF files
I want Precision Fix and Gap Bridge to be mutually exclusive options
So that I can clearly choose one coordinate correction approach without confusion about their interaction

## Problem Statement
Currently, Precision Fix and Gap Bridge can both be enabled simultaneously, which could lead to unexpected behavior or confusion about which approach is being applied. Additionally, Gap Bridge uses a different algorithm pattern (post-union snapping) compared to Precision Fix (pre-union snapping), making their behavior inconsistent and harder to reason about.

## Solution Statement
1. **GUI Mutual Exclusivity**: When either checkbox is enabled, automatically disable the other. This provides clear visual feedback and prevents conflicting settings.
2. **Alternative Approach for Gap Bridge**: Change Gap Bridge from post-union snapping (`snap(merged, merged, tolerance)`) to pre-union snapping (same pattern as Precision Fix). This makes both approaches consistent alternative methods for coordinate correction.

## Relevant Files
Use these files to implement the feature:

- **`app/main.py`** (lines 676-715) - Contains `_on_precision_fix_toggle()` and `_on_gap_bridge_toggle()` callback methods that need modification to enforce mutual exclusivity
- **`app/core/geometry.py`** (lines 645-715) - Contains `_extract_paint_bucket_regions()` function where Gap Bridge algorithm needs to change from post-union to pre-union snapping
- **`app/tests/core/test_geometry.py`** - Contains unit tests for geometry functions including `_extract_paint_bucket_regions()`
- **`app/tests/core/extractor/test_extractor_precision_fix.py`** - Contains tests for precision fix toggle; pattern to follow for mutual exclusivity tests

## Implementation Plan
### Phase 1: Foundation
- Understand the current toggle callback implementations in `app/main.py`
- Review the current Gap Bridge algorithm in `_extract_paint_bucket_regions()`
- Identify test patterns for toggle behavior

### Phase 2: Core Implementation
- Modify `_on_precision_fix_toggle()` to uncheck and disable Gap Bridge when Precision Fix is enabled
- Modify `_on_gap_bridge_toggle()` to uncheck and disable Precision Fix when Gap Bridge is enabled
- Replace Gap Bridge's post-union snapping with pre-union snapping in `_extract_paint_bucket_regions()`
- Update docstrings to remove "Stage 1/Stage 2" terminology

### Phase 3: Integration
- Ensure logging captures mutual exclusivity actions
- Verify the new Gap Bridge algorithm produces correct results
- Run existing tests to confirm no regressions

## Step by Step Tasks

### Step 0: Modify `_on_precision_fix_toggle()` for Mutual Exclusivity

**File:** `app/main.py` (line 676)

- When precision fix is enabled (`enabled = True`), check if gap bridge is currently checked
- If gap bridge is checked, uncheck it by setting `self.gap_bridge_var.set(False)` and disable its entry field
- Add debug log message: `"Disabled gap bridge (mutually exclusive with precision fix)"`

**Modified code structure:**
```python
def _on_precision_fix_toggle(self) -> None:
    """Handle precision fix checkbox toggle."""
    enabled = self.precision_fix_var.get()
    self.logger.debug(f"Precision fix toggled: {enabled}")

    if enabled:
        self.precision_fix_entry.configure(state="normal")
        self._update_precision_fix_default()
        # Mutual exclusivity: disable gap bridge when precision fix is enabled
        if self.gap_bridge_var.get():
            self.gap_bridge_var.set(False)
            self.gap_bridge_entry.configure(state="disabled")
            self.logger.debug("Disabled gap bridge (mutually exclusive with precision fix)")
    else:
        self.precision_fix_entry.configure(state="disabled")
```

### Step 1: Modify `_on_gap_bridge_toggle()` for Mutual Exclusivity

**File:** `app/main.py` (line 696)

- When gap bridge is enabled (`enabled = True`), check if precision fix is currently checked
- If precision fix is checked, uncheck it by setting `self.precision_fix_var.set(False)` and disable its entry field
- Add debug log message: `"Disabled precision fix (mutually exclusive with gap bridge)"`

**Modified code structure:**
```python
def _on_gap_bridge_toggle(self) -> None:
    """Handle gap bridge checkbox toggle."""
    enabled = self.gap_bridge_var.get()
    self.logger.debug(f"Gap bridge toggled: {enabled}")

    if enabled:
        self.gap_bridge_entry.configure(state="normal")
        self._update_gap_bridge_default()
        # Mutual exclusivity: disable precision fix when gap bridge is enabled
        if self.precision_fix_var.get():
            self.precision_fix_var.set(False)
            self.precision_fix_entry.configure(state="disabled")
            self.logger.debug("Disabled precision fix (mutually exclusive with gap bridge)")
    else:
        self.gap_bridge_entry.configure(state="disabled")
```

### Step 2: Implement Alternative Approach in `_extract_paint_bucket_regions()`

**File:** `app/core/geometry.py` (lines 687-702)

**Current code to replace:**
```python
# Stage 1: Precision snapping BEFORE union to fix floating-point artifacts
# This ensures endpoints with nanometer-scale errors align to grid points
# before intersection detection occurs in unary_union()
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
# Note: Mutually exclusive with gap bridge (GUI enforces this)
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

# Single authoritative intersection computation via unary_union
merged = unary_union(edges)
if merged.is_empty:
    return []
```

### Step 3: Update Docstring for `_extract_paint_bucket_regions()`

**File:** `app/core/geometry.py` (lines 651-678)

Update the docstring to remove "Stage 1/Stage 2" terminology and describe the two methods as alternative approaches:

**Replace:**
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

Args:
    block_def: ezdxf block definition object
    abort_event: Optional threading.Event to signal abort request
    precision_tolerance: Stage 1 snap tolerance for fixing floating-point
        artifacts. Default 1e-6 (appropriate for most unit systems).
        Set to 0 to disable Stage 1 snapping.
    gap_bridge_tolerance: Stage 2 snap tolerance for bridging intentional
        gaps. Default 0.0 (disabled). Set > 0 to bridge gaps up to this size.

Returns:
    List of Polygon objects (coordinate tuples) representing all visual regions.

Raises:
    GeometryAbortedError: If abort_event is set during processing.
"""
```

**With:**
```python
"""
Extract all visual regions using paint-bucket algorithm.

Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
splits at intersections using unary_union, and finds all closed
regions using polygonize.

Two alternative pre-union snapping methods (mutually exclusive):
- Precision Fix: Snaps individual edge coordinates to grid points to fix
  floating-point artifacts. Uses _snap_linestring_coords() for direct
  coordinate rounding.
- Gap Bridge: Snaps individual edges to reference geometry to bridge
  intentional design gaps. Uses Shapely's snap() function against a
  reference geometry created from all edges.

Args:
    block_def: ezdxf block definition object
    abort_event: Optional threading.Event to signal abort request
    precision_tolerance: Precision fix snap tolerance for fixing floating-point
        artifacts. Default 1e-6 (appropriate for most unit systems).
        Set to 0 to disable. Mutually exclusive with gap_bridge_tolerance.
    gap_bridge_tolerance: Gap bridge snap tolerance for bridging intentional
        gaps. Default 0.0 (disabled). Set > 0 to bridge gaps up to this size.
        Mutually exclusive with precision_tolerance.

Returns:
    List of Polygon objects (coordinate tuples) representing all visual regions.

Raises:
    GeometryAbortedError: If abort_event is set during processing.
"""
```

### Step 4: Run Tests and Validate

Run the validation commands to ensure all changes work correctly with zero regressions.

## Testing Strategy
### Unit Tests
- Existing tests in `app/tests/core/test_geometry.py` cover `_extract_paint_bucket_regions()` behavior
- Existing tests in `app/tests/core/extractor/test_extractor_precision_fix.py` cover precision fix toggle behavior
- The mutual exclusivity is GUI-level logic that is difficult to unit test without mocking tkinter

### Integration Tests
- The existing extraction tests will validate that both precision fix and gap bridge continue to work correctly
- The algorithm change for gap bridge should produce equivalent or better results for closing gaps

### Edge Cases
- Both checkboxes disabled: Should work normally with no snapping
- Precision fix enabled then gap bridge enabled: Gap bridge should auto-disable precision fix
- Gap bridge enabled then precision fix enabled: Precision fix should auto-disable gap bridge
- Rapid toggling between options: Should maintain consistent state

### Playwright MCP Tests
- Not applicable for this feature as it involves desktop GUI behavior, not web UI

## Acceptance Criteria
- [ ] When Precision Fix checkbox is enabled, Gap Bridge checkbox is automatically unchecked and its entry field is disabled
- [ ] When Gap Bridge checkbox is enabled, Precision Fix checkbox is automatically unchecked and its entry field is disabled
- [ ] Debug log messages are emitted when mutual exclusivity is enforced
- [ ] Gap Bridge now uses pre-union snapping (snap individual edges to reference geometry before unary_union)
- [ ] The "Stage 1/Stage 2" terminology is removed from code comments and docstrings
- [ ] All existing tests pass with zero regressions
- [ ] Type checking passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate paint bucket region extraction
- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run precision fix tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run mypy app/` - Run type checking to ensure type safety
- `uv run ruff check app/` - Run linter to ensure code quality

## Notes
- The GUI mutual exclusivity is enforced at the callback level, not through tkinter's built-in mechanisms, for better logging and control
- The gap bridge algorithm change from post-union to pre-union snapping aligns its implementation pattern with precision fix, making both approaches conceptually similar
- Both approaches now operate on individual edges before the final `unary_union()` call, which is the single authoritative intersection computation
- Future consideration: Could add a visual indicator (e.g., grouped radio buttons) to make the mutual exclusivity more obvious in the UI
