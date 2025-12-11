# Early Exit and Parallel Processing Implementation Plan

## Executive Summary
This plan implements three targeted optimizations for content zone detection: early entity count pre-check, fast edge count estimation, and parallel block processing. The sequence is critical - faster checks must run first to skip expensive operations early. Combined, these changes target reducing complex block processing from 50-90 seconds to <5 seconds (skip) or eliminating the bottleneck entirely via parallelization.

## Table Summary

| Unit | Change | Location | Impact | Risk |
|------|--------|----------|--------|------|
| 1 | Entity count pre-check | `geometry.py:_detect_content_zone()` | Skip before ANY geometry work | Low |
| 2 | Fast edge count estimation | `geometry.py` (new function) | Skip before coordinate extraction | Low |
| 3 | Parallel block processing | `extractor.py:extract_blocks()` | Process all blocks concurrently | Medium |

## Relevant Files

- `app/core/geometry.py:990-1191` - `_detect_content_zone()` function where early exits are added
- `app/core/geometry.py:595-642` - `_extract_all_edges()` that we want to avoid calling
- `app/core/extractor.py:1164-1293` - Block definition analysis loop to parallelize
- `app/core/constants.py:160-170` - Threshold constants to add `ENTITY_COUNT_THRESHOLD`

## In-Scope

1. Add `ENTITY_COUNT_THRESHOLD` constant (1000 entities)
2. Add entity count pre-check in `_detect_content_zone()` BEFORE any geometry extraction
3. Create `_estimate_edge_count()` function for fast O(n) edge counting without coordinates
4. Replace `len(_extract_all_edges(block_def))` with `_estimate_edge_count()` for threshold check
5. Parallelize block definition analysis using `concurrent.futures.ThreadPoolExecutor`
6. Add thread-safe result collection for parallel processing

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

## Implementation Sequence

**Critical**: Units must be implemented in order 1 → 2 → 3.

| Step | Unit | Reason |
|------|------|--------|
| 1 | Entity Count Pre-Check | Fastest check, eliminates most complex blocks immediately |
| 2 | Fast Edge Estimation | Second gate, avoids coordinate extraction for remaining blocks |
| 3 | Parallel Processing | Processes surviving blocks concurrently |

The sequence ensures that by the time parallel processing runs, most complex blocks have already been skipped by the cheaper checks.

## Testing Considerations

1. **Unit 1**: Test with blocks having >1000 entities - should return empty ContentZoneData immediately
2. **Unit 2**: Test edge estimation accuracy against actual `_extract_all_edges()` counts
3. **Unit 3**: Test thread safety - run same DXF file multiple times, verify identical results

## Performance Targets

| Metric | Current | After Unit 1+2 | After Unit 3 |
|--------|---------|----------------|--------------|
| Complex block (1000+ entities) | 50-90s | <0.1s (skip) | <0.1s (skip) |
| Medium blocks (100-999 entities) | 5-50s | 5-50s | <5s (parallel) |
| Total extraction (100 blocks) | 18+ min | <5 min | <1 min |
