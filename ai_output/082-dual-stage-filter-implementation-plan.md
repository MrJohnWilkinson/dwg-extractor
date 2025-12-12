# Dual-Stage Filter Implementation Plan

## Executive Summary

This plan consolidates the dual-stage filter architecture (report 081) and curved lines filter (plan 079) into a unified implementation. The architecture separates **entity-level pre-filters** (before `unary_union`) from **polygon-level post-filters** (after `polygonize`). Pre-filters reduce computational load; post-filters validate correctness. The implementation adds 3 new filters: 2 pre-filters (Skip Curved Entities, Min Line Length Filter) and 1 post-filter (Curved Lines Filter).

## Table Summary

| Step | Component | File | Description |
|------|-----------|------|-------------|
| 1 | Constants | `app/core/constants.py` | Add 3 new filter constants and validation registry entries |
| 2 | Types | `app/core/types.py` | Add 3 new settings to AppSettings TypedDict |
| 3 | Settings Section | `app/core/settings.py` | Add 3 new settings to SETTINGS_SECTIONS "filters" list |
| 4 | Pre-Filter Logic | `app/core/geometry.py` | Add `_extract_all_edges()` pre-filter parameters |
| 5 | Post-Filter Logic | `app/core/geometry.py` | Add `_polygon_has_curved_edges()` function |
| 6 | Content Zone Integration | `app/core/geometry.py` | Add filter params to `_detect_content_zone()` |
| 7 | Extractor Params | `app/core/extractor.py` | Thread 3 new filter params through `extract_blocks()` |
| 8 | Main GUI | `app/main.py` | Add Pre-Filters section with 2 controls |
| 9 | Main GUI | `app/main.py` | Add Curved Lines Filter to Post-Filters section |
| 10 | Settings Window | `app/core/settings_window.py` | Add Pre-Filters and Post-Filters subsections |
| 11 | Unit Tests | `app/tests/core/` | Add tests for pre-filters and post-filter |
| 12 | Type Check & Lint | - | Run mypy and ruff to verify |

## Relevant Files

- **`app/core/constants.py`** - All filter constants (defaults, min/max values, validation registry). Lines 273-422.
- **`app/core/types.py`** - `AppSettings` TypedDict (lines 274-322) where new filter settings must be added.
- **`app/core/settings.py`** - `SETTINGS_SECTIONS` (lines 52-88) mapping filters to their settings keys.
- **`app/core/geometry.py`** - `_extract_all_edges()` (lines 658-706), `_extract_paint_bucket_regions()` (lines 708-800), `_detect_content_zone()` (lines 1069-1316).
- **`app/core/extractor.py`** - `extract_blocks()` (lines 975-1706) which passes filter params to geometry functions.
- **`app/main.py`** - GUI filter controls (lines 320-382) and extraction worker (lines 565-720).
- **`app/core/settings_window.py`** - Filters tab (lines 539-664) with read-only filter display.
- **`ai_output/079-curved-lines-filter-implementation-plan.md`** - Original curved filter plan (post-filter).
- **`ai_output/081-dual-stage-filter-architecture-analysis.md`** - Dual-stage architecture design.

## In-Scope

1. **Pre-Filter 1**: Skip Curved Entities filter - excludes CIRCLE and ARC entities from edge extraction
2. **Pre-Filter 2**: Min Line Length Filter - excludes LINE entities below length threshold
3. **Post-Filter**: Curved Lines Filter - excludes polygons containing curved edges
4. **GUI**: New "Pre-Filters" section in main window with labeled visual separation
5. **GUI**: Add Curved Lines Filter checkbox to existing Post-Filters section
6. **Settings Window**: Add Pre-Filters and Post-Filters subsections in Filters tab
7. **Constants**: Add defaults and validation registry entries for all 3 filters
8. **Types**: Add new settings to AppSettings TypedDict
9. **Extraction Pipeline**: Thread all filter params through extractor to geometry
10. **Unit Tests**: Test pre-filter entity exclusion and post-filter curve detection

## Out-of-Scope

1. Per-filter timing logs (future diagnostic feature)
2. Automatic fallback retry without pre-filters (mentioned in 081 but adds complexity)
3. GUI tooltips (would require customtkinter ToolTip implementation)
4. Unit override integration for Min Line Length Filter (use absolute units)
5. Curved entity detection tolerance settings (use fixed tolerance)
6. Changes to existing filter behavior (precision fix, gap bridge, min area, min side)
7. Excel output format changes
8. Performance benchmarking (separate task)

## ASCII UI Mockup

```
┌──────────────────────────────────────────────────────────────┐
│                    DXF Block Extractor                       │
├──────────────────────────────────────────────────────────────┤
│  [Browse...]  /path/to/drawing.dxf                           │
│                                                              │
│  Units: [Auto-detect ▼]                                      │
│                                                              │
│  ══════════════════ PRE-FILTERS ══════════════════           │
│  (Applied before polygon detection - reduces processing)     │
│                                                              │
│  [✓] Skip Curved Entities     (excludes circles and arcs)   │
│                                                              │
│  ─────────────────────────────────────────────────           │
│                                                              │
│  [✓] Min Line Length Filter   Amount: [0.5    ]              │
│                               (excludes short LINE entities) │
│                                                              │
│  ═══════════════════ FILTERS ═══════════════════             │
│  (Applied after polygon detection - validates shapes)        │
│                                                              │
│  [✓] Precision Fix            Amount: [0.000001]             │
│                                                              │
│  ─────────────────────────────────────────────────           │
│                                                              │
│  [ ] Gap Bridge               Amount: [0.1     ]             │
│                                                              │
│  ─────────────────────────────────────────────────           │
│                                                              │
│  [✓] Min Area Filter          Amount: [10.0   ]              │
│                                                              │
│  ─────────────────────────────────────────────────           │
│                                                              │
│  [✓] Min Side Filter          Amount: [2.0    ]              │
│                                                              │
│  ─────────────────────────────────────────────────           │
│                                                              │
│  [✓] Curved Lines Filter      (excludes polygons with arcs)  │
│                                                              │
│  ════════════════════════════════════════════════            │
│                                                              │
│  [========================================] 100%             │
│                                                              │
│  Status: Extraction complete                                 │
│                                                              │
│  ┌────────────────────────────────────────────────┐          │
│  │ Log Viewer                                     │          │
│  └────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### Settings Window - Filters Tab Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Filters | Performance | Precision | Output | Logging        │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ i  Filter settings are configured in the main window.  │ │
│  │    This tab displays current values for reference only.│ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  PRE-FILTERS                               [Reset Section]   │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Skip Curved Entities                              Yes       │
│  Excludes CIRCLE and ARC entities from edge                  │
│  extraction to reduce polygon detection workload.            │
│                                                              │
│  Min Line Length Filter                            Yes       │
│  Filters out LINE entities shorter than threshold.           │
│                                                              │
│  Min Line Length Amount                            0.5       │
│  Minimum LINE entity length in drawing units.                │
│                                                              │
│  POST-FILTERS                              [Reset Section]   │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Precision Fix                                     Yes       │
│  Closes small floating-point gaps in polygon edges.          │
│                                                              │
│  Precision Fix Amount                              0.000001  │
│  Maximum gap size to close (in drawing units).               │
│                                                              │
│  Gap Bridge                                        No        │
│  Bridges larger intentional gaps using buffering.            │
│                                                              │
│  ...                                                         │
│                                                              │
│  Curved Lines Filter                               Yes       │
│  Excludes polygons containing curved edges.                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Add Constants (`app/core/constants.py`)

Add after line 311 (after `MIN_SIDE_FILTER_MAX`):

```python
# Pre-Filter: Skip Curved Entities
DEFAULT_SKIP_CURVED_ENTITIES: bool = False
"""Default state for skip curved entities pre-filter (disabled by default)."""

# Pre-Filter: Min Line Length Filter
DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED: bool = False
"""Default state for min line length filter (disabled by default)."""

DEFAULT_MIN_LINE_LENGTH_FILTER: float = 0.5
"""Default minimum line length in drawing units."""

MIN_LINE_LENGTH_FILTER_MIN: float = 0.0
"""Minimum allowed value for min line length filter."""

MIN_LINE_LENGTH_FILTER_MAX: float = 100.0
"""Maximum allowed value for min line length filter."""

# Post-Filter: Curved Lines Filter
DEFAULT_CURVED_FILTER_ENABLED: bool = False
"""Default state for curved lines filter (disabled by default)."""

CURVED_FILTER_TOLERANCE: float = 0.01
"""Tolerance for detecting curved segments in polygons."""
```

Add to `SETTINGS_VALIDATION_REGISTRY` (after `min_side_filter_amount` entry):

```python
    # Pre-Filters
    "skip_curved_entities": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_line_length_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_line_length_filter_amount": {
        "min_value": 0.0,
        "max_value": 100.0,
        "default": 0.5,
        "unit_aware": False,
    },
    # Post-Filters
    "curved_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
```

### Step 2: Add Types (`app/core/types.py`)

Add to `AppSettings` TypedDict (after `min_side_filter_amount`, ~line 298):

```python
    # Pre-Filters
    skip_curved_entities: bool
    min_line_length_filter_enabled: bool
    min_line_length_filter_amount: float | None
    # Post-Filters
    curved_filter_enabled: bool
```

### Step 3: Add to Settings Section (`app/core/settings.py`)

Update `SETTINGS_SECTIONS["filters"]` list to include new settings:

```python
    "filters": [
        "unit_override",
        # Pre-Filters
        "skip_curved_entities",
        "min_line_length_filter_enabled",
        "min_line_length_filter_amount",
        # Post-Filters (existing + new)
        "precision_fix_enabled",
        "precision_fix_amount",
        "gap_bridge_enabled",
        "gap_bridge_amount",
        "min_area_filter_enabled",
        "min_area_filter_amount",
        "min_side_filter_enabled",
        "min_side_filter_amount",
        "curved_filter_enabled",
    ],
```

### Step 4: Add Pre-Filter Logic (`app/core/geometry.py`)

Modify `_extract_all_edges()` signature and implementation (~line 658):

```python
def _extract_all_edges(
    block_def: BlockLayout,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Pre-filter options (reduce edge count before union):
    - skip_curved_entities: Skip CIRCLE and ARC entities entirely
    - min_line_length: Skip LINE entities shorter than threshold

    ... existing docstring ...
    """
    edges: list[LineString] = []

    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            # PRE-FILTER: Skip short LINE entities
            if min_line_length > 0:
                length = math.sqrt(
                    (end.x - start.x) ** 2 + (end.y - start.y) ** 2
                )
                if length < min_line_length:
                    continue
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            # ... existing code unchanged ...

        elif entity_type == "CIRCLE":
            # PRE-FILTER: Skip curved entities
            if skip_curved_entities:
                continue
            edges.extend(_extract_circle_edges(entity))

        elif entity_type == "ARC":
            # PRE-FILTER: Skip curved entities
            if skip_curved_entities:
                continue
            edges.extend(_extract_arc_edges(entity))

        elif entity_type == "HATCH":
            edges.extend(_extract_hatch_boundary_edges(entity))

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges
```

### Step 5: Add Post-Filter Logic (`app/core/geometry.py`)

Add new function after `_extract_paint_bucket_regions()` (~line 801):

```python
def _polygon_has_curved_edges(
    polygon: Polygon,
    tolerance: float = 0.01,
) -> bool:
    """
    Detect if a polygon contains curved (non-straight) edges.

    A polygon is considered to have curved edges if any edge has
    intermediate points that deviate from a straight line by more
    than the tolerance. This detects arcs/circles that were flattened
    during edge extraction.

    Args:
        polygon: List of (x, y) vertices
        tolerance: Maximum deviation from straight line to consider
                   an edge as straight. Default 0.01 drawing units.

    Returns:
        True if polygon contains curved edges, False if all edges
        are straight (within tolerance).
    """
    if len(polygon) < 3:
        return False

    # For each triplet of consecutive vertices, check if middle point
    # deviates from the line connecting first and third points
    n = len(polygon)
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        p3 = polygon[(i + 2) % n]

        # Calculate perpendicular distance from p2 to line p1-p3
        ax, ay = p3[0] - p1[0], p3[1] - p1[1]
        bx, by = p2[0] - p1[0], p2[1] - p1[1]

        cross = abs(ax * by - ay * bx)
        line_length = math.sqrt(ax * ax + ay * ay)

        if line_length > 1e-9:
            distance = cross / line_length
            if distance > tolerance:
                return True

    return False
```

### Step 6: Update Content Zone Integration (`app/core/geometry.py`)

Modify `_extract_paint_bucket_regions()` to accept pre-filter params:

```python
def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[Polygon]:
    """... existing docstring with pre-filter additions ..."""
    t_start = time.perf_counter()
    edges = _extract_all_edges(
        block_def,
        skip_curved_entities=skip_curved_entities,
        min_line_length=min_line_length,
    )
    # ... rest unchanged ...
```

Modify `_detect_content_zone()` signature and implementation (~line 1069):

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

Update paint bucket call:

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

Add curved filter AFTER paint bucket, BEFORE side filter:

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

### Step 7: Update Extractor Params (`app/core/extractor.py`)

Add parameters to `extract_blocks()` signature:

```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    *,
    # ... existing params ...
    min_side_filter_enabled: bool = False,
    min_side_filter_amount: float | None = None,
    # Pre-Filters
    skip_curved_entities: bool = False,
    min_line_length_filter_enabled: bool = False,
    min_line_length_filter_amount: float | None = None,
    # Post-Filters
    curved_filter_enabled: bool = False,
    # Early-exit thresholds
    polygon_count_threshold: int | None = None,
    # ...
) -> ExtractionResult:
```

Calculate effective values and pass to `_detect_content_zone()`:

```python
    # Calculate effective min line length
    min_line_length = 0.0
    if min_line_length_filter_enabled and min_line_length_filter_amount:
        min_line_length = min_line_length_filter_amount
```

Pass all params to content zone detection:

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

### Step 8: Add Main GUI Pre-Filters Section (`app/main.py`)

Add instance variables after existing filter vars:

```python
        # Pre-Filter settings
        self.skip_curved_entities_var = ctk.BooleanVar(
            value=self.settings.get("skip_curved_entities")
        )
        self.min_line_length_filter_var = ctk.BooleanVar(
            value=self.settings.get("min_line_length_filter_enabled")
        )
        self.min_line_length_filter_amount_var = ctk.StringVar(
            value=str(self.settings.get("min_line_length_filter_amount") or "")
        )
```

Add Pre-Filters section BEFORE existing filters (after Units dropdown):

```python
        # Pre-Filters section header
        prefilter_header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        prefilter_header_frame.pack(fill="x", pady=(10, 5))

        prefilter_label = ctk.CTkLabel(
            prefilter_header_frame,
            text="PRE-FILTERS",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        prefilter_label.pack(side="left")

        prefilter_hint = ctk.CTkLabel(
            prefilter_header_frame,
            text="(reduces processing before polygon detection)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        prefilter_hint.pack(side="left", padx=(10, 0))

        # Pre-filter separator
        prefilter_sep = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray40")
        prefilter_sep.pack(fill="x", pady=(0, 10))

        # Skip Curved Entities checkbox
        skip_curved_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        skip_curved_frame.pack(pady=(5, 10))

        self.skip_curved_checkbox = ctk.CTkCheckBox(
            skip_curved_frame,
            text="Skip Curved Entities",
            variable=self.skip_curved_entities_var,
            command=self._on_skip_curved_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.skip_curved_checkbox.pack(side="left", padx=(0, 10))

        skip_curved_hint = ctk.CTkLabel(
            skip_curved_frame,
            text="(excludes circles and arcs)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        skip_curved_hint.pack(side="left")

        # Separator
        separator_prefilter1 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator_prefilter1.pack(fill="x", pady=5)

        # Min Line Length Filter row
        min_line_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        min_line_frame.pack(pady=(5, 10))

        self.min_line_length_checkbox = ctk.CTkCheckBox(
            min_line_frame,
            text="Min Line Length Filter",
            variable=self.min_line_length_filter_var,
            command=self._on_min_line_length_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.min_line_length_checkbox.pack(side="left", padx=(0, 10))

        min_line_amount_label = ctk.CTkLabel(
            min_line_frame,
            text="Amount:",
            font=ctk.CTkFont(size=12),
        )
        min_line_amount_label.pack(side="left", padx=(0, 5))

        self.min_line_length_entry = ctk.CTkEntry(
            min_line_frame,
            width=80,
            textvariable=self.min_line_length_filter_amount_var,
            state="disabled",
        )
        self.min_line_length_entry.pack(side="left")

        # Filters section header (existing filters become "FILTERS")
        filter_header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        filter_header_frame.pack(fill="x", pady=(15, 5))

        filter_label = ctk.CTkLabel(
            filter_header_frame,
            text="FILTERS",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        filter_label.pack(side="left")

        filter_hint = ctk.CTkLabel(
            filter_header_frame,
            text="(validates shapes after polygon detection)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        filter_hint.pack(side="left", padx=(10, 0))

        filter_sep = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray40")
        filter_sep.pack(fill="x", pady=(0, 10))
```

### Step 9: Add Curved Lines Filter (`app/main.py`)

Add instance variable:

```python
        # Curved Lines Filter setting
        self.curved_filter_var = ctk.BooleanVar(
            value=self.settings.get("curved_filter_enabled")
        )
```

Add after Min Side Filter section, before progress bar:

```python
        # Fifth separator
        separator5 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator5.pack(fill="x", pady=5)

        # Curved Lines Filter row
        curved_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        curved_frame.pack(pady=(5, 10))

        self.curved_filter_checkbox = ctk.CTkCheckBox(
            curved_frame,
            text="Curved Lines Filter",
            variable=self.curved_filter_var,
            command=self._on_curved_filter_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.curved_filter_checkbox.pack(side="left", padx=(0, 10))

        curved_hint = ctk.CTkLabel(
            curved_frame,
            text="(excludes polygons with curved edges)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        curved_hint.pack(side="left")
```

Add toggle handlers:

```python
    def _on_skip_curved_toggle(self) -> None:
        """Handle skip curved entities checkbox toggle."""
        self._sync_settings_to_manager()

    def _on_min_line_length_toggle(self) -> None:
        """Handle min line length filter checkbox toggle."""
        enabled = self.min_line_length_filter_var.get()
        state = "normal" if enabled else "disabled"
        self.min_line_length_entry.configure(state=state)
        self._sync_settings_to_manager()

    def _on_curved_filter_toggle(self) -> None:
        """Handle curved filter checkbox toggle."""
        self._sync_settings_to_manager()
```

Update `_sync_settings_to_manager()`:

```python
        # Pre-Filters
        self.settings.set("skip_curved_entities", self.skip_curved_entities_var.get())
        self.settings.set("min_line_length_filter_enabled", self.min_line_length_filter_var.get())
        try:
            amount = float(self.min_line_length_filter_amount_var.get())
            self.settings.set("min_line_length_filter_amount", amount)
        except ValueError:
            pass
        # Post-Filters
        self.settings.set("curved_filter_enabled", self.curved_filter_var.get())
```

Update `_extraction_worker()` to pass new params:

```python
            # Pre-Filters
            skip_curved_entities = self.skip_curved_entities_var.get()
            min_line_length_filter_enabled = self.min_line_length_filter_var.get()
            min_line_length_filter_amount = None
            if min_line_length_filter_enabled:
                try:
                    min_line_length_filter_amount = float(
                        self.min_line_length_filter_amount_var.get()
                    )
                except ValueError:
                    pass
            # Post-Filters
            curved_filter_enabled = self.curved_filter_var.get()
```

Pass to `extract_blocks()`:

```python
                skip_curved_entities=skip_curved_entities,
                min_line_length_filter_enabled=min_line_length_filter_enabled,
                min_line_length_filter_amount=min_line_length_filter_amount,
                curved_filter_enabled=curved_filter_enabled,
```

### Step 10: Update Settings Window (`app/core/settings_window.py`)

Update `_populate_filters_tab()` to add Pre-Filters and Post-Filters subsections:

```python
    def _populate_filters_tab(self, parent: ctk.CTkFrame) -> None:
        """Populate the Filters tab with settings."""
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Section header
        self._create_section_header(scroll_frame, "Filter Settings", "filters")

        # Info banner (existing)
        # ... existing info_frame code ...

        # PRE-FILTERS subsection
        prefilter_label = ctk.CTkLabel(
            scroll_frame,
            text="Pre-Filters",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        prefilter_label.pack(anchor="w", pady=(10, 5))

        prefilter_desc = ctk.CTkLabel(
            scroll_frame,
            text="Applied before polygon detection to reduce processing",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        prefilter_desc.pack(anchor="w", pady=(0, 10))

        self._create_setting_row(
            scroll_frame,
            "skip_curved_entities",
            "Skip Curved Entities",
            "Excludes CIRCLE and ARC entities from edge extraction. "
            "Reduces polygon detection workload for drawings with many curves.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_line_length_filter_enabled",
            "Min Line Length Filter",
            "Filters out LINE entities shorter than the threshold. "
            "Useful for removing small detail lines.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_line_length_filter_amount",
            "Min Line Length Amount",
            "Minimum LINE entity length in drawing units. "
            "Lines shorter than this are excluded.",
            readonly=True,
        )

        # POST-FILTERS subsection
        postfilter_label = ctk.CTkLabel(
            scroll_frame,
            text="Post-Filters",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        postfilter_label.pack(anchor="w", pady=(15, 5))

        postfilter_desc = ctk.CTkLabel(
            scroll_frame,
            text="Applied after polygon detection to validate shapes",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        postfilter_desc.pack(anchor="w", pady=(0, 10))

        # ... existing filter rows (precision_fix, gap_bridge, min_area, min_side) ...

        self._create_setting_row(
            scroll_frame,
            "curved_filter_enabled",
            "Curved Lines Filter",
            "Excludes polygons containing curved edges (arcs, circles). "
            "Useful for focusing on rectangular shapes only.",
            readonly=True,
        )

        # Unit override (standalone)
        self._create_setting_row(
            scroll_frame,
            "unit_override",
            "Unit Override",
            "Manual unit override for drawing interpretation. "
            "None means auto-detect from DXF file.",
            readonly=True,
        )
```

### Step 11: Add Unit Tests

Create `app/tests/core/test_prefilters.py`:

```python
"""Tests for pre-filter functionality in geometry module."""

import pytest
from unittest.mock import MagicMock


class TestExtractAllEdgesPreFilters:
    """Tests for _extract_all_edges pre-filter parameters."""

    def test_skip_curved_entities_excludes_circles(self):
        """CIRCLE entities should be excluded when skip_curved_entities=True."""
        # ... test implementation

    def test_skip_curved_entities_excludes_arcs(self):
        """ARC entities should be excluded when skip_curved_entities=True."""
        # ... test implementation

    def test_min_line_length_excludes_short_lines(self):
        """LINE entities shorter than threshold should be excluded."""
        # ... test implementation

    def test_min_line_length_keeps_long_lines(self):
        """LINE entities longer than threshold should be kept."""
        # ... test implementation

    def test_prefilters_disabled_by_default(self):
        """Pre-filters should not affect extraction when disabled."""
        # ... test implementation
```

Create `app/tests/core/test_curved_filter.py`:

```python
"""Tests for curved lines filter (post-filter) functionality."""

import pytest
from core.geometry import _polygon_has_curved_edges


class TestPolygonHasCurvedEdges:
    """Tests for _polygon_has_curved_edges function."""

    def test_rectangle_no_curves(self):
        """Rectangle should not be detected as curved."""
        rect = [(0, 0), (100, 0), (100, 50), (0, 50)]
        assert _polygon_has_curved_edges(rect) is False

    def test_triangle_no_curves(self):
        """Triangle should not be detected as curved."""
        tri = [(0, 0), (50, 100), (100, 0)]
        assert _polygon_has_curved_edges(tri) is False

    def test_arc_approximation_detected(self):
        """Flattened arc should be detected as curved."""
        arc = [
            (0, 0), (10, 0),
            (20, 2), (28, 6), (34, 12), (38, 20), (40, 30),
            (40, 50), (0, 50)
        ]
        assert _polygon_has_curved_edges(arc) is True

    def test_degenerate_polygon(self):
        """Degenerate polygon (< 3 vertices) returns False."""
        assert _polygon_has_curved_edges([]) is False
        assert _polygon_has_curved_edges([(0, 0)]) is False
        assert _polygon_has_curved_edges([(0, 0), (1, 1)]) is False

    def test_hexagon_no_curves(self):
        """Regular hexagon should not be detected as curved."""
        import math
        hexagon = [
            (math.cos(i * math.pi / 3), math.sin(i * math.pi / 3))
            for i in range(6)
        ]
        assert _polygon_has_curved_edges(hexagon) is False
```

### Step 12: Type Check and Lint

Run verification commands:

```bash
uv run mypy app/
uv run ruff check app/
uv run pytest app/tests/
```

## Filter Pipeline Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PRE-FILTERS (O(n) - reduces unary_union input)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Entity count threshold check → Early exit if > 1000 entities             │
│ 2. Edge count estimation        → Early exit if > 5000 estimated edges      │
│ 3. _extract_all_edges() with pre-filters:                                   │
│    ├─ Skip CIRCLE entities (if skip_curved_entities=True)                   │
│    ├─ Skip ARC entities (if skip_curved_entities=True)                      │
│    └─ Skip LINE entities where length < min_line_length                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: POLYGON EXTRACTION (expensive - now with fewer edges)              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Edge snapping (precision fix OR gap bridge)                              │
│ 5. unary_union()  → O(n log n) - FASTER due to fewer edges from pre-filters │
│ 6. polygonize()   → Creates closed polygons                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: POST-FILTERS (validate polygon properties)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 7. Curved lines filter   → Polygons with curved edges (NEW)                 │
│ 8. Side filter           → Polygons with short sides (EXISTING)             │
│ 9. Polygon count check   → Early exit if > 500                              │
│ 10. _calculate_net_areas() → O(n²) - now with fewer polygons                │
│ 11. Area filter          → Polygons below minimum area (EXISTING)           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Recommendations

1. **Default All Pre-Filters Disabled**: Pre-filters are optimization tools for power users dealing with complex drawings. Safe defaults preserve existing behavior.

2. **Order Matters**: Curved lines post-filter should run BEFORE side filter since it's cheaper (no sqrt) and reduces polygon count for subsequent filters.

3. **Logging**: Add debug logs showing pre-filter impact (edges skipped) and post-filter impact (polygons filtered) for troubleshooting.

4. **No Mutual Exclusivity**: Unlike Precision Fix / Gap Bridge, the pre-filters can be used together or independently.

## Next Steps

1. Implement Step 1 (constants.py)
2. Implement Step 2 (types.py)
3. Implement Step 3 (settings.py)
4. Implement Steps 4-6 (geometry.py)
5. Implement Step 7 (extractor.py)
6. Implement Steps 8-9 (main.py)
7. Implement Step 10 (settings_window.py)
8. Implement Step 11 (tests)
9. Run Step 12 verification
10. Manual testing with problematic DXF files
