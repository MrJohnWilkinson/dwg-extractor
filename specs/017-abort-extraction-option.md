# Feature: Abort Extraction Option

## Feature Description
Add an "Abort" button to the DXF Block Extractor GUI that allows users to cancel an in-progress extraction operation. When aborted, the extraction process is cleanly terminated without producing incomplete Excel files, while preserving all log output up to the abort point for debugging and progress visibility. The logs should clearly indicate how far the extraction progressed before being stopped.

## User Story
As a DXF Block Extractor user
I want to abort a running extraction operation
So that I can stop processing large files when I need to make corrections or when I realize I selected the wrong file

## Problem Statement
Currently, once a DXF extraction begins, users must wait for it to complete or force-close the application. For large DXF files with thousands of entities, this can take considerable time. Users have no way to cancel the operation if they:
- Selected the wrong file
- Need to make changes to the DXF file first
- Want to stop processing due to time constraints
- See errors in the log that indicate a problem

## Solution Statement
Implement a cooperative cancellation mechanism using Python's threading.Event:
1. Add an "Abort" button to the UI that appears during extraction (replacing or alongside the Extract button)
2. Use a threading.Event to signal cancellation to the background extraction worker
3. Check the cancellation flag at key points during extraction (between major processing phases)
4. When aborted, skip Excel file generation entirely and log the abort with progress statistics
5. Preserve all log messages for user review and copyability
6. Re-enable the UI for a new extraction attempt

## Relevant Files
Use these files to implement the feature:

- `app/main.py` - Main GUI application containing the extraction workflow, button management, and threading logic. This is where the Abort button UI and cancellation signaling will be added.
- `app/core/extractor.py` - Core extraction logic with `extract_blocks()` function. This module will need to accept and check a cancellation event at processing checkpoints.
- `app/core/constants.py` - UI message constants. New abort-related messages will be added here.
- `app/core/logger.py` - Logging infrastructure (read-only reference). Used to understand existing logging patterns for abort messages.
- `app/tests/core/extractor/test_extractor_core.py` - Core extractor tests. New tests for abort handling will follow this pattern.

### New Files
- `app/tests/core/extractor/test_extractor_abort.py` - New test file specifically for abort/cancellation behavior testing.

## Implementation Plan
### Phase 1: Foundation
Add the cancellation signaling infrastructure:
1. Create a threading.Event instance in DXFExtractorApp to signal abort requests
2. Define new UI message constants for abort states (MSG_ABORTED, MSG_ABORTING)
3. Create a custom exception class `ExtractionAbortedError` for clean abort signaling

### Phase 2: Core Implementation
Modify the extraction worker to support cancellation:
1. Add an optional `abort_event` parameter to `extract_blocks()` function
2. Insert cancellation checkpoint checks at key points in the extraction loop:
   - After DXF file loading
   - During block definition analysis (every N blocks)
   - During modelspace entity analysis (every N entities)
   - Before color analysis extraction
3. Log progress statistics when abort is detected (files processed, blocks found, entities analyzed)
4. Raise `ExtractionAbortedError` when abort is detected

### Phase 3: Integration
Connect the UI controls to the cancellation mechanism:
1. Add an "Abort" button to the button_frame (hidden by default)
2. Show Abort button and hide Browse/Extract buttons during extraction
3. Handle Abort button click to set the abort_event
4. Catch `ExtractionAbortedError` in the worker thread and skip Excel generation
5. Update status label and progress bar to reflect aborted state
6. Restore UI state to allow new extraction attempts

## Step by Step Tasks

### Step 1: Add UI Message Constants
- Add `MSG_ABORTING` and `MSG_ABORTED` constants to `app/core/constants.py`
- Follow existing naming pattern (MSG_* prefix)

### Step 2: Create ExtractionAbortedError Exception
- Add `ExtractionAbortedError` class to `app/core/extractor.py`
- Make it inherit from `Exception` with an optional message containing abort statistics

### Step 3: Modify extract_blocks() Function Signature
- Add optional `abort_event: threading.Event | None = None` parameter to `extract_blocks()`
- Document the parameter in the docstring

### Step 4: Add Cancellation Checkpoints to Extractor
- Create a helper function `_check_abort(abort_event, context_msg)` that:
  - Checks if abort_event is set
  - Logs an INFO message with context (e.g., "Abort requested during block analysis")
  - Raises `ExtractionAbortedError` with statistics
- Insert checkpoint calls at:
  - After `doc = ezdxf.readfile(file_path)`
  - Inside block definition loop (check every 25 blocks)
  - Inside modelspace entity loop (check every 500 entities)
  - Before `extract_color_analysis(doc)` call

### Step 5: Add Progress Tracking to Extractor
- Track current progress counts in local variables:
  - `blocks_processed` counter
  - `entities_processed` counter
- Include these in the abort exception message for log visibility

### Step 6: Create Abort Button in GUI
- Add `self.abort_button` CTkButton to button_frame (initially hidden with `pack_forget()`)
- Configure with text="Abort", width=120, command=self._abort_extraction
- Add `self.abort_event: threading.Event | None = None` instance variable

### Step 7: Implement UI State Management for Extraction
- Modify `_extract_blocks()` to:
  - Create new `threading.Event()` for abort signaling
  - Hide Browse and Extract buttons
  - Show Abort button
- Create `_restore_ui_after_extraction()` helper to:
  - Hide Abort button
  - Show and enable Browse and Extract buttons
  - Reset abort_event to None

### Step 8: Implement Abort Button Handler
- Create `_abort_extraction()` method that:
  - Sets the abort_event if it exists
  - Updates status label to MSG_ABORTING
  - Disables the Abort button (prevent multiple clicks)
  - Logs "User requested extraction abort"

### Step 9: Pass Abort Event to Extraction Worker
- Modify `_extraction_worker()` to pass `self.abort_event` to `extract_blocks()`
- Add try/except for `ExtractionAbortedError`:
  - Log abort with statistics from exception message
  - Update status to MSG_ABORTED
  - Skip Excel generation and success dialog
  - Do NOT show error dialog (abort is intentional, not an error)

### Step 10: Ensure Clean UI Restoration on Abort
- Modify the finally block in `_extraction_worker()` to call `_restore_ui_after_extraction()`
- Ensure progress bar is reset on abort
- Ensure logs remain visible and scrollable

### Step 11: Write Unit Tests for Abort Functionality
- Create `app/tests/core/extractor/test_extractor_abort.py`
- Test cases:
  - `test_extract_blocks_without_abort_event` - existing behavior unchanged
  - `test_extract_blocks_with_abort_during_loading` - abort immediately after file load
  - `test_extract_blocks_abort_raises_exception` - verify ExtractionAbortedError is raised
  - `test_abort_preserves_partial_progress_info` - exception contains progress stats

### Step 12: Update Extractor Core Tests
- Ensure existing tests in `test_extractor_core.py` pass with new optional parameter
- Add test that default `abort_event=None` works correctly

### Step 13: Run Validation Commands
- Run full test suite to ensure no regressions
- Run type checking to verify typing is correct
- Run linting to ensure code quality

## Testing Strategy
### Unit Tests
- Test that `extract_blocks()` works normally when abort_event is None (backward compatibility)
- Test that `extract_blocks()` raises `ExtractionAbortedError` when abort_event is set
- Test that abort exception contains meaningful progress information
- Test the `_check_abort()` helper function directly

### Integration Tests
- Test that setting abort_event during extraction stops processing
- Test that no Excel file is created when extraction is aborted
- Test that logs contain abort-related messages

### Edge Cases
- Abort requested before extraction starts (should be no-op)
- Abort requested right as extraction completes (race condition handling)
- Multiple rapid abort clicks (button is disabled after first click)
- Abort during different phases (file load, block analysis, entity analysis, color analysis)
- Very small file that completes before abort can be processed

### Playwright MCP Tests
GUI testing is skipped in WSL environment per project README. Manual testing should verify:
- Abort button appears during extraction
- Abort button disappears after abort completes
- Browse/Extract buttons return after abort
- Log viewer shows abort messages
- Progress bar resets after abort

## Acceptance Criteria
1. An "Abort" button appears in the UI when extraction is in progress
2. Clicking "Abort" stops the extraction within 1-2 seconds (at next checkpoint)
3. No Excel file is generated when extraction is aborted
4. All log messages up to the abort point are visible in the log viewer
5. The log shows how many blocks and entities were processed before abort
6. The status label shows "Extraction aborted" after abort completes
7. Browse and Extract buttons are re-enabled after abort
8. The application remains stable and can perform a new extraction after abort
9. Existing extraction functionality works unchanged when abort is not used
10. All existing tests pass without modification

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/extractor/` - Run extractor tests including new abort tests
- `uv run pytest app/tests/` - Run full test suite to verify no regressions
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting

## Notes
- The cooperative cancellation approach using threading.Event is preferred over thread.interrupt() or similar mechanisms because it allows for clean resource cleanup and predictable behavior.
- Checkpoint frequency (every 25 blocks, every 500 entities) is a balance between responsiveness and performance overhead. These values can be tuned based on real-world usage.
- The feature uses existing log levels (INFO for abort messages) rather than creating custom levels, following the DRY principle specified in requirements.
- Consider future enhancement: Add a "Cancel" confirmation dialog if extraction is nearly complete (>90% progress) to prevent accidental aborts.
