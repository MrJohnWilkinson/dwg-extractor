# Settings Synchronization Implementation Plan

## Executive Summary

This plan implements settings synchronization fixes between the main GUI and Advanced Settings window in the DXF Block Extractor. The implementation addresses bi-directional sync bugs, UI clarity improvements, real-time validation, and a copyable plain-text settings summary for user debugging/support purposes. Implementation is sequenced to build on prior changes systematically.

## Table Summary

| Step | Task | Files Modified | Dependencies |
|------|------|----------------|--------------|
| 1 | Expand `_sync_settings_to_manager()` with all numeric amounts | `app/main.py` | None |
| 2 | Add pre-open sync and post-close refresh to Advanced Settings flow | `app/main.py` | Step 1 |
| 3 | Add `trace_add` callbacks for instant sync on filter changes | `app/main.py` | Steps 1-2 |
| 4 | Rename "Settings" button to "Advanced Settings" | `app/main.py` | None |
| 5 | Rename buttons to "Apply All Changes" / "Save All as Default" | `app/core/settings_window.py` | None |
| 6 | Add `minsize(650, 600)` constraint to Advanced Settings window | `app/core/settings_window.py` | None |
| 7 | Style Filters tab info banner with distinct background | `app/core/settings_window.py` | None |
| 8 | Implement real-time validation with `trace_add` and red border | `app/core/settings_window.py` | None |
| 9 | Add Summary tab with copyable plain-text settings and Copy button | `app/core/settings_window.py` | None |

## Relevant Files

- **app/main.py:1067-1084** - `_sync_settings_to_manager()` only syncs booleans, missing numeric amounts
- **app/main.py:754-761** - `_open_advanced_settings()` lacks pre-sync and post-refresh calls
- **app/main.py:86-114** - Main GUI tkinter variables for filters (need trace callbacks)
- **app/main.py:174-181** - Settings button definition (needs rename)
- **app/core/settings_window.py:92-94** - Window geometry, needs minsize constraint
- **app/core/settings_window.py:162-186** - Button frame with Apply/Save lacking scope clarity
- **app/core/settings_window.py:543-551** - Filters tab info label needs prominent styling
- **app/core/settings_window.py:334-337** - Validation bound to FocusOut, needs trace_add
- **app/core/settings.py:52-88** - SETTINGS_SECTIONS dict for Summary tab grouping

## Scope

### In Scope

1. Expand `_sync_settings_to_manager()` to sync all numeric filter amounts
2. Add `_sync_settings_to_manager()` call before opening Advanced Settings
3. Add `_refresh_from_settings()` method and call after Advanced Settings closes
4. Add `trace_add` callbacks for instant sync on all filter variable changes
5. Rename "Settings" button to "Advanced Settings" in main GUI
6. Rename buttons to "Apply All Changes" and "Save All as Default" in Advanced Settings
7. Add `minsize(650, 600)` to Advanced Settings window
8. Style Filters tab info banner with distinct background and info indicator
9. Implement real-time validation using `trace_add` with red border feedback
10. Add Summary tab with plain-text copyable settings list and "Copy to Clipboard" button

### Out of Scope

- Keyboard shortcuts (Ctrl+Shift+S for Advanced Settings access)
- Preset configurations / named settings profiles
- Undo/redo capability for settings changes
- Live preview during settings changes
- Cloud sync across machines
- Multiple settings windows
- Bi-directional filter editing (filters editable in both main GUI and Advanced Settings)
- Export settings to file (.txt/.json) - in-app copy is sufficient
- Per-section Apply buttons (non-standard for tabbed dialogs)
- Visual indicator showing which tabs have unsaved changes
- Active filters chip/tag display in main window (filters already visible in main GUI)
- Main window height increase (no summary panel added to main window)

## Implementation Steps

### Step 1: Expand `_sync_settings_to_manager()` with Numeric Amounts

**File:** `app/main.py`

**Location:** Lines 1067-1084

**Changes:**

Add numeric filter amounts and unit override to the sync method:

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

    # Save to disk
    self.settings.save()
    self.logger.debug("Settings synchronized and saved")

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

---

### Step 2: Add Pre-Open Sync and Post-Close Refresh

**File:** `app/main.py`

**Location:** Lines 754-761 and new method

**Changes:**

1. Modify `_open_advanced_settings()` to sync before opening and refresh after closing:

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

2. Add new `_refresh_from_settings()` method:

```python
def _refresh_from_settings(self) -> None:
    """Refresh main GUI state from SettingsManager.

    Called after Advanced Settings closes to reflect any changes
    made to settings that affect the main window display.
    """
    # Refresh logging settings
    generate_log = self.settings.get("generate_log_file")
    self.log_file_var.set(generate_log)
    if generate_log:
        self.file_log_level_menu.configure(state="normal")
    else:
        self.file_log_level_menu.configure(state="disabled")

    self.file_log_level_var.set(self.settings.get("file_log_level"))

    self.logger.debug("Main GUI refreshed from settings")
```

---

### Step 3: Add `trace_add` Callbacks for Instant Sync

**File:** `app/main.py`

**Location:** After variable creation (around line 114), in `__init__`

**Changes:**

Add trace callbacks to all filter variables for instant sync:

```python
# In __init__, after creating all filter variables, add trace callbacks:

# Trace callbacks for instant sync
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

---

### Step 4: Rename Settings Button to "Advanced Settings"

**File:** `app/main.py`

**Location:** Lines 174-181

**Changes:**

```python
# Settings button
self.settings_button = ctk.CTkButton(
    button_frame,
    text="Advanced Settings",  # Changed from "Settings"
    width=120,  # Increased from 80 to fit longer text
    command=self._open_advanced_settings,
)
self.settings_button.pack(side="left", padx=(10, 0))
```

---

### Step 5: Rename Apply/Save Buttons with Scope Clarity

**File:** `app/core/settings_window.py`

**Location:** Lines 162-186

**Changes:**

```python
# Left side - Save as Default
self.save_default_button = ctk.CTkButton(
    button_frame,
    text="Save All as Default",  # Changed from "Save as Default"
    width=140,  # Increased from 120
    command=self._on_save_as_default,
)
self.save_default_button.pack(side="left")

# Right side - Cancel and Apply
self.apply_button = ctk.CTkButton(
    button_frame,
    text="Apply All Changes",  # Changed from "Apply"
    width=130,  # Increased from 100
    command=self._on_apply,
)
self.apply_button.pack(side="right")
```

---

### Step 6: Add minsize Constraint to Advanced Settings Window

**File:** `app/core/settings_window.py`

**Location:** Lines 92-94

**Changes:**

```python
# Configure window
self.title("Advanced Settings")
self.geometry("650x600")
self.resizable(True, True)
self.minsize(650, 600)  # ADD: Prevent window from being too small
```

---

### Step 7: Style Filters Tab Info Banner

**File:** `app/core/settings_window.py`

**Location:** Lines 543-551 (in `_populate_filters_tab`)

**Changes:**

Replace the plain info label with a styled banner:

```python
def _populate_filters_tab(self, parent: ctk.CTkFrame) -> None:
    """Populate the Filters tab with settings."""
    # Scrollable frame for content
    scroll_frame = ctk.CTkScrollableFrame(parent)
    scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # Section header
    self._create_section_header(scroll_frame, "Filter Settings", "filters")

    # PROMINENT INFO BANNER - styled frame with info indicator
    info_frame = ctk.CTkFrame(
        scroll_frame,
        fg_color=("gray85", "gray25"),  # Subtle but distinct background
        corner_radius=8,
    )
    info_frame.pack(fill="x", pady=(0, 15), padx=5)

    # Info icon/indicator
    info_indicator = ctk.CTkLabel(
        info_frame,
        text="i",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=("gray40", "gray70"),
        width=24,
    )
    info_indicator.pack(side="left", padx=(12, 8), pady=10)

    # Info text
    info_label = ctk.CTkLabel(
        info_frame,
        text="Filter settings are configured in the main window.\n"
             "This tab displays current values for reference only.",
        font=ctk.CTkFont(size=11),
        text_color=("gray30", "gray80"),
        anchor="w",
        justify="left",
    )
    info_label.pack(side="left", fill="x", expand=True, pady=10, padx=(0, 12))

    # Rest of filter display (read-only)...
```

---

### Step 8: Implement Real-Time Validation with `trace_add`

**File:** `app/core/settings_window.py`

**Location:** Lines 298-349 (in `_create_setting_row`, entry widget creation)

**Changes:**

Replace FocusOut binding with trace_add for real-time validation:

```python
else:  # entry
    validation: SettingValidation = SETTINGS_VALIDATION_REGISTRY.get(
        setting_key,
        {
            "min_value": None,
            "max_value": None,
            "default": None,
            "unit_aware": False,
        },
    )
    min_val = validation.get("min_value")
    max_val = validation.get("max_value")

    # Show range hint
    if min_val is not None and max_val is not None:
        range_text = f"({min_val} - {max_val})"
        range_label = ctk.CTkLabel(
            control_frame,
            text=range_text,
            font=ctk.CTkFont(size=9),
            text_color="gray",
        )
        range_label.pack()

    var = ctk.StringVar(
        value=str(current_value) if current_value is not None else ""
    )
    entry = ctk.CTkEntry(
        control_frame,
        width=100,
        textvariable=var,
    )
    entry.pack()
    entry.var = var

    # Real-time validation using trace_add
    var.trace_add(
        "write",
        lambda *_, k=setting_key, w=entry: self._validate_entry(k, w),
    )

    self._entry_widgets[setting_key] = entry

    # Error label (initially hidden)
    error_label = ctk.CTkLabel(
        control_frame,
        text="",
        font=ctk.CTkFont(size=9),
        text_color="red",
    )
    error_label.pack()
    self._error_labels[setting_key] = error_label
```

---

### Step 9: Add Summary Tab with Copyable Plain-Text Settings

**File:** `app/core/settings_window.py`

**Location:** After logging tab creation (in `_create_widgets`)

**Changes:**

1. Add Summary tab creation in `_create_widgets()`:

```python
# Create tabs
self.tabview.add("Filters")
self.tabview.add("Performance")
self.tabview.add("Precision")
self.tabview.add("Output")
self.tabview.add("Logging")
self.tabview.add("Summary")  # ADD: New Summary tab

# Populate tabs
self._create_filters_tab()
self._create_performance_tab()
self._create_precision_tab()
self._create_output_tab()
self._create_logging_tab()
self._create_summary_tab()  # ADD: New Summary tab
```

2. Add new methods for Summary tab:

```python
def _create_summary_tab(self) -> None:
    """Create the Summary tab content."""
    tab = self.tabview.tab("Summary")
    self._populate_summary_tab(tab)

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
            # Format key nicely
            display_key = key.replace("_", " ").title()
            summary_lines.append(f"  {display_key}: {display_value}")
        summary_lines.append("")

    self.summary_textbox.configure(state="normal")
    self.summary_textbox.delete("1.0", "end")
    self.summary_textbox.insert("1.0", "\n".join(summary_lines))
    self.summary_textbox.configure(state="disabled")  # Read-only but selectable

def _copy_summary(self) -> None:
    """Copy summary text to clipboard."""
    self.clipboard_clear()
    self.clipboard_append(self.summary_textbox.get("1.0", "end-1c"))

    # Visual feedback
    self.copy_btn.configure(text="Copied!")
    self.after(1500, lambda: self.copy_btn.configure(text="Copy to Clipboard"))
```

3. Update `_refresh_tab()` to handle Summary tab:

```python
def _refresh_tab(self, section: str) -> None:
    """Refresh all controls in a tab after reset."""
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
    elif section == "summary":
        self._populate_summary_tab(tab_frame)
```

4. Update `_on_apply()` and `_on_save_as_default()` to refresh Summary tab after changes:

```python
def _on_apply(self) -> None:
    """Handle Apply button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot apply - validation errors exist")
        return

    self._apply_settings()
    self._refresh_summary()  # ADD: Update summary after applying
    logger.info("Settings applied")
    self.destroy()

def _on_save_as_default(self) -> None:
    """Handle Save as Default button click."""
    if not self._validate_all_entries():
        logger.warning("Cannot save - validation errors exist")
        return

    self._apply_settings()
    self._refresh_summary()  # ADD: Update summary after saving

    if self.settings.save():
        logger.info("Settings saved as default")
        # Show brief confirmation
        self.save_default_button.configure(text="Saved!")
        self.after(
            1500, lambda: self.save_default_button.configure(text="Save All as Default")
        )
    else:
        logger.error("Failed to save settings")
```

---

## Testing Checklist

### Step 1-3: Settings Synchronization
- [ ] Change Gap Bridge amount in main GUI to 4, open Advanced Settings, verify Filters tab shows 4
- [ ] Change all filter amounts, verify they appear in Advanced Settings
- [ ] Enable/disable filters, verify state syncs to Advanced Settings
- [ ] Verify unit override syncs correctly

### Step 2: Post-Close Refresh
- [ ] Change logging settings in Advanced Settings, verify main GUI reflects changes after close
- [ ] Verify "Generate Log File" checkbox state updates
- [ ] Verify file log level dropdown state updates

### Step 4: Button Rename
- [ ] Verify "Advanced Settings" button displays correctly
- [ ] Verify button width accommodates new text

### Steps 5-6: Advanced Settings Window
- [ ] Verify "Apply All Changes" and "Save All as Default" buttons display correctly
- [ ] Verify window cannot be resized smaller than 650x600
- [ ] Verify window can still be maximized/expanded

### Step 7: Filters Tab Banner
- [ ] Verify info banner has distinct background color
- [ ] Verify info indicator "i" displays correctly
- [ ] Verify text is readable in both light and dark modes

### Step 8: Real-Time Validation
- [ ] Type invalid value in Performance threshold, verify red border appears immediately
- [ ] Type valid value, verify border returns to normal
- [ ] Verify validation works for all numeric entry fields
- [ ] Verify error messages display correctly

### Step 9: Summary Tab
- [ ] Verify Summary tab appears after Logging tab
- [ ] Verify all settings display with proper formatting
- [ ] Verify "Copy to Clipboard" button copies text
- [ ] Verify "Copied!" feedback displays for 1.5 seconds
- [ ] Verify copied text is plain text suitable for pasting in support channels
- [ ] Verify summary updates after Reset Section is clicked
