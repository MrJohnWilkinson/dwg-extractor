# Feature: Logging Architecture Improvements

## Feature Description
This feature improves the logging system architecture by separating log message generation from display, fixing file logging independence, and improving the GUI user experience with better labels and visual hints. The changes ensure that file logging captures all DEBUG messages during extraction regardless of the GUI log viewer level setting, while providing clear feedback to users about how the logging controls work.

## User Story
As a developer or power user
I want file logging to always capture DEBUG-level messages during extraction
So that I can analyze detailed extraction logs without having to manually change the GUI log level first

## Problem Statement
The current logging architecture has several issues:
1. **Coupled Generation/Display**: The GUI log level dropdown changes source logger levels, affecting both display AND file logging. If the user sets INFO level, DEBUG messages aren't generated, so file logging misses them even when set to DEBUG.
2. **Missing Settings Sync**: The log_viewer_level setting from SettingsManager isn't synchronized to the GUI dropdown on startup.
3. **Unclear GUI Labels**: The log level dropdown doesn't explain its dual role in controlling message capture and display.
4. **No File Logging Feedback**: When file logging is enabled, there's no visual indication that DEBUG messages will be captured.

## Solution Statement
Implement a decoupled logging architecture:
1. **Decouple File Logging**: During extraction, temporarily set source loggers to DEBUG level to ensure all messages are generated, regardless of GUI setting. The GUI log viewer filters display based on its level setting.
2. **Update GUI Labels**: Add a tooltip to the log level dropdown explaining its behavior.
3. **Sync Settings to GUI**: Initialize the GUI dropdown from SettingsManager on startup and save changes.
4. **Add File Logging Hint**: Show a visual hint when file logging is enabled indicating DEBUG capture is active.

## Relevant Files
Use these files to implement the feature:

- `app/main.py` - Main GUI application containing the log level dropdown, file logging controls, and extraction worker. Needs changes for settings sync, tooltip, hint display, and extraction-time logger level management.
- `app/core/settings.py` - SettingsManager class. May need minor updates for log_viewer_level persistence.
- `app/core/constants.py` - Contains DEFAULT_LOG_VIEWER_LEVEL constant. Reference only, no changes needed.
- `app/core/logger.py` - Logging utilities. Reference for understanding current architecture.
- `app/tests/core/test_settings.py` - Existing settings tests. Add tests for log_viewer_level sync.
- `app/tests/core/test_logger.py` - Existing logger tests. Add tests for decoupled logging behavior.

### New Files
None required - all changes fit within existing modules.

## Implementation Plan

### Phase 1: Foundation - Settings Synchronization
Establish proper bidirectional sync between SettingsManager and GUI dropdown:
- Initialize GUI dropdown value from settings on startup
- Save dropdown changes to settings when modified
- Ensure log_viewer_level persists across sessions

### Phase 2: Core Implementation - Decouple File Logging
Modify extraction worker to temporarily enable DEBUG on source loggers:
- Before extraction: If file logging enabled, set source loggers to DEBUG
- After extraction: Restore original logger levels
- QueueHandler filtering remains unchanged (controlled by GUI dropdown)

### Phase 3: Integration - UI/UX Improvements
Add user-facing improvements:
- Add tooltip to log level dropdown explaining its behavior
- Add visual hint label when file logging is enabled
- Ensure hint updates dynamically when file logging is toggled

## Step by Step Tasks

### Step 1: Add Settings Synchronization for Log Viewer Level
- In `DXFExtractorApp.__init__()`, initialize `log_level_var` from `settings.get("log_viewer_level")` instead of hardcoded "INFO"
- In `_on_log_level_change()`, add call to `settings.set("log_viewer_level", value)` and `settings.save()`
- This ensures the log viewer level persists across application restarts

### Step 2: Add Tooltip to Log Level Dropdown
- In `_create_widgets()`, create the log level dropdown with a descriptive tooltip
- CustomTkinter doesn't have native tooltips, so add a hint label below the dropdown
- Label text: "Controls message capture and display. Set to DEBUG to enable DEBUG file logging."

### Step 3: Implement Decoupled File Logging in Extraction Worker
- In `_extraction_worker()`, before setting up file handler, store original source logger levels
- If file logging is enabled, set source loggers (`core.extractor`, `core.geometry`, `__main__`) to DEBUG level
- In the `finally` block, restore original logger levels after extraction completes
- This ensures file logging captures DEBUG messages regardless of GUI dropdown setting

### Step 4: Add Visual Hint for File Logging Active
- Add a new label widget below the file logging checkbox row
- When file logging checkbox is checked, show hint: "DEBUG messages will be captured to file"
- When unchecked, hide the hint label
- Update `_on_log_file_toggle()` to show/hide this hint

### Step 5: Update Tests for Settings Synchronization
- Add test in `test_settings.py` verifying log_viewer_level is persisted and loaded correctly
- Verify default value is "INFO" when no settings file exists
- Verify saved value is restored on reload

### Step 6: Add Tests for Decoupled Logging Behavior
- Add test verifying source loggers are set to DEBUG during extraction when file logging enabled
- Add test verifying source loggers are restored after extraction completes
- Add test verifying GUI filtering still works independently

### Step 7: Run Validation Commands
- Run all tests to ensure no regressions
- Run type checking to verify type safety
- Run linting to ensure code quality

## Testing Strategy

### Unit Tests
- `test_settings.py`:
  - Test log_viewer_level default is "INFO"
  - Test log_viewer_level persists after save/load cycle
  - Test log_viewer_level validation (only accepts valid log levels)

### Integration Tests
- `test_logger.py`:
  - Test source logger levels are set to DEBUG when file logging starts
  - Test source logger levels are restored after extraction completes
  - Test QueueHandler filtering is independent of source logger levels

### Edge Cases
- File logging enabled but extraction aborted - logger levels must still be restored
- File logging toggled during extraction - should not affect current extraction
- Invalid log level in saved settings - should fall back to default
- Multiple rapid extractions - logger level state must be consistent

### Playwright MCP Tests
Not applicable - logging behavior is internal and not visible in E2E tests.

## Acceptance Criteria
1. Log viewer dropdown initializes from saved settings on application startup
2. Changing log viewer dropdown saves the new value to settings
3. Log level dropdown has descriptive hint text explaining its behavior
4. When file logging is enabled, a hint shows "DEBUG messages will be captured to file"
5. File logging captures DEBUG messages regardless of GUI log viewer level setting
6. Source logger levels are restored after extraction completes (success, error, or abort)
7. All existing tests continue to pass
8. New tests cover settings sync and decoupled logging behavior

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests for log_viewer_level sync
- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests for decoupled logging
- `uv run pytest app/tests/ -v` - Run all tests for regression check
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- CustomTkinter doesn't have native tooltip support; using a hint label is the recommended pattern
- The decoupling approach (Option B) was chosen over alternatives because it:
  - Requires minimal architectural changes
  - Maintains backward compatibility with existing GUI behavior
  - Doesn't require changes to the logging infrastructure
- Consider future enhancement: Add a "capture all" checkbox that forces DEBUG regardless of file logging level dropdown
- The file log level dropdown becomes less relevant with this change since DEBUG is always captured during extraction, but keeping it allows users to filter file output if they only want WARNING-level file logs
