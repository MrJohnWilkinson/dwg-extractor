"""
DWG Block Extractor - GUI Application

A desktop application for extracting block insertion counts from DWG/DXF CAD files
and exporting them to formatted Excel files.

Usage:
    python main.py
    or
    uv run python app/main.py
"""

import logging
import os
import platform
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.extractor import extract_blocks
from core.excel_writer import write_excel
from core.logger import setup_logger
from core.constants import (
    SUPPORTED_EXTENSIONS,
    MSG_SELECT_FILE,
    MSG_PROCESSING,
    MSG_SUCCESS,
    MSG_ERROR_INVALID_FILE,
    MSG_ERROR_NO_BLOCKS,
    MSG_ERROR_FILE_NOT_FOUND
)

# Set CustomTkinter appearance
ctk.set_appearance_mode("system")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class DWGExtractorApp(ctk.CTk):
    """Main GUI application for DWG Block Extractor."""

    def __init__(self) -> None:
        super().__init__()

        # Initialize logger
        self.logger: logging.Logger = setup_logger(__name__)
        self.logger.info("DWG Block Extractor application started")

        # Window configuration
        self.title("DWG Block Extractor")
        self.geometry("500x300")
        self.resizable(False, False)

        # Instance variables
        self.selected_file_path: str | None = None

        # Create UI
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Main container with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title label
        title_label = ctk.CTkLabel(
            main_frame,
            text="DWG Block Extractor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # File path entry
        self.file_entry = ctk.CTkEntry(
            main_frame,
            width=360,
            placeholder_text=MSG_SELECT_FILE,
            state="readonly"
        )
        self.file_entry.pack(pady=(0, 15))

        # Button frame for horizontal layout
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 15))

        # Browse button
        self.browse_button = ctk.CTkButton(
            button_frame,
            text="Browse",
            width=120,
            command=self._browse_file
        )
        self.browse_button.pack(side="left", padx=(0, 10))

        # Extract button (initially disabled)
        self.extract_button = ctk.CTkButton(
            button_frame,
            text="Extract",
            width=120,
            command=self._extract_blocks,
            state="disabled"
        )
        self.extract_button.pack(side="left")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            width=400,
            height=20
        )
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack()

    def _browse_file(self) -> None:
        """Handle browse button click - open file dialog."""
        self.logger.info("User clicked Browse button")

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select DWG or DXF File",
            filetypes=[
                ("DWG/DXF Files", "*.dwg *.dxf"),
                ("All Files", "*.*")
            ]
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

        # Disable buttons during processing
        self.browse_button.configure(state="disabled")
        self.extract_button.configure(state="disabled")

        # Reset progress
        self.progress_bar.set(0)
        self.status_label.configure(text=MSG_PROCESSING)

        self.logger.info(f"Starting extraction for {self.selected_file_path}")

        # Start extraction in background thread
        thread = threading.Thread(target=self._extraction_worker, daemon=True)
        thread.start()

    def _extraction_worker(self) -> None:
        """Background worker thread for extraction process."""
        try:
            # Step 1: Load file
            self._update_progress(0.2, "Loading file...")

            # Validate file path exists
            if not self.selected_file_path:
                self._show_error("No file selected")
                return

            block_counts = extract_blocks(self.selected_file_path)

            # Step 2: Count blocks
            self._update_progress(0.5, "Counting blocks...")

            # Check for empty results
            if not block_counts:
                self.logger.warning(f"No blocks found in {self.selected_file_path}")
                self._show_error(MSG_ERROR_NO_BLOCKS)
                return

            # Step 3: Generate Excel
            self._update_progress(0.7, "Generating Excel...")

            excel_path = write_excel(block_counts, self.selected_file_path)

            # Step 4: Complete
            self._update_progress(1.0, MSG_SUCCESS)

            # Show success and open file
            self._show_success(excel_path)

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
            # Re-enable buttons
            self.after(0, lambda: self.browse_button.configure(state="normal"))
            self.after(0, lambda: self.extract_button.configure(state="normal"))

    def _update_progress(self, value: float, message: str) -> None:
        """Update progress bar and status message (thread-safe)."""
        self.after(0, lambda: self._update_progress_ui(value, message))

    def _update_progress_ui(self, value: float, message: str) -> None:
        """Actually update the progress UI (must run on main thread)."""
        self.progress_bar.set(value)
        self.status_label.configure(text=message)
        self.logger.info(f"Progress: {int(value*100)}% - {message}")

    def _show_success(self, excel_path: str) -> None:
        """Show success message and open Excel file (thread-safe)."""
        self.after(0, lambda: self._show_success_ui(excel_path))

    def _show_success_ui(self, excel_path: str) -> None:
        """Actually show success dialog (must run on main thread)."""
        self.logger.info(f"Extraction completed successfully, Excel file: {excel_path}")

        messagebox.showinfo(
            "Success",
            f"Extraction complete!\n\nExcel file created:\n{Path(excel_path).name}"
        )

        # Auto-open Excel file
        self._open_excel_file(excel_path)

    def _show_error(self, message: str) -> None:
        """Show error message dialog (thread-safe)."""
        self.after(0, lambda: self._show_error_ui(message))

    def _show_error_ui(self, message: str) -> None:
        """Actually show error dialog (must run on main thread)."""
        self.logger.error(f"Error shown to user: {message}")

        messagebox.showerror(
            "Error",
            message
        )

    def _open_excel_file(self, file_path: str) -> None:
        """Open Excel file with platform-specific command."""
        try:
            self.logger.info(f"Opening Excel file: {file_path}")

            system = platform.system()

            if system == "Windows":
                os.startfile(file_path)  # type: ignore[attr-defined]
            elif system == "Linux":
                subprocess.run(['xdg-open', file_path], check=False)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', file_path], check=False)
            else:
                self.logger.warning(f"Unknown platform: {system}, cannot auto-open file")

        except Exception as e:
            # Don't show error to user - file was created successfully
            self.logger.warning(f"Failed to open Excel file: {str(e)}")

    def destroy(self) -> None:
        """Override destroy to log application close."""
        self.logger.info("Application closed")
        super().destroy()


def main() -> None:
    """Main entry point for the application."""
    app = DWGExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
