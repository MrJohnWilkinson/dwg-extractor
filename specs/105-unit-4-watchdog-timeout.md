# Chore: Add Watchdog Timeout Detection for Extraction Hang Diagnosis

## Chore Description

Add a threading-based watchdog timer mechanism to detect where hangs occur during DXF extraction. This is Unit 4 of the extractor lockup diagnostic investigation plan.

**Platform Consideration:** The original diagnostic plan (Step 5) suggested using `signal.SIGALRM` for timeout detection. However, this project runs on **WSL2 (Windows)** as noted in README.md. On Windows/WSL environments, `signal.SIGALRM` does not work reliably.

**Threading-based Alternative:** Instead of signals, use a `threading.Timer` watchdog that:
1. Runs a background thread with a configurable timer
2. Logs a warning with "DIAG: WATCHDOG" prefix if operations exceed the timeout
3. Continues execution (doesn't kill the operation) so we can gather more diagnostic information
4. Is cancellable when the operation completes normally

The watchdog should wrap the `write_excel()` call in `_extraction_worker()` since this is the suspected hang point based on previous diagnostic logging (Units 1-2 show `extract_blocks()` completes successfully but `write_excel()` never logs).

## Relevant Files

Use these files to resolve the chore:

- **`app/main.py`** - Contains the `DXFExtractorApp` class and `_extraction_worker()` method (lines 715-913) where the watchdog timer will be implemented. The `write_excel()` call is at lines 870-872. Already imports `threading` module (line 18).

- **`specs/102-unit-1-diagnostic-logging.md`** - Reference for DIAG logging pattern established in Unit 1 (uses "DIAG:" prefix for all diagnostic messages).

- **`specs/103-unit-2-memory-monitoring.md`** - Reference for Unit 2's memory monitoring addition to understand the diagnostic context.

- **`ai_output/089-extractor-lockup-diagnostic-plan.md`** - Contains the original diagnostic plan with Step 5 (Timeout Detection) that this unit implements with WSL2-compatible approach.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add `_watchdog_timer()` Method to DXFExtractorApp Class

Add a new method to the `DXFExtractorApp` class in `app/main.py` that creates a watchdog timer:

- Place the method after the `_abort_extraction()` method (around line 703) for logical grouping with extraction-related methods
- Method signature: `def _watchdog_timer(self, operation_name: str, timeout_seconds: int = 30) -> threading.Timer:`
- Implementation:
  ```python
  def _watchdog_timer(self, operation_name: str, timeout_seconds: int = 30) -> threading.Timer:
      """Create a watchdog timer that logs if operation takes too long.

      This is a diagnostic tool to help identify hang locations. The timer
      runs in a background thread and logs a warning if the operation
      exceeds the timeout. It does NOT kill the operation - this allows
      gathering more diagnostic information.

      Args:
          operation_name: Name of operation being monitored (for logging)
          timeout_seconds: Seconds before timeout warning (default 30)

      Returns:
          threading.Timer that must be cancelled when operation completes
      """
      def timeout_handler() -> None:
          self.logger.warning(
              f"DIAG: WATCHDOG - {operation_name} exceeded {timeout_seconds}s"
          )

      timer = threading.Timer(timeout_seconds, timeout_handler)
      timer.start()
      return timer
  ```

### Step 2: Wrap `write_excel()` Call with Watchdog Timer

In the `_extraction_worker()` method, wrap the `write_excel()` call (lines 870-872) with the watchdog timer:

- Add watchdog start before the `write_excel()` call
- Use try/finally to ensure watchdog is always cancelled
- Preserve existing DIAG logging around the call

Updated code structure (replacing lines 869-873):
```python
self.logger.debug("DIAG: About to call write_excel")
watchdog = self._watchdog_timer("write_excel", timeout_seconds=30)
try:
    excel_path = write_excel(
        extraction_result, self.selected_file_path, custom_output_path
    )
finally:
    watchdog.cancel()
self.output_excel_path = excel_path
```

### Step 3: Run Validation Commands

Execute the validation commands to ensure the chore is complete with zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

```bash
# 1. Type check the modified file
uv run mypy app/main.py

# 2. Lint check for code quality
uv run ruff check app/main.py

# 3. Format check
uv run ruff format --check app/main.py

# 4. Run main.py related tests
uv run pytest app/tests/core/test_main_settings_sync.py -v

# 5. Verify the DIAG logging pattern is consistent (should see WATCHDOG pattern)
grep -n "DIAG:" app/main.py | head -20

# 6. Verify threading.Timer is used correctly (grep for the new method)
grep -n "_watchdog_timer" app/main.py

# 7. Run full test suite to ensure no regressions
uv run pytest app/tests/core/ -v --tb=short
```

## Notes

- This is Unit 4 of the extractor lockup diagnostic investigation plan (following Units 1-3 in specs 102-104)
- All diagnostic logging uses the "DIAG:" prefix for easy identification and later removal
- The watchdog uses `self.logger.warning()` (not debug) so timeout alerts are visible in normal operation
- The 30-second default timeout is chosen because:
  - Normal Excel generation should complete in seconds
  - Long enough to not trigger false positives on moderately large files
  - Short enough to quickly identify true hangs
- The watchdog does NOT kill operations - it only logs. This is intentional to allow:
  - Gathering more diagnostic information after timeout
  - Testing if operation eventually completes
  - Avoiding data corruption from interrupted writes
- `threading.Timer` is part of Python's standard library, no additional dependencies needed
- The timer is cancelled in a `finally` block to ensure cleanup even if `write_excel()` raises an exception
- Platform: WSL2 (Ubuntu on Windows 11) - `signal.SIGALRM` not used due to Windows compatibility issues
- Previous commits: Unit 1 (dc80402), Unit 2 (fc5bc53), Unit 3 (44c30de)
