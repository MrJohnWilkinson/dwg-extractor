# Feature: Summary Tab with Copyable Plain-Text Settings

## Feature Description
Add a Summary tab to the Advanced Settings window that displays all current settings in a human-readable, plain-text format. The tab includes a read-only textbox showing all settings grouped by section, a "Copy to Clipboard" button with visual feedback, and automatic refresh when settings change. This allows users to easily share their configuration for debugging or support purposes.

This is Unit 4 of the settings synchronization plan (Step 9 from plan 075), following:
- Unit 1 (commit 700cad8): Bidirectional settings sync between main GUI and Advanced Settings
- Unit 2 (commit 29777db): UI button/window polish (button renames, minsize constraint)
- Unit 3 (commit 15b0ded): Filters tab UX improvements (styled info banner, real-time validation)

## User Story
As a DXF Block Extractor user
I want to view and copy all my current settings in a readable format
So that I can share them for debugging, support, or documentation purposes

## Problem Statement
When users encounter issues or need support, they currently have no easy way to share their settings configuration. They would need to manually note down each setting from multiple tabs, which is error-prone and time-consuming. Additionally, there's no single view that shows all settings at once for quick reference.

## Solution Statement
Add a "Summary" tab as the last tab in the Advanced Settings window that:
1. Displays all settings in a plain-text format with section headers matching the existing tab organization
2. Provides a read-only but selectable textbox using monospace font for easy reading
3. Includes a "Copy to Clipboard" button that provides visual "Copied!" feedback for 1.5 seconds
4. Automatically refreshes when settings change via Apply, Save as Default, or Reset Section actions

The implementation leverages the existing `SETTINGS_SECTIONS` dictionary in `app/core/settings.py` (lines 52-88) to organize settings by section, ensuring consistency with the tab structure.

## Relevant Files
Use these files to implement the feature:

- **`app/core/settings_window.py`** - Advanced Settings window containing:
  - `_create_widgets()` method (lines 135-187) - needs Summary tab addition
  - `_refresh_tab()` method (lines 492-527) - needs Summary tab handling
  - `_on_apply()` method (lines 970-978) - needs `_refresh_summary()` call
  - `_on_save_as_default()` method (lines 987-1004) - needs `_refresh_summary()` call
  - New methods needed: `_create_summary_tab()`, `_populate_summary_tab()`, `_refresh_summary()`, `_copy_summary()`

- **`app/core/settings.py`** - Contains `SETTINGS_SECTIONS` dictionary (lines 52-88) used for organizing the summary display by section

- **`app/tests/core/test_settings.py`** - Existing settings tests for reference on test patterns

## Implementation Plan

### Phase 1: Foundation
Verify the existing `SETTINGS_SECTIONS` dictionary structure in `app/core/settings.py` and understand the tab creation pattern used by other tabs (Filters, Performance, Precision, Output, Logging).

### Phase 2: Core Implementation
1. Add "Summary" tab to the tabview in `_create_widgets()`
2. Implement `_create_summary_tab()` method following the pattern of other `_create_*_tab()` methods
3. Implement `_populate_summary_tab()` to create the UI with header, subheader, textbox, and copy button
4. Implement `_refresh_summary()` to generate the plain-text settings display
5. Implement `_copy_summary()` to copy text and show visual feedback

### Phase 3: Integration
1. Update `_refresh_tab()` to handle the "summary" section
2. Update `_on_apply()` to call `_refresh_summary()` after applying changes
3. Update `_on_save_as_default()` to call `_refresh_summary()` after saving
4. Ensure `_on_reset_section()` triggers summary refresh via `_refresh_tab()`

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Summary Tab to Tab View

Update `_create_widgets()` in `app/core/settings_window.py`:

- Add `self.tabview.add("Summary")` after the Logging tab
- Add `self._create_summary_tab()` call after `_create_logging_tab()`

**Location:** Lines 145-157 in `app/core/settings_window.py`

**Current code:**
```python
# Create tabs
self.tabview.add("Filters")
self.tabview.add("Performance")
self.tabview.add("Precision")
self.tabview.add("Output")
self.tabview.add("Logging")

# Populate tabs
self._create_filters_tab()
self._create_performance_tab()
self._create_precision_tab()
self._create_output_tab()
self._create_logging_tab()
```

**Updated code:**
```python
# Create tabs
self.tabview.add("Filters")
self.tabview.add("Performance")
self.tabview.add("Precision")
self.tabview.add("Output")
self.tabview.add("Logging")
self.tabview.add("Summary")

# Populate tabs
self._create_filters_tab()
self._create_performance_tab()
self._create_precision_tab()
self._create_output_tab()
self._create_logging_tab()
self._create_summary_tab()
```

### Step 2: Add `_create_summary_tab()` Method

Add a new method after `_create_logging_tab()` and before `_validate_all_entries()`:

**Location:** After line 893 (end of `_populate_logging_tab()`) in `app/core/settings_window.py`

**Code to add:**
```python
def _create_summary_tab(self) -> None:
    """Create the Summary tab content."""
    tab = self.tabview.tab("Summary")
    self._populate_summary_tab(tab)
```

### Step 3: Add `_populate_summary_tab()` Method

Add the method to create the Summary tab UI with header, textbox, and copy button:

**Location:** After `_create_summary_tab()` method

**Code to add:**
```python
def _populate_summary_tab(self, parent: ctk.CTkFrame) -> None:
    """Populate the Summary tab with copyable settings text."""
    # Header
    header = ctk.CTkLabel(
        parent,
        text="Current Settings Summary",
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    header.pack(pady=(15, 5))

    # Subheader
    subheader = ctk.CTkLabel(
        parent,
        text="Copy this text to share settings for debugging or support",
        font=ctk.CTkFont(size=10),
        text_color="gray",
    )
    subheader.pack(pady=(0, 10))

    # Copyable text box (read-only but selectable)
    self.summary_textbox = ctk.CTkTextbox(
        parent,
        height=400,
        width=580,
        font=("Courier", 11),
    )
    self.summary_textbox.pack(fill="both", expand=True, padx=15, pady=5)

    # Copy button
    self.copy_btn = ctk.CTkButton(
        parent,
        text="Copy to Clipboard",
        width=150,
        command=self._copy_summary,
    )
    self.copy_btn.pack(pady=15)

    # Populate summary
    self._refresh_summary()
```

### Step 4: Add `_refresh_summary()` Method

Add the method to generate the plain-text settings display:

**Location:** After `_populate_summary_tab()` method

**Code to add:**
```python
def _refresh_summary(self) -> None:
    """Refresh the summary textbox with current settings."""
    from .settings import SETTINGS_SECTIONS

    summary_lines = [
        "DXF Block Extractor Settings",
        "=" * 35,
        "",
    ]

    for section, keys in SETTINGS_SECTIONS.items():
        summary_lines.append(f"[{section.upper()}]")
        for key in keys:
            value = self.settings.get(key)
            if value is None:
                display_value = "(default)"
            elif isinstance(value, bool):
                display_value = "Yes" if value else "No"
            else:
                display_value = str(value)
            display_key = key.replace("_", " ").title()
            summary_lines.append(f"  {display_key}: {display_value}")
        summary_lines.append("")

    self.summary_textbox.configure(state="normal")
    self.summary_textbox.delete("1.0", "end")
    self.summary_textbox.insert("1.0", "\n".join(summary_lines))
    self.summary_textbox.configure(state="disabled")
```

### Step 5: Add `_copy_summary()` Method

Add the method to copy text to clipboard with visual feedback:

**Location:** After `_refresh_summary()` method

**Code to add:**
```python
def _copy_summary(self) -> None:
    """Copy summary text to clipboard."""
    self.clipboard_clear()
    self.clipboard_append(self.summary_textbox.get("1.0", "end-1c"))

    # Visual feedback
    self.copy_btn.configure(text="Copied!")
    self.after(1500, lambda: self.copy_btn.configure(text="Copy to Clipboard"))
```

### Step 6: Update `_refresh_tab()` to Handle Summary Tab

Update `_refresh_tab()` to include handling for the Summary section:

**Location:** Lines 492-527 in `app/core/settings_window.py`

**Add at the end of the if/elif chain (before the closing of the method):**
```python
elif section == "summary":
    self._populate_summary_tab(tab_frame)
```

**Note:** Also need to handle the summary tab specially since it doesn't have entries to clear in SETTINGS_SECTIONS. The method should check if the section is "summary" and call `_refresh_summary()` instead of the standard widget clearing logic.

**Updated `_refresh_tab()` method:**
```python
def _refresh_tab(self, section: str) -> None:
    """Refresh all controls in a tab after reset.

    Args:
        section: Section name matching tab name (lowercase)
    """
    # Handle Summary tab specially - just refresh content
    if section == "summary":
        self._refresh_summary()
        return

    # Re-create the tab content
    tab_name = section.capitalize()

    # Get the tab frame
    tab_frame = self.tabview.tab(tab_name)

    # Clear existing widgets
    for widget in tab_frame.winfo_children():
        widget.destroy()

    # Clear tracked widgets for this section
    from .settings import SETTINGS_SECTIONS

    for key in SETTINGS_SECTIONS.get(section, []):
        self._entry_widgets.pop(key, None)
        self._error_labels.pop(key, None)
        self._checkbox_vars.pop(key, None)
        self._dropdown_vars.pop(key, None)

    # Re-create based on section
    if section == "filters":
        self._populate_filters_tab(tab_frame)
    elif section == "performance":
        self._populate_performance_tab(tab_frame)
    elif section == "precision":
        self._populate_precision_tab(tab_frame)
    elif section == "output":
        self._populate_output_tab(tab_frame)
    elif section == "logging":
        self._populate_logging_tab(tab_frame)
```

### Step 7: Update `_on_apply()` to Refresh Summary

Update `_on_apply()` to call `_refresh_summary()` after applying settings:

**Location:** Lines 970-978 in `app/core/settings_window.py`

**Current code:**
```python
def _on_apply(self) -> None:
    """Handle Apply button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot apply - validation errors exist")
        return

    self._apply_settings()
    logger.info("Settings applied")
    self.destroy()
```

**Updated code:**
```python
def _on_apply(self) -> None:
    """Handle Apply button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot apply - validation errors exist")
        return

    self._apply_settings()
    self._refresh_summary()
    logger.info("Settings applied")
    self.destroy()
```

### Step 8: Update `_on_save_as_default()` to Refresh Summary

Update `_on_save_as_default()` to call `_refresh_summary()` after saving settings:

**Location:** Lines 987-1004 in `app/core/settings_window.py`

**Current code:**
```python
def _on_save_as_default(self) -> None:
    """Handle Save as Default button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot save - validation errors exist")
        return

    self._apply_settings()

    if self.settings.save():
        logger.info("Settings saved as default")
        # Show brief confirmation
        self.save_default_button.configure(text="Saved!")
        self.after(
            1500,
            lambda: self.save_default_button.configure(text="Save All as Default"),
        )
    else:
        logger.error("Failed to save settings")
```

**Updated code:**
```python
def _on_save_as_default(self) -> None:
    """Handle Save as Default button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot save - validation errors exist")
        return

    self._apply_settings()
    self._refresh_summary()

    if self.settings.save():
        logger.info("Settings saved as default")
        # Show brief confirmation
        self.save_default_button.configure(text="Saved!")
        self.after(
            1500,
            lambda: self.save_default_button.configure(text="Save All as Default"),
        )
    else:
        logger.error("Failed to save settings")
```

### Step 9: Update `_on_reset_section()` to Refresh Summary

The `_on_reset_section()` method already calls `_refresh_tab()` which will handle standard tabs. We need to also refresh the summary after any section reset.

**Location:** Lines 484-490 in `app/core/settings_window.py`

**Current code:**
```python
def _on_reset_section(self, section: str) -> None:
    """Reset a section to defaults and update UI."""
    logger.info(f"Resetting section: {section}")
    self.settings.reset_section(section)

    # Refresh the UI for this section
    self._refresh_tab(section)
```

**Updated code:**
```python
def _on_reset_section(self, section: str) -> None:
    """Reset a section to defaults and update UI."""
    logger.info(f"Resetting section: {section}")
    self.settings.reset_section(section)

    # Refresh the UI for this section
    self._refresh_tab(section)

    # Also refresh summary to reflect the reset
    self._refresh_summary()
```

### Step 10: Run Validation Commands

Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
No new unit tests required for this feature:
- The Summary tab is purely UI functionality
- The `SETTINGS_SECTIONS` dictionary is already tested in existing settings tests
- The clipboard operations use standard tkinter methods that don't require testing
- The settings display logic is straightforward string formatting

### Integration Tests
Not applicable - the Summary tab is a self-contained display feature that integrates with existing settings infrastructure.

### Edge Cases
- Empty settings (all at defaults): Should display "(default)" for all None values
- Boolean values: Should display "Yes" or "No" instead of "True" or "False"
- Long string values (e.g., output_directory path): Should display without truncation
- Special characters in settings values: Should display correctly
- Summary refresh after reset: Should show updated default values

### Playwright MCP Tests
Not applicable - this UI feature requires manual visual verification. The functionality is straightforward clipboard copy that doesn't benefit from E2E testing.

## Acceptance Criteria

1. **Summary tab appears after Logging tab**: The tab order should be Filters, Performance, Precision, Output, Logging, Summary
2. **Header displays correctly**: "Current Settings Summary" in bold 14pt font
3. **Subheader displays correctly**: "Copy this text to share settings for debugging or support" in gray 10pt font
4. **Textbox displays all settings**: All settings from SETTINGS_SECTIONS are shown with section headers
5. **Section headers are uppercase**: [FILTERS], [PERFORMANCE], [PRECISION], [OUTPUT], [LOGGING]
6. **Setting keys are human-readable**: Snake_case converted to Title Case (e.g., "precision_fix_enabled" -> "Precision Fix Enabled")
7. **Boolean values show Yes/No**: Not "True"/"False"
8. **None values show "(default)"**: Indicates setting is using default value
9. **Textbox is read-only**: User can select text but not edit
10. **Monospace font**: Textbox uses Courier 11pt for clean alignment
11. **Copy button works**: Clicking copies all text to clipboard
12. **Visual feedback shows**: Button text changes to "Copied!" for 1.5 seconds
13. **Summary refreshes on Apply**: After clicking "Apply All Changes"
14. **Summary refreshes on Save**: After clicking "Save All as Default"
15. **Summary refreshes on Reset**: After clicking any "Reset Section" button
16. **All existing tests pass**: No regressions in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run settings sync tests (from Unit 1)
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check all code
- `uv run ruff check app/` - Lint all code
- `uv run ruff format app/ --check` - Verify formatting

## Testing Checklist (Manual)

These changes require manual testing on a system with a display server:

- [ ] Verify Summary tab appears after Logging tab
- [ ] Verify header "Current Settings Summary" displays correctly
- [ ] Verify subheader text displays in gray
- [ ] Verify all settings display with proper section headers
- [ ] Verify boolean values show "Yes" or "No"
- [ ] Verify None values show "(default)"
- [ ] Verify setting names are human-readable (Title Case)
- [ ] Verify textbox uses monospace font
- [ ] Verify textbox is read-only (can select, cannot edit)
- [ ] Verify "Copy to Clipboard" button is visible
- [ ] Click "Copy to Clipboard" and verify text is copied (paste elsewhere to confirm)
- [ ] Verify "Copied!" feedback displays for ~1.5 seconds
- [ ] Change a setting, click "Apply All Changes", verify summary updates before window closes
- [ ] Open Advanced Settings again, change a setting, click "Save All as Default", verify summary updates
- [ ] Click "Reset Section" on any tab, verify summary updates to show default values

## Notes

### Implementation Order
The steps are ordered for clean implementation:
1. Add tab and creation method first (Steps 1-2)
2. Add UI population method (Step 3)
3. Add refresh and copy methods (Steps 4-5)
4. Update existing methods for integration (Steps 6-9)
5. Run validation (Step 10)

### GUI Testing Limitation
Per README.md: "Skip GUI tests in WSL - X server issues make it unreliable." These UI changes require manual testing on a system with a display server. The automated tests verify no regressions in existing functionality.

### SETTINGS_SECTIONS Already Exists
The `SETTINGS_SECTIONS` dictionary already exists in `app/core/settings.py` (lines 52-88) and is used by the `_refresh_tab()` method. No changes to settings.py are needed.

### Prior Unit Context
This is Unit 4 of the settings synchronization plan:
- Unit 1 (spec 076, commit 700cad8): Added bidirectional settings sync, `_sync_numeric_setting()`, `_refresh_from_settings()`, trace_add callbacks
- Unit 2 (spec 077, commit 29777db): Renamed buttons ("Advanced Settings", "Apply All Changes", "Save All as Default"), added minsize(650, 600) constraint
- Unit 3 (spec 078, commit 15b0ded): Added styled info banner in Filters tab, replaced FocusOut with trace_add for real-time validation

### Clipboard API
The implementation uses standard tkinter clipboard methods (`clipboard_clear()`, `clipboard_append()`, `get()`) which are inherited by CTkToplevel from the tkinter Toplevel class. These are cross-platform and work on Windows, macOS, and Linux (with X server).

### Button Feedback Pattern
The "Copied!" feedback pattern with `self.after(1500, ...)` is consistent with the "Saved!" feedback already implemented for the "Save All as Default" button in `_on_save_as_default()`.
