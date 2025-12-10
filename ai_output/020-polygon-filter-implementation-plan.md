# Implementation Plan: Polygon Area and Shortest Side Filtering for Content Zone

## Executive Summary

This plan implements the recommended approaches from `ai_output/019-polygon-area-shortest-side-calculation.md` to add polygon surface area and shortest straight side calculations, plus two new GUI filter options (Minimum Area Filter and Minimum Side Filter) that filter out small polygons before calculating the block content zone bounding box.

## Table Summary

| Step | Component | Description | Files | Complexity |
|------|-----------|-------------|-------|------------|
| 1 | Constants | Add filter constants and defaults | `constants.py` | Low |
| 2 | Types | Add new TypedDicts for filter data | `types.py` | Low |
| 3 | Geometry Core | Implement area and shortest side functions | `geometry.py` | Medium |
| 4 | Geometry Filter | Add polygon filtering logic | `geometry.py` | Medium |
| 5 | Extractor | Update signatures and pass filter params | `extractor.py` | Medium |
| 6 | GUI Layout | Add two new filter rows | `main.py` | Medium |
| 7 | GUI Handlers | Add toggle/getter methods | `main.py` | Low |
| 8 | Unit Tests | Test new calculation functions | `test_geometry.py` | Medium |
| 9 | Integration Tests | Test end-to-end filter flow | `test_extractor_*.py` | Medium |
| 10 | Validation | Type check, lint, full test suite | All | Low |

## Relevant Files

- **app/core/constants.py** - Add filter constants (defaults, min/max ranges, unit-specific defaults)
- **app/core/types.py** - Add `PolygonMetrics` TypedDict for area/side data
- **app/core/geometry.py** - Add `calculate_polygon_area()`, `calculate_shortest_straight_side()`, update `_detect_content_zone()` with filtering
- **app/core/extractor.py** - Update `extract_blocks()` and `get_snap_tolerances()` signatures with filter parameters
- **app/main.py** - Add GUI rows for Min Area Filter and Min Side Filter following Precision Fix pattern
- **app/tests/core/test_geometry.py** - Unit tests for new geometry functions
- **app/tests/core/extractor/test_extractor_*.py** - Integration tests for filter parameters
- **ai_docs/019-polygon-area-shortest-side-calculation.md** - Source recommendations (read-only reference)
- **ai_docs/ezdxf-geometry-reference.md** - ezdxf geometry reference (read-only)
- **ai_docs/shapely-geometry-reference.md** - Shapely geometry reference (read-only)

## In Scope

1. **New geometry functions** in `geometry.py`:
   - `calculate_polygon_area(polygon, unit_code, target_unit)` - Calculate polygon surface area with unit conversion
   - `calculate_shortest_straight_side(polygon, angle_tolerance)` - Calculate shortest merged straight side length

2. **New GUI filter controls** in `main.py` (two new rows):
   - **Min Area Filter row**: Checkbox + Amount entry field (filter polygons by minimum surface area)
   - **Min Side Filter row**: Checkbox + Amount entry field (filter polygons by minimum shortest side length)
   - Follow exact same pattern as Precision Fix and Gap Bridge rows

3. **Updated content zone detection**:
   - After extracting paint-bucket regions, filter out polygons where:
     - Area < min_area_filter (if enabled)
     - Shortest side < min_side_filter (if enabled)
   - Calculate content zone bounding box from remaining filtered polygons

4. **Parameter flow**:
   - GUI entry fields -> getter methods -> `extract_blocks()` -> `_detect_content_zone()` -> filtering

5. **Constants and defaults**:
   - Unit-specific default filter values
   - Min/max range validation

6. **Unit tests** for new functions and integration tests for parameter flow

## Out of Scope

1. **Excel output columns** for area/side data per polygon - future enhancement
2. **Per-polygon metrics storage** in `ExtractionResult` - not needed for filtering use case
3. **Unit conversion in GUI** - filter values are in DXF drawing units (same as Precision Fix)
4. **Visual preview** of filtered polygons - not part of current GUI design
5. **Reporting which polygons were filtered** - silent filtering for content zone calculation

## Implementation Steps (Sequenced for Full Completion)

---

### Step 1: Add Constants for Polygon Filters

**File:** `app/core/constants.py`

Add constants for the two new filter options following the pattern of existing gap bridge and precision fix constants.

```python
# Minimum Area Filter constants
DEFAULT_MIN_AREA_FILTER: dict[int, float] = {
    0: 100.0,      # Unitless: assume mm-equivalent
    1: 0.01,       # Inches: 0.01 sq inches
    2: 0.001,      # Feet: 0.001 sq feet
    4: 100.0,      # Millimeters: 100 sq mm
    5: 1.0,        # Centimeters: 1 sq cm
    6: 0.0001,     # Meters: 0.0001 sq m (100 sq mm)
}
"""Default minimum area filter by unit code.
Polygons with area less than this value are filtered out of content zone calculation."""

MIN_AREA_FILTER_MIN: float = 0.0
MIN_AREA_FILTER_MAX: float = 1000000.0

# Minimum Side Filter constants
DEFAULT_MIN_SIDE_FILTER: dict[int, float] = {
    0: 10.0,       # Unitless: assume mm-equivalent
    1: 0.5,        # Inches: 0.5 inches
    2: 0.05,       # Feet: 0.05 feet (~0.6 inches)
    4: 10.0,       # Millimeters: 10mm
    5: 1.0,        # Centimeters: 1cm
    6: 0.01,       # Meters: 0.01m (10mm)
}
"""Default minimum side filter by unit code.
Polygons with shortest straight side less than this value are filtered out."""

MIN_SIDE_FILTER_MIN: float = 0.0
MIN_SIDE_FILTER_MAX: float = 100000.0
```

---

### Step 2: Add Types for Polygon Metrics

**File:** `app/core/types.py`

Add TypedDict for polygon metrics.

```python
class PolygonMetrics(TypedDict):
    """
    Metrics calculated for a single polygon after precision fix.

    Attributes:
        area_raw: Area in DXF drawing units squared
        shortest_side: Length of shortest straight side in DXF units
        perimeter: Total perimeter length in DXF units
    """
    area_raw: float
    shortest_side: float
    perimeter: float
```

---

### Step 3: Implement Core Geometry Functions

**File:** `app/core/geometry.py`

Add the two core calculation functions as recommended in the analysis document.

**3a. Add `calculate_polygon_area()` function:**

```python
def calculate_polygon_area(polygon: Polygon) -> float:
    """
    Calculate the surface area of a polygon.

    Args:
        polygon: List of (x, y) vertices from _extract_paint_bucket_regions()

    Returns:
        Area in DXF drawing units squared (always positive)
    """
    if len(polygon) < 3:
        return 0.0
    shapely_poly = ShapelyPolygon(polygon)
    return abs(shapely_poly.area)
```

**3b. Add `calculate_shortest_straight_side()` function:**

```python
import math

def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> float:
    """
    Calculate the shortest straight side of a polygon.

    Merges consecutive collinear edges into single sides before
    finding the minimum. Handles LINE1 (Part1) + LINE1 (Part2)
    being counted as one side.

    Args:
        polygon: List of (x, y) vertices (closed polygon, no repeat of first point)
        angle_tolerance: Maximum angle deviation to consider edges collinear (degrees)

    Returns:
        Length of shortest straight side in DXF drawing units
    """
    if len(polygon) < 3:
        return 0.0

    # Close the polygon by appending first vertex
    vertices = polygon + [polygon[0]]

    def edge_angle(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate angle of edge in degrees (0-180 range)."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        return angle % 180

    def edge_length(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def angles_collinear(a1: float, a2: float, tolerance: float) -> bool:
        """Check if two angles are within tolerance (handles wraparound)."""
        diff = abs(a1 - a2)
        return diff <= tolerance or abs(diff - 180) <= tolerance

    # Build list of merged straight sides
    straight_sides: list[float] = []

    i = 0
    while i < len(vertices) - 1:
        # Start a new side
        side_start = vertices[i]
        current_angle = edge_angle(vertices[i], vertices[i + 1])

        # Extend side while consecutive edges are collinear
        j = i + 1
        while j < len(vertices) - 1:
            next_angle = edge_angle(vertices[j], vertices[j + 1])
            if angles_collinear(current_angle, next_angle, angle_tolerance):
                j += 1
            else:
                break

        # Calculate total length of merged side
        side_end = vertices[j]
        side_length = edge_length(side_start, side_end)

        if side_length > 1e-9:  # Ignore degenerate edges
            straight_sides.append(side_length)

        i = j

    return min(straight_sides) if straight_sides else 0.0
```

---

### Step 4: Add Polygon Filtering to Content Zone Detection

**File:** `app/core/geometry.py`

Update `_detect_content_zone()` signature and implementation to accept and apply filter parameters.

**4a. Update function signature:**

```python
def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,      # NEW
    min_side_filter: float = 0.0,      # NEW
) -> ContentZoneData:
```

**4b. Add filtering logic after polygon extraction:**

After the line `all_shapes = _extract_paint_bucket_regions(...)`, add filtering:

```python
# Filter polygons by area and shortest side if filters are enabled
if min_area_filter > 0 or min_side_filter > 0:
    filtered_shapes: list[Polygon] = []
    for shape in all_shapes:
        # Check area filter
        if min_area_filter > 0:
            area = calculate_polygon_area(shape)
            if area < min_area_filter:
                continue
        # Check side filter
        if min_side_filter > 0:
            shortest_side = calculate_shortest_straight_side(shape)
            if shortest_side < min_side_filter:
                continue
        filtered_shapes.append(shape)

    logger.debug(
        f"[{block_name}] Filtered {len(all_shapes)} -> {len(filtered_shapes)} polygons "
        f"(min_area={min_area_filter}, min_side={min_side_filter})"
    )
    all_shapes = filtered_shapes
```

---

### Step 5: Update Extractor to Pass Filter Parameters

**File:** `app/core/extractor.py`

**5a. Update `extract_blocks()` signature:**

```python
def extract_blocks(
    file_path: str,
    abort_event: threading.Event | None = None,
    unit_override: int | None = None,
    gap_bridge_enabled: bool = False,
    gap_bridge_amount: float | None = None,
    precision_fix_enabled: bool = True,
    precision_fix_amount: float | None = None,
    min_area_filter_enabled: bool = False,     # NEW
    min_area_filter_amount: float | None = None,  # NEW
    min_side_filter_enabled: bool = False,     # NEW
    min_side_filter_amount: float | None = None,  # NEW
) -> ExtractionResult:
```

**5b. Add helper function to calculate filter values:**

```python
def get_filter_values(
    detected_units: int,
    override_units: int | None,
    min_area_enabled: bool,
    min_area_amount: float | None,
    min_side_enabled: bool,
    min_side_amount: float | None,
) -> tuple[float, float]:
    """Calculate min area and min side filter values based on settings."""
    effective_units = override_units if override_units not in (None, -1) else detected_units

    # Min area filter
    if not min_area_enabled:
        min_area = 0.0
    elif min_area_amount is not None and min_area_amount > 0:
        min_area = min_area_amount
    else:
        min_area = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)

    # Min side filter
    if not min_side_enabled:
        min_side = 0.0
    elif min_side_amount is not None and min_side_amount > 0:
        min_side = min_side_amount
    else:
        min_side = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)

    return (min_area, min_side)
```

**5c. Update `_detect_content_zone()` call inside `extract_blocks()`:**

```python
min_area, min_side = get_filter_values(
    detected_units,
    unit_override,
    min_area_filter_enabled,
    min_area_filter_amount,
    min_side_filter_enabled,
    min_side_filter_amount,
)

content_zone_result = _detect_content_zone(
    block_def,
    bbox,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
    min_area,      # NEW
    min_side,      # NEW
)
```

---

### Step 6: Add GUI Filter Rows

**File:** `app/main.py`

Add two new rows following the exact pattern of Precision Fix and Gap Bridge rows.

**6a. Add instance variables in `__init__`:**

```python
# Min Area Filter settings
self.min_area_filter_var = ctk.BooleanVar(value=False)
self.min_area_filter_amount_var = ctk.StringVar(value="100.0")

# Min Side Filter settings
self.min_side_filter_var = ctk.BooleanVar(value=False)
self.min_side_filter_amount_var = ctk.StringVar(value="10.0")
```

**6b. Add third separator and Min Area Filter row after Gap Bridge section in `_create_widgets()`:**

```python
# Third separator
separator3 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator3.pack(fill="x", pady=5)

# Min Area Filter row frame
min_area_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
min_area_frame.pack(pady=(5, 10))

# Min area filter checkbox
self.min_area_filter_checkbox = ctk.CTkCheckBox(
    min_area_frame,
    text="Min Area Filter",
    variable=self.min_area_filter_var,
    command=self._on_min_area_filter_toggle,
    font=ctk.CTkFont(size=12),
)
self.min_area_filter_checkbox.pack(side="left", padx=(0, 10))

# Min area filter amount label
min_area_amount_label = ctk.CTkLabel(
    min_area_frame,
    text="Amount:",
    font=ctk.CTkFont(size=12),
)
min_area_amount_label.pack(side="left", padx=(0, 5))

# Min area filter amount entry
self.min_area_filter_entry = ctk.CTkEntry(
    min_area_frame,
    width=80,
    textvariable=self.min_area_filter_amount_var,
    state="disabled",
)
self.min_area_filter_entry.pack(side="left")
```

**6c. Add fourth separator and Min Side Filter row:**

```python
# Fourth separator
separator4 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
separator4.pack(fill="x", pady=5)

# Min Side Filter row frame
min_side_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
min_side_frame.pack(pady=(5, 10))

# Min side filter checkbox
self.min_side_filter_checkbox = ctk.CTkCheckBox(
    min_side_frame,
    text="Min Side Filter",
    variable=self.min_side_filter_var,
    command=self._on_min_side_filter_toggle,
    font=ctk.CTkFont(size=12),
)
self.min_side_filter_checkbox.pack(side="left", padx=(0, 10))

# Min side filter amount label
min_side_amount_label = ctk.CTkLabel(
    min_side_frame,
    text="Amount:",
    font=ctk.CTkFont(size=12),
)
min_side_amount_label.pack(side="left", padx=(0, 5))

# Min side filter amount entry
self.min_side_filter_entry = ctk.CTkEntry(
    min_side_frame,
    width=80,
    textvariable=self.min_side_filter_amount_var,
    state="disabled",
)
self.min_side_filter_entry.pack(side="left")
```

---

### Step 7: Add GUI Handler Methods

**File:** `app/main.py`

**7a. Add toggle handlers:**

```python
def _on_min_area_filter_toggle(self) -> None:
    """Handle min area filter checkbox toggle."""
    enabled = self.min_area_filter_var.get()
    self.logger.debug(f"Min area filter toggled: {enabled}")

    if enabled:
        self.min_area_filter_entry.configure(state="normal")
        self._update_min_area_filter_default()
    else:
        self.min_area_filter_entry.configure(state="disabled")

def _on_min_side_filter_toggle(self) -> None:
    """Handle min side filter checkbox toggle."""
    enabled = self.min_side_filter_var.get()
    self.logger.debug(f"Min side filter toggled: {enabled}")

    if enabled:
        self.min_side_filter_entry.configure(state="normal")
        self._update_min_side_filter_default()
    else:
        self.min_side_filter_entry.configure(state="disabled")
```

**7b. Add default update methods:**

```python
def _update_min_area_filter_default(self) -> None:
    """Update min area filter amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)
    self.min_area_filter_amount_var.set(str(default_amount))
    self.logger.debug(f"Min area filter default updated to {default_amount}")

def _update_min_side_filter_default(self) -> None:
    """Update min side filter amount to default for selected unit."""
    selection = self.unit_selection_var.get()
    insunits = UNIT_SELECTION_OPTIONS.get(selection, -1)
    effective_units = insunits if insunits != -1 else 4  # Default to mm
    default_amount = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)
    self.min_side_filter_amount_var.set(str(default_amount))
    self.logger.debug(f"Min side filter default updated to {default_amount}")
```

**7c. Add getter methods:**

```python
def _get_min_area_filter_amount(self) -> float | None:
    """Get validated min area filter amount, or None if invalid/disabled."""
    if not self.min_area_filter_var.get():
        return None
    try:
        amount = float(self.min_area_filter_amount_var.get())
        if MIN_AREA_FILTER_MIN <= amount <= MIN_AREA_FILTER_MAX:
            return amount
        else:
            self.logger.warning(f"Min area filter amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid min area filter amount")
        return None

def _get_min_side_filter_amount(self) -> float | None:
    """Get validated min side filter amount, or None if invalid/disabled."""
    if not self.min_side_filter_var.get():
        return None
    try:
        amount = float(self.min_side_filter_amount_var.get())
        if MIN_SIDE_FILTER_MIN <= amount <= MIN_SIDE_FILTER_MAX:
            return amount
        else:
            self.logger.warning(f"Min side filter amount {amount} out of range")
            return None
    except ValueError:
        self.logger.warning("Invalid min side filter amount")
        return None
```

**7d. Update `_on_unit_change()` to update filter defaults:**

```python
def _on_unit_change(self, value: str) -> None:
    """Handle unit dropdown selection change."""
    self.logger.debug(f"Unit selection changed to: {value}")
    if self.precision_fix_var.get():
        self._update_precision_fix_default()
    if self.gap_bridge_var.get():
        self._update_gap_bridge_default()
    if self.min_area_filter_var.get():  # NEW
        self._update_min_area_filter_default()
    if self.min_side_filter_var.get():  # NEW
        self._update_min_side_filter_default()
```

**7e. Update `_extraction_worker()` to pass filter parameters:**

```python
# Get filter settings
min_area_filter_enabled = self.min_area_filter_var.get()
min_area_filter_amount = self._get_min_area_filter_amount()
min_side_filter_enabled = self.min_side_filter_var.get()
min_side_filter_amount = self._get_min_side_filter_amount()

extraction_result = extract_blocks(
    self.selected_file_path,
    self.abort_event,
    unit_override=unit_override,
    gap_bridge_enabled=gap_bridge_enabled,
    gap_bridge_amount=gap_bridge_amount,
    precision_fix_enabled=precision_fix_enabled,
    precision_fix_amount=precision_fix_amount,
    min_area_filter_enabled=min_area_filter_enabled,      # NEW
    min_area_filter_amount=min_area_filter_amount,        # NEW
    min_side_filter_enabled=min_side_filter_enabled,      # NEW
    min_side_filter_amount=min_side_filter_amount,        # NEW
)
```

---

### Step 8: Add Unit Tests for Geometry Functions

**File:** `app/tests/core/test_geometry.py`

Add tests for the new geometry calculation functions.

```python
class TestCalculatePolygonArea:
    """Tests for calculate_polygon_area() function."""

    def test_square_area(self):
        """Test area calculation for a unit square."""
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert calculate_polygon_area(square) == 100.0

    def test_triangle_area(self):
        """Test area calculation for a right triangle."""
        triangle = [(0, 0), (10, 0), (10, 10)]
        assert calculate_polygon_area(triangle) == 50.0

    def test_degenerate_polygon(self):
        """Test area calculation for degenerate polygon."""
        line = [(0, 0), (10, 0)]
        assert calculate_polygon_area(line) == 0.0

    def test_empty_polygon(self):
        """Test area calculation for empty polygon."""
        assert calculate_polygon_area([]) == 0.0


class TestCalculateShortestStraightSide:
    """Tests for calculate_shortest_straight_side() function."""

    def test_square_shortest_side(self):
        """Test shortest side for a rectangle."""
        rect = [(0, 0), (100, 0), (100, 50), (0, 50)]
        assert calculate_shortest_straight_side(rect) == 50.0

    def test_collinear_edge_merging(self):
        """Test that collinear edges are merged."""
        # Rectangle with split bottom edge
        rect = [(0, 0), (50, 0), (100, 0), (100, 50), (0, 50)]
        # Bottom edge is 100 (merged from two 50-unit segments)
        # Vertical edges are 50
        assert calculate_shortest_straight_side(rect) == 50.0

    def test_degenerate_polygon(self):
        """Test shortest side for degenerate polygon."""
        line = [(0, 0), (10, 0)]
        assert calculate_shortest_straight_side(line) == 0.0
```

---

### Step 9: Add Integration Tests

**File:** `app/tests/core/extractor/test_extractor_filter.py` (new file)

```python
"""Tests for polygon filter parameters in extract_blocks()."""
import pytest
from app.core.extractor import extract_blocks

SAMPLE_DXF = "app/tests/assets/sample_drawing.dxf"


class TestExtractBlocksFilterParameters:
    """Tests for extract_blocks() filter parameter handling."""

    def test_accepts_min_area_filter_parameters(self):
        """Verify extract_blocks accepts min area filter parameters."""
        result = extract_blocks(
            SAMPLE_DXF,
            min_area_filter_enabled=True,
            min_area_filter_amount=100.0,
        )
        assert result is not None

    def test_accepts_min_side_filter_parameters(self):
        """Verify extract_blocks accepts min side filter parameters."""
        result = extract_blocks(
            SAMPLE_DXF,
            min_side_filter_enabled=True,
            min_side_filter_amount=10.0,
        )
        assert result is not None

    def test_filter_disabled_by_default(self):
        """Verify filters are disabled by default."""
        result = extract_blocks(SAMPLE_DXF)
        assert result is not None

    def test_all_filter_parameters_together(self):
        """Verify all filter parameters work together."""
        result = extract_blocks(
            SAMPLE_DXF,
            precision_fix_enabled=True,
            precision_fix_amount=0.01,
            gap_bridge_enabled=True,
            gap_bridge_amount=0.5,
            min_area_filter_enabled=True,
            min_area_filter_amount=50.0,
            min_side_filter_enabled=True,
            min_side_filter_amount=5.0,
        )
        assert result is not None
```

---

### Step 10: Validation

Run all validation commands to ensure zero regressions:

```bash
# Type checking
uv run mypy app/

# Linting
uv run ruff check app/
uv run ruff format app/ --check

# Run new geometry tests
uv run pytest app/tests/core/test_geometry.py -v

# Run new filter tests
uv run pytest app/tests/core/extractor/test_extractor_filter.py -v

# Run all tests
uv run pytest app/tests/ -v
```

---

## Recommendations

1. **Implement in exact sequence** - Each step builds on the previous; constants before types before geometry before extractor before GUI

2. **Test incrementally** - Run type checking and relevant tests after each step to catch issues early

3. **Follow existing patterns exactly** - The GUI layout and handler methods should mirror the Precision Fix and Gap Bridge implementations for consistency

4. **Use angle-based collinearity** (Approach 1 from source doc) - More control over what constitutes "collinear" and handles flattened arcs correctly

5. **Filter values are in DXF units** - Same as Precision Fix and Gap Bridge amounts; no unit conversion needed

## Next Steps

After implementation:

1. Manual testing with the Frysetorg test block to verify:
   - 21 polygons detected with appropriate precision fix
   - Filtering reduces polygon count appropriately
   - Content zone bounding box updates correctly after filtering

2. Consider future enhancements:
   - Add Excel columns showing area/shortest_side per block
   - Add polygon metrics to `ContentZoneData` for debugging
   - Add visual preview of filtered vs retained polygons
