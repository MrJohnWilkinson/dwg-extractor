# Live Log Viewer User Story Evaluation

## Executive Summary

The user story is **well-designed and appropriate** for this codebase. It follows DRY principles by reusing existing logger infrastructure, aligns with established naming conventions, and correctly identifies minimal modification scope. One addition is recommended: include log level selection in the GUI to meet the user's stated requirement.

## Table Summary

| Aspect | Assessment | Notes |
|--------|------------|-------|
| DRY Compliance | Excellent | Reuses existing `setup_logger()`, adds factory without duplication |
| Naming Conventions | Aligned | Existing pattern: `setup_logger()`, new: `create_queue_handler()` |
| Thread Safety | Correct | QueueHandler + `self.after()` is the standard Tkinter pattern |
| Scope | Appropriate | 3 files modified, no new dependencies |
| Log Level Control | **Missing** | User requested GUI log level setting - add dropdown |
| Existing Patterns | Compatible | `_update_progress()` already uses `self.after()` for thread-safe UI |

## Relevant Files

- **app/main.py** (lines 1-334): GUI application entry point. Contains `DXFExtractorApp` class with existing thread-safe patterns (`self.after()` at lines 226-227, 231, 241, 260). Will add log viewer panel and queue polling.

- **app/core/logger.py** (lines 1-255): Centralized logging module. Has `setup_logger()` (lines 127-169), `JsonFormatter`, env-based configuration. Will add `create_queue_handler()` factory.

- **app/core/extractor.py** (lines 1-1170): DXF extraction logic. Module-level logger at line 43. Currently has 35 logger calls (mix of info/debug/error). Will add block-by-block progress logging.

- **app/core/constants.py** (lines 1-128): Application constants including UI messages (`MSG_PROCESSING`, `MSG_SUCCESS`). May add log-related constants if needed.

## Alignment with Existing Patterns

### Logger Module Design
The existing `logger.py` uses factory pattern with environment configuration:
```python
# Existing pattern (line 127-169)
def setup_logger(name: str) -> logging.Logger:
    log_level = _get_log_level_from_env()
    ...
```

Proposed `create_queue_handler()` follows this pattern naturally. No architectural conflict.

### Thread-Safe UI Updates
The codebase already implements thread-safe GUI updates:
```python
# Existing pattern (main.py:229-231)
def _update_progress(self, value: float, message: str) -> None:
    self.after(0, lambda: self._update_progress_ui(value, message))
```

The proposed 100ms queue polling with `self.after()` is identical in approach.

### Naming Conventions
Following `app_docs/005-field-naming-convention.md`:
- **Function names**: `setup_logger`, `create_queue_handler` (verb_noun pattern)
- **GUI widgets**: `self.file_entry`, `self.progress_bar`, `self.status_label` -> propose `self.log_viewer`
- **Constants**: `MSG_PROCESSING`, `MSG_SUCCESS` -> propose `LOG_POLL_INTERVAL_MS = 100`

## Gap Analysis: Log Level Control

**User Requirement (quoted):**
> "I also want to be able to set the log level output in the gui"

**Current Story Status:** Out of scope

**Recommendation:** Move log level dropdown to In Scope. Implementation:

1. Add `CTkOptionMenu` with values: DEBUG, INFO, WARNING, ERROR
2. Store selection in instance variable `self.log_level: str`
3. Pass level to `create_queue_handler()`
4. Allow runtime level changes via `handler.setLevel()`

Widget naming following existing patterns:
```python
self.log_level_dropdown  # CTkOptionMenu
self.log_level_label     # Optional label
```

## Proposed Logger Enhancement

```python
# Addition to app/core/logger.py
def create_queue_handler(
    log_queue: queue.Queue[logging.LogRecord],
    level: int = logging.INFO
) -> logging.Handler:
    """
    Create a QueueHandler for thread-safe log delivery to GUI.

    Args:
        log_queue: Queue to receive log records
        level: Minimum log level (default: INFO)

    Returns:
        Configured QueueHandler
    """
    handler = logging.handlers.QueueHandler(log_queue)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    return handler
```

## Extractor Progress Logging

Current logging in `extractor.py` is coarse-grained. Suggested additions:

| Location | Current | Proposed Addition |
|----------|---------|-------------------|
| Line 704 | `Starting block extraction...` | Keep as-is |
| Line 762 | `Analyzing block definitions...` | Add: block count progress |
| Line 871 | `Analyzing modelspace entities...` | Add: entity progress |
| Line 1113 | Color analysis | Add: `Extracted X/Y color records` |

Example granular logging:
```python
# After line 834
if entity_count % 100 == 0:
    logger.info(f"Processed {entity_count} entities...")
```

## Recommendations

1. **Add log level dropdown to In Scope** - User explicitly requested this
2. **Keep elapsed time logging** - Use existing `timed_block()` context manager from `logger.py`
3. **Consider future extensibility** - Log level dropdown can later support runtime level changes
4. **Test in WSL** - As noted, GUI tests unreliable; manual testing with `bash scripts/start.sh` is correct approach

## Next Steps

1. Update user story to include log level dropdown in In Scope
2. Define widget placement in GUI layout (suggest: above log viewer panel)
3. Proceed with implementation following the 3-file modification plan
4. Add integration test for queue-based logging (non-GUI)
