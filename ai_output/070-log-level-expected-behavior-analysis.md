# Log Level Expected Behavior Analysis

## Executive Summary
Your log output showing only INFO and TIMING messages is **correct and expected** with the default GUI settings. DEBUG level messages will only appear if you select "DEBUG" from the log level dropdown **before** starting extraction. The current implementation correctly filters at INFO level by default.

## Table Summary

| Setting | Default Value | Effect | How to Change |
|---------|---------------|--------|---------------|
| GUI Log Level Dropdown | INFO | Only INFO+ messages shown in viewer | Select DEBUG before extraction |
| Source Logger Levels | INFO (env default) | DEBUG messages not captured | Changed when dropdown changes |
| Queue Handler Level | DEBUG | Captures all messages sent to it | Fixed - always DEBUG |
| File Log Level | INFO | Controls debug log file verbosity | Change dropdown (when enabled) |

## Relevant Files

- **`app/core/logger.py`** - Defines logging infrastructure; `DEFAULT_LOG_LEVEL = "INFO"` at line 35; `create_queue_handler()` sets handler to DEBUG at line 237
- **`app/main.py:374`** - GUI log level dropdown defaults to "INFO"
- **`app/main.py:1049-1060`** - `_on_log_level_change()` dynamically sets source logger levels when dropdown changes
- **`app/main.py:763-778`** - `_poll_log_queue()` filters displayed messages based on dropdown value

## How Log Levels Work in This Application

### Log Message Flow
```
Source Loggers (extractor, geometry)  →  Queue Handler  →  Log Queue  →  GUI Display Filter
    [Level: INFO by default]             [Level: DEBUG]                   [Level: dropdown value]
```

### Why You See Only INFO and TIMING

1. **Source loggers default to INFO** - The `setup_logger()` function reads `DXF_EXTRACTOR_LOG_LEVEL` env var, defaulting to INFO
2. **DEBUG messages are suppressed at source** - When logger level is INFO, `logger.debug()` calls are no-ops
3. **Dropdown change triggers level update** - `_on_log_level_change()` sets source logger levels dynamically
4. **Default dropdown is INFO** - At startup, no change event fires, so loggers stay at INFO

### What DEBUG Messages Would Show

The codebase has **88 debug log statements** across core modules:
- `app/core/geometry.py` - 25 debug calls (detailed geometry analysis steps)
- `app/core/extractor.py` - 37 debug calls (block processing details)
- `app/core/excel_writer.py` - 20 debug calls (Excel writing details)
- `app/core/settings.py` - 3 debug calls
- `app/core/settings_window.py` - 3 debug calls

## How to Enable DEBUG Logging

### Method 1: GUI Dropdown (Recommended)
1. Select **"DEBUG"** from the log level dropdown in the Log Viewer section
2. Then click **Extract**
3. DEBUG messages will now appear in the log viewer

### Method 2: Environment Variable
```bash
export DXF_EXTRACTOR_LOG_LEVEL=DEBUG
# Then start the application
```

### Method 3: Generate Debug Log File
1. Check **"Generate Log File"** checkbox
2. Set the file level dropdown to **"DEBUG"**
3. DEBUG messages will be written to the log file (even if viewer shows INFO)

## Your Sample Output Analysis

Your sample shows the expected INFO-level output:
- `[INFO] Detecting content zone...` - Block processing start
- `[INFO] Content zone detected: ...` - Successful detection
- `[INFO] Paint bucket regions: ...` - Geometry analysis timing
- `[INFO] [TIMING] Block '...' completed` - Block completion timing

All messages are correctly tagged as INFO level.

## Recommendations

1. **For normal operation**: Keep dropdown at INFO - this is the appropriate verbosity
2. **For debugging issues**: Select DEBUG before extraction to see detailed geometry analysis
3. **For performance analysis**: INFO level with TIMING messages is sufficient

## Next Steps

If you want to see DEBUG output:
1. Set log level dropdown to "DEBUG"
2. Re-run extraction
3. You'll see detailed messages about polygon operations, coordinate calculations, etc.
