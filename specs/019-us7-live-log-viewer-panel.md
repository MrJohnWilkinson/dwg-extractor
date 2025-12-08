# Feature: Live Log Viewer Panel (US-7)

## Feature Description
Add a real-time log viewer panel to the DXF Block Extractor GUI that displays log messages as they occur. This provides users with immediate feedback during extraction operations without requiring terminal access. The viewer includes a log level dropdown for filtering messages and auto-scrolls to show the latest entries.

**Important Note:** File-based logging (implemented in US-2) remains the more reliable solution for debugging hangs since the GUI log viewer will block during heavy computation. However, the log viewer provides convenience for normal operation and quick monitoring.

## User Story
As a user
I want a log viewer in the GUI showing messages in real-time
So that I can monitor progress without terminal access

## Problem Statement
Currently, users must have access to the terminal/stdout to monitor detailed log messages during DXF extraction. This is inconvenient for users running the application without a visible terminal window, and makes it difficult to understand what's happening during long-running operations.

## Solution Statement
Implement a queue-based logging handler that captures log messages and displays them in a GUI text widget. The solution uses Python's standard `queue.Queue` for thread-safe message passing from the extraction worker thread to the main GUI thread. A polling mechanism (100ms interval) updates the display without blocking the main thread.

## Relevant Files
Use these files to implement the feature:

- **`app/core/logger.py`** - Add `QueueHandler` class and `create_queue_handler()` factory function. This file already contains `FlushingFileHandler`, `MillisecondFormatter`, and other logging utilities from US-2.

- **`app/main.py`** - Add log viewer panel (CTkFrame, CTkTextbox, CTkOptionMenu) to the GUI. Integrate queue handler with root logger and implement polling mechanism.

- **`app/tests/core/test_logger.py`** - Add unit tests for `QueueHandler` and `create_queue_handler()`. This file already contains comprehensive tests for existing logger components.

### New Files
None required - all changes are additions to existing files.

## Implementation Plan

### Phase 1: Foundation
Add the `QueueHandler` class and `create_queue_handler()` factory function to `logger.py`. This provides the infrastructure for capturing log messages in a queue for GUI consumption.

### Phase 2: Core Implementation
Modify the GUI in `main.py` to include:
- Log viewer frame with proper layout
- Log level dropdown (CTkOptionMenu) for filtering
- Log text area (CTkTextbox) with monospace font
- Queue and handler initialization
- Polling mechanism using `after()`

### Phase 3: Integration
Ensure the queue handler is added to the root logger so all log messages are captured. The existing stdout handler continues to receive all logs (no change to terminal output). Clean up handler on application destroy.

## Step by Step Tasks

### Step 1: Add QueueHandler class to logger.py
- Add `import queue` at the top of the file (after existing imports)
- Add `QueueHandler` class that extends `logging.Handler`
- Implement `__init__` to accept a `queue.Queue` parameter
- Implement `emit` method that formats the record and puts `(levelno, formatted_message)` tuple into queue
- Use `put_nowait()` to avoid blocking; catch `queue.Full` and silently drop messages

### Step 2: Add create_queue_handler factory function to logger.py
- Add `create_queue_handler(log_queue: queue.Queue) -> QueueHandler` function
- Set handler level to `logging.DEBUG` (capture all, filter in GUI)
- Use formatter with `"%(asctime)s [%(levelname)s] %(message)s"` format and `datefmt="%H:%M:%S"`
- Return configured handler

### Step 3: Add unit tests for QueueHandler
- Add `TestQueueHandler` class to `test_logger.py`
- Test `test_queue_handler_puts_messages()` - verify formatted messages are put into queue
- Test `test_queue_handler_handles_full_queue()` - verify no exception when queue is full
- Test `test_queue_handler_message_format()` - verify tuple contains `(levelno, formatted_string)`

### Step 4: Add unit tests for create_queue_handler
- Add `TestCreateQueueHandler` class to `test_logger.py`
- Test `test_create_queue_handler_returns_handler()` - verify returns `QueueHandler` instance
- Test `test_create_queue_handler_debug_level()` - verify handler level is DEBUG
- Test `test_create_queue_handler_format()` - verify timestamp format HH:MM:SS

### Step 5: Run tests to verify logger additions
- Run `uv run pytest app/tests/core/test_logger.py -v` to verify new tests pass
- Run `uv run mypy app/core/logger.py` to verify type hints

### Step 6: Update main.py window size for log viewer
- Change `self.geometry("500x300")` to `self.geometry("600x500")` to accommodate log viewer
- Change `self.resizable(False, False)` to `self.resizable(True, True)` to allow window resizing

### Step 7: Add log viewer frame to main.py GUI
- Add `import queue` at the top of the file
- Add `from core.logger import create_queue_handler` to imports
- Store reference to `main_frame` as `self.main_frame` for accessing later
- After the status label, add log viewer frame:
  - Create `self.log_frame = ctk.CTkFrame(self.main_frame)`
  - Pack with `fill="both", expand=True, pady=10`

### Step 8: Add log level dropdown to log viewer frame
- Create `self.log_level_var = ctk.StringVar(value="INFO")`
- Create `self.log_level_menu = ctk.CTkOptionMenu()`
  - Parent: `self.log_frame`
  - Values: `["DEBUG", "INFO", "WARNING", "ERROR"]`
  - Variable: `self.log_level_var`
  - Command: `self._on_log_level_change`
- Pack with `anchor="w", padx=5, pady=5`

### Step 9: Add log text area to log viewer frame
- Create `self.log_text = ctk.CTkTextbox()`
  - Parent: `self.log_frame`
  - Font: `("Courier", 10)` for monospace
  - State: `"disabled"` to prevent user editing
  - Height: `200` (will expand with frame)
- Pack with `fill="both", expand=True, padx=5, pady=5`

### Step 10: Initialize queue handler in __init__
- Create `self.log_queue: queue.Queue[tuple[int, str]] = queue.Queue(maxsize=1000)`
- Create `self.queue_handler = create_queue_handler(self.log_queue)`
- Add handler to root logger: `logging.getLogger().addHandler(self.queue_handler)`
- Start polling: `self._poll_log_queue()`

### Step 11: Implement _poll_log_queue method
- Get current filter level: `level_filter = getattr(logging, self.log_level_var.get())`
- Loop with `while True:` and `try/except queue.Empty: break`
- Get message: `level, msg = self.log_queue.get_nowait()`
- If `level >= level_filter`:
  - `self.log_text.configure(state="normal")`
  - `self.log_text.insert("end", msg + "\n")`
  - `self.log_text.see("end")` for auto-scroll
  - `self.log_text.configure(state="disabled")`
- Schedule next poll: `self.after(100, self._poll_log_queue)`

### Step 12: Implement _on_log_level_change method
- Add method stub with pass (filtering happens in `_poll_log_queue`)
- Add docstring explaining level filtering is done during poll

### Step 13: Clean up handler on destroy
- Override `destroy()` method (already exists)
- Before `super().destroy()`, remove handler: `logging.getLogger().removeHandler(self.queue_handler)`

### Step 14: Run full validation
- Run all tests: `uv run pytest app/tests/ -v`
- Run type checker: `uv run mypy app/`
- Run linter: `uv run ruff check app/`
- Run formatter: `uv run ruff format app/`

## Testing Strategy

### Unit Tests
- `QueueHandler` puts formatted messages into queue with correct tuple format
- `QueueHandler` silently drops messages when queue is full (no exception)
- `create_queue_handler` returns properly configured `QueueHandler`
- `create_queue_handler` sets DEBUG level on handler
- `create_queue_handler` uses HH:MM:SS timestamp format

### Integration Tests
Not applicable - GUI testing is limited in WSL environment. Focus on unit tests for the logger components which can be tested without GUI.

### Edge Cases
- Queue full (maxsize=1000) - messages should be dropped silently
- Rapid log messages - polling should handle multiple messages per cycle
- Log level filtering - only messages at or above selected level should display
- Application close - handler should be removed cleanly

### Playwright MCP Tests
Not applicable - this is a desktop GUI application, not a web application.

## Acceptance Criteria
1. GUI displays log viewer panel below the status label
2. Log text area uses monospace font (Courier)
3. Log text area is read-only (state="disabled")
4. Log level dropdown shows: DEBUG, INFO, WARNING, ERROR
5. Default log level is INFO
6. Messages are polled from queue every 100ms
7. Display auto-scrolls to latest entry
8. Terminal/stdout continues receiving all logs (no change to existing behavior)
9. All existing tests pass (476+ tests)
10. Type checking passes with mypy
11. Linting passes with ruff

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Run new logger tests specifically:
  - `uv run pytest app/tests/core/test_logger.py -v`
- Run all tests to validate zero regressions:
  - `uv run pytest app/tests/`
- Run type checker:
  - `uv run mypy app/`
- Run linter:
  - `uv run ruff check app/`
- Run formatter:
  - `uv run ruff format app/`
- Fix any auto-fixable issues:
  - `uv run ruff check app/ --fix`

## Notes
- **GUI Testing Limitation:** GUI testing is unreliable in WSL due to X server issues. Focus on unit testing the logger components (`QueueHandler`, `create_queue_handler`) which can be tested without the GUI.
- **File-based logging is primary:** The log viewer is secondary to file-based logging (US-2) for debugging hangs. During heavy computation, the GUI main loop blocks, so the log viewer won't update until computation completes. The debug file (created per extraction) remains the reliable source for debugging.
- **Queue size:** Using `maxsize=1000` provides a buffer while preventing unbounded memory growth. Messages are dropped if the queue fills (unlikely in normal operation).
- **No new dependencies:** This feature uses only Python standard library (`queue`) and existing CustomTkinter widgets.
