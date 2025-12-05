# Bug: Content Zone Detection Hangs on Complex Blocks with Many LINE Segments

## Bug Description
When extracting DXF files containing blocks with many LINE segments (e.g., 'MARLIN52 2D.plan' with 967 LINE segments), the application hangs indefinitely during content zone detection. The hang occurs in the `_extract_line_cycles()` function which uses a DFS-based cycle detection algorithm that becomes computationally intractable for dense graphs. The abort button becomes unresponsive because abort checks only occur every 50 vertices, and when a single `find_cycle_from()` call takes minutes, the abort signal is never processed.

**Expected behavior:** Complex blocks either complete quickly or gracefully skip content zone detection. The abort button should always respond within 1-2 seconds.

**Actual behavior:** Application freezes for 6+ minutes with no ability to cancel. GUI becomes completely unresponsive.

## Problem Statement
The existing `POLYGON_COUNT_THRESHOLD` (30) check occurs **after** the expensive `_extract_line_cycles()` operation completes, providing no protection against complex input graphs. The DFS algorithm explores exponentially many paths in dense graphs, and abort checks are not granular enough to allow responsive cancellation during the DFS exploration.

## Solution Statement
Implement a three-tier protection strategy:
1. **Early exit**: Add `LINE_SEGMENT_THRESHOLD` constant (200) and check before cycle detection starts
2. **Timeout safety net**: Add 5-second timeout to cycle detection phase
3. **Responsive abort**: Add abort checks inside the DFS loop for sub-second cancellation response

## Steps to Reproduce
1. Open a DXF file containing a block with 500+ LINE segments (e.g., 'MARLIN52 2D.plan' with 967 LINE segments)
2. Click Extract to begin extraction
3. Observe the application hang during "Content zone detection" phase
4. Attempt to click Cancel/Abort button
5. Observe that the button is unresponsive and the application remains frozen

## Root Cause Analysis
The root cause is a combination of three issues:

1. **No input complexity threshold**: The `POLYGON_COUNT_THRESHOLD` check on line 869 of `geometry.py` occurs AFTER `_extract_line_cycles()` completes. Blocks with many LINE segments trigger expensive cycle detection unconditionally.

2. **Exponential DFS complexity**: The `find_cycle_from()` function (lines 642-668) explores all possible paths through the adjacency graph. With 504 vertices and 967 edges (average degree ~3.8), the search space is massive. A single cycle search can take minutes.

3. **Insufficient abort granularity**: The abort check in `_extract_line_cycles()` only triggers every 50 vertices (line 675-676). When stuck inside `find_cycle_from()`, no abort checks occur, making cancellation impossible.

**Timeline from logs:**
- 15:03:20.678 - Content zone detection starting
- 15:03:20.679 - Found 967 LINE segments
- 15:03:21.304 - Last log entry (DFS started)
- ~15:09:00 - User attempted cancel (~6 minute hang)

## Relevant Files
Use these files to fix the bug:

### `app/core/constants.py`
- Add `LINE_SEGMENT_THRESHOLD` constant (value: 200)
- This constant defines the maximum number of LINE segments before skipping cycle detection

### `app/core/geometry.py`
- `_extract_line_cycles()` (lines 555-699): Add timeout logic and abort checks inside DFS loop
- `_detect_content_zone()` (lines 801-997): Add early exit when LINE count exceeds threshold, before calling `_extract_line_cycles()`
- `_count_line_segments()`: New helper function to count LINE entities efficiently

### `app/tests/core/test_geometry.py`
- Add tests for LINE segment threshold behavior
- Add tests for timeout behavior
- Add tests for abort responsiveness

### New Files

#### `app/tests/assets/create_many_lines_test.py`
- Script to create a test DXF file with many LINE segments for testing threshold behavior

#### `app/tests/assets/many_lines_test.dxf`
- Test asset with 250+ LINE segments to test threshold behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add LINE_SEGMENT_THRESHOLD constant to constants.py
- Add `LINE_SEGMENT_THRESHOLD: int = 200` constant after `POLYGON_COUNT_THRESHOLD`
- Add comment explaining the threshold prevents exponential DFS complexity
- Add `CYCLE_DETECTION_TIMEOUT_SECONDS: float = 5.0` constant for timeout safety net

### Step 2: Add _count_line_segments() helper function in geometry.py
- Add helper function after the imports section (around line 27)
- Function signature: `def _count_line_segments(block_def: BlockLayout) -> int`
- Efficiently count LINE entities without creating any data structures
- Return the count as soon as it exceeds `LINE_SEGMENT_THRESHOLD` (early exit optimization)

### Step 3: Add LINE segment threshold check in _detect_content_zone()
- Before the call to `_extract_line_cycles()` (around line 850), add threshold check
- Use `_count_line_segments()` to get the count
- If count exceeds `LINE_SEGMENT_THRESHOLD`, log warning and skip line cycle extraction
- Set `line_cycle_shapes = []` when skipping
- Continue with polyline shapes only for content zone detection

### Step 4: Add timeout to _extract_line_cycles() cycle detection phase
- Import `CYCLE_DETECTION_TIMEOUT_SECONDS` from constants
- Add timeout check inside the main vertex iteration loop (around line 672)
- Check `time.perf_counter() - cycle_start_time > CYCLE_DETECTION_TIMEOUT_SECONDS`
- If timeout exceeded, log warning and break out of the loop, returning partial results
- Ensure this works alongside the existing timing already in the function

### Step 5: Add abort checks inside find_cycle_from() DFS loop
- Modify the `find_cycle_from()` inner function (lines 642-668)
- Add iteration counter inside the while loop
- Check abort every 1000 iterations: `if iterations % 1000 == 0: _check_geometry_abort(abort_event)`
- Pass `abort_event` to `find_cycle_from()` as a parameter (modify function signature)

### Step 6: Create test asset generator script
- Create `app/tests/assets/create_many_lines_test.py`
- Generate a block with 250 LINE segments forming a complex interconnected pattern
- Ensure the pattern would cause exponential DFS exploration if not thresholded
- Save to `many_lines_test.dxf`

### Step 7: Generate the test DXF asset
- Run the generator script to create `app/tests/assets/many_lines_test.dxf`
- Verify the file contains the expected number of LINE segments

### Step 8: Add tests for LINE segment threshold behavior
- Add `TestLineSegmentThreshold` class in `app/tests/core/test_geometry.py`
- Test that `_count_line_segments()` correctly counts LINE entities
- Test that content zone detection skips line cycle extraction when threshold exceeded
- Test that polyline-based detection still works when LINE threshold exceeded

### Step 9: Add tests for timeout behavior
- Add `TestCycleDetectionTimeout` class in `app/tests/core/test_geometry.py`
- Test that cycle detection respects the timeout and returns partial results
- Verify warning is logged when timeout occurs

### Step 10: Add tests for abort responsiveness
- Add `TestAbortResponsiveness` class in `app/tests/core/test_geometry.py`
- Test that abort event is checked inside DFS loop
- Test that `GeometryAbortedError` is raised within expected iteration count

### Step 11: Run validation commands
- Execute all validation commands listed below to confirm the fix works correctly

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests including new threshold and timeout tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run existing content zone tests to ensure no regressions
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests to validate integration
- `uv run pytest app/tests/ -v --tb=short` - Run full test suite to ensure no regressions
- `uv run mypy app/core/geometry.py app/core/constants.py` - Type check modified files
- `uv run ruff check app/core/geometry.py app/core/constants.py` - Lint modified files

## Notes
- The LINE_SEGMENT_THRESHOLD value of 200 is chosen based on analysis: blocks with <50 LINE segments are typical, and blocks with 200+ segments are rare and likely too complex for accurate cycle detection anyway
- The 5-second timeout is a safety net - most legitimate blocks complete cycle detection in <1 second
- The abort check every 1000 DFS iterations ensures sub-second response even in pathological cases (1000 iterations at ~1μs each = ~1ms)
- When LINE threshold is exceeded, polyline-based content zone detection still runs - only LINE cycle detection is skipped
- The fix is surgical and does not change the algorithm's correctness for blocks below the threshold
