# DEBUG Logging Bug Verification Report

## Executive Summary
The findings in `071-debug-logging-bug-logger-name-mismatch.md` are **CONFIRMED**. The logger name mismatch bug in `app/main.py:1057-1060` is real and affects all platforms. The lack of DEBUG output is **NOT caused by Windows builds** - it's a source code bug introduced by spec 069 using incorrect logger name assumptions.

## Table Summary

| Investigation Area | Finding | Impact |
|-------------------|---------|--------|
| Logger name mismatch | CONFIRMED | High - DEBUG messages never captured |
| Windows build issue | RULED OUT | None - bug is in source code |
| Spec 069 accuracy | INCORRECT | Spec assumed wrong logger names |
| PyInstaller bundling | NOT A FACTOR | Module names identical in .exe |
| Platform differences | NONE | Bug affects all platforms equally |

## Relevant Files

- **`app/main.py:1057-1060`** - Contains the broken `_on_log_level_change()` with wrong logger names
- **`app/core/geometry.py:47`** - Logger created as `setup_logger(__name__)` = `"core.geometry"`
- **`app/core/extractor.py:56`** - Logger created as `setup_logger(__name__)` = `"core.extractor"`
- **`specs/069-gui-log-level-dropdown-control.md:30-32`** - Spec that introduced incorrect logger names

## Bug Verification Details

### Actual Logger Names (Runtime-Verified)

```
geometry logger: "core.geometry"
extractor logger: "core.extractor"
settings logger: "core.settings"
main module __name__: "__main__"
```

### What _on_log_level_change() Sets (Broken)

```python
logging.getLogger("app.core.extractor").setLevel(level)  # WRONG - creates orphan
logging.getLogger("app.core.geometry").setLevel(level)   # WRONG - creates orphan
logging.getLogger("app.main").setLevel(level)            # WRONG - creates orphan
```

### Proof of Bug

```python
# After calling _on_log_level_change('DEBUG'):
geometry logger: "core.geometry", level: 20 (INFO - UNCHANGED)
extractor logger: "core.extractor", level: 20 (INFO - UNCHANGED)

# The "app.core.*" loggers are empty orphans with no handlers:
app.core.extractor - handlers: 0, level: 10 (DEBUG - but no handlers!)
app.core.geometry - handlers: 0, level: 10 (DEBUG - but no handlers!)
```

Setting level on non-existent logger names creates orphan loggers with no handlers, leaving the actual loggers at their default INFO level.

## Windows Build Analysis

### Is the Bug Caused by Windows Build?

**NO.** The investigation confirmed:

1. **PyInstaller preserves module names**: When PyInstaller bundles `app/main.py`, it freezes the import structure. Module names remain based on import paths (e.g., `core.geometry`), not the entry point path.

2. **The bug is in source code**: The incorrect logger names (`"app.core.extractor"`) exist in `app/main.py`, not in build configuration.

3. **Same behavior on all platforms**: The bug reproduces identically on:
   - Windows .exe (built with PyInstaller)
   - Linux (via `uv run python app/main.py`)
   - WSL2 (current test environment)

4. **Settings path differences don't affect logging**: Windows uses `%APPDATA%/DXFExtractor/settings.json`, Linux uses `~/.config/dxf-extractor/settings.json`, but this only affects settings persistence, not logger names.

### Why the Spec Was Wrong

Spec 069 incorrectly assumed:
```markdown
- `app/core/extractor.py` - creating logger `app.core.extractor`
- `app/core/geometry.py` - creating logger `app.core.geometry`
```

But the actual `__name__` values depend on **how modules are imported**, not their file paths:
- App runs with `sys.path` including `app/`
- Imports are `from core.extractor import ...`
- Therefore `__name__` is `"core.extractor"`, not `"app.core.extractor"`

## Recommendations

1. **Fix the logger names** in `app/main.py:1057-1060`:
   ```python
   logging.getLogger("core.extractor").setLevel(level)
   logging.getLogger("core.geometry").setLevel(level)
   logging.getLogger("__main__").setLevel(level)
   ```

2. **Update spec 069** to correct the logger name documentation

3. **Add verification test**: Create test that confirms DEBUG messages are captured when dropdown is set to DEBUG

## Next Steps

1. Apply the 3-line fix to `app/main.py:1057-1060`
2. Test by selecting DEBUG in dropdown and running extraction
3. Verify sub-operation timing from spec 068 now appears:
   - Edge extraction timing
   - Unary union timing
   - Polygonize timing
