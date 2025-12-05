# Bug: Extraction stalls without progress indication during block analysis

## Bug Description
The extraction process appears to stall after processing approximately 100 out of 208 block definitions. User logs show a ~38 second gap between progress updates before the user aborted:

```
12:14:21.515 [INFO] Analyzing block definitions... 100/208
12:14:59.097 [INFO] User requested extraction abort
```

Expected behavior: Progress updates should occur at regular intervals (every 50 blocks or every ~5 seconds) with detailed information about which block is being analyzed and what operation is slow.

Actual behavior: Extraction appears frozen with no log output for 38+ seconds, leaving users unable to determine if the application is still working.

## Problem Statement
1. **Missing abort checkpoints in geometry functions**: The content zone detection (`_detect_content_zone`) and related functions (`_extract_line_cycles`, `_calculate_net_areas`) can take very long for complex blocks but have no abort checkpoints, meaning users cannot cancel during these operations.

2. **Insufficient logging granularity**: The extraction only logs progress every 50 blocks at INFO level. There's no DEBUG-level logging to identify which specific block or operation is slow.

3. **Default log level is INFO**: The GUI initializes with INFO log level, but users troubleshooting performance issues need DEBUG-level visibility by default to understand where time is being spent.

4. **No per-block timing visibility**: When a single block takes excessive time to analyze, there's no indication of which block is the culprit or which geometry operation is slow.

## Solution Statement
1. **Add DEBUG logging throughout geometry functions**: Add timing and progress logs to `_detect_content_zone`, `_extract_line_cycles`, and `_calculate_net_areas` to identify slow operations.

2. **Add per-block timing at DEBUG level**: Log the start/completion of each block's geometry analysis with timing information.

3. **Add abort checkpoints in geometry functions**: Pass abort_event through to geometry functions and check it at key points during expensive operations.

4. **Set default log level to DEBUG in GUI**: Change the default dropdown selection and initial log level from INFO to DEBUG as requested by the user.

5. **Add time-based progress logging**: In addition to every-50-blocks logging, log progress when more than 5 seconds have elapsed since last update.

## Steps to Reproduce
1. Load a DXF file with 200+ block definitions, some with complex geometry (many LINEs forming cycles, nested polylines)
2. Click Extract
3. Observe that after "Analyzing block definitions... 100/208", no further progress is shown for an extended period
4. User cannot determine if the extraction is stuck or just slow

## Root Cause Analysis
The root cause is that `_detect_content_zone` calls `_extract_line_cycles` which uses O(n²) adjacency graph building and O(n!) worst-case DFS cycle detection for blocks with many LINE entities. Subsequently, `_calculate_net_areas` performs O(n³) polygon containment checks.

For a block with ~100 LINE entities forming complex shapes, this can take tens of seconds per block, and there's:
1. No logging inside these functions to show progress
2. No abort checkpoints to allow cancellation
3. No indication of which block is being processed
4. INFO-level default hides all DEBUG logs that would show the internal operations

## Relevant Files
Use these files to fix the bug:

- `app/core/geometry.py` - Contains `_detect_content_zone`, `_extract_line_cycles`, `_calculate_net_areas` which need DEBUG logging for timing and progress, plus abort checkpoint support
- `app/core/extractor.py` - Contains the block analysis loop that needs per-block timing logs and needs to pass abort_event to geometry functions
- `app/main.py` - Contains GUI initialization where default log level needs to be changed from INFO to DEBUG
- `app/core/logger.py` - Already has `timed_block` context manager that can be used; no changes needed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update geometry.py with comprehensive DEBUG logging

Add DEBUG-level logging to geometry functions:

- Add timing logs to `_detect_content_zone`:
  - Log entry with block name context
  - Log timing for `_extract_closed_lwpolylines`
  - Log timing for `_extract_line_cycles`
  - Log timing for `_calculate_net_areas`
  - Log count of shapes found at each stage

- Add timing/progress logs to `_extract_line_cycles`:
  - Log number of LINE segments found
  - Log adjacency graph size
  - Log number of cycles found
  - Log timing for cycle detection

- Add timing/progress logs to `_calculate_net_areas`:
  - Log number of polygons being processed
  - Log progress during containment checks (every 10 polygons if > 20 total)

### Step 2: Add abort checkpoint support to geometry functions

- Update `_detect_content_zone` signature to accept optional `abort_event: threading.Event | None = None`
- Add abort checks after each major operation (after polyline extraction, after line cycle extraction, after net area calculation)
- Import `_check_abort` from extractor module or define local check function

### Step 3: Update extractor.py to pass abort_event to geometry and add per-block timing

- Update the call to `_detect_content_zone(block_def, bbox)` to include `abort_event` parameter
- Add DEBUG-level logging before each block's geometry analysis showing the block name
- Add timing log after each block completes (at DEBUG level)
- Add time-based progress logging: if more than 5 seconds since last INFO log, emit an INFO log even if not at the 50-block boundary
- Import `time` module if not already imported

### Step 4: Change default log level in GUI to DEBUG

In `app/main.py`:
- Change `self.current_log_level: int = logging.INFO` to `self.current_log_level: int = logging.DEBUG`
- Change `self.log_level_dropdown.set("INFO")` to `self.log_level_dropdown.set("DEBUG")`

### Step 5: Run validation tests

Execute the validation commands to ensure no regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to validate logging changes don't break functionality
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests to validate abort and timing changes
- `uv run pytest app/tests/ -v` - Run all tests to ensure no regressions
- `uv run mypy app/` - Ensure type checking passes with new optional parameters

## Notes
- The `timed_block` context manager from `logger.py` can be used for timing major operations
- Be careful not to create circular imports when sharing `_check_abort` - consider defining a simple local check in geometry.py if needed
- DEBUG logs should use f-strings for efficiency (only formatted when DEBUG level is active)
- The abort_event parameter should be optional with default None to maintain backwards compatibility
- Consider adding a constant for the time-based logging threshold (e.g., `PROGRESS_LOG_INTERVAL_SECONDS = 5`)
