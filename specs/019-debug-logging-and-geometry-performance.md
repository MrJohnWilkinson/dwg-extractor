# Bug: Debug Logging Not Visible and Geometry Analysis Lockup

## Bug Description
The DXF Block Extractor application has two related issues:

1. **DEBUG level logging not visible in GUI**: When the log level dropdown is set to DEBUG (the default), DEBUG messages from the extraction process are not displayed in the log viewer. Only INFO and higher level messages appear.

2. **Application lockup during geometry analysis**: The application becomes unresponsive during "Analyzing block definitions..." phase, taking over 2 minutes to respond to an abort request (user clicked abort at 12:28:28, app responded at 12:29:50 - 82 seconds delay).

**Log excerpt showing the issue:**
```
12:27:35.778 [INFO] Analyzing block definitions... 100/208
12:28:28.301 [INFO] User requested extraction abort
12:29:50.438 [INFO] Abort detected during geometry analysis of block 'GUB-460.fotocelle'
```

The 82-second gap between abort request and response indicates the geometry code is not checking abort frequently enough.

## Problem Statement
1. The root logger and module loggers are not set to DEBUG level at initialization, even though the log viewer dropdown defaults to DEBUG. This prevents DEBUG messages from being emitted.

2. The `_calculate_net_areas()` function in `geometry.py` has O(n³) complexity with insufficient abort checkpoints, causing the application to become unresponsive when processing blocks with many closed shapes.

## Solution Statement
1. **Fix DEBUG logging**: Initialize the root logger level to DEBUG when the application starts, matching the dropdown's default value. This ensures DEBUG messages from all modules (extractor, geometry) are captured.

2. **Fix geometry lockup**: Add more frequent abort checkpoints in `_calculate_net_areas()` to ensure abort requests are processed within a reasonable time (target: <2 seconds response time).

## Steps to Reproduce
1. Launch the application: `bash scripts/start.sh`
2. Observe that log level dropdown shows "DEBUG"
3. Select the test file: `app/tests/assets/samples/05-02 MASTERTEGNING SPAR SUPERMARKED - 670 M2 - 280525.dxf`
4. Click Extract
5. Observe: Only INFO messages appear, no DEBUG messages
6. Click Abort button
7. Observe: Application takes over 1 minute to respond to abort

## Root Cause Analysis

### Issue 1: DEBUG Messages Not Displayed

**Root Cause**: In `main.py` at initialization:

```python
# Line 69-76
self.current_log_level: int = logging.DEBUG  # Display filter only
self.log_queue: queue.Queue[logging.LogRecord] = queue.Queue()

# Queue handler created at DEBUG level
self.queue_handler = create_queue_handler(self.log_queue)
# Added to root logger, but ROOT LOGGER LEVEL IS NEVER SET
logging.getLogger().addHandler(self.queue_handler)
```

The problem is that:
1. The root logger's default level is WARNING (Python default)
2. Module loggers created by `setup_logger()` default to INFO (from env var)
3. Even though the queue handler accepts DEBUG, the loggers filter out DEBUG before it reaches handlers
4. The `_on_log_level_change()` method correctly updates levels, but it's only called when the dropdown CHANGES, not at initialization

The dropdown shows DEBUG but the actual logger levels are INFO/WARNING.

### Issue 2: Geometry Lockup

**Root Cause**: In `geometry.py`, the `_calculate_net_areas()` function (lines 701-787) has insufficient abort checkpoints:

```python
# First loop - O(n²) with abort check every 10 iterations (lines 739-748)
for i in range(n):
    if n > 20 and i > 0 and i % 10 == 0:
        _check_geometry_abort(abort_event)
    for j in range(n):
        if i != j and _polygon_contains_polygon(polygons[j], polygons[i]):
            contained_by[i].append(j)

# Second loop - O(n³) with NO abort checks (lines 763-778)
for i in range(n):
    directly_contained: list[int] = []
    for j in range(n):
        if i != j and _polygon_contains_polygon(polygons[i], polygons[j]):
            is_direct = True
            for k in range(n):  # Third nested loop!
                if k != i and k != j:
                    if _polygon_contains_polygon(polygons[i], polygons[k]) and \
                       _polygon_contains_polygon(polygons[k], polygons[j]):
                        is_direct = False
                        break
```

The second loop is O(n³) and has ZERO abort checks. For a block with 50 closed shapes, this is 125,000 containment checks without checking for abort.

## Relevant Files
Use these files to fix the bug:

- `app/main.py` - Contains the GUI application initialization where root logger level needs to be set at startup
- `app/core/geometry.py` - Contains `_calculate_net_areas()` which needs more abort checkpoints
- `app/core/logger.py` - Reference for understanding the logging setup
- `app/tests/core/test_logger.py` - Tests for logging functionality

### New Files
None required.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Initialize Root Logger Level at Startup

In `app/main.py`, after creating the queue handler and adding it to the root logger, set the root logger's level to DEBUG to match the dropdown's default.

**Location**: In `__init__()` method, after line 76 (`logging.getLogger().addHandler(self.queue_handler)`)

**Change**: Add `logging.getLogger().setLevel(logging.DEBUG)` to initialize the root logger at DEBUG level

This ensures that on startup:
- Queue handler level = DEBUG (already set by `create_queue_handler()`)
- Root logger level = DEBUG (new)
- Module loggers propagate to root, so DEBUG messages will flow through

### Step 2: Add Abort Checkpoints in _calculate_net_areas Second Loop

In `app/core/geometry.py`, the `_calculate_net_areas()` function's second nested loop (lines 763-787) needs abort checkpoints.

**Location**: Inside the `for i in range(n):` loop that calculates `directly_contained` (around line 763)

**Change**: Add abort checkpoint every iteration of the outer loop:
- Add `_check_geometry_abort(abort_event)` at the start of each iteration
- This ensures abort is checked at least once per polygon, keeping response time proportional to polygon count

### Step 3: Add Progress Logging in _calculate_net_areas

Add DEBUG logging in `_calculate_net_areas()` to provide visibility into the expensive net area calculation phase.

**Location**: In `_calculate_net_areas()` function

**Changes**:
- Log progress in the second nested loop every 10 iterations
- This helps diagnose slow blocks and gives visibility into where time is spent

### Step 4: Run Tests to Validate No Regressions

Run the test suite to ensure logging and geometry changes don't break existing functionality.

### Step 5: Manual Validation

Verify the fixes work correctly:
1. Start the app and confirm DEBUG messages appear immediately
2. Process a test file and confirm abort responds within 2 seconds

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests
- `uv run pytest app/tests/ -v` - Run all tests for regression check
- `uv run mypy app/` - Type check for any type errors
- `uv run ruff check app/` - Lint check for code quality

## Notes
- The geometry O(n³) algorithm is inherently slow for blocks with many closed shapes. The abort checkpoint fix ensures responsiveness but doesn't improve algorithm efficiency. Future optimization could use spatial indexing or limit content zone detection to simpler heuristics for complex blocks.
- The logging fix ensures DEBUG messages flow at startup. When the user changes the dropdown, `_on_log_level_change()` correctly updates all levels - this fix addresses only the initial state.
- The test file `05-02 MASTERTEGNING SPAR SUPERMARKED - 670 M2 - 280525.dxf` should be used for manual testing as it triggers the slow geometry analysis path.
