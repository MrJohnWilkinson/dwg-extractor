# Chore: Add Diagnostic Logging for Extraction Hang Investigation

## Chore Description

Add granular diagnostic logging to pinpoint the exact hang location in the DXF Block Extractor application. The app hangs after completing extraction on large DXF files (7M lines). Debug logs show extraction completing successfully with "Found 10 extraction issues" message, but no subsequent logs appear from `write_excel()`.

This diagnostic logging will help identify whether the hang occurs:
1. After `extract_blocks()` returns but before `write_excel()` is called
2. During the progress update callback
3. When computing the output path
4. At the entry point of `write_excel()`

## Relevant Files

Use these files to resolve the chore:

- **`app/main.py`** (lines ~816-851): Contains the `_run_extraction()` method where `extract_blocks()` is called and results are processed before calling `write_excel()`. Diagnostic logging needs to be added between the `extract_blocks()` return and the `write_excel()` call.

- **`app/core/extractor.py`** (lines ~1700-1731): Contains the result dictionary building and return statement at the end of `extract_blocks()`. Diagnostic logging needs to be added before building the result dictionary and before returning.

- **`app/core/logger.py`**: Reference file for understanding the logging patterns used in the application (uses `self.logger.debug()` in main.py and module-level `logger` in extractor.py).

## Step by Step Tasks

### Step 1: Add Diagnostic Logging in extractor.py

Add diagnostic logging in `app/core/extractor.py` around lines 1700-1731 before the result dictionary is built and before the return statement:

- Add `logger.debug("DIAG: Building result dictionary...")` before line 1708 (before the `result: ExtractionResult = {` assignment)
- Add `logger.debug(f"DIAG: Result dictionary built successfully")` after line 1729 (after the closing `}` of the result dictionary)
- Add `logger.debug(f"DIAG: nested_block_parents has {len(result['nested_block_parents'])} entries")` after the result dictionary is built
- Add `logger.debug("DIAG: About to return from extract_blocks")` immediately before the `return result` statement on line 1731

### Step 2: Add Diagnostic Logging in main.py

Add diagnostic logging in `app/main.py` after `extract_blocks()` returns (line 835) and before `write_excel()` is called (line 849):

- Add `self.logger.debug("DIAG: extract_blocks returned successfully")` immediately after line 835 (after the `extract_blocks()` call completes)
- Add `self.logger.debug(f"DIAG: block_counts has {len(extraction_result['block_counts'])} entries")` after the success log
- Add `self.logger.debug(f"DIAG: all_block_definitions has {len(extraction_result['all_block_definitions'])} entries")` after the block_counts log
- Add `self.logger.debug("DIAG: About to call _update_progress(0.7)")` before line 844 (before the `_update_progress(0.7, "Generating Excel...")` call)
- Add `self.logger.debug("DIAG: _update_progress(0.7) scheduled")` after line 844 (after the `_update_progress` call)
- Add `self.logger.debug("DIAG: About to call _get_output_path")` before line 847 (before `custom_output_path = self._get_output_path(input_path)`)
- Add `self.logger.debug(f"DIAG: output_path = {custom_output_path}")` after line 847 (after the `_get_output_path` call)
- Add `self.logger.debug("DIAG: About to call write_excel")` before line 849 (before the `excel_path = write_excel(...)` call)

### Step 3: Run Validation Commands

Execute validation commands to ensure the changes don't break existing functionality.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# Type check the modified files
uv run mypy app/main.py app/core/extractor.py

# Run linting on modified files
uv run ruff check app/main.py app/core/extractor.py

# Run extractor tests to ensure no regressions
uv run pytest app/tests/core/extractor/ -v

# Run a quick smoke test on the core extraction functionality
uv run pytest app/tests/core/extractor/test_extractor_core.py -v
```

## Notes

- All diagnostic log messages use the "DIAG:" prefix for easy identification and later removal
- Logging uses `debug` level so messages only appear when `DXF_EXTRACTOR_LOG_LEVEL=DEBUG` is set
- The diagnostic logs are designed to be temporary and should be removed once the hang issue is resolved
- The logging follows existing patterns: `self.logger.debug()` in main.py and module-level `logger.debug()` in extractor.py
- These logs will help identify if the hang occurs during:
  - Result dictionary construction in extractor.py
  - GUI progress update callback scheduling
  - Output path computation
  - Entry into write_excel() function
