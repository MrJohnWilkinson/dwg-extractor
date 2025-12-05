# Chore: Diagnose 10-Minute Gap Between Extraction Complete and Excel Generation

## Chore Description
After implementing spec 023 (LINE segment threshold), the application appears to hang for approximately 10 minutes between extraction completion and Excel generation start. The logs show:

```
15:35:57.230 [INFO] Found 5 extraction issues (7 total insertions)
15:45:22.106 [INFO] Progress: 60% - Processing extraction results...
```

The ~9.5 minute gap occurs somewhere between:
1. extractor.py line 1363: `Found 5 extraction issues`
2. main.py line 360: `Progress: 60% - Processing extraction results...`

The following logs that SHOULD appear in this gap are MISSING:
- `[TIMING] extraction complete, returning result with X blocks` (extractor.py line 1386)
- `extract_blocks() returned, processing X blocks` (main.py line 346)

This suggests the worker thread is blocked somewhere between extractor.py line 1364 and main.py line 360, but we don't know exactly where.

This chore adds targeted logging to identify the exact location of the hang.

## Relevant Files
Use these files to resolve the chore:

- `app/core/extractor.py` - Add logging at key checkpoints between lines 1364-1389:
  - After building the result dict (line 1384)
  - Before and after the return statement
- `app/main.py` - Add logging in `_extraction_worker()` between lines 343-360:
  - Immediately after `extract_blocks()` call returns
  - Before each `self.after()` callback scheduling
  - After abort event checks
- `app/core/logger.py` - Verify file handler is flushing immediately with `handler.flush()` calls

### New Files
None - only modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add diagnostic logging after result dict construction in extractor.py
- Open `app/core/extractor.py`
- After line 1384 (end of result dict construction), add:
  ```python
  logger.debug("ExtractionResult dict constructed")
  ```
- This confirms dict construction completed

### Step 2: Add explicit flush after critical log messages in extractor.py
- In `app/core/extractor.py`, import `logging` module (already imported)
- After the TIMING log at line 1386-1388, add:
  ```python
  # Force flush all handlers to ensure log appears immediately
  for handler in logging.getLogger().handlers:
      handler.flush()
  ```
- This ensures the TIMING log is written to disk before returning

### Step 3: Add return-side logging in extractor.py
- Before the `return result` statement (line 1389), add:
  ```python
  logger.debug("About to return from extract_blocks()")
  ```
- After the try block but before except handlers, this isn't possible in Python
- Instead, consider wrapping the return in a function to add logging

### Step 4: Add immediate logging after extract_blocks() call in main.py
- Open `app/main.py`
- In `_extraction_worker()`, immediately after line 343-344 (`extraction_result = extract_blocks(...)`), add:
  ```python
  import time
  self.logger.info(f"[TIMING] extract_blocks() returned at {time.strftime('%H:%M:%S')}")
  ```
- This will help identify if the delay is inside extract_blocks() or after it returns

### Step 5: Add logging before self.after() calls in main.py
- Before each `self._update_progress()` call in `_extraction_worker()`, add:
  ```python
  self.logger.debug(f"About to schedule progress update: X%")
  ```
- This identifies if the delay is in scheduling vs callback execution

### Step 6: Add logging around abort event checks in main.py
- Before line 350 (first abort check after extraction), add:
  ```python
  self.logger.debug("Checking abort event after extraction")
  ```
- After line 354, add:
  ```python
  self.logger.debug("Abort check passed, continuing to results processing")
  ```

### Step 7: Add explicit handler flush calls in main.py
- After critical log messages in `_extraction_worker()`, add handler flush:
  ```python
  import logging
  for handler in logging.getLogger().handlers:
      handler.flush()
  ```
- This ensures messages appear in the log file immediately

### Step 8: Verify file handler flush behavior in logger.py
- Open `app/core/logger.py`
- In `create_debug_file_handler()`, verify the handler is configured for immediate write-through
- Consider adding `handler.flush()` after each emit by subclassing FileHandler:
  ```python
  class FlushingFileHandler(logging.FileHandler):
      def emit(self, record: logging.LogRecord) -> None:
          super().emit(record)
          self.flush()
  ```
- Use this class instead of `logging.FileHandler`

### Step 9: Run validation commands
- Execute all validation commands listed below to confirm changes work correctly

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests
- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests
- `uv run pytest app/tests/ -v --tb=short` - Run full test suite
- `uv run mypy app/core/extractor.py app/core/logger.py app/main.py` - Type check modified files
- `uv run ruff check app/core/extractor.py app/core/logger.py app/main.py` - Lint modified files

## Notes
- The primary goal is **diagnosis** - identifying WHERE the 10-minute hang occurs
- Once location is identified, a follow-up chore will address the root cause
- The explicit `flush()` calls ensure log messages are written to disk immediately, ruling out buffering issues
- Consider that the delay might be in:
  1. Building the ExtractionResult dict (unlikely but possible with large data)
  2. Python's return mechanism with large objects
  3. The `self.after(0, ...)` callback scheduling
  4. Main thread blocked, preventing scheduled callbacks from executing
  5. Some hidden lazy evaluation being triggered when result is accessed
- If logs show the delay is after `extract_blocks()` returns, investigate:
  - Thread scheduling issues
  - GIL contention
  - Memory pressure causing swap
- If logs show delay is inside `extract_blocks()` between lines 1364-1389, investigate:
  - Large data structure serialization
  - Hidden lazy evaluation
- The FlushingFileHandler subclass ensures every log message is immediately visible, even if Python's default buffering would otherwise delay it
