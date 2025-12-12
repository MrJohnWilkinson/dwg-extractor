# Settings Synchronization Implementation Plan - Updated

## Executive Summary

This is an updated version of plan 067, revised to account for logging-related changes made since the original plan. Several improvements have been implemented around log level control and settings persistence, but the core synchronization issues between the main GUI and Advanced Settings window remain. This plan details what's still needed and provides updated implementation steps.

## Table Summary

| Step | Task | Status | Files Modified | Notes |
|------|------|--------|----------------|-------|
| 1 | Expand `_sync_settings_to_manager()` with numeric amounts + unit | **Needed** | `app/main.py` | Logging settings already synced; add numeric filter amounts |
| 2 | Add pre-open sync and post-close refresh | **Needed** | `app/main.py` | Log viewer level now in Advanced Settings |
| 3 | Add `trace_add` callbacks for instant sync | **Needed** | `app/main.py` | For numeric amount entries |
| 4 | Rename "Settings" button to "Advanced Settings" | **Needed** | `app/main.py` | Line 177 still shows "Settings" |
| 5 | Rename buttons to "Apply All Changes" / "Save All as Default" | **Needed** | `settings_window.py` | Lines 165, 174 still have short names |
| 6 | Add `minsize(650, 600)` constraint | **Needed** | `settings_window.py` | Line 94 lacks constraint |
| 7 | Style Filters tab info banner | **Needed** | `settings_window.py` | Lines 543-551 are plain text |
| 8 | Implement real-time validation with `trace_add` | **Needed** | `settings_window.py` | Lines 333-337 use FocusOut |
| 9 | Add Summary tab with copyable settings | **Needed** | `settings_window.py` | Not implemented yet |

## Relevant Files

- **app/main.py:1117-1135** - `_sync_settings_to_manager()` syncs booleans and logging, but missing numeric amounts
- **app/main.py:790-797** - `_open_advanced_settings()` lacks pre-sync and post-refresh
- **app/main.py:1085-1101** - `_on_log_level_change()` now sets source logger levels dynamically
- **app/main.py:177** - Settings button text still "Settings"
- **app/core/settings_window.py:163-186** - Button frame with Apply/Save buttons
- **app/core/settings_window.py:94** - Window geometry lacks minsize
- **app/core/settings_window.py:543-551** - Filters tab info label is plain text
- **app/core/settings_window.py:333-337** - Validation uses FocusOut binding
- **app/core/settings.py:52-88** - SETTINGS_SECTIONS dict for Summary tab grouping

## Changes Since Original Plan (067)

### Already Implemented

1. **Logging Settings Sync** - `_sync_settings_to_manager()` now syncs:
   - `generate_log_file`
   - `file_log_level`
   - `log_viewer_level`

2. **Dynamic Logger Level Control** - `_on_log_level_change()` (lines 1085-1101) sets source logger levels when dropdown changes:
   ```python
   logging.getLogger("core.extractor").setLevel(level)
   logging.getLogger("core.geometry").setLevel(level)
   logging.getLogger("__main__").setLevel(level)
   ```

3. **Settings Persistence** - Log file and level settings are saved to disk

### Still Missing

1. **Numeric Amount Sync** - Filter amounts not synced:
   - `precision_fix_amount`
   - `gap_bridge_amount`
   - `min_area_filter_amount`
   - `min_side_filter_amount`
   - `unit_override`

2. **Post-Close Refresh** - Main window doesn't refresh `log_level_var` after Advanced Settings closes (if user changes `log_viewer_level` there)

## Implementation Steps

### Step 1: Expand `_sync_settings_to_manager()` with Numeric Amounts

**File:** `app/main.py`
**Location:** Lines 1117-1135

**Changes:** Add numeric filter amounts and unit override:

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
**Location:** Lines 790-797

**Changes:**

1. Modify `_open_advanced_settings()`:

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

---

### Step 3: Add `trace_add` Callbacks for Instant Sync

**File:** `app/main.py`
**Location:** In `__init__`, after filter variable creation (around line 114)

**Changes:** Add trace callbacks for numeric filter amounts:

```python
# In __init__, after creating all filter variables, add trace callbacks
# for instant sync of numeric amounts:

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
**Location:** Line 175-181

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
**Location:** Line 94

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

**Changes:** Replace the plain info label with a styled banner:

```python
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
```

---

### Step 8: Implement Real-Time Validation with `trace_add`

**File:** `app/core/settings_window.py`
**Location:** Lines 298-349 (in `_create_setting_row`, entry widget creation)

**Changes:** Replace FocusOut binding with trace_add:

```python
else:  # entry
    # ... existing validation setup code ...

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

    # Real-time validation using trace_add (replaces FocusOut binding)
    var.trace_add(
        "write",
        lambda *_, k=setting_key, w=entry: self._validate_entry(k, w),
    )

    self._entry_widgets[setting_key] = entry

    # ... rest of error label creation ...
```

---

### Step 9: Add Summary Tab with Copyable Plain-Text Settings

**File:** `app/core/settings_window.py`
**Location:** After logging tab creation

**Changes:**

1. Add tab in `_create_widgets()`:

```python
# Create tabs
self.tabview.add("Filters")
self.tabview.add("Performance")
self.tabview.add("Precision")
self.tabview.add("Output")
self.tabview.add("Logging")
self.tabview.add("Summary")  # ADD

# Populate tabs
self._create_filters_tab()
self._create_performance_tab()
self._create_precision_tab()
self._create_output_tab()
self._create_logging_tab()
self._create_summary_tab()  # ADD
```

2. Add new methods:

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
            display_key = key.replace("_", " ").title()
            summary_lines.append(f"  {display_key}: {display_value}")
        summary_lines.append("")

    self.summary_textbox.configure(state="normal")
    self.summary_textbox.delete("1.0", "end")
    self.summary_textbox.insert("1.0", "\n".join(summary_lines))
    self.summary_textbox.configure(state="disabled")

def _copy_summary(self) -> None:
    """Copy summary text to clipboard."""
    self.clipboard_clear()
    self.clipboard_append(self.summary_textbox.get("1.0", "end-1c"))

    # Visual feedback
    self.copy_btn.configure(text="Copied!")
    self.after(1500, lambda: self.copy_btn.configure(text="Copy to Clipboard"))
```

3. Update `_refresh_tab()` to handle Summary tab.

4. Update `_on_apply()` and `_on_save_as_default()` to call `_refresh_summary()` after changes.

---

## Testing Checklist

### Step 1-3: Settings Synchronization
- [ ] Change Gap Bridge amount in main GUI to 4, open Advanced Settings, verify Filters tab shows 4
- [ ] Change all filter amounts, verify they appear in Advanced Settings
- [ ] Enable/disable filters, verify state syncs to Advanced Settings
- [ ] Verify unit override syncs correctly

### Step 2: Post-Close Refresh
- [ ] Change `log_viewer_level` in Advanced Settings, verify main GUI dropdown updates after close
- [ ] Verify source loggers are updated to new level after refresh

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

### Step 9: Summary Tab
- [ ] Verify Summary tab appears after Logging tab
- [ ] Verify all settings display with proper formatting
- [ ] Verify "Copy to Clipboard" button copies text
- [ ] Verify "Copied!" feedback displays for 1.5 seconds
- [ ] Verify summary updates after Reset Section is clicked

## Recommendations

1. **Implement Steps 1-3 First** - These address the core sync bugs and should be done together
2. **Steps 4-6 Are Low-Risk UI Polish** - Can be done independently
3. **Step 7-8 Improve UX** - Should be done together for consistency
4. **Step 9 Is Self-Contained** - Can be implemented last as it's additive functionality

## Next Steps

1. Create a spec file from this plan for implementation
2. Implement Steps 1-3 as a single unit (sync functionality)
3. Implement Steps 4-6 as UI improvements
4. Implement Steps 7-9 as UX enhancements
