# Complete Rebuild User Stories: Content Zone Feature Set

## Executive Summary

This report provides a complete, sequentially-implementable set of user stories for rebuilding the content zone feature set from commit ad25eab. The order has been restructured so threshold safeguards and logging are implemented BEFORE the complex algorithms, preventing the hangs that plagued the original implementation. Includes git setup steps as the first user story.

## Table Summary

| Order | User Story | Type | Complexity | Dependencies | Key Files |
|-------|-----------|------|------------|--------------|-----------|
| 0 | Git Rebuild Setup | chore | Low | None | git commands only |
| 1 | Performance Threshold Constants | chore | Low | US-0 | constants.py |
| 2 | File-Based Debug Logging | feature | Medium | US-0 | logger.py, main.py |
| 3 | Content Zone Detection Core | feature | High | US-1, US-2 | geometry.py, types.py |
| 4 | Union Bounding Box | feature | Low | US-3 | geometry.py |
| 5 | Excel Output Integration | feature | Medium | US-3, US-4 | excel_writer.py, excel_formatting.py |
| 6 | Abort Extraction Option | feature | High | US-2, US-3 | main.py, extractor.py, geometry.py |
| 7 | Live Log Viewer Panel | feature | Medium | US-2 | main.py |

## Relevant Files

- **app/core/constants.py** - Threshold constants, Excel column definitions, log viewer config
- **app/core/types.py** - `ContentZoneData` TypedDict, `Polygon` type alias
- **app/core/geometry.py** - All geometric algorithms: polygon detection, cycle detection, net area calculation
- **app/core/logger.py** - `FlushingFileHandler` class, `create_debug_file_handler()`, `create_queue_handler()`
- **app/core/extractor.py** - `ExtractionAbortedError`, `_check_abort()`, integration with geometry
- **app/core/excel_writer.py** - New columns for trim values and content zone flag
- **app/core/excel_formatting.py** - Column formatting for new content zone columns
- **app/main.py** - GUI: abort button, log viewer, file handler management
- **app/tests/core/test_geometry.py** - Unit tests for geometric functions
- **app/tests/core/test_content_zone.py** - Integration tests for content zone detection
- **app/tests/assets/** - Test DXF fixtures

---

## User Story 0: Git Rebuild Setup [chore]

### User Story
As a developer, I want to create a clean branch from ad25eab with retrospective documentation so that I can rebuild the content zone feature without inheriting technical debt from the previous implementation.

### Acceptance Criteria
1. Current work preserved as reference (tag + branch)
2. New branch created from ad25eab commit
3. Retrospective documentation copied to new branch
4. Clean working state confirmed

### Implementation Steps
```bash
# Step 1: Preserve current work
git tag backup-content-zone-v1 HEAD
git branch content-zone-reference dwg-extractor-stage

# Step 2: Create clean rebuild branch
git checkout -b content-zone-rebuild-v2 ad25eab

# Step 3: Copy retrospective docs from reference
git checkout content-zone-reference -- ai_output/005-content-zone-optimization-retrospective.md
git checkout content-zone-reference -- ai_output/006-rebuild-user-stories-from-e356096.md
git checkout content-zone-reference -- ai_output/007-git-rebuild-strategy-analysis.md
git checkout content-zone-reference -- ai_output/008-complete-rebuild-user-stories.md

# Step 4: Commit documentation
git add ai_output/
git commit -m "docs: add retrospective analysis for content zone rebuild

Include lessons learned from previous implementation attempt.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Step 5: Verify clean state
git status
git log --oneline -5
```

### Verification
- `git log --oneline -3` shows: docs commit, then ad25eab
- `ls ai_output/` shows 4 retrospective documents
- No uncommitted changes

### Reference Commands (During Development)
```bash
# View old implementation for reference
git show content-zone-reference:app/core/geometry.py | head -100

# Diff specific file against old implementation
git diff content-zone-rebuild-v2..content-zone-reference -- app/core/geometry.py

# Copy specific test file from old implementation
git checkout content-zone-reference -- app/tests/assets/content_zone_test.dxf
```

---

## User Story 1: Performance Threshold Constants [chore]

### User Story
As a DXF block analyzer, I want performance threshold constants defined upfront so that all subsequent algorithms have safeguards against exponential complexity from day one.

### Acceptance Criteria
1. `POLYGON_COUNT_THRESHOLD = 30` constant defined
2. `LINE_SEGMENT_THRESHOLD = 200` constant defined
3. `CYCLE_DETECTION_TIMEOUT_SECONDS = 5.0` constant defined
4. Excel column constants for content zone fields defined
5. All constants have documentation comments explaining their purpose

### Implementation (constants.py)
```python
# Content Zone Detection Thresholds
# These prevent O(n^3) and exponential DFS hangs on complex blocks

POLYGON_COUNT_THRESHOLD: int = 30
"""Maximum polygons for content zone net area calculation.
Blocks with more polygons skip content zone detection.
Rationale: _calculate_net_areas() is O(n^3) - 102 polygons = 140+ seconds."""

LINE_SEGMENT_THRESHOLD: int = 200
"""Maximum LINE segments for cycle detection DFS.
Blocks with more LINE segments skip LINE cycle extraction.
Rationale: DFS on 967 segments (504 vertices) caused 6+ minute hang."""

CYCLE_DETECTION_TIMEOUT_SECONDS: float = 5.0
"""Safety timeout for cycle detection algorithm.
Prevents indefinite hang even if threshold check is bypassed."""

# Content Zone Excel Columns
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: str = "block_suggested_trim_left"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: str = "block_suggested_trim_right"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: str = "block_suggested_trim_top"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: str = "block_suggested_trim_bottom"
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: str = "block_content_zone_detected"
```

### Test Requirements
```python
# app/tests/core/test_constants.py
def test_polygon_threshold_reasonable():
    """Threshold should be between 10 and 100."""
    assert 10 <= POLYGON_COUNT_THRESHOLD <= 100

def test_line_threshold_reasonable():
    """Threshold should be between 50 and 500."""
    assert 50 <= LINE_SEGMENT_THRESHOLD <= 500

def test_timeout_reasonable():
    """Timeout should be between 1 and 30 seconds."""
    assert 1.0 <= CYCLE_DETECTION_TIMEOUT_SECONDS <= 30.0
```

### Commit Message
```
feat: add performance threshold constants for content zone detection

Define POLYGON_COUNT_THRESHOLD (30), LINE_SEGMENT_THRESHOLD (200),
and CYCLE_DETECTION_TIMEOUT_SECONDS (5.0) to prevent O(n^3) and
exponential DFS hangs before implementing content zone algorithms.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 2: File-Based Debug Logging [feature]

### User Story
As a user or developer, I want DEBUG logs written directly to a timestamped file during extraction so that I can monitor progress via `tail -f` and diagnose issues without depending on the GUI.

### Acceptance Criteria
1. `FlushingFileHandler` class that flushes after every emit
2. `create_debug_file_handler(file_path)` factory function
3. Log file created at extraction start: `{dxf_filename}_debug_{timestamp}.log`
4. DEBUG+ messages written with timestamps (HH:MM:SS.mmm format)
5. Log file path displayed in GUI status
6. Handler removed and closed after extraction completes

### Implementation (logger.py)
```python
import time
import logging

class FlushingFileHandler(logging.FileHandler):
    """FileHandler that flushes after every emit for immediate visibility.

    Standard FileHandler buffers writes, making `tail -f` unreliable.
    This handler ensures each log message is immediately written to disk.
    """
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


class MillisecondFormatter(logging.Formatter):
    """Formatter with millisecond precision timestamps."""
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        ct = self.converter(record.created)
        s = time.strftime("%H:%M:%S", ct)
        return f"{s}.{int(record.msecs):03d}"


def create_debug_file_handler(file_path: str) -> logging.FileHandler:
    """Create file handler with DEBUG level and immediate flush.

    Args:
        file_path: Absolute path to log file

    Returns:
        Configured FlushingFileHandler ready to add to logger
    """
    handler = FlushingFileHandler(file_path, mode='w', encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(MillisecondFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    return handler
```

### Implementation (main.py integration)
```python
from datetime import datetime
from app.core.logger import create_debug_file_handler

# In extraction method:
def _start_extraction(self) -> None:
    # Create debug log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{input_path.stem}_debug_{timestamp}.log"
    log_path = input_path.parent / log_filename

    self.debug_file_handler = create_debug_file_handler(str(log_path))
    logging.getLogger().addHandler(self.debug_file_handler)

    logger.info(f"Debug log: {log_path}")
    self.status_label.configure(text=f"Logging to: {log_filename}")

def _cleanup_extraction(self) -> None:
    if self.debug_file_handler:
        logging.getLogger().removeHandler(self.debug_file_handler)
        self.debug_file_handler.close()
        self.debug_file_handler = None
```

### Test Requirements
```python
# app/tests/core/test_logger.py
def test_flushing_file_handler_immediate_write(tmp_path):
    """Verify FlushingFileHandler writes immediately without explicit flush."""
    log_file = tmp_path / "test.log"
    handler = FlushingFileHandler(str(log_file), mode='w')
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger("test_flush")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("test message")

    # File should contain message immediately (no flush() call)
    content = log_file.read_text()
    assert "test message" in content

    handler.close()

def test_create_debug_file_handler_format(tmp_path):
    """Verify debug handler uses millisecond timestamp format."""
    log_file = tmp_path / "debug.log"
    handler = create_debug_file_handler(str(log_file))

    logger = logging.getLogger("test_format")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.debug("test")
    handler.close()

    content = log_file.read_text()
    # Should match HH:MM:SS.mmm format
    assert re.match(r"\d{2}:\d{2}:\d{2}\.\d{3}", content)
```

### Commit Message
```
feat: add file-based DEBUG logging for real-time extraction monitoring

Add FlushingFileHandler that writes immediately to disk, enabling
reliable `tail -f` monitoring during extraction. GUI log viewer
blocks during heavy computation - file logging provides reliable
real-time visibility.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 3: Content Zone Detection Core [feature]

### User Story
As a DXF block analyzer, I want to automatically identify the "content zone" shape within a block definition so that I can derive trim values and reduce manual data entry.

### Acceptance Criteria
1. Detect closed polygons via LWPOLYLINE extraction
2. Detect closed polygons via LINE cycle detection (DFS)
3. **Skip LINE cycle detection if segment count > LINE_SEGMENT_THRESHOLD**
4. Calculate polygon areas using shoelace formula
5. Determine containment relationships using point-in-polygon
6. **Skip net area calculation if polygon count > POLYGON_COUNT_THRESHOLD**
7. **Timeout cycle detection after CYCLE_DETECTION_TIMEOUT_SECONDS**
8. Select shape with largest net area as content zone
9. Derive trim values from content zone bbox relative to block bbox
10. Return `ContentZoneData` TypedDict with results

### Data Types (types.py)
```python
from typing import TypedDict

Polygon = list[tuple[float, float]]
"""List of (x, y) vertices forming a closed polygon."""


class ContentZoneData(TypedDict):
    """Results from content zone detection analysis."""
    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
```

### Core Algorithm Structure (geometry.py)
```python
import time
from app.core.constants import (
    POLYGON_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    CYCLE_DETECTION_TIMEOUT_SECONDS,
)

def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
) -> ContentZoneData:
    """Detect content zone and calculate trim values.

    Performance safeguards:
    - Skips LINE cycle detection if > LINE_SEGMENT_THRESHOLD segments
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons
    - Times out cycle detection after CYCLE_DETECTION_TIMEOUT_SECONDS
    """
    block_name = block_def.name

    # Extract LWPOLYLINE shapes (always fast)
    lwpolyline_shapes = _extract_closed_lwpolylines(block_def)
    logger.debug(f"[{block_name}] Found {len(lwpolyline_shapes)} closed LWPOLYLINEs")

    # Check LINE segment count BEFORE extraction
    line_count = _count_line_segments(block_def)
    if line_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping LINE cycle detection: "
            f"{line_count} segments exceeds threshold {LINE_SEGMENT_THRESHOLD}"
        )
        line_cycle_shapes = []
    else:
        line_cycle_shapes = _extract_line_cycles(block_def, abort_event)
        logger.debug(f"[{block_name}] Found {len(line_cycle_shapes)} LINE cycles")

    # Combine all shapes
    all_shapes = lwpolyline_shapes + line_cycle_shapes
    polygon_count = len(all_shapes)

    if polygon_count == 0:
        logger.debug(f"[{block_name}] No closed shapes found")
        return _empty_content_zone_data()

    # Check polygon count BEFORE net area calculation
    if polygon_count > POLYGON_COUNT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{polygon_count} polygons exceeds threshold {POLYGON_COUNT_THRESHOLD}"
        )
        return _empty_content_zone_data()

    # Calculate net areas (O(n^3) but bounded by threshold)
    net_areas = _calculate_net_areas(all_shapes, abort_event)

    # Find largest net area and derive trim values
    # ... (implementation continues)


def _extract_line_cycles(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    """Extract closed cycles from LINE segments using DFS.

    Includes timeout protection and abort checkpoints.
    """
    start_time = time.perf_counter()
    iterations = 0

    # Build adjacency graph from LINE segments
    # ...

    # DFS with safeguards
    while stack:
        iterations += 1

        # Timeout check
        if time.perf_counter() - start_time > CYCLE_DETECTION_TIMEOUT_SECONDS:
            logger.warning(f"Cycle detection timeout after {iterations} iterations")
            break

        # Abort check every 1000 iterations
        if iterations % 1000 == 0 and abort_event and abort_event.is_set():
            raise GeometryAbortedError("Cycle detection aborted")

        # ... DFS logic


def _calculate_net_areas(
    polygons: list[Polygon],
    abort_event: threading.Event | None = None,
) -> list[tuple[Polygon, float]]:
    """Calculate net area for each polygon (own area minus contained areas).

    Complexity: O(n^3) where n = polygon count
    - n polygons
    - n containment checks per polygon
    - n vertices per containment check

    MUST be protected by POLYGON_COUNT_THRESHOLD check before calling.
    """
    # Abort check every 10 polygons
    for i, outer in enumerate(polygons):
        if i % 10 == 0 and abort_event and abort_event.is_set():
            raise GeometryAbortedError("Net area calculation aborted")
        # ... containment logic
```

### Test Assets Required
```bash
# Create test fixtures
uv run python app/tests/assets/create_content_zone_test.py
uv run python app/tests/assets/create_many_lines_test.py
```

Test scenarios:
- `content_zone_test.dxf`: Nested rectangles, chamfered shapes, mixed shapes
- `many_lines_test.dxf`: 500+ LINE segments to test threshold skip

### Test Requirements
```python
# app/tests/core/test_content_zone.py

def test_lwpolyline_detection():
    """Detect closed LWPOLYLINE shapes."""

def test_line_cycle_detection():
    """Detect cycles from connected LINE segments."""

def test_line_threshold_skip():
    """Skip LINE cycle detection when segment count exceeds threshold."""

def test_polygon_threshold_skip():
    """Skip net area calculation when polygon count exceeds threshold."""

def test_cycle_detection_timeout():
    """Timeout cycle detection within CYCLE_DETECTION_TIMEOUT_SECONDS."""

def test_nested_containment():
    """Correctly calculate net area for nested shapes."""

def test_trim_value_calculation():
    """Derive correct trim values from content zone bbox."""
```

### Commit Message
```
feat: add content zone detection with performance safeguards

Implement content zone detection for automatic trim value derivation.
Includes threshold checks (polygon=30, LINE=200) and timeout (5s)
to prevent O(n^3) and exponential DFS hangs on complex blocks.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 4: Union Bounding Box for Tied Net Areas [feature]

### User Story
As a DXF block analyzer, when multiple shapes have equal maximum net area, I want the system to combine all tied shapes into a union bounding box so that trim values represent the full usable area.

### Acceptance Criteria
1. Detect when multiple shapes tie for maximum net area
2. Calculate union bounding box encompassing all tied shapes
3. Derive trim values from union bbox (not arbitrary first shape)
4. Log when union is computed with shape count

### Implementation (geometry.py)
```python
def _get_union_bounding_box(polygons: list[Polygon]) -> tuple[float, float, float, float]:
    """Calculate union bounding box of multiple polygons."""
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)

    union_min_x, union_min_y, union_max_x, union_max_y = _get_polygon_bounding_box(polygons[0])

    for polygon in polygons[1:]:
        min_x, min_y, max_x, max_y = _get_polygon_bounding_box(polygon)
        union_min_x = min(union_min_x, min_x)
        union_min_y = min(union_min_y, min_y)
        union_max_x = max(union_max_x, max_x)
        union_max_y = max(union_max_y, max_y)

    return (union_min_x, union_min_y, union_max_x, union_max_y)


# In _detect_content_zone():
max_net_area = max(net_area for _, net_area in valid_shapes)
tied_shapes = [shape for shape, net_area in valid_shapes if net_area == max_net_area]

if len(tied_shapes) == 1:
    content_zone_bbox = _get_polygon_bounding_box(tied_shapes[0])
else:
    content_zone_bbox = _get_union_bounding_box(tied_shapes)
    logger.debug(f"[{block_name}] Content zone: union of {len(tied_shapes)} tied shapes")
```

### Test Asset Required
```bash
uv run python app/tests/assets/create_equal_area_test.py
```

`equal_area_test.dxf`: Block with 4 equal rectangles in corners

### Test Requirements
```python
def test_single_max_area():
    """Single shape with max area uses its bbox."""

def test_tied_max_area_union():
    """Multiple tied shapes use union bbox."""

def test_union_bbox_calculation():
    """Union bbox encompasses all input polygons."""
```

### Commit Message
```
feat: add union bounding box for tied net area content zones

When multiple shapes tie for maximum net area, compute union bounding
box encompassing all tied shapes for accurate trim value derivation.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 5: Excel Output Integration [feature]

### User Story
As a user, I want content zone detection results exported to the Excel file so that I can see suggested trim values and whether detection succeeded for each block.

### Acceptance Criteria
1. Five new columns added to Excel output:
   - block_suggested_trim_left
   - block_suggested_trim_right
   - block_suggested_trim_top
   - block_suggested_trim_bottom
   - block_content_zone_detected (TRUE/FALSE)
2. Columns formatted with appropriate width and number format
3. Empty values for blocks where detection was skipped
4. Follow field naming convention from app_docs/005-field-naming-convention.md

### Implementation (excel_writer.py)
```python
from app.core.constants import (
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
)

# Add columns to COLUMN_ORDER
COLUMN_ORDER = [
    # ... existing columns ...
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
]
```

### Implementation (excel_formatting.py)
```python
# Add column formatting
COLUMN_FORMATS = {
    # ... existing formats ...
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: {"width": 12, "number_format": "0.00"},
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: {"width": 12, "number_format": "0.00"},
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: {"width": 12, "number_format": "0.00"},
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: {"width": 12, "number_format": "0.00"},
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: {"width": 15},
}
```

### Test Requirements
```python
def test_content_zone_columns_in_output():
    """Excel output includes all 5 content zone columns."""

def test_trim_values_numeric_format():
    """Trim value columns formatted as 2 decimal places."""

def test_detection_flag_boolean():
    """Content zone detected column shows TRUE/FALSE."""
```

### Commit Message
```
feat: add content zone columns to Excel output

Add suggested_trim_left/right/top/bottom and content_zone_detected
columns to Excel export. Follows field naming convention.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 6: Abort Extraction Option [feature]

### User Story
As a user, I want to abort a running extraction within 1-2 seconds so that I can stop processing when I selected the wrong file or see errors.

### Acceptance Criteria
1. Abort button replaces Browse/Extract during extraction
2. Clicking Abort stops extraction within 1-2 seconds
3. Abort checkpoints in:
   - Block definition loop (every 25 blocks)
   - Modelspace entity loop (every 500 entities)
   - LINE cycle DFS (every 1000 iterations)
   - Net area calculation (every 10 polygons)
4. No Excel file generated when aborted
5. UI restores for new extraction attempt

### Implementation (extractor.py)
```python
class ExtractionAbortedError(Exception):
    """Raised when extraction is aborted by user."""
    pass


def _check_abort(abort_event: threading.Event | None, context: str) -> None:
    """Check if abort requested and raise if so."""
    if abort_event and abort_event.is_set():
        logger.info(f"Extraction aborted during {context}")
        raise ExtractionAbortedError(f"Aborted during {context}")
```

### Implementation (geometry.py)
```python
class GeometryAbortedError(Exception):
    """Raised when geometry analysis is aborted."""
    pass


def _check_geometry_abort(abort_event: threading.Event | None) -> None:
    """Check abort in geometry loops."""
    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Geometry analysis aborted")
```

### Implementation (main.py)
```python
def _start_extraction(self) -> None:
    self.abort_event = threading.Event()
    self.browse_button.pack_forget()
    self.extract_button.pack_forget()
    self.abort_button.pack(side="left", padx=10)

def _abort_extraction(self) -> None:
    if self.abort_event:
        self.abort_event.set()
    self.abort_button.configure(state="disabled")
    self.status_label.configure(text="Aborting...")

def _restore_ui(self) -> None:
    self.abort_button.pack_forget()
    self.browse_button.pack(side="left", padx=10)
    self.extract_button.pack(side="left", padx=10)
    self.abort_event = None
```

### Test Requirements
```python
# app/tests/core/extractor/test_extractor_abort.py

def test_abort_during_block_loop():
    """Abort during block definition processing."""

def test_abort_during_geometry():
    """Abort during geometry analysis."""

def test_abort_responsiveness():
    """Abort completes within 2 seconds."""

def test_no_excel_on_abort():
    """No Excel file created when aborted."""
```

### Commit Message
```
feat: add abort extraction option with responsive cancellation

Add abort button with checkpoints in block loop, entity loop,
LINE cycle DFS, and net area calculation. Ensures abort completes
within 1-2 seconds even during expensive algorithms.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## User Story 7: Live Log Viewer Panel [feature]

### User Story
As a user, I want a log viewer in the GUI showing messages in real-time so that I can monitor progress without terminal access.

### Acceptance Criteria
1. GUI displays log viewer panel with monospace font
2. Log level dropdown: DEBUG, INFO, WARNING, ERROR
3. Messages polled from queue every 100ms
4. Auto-scrolls to latest entry
5. Terminal/stdout continues receiving all logs

**NOTE:** File-based logging (US-2) is the more reliable solution for debugging hangs since the GUI log viewer will block during heavy computation. However, the log viewer provides convenience for normal operation.

### Implementation Summary
- Add `CTkTextbox` with `state="disabled"`, monospace font
- Add `CTkOptionMenu` for log level selection
- Create `queue.Queue()` and `QueueHandler`
- Poll queue with `self.after(100, self._poll_log_queue)`

### Commit Message
```
feat: add live log viewer panel to GUI

Add log viewer panel with level filtering. Note: GUI blocks during
heavy computation - use file-based logging for hang diagnosis.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Implementation Checklist

```
[ ] US-0: Git Rebuild Setup
    [ ] Create backup tag
    [ ] Create reference branch
    [ ] Create rebuild branch from ad25eab
    [ ] Copy retrospective docs
    [ ] Commit docs

[ ] US-1: Performance Threshold Constants
    [ ] Add constants to constants.py
    [ ] Add Excel column constants
    [ ] Add tests for constant values
    [ ] Commit

[ ] US-2: File-Based Debug Logging
    [ ] Add FlushingFileHandler class
    [ ] Add create_debug_file_handler function
    [ ] Integrate with main.py
    [ ] Add tests
    [ ] Commit

[ ] US-3: Content Zone Detection Core
    [ ] Add types to types.py
    [ ] Implement polygon extraction
    [ ] Implement LINE cycle detection with threshold
    [ ] Implement net area calculation with threshold
    [ ] Implement timeout protection
    [ ] Create test assets
    [ ] Add comprehensive tests
    [ ] Commit

[ ] US-4: Union Bounding Box
    [ ] Add _get_union_bounding_box function
    [ ] Update _detect_content_zone for ties
    [ ] Create equal_area_test.dxf
    [ ] Add tests
    [ ] Commit

[ ] US-5: Excel Output Integration
    [ ] Add columns to excel_writer.py
    [ ] Add formatting to excel_formatting.py
    [ ] Add tests
    [ ] Commit

[ ] US-6: Abort Extraction Option
    [ ] Add exception classes
    [ ] Add _check_abort functions
    [ ] Add abort checkpoints to extractor.py
    [ ] Add abort checkpoints to geometry.py
    [ ] Add UI state management to main.py
    [ ] Add tests
    [ ] Commit

[ ] US-7: Live Log Viewer
    [ ] Add log viewer panel
    [ ] Add level dropdown
    [ ] Add queue polling
    [ ] Commit
```

## Validation Commands

Run after each user story:
```bash
uv run pytest app/tests/ -v
uv run mypy app/
uv run ruff check app/
```

Run full validation after US-6:
```bash
uv run pytest app/tests/core/test_content_zone.py -v
uv run pytest app/tests/core/test_geometry.py -v
uv run pytest app/tests/core/extractor/test_extractor_abort.py -v
uv run pytest --cov=app/core app/tests/
```

## Recommendations

1. **Implement US-0 through US-2 first** - Git setup, constants, and logging are prerequisites
2. **US-3 is the complex one** - Take time, test thoroughly with fixtures
3. **Reference old branch** - Use `git show content-zone-reference:path/file` when stuck
4. **Test with production files** after US-3 - Small test files won't reveal issues
5. **For hang diagnosis** - Use file logging (`tail -f`) rather than GUI log viewer

## Next Steps

1. Execute US-0 git commands to set up clean branch
2. Implement US-1 (constants) - quick win, establishes foundation
3. Implement US-2 (logging) - enables monitoring for US-3 development
4. Implement US-3 (core detection) - the main feature
5. Implement US-4 (union bbox) - enhancement to core
6. Implement US-5 (Excel output) - export results
7. Implement US-6 (abort option) - user control
8. Implement US-7 (log viewer) - GUI monitoring
