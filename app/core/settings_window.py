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
    SETTINGS_VALIDATION_REGISTRY,
)
from .types import SettingValidation


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

        # Track checkbox variables for collecting settings
        self._checkbox_vars: dict[str, ctk.BooleanVar] = {}

        # Track dropdown variables for collecting settings
        self._dropdown_vars: dict[str, ctk.StringVar] = {}

        # Configure window
        self.title("Advanced Settings")
        self.geometry("650x600")
        self.resizable(True, True)
        self.minsize(650, 600)  # Prevent window from being too small

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
            text="Save All as Default",
            width=140,
            command=self._on_save_as_default,
        )
        self.save_default_button.pack(side="left")

        # Right side - Cancel and Apply
        self.apply_button = ctk.CTkButton(
            button_frame,
            text="Apply All Changes",
            width=130,
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
            self._checkbox_vars[setting_key] = var

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
            self._dropdown_vars[setting_key] = var

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

        elif readonly:
            # Read-only display
            display_text = (
                str(current_value) if current_value is not None else "Not set"
            )
            widget = ctk.CTkLabel(
                control_frame,
                text=display_text,
                font=ctk.CTkFont(size=12),
                anchor="e",
            )
            widget.pack()

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

            # Real-time validation using trace_add (replaces FocusOut binding)
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
        validation: SettingValidation = SETTINGS_VALIDATION_REGISTRY.get(
            key,
            {
                "min_value": None,
                "max_value": None,
                "default": None,
                "unit_aware": False,
            },
        )
        default_val = validation.get("default")

        try:
            if isinstance(default_val, bool):
                value: Any = value_str.lower() in ("true", "1", "yes")
            elif isinstance(default_val, int) or (
                validation.get("min_value") is not None
                and isinstance(validation.get("min_value"), int)
            ):
                value = int(float(value_str))  # Handle "100.0" -> 100
            elif (
                isinstance(default_val, float)
                or validation.get("min_value") is not None
            ):
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

    def _create_performance_tab(self) -> None:
        """Create the Performance tab content."""
        tab = self.tabview.tab("Performance")
        self._populate_performance_tab(tab)

    def _populate_performance_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Performance tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(
            scroll_frame, "Performance Thresholds", "performance"
        )

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

            validation: SettingValidation = SETTINGS_VALIDATION_REGISTRY.get(
                key,
                {
                    "min_value": None,
                    "max_value": None,
                    "default": None,
                    "unit_aware": False,
                },
            )
            default_val = validation.get("default")

            try:
                if isinstance(default_val, int) or (
                    validation.get("min_value") is not None
                    and isinstance(validation.get("min_value"), int)
                ):
                    settings[key] = int(float(value_str))
                elif (
                    isinstance(default_val, float)
                    or validation.get("min_value") is not None
                ):
                    settings[key] = float(value_str)
                else:
                    settings[key] = value_str
            except ValueError:
                settings[key] = None

        # Collect from checkbox widgets
        for key, var in self._checkbox_vars.items():
            settings[key] = var.get()

        # Collect from dropdown widgets
        for key, var in self._dropdown_vars.items():
            settings[key] = var.get()

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
            self.after(
                1500,
                lambda: self.save_default_button.configure(text="Save All as Default"),
            )
        else:
            logger.error("Failed to save settings")
