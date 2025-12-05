# Bug: DEBUG logging not showing in GUI log viewer

## Bug Description
The GUI log viewer does not display DEBUG level log messages, even when the user explicitly selects "DEBUG" from the log level dropdown. The output shows only INFO level and above messages regardless of the selected log level.

**Expected behavior:** When DEBUG is selected in the dropdown (or by default since dropdown starts at DEBUG), all DEBUG messages from `core.extractor`, `core.geometry`, `core.excel_writer`, and other modules should appear in the log viewer.

**Actual behavior:** Only INFO level messages appear. DEBUG messages like "Analyzing block definition: X", "Bounding box: processing entity type Y", "Net areas: calculating for Z polygons" are never shown.

## Problem Statement
Module loggers in `core/extractor.py`, `core/geometry.py`, `core/excel_writer.py`, and `core/excel_formatting.py` are initialized at import time via `setup_logger(__name__)`. This function:
1. Creates a StreamHandler for stdout
2. Sets the handler's level based on `DXF_EXTRACTOR_LOG_LEVEL` environment variable (defaults to INFO)
3. Sets the logger's level to match

When the GUI's `_on_log_level_change()` method is called, it updates:
- The queue handler level
- The main.py logger level
- The root logger level

However, it does **not** update the individual module loggers (`core.extractor`, `core.geometry`, etc.) which retain their original INFO level. Since Python's logging filters at the logger level first, DEBUG messages never reach the queue handler.

## Solution Statement
Modify `_on_log_level_change()` in `app/main.py` to also update the log level on all relevant module loggers when the user changes the dropdown selection. This ensures DEBUG messages from all modules are captured by the queue handler and displayed in the GUI.

## Steps to Reproduce
1. Run the application: `bash scripts/start.sh`
2. Observe the log level dropdown shows "DEBUG" by default
3. Select a DXF file and click Extract
4. Observe the log output - only INFO level messages appear
5. Change dropdown to INFO, then back to DEBUG
6. Extract again - still only INFO messages appear
7. No DEBUG messages like "Analyzing block definition:" ever appear

## Root Cause Analysis
The logging hierarchy issue occurs because:

1. **Import-time initialization:** Each module calls `logger = setup_logger(__name__)` at module load time, which creates loggers with INFO level (the default when `DXF_EXTRACTOR_LOG_LEVEL` is not set).

2. **Logger hierarchy:** Python logging uses a hierarchy where child loggers (e.g., `core.extractor`) can propagate messages to parent loggers (e.g., root). However, filtering happens at the source logger first.

3. **Level filtering order:** When `logger.debug("message")` is called:
   - First, the logger checks if DEBUG >= logger.level (INFO=20, DEBUG=10) → **FAILS, message discarded**
   - The message never reaches any handlers

4. **GUI only updates root/queue:** The `_on_log_level_change()` method updates the root logger and queue handler, but the source loggers still filter out DEBUG messages before propagation.

## Relevant Files
Use these files to fix the bug:

- `app/main.py` - Contains `_on_log_level_change()` method that needs to update module logger levels. Lines 187-205 handle the log level change.
- `app/core/logger.py` - Contains `setup_logger()` function. May need a helper function to get all app loggers or update all logger levels.
- `app/core/extractor.py` - Uses `logger = setup_logger(__name__)` at line 47. Contains many `logger.debug()` calls that should be visible.
- `app/core/geometry.py` - Uses `logger = setup_logger(__name__)` at line 26. Contains many `logger.debug()` calls for geometry analysis.
- `app/core/excel_writer.py` - Uses `logger = setup_logger(__name__)` at line 96. Contains `logger.debug()` calls.
- `app/core/excel_formatting.py` - Uses `logger = setup_logger(__name__)` at line 35. Contains `logger.debug()` calls.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add helper function to logger.py to update all app logger levels

- Add a new function `set_all_logger_levels(level: int)` to `app/core/logger.py`
- This function should iterate through all loggers with names starting with `core.` or `__main__`
- For each matching logger, set both the logger level and all handler levels to the specified level
- Use `logging.Logger.manager.loggerDict` to access all registered loggers

```python
def set_all_logger_levels(level: int) -> None:
    """
    Set log level for all application loggers.

    Updates both logger level and handler levels for all loggers
    in the core.* namespace and __main__.

    Args:
        level: Logging level constant (e.g., logging.DEBUG, logging.INFO)
    """
    # Get all logger names
    logger_dict = logging.Logger.manager.loggerDict

    # Update core.* loggers
    for name in logger_dict:
        if name.startswith("core.") or name == "__main__":
            logger = logging.getLogger(name)
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
```

### Step 2: Update main.py to import and use the new helper function

- Add `set_all_logger_levels` to the import from `core.logger`
- Modify `_on_log_level_change()` to call `set_all_logger_levels(new_level)` after setting the queue handler level

Update the import line:
```python
from core.logger import create_queue_handler, set_all_logger_levels, setup_logger
```

Update `_on_log_level_change()`:
```python
def _on_log_level_change(self, choice: str) -> None:
    """Handle log level dropdown change."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    new_level = level_map.get(choice, logging.INFO)
    self.current_log_level = new_level

    # Update handler level
    self.queue_handler.setLevel(new_level)

    # Update all application logger levels
    set_all_logger_levels(new_level)

    # Update root logger level
    logging.getLogger().setLevel(new_level)

    self.logger.info(f"Log level changed to {choice}")
```

### Step 3: Initialize logger levels to DEBUG at application startup

- In `DXFExtractorApp.__init__()`, after setting up the queue handler and before creating widgets, call `set_all_logger_levels(logging.DEBUG)` to ensure all loggers start at DEBUG level (matching the dropdown default)
- This ensures DEBUG messages are captured from the very start of extraction

Add after line 79 in main.py (after `logging.getLogger().setLevel(logging.DEBUG)`):
```python
# Initialize all application loggers to DEBUG to match dropdown default
set_all_logger_levels(logging.DEBUG)
```

### Step 4: Add unit tests for the new helper function

- Create test file `app/tests/core/test_logger.py` (if not exists, add to existing)
- Add tests for `set_all_logger_levels()`:
  - Test that it updates logger levels correctly
  - Test that it updates handler levels correctly
  - Test that it only affects core.* and __main__ loggers

### Step 5: Run validation commands

- Run the test suite to ensure no regressions
- Manually test the GUI to verify DEBUG messages now appear

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests to validate the new helper function
- `uv run pytest app/tests/ -v` - Run all tests to validate no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors introduced
- `uv run ruff check app/` - Run linting to ensure code quality

Manual validation (requires GUI):
1. Run `bash scripts/start.sh`
2. Verify dropdown shows DEBUG by default
3. Select a DXF file and extract
4. Verify DEBUG messages appear (e.g., "Analyzing block definition:", "Bounding box:", "Net areas:")
5. Change dropdown to INFO - verify DEBUG messages stop appearing
6. Change dropdown back to DEBUG - verify DEBUG messages appear again

## Notes
- The fix is minimal and surgical - only adds one helper function and updates two locations in main.py
- The helper function uses the standard `logging.Logger.manager.loggerDict` which is the correct way to access all registered loggers
- This fix does not change how loggers are initialized in each module - they still use `setup_logger()` which allows environment variable override for CLI/automated usage
- The GUI-specific level change is handled separately, allowing the GUI to override the environment variable setting dynamically
