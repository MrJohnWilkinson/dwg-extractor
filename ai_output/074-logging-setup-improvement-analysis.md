# Logging Setup Improvement Analysis

## Executive Summary

The current logging setup has **three independent log outputs** (console, GUI viewer, file) but **confusing GUI controls**. The main window's "Log Level" dropdown actually controls **both** what messages are generated AND what's displayed, while the file log level appears independent but is actually dependent on source logger levels. This creates user confusion about what each setting affects.

## Table Summary

| Component | Current Behavior | What GUI Label Implies | Needs Clarification |
|-----------|------------------|------------------------|---------------------|
| Main "Log Level" dropdown | Sets source logger levels + filters GUI display | Only filters GUI display | YES |
| File "Level" dropdown | Sets file handler level only | Controls file log level | Partially |
| `log_viewer_level` setting | Not connected to main window | Affects GUI viewer | YES - unused |
| Console output | Fixed by env var at startup | N/A | No |
| QueueHandler | Always DEBUG (captures all from sources) | N/A | Correct |

## Relevant Files

- **app/main.py** - Main GUI with log controls (lines 374-413, 1049-1070)
  - `log_level_var` - GUI log level dropdown variable
  - `file_log_level_var` - File log level dropdown variable
  - `_on_log_level_change()` - Sets source logger levels (line 1049)
  - `_poll_log_queue()` - Filters GUI display (line 763)

- **app/core/logger.py** - Logging infrastructure
  - `create_queue_handler()` - Always sets handler to DEBUG level (line 237)
  - `create_debug_file_handler()` - Creates file handler at DEBUG (line 263)
  - `setup_logger()` - Creates console handlers from env var

- **app/core/settings.py** - Settings management
  - `SETTINGS_SECTIONS["logging"]` - Contains `log_viewer_level` setting

- **app/core/settings_window.py** - Advanced settings dialog
  - Logging tab (lines 813-873) - Shows `log_viewer_level` but not synced

- **app/core/constants.py** - Default values
  - `DEFAULT_LOG_VIEWER_LEVEL = "INFO"` (line 357)
  - `DEFAULT_FILE_LOG_LEVEL = "DEBUG"` (line 356)

## Current Behavior Analysis

### Log Message Flow

```
Source Logger (extractor/geometry/__main__)
    │
    ├─> Console Handler (level from env var)
    │       └─> Terminal output
    │
    └─> Root Logger
            │
            ├─> QueueHandler (level=DEBUG, always captures)
            │       └─> GUI Log Viewer (filtered by log_level_var)
            │
            └─> FileHandler (level from file_log_level_var, temp)
                    └─> Debug log file
```

### The Coupling Problem

When user sets GUI "Log Level" dropdown to INFO:

1. `_on_log_level_change()` sets source logger levels to INFO
2. Source loggers no longer emit DEBUG messages
3. **File handler cannot capture DEBUG** even if file level is DEBUG
4. GUI correctly shows only INFO+

This means **file log level dropdown is misleading** - selecting DEBUG won't capture DEBUG messages unless the GUI dropdown is also set to DEBUG.

### User's Analysis Verification

**CONFIRMED**: The main log level IS used for both GUI and file. However, it's not because they share a setting - it's because the GUI dropdown controls the **source logger levels**, which affects all downstream handlers.

## Architectural Issues

### Issue 1: Overloaded Control
The main window's "Log Level" dropdown does two things:
1. Sets source logger levels (controls what gets generated)
2. Filters GUI display (controls what gets shown)

Users expect it only filters display.

### Issue 2: Disconnected Settings
The `log_viewer_level` setting in SettingsManager:
- Is defined in `SETTINGS_SECTIONS["logging"]`
- Shows in Advanced Settings window
- **Is not connected** to main window's `log_level_var`

### Issue 3: Misleading File Level
The file log level dropdown appears independent but:
- File handler level is set correctly
- Source loggers gate what reaches the handler
- If GUI is INFO and file is DEBUG, no DEBUG messages captured

### Issue 4: No UI Explanation
No tooltips or descriptions explain:
- What "Log Level" actually controls
- Why DEBUG file logging might not work
- The relationship between controls

## Recommendations

### 1. Separate Generation from Display (Architectural)
```
[Source Log Level]  ← Controls what messages are generated
        │
        ├─> [GUI Display Level]  ← Filters what's shown in viewer
        └─> [File Log Level]     ← Already independent handler level
```

**Implementation**: Add a new "Source Log Level" control (or use env var) that's separate from GUI display filtering.

### 2. Update GUI Labels (UI/UX)
Current:
- "Log Level" (in log viewer section)

Proposed:
- "Display Level" with description: "Filter messages shown in viewer"
- OR keep label but add tooltip: "Controls message capture and display. Set to DEBUG to enable DEBUG file logging."

### 3. Sync Settings to GUI
Connect `log_viewer_level` setting to main window:
```python
# In __init__
self.log_level_var = ctk.StringVar(
    value=self.settings.get("log_viewer_level")
)
```

### 4. Fix File Logging Independence
Two options:
- **Option A**: Keep coupled - document that file DEBUG requires GUI DEBUG
- **Option B**: Decouple - file handler sets source loggers to DEBUG during extraction regardless of GUI setting

### 5. Add Hint/Warning for File Logging
When "Generate Log File" is checked with DEBUG level:
- Show hint: "Set Display Level to DEBUG to capture DEBUG messages"

## Proposed GUI Layout

```
┌─ Log Viewer ─────────────────────────────────────────┐
│  Display Level: [DEBUG ▼]                            │
│    └─ Filters which messages appear below            │
│                                                      │
│  ☑ Generate Log File   File Level: [DEBUG ▼]        │
│    └─ Note: File captures based on Display Level    │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 14:30:22 [INFO] Starting extraction...       │   │
│  │ 14:30:23 [DEBUG] Processing block ABC...     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## Next Steps

1. **Quick Win**: Add description text below the "Log Level" dropdown explaining its dual purpose
2. **Medium Term**: Sync `log_viewer_level` setting with main window dropdown
3. **Full Fix**: Decouple source logger levels from GUI display filtering
4. **Documentation**: Update any user docs to explain logging behavior
