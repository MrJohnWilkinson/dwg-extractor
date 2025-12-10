"""
Tests for constants module - Content Zone Detection Thresholds and Drawing Unit Configuration.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
- Drawing unit configuration constants
"""

from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_PRECISION_SNAP_TOLERANCE,
    DXF_INSUNITS_MAP,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    GAP_BRIDGE_MAX,
    GAP_BRIDGE_MIN,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
    PRECISION_SNAP_TOLERANCE,
    UNIT_SELECTION_OPTIONS,
)


class TestContentZoneThresholds:
    """Tests for content zone detection threshold constants."""

    def test_polygon_threshold_reasonable(self) -> None:
        """Threshold should be between 10 and 1000.

        With Shapely's efficient GEOS-based operations, the threshold can be
        much higher than the original O(n^3) implementation. 500 is conservative.
        """
        assert 10 <= POLYGON_COUNT_THRESHOLD <= 1000

    def test_line_threshold_reasonable(self) -> None:
        """Threshold should be between 1000 and 10000.

        With Shapely's efficient GEOS-based polygonize(), the threshold can be
        much higher than the original DFS implementation. 5000 is conservative.
        """
        assert 1000 <= LINE_SEGMENT_THRESHOLD <= 10000


class TestContentZoneExcelColumns:
    """Tests for content zone Excel column constants."""

    def test_content_zone_excel_columns_follow_naming_convention(self) -> None:
        """All content zone columns should start with 'block_' prefix."""
        content_zone_columns = [
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
            EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
        ]

        for column in content_zone_columns:
            assert column.startswith("block_"), (
                f"Column '{column}' does not follow naming convention"
            )


class TestDrawingUnitConstants:
    """Tests for drawing unit configuration constants."""

    def test_dxf_insunits_map_has_all_supported_units(self) -> None:
        """DXF_INSUNITS_MAP should have all supported unit codes.

        Supported codes: 0 (Unitless), 1 (Inches), 2 (Feet), 4 (MM), 5 (CM), 6 (M).
        Note: Code 3 (Miles) is intentionally not supported.
        """
        expected_codes = {0, 1, 2, 4, 5, 6}
        actual_codes = set(DXF_INSUNITS_MAP.keys())
        assert actual_codes == expected_codes, (
            f"Expected codes {expected_codes}, got {actual_codes}"
        )
        # Verify all values are non-empty strings
        for code, name in DXF_INSUNITS_MAP.items():
            assert isinstance(name, str) and len(name) > 0, (
                f"Unit code {code} has invalid name: {name!r}"
            )

    def test_unit_selection_options_keys_match_display_labels(self) -> None:
        """UNIT_SELECTION_OPTIONS keys should be valid display labels (strings)."""
        expected_labels = {"DXF/DWG", "MM", "CM", "M", "IN", "FT"}
        actual_labels = set(UNIT_SELECTION_OPTIONS.keys())
        assert actual_labels == expected_labels, (
            f"Expected labels {expected_labels}, got {actual_labels}"
        )
        # Verify all values are integers
        for label, code in UNIT_SELECTION_OPTIONS.items():
            assert isinstance(code, int), (
                f"Label '{label}' has non-integer code: {code!r}"
            )
        # Verify DXF/DWG maps to -1 (auto-detect)
        assert UNIT_SELECTION_OPTIONS["DXF/DWG"] == -1, (
            "DXF/DWG should map to -1 for auto-detect"
        )

    def test_precision_snap_tolerances_in_reasonable_range(self) -> None:
        """Precision snap tolerances should be between 1e-9 and 1e-3.

        Stage 1 tolerances are extremely small to only fix floating-point artifacts.
        """
        for code, tolerance in PRECISION_SNAP_TOLERANCE.items():
            assert 1e-9 <= tolerance <= 1e-3, (
                f"Precision tolerance for code {code} is {tolerance}, "
                "expected between 1e-9 and 1e-3"
            )
        # Verify default is also in range
        assert 1e-9 <= DEFAULT_PRECISION_SNAP_TOLERANCE <= 1e-3, (
            f"Default precision tolerance {DEFAULT_PRECISION_SNAP_TOLERANCE} out of range"
        )

    def test_gap_bridge_tolerances_in_reasonable_range(self) -> None:
        """Gap bridge tolerances should be between 0.001 and 1000.

        Stage 2 tolerances represent typical small gaps in CAD drawings.
        """
        for code, tolerance in DEFAULT_GAP_BRIDGE_TOLERANCE.items():
            assert 0.001 <= tolerance <= 1000, (
                f"Gap bridge tolerance for code {code} is {tolerance}, "
                "expected between 0.001 and 1000"
            )

    def test_gap_bridge_constraints_valid(self) -> None:
        """GAP_BRIDGE_MIN should be less than GAP_BRIDGE_MAX."""
        assert GAP_BRIDGE_MIN < GAP_BRIDGE_MAX, (
            f"GAP_BRIDGE_MIN ({GAP_BRIDGE_MIN}) must be < GAP_BRIDGE_MAX ({GAP_BRIDGE_MAX})"
        )
        assert GAP_BRIDGE_MIN >= 0.0, "GAP_BRIDGE_MIN must be non-negative"
        assert GAP_BRIDGE_MAX > 0.0, "GAP_BRIDGE_MAX must be positive"
