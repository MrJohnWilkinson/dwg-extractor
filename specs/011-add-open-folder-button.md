# Feature: Add "Open Folder" Button to GUI

## Feature Description
Add an "Open Folder" button to the GUI that opens the output directory containing the generated Excel file. This provides users with quick access to the output folder for file operations such as renaming, moving, or emailing the generated Excel reports without needing to manually navigate through the file system.

The button will be positioned to the right of the existing "Extract" button in the button frame, initially disabled, and enabled after the first successful extraction. Once enabled, it remains enabled to allow re-access to the folder without re-running extraction.

## User Story
As a DWG Block Extractor user
I want to quickly open the folder containing my generated Excel files
So that I can easily perform file operations (rename, move, email) without manually navigating through directories

## Problem Statement
Currently, after extracting block data and generating an Excel file, users must manually navigate to the output directory if they want to:
- Rename the file
- Move the file to another location
- Email the file as an attachment
- Access previous extraction results

This manual navigation interrupts the workflow and reduces user productivity, especially for users who frequently extract multiple files and need to organize or share the results.

## Solution Statement
Implement an "Open Folder" button that:
1. Opens the OS file manager (Explorer/Nautilus/Finder) to the directory containing the generated Excel file
2. Uses platform-specific commands to ensure cross-platform compatibility (Windows, Linux, macOS)
3. Remains disabled until the first successful extraction completes
4. Stays enabled after first use to allow quick re-access without re-extraction
5. Follows the existing UI patterns and code architecture in `app/main.py`

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application
  - Contains the `DWGExtractorApp` class with all UI logic
  - Line 86: `button_frame` where the new button will be added
  - Line 264-283: `_open_excel_file()` method - pattern to follow for platform-specific folder opening
  - Line 175-224: `_extraction_worker()` - where output path tracking will be added
  - Line 56-57: Instance variables - where `output_excel_path` will be declared

- **app/core/constants.py** - Application constants
  - Contains message constants used throughout the app
  - Will need new constants for button text and tooltips if applicable

- **app/tests/core/test_excel_writer.py** - Excel writer tests
  - To understand how Excel file paths are generated and returned
  - Provides insight into output path structure

### New Files
None - all changes are isolated to existing `app/main.py` and potentially `app/core/constants.py`

## Implementation Plan

### Phase 1: Foundation
1. Add instance variable to track the output Excel file path
2. Modify the extraction worker to capture and store the Excel output path
3. Add any necessary constants for the new button

### Phase 2: Core Implementation
1. Create the `_open_output_folder()` method using platform-specific commands
2. Add the "Open Folder" button widget to the button frame
3. Configure button state management (initially disabled)

### Phase 3: Integration
1. Enable the "Open Folder" button in the success handler after extraction completes
2. Ensure the button remains enabled for subsequent folder access
3. Add error handling for edge cases (folder deleted, permissions, etc.)

## Step by Step Tasks

### 1. Add output path tracking
- Add `self.output_excel_path: str | None = None` to instance variables in `__init__` method (after line 57)
- Modify `_extraction_worker` to store the Excel path from `write_excel()` return value (around line 200)

### 2. Add button text constant
- Add constant to `app/core/constants.py` if needed (e.g., `BTN_OPEN_FOLDER = "Open Folder"`)
- If no constant needed, use inline string "Open Folder"

### 3. Create folder opening method
- Add `_open_output_folder()` method after `_open_excel_file()` (around line 284)
- Implement platform-specific folder opening using `platform.system()`:
  - Windows: `subprocess.run(['explorer', '/select,', file_path])`
  - Linux: `subprocess.run(['xdg-open', folder_path])`
  - macOS: `subprocess.run(['open', '-R', file_path])`
- Use `Path(self.output_excel_path).parent` to get folder path
- Include error handling with logger warnings (don't show errors to user)
- Add validation check for `self.output_excel_path` existence

### 4. Add "Open Folder" button widget
- Create button in `_create_widgets()` method in the `button_frame` section (after line 106)
- Position to the right of Extract button using `pack(side="left", padx=(10, 0))`
- Set initial state to "disabled"
- Set width to 120 (consistent with Browse and Extract buttons)
- Assign to `self.open_folder_button` instance variable
- Set command to `self._open_output_folder`

### 5. Enable button after successful extraction
- In `_show_success_ui()` method (around line 249), enable the open folder button
- Add: `self.open_folder_button.configure(state="normal")`
- This should be called after the messagebox but before opening the Excel file

### 6. Write unit tests for folder opening logic
- Add test file: `app/tests/core/test_gui_helpers.py` (new file)
- Test `_open_output_folder()` with mocked platform checks
- Test edge cases: missing path, deleted folder, permission errors
- Mock `subprocess.run` and `platform.system` for cross-platform testing

### 7. Manual testing
- Test on Linux (WSL2) environment
- Verify button states: disabled initially, enabled after extraction
- Verify folder opens correctly with `xdg-open`
- Test re-clicking button without re-extraction

### 8. Run validation commands
- Execute all validation commands listed below to ensure zero regressions

## Testing Strategy

### Unit Tests
- **Test folder opening logic**: Mock `subprocess.run` and verify correct platform-specific commands
- **Test platform detection**: Mock `platform.system()` for Windows, Linux, macOS
- **Test path handling**: Verify correct folder path extraction from Excel file path
- **Test state validation**: Verify method checks for `self.output_excel_path` before proceeding

### Integration Tests
Skip GUI integration tests in WSL2 due to X server unreliability (per README.md line 75)

### Edge Cases
1. **No output path stored**: User clicks button before any extraction (shouldn't happen - button disabled)
2. **Folder deleted**: Output folder deleted after extraction but before button click
3. **Permission denied**: User lacks permissions to access the folder
4. **Invalid path**: Path contains invalid characters or no longer exists
5. **Unknown platform**: Running on non-Windows/Linux/macOS system
6. **Multiple extractions**: User extracts multiple files, button opens correct (latest) folder

### Playwright MCP Tests
Not applicable - this is a desktop GUI application, not a web application. Playwright is for browser automation.

## Acceptance Criteria
1. "Open Folder" button is visible in the GUI to the right of the "Extract" button
2. Button is initially disabled when application starts
3. Button becomes enabled after first successful extraction completes
4. Clicking the button opens the OS file manager to the folder containing the Excel file
5. Button remains enabled for subsequent clicks without re-extraction
6. Platform-specific folder opening works correctly:
   - Windows: Opens Explorer with file selected
   - Linux: Opens file manager to folder
   - macOS: Opens Finder with file selected
7. Errors during folder opening are logged but don't show error dialogs to user
8. All existing functionality remains unchanged (zero regressions)
9. All existing tests continue to pass
10. Type checking passes with mypy

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run pytest app/tests/core/test_gui_helpers.py -v` - Run new unit tests for folder opening logic
- `uv run pytest --cov=app/core app/tests/` - Verify code coverage remains high
- `uv run mypy app/` - Ensure type checking passes with no errors
- `bash scripts/start.sh` - Launch application manually to test GUI behavior
  - Verify button is disabled initially
  - Extract a file and verify button becomes enabled
  - Click "Open Folder" and verify correct folder opens
  - Close and restart app, verify button is disabled again

## Notes

### Platform-Specific Folder Opening Commands
- **Windows**: Use `explorer /select,<filepath>` to open Explorer with the file selected
- **Linux**: Use `xdg-open <folderpath>` to open default file manager to folder
- **macOS**: Use `open -R <filepath>` to open Finder with file selected

### Design Decisions
- Button remains enabled after first extraction for convenience - users can re-access folder without re-extracting
- Errors don't show user dialogs - folder opening is a convenience feature, failures shouldn't interrupt workflow
- Use `Path.parent` instead of `os.path.dirname` for consistency with pathlib usage
- Follow existing pattern from `_open_excel_file()` for platform detection and subprocess usage

### Future Enhancements (Out of Scope)
- Add keyboard shortcut for "Open Folder" (e.g., Ctrl+O)
- Add tooltip showing the current output path on hover
- Add "Recent Files" list showing all extraction results
- Add context menu on file entry field to open folder
