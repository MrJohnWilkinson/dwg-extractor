# Chore: Enforce Mutual Exclusivity Between Precision Fix and Gap Bridge Options

## Chore Description
Enforce mutual exclusivity between the Precision Fix and Gap Bridge options in the GUI. When one option is enabled, the other should be automatically disabled. This ensures users cannot accidentally enable both features simultaneously, as they represent alternative approaches to closing gaps for accurate polygon counts.

Additionally, update the docstrings in `geometry.py` and `constants.py` to clearly document this mutual exclusivity relationship, explaining that both methods achieve similar goals (closing gaps for polygon detection) but use different approaches and tolerances.

## Relevant Files
Use these files to resolve the chore:

- **`app/main.py`** (lines 676-705) - Contains the GUI callback methods `_on_precision_fix_toggle()` and `_on_gap_bridge_toggle()` that need to be modified to enforce mutual exclusivity when either option is enabled.

- **`app/core/geometry.py`** (lines 651-678) - Contains the `_extract_paint_bucket_regions()` function with the main docstring that needs to be updated to document the mutual exclusivity between Precision Fix and Gap Bridge, replacing the current "two-stage snapping" documentation.

- **`app/core/constants.py`** (lines 217-229) - Contains the `DEFAULT_GAP_BRIDGE_TOLERANCE` constant with comments that need to be updated to document that Gap Bridge is an alternative to Precision Fix rather than a "Stage 2" process.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_on_precision_fix_toggle()` in `app/main.py`

Modify the `_on_precision_fix_toggle()` method at line 676 to disable Gap Bridge when Precision Fix is enabled:

- When `enabled` is `True`, check if `self.gap_bridge_var.get()` is also `True`
- If Gap Bridge is enabled, set `self.gap_bridge_var.set(False)` to uncheck it
- Disable the gap bridge entry field with `self.gap_bridge_entry.configure(state="disabled")`
- Log the mutual exclusivity action with `self.logger.debug("Gap bridge disabled (mutual exclusivity)")`

**Target code change:**
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

### Step 2: Update `_on_gap_bridge_toggle()` in `app/main.py`

Modify the `_on_gap_bridge_toggle()` method at line 696 to disable Precision Fix when Gap Bridge is enabled:

- When `enabled` is `True`, check if `self.precision_fix_var.get()` is also `True`
- If Precision Fix is enabled, set `self.precision_fix_var.set(False)` to uncheck it
- Disable the precision fix entry field with `self.precision_fix_entry.configure(state="disabled")`
- Log the mutual exclusivity action with `self.logger.debug("Precision fix disabled (mutual exclusivity)")`

**Target code change:**
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

### Step 3: Update docstring in `app/core/geometry.py`

Replace the docstring for `_extract_paint_bucket_regions()` function (lines 651-678) to document mutual exclusivity between the two gap closure methods:

**Replace current docstring with:**
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

### Step 4: Update comment in `app/core/constants.py`

Replace the comment block at lines 217-218 (above `DEFAULT_GAP_BRIDGE_TOLERANCE`) to document that Gap Bridge is an alternative to Precision Fix:

**Replace:**
```python
# Stage 2: Default gap bridge tolerances for intentional gap bridging
# These represent typical small gaps in CAD drawings that users may want to bridge
```

**With:**
```python
# Default gap bridge tolerances for closing small gaps in polygon edges.
# Gap Bridge is an alternative to Precision Fix - both close gaps for accurate
# polygon counts. Gap Bridge uses larger tolerances suitable for visible
# coordinate discrepancies in CAD drawings. Mutually exclusive with Precision Fix.
```

### Step 5: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests to validate no regressions
- `uv run mypy app/` - Run type checking to ensure type safety
- `uv run ruff check app/` - Run linter to ensure code quality

## Notes
- The mutual exclusivity is enforced at the GUI level only. The underlying `_extract_paint_bucket_regions()` function still accepts both parameters, but the GUI prevents users from enabling both simultaneously.
- This change aligns with the Gap Bridge Alternative Approach plan where Precision Fix and Gap Bridge are treated as alternative methods for achieving the same goal (closing gaps for accurate polygon counts).
- The docstring updates remove references to "two-stage snapping" and "Stage 1/Stage 2" terminology, which implied the features worked together sequentially rather than as alternatives.
