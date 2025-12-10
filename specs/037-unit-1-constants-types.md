# Feature: Polygon Filter Constants and Types (Unit 1)

## Feature Description
This feature adds the foundation constants and types needed for polygon filtering in content zone detection. It introduces two new filter mechanisms:
1. **Minimum Area Filter** - Filters out polygons with surface area below a threshold
2. **Minimum Side Filter** - Filters out polygons with shortest straight side below a threshold

This is Unit 1 of the Polygon Filter Implementation, focusing solely on the constants and types foundation. It establishes the building blocks for the geometry functions (Unit 2), extractor integration (Unit 3), and GUI controls (Unit 4).

## User Story
As a CAD engineer processing DXF files
I want polygon filter constants and types defined
So that subsequent implementation units can use well-defined defaults and type-safe data structures for filtering small polygons from content zone calculations

## Problem Statement
When calculating content zone bounding boxes, small artifact polygons (dust, debris, construction lines) can skew results. The application needs:
1. Unit-aware default filter values (different thresholds for mm, inches, feet, etc.)
2. Input constraint constants for future GUI validation
3. A typed data structure to hold polygon metrics (area, shortest side, perimeter)

Currently, there are no constants or types to support polygon filtering by area or shortest side length.

## Solution Statement
1. Add `DEFAULT_MIN_AREA_FILTER` dictionary in `constants.py` with unit-specific area thresholds:
   - Unitless (0): 100.0 (mm-equivalent)
   - Inches (1): 0.01 sq inches
   - Feet (2): 0.001 sq feet
   - Millimeters (4): 100 sq mm
   - Centimeters (5): 1 sq cm
   - Meters (6): 0.0001 sq m (100 sq mm equivalent)

2. Add `DEFAULT_MIN_SIDE_FILTER` dictionary with unit-specific length thresholds:
   - Unitless (0): 10.0 (mm-equivalent)
   - Inches (1): 0.5 inches
   - Feet (2): 0.05 feet (~0.6 inches)
   - Millimeters (4): 10mm
   - Centimeters (5): 1cm
   - Meters (6): 0.01m (10mm equivalent)

3. Add `MIN_AREA_FILTER_MIN`, `MIN_AREA_FILTER_MAX`, `MIN_SIDE_FILTER_MIN`, `MIN_SIDE_FILTER_MAX` constraint constants for future GUI validation.

4. Add `PolygonMetrics` TypedDict in `types.py` for type-safe polygon metric storage.

## Relevant Files
Use these files to implement the feature:

- **app/core/constants.py** - Contains all application constants including tolerance dictionaries and constraint values
  - Add `DEFAULT_MIN_AREA_FILTER` dict with unit-specific area thresholds
  - Add `MIN_AREA_FILTER_MIN` and `MIN_AREA_FILTER_MAX` constraint constants
  - Add `DEFAULT_MIN_SIDE_FILTER` dict with unit-specific length thresholds
  - Add `MIN_SIDE_FILTER_MIN` and `MIN_SIDE_FILTER_MAX` constraint constants
  - Follow existing pattern of `DEFAULT_GAP_BRIDGE_TOLERANCE` and `DEFAULT_PRECISION_FIX_TOLERANCE`

- **app/core/types.py** - Contains TypedDict definitions for internal data structures
  - Add `PolygonMetrics` TypedDict with area_raw, shortest_side, perimeter fields
  - Follow existing pattern of `BlockTrimmingData` and `ContentZoneData` TypedDicts

- **app/tests/core/test_constants.py** - Tests for constants module
  - Add `TestMinAreaFilterConstants` test class for area filter constants
  - Add `TestMinSideFilterConstants` test class for side filter constants
  - Follow existing pattern of `TestPrecisionFixToleranceConstants` and `TestDrawingUnitConstants`

### New Files
None - all changes are to existing files.

## Implementation Plan
### Phase 1: Foundation
Add all filter constants to `constants.py` following the pattern of existing gap bridge and precision fix constants. These constants must be added first as they will be imported by tests.

### Phase 2: Core Implementation
Add `PolygonMetrics` TypedDict to `types.py` following the pattern of existing TypedDicts. This provides the type-safe data structure for polygon metrics.

### Phase 3: Integration
Add comprehensive tests to `test_constants.py` to verify the new constants exist, have correct values, and follow established patterns. Run validation to ensure zero regressions.

## Step by Step Tasks

### Step 1: Add Min Area Filter Constants to constants.py
Add the following constants at the end of the file, after the existing `PRECISION_FIX_MAX` constant:

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
"""Minimum area filter amount (0 = no area filtering)."""

MIN_AREA_FILTER_MAX: float = 1000000.0
"""Maximum area filter amount. Large value allows extreme cases while
preventing overflow issues in calculations."""
```

### Step 2: Add Min Side Filter Constants to constants.py
Add the following constants immediately after the area filter constants:

```python
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
"""Minimum side filter amount (0 = no side filtering)."""

MIN_SIDE_FILTER_MAX: float = 100000.0
"""Maximum side filter amount. Large value allows extreme cases while
preventing overflow issues in calculations."""
```

### Step 3: Add PolygonMetrics TypedDict to types.py
Add the following TypedDict at the end of `types.py`, after the existing `ContentZoneData` class:

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

### Step 4: Add Tests for Min Area Filter Constants
Add the following test class to `test_constants.py`:

- Import the new constants: `DEFAULT_MIN_AREA_FILTER`, `MIN_AREA_FILTER_MIN`, `MIN_AREA_FILTER_MAX`
- Create `TestMinAreaFilterConstants` class with these tests:
  - `test_default_min_area_filter_has_all_supported_units` - Verify unit codes 0, 1, 2, 4, 5, 6 are present
  - `test_default_min_area_filter_values_non_negative` - All values must be >= 0
  - `test_min_area_filter_min_value` - Verify MIN_AREA_FILTER_MIN == 0.0
  - `test_min_area_filter_max_value` - Verify MIN_AREA_FILTER_MAX == 1000000.0
  - `test_min_area_filter_min_less_than_max` - Verify MIN < MAX
  - `test_default_min_area_filter_mm_value` - Verify MM (4) == 100.0
  - `test_default_min_area_filter_inch_value` - Verify IN (1) == 0.01

### Step 5: Add Tests for Min Side Filter Constants
Add the following test class to `test_constants.py`:

- Import the new constants: `DEFAULT_MIN_SIDE_FILTER`, `MIN_SIDE_FILTER_MIN`, `MIN_SIDE_FILTER_MAX`
- Create `TestMinSideFilterConstants` class with these tests:
  - `test_default_min_side_filter_has_all_supported_units` - Verify unit codes 0, 1, 2, 4, 5, 6 are present
  - `test_default_min_side_filter_values_non_negative` - All values must be >= 0
  - `test_min_side_filter_min_value` - Verify MIN_SIDE_FILTER_MIN == 0.0
  - `test_min_side_filter_max_value` - Verify MIN_SIDE_FILTER_MAX == 100000.0
  - `test_min_side_filter_min_less_than_max` - Verify MIN < MAX
  - `test_default_min_side_filter_mm_value` - Verify MM (4) == 10.0
  - `test_default_min_side_filter_inch_value` - Verify IN (1) == 0.5

### Step 6: Run Validation Commands
Execute all validation commands to ensure zero regressions:

```bash
# Type check all application code
uv run mypy app/

# Lint all application code
uv run ruff check app/

# Format check
uv run ruff format app/ --check

# Run constants tests specifically
uv run pytest app/tests/core/test_constants.py -v

# Run all tests to ensure zero regressions
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests
1. **Constants Tests (`test_constants.py`)**:
   - `DEFAULT_MIN_AREA_FILTER` contains all supported unit codes (0, 1, 2, 4, 5, 6)
   - All area filter values are non-negative
   - `MIN_AREA_FILTER_MIN` (0.0) and `MIN_AREA_FILTER_MAX` (1000000.0) constraints are valid
   - `MIN_AREA_FILTER_MIN` < `MIN_AREA_FILTER_MAX`
   - `DEFAULT_MIN_SIDE_FILTER` contains all supported unit codes (0, 1, 2, 4, 5, 6)
   - All side filter values are non-negative
   - `MIN_SIDE_FILTER_MIN` (0.0) and `MIN_SIDE_FILTER_MAX` (100000.0) constraints are valid
   - `MIN_SIDE_FILTER_MIN` < `MIN_SIDE_FILTER_MAX`
   - Specific value tests for MM and IN unit codes

### Integration Tests
Not applicable for this unit - constants and types are foundational components with no integration points yet.

### Edge Cases
1. Verify all 6 standard unit codes (0, 1, 2, 4, 5, 6) are present in both filter dictionaries
2. Verify constraint constants have correct relationships (MIN < MAX)
3. Verify non-negative values for all defaults (areas and lengths cannot be negative)
4. Verify specific expected values for MM and IN units match the specification

### Playwright MCP Tests
Not applicable for this unit - no GUI changes are included.

## Acceptance Criteria
1. `DEFAULT_MIN_AREA_FILTER` dict exists in `constants.py` with correct values for all 6 unit codes (0, 1, 2, 4, 5, 6)
2. `MIN_AREA_FILTER_MIN` (0.0) and `MIN_AREA_FILTER_MAX` (1000000.0) constants exist in `constants.py`
3. `DEFAULT_MIN_SIDE_FILTER` dict exists in `constants.py` with correct values for all 6 unit codes (0, 1, 2, 4, 5, 6)
4. `MIN_SIDE_FILTER_MIN` (0.0) and `MIN_SIDE_FILTER_MAX` (100000.0) constants exist in `constants.py`
5. `PolygonMetrics` TypedDict exists in `types.py` with `area_raw`, `shortest_side`, `perimeter` fields (all float)
6. All existing tests pass (backward compatibility)
7. All new tests pass
8. Type checking passes with `uv run mypy app/`
9. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests to validate new filter constants
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This is Unit 1 of a multi-unit implementation plan for polygon filtering (source: `ai_output/020-polygon-filter-implementation-plan.md`)
- Unit 2 will add geometry functions (`calculate_polygon_area()`, `calculate_shortest_straight_side()`) that use these constants
- Unit 3 will add extractor integration to pass filter parameters through `extract_blocks()`
- Unit 4 will add GUI controls (checkboxes and entry fields) for the filter settings
- The filter constants follow the exact pattern established by `DEFAULT_PRECISION_FIX_TOLERANCE` and `DEFAULT_GAP_BRIDGE_TOLERANCE`
- The `PolygonMetrics` TypedDict follows the pattern of existing TypedDicts like `BlockTrimmingData` and `ContentZoneData`
- All filter values are in DXF drawing units (same as Precision Fix and Gap Bridge amounts)
- The `PolygonMetrics.perimeter` field is included for future extensibility even though it's not immediately needed for filtering

### Reference Table (Filter Default Values)
| Unit | Code | Area Filter Default | Side Filter Default |
|------|------|---------------------|---------------------|
| Unitless | 0 | 100.0 sq units | 10.0 units |
| Inches | 1 | 0.01 sq inches | 0.5 inches |
| Feet | 2 | 0.001 sq feet | 0.05 feet |
| Millimeters | 4 | 100.0 sq mm | 10.0 mm |
| Centimeters | 5 | 1.0 sq cm | 1.0 cm |
| Meters | 6 | 0.0001 sq m | 0.01 m |
