# Trim Bottom 782.27 Issue: Root Cause and Correct Solution

## Executive Summary

The 782.27 vs 781 discrepancy is caused by an **asymmetry bug**: block bounding box calculation ALWAYS includes curved entities, while content zone detection respects `skip_curved_entities`. The specs (090-094) correctly implemented accurate geometry calculations but did NOT address this asymmetry. The correct solution is to add `skip_curved_entities` parameter to `_get_block_bounding_box()`.

## Table Summary

| Component | Current Behavior | Expected Behavior | Fix Required |
|-----------|-----------------|-------------------|--------------|
| `_get_block_bounding_box()` | Always includes ARCs | Skip curves when `skip_curved_entities=True` | **YES** |
| `_extract_all_edges()` | Respects `skip_curved_entities` | Already correct | No |
| `_detect_content_zone()` | Respects `skip_curved_entities` | Already correct | No |
| Trim calculation | Uses asymmetric values | Should use consistent geometry set | Fix via bbox |

## Relevant Files

- **`app/core/geometry.py:332-519`** - `_get_block_bounding_box()` - needs `skip_curved_entities` parameter
- **`app/core/geometry.py:1068-1156`** - `_extract_all_edges()` - already has `skip_curved_entities` (line 1070)
- **`app/core/geometry.py:1604-1877`** - `_detect_content_zone()` - passes `skip_curved_entities` to edge extraction
- **`app/core/extractor.py:1284`** - call site that needs to pass `skip_curved_entities`
- **`specs/090-unit-1-arc-bbox-accurate-calculation.md`** - addressed accuracy, NOT asymmetry

## Clarifying the User's Understanding

### What YOU Said (All Correct):

1. **"We do NOT want bbox to skip curved entities when setting is enabled"** - PARTIALLY TRUE
   - You DON'T want to skip curves ENTIRELY (would break trim calculation)
   - But bbox SHOULD skip curves **when the setting is enabled** to match content zone behavior

2. **"We DO want BBox to bound to ACTUAL extent, not extrapolated"** - ALREADY IMPLEMENTED
   - Spec 090 implemented `_get_arc_bounding_box()` which calculates accurate angular extent
   - The ARC really DOES extend to y=11664.66 - that's its TRUE geometric bottom

3. **"I thought we already addressed this"** - PARTIALLY ADDRESSED
   - Spec 090: Made arc bbox ACCURATE (actual extent, not full circle) - DONE
   - But: Did NOT address the asymmetry between bbox and content zone

## The Actual Problem

The ARC in block R23-0103 genuinely extends 1.27 units below the LWPOLYLINE:

```
                     ┌────────────────────────────┐
                     │    Content Zone            │
                     │    (polygons only)         │
                     └────────────────────────────┘  ← cz_min_y = 12446.94
                                 │
                          gap = 782.27 (current)
                          gap = 781.00 (expected)
                                 │
    ╭─────────╮               ╭─────────╮
    │         │               │         │           ← LWPOLYLINE min_y = 11665.94
    ╰────┬────╯               ╰────┬────╯
         │                        │
         ▼ ARC extends here ▼     │
    ─────────────────────────────────────────────  ← ARC bottom = 11664.66 (CURRENT block_min_y)
```

**When `skip_curved_entities=True`:**
- Content zone: Uses only LWPOLYLINE/LINE → `cz_min_y = 12446.94`
- Block bbox: Uses ALL geometry (including ARC) → `block_min_y = 11664.66` (WRONG)
- **Should be**: `block_min_y = 11665.94` (LWPOLYLINE bottom)

## What the Specs Actually Fixed

| Spec | Issue Fixed | Related to This Bug? |
|------|------------|---------------------|
| 090 | Arc bbox used full-circle extents | No - made bbox ACCURATE, not skip behavior |
| 091 | LWPOLYLINE bulge ignored | No - edge extraction, not bbox skip |
| 092 | Nested INSERT geometry missing | No - recursion, not skip behavior |
| 093 | ELLIPSE/SPLINE not supported | No - added support, not skip behavior |
| 094 | Edge count estimation hardcoded | No - estimation, not skip behavior |

**None of these specs addressed the asymmetry in `skip_curved_entities` handling.**

## The Correct Solution

### Option A: Add `skip_curved_entities` to `_get_block_bounding_box()` (RECOMMENDED)

```python
def _get_block_bounding_box(
    block_def: BlockLayout,
    doc: Any | None = None,
    processed_blocks: set[str] | None = None,
    skip_curved_entities: bool = False,  # ADD THIS
) -> tuple[float, float, float, float]:
    ...
    elif entity_type == "ARC":
        if skip_curved_entities:  # ADD THIS CHECK
            continue
        # existing accurate arc bbox code

    elif entity_type == "CIRCLE":
        if skip_curved_entities:  # ADD THIS CHECK
            continue
        # existing circle bbox code

    elif entity_type == "ELLIPSE":
        if skip_curved_entities:  # ADD THIS CHECK
            continue
        # existing ellipse bbox code

    elif entity_type == "SPLINE":
        if skip_curved_entities:  # ADD THIS CHECK
            continue
        # existing spline bbox code
```

**Then update `extractor.py` call site:**
```python
bbox = _get_block_bounding_box(block_def, doc, skip_curved_entities=user_setting)
```

### Why This Is Correct:

1. **Consistency**: Both bbox and content zone use the same geometry set
2. **User expectation**: "Skip Curved" means skip them EVERYWHERE
3. **Backward compatible**: `skip_curved_entities=False` preserves existing behavior
4. **Minimal change**: Single parameter addition, 4 continue statements

### Why NOT to Skip All Curves in BBox (Your Concern Addressed):

You said "skipping would break trim calculation" - this is only true if curves are skipped UNCONDITIONALLY. The solution is conditional:

- `skip_curved_entities=False` (default): Include all curves in bbox - trim works
- `skip_curved_entities=True` (user setting): Skip curves in BOTH bbox AND content zone - trim still works because both use same geometry set

## Expected Result After Fix

With `skip_curved_entities=True`:
- Block bbox min_y: 11665.94 (LWPOLYLINE, excluding ARC)
- Content zone min_y: 12446.94 (unchanged)
- **Trim bottom: 781.00** (matches user expectation)

## Simple List Summary

- The 1.27 discrepancy is real - the ARC genuinely extends below the LWPOLYLINE
- Spec 090 fixed arc bbox ACCURACY (not full-circle), but did NOT address skip behavior
- **Root cause**: `_get_block_bounding_box()` has no `skip_curved_entities` parameter
- **Fix**: Add `skip_curved_entities` parameter to `_get_block_bounding_box()`
- When enabled, skip ARC/CIRCLE/ELLIPSE/SPLINE in bbox calculation (4 continue statements)
- Result: bbox and content zone use consistent geometry, trim becomes 781.00
