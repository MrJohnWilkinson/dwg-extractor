# Extractor Application Lockup Diagnostic Plan

## Executive Summary

The DXF Block Extractor app hangs after completing extraction on `SP-GF-EX-4154.dxf` (7M lines). The debug log shows extraction completing successfully ("Found 10 extraction issues") but no subsequent logs from `write_excel()`. This plan outlines diagnostic steps to identify the root cause without making permanent code changes.

## Table Summary

| Phase | Location | Last Known Log | Next Expected Log | Hypothesis |
|-------|----------|----------------|-------------------|------------|
| Extraction | `extractor.py:1704` | "Found 10 extraction issues" | (none in extractor) | Completes OK |
| Result Build | `extractor.py:1708-1729` | (no logging) | (none) | Possible slowdown in dict comprehension |
| Progress Update | `main.py:844` | (via tkinter after) | "Progress: 70%" | May not execute if main thread blocked |
| Excel Write | `excel_writer.py:369` | NEVER REACHED | "Starting multi-sheet..." | Hang occurs before this |

## Relevant Files

- **`app/main.py:714-892`** - `_extraction_worker()` background thread that calls `extract_blocks()` then `write_excel()`
- **`app/core/extractor.py:1700-1731`** - End of `extract_blocks()` where result dict is built and returned
- **`app/core/excel_writer.py:325-455`** - `write_excel()` function that never logs its first message
- **`app/core/excel_writer.py:1024-1322`** - `_create_all_blocks_sheet()` with O(n^2) complexity (potential future issue)
- **`app/core/logger.py`** - Logging infrastructure with `FlushingFileHandler`
- **`app/tests/assets/samples/SP-GF-EX-4154.dxf`** - 7,030,564 line test file

## Root Cause Hypotheses

### Hypothesis 1: Memory Pressure / GC Pause (HIGH PROBABILITY)
The extraction produces large data structures. Building the return dictionary or passing it to `write_excel()` may trigger garbage collection that takes extremely long due to memory pressure.

**Evidence:**
- 7M line DXF file
- 586 block definitions, 3585 insertions
- 181,031 lines of debug logging generated
- No error logged, just silence

### Hypothesis 2: Blocking on `self.after()` (MEDIUM PROBABILITY)
The `_update_progress()` call at line 844 uses `self.after(0, ...)` to schedule UI updates. If the tkinter main thread is overwhelmed processing 181K log messages in the queue, callbacks may be severely delayed.

**Evidence:**
- Queue handler has `maxsize=1000` and drops messages when full
- Main thread must process log viewer updates
- Progress logging happens in `_update_progress_ui` on main thread

### Hypothesis 3: Large Data Structure Operations (MEDIUM PROBABILITY)
The dict comprehension `{k: sorted(list(v)) for k, v in nested_block_parents.items()}` at line 1726-1727 converts sets to sorted lists. With many nested relationships, this could be expensive.

**Evidence:**
- No logging between "Found issues" and return statement
- Unknown size of `nested_block_parents` dictionary

### Hypothesis 4: File Logger Level Configuration (LOW PROBABILITY)
The `core.excel_writer` logger is not in the list of loggers explicitly set to DEBUG in `_extraction_worker()`, but INFO level messages should still propagate.

**Evidence:**
- File handler set to DEBUG level (accepts all)
- First log in `write_excel()` is INFO level
- Should work based on logging configuration

## Diagnostic Investigation Plan

### Step 1: Add Diagnostic Logging

Add granular logging to pinpoint exact hang location.

**File: `app/main.py` around line 838-850:**
```python
# DIAGNOSTIC: Add after line 836 (after extract_blocks returns)
self.logger.info("DIAG: extract_blocks returned successfully")
self.logger.info(f"DIAG: block_counts has {len(extraction_result.get('block_counts', {}))} entries")
self.logger.info(f"DIAG: all_block_definitions has {len(extraction_result.get('all_block_definitions', {}))} entries")

# Check for empty results
if not extraction_result["block_counts"]:
    ...

# DIAGNOSTIC: Add before line 844
self.logger.info("DIAG: About to call _update_progress(0.7)")

# Step 3: Generate Excel
self._update_progress(0.7, "Generating Excel...")

# DIAGNOSTIC: Add after line 844
self.logger.info("DIAG: _update_progress scheduled")

# Get custom output path based on settings
# DIAGNOSTIC: Add before line 847
self.logger.info("DIAG: About to call _get_output_path")
custom_output_path = self._get_output_path(input_path)
self.logger.info(f"DIAG: output_path = {custom_output_path}")

# DIAGNOSTIC: Add before line 849
self.logger.info("DIAG: About to call write_excel")
excel_path = write_excel(...)
```

**File: `app/core/extractor.py` around line 1700-1731:**
```python
# DIAGNOSTIC: Add before line 1707
logger.info("DIAG: Building result dictionary...")

# Return comprehensive result
result: ExtractionResult = {
    ...
}

# DIAGNOSTIC: Add after result dict, before return
logger.info("DIAG: Result dictionary built successfully")
logger.info(f"DIAG: nested_block_parents has {len(result.get('nested_block_parents', {}))} entries")

return result
```

### Step 2: Monitor Memory Usage

Run extraction with memory monitoring:

```bash
# Option A: Using /usr/bin/time
/usr/bin/time -v uv run python app/main.py 2>&1 | tee memory_log.txt

# Option B: Add memory logging
# Add to _extraction_worker after extract_blocks returns:
import tracemalloc
tracemalloc.start()
# ... extraction call ...
current, peak = tracemalloc.get_traced_memory()
self.logger.info(f"DIAG: Memory current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
tracemalloc.stop()
```

### Step 3: Profile the Code Path

Run with cProfile to identify bottlenecks:

```bash
uv run python -m cProfile -o profile.out app/main.py
# After hang/completion, analyze:
uv run python -c "import pstats; p = pstats.Stats('profile.out'); p.sort_stats('cumulative').print_stats(30)"
```

### Step 4: Test with Reduced Data

Create a truncated version of the DXF file:
```bash
head -100000 app/tests/assets/samples/SP-GF-EX-4154.dxf > app/tests/assets/samples/SP-GF-EX-4154-small.dxf
```
Test if the smaller file processes successfully to confirm size-related issue.

### Step 5: Add Timeout Detection

Add a watchdog timer to detect where the hang occurs:

```python
# In _extraction_worker, wrap suspect sections:
import signal

def timeout_handler(signum, frame):
    self.logger.error("DIAG: TIMEOUT - operation took too long")
    raise TimeoutError("Operation timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout
try:
    excel_path = write_excel(...)
finally:
    signal.alarm(0)  # Cancel alarm
```

### Step 6: Check Thread State (if still hung)

If app is hung, attach debugger or use:
```bash
# Get thread dump for hung Python process
kill -SIGUSR1 <pid>
# Or use py-spy
py-spy dump --pid <pid>
```

## Diagnostic Execution Order

1. **First**: Add Step 1 logging and re-run extraction
2. **Based on results**:
   - If "DIAG: About to call write_excel" appears but "Starting multi-sheet..." doesn't: Issue is in `write_excel()` entry
   - If "DIAG: Result dictionary built" doesn't appear: Issue is in dict comprehension
   - If "DIAG: extract_blocks returned" doesn't appear: Issue is in extractor return
3. **Then**: Add memory monitoring (Step 2) to the identified problem area

## Simple List Summary

- Last successful log: "Found 10 extraction issues" at 06:53:11.815
- Expected next log ("Starting multi-sheet Excel file generation") never appears
- Hang occurs between `extract_blocks()` return and `write_excel()` first log
- Most likely cause: Memory pressure or large data structure operations
- Add diagnostic logging to narrow down exact hang location
- Monitor memory usage during extraction
