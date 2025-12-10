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
