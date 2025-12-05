# Chore: Add Comprehensive Logging to Catch Extraction Hangs

## Chore Description
The application hangs after extraction completes (log shows `Found 5 extraction issues`) but before Excel writing begins. The log stops abruptly at `15:35:57.230 [INFO] Found 5 extraction issues (7 total insertions)` with no further output, indicating a gap in logging coverage. Additionally, the abort button becomes unresponsive and the application switches to "(Not Responding)" state.

This chore adds comprehensive logging to:
1. Identify exactly where hangs occur by adding logging at every major step
2. Add logging to Excel writing operations (DataFrame creation, sheet writing, formatting)
3. Add logging to GUI worker thread operations
4. Ensure abort event is checked during Excel writing operations
5. Add periodic abort checks to long-running Excel operations

The goal is to provide full visibility into the extraction and Excel writing pipeline so future hangs can be quickly diagnosed.

## Relevant Files
Use these files to resolve the chore:

- `app/core/extractor.py` - Add logging after the final `ExtractionResult` is constructed (line ~1368) to confirm function exit
- `app/core/excel_writer.py` - Add detailed logging throughout Excel generation:
  - Log entry/exit for each `_create_*_sheet()` function
  - Log iteration progress for large datasets
  - Add timing for each sheet creation
- `app/core/excel_formatting.py` - Add logging for each formatting operation
- `app/main.py` - Add logging to `_extraction_worker()`:
  - Log immediately after `extract_blocks()` returns
  - Log before each progress update
  - Log before `write_excel()` call
  - Add abort checks between major steps

### New Files
None required - only modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add logging after ExtractionResult construction in extractor.py
- Open `app/core/extractor.py`
- After the `ExtractionResult` dict is constructed (line ~1384), add:
  ```python
  logger.info(f"[TIMING] extraction complete, returning result with {len(block_counts)} blocks")
  ```
- This confirms that `extract_blocks()` is actually returning and not hanging before return

### Step 2: Add logging to _extraction_worker in main.py
- Open `app/main.py`
- After `extract_blocks()` call returns (line ~333), add:
  ```python
  self.logger.info(f"extract_blocks() returned, processing {len(extraction_result['block_counts'])} blocks")
  ```
- Before the empty results check (line ~339), add:
  ```python
  self.logger.debug("Checking for empty extraction results...")
  ```
- Before `write_excel()` call (line ~347), add:
  ```python
  self.logger.info("Starting Excel file generation...")
  ```
- After `write_excel()` returns (line ~348), add:
  ```python
  self.logger.info(f"Excel file generated: {excel_path}")
  ```

### Step 3: Add abort checks to _extraction_worker in main.py
- In `_extraction_worker()`, add abort event checks between major steps
- After extract_blocks returns, check abort:
  ```python
  if self.abort_event and self.abort_event.is_set():
      self.logger.info("Abort detected after extraction, skipping Excel generation")
      return
  ```
- Before write_excel call, check abort again
- This ensures abort works even after extraction completes

### Step 4: Add comprehensive logging to excel_writer.py sheet creation functions
- Open `app/core/excel_writer.py`
- For each `_create_*_sheet()` function, add:
  - Entry log with data size: `logger.debug(f"Starting {sheet_name}: {len(data)} items to process")`
  - Progress logging every 100 items for large datasets
  - Exit log with timing: `logger.debug(f"Completed {sheet_name} in {elapsed:.3f}s")`
- In `write_excel()`:
  - Log before and after each sheet creation call
  - Log before workbook load for formatting
  - Log before and after each format function call
  - Log before final save

### Step 5: Add iteration logging to large dataset processing in excel_writer.py
- In `_create_block_analysis_sheet()` (line ~398-419):
  - Add progress logging every 100 block-layer pairs processed
- In `_create_block_geometry_analysis_sheet()` (line ~542-679):
  - Add progress logging every 100 rows processed
  - Log slow operations (e.g., scale variance calculations)
- In `_create_annotations_analysis_sheet()` (line ~730-745):
  - Add progress logging every 100 annotations
- In `_create_color_analysis_sheet()` (line ~782-801):
  - Add progress logging every 100 records

### Step 6: Add logging to excel_formatting.py
- Open `app/core/excel_formatting.py`
- Add entry/exit logging for each `_format_*_sheet()` function
- Add logging for slow operations:
  - Auto-filter creation
  - Column width adjustment
  - Color sample fill operations (can be slow with many rows)
- Example:
  ```python
  logger.debug(f"Formatting {sheet_name}: {ws.max_row} rows, {ws.max_column} columns")
  ```

### Step 7: Add timed_block context manager usage for major operations
- Import `timed_block` from `core.logger` in `excel_writer.py` and `main.py`
- Wrap major operations in `timed_block` for automatic timing:
  ```python
  with timed_block("Excel generation", logger, logging.INFO):
      excel_path = write_excel(extraction_result, self.selected_file_path)
  ```
- Use `timed_block` for each sheet creation in `write_excel()`

### Step 8: Add GUI thread safety logging
- In `main.py`, log thread information for debugging:
  ```python
  import threading
  self.logger.debug(f"Worker thread: {threading.current_thread().name}")
  ```
- Log before each `self.after()` call to help diagnose GUI freezes
- Add logging to `_update_progress()` to track if UI updates are blocking

### Step 9: Run validation commands
- Execute all validation commands listed below to confirm changes work correctly

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests to ensure logging doesn't break functionality
- `uv run pytest app/tests/core/excel_writer/ -v` - Run Excel writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run Excel formatting tests
- `uv run pytest app/tests/ -v --tb=short` - Run full test suite for regressions
- `uv run mypy app/core/extractor.py app/core/excel_writer.py app/core/excel_formatting.py app/main.py` - Type check modified files
- `uv run ruff check app/core/extractor.py app/core/excel_writer.py app/core/excel_formatting.py app/main.py` - Lint modified files

## Notes
- The logging additions are primarily DEBUG level to avoid cluttering INFO output during normal operation
- Use INFO level for major phase transitions (extraction complete, Excel generation start/complete)
- Use DEBUG level for detailed progress within phases
- The `timed_block` context manager provides automatic timing without manual start/end tracking
- Abort checks are added between major steps but NOT during file I/O (which should be fast)
- The "(Not Responding)" state occurs when the GUI thread is blocked - this logging will help identify if the worker thread is blocking on GUI updates
- Consider that pandas DataFrame operations can be slow for large datasets - logging will help identify if this is the cause
- The abort event checks in `_extraction_worker` ensure the user can cancel even after extraction completes but before Excel writing
