# Two-Stage Snapping with GUI Controls Implementation Plan

## Executive Summary

This plan details a complete implementation of Two-Stage Snapping with GUI controls for unit selection and gap bridging. The application will auto-detect drawing units from the DXF `$INSUNITS` header, but users can override with manual unit selection (MM, CM, M, IN, FT). Stage 1 (precision normalization) fixes floating-point artifacts automatically, while Stage 2 (gap bridging) is user-configurable with unit-appropriate defaults.

## Table Summary

| Feature | Default | User Override | Purpose |
|---------|---------|---------------|---------|
| Unit Selection | "DXF/DWG" (auto-detect) | MM, CM, M, IN, FT | Determines snap tolerances |
| Stage 1: Precision Fix | Always ON | No | Fix floating-point artifacts |
| Stage 2: Gap Bridge | OFF (0.0) | Toggle + Amount | Bridge intentional design gaps |

| Unit | $INSUNITS | Stage 1 Tolerance | Stage 2 Default |
|------|-----------|-------------------|-----------------|
| Millimeters (MM) | 4 | 1e-6 | 100.0 |
| Centimeters (CM) | 5 | 1e-5 | 10.0 |
| Meters (M) | 6 | 1e-4 | 0.1 |
| Inches (IN) | 1 | 1e-7 | 4.0 |
| Feet (FT) | 2 | 1e-6 | 0.33 |
| Unitless/Auto | 0 | 1e-6 | 100.0 |

## Relevant Files

- **app/main.py:46-455** - GUI application class, widget creation, extraction workflow
- **app/core/geometry.py:515-560** - `_extract_paint_bucket_regions()` where snapping will be applied
- **app/core/geometry.py:829-975** - `_detect_content_zone()` which calls region detection
- **app/core/constants.py:152-156** - Arc flattening config, pattern for tolerance constants
- **app/core/extractor.py:710-1243** - `extract_blocks()` main extraction function
- **app/core/types.py** - Type definitions for new data structures
- **ai_docs/ezdxf-geometry-reference.md** - ezdxf API reference
- **ai_docs/shapely-geometry-reference.md** - Shapely API reference

## In Scope

1. **Unit Detection** - Read `$INSUNITS` header from DXF files to auto-detect drawing units
2. **GUI Unit Selector** - Dropdown with "DXF/DWG" (auto), MM, CM, M, IN, FT options
3. **GUI Gap Bridge Controls** - Checkbox toggle + numeric entry for bridge amount
4. **Stage 1 Implementation** - Always-on precision normalization with unit-appropriate tolerance
5. **Stage 2 Implementation** - Optional gap bridging with user-configurable or default tolerance
6. **Default Gap Amounts** - Unit-appropriate default values when gap bridging is enabled
7. **Constants Module Updates** - New tolerance constants and unit mappings
8. **Tolerance Propagation** - Pass tolerances through extraction and geometry call chains
9. **Unit Tests** - Tests for snapping behavior and unit detection
10. **Logging** - Debug logging for snap operations and tolerance values

## Out of Scope

1. **Per-Block Tolerance** - Single tolerance per drawing, not per-block customization
2. **3D Coordinate Snapping** - Z-axis snapping (2D operations only)
3. **DXF File Modification** - No writing back snapped coordinates to files
4. **Preference Persistence** - Settings reset on each session (no save/load)
5. **Advanced Unit Systems** - Only supporting MM, CM, M, IN, FT (no miles, microns, etc.)

## Implementation Sequence

### Unit 1: Constants Module - Tolerance Definitions (constants.py)

**Purpose:** Add all tolerance constants and unit mappings to the constants module.

**File:** `app/core/constants.py`

**Implementation:**

```python
# =============================================================================
# Drawing Unit Configuration
# =============================================================================

# DXF $INSUNITS value to unit name mapping (subset for GUI)
DXF_INSUNITS_MAP: dict[int, str] = {
    0: "unitless",
    1: "inches",
    2: "feet",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
}

# User-selectable unit options for GUI dropdown
# Key: Display label, Value: $INSUNITS equivalent
UNIT_SELECTION_OPTIONS: dict[str, int] = {
    "DXF/DWG": -1,  # -1 indicates auto-detect from file
    "MM": 4,
    "CM": 5,
    "M": 6,
    "IN": 1,
    "FT": 2,
}

# Stage 1: Unit-aware precision snap tolerance
# Values chosen to fix floating-point artifacts without affecting valid geometry
PRECISION_SNAP_TOLERANCE: dict[int, float] = {
    -1: 1e-6,  # Auto-detect fallback
    0: 1e-6,   # Unitless: assume mm-like
    1: 1e-7,   # Inches: ~2.5nm
    2: 1e-6,   # Feet: ~0.3um
    4: 1e-6,   # Millimeters: ~1nm
    5: 1e-5,   # Centimeters: ~0.1um
    6: 1e-4,   # Meters: ~0.1mm
}

DEFAULT_PRECISION_SNAP_TOLERANCE: float = 1e-6
"""Fallback tolerance when $INSUNITS not specified or unrecognized."""

# Stage 2: Default gap bridge tolerances per unit (when enabled)
# Values represent typical CAD drafting gap sizes in each unit system
DEFAULT_GAP_BRIDGE_TOLERANCE: dict[int, float] = {
    -1: 100.0,  # Auto-detect fallback (mm-like)
    0: 100.0,   # Unitless: assume mm-like
    1: 4.0,     # Inches: ~4 inch gap
    2: 0.33,    # Feet: ~4 inch gap in feet
    4: 100.0,   # Millimeters: ~100mm gap
    5: 10.0,    # Centimeters: ~10cm gap
    6: 0.1,     # Meters: ~100mm gap in meters
}

# Gap bridge input constraints
GAP_BRIDGE_MIN: float = 0.0
GAP_BRIDGE_MAX: float = 10000.0
"""Maximum allowed gap bridge tolerance to prevent unreasonable values."""
```

**Tests required:**
- Verify all unit mappings exist
- Verify tolerance values are within expected ranges
- Verify UNIT_SELECTION_OPTIONS keys match display labels

---

### Unit 2: Extractor - Unit Detection Function (extractor.py)

**Purpose:** Add function to detect drawing units from DXF header.

**File:** `app/core/extractor.py`

**Implementation:**

```python
from .constants import (
    # ... existing imports ...
    DXF_INSUNITS_MAP,
    PRECISION_SNAP_TOLERANCE,
    DEFAULT_PRECISION_SNAP_TOLERANCE,
    DEFAULT_GAP_BRIDGE_TOLERANCE,
)

def _get_drawing_units(doc: Drawing) -> int:
    """
    Extract drawing units from DXF header.

    Reads the $INSUNITS header variable to determine the drawing's
    unit system.

    Args:
        doc: ezdxf Drawing document

    Returns:
        The $INSUNITS integer value (0-6 for supported units).
        Returns 0 (unitless) if header is missing or unrecognized.
    """
    try:
        insunits = doc.header.get("$INSUNITS", 0)
        unit_name = DXF_INSUNITS_MAP.get(insunits, "unknown")
        logger.debug(f"Drawing units: $INSUNITS={insunits} ({unit_name})")
        return insunits
    except (AttributeError, KeyError):
        logger.debug("$INSUNITS not found, using default (unitless)")
        return 0


def get_snap_tolerances(
    detected_units: int,
    override_units: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
) -> tuple[float, float]:
    """
    Calculate snap tolerances based on units and user settings.

    Args:
        detected_units: $INSUNITS value from DXF file
        override_units: User-selected unit override (-1 for auto, or $INSUNITS value)
        gap_bridge_enabled: Whether Stage 2 gap bridging is enabled
        gap_bridge_amount: User-specified gap bridge amount (None = use default)

    Returns:
        Tuple of (precision_tolerance, gap_bridge_tolerance) where:
        - precision_tolerance: Stage 1 tolerance (always > 0)
        - gap_bridge_tolerance: Stage 2 tolerance (0.0 if disabled)
    """
    # Determine effective units
    if override_units is None or override_units == -1:
        effective_units = detected_units
    else:
        effective_units = override_units

    # Stage 1: Precision tolerance (always on)
    precision_tolerance = PRECISION_SNAP_TOLERANCE.get(
        effective_units, DEFAULT_PRECISION_SNAP_TOLERANCE
    )

    # Stage 2: Gap bridge tolerance (user-controlled)
    if gap_bridge_enabled:
        if gap_bridge_amount is not None and gap_bridge_amount > 0:
            gap_tolerance = gap_bridge_amount
        else:
            gap_tolerance = DEFAULT_GAP_BRIDGE_TOLERANCE.get(effective_units, 100.0)
    else:
        gap_tolerance = 0.0

    logger.debug(
        f"Snap tolerances: units={effective_units}, "
        f"precision={precision_tolerance}, gap_bridge={gap_tolerance}"
    )
    return (precision_tolerance, gap_tolerance)
```

**Tests required:**
- Test detection of various $INSUNITS values
- Test fallback for missing $INSUNITS header
- Test tolerance calculation with/without overrides
- Test gap bridge default selection

---

### Unit 3: Geometry - Stage 1 & 2 Snapping (geometry.py)

**Purpose:** Modify `_extract_paint_bucket_regions()` to apply precision snapping and optional gap bridging.

**File:** `app/core/geometry.py`

**Implementation:**

```python
from shapely.ops import polygonize, snap, unary_union

def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
) -> list[Polygon]:
    """
    Extract all visual regions using paint-bucket algorithm.

    Combines all edges (LWPOLYLINE + LINE + CIRCLE + ARC + HATCH) into a
    unified edge set, applies precision snapping to fix floating-point
    artifacts, optionally applies gap bridging, splits at intersections
    using unary_union, and finds all closed regions using polygonize.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading.Event to signal abort request
        precision_tolerance: Stage 1 snap tolerance for fixing precision errors.
            Should be derived from drawing units. Default 1e-6.
        gap_bridge_tolerance: Stage 2 tolerance for bridging intentional gaps.
            Default 0.0 (disabled). Set > 0 to bridge large gaps.

    Returns:
        List of Polygon objects (coordinate tuples) representing all visual regions.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    edges = _extract_all_edges(block_def)

    if not edges:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Region detection aborted")

    # Merge and split at all intersections
    merged = unary_union(edges)
    if merged.is_empty:
        return []

    # Stage 1: Always apply precision snapping to fix floating-point artifacts
    if precision_tolerance > 0:
        merged = snap(merged, merged, precision_tolerance)
        logger.debug(f"Applied Stage 1 precision snap: tolerance={precision_tolerance}")

    # Stage 2: Optional gap bridging (user-controlled)
    if gap_bridge_tolerance > 0:
        merged = snap(merged, merged, gap_bridge_tolerance)
        logger.debug(f"Applied Stage 2 gap bridge: tolerance={gap_bridge_tolerance}")

    line_segments = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    polygons = list(polygonize(line_segments))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} paint-bucket regions")
    return result
```

**Tests required:**
- Test Stage 1 fixes nanometer-scale gaps
- Test Stage 2 bridges larger gaps when enabled
- Test Stage 2 has no effect when tolerance is 0.0
- Test normal drawings are unaffected by Stage 1

---

### Unit 4: Geometry - Update _detect_content_zone Signature (geometry.py)

**Purpose:** Propagate tolerance parameters through the content zone detection call chain.

**File:** `app/core/geometry.py`

**Implementation:**

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
) -> ContentZoneData:
    """
    Detect content zone and calculate trim values.

    ... existing docstring ...

    Args:
        block_def: ezdxf block definition object
        block_bbox: Block bounding box as (min_x, min_y, max_x, max_y)
        abort_event: Optional threading.Event to signal abort request
        precision_tolerance: Stage 1 snap tolerance derived from drawing units.
        gap_bridge_tolerance: Stage 2 tolerance for bridging gaps. Default 0.0.

    Returns:
        ContentZoneData with detected trim values.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    block_name = block_def.name

    # Count edges for threshold check
    edge_count = len(_extract_all_edges(block_def))
    if edge_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping region detection: "
            f"{edge_count} edges exceeds threshold {LINE_SEGMENT_THRESHOLD}"
        )
        return ContentZoneData(
            # ... existing empty return ...
        )

    # Use paint-bucket algorithm with snapping tolerances
    all_shapes = _extract_paint_bucket_regions(
        block_def, abort_event, precision_tolerance, gap_bridge_tolerance
    )

    # ... rest of function unchanged ...
```

**Tests required:**
- Verify tolerance parameters are passed through correctly
- Integration test with different tolerance values

---

### Unit 5: Extractor - Pass Tolerances Through extract_blocks (extractor.py)

**Purpose:** Modify `extract_blocks()` to accept tolerance parameters and pass them through.

**File:** `app/core/extractor.py`

**Implementation:**

```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DXF file.

    ... existing docstring with updated Args ...

    Args:
        file_path: Path to the DXF file to process
        abort_event: Optional threading.Event to signal abort request.
        unit_override: User-selected unit override. -1 for auto-detect,
            or $INSUNITS value (1=IN, 2=FT, 4=MM, 5=CM, 6=M). None = auto.
        gap_bridge_enabled: Enable Stage 2 gap bridging.
        gap_bridge_amount: Custom gap bridge tolerance. None = use default for unit.

    Returns:
        ExtractionResult TypedDict containing all analysis data.
    """
    # ... existing validation code ...

    try:
        # ... existing abort check and file loading ...
        doc = ezdxf.readfile(file_path)

        # Detect drawing units from file
        detected_units = _get_drawing_units(doc)

        # Calculate snap tolerances
        precision_tolerance, gap_bridge_tolerance = get_snap_tolerances(
            detected_units,
            unit_override,
            gap_bridge_enabled,
            gap_bridge_amount,
        )

        logger.info(
            f"Using tolerances: precision={precision_tolerance}, "
            f"gap_bridge={gap_bridge_tolerance} "
            f"(units={'auto' if unit_override in (None, -1) else unit_override})"
        )

        # ... later when processing blocks ...

        # Detect content zone for trim value suggestions
        content_zone_result = _detect_content_zone(
            block_def,
            bbox,
            abort_event,
            precision_tolerance,
            gap_bridge_tolerance,
        )
```

**Tests required:**
- Test extraction with various unit_override values
- Test extraction with gap_bridge enabled/disabled
- Test custom gap_bridge_amount is used when provided

---

### Unit 6: GUI - Unit Selection Dropdown (main.py)

**Purpose:** Add unit selection dropdown to the GUI.

**File:** `app/main.py`

**Implementation:**

```python
from core.constants import (
    # ... existing imports ...
    UNIT_SELECTION_OPTIONS,
)

class DXFExtractorApp(ctk.CTk):
    def __init__(self) -> None:
        # ... existing init ...

        # Unit selection state
        self.unit_selection_var = ctk.StringVar(value="DXF/DWG")

        # ... rest of init ...

    def _create_widgets(self) -> None:
        # ... existing widgets up to button_frame ...

        # Options frame for unit selection and gap bridge
        options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        options_frame.pack(pady=(0, 15))

        # Unit selection label and dropdown
        unit_label = ctk.CTkLabel(
            options_frame,
            text="Units:",
            font=ctk.CTkFont(size=12),
        )
        unit_label.pack(side="left", padx=(0, 5))

        self.unit_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=list(UNIT_SELECTION_OPTIONS.keys()),
            variable=self.unit_selection_var,
            width=100,
            command=self._on_unit_change,
        )
        self.unit_dropdown.pack(side="left", padx=(0, 20))

        # ... gap bridge widgets will be added in Unit 7 ...

    def _on_unit_change(self, value: str) -> None:
        """Handle unit dropdown selection change."""
        self.logger.debug(f"Unit selection changed to: {value}")
        # Update gap bridge default if gap bridging is enabled
        if hasattr(self, 'gap_bridge_var') and self.gap_bridge_var.get():
            self._update_gap_bridge_default()

    def _get_selected_unit_override(self) -> int | None:
        """Get the $INSUNITS value for selected unit, or None for auto."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        return None if insunits == -1 else insunits
```

**Tests required:**
- GUI dropdown displays all unit options
- Selection change updates internal state
- _get_selected_unit_override returns correct values

---

### Unit 7: GUI - Gap Bridge Controls (main.py)

**Purpose:** Add gap bridge toggle checkbox and amount entry.

**File:** `app/main.py`

**Implementation:**

```python
from core.constants import (
    # ... existing imports ...
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    GAP_BRIDGE_MIN,
    GAP_BRIDGE_MAX,
)

class DXFExtractorApp(ctk.CTk):
    def __init__(self) -> None:
        # ... existing init ...

        # Gap bridge state
        self.gap_bridge_var = ctk.BooleanVar(value=False)
        self.gap_bridge_amount_var = ctk.StringVar(value="100.0")

        # ... rest of init ...

    def _create_widgets(self) -> None:
        # ... in options_frame after unit dropdown ...

        # Gap bridge checkbox
        self.gap_bridge_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Gap Bridge:",
            variable=self.gap_bridge_var,
            command=self._on_gap_bridge_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.gap_bridge_checkbox.pack(side="left", padx=(0, 5))

        # Gap bridge amount entry
        self.gap_bridge_entry = ctk.CTkEntry(
            options_frame,
            width=80,
            textvariable=self.gap_bridge_amount_var,
            state="disabled",  # Disabled until checkbox is checked
        )
        self.gap_bridge_entry.pack(side="left")

    def _on_gap_bridge_toggle(self) -> None:
        """Handle gap bridge checkbox toggle."""
        enabled = self.gap_bridge_var.get()
        self.logger.debug(f"Gap bridge toggled: {enabled}")

        if enabled:
            self.gap_bridge_entry.configure(state="normal")
            self._update_gap_bridge_default()
        else:
            self.gap_bridge_entry.configure(state="disabled")

    def _update_gap_bridge_default(self) -> None:
        """Update gap bridge amount to default for selected unit."""
        selection = self.unit_selection_var.get()
        insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
        # Use detected units fallback if auto
        effective_units = insunits if insunits != -1 else 4  # Default to mm
        default_amount = DEFAULT_GAP_BRIDGE_TOLERANCE.get(effective_units, 100.0)
        self.gap_bridge_amount_var.set(str(default_amount))
        self.logger.debug(f"Gap bridge default updated to {default_amount}")

    def _get_gap_bridge_amount(self) -> float | None:
        """Get validated gap bridge amount, or None if invalid/disabled."""
        if not self.gap_bridge_var.get():
            return None
        try:
            amount = float(self.gap_bridge_amount_var.get())
            if GAP_BRIDGE_MIN <= amount <= GAP_BRIDGE_MAX:
                return amount
            else:
                self.logger.warning(f"Gap bridge amount {amount} out of range")
                return None
        except ValueError:
            self.logger.warning("Invalid gap bridge amount")
            return None
```

**Tests required:**
- Checkbox enables/disables entry field
- Default amount updates when unit changes
- Validation rejects invalid amounts
- Entry accepts valid numeric input

---

### Unit 8: GUI - Connect Controls to Extraction (main.py)

**Purpose:** Pass GUI settings to the extraction process.

**File:** `app/main.py`

**Implementation:**

```python
def _extraction_worker(self) -> None:
    """Background worker thread for extraction process."""
    try:
        # ... existing validation and setup ...

        # Get user settings
        unit_override = self._get_selected_unit_override()
        gap_bridge_enabled = self.gap_bridge_var.get()
        gap_bridge_amount = self._get_gap_bridge_amount()

        self.logger.info(
            f"Extraction settings: unit_override={unit_override}, "
            f"gap_bridge_enabled={gap_bridge_enabled}, "
            f"gap_bridge_amount={gap_bridge_amount}"
        )

        # Step 2: Extract comprehensive data
        self._update_progress(0.5, "Analyzing CAD file...")

        extraction_result = extract_blocks(
            self.selected_file_path,
            self.abort_event,
            unit_override=unit_override,
            gap_bridge_enabled=gap_bridge_enabled,
            gap_bridge_amount=gap_bridge_amount,
        )

        # ... rest of function unchanged ...
```

**Tests required:**
- Settings are correctly passed to extract_blocks
- Extraction uses correct tolerances based on settings

---

### Unit 9: Unit Tests - Snapping Behavior (tests/core/test_geometry.py)

**Purpose:** Add comprehensive tests for the two-stage snapping behavior.

**File:** `app/tests/core/test_geometry.py`

**Implementation:**

```python
import pytest
from shapely.geometry import LineString
from shapely.ops import polygonize, snap, unary_union

from app.core.constants import (
    PRECISION_SNAP_TOLERANCE,
    DEFAULT_GAP_BRIDGE_TOLERANCE,
)


class TestPrecisionSnapping:
    """Tests for Stage 1 precision snapping behavior."""

    def test_stage1_fixes_nanometer_gap(self):
        """Stage 1 should fix floating-point precision gaps."""
        # Create edges with ~3.7nm gap (like SPAR Gulv)
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            # Horizontal line with precision error (~3.7nm short)
            LineString([(0, 5), (9.9999999962746, 5)]),
        ]

        # Without snapping: only 1 polygon (gap prevents split)
        merged_no_snap = unary_union(edges)
        polygons_no_snap = list(polygonize(list(merged_no_snap.geoms)))
        assert len(polygons_no_snap) == 1

        # With Stage 1 snapping: 2 polygons (gap fixed)
        merged = unary_union(edges)
        merged = snap(merged, merged, 1e-6)
        polygons_with_snap = list(polygonize(list(merged.geoms)))
        assert len(polygons_with_snap) == 2

    def test_stage1_no_effect_on_clean_geometry(self):
        """Stage 1 should not affect geometry without precision errors."""
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            LineString([(0, 5), (10, 5)]),  # Clean line, no gap
        ]

        merged_no_snap = unary_union(edges)
        polygons_no_snap = list(polygonize(list(merged_no_snap.geoms)))

        merged = unary_union(edges)
        merged = snap(merged, merged, 1e-6)
        polygons_with_snap = list(polygonize(list(merged.geoms)))

        # Same result with or without snapping
        assert len(polygons_no_snap) == len(polygons_with_snap) == 2


class TestGapBridging:
    """Tests for Stage 2 gap bridging behavior."""

    def test_stage2_disabled_by_default(self):
        """Gap bridge with tolerance 0.0 should have no effect."""
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            LineString([(0, 5), (9, 5)]),  # 1 unit gap
        ]

        merged = unary_union(edges)
        merged = snap(merged, merged, 1e-6)  # Stage 1 only
        polygons = list(polygonize(list(merged.geoms)))

        # Gap is too large for Stage 1 - still 1 polygon
        assert len(polygons) == 1

    def test_stage2_bridges_large_gaps(self):
        """Stage 2 should bridge intentional design gaps when enabled."""
        edges = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (10, 10)]),
            LineString([(10, 10), (0, 10)]),
            LineString([(0, 10), (0, 0)]),
            LineString([(0, 5), (9, 5)]),  # 1 unit gap
        ]

        merged = unary_union(edges)
        merged = snap(merged, merged, 1e-6)   # Stage 1
        merged = snap(merged, merged, 2.0)    # Stage 2 with 2.0 tolerance
        polygons = list(polygonize(list(merged.geoms)))

        # Gap bridged - now 2 polygons
        assert len(polygons) == 2


class TestUnitToleranceMapping:
    """Tests for unit-to-tolerance mapping."""

    def test_mm_tolerance(self):
        """MM drawings should use 1e-6 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[4] == 1e-6

    def test_meter_tolerance(self):
        """Meter drawings should use 1e-4 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[6] == 1e-4

    def test_inch_tolerance(self):
        """Inch drawings should use 1e-7 precision tolerance."""
        assert PRECISION_SNAP_TOLERANCE[1] == 1e-7

    def test_default_gap_amounts(self):
        """Default gap amounts should be appropriate for each unit."""
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[4] == 100.0   # MM: 100mm
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[6] == 0.1     # M: 0.1m = 100mm
        assert DEFAULT_GAP_BRIDGE_TOLERANCE[1] == 4.0     # IN: 4 inches
```

**Tests required:**
- All tests in TestPrecisionSnapping pass
- All tests in TestGapBridging pass
- All tests in TestUnitToleranceMapping pass

---

### Unit 10: Unit Tests - Extractor Functions (tests/core/extractor/)

**Purpose:** Add tests for unit detection and tolerance calculation functions.

**File:** `app/tests/core/extractor/test_extractor_units.py`

**Implementation:**

```python
import pytest
from unittest.mock import MagicMock, patch

from app.core.extractor import _get_drawing_units, get_snap_tolerances


class TestGetDrawingUnits:
    """Tests for _get_drawing_units function."""

    def test_detects_mm_units(self):
        """Should detect millimeter units from $INSUNITS=4."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 4

        result = _get_drawing_units(mock_doc)
        assert result == 4

    def test_detects_inch_units(self):
        """Should detect inch units from $INSUNITS=1."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 1

        result = _get_drawing_units(mock_doc)
        assert result == 1

    def test_missing_insunits_returns_zero(self):
        """Should return 0 when $INSUNITS is missing."""
        mock_doc = MagicMock()
        mock_doc.header.get.side_effect = KeyError("$INSUNITS")

        result = _get_drawing_units(mock_doc)
        assert result == 0


class TestGetSnapTolerances:
    """Tests for get_snap_tolerances function."""

    def test_auto_detect_mm(self):
        """Auto-detect with MM units should return MM tolerances."""
        precision, gap = get_snap_tolerances(
            detected_units=4,
            override_units=None,
            gap_bridge_enabled=False,
        )
        assert precision == 1e-6
        assert gap == 0.0

    def test_override_to_meters(self):
        """Override to meters should use meter tolerances."""
        precision, gap = get_snap_tolerances(
            detected_units=4,  # File says MM
            override_units=6,  # User says M
            gap_bridge_enabled=False,
        )
        assert precision == 1e-4  # Meter tolerance

    def test_gap_bridge_enabled_uses_default(self):
        """Enabled gap bridge with no amount uses unit default."""
        precision, gap = get_snap_tolerances(
            detected_units=4,
            override_units=None,
            gap_bridge_enabled=True,
            gap_bridge_amount=None,
        )
        assert gap == 100.0  # MM default

    def test_gap_bridge_custom_amount(self):
        """Custom gap bridge amount overrides default."""
        precision, gap = get_snap_tolerances(
            detected_units=4,
            override_units=None,
            gap_bridge_enabled=True,
            gap_bridge_amount=50.0,
        )
        assert gap == 50.0
```

---

## Dependency Graph

```
Unit 1: Constants (tolerance definitions)
    └── Unit 2: Extractor (unit detection functions)
        └── Unit 3: Geometry (snapping implementation)
            └── Unit 4: Geometry (content zone signature update)
                └── Unit 5: Extractor (pass tolerances through extract_blocks)
                    ├── Unit 6: GUI (unit selection dropdown)
                    │   └── Unit 7: GUI (gap bridge controls)
                    │       └── Unit 8: GUI (connect to extraction)
                    └── Unit 9: Unit Tests (snapping behavior)
                        └── Unit 10: Unit Tests (extractor functions)
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| snap() creates invalid geometry | Low | Medium | Validate polygons after snap, log warnings |
| Wrong tolerance for unit system | Medium | Low | GUI shows selected unit, comprehensive tests |
| Performance degradation | Low | Low | snap() is O(n), minimal overhead |
| User enters invalid gap amount | Medium | Low | Input validation with min/max bounds |
| GUI layout issues with new controls | Medium | Low | Test on different window sizes |

## Validation Checklist

- [ ] Unit 1: All tolerance constants defined and exported
- [ ] Unit 2: `_get_drawing_units()` returns correct values for all supported units
- [ ] Unit 2: `get_snap_tolerances()` calculates correct tolerances
- [ ] Unit 3: Stage 1 snap fixes SPAR Gulv 5→7 polygon issue
- [ ] Unit 3: Stage 2 snap bridges large gaps when enabled
- [ ] Unit 4: Tolerance parameters propagate to region detection
- [ ] Unit 5: `extract_blocks()` accepts and uses new parameters
- [ ] Unit 6: Unit dropdown displays all options correctly
- [ ] Unit 6: Unit selection change is logged
- [ ] Unit 7: Gap bridge checkbox enables/disables entry
- [ ] Unit 7: Default gap amount updates on unit change
- [ ] Unit 7: Invalid amounts are rejected
- [ ] Unit 8: GUI settings are passed to extract_blocks
- [ ] Unit 9: All snapping unit tests pass
- [ ] Unit 10: All extractor unit tests pass
- [ ] Performance: No significant slowdown on large drawings
- [ ] Regression: Existing test suite passes without modification
