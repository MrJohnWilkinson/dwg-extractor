# Bug: Log File Controls Not Visible in GUI

## Bug Description
After implementing specs/059-unit-4-5-log-file-controls.md, the new "Generate Log File" checkbox and file log level dropdown are not visible in the GUI. The controls exist in the code and are properly packed into the log frame, but users cannot see them because the window height is too small to display all UI elements.

**Expected behavior:** Users should see the "Generate Log File" checkbox and "Level:" dropdown in the log viewer panel when the application starts.

**Actual behavior:** The controls are added to the widget hierarchy but are cut off below the visible window area. Users only see the display log level dropdown, and the new file logging controls are hidden.

## Problem Statement
The window geometry is set to `600x500` pixels (line 70 in `app/main.py`), but the cumulative height of all UI elements (including 4 filter rows, progress bar, status label, and expanded log frame) requires approximately 790-800 pixels. The log file options frame, being packed after the display log level menu but before the log text area, gets squeezed out when there's insufficient vertical space.

## Solution Statement
Increase the initial window height from 500 to 750 pixels to accommodate all UI elements including the newly added log file controls. This is a minimal, surgical fix that only changes the geometry string on line 70.

## Steps to Reproduce
1. Run the application with `bash scripts/start.sh`
2. Observe the log viewer panel at the bottom
3. Note that only the display log level dropdown (DEBUG/INFO/WARNING/ERROR) is visible
4. The "Generate Log File" checkbox and file level dropdown are NOT visible
5. Resize the window taller manually - the controls appear once the window is large enough

## Root Cause Analysis
The root cause is a **window geometry mismatch**. When specs/059-unit-4-5-log-file-controls.md was implemented, it added:
- `log_file_options_frame` - a transparent frame container (~35px with padding)
- `log_file_checkbox` - "Generate Log File" checkbox
- `file_level_label` - "Level:" label
- `file_log_level_menu` - dropdown for DEBUG/INFO/WARNING

These controls are packed into `log_frame` between `log_level_menu` and `log_text`. The log frame has `expand=True` but the fixed window height of 500px doesn't provide enough space. The pack geometry manager allocates space top-to-bottom, and by the time it reaches the log_file_options_frame, there's minimal space left. Combined with the `log_text` widget's `height=200` preference, the log file controls get squeezed out.

The window was likely sized for an earlier version of the UI with fewer controls. Multiple features have been added over time (Units selector, Precision Fix, Gap Bridge, Min Area Filter, Min Side Filter, Log File Controls), each consuming vertical space.

## Relevant Files
Use these files to fix the bug:

- `app/main.py` - Main GUI application file containing the window geometry setting at line 70. This is the only file that needs modification.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update window geometry
- Open `app/main.py`
- Locate line 70: `self.geometry("600x500")`
- Change to: `self.geometry("600x750")`
- This increases the initial window height from 500 to 750 pixels, providing adequate space for all UI elements including the log file controls

### 2. Run type checking
- Run `uv run mypy app/` to verify no type errors introduced
- Expected: Success with 0 errors

### 3. Run linting
- Run `uv run ruff check app/` to verify no linting issues
- Expected: Success with 0 errors

### 4. Run full test suite
- Run `uv run pytest app/tests/ -v` to verify no regressions
- Expected: All tests pass

### 5. Manual verification (if GUI available)
- Run `bash scripts/start.sh` to launch the application
- Verify the log viewer panel shows:
  1. Display log level dropdown (DEBUG/INFO/WARNING/ERROR) at the top
  2. "Generate Log File" checkbox below the display dropdown
  3. "Level:" label and file log level dropdown next to the checkbox
  4. Log text area below all controls
- Verify the checkbox toggle enables/disables the file level dropdown
- Verify all other UI elements remain visible and functional

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/ -v` - Run full test suite - must pass with 0 failures
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The fix is intentionally minimal - only changing the geometry string. No structural changes to widget layout are needed since the controls are correctly implemented and packed.
- Height of 750px was chosen to provide ~790-800px of content space plus some buffer for window chrome variations across platforms.
- The window remains resizable (`self.resizable(True, True)` on line 71), so users can still adjust the size as needed.
- Future UI additions should consider whether the window geometry needs adjustment.
- Alternative approaches considered but rejected:
  - Making the log text area smaller: Would reduce usability of the log viewer
  - Adding scrolling to the main frame: Would complicate the UI unnecessarily
  - Collapsible sections: Over-engineered for this simple visibility fix
