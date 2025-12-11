# Feature: Log File Controls (Units 4+5)

## Feature Description
Implement two related GUI enhancements that give users control over debug log file generation:

1. **Unit 4 - Log File Toggle**: Add a checkbox that allows users to opt-in to log file generation. By default, no log file is created, reducing clutter in user directories.

2. **Unit 5 - Log Level for File Output**: Add a dropdown that allows users to control the verbosity level of log file output independently from the GUI display level. Users can select DEBUG, INFO, or WARNING levels for file output.

These controls are placed in the log viewer panel and work together: the file level dropdown is disabled when log file generation is unchecked, and enabled when checked.

## User Story
As a CAD analyst
I want to control when debug log files are created and their verbosity
So that I can keep my directories clean during normal use and get detailed logs only when troubleshooting

## Problem Statement
The current implementation always creates a debug log file (`<filename>_debug_<timestamp>.log`) during every extraction, regardless of whether the user needs it. This results in:

1. **Directory clutter**: Users accumulate many log files they never use
2. **No verbosity control**: The file always captures DEBUG level, which may be too verbose for troubleshooting INFO-level issues
3. **Wasted I/O**: File writes occur even when debugging is not needed

Most users only need log files when troubleshooting specific issues. The unconditional file creation is an artifact of development-time debugging needs.

## Solution Statement
Add two new GUI controls in the log viewer panel:

1. **Log File Checkbox** (`self.log_file_var`): A BooleanVar defaulting to False that controls whether a debug log file is created. When unchecked (default), no file is created and extraction proceeds without file logging overhead.

2. **File Log Level Dropdown** (`self.file_log_level_var`): A StringVar defaulting to "DEBUG" that controls the verbosity of the log file when enabled. Options are DEBUG, INFO, and WARNING. The dropdown is disabled when the checkbox is unchecked.

The implementation modifies `_extraction_worker()` to conditionally create the file handler based on the checkbox state, and applies the selected log level to the handler when created.

## Relevant Files
Use these files to implement the feature:

### Core Implementation Files
- `app/main.py` - Main GUI application file. Contains:
  - `__init__` method (lines 61-103): Add state variables after existing filter variables (around line 97)
  - `_create_widgets` method (lines 105-366): Add checkbox and dropdown in log frame section after `log_level_menu` (line 356)
  - `_extraction_worker` method (lines 438-549): Modify debug file logging setup (lines 446-456) to be conditional
  - Add new `_on_log_file_toggle` method after `_on_log_level_change` (line 840)

### Reference Files (Read-Only)
- `app/core/logger.py` - Contains `create_debug_file_handler()` factory function used for creating the file handler. The handler's `setLevel()` method will be used to apply the user-selected log level.
- `app/tests/core/test_logger.py` - Contains existing logger tests demonstrating handler level configuration patterns

### Test Files
- `app/tests/core/test_logger.py` - May add tests for handler level configuration if needed (existing tests cover `create_debug_file_handler`)

## Implementation Plan

### Phase 1: Foundation (Unit 4 - State Variables)
Add the necessary state variables to track user preferences for log file generation.

1. Add `self.log_file_var = ctk.BooleanVar(value=False)` in `__init__` after existing filter variables
2. Add `self.file_log_level_var = ctk.StringVar(value="DEBUG")` immediately after `log_file_var`

### Phase 2: Core Implementation (Unit 4+5 - GUI Controls)
Add the checkbox and dropdown controls to the log viewer panel, creating a horizontal options row.

1. Create a transparent frame (`log_file_options_frame`) to hold the checkbox and dropdown in a horizontal layout
2. Add the "Generate Log File" checkbox bound to `log_file_var` with command callback
3. Add a "Level:" label and dropdown bound to `file_log_level_var`, initially disabled
4. Add `_on_log_file_toggle()` method to enable/disable dropdown based on checkbox state

### Phase 3: Integration (Unit 4+5 - Conditional File Handler)
Modify the extraction worker to conditionally create and configure the file handler.

1. Replace unconditional file handler creation with conditional logic based on `log_file_var.get()`
2. When enabled, apply user-selected log level using `handler.setLevel()`
3. Update progress/status messages to reflect whether file logging is active
4. Ensure cleanup logic handles the case where no handler was created

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add state variables to __init__
- Open `app/main.py`
- Locate the `__init__` method, specifically after line 97 (after `self.min_side_filter_amount_var`)
- Add the two new state variables:
```python
# Log file generation settings
self.log_file_var = ctk.BooleanVar(value=False)  # Default: no log file
self.file_log_level_var = ctk.StringVar(value="DEBUG")
```
- Run `uv run mypy app/main.py` to verify no type errors

### 2. Add log file options row to _create_widgets
- Open `app/main.py`
- Locate `_create_widgets`, specifically after line 356 (after `self.log_level_menu.pack(...)`)
- Add the log file options frame with checkbox and dropdown:
```python
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
```
- Run `uv run mypy app/main.py` to verify no type errors

### 3. Add _on_log_file_toggle method
- Open `app/main.py`
- Locate the `_on_log_level_change` method (around line 834-840)
- Add the new toggle handler method immediately after it:
```python
def _on_log_file_toggle(self) -> None:
    """Handle log file checkbox toggle - enable/disable level dropdown."""
    if self.log_file_var.get():
        self.file_log_level_menu.configure(state="normal")
    else:
        self.file_log_level_menu.configure(state="disabled")
```
- Run `uv run mypy app/main.py` to verify no type errors

### 4. Modify _extraction_worker for conditional file handler
- Open `app/main.py`
- Locate `_extraction_worker`, specifically lines 446-456 (debug file logging setup)
- Replace the unconditional file handler creation:
```python
# Set up debug file logging
input_path = Path(self.selected_file_path)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{input_path.stem}_debug_{timestamp}.log"
log_path = input_path.parent / log_filename

self.debug_file_handler = create_debug_file_handler(str(log_path))
logging.getLogger().addHandler(self.debug_file_handler)

self.logger.info(f"Debug log: {log_path}")
self._update_progress(0.1, f"Logging to: {log_filename}")
```
- With the conditional version:
```python
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

    self.logger.info(f"Debug log ({self.file_log_level_var.get()}): {log_path}")
    self._update_progress(0.1, f"Logging to: {log_filename}")
else:
    self._update_progress(0.1, "Starting extraction...")
```
- Run `uv run mypy app/main.py` to verify no type errors

### 5. Run type checking
- Run `uv run mypy app/` - Full type checking on all application code
- Verify zero type errors

### 6. Run existing tests
- Run `uv run pytest app/tests/core/test_logger.py -v` - Verify logger tests pass
- Run `uv run pytest app/tests/ -v` - Run full test suite
- Verify all tests pass with zero failures

### 7. Run linting and formatting
- Run `uv run ruff check app/` - Linting
- Run `uv run ruff format app/ --check` - Format check
- Verify both pass with zero errors

### 8. Run final validation
- Execute all validation commands to ensure the feature works correctly with zero regressions

## Testing Strategy

### Unit Tests
- The existing `test_logger.py` tests cover `create_debug_file_handler()` functionality including:
  - Handler creation and level configuration (`test_create_debug_file_handler_debug_level`)
  - All log levels being captured (`test_create_debug_file_handler_all_levels`)
  - Handler level can be changed via `setLevel()` (tested in `TestQueueHandler`)
- No new unit tests required as the changes are UI-only and the handler configuration is already tested

### Integration Tests
- Manual testing is required for GUI behavior:
  - Verify checkbox defaults to unchecked
  - Verify dropdown defaults to disabled
  - Verify checkbox toggle enables/disables dropdown
  - Verify no log file created when checkbox unchecked
  - Verify log file created when checkbox checked

### Edge Cases
- Extraction with log file disabled (default case)
- Extraction with log file enabled at DEBUG level
- Extraction with log file enabled at INFO level (should not contain DEBUG messages)
- Extraction with log file enabled at WARNING level (should only contain WARNING and above)
- Toggling checkbox multiple times before extraction
- Changing dropdown selection while checkbox is checked

### Playwright MCP Tests
Not applicable - these are GUI widget additions with no complex user flows. Manual visual inspection and functional testing is appropriate for:
- Verifying checkbox and dropdown render correctly
- Verifying dropdown state changes with checkbox toggle
- Verifying file creation behavior matches checkbox state

## Acceptance Criteria
1. `log_file_var` BooleanVar exists and defaults to `False`
2. `file_log_level_var` StringVar exists and defaults to `"DEBUG"`
3. "Generate Log File" checkbox appears in log frame below the display log level dropdown
4. File log level dropdown appears next to checkbox with "Level:" label
5. Dropdown is disabled when checkbox is unchecked (default state)
6. Dropdown is enabled when checkbox is checked
7. No log file is created during extraction when checkbox is unchecked
8. Log file is created during extraction when checkbox is checked
9. Log file respects selected level (DEBUG/INFO/WARNING) for message filtering
10. Progress message shows "Starting extraction..." when file logging disabled
11. Progress message shows "Logging to: <filename>" when file logging enabled
12. All existing tests pass without modification
13. Type checking passes with zero errors
14. Linting passes with zero errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checker on full application - must pass with 0 errors
- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests to verify handler configuration
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run ruff check app/` - Run linter - must pass with 0 errors
- `uv run ruff format app/ --check` - Verify code formatting - must pass

## Notes
- The `create_debug_file_handler()` function in `logger.py` sets the handler level to DEBUG by default. The implementation overrides this by calling `handler.setLevel()` with the user-selected level after creation.
- The file handler cleanup in the `finally` block of `_extraction_worker()` already handles the case where `self.debug_file_handler` is `None`, so no changes needed there.
- The log level dropdown options (DEBUG, INFO, WARNING) match the display log level dropdown for consistency. ERROR and CRITICAL are omitted as they're rarely needed for file logging.
- The horizontal layout using a transparent frame is consistent with other option rows in the UI (precision fix, gap bridge, etc.).
- Default behavior change: Previously, a log file was always created. Now, no file is created by default. This is intentional to reduce directory clutter for users who don't need debug logs.
