# DEBUG Logging Bug: Logger Name Mismatch

## Executive Summary
DEBUG logging is broken due to a **logger name mismatch bug**. The `_on_log_level_change()` method sets levels on loggers named `app.core.*` but the actual logger names are `core.*`. This means selecting DEBUG in the dropdown has NO effect on DEBUG message capture - the detailed timing from spec 068 never appears.

## Table Summary

| Component | Expected Logger Name | Actual Logger Name | Level Set By Dropdown |
|-----------|---------------------|-------------------|----------------------|
| geometry.py | `app.core.geometry` | `core.geometry` | No - wrong name |
| extractor.py | `app.core.extractor` | `core.extractor` | No - wrong name |
| main.py | `app.main` | `__main__` | No - wrong name |

## Relevant Files

- **`app/main.py:1057-1060`** - `_on_log_level_change()` uses WRONG logger names (`app.core.*`)
- **`app/core/geometry.py:47`** - Logger created as `setup_logger(__name__)` → name is `core.geometry`
- **`app/core/extractor.py:56`** - Logger created as `setup_logger(__name__)` → name is `core.extractor`
- **`specs/069-gui-log-level-dropdown-control.md`** - Spec that introduced the bug with incorrect logger names

## Root Cause Analysis

### The Bug
```python
# In app/main.py _on_log_level_change():
logging.getLogger("app.core.extractor").setLevel(level)  # WRONG
logging.getLogger("app.core.geometry").setLevel(level)   # WRONG
logging.getLogger("app.main").setLevel(level)            # WRONG
```

### Why Names Are Different
The app runs from the `app/` directory with `sys.path.insert(0, 'app')`. Imports are:
```python
from core.extractor import ...  # Not from app.core.extractor
```

So `__name__` in `core/geometry.py` is `core.geometry`, NOT `app.core.geometry`.

### Verification
```bash
$ uv run python -c "from core.geometry import logger; print(logger.name)"
core.geometry
```

## The Fix

Change `_on_log_level_change()` in `app/main.py:1057-1060`:

**From (broken):**
```python
logging.getLogger("app.core.extractor").setLevel(level)
logging.getLogger("app.core.geometry").setLevel(level)
logging.getLogger("app.main").setLevel(level)
```

**To (fixed):**
```python
logging.getLogger("core.extractor").setLevel(level)
logging.getLogger("core.geometry").setLevel(level)
logging.getLogger("__main__").setLevel(level)
```

## What DEBUG Output You Should See

Once fixed, with DEBUG selected, you should see sub-operation breakdown:
```
13:41:42.596 [INFO] [GM_MobileBin...] Detecting content zone...
13:41:42.800 [DEBUG] Edge extraction: 0.20s (1500 edges)
13:41:43.500 [DEBUG] Applied precision fix snap: tolerance=1e-06
13:41:45.000 [DEBUG] Edge snapping: 1.50s
13:42:20.000 [DEBUG] Unary union: 35.00s          ← The bottleneck!
13:42:30.800 [DEBUG] Polygonize: 10.80s (699 polygons)
13:42:31.032 [INFO] Paint bucket regions: 48.43s (699 polygons)
```

## Recommendations

1. **Immediate fix**: Update the three logger names in `_on_log_level_change()`
2. **Testing**: Verify DEBUG messages appear after fix
3. **Future-proofing**: Consider using dynamic logger discovery instead of hardcoded names

## Next Steps

1. Create a bug fix spec or directly fix `app/main.py:1057-1060`
2. Test by selecting DEBUG and running extraction
3. Verify sub-operation timing appears for slow blocks
