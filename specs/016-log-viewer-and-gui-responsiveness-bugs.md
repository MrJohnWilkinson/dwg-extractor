# Bug: Log Viewer and GUI Responsiveness Issues

## Bug Description
The DXF Block Extractor application has multiple issues with the log viewer panel and GUI responsiveness:

1. **Duplicate log lines**: Each log message appears twice in the log viewer
2. **No DEBUG messages**: Changing log level dropdown to DEBUG doesn't show debug-level messages
3. **App freezes**: Application appears frozen during extraction (2+ minutes for large files)
4. **Unresponsive log viewer**: Log viewer doesn't update smoothly during extraction
5. **Extraction stalled**: Progress appears to stall at "Analyzing block definitions..."

## Problem Statement
The log viewer implementation has architectural issues causing duplicate messages, missing debug output, and poor GUI responsiveness during CPU-intensive extraction operations.

## Solution Statement
Fix the logging architecture to prevent duplicates, properly propagate log level changes, and ensure the GUI remains responsive during extraction by yielding control back to the main thread periodically.

## Steps to Reproduce
1. Launch the application: `bash scripts/start.sh`
2. Change log level dropdown from INFO to DEBUG
3. Observe: "Log level changed to DEBUG" appears twice, no debug messages appear
4. Select a large DXF file (e.g., 74 layers, many entities)
5. Click Extract
6. Observe: GUI freezes, log viewer stops updating, progress bar stalls

## Root Cause Analysis

### Bug 1: Duplicate Log Lines
**Root Cause**: In `main.py` lines 68-71, the queue handler is added to both the module logger AND the root logger:
```python
self.queue_handler = create_queue_handler(self.log_queue)
self.logger.addHandler(self.queue_handler)  # Line 69
logging.getLogger().addHandler(self.queue_handler)  # Line 71 - DUPLICATE!
```
When the module logger logs a message, it propagates to the root logger (default behavior), so both handlers receive it.

### Bug 2: No DEBUG Messages After Level Change
**Root Cause**: The `_on_log_level_change` method (lines 168-177) only updates `self.current_log_level` for display filtering. However:
1. The `queue_handler` level is set at creation time to `logging.DEBUG` (default in `create_queue_handler`)
2. The module logger's level is set by `setup_logger()` from environment variable at startup
3. The extractor module has its own logger created at import time with level from env var

The dropdown change doesn't update:
- `self.queue_handler.setLevel()`
- `self.logger.setLevel()`
- The extractor module's logger level

### Bug 3-5: App Freezes / Unresponsive Log Viewer / Extraction Stalled
**Root Cause**: The extraction runs in a background thread (`_extraction_worker`), but the `extract_blocks()` function in `extractor.py` performs CPU-intensive operations without yielding:
- Block definition analysis iterates all blocks with geometry calculations
- Modelspace entity analysis iterates all entities
- Color analysis re-iterates all entities

The log queue fills up, but since `_poll_log_queue()` runs on a 100ms timer, if the main thread is starved (due to queue processing or other reasons), updates don't appear. The real issue is that the extraction itself takes a long time for large files (1.7s just to load, then extensive analysis).

The "stall" at "Analyzing block definitions" is actually the app working - it's just that there are no progress updates within `extract_blocks()` itself. The function logs at the start and end of major phases but not during iteration.

## Relevant Files
Use these files to fix the bug:

- `app/main.py` - Contains the GUI application class with log viewer setup. The queue handler attachment and log level change handler need fixes.
- `app/core/logger.py` - Contains `create_queue_handler()` and `setup_logger()`. May need to expose methods for dynamic level changes.
- `app/core/constants.py` - Contains `LOG_POLL_INTERVAL_MS`. May need adjustment.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Duplicate Log Lines in main.py
- Remove the duplicate root logger handler attachment at line 71
- Keep only the attachment to `self.logger` (the module logger)
- The module logger already propagates to root, so root logger handlers aren't needed for our queue
- Alternatively, set `self.logger.propagate = False` to prevent propagation if root handler is needed for other purposes

Changes in `app/main.py`:
- Remove line 71: `logging.getLogger().addHandler(self.queue_handler)`

### Step 2: Fix Log Level Change to Actually Change Logger Levels
- Update `_on_log_level_change()` to also update:
  1. `self.queue_handler.setLevel(level)` - so handler filters at capture time
  2. `self.logger.setLevel(level)` - so module logger respects the level
  3. Root logger level - so all loggers (including extractor) respect the level

Changes in `app/main.py` method `_on_log_level_change()`:
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

    # Update logger levels
    self.logger.setLevel(new_level)
    logging.getLogger().setLevel(new_level)

    self.logger.info(f"Log level changed to {choice}")
```

### Step 3: Improve GUI Responsiveness During Extraction
The extraction is CPU-bound and takes time for large files. The GUI thread runs separately, but the log queue polling may not keep up. Reduce poll interval for smoother updates.

Changes in `app/core/constants.py`:
- Change `LOG_POLL_INTERVAL_MS` from 100 to 50 for more responsive log updates

### Step 4: Add Progress Logging Within extract_blocks()
Add periodic progress logging within the long-running loops to show the user that extraction is progressing.

Changes in `app/core/extractor.py`:
- In the block definition analysis loop, log progress every 50 blocks
- In the modelspace entity analysis loop, log progress every 1000 entities
- In the color analysis loop, log progress periodically

### Step 5: Run Tests to Validate No Regressions
- Run all existing tests to ensure logging changes don't break anything
- Verify logger tests still pass

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests to validate logging changes
- `uv run pytest app/tests/ -v` - Run all tests to validate no regressions
- `uv run mypy app/` - Type check to ensure no type errors introduced
- `uv run ruff check app/` - Lint check for code quality

## Notes
- The extraction time for large files (2+ minutes) is expected behavior for complex CAD files with many entities. The fix improves perceived responsiveness through better progress feedback, not extraction speed.
- The `propagate` attribute on loggers controls whether messages bubble up to parent loggers. By default it's True, which caused the duplicate messages when both module and root logger had the queue handler.
- Consider future enhancement: Add a "Cancel" button for long extractions, requiring the extraction to check a cancellation flag periodically.
