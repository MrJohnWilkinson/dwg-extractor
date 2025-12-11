# Bug: Fix _on_unit_change() to Update ALL Values Regardless of Checkbox State

## Bug Description

When users change the unit selection in the dropdown (e.g., from "Millimeters" to "Inches"), the application only updates default values for features that are currently enabled (checkboxes that are ON). Disabled features retain their previous unit's values, causing user confusion when they later enable a filter and see stale values from the previous unit system.

**Current Behavior (Incorrect):**
- User selects "Millimeters" - precision fix shows "3.0" (enabled)
- User disables precision fix, enables gap bridge - gap bridge shows "3.0" (correct for MM)
- User changes to "Inches" - only gap bridge updates to "0.125" (because it's enabled)
- User enables precision fix - still shows "3.0" (MM value) instead of "0.125" (Inches value)

**Expected Behavior (Correct):**
- When user changes units in dropdown, ALL filter defaults should update regardless of checkbox state
- Users should always see appropriate values for their selected unit system whether a filter is enabled or not
- This prevents confusion when enabling a filter after changing units

## Problem Statement

The `_on_unit_change()` method in `app/main.py` (lines 659-673) contains conditional checks that only update defaults for enabled features. This creates a state mismatch where disabled input fields retain values from the previous unit system, leading to user confusion.

## Solution Statement

Modify the `_on_unit_change()` method to unconditionally call all four update methods (`_update_precision_fix_default()`, `_update_gap_bridge_default()`, `_update_min_area_filter_default()`, `_update_min_side_filter_default()`) regardless of checkbox state. This ensures all values are always synchronized with the selected unit system.

## Steps to Reproduce

1. Launch the application
2. Select "Millimeters" as the unit (precision_fix will show "3.0")
3. Enable Precision Fix checkbox (if not already enabled)
4. Disable Precision Fix checkbox
5. Change unit selection to "Inches"
6. Re-enable Precision Fix checkbox
7. **Bug:** The value still shows "3.0" (MM value) instead of "0.125" (Inches value)

## Root Cause Analysis

The root cause is in the `_on_unit_change()` method (lines 659-673 in `app/main.py`):

```python
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change."""
    self.logger.debug(f"Unit selection changed to: {value}")
    # Update precision fix default if enabled
    if self.precision_fix_var.get():       # <-- BUG: conditional check
        self._update_precision_fix_default()
    # Update gap bridge default if enabled
    if self.gap_bridge_var.get():          # <-- BUG: conditional check
        self._update_gap_bridge_default()
    # Update min area filter default if enabled
    if self.min_area_filter_var.get():     # <-- BUG: conditional check
        self._update_min_area_filter_default()
    # Update min side filter default if enabled
    if self.min_side_filter_var.get():     # <-- BUG: conditional check
        self._update_min_side_filter_default()
```

The conditional checks (`if self.*_var.get()`) prevent updates to disabled features. When the user later enables a feature, the toggle handler calls the update method, but if the unit was changed while the feature was disabled, the stale value persists until that point.

The fix is simple: remove all four conditional checks so that all defaults are updated whenever the unit changes.

## Relevant Files

Use these files to fix the bug:

- **`app/main.py`** (lines 659-673): Contains the `_on_unit_change()` method that needs modification. The four conditional checks need to be removed so all update methods are called unconditionally.

## Step by Step Tasks

### Step 1: Modify _on_unit_change() method to remove conditional checks

Update `/workspace/app/main.py` lines 659-673 to remove all conditional checks:

```python
# Before (INCORRECT):
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change."""
    self.logger.debug(f"Unit selection changed to: {value}")
    # Update precision fix default if enabled
    if self.precision_fix_var.get():
        self._update_precision_fix_default()
    # Update gap bridge default if enabled
    if self.gap_bridge_var.get():
        self._update_gap_bridge_default()
    # Update min area filter default if enabled
    if self.min_area_filter_var.get():
        self._update_min_area_filter_default()
    # Update min side filter default if enabled
    if self.min_side_filter_var.get():
        self._update_min_side_filter_default()

# After (CORRECT):
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change.

    Updates ALL filter defaults when units change, regardless of checkbox state.
    This ensures users see appropriate values for their selected unit system
    whether or not a filter is currently enabled.
    """
    self.logger.debug(f"Unit selection changed to: {value}")
    # Always update all defaults when unit changes (regardless of checkbox state)
    self._update_precision_fix_default()
    self._update_gap_bridge_default()
    self._update_min_area_filter_default()
    self._update_min_side_filter_default()
```

### Step 2: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check to ensure no type errors after changes
- `uv run ruff check app/` - Lint check for code quality

## Notes

- **No new tests required for this fix:** This is a GUI behavior change. The existing unit tests for the `_update_*_default()` methods already validate that each method correctly sets values based on unit selection. This fix ensures those methods are always called when units change, which is a straightforward behavioral change that doesn't require additional unit tests.

- **Dependency on prior units:** This task assumes Unit 1 (spec 049) and Unit 2 (spec 050) have been completed:
  - Unit 1 established `DEFAULT_GAP_CLOSURE_TOLERANCE` in `constants.py`
  - Unit 2 updated initial StringVar values to match MM defaults

- **Impact on user experience:** After this fix, users will always see consistent values across all filter inputs when they change the unit selection, preventing confusion and potential errors from applying values in the wrong unit system.

- **Minimal change:** This is a surgical fix that only removes conditional checks from 4 lines in a single method. The update methods themselves remain unchanged.
