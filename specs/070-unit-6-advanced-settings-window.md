# Feature: Advanced Settings Window Modal (Unit 6 - Phase C2)

## Feature Description

This specification covers the implementation of the Advanced Settings Window modal (`app/core/settings_window.py`), which provides a comprehensive tabbed interface for configuring all 24 application settings. The window is phase C2 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md).

The Advanced Settings Window:
- Opens as a modal dialog blocking the main window
- Uses `CTkTabview` with 5 tabs: Filters, Performance, Precision, Output, Logging
- Displays each setting with label, control, description, and valid range
- Provides per-section Reset buttons to restore section defaults
- Implements Apply, Cancel, and Save as Default buttons
- Shows real-time validation feedback with red borders on invalid entries
- Integrates with the existing `_open_advanced_settings()` placeholder in main.py

**Scope:** C2 only (Advanced Settings Window)

**Out of Scope (handled in later units):**
- D1: Pipeline integration for new threshold parameters
- D2: Output directory customization, filename preview features

**Prerequisites:**
- Unit 1-2 (A1-A6) completed: Parallel processing removed
- Unit 3 (B1-B2) completed: AppSettings TypedDict (24 fields), SETTINGS_VALIDATION_REGISTRY
- Unit 4 (B3-B4) completed: SettingsManager class with persistence
- Unit 5 (C1) completed: Main GUI migration with Settings button
- Tests: 919 passing

## User Story

As a DXF Block Extractor user
I want to access and configure advanced application settings through a dedicated window
So that I can fine-tune extraction parameters, performance thresholds, and output options without cluttering the main interface

## Problem Statement

The main GUI currently only exposes a subset of settings (filters and logging). Users cannot access:

1. **Performance thresholds** - polygon_count_threshold, line_segment_threshold, entity_count_threshold
2. **Precision settings** - arc_flattening_sagitta, coord_dedup_epsilon, rotation_tolerance
3. **Output settings** - output_directory, auto_open_excel, show_success_dialog, filename_prefix, include_timestamp
4. **Advanced logging** - log_viewer_level, log_viewer_auto_scroll, log_viewer_max_lines

Additionally, the existing filter settings in the main window lack:
- Descriptions explaining what each setting does
- Visible valid ranges for numeric inputs
- Reset-to-default functionality

## Solution Statement

Create a new `AdvancedSettingsWindow` class (`app/core/settings_window.py`) that:

1. **Extends `ctk.CTkToplevel`** - Creates a modal window that blocks the main window
2. **Uses `CTkTabview` for organization** - 5 tabs group related settings logically
3. **Standardized setting rows** - Each setting displays label, control, description, and valid range
4. **Real-time validation** - Invalid entries show red borders with error messages
5. **Per-section Reset buttons** - Allow users to reset individual sections to defaults
6. **Three action buttons**:
   - **Apply** - Validates all settings, applies changes, and closes window
   - **Cancel** - Discards all changes and closes window
   - **Save as Default** - Persists current settings to JSON file
7. **Integrates with main.py** - Updates `_open_advanced_settings()` to open this window

## Relevant Files

Use these files to implement the feature:

- `app/core/settings.py` - SettingsManager class for get/set/validate/reset operations
  - Import and use for all settings operations
  - Use `SETTINGS_SECTIONS` dict for section groupings

- `app/core/constants.py` - Contains validation ranges and default values
  - `SETTINGS_VALIDATION_REGISTRY` - Validation metadata for all settings
  - All `*_MIN`, `*_MAX`, `DEFAULT_*` constants

- `app/core/types.py` - Type definitions
  - `AppSettings` TypedDict for type hints
  - `SettingValidation` TypedDict

- `app/main.py` - Main GUI application
  - Update `_open_advanced_settings()` to create and show the window
  - Pass `self` and `self.settings` to AdvancedSettingsWindow

- `app/tests/core/test_settings.py` - Existing SettingsManager tests (reference)

### New Files

- `app/core/settings_window.py` - New file containing `AdvancedSettingsWindow` class

## Implementation Plan

### Phase 1: Foundation

Create the base `AdvancedSettingsWindow` class with modal behavior:

1. Create `app/core/settings_window.py` with class skeleton
2. Implement modal window behavior (grab_set, transient, focus)
3. Create main layout structure with CTkTabview and button frame
4. Define helper methods for creating standardized setting rows

### Phase 2: Core Implementation

Build out the 5 tabs with all settings controls:

1. **Filters Tab** - Read-only display of main window filter settings with descriptions
2. **Performance Tab** - Three threshold settings with spinboxes/entries
3. **Precision Tab** - Three precision settings with entries
4. **Output Tab** - Directory chooser, checkboxes, and text entry
5. **Logging Tab** - Log viewer settings with dropdowns and entries

Implement validation and feedback:
- Real-time validation on entry changes
- Red border for invalid values
- Error message display near invalid fields

### Phase 3: Integration

Connect all functionality:

1. Wire Reset buttons to `SettingsManager.reset_section()`
2. Implement Apply button logic (validate all, apply, close)
3. Implement Cancel button logic (discard changes, close)
4. Implement Save as Default button (save to JSON)
5. Update `main.py` `_open_advanced_settings()` to open window
6. Handle window close events properly

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create settings_window.py File with Class Skeleton

Create `app/core/settings_window.py`:

```python
"""
Advanced Settings Window for the DXF Block Extractor.

This module provides the AdvancedSettingsWindow class, a modal dialog
for configuring all application settings organized in tabbed sections.

Usage:
    from core.settings_window import AdvancedSettingsWindow

    # In main.py
    def _open_advanced_settings(self) -> None:
        window = AdvancedSettingsWindow(self, self.settings)
        self.wait_window(window)  # Block until closed
"""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from .constants import (
    ARC_FLATTENING_SAGITTA_MAX,
    ARC_FLATTENING_SAGITTA_MIN,
    COORD_DEDUP_EPSILON_MAX,
    COORD_DEDUP_EPSILON_MIN,
    DEFAULT_ARC_FLATTENING_SAGITTA,
    DEFAULT_AUTO_OPEN_EXCEL,
    DEFAULT_COORD_DEDUP_EPSILON,
    DEFAULT_ENTITY_COUNT_THRESHOLD,
    DEFAULT_FILENAME_PREFIX,
    DEFAULT_INCLUDE_TIMESTAMP,
    DEFAULT_LINE_SEGMENT_THRESHOLD,
    DEFAULT_LOG_VIEWER_AUTO_SCROLL,
    DEFAULT_LOG_VIEWER_LEVEL,
    DEFAULT_LOG_VIEWER_MAX_LINES,
    DEFAULT_POLYGON_COUNT_THRESHOLD,
    DEFAULT_ROTATION_TOLERANCE,
    DEFAULT_SHOW_SUCCESS_DIALOG,
    ENTITY_COUNT_THRESHOLD_MAX,
    ENTITY_COUNT_THRESHOLD_MIN,
    LINE_SEGMENT_THRESHOLD_MAX,
    LINE_SEGMENT_THRESHOLD_MIN,
    LOG_VIEWER_MAX_LINES_MAX,
    LOG_VIEWER_MAX_LINES_MIN,
    POLYGON_COUNT_THRESHOLD_MAX,
    POLYGON_COUNT_THRESHOLD_MIN,
    ROTATION_TOLERANCE_MAX,
    ROTATION_TOLERANCE_MIN,
    SETTINGS_VALIDATION_REGISTRY,
)


if TYPE_CHECKING:
    from .settings import SettingsManager


logger = logging.getLogger(__name__)


class AdvancedSettingsWindow(ctk.CTkToplevel):
    """Modal window for advanced settings configuration.

    Provides a tabbed interface for configuring all 24 application settings:
    - Filters: Read-only display of main window filter settings
    - Performance: Early-exit thresholds for content zone detection
    - Precision: Numeric precision for geometry operations
    - Output: File output and Excel behavior settings
    - Logging: Log viewer configuration

    Attributes:
        parent: Parent window (DXFExtractorApp instance)
        settings: SettingsManager instance for get/set operations
    """

    def __init__(self, parent: ctk.CTk, settings: "SettingsManager") -> None:
        """Initialize the Advanced Settings window.

        Args:
            parent: Parent window (main application)
            settings: SettingsManager instance for settings operations
        """
        super().__init__(parent)

        self.parent = parent
        self.settings = settings

        # Store original settings for cancel operation
        self._original_settings = settings.to_dict()

        # Track entry widgets for validation feedback
        self._entry_widgets: dict[str, ctk.CTkEntry] = {}
        self._error_labels: dict[str, ctk.CTkLabel] = {}

        # Configure window
        self.title("Advanced Settings")
        self.geometry("650x600")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self._center_on_parent()

        # Create UI
        self._create_widgets()

        # Focus this window
        self.focus_set()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        logger.info("Advanced Settings window opened")

    def _center_on_parent(self) -> None:
        """Center the window on the parent window."""
        self.update_idletasks()

        # Get parent geometry
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get this window's size
        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab view
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)

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

        # Button frame at bottom
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        # Left side - Save as Default
        self.save_default_button = ctk.CTkButton(
            button_frame,
            text="Save as Default",
            width=120,
            command=self._on_save_as_default,
        )
        self.save_default_button.pack(side="left")

        # Right side - Cancel and Apply
        self.apply_button = ctk.CTkButton(
            button_frame,
            text="Apply",
            width=100,
            command=self._on_apply,
        )
        self.apply_button.pack(side="right")

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self._on_cancel,
        )
        self.cancel_button.pack(side="right", padx=(0, 10))
```

### Step 2: Add Helper Methods for Creating Setting Rows

Add these helper methods to the `AdvancedSettingsWindow` class:

```python
    def _create_setting_row(
        self,
        parent: ctk.CTkFrame,
        setting_key: str,
        label_text: str,
        description: str,
        widget_type: str = "entry",
        options: list[str] | None = None,
        readonly: bool = False,
    ) -> ctk.CTkFrame:
        """Create a standardized setting row with label, control, and description.

        Args:
            parent: Parent frame for the setting row
            setting_key: Key in SETTINGS_VALIDATION_REGISTRY
            label_text: Display label for the setting
            description: Help text describing the setting
            widget_type: Type of control ("entry", "checkbox", "dropdown", "directory")
            options: List of options for dropdown widget_type
            readonly: If True, display as read-only label instead of entry

        Returns:
            The frame containing the setting row
        """
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", pady=5)

        # Left column - Label and description
        label_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        label_frame.pack(side="left", fill="x", expand=True)

        label = ctk.CTkLabel(
            label_frame,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        label.pack(anchor="w")

        desc_label = ctk.CTkLabel(
            label_frame,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
            wraplength=350,
        )
        desc_label.pack(anchor="w")

        # Right column - Control widget
        control_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        control_frame.pack(side="right", padx=(10, 0))

        current_value = self.settings.get(setting_key)

        if widget_type == "checkbox":
            var = ctk.BooleanVar(value=bool(current_value))
            widget = ctk.CTkCheckBox(
                control_frame,
                text="",
                variable=var,
                command=lambda k=setting_key, v=var: self._on_checkbox_change(k, v),
            )
            widget.pack()
            widget.var = var  # Store reference for later access

        elif widget_type == "dropdown":
            var = ctk.StringVar(value=str(current_value) if current_value else "")
            widget = ctk.CTkOptionMenu(
                control_frame,
                values=options or [],
                variable=var,
                width=100,
                command=lambda val, k=setting_key: self._on_dropdown_change(k, val),
            )
            widget.pack()
            widget.var = var

        elif widget_type == "directory":
            dir_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
            dir_frame.pack()

            var = ctk.StringVar(value=str(current_value) if current_value else "")
            entry = ctk.CTkEntry(dir_frame, width=150, textvariable=var)
            entry.pack(side="left")

            browse_btn = ctk.CTkButton(
                dir_frame,
                text="...",
                width=30,
                command=lambda v=var: self._browse_directory(v),
            )
            browse_btn.pack(side="left", padx=(5, 0))

            entry.var = var
            self._entry_widgets[setting_key] = entry
            widget = entry

        elif readonly:
            # Read-only display
            display_text = str(current_value) if current_value is not None else "Not set"
            widget = ctk.CTkLabel(
                control_frame,
                text=display_text,
                font=ctk.CTkFont(size=12),
                anchor="e",
            )
            widget.pack()

        else:  # entry
            validation = SETTINGS_VALIDATION_REGISTRY.get(setting_key, {})
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

            var = ctk.StringVar(value=str(current_value) if current_value is not None else "")
            entry = ctk.CTkEntry(
                control_frame,
                width=100,
                textvariable=var,
            )
            entry.pack()
            entry.var = var

            # Bind validation on focus out
            entry.bind("<FocusOut>", lambda e, k=setting_key, w=entry: self._validate_entry(k, w))

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

            widget = entry

        return row_frame

    def _create_section_header(
        self, parent: ctk.CTkFrame, title: str, section_key: str
    ) -> ctk.CTkFrame:
        """Create a section header with Reset button.

        Args:
            parent: Parent frame
            title: Section title text
            section_key: Key for reset_section() call

        Returns:
            The header frame
        """
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title_label.pack(side="left")

        reset_button = ctk.CTkButton(
            header_frame,
            text="Reset Section",
            width=100,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda: self._on_reset_section(section_key),
        )
        reset_button.pack(side="right")

        # Separator
        separator = ctk.CTkFrame(parent, height=1, fg_color="gray50")
        separator.pack(fill="x", pady=(0, 10))

        return header_frame

    def _browse_directory(self, var: ctk.StringVar) -> None:
        """Open directory chooser dialog."""
        current = var.get()
        initial_dir = current if current and Path(current).exists() else None

        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=initial_dir,
        )

        if directory:
            var.set(directory)
            logger.debug(f"Output directory selected: {directory}")
```

### Step 3: Add Validation and Event Handler Methods

Add these methods to handle validation and control changes:

```python
    def _validate_entry(self, key: str, entry: ctk.CTkEntry) -> bool:
        """Validate entry value and show feedback.

        Args:
            key: Setting key
            entry: Entry widget to validate

        Returns:
            True if valid, False otherwise
        """
        value_str = entry.var.get().strip()
        error_label = self._error_labels.get(key)

        # Empty string is valid for optional settings
        if not value_str:
            entry.configure(border_color=("gray50", "gray50"))
            if error_label:
                error_label.configure(text="")
            return True

        # Try to convert to appropriate type
        validation = SETTINGS_VALIDATION_REGISTRY.get(key, {})
        default_val = validation.get("default")

        try:
            if isinstance(default_val, bool):
                value = value_str.lower() in ("true", "1", "yes")
            elif isinstance(default_val, int) or (
                validation.get("min_value") is not None
                and isinstance(validation.get("min_value"), int)
            ):
                value = int(float(value_str))  # Handle "100.0" -> 100
            elif isinstance(default_val, float) or validation.get("min_value") is not None:
                value = float(value_str)
            else:
                value = value_str
        except ValueError:
            entry.configure(border_color="red")
            if error_label:
                error_label.configure(text="Invalid number")
            return False

        # Validate against constraints
        is_valid, error_msg = self.settings.validate(key, value)

        if is_valid:
            entry.configure(border_color=("gray50", "gray50"))
            if error_label:
                error_label.configure(text="")
            return True
        else:
            entry.configure(border_color="red")
            if error_label:
                # Shorten error message for display
                short_msg = error_msg.split(",")[0] if "," in error_msg else error_msg
                error_label.configure(text=short_msg)
            return False

    def _on_checkbox_change(self, key: str, var: ctk.BooleanVar) -> None:
        """Handle checkbox state change."""
        logger.debug(f"Checkbox {key} changed to {var.get()}")

    def _on_dropdown_change(self, key: str, value: str) -> None:
        """Handle dropdown selection change."""
        logger.debug(f"Dropdown {key} changed to {value}")

    def _on_reset_section(self, section: str) -> None:
        """Reset a section to defaults and update UI."""
        logger.info(f"Resetting section: {section}")
        self.settings.reset_section(section)

        # Refresh the UI for this section
        self._refresh_tab(section)

    def _refresh_tab(self, section: str) -> None:
        """Refresh all controls in a tab after reset.

        Args:
            section: Section name matching tab name (lowercase)
        """
        # Re-create the tab content
        tab_name = section.capitalize()

        # Get the tab frame
        tab_frame = self.tabview.tab(tab_name)

        # Clear existing widgets
        for widget in tab_frame.winfo_children():
            widget.destroy()

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

### Step 4: Create the Filters Tab

Add the Filters tab implementation (read-only display of main window settings):

```python
    def _create_filters_tab(self) -> None:
        """Create the Filters tab content."""
        tab = self.tabview.tab("Filters")
        self._populate_filters_tab(tab)

    def _populate_filters_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Filters tab with settings."""
        # Scrollable frame for content
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Filter Settings", "filters")

        # Info label - filters are controlled from main window
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="Note: Filter settings are controlled from the main window. "
                 "This tab shows current values for reference.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label.pack(anchor="w", pady=(0, 10))

        # Display current filter values (read-only)
        self._create_setting_row(
            scroll_frame,
            "precision_fix_enabled",
            "Precision Fix",
            "Closes small floating-point gaps in polygon edges. "
            "Recommended for most drawings.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "precision_fix_amount",
            "Precision Fix Amount",
            "Maximum gap size to close (in drawing units). "
            "Unit-aware: changes based on selected units.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "gap_bridge_enabled",
            "Gap Bridge",
            "Bridges larger intentional gaps using buffering. "
            "Mutually exclusive with Precision Fix.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "gap_bridge_amount",
            "Gap Bridge Amount",
            "Maximum gap size to bridge (in drawing units). "
            "Larger values close bigger gaps.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_area_filter_enabled",
            "Min Area Filter",
            "Filters out polygons smaller than the specified area. "
            "Useful for removing small artifacts.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_area_filter_amount",
            "Min Area Filter Amount",
            "Minimum polygon area in drawing units squared. "
            "Polygons below this are excluded.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_side_filter_enabled",
            "Min Side Filter",
            "Filters out polygons with shortest side below threshold. "
            "Helps remove thin artifacts.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_side_filter_amount",
            "Min Side Filter Amount",
            "Minimum side length in drawing units. "
            "Polygons with shorter sides are excluded.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "unit_override",
            "Unit Override",
            "Manual unit override for drawing interpretation. "
            "None means auto-detect from DXF file.",
            readonly=True,
        )
```

### Step 5: Create the Performance Tab

Add the Performance tab implementation:

```python
    def _create_performance_tab(self) -> None:
        """Create the Performance tab content."""
        tab = self.tabview.tab("Performance")
        self._populate_performance_tab(tab)

    def _populate_performance_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Performance tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Performance Thresholds", "performance")

        # Info label
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="These thresholds control early-exit behavior for content zone detection. "
                 "Lower values improve performance but may skip complex blocks.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label.pack(anchor="w", pady=(0, 10))

        self._create_setting_row(
            scroll_frame,
            "polygon_count_threshold",
            "Polygon Count Threshold",
            f"Maximum polygons for content zone calculation. "
            f"Blocks with more polygons skip content zone detection. "
            f"Default: {DEFAULT_POLYGON_COUNT_THRESHOLD}",
            widget_type="entry",
        )

        self._create_setting_row(
            scroll_frame,
            "line_segment_threshold",
            "Line Segment Threshold",
            f"Maximum LINE segments for cycle detection. "
            f"Blocks with more segments skip LINE cycle extraction. "
            f"Default: {DEFAULT_LINE_SEGMENT_THRESHOLD}",
            widget_type="entry",
        )

        self._create_setting_row(
            scroll_frame,
            "entity_count_threshold",
            "Entity Count Threshold",
            f"Maximum entities for content zone detection. "
            f"Blocks with more entities skip content zone entirely. "
            f"Default: {DEFAULT_ENTITY_COUNT_THRESHOLD}",
            widget_type="entry",
        )
```

### Step 6: Create the Precision Tab

Add the Precision tab implementation:

```python
    def _create_precision_tab(self) -> None:
        """Create the Precision tab content."""
        tab = self.tabview.tab("Precision")
        self._populate_precision_tab(tab)

    def _populate_precision_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Precision tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Precision Settings", "precision")

        # Info label
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="These settings control numeric precision for geometry operations. "
                 "Adjust with caution - incorrect values may affect extraction accuracy.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label.pack(anchor="w", pady=(0, 10))

        self._create_setting_row(
            scroll_frame,
            "arc_flattening_sagitta",
            "Arc Flattening Sagitta",
            f"Maximum distance from arc to chord for flattening. "
            f"Smaller values create more segments. "
            f"Default: {DEFAULT_ARC_FLATTENING_SAGITTA}",
            widget_type="entry",
        )

        self._create_setting_row(
            scroll_frame,
            "coord_dedup_epsilon",
            "Coordinate Dedup Epsilon",
            f"Tolerance for considering coordinates equal. "
            f"Used for deduplicating nearby points. "
            f"Default: {DEFAULT_COORD_DEDUP_EPSILON}",
            widget_type="entry",
        )

        self._create_setting_row(
            scroll_frame,
            "rotation_tolerance",
            "Rotation Tolerance",
            f"Tolerance in degrees for rotation categorization. "
            f"Angles within this range snap to standard rotations. "
            f"Default: {DEFAULT_ROTATION_TOLERANCE}",
            widget_type="entry",
        )
```

### Step 7: Create the Output Tab

Add the Output tab implementation:

```python
    def _create_output_tab(self) -> None:
        """Create the Output tab content."""
        tab = self.tabview.tab("Output")
        self._populate_output_tab(tab)

    def _populate_output_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Output tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Output Settings", "output")

        # Info label
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="Configure how and where output files are generated.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label.pack(anchor="w", pady=(0, 10))

        self._create_setting_row(
            scroll_frame,
            "output_directory",
            "Output Directory",
            "Custom directory for Excel output files. "
            "Leave empty to save alongside input file.",
            widget_type="directory",
        )

        self._create_setting_row(
            scroll_frame,
            "auto_open_excel",
            "Auto-Open Excel",
            f"Automatically open the Excel file after extraction. "
            f"Default: {DEFAULT_AUTO_OPEN_EXCEL}",
            widget_type="checkbox",
        )

        self._create_setting_row(
            scroll_frame,
            "show_success_dialog",
            "Show Success Dialog",
            f"Display success message dialog after extraction. "
            f"Default: {DEFAULT_SHOW_SUCCESS_DIALOG}",
            widget_type="checkbox",
        )

        self._create_setting_row(
            scroll_frame,
            "filename_prefix",
            "Filename Prefix",
            f"Prefix to add to output filenames. "
            f"Default: '{DEFAULT_FILENAME_PREFIX}' (none)",
            widget_type="entry",
        )

        self._create_setting_row(
            scroll_frame,
            "include_timestamp",
            "Include Timestamp",
            f"Add timestamp to output filenames for uniqueness. "
            f"Default: {DEFAULT_INCLUDE_TIMESTAMP}",
            widget_type="checkbox",
        )
```

### Step 8: Create the Logging Tab

Add the Logging tab implementation:

```python
    def _create_logging_tab(self) -> None:
        """Create the Logging tab content."""
        tab = self.tabview.tab("Logging")
        self._populate_logging_tab(tab)

    def _populate_logging_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Logging tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Logging Settings", "logging")

        # Info label
        info_label = ctk.CTkLabel(
            scroll_frame,
            text="Configure log viewer behavior and file logging options.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label.pack(anchor="w", pady=(0, 10))

        # Note: generate_log_file and file_log_level are in main window
        info_label2 = ctk.CTkLabel(
            scroll_frame,
            text="Note: File logging toggle and level are controlled from the main window.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=550,
        )
        info_label2.pack(anchor="w", pady=(0, 10))

        self._create_setting_row(
            scroll_frame,
            "log_viewer_level",
            "Log Viewer Level",
            f"Minimum log level to display in the log viewer panel. "
            f"Default: {DEFAULT_LOG_VIEWER_LEVEL}",
            widget_type="dropdown",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
        )

        self._create_setting_row(
            scroll_frame,
            "log_viewer_auto_scroll",
            "Auto-Scroll Log Viewer",
            f"Automatically scroll to show newest log messages. "
            f"Default: {DEFAULT_LOG_VIEWER_AUTO_SCROLL}",
            widget_type="checkbox",
        )

        self._create_setting_row(
            scroll_frame,
            "log_viewer_max_lines",
            "Max Log Lines",
            f"Maximum number of lines to keep in the log viewer. "
            f"Older lines are removed when exceeded. "
            f"Default: {DEFAULT_LOG_VIEWER_MAX_LINES}",
            widget_type="entry",
        )
```

### Step 9: Add Button Action Methods

Add the Apply, Cancel, and Save as Default button handlers:

```python
    def _validate_all_entries(self) -> bool:
        """Validate all entry widgets.

        Returns:
            True if all entries are valid, False otherwise
        """
        all_valid = True

        for key, entry in self._entry_widgets.items():
            if not self._validate_entry(key, entry):
                all_valid = False

        return all_valid

    def _collect_settings(self) -> dict[str, Any]:
        """Collect all current settings from UI controls.

        Returns:
            Dictionary of setting key -> value pairs
        """
        settings: dict[str, Any] = {}

        # Collect from entry widgets
        for key, entry in self._entry_widgets.items():
            value_str = entry.var.get().strip()

            if not value_str:
                settings[key] = None
                continue

            validation = SETTINGS_VALIDATION_REGISTRY.get(key, {})
            default_val = validation.get("default")

            try:
                if isinstance(default_val, int) or (
                    validation.get("min_value") is not None
                    and isinstance(validation.get("min_value"), int)
                ):
                    settings[key] = int(float(value_str))
                elif isinstance(default_val, float) or validation.get("min_value") is not None:
                    settings[key] = float(value_str)
                else:
                    settings[key] = value_str
            except ValueError:
                settings[key] = None

        return settings

    def _apply_settings(self) -> None:
        """Apply collected settings to the SettingsManager."""
        settings = self._collect_settings()

        for key, value in settings.items():
            if value is not None:
                self.settings.set(key, value)

    def _on_apply(self) -> None:
        """Handle Apply button click."""
        if not self._validate_all_entries():
            logger.warning("Cannot apply - validation errors exist")
            return

        self._apply_settings()
        logger.info("Settings applied")
        self.destroy()

    def _on_cancel(self) -> None:
        """Handle Cancel button click or window close."""
        # Restore original settings
        self.settings.from_dict(self._original_settings)
        logger.info("Settings changes cancelled")
        self.destroy()

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
            self.after(1500, lambda: self.save_default_button.configure(text="Save as Default"))
        else:
            logger.error("Failed to save settings")
```

### Step 10: Update main.py to Open the Window

Update `app/main.py` to import and use the AdvancedSettingsWindow:

**Add import at top of file:**
```python
from core.settings_window import AdvancedSettingsWindow
```

**Update the `_open_advanced_settings` method:**
```python
def _open_advanced_settings(self) -> None:
    """Open the Advanced Settings window."""
    self.logger.info("Opening Advanced Settings window")
    window = AdvancedSettingsWindow(self, self.settings)
    self.wait_window(window)  # Block until window closes

    # Refresh main window if needed (settings may have changed)
    self.logger.debug("Advanced Settings window closed")
```

### Step 11: Update app/core/__init__.py

Update `app/core/__init__.py` to include the new module:

```python
"""
Core module for DXF Block Extractor.

This module exports the main types and functions used throughout the application.
"""

from .types import BlockTrimmingData, ColorAnalysisRecord


__all__ = ["BlockTrimmingData", "ColorAnalysisRecord"]
```

Note: No changes needed - the settings_window module will be imported directly where needed.

### Step 12: Run Type Checking

Verify the changes pass type checking:

```bash
uv run mypy app/core/settings_window.py
uv run mypy app/main.py
uv run mypy app/
```

### Step 13: Run Linting and Formatting

Verify the changes pass linting:

```bash
uv run ruff check app/core/settings_window.py
uv run ruff format app/core/settings_window.py --check
uv run ruff check app/
uv run ruff format app/ --check
```

### Step 14: Run Full Test Suite

Run all tests to ensure no regressions:

```bash
uv run pytest app/tests/ -v
```

### Step 15: Manual Verification (Optional - Skip in WSL)

If running on a system with GUI support:

1. Launch application: `uv run python app/main.py`
2. Click "Settings" button - verify Advanced Settings window opens
3. Verify window is modal (cannot interact with main window)
4. Verify all 5 tabs are present and populated
5. Test validation:
   - Enter invalid number in threshold field
   - Verify red border appears
   - Verify error message shows
6. Test Reset Section:
   - Change a Performance value
   - Click Reset Section
   - Verify value returns to default
7. Test Cancel:
   - Change settings
   - Click Cancel
   - Re-open window, verify changes were discarded
8. Test Apply:
   - Change settings
   - Click Apply
   - Verify window closes
9. Test Save as Default:
   - Change settings
   - Click "Save as Default"
   - Verify "Saved!" confirmation appears
   - Restart application, verify settings persisted

## Testing Strategy

### Unit Tests

No new unit test file is required for this feature because:
- The `SettingsManager` class is already thoroughly tested (54 tests in `test_settings.py`)
- The `AdvancedSettingsWindow` is a GUI component that primarily orchestrates SettingsManager calls
- GUI tests are skipped in WSL per README.md guidance

### Integration Tests

- Manual verification of window opening from main.py
- Manual verification of settings persistence across window sessions

### Edge Cases

- Window opened when no settings file exists (first run)
- Window opened with corrupted settings (graceful fallback to defaults)
- Enter empty string in numeric field (should be treated as None/default)
- Enter non-numeric value in numeric field (should show validation error)
- Enter value outside valid range (should show validation error)
- Cancel after making changes (changes should be discarded)
- Save as Default with invalid values (should prevent save)
- Close window via X button (should behave like Cancel)
- Reset section while other sections have changes (should only reset that section)

### Playwright MCP Tests

- Skip GUI tests in WSL per README.md guidance
- E2E tests may be added in a future unit if GUI testing infrastructure is established

## Acceptance Criteria

- [ ] New file `app/core/settings_window.py` created with `AdvancedSettingsWindow` class
- [ ] Window opens as modal (blocks main window interaction)
- [ ] Window is centered on parent when opened
- [ ] All 5 tabs render correctly: Filters, Performance, Precision, Output, Logging
- [ ] Filters tab shows read-only display of main window settings with descriptions
- [ ] Performance tab has editable entries for 3 threshold settings
- [ ] Precision tab has editable entries for 3 precision settings
- [ ] Output tab has directory chooser, 3 checkboxes, and 1 text entry
- [ ] Logging tab has 1 dropdown, 1 checkbox, and 1 entry
- [ ] Each setting displays: label, control, description, and valid range (where applicable)
- [ ] Per-section Reset buttons restore section defaults
- [ ] Apply button validates all settings, applies changes, and closes window
- [ ] Cancel button closes window without applying changes
- [ ] Window X button behaves like Cancel
- [ ] Save as Default button validates, applies, and persists to JSON file
- [ ] Invalid entries show red border with validation error message
- [ ] Valid entries have normal border color
- [ ] `main.py` `_open_advanced_settings()` opens the AdvancedSettingsWindow
- [ ] mypy passes with no errors on new file
- [ ] ruff check passes with no errors
- [ ] ruff format passes with no changes needed
- [ ] All existing tests pass (919+ tests)

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/settings_window.py` - Type check the new settings window module
- `uv run mypy app/main.py` - Type check main.py for import and integration
- `uv run mypy app/` - Full type check to catch any cascading issues
- `uv run ruff check app/core/settings_window.py` - Lint the new module
- `uv run ruff format app/core/settings_window.py --check` - Check formatting
- `uv run ruff check app/` - Lint entire app directory
- `uv run ruff format app/ --check` - Check formatting for entire app
- `uv run pytest app/tests/core/test_settings.py -v` - Run SettingsManager tests (54 tests)
- `uv run pytest app/tests/ -v` - Run full test suite (should be 919+ tests, all passing)

## Notes

1. **Modal behavior** - Using `transient()` and `grab_set()` ensures the window blocks interaction with the main window until closed.

2. **Filters tab is read-only** - Per the combined plan, filter settings are controlled from the main window. The Filters tab provides a reference view with descriptions to help users understand each setting.

3. **Validation approach** - Real-time validation on focus-out provides immediate feedback without being intrusive. The red border is a standard UI pattern for indicating errors.

4. **Settings restoration on Cancel** - The original settings are captured at window creation and restored if the user cancels, ensuring no unintended changes.

5. **No new dependencies** - This feature uses only existing dependencies (customtkinter, tkinter.filedialog).

6. **Scrollable frames** - Each tab uses a scrollable frame to accommodate all settings without requiring a larger window.

7. **Section reset** - Reset buttons call `SettingsManager.reset_section()` and refresh the tab UI to show updated values.

8. **Window centering** - The window is centered on the parent window for a professional appearance.

9. **After this unit completes**:
   - Advanced Settings Window fully functional
   - All 24 settings accessible (Filters read-only, others editable)
   - Settings persist via JSON
   - Ready for D1 (Pipeline Integration) to wire threshold settings to extraction
