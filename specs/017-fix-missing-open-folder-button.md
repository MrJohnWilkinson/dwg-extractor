# Bug: Missing Open Folder Button in GUI

## Bug Description
The "Open Folder" button is not appearing in the DWG Block Extractor GUI, despite commit 8e81b07 claiming to have implemented this feature per spec 011-add-open-folder-button.md. The GUI currently only shows two buttons: "Browse" and "Extract", missing the third "Open Folder" button that should appear to the right of the Extract button.

**Expected Behavior:**
- GUI should display three buttons in the button frame: "Browse", "Extract", and "Open Folder"
- "Open Folder" button should be initially disabled
- After successful extraction, button should enable and open the folder containing the generated Excel file
- Button should remain enabled for subsequent clicks without re-extraction

**Actual Behavior:**
- GUI only displays two buttons: "Browse" and "Extract"
- No "Open Folder" button is present in the interface
- Users cannot quickly access the output folder containing Excel files

## Problem Statement
Investigation reveals that commit 8e81b07 ("feat: add Open Folder button to GUI for quick folder access") has a misleading commit message. While the message describes GUI changes to app/main.py (lines 58, 109-117, 202, 260-261, 286-315), the actual commit only contains changes to:
- app/core/excel_writer.py (refactoring function names)
- specs/011-add-open-folder-button.md (the spec file)
- specs/012-verify-and-fix-spec-010-naming-conventions.md

**Root Cause:** The GUI implementation code for the Open Folder button was never committed to app/main.py, despite the commit message claiming it was. This appears to be a staging/commit oversight where the spec and related refactoring were committed, but the actual GUI implementation was left out.

## Solution Statement
Implement the missing "Open Folder" button functionality in app/main.py according to the original spec (011-add-open-folder-button.md). This involves:

1. Adding instance variable `output_excel_path` to track the Excel file location
2. Modifying the extraction worker to capture and store the Excel output path
3. Creating the `_open_output_folder()` method with platform-specific commands
4. Adding the "Open Folder" button widget to the button frame
5. Implementing button state management (disabled initially, enabled after extraction)

The implementation will follow the existing code patterns in app/main.py, particularly the `_open_excel_file()` method for platform-specific file operations.

## Steps to Reproduce
1. Run the application: `bash scripts/start.sh`
2. Observe the GUI interface
3. Count the buttons in the button frame below the file entry field
4. Expected: 3 buttons (Browse, Extract, Open Folder)
5. Actual: 2 buttons (Browse, Extract)

## Root Cause Analysis
The root cause is a git commit oversight:

1. Spec 011 was created outlining the Open Folder button implementation
2. Implementation work was done (likely in working directory)
3. During commit, only partial changes were staged:
   - excel_writer.py refactoring was staged and committed
   - Spec files were staged and committed
   - **app/main.py GUI changes were NOT staged/committed**
4. Commit message was written describing ALL intended changes (including main.py)
5. Subsequent commit 103a357 ran Ruff formatter, which reformatted main.py but didn't add the missing functionality

Evidence:
- `git show 8e81b07 --name-only` shows only 3 files: excel_writer.py and 2 spec files
- `git diff 8e81b07^..8e81b07 -- app/main.py` shows no changes
- Current app/main.py (line 57) has only `self.selected_file_path` variable, missing `self.output_excel_path`
- Current app/main.py (lines 86-100) shows only Browse and Extract buttons in button_frame
- No `_open_output_folder()` method exists in current main.py

## Relevant Files
Use these files to fix the bug:

- **app/main.py** (app/main.py:1-280)
  - Main GUI application file where button implementation is missing
  - Line 57: Instance variables - need to add `self.output_excel_path: str | None = None`
  - Line 86-100: Button frame - need to add Open Folder button after Extract button
  - Line 183: Extraction worker - need to store `excel_path` to `self.output_excel_path`
  - Line 232: After auto-open Excel - need to enable Open Folder button
  - Line 244: After `_open_excel_file()` - need to add `_open_output_folder()` method

- **app/core/constants.py** (app/core/constants.py:1-69)
  - Contains application constants
  - May need to add button text constant (optional, can use inline string)

- **specs/011-add-open-folder-button.md** (specs/011-add-open-folder-button.md:1-184)
  - Original specification for the feature
  - Provides detailed implementation guidance
  - Lines 52-106: Step by step implementation tasks
  - Lines 168-171: Platform-specific folder opening commands

### New Files
None required - all changes are to existing app/main.py file.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add output path tracking instance variable
- Open app/main.py and locate the `__init__` method instance variables section (around line 57)
- Add `self.output_excel_path: str | None = None` after `self.selected_file_path: str | None = None`
- This will track the Excel file path after extraction for folder opening

### 2. Create the folder opening method
- Add the `_open_output_folder()` method after the `_open_excel_file()` method (after line 264)
- Implement platform-specific folder opening using `platform.system()`:
  - Windows: `subprocess.run(['explorer', '/select,', file_path], check=False)`
  - Linux: `subprocess.run(['xdg-open', str(folder_path)], check=False)`
  - macOS: `subprocess.run(['open', '-R', file_path], check=False)`
- Use `Path(self.output_excel_path).parent` to get folder path for Linux
- Include validation check: return early if `self.output_excel_path` is None
- Add error handling with `try/except` and logger warnings (don't show errors to user)
- Follow the pattern from `_open_excel_file()` for consistency

### 3. Add Open Folder button widget
- Locate the `_create_widgets()` method button frame section (around lines 86-100)
- After the Extract button creation (line 100), add the Open Folder button:
  - Create button with text "Open Folder"
  - Set width to 120 (consistent with Browse and Extract)
  - Set command to `self._open_output_folder`
  - Set initial state to "disabled"
  - Pack with `side="left"` and `padx=(10, 0)` for spacing
  - Store reference as `self.open_folder_button`

### 4. Store Excel path after extraction
- Locate the `_extraction_worker()` method where Excel is generated (around line 183)
- After `excel_path = write_excel(extraction_result, self.selected_file_path)`
- Add: `self.output_excel_path = excel_path`
- This captures the path for later folder opening

### 5. Enable button after successful extraction
- Locate the `_show_success_ui()` method (around line 222)
- After the messagebox.showinfo() call but before `_open_excel_file()` (around line 232)
- Add: `self.open_folder_button.configure(state="normal")`
- This enables the button once we have a valid output path

### 6. Run type checking to ensure no errors
- Execute: `uv run mypy app/`
- Verify no type errors are introduced
- Fix any type issues if they appear

### 7. Run all tests to ensure zero regressions
- Execute: `uv run pytest app/tests/ -v`
- Verify all existing tests still pass
- Confirm no functionality was broken

### 8. Manual GUI testing
- Execute: `bash scripts/start.sh`
- Verify button states and functionality:
  - Check "Open Folder" button is visible and disabled on startup
  - Select a test DWG/DXF file using Browse
  - Click Extract and wait for completion
  - Verify "Open Folder" button becomes enabled after extraction
  - Click "Open Folder" and verify folder opens in file manager
  - Click "Open Folder" again to verify it works without re-extraction
  - Close and restart app, verify button is disabled again

### 9. Run validation commands
- Execute all commands listed in "Validation Commands" section below
- Ensure every command passes without errors

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run mypy app/` - Ensure type checking passes with no errors
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions
- `uv run pytest --cov=app/core app/tests/` - Verify code coverage remains high (>85%)
- `bash scripts/start.sh` - Launch application for manual testing:
  - Verify 3 buttons are visible (Browse, Extract, Open Folder)
  - Verify Open Folder button is disabled initially
  - Extract a test file (app/tests/assets/sample_drawing.dxf)
  - Verify Open Folder button becomes enabled after extraction
  - Click Open Folder and verify folder opens in file manager
  - Verify no error dialogs appear if folder opening fails
- `uv run ruff check app/` - Ensure code quality standards are met
- `git diff app/main.py` - Review changes before committing

## Notes

### Platform-Specific Folder Opening Commands
Reference from spec 011, lines 168-171:
- **Windows**: `explorer /select,<filepath>` - Opens Explorer with file selected
- **Linux**: `xdg-open <folderpath>` - Opens default file manager to folder
- **macOS**: `open -R <filepath>` - Opens Finder with file selected

### Implementation Pattern
Follow the existing `_open_excel_file()` method (lines 244-264) as a template:
- Use `platform.system()` for platform detection
- Use try/except for error handling
- Log errors but don't show user dialogs (convenience feature)
- Use `check=False` for subprocess.run to avoid exceptions

### Design Decisions from Original Spec
- Button remains enabled after first extraction for convenience
- Errors don't show user dialogs - failures shouldn't interrupt workflow
- Use Path.parent for folder path extraction
- No constants needed - inline "Open Folder" string is acceptable

### Code Quality
- Maintain type hints for all variables and return types
- Follow existing code style (Ruff formatted)
- Maintain consistency with existing button creation patterns
- Log all significant actions for debugging

### Testing Notes
- GUI tests were removed in commit f1e298a due to WSL2 X server issues
- Manual testing is the primary validation method for GUI changes
- Unit tests would be nice but not critical for this GUI-only feature
- Focus on ensuring existing tests pass (zero regressions)
