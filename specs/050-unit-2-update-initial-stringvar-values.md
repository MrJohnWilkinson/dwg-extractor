# Chore: Update Initial StringVar Values in main.py

## Chore Description

This is a refactoring task to ensure initial GUI values match the new shared defaults established in Unit 1. The `DEFAULT_GAP_CLOSURE_TOLERANCE` constant (with 3mm base value) was created in `constants.py` and is now used by the `_update_precision_fix_default()` and `_update_gap_bridge_default()` methods. However, the initial StringVar values in `__init__` are still using old hardcoded defaults that don't match the new MM defaults.

**Current state (incorrect):**
- `precision_fix_amount_var` initialized to `"0.01"` (should be `"3.0"` for MM)
- `gap_bridge_amount_var` initialized to `"100.0"` (should be `"3.0"` for MM)
- `min_area_filter_amount_var` initialized to `"100.0"` (should be `"100000.0"` for MM)
- `min_side_filter_amount_var` initialized to `"10.0"` (correct, no change needed)

**Why this matters:**
- The default unit selection is "DXF/DWG" which defaults to MM when no unit is specified
- Users should see "3.0" for both gap closure tolerances on app startup (matching MM defaults)
- Min area filter should show 100000.0 sq mm on startup (matching MM defaults)
- Initial values should be consistent with what the `_update_*_default()` methods would set for MM units

## Relevant Files

Use these files to resolve the chore:

- **`app/main.py`** (lines 84-97): Contains the StringVar initializations in `__init__` that need to be updated:
  - Line 87: `self.precision_fix_amount_var = ctk.StringVar(value="0.01")` - needs update to `"3.0"`
  - Line 89: `self.gap_bridge_amount_var = ctk.StringVar(value="100.0")` - needs update to `"3.0"`
  - Line 93: `self.min_area_filter_amount_var = ctk.StringVar(value="100.0")` - needs update to `"100000.0"`
  - Line 97: `self.min_side_filter_amount_var = ctk.StringVar(value="10.0")` - verify unchanged (correct)

- **`app/core/constants.py`** (lines 222-289): Reference for the default values:
  - `DEFAULT_GAP_CLOSURE_TOLERANCE[4]` = 3.0 (MM)
  - `DEFAULT_MIN_AREA_FILTER[4]` = 100000.0 (MM)
  - `DEFAULT_MIN_SIDE_FILTER[4]` = 10.0 (MM)

## Step by Step Tasks

### Step 1: Update precision_fix_amount_var initial value

Update `/workspace/app/main.py` line 87:

```python
# Before:
self.precision_fix_amount_var = ctk.StringVar(value="0.01")

# After:
self.precision_fix_amount_var = ctk.StringVar(value="3.0")
```

**Rationale:** The new `DEFAULT_GAP_CLOSURE_TOLERANCE[4]` (MM) is 3.0, so the initial value should match.

### Step 2: Update gap_bridge_amount_var initial value

Update `/workspace/app/main.py` line 89:

```python
# Before:
self.gap_bridge_amount_var = ctk.StringVar(value="100.0")

# After:
self.gap_bridge_amount_var = ctk.StringVar(value="3.0")
```

**Rationale:** The new `DEFAULT_GAP_CLOSURE_TOLERANCE[4]` (MM) is 3.0, so the initial value should match. Both precision fix and gap bridge now share the same default tolerance.

### Step 3: Update min_area_filter_amount_var initial value

Update `/workspace/app/main.py` line 93:

```python
# Before:
self.min_area_filter_amount_var = ctk.StringVar(value="100.0")

# After:
self.min_area_filter_amount_var = ctk.StringVar(value="100000.0")
```

**Rationale:** The `DEFAULT_MIN_AREA_FILTER[4]` (MM) is 100000.0 sq mm, so the initial value should match.

### Step 4: Verify min_side_filter_amount_var is unchanged

Verify `/workspace/app/main.py` line 97 remains:

```python
self.min_side_filter_amount_var = ctk.StringVar(value="10.0")
```

**Rationale:** The `DEFAULT_MIN_SIDE_FILTER[4]` (MM) is 10.0, which already matches the current initial value. No change needed.

### Step 5: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check to ensure no type errors after changes
- `uv run ruff check app/` - Lint check for code quality

## Notes

- **No test changes required:** This is a GUI-only change that updates initial display values. The existing tests focus on the `_update_*_default()` methods which already use the correct constants. There are no unit tests for the specific initial StringVar values since GUI initialization is typically not unit tested.

- **Consistency with MM defaults:** The default unit selection "DXF/DWG" defaults to MM (unit code 4) when no units are specified in the DXF file. The initial StringVar values should match what users would see for MM units:
  - Gap closure tolerance: 3.0 mm
  - Min area filter: 100,000 sq mm
  - Min side filter: 10.0 mm

- **Dependency on Unit 1:** This task assumes Unit 1 (spec 049) has been completed, which established `DEFAULT_GAP_CLOSURE_TOLERANCE` with the 3mm base value and updated the `_update_*_default()` methods to use it.

- **Visual impact:** After this change, when users launch the application, they will immediately see the correct default values in the GUI input fields instead of outdated values that would be overwritten as soon as they interact with the unit selection.
