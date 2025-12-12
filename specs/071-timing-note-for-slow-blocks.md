# Chore: Add [TIMING] Note for Slow Blocks

## Chore Description
Add a `[TIMING]` log message just before `[BLOCK END]` when block processing takes more than 3 seconds. This provides a quick visual indicator in the logs for slow blocks that need attention, without requiring users to parse the timing from the `[BLOCK END]` message.

The expected log output for a slow block would be:
```
[BLOCK START] 'SlowBlockName'
... processing logs ...
[TIMING] Block 'SlowBlockName' took 5.234s (>3s threshold)
[BLOCK END] 'SlowBlockName' (5.234s)
```

For blocks that complete in under 3 seconds, no `[TIMING]` message is logged.

## Relevant Files
Use these files to resolve the chore:

- **app/core/extractor.py** (lines 1232-1301) - Contains the block processing loop where `[BLOCK START]` and `[BLOCK END]` are logged. This is where the timing check and new log message must be added.
- **app/tests/core/extractor/test_extractor_core.py** - Contains tests for the extractor module; add a test to verify the `[TIMING]` note appears for slow blocks.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Timing Threshold Constant
- Open `app/core/extractor.py`
- Add a constant at the top of the file (near other constants or imports): `SLOW_BLOCK_THRESHOLD_SECONDS = 3.0`
- This makes the threshold configurable and self-documenting

### Step 2: Add [TIMING] Log Message for Slow Blocks
- In `app/core/extractor.py`, locate line ~1299-1301 where block timing is calculated
- Current code:
  ```python
  # Log block processing end with timing
  block_duration = time.perf_counter() - block_start
  logger.info(f"[BLOCK END] '{effective_name}' ({block_duration:.3f}s)")
  ```
- Modify to add a `[TIMING]` log message before `[BLOCK END]` when duration exceeds threshold:
  ```python
  # Log block processing end with timing
  block_duration = time.perf_counter() - block_start
  if block_duration > SLOW_BLOCK_THRESHOLD_SECONDS:
      logger.info(f"[TIMING] Block '{effective_name}' took {block_duration:.3f}s (>3s threshold)")
  logger.info(f"[BLOCK END] '{effective_name}' ({block_duration:.3f}s)")
  ```

### Step 3: Add Unit Test for [TIMING] Note
- Open `app/tests/core/extractor/test_extractor_core.py`
- Add a test that verifies `[TIMING]` appears for slow blocks (mocking time or using a large test file)
- Since real slow processing is hard to test, use `unittest.mock.patch` to mock `time.perf_counter()` to simulate a 4-second block duration
- Test should verify:
  1. `[TIMING]` message contains the block name
  2. `[TIMING]` message appears before `[BLOCK END]`
  3. `[TIMING]` includes the duration
- Also add a negative test that verifies `[TIMING]` does NOT appear for fast blocks (<3s)

### Step 4: Run Validation Commands
- Run all tests to ensure no regressions
- Run type checker to ensure type safety
- Run linter to ensure code quality

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests to validate the new timing functionality
- `uv run pytest app/tests/ -v --tb=short` - Run all tests to ensure no regressions
- `uv run mypy app/` - Type check the codebase
- `uv run ruff check app/` - Lint the codebase

## Notes
- The `[TIMING]` message uses INFO level (same as `[BLOCK START]` and `[BLOCK END]`) so it appears in standard log output
- The threshold of 3 seconds is a reasonable default for identifying blocks that may need optimization
- The message format `[TIMING] Block 'name' took X.XXXs (>3s threshold)` is grep-able and pairs well with existing `[BLOCK START]` and `[BLOCK END]` markers
- Consider that in the future, this threshold could be made configurable via environment variable or settings, but that is out of scope for this chore
