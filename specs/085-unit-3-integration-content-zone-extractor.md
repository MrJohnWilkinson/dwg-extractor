# Chore: Unit 3 - Integration of Filter Parameters through Content Zone and Extractor

## Chore Description

This unit threads the new filter parameters (added in Units 1-2) through the extraction pipeline from `extractor.py` to `geometry.py`. It updates function signatures to accept pre-filter parameters (`skip_curved_entities`, `min_line_length`) and post-filter parameters (`curved_filter_enabled`), then passes them through the call chain.

The integration consists of two steps:
- **Step 6**: Update Content Zone Integration in `geometry.py` - modify `_extract_paint_bucket_regions()` and `_detect_content_zone()` to accept and pass through the filter parameters
- **Step 7**: Update Extractor Params in `extractor.py` - modify `extract_blocks()` to accept the new filter parameters and pass them to `_detect_content_zone()`

This is a wiring/integration unit - no new filtering logic is implemented, just parameter threading through existing function signatures.

## Relevant Files

Use these files to resolve the chore:

- **`app/core/geometry.py`** - Contains `_extract_paint_bucket_regions()` (~line 732) and `_detect_content_zone()` (~line 1167) that need signature updates to accept and pass filter parameters. Also contains `_polygon_has_curved_edges()` (~line 827) added in Unit 2 for post-filter detection.
- **`app/core/extractor.py`** - Contains `extract_blocks()` (~line 975) that needs new parameters and must pass them through to `_detect_content_zone()`.
- **`app/core/constants.py`** - Contains the filter constants added in Unit 1: `DEFAULT_SKIP_CURVED_ENTITIES`, `DEFAULT_MIN_LINE_LENGTH_FILTER`, `DEFAULT_CURVED_FILTER_ENABLED`. Reference for default values.
- **`app/tests/core/test_geometry.py`** - Existing geometry tests. May need updates if tests call modified functions directly with positional args.
- **`app/tests/core/test_content_zone.py`** - Existing content zone tests. May need updates if tests call `_detect_content_zone()` directly.
- **`app/tests/core/extractor/test_extractor_core.py`** - Existing extractor tests. Verify `extract_blocks()` signature changes don't break existing tests.

## Step by Step Tasks

### Step 1: Update `_extract_paint_bucket_regions()` signature in `app/core/geometry.py`

Modify the function signature at line 732 to accept pre-filter parameters:

**Current signature:**
```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
) -> list[Polygon]:
```

**New signature:**
```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[Polygon]:
```

- Add `skip_curved_entities: bool = False` parameter after `gap_bridge_tolerance`
- Add `min_line_length: float = 0.0` parameter after `skip_curved_entities`
- Update the docstring to document the new pre-filter parameters

### Step 2: Pass pre-filter params to `_extract_all_edges()` in `_extract_paint_bucket_regions()`

Update the `_extract_all_edges()` call inside `_extract_paint_bucket_regions()` (around line 770) to pass the pre-filter parameters:

**Current call:**
```python
edges = _extract_all_edges(block_def)
```

**New call:**
```python
edges = _extract_all_edges(
    block_def,
    skip_curved_entities=skip_curved_entities,
    min_line_length=min_line_length,
)
```

### Step 3: Update `_detect_content_zone()` signature in `app/core/geometry.py`

Modify the function signature at line 1167 to accept all filter parameters:

**Current signature (partial):**
```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
    *,
    polygon_count_threshold: int = POLYGON_COUNT_THRESHOLD,
    line_segment_threshold: int = LINE_SEGMENT_THRESHOLD,
    entity_count_threshold: int = ENTITY_COUNT_THRESHOLD,
) -> ContentZoneData:
```

**New signature:**
```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
    curved_filter_enabled: bool = False,
    *,
    polygon_count_threshold: int = POLYGON_COUNT_THRESHOLD,
    line_segment_threshold: int = LINE_SEGMENT_THRESHOLD,
    entity_count_threshold: int = ENTITY_COUNT_THRESHOLD,
) -> ContentZoneData:
```

- Add `skip_curved_entities: bool = False` after `min_side_filter`
- Add `min_line_length: float = 0.0` after `skip_curved_entities`
- Add `curved_filter_enabled: bool = False` after `min_line_length`
- Update the docstring to document all new parameters

### Step 4: Pass pre-filter params to `_extract_paint_bucket_regions()` in `_detect_content_zone()`

Update the `_extract_paint_bucket_regions()` call inside `_detect_content_zone()` (around line 1272) to pass the pre-filter parameters:

**Current call:**
```python
all_shapes = _extract_paint_bucket_regions(
    block_def, abort_event, precision_tolerance, gap_bridge_tolerance
)
```

**New call:**
```python
all_shapes = _extract_paint_bucket_regions(
    block_def,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
    skip_curved_entities,
    min_line_length,
)
```

### Step 5: Add curved filter post-processing in `_detect_content_zone()`

Add the curved filter logic AFTER the paint bucket regions call and BEFORE the side filter (around line 1284). The curved filter should be applied before the side filter for efficiency (filter out curved polygons early):

**Insert this code after `all_shapes = _extract_paint_bucket_regions(...)` call and before the side filter block:**

```python
# Post-filter: Curved lines filter (before side filter for efficiency)
if curved_filter_enabled:
    pre_curved_count = len(all_shapes)
    all_shapes = [
        s for s in all_shapes
        if not _polygon_has_curved_edges(s)
    ]
    logger.debug(
        f"[{block_name}] Curved filter: {pre_curved_count} -> {len(all_shapes)} polygons"
    )
```

### Step 6: Update `extract_blocks()` signature in `app/core/extractor.py`

Modify the function signature at line 975 to accept the new filter parameters:

**Current signature (partial - showing filter section):**
```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,
    min_area_filter_amount: float | None = None,
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
    # Early-exit threshold parameters
    polygon_count_threshold: int | None = None,
    ...
```

**New signature (insert after `min_side_filter_amount` and before threshold params):**
```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,
    min_area_filter_amount: float | None = None,
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
    # Pre-Filters
    skip_curved_entities: bool = False,
    min_line_length_filter_enabled: bool = False,
    min_line_length_filter_amount: float | None = None,
    # Post-Filters
    curved_filter_enabled: bool = False,
    # Early-exit threshold parameters
    polygon_count_threshold: int | None = None,
    ...
```

- Add `skip_curved_entities: bool = False` with "Pre-Filters" comment
- Add `min_line_length_filter_enabled: bool = False`
- Add `min_line_length_filter_amount: float | None = None`
- Add `curved_filter_enabled: bool = False` with "Post-Filters" comment
- Update the docstring to document all new parameters

### Step 7: Calculate effective min_line_length value in `extract_blocks()`

Add calculation logic after the `get_filter_values()` call (around line 1134) to compute the effective `min_line_length` value:

**Insert this code after the `logger.info(f"Using polygon filters: ...")` line:**

```python
# Calculate effective min line length
min_line_length = 0.0
if min_line_length_filter_enabled and min_line_length_filter_amount:
    min_line_length = min_line_length_filter_amount
logger.info(
    f"Using pre-filters: skip_curved={skip_curved_entities}, "
    f"min_line_length={min_line_length} "
    f"(min_line_filter={'enabled' if min_line_length_filter_enabled else 'disabled'})"
)
logger.info(
    f"Using post-filters: curved_filter={'enabled' if curved_filter_enabled else 'disabled'}"
)
```

### Step 8: Pass all filter params to `_detect_content_zone()` in `extract_blocks()`

Update the `_detect_content_zone()` call inside the block processing loop (around line 1288) to pass all filter parameters:

**Current call:**
```python
content_zone = _detect_content_zone(
    block_def,
    bbox,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
    min_area,
    min_side,
    polygon_count_threshold=effective_polygon_threshold,
    line_segment_threshold=effective_line_threshold,
    entity_count_threshold=effective_entity_threshold,
)
```

**New call:**
```python
content_zone = _detect_content_zone(
    block_def,
    bbox,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
    min_area,
    min_side,
    skip_curved_entities,
    min_line_length,
    curved_filter_enabled,
    polygon_count_threshold=effective_polygon_threshold,
    line_segment_threshold=effective_line_threshold,
    entity_count_threshold=effective_entity_threshold,
)
```

### Step 9: Update docstrings for all modified functions

Ensure all modified functions have updated docstrings that document the new parameters:

**`_extract_paint_bucket_regions()` docstring additions:**
```
Args:
    ...
    skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
        extraction. Default False.
    min_line_length: Skip LINE entities shorter than this threshold (drawing units).
        Default 0.0 (no filtering).
```

**`_detect_content_zone()` docstring additions:**
```
Args:
    ...
    skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
        extraction. Default False (pre-filter).
    min_line_length: Skip LINE entities shorter than this threshold during edge
        extraction. Default 0.0 (pre-filter).
    curved_filter_enabled: If True, filter out polygons that contain curved edges
        (detected via vertex analysis). Default False (post-filter).
```

**`extract_blocks()` docstring additions:**
```
Args:
    ...
    skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
        extraction for content zone detection. Default False.
    min_line_length_filter_enabled: Enable minimum line length filtering.
        When True, short LINE entities are filtered out. Default False.
    min_line_length_filter_amount: Minimum line length threshold. Lines shorter
        than this are excluded. If None or <= 0, filter is inactive.
    curved_filter_enabled: Enable curved polygon post-filtering.
        When True, polygons containing curved edges are filtered out. Default False.
```

### Step 10: Verify existing tests still pass

Run tests to ensure the signature changes don't break existing functionality. The default parameter values should ensure backward compatibility.

- Run `uv run pytest app/tests/core/test_geometry.py -v` to verify geometry tests
- Run `uv run pytest app/tests/core/test_content_zone.py -v` to verify content zone tests
- Run `uv run pytest app/tests/core/extractor/ -v` to verify extractor tests

### Step 11: Run full validation suite

Execute all validation commands to ensure zero regressions.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_geometry.py -v` - Run geometry tests to verify signature changes
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Notes

- **Backward Compatibility**: All new parameters have default values that preserve existing behavior:
  - `skip_curved_entities=False` - curved entities are processed as before
  - `min_line_length=0.0` - no line filtering by default
  - `curved_filter_enabled=False` - no curved polygon filtering by default

- **Parameter Ordering**: The new parameters are inserted AFTER existing filters but BEFORE the keyword-only threshold parameters (after the `*,` marker). This maintains a logical grouping:
  1. Snap tolerances (precision_tolerance, gap_bridge_tolerance)
  2. Post-filters (min_area_filter, min_side_filter)
  3. Pre-filters (skip_curved_entities, min_line_length)
  4. Post-filters (curved_filter_enabled)
  5. Threshold parameters (keyword-only)

- **Filter Order in `_detect_content_zone()`**: The curved filter is applied AFTER paint bucket regions but BEFORE the side filter. This order is chosen because:
  1. Curved filter is cheap (O(n) polygon analysis)
  2. Filtering curved polygons early reduces the count for subsequent expensive operations
  3. Side filter comes next (also O(n) but more complex per-polygon)
  4. Area filter comes last (requires O(n^2) net area calculation)

- **No GUI Changes**: This unit only threads parameters through the pipeline. GUI controls will be added in a future unit (Unit 4 or 5).

- **Testing Strategy**: Since this is a wiring-only change with backward-compatible defaults, existing tests should pass without modification. No new tests are required for this unit - the filter functionality was tested in Unit 2, and end-to-end integration testing will come in the GUI unit.

- **Logger Messages**: Added info-level logging for the new filter settings to help with debugging and user feedback during extraction.
