# Chore: GUI Log Level Dropdown Controls Source Logger Levels

## Chore Description
Enable the GUI log level dropdown to control which log messages are captured by dynamically setting source logger levels. Currently, the dropdown only filters messages at display time in `_poll_log_queue()`, but DEBUG messages from modules like `extractor.py` and `geometry.py` may never reach the queue because the source loggers are set to INFO by default (from environment variable fallback).

When a user selects "DEBUG" in the log level dropdown, DEBUG messages from all modules should appear in the log viewer. When "INFO" or higher is selected, DEBUG messages should be suppressed. This change should take effect immediately without restarting the application.

## Relevant Files
Use these files to resolve the chore:

- **`app/main.py`** - Contains `_on_log_level_change()` method (lines 1049-1055) that currently does nothing (`pass`). This is where we add the logic to set source logger levels dynamically.
- **`app/core/logger.py`** - Reference for understanding how loggers are created with `setup_logger()` function. No changes needed.
- **`app/core/extractor.py`** - Uses `logger = setup_logger(__name__)` at line 56, creating logger `app.core.extractor`. No changes needed.
- **`app/core/geometry.py`** - Uses `logger = setup_logger(__name__)` at line 47, creating logger `app.core.geometry`. No changes needed.
- **`app/tests/core/test_logger.py`** - Existing logger tests. We'll add a new test for the dynamic level setting behavior.

### New Files
- None required.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Modify `_on_log_level_change()` in `app/main.py`

Update the `_on_log_level_change()` method to dynamically set source logger levels:

- Replace the current `pass` statement with logic to:
  1. Convert the dropdown value (string like "DEBUG") to logging level constant using `getattr(logging, value)`
  2. Set the level for known source loggers:
     - `logging.getLogger("app.core.extractor").setLevel(level)`
     - `logging.getLogger("app.core.geometry").setLevel(level)`
     - `logging.getLogger("app.main").setLevel(level)`
  3. Also set the root logger level for comprehensive coverage of any other loggers

- Update the docstring to accurately describe the new behavior

The implementation should be:

```python
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
```

### Step 2: Add Unit Test for Dynamic Log Level Change

Create a test in `app/tests/core/test_logger.py` to verify the dynamic level setting pattern works correctly:

- Add a new test class `TestDynamicLogLevelSetting` with tests that verify:
  1. Setting a logger level dynamically affects message capture
  2. Setting DEBUG level captures DEBUG messages
  3. Setting INFO level filters out DEBUG messages

### Step 3: Run Validation Commands

Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests to validate new dynamic level behavior
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors introduced
- `uv run ruff check app/` - Run linter to ensure code quality

## Notes
- The `_poll_log_queue()` method already filters messages at display time based on the dropdown value. This change ensures that DEBUG messages are actually captured in the first place.
- The QueueHandler is set to `logging.DEBUG` level in `create_queue_handler()` (line 237 of logger.py), so it will capture any messages that reach it. The bottleneck is the source loggers themselves.
- File log level dropdown behavior remains unchanged - it independently controls the file handler verbosity during extraction.
- This is a minimal, focused change that only modifies the `_on_log_level_change()` method body and docstring.
