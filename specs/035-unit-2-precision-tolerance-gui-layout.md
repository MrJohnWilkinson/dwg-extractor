# Feature: Precision Tolerance GUI Layout - Unit 2

## Feature Description
This feature restructures the main.py GUI options section from a single horizontal row into three separate rows with horizontal separators, providing a clearer and more organized layout for precision fix and gap bridge controls. The restructured layout includes:
1. A Units row with an explanatory hint about what settings it affects
2. A Precision Fix row with checkbox, amount label, and entry field
3. A Gap Bridge row with checkbox, amount label, and entry field

Additionally, this feature adds the `precision_fix_amount_var` instance variable and implements handlers for the precision fix entry field state, unit-aware default values, and a getter method for validated precision fix amounts.

This is Unit 2 of the Precision Tolerance GUI Implementation, building on the backend foundation established in Unit 1 (constants and extractor logic).

## User Story
As a CAD engineer using the DXF Block Extractor
I want to see a clearly organized options panel with precision fix amount controls
So that I can easily understand and configure precision fix tolerances with unit-appropriate defaults

## Problem Statement
The current GUI has all options (Units dropdown, Precision Fix checkbox, Gap Bridge checkbox and entry) in a single horizontal row, which:
1. Makes the interface cramped and harder to scan
2. Doesn't visually associate the entry fields with their respective checkboxes
3. Lacks the precision fix amount entry field that Unit 1 backend now supports
4. Doesn't explain to users that the Units selection affects both precision fix and gap bridge defaults

## Solution Statement
Restructure the `_create_widgets()` method in `main.py` to:
1. Replace the single `options_frame` with three separate frames (units_frame, precision_frame, gap_frame)
2. Add horizontal separator lines (CTkFrame with height=1) between the rows
3. Add an explanatory hint label after the Units dropdown
4. Add a precision fix amount entry field that enables/disables with the checkbox
5. Add new instance variable `precision_fix_amount_var` for the entry field
6. Implement `_update_precision_fix_default()` to set unit-appropriate defaults
7. Update `_on_precision_fix_toggle()` to enable/disable the entry field
8. Update `_on_unit_change()` to update both precision fix and gap bridge defaults
9. Implement `_get_precision_fix_amount()` to return validated amount or None

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application file
  - Add `precision_fix_amount_var` instance variable in `__init__`
  - Restructure `_create_widgets()` with three-row layout
  - Update `_on_precision_fix_toggle()` to handle entry field state
  - Add `_update_precision_fix_default()` method
  - Update `_on_unit_change()` to update both defaults
  - Add `_get_precision_fix_amount()` getter method
  - Update imports to include `DEFAULT_PRECISION_FIX_TOLERANCE`, `PRECISION_FIX_MIN`, `PRECISION_FIX_MAX`

- **app/core/constants.py** - Contains the precision fix constants (read-only reference)
  - `DEFAULT_PRECISION_FIX_TOLERANCE` - dict with unit-specific default tolerances
  - `PRECISION_FIX_MIN` - minimum allowed precision fix amount (0.0)
  - `PRECISION_FIX_MAX` - maximum allowed precision fix amount (10.0)
  - `UNIT_SELECTION_OPTIONS` - dict mapping dropdown labels to unit codes

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Add the new instance variable `precision_fix_amount_var` in `__init__` and update the imports to include the precision fix constants from Unit 1.

### Phase 2: Core Implementation
Restructure `_create_widgets()` to create three separate frames with horizontal separators:
1. Units row with dropdown and explanatory hint
2. Precision Fix row with checkbox, amount label, and entry field
3. Gap Bridge row with checkbox, amount label, and entry field

### Phase 3: Integration
Implement the handler methods that connect the GUI controls to the backend:
1. Update `_on_precision_fix_toggle()` to enable/disable entry field and set default
2. Add `_update_precision_fix_default()` to calculate unit-appropriate defaults
3. Update `_on_unit_change()` to update both precision fix and gap bridge defaults
4. Add `_get_precision_fix_amount()` to return validated amount for extraction

## Step by Step Tasks

### Step 1: Update Imports in main.py
- Add `DEFAULT_PRECISION_FIX_TOLERANCE`, `PRECISION_FIX_MIN`, `PRECISION_FIX_MAX` to the imports from `core.constants`
- Verify all required constants are imported

### Step 2: Add Instance Variable in __init__
- Add `self.precision_fix_amount_var = ctk.StringVar(value="0.01")` after `self.precision_fix_var`
- Place it in the comment section "# Unit selection and gap bridge settings" (update comment to include precision fix)

### Step 3: Restructure _create_widgets() - Units Row
- Remove the existing `options_frame` and all its child widgets
- Create `units_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")`
- Pack units_frame with `pady=(0, 10)`
- Add `unit_label` with text "Units:" and font size 12
- Add `self.unit_dropdown` (same as before but with different parent)
- Add `units_hint` label with text "(applies to precision fix and gap bridge)", font size 10, text_color="gray"

### Step 4: Restructure _create_widgets() - First Separator
- Create `separator1 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")`
- Pack with `fill="x", pady=5`

### Step 5: Restructure _create_widgets() - Precision Fix Row
- Create `precision_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")`
- Pack precision_frame with `pady=(5, 10)`
- Add `self.precision_fix_checkbox` with text "Precision Fix" (remove colon)
- Add `precision_amount_label` with text "Amount:"
- Add `self.precision_fix_entry = ctk.CTkEntry(precision_frame, width=80, textvariable=self.precision_fix_amount_var)`
- Entry should start enabled since precision_fix_var defaults to True

### Step 6: Restructure _create_widgets() - Second Separator
- Create `separator2 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")`
- Pack with `fill="x", pady=5`

### Step 7: Restructure _create_widgets() - Gap Bridge Row
- Create `gap_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")`
- Pack gap_frame with `pady=(5, 10)`
- Add `self.gap_bridge_checkbox` with text "Gap Bridge" (remove colon)
- Add `gap_amount_label` with text "Amount:"
- Add `self.gap_bridge_entry` with state="disabled" (same as before but with different parent)

### Step 8: Update _on_precision_fix_toggle() Method
- Update the method to enable/disable the precision fix entry field based on checkbox state:
  ```python
  def _on_precision_fix_toggle(self) -> None:
      """Handle precision fix checkbox toggle."""
      enabled = self.precision_fix_var.get()
      self.logger.debug(f"Precision fix toggled: {enabled}")

      if enabled:
          self.precision_fix_entry.configure(state="normal")
          self._update_precision_fix_default()
      else:
          self.precision_fix_entry.configure(state="disabled")
  ```

### Step 9: Add _update_precision_fix_default() Method
- Add new method to update precision fix amount to default for selected unit:
  ```python
  def _update_precision_fix_default(self) -> None:
      """Update precision fix amount to default for selected unit."""
      selection = self.unit_selection_var.get()
      insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
      effective_units = insunits if insunits != -1 else 4  # Default to mm
      default_amount = DEFAULT_PRECISION_FIX_TOLERANCE.get(effective_units, 0.01)
      self.precision_fix_amount_var.set(str(default_amount))
      self.logger.debug(f"Precision fix default updated to {default_amount}")
  ```
- Place this method after `_on_precision_fix_toggle()`

### Step 10: Update _on_unit_change() Method
- Update the method to also update precision fix default when precision fix is enabled:
  ```python
  def _on_unit_change(self, value: str) -> None:
      """Handle unit dropdown selection change."""
      self.logger.debug(f"Unit selection changed to: {value}")
      # Update precision fix default if enabled
      if self.precision_fix_var.get():
          self._update_precision_fix_default()
      # Update gap bridge default if enabled
      if self.gap_bridge_var.get():
          self._update_gap_bridge_default()
  ```
- Remove the `hasattr` check since `gap_bridge_var` is always defined before this method can be called

### Step 11: Add _get_precision_fix_amount() Method
- Add new method to get validated precision fix amount:
  ```python
  def _get_precision_fix_amount(self) -> float | None:
      """Get validated precision fix amount, or None if invalid/disabled."""
      if not self.precision_fix_var.get():
          return None
      try:
          amount = float(self.precision_fix_amount_var.get())
          if PRECISION_FIX_MIN <= amount <= PRECISION_FIX_MAX:
              return amount
          else:
              self.logger.warning(f"Precision fix amount {amount} out of range")
              return None
      except ValueError:
          self.logger.warning("Invalid precision fix amount")
          return None
  ```
- Place this method after `_get_gap_bridge_amount()`

### Step 12: Run Validation Commands
- Run `uv run mypy app/` to verify type hints are correct
- Run `uv run ruff check app/` to verify code style compliance
- Run `uv run ruff format app/` to format code if needed
- Run `uv run pytest app/tests/ -v` to ensure all existing tests pass

## Testing Strategy

### Unit Tests
No new unit tests are required for this unit since:
1. The GUI changes are UI layout restructuring that cannot be unit tested without X server
2. The new methods (`_update_precision_fix_default`, `_get_precision_fix_amount`) follow the exact same pattern as existing methods (`_update_gap_bridge_default`, `_get_gap_bridge_amount`) which are tested via integration
3. The README explicitly states: "Skip GUI tests in WSL - X server issues make it unreliable. Focus WSL testing on unit/integration tests only"

### Integration Tests
The existing extraction tests in `test_extractor_precision_fix.py` already cover the precision fix amount functionality at the extractor level (Unit 1). The GUI integration will be validated via manual testing and type checking.

### Edge Cases
1. Precision fix amount entry with non-numeric input - handled by `_get_precision_fix_amount()` returning None
2. Precision fix amount outside valid range - handled by range check in `_get_precision_fix_amount()`
3. Unit change while precision fix is disabled - should not update the default (checkbox is unchecked)
4. Unit change while precision fix is enabled - should update the default to unit-appropriate value
5. Toggling precision fix checkbox - entry should enable/disable and default should update when enabling

### Playwright MCP Tests
Not applicable for this unit - GUI testing in WSL is unreliable per README. Visual verification should be done manually or in a Windows environment.

## Acceptance Criteria
1. `precision_fix_amount_var` instance variable exists and is initialized to "0.01"
2. GUI displays three separate rows: Units, Precision Fix, Gap Bridge
3. Horizontal separators (gray lines) appear between the three rows
4. Units row includes explanatory hint text "(applies to precision fix and gap bridge)"
5. Precision Fix row has checkbox, "Amount:" label, and entry field
6. Gap Bridge row has checkbox, "Amount:" label, and entry field
7. Precision fix entry field starts enabled (since precision fix defaults to True)
8. Precision fix entry field enables/disables when checkbox is toggled
9. Precision fix default updates to unit-appropriate value when toggled on or unit changes
10. Gap bridge default updates when unit changes (if gap bridge is enabled)
11. `_get_precision_fix_amount()` returns validated float or None
12. All existing tests pass
13. Type checking passes with `uv run mypy app/`
14. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to verify imports work
- `uv run pytest app/tests/core/extractor/test_extractor_precision_fix.py -v` - Run precision fix tests

## Notes
- This unit focuses on GUI layout restructuring and does not pass the precision fix amount to the extraction worker yet. That integration is planned for Unit 3.
- The precision fix entry starts enabled because `self.precision_fix_var` defaults to `True` in `__init__`
- The default precision fix amount is "0.01" which corresponds to the millimeters default from `DEFAULT_PRECISION_FIX_TOLERANCE[4]`
- The `hasattr` check in the existing `_on_unit_change()` is removed since `gap_bridge_var` is always defined before `_create_widgets()` is called
- The separator frames use `height=1` and `fg_color="gray50"` to create subtle horizontal lines
- The hint label uses `font_size=10` and `text_color="gray"` to be visually subordinate to the main controls

### GUI Layout Reference
```
+----------------------------------------------------------------------+
|                                                                      |
|  Units: [DXF/DWG v]  (applies to precision fix and gap bridge)       |
|                                                                      |
|  ------------------------------------------------------------------- |
|                                                                      |
|  [x] Precision Fix     Amount: [0.01    ]                           |
|                                                                      |
|  ------------------------------------------------------------------- |
|                                                                      |
|  [ ] Gap Bridge        Amount: [0.5     ]  (disabled)                |
|                                                                      |
+----------------------------------------------------------------------+
```

### Dependencies on Unit 1
This unit depends on the following from Unit 1 (specs/034):
- `DEFAULT_PRECISION_FIX_TOLERANCE` dict in `constants.py`
- `PRECISION_FIX_MIN` constant in `constants.py`
- `PRECISION_FIX_MAX` constant in `constants.py`
