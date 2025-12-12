# Feature: Settings Synchronization Core

## Feature Description
Implement bidirectional settings synchronization between the main GUI window and the Advanced Settings window. Currently, filter settings (boolean flags) are synced, but numeric filter amounts and unit override are not. Additionally, when the Advanced Settings window closes, the main GUI doesn't refresh to reflect changes made there (such as log viewer level changes).

This feature implements three core synchronization mechanisms:
1. Expanding `_sync_settings_to_manager()` to sync numeric filter amounts and unit override
2. Adding pre-open sync (main GUI -> SettingsManager) and post-close refresh (SettingsManager -> main GUI) to the Advanced Settings window lifecycle
3. Adding `trace_add` callbacks for instant sync of numeric filter amounts as users type

## User Story
As a DXF Block Extractor user
I want my filter settings to automatically sync between the main window and Advanced Settings
So that I can see consistent values across both windows without manual coordination

## Problem Statement
The main GUI and Advanced Settings window share settings through SettingsManager, but synchronization is incomplete:
- Numeric filter amounts (`precision_fix_amount`, `gap_bridge_amount`, `min_area_filter_amount`, `min_side_filter_amount`) are not synced
- Unit override selection is not synced
- When the user changes `log_viewer_level` in Advanced Settings, the main GUI dropdown doesn't update
- Changes to numeric amounts in the main GUI aren't reflected in Advanced Settings until explicitly saved

This creates a confusing user experience where values appear different in different windows.

## Solution Statement
Implement comprehensive settings synchronization:
1. **Expand `_sync_settings_to_manager()`** - Add a helper method `_sync_numeric_setting()` that safely converts StringVar values to floats and syncs them to SettingsManager. Call this for all four numeric filter amounts. Also sync `unit_override`.
2. **Pre-open sync and post-close refresh** - Before opening Advanced Settings, sync all main GUI state to SettingsManager. After Advanced Settings closes, refresh main GUI state from SettingsManager (specifically `log_viewer_level` which can be changed there).
3. **Instant sync via `trace_add`** - Add trace callbacks on all four numeric amount StringVars so changes are immediately synced to SettingsManager as users type.

## Relevant Files
Use these files to implement the feature:

- **`app/main.py`** - Main GUI application containing:
  - `_sync_settings_to_manager()` method (lines 1117-1135) - needs expansion
  - `_open_advanced_settings()` method (lines 790-797) - needs pre-sync and post-refresh
  - `__init__()` method (lines 55-119) - needs trace_add callbacks after filter variable creation
  - Filter amount StringVars: `precision_fix_amount_var`, `gap_bridge_amount_var`, `min_area_filter_amount_var`, `min_side_filter_amount_var`

- **`app/core/settings.py`** - SettingsManager class for reference on available settings keys and validation

- **`app/core/settings_window.py`** - AdvancedSettingsWindow for understanding how settings are displayed in the Filters tab (read-only display)

- **`app/tests/core/test_settings.py`** - Existing settings tests for test patterns

### New Files
- **`app/tests/core/test_main_settings_sync.py`** - New test file for settings synchronization unit tests

## Implementation Plan

### Phase 1: Foundation
Add the `_sync_numeric_setting()` helper method that safely converts StringVar values to floats and syncs to SettingsManager. This helper will be reused by both the expanded `_sync_settings_to_manager()` and the trace callbacks.

### Phase 2: Core Implementation
1. Expand `_sync_settings_to_manager()` to call `_sync_numeric_setting()` for all four numeric amounts plus sync unit override
2. Modify `_open_advanced_settings()` to call `_sync_settings_to_manager()` before opening the window
3. Add `_refresh_from_settings()` method to refresh main GUI state from SettingsManager
4. Call `_refresh_from_settings()` after Advanced Settings window closes

### Phase 3: Integration
Add `trace_add` callbacks in `__init__()` after filter variable creation to enable instant sync of numeric amounts as users type.

## Step by Step Tasks

### Step 1: Add `_sync_numeric_setting()` Helper Method

Add a new helper method after `_sync_settings_to_manager()` in `app/main.py`:

- Add `_sync_numeric_setting(self, key: str, var: ctk.StringVar) -> None` method
- Method should try to convert `var.get()` to float
- If successful, call `self.settings.set(key, value)`
- If ValueError (invalid input), silently pass (don't sync invalid values)
- Include docstring explaining the purpose and parameters

**Location:** After line 1135 in `app/main.py`

**Code to add:**
```python
def _sync_numeric_setting(self, key: str, var: ctk.StringVar) -> None:
    """Sync a numeric setting from StringVar to SettingsManager.

    Args:
        key: Setting key in SettingsManager
        var: StringVar containing the numeric value
    """
    try:
        value = float(var.get())
        self.settings.set(key, value)
    except ValueError:
        pass  # Invalid input, don't sync
```

### Step 2: Expand `_sync_settings_to_manager()` Method

Modify the existing `_sync_settings_to_manager()` method in `app/main.py`:

- After syncing boolean flags (line 1126), add calls to sync numeric amounts
- Call `_sync_numeric_setting()` for each of:
  - `"precision_fix_amount"` with `self.precision_fix_amount_var`
  - `"gap_bridge_amount"` with `self.gap_bridge_amount_var`
  - `"min_area_filter_amount"` with `self.min_area_filter_amount_var`
  - `"min_side_filter_amount"` with `self.min_side_filter_amount_var`
- Add unit override sync using `self._get_selected_unit_override()`
- Update docstring to reflect new scope

**Location:** Lines 1117-1135 in `app/main.py`

**Updated code:**
```python
def _sync_settings_to_manager(self) -> None:
    """Synchronize current GUI settings to SettingsManager.

    Called when filter settings change to persist user preferences.
    """
    # Sync filter boolean flags
    self.settings.set("precision_fix_enabled", self.precision_fix_var.get())
    self.settings.set("gap_bridge_enabled", self.gap_bridge_var.get())
    self.settings.set("min_area_filter_enabled", self.min_area_filter_var.get())
    self.settings.set("min_side_filter_enabled", self.min_side_filter_var.get())

    # Sync filter numeric amounts
    self._sync_numeric_setting("precision_fix_amount", self.precision_fix_amount_var)
    self._sync_numeric_setting("gap_bridge_amount", self.gap_bridge_amount_var)
    self._sync_numeric_setting("min_area_filter_amount", self.min_area_filter_amount_var)
    self._sync_numeric_setting("min_side_filter_amount", self.min_side_filter_amount_var)

    # Sync unit override
    unit_override = self._get_selected_unit_override()
    self.settings.set("unit_override", unit_override)

    # Sync logging settings
    self.settings.set("generate_log_file", self.log_file_var.get())
    self.settings.set("file_log_level", self.file_log_level_var.get())
    self.settings.set("log_viewer_level", self.log_level_var.get())

    # Save to disk
    self.settings.save()
    self.logger.debug("Settings synchronized and saved")
```

### Step 3: Add `_refresh_from_settings()` Method

Add a new method to refresh main GUI state from SettingsManager after Advanced Settings closes:

- Add `_refresh_from_settings(self) -> None` method
- Get `log_viewer_level` from settings
- Compare with current `log_level_var` value
- If different, update `log_level_var` and apply to source loggers
- Include debug logging

**Location:** After `_open_advanced_settings()` method (around line 798)

**Code to add:**
```python
def _refresh_from_settings(self) -> None:
    """Refresh main GUI state from SettingsManager.

    Called after Advanced Settings closes to reflect any changes
    made to settings that affect the main window display.
    """
    # Refresh log viewer level (may have changed in Advanced Settings)
    new_level = self.settings.get("log_viewer_level")
    if self.log_level_var.get() != new_level:
        self.log_level_var.set(new_level)
        # Apply the level change to source loggers
        level = getattr(logging, new_level)
        logging.getLogger("core.extractor").setLevel(level)
        logging.getLogger("core.geometry").setLevel(level)
        logging.getLogger("__main__").setLevel(level)

    self.logger.debug("Main GUI refreshed from settings")
```

### Step 4: Modify `_open_advanced_settings()` Method

Update `_open_advanced_settings()` to sync before opening and refresh after closing:

- Add `_sync_settings_to_manager()` call before creating AdvancedSettingsWindow
- Add `_refresh_from_settings()` call after `wait_window()` returns
- Update debug log message

**Location:** Lines 790-797 in `app/main.py`

**Updated code:**
```python
def _open_advanced_settings(self) -> None:
    """Open the Advanced Settings window."""
    self.logger.info("Opening Advanced Settings window")

    # Sync current GUI state to SettingsManager before opening
    self._sync_settings_to_manager()

    window = AdvancedSettingsWindow(self, self.settings)
    self.wait_window(window)  # Block until window closes

    # Refresh main window from SettingsManager after closing
    self._refresh_from_settings()
    self.logger.debug("Advanced Settings window closed, main GUI refreshed")
```

### Step 5: Add `trace_add` Callbacks for Instant Sync

Add trace callbacks in `__init__()` after filter variable creation:

- Add `trace_add("write", ...)` callbacks for each numeric amount StringVar
- Each callback calls `_sync_numeric_setting()` with the appropriate key
- Place after line 113 (after `file_log_level_var` creation, before `_create_widgets()`)

**Location:** After line 113, before line 115 in `app/main.py`

**Code to add:**
```python
# Add trace callbacks for instant sync of numeric filter amounts
self.precision_fix_amount_var.trace_add(
    "write",
    lambda *_: self._sync_numeric_setting(
        "precision_fix_amount", self.precision_fix_amount_var
    ),
)
self.gap_bridge_amount_var.trace_add(
    "write",
    lambda *_: self._sync_numeric_setting(
        "gap_bridge_amount", self.gap_bridge_amount_var
    ),
)
self.min_area_filter_amount_var.trace_add(
    "write",
    lambda *_: self._sync_numeric_setting(
        "min_area_filter_amount", self.min_area_filter_amount_var
    ),
)
self.min_side_filter_amount_var.trace_add(
    "write",
    lambda *_: self._sync_numeric_setting(
        "min_side_filter_amount", self.min_side_filter_amount_var
    ),
)
```

### Step 6: Create Unit Tests for Settings Synchronization

Create a new test file `app/tests/core/test_main_settings_sync.py`:

- Test `_sync_numeric_setting()` with valid float values
- Test `_sync_numeric_setting()` with invalid values (should not raise)
- Test that `_sync_settings_to_manager()` syncs all expected settings
- Test that `_refresh_from_settings()` updates log level var
- Use mocking to avoid GUI instantiation where possible

**Location:** New file `app/tests/core/test_main_settings_sync.py`

### Step 7: Run Validation Commands

Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
- Test `_sync_numeric_setting()` with valid float string ("3.5") - should sync value 3.5
- Test `_sync_numeric_setting()` with invalid string ("abc") - should not raise, should not sync
- Test `_sync_numeric_setting()` with empty string ("") - should not raise, should not sync
- Test `_sync_settings_to_manager()` syncs all 9 filter-related settings (4 booleans, 4 numeric amounts, 1 unit override)
- Test `_refresh_from_settings()` updates log_level_var when settings differ

### Integration Tests
- Test that opening Advanced Settings triggers pre-sync (settings should reflect main GUI state)
- Test that closing Advanced Settings triggers refresh (main GUI should reflect any changes)
- Test trace callbacks trigger sync on StringVar changes

### Edge Cases
- Empty numeric amount field (should not sync)
- Invalid numeric input like "abc" (should not sync or raise)
- Very large numbers (should sync if valid)
- Negative numbers (should sync - validation is in SettingsManager)
- Unit override set to "DXF/DWG" (auto-detect, should sync as None)

### Playwright MCP Tests
Not applicable - this feature is internal settings management without user-visible UI changes that require E2E testing. The Filters tab in Advanced Settings already displays read-only values that will be updated by this sync mechanism.

## Acceptance Criteria

1. **Numeric amounts sync to SettingsManager**: Changing Gap Bridge amount to 4.0 in main GUI should result in `settings.get("gap_bridge_amount")` returning 4.0
2. **All filter amounts sync**: All four filter amounts (precision_fix, gap_bridge, min_area, min_side) sync to SettingsManager
3. **Unit override syncs**: Changing unit dropdown should sync to `settings.get("unit_override")`
4. **Pre-open sync works**: Opening Advanced Settings shows current main GUI values in Filters tab
5. **Post-close refresh works**: Changing `log_viewer_level` in Advanced Settings updates main GUI dropdown after close
6. **Instant sync via trace**: Typing in numeric fields immediately syncs values (no need to click elsewhere)
7. **Invalid input handling**: Invalid numeric input (like "abc") doesn't raise exceptions or corrupt settings
8. **All existing tests pass**: No regressions in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_settings.py -v` - Run existing settings tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run new sync tests
- `uv run pytest app/tests/ -v` - Run full test suite
- `uv run mypy app/` - Type check all code
- `uv run ruff check app/` - Lint all code
- `uv run ruff format app/ --check` - Verify formatting

## Notes

### Implementation Order
The steps are ordered for clean implementation:
1. Add helper method first (Step 1) so it's available for subsequent steps
2. Expand existing method (Step 2) using the helper
3. Add refresh method (Step 3) before modifying the caller
4. Modify Advanced Settings lifecycle (Step 4) using the new methods
5. Add trace callbacks (Step 5) last since they depend on the helper
6. Tests (Step 6) verify all functionality

### GUI Testing Limitation
Per README.md: "Skip GUI tests in WSL - X server issues make it unreliable." Unit tests should use mocking to avoid GUI instantiation. Manual testing is recommended for full validation.

### Trace Callback Behavior
The `trace_add` callbacks will fire on every character typed. This is intentional for instant sync. The `_sync_numeric_setting()` method handles invalid partial input (like "3." while typing "3.5") by catching ValueError and not syncing until input is valid.

### Future Considerations
- This is Unit 1 of a larger settings synchronization plan (Steps 1-3 from plan 075)
- Future units will add UI polish (button renames, min window size) and UX enhancements (real-time validation, Summary tab)
- The `_refresh_from_settings()` method can be extended in future to refresh other settings if needed
