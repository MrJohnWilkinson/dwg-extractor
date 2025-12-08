# Feature: Abort Extraction Option

## Feature Description
This feature adds the ability for users to abort a running DXF extraction process within 1-2 seconds. When processing large or incorrect files, users need a way to cancel the operation without waiting for completion or forcibly closing the application. The implementation uses a threading.Event signal with strategically placed abort checkpoints throughout the extraction pipeline.

## User Story
As a user
I want to abort a running extraction within 1-2 seconds
So that I can stop processing when I selected the wrong file or see errors

## Problem Statement
Currently, once extraction begins, users must wait for the entire process to complete even if they realize they selected the wrong file or encounter unexpected behavior. Large DXF files with complex geometry can take significant time to process, leaving users with no option but to wait or force-close the application, potentially losing application state.

## Solution Statement
Implement an abort mechanism using `threading.Event` that can be checked at regular intervals during extraction. The solution includes:
1. An `ExtractionAbortedError` exception class in extractor.py
2. A `_check_abort()` helper function for consistent abort checking
3. Abort checkpoints at strategic locations (every 25 blocks, every 500 entities)
4. UI changes to show an Abort button during extraction that replaces Browse/Extract
5. Integration with existing `GeometryAbortedError` in geometry.py (already implemented in US-3)

## Relevant Files
Use these files to implement the feature:

- `app/core/extractor.py` - Main extraction logic; add `ExtractionAbortedError`, `_check_abort()` helper, and abort checkpoints in block definition and modelspace loops
- `app/core/geometry.py` - Already has `GeometryAbortedError` and abort checkpoints from US-3; no changes needed
- `app/main.py` - GUI application; add abort button, event handling, and UI state management
- `app/core/constants.py` - Add abort-related constants (MSG_ABORTING, MSG_ABORTED)

### New Files
- `app/tests/core/extractor/test_extractor_abort.py` - Unit tests for abort functionality

## Implementation Plan

### Phase 1: Foundation
1. Add abort-related UI message constants to `constants.py`
2. Create `ExtractionAbortedError` exception class in `extractor.py`
3. Create `_check_abort()` helper function in `extractor.py`

### Phase 2: Core Implementation
1. Modify `extract_blocks()` function signature to accept optional `abort_event` parameter
2. Add abort checkpoints in block definition loop (every 25 blocks)
3. Add abort checkpoints in modelspace entity loop (every 500 entities)
4. Pass abort_event to geometry functions that already support it (`_detect_content_zone()`)

### Phase 3: Integration
1. Add `abort_event` instance variable to `DXFExtractorApp` class
2. Create Abort button widget (initially hidden)
3. Implement `_start_extraction()` to show abort button and create event
4. Implement `_abort_extraction()` to set abort event and update UI
5. Implement `_restore_ui()` to restore normal button state
6. Handle `ExtractionAbortedError` and `GeometryAbortedError` in worker thread
7. Ensure no Excel file is generated when aborted

## Step by Step Tasks

### Step 1: Add Constants for Abort Messages
- Add `MSG_ABORTING: str = "Aborting..."` to `app/core/constants.py`
- Add `MSG_ABORTED: str = "Extraction aborted"` to `app/core/constants.py`

### Step 2: Add ExtractionAbortedError and _check_abort Helper
- Add `import threading` to extractor.py imports
- Add `ExtractionAbortedError` exception class after the logger initialization
- Add `_check_abort(abort_event: threading.Event | None, context: str) -> None` helper function

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

### Step 3: Modify extract_blocks Function Signature
- Add `abort_event: threading.Event | None = None` parameter to `extract_blocks()` function
- Update function docstring to document the new parameter

### Step 4: Add Abort Checkpoints in Block Definition Loop
- Add abort check every 25 blocks in the block definition analysis loop
- Use counter variable to track iterations
- Call `_check_abort(abort_event, "block definition analysis")`

```python
# In block definition loop:
block_count = 0
for block_def in doc.blocks:
    block_count += 1
    if block_count % 25 == 0:
        _check_abort(abort_event, "block definition analysis")
    # ... existing logic
```

### Step 5: Add Abort Checkpoints in Modelspace Entity Loop
- Add abort check every 500 entities in the modelspace entity loop
- Use counter variable to track iterations
- Call `_check_abort(abort_event, "modelspace entity processing")`

```python
# In modelspace loop:
entity_idx = 0
for entity in msp:
    entity_idx += 1
    if entity_idx % 500 == 0:
        _check_abort(abort_event, "modelspace entity processing")
    # ... existing logic
```

### Step 6: Pass abort_event to Geometry Functions
- Pass `abort_event` to `_detect_content_zone()` calls (already supports it from US-3)
- The geometry module already handles `GeometryAbortedError` internally

```python
content_zone_result = _detect_content_zone(block_def, bbox, abort_event)
```

### Step 7: Create Abort Button in GUI
- Add `self.abort_event: threading.Event | None = None` to `__init__`
- Create abort button in `_create_widgets()` (initially not packed)

```python
# In _create_widgets():
self.abort_button = ctk.CTkButton(
    button_frame,
    text="Abort",
    width=120,
    command=self._abort_extraction,
    fg_color="red",
    hover_color="darkred",
)
# Don't pack - will be shown during extraction
```

### Step 8: Implement UI State Management Methods
- Implement `_start_extraction()` method to swap buttons and create event
- Implement `_abort_extraction()` method to signal abort
- Implement `_restore_ui()` method to restore normal state

```python
def _start_extraction(self) -> None:
    """Prepare UI for extraction - show abort button, create event."""
    self.abort_event = threading.Event()
    self.browse_button.pack_forget()
    self.extract_button.pack_forget()
    self.abort_button.pack(side="left", padx=10)

def _abort_extraction(self) -> None:
    """Handle abort button click."""
    if self.abort_event:
        self.abort_event.set()
    self.abort_button.configure(state="disabled")
    self.status_label.configure(text=MSG_ABORTING)
    self.logger.info("User requested extraction abort")

def _restore_ui(self) -> None:
    """Restore UI to normal state after extraction completes or aborts."""
    self.abort_button.pack_forget()
    self.browse_button.pack(side="left", padx=(0, 10))
    self.extract_button.pack(side="left")
    self.abort_event = None
```

### Step 9: Update _extract_blocks Method
- Call `_start_extraction()` at the beginning
- Call `_restore_ui()` in finally block instead of re-enabling buttons directly

### Step 10: Update _extraction_worker to Handle Abort
- Pass `self.abort_event` to `extract_blocks()` call
- Add exception handler for `ExtractionAbortedError`
- Add exception handler for `GeometryAbortedError` (imported from geometry)
- Ensure no Excel file is generated when aborted
- Call `_restore_ui()` via `self.after()` in finally block

```python
from core.extractor import extract_blocks, ExtractionAbortedError
from core.geometry import GeometryAbortedError

# In _extraction_worker:
try:
    extraction_result = extract_blocks(self.selected_file_path, self.abort_event)
    # ... rest of processing
except ExtractionAbortedError:
    self.logger.info("Extraction aborted by user")
    self._update_progress(0, MSG_ABORTED)
except GeometryAbortedError:
    self.logger.info("Extraction aborted during geometry processing")
    self._update_progress(0, MSG_ABORTED)
finally:
    # ... cleanup
    self.after(0, self._restore_ui)
```

### Step 11: Create Test File for Abort Functionality
- Create `app/tests/core/extractor/test_extractor_abort.py`
- Implement test class `TestExtractionAbort`

### Step 12: Implement test_abort_raises_exception
- Test that setting abort_event before extraction raises `ExtractionAbortedError`

```python
def test_abort_raises_exception(self) -> None:
    """Test that abort event causes ExtractionAbortedError."""
    abort_event = threading.Event()
    abort_event.set()  # Pre-set to trigger immediately

    with pytest.raises(ExtractionAbortedError):
        extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)
```

### Step 13: Implement test_abort_during_block_loop
- Test abort during block definition processing with a file that has many blocks

```python
def test_abort_during_block_loop(self) -> None:
    """Test abort during block definition processing."""
    abort_event = threading.Event()
    abort_event.set()

    with pytest.raises(ExtractionAbortedError, match="block definition"):
        extract_blocks("app/tests/assets/many_lines_test.dxf", abort_event)
```

### Step 14: Implement test_abort_during_entity_loop
- Test abort during modelspace entity processing

```python
def test_abort_during_entity_loop(self) -> None:
    """Test abort during modelspace entity processing."""
    abort_event = threading.Event()

    # Use a file with many entities
    # Set abort after a short delay to let block loop complete
    def delayed_abort():
        time.sleep(0.01)
        abort_event.set()

    thread = threading.Thread(target=delayed_abort)
    thread.start()

    with pytest.raises(ExtractionAbortedError):
        extract_blocks("app/tests/assets/many_lines_test.dxf", abort_event)

    thread.join()
```

### Step 15: Implement test_no_abort_when_event_not_set
- Test normal extraction completes when abort_event is provided but not set

```python
def test_no_abort_when_event_not_set(self) -> None:
    """Test extraction completes normally when abort not triggered."""
    abort_event = threading.Event()
    # Don't set the event

    result = extract_blocks("app/tests/assets/sample_drawing.dxf", abort_event)

    assert result["block_counts"]["VALVE_GATE"] == 10
```

### Step 16: Implement test_abort_event_none_works
- Test extraction works normally when abort_event is None (default)

```python
def test_abort_event_none_works(self) -> None:
    """Test extraction works when abort_event is None."""
    result = extract_blocks("app/tests/assets/sample_drawing.dxf", None)

    assert len(result["block_counts"]) == 3
```

### Step 17: Implement test_check_abort_helper
- Test the `_check_abort` helper function directly

```python
def test_check_abort_helper_raises_when_set(self) -> None:
    """Test _check_abort raises when event is set."""
    from core.extractor import _check_abort

    abort_event = threading.Event()
    abort_event.set()

    with pytest.raises(ExtractionAbortedError, match="test context"):
        _check_abort(abort_event, "test context")

def test_check_abort_helper_passes_when_not_set(self) -> None:
    """Test _check_abort does nothing when event not set."""
    from core.extractor import _check_abort

    abort_event = threading.Event()
    # Should not raise
    _check_abort(abort_event, "test context")

def test_check_abort_helper_passes_when_none(self) -> None:
    """Test _check_abort does nothing when event is None."""
    from core.extractor import _check_abort

    # Should not raise
    _check_abort(None, "test context")
```

### Step 18: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Test `ExtractionAbortedError` is raised when abort_event is set
- Test `_check_abort()` helper function behavior with set/unset/None event
- Test extraction completes normally when abort_event is not set
- Test extraction completes normally when abort_event is None
- Test abort during block definition loop raises correct exception
- Test abort during modelspace entity loop raises correct exception

### Integration Tests
- Test that geometry abort (via `GeometryAbortedError`) propagates correctly
- Test that no partial results are returned on abort

### Edge Cases
- Abort event set before extraction starts (immediate abort)
- Abort event set during geometry processing (handled by geometry.py)
- Abort event never set (normal completion)
- Abort event is None (backwards compatibility)
- Small files that complete before checkpoint is reached

### Playwright MCP Tests
- Not applicable for this feature (abort timing is non-deterministic in E2E tests)
- Manual GUI testing recommended for abort button visibility and responsiveness

## Acceptance Criteria
1. Abort button appears and replaces Browse/Extract buttons during extraction
2. Clicking Abort stops extraction within 1-2 seconds
3. Abort checkpoints exist in block definition loop (every 25 blocks)
4. Abort checkpoints exist in modelspace entity loop (every 500 entities)
5. LINE cycle DFS abort checkpoints already in place (US-3)
6. Net area calculation abort checkpoints already in place (US-3)
7. No Excel file is generated when extraction is aborted
8. UI restores to normal state after abort (Browse/Extract buttons visible)
9. Status label shows "Aborting..." when abort is clicked
10. Status label shows "Extraction aborted" after abort completes
11. All existing tests continue to pass

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Run tests to validate the feature works with zero regressions
    - `uv run pytest app/tests/`
    - `uv run mypy app/`
    - `uv run ruff check app/`
    - `uv run ruff format app/`
    - `uv run ruff check app/ --fix`

## Notes
- The geometry.py module already has `GeometryAbortedError` and abort checkpoints in `_extract_line_cycles()` (every 1000 iterations) and `_calculate_net_areas()` (every 10 polygons) from US-3
- The `extract_blocks()` function signature change is backwards compatible since `abort_event` defaults to `None`
- GUI testing should be done manually in WSL2 environment with X server, or on Windows
- Checkpoint intervals (25 blocks, 500 entities) are chosen to balance responsiveness (1-2 second abort time) with performance overhead
- The abort button uses red color (`fg_color="red"`) to visually distinguish it from normal actions
