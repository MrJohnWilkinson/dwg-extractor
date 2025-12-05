# Feature: Live Log Viewer in GUI

## Feature Description
Add a real-time log viewer panel to the DXF Block Extractor GUI that displays extraction progress, timing information, and debug messages. The viewer enables developers and users to monitor long-running DXF extractions, identify performance bottlenecks, and copy logs for debugging purposes. The implementation uses a thread-safe queue-based architecture to deliver log messages from background extraction threads to the GUI.

## User Story
As a developer/user running long DXF extractions
I want a live log viewer in the GUI showing real-time extraction progress
So that I can monitor progress, identify bottlenecks, and copy logs for debugging

## Problem Statement
Currently, log messages from the extraction process are only visible in the terminal/stdout. Users running the GUI application cannot see real-time progress details, timing information, or debug messages without access to the terminal. This makes it difficult to:
- Monitor extraction progress for large DXF files
- Identify which extraction phases are slow
- Debug issues without terminal access
- Understand what the application is doing during processing

## Solution Statement
Implement a live log viewer panel in the GUI using:
1. A `CTkTextbox` widget configured as read-only with monospace font for log display
2. A log level dropdown (`CTkOptionMenu`) to filter displayed log levels (DEBUG, INFO, WARNING, ERROR)
3. Python's `logging.handlers.QueueHandler` with `queue.Queue` for thread-safe log delivery
4. A 100ms polling loop using `self.after()` to read from the queue and update the textbox
5. Auto-scroll behavior to always show the latest log entry
6. Formatted log entries with timestamps, log level, and message

The existing stdout logging continues unchanged (DRY principle - no duplication of log calls).

## Relevant Files
Use these files to implement the feature:

- **app/main.py** - Main GUI application file. Add log viewer widget (`CTkTextbox`), log level dropdown (`CTkOptionMenu`), queue handler setup, and polling mechanism. Resize window to accommodate new UI elements.

- **app/core/logger.py** - Centralized logging configuration. Add `create_queue_handler()` factory function that creates a `QueueHandler` attached to a provided `queue.Queue`.

- **app/core/extractor.py** - DXF extraction logic. Add granular `logger.info()` calls at key extraction phases to provide progress visibility. Use existing `timed_block()` context manager for timing.

- **app/core/constants.py** - Application constants. Add `LOG_POLL_INTERVAL_MS = 100` constant for the queue polling interval.

### New Files
No new files needed - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation
Extend the logging infrastructure to support queue-based delivery:
1. Add `LOG_POLL_INTERVAL_MS` constant to `constants.py`
2. Create `create_queue_handler()` factory function in `logger.py` that returns a configured `QueueHandler`
3. Ensure the queue handler uses the same formatter as stdout handler

### Phase 2: Core Implementation
Add the log viewer UI components and queue polling:
1. Resize GUI window from 500x300 to 600x500 to accommodate log viewer
2. Add log level dropdown widget (`CTkOptionMenu`) with options: DEBUG, INFO, WARNING, ERROR
3. Add log viewer widget (`CTkTextbox`) configured as read-only with monospace font
4. Create `queue.Queue` instance and attach `QueueHandler` to the application logger
5. Implement `_poll_log_queue()` method that reads from queue and appends to textbox
6. Start polling loop using `self.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)`
7. Implement auto-scroll to end of textbox after each append

### Phase 3: Integration
Add progress logging to extractor and integrate all components:
1. Add granular `logger.info()` calls in `extractor.py` at key phases:
   - File loading start/complete
   - Block definition analysis start/complete with count
   - Modelspace entity iteration start/complete
   - Color analysis start/complete
   - Final summary statistics
2. Wrap major extraction phases with `timed_block()` for elapsed time reporting
3. Ensure log level dropdown dynamically filters displayed messages
4. Test end-to-end flow with sample DXF files

## Step by Step Tasks

### Step 1: Add constant for poll interval
- Add `LOG_POLL_INTERVAL_MS = 100` to `app/core/constants.py`
- Place it in a new section with comment "# Log viewer configuration"

### Step 2: Create queue handler factory in logger.py
- Import `queue` and `logging.handlers.QueueHandler` in `app/core/logger.py`
- Create `create_queue_handler(log_queue: queue.Queue[logging.LogRecord], level: int = logging.DEBUG) -> logging.Handler` function
- The function should:
  - Create a `QueueHandler` with the provided queue
  - Set the handler level to the provided level
  - Return the handler (no formatter needed - formatting happens on display)

### Step 3: Resize GUI window and update layout
- In `app/main.py`, change `self.geometry("500x300")` to `self.geometry("600x500")`
- Change `self.resizable(False, False)` to `self.resizable(True, True)` to allow window resizing

### Step 4: Add log level dropdown widget
- Import `LOG_POLL_INTERVAL_MS` from `core.constants`
- Add instance variable `self.current_log_level: int = logging.INFO`
- In `_create_widgets()`, after the status label, add:
  - A frame for log controls (`log_controls_frame`)
  - Label "Log Level:"
  - `CTkOptionMenu` with values ["DEBUG", "INFO", "WARNING", "ERROR"]
  - Set default value to "INFO"
  - Add command callback `_on_log_level_change` to handle selection

### Step 5: Add log viewer textbox widget
- Add `CTkTextbox` widget (`self.log_viewer`) below the log controls
- Configure: `width=560`, `height=150`, `state="disabled"` (read-only), `font=("Courier", 10)`
- Pack with appropriate padding to fill available space

### Step 6: Set up queue and queue handler
- Import `queue` module and `create_queue_handler` from `core.logger`
- In `__init__`, create `self.log_queue: queue.Queue[logging.LogRecord] = queue.Queue()`
- Create queue handler: `self.queue_handler = create_queue_handler(self.log_queue)`
- Add queue handler to the logger: `self.logger.addHandler(self.queue_handler)`
- Also add to root logger to capture logs from extractor module

### Step 7: Implement queue polling method
- Create `_poll_log_queue(self) -> None` method that:
  - Uses `while True` loop with `self.log_queue.get_nowait()` in try/except
  - Catches `queue.Empty` to break the loop
  - For each `LogRecord`:
    - Check if record level >= `self.current_log_level`
    - If yes, format the message: `f"{record.asctime} [{record.levelname}] {record.getMessage()}"`
    - Append to textbox (enable, insert at end, disable, scroll to end)
  - Schedule next poll: `self.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)`

### Step 8: Implement log level change handler
- Create `_on_log_level_change(self, choice: str) -> None` method
- Map choice string to logging level: `{"DEBUG": logging.DEBUG, "INFO": logging.INFO, ...}`
- Update `self.current_log_level` with selected level
- Optionally append a message to log viewer indicating level change

### Step 9: Start polling loop
- At end of `__init__`, call `self._poll_log_queue()` to start the polling loop
- This kicks off the recurring `self.after()` chain

### Step 10: Add progress logging to extractor.py
- Add `logger.info()` calls at these points in `extract_blocks()`:
  - After loading DXF file: `logger.info(f"Loaded DXF file: {path.name}")`
  - Before block definition loop: `logger.info("Analyzing block definitions...")`  (already exists)
  - After block definition loop: `logger.info(f"Analyzed {len(block_entities)} block definitions")` (already exists)
  - Before modelspace iteration: `logger.info("Analyzing modelspace entities...")` (already exists)
  - After modelspace iteration (add entity count)
  - Before color analysis: `logger.info("Starting color analysis...")` (already exists in extract_color_analysis)
- Wrap major phases with `timed_block()`:
  - `with timed_block("DXF file loading", logger, logging.INFO):`
  - `with timed_block("block definition analysis", logger, logging.INFO):`
  - `with timed_block("modelspace entity analysis", logger, logging.INFO):`
  - `with timed_block("color analysis", logger, logging.INFO):`

### Step 11: Add timed_block imports and usage
- Import `timed_block` from `core.logger` in `extractor.py` (if not already imported)
- Wrap the identified extraction phases with timed_block context managers
- Use `level=logging.INFO` so timing appears at INFO level

### Step 12: Test manually in WSL
- Run `bash scripts/start.sh` to launch the application
- Select a sample DXF file and click Extract
- Verify:
  - Log viewer displays real-time progress messages
  - Timestamps are visible on each log line
  - Auto-scroll works (latest message always visible)
  - Log level dropdown filters messages correctly
  - Terminal/stdout still shows all log messages (DRY)

### Step 13: Validate with existing tests
- Run `uv run pytest app/tests/` to ensure no regressions
- Run `uv run mypy app/` to verify type checking passes
- Run `uv run ruff check app/` for linting

## Testing Strategy

### Unit Tests
- **logger.py tests**: Test `create_queue_handler()` returns a properly configured `QueueHandler`
- **Integration test**: Verify queue handler receives log records when logger is invoked

### Integration Tests
- No new integration tests required - existing extraction tests cover the extractor functionality
- Manual testing verifies GUI integration

### Edge Cases
- Empty queue on poll (should handle gracefully without error)
- Very long log messages (textbox should wrap or truncate appropriately)
- Rapid log messages (queue should buffer without blocking extraction thread)
- Log level change during extraction (should immediately filter displayed messages)
- Application close during polling (should not raise errors)

### Playwright MCP Tests
- Not applicable - this is a desktop GUI application using customtkinter, not a web application

## Acceptance Criteria
1. GUI window displays a log viewer panel with monospace font
2. Log level dropdown above viewer allows selecting DEBUG, INFO, WARNING, ERROR
3. Log messages appear in real-time during extraction (within 100ms of being logged)
4. Each log line shows timestamp, log level, and message
5. Log viewer auto-scrolls to show latest entry
6. Changing log level filters which messages are displayed
7. Terminal/stdout continues to receive all log messages
8. Existing tests pass without modification
9. Type checking (mypy) passes
10. Linting (ruff) passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/` - Run all tests to verify no regressions
- `uv run pytest app/tests/core/test_logger.py -v` - Run logger-specific tests
- `uv run mypy app/` - Verify type checking passes
- `uv run ruff check app/` - Verify linting passes
- `bash scripts/start.sh` - Launch GUI and manually test log viewer functionality

## Notes
- No new dependencies required - uses Python stdlib `queue` and `logging.handlers`
- The queue handler is attached to both the application logger and root logger to capture logs from all modules (main.py and extractor.py)
- Log formatting happens during display, not at queue insertion, to keep queue operations fast
- The 100ms poll interval provides responsive updates without excessive CPU usage
- Future enhancements (out of scope): clear button, export logs, color-coded levels, collapsible panel
