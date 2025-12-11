"""
Tests for constants module - Content Zone Detection Thresholds and Drawing Unit Configuration.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
- Drawing unit configuration constants
"""

from core.constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    DEFAULT_PRECISION_SNAP_TOLERANCE,
    DXF_INSUNITS_MAP,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_LAYER_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAMES,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    EXCEL_SHEET_ALL_BLOCKS,
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

    def test_gap_closure_tolerances_in_reasonable_range(self) -> None:
        """Gap closure tolerances should be between 0.001 and 10.0.

        Shared gap closure tolerances for both Precision Fix and Gap Bridge.
        Base value is 3mm - typical visible CAD gap.
        """
        for code, tolerance in DEFAULT_GAP_CLOSURE_TOLERANCE.items():
            assert 0.001 <= tolerance <= 10.0, (
                f"Gap closure tolerance for code {code} is {tolerance}, "
                "expected between 0.001 and 10.0"
            )

    def test_gap_bridge_constraints_valid(self) -> None:
        """GAP_BRIDGE_MIN should be less than GAP_BRIDGE_MAX."""
        assert GAP_BRIDGE_MIN < GAP_BRIDGE_MAX, (
            f"GAP_BRIDGE_MIN ({GAP_BRIDGE_MIN}) must be < GAP_BRIDGE_MAX ({GAP_BRIDGE_MAX})"
        )
        assert GAP_BRIDGE_MIN >= 0.0, "GAP_BRIDGE_MIN must be non-negative"
        assert GAP_BRIDGE_MAX > 0.0, "GAP_BRIDGE_MAX must be positive"


class TestGapClosureToleranceConstants:
    """Tests for shared gap closure tolerance constants (used by both Precision Fix and Gap Bridge)."""

    def test_default_gap_closure_tolerance_has_all_supported_units(self) -> None:
        """DEFAULT_GAP_CLOSURE_TOLERANCE should have all supported unit codes.

        Supported codes: 0 (Unitless), 1 (Inches), 2 (Feet), 4 (MM), 5 (CM), 6 (M).
        """
        expected_codes = {0, 1, 2, 4, 5, 6}
        actual_codes = set(DEFAULT_GAP_CLOSURE_TOLERANCE.keys())
        assert actual_codes == expected_codes, (
            f"Expected codes {expected_codes}, got {actual_codes}"
        )

    def test_default_gap_closure_tolerance_values_in_reasonable_range(self) -> None:
        """DEFAULT_GAP_CLOSURE_TOLERANCE values should be between 0.001 and 10.0.

        These are practical CAD gap closure tolerances. Base value is 3mm.
        """
        for code, tolerance in DEFAULT_GAP_CLOSURE_TOLERANCE.items():
            assert 0.001 <= tolerance <= 10.0, (
                f"Gap closure tolerance for code {code} is {tolerance}, "
                "expected between 0.001 and 10.0"
            )

    def test_default_gap_closure_tolerance_mm_value(self) -> None:
        """MM tolerance should be 3.0mm."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[4] == 3.0, (
            f"MM tolerance should be 3.0, got {DEFAULT_GAP_CLOSURE_TOLERANCE[4]}"
        )

    def test_default_gap_closure_tolerance_inch_value(self) -> None:
        """Inch tolerance should be 0.125in (1/8 inch)."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[1] == 0.125, (
            f"Inch tolerance should be 0.125, got {DEFAULT_GAP_CLOSURE_TOLERANCE[1]}"
        )

    def test_default_gap_closure_tolerance_feet_value(self) -> None:
        """Feet tolerance should be 0.0104ft (1/8 inch in feet)."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[2] == 0.0104, (
            f"Feet tolerance should be 0.0104, got {DEFAULT_GAP_CLOSURE_TOLERANCE[2]}"
        )

    def test_default_gap_closure_tolerance_cm_value(self) -> None:
        """CM tolerance should be 0.3cm (= 3mm)."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[5] == 0.3, (
            f"CM tolerance should be 0.3, got {DEFAULT_GAP_CLOSURE_TOLERANCE[5]}"
        )

    def test_default_gap_closure_tolerance_meter_value(self) -> None:
        """Meter tolerance should be 0.003m (= 3mm)."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[6] == 0.003, (
            f"Meter tolerance should be 0.003, got {DEFAULT_GAP_CLOSURE_TOLERANCE[6]}"
        )

    def test_default_gap_closure_tolerance_unitless_value(self) -> None:
        """Unitless tolerance should be 3.0 (mm-equivalent)."""
        assert DEFAULT_GAP_CLOSURE_TOLERANCE[0] == 3.0, (
            f"Unitless tolerance should be 3.0, got {DEFAULT_GAP_CLOSURE_TOLERANCE[0]}"
        )

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
        """MM (4) area filter should be 100000.0 sq mm."""
        assert DEFAULT_MIN_AREA_FILTER[4] == 100000.0, (
            f"MM area filter should be 100000.0, got {DEFAULT_MIN_AREA_FILTER[4]}"
        )

    def test_default_min_area_filter_inch_value(self) -> None:
        """Inch (1) area filter should be 155.0 sq inches (~100,000 sq mm)."""
        assert DEFAULT_MIN_AREA_FILTER[1] == 155.0, (
            f"Inch area filter should be 155.0, got {DEFAULT_MIN_AREA_FILTER[1]}"
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
        """Inch (1) side filter should be 0.394 inches (~10mm)."""
        assert DEFAULT_MIN_SIDE_FILTER[1] == 0.394, (
            f"Inch side filter should be 0.394, got {DEFAULT_MIN_SIDE_FILTER[1]}"
        )


class TestAllBlocksSheetConstants:
    """Tests for All Blocks consolidated sheet constants."""

    def test_excel_sheet_all_blocks_value(self) -> None:
        """EXCEL_SHEET_ALL_BLOCKS should have value 'All Blocks'."""
        assert EXCEL_SHEET_ALL_BLOCKS == "All Blocks", (
            f"EXCEL_SHEET_ALL_BLOCKS should be 'All Blocks', got {EXCEL_SHEET_ALL_BLOCKS!r}"
        )

    def test_block_layer_count_follows_naming_convention(self) -> None:
        """EXCEL_COLUMN_BLOCK_LAYER_COUNT should start with 'block_' prefix."""
        assert EXCEL_COLUMN_BLOCK_LAYER_COUNT.startswith("block_"), (
            f"Column '{EXCEL_COLUMN_BLOCK_LAYER_COUNT}' does not follow naming convention"
        )

    def test_block_layer_count_value(self) -> None:
        """EXCEL_COLUMN_BLOCK_LAYER_COUNT should have value 'block_layer_count'."""
        assert EXCEL_COLUMN_BLOCK_LAYER_COUNT == "block_layer_count", (
            f"Expected 'block_layer_count', got {EXCEL_COLUMN_BLOCK_LAYER_COUNT!r}"
        )

    def test_block_layer_names_follows_naming_convention(self) -> None:
        """EXCEL_COLUMN_BLOCK_LAYER_NAMES should start with 'block_' prefix."""
        assert EXCEL_COLUMN_BLOCK_LAYER_NAMES.startswith("block_"), (
            f"Column '{EXCEL_COLUMN_BLOCK_LAYER_NAMES}' does not follow naming convention"
        )

    def test_block_layer_names_value(self) -> None:
        """EXCEL_COLUMN_BLOCK_LAYER_NAMES should have value 'block_layer_names'."""
        assert EXCEL_COLUMN_BLOCK_LAYER_NAMES == "block_layer_names", (
            f"Expected 'block_layer_names', got {EXCEL_COLUMN_BLOCK_LAYER_NAMES!r}"
        )

    def test_block_layer_names_uses_plural_suffix(self) -> None:
        """EXCEL_COLUMN_BLOCK_LAYER_NAMES should end with '_names' (plural for collections)."""
        assert EXCEL_COLUMN_BLOCK_LAYER_NAMES.endswith("_names"), (
            f"Column '{EXCEL_COLUMN_BLOCK_LAYER_NAMES}' should end with '_names' "
            "to indicate it contains a collection (per naming convention)"
        )
