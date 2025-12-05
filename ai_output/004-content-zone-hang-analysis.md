# Content Zone Detection Hang Analysis

## Executive Summary
The application hang during extraction of block 'MARLIN52 2D.plan' was caused by the `_extract_line_cycles` function in `geometry.py`. The block contains 967 LINE segments forming a complex graph with 504 vertices, which caused the DFS-based cycle detection algorithm to become computationally intractable. The existing polygon count threshold (30) only applies AFTER cycle detection completes, providing no protection against expensive input graphs.

## Table Summary

| Metric | Value | Impact |
|--------|-------|--------|
| LINE segments | 967 | Far exceeds typical blocks (usually <50) |
| Unique vertices | 504 | Creates a dense graph for DFS |
| Processing start | 15:03:20.678 | Content zone detection began |
| Last log entry | 15:03:21.304 | DFS got stuck within 1 second |
| Cancel attempt | ~15:09:00 | ~6 minutes after hang |
| POLYGON_COUNT_THRESHOLD | 30 | Checked AFTER cycle detection (too late) |
| Abort check interval | Every 50 vertices | Not granular enough within DFS |

## Relevant Files

- `app/core/geometry.py:555-699` - `_extract_line_cycles()` function where hang occurred. Uses DFS to find closed cycles from LINE entities.
- `app/core/geometry.py:801-997` - `_detect_content_zone()` function that calls `_extract_line_cycles()`. Polygon threshold check is on line 869, AFTER the expensive operation.
- `app/core/constants.py:127` - `POLYGON_COUNT_THRESHOLD = 30` - only limits final polygon count, not input complexity.
- `app/core/extractor.py:1014` - Calls `_detect_content_zone()` from the main extraction loop.

## Root Cause Analysis

### 1. No Input Complexity Threshold
The current `POLYGON_COUNT_THRESHOLD` (30) is checked on line 869 of `geometry.py`:

```python
# Check polygon count threshold to avoid O(n³) containment analysis
polygon_count = len(all_shapes)
if polygon_count > POLYGON_COUNT_THRESHOLD:
```

This check occurs **AFTER** `_extract_line_cycles()` completes. The expensive cycle detection runs unconditionally regardless of input size.

### 2. Exponential DFS Complexity
The `find_cycle_from()` function (lines 642-668) uses depth-first search that can explore exponentially many paths:

```python
def find_cycle_from(start: tuple[float, float]) -> Polygon | None:
    stack = [(start, [start], {start})]
    while stack:
        current, path, visited = stack.pop()
        for neighbor in adjacency[current]:
            # ... explores all unvisited neighbors
```

With 504 vertices and 967 edges, the graph is dense (average degree ~3.8). This creates a massive search space.

### 3. Insufficient Abort Granularity
The abort check in `_extract_line_cycles()` only triggers every 50 vertices (line 675-676):

```python
if vertices_processed % 50 == 0:
    _check_geometry_abort(abort_event)
```

When a single `find_cycle_from()` call takes minutes (as happened here), the abort is never checked. The GUI freezes because the event loop cannot process the cancellation request.

### 4. Adjacency Graph Construction is O(n²)
The `get_canonical()` function (lines 603-613) iterates through all existing canonical points for each new point:

```python
def get_canonical(point: tuple[float, float]) -> tuple[float, float]:
    for existing in canonical:  # O(n) for each point
        if abs(existing[0] - point[0]) <= epsilon ...
```

With 1934 points (967 segments × 2 endpoints), this is ~1.9M comparisons before DFS even starts.

## Log Timeline

```
15:03:20.678 - Content zone detection starting for block 'MARLIN52 2D.plan'
15:03:20.678 - Extracted 4 closed polylines (0.001s) - FAST
15:03:20.679 - Line cycles: found 967 LINE segments
15:03:20.704 - Built adjacency graph with 504 unique vertices (~25ms)
15:03:20.704 - Started finding cycles (first 9 cycles found quickly)
15:03:21.296 - After ~600ms, still finding cycles (11 more cycles)
15:03:21.304 - Last log entry: "Found line cycle with 28 vertices"
             [6+ MINUTE GAP - Algorithm stuck in DFS]
~15:09:00    - User attempted cancel (GUI unresponsive)
```

The DFS got stuck processing a complex subgraph where the exponential path exploration took too long.

## Recommendations

### Immediate Fix: Add LINE Segment Threshold
Add an early exit before `_extract_line_cycles()` when input complexity is too high:

```python
# In _detect_content_zone(), before line cycle extraction:
LINE_SEGMENT_THRESHOLD = 200  # or similar reasonable limit

for entity in block_def:
    if entity.dxftype() == "LINE":
        line_count += 1
        if line_count > LINE_SEGMENT_THRESHOLD:
            logger.warning(f"Skipping line cycle detection: {line_count}+ LINE segments")
            break  # Skip cycle detection entirely
```

### Secondary Fix: Add Timeout to Cycle Detection
Wrap cycle detection in a timeout mechanism:

```python
CYCLE_DETECTION_TIMEOUT_SECONDS = 5.0
cycle_start_time = time.perf_counter()

for vertex in list(adjacency.keys()):
    if time.perf_counter() - cycle_start_time > CYCLE_DETECTION_TIMEOUT_SECONDS:
        logger.warning("Cycle detection timeout - returning partial results")
        break
    # ... existing logic
```

### Tertiary Fix: Add Abort Check Inside DFS
Make abort checks more granular:

```python
def find_cycle_from(start: tuple[float, float]) -> Polygon | None:
    iterations = 0
    while stack:
        iterations += 1
        if iterations % 1000 == 0:
            _check_geometry_abort(abort_event)  # Check frequently
        # ... existing logic
```

## Next Steps

1. **Implement LINE segment threshold** - Add `LINE_SEGMENT_THRESHOLD` constant (suggested: 200) and early exit in `_detect_content_zone()` before calling `_extract_line_cycles()`

2. **Add cycle detection timeout** - Implement 5-second timeout for the entire cycle detection phase

3. **Improve abort responsiveness** - Add abort checks inside `find_cycle_from()` loop, not just between vertices

4. **Consider algorithm replacement** - For complex blocks, consider simpler heuristics (e.g., use bounding box of polylines only, skip LINE-based cycle detection)
