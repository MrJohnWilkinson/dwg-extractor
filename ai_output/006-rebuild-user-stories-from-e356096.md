# Rebuild User Stories from e356096: Content Zone Detection Feature Set

## Executive Summary

This report distills the 17 commits from 2025-12-05 (8e8de6e through cffaabd) into comprehensive user stories for rebuilding the content zone detection feature set. Based on the retrospective analysis, only 3 implementations were fully successful, while others required multiple follow-up fixes or remain partially solved. The user stories below incorporate lessons learned to avoid the original pitfalls.

## Table Summary

| Priority | User Story | Complexity | Key Implementation Files | Status in Original |
|----------|-----------|------------|--------------------------|-------------------|
| 1 | Content Zone Detection | High | geometry.py, types.py, constants.py | Working with thresholds |
| 2 | Polygon Count Threshold | Low | geometry.py, constants.py | **WIN** - Essential safeguard |
| 3 | LINE Segment Threshold | Low | geometry.py, constants.py | **WIN** - Essential safeguard |
| 4 | Union Bounding Box | Medium | geometry.py | Working |
| 5 | File-Based Debug Logging | Medium | logger.py, main.py | **WIN** - Best monitoring solution |
| 6 | Abort Extraction Option | High | main.py, extractor.py, geometry.py | Partial - needed 3 follow-ups |
| 7 | Live Log Viewer Panel | Medium | main.py, logger.py | Partial - GUI blocks during computation |

## Relevant Files

- **app/core/geometry.py** - Core content zone detection, polygon analysis, cycle detection, threshold checks. Most critical file for this feature set.
- **app/core/types.py** - Contains `ContentZoneData` TypedDict for content zone results, `Polygon` type alias.
- **app/core/constants.py** - Contains `POLYGON_COUNT_THRESHOLD`, `LINE_SEGMENT_THRESHOLD`, `CYCLE_DETECTION_TIMEOUT_SECONDS`, log viewer config.
- **app/core/logger.py** - Contains `FlushingFileHandler` class, `create_debug_file_handler()`, `create_queue_handler()`.
- **app/core/extractor.py** - Contains `ExtractionAbortedError`, `_check_abort()`, abort checkpoint integration.
- **app/main.py** - GUI with abort button, live log viewer, file handler management, UI state management.
- **app/core/excel_writer.py** - New columns for suggested trim values and content zone detection flag.
- **app/core/excel_formatting.py** - Column formatting for new content zone columns.
- **specs/013-net-area-content-zone-detection.md** - Original comprehensive spec for content zone detection.
- **specs/014-union-bounding-box-tied-net-area.md** - Union bounding box spec for tied net areas.
- **specs/022-polygon-count-threshold.md** - Polygon threshold implementation spec.
- **specs/023-line-segment-threshold.md** - LINE segment threshold implementation spec.
- **specs/021-file-based-debug-logging.md** - File-based logging implementation spec.
- **specs/017-abort-extraction-option.md** - Abort feature implementation spec.
- **specs/015-live-log-viewer.md** - Live log viewer implementation spec.

---

## User Story 1: Content Zone Detection for Automatic Trim Value Derivation

### User Story
As a DXF block analyzer, I want to automatically identify the "content zone" shape within a block definition so that I can derive trim values (distance from block bounding box to content zone bounding box) and reduce manual data entry.

### Acceptance Criteria
1. System detects closed polygons using two methods:
   - LWPOLYLINE detection: Identify closed polylines of any vertex count
   - LINE cycle detection: Find closed cycles from connected line segments using graph-based DFS
2. Calculate area for each shape using shoelace formula
3. Determine containment relationships using point-in-polygon tests
4. Compute net area (own area minus contained shapes' areas)
5. Select shape with largest net area as content zone
6. Derive trim values from content zone bounding box relative to block bounding box
7. Add new Excel columns: Suggested Trim Left/Right/Top/Bottom, Content Zone Detected

### Implementation Requirements

**Data Types (types.py)**
```python
Polygon = list[tuple[float, float]]

class ContentZoneData(TypedDict):
    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
```

**Core Algorithms (geometry.py)**
- `_calculate_polygon_area(vertices: Polygon) -> float` - Shoelace formula
- `_point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool` - Ray casting
- `_polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool` - All vertices check
- `_get_polygon_bounding_box(polygon: Polygon) -> tuple[float, float, float, float]`
- `_extract_closed_lwpolylines(block_def: BlockLayout) -> list[Polygon]`
- `_extract_line_cycles(block_def: BlockLayout) -> list[Polygon]` - DFS-based cycle detection
- `_calculate_net_areas(polygons: list[Polygon]) -> list[tuple[Polygon, float]]`
- `_detect_content_zone(block_def: BlockLayout, block_bbox: tuple) -> ContentZoneData`

**Excel Columns (constants.py)**
```python
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: str = "block_suggested_trim_left"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: str = "block_suggested_trim_right"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: str = "block_suggested_trim_top"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: str = "block_suggested_trim_bottom"
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: str = "block_content_zone_detected"
```

### Test Assets Required
- `app/tests/assets/create_content_zone_test.py` - Generator script
- `app/tests/assets/content_zone_test.dxf` - Scenarios: nested rectangles, chamfered shapes, LINE cycles, mixed shapes, single shape, no shapes
- `app/tests/core/test_content_zone.py` - Comprehensive unit tests

### Critical Lesson Learned
**IMPORTANT**: The `_calculate_net_areas()` function has O(n^3) complexity (n polygons, n containment checks per polygon, n vertices per check). The `_extract_line_cycles()` DFS can hang indefinitely on dense graphs. **User Stories 2 and 3 MUST be implemented concurrently** to prevent application hangs.

---

## User Story 2: Polygon Count Threshold (CRITICAL SAFEGUARD)

### User Story
As a DXF block analyzer, I want content zone detection to automatically skip blocks with more than 30 polygons so that the application doesn't hang on complex blocks with O(n^3) containment analysis.

### Acceptance Criteria
1. Add `POLYGON_COUNT_THRESHOLD = 30` constant
2. Check polygon count BEFORE calling `_calculate_net_areas()`
3. If count > 30, log warning and return empty `ContentZoneData`
4. Extraction continues with other blocks (graceful degradation)

### Implementation (geometry.py)
```python
# After combining shapes, before net area calculation:
all_shapes = lwpolyline_shapes + line_cycle_shapes
polygon_count = len(all_shapes)

if polygon_count > POLYGON_COUNT_THRESHOLD:
    logger.warning(
        f"Skipping content zone detection{block_context}: {polygon_count} polygons "
        f"exceeds threshold of {POLYGON_COUNT_THRESHOLD}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
    )
```

### Critical Lesson Learned
This threshold was proven essential in production. A block with 102 polygons took 140.7 seconds (1,061,208 iterations). Most useful blocks have 1-12 polygons; 30+ are edge cases where detection provides diminishing value.

---

## User Story 3: LINE Segment Threshold (CRITICAL SAFEGUARD)

### User Story
As a DXF block analyzer, I want content zone detection to skip LINE cycle detection for blocks with more than 200 LINE segments so that the application doesn't hang on dense graphs during DFS exploration.

### Acceptance Criteria
1. Add `LINE_SEGMENT_THRESHOLD = 200` constant
2. Add `CYCLE_DETECTION_TIMEOUT_SECONDS = 5.0` constant as safety net
3. Count LINE segments BEFORE calling `_extract_line_cycles()`
4. If count > 200, skip LINE cycle extraction (polyline detection still runs)
5. Add timeout check inside DFS loop as additional protection
6. Add abort checks every 1000 DFS iterations for responsive cancellation

### Implementation (constants.py)
```python
POLYGON_COUNT_THRESHOLD: int = 30
LINE_SEGMENT_THRESHOLD: int = 200
CYCLE_DETECTION_TIMEOUT_SECONDS: float = 5.0
```

### Implementation (geometry.py)
```python
# Before _extract_line_cycles():
line_count = _count_line_segments(block_def)
if line_count > LINE_SEGMENT_THRESHOLD:
    logger.warning(f"Skipping LINE cycle detection: {line_count} segments exceeds {LINE_SEGMENT_THRESHOLD}")
    line_cycle_shapes = []
else:
    line_cycle_shapes = _extract_line_cycles(block_def, abort_event)

# Inside DFS loop:
if time.perf_counter() - start_time > CYCLE_DETECTION_TIMEOUT_SECONDS:
    logger.warning("Cycle detection timeout - returning partial results")
    break

if iterations % 1000 == 0:
    _check_geometry_abort(abort_event)
```

### Critical Lesson Learned
A block with 967 LINE segments (504 vertices, dense graph) caused 6+ minute hang. The DFS explores exponentially many paths. This threshold was proven essential for production reliability.

---

## User Story 4: Union Bounding Box for Tied Net Area Content Zones

### User Story
As a DXF block analyzer, when multiple shapes have equal maximum net area, I want the system to combine all tied shapes' bounding boxes into a union bounding box so that trim values accurately represent the full usable area.

### Acceptance Criteria
1. When multiple shapes tie for maximum net area, collect ALL tied shapes
2. Calculate union bounding box encompassing all tied shapes
3. Derive trim values from union bounding box (not arbitrary first shape)
4. Log number of tied shapes when union is computed

### Implementation (geometry.py)
```python
def _get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]:
    """Calculate union bounding box of multiple polygons."""
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)

    union_min_x, union_min_y, union_max_x, union_max_y = _get_polygon_bounding_box(polygons[0])
    for polygon in polygons[1:]:
        bbox = _get_polygon_bounding_box(polygon)
        union_min_x = min(union_min_x, bbox[0])
        union_min_y = min(union_min_y, bbox[1])
        union_max_x = max(union_max_x, bbox[2])
        union_max_y = max(union_max_y, bbox[3])
    return (union_min_x, union_min_y, union_max_x, union_max_y)

# In _detect_content_zone():
max_net_area = max(net_area for _, net_area in valid_shapes)
tied_shapes = [shape for shape, net_area in valid_shapes if net_area == max_net_area]

if len(tied_shapes) == 1:
    cz_bbox = _get_polygon_bounding_box(tied_shapes[0])
else:
    cz_bbox = _get_union_bounding_box(tied_shapes)
    logger.debug(f"Content zone: union of {len(tied_shapes)} tied shapes")
```

### Test Asset Required
- `app/tests/assets/create_equal_area_test.py` - Create block with 4 equal rectangles in corners
- `app/tests/assets/equal_area_test.dxf` - Test fixture

---

## User Story 5: File-Based DEBUG Logging for Real-Time Monitoring

### User Story
As a user experiencing slow or stuck extractions, I want DEBUG logs written directly to a timestamped file in real-time during extraction so that I can monitor progress via `tail -f` and share logs for diagnosis without waiting for extraction to complete.

### Acceptance Criteria
1. When extraction starts, create log file: `{dxf_filename}_debug_{timestamp}.log`
2. DEBUG messages written immediately (no queuing/buffering)
3. Log file path displayed in GUI at extraction start
4. File contains all DEBUG, INFO, WARNING, ERROR with timestamps
5. User can `tail -f` the log file for live monitoring
6. Log file persists regardless of extraction outcome

### Implementation (logger.py)
```python
class FlushingFileHandler(logging.FileHandler):
    """FileHandler that flushes after every emit for immediate visibility."""
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()  # Immediate disk write

def create_debug_file_handler(file_path: str) -> logging.FileHandler:
    """Create file handler with DEBUG level and immediate flush."""
    handler = FlushingFileHandler(file_path, mode='w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)

    # Custom formatter with milliseconds
    class MillisecondFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            ct = self.converter(record.created)
            s = time.strftime("%H:%M:%S", ct)
            return f"{s}.{int(record.msecs):03d}"

    handler.setFormatter(MillisecondFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    return handler
```

### Implementation (main.py)
```python
# In _extract_blocks():
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{input_path.stem}_debug_{timestamp}.log"
log_path = input_path.parent / log_filename
self.debug_file_handler = create_debug_file_handler(str(log_path))
logging.getLogger().addHandler(self.debug_file_handler)

# In _restore_ui_after_extraction():
if self.debug_file_handler:
    logging.getLogger().removeHandler(self.debug_file_handler)
    self.debug_file_handler.close()
    self.debug_file_handler = None
```

### Critical Lesson Learned
This was the actual solution to monitoring hang issues. The GUI log viewer blocks during heavy computation, making it unreliable for debugging hangs. File-based logging with `tail -f` provides reliable real-time visibility.

---

## User Story 6: Abort Extraction Option with Responsive Cancellation

### User Story
As a user, I want to abort a running extraction so that I can stop processing large files when I selected the wrong file or see errors indicating a problem.

### Acceptance Criteria
1. Abort button appears during extraction (replaces Browse/Extract)
2. Clicking Abort stops extraction within 1-2 seconds
3. No Excel file generated when aborted
4. Logs show progress statistics at abort point
5. UI restores for new extraction attempt

### Implementation Details

**Exception Class (extractor.py)**
```python
class ExtractionAbortedError(Exception):
    """Raised when extraction is aborted by user."""
    pass

def _check_abort(abort_event: threading.Event | None, context: str) -> None:
    """Check if abort requested and raise if so."""
    if abort_event and abort_event.is_set():
        raise ExtractionAbortedError(f"Aborted during {context}")
```

**Abort Checkpoints (extractor.py)**
- After `ezdxf.readfile()` - Check immediately after loading
- Block definition loop - Check every 25 blocks
- Modelspace entity loop - Check every 500 entities
- Before color analysis

**Geometry Abort Checkpoints (geometry.py) - CRITICAL FOR RESPONSIVENESS**
```python
def _check_geometry_abort(abort_event: threading.Event | None) -> None:
    """Check abort and raise GeometryAbortedError if set."""
    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Geometry analysis aborted")

# In _extract_line_cycles DFS:
if iterations % 1000 == 0:
    _check_geometry_abort(abort_event)

# In _calculate_net_areas containment loop:
if polygon_idx % 10 == 0:
    _check_geometry_abort(abort_event)
```

**UI State Management (main.py)**
```python
def _extract_blocks(self) -> None:
    self.abort_event = threading.Event()
    self.browse_button.pack_forget()
    self.extract_button.pack_forget()
    self.abort_button.pack(side="left", padx=10)

def _abort_extraction(self) -> None:
    if self.abort_event:
        self.abort_event.set()
    self.abort_button.configure(state="disabled")
    self.status_label.configure(text=MSG_ABORTING)

def _restore_ui_after_extraction(self) -> None:
    self.abort_button.pack_forget()
    self.browse_button.pack(side="left", padx=10)
    self.extract_button.pack(side="left", padx=10)
    self.abort_event = None
```

### Critical Lesson Learned
The original implementation (b5d8e34) required 3 follow-up commits because abort checks weren't granular enough. When stuck inside `_extract_line_cycles()` DFS or `_calculate_net_areas()`, no abort checks occurred. **Abort checks MUST be added inside expensive loops**, not just between phases.

---

## User Story 7: Live Log Viewer Panel in GUI

### User Story
As a developer/user running long extractions, I want a live log viewer in the GUI showing real-time progress so that I can monitor progress and identify bottlenecks without terminal access.

### Acceptance Criteria
1. GUI displays log viewer panel with monospace font
2. Log level dropdown: DEBUG, INFO, WARNING, ERROR
3. Messages appear in real-time (within 100ms of logging)
4. Each line shows timestamp, level, message
5. Auto-scrolls to latest entry
6. Terminal/stdout continues receiving all logs

### Implementation Details

**Queue Handler (logger.py)**
```python
def create_queue_handler(log_queue: queue.Queue, level: int = logging.DEBUG) -> logging.Handler:
    """Create QueueHandler for thread-safe log delivery to GUI."""
    handler = logging.handlers.QueueHandler(log_queue)
    handler.setLevel(level)
    return handler
```

**GUI Components (main.py)**
- Window resize: 500x300 -> 600x500
- `CTkOptionMenu` for log level selection
- `CTkTextbox` with `state="disabled"`, `font=("Courier", 10)`
- `self.log_queue = queue.Queue()`
- 100ms polling via `self.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)`

```python
def _poll_log_queue(self) -> None:
    while True:
        try:
            record = self.log_queue.get_nowait()
            if record.levelno >= self.current_log_level:
                msg = f"{record.asctime} [{record.levelname}] {record.getMessage()}\n"
                self.log_viewer.configure(state="normal")
                self.log_viewer.insert("end", msg)
                self.log_viewer.configure(state="disabled")
                self.log_viewer.see("end")
        except queue.Empty:
            break
    self.after(LOG_POLL_INTERVAL_MS, self._poll_log_queue)
```

### Critical Lesson Learned
The GUI log viewer **blocks during heavy computation** because the main thread is busy. Users cannot see real-time updates when extraction is running expensive algorithms. This is why **User Story 5 (File-Based Logging)** was the actual solution for debugging hangs. The GUI log viewer is useful for normal operation but unreliable for hang diagnosis.

---

## Recommended Implementation Order

1. **User Story 1** (Content Zone Detection) - Core feature
2. **User Story 2** (Polygon Threshold) - MUST be concurrent with #1
3. **User Story 3** (LINE Threshold) - MUST be concurrent with #1
4. **User Story 4** (Union Bounding Box) - After core detection works
5. **User Story 5** (File-Based Logging) - Before testing with real files
6. **User Story 6** (Abort Option) - After logging is in place
7. **User Story 7** (Live Log Viewer) - Optional enhancement

## Recommendations

1. **Implement thresholds from the start** - Don't wait for hangs to discover O(n^3) complexity issues
2. **Add abort checkpoints inside loops** - Not just between phases
3. **Rely on file-based logging** - Don't depend on GUI log viewer for debugging hangs
4. **Test with production-scale files early** - Small test files won't reveal performance issues
5. **Track elapsed time for each block** - Log timing to identify which blocks cause delays

## Next Steps

1. Create implementation branch from e356096
2. Implement User Stories 1-3 together (core + safeguards)
3. Add comprehensive test suite with complex block fixtures
4. Implement User Stories 4-5 for monitoring capability
5. Add User Story 6 for user control
6. Optionally add User Story 7 for convenience

## Validation Commands

After implementation, run these commands to verify:
```bash
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/core/test_geometry.py -v
uv run pytest app/tests/core/extractor/ -v
uv run pytest app/tests/ -v
uv run mypy app/
uv run ruff check app/
```
