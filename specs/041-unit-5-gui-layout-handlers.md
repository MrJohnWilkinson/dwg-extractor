# Feature: GUI Layout and Handlers for Min Area and Min Side Polygon Filters (Unit 5)

## Feature Description
This feature adds GUI controls for minimum area and minimum side polygon filters to the DXF Block Extractor application. Building on the backend foundation from Units 1-4, this unit implements:
1. Four new instance variables for filter settings (`min_area_filter_var`, `min_area_filter_amount_var`, `min_side_filter_var`, `min_side_filter_amount_var`)
2. Two new GUI rows with checkboxes, amount labels, and entry fields (following the Precision Fix/Gap Bridge pattern)
3. Toggle handlers to enable/disable entry fields
4. Default update methods that set unit-appropriate filter defaults
5. Getter methods that return validated filter amounts
6. Updates to `_on_unit_change()` and `_extraction_worker()` to integrate filter parameters

This is Unit 5 of the Polygon Filter Implementation plan, completing the GUI integration that connects user interface controls to the filter parameters added in Units 1-4.

## User Story
As a CAD engineer using the DXF Block Extractor
I want to enable polygon filtering options through the GUI interface
So that I can filter out small artifact polygons during content zone detection with unit-appropriate default values

## Problem Statement
The polygon filtering backend has been implemented across Units 1-4:
- Unit 1: Added filter constants (`DEFAULT_MIN_AREA_FILTER`, `DEFAULT_MIN_SIDE_FILTER`, `MIN_*_FILTER_MIN/MAX`)
- Unit 2: Added `calculate_polygon_area()` and `calculate_shortest_straight_side()` to geometry.py
- Unit 3: Updated `_detect_content_zone()` with `min_area_filter` and `min_side_filter` parameters
- Unit 4: Updated `extract_blocks()` with 4 new filter params and `get_filter_values()` helper (722 tests passing)

However, users have no way to access these filtering capabilities from the GUI. The filter parameters are not exposed through checkboxes or entry fields, preventing users from utilizing the polygon filtering feature.

## Solution Statement
Add GUI controls following the established pattern of Precision Fix and Gap Bridge rows:
1. Add instance variables in `__init__` for filter state and amounts
2. Add two new GUI rows after the Gap Bridge section with separators
3. Implement toggle handlers that enable/disable entry fields
4. Implement default update methods that set unit-appropriate defaults
5. Implement getter methods that return validated filter amounts
6. Update `_on_unit_change()` to update filter defaults when unit changes
7. Update `_extraction_worker()` to pass filter parameters to `extract_blocks()`
8. Add required constant imports from `core.constants`

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application file
  - Add imports for filter constants (`DEFAULT_MIN_AREA_FILTER`, `DEFAULT_MIN_SIDE_FILTER`, `MIN_AREA_FILTER_MIN`, `MIN_AREA_FILTER_MAX`, `MIN_SIDE_FILTER_MIN`, `MIN_SIDE_FILTER_MAX`)
  - Add instance variables for filter settings in `__init__`
  - Add GUI rows in `_create_widgets()` after Gap Bridge section
  - Add toggle handler methods `_on_min_area_filter_toggle()` and `_on_min_side_filter_toggle()`
  - Add default update methods `_update_min_area_filter_default()` and `_update_min_side_filter_default()`
  - Add getter methods `_get_min_area_filter_amount()` and `_get_min_side_filter_amount()`
  - Update `_on_unit_change()` to include filter default updates
  - Update `_extraction_worker()` to pass filter parameters to `extract_blocks()`

- **app/core/constants.py** - Contains the filter constants (read-only reference)
  - `DEFAULT_MIN_AREA_FILTER` - dict with unit-specific default area filter values
  - `DEFAULT_MIN_SIDE_FILTER` - dict with unit-specific default side filter values
  - `MIN_AREA_FILTER_MIN` - minimum allowed area filter amount (0.0)
  - `MIN_AREA_FILTER_MAX` - maximum allowed area filter amount (1000000.0)
  - `MIN_SIDE_FILTER_MIN` - minimum allowed side filter amount (0.0)
  - `MIN_SIDE_FILTER_MAX` - maximum allowed side filter amount (100000.0)

- **app/core/extractor.py** - Extractor module (read-only reference)
  - `extract_blocks()` function accepts filter parameters (implemented in Unit 4)
  - No changes needed - just verify the call signature

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Add the new instance variables for filter settings in `__init__` and update the imports to include the filter constants from Unit 1. This follows the exact pattern established by Precision Fix and Gap Bridge settings.

### Phase 2: Core Implementation
Restructure `_create_widgets()` to add two new rows with separators:
1. Third separator and Min Area Filter row with checkbox, amount label, and entry field
2. Fourth separator and Min Side Filter row with checkbox, amount label, and entry field

Add the handler methods:
1. `_on_min_area_filter_toggle()` and `_on_min_side_filter_toggle()` for checkbox events
2. `_update_min_area_filter_default()` and `_update_min_side_filter_default()` for unit-aware defaults
3. `_get_min_area_filter_amount()` and `_get_min_side_filter_amount()` for validated amounts

### Phase 3: Integration
Update existing methods to integrate the new filter controls:
1. Update `_on_unit_change()` to update filter defaults when enabled
2. Update `_extraction_worker()` to pass filter parameters to `extract_blocks()`
3. Update logging to include filter settings in extraction summary

## Step by Step Tasks

### Step 1: Update Imports in main.py
Add the filter constants to the imports from `core.constants`:

```python
from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,          # NEW
    DEFAULT_MIN_SIDE_FILTER,          # NEW
    DEFAULT_PRECISION_FIX_TOLERANCE,
    GAP_BRIDGE_MAX,
    GAP_BRIDGE_MIN,
    MIN_AREA_FILTER_MAX,              # NEW
    MIN_AREA_FILTER_MIN,              # NEW
    MIN_SIDE_FILTER_MAX,              # NEW
    MIN_SIDE_FILTER_MIN,              # NEW
    MSG_ABORTED,
    MSG_ABORTING,
    MSG_ERROR_FILE_NOT_FOUND,
    MSG_ERROR_INVALID_FILE,
    MSG_ERROR_NO_BLOCKS,
    MSG_PROCESSING,
    MSG_SELECT_FILE,
    MSG_SUCCESS,
    PRECISION_FIX_MAX,
    PRECISION_FIX_MIN,
    UNIT_SELECTION_OPTIONS,
)
```

### Step 2: Add Instance Variables in __init__
Add the filter instance variables after the gap bridge settings in `__init__`:

```python
# Unit selection, precision fix, and gap bridge settings
self.unit_selection_var = ctk.StringVar(value="DXF/DWG")
self.precision_fix_var = ctk.BooleanVar(value=True)
self.precision_fix_amount_var = ctk.StringVar(value="0.01")
self.gap_bridge_var = ctk.BooleanVar(value=False)
self.gap_bridge_amount_var = ctk.StringVar(value="100.0")

# Min Area Filter settings
self.min_area_filter_var = ctk.BooleanVar(value=False)
self.min_area_filter_amount_var = ctk.StringVar(value="100.0")

# Min Side Filter settings
self.min_side_filter_var = ctk.BooleanVar(value=False)
self.min_side_filter_amount_var = ctk.StringVar(value="10.0")
```

### Step 3: Add Third Separator and Min Area Filter Row in _create_widgets()
After the Gap Bridge section (after `self.gap_bridge_entry.pack(side="left")`), add:

```python
# Third separator
separator3 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator3.pack(fill="x", pady=5)

# Min Area Filter row frame
min_area_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
min_area_frame.pack(pady=(5, 10))

self.min_area_filter_checkbox = ctk.CTkCheckBox(
    min_area_frame,
    text="Min Area Filter",
    variable=self.min_area_filter_var,
    command=self._on_min_area_filter_toggle,
    font=ctk.CTkFont(size=12),
)
self.min_area_filter_checkbox.pack(side="left", padx=(0, 10))

min_area_amount_label = ctk.CTkLabel(
    min_area_frame,
    text="Amount:",
    font=ctk.CTkFont(size=12),
)
min_area_amount_label.pack(side="left", padx=(0, 5))

self.min_area_filter_entry = ctk.CTkEntry(
    min_area_frame,
    width=80,
    textvariable=self.min_area_filter_amount_var,
    state="disabled",
)
self.min_area_filter_entry.pack(side="left")
```

### Step 4: Add Fourth Separator and Min Side Filter Row in _create_widgets()
After the Min Area Filter row, add:

```python
# Fourth separator
separator4 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator4.pack(fill="x", pady=5)

# Min Side Filter row frame
min_side_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
min_side_frame.pack(pady=(5, 10))

self.min_side_filter_checkbox = ctk.CTkCheckBox(
    min_side_frame,
    text="Min Side Filter",
    variable=self.min_side_filter_var,
    command=self._on_min_side_filter_toggle,
    font=ctk.CTkFont(size=12),
)
self.min_side_filter_checkbox.pack(side="left", padx=(0, 10))

min_side_amount_label = ctk.CTkLabel(
    min_side_frame,
    text="Amount:",
    font=ctk.CTkFont(size=12),
)
min_side_amount_label.pack(side="left", padx=(0, 5))

self.min_side_filter_entry = ctk.CTkEntry(
    min_side_frame,
    width=80,
    textvariable=self.min_side_filter_amount_var,
    state="disabled",
)
self.min_side_filter_entry.pack(side="left")
```

### Step 5: Add _on_min_area_filter_toggle() Method
Add the toggle handler method after `_on_gap_bridge_toggle()`:

```python
def _on_min_area_filter_toggle(self) -> None:
    """Handle min area filter checkbox toggle."""
    enabled = self.min_area_filter_var.get()
    self.logger.debug(f"Min area filter toggled: {enabled}")

    if enabled:
        self.min_area_filter_entry.configure(state="normal")
        self._update_min_area_filter_default()
    else:
        self.min_area_filter_entry.configure(state="disabled")
```

### Step 6: Add _on_min_side_filter_toggle() Method
Add the toggle handler method after `_on_min_area_filter_toggle()`:

```python
def _on_min_side_filter_toggle(self) -> None:
    """Handle min side filter checkbox toggle."""
    enabled = self.min_side_filter_var.get()
    self.logger.debug(f"Min side filter toggled: {enabled}")

    if enabled:
        self.min_side_filter_entry.configure(state="normal")
        self._update_min_side_filter_default()
    else:
        self.min_side_filter_entry.configure(state="disabled")
```

### Step 7: Add _update_min_area_filter_default() Method
Add the default update method after `_update_gap_bridge_default()`:

```python
def _update_min_area_filter_default(self) -> None:
    """Update min area filter amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)
    self.min_area_filter_amount_var.set(str(default_amount))
    self.logger.debug(f"Min area filter default updated to {default_amount}")
```

### Step 8: Add _update_min_side_filter_default() Method
Add the default update method after `_update_min_area_filter_default()`:

```python
def _update_min_side_filter_default(self) -> None:
    """Update min side filter amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)
    self.min_side_filter_amount_var.set(str(default_amount))
    self.logger.debug(f"Min side filter default updated to {default_amount}")
```

### Step 9: Add _get_min_area_filter_amount() Method
Add the getter method after `_get_precision_fix_amount()`:

```python
def _get_min_area_filter_amount(self) -> float | None:
    """Get validated min area filter amount, or None if invalid/disabled."""
    if not self.min_area_filter_var.get():
        return None
    try:
        amount = float(self.min_area_filter_amount_var.get())
        if MIN_AREA_FILTER_MIN <= amount <= MIN_AREA_FILTER_MAX:
            return amount
        else:
            self.logger.warning(f"Min area filter amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid min area filter amount")
        return None
```

### Step 10: Add _get_min_side_filter_amount() Method
Add the getter method after `_get_min_area_filter_amount()`:

```python
def _get_min_side_filter_amount(self) -> float | None:
    """Get validated min side filter amount, or None if invalid/disabled."""
    if not self.min_side_filter_var.get():
        return None
    try:
        amount = float(self.min_side_filter_amount_var.get())
        if MIN_SIDE_FILTER_MIN <= amount <= MIN_SIDE_FILTER_MAX:
            return amount
        else:
            self.logger.warning(f"Min side filter amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid min side filter amount")
        return None
```

### Step 11: Update _on_unit_change() Method
Update `_on_unit_change()` to include filter default updates:

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
    # Update min area filter default if enabled
    if self.min_area_filter_var.get():
        self._update_min_area_filter_default()
    # Update min side filter default if enabled
    if self.min_side_filter_var.get():
        self._update_min_side_filter_default()
```

### Step 12: Update _extraction_worker() Method
Update `_extraction_worker()` to get filter settings and pass them to `extract_blocks()`. After the existing settings retrieval (around line 386), add:

```python
# Get filter settings
min_area_filter_enabled = self.min_area_filter_var.get()
min_area_filter_amount = self._get_min_area_filter_amount()
min_side_filter_enabled = self.min_side_filter_var.get()
min_side_filter_amount = self._get_min_side_filter_amount()
```

Update the logging to include filter settings:

```python
self.logger.info(
    f"Extraction settings: unit_override={unit_override}, "
    f"gap_bridge_enabled={gap_bridge_enabled}, "
    f"gap_bridge_amount={gap_bridge_amount}, "
    f"precision_fix_enabled={precision_fix_enabled}, "
    f"precision_fix_amount={precision_fix_amount}, "
    f"min_area_filter_enabled={min_area_filter_enabled}, "
    f"min_area_filter_amount={min_area_filter_amount}, "
    f"min_side_filter_enabled={min_side_filter_enabled}, "
    f"min_side_filter_amount={min_side_filter_amount}"
)
```

Update the `extract_blocks()` call to include the new parameters:

```python
extraction_result = extract_blocks(
    self.selected_file_path,
    self.abort_event,
    unit_override=unit_override,
    gap_bridge_enabled=gap_bridge_enabled,
    gap_bridge_amount=gap_bridge_amount,
    precision_fix_enabled=precision_fix_enabled,
    precision_fix_amount=precision_fix_amount,
    min_area_filter_enabled=min_area_filter_enabled,
    min_area_filter_amount=min_area_filter_amount,
    min_side_filter_enabled=min_side_filter_enabled,
    min_side_filter_amount=min_side_filter_amount,
)
```

### Step 13: Run Type Checking
Execute mypy to verify type annotations are correct:

```bash
uv run mypy app/main.py
```

### Step 14: Run Linting
Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/main.py
uv run ruff format app/ --check
```

### Step 15: Run All Tests
Execute the full test suite to verify zero regressions:

```bash
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests
No new unit tests are required for this unit since:
1. The GUI changes are UI layout additions that cannot be unit tested without X server
2. The new methods follow the exact same pattern as existing methods (`_update_gap_bridge_default`, `_get_gap_bridge_amount`) which are tested via integration
3. The README explicitly states: "Skip GUI tests in WSL - X server issues make it unreliable. Focus WSL testing on unit/integration tests only"
4. The extraction integration with filter parameters was already tested in Unit 4 (`test_extractor_polygon_filter.py`)

### Integration Tests
The existing extraction tests in `test_extractor_polygon_filter.py` already cover the filter parameter functionality at the extractor level (Unit 4). The GUI integration will be validated via type checking, linting, and manual testing.

### Edge Cases
1. Filter amount entry with non-numeric input - handled by `_get_min_*_filter_amount()` returning None
2. Filter amount outside valid range - handled by range check in getter methods
3. Unit change while filter is disabled - should not update the default (checkbox is unchecked)
4. Unit change while filter is enabled - should update the default to unit-appropriate value
5. Toggling filter checkbox - entry should enable/disable and default should update when enabling
6. Both filters enabled simultaneously - both should work independently
7. Filters combined with precision fix and gap bridge - all settings should work together

### Playwright MCP Tests
Not applicable for this unit - GUI testing in WSL is unreliable per README. Visual verification should be done manually or in a Windows environment.

## Acceptance Criteria
1. `min_area_filter_var` and `min_area_filter_amount_var` instance variables exist
2. `min_side_filter_var` and `min_side_filter_amount_var` instance variables exist
3. GUI displays Min Area Filter row with checkbox, "Amount:" label, and entry field
4. GUI displays Min Side Filter row with checkbox, "Amount:" label, and entry field
5. Horizontal separators (gray lines) appear between all option rows
6. Filter entry fields start disabled (since filter checkboxes default to False)
7. Filter entry fields enable/disable when corresponding checkbox is toggled
8. Filter defaults update to unit-appropriate values when toggled on or unit changes
9. `_get_min_area_filter_amount()` returns validated float or None
10. `_get_min_side_filter_amount()` returns validated float or None
11. `_extraction_worker()` passes all four filter parameters to `extract_blocks()`
12. Filter settings are logged during extraction
13. All existing 722+ tests pass
14. Type checking passes with `uv run mypy app/`
15. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/main.py` - Type check the modified main module
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/main.py` - Lint the modified main module
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to verify imports work
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run filter tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This is Unit 5 of a multi-unit implementation plan for polygon filtering (source: `ai_output/020-polygon-filter-implementation-plan.md`)
- Unit 1 (commit 0332046) added constants and `PolygonMetrics` TypedDict
- Unit 2 (commit 62af902) added `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions
- Unit 3 (commit fda4ddc) updated `_detect_content_zone()` signature and added filtering logic
- Unit 4 updated `extract_blocks()` with 4 new filter params and `get_filter_values()` helper (722 tests passing)
- The filter entry fields start disabled because the checkboxes default to False
- The default filter amounts ("100.0" for area, "10.0" for side) correspond to the millimeters defaults from the constants
- The separator frames use `height=1` and `fg_color="gray50"` to create subtle horizontal lines (consistent with existing separators)
- All new methods follow the exact patterns established by Precision Fix and Gap Bridge implementations

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
|  [ ] Gap Bridge        Amount: [100.0   ]  (disabled)                |
|                                                                      |
|  ------------------------------------------------------------------- |
|                                                                      |
|  [ ] Min Area Filter   Amount: [100.0   ]  (disabled)                |
|                                                                      |
|  ------------------------------------------------------------------- |
|                                                                      |
|  [ ] Min Side Filter   Amount: [10.0    ]  (disabled)                |
|                                                                      |
+----------------------------------------------------------------------+
```

### Dependencies on Prior Units
This unit depends on the following from prior units:
- Unit 1: `DEFAULT_MIN_AREA_FILTER`, `DEFAULT_MIN_SIDE_FILTER`, `MIN_AREA_FILTER_MIN`, `MIN_AREA_FILTER_MAX`, `MIN_SIDE_FILTER_MIN`, `MIN_SIDE_FILTER_MAX` in `constants.py`
- Unit 4: `extract_blocks()` function signature with `min_area_filter_enabled`, `min_area_filter_amount`, `min_side_filter_enabled`, `min_side_filter_amount` parameters
