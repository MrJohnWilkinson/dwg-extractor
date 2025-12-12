# Feature: Main GUI Migration to SettingsManager (Unit 5 - Phase C1)

## Feature Description

This specification covers the migration of the main GUI (`app/main.py`) to use the `SettingsManager` class for centralized settings management. It implements phase C1 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md).

The migration involves:
- Adding a `SettingsManager` instance to `DXFExtractorApp.__init__()`
- Loading persisted settings at startup via `settings.load()`
- Initializing GUI control variables from SettingsManager values
- Updating getter methods to use SettingsManager for validation
- Adding a "Settings" button to the main window
- Saving settings on changes via `settings.save()`

**Scope:** C1 only (Main GUI Migration)

**Out of Scope (handled in later units):**
- C2: Advanced Settings Window modal (the button opens it, but the window is not implemented)
- D1-D2: Pipeline integration for new threshold parameters
- Output directory customization, filename prefix features

**Prerequisites:**
- Unit 1-2 (A1-A6) completed: Parallel processing removed, tests updated
- Unit 3 (B1-B2) completed: AppSettings TypedDict (24 fields), SETTINGS_VALIDATION_REGISTRY
- Unit 4 (B3-B4) completed: SettingsManager class with persistence
- Tests: 919 passing

**Implementation Learnings from Previous Units:**
- Unit 1-2: Removed parallel processing from extractor.py
- Unit 3: Added AppSettings TypedDict (24 fields), SettingValidation TypedDict
- Unit 4: Created app/core/settings.py with SettingsManager class (54 tests)
- Tests: 919 total tests passing

## User Story

As a DXF Block Extractor user
I want my filter settings to be automatically saved and restored between sessions
So that I don't have to reconfigure them every time I open the application

## Problem Statement

Currently the main GUI (`app/main.py`) has several limitations:

1. **No settings persistence** - Filter settings reset to defaults on every application launch
2. **Duplicated validation logic** - Each getter method (`_get_gap_bridge_amount`, etc.) has its own validation code
3. **No centralized settings management** - Settings are scattered across individual tkinter variables
4. **No pathway to Advanced Settings** - Users cannot access additional configuration options
5. **Inconsistent defaults** - Default values are hardcoded in multiple places

## Solution Statement

Migrate the main GUI to use `SettingsManager` as the centralized settings management system:

1. **Initialize SettingsManager at startup** - Load persisted settings automatically
2. **Populate GUI controls from SettingsManager** - Default values come from the manager
3. **Delegate validation to SettingsManager** - Remove duplicated validation logic
4. **Add Settings button** - Provide entry point for future Advanced Settings Window
5. **Save settings on changes** - Persist user preferences automatically

The existing UI behavior and appearance remain unchanged - this is a behind-the-scenes infrastructure migration.

## Relevant Files

Use these files to implement the feature:

- `app/main.py` - Main GUI application file that needs migration
  - `DXFExtractorApp.__init__()` - Add SettingsManager instance and load()
  - `_create_widgets()` - Add Settings button to button_frame
  - `_get_*_amount()` methods - Update to use SettingsManager.validate()
  - Add `_open_advanced_settings()` placeholder method
  - Add `_sync_settings_to_manager()` method for persistence

- `app/core/settings.py` - SettingsManager class (already implemented in Unit 4)
  - Import and instantiate in main.py

- `app/core/constants.py` - Contains validation ranges and defaults
  - Already imported in main.py, no changes needed

- `app/core/types.py` - Contains AppSettings TypedDict
  - For type annotations if needed

### Existing Tests (no changes expected)

- `app/tests/core/test_settings.py` - SettingsManager tests (54 tests from Unit 4)
- All existing extractor, excel_writer, geometry tests

### New Tests

- No new test file needed - existing tests validate behavior
- GUI tests are skipped in WSL per README.md guidance

## Implementation Plan

### Phase 1: Foundation

Add SettingsManager instance to `DXFExtractorApp`:

1. Import `SettingsManager` from `core.settings`
2. Create instance in `__init__()` before widget creation
3. Call `settings.load()` to restore persisted settings
4. Log whether settings were loaded from file or defaults used

### Phase 2: Core Implementation

Integrate SettingsManager with existing GUI controls:

1. **Initialize GUI variables from SettingsManager** - Use `settings.get()` for initial values
2. **Update getter methods** - Delegate validation to `settings.validate()`
3. **Add Settings button** - Insert into button_frame with proper layout
4. **Add placeholder method** - `_open_advanced_settings()` logs message
5. **Add settings sync method** - `_sync_settings_to_manager()` captures GUI state

### Phase 3: Integration

Wire up settings persistence:

1. **Save on filter toggle** - Call sync and save when checkboxes change
2. **Save on amount entry** - Consider saving when entry loses focus (optional, may defer)
3. **Maintain backwards compatibility** - Existing behavior unchanged
4. **Test manually** - Verify settings persist across application restarts

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add SettingsManager Import

Add the import statement to `app/main.py`:

```python
from core.settings import SettingsManager
```

Add this after the existing imports from `core.constants`.

### Step 2: Add SettingsManager Instance to __init__

In `DXFExtractorApp.__init__()`, add the SettingsManager initialization **before** the GUI control variables are set:

```python
def __init__(self) -> None:
    super().__init__()

    # Initialize logger
    self.logger: logging.Logger = setup_logger(__name__)
    self.logger.info("DXF Block Extractor application started")

    # Initialize settings manager and load persisted settings
    self.settings = SettingsManager()
    settings_loaded = self.settings.load()
    if settings_loaded:
        self.logger.info("Loaded settings from config file")
    else:
        self.logger.debug("Using default settings (no config file found)")

    # ... rest of __init__ continues
```

### Step 3: Initialize GUI Variables from SettingsManager

Update the GUI control variable initialization to use SettingsManager values where applicable. Note that filter settings use unit-aware defaults from the GUI dropdown, so we keep the existing pattern for filter amounts but use SettingsManager for boolean flags:

```python
# Unit selection, precision fix, and gap bridge settings
self.unit_selection_var = ctk.StringVar(value="DXF/DWG")
self.precision_fix_var = ctk.BooleanVar(
    value=self.settings.get("precision_fix_enabled")
)
self.precision_fix_amount_var = ctk.StringVar(value="3.0")
self.gap_bridge_var = ctk.BooleanVar(
    value=self.settings.get("gap_bridge_enabled")
)
self.gap_bridge_amount_var = ctk.StringVar(value="3.0")

# Min Area Filter settings
self.min_area_filter_var = ctk.BooleanVar(
    value=self.settings.get("min_area_filter_enabled")
)
self.min_area_filter_amount_var = ctk.StringVar(value="100000.0")

# Min Side Filter settings
self.min_side_filter_var = ctk.BooleanVar(
    value=self.settings.get("min_side_filter_enabled")
)
self.min_side_filter_amount_var = ctk.StringVar(value="10.0")

# Log file generation settings
self.log_file_var = ctk.BooleanVar(
    value=self.settings.get("generate_log_file")
)
self.file_log_level_var = ctk.StringVar(
    value=self.settings.get("file_log_level")
)
```

### Step 4: Update _create_widgets to Enable/Disable Based on Initial Settings

After creating widgets, sync the entry states with the boolean flags. Add this at the end of `_create_widgets()`:

```python
# Sync entry widget states with initial checkbox values
if self.precision_fix_var.get():
    self.precision_fix_entry.configure(state="normal")
else:
    self.precision_fix_entry.configure(state="disabled")

if self.gap_bridge_var.get():
    self.gap_bridge_entry.configure(state="normal")
# gap_bridge_entry is already disabled by default in widget creation

if self.min_area_filter_var.get():
    self.min_area_filter_entry.configure(state="normal")
# min_area_filter_entry is already disabled by default

if self.min_side_filter_var.get():
    self.min_side_filter_entry.configure(state="normal")
# min_side_filter_entry is already disabled by default

if self.log_file_var.get():
    self.file_log_level_menu.configure(state="normal")
# file_log_level_menu is already disabled by default
```

### Step 5: Add Settings Button to button_frame

In `_create_widgets()`, add the Settings button after the Open Folder button but before the Abort button:

```python
# Open Folder button (initially disabled)
self.open_folder_button = ctk.CTkButton(
    button_frame,
    text="Open Folder",
    width=120,
    command=self._open_output_folder,
    state="disabled",
)
self.open_folder_button.pack(side="left", padx=(10, 0))

# Settings button
self.settings_button = ctk.CTkButton(
    button_frame,
    text="Settings",
    width=80,
    command=self._open_advanced_settings,
)
self.settings_button.pack(side="left", padx=(10, 0))

# Abort button (initially hidden - shown during extraction)
self.abort_button = ctk.CTkButton(
    # ... existing code
)
```

### Step 6: Add _open_advanced_settings Placeholder Method

Add the placeholder method to `DXFExtractorApp`:

```python
def _open_advanced_settings(self) -> None:
    """Open the Advanced Settings window.

    Currently a placeholder - will be implemented in Unit 6 (C2).
    """
    self.logger.info("Advanced Settings not yet implemented")
```

### Step 7: Add _sync_settings_to_manager Method

Add a method to synchronize GUI state to SettingsManager:

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

    # Sync logging settings
    self.settings.set("generate_log_file", self.log_file_var.get())
    self.settings.set("file_log_level", self.file_log_level_var.get())

    # Save to disk
    self.settings.save()
    self.logger.debug("Settings synchronized and saved")
```

### Step 8: Update Toggle Methods to Sync Settings

Update each toggle method to call `_sync_settings_to_manager()`:

**Update `_on_precision_fix_toggle()`:**
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
            self.logger.debug(
                "Disabled gap bridge (mutually exclusive with precision fix)"
            )
    else:
        self.precision_fix_entry.configure(state="disabled")

    # Sync settings to manager and save
    self._sync_settings_to_manager()
```

**Update `_on_gap_bridge_toggle()`:**
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
            self.logger.debug(
                "Disabled precision fix (mutually exclusive with gap bridge)"
            )
    else:
        self.gap_bridge_entry.configure(state="disabled")

    # Sync settings to manager and save
    self._sync_settings_to_manager()
```

**Update `_on_min_area_filter_toggle()`:**
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

    # Sync settings to manager and save
    self._sync_settings_to_manager()
```

**Update `_on_min_side_filter_toggle()`:**
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

    # Sync settings to manager and save
    self._sync_settings_to_manager()
```

**Update `_on_log_file_toggle()`:**
```python
def _on_log_file_toggle(self) -> None:
    """Handle log file checkbox toggle - enable/disable level dropdown."""
    if self.log_file_var.get():
        self.file_log_level_menu.configure(state="normal")
    else:
        self.file_log_level_menu.configure(state="disabled")

    # Sync settings to manager and save
    self._sync_settings_to_manager()
```

### Step 9: Update _start_extraction to Hide Settings Button

Update `_start_extraction()` to hide the Settings button during extraction:

```python
def _start_extraction(self) -> None:
    """Prepare UI for extraction - show abort button, create event."""
    self.abort_event = threading.Event()
    self.browse_button.pack_forget()
    self.extract_button.pack_forget()
    self.open_folder_button.pack_forget()
    self.settings_button.pack_forget()  # Hide settings button during extraction
    self.abort_button.pack(side="left", padx=10)
```

### Step 10: Update _restore_ui to Show Settings Button

Update `_restore_ui()` to restore the Settings button:

```python
def _restore_ui(self) -> None:
    """Restore UI to normal state after extraction completes or aborts."""
    self.abort_button.pack_forget()
    self.abort_button.configure(state="normal")  # Reset state for next use
    self.browse_button.pack(side="left", padx=(0, 10))
    self.extract_button.pack(side="left")
    self.open_folder_button.pack(side="left", padx=(10, 0))
    self.settings_button.pack(side="left", padx=(10, 0))  # Restore settings button
    self.abort_event = None
```

### Step 11: Update Getter Methods to Use SettingsManager Validation

Update the getter methods to use SettingsManager.validate() for consistent validation. The existing validation logic remains but uses the centralized validation:

**Update `_get_gap_bridge_amount()`:**
```python
def _get_gap_bridge_amount(self) -> float | None:
    """Get validated gap bridge amount, or None if invalid/disabled."""
    if not self.gap_bridge_var.get():
        return None
    try:
        amount = float(self.gap_bridge_amount_var.get())
        is_valid, error_msg = self.settings.validate("gap_bridge_amount", amount)
        if is_valid:
            return amount
        else:
            self.logger.warning(f"Gap bridge amount validation failed: {error_msg}")
            return None
    except ValueError:
        self.logger.warning("Invalid gap bridge amount")
        return None
```

**Update `_get_precision_fix_amount()`:**
```python
def _get_precision_fix_amount(self) -> float | None:
    """Get validated precision fix amount, or None if invalid/disabled."""
    if not self.precision_fix_var.get():
        return None
    try:
        amount = float(self.precision_fix_amount_var.get())
        is_valid, error_msg = self.settings.validate("precision_fix_amount", amount)
        if is_valid:
            return amount
        else:
            self.logger.warning(f"Precision fix amount validation failed: {error_msg}")
            return None
    except ValueError:
        self.logger.warning("Invalid precision fix amount")
        return None
```

**Update `_get_min_area_filter_amount()`:**
```python
def _get_min_area_filter_amount(self) -> float | None:
    """Get validated min area filter amount, or None if invalid/disabled."""
    if not self.min_area_filter_var.get():
        return None
    try:
        amount = float(self.min_area_filter_amount_var.get())
        is_valid, error_msg = self.settings.validate("min_area_filter_amount", amount)
        if is_valid:
            return amount
        else:
            self.logger.warning(f"Min area filter amount validation failed: {error_msg}")
            return None
    except ValueError:
        self.logger.warning("Invalid min area filter amount")
        return None
```

**Update `_get_min_side_filter_amount()`:**
```python
def _get_min_side_filter_amount(self) -> float | None:
    """Get validated min side filter amount, or None if invalid/disabled."""
    if not self.min_side_filter_var.get():
        return None
    try:
        amount = float(self.min_side_filter_amount_var.get())
        is_valid, error_msg = self.settings.validate("min_side_filter_amount", amount)
        if is_valid:
            return amount
        else:
            self.logger.warning(f"Min side filter amount validation failed: {error_msg}")
            return None
    except ValueError:
        self.logger.warning("Invalid min side filter amount")
        return None
```

### Step 12: Run Type Checking

Verify the changes pass type checking:

```bash
uv run mypy app/main.py
```

### Step 13: Run Linting

Verify the changes pass linting:

```bash
uv run ruff check app/main.py
uv run ruff format app/main.py --check
```

### Step 14: Run Full Test Suite

Run all tests to ensure no regressions:

```bash
uv run pytest app/tests/ -v
```

### Step 15: Manual Verification (Optional - Skip in WSL)

If running on a system with GUI support:

1. Launch application: `uv run python app/main.py`
2. Verify Settings button appears in button row
3. Click Settings button - verify log message appears
4. Toggle filter checkboxes - verify settings persist after restart
5. Start extraction - verify Settings button hides
6. After extraction - verify Settings button reappears

## Testing Strategy

### Unit Tests

- No new unit tests required for this migration
- Existing `test_settings.py` covers SettingsManager functionality (54 tests)
- Existing extractor tests validate extraction behavior is unchanged

### Integration Tests

- Manual testing of settings persistence across application restarts
- Verify checkbox states restore correctly on startup

### Edge Cases

- Application startup with no existing settings file (first run)
- Application startup with corrupted settings file (graceful fallback)
- Mutual exclusivity between precision_fix and gap_bridge preserved
- Settings button visibility during extraction vs idle states
- Log file toggle persists file_log_level setting

### Playwright MCP Tests

- Skip GUI tests in WSL per README.md guidance
- E2E tests for Advanced Settings Window will be added in Unit 6 (C2)

## Acceptance Criteria

- [ ] SettingsManager instance created in `DXFExtractorApp.__init__()`
- [ ] `settings.load()` called at startup
- [ ] GUI filter checkboxes initialize from SettingsManager values
- [ ] GUI logging settings initialize from SettingsManager values
- [ ] "Settings" button visible in main window button_frame
- [ ] Settings button positioned after "Open Folder" button
- [ ] Settings button hides during extraction
- [ ] Settings button reappears after extraction completes
- [ ] `_open_advanced_settings()` logs "Advanced Settings not yet implemented"
- [ ] Filter toggle methods call `_sync_settings_to_manager()`
- [ ] `_sync_settings_to_manager()` saves settings to disk
- [ ] Getter methods use `SettingsManager.validate()` for validation
- [ ] Existing filter controls function identically to before
- [ ] No visual changes to existing UI layout (except new Settings button)
- [ ] mypy passes with no errors
- [ ] ruff check passes with no errors
- [ ] ruff format passes with no changes needed
- [ ] All existing tests pass (919+ tests)

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/main.py` - Type check main.py for import and type errors
- `uv run mypy app/` - Full type check to catch any cascading issues
- `uv run ruff check app/main.py` - Lint main.py for code quality issues
- `uv run ruff format app/main.py --check` - Verify main.py formatting
- `uv run pytest app/tests/core/test_settings.py -v` - Run SettingsManager tests (54 tests)
- `uv run pytest app/tests/ -v` - Run full test suite (should be 919+ tests, all passing)

## Notes

1. **Settings button width** - Using 80px width to keep button compact and consistent with the plan specification.

2. **Settings persistence scope** - This unit only persists boolean flags (enabled/disabled states) and logging settings. Filter amount values continue to use unit-aware defaults based on the dropdown selection. Full filter amount persistence may be added in a future unit if desired.

3. **Mutual exclusivity preservation** - The existing mutual exclusivity between precision_fix and gap_bridge checkboxes is preserved. When one is enabled, the other is disabled and both changes are synced to SettingsManager.

4. **No new test file** - Per README.md guidance, GUI tests are skipped in WSL. The SettingsManager is thoroughly tested in `test_settings.py`. The main.py changes are infrastructure-level and don't introduce new testable logic beyond what's already covered.

5. **Entry state synchronization** - Added explicit entry state sync at the end of `_create_widgets()` to handle edge case where persisted settings differ from widget creation defaults.

6. **Import location** - The `SettingsManager` import is added after the existing `core.constants` imports to maintain import organization.

7. **Log level persistence** - The file_log_level dropdown value is persisted even when generate_log_file is disabled. This preserves the user's preferred log level for when they re-enable logging.

8. **After this unit completes**:
   - Main GUI uses SettingsManager for settings management
   - Filter checkbox states persist across application restarts
   - Settings button visible and ready for Advanced Settings Window (Unit 6)
   - All 919+ tests continue to pass
