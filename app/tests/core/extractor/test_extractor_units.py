"""
Tests for unit detection and tolerance calculation functions.

Tests cover:
- _get_drawing_units() function for reading $INSUNITS from DXF header
- get_snap_tolerances() function for calculating appropriate tolerances
- extract_blocks() tolerance parameter passing
"""

from pathlib import Path
from unittest.mock import MagicMock

from core.constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
)
from core.extractor import _get_drawing_units, extract_blocks, get_snap_tolerances


# Test assets directory
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


class TestGetDrawingUnits:
    """Tests for _get_drawing_units function."""

    def test_detects_mm_units(self) -> None:
        """Should detect millimeter units (code 4) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 4

        result = _get_drawing_units(mock_doc)

        assert result == 4
        mock_doc.header.get.assert_called_once_with("$INSUNITS", 0)

    def test_detects_inch_units(self) -> None:
        """Should detect inch units (code 1) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 1

        result = _get_drawing_units(mock_doc)

        assert result == 1
        mock_doc.header.get.assert_called_once_with("$INSUNITS", 0)

    def test_detects_meter_units(self) -> None:
        """Should detect meter units (code 6) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 6

        result = _get_drawing_units(mock_doc)

        assert result == 6
        mock_doc.header.get.assert_called_once_with("$INSUNITS", 0)

    def test_detects_feet_units(self) -> None:
        """Should detect feet units (code 2) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 2

        result = _get_drawing_units(mock_doc)

        assert result == 2

    def test_detects_cm_units(self) -> None:
        """Should detect centimeter units (code 5) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 5

        result = _get_drawing_units(mock_doc)

        assert result == 5

    def test_detects_unitless(self) -> None:
        """Should detect unitless (code 0) from $INSUNITS header."""
        mock_doc = MagicMock()
        mock_doc.header.get.return_value = 0

        result = _get_drawing_units(mock_doc)

        assert result == 0

    def test_missing_insunits_returns_zero(self) -> None:
        """Should return 0 when $INSUNITS header is missing (KeyError)."""
        mock_doc = MagicMock()
        mock_doc.header.get.side_effect = KeyError("$INSUNITS")

        result = _get_drawing_units(mock_doc)

        assert result == 0

    def test_invalid_header_returns_zero(self) -> None:
        """Should return 0 when header attribute raises AttributeError."""
        # Create a mock where accessing .header raises AttributeError
        mock_doc = MagicMock(spec=[])  # Empty spec means no attributes
        # Make header property raise AttributeError when accessed
        mock_doc.configure_mock(**{"header": MagicMock()})
        mock_doc.header.get.side_effect = AttributeError("header.get not available")

        result = _get_drawing_units(mock_doc)

        assert result == 0

    def test_header_get_raises_attribute_error_returns_zero(self) -> None:
        """Should return 0 when header.get raises AttributeError."""
        mock_doc = MagicMock()
        mock_doc.header.get.side_effect = AttributeError("get not callable")

        result = _get_drawing_units(mock_doc)

        assert result == 0


class TestGetSnapTolerances:
    """Tests for get_snap_tolerances function.

    NOTE: These tests now use DEFAULT_GAP_CLOSURE_TOLERANCE (shared for both
    Precision Fix and Gap Bridge). The function now uses the shared tolerance
    values (3mm base) for consistent gap closure behavior.
    """

    def test_auto_detect_uses_detected_units(self) -> None:
        """When override is None, should use detected units for tolerance calculation.

        Uses DEFAULT_GAP_CLOSURE_TOLERANCE which has practical CAD-scale tolerances.
        """
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use mm tolerance from DEFAULT_GAP_CLOSURE_TOLERANCE
        assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[4]
        assert gap_bridge == 0.0

    def test_override_minus_one_uses_detected_units(self) -> None:
        """When override is -1 (DXF/DWG auto), should use detected units."""
        detected_units = 4  # Millimeters
        override_units = -1  # Auto-detect
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use mm tolerance (detected) from DEFAULT_GAP_CLOSURE_TOLERANCE
        assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[4]
        assert gap_bridge == 0.0

    def test_override_replaces_detected_units(self) -> None:
        """When override is specified, should use override unit for tolerance."""
        detected_units = 4  # Millimeters
        override_units = 6  # Meters
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use meter tolerance (override) from DEFAULT_GAP_CLOSURE_TOLERANCE
        assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[6]
        assert gap_bridge == 0.0

    def test_gap_bridge_disabled_returns_zero(self) -> None:
        """When gap bridging is disabled, gap_bridge_tolerance should be 0.0."""
        detected_units = 4
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = 50.0  # Should be ignored

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        assert gap_bridge == 0.0

    def test_gap_bridge_enabled_uses_default(self) -> None:
        """When gap bridging enabled without custom amount, should use default for unit."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = None  # Use default

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use mm default gap closure tolerance
        assert gap_bridge == DEFAULT_GAP_CLOSURE_TOLERANCE[4]

    def test_gap_bridge_enabled_default_zero_amount(self) -> None:
        """When gap bridging enabled with amount=0, should use default for unit."""
        detected_units = 1  # Inches
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 0.0  # Zero should trigger default

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use inch default gap closure tolerance
        assert gap_bridge == DEFAULT_GAP_CLOSURE_TOLERANCE[1]

    def test_gap_bridge_custom_amount_used(self) -> None:
        """When gap bridging enabled with custom amount, should use custom amount."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 50.0  # Custom amount

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        assert gap_bridge == 50.0

    def test_gap_bridge_negative_amount_uses_default(self) -> None:
        """When gap bridging enabled with negative amount, should use default."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = -5.0  # Negative should trigger default

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use mm default gap closure tolerance
        assert gap_bridge == DEFAULT_GAP_CLOSURE_TOLERANCE[4]

    def test_unknown_unit_uses_fallback_tolerance(self) -> None:
        """When unit code is unknown, should use fallback tolerances.

        Falls back to DEFAULT_GAP_CLOSURE_TOLERANCE[0] (unitless default of 3.0).
        """
        detected_units = 99  # Unknown unit code
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use unitless fallback from DEFAULT_GAP_CLOSURE_TOLERANCE
        assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[0]
        # Should use unitless (0) default for gap closure
        assert gap_bridge == DEFAULT_GAP_CLOSURE_TOLERANCE[0]

    def test_all_supported_units_have_tolerances(self) -> None:
        """All supported unit codes should return valid tolerances.

        Uses DEFAULT_GAP_CLOSURE_TOLERANCE which has practical CAD-scale tolerances.
        """
        supported_units = [0, 1, 2, 4, 5, 6]

        for unit_code in supported_units:
            precision, gap_bridge = get_snap_tolerances(unit_code, None, True, None)

            assert precision > 0, (
                f"Unit {unit_code} should have positive precision tolerance"
            )
            assert gap_bridge > 0, (
                f"Unit {unit_code} should have positive gap bridge default"
            )
            assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[unit_code]
            assert gap_bridge == DEFAULT_GAP_CLOSURE_TOLERANCE[unit_code]

    def test_override_with_gap_bridge_custom_amount(self) -> None:
        """Override units with custom gap bridge amount should use both overrides."""
        detected_units = 4  # Millimeters
        override_units = 1  # Inches
        gap_bridge_enabled = True
        gap_bridge_amount = 0.05  # Custom inch amount

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use inch precision tolerance from DEFAULT_GAP_CLOSURE_TOLERANCE
        assert precision == DEFAULT_GAP_CLOSURE_TOLERANCE[1]
        # Should use custom amount
        assert gap_bridge == 0.05


class TestExtractBlocksToleranceParameters:
    """Tests for extract_blocks() tolerance parameter acceptance."""

    def test_extract_blocks_accepts_unit_override_parameter(self) -> None:
        """Verify extract_blocks accepts unit_override parameter without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should not raise any exception
        result = extract_blocks(str(sample_dxf), unit_override=4)

        assert "block_counts" in result

    def test_extract_blocks_accepts_gap_bridge_enabled_parameter(self) -> None:
        """Verify extract_blocks accepts gap_bridge_enabled parameter without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should not raise any exception
        result = extract_blocks(str(sample_dxf), gap_bridge_enabled=True)

        assert "block_counts" in result

    def test_extract_blocks_accepts_gap_bridge_amount_parameter(self) -> None:
        """Verify extract_blocks accepts gap_bridge_amount parameter without error."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should not raise any exception
        result = extract_blocks(str(sample_dxf), gap_bridge_amount=1.0)

        assert "block_counts" in result

    def test_extract_blocks_default_parameters_work(self) -> None:
        """Verify extract_blocks works without new parameters (backward compatibility)."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should work exactly as before with no new parameters
        result = extract_blocks(str(sample_dxf))

        assert "block_counts" in result
        assert "block_content_zone_data" in result


class TestExtractBlocksToleranceIntegration:
    """Integration tests for extract_blocks() tolerance parameter propagation."""

    def test_extract_blocks_with_unit_override(self) -> None:
        """Call extract_blocks with unit_override=4 (mm), verify no errors."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf), unit_override=4)

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)

    def test_extract_blocks_with_gap_bridge_enabled(self) -> None:
        """Call extract_blocks with gap_bridge_enabled=True, verify no errors."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(str(sample_dxf), gap_bridge_enabled=True)

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_with_custom_gap_amount(self) -> None:
        """Call extract_blocks with gap_bridge_amount=1.0, verify no errors."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf), gap_bridge_enabled=True, gap_bridge_amount=1.0
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_with_all_tolerance_params(self) -> None:
        """Call extract_blocks with all three new params set."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        result = extract_blocks(
            str(sample_dxf),
            unit_override=1,  # Inches
            gap_bridge_enabled=True,
            gap_bridge_amount=0.05,
        )

        assert result is not None
        assert isinstance(result["block_counts"], dict)
        assert isinstance(result["block_content_zone_data"], dict)


class TestExtractBlocksToleranceEdgeCases:
    """Edge case tests for extract_blocks() tolerance parameters."""

    def test_extract_blocks_unit_override_minus_one_uses_auto(self) -> None:
        """Verify -1 behaves like None (auto-detect)."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Both should produce the same results
        result_auto = extract_blocks(str(sample_dxf), unit_override=None)
        result_minus_one = extract_blocks(str(sample_dxf), unit_override=-1)

        # Results should be equivalent (same block counts)
        assert result_auto["block_counts"] == result_minus_one["block_counts"]

    def test_extract_blocks_gap_bridge_disabled_ignores_amount(self) -> None:
        """Verify amount is ignored when gap bridging is disabled."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # These should produce equivalent results since gap bridging is disabled
        result_no_amount = extract_blocks(
            str(sample_dxf), gap_bridge_enabled=False, gap_bridge_amount=None
        )
        result_with_amount = extract_blocks(
            str(sample_dxf), gap_bridge_enabled=False, gap_bridge_amount=100.0
        )

        # Block counts should be the same regardless of amount when disabled
        assert result_no_amount["block_counts"] == result_with_amount["block_counts"]

    def test_extract_blocks_invalid_unit_uses_fallback(self) -> None:
        """Test with unsupported unit code (99) - should use fallback tolerance."""
        sample_dxf = ASSETS_DIR / "sample_drawing.dxf"

        # Should not raise an exception with unknown unit code
        result = extract_blocks(str(sample_dxf), unit_override=99)

        assert result is not None
        assert isinstance(result["block_counts"], dict)

    def test_extract_blocks_empty_file_with_tolerance_params(self) -> None:
        """Verify extraction works on empty DXF file with tolerance parameters."""
        empty_dxf = ASSETS_DIR / "empty_drawing.dxf"

        result = extract_blocks(
            str(empty_dxf),
            unit_override=4,
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
        )

        assert result is not None
        # Empty file should have empty block counts
        assert result["block_counts"] == {}


class TestGetSnapTolerancesIndependence:
    """Tests verifying precision_fix_enabled and gap_bridge_enabled are independent."""

    def test_gap_bridge_unaffected_by_precision_fix_enabled(self) -> None:
        """Gap bridge tolerance should be the same regardless of precision_fix setting."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 2.0

        # Test with precision fix enabled
        _, gap_on = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=True,
        )

        # Test with precision fix disabled
        _, gap_off = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled,
            gap_bridge_amount,
            precision_fix_enabled=False,
        )

        # Gap bridge should be identical regardless of precision_fix setting
        assert gap_on == gap_off == 2.0

    def test_precision_fix_unaffected_by_gap_bridge_enabled(self) -> None:
        """Precision tolerance should be the same regardless of gap_bridge setting.

        Uses DEFAULT_GAP_CLOSURE_TOLERANCE which has practical CAD-scale tolerances.
        """
        detected_units = 4  # Millimeters
        override_units = None

        # Test with gap bridge enabled
        precision_on, _ = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled=True,
            gap_bridge_amount=1.0,
            precision_fix_enabled=True,
        )

        # Test with gap bridge disabled
        precision_off, _ = get_snap_tolerances(
            detected_units,
            override_units,
            gap_bridge_enabled=False,
            gap_bridge_amount=None,
            precision_fix_enabled=True,
        )

        # Precision tolerance should be identical regardless of gap_bridge setting
        assert precision_on == precision_off == DEFAULT_GAP_CLOSURE_TOLERANCE[4]

    def test_all_four_combinations(self) -> None:
        """Test all four combinations of precision_fix and gap_bridge settings.

        Uses DEFAULT_GAP_CLOSURE_TOLERANCE which has practical CAD-scale tolerances.
        """
        detected_units = 1  # Inches
        override_units = None
        custom_gap = 0.05

        # Both disabled
        p1, g1 = get_snap_tolerances(
            detected_units, override_units, False, None, precision_fix_enabled=False
        )
        assert p1 == 0.0
        assert g1 == 0.0

        # Precision only
        p2, g2 = get_snap_tolerances(
            detected_units, override_units, False, None, precision_fix_enabled=True
        )
        assert p2 == DEFAULT_GAP_CLOSURE_TOLERANCE[1]
        assert g2 == 0.0

        # Gap bridge only
        p3, g3 = get_snap_tolerances(
            detected_units,
            override_units,
            True,
            custom_gap,
            precision_fix_enabled=False,
        )
        assert p3 == 0.0
        assert g3 == custom_gap

        # Both enabled
        p4, g4 = get_snap_tolerances(
            detected_units, override_units, True, custom_gap, precision_fix_enabled=True
        )
        assert p4 == DEFAULT_GAP_CLOSURE_TOLERANCE[1]
        assert g4 == custom_gap
