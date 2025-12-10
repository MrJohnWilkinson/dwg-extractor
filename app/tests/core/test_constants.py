"""
Tests for constants module - Content Zone Detection Thresholds and Drawing Unit Configuration.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
- Drawing unit configuration constants
"""

from core.constants import (
    DEFAULT_GAP_BRIDGE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    DEFAULT_PRECISION_FIX_TOLERANCE,
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
    MIN_AREA_FILTER_MAX,
    MIN_AREA_FILTER_MIN,
    MIN_SIDE_FILTER_MAX,
    MIN_SIDE_FILTER_MIN,
    POLYGON_COUNT_THRESHOLD,
    PRECISION_FIX_MAX,
    PRECISION_FIX_MIN,
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


class TestPrecisionFixToleranceConstants:
    """Tests for user-configurable precision fix tolerance constants."""

    def test_default_precision_fix_tolerance_has_all_supported_units(self) -> None:
        """DEFAULT_PRECISION_FIX_TOLERANCE should have all supported unit codes.

        Supported codes: 0 (Unitless), 1 (Inches), 2 (Feet), 4 (MM), 5 (CM), 6 (M).
        """
        expected_codes = {0, 1, 2, 4, 5, 6}
        actual_codes = set(DEFAULT_PRECISION_FIX_TOLERANCE.keys())
        assert actual_codes == expected_codes, (
            f"Expected codes {expected_codes}, got {actual_codes}"
        )

    def test_default_precision_fix_tolerance_values_in_reasonable_range(self) -> None:
        """DEFAULT_PRECISION_FIX_TOLERANCE values should be between 1e-6 and 1.0.

        These are practical CAD tolerances, larger than PRECISION_SNAP_TOLERANCE
        but still small enough to not merge distinct geometry.
        """
        for code, tolerance in DEFAULT_PRECISION_FIX_TOLERANCE.items():
            assert 1e-6 <= tolerance <= 1.0, (
                f"Precision fix tolerance for code {code} is {tolerance}, "
                "expected between 1e-6 and 1.0"
            )

    def test_default_precision_fix_tolerance_appropriate_scale(self) -> None:
        """DEFAULT_PRECISION_FIX_TOLERANCE should be at practical CAD scale.

        The new tolerances are designed to be equivalent to approximately 0.01mm
        across unit systems, which is larger than the nanometer-scale values in
        PRECISION_SNAP_TOLERANCE for most units (MM, IN, Unitless).

        Note: For meters and feet, the old tolerances were already relatively
        large (0.0001m = 0.1mm, 0.00001ft = 0.003mm), so the new values may be
        smaller in absolute terms but are more consistently scaled.
        """
        # For MM, IN, and Unitless, new tolerances should be significantly larger
        units_with_larger_tolerance = [0, 1, 4]  # Unitless, Inches, Millimeters
        for code in units_with_larger_tolerance:
            new_tolerance = DEFAULT_PRECISION_FIX_TOLERANCE[code]
            old_tolerance = PRECISION_SNAP_TOLERANCE.get(
                code, DEFAULT_PRECISION_SNAP_TOLERANCE
            )
            assert new_tolerance > old_tolerance, (
                f"Unit {code}: new tolerance {new_tolerance} should be > "
                f"old tolerance {old_tolerance}"
            )

        # All new tolerances should be consistent with ~0.01mm equivalent
        # MM: 0.01, CM: 0.001 (= 0.01mm), M: 0.00001 (= 0.01mm), IN: 0.0005 (~0.0127mm)
        assert DEFAULT_PRECISION_FIX_TOLERANCE[4] == 0.01  # MM
        assert DEFAULT_PRECISION_FIX_TOLERANCE[5] == 0.001  # CM = 0.01mm
        assert DEFAULT_PRECISION_FIX_TOLERANCE[6] == 0.00001  # M = 0.01mm

    def test_precision_fix_min_less_than_max(self) -> None:
        """PRECISION_FIX_MIN should be less than PRECISION_FIX_MAX."""
        assert PRECISION_FIX_MIN < PRECISION_FIX_MAX, (
            f"PRECISION_FIX_MIN ({PRECISION_FIX_MIN}) must be < "
            f"PRECISION_FIX_MAX ({PRECISION_FIX_MAX})"
        )

    def test_precision_fix_min_non_negative(self) -> None:
        """PRECISION_FIX_MIN must be non-negative (>= 0.0)."""
        assert PRECISION_FIX_MIN >= 0.0, (
            f"PRECISION_FIX_MIN must be >= 0.0, got {PRECISION_FIX_MIN}"
        )

    def test_precision_fix_max_positive(self) -> None:
        """PRECISION_FIX_MAX must be positive (> 0.0)."""
        assert PRECISION_FIX_MAX > 0.0, (
            f"PRECISION_FIX_MAX must be > 0.0, got {PRECISION_FIX_MAX}"
        )

    def test_precision_fix_max_reasonable_limit(self) -> None:
        """PRECISION_FIX_MAX should be a reasonable value (10.0 as per spec)."""
        assert PRECISION_FIX_MAX == 10.0, (
            f"PRECISION_FIX_MAX should be 10.0, got {PRECISION_FIX_MAX}"
        )

    def test_default_precision_fix_tolerance_mm_value(self) -> None:
        """MM tolerance should be 0.01mm (10 micrometers)."""
        assert DEFAULT_PRECISION_FIX_TOLERANCE[4] == 0.01, (
            f"MM tolerance should be 0.01, got {DEFAULT_PRECISION_FIX_TOLERANCE[4]}"
        )

    def test_default_precision_fix_tolerance_inch_value(self) -> None:
        """Inch tolerance should be 0.0005in (0.5 mils)."""
        assert DEFAULT_PRECISION_FIX_TOLERANCE[1] == 0.0005, (
            f"Inch tolerance should be 0.0005, got {DEFAULT_PRECISION_FIX_TOLERANCE[1]}"
        )

    def test_default_precision_fix_tolerance_meter_value(self) -> None:
        """Meter tolerance should be 0.00001m (= 0.01mm)."""
        assert DEFAULT_PRECISION_FIX_TOLERANCE[6] == 0.00001, (
            f"Meter tolerance should be 0.00001, got {DEFAULT_PRECISION_FIX_TOLERANCE[6]}"
        )


class TestMinAreaFilterConstants:
    """Tests for minimum area filter constants."""

    def test_default_min_area_filter_has_all_supported_units(self) -> None:
        """DEFAULT_MIN_AREA_FILTER should have all supported unit codes.

        Supported codes: 0 (Unitless), 1 (Inches), 2 (Feet), 4 (MM), 5 (CM), 6 (M).
        """
        expected_codes = {0, 1, 2, 4, 5, 6}
        actual_codes = set(DEFAULT_MIN_AREA_FILTER.keys())
        assert actual_codes == expected_codes, (
            f"Expected codes {expected_codes}, got {actual_codes}"
        )

    def test_default_min_area_filter_values_non_negative(self) -> None:
        """All area filter values must be non-negative (>= 0)."""
        for code, value in DEFAULT_MIN_AREA_FILTER.items():
            assert value >= 0, (
                f"Area filter value for code {code} is {value}, must be >= 0"
            )

    def test_min_area_filter_min_value(self) -> None:
        """MIN_AREA_FILTER_MIN should be 0.0."""
        assert MIN_AREA_FILTER_MIN == 0.0, (
            f"MIN_AREA_FILTER_MIN should be 0.0, got {MIN_AREA_FILTER_MIN}"
        )

    def test_min_area_filter_max_value(self) -> None:
        """MIN_AREA_FILTER_MAX should be 1000000.0."""
        assert MIN_AREA_FILTER_MAX == 1000000.0, (
            f"MIN_AREA_FILTER_MAX should be 1000000.0, got {MIN_AREA_FILTER_MAX}"
        )

    def test_min_area_filter_min_less_than_max(self) -> None:
        """MIN_AREA_FILTER_MIN should be less than MIN_AREA_FILTER_MAX."""
        assert MIN_AREA_FILTER_MIN < MIN_AREA_FILTER_MAX, (
            f"MIN_AREA_FILTER_MIN ({MIN_AREA_FILTER_MIN}) must be < "
            f"MIN_AREA_FILTER_MAX ({MIN_AREA_FILTER_MAX})"
        )

    def test_default_min_area_filter_mm_value(self) -> None:
        """MM (4) area filter should be 100.0 sq mm."""
        assert DEFAULT_MIN_AREA_FILTER[4] == 100.0, (
            f"MM area filter should be 100.0, got {DEFAULT_MIN_AREA_FILTER[4]}"
        )

    def test_default_min_area_filter_inch_value(self) -> None:
        """Inch (1) area filter should be 0.01 sq inches."""
        assert DEFAULT_MIN_AREA_FILTER[1] == 0.01, (
            f"Inch area filter should be 0.01, got {DEFAULT_MIN_AREA_FILTER[1]}"
        )


class TestMinSideFilterConstants:
    """Tests for minimum side filter constants."""

    def test_default_min_side_filter_has_all_supported_units(self) -> None:
        """DEFAULT_MIN_SIDE_FILTER should have all supported unit codes.

        Supported codes: 0 (Unitless), 1 (Inches), 2 (Feet), 4 (MM), 5 (CM), 6 (M).
        """
        expected_codes = {0, 1, 2, 4, 5, 6}
        actual_codes = set(DEFAULT_MIN_SIDE_FILTER.keys())
        assert actual_codes == expected_codes, (
            f"Expected codes {expected_codes}, got {actual_codes}"
        )

    def test_default_min_side_filter_values_non_negative(self) -> None:
        """All side filter values must be non-negative (>= 0)."""
        for code, value in DEFAULT_MIN_SIDE_FILTER.items():
            assert value >= 0, (
                f"Side filter value for code {code} is {value}, must be >= 0"
            )

    def test_min_side_filter_min_value(self) -> None:
        """MIN_SIDE_FILTER_MIN should be 0.0."""
        assert MIN_SIDE_FILTER_MIN == 0.0, (
            f"MIN_SIDE_FILTER_MIN should be 0.0, got {MIN_SIDE_FILTER_MIN}"
        )

    def test_min_side_filter_max_value(self) -> None:
        """MIN_SIDE_FILTER_MAX should be 100000.0."""
        assert MIN_SIDE_FILTER_MAX == 100000.0, (
            f"MIN_SIDE_FILTER_MAX should be 100000.0, got {MIN_SIDE_FILTER_MAX}"
        )

    def test_min_side_filter_min_less_than_max(self) -> None:
        """MIN_SIDE_FILTER_MIN should be less than MIN_SIDE_FILTER_MAX."""
        assert MIN_SIDE_FILTER_MIN < MIN_SIDE_FILTER_MAX, (
            f"MIN_SIDE_FILTER_MIN ({MIN_SIDE_FILTER_MIN}) must be < "
            f"MIN_SIDE_FILTER_MAX ({MIN_SIDE_FILTER_MAX})"
        )

    def test_default_min_side_filter_mm_value(self) -> None:
        """MM (4) side filter should be 10.0 mm."""
        assert DEFAULT_MIN_SIDE_FILTER[4] == 10.0, (
            f"MM side filter should be 10.0, got {DEFAULT_MIN_SIDE_FILTER[4]}"
        )

    def test_default_min_side_filter_inch_value(self) -> None:
        """Inch (1) side filter should be 0.5 inches."""
        assert DEFAULT_MIN_SIDE_FILTER[1] == 0.5, (
            f"Inch side filter should be 0.5, got {DEFAULT_MIN_SIDE_FILTER[1]}"
        )
