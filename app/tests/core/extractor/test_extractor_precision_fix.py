"""
Tests for precision fix toggle functionality in the extractor module.

Tests cover:
- get_snap_tolerances() with precision_fix_enabled=True (returns calculated tolerance)
- get_snap_tolerances() with precision_fix_enabled=False (returns 0.0)
- Backward compatibility (default precision_fix_enabled=True)
- Independence of precision_fix_enabled and gap_bridge_enabled settings
- extract_blocks() propagation of precision_fix_enabled parameter
"""

from pathlib import Path

from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_PRECISION_FIX_TOLERANCE,
)
from core.extractor import extract_blocks, get_snap_tolerances


# Test assets directory
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class TestPrecisionFixToggle:
    """Tests for precision_fix_enabled parameter in get_snap_tolerances().

    NOTE: This class now tests with DEFAULT_PRECISION_FIX_TOLERANCE (practical CAD scale)
    instead of the old PRECISION_SNAP_TOLERANCE (nanometer scale). The function now uses
    the new larger tolerances by default for better coordinate precision error correction.
    """

    def test_precision_fix_enabled_returns_calculated_tolerance(self) -> None:
        """When precision_fix_enabled=True, should return calculated tolerance for unit.

        Uses DEFAULT_PRECISION_FIX_TOLERANCE which has practical CAD-scale tolerances
        (e.g., 0.01mm for millimeters instead of 1e-6mm).
        """
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Should use mm precision tolerance from new DEFAULT_PRECISION_FIX_TOLERANCE
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]
        assert precision > 0.0
        assert gap_bridge == 0.0

    def test_precision_fix_disabled_returns_zero(self) -> None:
        """When precision_fix_enabled=False, should return 0.0 precision tolerance."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        # Should return 0.0 when precision fix is disabled
        assert precision == 0.0
        assert gap_bridge == 0.0

    def test_default_precision_fix_enabled_backward_compatible(self) -> None:
        """Default value of precision_fix_enabled should be True (backward compatible).

        Note: The returned tolerance value has changed to use DEFAULT_PRECISION_FIX_TOLERANCE
        (practical CAD scale) instead of PRECISION_SNAP_TOLERANCE (nanometer scale).
        """
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        # Call without precision_fix_enabled parameter (uses default)
        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should behave as if precision_fix_enabled=True (backward compatible)
        # Now uses DEFAULT_PRECISION_FIX_TOLERANCE instead of PRECISION_SNAP_TOLERANCE
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]
        assert precision > 0.0

    def test_precision_fix_disabled_with_all_units(self) -> None:
        """When precision_fix_enabled=False, should return 0.0 for all unit types."""
        supported_units = [0, 1, 2, 4, 5, 6]

        for unit_code in supported_units:
            precision, gap_bridge = get_snap_tolerances(
                unit_code, None, False, None, precision_fix_enabled=False
            )

            assert precision == 0.0, (
                f"Unit {unit_code} should have 0.0 precision when disabled"
            )

    def test_precision_fix_enabled_with_all_units(self) -> None:
        """When precision_fix_enabled=True, should return correct tolerance for all units.

        Uses DEFAULT_PRECISION_FIX_TOLERANCE which has practical CAD-scale tolerances.
        """
        supported_units = [0, 1, 2, 4, 5, 6]

        for unit_code in supported_units:
            precision, gap_bridge = get_snap_tolerances(
                unit_code, None, False, None, precision_fix_enabled=True
            )

            # Now uses DEFAULT_PRECISION_FIX_TOLERANCE
            expected = DEFAULT_PRECISION_FIX_TOLERANCE[unit_code]
            assert precision == expected, (
                f"Unit {unit_code} should have {expected} precision when enabled"
            )
            assert precision > 0.0


class TestPrecisionFixGapBridgeInteraction:
    """Tests for interaction between precision_fix_enabled and gap_bridge_enabled."""

    def test_both_disabled(self) -> None:
        """Both precision fix and gap bridge disabled should return (0.0, 0.0)."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        assert precision == 0.0
        assert gap_bridge == 0.0

    def test_precision_fix_disabled_gap_bridge_enabled(self) -> None:
        """Precision fix disabled, gap bridge enabled should return (0.0, gap_bridge_value)."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = None  # Use default

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        # Precision should be 0.0 when disabled
        assert precision == 0.0
        # Gap bridge should use default for mm
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[4]
        assert gap_bridge > 0.0

    def test_precision_fix_enabled_gap_bridge_disabled(self) -> None:
        """Precision fix enabled, gap bridge disabled should return (precision_value, 0.0)."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Precision should use mm tolerance from DEFAULT_PRECISION_FIX_TOLERANCE
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]
        assert precision > 0.0
        # Gap bridge should be 0.0 when disabled
        assert gap_bridge == 0.0

    def test_both_enabled_default_case(self) -> None:
        """Both enabled should return (precision_value, gap_bridge_value) - default case."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = None  # Use default

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Both should have positive values
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]
        assert precision > 0.0
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[4]
        assert gap_bridge > 0.0

    def test_precision_fix_disabled_custom_gap_bridge_amount(self) -> None:
        """Precision fix disabled with custom gap bridge amount."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 2.5  # Custom amount

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        assert precision == 0.0
        assert gap_bridge == 2.5

    def test_both_parameters_independent_inches(self) -> None:
        """Verify both parameters work independently for inches."""
        detected_units = 1  # Inches
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 0.05

        # Test with precision fix enabled
        precision_on, gap_on = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Test with precision fix disabled
        precision_off, gap_off = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        # Precision should differ based on enabled/disabled
        assert precision_on == DEFAULT_PRECISION_FIX_TOLERANCE[1]
        assert precision_off == 0.0

        # Gap bridge should be the same regardless of precision fix setting
        assert gap_on == gap_off == 0.05


class TestPrecisionFixWithUnitOverride:
    """Tests for precision_fix_enabled with unit override settings."""

    def test_precision_fix_disabled_with_override(self) -> None:
        """Precision fix disabled should return 0.0 even with unit override."""
        detected_units = 4  # Millimeters
        override_units = 6  # Override to Meters
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        # Should still be 0.0 even with override
        assert precision == 0.0
        assert gap_bridge == 0.0

    def test_precision_fix_enabled_with_override(self) -> None:
        """Precision fix enabled with unit override should use override unit tolerance."""
        detected_units = 4  # Millimeters
        override_units = 6  # Override to Meters
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Should use meter tolerance (override), not mm
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[6]
        assert precision != DEFAULT_PRECISION_FIX_TOLERANCE[4]

    def test_precision_fix_disabled_override_minus_one(self) -> None:
        """Precision fix disabled with -1 override (auto) should return 0.0."""
        detected_units = 4  # Millimeters
        override_units = -1  # Auto-detect
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        assert precision == 0.0


class TestPrecisionFixUnknownUnits:
    """Tests for precision_fix_enabled with unknown unit codes."""

    def test_precision_fix_disabled_unknown_unit(self) -> None:
        """Precision fix disabled with unknown unit should return 0.0."""
        detected_units = 99  # Unknown unit code
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        assert precision == 0.0
        assert gap_bridge == 0.0

    def test_precision_fix_enabled_unknown_unit_uses_fallback(self) -> None:
        """Precision fix enabled with unknown unit should use fallback tolerance.

        When unit code is unknown, falls back to DEFAULT_PRECISION_FIX_TOLERANCE[0]
        (unitless default of 0.01).
        """
        detected_units = 99  # Unknown unit code
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Should use unitless fallback from DEFAULT_PRECISION_FIX_TOLERANCE
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[0]
        assert precision > 0.0


class TestExtractBlocksPrecisionFixParameter:
    """Tests for extract_blocks() accepting precision_fix_enabled parameter."""

    def test_extract_blocks_accepts_precision_fix_enabled_true(self) -> None:
        """Verify extract_blocks accepts precision_fix_enabled=True without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf), precision_fix_enabled=True)

        assert "block_counts" in result
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_accepts_precision_fix_enabled_false(self) -> None:
        """Verify extract_blocks accepts precision_fix_enabled=False without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf), precision_fix_enabled=False)

        assert "block_counts" in result
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_default_precision_fix_works(self) -> None:
        """Verify extract_blocks works without precision_fix_enabled (default=True)."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should work exactly as before with no precision_fix_enabled parameter
        result = extract_blocks(str(sample_dxf))

        assert "block_counts" in result
        assert "block_content_zone_data" in result

    def test_extract_blocks_with_all_new_parameters(self) -> None:
        """Verify extract_blocks works with all tolerance parameters including precision_fix."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=4,  # Millimeters
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
            precision_fix_enabled=True,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)

    def test_extract_blocks_precision_fix_disabled_with_gap_bridge(self) -> None:
        """Verify extract_blocks works with precision_fix disabled and gap_bridge enabled."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            gap_bridge_enabled=True,
            gap_bridge_amount=0.5,
            precision_fix_enabled=False,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)


class TestExtractBlocksPrecisionFixEdgeCases:
    """Edge case tests for extract_blocks() with precision_fix_enabled."""

    def test_empty_file_with_precision_fix_disabled(self) -> None:
        """Verify extraction works on empty DXF file with precision_fix disabled."""
        empty_dxf = ASSETS_DIR / "empty_drawing.dxf"

        result = extract_blocks(
            str(empty_dxf),
            precision_fix_enabled=False,
        )

        assert result is not None
        assert result["block_counts"] == {}

    def test_empty_file_with_all_params_disabled(self) -> None:
        """Verify extraction works on empty DXF with both precision_fix and gap_bridge disabled."""
        empty_dxf = ASSETS_DIR / "empty_drawing.dxf"

        result = extract_blocks(
            str(empty_dxf),
            gap_bridge_enabled=False,
            precision_fix_enabled=False,
        )

        assert result is not None
        assert result["block_counts"] == {}

    def test_precision_fix_results_consistency(self) -> None:
        """Results should be consistent regardless of precision_fix_enabled setting."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Block counts should be the same regardless of precision_fix setting
        # (precision_fix affects polygon detection, not block counting)
        result_enabled = extract_blocks(str(sample_dxf), precision_fix_enabled=True)
        result_disabled = extract_blocks(str(sample_dxf), precision_fix_enabled=False)

        # Block counts should be identical
        assert result_enabled["block_counts"] == result_disabled["block_counts"]


class TestPrecisionFixAmountParameter:
    """Tests for precision_fix_amount parameter in get_snap_tolerances().

    The precision_fix_amount parameter allows users to specify a custom precision
    tolerance value instead of using the default from DEFAULT_PRECISION_FIX_TOLERANCE.
    """

    def test_custom_amount_used_when_provided_and_positive(self) -> None:
        """When precision_fix_amount is provided and > 0, that value is used."""
        detected_units = 4  # Millimeters
        custom_amount = 0.05  # 5x the default mm tolerance

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=custom_amount,
        )

        # Should use custom amount, not default
        assert precision == custom_amount
        assert precision != DEFAULT_PRECISION_FIX_TOLERANCE[4]

    def test_default_used_when_amount_is_none(self) -> None:
        """When precision_fix_amount is None, use default from DEFAULT_PRECISION_FIX_TOLERANCE."""
        detected_units = 4  # Millimeters

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=None,
        )

        # Should use default tolerance
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]

    def test_default_used_when_amount_is_zero(self) -> None:
        """When precision_fix_amount is 0.0, use default from DEFAULT_PRECISION_FIX_TOLERANCE."""
        detected_units = 4  # Millimeters

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=0.0,
        )

        # Should use default tolerance (0.0 is treated as "use default")
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]

    def test_default_used_when_amount_is_negative(self) -> None:
        """When precision_fix_amount is negative, use default from DEFAULT_PRECISION_FIX_TOLERANCE."""
        detected_units = 4  # Millimeters

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=-1.0,
        )

        # Should use default tolerance (negative is treated as "use default")
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]

    def test_custom_amount_with_all_unit_types(self) -> None:
        """Custom amount should work regardless of unit type (bypasses unit-specific default)."""
        supported_units = [0, 1, 2, 4, 5, 6]
        custom_amount = 0.123

        for unit_code in supported_units:
            precision, _ = get_snap_tolerances(
                unit_code,
                None,
                False,
                None,
                precision_fix_enabled=True,
                precision_fix_amount=custom_amount,
            )

            # All should use the same custom amount regardless of unit
            assert precision == custom_amount, (
                f"Unit {unit_code} should use custom amount {custom_amount}"
            )

    def test_custom_amount_with_unit_override(self) -> None:
        """Custom amount should be used even with unit override specified."""
        detected_units = 4  # Millimeters
        override_units = 6  # Override to Meters
        custom_amount = 0.02

        precision, _ = get_snap_tolerances(
            detected_units,
            override_units,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=custom_amount,
        )

        # Should use custom amount, not meter default
        assert precision == custom_amount
        assert precision != DEFAULT_PRECISION_FIX_TOLERANCE[6]

    def test_custom_amount_ignored_when_precision_fix_disabled(self) -> None:
        """When precision_fix_enabled=False, custom amount is ignored and 0.0 is returned."""
        detected_units = 4  # Millimeters
        custom_amount = 0.05

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=False,
            precision_fix_amount=custom_amount,
        )

        # Should return 0.0 when disabled, ignoring custom amount
        assert precision == 0.0
        assert precision != custom_amount

    def test_small_custom_amount(self) -> None:
        """Very small custom amounts should work correctly."""
        detected_units = 4  # Millimeters
        custom_amount = 1e-9  # Very small

        precision, _ = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=custom_amount,
        )

        assert precision == custom_amount

    def test_large_custom_amount(self) -> None:
        """Large custom amounts should work correctly."""
        detected_units = 4  # Millimeters
        custom_amount = 5.0  # Large (within PRECISION_FIX_MAX)

        precision, _ = get_snap_tolerances(
            detected_units,
            None,
            False,
            None,
            precision_fix_enabled=True,
            precision_fix_amount=custom_amount,
        )

        assert precision == custom_amount

    def test_custom_precision_with_custom_gap_bridge(self) -> None:
        """Both custom precision_fix_amount and gap_bridge_amount should work together."""
        detected_units = 4  # Millimeters
        custom_precision = 0.025
        custom_gap = 1.5

        precision, gap_bridge = get_snap_tolerances(
            detected_units,
            None,
            True,  # gap_bridge_enabled
            custom_gap,
            precision_fix_enabled=True,
            precision_fix_amount=custom_precision,
        )

        # Both should use custom values
        assert precision == custom_precision
        assert gap_bridge == custom_gap

    def test_backward_compatibility_no_precision_fix_amount_param(self) -> None:
        """Function should work without precision_fix_amount parameter (backward compatible)."""
        detected_units = 4  # Millimeters

        # Call without precision_fix_amount
        precision, gap_bridge = get_snap_tolerances(
            detected_units, None, False, None, precision_fix_enabled=True
        )

        # Should use default from DEFAULT_PRECISION_FIX_TOLERANCE
        assert precision == DEFAULT_PRECISION_FIX_TOLERANCE[4]
        assert precision > 0.0


class TestExtractBlocksPrecisionFixAmount:
    """Tests for extract_blocks() accepting precision_fix_amount parameter.

    These tests verify that the precision_fix_amount parameter is correctly
    accepted by extract_blocks() and passed through to get_snap_tolerances().
    """

    def test_extract_blocks_accepts_precision_fix_amount_parameter(self) -> None:
        """Verify extract_blocks accepts precision_fix_amount parameter without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf), precision_fix_amount=0.05)

        assert "block_counts" in result
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_with_custom_precision_fix_amount(self) -> None:
        """Verify extract_blocks accepts a custom precision_fix_amount value."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=0.025,  # Custom amount
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)

    def test_extract_blocks_with_precision_fix_amount_none(self) -> None:
        """Verify extract_blocks with precision_fix_amount=None uses default."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=None,  # Should use default
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_with_precision_fix_amount_zero(self) -> None:
        """Verify extract_blocks with precision_fix_amount=0 uses default."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=0.0,  # Should use default
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_with_all_tolerance_parameters(self) -> None:
        """Verify extract_blocks works with all tolerance parameters including precision_fix_amount."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=4,  # Millimeters
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
            precision_fix_enabled=True,
            precision_fix_amount=0.03,  # Custom precision amount
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)


class TestPrecisionFixAmountIntegration:
    """Integration tests for precision_fix_amount parameter.

    These tests verify that precision_fix_amount works correctly with
    other extraction parameters and maintains backward compatibility.
    """

    def test_precision_fix_amount_with_unit_override(self) -> None:
        """Verify custom precision_fix_amount works with unit override."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=1,  # Override to inches
            precision_fix_enabled=True,
            precision_fix_amount=0.001,  # Custom amount for inches
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_with_gap_bridge(self) -> None:
        """Verify custom precision_fix_amount works with gap bridging enabled."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            gap_bridge_enabled=True,
            gap_bridge_amount=0.5,
            precision_fix_enabled=True,
            precision_fix_amount=0.02,  # Custom precision amount
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_disabled_ignores_amount(self) -> None:
        """Verify that precision_fix_enabled=False ignores precision_fix_amount."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # When precision_fix_enabled=False, the amount should be ignored
        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=False,
            precision_fix_amount=0.05,  # This should be ignored
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_backward_compatibility(self) -> None:
        """Verify calling extract_blocks without precision_fix_amount still works."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Call without precision_fix_amount parameter (backward compatible)
        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)

    def test_precision_fix_amount_very_small_value(self) -> None:
        """Verify extraction works with very small precision_fix_amount."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=1e-9,  # Very small value
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_large_value(self) -> None:
        """Verify extraction works with large precision_fix_amount."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=5.0,  # Large value (within PRECISION_FIX_MAX)
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_unknown_unit_uses_custom_amount(self) -> None:
        """Verify custom precision_fix_amount is used even with unknown unit code."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # When unit is unknown but custom amount is provided, use custom amount
        result = extract_blocks(
            str(sample_dxf),
            unit_override=99,  # Unknown unit code
            precision_fix_enabled=True,
            precision_fix_amount=0.05,  # Custom amount should be used
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_precision_fix_amount_results_consistency(self) -> None:
        """Block counts should be consistent regardless of precision_fix_amount.

        The precision_fix_amount affects polygon detection tolerance, not block counting.
        Block counts should be identical regardless of the precision amount used.
        """
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result_default = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=None,  # Default
        )

        result_custom = extract_blocks(
            str(sample_dxf),
            precision_fix_enabled=True,
            precision_fix_amount=0.05,  # Custom
        )

        # Block counts should be identical
        assert result_default["block_counts"] == result_custom["block_counts"]
