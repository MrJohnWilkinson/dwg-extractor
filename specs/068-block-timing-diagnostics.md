# Chore: Add Block Timing Diagnostics

## Chore Description
Add timing logs to identify exact bottlenecks in problem blocks during DXF extraction. Some blocks take 35-133 seconds to process (e.g., `FrontEnd_Checkout_BeltedTACO_MerchGA` at 133s). The timing logs will help identify which specific operations within block processing are consuming time, enabling targeted optimization.

Example problem blocks from user's DXF file:
```
Time        Block                                    Duration
12:43:24 -> 12:43:59  Stockroom_Hook_SafetyVestRail         35s
12:44:01 -> 12:45:05  FreshProduce_ScoopWeighPottles_Wood   64s
12:45:26 -> 12:45:50  Grocery_GondolaACO_Combined           24s
12:46:10 -> 12:47:00  GM_MobileBin (1st, skipped)           50s
12:47:22 -> 12:49:35  FrontEnd_Checkout_BeltedTACO_MerchGA  133s ← WORST
12:50:22 -> 12:51:09  GM_MobileBin (2nd, skipped)           47s
12:51:09 -> 12:51:58  GM_MobileBin (3rd, skipped)           49s
12:51:58 -> 12:52:52  GM_MobileBin (4th, skipped)           54s
```

## Relevant Files
Use these files to resolve the chore:

- `app/core/extractor.py` - Main extraction logic with PHASE 2 block processing loop (lines 1206-1296). Add per-block timing wrapper around the entire block processing section.
- `app/core/geometry.py` - Contains `_detect_content_zone()` function (lines 1052-1277) which is the suspected bottleneck. Add timing to internal operations:
  - `_extract_paint_bucket_regions()`
  - `_calculate_net_areas()`
  - Edge extraction and snapping
- `app/core/logger.py` - Already provides `timed_block()` context manager (lines 365-399) which is ideal for this task. No modifications needed.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Per-Block Timing to extractor.py PHASE 2

In `extractor.py`, wrap the PHASE 2 block processing loop body with timing. The loop starts at line 1206 and processes each block definition.

Add timing around the entire per-block processing section (entity counting through content zone detection):

```python
# At the start of the PHASE 2 loop body (after determining effective_name)
from .logger import timed_block
import time

# Inside the loop, after effective_name is determined:
block_start = time.perf_counter()

# ... existing block processing code ...

# After block_content_zone_data[effective_name] = content_zone
block_duration = time.perf_counter() - block_start
if block_duration > 1.0:  # Only log blocks taking > 1 second
    logger.info(
        f"[TIMING] Block '{effective_name}' completed in {block_duration:.1f}s"
    )
```

### Step 2: Add Sub-Operation Timing to _detect_content_zone() in geometry.py

In `geometry.py`, add timing logs to key operations within `_detect_content_zone()` function (lines 1052-1277). Use the existing `timed_block()` context manager from logger.py.

Add timing to these operations:
1. **Edge extraction** - `_extract_paint_bucket_regions()` call (line 1156)
2. **Side filtering** - The side filter loop (lines 1164-1174)
3. **Net area calculation** - `_calculate_net_areas()` call (line 1209)
4. **Area filtering** - The area filter loop (lines 1213-1223)

Implementation approach - add `import time` at the start of the function and use inline timing:

```python
# Before _extract_paint_bucket_regions() call:
t0 = time.perf_counter()
all_shapes = _extract_paint_bucket_regions(...)
t1 = time.perf_counter()
if t1 - t0 > 0.5:
    logger.info(f"[{block_name}] Paint bucket regions: {t1-t0:.2f}s ({original_polygon_count} polygons)")

# Before side filter:
t2 = time.perf_counter()
# ... side filter code ...
t3 = time.perf_counter()
if min_side_filter > 0 and t3 - t2 > 0.5:
    logger.info(f"[{block_name}] Side filtering: {t3-t2:.2f}s")

# Before _calculate_net_areas() call:
t4 = time.perf_counter()
net_areas = _calculate_net_areas(all_shapes, abort_event)
t5 = time.perf_counter()
if t5 - t4 > 0.5:
    logger.info(f"[{block_name}] Net area calculation: {t5-t4:.2f}s ({len(all_shapes)} polygons)")

# Before area filter:
t6 = time.perf_counter()
# ... area filter code ...
t7 = time.perf_counter()
if min_area_filter > 0 and t7 - t6 > 0.5:
    logger.info(f"[{block_name}] Area filtering: {t7-t6:.2f}s")
```

### Step 3: Add Detailed Timing Inside _extract_paint_bucket_regions() in geometry.py

The `_extract_paint_bucket_regions()` function (lines 707-783) contains expensive Shapely operations. Add timing to:

1. **Edge extraction** - `_extract_all_edges()` call (line 744)
2. **Edge snapping** - Precision fix or gap bridge loops (lines 755-765)
3. **Union operation** - `unary_union(edges)` call (line 768)
4. **Polygonize** - `polygonize(line_segments)` call (line 773)

```python
# At start of function:
import time
t_start = time.perf_counter()

# After _extract_all_edges():
t_edges = time.perf_counter()
if t_edges - t_start > 0.2:
    logger.debug(f"Edge extraction: {t_edges - t_start:.2f}s ({len(edges)} edges)")

# After snapping (if applied):
t_snap = time.perf_counter()
if precision_tolerance > 0 or gap_bridge_tolerance > 0:
    if t_snap - t_edges > 0.2:
        logger.debug(f"Edge snapping: {t_snap - t_edges:.2f}s")

# After unary_union():
t_union = time.perf_counter()
if t_union - t_snap > 0.2:
    logger.debug(f"Unary union: {t_union - t_snap:.2f}s")

# After polygonize():
t_poly = time.perf_counter()
if t_poly - t_union > 0.2:
    logger.debug(f"Polygonize: {t_poly - t_union:.2f}s ({len(polygons)} polygons)")
```

### Step 4: Ensure INFO Level Logging Shows Block-Level Timing

The timing logs should be visible at INFO level (the default) for block-level operations, and at DEBUG level for detailed sub-operation timing. The existing `_detect_content_zone()` already uses INFO level for block start/complete messages.

Verify the logging levels are appropriate:
- Block processing time (> 1s): `logger.info`
- Paint bucket regions time (> 0.5s): `logger.info`
- Net area calculation time (> 0.5s): `logger.info`
- Internal sub-operations (> 0.2s): `logger.debug`

### Step 5: Run Tests to Verify No Regressions

Run the test suite to ensure the timing additions don't break any existing functionality.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests to verify no regressions from timing additions
- `uv run mypy app/` - Type check to ensure no type errors introduced
- `uv run ruff check app/` - Lint check for code quality

## Notes
- The timing logs use thresholds (1s, 0.5s, 0.2s) to avoid cluttering output with fast operations
- Timing uses `time.perf_counter()` for high-precision measurement (already used in `logger.py`)
- The `timed_block()` context manager from logger.py could be used for some operations, but inline timing provides more granular control and allows conditional logging
- Debug logging for sub-operations allows detailed analysis when needed via `DXF_EXTRACTOR_LOG_LEVEL=DEBUG`
- The test file mentioned (`app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf`) is a large production file used to reproduce the performance issue - it may not be in the git-tracked test assets
