# Feature: Extractor Parameter Updates for Polygon Filtering (Unit 4)

## Feature Description
This feature updates the `extract_blocks()` function in `app/core/extractor.py` to accept new polygon filter parameters and pass them through to the `_detect_content_zone()` function. This is Unit 4 of the Polygon Filter Implementation, building on:
- Unit 1 (commit 0332046): Added filter constants (DEFAULT_MIN_AREA_FILTER, DEFAULT_MIN_SIDE_FILTER) and PolygonMetrics TypedDict
- Unit 2 (commit 62af902): Added `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions to geometry.py
- Unit 3 (commit fda4ddc): Updated `_detect_content_zone()` signature with min_area_filter and min_side_filter params, added filtering logic and 9 unit tests

The feature adds four new parameters to `extract_blocks()` and a new helper function `get_filter_values()` that mirrors the existing `get_snap_tolerances()` pattern for calculating effective filter values based on unit settings.

## User Story
As a CAD engineer using the DXF Block Extractor
I want the extraction function to accept polygon filter settings
So that the filter parameters flow from the GUI to the content zone detection logic

## Problem Statement
The `_detect_content_zone()` function now accepts `min_area_filter` and `min_side_filter` parameters (Unit 3), but the `extract_blocks()` function does not yet accept these parameters or pass them through. The parameter flow from GUI to content zone detection is incomplete, preventing users from controlling polygon filtering during extraction.

## Solution Statement
1. Update `extract_blocks()` signature to add four new parameters following the existing precision_fix pattern:
   - `min_area_filter_enabled: bool = False`
   - `min_area_filter_amount: float | None = None`
   - `min_side_filter_enabled: bool = False`
   - `min_side_filter_amount: float | None = None`

2. Add a new helper function `get_filter_values()` that calculates the effective filter values based on:
   - Whether filters are enabled (returns 0.0 when disabled)
   - User-specified amounts (if provided and > 0)
   - Default values from constants for the effective unit (fallback)

3. Update the `_detect_content_zone()` call inside `extract_blocks()` to pass the calculated filter values

4. Add import for `DEFAULT_MIN_AREA_FILTER` and `DEFAULT_MIN_SIDE_FILTER` from constants

## Relevant Files
Use these files to implement the feature:

- **app/core/extractor.py** - Main implementation file
  - Add import for DEFAULT_MIN_AREA_FILTER, DEFAULT_MIN_SIDE_FILTER from constants
  - Add `get_filter_values()` helper function (similar to `get_snap_tolerances()`)
  - Update `extract_blocks()` signature with 4 new parameters
  - Update `_detect_content_zone()` call to pass filter values
  - Update docstring to document new parameters

- **app/core/constants.py** - Already contains DEFAULT_MIN_AREA_FILTER and DEFAULT_MIN_SIDE_FILTER (Unit 1)
  - Reference only - no changes needed

- **app/core/geometry.py** - Already contains updated `_detect_content_zone()` signature (Unit 3)
  - Reference only - no changes needed

- **app/tests/core/extractor/test_extractor_precision_fix.py** - Reference for test patterns
  - Shows established patterns for testing tolerance parameters

### New Files
- **app/tests/core/extractor/test_extractor_polygon_filter.py** - New test file for polygon filter parameters
  - Tests for `get_filter_values()` helper function
  - Tests for `extract_blocks()` accepting new filter parameters
  - Tests for filter parameter combinations and edge cases

## Implementation Plan
### Phase 1: Foundation
Review the existing `get_snap_tolerances()` function pattern and the `extract_blocks()` signature. Confirm that `DEFAULT_MIN_AREA_FILTER` and `DEFAULT_MIN_SIDE_FILTER` constants exist in constants.py (Unit 1) and that `_detect_content_zone()` accepts the filter parameters (Unit 3).

### Phase 2: Core Implementation
1. Add imports for filter constants to extractor.py
2. Implement `get_filter_values()` helper function following the `get_snap_tolerances()` pattern
3. Update `extract_blocks()` signature with 4 new parameters
4. Calculate filter values using `get_filter_values()` inside `extract_blocks()`
5. Pass filter values to `_detect_content_zone()` call
6. Update docstrings to document new parameters

### Phase 3: Integration
Add comprehensive unit tests to verify:
- `get_filter_values()` returns correct values for all scenarios
- `extract_blocks()` accepts and propagates new parameters
- Backward compatibility is maintained (existing tests pass)
- Edge cases are handled correctly

## Step by Step Tasks

### Step 1: Add Imports for Filter Constants
Add imports for `DEFAULT_MIN_AREA_FILTER` and `DEFAULT_MIN_SIDE_FILTER` from constants module in `app/core/extractor.py`:

```python
from .constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,      # NEW
    DEFAULT_MIN_SIDE_FILTER,      # NEW
    DEFAULT_PRECISION_FIX_TOLERANCE,
    DXF_INSUNITS_MAP,
    SUPPORTED_EXTENSIONS,
)
```

### Step 2: Add get_filter_values() Helper Function
Add the `get_filter_values()` function after the existing `get_snap_tolerances()` function in `app/core/extractor.py`. This follows the same pattern as `get_snap_tolerances()`:

```python
def get_filter_values(
    detected_units: int,
    override_units: int | None,
    min_area_enabled: bool,
    min_area_amount: float | None,
    min_side_enabled: bool,
    min_side_amount: float | None,
) -> tuple[float, float]:
    """
    Calculate min area and min side filter values based on settings.

    This function computes filter values for polygon filtering in content zone detection:
    - When a filter is disabled, returns 0.0 (no filtering)
    - When enabled with a positive amount, uses that amount
    - When enabled without an amount (None, 0, or negative), uses unit-specific default

    Args:
        detected_units: The unit code detected from the DXF file's $INSUNITS header
        override_units: User-selected unit override. If None or -1, use detected_units
        min_area_enabled: Whether minimum area filtering is enabled
        min_area_amount: Custom min area amount. If None or <= 0, use default for unit
        min_side_enabled: Whether minimum side filtering is enabled
        min_side_amount: Custom min side amount. If None or <= 0, use default for unit

    Returns:
        Tuple of (min_area, min_side):
        - min_area: Returns 0.0 if disabled, user amount if provided and > 0,
                    otherwise default from DEFAULT_MIN_AREA_FILTER for the effective unit
        - min_side: Returns 0.0 if disabled, user amount if provided and > 0,
                    otherwise default from DEFAULT_MIN_SIDE_FILTER for the effective unit

    Examples:
        >>> # Both filters disabled
        >>> get_filter_values(4, None, False, None, False, None)
        (0.0, 0.0)

        >>> # Area filter enabled with default, side filter disabled
        >>> get_filter_values(4, None, True, None, False, None)
        (100.0, 0.0)  # Uses DEFAULT_MIN_AREA_FILTER[4]

        >>> # Both enabled with custom amounts
        >>> get_filter_values(4, None, True, 50.0, True, 5.0)
        (50.0, 5.0)

        >>> # Unit override affects default values
        >>> get_filter_values(4, 1, True, None, True, None)
        (0.01, 0.5)  # Uses inch defaults from constants
    """
    # Determine effective units: use override if provided and not -1
    if override_units is not None and override_units != -1:
        effective_units = override_units
        logger.debug(
            f"Using override units for filters: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )
    else:
        effective_units = detected_units
        logger.debug(
            f"Using detected units for filters: {DXF_INSUNITS_MAP.get(effective_units, f'Unknown ({effective_units})')}"
        )

    # Calculate min area filter value
    if not min_area_enabled:
        min_area = 0.0
    elif min_area_amount is not None and min_area_amount > 0:
        min_area = min_area_amount
        logger.debug(f"Using custom min area filter amount: {min_area}")
    else:
        min_area = DEFAULT_MIN_AREA_FILTER.get(effective_units, 100.0)
        logger.debug(f"Using default min area filter: {min_area}")

    # Calculate min side filter value
    if not min_side_enabled:
        min_side = 0.0
    elif min_side_amount is not None and min_side_amount > 0:
        min_side = min_side_amount
        logger.debug(f"Using custom min side filter amount: {min_side}")
    else:
        min_side = DEFAULT_MIN_SIDE_FILTER.get(effective_units, 10.0)
        logger.debug(f"Using default min side filter: {min_side}")

    logger.debug(f"Calculated filter values: min_area={min_area}, min_side={min_side}")

    return (min_area, min_side)
```

### Step 3: Update extract_blocks() Signature
Update the `extract_blocks()` function signature in `app/core/extractor.py` to add four new parameters:

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

### Step 4: Update extract_blocks() Docstring
Update the docstring for `extract_blocks()` to document the new parameters:

Add to Args section:
```
        min_area_filter_enabled: Enable minimum area filtering for content zone detection.
                                 When True, polygons with area below threshold are filtered out.
                                 Defaults to False.
        min_area_filter_amount: Custom minimum area threshold. If provided and > 0, this value
                                is used. If None, 0, or negative, uses the default from
                                DEFAULT_MIN_AREA_FILTER for the effective unit.
                                Defaults to None.
        min_side_filter_enabled: Enable minimum side filtering for content zone detection.
                                 When True, polygons with shortest side below threshold are
                                 filtered out. Defaults to False.
        min_side_filter_amount: Custom minimum side threshold. If provided and > 0, this value
                                is used. If None, 0, or negative, uses the default from
                                DEFAULT_MIN_SIDE_FILTER for the effective unit.
                                Defaults to None.
```

Add to Examples section:
```
        >>> # With polygon filtering enabled
        >>> result = extract_blocks('drawing.dxf', min_area_filter_enabled=True)

        >>> # With custom filter amounts
        >>> result = extract_blocks('drawing.dxf',
        ...     min_area_filter_enabled=True,
        ...     min_area_filter_amount=50.0,
        ...     min_side_filter_enabled=True,
        ...     min_side_filter_amount=5.0)
```

### Step 5: Calculate Filter Values Inside extract_blocks()
After the tolerance calculation in `extract_blocks()`, add filter value calculation:

```python
# Calculate polygon filter values
min_area, min_side = get_filter_values(
    detected_units,
    unit_override,
    min_area_filter_enabled,
    min_area_filter_amount,
    min_side_filter_enabled,
    min_side_filter_amount,
)
logger.info(
    f"Using polygon filters: min_area={min_area}, min_side={min_side} "
    f"(area_filter={'enabled' if min_area_filter_enabled else 'disabled'}, "
    f"side_filter={'enabled' if min_side_filter_enabled else 'disabled'})"
)
```

### Step 6: Update _detect_content_zone() Call
Update the `_detect_content_zone()` call inside `extract_blocks()` to pass the filter values. Find the existing call (around line 1120-1127) and update it:

```python
# Detect content zone for trim value suggestions
content_zone_result = _detect_content_zone(
    block_def,
    bbox,
    abort_event,
    precision_tolerance,
    gap_bridge_tolerance,
    min_area,      # NEW
    min_side,      # NEW
)
block_content_zone_data[effective_name] = content_zone_result
```

### Step 7: Create Test File for get_filter_values()
Create new test file `app/tests/core/extractor/test_extractor_polygon_filter.py`:

```python
"""
Tests for polygon filter parameters in the extractor module.

Tests cover:
- get_filter_values() with various enabled/disabled combinations
- get_filter_values() with custom and default amounts
- get_filter_values() with unit override
- extract_blocks() accepting new filter parameters
- Backward compatibility (existing behavior preserved)
"""

from pathlib import Path

from core.constants import (
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
)
from core.extractor import extract_blocks, get_filter_values


# Test assets directory
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class TestGetFilterValuesDisabled:
    """Tests for get_filter_values() when filters are disabled."""

    def test_both_filters_disabled_returns_zeros(self) -> None:
        """When both filters disabled, should return (0.0, 0.0)."""
        min_area, min_side = get_filter_values(
            detected_units=4,  # Millimeters
            override_units=None,
            min_area_enabled=False,
            min_area_amount=None,
            min_side_enabled=False,
            min_side_amount=None,
        )

        assert min_area == 0.0
        assert min_side == 0.0

    def test_area_disabled_side_enabled_default(self) -> None:
        """Area filter disabled, side filter enabled with default."""
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=False,
            min_area_amount=None,
            min_side_enabled=True,
            min_side_amount=None,
        )

        assert min_area == 0.0
        assert min_side == DEFAULT_MIN_SIDE_FILTER[4]

    def test_area_enabled_side_disabled_default(self) -> None:
        """Area filter enabled with default, side filter disabled."""
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=True,
            min_area_amount=None,
            min_side_enabled=False,
            min_side_amount=None,
        )

        assert min_area == DEFAULT_MIN_AREA_FILTER[4]
        assert min_side == 0.0


class TestGetFilterValuesCustomAmounts:
    """Tests for get_filter_values() with custom amounts."""

    def test_custom_area_amount_used(self) -> None:
        """When custom area amount provided, should use it."""
        custom_amount = 50.0
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=True,
            min_area_amount=custom_amount,
            min_side_enabled=False,
            min_side_amount=None,
        )

        assert min_area == custom_amount
        assert min_side == 0.0

    def test_custom_side_amount_used(self) -> None:
        """When custom side amount provided, should use it."""
        custom_amount = 5.0
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=False,
            min_area_amount=None,
            min_side_enabled=True,
            min_side_amount=custom_amount,
        )

        assert min_area == 0.0
        assert min_side == custom_amount

    def test_both_custom_amounts(self) -> None:
        """Both filters with custom amounts."""
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=True,
            min_area_amount=200.0,
            min_side_enabled=True,
            min_side_amount=15.0,
        )

        assert min_area == 200.0
        assert min_side == 15.0

    def test_zero_amount_uses_default(self) -> None:
        """When amount is 0, should use default."""
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=True,
            min_area_amount=0.0,
            min_side_enabled=True,
            min_side_amount=0.0,
        )

        assert min_area == DEFAULT_MIN_AREA_FILTER[4]
        assert min_side == DEFAULT_MIN_SIDE_FILTER[4]

    def test_negative_amount_uses_default(self) -> None:
        """When amount is negative, should use default."""
        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=None,
            min_area_enabled=True,
            min_area_amount=-10.0,
            min_side_enabled=True,
            min_side_amount=-5.0,
        )

        assert min_area == DEFAULT_MIN_AREA_FILTER[4]
        assert min_side == DEFAULT_MIN_SIDE_FILTER[4]


class TestGetFilterValuesUnitHandling:
    """Tests for get_filter_values() unit handling."""

    def test_all_units_have_defaults(self) -> None:
        """All supported units should have default filter values."""
        supported_units = [0, 1, 2, 4, 5, 6]

        for unit_code in supported_units:
            min_area, min_side = get_filter_values(
                detected_units=unit_code,
                override_units=None,
                min_area_enabled=True,
                min_area_amount=None,
                min_side_enabled=True,
                min_side_amount=None,
            )

            assert min_area == DEFAULT_MIN_AREA_FILTER[unit_code], (
                f"Unit {unit_code} should have default area filter"
            )
            assert min_side == DEFAULT_MIN_SIDE_FILTER[unit_code], (
                f"Unit {unit_code} should have default side filter"
            )

    def test_unit_override_applies(self) -> None:
        """When unit override specified, should use override unit defaults."""
        detected_units = 4  # Millimeters
        override_units = 1  # Inches

        min_area, min_side = get_filter_values(
            detected_units=detected_units,
            override_units=override_units,
            min_area_enabled=True,
            min_area_amount=None,
            min_side_enabled=True,
            min_side_amount=None,
        )

        # Should use inch defaults, not mm
        assert min_area == DEFAULT_MIN_AREA_FILTER[1]
        assert min_side == DEFAULT_MIN_SIDE_FILTER[1]
        assert min_area != DEFAULT_MIN_AREA_FILTER[4]
        assert min_side != DEFAULT_MIN_SIDE_FILTER[4]

    def test_override_minus_one_uses_detected(self) -> None:
        """When override is -1 (auto), should use detected units."""
        detected_units = 4  # Millimeters
        override_units = -1  # Auto-detect

        min_area, min_side = get_filter_values(
            detected_units=detected_units,
            override_units=override_units,
            min_area_enabled=True,
            min_area_amount=None,
            min_side_enabled=True,
            min_side_amount=None,
        )

        assert min_area == DEFAULT_MIN_AREA_FILTER[4]
        assert min_side == DEFAULT_MIN_SIDE_FILTER[4]

    def test_unknown_unit_uses_fallback(self) -> None:
        """Unknown unit code should use fallback values."""
        min_area, min_side = get_filter_values(
            detected_units=99,  # Unknown
            override_units=None,
            min_area_enabled=True,
            min_area_amount=None,
            min_side_enabled=True,
            min_side_amount=None,
        )

        # Should use fallback values (100.0 for area, 10.0 for side)
        assert min_area == 100.0
        assert min_side == 10.0


class TestGetFilterValuesCustomWithOverride:
    """Tests for custom amounts with unit override."""

    def test_custom_amount_overrides_unit_default(self) -> None:
        """Custom amount should be used even with unit override."""
        custom_area = 75.0
        custom_side = 8.0

        min_area, min_side = get_filter_values(
            detected_units=4,
            override_units=1,  # Inches
            min_area_enabled=True,
            min_area_amount=custom_area,
            min_side_enabled=True,
            min_side_amount=custom_side,
        )

        # Custom amounts should override unit-specific defaults
        assert min_area == custom_area
        assert min_side == custom_side
        assert min_area != DEFAULT_MIN_AREA_FILTER[1]
        assert min_side != DEFAULT_MIN_SIDE_FILTER[1]


class TestExtractBlocksFilterParameters:
    """Tests for extract_blocks() accepting filter parameters."""

    def test_accepts_min_area_filter_enabled(self) -> None:
        """Verify extract_blocks accepts min_area_filter_enabled parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_area_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_min_side_filter_enabled(self) -> None:
        """Verify extract_blocks accepts min_side_filter_enabled parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_side_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_min_area_filter_amount(self) -> None:
        """Verify extract_blocks accepts min_area_filter_amount parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=50.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_min_side_filter_amount(self) -> None:
        """Verify extract_blocks accepts min_side_filter_amount parameter."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_side_filter_enabled=True,
            min_side_filter_amount=5.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_accepts_all_four_filter_parameters(self) -> None:
        """Verify extract_blocks accepts all four new filter parameters."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=100.0,
            min_side_filter_enabled=True,
            min_side_filter_amount=10.0,
        )

        assert result is not None
        assert "block_counts" in result
        assert "block_content_zone_data" in result


class TestExtractBlocksFilterWithOtherParams:
    """Tests for filter parameters combined with other extract_blocks params."""

    def test_filters_with_precision_fix(self) -> None:
        """Filters work correctly with precision_fix parameters."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=0.01,
            min_area_filter_enabled=True,
            min_area_filter_amount=50.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_filters_with_gap_bridge(self) -> None:
        """Filters work correctly with gap_bridge parameters."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            gap_bridge_enabled=True,
            gap_bridge_amount=0.5,
            min_side_filter_enabled=True,
            min_side_filter_amount=5.0,
        )

        assert result is not None
        assert "block_counts" in result

    def test_all_tolerance_and_filter_params(self) -> None:
        """All tolerance and filter parameters work together."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=4,
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
            precision_fix_enabled=True,
            precision_fix_amount=0.01,
            min_area_filter_enabled=True,
            min_area_filter_amount=100.0,
            min_side_filter_enabled=True,
            min_side_filter_amount=10.0,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)


class TestExtractBlocksFilterBackwardCompatibility:
    """Tests for backward compatibility with filter parameters."""

    def test_default_filters_disabled(self) -> None:
        """By default, filters should be disabled (no filtering)."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Call without filter parameters
        result = extract_blocks(str(sample_dxf))

        assert result is not None
        assert "block_counts" in result

    def test_block_counts_consistent_with_filters_disabled(self) -> None:
        """Block counts should be identical with filters disabled vs no params."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result_default = extract_blocks(str(sample_dxf))
        result_explicit = extract_blocks(
            str(sample_dxf),
            min_area_filter_enabled=False,
            min_side_filter_enabled=False,
        )

        assert result_default["block_counts"] == result_explicit["block_counts"]


class TestExtractBlocksFilterEdgeCases:
    """Edge case tests for filter parameters."""

    def test_empty_file_with_filters_enabled(self) -> None:
        """Extraction works on empty DXF file with filters enabled."""
        empty_dxf = ASSETS_DIR / "empty_drawing.dxf"

        result = extract_blocks(
            str(empty_dxf),
            min_area_filter_enabled=True,
            min_side_filter_enabled=True,
        )

        assert result is not None
        assert result["block_counts"] == {}

    def test_filter_enabled_with_zero_amount(self) -> None:
        """Filter enabled with amount=0 should use default."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=0.0,  # Should use default
        )

        assert result is not None
        assert "block_counts" in result

    def test_filter_enabled_with_negative_amount(self) -> None:
        """Filter enabled with negative amount should use default."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            min_side_filter_enabled=True,
            min_side_filter_amount=-5.0,  # Should use default
        )

        assert result is not None
        assert "block_counts" in result

    def test_filters_with_unit_override(self) -> None:
        """Filters work correctly with unit override."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=1,  # Inches
            min_area_filter_enabled=True,
            min_side_filter_enabled=True,
        )

        assert result is not None
        assert "block_counts" in result
```

### Step 8: Run Type Checking
Execute mypy to verify type annotations are correct:

```bash
uv run mypy app/core/extractor.py
```

### Step 9: Run Linting
Execute ruff to ensure code style compliance:

```bash
uv run ruff check app/core/extractor.py
uv run ruff format app/ --check
```

### Step 10: Run New Filter Tests
Run the new filter test suite:

```bash
uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v
```

### Step 11: Run Extractor Test Suite
Run the full extractor test suite to verify no regressions:

```bash
uv run pytest app/tests/core/extractor/ -v
```

### Step 12: Run All Tests
Execute the full test suite to verify zero regressions:

```bash
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests
1. **TestGetFilterValuesDisabled** - Tests for disabled filter scenarios:
   - Both filters disabled returns (0.0, 0.0)
   - One filter disabled, one enabled with default

2. **TestGetFilterValuesCustomAmounts** - Tests for custom amounts:
   - Custom area amount used when provided and > 0
   - Custom side amount used when provided and > 0
   - Both custom amounts work together
   - Zero amount falls back to default
   - Negative amount falls back to default

3. **TestGetFilterValuesUnitHandling** - Tests for unit-based defaults:
   - All supported units (0, 1, 2, 4, 5, 6) have correct defaults
   - Unit override applies correctly
   - Override -1 (auto) uses detected units
   - Unknown unit uses fallback values

4. **TestExtractBlocksFilterParameters** - Tests for parameter acceptance:
   - Each new parameter is accepted without error
   - All four parameters work together

### Integration Tests
1. **TestExtractBlocksFilterWithOtherParams** - Tests with other extractor params:
   - Filters work with precision_fix parameters
   - Filters work with gap_bridge parameters
   - All parameters work together

2. **TestExtractBlocksFilterBackwardCompatibility** - Backward compatibility:
   - Default behavior unchanged (no filter params = no filtering)
   - Block counts consistent with filters disabled

### Edge Cases
1. Empty DXF file with filters enabled
2. Filter enabled with amount = 0 (use default)
3. Filter enabled with negative amount (use default)
4. Filters with unit override
5. Unknown unit code (use fallback)
6. All combinations of enabled/disabled and custom/default

### Playwright MCP Tests
Not applicable for this unit - no GUI changes are included. GUI integration will be tested in Unit 5.

## Acceptance Criteria
1. `extract_blocks()` signature updated with 4 new parameters:
   - `min_area_filter_enabled: bool = False`
   - `min_area_filter_amount: float | None = None`
   - `min_side_filter_enabled: bool = False`
   - `min_side_filter_amount: float | None = None`
2. `get_filter_values()` helper function added with correct logic matching spec
3. `_detect_content_zone()` call updated to pass calculated filter values
4. Constants imported: `DEFAULT_MIN_AREA_FILTER`, `DEFAULT_MIN_SIDE_FILTER`
5. Docstrings updated for new parameters in both functions
6. New test file created with comprehensive tests for all scenarios
7. All existing 695+ tests continue to pass
8. Type checking passes with `uv run mypy app/`
9. Linting passes with `uv run ruff check app/`

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/extractor.py` - Type check the modified extractor module
- `uv run mypy app/` - Type check all application code
- `uv run ruff check app/core/extractor.py` - Lint the modified extractor module
- `uv run ruff check app/` - Lint all application code
- `uv run ruff format app/ --check` - Verify code formatting
- `uv run pytest app/tests/core/extractor/test_extractor_polygon_filter.py -v` - Run new filter tests
- `uv run pytest app/tests/core/extractor/ -v` - Run all extractor tests
- `uv run pytest app/tests/core/test_content_zone.py -v` - Run content zone tests (related)
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes
- This is Unit 4 of a multi-unit implementation plan for polygon filtering (source: `ai_output/020-polygon-filter-implementation-plan.md`)
- Unit 1 (commit 0332046) added constants and `PolygonMetrics` TypedDict
- Unit 2 (commit 62af902) added `calculate_polygon_area()` and `calculate_shortest_straight_side()` functions
- Unit 3 (commit fda4ddc) updated `_detect_content_zone()` signature and added filtering logic with 9 unit tests
- Unit 5 will add GUI controls (checkboxes and entry fields) for the filter settings
- The `get_filter_values()` function follows the same pattern as `get_snap_tolerances()` for consistency
- Filter values are in DXF drawing units (same as precision fix and gap bridge amounts)
- Default parameters ensure backward compatibility - existing code calling `extract_blocks()` without filter parameters will work unchanged
- Current test count before this unit: 695+ tests passing
