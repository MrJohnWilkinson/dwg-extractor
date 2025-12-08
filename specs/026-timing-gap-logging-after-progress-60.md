# Chore: Add Logging to Timing Gap After 60% Progress

## Chore Description
After implementing spec 025 (diagnostic logging), we identified a timing gap of ~8 minutes occurring between the 60% progress update and the "Checking for empty extraction results" log:

```
16:07:42.176 [INFO] extract_blocks() returned, processing 156 blocks
16:07:42.176 [DEBUG] Calling _update_progress for step 4 (Processing results)
16:07:42.176 [DEBUG] Scheduling UI update via self.after(): 60%
16:16:25.138 [DEBUG] Checking for empty extraction results...
```

The gap is happening in `app/main.py` between:
- Line 369: `self._update_progress(0.6, "Processing extraction results...")`
- Line 373: `self.logger.debug("Checking for empty extraction results...")`

Since there are only 4 lines of code between these two log statements and no visible operations, this suggests either:
1. The `_update_progress` call itself is blocking (waiting for main thread)
2. There's hidden work happening that we're not logging
3. The worker thread is being starved/blocked

This chore adds targeted logging between these specific lines to pinpoint the exact source of the delay.

## Relevant Files
Use these files to resolve the chore:

- `app/main.py` - Add logging between lines 367-373 in `_extraction_worker()`:
  - After `_update_progress(0.6, ...)` call returns
  - Before and after `self.logger.debug("Progress 60% scheduled, continuing")`
  - Add timestamps with millisecond precision to measure actual delays

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add detailed timing log after _update_progress(0.6) returns
- Open `app/main.py`
- In `_extraction_worker()`, after line 369 (`self._update_progress(0.6, "Processing extraction results...")`), the current code has:
  ```python
  self.logger.debug("Progress 60% scheduled, continuing")
  ```
- Replace this with more detailed timing information:
  ```python
  self.logger.debug(f"[TIMING] Progress 60% scheduled at {time.strftime('%H:%M:%S.%f')[:-3]}, continuing worker thread")
  ```
- The `time` module is already imported at line 19

### Step 2: Add logging before the empty results check
- Before line 373 (`self.logger.debug("Checking for empty extraction results...")`), add:
  ```python
  self.logger.debug(f"[TIMING] Worker thread reached empty check at {time.strftime('%H:%M:%S.%f')[:-3]}")
  ```
- Note: `time.strftime('%H:%M:%S.%f')` won't work for microseconds with time module
- Instead use:
  ```python
  from datetime import datetime
  self.logger.debug(f"[TIMING] Worker thread reached empty check at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
  ```
- The `datetime` module is already imported at line 20

### Step 3: Add a loop-based timing diagnostic between the two points
- To identify if the thread is actually blocked or if it's something else, add:
  ```python
  # Timing diagnostic: log every second until we proceed
  check_start = time.perf_counter()
  self.logger.debug(f"[TIMING] Starting post-progress-60 timing at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
  ```
- After line 370, add these diagnostic lines to create detailed timestamps:
  ```python
  # Timing checkpoint 1
  self.logger.debug(f"[TIMING] Checkpoint 1: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

  # Timing checkpoint 2
  self.logger.debug(f"[TIMING] Checkpoint 2: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
  ```

### Step 4: Implement precise elapsed time measurement
- Wrap the section between progress 60% and the empty check with elapsed time measurement:
  - Before `_update_progress(0.6, ...)`:
    ```python
    step4_start = time.perf_counter()
    self.logger.debug(f"[TIMING] Step 4 start: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    ```
  - After `_update_progress(0.6, ...)` returns:
    ```python
    step4_progress_done = time.perf_counter()
    self.logger.debug(f"[TIMING] _update_progress(0.6) returned after {step4_progress_done - step4_start:.3f}s")
    ```
  - Before the empty check:
    ```python
    step4_elapsed = time.perf_counter() - step4_start
    self.logger.debug(f"[TIMING] Step 4 total elapsed before empty check: {step4_elapsed:.3f}s")
    ```

### Step 5: Apply the complete set of changes to main.py
- The complete modified section (lines ~365-378) should look like:
  ```python
  # Step 4: Process results
  step4_start = time.perf_counter()
  self.logger.debug(f"[TIMING] Step 4 start: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
  self.logger.debug(
      "About to schedule progress update: 60% (Processing results)"
  )
  self._update_progress(0.6, "Processing extraction results...")
  step4_progress_done = time.perf_counter()
  self.logger.debug(f"[TIMING] _update_progress(0.6) returned after {step4_progress_done - step4_start:.3f}s at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

  # Check for empty results
  step4_elapsed = time.perf_counter() - step4_start
  self.logger.debug(f"[TIMING] Step 4 elapsed before empty check: {step4_elapsed:.3f}s at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
  self.logger.debug("Checking for empty extraction results...")
  ```

### Step 6: Run validation commands
- Execute all validation commands listed below to confirm changes work correctly

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests
- `uv run pytest app/tests/ -v --tb=short` - Run full test suite
- `uv run mypy app/main.py` - Type check modified file
- `uv run ruff check app/main.py` - Lint modified file

## Notes
- The goal is to capture precise timestamps showing when each line executes
- If `_update_progress(0.6)` returns immediately (within milliseconds), the delay is elsewhere
- If `_update_progress(0.6)` blocks for ~8 minutes, the issue is in the `self.after()` call or main thread blocking
- The `time.perf_counter()` provides high-resolution timing for measuring durations
- The `datetime.now().strftime()` provides human-readable wall-clock timestamps for correlation with other logs
- Consider that `self.after(0, callback)` should return immediately in tkinter - it schedules the callback but doesn't wait for it
- If the worker thread is blocked despite `self.after()` returning, investigate potential GIL issues or main thread blocking operations
