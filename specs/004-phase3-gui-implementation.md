# Feature: Phase 3 - GUI Implementation

## Feature Description
Implement the desktop graphical user interface (GUI) for the DWG Block Extractor application using CustomTkinter. This feature creates a modern, user-friendly single-window interface that allows users to browse for DWG/DXF files, extract block counts, view real-time progress updates, and automatically open the generated Excel reports. The GUI integrates with the existing core extraction and Excel generation logic implemented in Phase 2, providing a complete end-to-end user experience with logging support for monitoring by LLM agents.

## User Story
As a CAD technician or engineer
I want to use a simple desktop application with a graphical interface
So that I can extract block counts from DWG/DXF files and generate Excel reports with just 2 clicks (Browse and Extract), without needing to use command-line tools or write code.

## Problem Statement
The DWG Block Extractor currently has working core logic for extraction and Excel generation (Phase 2), but no user interface. Users cannot interact with the application without writing Python code to call the core functions directly. This creates a barrier to adoption for non-technical users who need a simple, visual way to process CAD files. The application needs a desktop GUI that provides:
- File selection through a standard file picker dialog
- Visual feedback during processing (progress bar and status messages)
- Automatic opening of generated Excel files
- Clear error messages for invalid files or processing failures
- Integration with the existing stdout logging system for monitoring

## Solution Statement
Create a single-window desktop application using CustomTkinter (a modern tkinter wrapper) that provides an intuitive 2-click workflow: Browse → Extract. The GUI will feature a clean layout with a file path display, browse/extract buttons, a progress bar, and status messages. The implementation will use threading to prevent UI freezing during extraction, integrate with the existing logging infrastructure for real-time monitoring, and automatically open Excel files upon successful completion. The interface will handle all error cases gracefully with user-friendly dialog boxes while logging detailed error information to stdout for debugging.

## Relevant Files
Use these files to implement the feature:

### Existing Files
- **`app/core/extractor.py`** - Core extraction logic that the GUI will call. Contains `extract_blocks()` function that takes a file path and returns block count dictionary. Already has logging and error handling.

- **`app/core/excel_writer.py`** - Excel generation logic that the GUI will call. Contains `write_excel()` function that takes block data and output path, returns path to created Excel file. Already has logging.

- **`app/core/constants.py`** - Application constants including UI messages (`MSG_SELECT_FILE`, `MSG_PROCESSING`, `MSG_SUCCESS`, `MSG_ERROR_INVALID_FILE`, `MSG_ERROR_NO_BLOCKS`, `MSG_ERROR_FILE_NOT_FOUND`) and supported file extensions (`SUPPORTED_EXTENSIONS`). GUI will use these constants for consistent messaging.

- **`app/core/logger.py`** - Logging configuration that outputs to stdout. GUI will use `setup_logger()` to create a logger instance for tracking all user actions and errors.

- **`app/pyproject.toml`** - Project dependencies including `customtkinter>=5.2.0` already configured. No changes needed.

### New Files
- **`app/main.py`** - Main GUI application entry point. Will contain `DWGExtractorApp` class (CustomTkinter window), UI layout with all widgets (file path entry, browse/extract buttons, progress bar, status label), event handlers for user interactions, threading logic for async extraction, and platform-specific code to auto-open Excel files.

## Implementation Plan
### Phase 1: Foundation
Before implementing the GUI, verify that all Phase 2 components are working correctly:
- Confirm `app/core/extractor.py` exists and `extract_blocks()` function works
- Confirm `app/core/excel_writer.py` exists and `write_excel()` function works
- Confirm `app/core/constants.py` contains all required UI message constants
- Confirm `app/core/logger.py` provides stdout logging
- Verify CustomTkinter is installed via `uv sync` in the app directory
- Review the test fixtures in `app/app/tests/assets/` to identify sample files for manual testing

### Phase 2: Core Implementation
Create the main GUI application with all required components:
- Set up the main `DWGExtractorApp` class inheriting from `ctk.CTk`
- Design the window layout (500x300px) with proper padding and spacing
- Create all UI widgets: file path entry, browse button, extract button, progress bar, status label
- Implement the browse button handler to open file picker dialog with DWG/DXF filters
- Implement the extract button handler with validation, threading, and error handling
- Add helper methods for updating progress, showing errors, and showing success messages
- Implement platform-specific code to auto-open Excel files on Windows and Linux
- Integrate logging throughout all user interactions and processing steps

### Phase 3: Integration
Integrate the GUI with existing core logic and ensure smooth end-to-end operation:
- Connect the extract button to call `extract_blocks()` from `app/core/extractor.py`
- Connect the Excel generation to call `write_excel()` from `app/core/excel_writer.py`
- Ensure all error handling from core modules is properly caught and displayed to users
- Verify that logging from both GUI and core modules appears in stdout for monitoring
- Test the complete workflow: browse file → extract → generate Excel → auto-open
- Handle edge cases: invalid files, empty drawings, cancelled file selection, missing permissions

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Phase 2 Dependencies
- Run `uv sync --directory app` to ensure all dependencies including CustomTkinter are installed
- Verify that `app/core/extractor.py`, `app/core/excel_writer.py`, `app/core/constants.py`, and `app/core/logger.py` exist
- Check that test assets exist in `app/app/tests/assets/` for manual GUI testing
- Confirm Python version is 3.8+ by running `python --version`

### Step 2: Create Main GUI Application File
- Create `app/main.py` as the GUI entry point
- Import required modules: `customtkinter as ctk`, `tkinter.filedialog`, `threading`, `os`, `subprocess`, `platform`
- Import core modules: `from core.extractor import extract_blocks`, `from core.excel_writer import write_excel`, `from core.logger import setup_logger`
- Import constants: `from core.constants import SUPPORTED_EXTENSIONS, MSG_SELECT_FILE, MSG_PROCESSING, MSG_SUCCESS, MSG_ERROR_INVALID_FILE, MSG_ERROR_NO_BLOCKS, MSG_ERROR_FILE_NOT_FOUND`
- Set CustomTkinter appearance mode and color theme at module level

### Step 3: Implement DWGExtractorApp Class Structure
- Create `DWGExtractorApp` class inheriting from `ctk.CTk`
- Initialize logger in `__init__`: `self.logger = setup_logger(__name__)`
- Log application startup: `self.logger.info("DWG Block Extractor application started")`
- Set window properties: title "DWG Block Extractor", size 500x300px, not resizable
- Initialize instance variables: `self.selected_file_path = None`
- Call `self._create_widgets()` to build UI

### Step 4: Create UI Widgets and Layout
- Implement `_create_widgets()` method to create all UI components
- Create main container frame with 20px padding
- Add title label at top: "DWG Block Extractor" in large font
- Create file path entry widget (CTkEntry, width=360px, read-only state, placeholder text from `MSG_SELECT_FILE`)
- Create button frame to hold browse and extract buttons horizontally
- Add Browse button (CTkButton, width=120px, command=`self._browse_file`)
- Add Extract button (CTkButton, width=120px, command=`self._extract_blocks`, initially disabled)
- Create progress bar (CTkProgressBar, width=400px, height=20px, initially set to 0)
- Add status label (CTkLabel, for displaying current operation status)
- Use grid or pack layout manager to arrange widgets vertically with proper spacing

### Step 5: Implement Browse File Handler
- Create `_browse_file()` method to handle browse button click
- Log user action: `self.logger.info("User clicked Browse button")`
- Open file dialog using `tkinter.filedialog.askopenfilename()`
- Set dialog title to "Select DWG or DXF File"
- Set file type filters: `[("DWG/DXF Files", "*.dwg *.dxf"), ("All Files", "*.*")]`
- If user selects a file, store path in `self.selected_file_path`
- Update file path entry widget to display selected file path
- Enable the Extract button
- Log selected file: `self.logger.info(f"File selected: {self.selected_file_path}")`
- If user cancels, log cancellation: `self.logger.info("File selection cancelled")`

### Step 6: Implement Extract Button Handler with Threading
- Create `_extract_blocks()` method to handle extract button click
- Validate that a file has been selected (`self.selected_file_path` is not None)
- If no file selected, show error dialog and return
- Disable both browse and extract buttons during processing
- Reset progress bar to 0
- Update status label to display `MSG_PROCESSING`
- Log extraction start: `self.logger.info(f"Starting extraction for {self.selected_file_path}")`
- Create and start a new thread: `threading.Thread(target=self._extraction_worker, daemon=True).start()`
- The thread will run the extraction logic without blocking the UI

### Step 7: Implement Extraction Worker Thread
- Create `_extraction_worker()` method to run in background thread
- Wrap entire method in try-except block for error handling
- Call `self._update_progress(0.2, "Loading file...")` to update UI (using `self.after()` for thread safety)
- Call `block_counts = extract_blocks(self.selected_file_path)` from core module
- Call `self._update_progress(0.5, "Counting blocks...")`
- Check if `block_counts` is empty, if so show warning with `MSG_ERROR_NO_BLOCKS`
- Call `self._update_progress(0.7, "Generating Excel...")`
- Call `excel_path = write_excel(block_counts, self.selected_file_path)` from core module
- Call `self._update_progress(1.0, MSG_SUCCESS)`
- Call `self._show_success(excel_path)` to display success message and open Excel
- In except block, catch `FileNotFoundError` and show `MSG_ERROR_FILE_NOT_FOUND`
- Catch `ValueError` (for invalid/corrupted files) and show `MSG_ERROR_INVALID_FILE`
- Catch general `Exception` and show detailed error message
- Log all errors with full traceback: `self.logger.error(f"Extraction failed: {str(e)}", exc_info=True)`
- In finally block, re-enable browse and extract buttons using `self.after()`

### Step 8: Implement UI Update Helper Methods
- Create `_update_progress(value: float, message: str)` method to update progress bar and status
- Use `self.after()` to schedule UI updates on main thread: `self.after(0, lambda: self._update_progress_ui(value, message))`
- Create `_update_progress_ui(value, message)` method that actually updates widgets
- Set progress bar value (0.0 to 1.0)
- Update status label text
- Log progress: `self.logger.info(f"Progress: {int(value*100)}% - {message}")`

### Step 9: Implement Success and Error Dialogs
- Create `_show_success(excel_path: str)` method for successful extraction
- Use `self.after()` to schedule on main thread
- Create actual implementation `_show_success_ui(excel_path)`
- Show CTkMessagebox or tkinter.messagebox with success message including file path
- Log success: `self.logger.info(f"Extraction completed successfully, Excel file: {excel_path}")`
- Call `self._open_excel_file(excel_path)` to auto-open the file
- Create `_show_error(message: str)` method for displaying error dialogs
- Use `self.after()` to schedule on main thread
- Show CTkMessagebox or tkinter.messagebox with error message
- Log error: `self.logger.error(f"Error shown to user: {message}")`

### Step 10: Implement Auto-Open Excel Functionality
- Create `_open_excel_file(file_path: str)` method for platform-specific file opening
- Use `platform.system()` to detect operating system
- For Windows: use `os.startfile(file_path)`
- For Linux: use `subprocess.run(['xdg-open', file_path], check=False)`
- For macOS: use `subprocess.run(['open', file_path], check=False)`
- Wrap in try-except to catch permission or application errors
- Log file opening: `self.logger.info(f"Opening Excel file: {file_path}")`
- If opening fails, log warning but don't show error (file still created successfully)

### Step 11: Add Main Entry Point
- At bottom of `app/main.py`, add standard Python entry point check: `if __name__ == "__main__":`
- Create and run application: `app = DWGExtractorApp()` then `app.mainloop()`
- Log application exit when window closes: `self.logger.info("Application closed")`

### Step 12: Manual Testing with Sample Files
- Run `uv run python main.py` to launch the GUI
- Test browse functionality: click Browse and select a test file from `app/app/tests/assets/`
- Test successful extraction: select a valid DWG/DXF file and click Extract
- Verify progress bar updates during processing
- Confirm Excel file opens automatically
- Verify stdout shows all logging messages from GUI and core modules
- Test error cases: select invalid file, cancel file dialog, select empty drawing
- Verify error dialogs display correctly with user-friendly messages
- Check that buttons are properly disabled/enabled during processing

### Step 13: Run Validation Commands
- Execute all validation commands listed below to ensure feature works with zero regressions
- Verify all unit tests still pass (core logic unchanged)
- Test GUI manually with multiple file types and edge cases
- Confirm logging output appears correctly in stdout for monitoring

## Testing Strategy
### Unit Tests
No new unit tests required for GUI (CustomTkinter GUI testing is complex and provides limited value). Core logic is already fully tested in Phase 2. Manual testing is more effective for GUI validation.

Focus manual testing on:
- UI layout and appearance (correct window size, widget alignment, spacing)
- Widget states (buttons enable/disable correctly, progress bar updates)
- Thread safety (UI doesn't freeze, multiple clicks handled gracefully)

### Integration Tests
Manual integration testing to verify GUI correctly calls core modules:
- Browse and select file → `selected_file_path` variable updates
- Extract button → calls `extract_blocks()` with correct file path
- Block counts returned → calls `write_excel()` with correct data and output path
- Excel file created → `_open_excel_file()` called with returned path
- Errors from core → caught and displayed in GUI error dialogs

### Edge Cases
Test the following edge cases manually:
- **No file selected**: Click Extract without browsing → error dialog appears
- **Cancel file dialog**: Click Browse then Cancel → no error, UI unchanged
- **Invalid file**: Select non-DWG/DXF file or corrupted file → error dialog with `MSG_ERROR_INVALID_FILE`
- **Empty drawing**: Select DXF file with no blocks → warning dialog with `MSG_ERROR_NO_BLOCKS`, but Excel still created
- **Missing file**: Select file then delete it before extracting → error dialog with `MSG_ERROR_FILE_NOT_FOUND`
- **Large file**: Test with DWG containing 1000+ blocks → progress bar updates smoothly, UI remains responsive
- **Rapid clicks**: Click Extract multiple times quickly → only one extraction runs (button disabled during processing)
- **Platform differences**: Test on both Windows and Linux if available → Excel opens correctly on both platforms

### Playwright MCP Tests
Not applicable for this phase. The application is a desktop GUI (not web-based), so Playwright end-to-end tests cannot be used. Manual testing is the appropriate approach for desktop applications.

## Acceptance Criteria
- [ ] Main window displays correctly at 500x300px with title "DWG Block Extractor"
- [ ] All widgets are present and properly laid out: file path entry, browse button, extract button, progress bar, status label
- [ ] Browse button opens file picker dialog with DWG/DXF file filters
- [ ] Selected file path displays in read-only entry field
- [ ] Extract button is initially disabled, becomes enabled after file selection
- [ ] Extract button triggers extraction process when clicked
- [ ] Progress bar updates during extraction showing 20%, 50%, 70%, 100%
- [ ] Status label displays appropriate messages: "Processing...", "Loading file...", "Counting blocks...", "Generating Excel...", "Extraction complete"
- [ ] Excel file is automatically opened upon successful extraction (Windows and Linux)
- [ ] Error dialogs display for invalid files with user-friendly messages
- [ ] Buttons are disabled during processing to prevent multiple simultaneous extractions
- [ ] All user actions and errors are logged to stdout for monitoring
- [ ] UI remains responsive during extraction (no freezing due to proper threading)
- [ ] Application can be closed gracefully without errors
- [ ] Complete workflow (Browse → Select → Extract) takes 2 clicks as specified

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv sync --directory app` - Ensure all dependencies including CustomTkinter are installed
- `uv run python --version` - Verify Python 3.8+ is being used
- `uv run pytest` - Run all existing unit tests to ensure zero regressions in core logic
- `uv run pytest --cov=app/core --cov-report=term-missing` - Verify core module test coverage remains >80%
- `test -f app/main.py && echo "main.py exists" || echo "main.py missing"` - Confirm GUI file was created
- `wc -l app/main.py` - Verify implementation is approximately 120-200 lines as estimated
- `uv run python main.py` - Launch GUI application (manual testing required)

**Manual Validation Steps** (execute while GUI is running):
1. Click Browse button → file dialog opens with DWG/DXF filters
2. Select a test file from `app/app/tests/assets/` → file path displays in entry field, Extract button enables
3. Click Extract button → progress bar updates, status messages appear, Excel file opens automatically
4. Verify stdout contains all logging messages from GUI and core modules
5. Close application → no errors, clean exit
6. Re-launch and test error case: select invalid file → error dialog appears with appropriate message
7. Re-launch and test edge case: click Extract without selecting file → error dialog appears

## Notes

### Design Decisions
1. **CustomTkinter vs tkinter**: Using CustomTkinter provides a modern look without additional complexity. The API is nearly identical to tkinter, making it easy to learn and maintain.

2. **Threading approach**: Using `threading.Thread` instead of `asyncio` for simplicity. The extraction process is I/O bound (file reading) and CPU bound (parsing), making threads appropriate. UI updates are scheduled on the main thread using `after()` for thread safety.

3. **No GUI unit tests**: CustomTkinter/tkinter GUI testing requires complex mocking and provides limited value. Manual testing is more effective and reliable for verifying UI behavior. Core logic remains fully unit tested.

4. **Stdout logging only**: All logging goes to stdout (no log files) for real-time monitoring by LLM agents during development and ADW workflows. This aligns with the project's design philosophy.

5. **Platform-specific file opening**: Different commands for Windows (`os.startfile`), Linux (`xdg-open`), and macOS (`open`). Failures in opening don't affect extraction success, so they only log warnings.

6. **Read-only file path entry**: The file path field is read-only to prevent users from manually typing invalid paths. File selection is only through the Browse button dialog.

7. **Button state management**: Browse and Extract buttons are disabled during processing to prevent race conditions and multiple simultaneous extractions that could corrupt the UI state.

### Future Enhancements
- Add drag-and-drop support for file selection (drop DWG/DXF directly onto window)
- Add batch processing mode (select multiple files, process all sequentially)
- Add progress percentage text overlay on progress bar
- Add "Recent files" menu for quick re-processing
- Add settings dialog for customizing Excel output format
- Add application icon for the window and taskbar
- Support dark/light theme switching via menu

### Dependencies
All required dependencies are already in `app/pyproject.toml`:
- `customtkinter>=5.2.0` - Modern GUI framework
- `ezdxf>=1.0.0` - CAD file parsing (used by core)
- `pandas>=2.0.0` - Data manipulation (used by core)
- `openpyxl>=3.1.0` - Excel generation (used by core)

No additional dependencies are needed for Phase 3.
