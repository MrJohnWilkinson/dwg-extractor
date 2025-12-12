"""
Tests for constants module - Content Zone Detection Thresholds and Drawing Unit Configuration.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
- Drawing unit configuration constants
"""

from core.constants import (
    CURVED_FILTER_TOLERANCE,
    DEFAULT_CURVED_FILTER_ENABLED,
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_LINE_LENGTH_FILTER,
    DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED,
    DEFAULT_MIN_SIDE_FILTER,
    DEFAULT_PRECISION_SNAP_TOLERANCE,
    DEFAULT_SKIP_CURVED_ENTITIES,
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
    MIN_LINE_LENGTH_FILTER_MAX,
    MIN_LINE_LENGTH_FILTER_MIN,
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


class TestPreFilterConstants:
    """Tests for pre-filter constants (Skip Curved Entities and Min Line Length)."""

    def test_default_skip_curved_entities_is_false(self) -> None:
        """DEFAULT_SKIP_CURVED_ENTITIES should be False (disabled by default)."""
        assert DEFAULT_SKIP_CURVED_ENTITIES is False, (
            f"DEFAULT_SKIP_CURVED_ENTITIES should be False, got {DEFAULT_SKIP_CURVED_ENTITIES}"
        )

    def test_default_min_line_length_filter_enabled_is_false(self) -> None:
        """DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED should be False (disabled by default)."""
        assert DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED is False, (
            f"DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED should be False, "
            f"got {DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED}"
        )

    def test_default_min_line_length_filter_value(self) -> None:
        """DEFAULT_MIN_LINE_LENGTH_FILTER should be 0.5."""
        assert DEFAULT_MIN_LINE_LENGTH_FILTER == 0.5, (
            f"DEFAULT_MIN_LINE_LENGTH_FILTER should be 0.5, "
            f"got {DEFAULT_MIN_LINE_LENGTH_FILTER}"
        )

    def test_min_line_length_filter_min_value(self) -> None:
        """MIN_LINE_LENGTH_FILTER_MIN should be 0.0."""
        assert MIN_LINE_LENGTH_FILTER_MIN == 0.0, (
            f"MIN_LINE_LENGTH_FILTER_MIN should be 0.0, got {MIN_LINE_LENGTH_FILTER_MIN}"
        )

    def test_min_line_length_filter_max_value(self) -> None:
        """MIN_LINE_LENGTH_FILTER_MAX should be 100.0."""
        assert MIN_LINE_LENGTH_FILTER_MAX == 100.0, (
            f"MIN_LINE_LENGTH_FILTER_MAX should be 100.0, got {MIN_LINE_LENGTH_FILTER_MAX}"
        )

    def test_min_line_length_filter_min_less_than_max(self) -> None:
        """MIN_LINE_LENGTH_FILTER_MIN should be less than MIN_LINE_LENGTH_FILTER_MAX."""
        assert MIN_LINE_LENGTH_FILTER_MIN < MIN_LINE_LENGTH_FILTER_MAX, (
            f"MIN_LINE_LENGTH_FILTER_MIN ({MIN_LINE_LENGTH_FILTER_MIN}) must be < "
            f"MIN_LINE_LENGTH_FILTER_MAX ({MIN_LINE_LENGTH_FILTER_MAX})"
        )


class TestCurvedFilterConstants:
    """Tests for curved filter constants (post-filter)."""

    def test_default_curved_filter_enabled_is_false(self) -> None:
        """DEFAULT_CURVED_FILTER_ENABLED should be False (disabled by default)."""
        assert DEFAULT_CURVED_FILTER_ENABLED is False, (
            f"DEFAULT_CURVED_FILTER_ENABLED should be False, "
            f"got {DEFAULT_CURVED_FILTER_ENABLED}"
        )

    def test_curved_filter_tolerance_value(self) -> None:
        """CURVED_FILTER_TOLERANCE should be 0.01."""
        assert CURVED_FILTER_TOLERANCE == 0.01, (
            f"CURVED_FILTER_TOLERANCE should be 0.01, got {CURVED_FILTER_TOLERANCE}"
        )

    def test_curved_filter_tolerance_in_reasonable_range(self) -> None:
        """CURVED_FILTER_TOLERANCE should be in reasonable range (0.001 to 1.0)."""
        assert 0.001 <= CURVED_FILTER_TOLERANCE <= 1.0, (
            f"CURVED_FILTER_TOLERANCE ({CURVED_FILTER_TOLERANCE}) should be "
            "between 0.001 and 1.0"
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


class TestSettingsValidationRegistry:
    """Test suite for SETTINGS_VALIDATION_REGISTRY."""

    def test_registry_has_all_settings(self) -> None:
        """Test that registry contains all 29 expected settings."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        expected_settings = [
            # Filters
            "unit_override",
            "precision_fix_enabled",
            "precision_fix_amount",
            "gap_bridge_enabled",
            "gap_bridge_amount",
            "min_area_filter_enabled",
            "min_area_filter_amount",
            "min_side_filter_enabled",
            "min_side_filter_amount",
            # Pre-Filters
            "skip_curved_entities",
            "min_line_length_filter_enabled",
            "min_line_length_filter_amount",
            # Post-Filters
            "curved_filter_enabled",
            # Performance
            "polygon_count_threshold",
            "line_segment_threshold",
            "entity_count_threshold",
            # Precision
            "arc_flattening_sagitta",
            "coord_dedup_epsilon",
            "rotation_tolerance",
            # Output
            "output_directory",
            "auto_open_excel",
            "show_success_dialog",
            "filename_prefix",
            "include_timestamp",
            # Logging
            "generate_log_file",
            "file_log_level",
            "log_viewer_level",
            "log_viewer_auto_scroll",
            "log_viewer_max_lines",
        ]
        assert len(SETTINGS_VALIDATION_REGISTRY) == 29
        for setting in expected_settings:
            assert setting in SETTINGS_VALIDATION_REGISTRY, (
                f"Missing setting: {setting}"
            )

    def test_registry_entries_have_required_keys(self) -> None:
        """Test that each registry entry has all required validation keys."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        required_keys = {"min_value", "max_value", "default", "unit_aware"}
        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            assert set(validation.keys()) == required_keys, (
                f"Setting '{setting_name}' has incorrect keys: {validation.keys()}"
            )

    def test_numeric_settings_have_valid_ranges(self) -> None:
        """Test that numeric settings have min <= max when both are defined."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            min_val = validation["min_value"]
            max_val = validation["max_value"]
            if min_val is not None and max_val is not None:
                assert min_val <= max_val, (
                    f"Setting '{setting_name}' has invalid range: {min_val} > {max_val}"
                )

    def test_default_values_within_range(self) -> None:
        """Test that default values are within their min/max range."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            default = validation["default"]
            min_val = validation["min_value"]
            max_val = validation["max_value"]

            # Skip if default is None or not numeric
            if default is None or not isinstance(default, (int, float)):
                continue

            if min_val is not None:
                assert default >= min_val, (
                    f"Setting '{setting_name}' default {default} < min {min_val}"
                )
            if max_val is not None:
                assert default <= max_val, (
                    f"Setting '{setting_name}' default {default} > max {max_val}"
                )

    def test_unit_aware_settings_identified(self) -> None:
        """Test that unit-aware settings are correctly flagged."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        # These settings should have unit_aware=True (defaults vary by unit)
        unit_aware_settings = [
            "precision_fix_amount",
            "gap_bridge_amount",
            "min_area_filter_amount",
            "min_side_filter_amount",
        ]

        for setting_name in unit_aware_settings:
            assert SETTINGS_VALIDATION_REGISTRY[setting_name]["unit_aware"] is True, (
                f"Setting '{setting_name}' should be unit_aware"
            )

        # All other settings should have unit_aware=False
        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            if setting_name not in unit_aware_settings:
                assert validation["unit_aware"] is False, (
                    f"Setting '{setting_name}' should not be unit_aware"
                )


class TestSettingsDefaultConstants:
    """Test suite for settings default value constants."""

    def test_performance_threshold_defaults(self) -> None:
        """Test performance threshold default values."""
        from core.constants import (
            DEFAULT_ENTITY_COUNT_THRESHOLD,
            DEFAULT_LINE_SEGMENT_THRESHOLD,
            DEFAULT_POLYGON_COUNT_THRESHOLD,
        )

        assert DEFAULT_POLYGON_COUNT_THRESHOLD == 500
        assert DEFAULT_LINE_SEGMENT_THRESHOLD == 5000
        assert DEFAULT_ENTITY_COUNT_THRESHOLD == 1000

    def test_precision_setting_defaults(self) -> None:
        """Test precision setting default values."""
        from core.constants import (
            DEFAULT_ARC_FLATTENING_SAGITTA,
            DEFAULT_COORD_DEDUP_EPSILON,
            DEFAULT_ROTATION_TOLERANCE,
        )

        assert DEFAULT_ARC_FLATTENING_SAGITTA == 0.1
        assert DEFAULT_COORD_DEDUP_EPSILON == 0.01
        assert DEFAULT_ROTATION_TOLERANCE == 1.0

    def test_output_setting_defaults(self) -> None:
        """Test output setting default values."""
        from core.constants import (
            DEFAULT_AUTO_OPEN_EXCEL,
            DEFAULT_FILENAME_PREFIX,
            DEFAULT_INCLUDE_TIMESTAMP,
            DEFAULT_SHOW_SUCCESS_DIALOG,
        )

        assert DEFAULT_AUTO_OPEN_EXCEL is True
        assert DEFAULT_SHOW_SUCCESS_DIALOG is True
        assert DEFAULT_INCLUDE_TIMESTAMP is True
        assert DEFAULT_FILENAME_PREFIX == ""

    def test_logging_setting_defaults(self) -> None:
        """Test logging setting default values."""
        from core.constants import (
            DEFAULT_FILE_LOG_LEVEL,
            DEFAULT_GENERATE_LOG_FILE,
            DEFAULT_LOG_VIEWER_AUTO_SCROLL,
            DEFAULT_LOG_VIEWER_LEVEL,
            DEFAULT_LOG_VIEWER_MAX_LINES,
        )

        assert DEFAULT_GENERATE_LOG_FILE is False
        assert DEFAULT_FILE_LOG_LEVEL == "DEBUG"
        assert DEFAULT_LOG_VIEWER_LEVEL == "INFO"
        assert DEFAULT_LOG_VIEWER_AUTO_SCROLL is True
        assert DEFAULT_LOG_VIEWER_MAX_LINES == 1000
