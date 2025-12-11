# Logging Controls and Performance Improvements Analysis

## Executive Summary

Analysis of five related improvements: (1) adding log file generation toggle, (2) log level selection for file output, (3) better progress feedback during long waits, (4) processing speed optimization for high-polygon blocks, and (5) updating the Units hint text. Current architecture supports most changes with minimal refactoring.

## Table Summary

| Feature | Current State | Recommended Approach | Effort |
|---------|--------------|---------------------|--------|
| Log file toggle | Always generates | Add checkbox + BooleanVar | Low |
| Log level for file | Fixed DEBUG level | Add separate dropdown, apply to file handler | Low |
| Progress feedback | 3+ min silent gap | Add per-block logging in `_detect_content_zone` | Low |
| Processing speed | 500 polygon threshold | Early bbox filtering + chunked logging | Medium |
| Units hint text | Partial list | Update string literal | Trivial |

## Relevant Files

- `app/main.py:191-198` - Units hint label that needs text update
- `app/main.py:345-365` - Log viewer panel with existing log level selector
- `app/main.py:438-549` - `_extraction_worker()` where debug file handler is created
- `app/main.py:452-454` - `create_debug_file_handler()` call - conditionally skip based on toggle
- `app/core/logger.py:244-268` - `create_debug_file_handler()` factory function
- `app/core/geometry.py:990-1191` - `_detect_content_zone()` - needs progress logging
- `app/core/extractor.py:1163-1301` - Block definition analysis loop - long running section
- `app/core/constants.py:160-164` - `POLYGON_COUNT_THRESHOLD = 500`

## 1. Log File Generation Toggle

### Current Behavior
A debug log file is **always** created in `_extraction_worker()` (main.py:448-454):
```python
log_filename = f"{input_path.stem}_debug_{timestamp}.log"
self.debug_file_handler = create_debug_file_handler(str(log_path))
logging.getLogger().addHandler(self.debug_file_handler)
```

### Recommended Implementation
Add a checkbox to the GUI logging section:

```python
# Add to __init__ after line 97:
self.log_file_var = ctk.BooleanVar(value=False)  # Default: no log file

# Add checkbox in _create_widgets() after line 356:
self.log_file_checkbox = ctk.CTkCheckBox(
    self.log_frame,
    text="Generate Log File",
    variable=self.log_file_var,
    font=ctk.CTkFont(size=12),
)
self.log_file_checkbox.pack(anchor="w", padx=5, pady=(0, 5))

# Modify _extraction_worker() around line 448:
if self.log_file_var.get():
    # Set up debug file logging
    self.debug_file_handler = create_debug_file_handler(str(log_path))
    logging.getLogger().addHandler(self.debug_file_handler)
    self.logger.info(f"Debug log: {log_path}")
```

## 2. Log Level Selection for File Output

### Current Behavior
- GUI has log level dropdown but only affects **display filtering** (main.py:643-657)
- File handler is always set to DEBUG level (logger.py:263)

### Recommended Implementation
Add a second dropdown for file log level:

```python
# Add to __init__:
self.file_log_level_var = ctk.StringVar(value="DEBUG")

# Add dropdown next to checkbox:
self.file_log_level_menu = ctk.CTkOptionMenu(
    self.log_frame,
    values=["DEBUG", "INFO", "WARNING"],
    variable=self.file_log_level_var,
    width=100,
    state="disabled",  # Enabled when checkbox checked
)

# In _extraction_worker(), after creating handler:
file_level = getattr(logging, self.file_log_level_var.get())
self.debug_file_handler.setLevel(file_level)
```

## 3. Progress Feedback During Long Waits

### Root Cause
The 3+ minute gap in the log example occurs between:
- `07:54:17.802 [INFO] Analyzing block definitions...`
- `07:57:54.908 [WARNING] [GM_MobileBin...] Skipping content zone...`

The `_detect_content_zone()` function runs silently for each block. With hundreds of blocks, each taking several seconds, there's no feedback.

### Recommended Implementation
Add per-block progress logging in `geometry.py:_detect_content_zone()`:

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    ...
) -> ContentZoneData:
    block_name = block_def.name
    logger.info(f"[{block_name}] Starting content zone detection...")  # ADD THIS

    # ... existing code ...

    logger.debug(f"[{block_name}] Found {original_polygon_count} paint-bucket regions")
```

Also add periodic progress in extractor.py block loop:

```python
# In extract_blocks(), around line 1167:
for block_def in doc.blocks:
    block_def_count += 1
    if block_def_count % 10 == 0:  # Every 10 blocks
        logger.info(f"Progress: Analyzed {block_def_count} block definitions...")
```

## 4. Processing Speed Optimization

### Current Bottleneck
The warning shows 699 polygons exceeds 500 threshold, but the **time to detect** this is the issue. The `_extract_paint_bucket_regions()` runs fully before the polygon count is checked.

### Analysis of Threshold Reduction (50 vs 500)

| Threshold | Pros | Cons |
|-----------|------|------|
| 50 | Very fast | Misses valid content zones in complex blocks |
| 100 | Reasonably fast | May miss some legitimate large fixtures |
| 500 | Good coverage | Current - can be slow for complex blocks |

**Recommendation**: Keep 500, but add **early exit strategies**:

### Optimization Strategies

**Strategy 1: Early Bounding Box Filtering** (Recommended)
Filter polygons by bounding box before expensive net area calculation:

```python
# In _detect_content_zone(), after paint-bucket extraction:
if len(all_shapes) > 100:  # Pre-filter if many polygons
    block_width = block_bbox[2] - block_bbox[0]
    block_height = block_bbox[3] - block_bbox[1]
    min_significant_area = block_width * block_height * 0.01  # 1% of block
    all_shapes = [s for s in all_shapes if _shoelace_area(s) >= min_significant_area]
    logger.debug(f"[{block_name}] After bbox pre-filter: {len(all_shapes)} polygons")
```

**Strategy 2: Progressive Logging**
Report progress during long operations:

```python
# In _calculate_net_areas():
for i, (poly, shapely_poly) in enumerate(zip(polygons, shapely_polys)):
    if i > 0 and i % 50 == 0:
        logger.debug(f"Net area calculation progress: {i}/{len(polygons)}")
```

**Strategy 3: Batch Polygon Processing**
Process polygons in batches with checkpoints:

```python
BATCH_SIZE = 100
for batch_start in range(0, len(all_shapes), BATCH_SIZE):
    batch = all_shapes[batch_start:batch_start + BATCH_SIZE]
    # Process batch
    logger.debug(f"Processed polygons {batch_start}-{batch_start + len(batch)}")
```

## 5. Units Hint Text Update

### Current Text (main.py:192-198)
```python
units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to precision fix and gap bridge)",
    ...
)
```

### Recommended Update
```python
text="(applies to all numeric filters)"
```

Or more explicit:
```python
text="(applies to precision fix, gap bridge, and area/side filters)"
```

## Recommendations

### Priority Order
1. **Units hint text** - Trivial fix, immediate value
2. **Progress logging** - Low effort, significant UX improvement
3. **Log file toggle** - Low effort, user-requested feature
4. **Early bbox filtering** - Medium effort, biggest performance gain
5. **File log level** - Low effort, nice-to-have

### Implementation Notes
- All changes are additive - no breaking changes to existing API
- Progress logging should use INFO level for visibility
- Consider adding a "Verbose" checkbox that controls DEBUG vs INFO output

## Next Steps

1. Update units hint text string in main.py:194
2. Add `log_file_var` BooleanVar and checkbox to GUI
3. Add per-block progress logging in `_detect_content_zone()`
4. Implement early bbox pre-filtering for polygon optimization
5. Test with the problematic file mentioned in the log example
