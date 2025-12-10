# Feature: GUI Controls for Two-Stage Snapping Configuration

## Feature Description
This feature adds GUI controls to the DXF Block Extractor application for configuring two-stage coordinate snapping. The controls allow users to:

1. **Unit Selection Dropdown** - Choose drawing units manually or use "DXF/DWG" for auto-detection from the file's $INSUNITS header. Options include: DXF/DWG (auto), MM, CM, M, IN, FT.

2. **Gap Bridge Checkbox** - Enable/disable Stage 2 gap bridging, which bridges intentional small gaps in CAD drawings for better polygon detection.

3. **Gap Bridge Amount Entry** - A numeric input field for specifying custom gap bridge tolerance. The field is disabled when the checkbox is unchecked and shows unit-appropriate default values when enabled.

4. **Extraction Integration** - Pass user-selected settings through the extraction pipeline to `extract_blocks()`, which calculates appropriate tolerances and propagates them to the geometry module.

This is Group D of the Two-Stage Snapping implementation plan, combining Units 6, 7, and 8. It builds on:
- **Group A (Units 1-2)**: Added constants (`UNIT_SELECTION_OPTIONS`, `DEFAULT_GAP_BRIDGE_TOLERANCE`, etc.) and functions (`_get_drawing_units()`, `get_snap_tolerances()`)
- **Group B (Units 3-4)**: Modified `_extract_paint_bucket_regions()` and `_detect_content_zone()` to accept tolerance parameters
- **Group C (Unit 5)**: Updated `extract_blocks()` to accept `unit_override`, `gap_bridge_enabled`, `gap_bridge_amount` parameters

## User Story
As a CAD professional using the DXF Block Extractor
I want to configure unit settings and gap bridging options through the GUI
So that I can optimize polygon detection for different drawing types and intentionally bridge small gaps in my CAD drawings

## Problem Statement
The tolerance calculation infrastructure exists (Group A), the geometry module accepts tolerance parameters (Group B), and the extractor function accepts user-configurable parameters (Group C), but there is no way for users to interact with these settings. The application currently uses auto-detection and default values without giving users control over:

1. Overriding the detected drawing units when the file's $INSUNITS header is incorrect
2. Enabling gap bridging for drawings with intentional small gaps
3. Specifying custom gap bridge amounts for specific use cases

Without GUI controls, users cannot leverage the two-stage snapping feature to improve polygon detection in problematic drawings.

## Solution Statement
Add GUI controls to `app/main.py` in the `DXFExtractorApp` class:

1. **State Variables in `__init__()`**:
   - `self.unit_selection_var = ctk.StringVar(value="DXF/DWG")` for unit dropdown
   - `self.gap_bridge_var = ctk.BooleanVar(value=False)` for checkbox state
   - `self.gap_bridge_amount_var = ctk.StringVar(value="100.0")` for entry field

2. **New Widgets in `_create_widgets()`**:
   - Options frame (transparent) to hold unit and gap bridge controls
   - Unit label and dropdown (`CTkOptionMenu`) with values from `UNIT_SELECTION_OPTIONS`
   - Gap bridge checkbox (`CTkCheckBox`) that controls entry field state
   - Gap bridge amount entry (`CTkEntry`) initially disabled

3. **Event Handlers**:
   - `_on_unit_change()` - Updates gap bridge default when unit changes
   - `_on_gap_bridge_toggle()` - Enables/disables entry field
   - `_update_gap_bridge_default()` - Sets unit-appropriate default value

4. **Helper Methods**:
   - `_get_selected_unit_override()` - Returns $INSUNITS value or None for auto
   - `_get_gap_bridge_amount()` - Returns validated float or None

5. **Extraction Integration in `_extraction_worker()`**:
   - Read GUI settings before extraction
   - Pass settings to `extract_blocks()` call

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application file. Contains `DXFExtractorApp` class where all widget creation, event handling, and extraction workflow happen. This is the primary file to modify.
- **app/core/constants.py** - Contains constants added by Group A that the GUI needs to import: `UNIT_SELECTION_OPTIONS`, `DEFAULT_GAP_BRIDGE_TOLERANCE`, `GAP_BRIDGE_MIN`, `GAP_BRIDGE_MAX`.
- **app/core/extractor.py** - Contains `extract_blocks()` function that already accepts the tolerance parameters (modified by Group C). No changes needed, just reference for understanding the interface.

### New Files
None - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
Import the required constants from the constants module into main.py. These constants are already defined (by Group A) and include:
- `UNIT_SELECTION_OPTIONS` - Dictionary mapping display labels to $INSUNITS codes
- `DEFAULT_GAP_BRIDGE_TOLERANCE` - Default gap bridge amounts per unit
- `GAP_BRIDGE_MIN` and `GAP_BRIDGE_MAX` - Input validation bounds

### Phase 2: Core Implementation
1. Add state variables to `__init__()` for tracking unit selection and gap bridge settings
2. Create new widgets in `_create_widgets()`:
   - Options frame placed after button_frame
   - Unit label and dropdown
   - Gap bridge checkbox and entry field
3. Implement event handlers for user interactions:
   - `_on_unit_change()` - Called when dropdown selection changes
   - `_on_gap_bridge_toggle()` - Called when checkbox is toggled
   - `_update_gap_bridge_default()` - Updates entry with unit-appropriate default
4. Implement helper methods for reading settings:
   - `_get_selected_unit_override()` - Converts dropdown selection to $INSUNITS value
   - `_get_gap_bridge_amount()` - Validates and returns gap bridge amount

### Phase 3: Integration
Update `_extraction_worker()` to:
1. Read current GUI settings using the helper methods
2. Log the extraction settings for debugging
3. Pass settings to `extract_blocks()` call as keyword arguments

All changes maintain backward compatibility - if settings are not used, defaults apply.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Imports to main.py
- Add imports for new constants from `core.constants`:
  - `UNIT_SELECTION_OPTIONS`
  - `DEFAULT_GAP_BRIDGE_TOLERANCE`
  - `GAP_BRIDGE_MIN`
  - `GAP_BRIDGE_MAX`
- Place imports alongside existing imports from core.constants

### Step 2: Add State Variables to __init__()
- Add `self.unit_selection_var = ctk.StringVar(value="DXF/DWG")` after existing instance variables
- Add `self.gap_bridge_var = ctk.BooleanVar(value=False)` after unit_selection_var
- Add `self.gap_bridge_amount_var = ctk.StringVar(value="100.0")` after gap_bridge_var

### Step 3: Create Options Frame in _create_widgets()
- After the existing `button_frame.pack()` line, create a new options frame:
```python
# Options frame for unit selection and gap bridge
options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
options_frame.pack(pady=(0, 15))
```

### Step 4: Add Unit Selection Dropdown
- Create unit label:
```python
unit_label = ctk.CTkLabel(
    options_frame,
    text="Units:",
    font=ctk.CTkFont(size=12),
)
unit_label.pack(side="left", padx=(0, 5))
```
- Create unit dropdown:
```python
self.unit_dropdown = ctk.CTkOptionMenu(
    options_frame,
    values=list(UNIT_SELECTION_OPTIONS.keys()),
    variable=self.unit_selection_var,
    width=100,
    command=self._on_unit_change,
)
self.unit_dropdown.pack(side="left", padx=(0, 20))
```

### Step 5: Add Gap Bridge Controls
- Create gap bridge checkbox:
```python
self.gap_bridge_checkbox = ctk.CTkCheckBox(
    options_frame,
    text="Gap Bridge:",
    variable=self.gap_bridge_var,
    command=self._on_gap_bridge_toggle,
    font=ctk.CTkFont(size=12),
)
self.gap_bridge_checkbox.pack(side="left", padx=(0, 5))
```
- Create gap bridge amount entry:
```python
self.gap_bridge_entry = ctk.CTkEntry(
    options_frame,
    width=80,
    textvariable=self.gap_bridge_amount_var,
    state="disabled",
)
self.gap_bridge_entry.pack(side="left")
```

### Step 6: Implement _on_unit_change() Method
- Add method after `_poll_log_queue()`:
```python
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change."""
    self.logger.debug(f"Unit selection changed to: {value}")
    # Update gap bridge default if gap bridging is enabled
    if hasattr(self, 'gap_bridge_var') and self.gap_bridge_var.get():
        self._update_gap_bridge_default()
```

### Step 7: Implement _on_gap_bridge_toggle() Method
- Add method after `_on_unit_change()`:
```python
def _on_gap_bridge_toggle(self) -> None:
    """Handle gap bridge checkbox toggle."""
    enabled = self.gap_bridge_var.get()
    self.logger.debug(f"Gap bridge toggled: {enabled}")

    if enabled:
        self.gap_bridge_entry.configure(state="normal")
        self._update_gap_bridge_default()
    else:
        self.gap_bridge_entry.configure(state="disabled")
```

### Step 8: Implement _update_gap_bridge_default() Method
- Add method after `_on_gap_bridge_toggle()`:
```python
def _update_gap_bridge_default(self) -> None:
    """Update gap bridge amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    # Use detected units fallback if auto
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_GAP_BRIDGE_TOLERANCE.get(effective_units, 100.0)
    self.gap_bridge_amount_var.set(str(default_amount))
    self.logger.debug(f"Gap bridge default updated to {default_amount}")
```

### Step 9: Implement _get_selected_unit_override() Method
- Add method after `_update_gap_bridge_default()`:
```python
def _get_selected_unit_override(self) -> int | None:
    """Get the $INSUNITS value for selected unit, or None for auto."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    return None if insunits == -1 else insunits
```

### Step 10: Implement _get_gap_bridge_amount() Method
- Add method after `_get_selected_unit_override()`:
```python
def _get_gap_bridge_amount(self) -> float | None:
    """Get validated gap bridge amount, or None if invalid/disabled."""
    if not self.gap_bridge_var.get():
        return None
    try:
        amount = float(self.gap_bridge_amount_var.get())
        if GAP_BRIDGE_MIN <= amount <= GAP_BRIDGE_MAX:
            return amount
        else:
            self.logger.warning(f"Gap bridge amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid gap bridge amount")
        return None
```

### Step 11: Update _extraction_worker() to Pass Settings
- In `_extraction_worker()`, after existing validation and setup, add settings retrieval:
```python
# Get user settings
unit_override = self._get_selected_unit_override()
gap_bridge_enabled = self.gap_bridge_var.get()
gap_bridge_amount = self._get_gap_bridge_amount()

self.logger.info(
    f"Extraction settings: unit_override={unit_override}, "
    f"gap_bridge_enabled={gap_bridge_enabled}, "
    f"gap_bridge_amount={gap_bridge_amount}"
)
```
- Update the `extract_blocks()` call to pass the new parameters:
```python
extraction_result = extract_blocks(
    self.selected_file_path,
    self.abort_event,
    unit_override=unit_override,
    gap_bridge_enabled=gap_bridge_enabled,
    gap_bridge_amount=gap_bridge_amount,
)
```

### Step 12: Run Validation Commands
- Run all tests to verify implementation is correct with zero regressions
- Run type checker to verify type annotations are correct
- Run linter to verify code style

## Testing Strategy

### Unit Tests
Testing GUI components directly is challenging in WSL2 without X server. Focus on testing the helper methods that can be tested without GUI:

1. **Test _get_selected_unit_override() behavior** (via mock or integration)
   - Returns None when "DXF/DWG" selected
   - Returns 4 when "MM" selected
   - Returns 1 when "IN" selected

2. **Test _get_gap_bridge_amount() validation** (via mock or integration)
   - Returns None when gap_bridge_var is False
   - Returns valid float when within range
   - Returns None for out-of-range values
   - Returns None for non-numeric input

### Integration Tests
1. **Test extraction with unit override** - Call `extract_blocks()` with `unit_override=4`, verify no errors
2. **Test extraction with gap bridge enabled** - Call `extract_blocks()` with `gap_bridge_enabled=True`, verify no errors
3. **Test extraction with custom gap amount** - Call `extract_blocks()` with `gap_bridge_amount=50.0`, verify no errors
4. **Test backward compatibility** - Verify extraction works without new parameters

### Edge Cases
- "DXF/DWG" selection should pass `None` to `extract_blocks()` for auto-detection
- Checkbox unchecked should pass `gap_bridge_enabled=False` regardless of entry value
- Entry field should be disabled when checkbox is unchecked
- Empty entry field should result in `None` being returned
- Negative values in entry should be rejected
- Values exceeding `GAP_BRIDGE_MAX` should be rejected
- Non-numeric entry values should be rejected

### Playwright MCP Tests
Skip GUI e2e tests in WSL2 - X server issues make it unreliable. The README explicitly states: "Skip GUI tests in WSL - X server issues make it unreliable. Focus WSL testing on unit/integration tests only."

## Acceptance Criteria
1. Unit selection dropdown displays all options from `UNIT_SELECTION_OPTIONS`: "DXF/DWG", "MM", "CM", "M", "IN", "FT"
2. Dropdown defaults to "DXF/DWG" (auto-detect) on application start
3. Gap bridge checkbox defaults to unchecked on application start
4. Gap bridge entry field is disabled when checkbox is unchecked
5. Gap bridge entry field is enabled when checkbox is checked
6. Entry field shows unit-appropriate default when checkbox is checked
7. Entry field default updates when unit selection changes while checkbox is checked
8. `_get_selected_unit_override()` returns `None` for "DXF/DWG", correct $INSUNITS code for other options
9. `_get_gap_bridge_amount()` returns `None` when checkbox unchecked or value invalid
10. `_get_gap_bridge_amount()` returns validated float when checkbox checked and value valid
11. Extraction worker logs settings before calling `extract_blocks()`
12. `extract_blocks()` is called with correct parameters from GUI settings
13. All existing tests pass (zero regressions)
14. Type checker passes with no errors
15. Linter passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/extractor/test_extractor_units.py -v` - Run extractor unit tests (includes tolerance parameter tests)
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests (verifies constants exist)
- `uv run pytest app/tests/core/ -v` - Run all core tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions
- `uv run mypy app/` - Run type checker to verify type annotations
- `uv run ruff check app/` - Run linter to verify code style

## Notes
- **Dependency on Group A (commit `eacc6e0`)**: This spec requires constants `UNIT_SELECTION_OPTIONS`, `DEFAULT_GAP_BRIDGE_TOLERANCE`, `GAP_BRIDGE_MIN`, `GAP_BRIDGE_MAX` from constants.py.

- **Dependency on Group B (commit `3f359c4`)**: This spec requires `_extract_paint_bucket_regions()` and `_detect_content_zone()` to accept tolerance parameters.

- **Dependency on Group C (commit `4d861cf`)**: This spec requires `extract_blocks()` to accept `unit_override`, `gap_bridge_enabled`, `gap_bridge_amount` parameters.

- **GUI Testing Limitations**: As noted in the README, GUI tests are unreliable in WSL2. Focus on testing the non-GUI helper methods and verifying integration through the extractor tests.

- **Default Gap Bridge Amount Logic**: When gap bridging is enabled but no custom amount is provided, the system uses unit-appropriate defaults from `DEFAULT_GAP_BRIDGE_TOLERANCE`. For "DXF/DWG" (auto-detect), the GUI defaults to mm-appropriate values since the actual detected units aren't known until file is loaded.

- **Widget Placement**: The options frame is placed after the button frame (Browse/Extract/Open Folder) and before the progress bar, providing a logical flow from file selection to options to extraction.

- **No new libraries needed**: All GUI components use customtkinter which is already installed.
