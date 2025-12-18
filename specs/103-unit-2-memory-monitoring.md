# Chore: Add Memory Monitoring to Extraction Workflow

## Chore Description
Add memory monitoring to the extraction workflow to help diagnose potential memory pressure issues causing hangs on large DXF files (7M lines, 586 block definitions, 3585 insertions). This involves adding tracemalloc-based memory logging to `app/main.py` in the `_extract_blocks()` method that:
- Starts tracemalloc before calling `extract_blocks()`
- Logs current and peak memory usage after `extract_blocks()` returns (before `write_excel()`)
- Stops tracemalloc after logging
- Uses DIAG prefix for consistency with other diagnostic logging added in Unit 1
- Reports memory in MB format with one decimal place

## Relevant Files
Use these files to resolve the chore:

- **`app/main.py`** - Contains the `_extract_blocks()` method where memory monitoring will be added. The `extract_blocks()` call is at lines 816-835, and existing DIAG logging appears at lines 836-860. The tracemalloc import needs to be added to the imports section (around line 13-44).

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add tracemalloc Import
- Add `import tracemalloc` to the imports section of `app/main.py`
- Place it alphabetically with other stdlib imports (after `import threading`, before `from datetime import datetime`)

### Step 2: Add tracemalloc.start() Before extract_blocks()
- In the `_extract_blocks()` method, add `tracemalloc.start()` immediately before the `extract_blocks()` call
- Add it after the "Step 2: Extract comprehensive data" progress update (after line 814)
- Add a debug log: `self.logger.debug("DIAG: Starting memory trace")`

### Step 3: Add Memory Logging After extract_blocks() Returns
- After the `extract_blocks()` call completes (line 835) and before the existing DIAG logging (line 836)
- Get memory stats: `current, peak = tracemalloc.get_traced_memory()`
- Log with DIAG prefix using `self.logger.info()`:
  ```python
  self.logger.info(f"DIAG: Memory current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
  ```
- Use `self.logger.info()` (not debug) so memory stats are visible in normal operation

### Step 4: Stop tracemalloc After Logging
- Add `tracemalloc.stop()` immediately after the memory logging line
- This ensures tracemalloc doesn't continue consuming resources during Excel generation

### Step 5: Run Validation Commands
Execute the validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

```bash
# Type check to ensure tracemalloc usage is correct
uv run mypy app/main.py

# Lint check for code quality
uv run ruff check app/main.py

# Run main.py related tests (settings sync test covers main.py initialization)
uv run pytest app/tests/core/test_main_settings_sync.py -v

# Verify the DIAG logging pattern is consistent
grep -n "DIAG:" app/main.py
```

## Notes
- This is Unit 2 of a diagnostic investigation plan; Unit 1 (spec 102) added DIAG-prefixed logging to extractor.py and main.py
- The `tracemalloc` module is part of Python's standard library, no additional dependencies needed
- Using `self.logger.info()` instead of `debug()` ensures memory stats appear in normal extraction logs for diagnosis
- Memory is reported in MB with one decimal place for readability (e.g., "Memory current=45.3MB, peak=123.7MB")
- The tracemalloc overhead is minimal but we stop it promptly after logging to avoid any impact on Excel generation
- Previous commit for Unit 1: dc80402
