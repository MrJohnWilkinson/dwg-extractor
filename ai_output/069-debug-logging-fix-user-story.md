# User Story: Enable Dynamic Source Logger Level Control

## Executive Summary
As a developer debugging extraction issues, I need DEBUG-level logs to appear when I select "DEBUG" in the GUI dropdown, so I can see detailed timing diagnostics and trace extraction problems. Currently, DEBUG logs are silently discarded because source loggers are hardcoded to INFO level, making the GUI dropdown ineffective for enabling verbose logging.

## Table Summary

| Aspect | Current State | Target State |
|--------|---------------|--------------|
| GUI Log Level Dropdown | Display filter only | Controls source logger levels |
| Source Logger Levels | Hardcoded to INFO | Dynamically set via GUI |
| DEBUG Log Visibility | Never shown (discarded) | Shown when DEBUG selected |
| Files Modified | 0 | 1 (main.py) |
| Risk Level | N/A | Low - additive change |

## Relevant Files

- **app/main.py** (lines 1049-1054) - `_on_log_level_change()` method is currently a no-op; needs to set source logger levels
- **app/core/logger.py** (lines 271-313) - `setup_logger()` creates loggers at INFO level; no changes needed for Option A
- **app/core/extractor.py** (line 56) - Uses `setup_logger(__name__)` creating `app.core.extractor` logger
- **app/core/geometry.py** (line 47) - Uses `setup_logger(__name__)` creating `app.core.geometry` logger

## User Story

**As a** developer or power user
**I want** the GUI log level dropdown to control which log messages are captured
**So that** I can see DEBUG-level timing diagnostics when troubleshooting extraction performance

### Acceptance Criteria

1. When user selects "DEBUG" in the log level dropdown, DEBUG messages from all modules appear in the log viewer
2. When user selects "INFO" (or higher), DEBUG messages are suppressed as before
3. Change takes effect immediately without restarting the application
4. File log level dropdown independently controls file handler verbosity

## In Scope

- Modify `_on_log_level_change()` in main.py to set source logger levels
- Set levels for known source loggers: `app.core.extractor`, `app.core.geometry`, `app.main`
- Optionally set root logger level for comprehensive coverage
- Existing GUI dropdown behavior (display filtering) continues to work

## Out of Scope

- Changes to `setup_logger()` in logger.py (Option B approach)
- Adding new GUI controls or UI changes
- Modifying log message formats or content
- Environment variable behavior changes
- File handler level synchronization (already functional)

## Implementation

```python
# In app/main.py, modify _on_log_level_change():

def _on_log_level_change(self, value: str) -> None:
    """Handle log level dropdown change.

    Sets source logger levels dynamically so DEBUG messages
    are captured when DEBUG is selected.
    """
    level = getattr(logging, value)

    # Set source logger levels to enable/disable DEBUG capture
    logging.getLogger("app.core.extractor").setLevel(level)
    logging.getLogger("app.core.geometry").setLevel(level)
    logging.getLogger("app.main").setLevel(level)
```

## Recommendations

1. **Implement Option A** - Minimal code change (5-7 lines), no architectural impact
2. **Test with spec 068 timing logs** - Verify DEBUG timing messages appear after fix
3. **Consider root logger fallback** - Add `logging.getLogger().setLevel(level)` as catch-all for any missed loggers

## Next Steps

1. Create implementation spec from this user story
2. Implement the fix in `_on_log_level_change()`
3. Test DEBUG log visibility in GUI
4. Verify timing diagnostics from spec 068 are visible
