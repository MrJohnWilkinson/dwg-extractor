# Performance Optimizations and Logging Controls Implementation Plan

## Executive Summary

This plan combines three performance optimizations (early exit checks and parallel processing from plan 055) with four logging control improvements. The performance units must be implemented first in sequence, followed by logging controls which can be implemented in any order. Combined, these changes reduce complex block processing from 50-90 seconds to <5 seconds while providing user control over log output and better progress visibility.

## Table Summary

| Unit | Change | Location | Impact | Risk |
|------|--------|----------|--------|------|
| 1 | Entity count pre-check | `geometry.py:_detect_content_zone()` | Skip before ANY geometry work | Low |
| 2 | Fast edge count estimation | `geometry.py` (new function) | Skip before coordinate extraction | Low |
| 3 | Parallel block processing | `extractor.py:extract_blocks()` | Process all blocks concurrently | Medium |
| 4 | Log file toggle | `main.py` GUI + `_extraction_worker()` | User controls log generation | Low |
| 5 | Log level for file output | `main.py` GUI + `_extraction_worker()` | User controls file verbosity | Low |
| 6 | Progress feedback | `geometry.py:_detect_content_zone()` | Eliminates silent 3+ min gaps | Low |
| 7 | Units hint text update | `main.py:192-198` | Accurate filter description | Trivial |

## Relevant Files

- `app/core/geometry.py:990-1191` - `_detect_content_zone()` function where early exits and progress logging are added
- `app/core/geometry.py:595-642` - `_extract_all_edges()` that we want to avoid calling
- `app/core/extractor.py:1164-1293` - Block definition analysis loop to parallelize
- `app/core/constants.py:160-170` - Threshold constants to add `ENTITY_COUNT_THRESHOLD`
- `app/main.py:191-198` - Units hint label that needs text update
- `app/main.py:345-365` - Log viewer panel where log file controls are added
- `app/main.py:438-549` - `_extraction_worker()` where debug file handler is created
- `app/core/logger.py:244-268` - `create_debug_file_handler()` factory function

## In-Scope

**Performance (Units 1-3):**
1. Add `ENTITY_COUNT_THRESHOLD` constant (1000 entities)
2. Add entity count pre-check in `_detect_content_zone()` BEFORE any geometry extraction
3. Create `_estimate_edge_count()` function for fast O(n) edge counting without coordinates
4. Replace `len(_extract_all_edges(block_def))` with `_estimate_edge_count()` for threshold check
5. Parallelize block definition analysis using `concurrent.futures.ThreadPoolExecutor`
6. Add thread-safe result collection for parallel processing

**Logging Controls (Units 4-7):**
7. Add checkbox to toggle log file generation (default: off)
8. Add dropdown for file log level (DEBUG/INFO/WARNING)
9. Add per-block progress logging in `_detect_content_zone()`
10. Update units hint text to reflect all numeric filters

## Out-of-Scope

- Block definition caching (separate optimization)
- Lazy content zone detection (architectural change)
- GUI options for processing depth (UX change)
- Spatial indexing with STRtree (complex optimization)
- Per-block timeout mechanism (requires significant refactoring)

---

## Unit 1: Entity Count Pre-Check

**Purpose**: Skip content zone detection for blocks with high entity counts BEFORE any geometry extraction.

**Rationale**: Entity count check is O(n) with no coordinate extraction - the fastest possible check. Should be the first gate.

### Changes

#### 1.1 Add Constant (`constants.py`)

```python
ENTITY_COUNT_THRESHOLD: int = 1000
"""Maximum entities in block for content zone detection.
Blocks with more entities skip content zone entirely.
Rationale: High entity counts strongly correlate with complex geometry
that will exceed polygon thresholds anyway."""
```

Location: After `LINE_SEGMENT_THRESHOLD` (line ~170)

#### 1.2 Add Early Exit (`geometry.py:_detect_content_zone()`)

Add at the START of `_detect_content_zone()`, before any other processing:

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
) -> ContentZoneData:
    block_name = block_def.name

    # UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
    entity_count = sum(1 for _ in block_def)
    if entity_count > ENTITY_COUNT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{entity_count} entities exceeds threshold {ENTITY_COUNT_THRESHOLD}"
        )
        return _empty_content_zone_data()

    # ... rest of function
```

**Import**: Add `ENTITY_COUNT_THRESHOLD` to imports from `.constants`

---

## Unit 2: Fast Edge Count Estimation

**Purpose**: Count edges without extracting coordinates to enable early exit before expensive `_extract_all_edges()`.

**Rationale**: The current code calls `_extract_all_edges()` just to get `len()`, which extracts all coordinates unnecessarily.

### Changes

#### 2.1 Add Fast Estimation Function (`geometry.py`)

Add after `_count_line_segments()` function (line ~484):

```python
def _estimate_edge_count(block_def: BlockLayout) -> int:
    """
    Fast O(n) edge count estimation without coordinate extraction.

    Counts the number of edges that would be extracted by _extract_all_edges()
    without actually creating LineString objects or extracting coordinates.
    Used for threshold checks before expensive geometry operations.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Estimated number of edges in the block.
    """
    count = 0
    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            count += 1

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                # Count vertices to estimate edge count
                # Each vertex pair = 1 edge, plus closing edge if closed
                points = list(entity.get_points())
                vertex_count = len(points)
                if vertex_count >= 2:
                    count += vertex_count - 1
                    if hasattr(entity, "closed") and entity.closed:
                        count += 1
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            # Estimate based on typical flattening (full circle ≈ 36 segments)
            count += 36

        elif entity_type == "ARC":
            # Estimate based on typical flattening (half circle ≈ 18 segments)
            count += 18

        elif entity_type == "HATCH":
            # Conservative estimate per hatch boundary path
            # Actual count varies, but 50 edges per hatch is reasonable average
            count += 50

    return count
```

#### 2.2 Replace Edge Count Check (`geometry.py:_detect_content_zone()`)

Replace lines 1048-1065:

```python
# OLD:
edge_count = len(_extract_all_edges(block_def))
if edge_count > LINE_SEGMENT_THRESHOLD:
    ...

# NEW:
# UNIT 2: Fast edge count estimation (no coordinate extraction)
estimated_edge_count = _estimate_edge_count(block_def)
if estimated_edge_count > LINE_SEGMENT_THRESHOLD:
    logger.warning(
        f"[{block_name}] Skipping region detection: "
        f"~{estimated_edge_count} estimated edges exceeds threshold {LINE_SEGMENT_THRESHOLD}"
    )
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=0,
        filtered_polygon_count=0,
    )
```

---

## Unit 3: Parallel Block Processing

**Purpose**: Process block definitions concurrently using ThreadPoolExecutor.

**Rationale**:
- Shapely/GEOS is thread-safe for read operations
- Block definitions are independent (no shared mutable state during analysis)
- Modern CPUs have multiple cores; single-threaded wastes resources

### Changes

#### 3.1 Add Import (`extractor.py`)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

#### 3.2 Extract Block Analysis Function (`extractor.py`)

Create a new function that encapsulates per-block analysis (extract from lines 1166-1293):

```python
def _analyze_single_block(
    block_def: Any,
    doc: Drawing,
    anonymous_to_resolved: dict[str, str],
    anonymous_resolution_details: dict[str, str],
    abort_event: threading.Event | None,
    precision_tolerance: float,
    gap_bridge_tolerance: float,
    min_area: float,
    min_side: float,
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Analyze a single block definition for content zone and geometry.

    Thread-safe function for parallel block processing.

    Args:
        block_def: ezdxf block definition object
        doc: The ezdxf Drawing document
        anonymous_to_resolved: Pre-built mapping of anonymous block names
        anonymous_resolution_details: Pre-built resolution details
        abort_event: Optional abort signal
        precision_tolerance: Precision snap tolerance
        gap_bridge_tolerance: Gap bridge tolerance
        min_area: Minimum area filter
        min_side: Minimum side filter

    Returns:
        Tuple of (effective_name, result_dict) or (None, None) if block should be skipped.
        result_dict contains: block_entities, block_trimming_data, block_content_zone_data,
                              nested_inserts (list of nested block names)
    """
    block_name = block_def.name

    # Skip modelspace/paperspace blocks
    if block_name in ("*Model_Space", "*Paper_Space") or block_name.startswith("*Paper_Space"):
        return (None, None)

    # Handle anonymous blocks starting with *U (dynamic block instances)
    if block_name.startswith("*U"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            return (None, None)  # Skip unresolved *U blocks

    elif block_name.startswith("A$C"):
        if block_name in anonymous_to_resolved:
            effective_name = anonymous_to_resolved[block_name]
        else:
            effective_name = block_name

    elif block_name.startswith("*"):
        return (None, None)  # Skip other system blocks
    else:
        effective_name = block_name

    # Count entities
    entity_count = sum(1 for _ in block_def)

    # Scan for nested INSERTs
    nested_inserts = []
    for entity in block_def:
        if entity.dxftype() == "INSERT":
            nested_name = entity.dxf.name
            if nested_name in anonymous_to_resolved:
                nested_name = anonymous_to_resolved[nested_name]
            nested_inserts.append(nested_name)

    # Analyze block geometry
    bbox = _get_block_bounding_box(block_def)
    native_width = round(bbox[2] - bbox[0], 2)
    native_height = round(bbox[3] - bbox[1], 2)

    vertical_points, horizontal_points = _get_intersection_points(block_def)
    vertical_segments = _calculate_segments(vertical_points)
    horizontal_segments = _calculate_segments(horizontal_points)

    block_trimming = {
        "native_width": native_width,
        "native_height": native_height,
        "vertical_segments": vertical_segments,
        "horizontal_segments": horizontal_segments,
    }

    # Detect content zone
    content_zone = _detect_content_zone(
        block_def,
        bbox,
        abort_event,
        precision_tolerance,
        gap_bridge_tolerance,
        min_area,
        min_side,
    )

    return (effective_name, {
        "entity_count": entity_count,
        "trimming_data": block_trimming,
        "content_zone_data": content_zone,
        "nested_inserts": nested_inserts,
    })
```

#### 3.3 Replace Sequential Loop with Parallel Processing (`extractor.py`)

Replace the block definition analysis loop (lines 1165-1293):

```python
# Extract block definition entity counts and geometry analysis
logger.info("Analyzing block definitions...")

# PHASE 1: Build anonymous block mappings (must be sequential - reads XDATA)
anonymous_to_resolved: dict[str, str] = {}
anonymous_resolution_details: dict[str, str] = {}

for block_def in doc.blocks:
    block_name = block_def.name

    if block_name.startswith("*U") or block_name.startswith("A$C"):
        try:
            block_record = block_def.block_record
            resolved_name, resolution_details = _resolve_dynamic_block_name(
                block_record, doc, block_name
            )
            anonymous_resolution_details[block_name] = resolution_details
            if resolved_name:
                anonymous_to_resolved[block_name] = resolved_name
            elif block_name.startswith("A$C"):
                anonymous_to_resolved[block_name] = block_name
        except (AttributeError, TypeError) as e:
            anonymous_resolution_details[block_name] = f"Error: {e}"
            if block_name.startswith("A$C"):
                anonymous_to_resolved[block_name] = block_name

# PHASE 2: Parallel block geometry analysis
block_defs_list = list(doc.blocks)
max_workers = min(8, len(block_defs_list))  # Cap at 8 threads

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = {
        executor.submit(
            _analyze_single_block,
            block_def,
            doc,
            anonymous_to_resolved,
            anonymous_resolution_details,
            abort_event,
            precision_tolerance,
            gap_bridge_tolerance,
            min_area,
            min_side,
        ): block_def.name
        for block_def in block_defs_list
    }

    for future in as_completed(futures):
        block_name = futures[future]
        try:
            effective_name, result = future.result()
            if effective_name is None or result is None:
                continue

            # Store results (thread-safe: each key is unique)
            block_entities[effective_name] = result["entity_count"]
            block_trimming_data[effective_name] = result["trimming_data"]
            block_content_zone_data[effective_name] = result["content_zone_data"]

            # Track nested relationships
            for nested_name in result["nested_inserts"]:
                if nested_name not in nested_block_parents:
                    nested_block_parents[nested_name] = set()
                nested_block_parents[nested_name].add(effective_name)

        except Exception as e:
            logger.warning(f"Error analyzing block {block_name}: {e}")
            continue

logger.info(f"Analyzed {len(block_entities)} block definitions")
```

#### 3.4 Import Updates (`extractor.py`)

Add to geometry imports:

```python
from .geometry import (
    _analyze_single_block,  # New function
    _calculate_segments,
    _categorize_rotation,
    _detect_content_zone,
    _get_block_bounding_box,
    _get_intersection_points,
)
```

---

## Unit 4: Log File Toggle

**Purpose**: Allow users to opt-in to log file generation instead of always creating files.

**Rationale**: Log files are only needed for debugging; most users don't need them cluttering their directories.

### Changes

#### 4.1 Add State Variable (`main.py:__init__`)

Add after existing BooleanVar declarations (around line 97):

```python
self.log_file_var = ctk.BooleanVar(value=False)  # Default: no log file
```

#### 4.2 Add Checkbox to GUI (`main.py:_create_widgets`)

Add in the log frame section after line 356 (after log_level_menu):

```python
# Log file generation checkbox
self.log_file_checkbox = ctk.CTkCheckBox(
    self.log_frame,
    text="Generate Log File",
    variable=self.log_file_var,
    font=ctk.CTkFont(size=12),
)
self.log_file_checkbox.pack(anchor="w", padx=5, pady=(0, 5))
```

#### 4.3 Conditionally Create File Handler (`main.py:_extraction_worker`)

Replace lines 446-455:

```python
# OLD:
# Set up debug file logging
input_path = Path(self.selected_file_path)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{input_path.stem}_debug_{timestamp}.log"
log_path = input_path.parent / log_filename

self.debug_file_handler = create_debug_file_handler(str(log_path))
logging.getLogger().addHandler(self.debug_file_handler)

self.logger.info(f"Debug log: {log_path}")
self._update_progress(0.1, f"Logging to: {log_filename}")

# NEW:
input_path = Path(self.selected_file_path)

# Conditionally set up debug file logging
if self.log_file_var.get():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{input_path.stem}_debug_{timestamp}.log"
    log_path = input_path.parent / log_filename

    self.debug_file_handler = create_debug_file_handler(str(log_path))
    logging.getLogger().addHandler(self.debug_file_handler)

    self.logger.info(f"Debug log: {log_path}")
    self._update_progress(0.1, f"Logging to: {log_filename}")
else:
    self._update_progress(0.1, "Starting extraction...")
```

---

## Unit 5: Log Level for File Output

**Purpose**: Allow users to control verbosity of log file output separately from display.

**Rationale**: Users may want INFO-level file logs without DEBUG noise, or DEBUG for troubleshooting.

### Changes

#### 5.1 Add State Variable (`main.py:__init__`)

Add after `log_file_var`:

```python
self.file_log_level_var = ctk.StringVar(value="DEBUG")
```

#### 5.2 Add Dropdown to GUI (`main.py:_create_widgets`)

Add after log_file_checkbox, creating a horizontal row:

```python
# Log file options row
log_file_options_frame = ctk.CTkFrame(self.log_frame, fg_color="transparent")
log_file_options_frame.pack(anchor="w", padx=5, pady=(0, 5))

# Log file generation checkbox
self.log_file_checkbox = ctk.CTkCheckBox(
    log_file_options_frame,
    text="Generate Log File",
    variable=self.log_file_var,
    font=ctk.CTkFont(size=12),
    command=self._on_log_file_toggle,
)
self.log_file_checkbox.pack(side="left", padx=(0, 10))

# File log level label
file_level_label = ctk.CTkLabel(
    log_file_options_frame,
    text="Level:",
    font=ctk.CTkFont(size=12),
)
file_level_label.pack(side="left", padx=(0, 5))

# File log level dropdown (disabled by default)
self.file_log_level_menu = ctk.CTkOptionMenu(
    log_file_options_frame,
    values=["DEBUG", "INFO", "WARNING"],
    variable=self.file_log_level_var,
    width=90,
    state="disabled",
)
self.file_log_level_menu.pack(side="left")
```

#### 5.3 Add Toggle Handler (`main.py`)

Add method after `_on_log_level_change`:

```python
def _on_log_file_toggle(self) -> None:
    """Handle log file checkbox toggle - enable/disable level dropdown."""
    if self.log_file_var.get():
        self.file_log_level_menu.configure(state="normal")
    else:
        self.file_log_level_menu.configure(state="disabled")
```

#### 5.4 Apply File Log Level (`main.py:_extraction_worker`)

Update the conditional file handler creation:

```python
if self.log_file_var.get():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{input_path.stem}_debug_{timestamp}.log"
    log_path = input_path.parent / log_filename

    self.debug_file_handler = create_debug_file_handler(str(log_path))

    # Apply user-selected log level to file handler
    file_level = getattr(logging, self.file_log_level_var.get())
    self.debug_file_handler.setLevel(file_level)

    logging.getLogger().addHandler(self.debug_file_handler)

    self.logger.info(f"Debug log ({self.file_log_level_var.get()}): {log_path}")
    self._update_progress(0.1, f"Logging to: {log_filename}")
else:
    self._update_progress(0.1, "Starting extraction...")
```

---

## Unit 6: Progress Feedback During Long Operations

**Purpose**: Eliminate silent 3+ minute gaps during content zone detection.

**Rationale**: Users need visibility into what's happening during long operations to distinguish progress from freezes.

### Changes

#### 6.1 Add Per-Block Start Logging (`geometry.py:_detect_content_zone`)

Add after the block_name assignment (around line 1000):

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
) -> ContentZoneData:
    block_name = block_def.name

    # UNIT 6: Progress feedback - log block processing start
    logger.info(f"[{block_name}] Detecting content zone...")

    # UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
    # ... rest of function
```

#### 6.2 Add Completion Logging (`geometry.py:_detect_content_zone`)

Add before successful return statements:

```python
# At end of function, before return with detected content zone:
logger.info(
    f"[{block_name}] Content zone detected: "
    f"{content_zone_width:.2f} x {content_zone_height:.2f}"
)
return ContentZoneData(...)

# For empty returns (no detection):
logger.debug(f"[{block_name}] No content zone detected")
return _empty_content_zone_data()
```

---

## Unit 7: Units Hint Text Update

**Purpose**: Update hint text to accurately describe which controls use the selected unit.

**Rationale**: Current text only mentions precision fix and gap bridge, but units also apply to area/side filters.

### Changes

#### 7.1 Update Label Text (`main.py:192-198`)

Replace:

```python
# OLD:
units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to precision fix and gap bridge)",
    font=ctk.CTkFont(size=10),
    text_color="gray",
)

# NEW:
units_hint = ctk.CTkLabel(
    units_frame,
    text="(applies to all numeric filters)",
    font=ctk.CTkFont(size=10),
    text_color="gray",
)
```

---

## Implementation Sequence

**Critical**: Units 1-3 must be implemented in order. Units 4-7 can be implemented in any order after Unit 3.

| Step | Unit | Reason |
|------|------|--------|
| 1 | Entity Count Pre-Check | Fastest check, eliminates most complex blocks immediately |
| 2 | Fast Edge Estimation | Second gate, avoids coordinate extraction for remaining blocks |
| 3 | Parallel Processing | Processes surviving blocks concurrently |
| 4 | Log File Toggle | Independent GUI change |
| 5 | Log Level for File | Depends on Unit 4 checkbox |
| 6 | Progress Feedback | Independent logging change |
| 7 | Units Hint Text | Independent trivial change |

**Recommended grouping:**
- Units 1-3: Performance sprint (test together)
- Units 4-5: Log file controls (implement together - shared UI area)
- Unit 6: Progress feedback (test with performance units)
- Unit 7: Quick fix (can be done anytime)

## Testing Considerations

1. **Unit 1**: Test with blocks having >1000 entities - should return empty ContentZoneData immediately
2. **Unit 2**: Test edge estimation accuracy against actual `_extract_all_edges()` counts
3. **Unit 3**: Test thread safety - run same DXF file multiple times, verify identical results
4. **Unit 4**: Verify no log file created when checkbox unchecked; log file created when checked
5. **Unit 5**: Verify file contains only messages at/above selected level
6. **Unit 6**: Verify log output shows per-block progress messages
7. **Unit 7**: Visual inspection of updated hint text

## Performance Targets

| Metric | Current | After Unit 1+2 | After Unit 3 |
|--------|---------|----------------|--------------|
| Complex block (1000+ entities) | 50-90s | <0.1s (skip) | <0.1s (skip) |
| Medium blocks (100-999 entities) | 5-50s | 5-50s | <5s (parallel) |
| Total extraction (100 blocks) | 18+ min | <5 min | <1 min |
