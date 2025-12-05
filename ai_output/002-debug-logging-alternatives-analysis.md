# Debug Logging and Performance Visibility: Alternative Approaches Analysis

## Executive Summary
Multiple spec implementations (013-020) have attempted to address debug logging visibility and extraction performance monitoring without achieving stable, responsive results. The root cause is architectural: CPU-bound O(n³) geometry algorithms combined with queue-based GUI logging creates an irreconcilable conflict between computation responsiveness and log visibility. This report analyzes alternative approaches that decouple logging from GUI responsiveness.

## Table Summary

| Approach | Complexity | GUI Impact | Debug Quality | Agent Access | Recommended |
|----------|------------|------------|---------------|--------------|-------------|
| File-based logging | Low | None | High | Excellent | **Yes** |
| Progress callbacks | Medium | Minimal | Medium | Limited | Partial |
| Algorithm optimization | High | None (fixes root cause) | N/A | N/A | **Yes (long-term)** |
| Bounded queue + aggregation | Medium | Low | Medium | Limited | No |
| JSON export for post-hoc | Low | None | High | **Best** | **Yes** |
| CLI diagnostic mode | Low | None | High | Excellent | **Yes** |
| Subprocess isolation | High | None | High | Good | Overkill |

## Relevant Files

- **app/main.py** - GUI application with queue-based logging infrastructure (lines 69-88, 190-235). The polling mechanism and level change handler are correctly implemented but fundamentally limited by the approach.
- **app/core/logger.py** - Logging setup with `set_all_logger_levels()` function. Current design adds handlers to multiple loggers creating complexity.
- **app/core/geometry.py** - Contains O(n³) `_calculate_net_areas()` (lines 701-797) which is the primary performance bottleneck. Many abort checkpoints exist but can't help when stuck in inner loops.
- **app/core/extractor.py** - Block extraction with abort support. Progress logging exists but doesn't provide useful visibility into slow operations.
- **specs/013-020** - Eight specification files documenting the evolution of attempted fixes, each adding complexity without solving the core issue.

## Root Cause Analysis

### Problem 1: Algorithm Complexity vs Logging Granularity
The content zone detection introduced in spec 013 uses `_calculate_net_areas()` with O(n³) complexity:
```python
# geometry.py:763-788 - Triple nested loop
for i in range(n):
    for j in range(n):
        for k in range(n):  # O(n³) containment checks
            if _polygon_contains_polygon(...) and _polygon_contains_polygon(...):
```
For a block with 50 closed shapes, this is 125,000 containment checks. No amount of DEBUG logging makes this faster or more interruptible.

### Problem 2: Queue-based Logging Architectural Limits
Current architecture:
```
[Extraction Thread] --DEBUG logs--> [Queue] --50ms poll--> [GUI Thread updates textbox]
```

Issues:
1. Heavy DEBUG logging floods the queue during geometry analysis
2. GUI textbox updates are expensive (enable, insert, disable, scroll)
3. CPU-bound extraction thread doesn't yield, so poll may not execute on time
4. Log level filtering happens AFTER message is logged (late filtering)

### Problem 3: Multiple Logger Management
The `set_all_logger_levels()` function iterates through `logging.Logger.manager.loggerDict` to update levels. This is fragile because:
- Loggers are created at import time with environment-based levels
- The function only updates loggers with names starting with `core.` or `__main__`
- Race conditions can occur if modules are imported after level change

## Alternative Approaches

### Approach 1: File-Based Logging (Recommended)
**Implementation**: Write DEBUG logs directly to a timestamped file instead of the queue.

```python
# In logger.py - add file handler
def setup_file_logger(log_path: str) -> None:
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(...)
    logging.getLogger().addHandler(file_handler)
```

**Benefits**:
- No queue overhead
- GUI remains responsive
- Complete log history preserved
- User can share log file with agent/developer
- Natural integration with `tail -f` for real-time viewing

**GUI Integration**: Show log file path, add "Open Log" button. Optionally show last N lines in viewer at INFO level only.

### Approach 2: JSON Export for Post-Hoc Analysis (Recommended for Agent)
**Implementation**: Export timing and progress data to a structured JSON file.

```python
# New: extraction_diagnostics.py
@dataclass
class BlockDiagnostics:
    block_name: str
    total_time_ms: float
    polyline_extraction_ms: float
    line_cycle_detection_ms: float
    net_area_calculation_ms: float
    polygon_count: int
    containment_checks: int

def write_diagnostics(data: list[BlockDiagnostics], path: str) -> None:
    with open(path, 'w') as f:
        json.dump([asdict(d) for d in data], f, indent=2)
```

**Benefits**:
- Structured data perfect for agent analysis
- User provides JSON file when reporting issues
- No GUI impact
- Agent can identify slow blocks, suggest optimizations

### Approach 3: CLI Diagnostic Mode (Recommended)
**Implementation**: Add `--diagnostic` flag to extraction that skips GUI, writes verbose logs.

```bash
# User runs when issue occurs:
uv run python app/main.py --diagnostic path/to/file.dxf > diagnostic.log 2>&1
```

**Benefits**:
- Full DEBUG output without GUI constraints
- Natural separation of concerns
- Easy to share with agent
- Can be run on problematic files specifically

### Approach 4: Algorithm Optimization (Long-term Recommended)
**Implementation**: Replace O(n³) containment analysis with spatial indexing.

```python
from rtree import index

def _calculate_net_areas_optimized(polygons: list[Polygon]) -> list[tuple[Polygon, float]]:
    # Build R-tree spatial index
    idx = index.Index()
    for i, poly in enumerate(polygons):
        bbox = _get_polygon_bounding_box(poly)
        idx.insert(i, bbox)

    # Query only spatially-relevant polygons instead of all-pairs
    for i, poly in enumerate(polygons):
        candidates = list(idx.intersection(_get_polygon_bounding_box(poly)))
        # Only check containment for spatial candidates
```

**Benefits**:
- Reduces O(n³) to approximately O(n log n) for typical cases
- Root cause fix - makes DEBUG logging feasible
- Improves user experience directly

**Trade-off**: Adds `rtree` dependency, requires careful implementation.

### Approach 5: Progress Callbacks (Partial Solution)
**Implementation**: Replace fine-grained logging with coarse progress callbacks.

```python
# In geometry.py
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[...],
    progress_callback: Callable[[str, float], None] | None = None,
) -> ContentZoneData:
    if progress_callback:
        progress_callback("polyline_extraction", 0.0)
    shapes = _extract_closed_lwpolylines(...)
    if progress_callback:
        progress_callback("polyline_extraction", 1.0)
```

**Benefits**:
- Lower overhead than logging
- GUI can show meaningful progress

**Limitations**:
- Still doesn't help agent diagnose issues
- Requires threading complexity for smooth updates

### Approach 6: Lazy Detailed Logging
**Implementation**: Only emit DEBUG logs for operations exceeding a threshold.

```python
# Log details only for slow blocks
block_start = time.perf_counter()
# ... processing ...
elapsed = time.perf_counter() - block_start
if elapsed > 1.0:  # Only log if > 1 second
    logger.warning(f"Slow block '{name}': {elapsed:.2f}s, {polygon_count} polygons")
```

**Benefits**:
- Reduces log noise dramatically
- Highlights problematic blocks automatically
- Keeps INFO log useful

## Recommendations

### Immediate Actions (Low Effort, High Impact)
1. **Add file-based DEBUG logging**: Write all DEBUG to `extraction_{timestamp}.log` alongside Excel output
2. **Add JSON diagnostics export**: Write `extraction_{timestamp}_diagnostics.json` with timing data per block
3. **Change GUI log viewer to INFO-only**: Keep GUI viewer but only show INFO+ messages (already mostly works)

### Short-term Actions (Medium Effort)
4. **Add CLI diagnostic mode**: `--diagnostic` flag for headless verbose extraction
5. **Implement lazy detailed logging**: Only log details for blocks taking > 1 second

### Long-term Actions (High Effort, Root Cause Fix)
6. **Optimize `_calculate_net_areas()`**: Use spatial indexing to reduce complexity
7. **Add "quick mode"**: Skip content zone detection for blocks with > N entities

## Implementation Priority

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| 1 | File-based DEBUG logging | 1 day | High |
| 2 | JSON diagnostics export | 1 day | High (for agent) |
| 3 | GUI to INFO-only default | 1 hour | Medium |
| 4 | CLI diagnostic mode | 0.5 day | Medium |
| 5 | Lazy detailed logging | 0.5 day | Medium |
| 6 | Algorithm optimization | 3-5 days | Critical |

## Next Steps

1. Implement file-based logging alongside (not replacing) queue-based GUI logging
2. Create JSON diagnostics export function in extraction workflow
3. Test with problematic DXF files to validate agent can diagnose issues from exported data
4. Plan algorithm optimization as separate spec for long-term fix
