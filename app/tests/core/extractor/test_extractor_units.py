"""
Tests for unit detection and tolerance calculation functions.

Tests cover:
- _get_drawing_units() function for reading $INSUNITS from DXF header
- get_snap_tolerances() function for calculating appropriate tolerances
"""

from unittest.mock import MagicMock

from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_PRECISION_SNAP_TOLERANCE,
    PRECISION_SNAP_TOLERANCE,
)
from core.extractor import _get_drawing_units, get_snap_tolerances


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
    """Tests for get_snap_tolerances function."""

    def test_auto_detect_uses_detected_units(self) -> None:
        """When override is None, should use detected units for tolerance calculation."""
        detected_units = 4  # Millimeters
        override_units = None
        gap_bridge_enabled = False
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use mm tolerance
        assert precision == PRECISION_SNAP_TOLERANCE[4]
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

        # Should use mm tolerance (detected)
        assert precision == PRECISION_SNAP_TOLERANCE[4]
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

        # Should use meter tolerance (override)
        assert precision == PRECISION_SNAP_TOLERANCE[6]
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

        # Should use mm default gap bridge tolerance
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[4]

    def test_gap_bridge_enabled_default_zero_amount(self) -> None:
        """When gap bridging enabled with amount=0, should use default for unit."""
        detected_units = 1  # Inches
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = 0.0  # Zero should trigger default

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use inch default gap bridge tolerance
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[1]

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

        # Should use mm default gap bridge tolerance
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[4]

    def test_unknown_unit_uses_fallback_tolerance(self) -> None:
        """When unit code is unknown, should use fallback tolerances."""
        detected_units = 99  # Unknown unit code
        override_units = None
        gap_bridge_enabled = True
        gap_bridge_amount = None

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use default fallback tolerance
        assert precision == DEFAULT_PRECISION_SNAP_TOLERANCE
        # Should use unitless (0) default for gap bridge
        assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[0]

    def test_all_supported_units_have_tolerances(self) -> None:
        """All supported unit codes should return valid tolerances."""
        supported_units = [0, 1, 2, 4, 5, 6]

        for unit_code in supported_units:
            precision, gap_bridge = get_snap_tolerances(
                unit_code, None, True, None
            )

            assert precision > 0, f"Unit {unit_code} should have positive precision tolerance"
            assert gap_bridge > 0, f"Unit {unit_code} should have positive gap bridge default"
            assert precision == PRECISION_SNAP_TOLERANCE[unit_code]
            assert gap_bridge == DEFAULT_GAP_BRIDGE_TOLERANCE[unit_code]

    def test_override_with_gap_bridge_custom_amount(self) -> None:
        """Override units with custom gap bridge amount should use both overrides."""
        detected_units = 4  # Millimeters
        override_units = 1  # Inches
        gap_bridge_enabled = True
        gap_bridge_amount = 0.05  # Custom inch amount

        precision, gap_bridge = get_snap_tolerances(
            detected_units, override_units, gap_bridge_enabled, gap_bridge_amount
        )

        # Should use inch precision tolerance
        assert precision == PRECISION_SNAP_TOLERANCE[1]
        # Should use custom amount
        assert gap_bridge == 0.05
