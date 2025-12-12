"""
DXF Block Extractor - GUI Application

A desktop application for extracting block insertion counts from DXF CAD files
and exporting them to formatted Excel files.

Usage:
    python main.py
    or
    uv run python app/main.py
"""

import logging
import os
import platform
import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    MSG_ABORTED,
    MSG_ABORTING,
    MSG_ERROR_FILE_NOT_FOUND,
    MSG_ERROR_INVALID_FILE,
    MSG_ERROR_NO_BLOCKS,
    MSG_PROCESSING,
    MSG_SELECT_FILE,
    MSG_SUCCESS,
    UNIT_SELECTION_OPTIONS,
)
from core.excel_writer import write_excel
from core.extractor import ExtractionAbortedError, extract_blocks
from core.geometry import GeometryAbortedError
from core.logger import create_debug_file_handler, create_queue_handler, setup_logger
from core.settings import SettingsManager
from core.settings_window import AdvancedSettingsWindow


# Set CustomTkinter appearance
ctk.set_appearance_mode("system")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class DXFExtractorApp(ctk.CTk):
    """Main GUI application for DXF Block Extractor."""

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

        # Window configuration
        self.title("DXF Block Extractor")
        self.geometry("600x750")
        self.resizable(True, True)

        # Instance variables
        self.selected_file_path: str | None = None
        self.output_excel_path: str | None = None
        self.debug_file_handler: logging.FileHandler | None = None
        self.abort_event: threading.Event | None = None

        # Log viewer queue and handler
        self.log_queue: queue.Queue[tuple[int, str]] = queue.Queue(maxsize=1000)
        self.queue_handler = create_queue_handler(self.log_queue)
        logging.getLogger().addHandler(self.queue_handler)

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
        self.log_file_var = ctk.BooleanVar(value=self.settings.get("generate_log_file"))
        self.file_log_level_var = ctk.StringVar(
            value=self.settings.get("file_log_level")
        )

        # Create UI
        self._create_widgets()

        # Start log queue polling
        self._poll_log_queue()

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title label
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="DXF Block Extractor",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.pack(pady=(0, 20))

        # File path entry
        self.file_entry = ctk.CTkEntry(
            self.main_frame,
            width=360,
            placeholder_text=MSG_SELECT_FILE,
            state="readonly",
        )
        self.file_entry.pack(pady=(0, 15))

        # Button frame for horizontal layout
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 15))

        # Browse button
        self.browse_button = ctk.CTkButton(
            button_frame, text="Browse", width=120, command=self._browse_file
        )
        self.browse_button.pack(side="left", padx=(0, 10))

        # Extract button (initially disabled)
        self.extract_button = ctk.CTkButton(
            button_frame,
            text="Extract",
            width=120,
            command=self._extract_blocks,
            state="disabled",
        )
        self.extract_button.pack(side="left")

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
            button_frame,
            text="Abort",
            width=120,
            command=self._abort_extraction,
            fg_color="red",
            hover_color="darkred",
        )
        # Don't pack - will be shown during extraction

        # Units row frame
        units_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        units_frame.pack(pady=(0, 10))

        # Unit selection label
        unit_label = ctk.CTkLabel(
            units_frame,
            text="Units:",
            font=ctk.CTkFont(size=12),
        )
        unit_label.pack(side="left", padx=(0, 5))

        # Unit selection dropdown
        self.unit_dropdown = ctk.CTkOptionMenu(
            units_frame,
            values=list(UNIT_SELECTION_OPTIONS.keys()),
            variable=self.unit_selection_var,
            width=100,
            command=self._on_unit_change,
        )
        self.unit_dropdown.pack(side="left", padx=(0, 10))

        # Units hint label
        units_hint = ctk.CTkLabel(
            units_frame,
            text="(applies to all numeric filters)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        units_hint.pack(side="left")

        # First separator
        separator1 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator1.pack(fill="x", pady=5)

        # Precision Fix row frame
        precision_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        precision_frame.pack(pady=(5, 10))

        # Precision fix checkbox
        self.precision_fix_checkbox = ctk.CTkCheckBox(
            precision_frame,
            text="Precision Fix",
            variable=self.precision_fix_var,
            command=self._on_precision_fix_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.precision_fix_checkbox.pack(side="left", padx=(0, 10))

        # Precision fix amount label
        precision_amount_label = ctk.CTkLabel(
            precision_frame,
            text="Amount:",
            font=ctk.CTkFont(size=12),
        )
        precision_amount_label.pack(side="left", padx=(0, 5))

        # Precision fix amount entry (starts enabled since precision_fix_var defaults to True)
        self.precision_fix_entry = ctk.CTkEntry(
            precision_frame,
            width=80,
            textvariable=self.precision_fix_amount_var,
        )
        self.precision_fix_entry.pack(side="left")

        # Second separator
        separator2 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator2.pack(fill="x", pady=5)

        # Gap Bridge row frame
        gap_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        gap_frame.pack(pady=(5, 10))

        # Gap bridge checkbox
        self.gap_bridge_checkbox = ctk.CTkCheckBox(
            gap_frame,
            text="Gap Bridge",
            variable=self.gap_bridge_var,
            command=self._on_gap_bridge_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.gap_bridge_checkbox.pack(side="left", padx=(0, 10))

        # Gap bridge amount label
        gap_amount_label = ctk.CTkLabel(
            gap_frame,
            text="Amount:",
            font=ctk.CTkFont(size=12),
        )
        gap_amount_label.pack(side="left", padx=(0, 5))

        # Gap bridge amount entry
        self.gap_bridge_entry = ctk.CTkEntry(
            gap_frame,
            width=80,
            textvariable=self.gap_bridge_amount_var,
            state="disabled",
        )
        self.gap_bridge_entry.pack(side="left")

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

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400, height=20)
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame, text="", font=ctk.CTkFont(size=12)
        )
        self.status_label.pack()

        # Log viewer panel
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.pack(fill="both", expand=True, pady=10)

        # Log level selector
        self.log_level_var = ctk.StringVar(value="INFO")
        self.log_level_menu = ctk.CTkOptionMenu(
            self.log_frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            variable=self.log_level_var,
            command=self._on_log_level_change,
        )
        self.log_level_menu.pack(anchor="w", padx=5, pady=5)

        # Log file options row
        log_file_options_frame = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_file_options_frame.pack(anchor="w", padx=5, pady=(0, 5))

        # Log file generation checkbox
        self.log_file_checkbox = ctk.CTkCheckBox(
            log_file_options_frame,
            text="Generate Log File",
            variable=self.log_file_var,
            font=ctk.CTkFont(size=12),
            command=self._on_log_file_toggle,
        )
        self.log_file_checkbox.pack(side="left", padx=(0, 10))

        # File log level label
        file_level_label = ctk.CTkLabel(
            log_file_options_frame,
            text="Level:",
            font=ctk.CTkFont(size=12),
        )
        file_level_label.pack(side="left", padx=(0, 5))

        # File log level dropdown (disabled by default)
        self.file_log_level_menu = ctk.CTkOptionMenu(
            log_file_options_frame,
            values=["DEBUG", "INFO", "WARNING"],
            variable=self.file_log_level_var,
            width=90,
            state="disabled",
        )
        self.file_log_level_menu.pack(side="left")

        # Log text area
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            font=("Courier", 10),
            state="disabled",
            height=200,
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

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

    def _browse_file(self) -> None:
        """Handle browse button click - open file dialog."""
        self.logger.info("User clicked Browse button")

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select DXF File",
            filetypes=[("DXF Files", "*.dxf"), ("All Files", "*.*")],
        )

        if file_path:
            # Store selected file path
            self.selected_file_path = file_path
            self.logger.info(f"File selected: {self.selected_file_path}")

            # Update UI
            self.file_entry.configure(state="normal")
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.file_entry.configure(state="readonly")

            # Enable extract button
            self.extract_button.configure(state="normal")
        else:
            self.logger.info("File selection cancelled")

    def _extract_blocks(self) -> None:
        """Handle extract button click - start extraction process."""
        # Validate file selected
        if not self.selected_file_path:
            self._show_error("Please select a file first")
            return

        # Prepare UI for extraction (swap buttons, create abort event)
        self._start_extraction()

        # Reset progress
        self.progress_bar.set(0)
        self.status_label.configure(text=MSG_PROCESSING)

        self.logger.info(f"Starting extraction for {self.selected_file_path}")

        # Start extraction in background thread
        thread = threading.Thread(target=self._extraction_worker, daemon=True)
        thread.start()

    def _start_extraction(self) -> None:
        """Prepare UI for extraction - show abort button, create event."""
        self.abort_event = threading.Event()
        self.browse_button.pack_forget()
        self.extract_button.pack_forget()
        self.open_folder_button.pack_forget()
        self.settings_button.pack_forget()  # Hide settings button during extraction
        self.abort_button.pack(side="left", padx=10)

    def _abort_extraction(self) -> None:
        """Handle abort button click - signal extraction to stop."""
        if self.abort_event:
            self.abort_event.set()
        self.abort_button.configure(state="disabled")
        self.status_label.configure(text=MSG_ABORTING)
        self.logger.info("User requested extraction abort")

    def _restore_ui(self) -> None:
        """Restore UI to normal state after extraction completes or aborts."""
        self.abort_button.pack_forget()
        self.abort_button.configure(state="normal")  # Reset state for next use
        self.browse_button.pack(side="left", padx=(0, 10))
        self.extract_button.pack(side="left")
        self.open_folder_button.pack(side="left", padx=(10, 0))
        self.settings_button.pack(side="left", padx=(10, 0))  # Restore settings button
        self.abort_event = None

    def _extraction_worker(self) -> None:
        """Background worker thread for extraction process."""
        try:
            # Validate file path exists
            if not self.selected_file_path:
                self._show_error("No file selected")
                return

            input_path = Path(self.selected_file_path)

            # Conditionally set up debug file logging
            if self.log_file_var.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"{input_path.stem}_debug_{timestamp}.log"
                log_path = input_path.parent / log_filename

                self.debug_file_handler = create_debug_file_handler(str(log_path))

                # Apply user-selected log level to file handler
                file_level = getattr(logging, self.file_log_level_var.get())
                self.debug_file_handler.setLevel(file_level)

                logging.getLogger().addHandler(self.debug_file_handler)

                self.logger.info(
                    f"Debug log ({self.file_log_level_var.get()}): {log_path}"
                )
                self._update_progress(0.1, f"Logging to: {log_filename}")
            else:
                self._update_progress(0.1, "Starting extraction...")

            # Get user settings
            unit_override = self._get_selected_unit_override()
            gap_bridge_enabled = self.gap_bridge_var.get()
            gap_bridge_amount = self._get_gap_bridge_amount()
            precision_fix_enabled = self.precision_fix_var.get()
            precision_fix_amount = self._get_precision_fix_amount()

            # Get filter settings
            min_area_filter_enabled = self.min_area_filter_var.get()
            min_area_filter_amount = self._get_min_area_filter_amount()
            min_side_filter_enabled = self.min_side_filter_var.get()
            min_side_filter_amount = self._get_min_side_filter_amount()

            # Get threshold settings from SettingsManager
            polygon_threshold = self.settings.get("polygon_count_threshold")
            line_threshold = self.settings.get("line_segment_threshold")
            entity_threshold = self.settings.get("entity_count_threshold")

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
            self.logger.debug(
                f"Threshold settings: polygon={polygon_threshold}, "
                f"line={line_threshold}, entity={entity_threshold}"
            )

            # Step 1: Load file
            self._update_progress(0.2, "Loading file...")

            # Step 2: Extract comprehensive data
            self._update_progress(0.5, "Analyzing CAD file...")

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
                polygon_count_threshold=polygon_threshold,
                line_segment_threshold=line_threshold,
                entity_count_threshold=entity_threshold,
            )

            # Check for empty results
            if not extraction_result["block_counts"]:
                self.logger.warning(f"No blocks found in {self.selected_file_path}")
                self._show_error(MSG_ERROR_NO_BLOCKS)
                return

            # Step 3: Generate Excel
            self._update_progress(0.7, "Generating Excel...")

            # Get custom output path based on settings
            custom_output_path = self._get_output_path(input_path)

            excel_path = write_excel(
                extraction_result, self.selected_file_path, custom_output_path
            )
            self.output_excel_path = excel_path

            # Step 4: Complete
            self._update_progress(1.0, MSG_SUCCESS)

            # Show success and optionally open file (based on settings)
            self._show_success(excel_path)

        except ExtractionAbortedError:
            self.logger.info("Extraction aborted by user")
            self._update_progress(0, MSG_ABORTED)

        except GeometryAbortedError:
            self.logger.info("Extraction aborted during geometry processing")
            self._update_progress(0, MSG_ABORTED)

        except FileNotFoundError as e:
            self.logger.error(f"File not found: {str(e)}", exc_info=True)
            self._show_error(MSG_ERROR_FILE_NOT_FOUND)

        except ValueError as e:
            self.logger.error(f"Invalid file: {str(e)}", exc_info=True)
            self._show_error(MSG_ERROR_INVALID_FILE)

        except Exception as e:
            self.logger.error(f"Extraction failed: {str(e)}", exc_info=True)
            self._show_error(f"Extraction failed: {str(e)}")

        finally:
            # Clean up debug file handler
            if self.debug_file_handler:
                logging.getLogger().removeHandler(self.debug_file_handler)
                self.debug_file_handler.close()
                self.debug_file_handler = None

            # Restore UI to normal state
            self.after(0, self._restore_ui)

    def _update_progress(self, value: float, message: str) -> None:
        """Update progress bar and status message (thread-safe)."""
        self.after(0, lambda: self._update_progress_ui(value, message))

    def _update_progress_ui(self, value: float, message: str) -> None:
        """Actually update the progress UI (must run on main thread)."""
        self.progress_bar.set(value)
        self.status_label.configure(text=message)
        self.logger.info(f"Progress: {int(value * 100)}% - {message}")

    def _show_success(self, excel_path: str) -> None:
        """Show success message and open Excel file (thread-safe)."""
        self.after(0, lambda: self._show_success_ui(excel_path))

    def _show_success_ui(self, excel_path: str) -> None:
        """Actually show success dialog (must run on main thread)."""
        self.logger.info(f"Extraction completed successfully, Excel file: {excel_path}")

        # Show success dialog if enabled in settings
        if self.settings.get("show_success_dialog"):
            messagebox.showinfo(
                "Success",
                f"Extraction complete!\n\nExcel file created:\n{Path(excel_path).name}",
            )

        # Enable Open Folder button
        self.open_folder_button.configure(state="normal")

        # Auto-open Excel file if enabled in settings
        if self.settings.get("auto_open_excel"):
            self._open_excel_file(excel_path)

    def _show_error(self, message: str) -> None:
        """Show error message dialog (thread-safe)."""
        self.after(0, lambda: self._show_error_ui(message))

    def _show_error_ui(self, message: str) -> None:
        """Actually show error dialog (must run on main thread)."""
        self.logger.error(f"Error shown to user: {message}")

        messagebox.showerror("Error", message)

    def _open_excel_file(self, file_path: str) -> None:
        """Open Excel file with platform-specific command."""
        try:
            self.logger.info(f"Opening Excel file: {file_path}")

            system = platform.system()

            if system == "Windows":
                os.startfile(file_path)  # type: ignore[attr-defined]
            elif system == "Linux":
                subprocess.run(["xdg-open", file_path], check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path], check=False)
            else:
                self.logger.warning(
                    f"Unknown platform: {system}, cannot auto-open file"
                )

        except Exception as e:
            # Don't show error to user - file was created successfully
            self.logger.warning(f"Failed to open Excel file: {str(e)}")

    def _open_output_folder(self) -> None:
        """Open folder containing the Excel file with platform-specific command."""
        # Validate we have an output path
        if not self.output_excel_path:
            self.logger.warning("Cannot open folder - no output path stored")
            return

        try:
            self.logger.info(f"Opening folder for: {self.output_excel_path}")

            system = platform.system()
            file_path = self.output_excel_path

            if system == "Windows":
                # Open Explorer with file selected
                subprocess.run(["explorer", "/select,", file_path], check=False)
            elif system == "Linux":
                # Open default file manager to folder
                folder_path = str(Path(file_path).parent)
                subprocess.run(["xdg-open", folder_path], check=False)
            elif system == "Darwin":  # macOS
                # Open Finder with file selected
                subprocess.run(["open", "-R", file_path], check=False)
            else:
                self.logger.warning(f"Unknown platform: {system}, cannot open folder")

        except Exception as e:
            # Don't show error to user - this is a convenience feature
            self.logger.warning(f"Failed to open output folder: {str(e)}")

    def _open_advanced_settings(self) -> None:
        """Open the Advanced Settings window."""
        self.logger.info("Opening Advanced Settings window")
        window = AdvancedSettingsWindow(self, self.settings)
        self.wait_window(window)  # Block until window closes

        # Refresh main window if needed (settings may have changed)
        self.logger.debug("Advanced Settings window closed")

    def _poll_log_queue(self) -> None:
        """Poll log queue and update text widget."""
        level_filter = getattr(logging, self.log_level_var.get())

        while True:
            try:
                level, msg = self.log_queue.get_nowait()
                if level >= level_filter:
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", msg + "\n")
                    self.log_text.see("end")  # Auto-scroll
                    self.log_text.configure(state="disabled")
            except queue.Empty:
                break

        self.after(100, self._poll_log_queue)

    def _on_unit_change(self, value: str) -> None:
        """Handle unit dropdown selection change.

        Updates ALL filter defaults when units change, regardless of checkbox state.
        This ensures users see appropriate values for their selected unit system
        whether or not a filter is currently enabled.
        """
        self.logger.debug(f"Unit selection changed to: {value}")
        # Always update all defaults when unit changes (regardless of checkbox state)
        self._update_precision_fix_default()
        self._update_gap_bridge_default()
        self._update_min_area_filter_default()
        self._update_min_side_filter_default()

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

    def _update_precision_fix_default(self) -> None:
        """Update precision fix amount to default for selected unit."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        effective_units = insunits if insunits != -1 else 4  # Default to mm
        default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
        self.precision_fix_amount_var.set(str(default_amount))
        self.logger.debug(f"Precision fix default updated to {default_amount}")

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

    def _update_gap_bridge_default(self) -> None:
        """Update gap bridge amount to default for selected unit."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        # Use detected units fallback if auto
        effective_units = insunits if insunits != -1 else 4  # Default to mm
        default_amount = DEFAULT_GAP_CLOSURE_TOLERANCE.get(effective_units, 3.0)
        self.gap_bridge_amount_var.set(str(default_amount))
        self.logger.debug(f"Gap bridge default updated to {default_amount}")

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

    def _update_min_area_filter_default(self) -> None:
        """Update min area filter amount to default for selected unit."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        effective_units = insunits if insunits != -1 else 4  # Default to mm
        default_amount = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)
        self.min_area_filter_amount_var.set(str(default_amount))
        self.logger.debug(f"Min area filter default updated to {default_amount}")

    def _update_min_side_filter_default(self) -> None:
        """Update min side filter amount to default for selected unit."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        effective_units = insunits if insunits != -1 else 4  # Default to mm
        default_amount = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)
        self.min_side_filter_amount_var.set(str(default_amount))
        self.logger.debug(f"Min side filter default updated to {default_amount}")

    def _get_selected_unit_override(self) -> int | None:
        """Get the $INSUNITS value for selected unit, or None for auto."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        return None if insunits == -1 else insunits

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
                self.logger.warning(
                    f"Precision fix amount validation failed: {error_msg}"
                )
                return None
        except ValueError:
            self.logger.warning("Invalid precision fix amount")
            return None

    def _get_min_area_filter_amount(self) -> float | None:
        """Get validated min area filter amount, or None if invalid/disabled."""
        if not self.min_area_filter_var.get():
            return None
        try:
            amount = float(self.min_area_filter_amount_var.get())
            is_valid, error_msg = self.settings.validate(
                "min_area_filter_amount", amount
            )
            if is_valid:
                return amount
            else:
                self.logger.warning(
                    f"Min area filter amount validation failed: {error_msg}"
                )
                return None
        except ValueError:
            self.logger.warning("Invalid min area filter amount")
            return None

    def _get_min_side_filter_amount(self) -> float | None:
        """Get validated min side filter amount, or None if invalid/disabled."""
        if not self.min_side_filter_var.get():
            return None
        try:
            amount = float(self.min_side_filter_amount_var.get())
            is_valid, error_msg = self.settings.validate(
                "min_side_filter_amount", amount
            )
            if is_valid:
                return amount
            else:
                self.logger.warning(
                    f"Min side filter amount validation failed: {error_msg}"
                )
                return None
        except ValueError:
            self.logger.warning("Invalid min side filter amount")
            return None

    def _format_filename(self, input_path: Path) -> str:
        """Format output filename with optional prefix and timestamp.

        Args:
            input_path: Path to the input DXF file

        Returns:
            Formatted filename (without directory) for the output Excel file
        """
        base_name = input_path.stem

        # Get settings
        prefix = self.settings.get("filename_prefix") or ""
        include_timestamp = self.settings.get("include_timestamp")

        # Build filename parts
        parts = []

        if prefix:
            parts.append(prefix)

        parts.append(base_name)

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parts.append(timestamp)

        # Join with underscore and add extension
        filename = "_".join(parts) + ".xlsx"

        self.logger.debug(f"Formatted filename: {filename}")
        return filename

    def _get_output_path(self, input_path: Path) -> Path:
        """Get output file path respecting output directory setting.

        Args:
            input_path: Path to the input DXF file

        Returns:
            Full path for the output Excel file
        """
        filename = self._format_filename(input_path)

        # Check for custom output directory
        custom_dir = self.settings.get("output_directory")

        if custom_dir:
            output_dir = Path(custom_dir)
            # Verify directory exists or can be created
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created output directory: {output_dir}")
                except OSError as e:
                    self.logger.warning(
                        f"Cannot create output directory {output_dir}: {e}. "
                        "Using input file directory."
                    )
                    output_dir = input_path.parent
        else:
            # Default: same directory as input file
            output_dir = input_path.parent

        output_path = output_dir / filename
        self.logger.debug(f"Output path: {output_path}")
        return output_path

    def _on_log_level_change(self, value: str) -> None:
        """Handle log level dropdown change.

        Sets source logger levels dynamically so DEBUG messages
        are captured when DEBUG is selected.
        """
        level = getattr(logging, value)

        # Set source logger levels to enable/disable DEBUG capture
        logging.getLogger("app.core.extractor").setLevel(level)
        logging.getLogger("app.core.geometry").setLevel(level)
        logging.getLogger("app.main").setLevel(level)

    def _on_log_file_toggle(self) -> None:
        """Handle log file checkbox toggle - enable/disable level dropdown."""
        if self.log_file_var.get():
            self.file_log_level_menu.configure(state="normal")
        else:
            self.file_log_level_menu.configure(state="disabled")

        # Sync settings to manager and save
        self._sync_settings_to_manager()

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

    def destroy(self) -> None:
        """Override destroy to clean up queue handler and log application close."""
        logging.getLogger().removeHandler(self.queue_handler)
        self.logger.info("Application closed")
        super().destroy()


def main() -> None:
    """Main entry point for the application."""
    app = DXFExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
