# DEBUG Logging Not Working Analysis

## Executive Summary
DEBUG level logging does not appear in the GUI log viewer or log files because the **source loggers** (extractor.py, geometry.py) are initialized with INFO level. The GUI dropdown only filters display output and the file log level dropdown only sets handler levels - neither changes the source logger levels. Python's logging architecture discards messages at the logger level check before they reach any handler.

## Table Summary

| Component | Level Set | Level Needed | Status |
|-----------|-----------|--------------|--------|
| `app.core.extractor` logger | INFO | DEBUG | **BLOCKING** |
| `app.core.geometry` logger | INFO | DEBUG | **BLOCKING** |
| `app.main` logger | INFO | DEBUG | **BLOCKING** |
| Queue handler (GUI) | DEBUG | DEBUG | OK |
| File handler | DEBUG | DEBUG | OK |
| GUI display filter | User-selected | N/A | OK (display only) |

## Relevant Files

- **app/core/logger.py** (lines 271-313) - `setup_logger()` function sets logger level to INFO by default. This is where source loggers are created.
- **app/main.py** (lines 83-84, 373-380, 406-413, 535-541) - Queue handler added to root logger; GUI dropdown is display filter only; file handler level set but not source loggers.
- **app/core/extractor.py** (line 56) - Creates logger via `setup_logger(__name__)` which sets level to INFO.
- **app/core/geometry.py** (line 47) - Creates logger via `setup_logger(__name__)` which sets level to INFO.
- **specs/068-block-timing-diagnostics.md** (lines 107-131) - Timing logs use `logger.debug()` which never reaches handlers.

## Root Cause: Python Logging Architecture

### How Python Logging Works

```
logger.debug("message")
       │
       ▼
┌─────────────────────────────────────┐
│  LOGGER LEVEL CHECK                 │
│  Is DEBUG (10) >= logger.level (20)?│
│  NO → Message DISCARDED             │  ← PROBLEM HERE
└─────────────────────────────────────┘
       │ (if passed)
       ▼
┌─────────────────────────────────────┐
│  HANDLER LEVEL CHECK                │
│  Is DEBUG (10) >= handler.level?    │
│  Queue handler: DEBUG (10) → PASS   │
│  File handler: DEBUG (10) → PASS    │
└─────────────────────────────────────┘
       │
       ▼
    Message emitted
```

### Current Implementation Flow

1. **Logger Creation** (`setup_logger()` in logger.py:288-311):
   ```python
   logger = logging.getLogger(name)
   log_level = _get_log_level_from_env()  # Returns INFO (20)
   handler.setLevel(log_level)
   logger.setLevel(log_level)  # ← Logger level = INFO
   ```

2. **Handlers Added to Root Logger** (main.py:83-84, 540-541):
   ```python
   logging.getLogger().addHandler(self.queue_handler)  # Level: DEBUG
   logging.getLogger().addHandler(self.debug_file_handler)  # Level: user-selected
   ```

3. **GUI Dropdown** (main.py:373-380, 763-778):
   - Only a **display filter** - filters what's shown from the queue
   - Does NOT change any logger levels

4. **File Log Level Dropdown** (main.py:538-539):
   ```python
   file_level = getattr(logging, self.file_log_level_var.get())
   self.debug_file_handler.setLevel(file_level)  # Only sets HANDLER level
   ```

### Why DEBUG Messages Are Lost

When `logger.debug()` is called in extractor.py or geometry.py:

1. The logger is `app.core.extractor` or `app.core.geometry`
2. Logger level = INFO (20) from `setup_logger()`
3. DEBUG level = 10
4. Check: Is 10 >= 20? **NO**
5. **Message discarded** - never reaches any handler

## Key Finding: Disconnected Control Paths

```
┌─────────────────────┐     ┌─────────────────────┐
│   SOURCE LOGGERS    │     │   GUI CONTROLS      │
│                     │     │                     │
│ extractor: INFO     │     │ Log Viewer: DEBUG   │
│ geometry:  INFO     │     │ File Level: DEBUG   │
│ main:      INFO     │     │                     │
└─────────────────────┘     └─────────────────────┘
         │                            │
         │ (Level 10 < 20)           │
         │ ╳ DISCARDED              │
         │                            │
         ▼                            ▼
         ∅                     HANDLERS (DEBUG)
                                      │
                               Never receive
                               DEBUG messages
```

## Evidence From Spec Implementation

The spec (068-block-timing-diagnostics.md) added timing logs at DEBUG level:

```python
# Step 3: Inside _extract_paint_bucket_regions()
logger.debug(f"Edge extraction: {t_edges - t_start:.2f}s ({len(edges)} edges)")
logger.debug(f"Edge snapping: {t_snap - t_edges:.2f}s")
logger.debug(f"Unary union: {t_union - t_snap:.2f}s")
logger.debug(f"Polygonize: {t_poly - t_union:.2f}s ({len(polygons)} polygons)")
```

These `logger.debug()` calls are made on the `app.core.geometry` logger, which has level INFO. The messages are discarded before reaching any handler.

## Recommendations

### Option A: Set Source Logger Levels Dynamically (Recommended)
When user changes GUI log level or file log level to DEBUG, also set the source logger levels:

```python
def _on_log_level_change(self, value: str) -> None:
    level = getattr(logging, value)
    # Set source logger levels
    logging.getLogger("app.core.extractor").setLevel(level)
    logging.getLogger("app.core.geometry").setLevel(level)
    logging.getLogger("app.main").setLevel(level)
    # Or set root logger level (affects all)
    logging.getLogger().setLevel(level)
```

### Option B: Initialize Source Loggers at DEBUG Level
Change `setup_logger()` to always set logger level to DEBUG, letting handlers filter:

```python
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_level = _get_log_level_from_env()
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)  # Handler filters output
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # Logger passes all to handlers
    return logger
```

### Option C: Use Root Logger Level
Set root logger to DEBUG and let all filtering happen at handler level:

```python
# In main.py __init__
logging.getLogger().setLevel(logging.DEBUG)
```

## Next Steps

1. Choose implementation approach (A, B, or C)
2. Implement fix in logger.py and/or main.py
3. Test with DEBUG level selected in GUI
4. Verify timing logs from spec 068 appear in log viewer and log file
