# Chore: File-Based DEBUG Logging

## Chore Description
Add file-based DEBUG logging that writes directly to a timestamped log file during extraction, enabling real-time monitoring via `tail -f` for users experiencing slow or stuck extractions.

**User Story:**
As a DXF Block Extractor user experiencing slow or stuck extractions, I want DEBUG logs written directly to a timestamped file in real-time during extraction, so that I can monitor progress, identify where extraction stalls, and share log files with an AI agent for diagnosis without waiting for extraction to complete.

**Acceptance Criteria:**
1. When extraction starts, a log file is created: `{dxf_filename}_debug_{timestamp}.log`
2. DEBUG messages are written immediately to file (no queuing/buffering)
3. Log file path is displayed in GUI at extraction start
4. File contains all DEBUG, INFO, WARNING, ERROR messages with timestamps
5. User can `tail -f` the log file externally for live monitoring
6. Log file persists regardless of extraction success, failure, or abort

**In Scope:**
- Create file handler at extraction start, write DEBUG+ logs directly to disk
- Timestamped log entries matching current format: `HH:MM:SS.mmm [LEVEL] message`
- Log file created in same directory as output Excel
- Display log file path in GUI status area when extraction begins
- File handler uses write-through (no Python buffering) for immediate visibility
- Existing GUI log viewer unchanged (continues showing INFO+ from queue)
- Log file includes all geometry timing, block names, polygon counts already in DEBUG

**Out of Scope:**
- Modifications to GUI log viewer polling or queue mechanism
- Changes to logging levels displayed in GUI dropdown
- New logging statements (existing DEBUG coverage is sufficient)
- Log rotation or cleanup of old log files
- In-app log file viewer or tail functionality
- Algorithm optimization (separate effort)
- JSON structured output (file is plain text log format)

## Relevant Files
Use these files to resolve the chore:

- `app/core/logger.py` - Central logging configuration module. Add new function to create a file handler with write-through mode and DEBUG level. Contains existing `setup_logger()`, `create_queue_handler()`, and `set_all_logger_levels()` functions.
- `app/main.py` - GUI application entry point. Modify `_extract_blocks()` and `_extraction_worker()` methods to create file handler at extraction start, display log file path in status, and clean up handler after extraction completes.
- `app/core/constants.py` - Application constants. Add new message constant for displaying log file path in GUI status.

### New Files
None - all changes are modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add file handler creation function to logger.py

Add a new function `create_debug_file_handler()` to `app/core/logger.py` that:
- Takes a file path as parameter
- Creates a `logging.FileHandler` with the specified path
- Sets level to `logging.DEBUG` to capture all messages
- Uses the same text format as existing handlers: `%(asctime)s [%(levelname)s] %(message)s` with millisecond timestamps
- Configures write-through mode (no buffering) using `delay=False` and opening with `mode='w'` plus setting `handler.stream.reconfigure(write_through=True)` or alternatively using `handler.stream = open(path, 'w', buffering=1)` for line buffering
- Returns the configured handler

```python
def create_debug_file_handler(file_path: str) -> logging.FileHandler:
    """
    Create a FileHandler for DEBUG logging with write-through mode.

    Creates a file handler that writes all DEBUG+ log messages directly to disk
    with no buffering, enabling real-time monitoring via `tail -f`.

    Args:
        file_path: Full path to the log file to create

    Returns:
        A configured FileHandler with DEBUG level and write-through enabled

    Examples:
        >>> handler = create_debug_file_handler('/path/to/extraction.log')
        >>> logging.getLogger().addHandler(handler)
        # Messages are immediately visible in the file
    """
    # Create handler - use 'w' mode to overwrite any existing file
    handler = logging.FileHandler(file_path, mode='w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)

    # Use same timestamp format as GUI: HH:MM:SS.mmm
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    # Add milliseconds manually since datefmt doesn't support %f
    class MillisecondFormatter(logging.Formatter):
        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
            ct = self.converter(record.created)
            if datefmt:
                s = time.strftime(datefmt, ct)
            else:
                s = time.strftime("%H:%M:%S", ct)
            return f"{s}.{int(record.msecs):03d}"

    handler.setFormatter(MillisecondFormatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    # Force immediate flush after each write
    handler.stream.reconfigure(write_through=True)

    return handler
```

Note: The `stream.reconfigure(write_through=True)` approach requires Python 3.11+. For cross-version compatibility, use line buffering by reopening the stream:
```python
# Close the default stream and reopen with line buffering
handler.stream.close()
handler.stream = open(file_path, 'w', encoding='utf-8', buffering=1)
```

### Step 2: Add constant for log file status message

Add a new constant to `app/core/constants.py` for the status message showing log file path:

```python
# Log file messages
MSG_LOG_FILE_CREATED: str = "Debug log: {}"
```

### Step 3: Add log file path instance variable to main.py

In `DXFExtractorApp.__init__()`, add instance variable to track the current debug log file handler:

```python
# Debug log file state
self.debug_file_handler: logging.Handler | None = None
```

### Step 4: Generate log file path and create handler at extraction start

Modify `_extract_blocks()` in `app/main.py` to:
1. Generate the log file path based on DXF filename and timestamp
2. Create the debug file handler
3. Add handler to root logger to capture all application logs
4. Update status to show log file path

Add this logic after creating the abort event and before updating the progress bar:

```python
def _extract_blocks(self) -> None:
    """Handle extract button click - start extraction process."""
    # ... existing validation code ...

    # Create new abort event for this extraction
    self.abort_event = threading.Event()

    # Create debug log file
    if self.selected_file_path:
        from datetime import datetime
        from pathlib import Path
        from core.logger import create_debug_file_handler

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = Path(self.selected_file_path)
        log_filename = f"{input_path.stem}_debug_{timestamp}.log"
        log_path = input_path.parent / log_filename

        # Create and attach file handler
        self.debug_file_handler = create_debug_file_handler(str(log_path))
        logging.getLogger().addHandler(self.debug_file_handler)

        # Store path for status display
        self.debug_log_path = str(log_path)
        self.logger.info(f"Debug log file created: {self.debug_log_path}")

    # ... rest of existing code ...
```

### Step 5: Display log file path in GUI status

Update the status label to show the log file path when extraction starts. In `_extract_blocks()`, after creating the file handler, update the status:

```python
# Update status to show log file path
from core.constants import MSG_LOG_FILE_CREATED
self.status_label.configure(text=MSG_LOG_FILE_CREATED.format(log_filename))
```

### Step 6: Clean up file handler after extraction completes

Modify `_restore_ui_after_extraction()` in `app/main.py` to remove and close the debug file handler:

```python
def _restore_ui_after_extraction(self) -> None:
    """Restore UI state after extraction completes or is aborted."""
    # Remove and close debug file handler
    if self.debug_file_handler is not None:
        logging.getLogger().removeHandler(self.debug_file_handler)
        self.debug_file_handler.close()
        self.debug_file_handler = None

    # ... rest of existing code ...
```

### Step 7: Add import for create_debug_file_handler

Update the import statement in `app/main.py` to include the new function:

```python
from core.logger import create_queue_handler, create_debug_file_handler, set_all_logger_levels, setup_logger
```

### Step 8: Initialize debug_log_path instance variable

Add `self.debug_log_path: str | None = None` in `DXFExtractorApp.__init__()` alongside the handler variable.

### Step 9: Run validation commands

Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests to validate the new file handler function
- `uv run pytest app/tests/ -v` - Run all tests to validate no regressions
- `uv run mypy app/` - Run type checking to ensure no type errors introduced
- `uv run ruff check app/` - Run linting to ensure code quality

Manual validation (requires GUI):
1. Run `bash scripts/start.sh`
2. Select a DXF file and click Extract
3. Verify status shows "Debug log: {filename}_debug_{timestamp}.log"
4. In a separate terminal, run `tail -f {path_to_log_file}`
5. Verify DEBUG messages appear in real-time in the log file
6. Verify log file contains timestamps in HH:MM:SS.mmm format
7. Verify log file persists after extraction completes (success or abort)
8. Verify log file is in same directory as the selected DXF file

## Notes
- The file handler uses line buffering (`buffering=1`) to ensure each log message is written immediately to disk without waiting for a buffer to fill
- The log file is created in the same directory as the input DXF file (same location where the output Excel file will be created)
- The handler is added to the root logger to capture logs from all modules (extractor, geometry, excel_writer, etc.)
- The handler is removed and closed after extraction to avoid file handle leaks and allow subsequent extractions to create new log files
- The timestamp format matches the existing GUI log viewer format for consistency
- This implementation does not modify the GUI log viewer behavior - it continues to poll the queue and display messages based on the dropdown selection
