# Feature: File-Based Debug Logging

## Feature Description
Add file-based debug logging capability to the DXF Block Extractor application that writes DEBUG-level logs to a timestamped file during extraction. This enables real-time monitoring via `tail -f` and provides a persistent log for post-extraction diagnosis without depending on the GUI.

The implementation includes:
- A `FlushingFileHandler` class that flushes after every emit for immediate disk writes
- A `MillisecondFormatter` for precise timestamps (HH:MM:SS.mmm format)
- A `create_debug_file_handler()` factory function
- Integration with the main application's extraction workflow
- Automatic cleanup of handlers after extraction completes

## User Story
As a user or developer
I want DEBUG logs written directly to a timestamped file during extraction
So that I can monitor progress via `tail -f` and diagnose issues without depending on the GUI

## Problem Statement
Currently, the application only logs to stdout via the existing `setup_logger()` function. This approach has limitations:
1. Logs are not persisted to disk for later analysis
2. Standard file handlers buffer writes, making `tail -f` unreliable for real-time monitoring
3. Users cannot easily review extraction logs after the fact
4. No millisecond-precision timestamps for performance analysis

## Solution Statement
Extend the existing logger module with:
1. `FlushingFileHandler` - A custom `logging.FileHandler` subclass that calls `flush()` after every `emit()` to ensure immediate disk writes
2. `MillisecondFormatter` - A custom formatter that provides HH:MM:SS.mmm timestamp format
3. `create_debug_file_handler()` - A factory function that creates a properly configured handler

Integrate with `main.py`:
1. Create a debug log file at extraction start: `{dxf_filename}_debug_{timestamp}.log`
2. Attach the handler to the root logger
3. Display the log file path in the GUI status
4. Clean up and close the handler after extraction completes

## Relevant Files
Use these files to implement the feature:

- `app/core/logger.py` - Existing logging module where `FlushingFileHandler`, `MillisecondFormatter`, and `create_debug_file_handler()` will be added
- `app/main.py` - Main GUI application where extraction workflow integration will be added
- `app/tests/core/test_logger.py` - Existing test file for logger module where new tests will be added

### New Files
No new files required - all changes extend existing files.

## Implementation Plan
### Phase 1: Foundation
Add the core logging classes and factory function to `app/core/logger.py`:
- Implement `FlushingFileHandler` class
- Implement `MillisecondFormatter` class
- Implement `create_debug_file_handler()` factory function

### Phase 2: Core Implementation
Add unit tests for the new logging components:
- Test `FlushingFileHandler` immediate write behavior
- Test `MillisecondFormatter` timestamp format
- Test `create_debug_file_handler()` configuration

### Phase 3: Integration
Integrate debug file logging with the main application:
- Add `debug_file_handler` instance variable to `DXFExtractorApp`
- Create handler at extraction start in `_extraction_worker()`
- Update status label with log filename
- Add cleanup in extraction finally block

## Step by Step Tasks

### Step 1: Add FlushingFileHandler class to logger.py
- Add `FlushingFileHandler` class that inherits from `logging.FileHandler`
- Override `emit()` method to call `super().emit()` followed by `self.flush()`
- Add proper docstring explaining the purpose (immediate visibility for `tail -f`)

### Step 2: Add MillisecondFormatter class to logger.py
- Add `MillisecondFormatter` class that inherits from `logging.Formatter`
- Override `formatTime()` method to return HH:MM:SS.mmm format
- Use `time.strftime()` for HH:MM:SS and `record.msecs` for milliseconds
- Add proper docstring

### Step 3: Add create_debug_file_handler() factory function to logger.py
- Add `create_debug_file_handler(file_path: str) -> logging.FileHandler` function
- Create `FlushingFileHandler` with mode='w' and encoding='utf-8'
- Set level to `logging.DEBUG`
- Set formatter to `MillisecondFormatter` with format `"%(asctime)s [%(levelname)s] %(message)s"`
- Return the configured handler
- Add proper docstring with Args and Returns sections

### Step 4: Update logger.py exports
- Ensure the new classes and function are properly exported
- Verify imports at the top of the file are complete

### Step 5: Add unit tests for FlushingFileHandler
- Add `test_flushing_file_handler_immediate_write()` test in `app/tests/core/test_logger.py`
- Use `tmp_path` fixture for temporary log file
- Create handler, attach to logger, write message
- Verify file contains message immediately without explicit flush call
- Clean up handler properly

### Step 6: Add unit tests for MillisecondFormatter
- Add `test_millisecond_formatter_time_format()` test
- Create formatter and format a log record
- Verify output matches HH:MM:SS.mmm pattern using regex
- Test edge cases (midnight, noon)

### Step 7: Add unit tests for create_debug_file_handler()
- Add `test_create_debug_file_handler_creates_file()` test
- Add `test_create_debug_file_handler_debug_level()` test
- Add `test_create_debug_file_handler_format()` test
- Verify handler is created with correct settings
- Verify log output format matches expected pattern

### Step 8: Integrate debug logging into main.py - Add instance variable
- Add `self.debug_file_handler: logging.FileHandler | None = None` in `__init__()`
- Add import for `create_debug_file_handler` from `core.logger`
- Add import for `datetime` from `datetime`

### Step 9: Integrate debug logging into main.py - Create handler at extraction start
- In `_extraction_worker()`, before processing, create the debug log file
- Generate filename: `{input_path.stem}_debug_{timestamp}.log` where timestamp is `%Y%m%d_%H%M%S`
- Create log path in same directory as input file
- Call `create_debug_file_handler()` with the log path
- Add handler to root logger with `logging.getLogger().addHandler()`
- Log the debug log path at INFO level
- Update status label (thread-safe) with log filename

### Step 10: Integrate debug logging into main.py - Cleanup handler
- In `_extraction_worker()` finally block, add cleanup code
- Check if `self.debug_file_handler` is not None
- Remove handler from root logger with `removeHandler()`
- Call `close()` on the handler
- Set `self.debug_file_handler = None`

### Step 11: Run validation commands
- Run `uv run pytest app/tests/` to verify all tests pass
- Run `uv run mypy app/` for type checking
- Run `uv run ruff check app/` for linting
- Run `uv run ruff format app/` for formatting
- Verify zero regressions (379+ tests should pass)

## Testing Strategy
### Unit Tests
- `test_flushing_file_handler_immediate_write()` - Verify writes are immediately visible on disk
- `test_flushing_file_handler_mode_write()` - Verify handler uses write mode (overwrites existing)
- `test_flushing_file_handler_encoding_utf8()` - Verify UTF-8 encoding is used
- `test_millisecond_formatter_time_format()` - Verify HH:MM:SS.mmm format
- `test_create_debug_file_handler_creates_handler()` - Verify factory returns FlushingFileHandler
- `test_create_debug_file_handler_debug_level()` - Verify DEBUG level is set
- `test_create_debug_file_handler_format()` - Verify timestamp format in output

### Integration Tests
- Manual testing: Run extraction, verify log file created in correct location
- Manual testing: Run `tail -f` on log file during extraction, verify real-time updates
- Manual testing: Verify log file path displayed in GUI status

### Edge Cases
- Test with DXF filename containing spaces
- Test with DXF filename containing special characters
- Test with read-only directory (should handle gracefully)
- Test handler cleanup on extraction error
- Test multiple extractions in sequence (verify no handler accumulation)

### Playwright MCP Tests
Not applicable - this feature is file I/O based and difficult to test via Playwright. Manual testing recommended for GUI integration.

## Acceptance Criteria
1. `FlushingFileHandler` class exists and flushes after every emit
2. `MillisecondFormatter` class exists and produces HH:MM:SS.mmm timestamps
3. `create_debug_file_handler(file_path)` factory function exists and returns configured handler
4. Log file created at extraction start with format: `{dxf_filename}_debug_{timestamp}.log`
5. DEBUG+ messages written to file with millisecond timestamps
6. Log file path displayed in GUI status during extraction
7. Handler removed and closed after extraction completes
8. All existing tests pass (379+)
9. New unit tests for logger components pass
10. mypy type checking passes
11. ruff linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Run tests to validate the feature works with zero regressions:
    - `uv run pytest app/tests/`
    - `uv run mypy app/`
    - `uv run ruff check app/`
    - `uv run ruff format app/`
    - `uv run ruff check app/ --fix`

## Notes
- The existing logger.py already imports `time` which is needed for `MillisecondFormatter`
- The existing logger.py uses `logging` module extensively - new classes follow the same patterns
- The main.py already uses threading for extraction - debug handler setup must be thread-safe
- Handler cleanup is critical to avoid file handle leaks on repeated extractions
- The log file is created in the same directory as the input DXF file for easy discovery
- Consider future enhancement: add option to customize log directory
