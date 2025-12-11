"""
Tests for polygon filter parameters in the extractor module.

Tests cover:
- get_filter_values() with various enabled/disabled combinations
- get_filter_values() with custom and default amounts
- get_filter_values() with unit override
- extract_blocks() accepting new filter parameters
- Backward compatibility (existing behavior preserved)
- Net area filter integration (nested polygon filtering via extract_blocks)
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


class TestNetAreaFilterIntegration:
    """Integration tests for net area filtering via extract_blocks().

    These tests verify that the full extraction pipeline correctly applies
    net area filtering to nested polygons. The tests use nested_polygon_filter_test.dxf
    which contains blocks with known nested polygon configurations.

    Test blocks:
    - PICTURE_FRAME: Outer 100x100 (net=3600), inner 80x80 (net=6400)
      With min_area_filter=5000: outer filtered (3600<5000), inner kept (6400>=5000)
    """

    def test_nested_polygon_filtered_by_net_area(self) -> None:
        """Extract blocks filters nested polygons by net area.

        Uses PICTURE_FRAME block which has:
        - Outer rectangle: 100x100 = 10,000 gross, net = 3,600 (after subtracting inner)
        - Inner rectangle: 80x80 = 6,400 gross = 6,400 net (no children)

        With min_area_filter=5000:
        - Outer fails: 3,600 < 5,000
        - Inner passes: 6,400 >= 5,000

        Expected: polygon_count == 1 in content_zone_data for PICTURE_FRAME
        """
        nested_dxf = ASSETS_DIR / "nested_polygon_filter_test.dxf"

        result = extract_blocks(
            str(nested_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=5000.0,
            min_side_filter_enabled=False,
        )

        assert result is not None
        assert "block_content_zone_data" in result

        # PICTURE_FRAME block should have content zone data
        content_zone_data = result["block_content_zone_data"]
        assert "PICTURE_FRAME" in content_zone_data

        # Only inner polygon should remain after net area filtering
        picture_frame_data = content_zone_data["PICTURE_FRAME"]
        assert picture_frame_data["content_zone_detected"] is True
        assert (
            picture_frame_data["polygon_count"] == 2
        )  # Original count before filtering
        assert (
            picture_frame_data["filtered_polygon_count"] == 1
        )  # After net area filter

    def test_content_zone_reflects_net_area_winner(self) -> None:
        """Content zone data shows correct polygon after net area filtering.

        When outer frame is filtered out by net area filter, the inner polygon
        should become the content zone with correct trim values.

        PICTURE_FRAME block:
        - Block bounding box: (0,0) to (100,100)
        - Inner polygon: (10,10) to (90,90)

        Expected trim values (distance from block bbox to content zone):
        - left: 10 (inner starts at x=10)
        - right: 10 (inner ends at x=90, bbox is 100)
        - top: 10 (inner ends at y=90, bbox is 100)
        - bottom: 10 (inner starts at y=10)
        """
        nested_dxf = ASSETS_DIR / "nested_polygon_filter_test.dxf"

        result = extract_blocks(
            str(nested_dxf),
            min_area_filter_enabled=True,
            min_area_filter_amount=5000.0,
            min_side_filter_enabled=False,
        )

        assert result is not None
        content_zone_data = result["block_content_zone_data"]
        picture_frame_data = content_zone_data["PICTURE_FRAME"]

        # Verify content zone was detected
        assert picture_frame_data["content_zone_detected"] is True

        # Inner rectangle is (10,10) to (90,90), so all trims should be 10
        assert picture_frame_data["suggested_trim_left"] == 10.0
        assert picture_frame_data["suggested_trim_right"] == 10.0
        assert picture_frame_data["suggested_trim_top"] == 10.0
        assert picture_frame_data["suggested_trim_bottom"] == 10.0

        # Content zone dimensions should be 80x80 (inner rectangle)
        assert picture_frame_data["content_zone_width"] == 80.0
        assert picture_frame_data["content_zone_height"] == 80.0
