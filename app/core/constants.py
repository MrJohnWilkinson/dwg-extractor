"""
Application-wide constants for the DXF Block Extractor.

This module defines all constants used throughout the application including:
- Supported file extensions for DXF files
- Excel output configuration (column names, worksheet name)
- User-facing messages for UI and error handling
- GUI settings defaults and validation ranges

Usage:
    from core.constants import SUPPORTED_EXTENSIONS, EXCEL_COLUMN_BLOCK_NAME
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .types import SettingValidation

# File extensions
SUPPORTED_EXTENSIONS: tuple[str] = (".dxf",)

# Excel configuration - Sheet names
EXCEL_SHEET_BLOCK_ANALYSIS: str = "Block Analysis"
EXCEL_SHEET_LAYER_ANALYSIS: str = "Layer Analysis"
EXCEL_SHEET_ENTITY_SUMMARY: str = "Entity Summary"
EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS: str = "Block Geometry Analysis"
EXCEL_SHEET_ANNOTATIONS_ANALYSIS: str = "Annotations Analysis"
EXCEL_SHEET_COLOR_ANALYSIS: str = "Color Analysis"
EXCEL_SHEET_EXTRACTION_ISSUES: str = "Extraction Issues"
EXCEL_SHEET_BLOCK_DEFINITIONS: str = "Block Definitions"
EXCEL_SHEET_ALL_BLOCKS: str = "All Blocks"

# Excel configuration - Block Counts sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_BLOCK_NAME: str = "block_name"
EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = "block_insertion_count"
EXCEL_COLUMN_BLOCK_ENTITY_COUNT: str = "block_entity_count"
EXCEL_COLUMN_BLOCK_LAYER_NAME: str = (
    "block_layer_name"  # See app_docs/005-field-naming-convention.md
)
# Domain: block, Attribute: xdata, Qualifier: apps (collection)
EXCEL_COLUMN_BLOCK_XDATA_APPS: str = "block_xdata_apps"

# Excel configuration - Block Counts sheet rotation columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_BLOCK_ROTATION_0: str = "block_rotation_0"
EXCEL_COLUMN_BLOCK_ROTATION_90: str = "block_rotation_90"
EXCEL_COLUMN_BLOCK_ROTATION_180: str = "block_rotation_180"
EXCEL_COLUMN_BLOCK_ROTATION_270: str = "block_rotation_270"
EXCEL_COLUMN_BLOCK_ROTATION_OTHER: str = "block_rotation_other"

# Excel configuration - Layer Analysis sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_LAYER_NAME: str = "layer_name"
EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT: str = "layer_block_insertion_count"
EXCEL_COLUMN_LAYER_ENTITY_COUNT: str = "layer_entity_count"
# Domain: layer, Attribute: unique, Qualifier: color, Suffix: count
EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT: str = "layer_unique_color_count"
# Domain: layer, Attribute: annotation (combined TEXT + MTEXT entities), Suffix: count
EXCEL_COLUMN_LAYER_ANNOTATION_COUNT: str = "layer_annotation_count"

# Excel configuration - Entity Summary sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_ENTITY_TYPE_NAME: str = "entity_type_name"
EXCEL_COLUMN_ENTITY_TYPE_COUNT: str = "entity_type_count"

# Excel configuration - Block Geometry Analysis sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: block, Attribute: scale, Qualifier: x/y (transformation factors)
EXCEL_COLUMN_BLOCK_SCALE_X: str = "block_scale_x"
EXCEL_COLUMN_BLOCK_SCALE_Y: str = "block_scale_y"
# Domain: block, Qualifier: native (at 0° rotation), Attribute: width/height
EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: str = "block_native_width"
EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: str = "block_native_height"
# Domain: block, Attribute: vertical/horizontal, Qualifier: segments (collection)
EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: str = "block_vertical_segments"
EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: str = "block_horizontal_segments"

# Excel configuration - Annotations Analysis sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: annotation (TEXT/MTEXT entities)
EXCEL_COLUMN_ANNOTATION_CONTENTS: str = "annotation_contents"
EXCEL_COLUMN_ANNOTATION_TYPE: str = "annotation_type"
EXCEL_COLUMN_ANNOTATION_LAYER_NAME: str = "annotation_layer_name"
EXCEL_COLUMN_ANNOTATION_COLOR_R: str = "annotation_color_r"
EXCEL_COLUMN_ANNOTATION_COLOR_G: str = "annotation_color_g"
EXCEL_COLUMN_ANNOTATION_COLOR_B: str = "annotation_color_b"
EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE: str = "annotation_color_sample"
EXCEL_COLUMN_ANNOTATION_COUNT: str = "annotation_count"

# Excel configuration - Color Analysis sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: color (color-based entity analysis)
EXCEL_COLUMN_COLOR_ANNOTATION_CONTENTS: str = "color_annotation_contents"
EXCEL_COLUMN_COLOR_LAYER_NAME: str = "color_layer_name"
EXCEL_COLUMN_COLOR_RED: str = "color_red"
EXCEL_COLUMN_COLOR_GREEN: str = "color_green"
EXCEL_COLUMN_COLOR_BLUE: str = "color_blue"
EXCEL_COLUMN_COLOR_SAMPLE: str = "color_sample"
EXCEL_COLUMN_COLOR_AUTOCAD_NAME: str = "color_autocad_name"
EXCEL_COLUMN_COLOR_ENTITY_TYPE: str = "color_entity_type"
EXCEL_COLUMN_COLOR_ENTITY_COUNT: str = "color_entity_count"

# Excel configuration - Extraction Issues sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_ISSUE_TYPE: str = "issue_type"
EXCEL_COLUMN_ISSUE_BLOCK_NAME: str = "issue_block_name"
EXCEL_COLUMN_ISSUE_LAYER_NAME: str = "issue_layer_name"
EXCEL_COLUMN_ISSUE_INSERTION_COUNT: str = "issue_insertion_count"
EXCEL_COLUMN_ISSUE_DETAILS: str = "issue_details"

# Excel configuration - Content Zone columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: block, Attribute: suggested_trim/content_zone (content zone detection results)
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: str = "block_suggested_trim_left"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: str = "block_suggested_trim_right"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: str = "block_suggested_trim_top"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: str = "block_suggested_trim_bottom"
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: str = "block_content_zone_detected"
# Domain: block, Attribute: content_zone (geometry dimensions)
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH: str = "block_content_zone_width"
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT: str = "block_content_zone_height"
EXCEL_COLUMN_BLOCK_POLYGON_COUNT: str = "block_polygon_count"
EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT: str = "block_filtered_polygon_count"

# Excel configuration - Block Definitions sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_BLOCK_RAW_NAME: str = "block_raw_name"
EXCEL_COLUMN_BLOCK_RESOLVED_NAME: str = "block_resolved_name"
EXCEL_COLUMN_BLOCK_INSERTION_STATUS: str = "block_insertion_status"
EXCEL_COLUMN_BLOCK_IS_NESTED: str = "block_is_nested"
EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: str = "block_nested_parent_names"
# Note: EXCEL_COLUMN_BLOCK_ENTITY_COUNT already exists (line 29)

# Excel configuration - All Blocks sheet additional columns
# See app_docs/005-field-naming-convention.md for naming conventions
# Domain: block, Attribute: layer, Qualifier: count/names
EXCEL_COLUMN_BLOCK_LAYER_COUNT: str = "block_layer_count"
EXCEL_COLUMN_BLOCK_LAYER_NAMES: str = (
    "block_layer_names"  # Plural: collection of layer names
)

# Excel configuration - Fill colors for scale highlighting
# Yellow: Warning color for scale variance with all positive values
EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE: str = "FFFFFF00"
# Orange: Moderate alert for consistent negative scales (mirroring/flipping)
EXCEL_FILL_COLOR_SCALE_NEGATIVE: str = "FFA500FF"
# Red: High priority alert for scale variance with negative values (mixed positive/negative)
EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE: str = "FFFF0000"
# Yellow: Warning color for extraction issues
EXCEL_FILL_COLOR_EXTRACTION_ISSUE: str = "FFFFFF00"
# Green: Highlight color for nested blocks in Block Definitions sheet
EXCEL_FILL_COLOR_NESTED_BLOCK: str = "FF90EE90"

# UI messages
MSG_SELECT_FILE: str = "Please select a DXF file"
MSG_PROCESSING: str = "Processing..."
MSG_SUCCESS: str = "Extraction complete"
MSG_ERROR_INVALID_FILE: str = "Invalid or corrupted file"
MSG_ERROR_NO_BLOCKS: str = "No blocks found in file"
MSG_ERROR_FILE_NOT_FOUND: str = "File not found"
MSG_ABORTING: str = "Aborting..."
MSG_ABORTED: str = "Extraction aborted"

# Content Zone Detection Thresholds
# Conservative limits for Shapely-based geometry operations

POLYGON_COUNT_THRESHOLD: int = 500
"""Maximum polygons for content zone net area calculation.
Blocks with more polygons skip content zone detection.
Rationale: With Shapely's efficient GEOS operations, can handle 500 polygons
in reasonable time (previously 30 with O(n^3) manual calculation)."""

LINE_SEGMENT_THRESHOLD: int = 5000
"""Maximum LINE segments for cycle detection using Shapely polygonize.
Blocks with more LINE segments skip LINE cycle extraction.
Rationale: With Shapely's GEOS-based polygonize(), can handle 5000 segments
efficiently (previously 200 with DFS-based cycle detection)."""

ENTITY_COUNT_THRESHOLD: int = 1000
"""Maximum entities in block for content zone detection.
Blocks with more entities skip content zone entirely.
Rationale: High entity counts strongly correlate with complex geometry
that will exceed polygon thresholds anyway."""

# Arc Flattening Configuration
ARC_FLATTENING_SAGITTA: float = 0.1
"""Maximum distance from arc center to chord center for flattening.
Smaller values = more segments = higher precision. 0.1 is appropriate for
typical CAD drawings with units in mm or inches."""

# Drawing Unit Configuration
# Maps DXF $INSUNITS header codes to human-readable unit names
# See: https://knowledge.autodesk.com/support/autocad/learn-explore/caas/CloudHelp/cloudhelp/2022/ENU/AutoCAD-Core/files/GUID-A58A87BB-482B-4042-A00A-EEF55D2B1FEC-htm.html
DXF_INSUNITS_MAP: dict[int, str] = {
    0: "Unitless",
    1: "Inches",
    2: "Feet",
    4: "Millimeters",
    5: "Centimeters",
    6: "Meters",
}
"""Maps DXF $INSUNITS header codes to human-readable unit names.
Only commonly used CAD units are supported. Code 3 (Miles) is intentionally excluded."""

# GUI unit selection options for user override dropdown
# -1 indicates "use DXF file units" (auto-detect)
UNIT_SELECTION_OPTIONS: dict[str, int] = {
    "DXF/DWG": -1,
    "MM": 4,
    "CM": 5,
    "M": 6,
    "IN": 1,
    "FT": 2,
}
"""GUI dropdown options for manual unit override.
Key is display label, value is DXF $INSUNITS code (-1 for auto-detect)."""

# Stage 1: Precision snap tolerances for fixing floating-point artifacts
# These are extremely small (nanometer scale relative to unit) to only fix
# floating-point precision errors, not intentional design gaps
PRECISION_SNAP_TOLERANCE: dict[int, float] = {
    0: 1e-6,  # Unitless: use small default
    1: 1e-6,  # Inches: ~25 nanometers
    2: 1e-5,  # Feet: ~3 micrometers (feet are larger units)
    4: 1e-6,  # Millimeters: 1 nanometer
    5: 1e-5,  # Centimeters: 0.1 nanometers (cm drawings have larger coords)
    6: 1e-4,  # Meters: 0.1 micrometers (meter coords can be very large)
}
"""Stage 1 precision snap tolerances by unit code.
These fix floating-point artifacts without affecting intentional gaps.
Values are scaled relative to typical coordinate magnitudes in each unit system."""

DEFAULT_PRECISION_SNAP_TOLERANCE: float = 1e-6
"""Fallback precision snap tolerance when unit is unknown or unsupported.
Conservative value appropriate for most CAD applications."""

# Shared gap closure tolerance for both Precision Fix and Gap Bridge algorithms.
# Both solve the same problem (closing small gaps for accurate polygon counts)
# using different algorithms, so they share the same default tolerance.
# Base: 3mm - typical visible CAD gap, large enough to bridge design gaps
# but small enough to not merge distinct geometry.
DEFAULT_GAP_CLOSURE_TOLERANCE: dict[int, float] = {
    0: 3.0,  # Unitless: assume mm-equivalent (3mm)
    1: 0.125,  # Inches: 1/8 inch (closest standard fraction to 3mm)
    2: 0.0104,  # Feet: 1/8 inch in feet (0.125/12)
    4: 3.0,  # Millimeters: 3mm
    5: 0.3,  # Centimeters: 0.3cm = 3mm
    6: 0.003,  # Meters: 0.003m = 3mm
}
"""Shared gap closure tolerance for both Precision Fix and Gap Bridge algorithms.
Both solve the same problem - closing small gaps for accurate polygon counts.
Base value is 3mm, a typical visible CAD gap."""

# Gap bridge amount input constraints for GUI slider/input
GAP_BRIDGE_MIN: float = 0.0
"""Minimum gap bridge amount (0 = no gap bridging)."""

GAP_BRIDGE_MAX: float = 10000.0
"""Maximum gap bridge amount. Large value allows extreme cases while
preventing overflow issues in calculations."""


# Precision fix amount input constraints for GUI slider/input
PRECISION_FIX_MIN: float = 0.0
"""Minimum precision fix amount (0 = use default tolerance for unit)."""

PRECISION_FIX_MAX: float = 10.0
"""Maximum precision fix amount. Conservative limit to prevent
unreasonably large tolerance values that could merge distinct geometry."""

# Minimum Area Filter constants
DEFAULT_MIN_AREA_FILTER: dict[int, float] = {
    0: 100000.0,  # Unitless: assume mm-equivalent (100,000 sq mm)
    1: 155.0,  # Inches: 155 sq inches (~100,000 sq mm)
    2: 1.076,  # Feet: 1.076 sq feet (~100,000 sq mm)
    4: 100000.0,  # Millimeters: 100,000 sq mm
    5: 1000.0,  # Centimeters: 1,000 sq cm = 100,000 sq mm
    6: 0.1,  # Meters: 0.1 sq m = 100,000 sq mm
}
"""Default minimum area filter by unit code.
Polygons with area less than this value are filtered out of content zone calculation.
Base value is 100,000 sq mm (~10" x 10" square)."""

MIN_AREA_FILTER_MIN: float = 0.0
"""Minimum area filter amount (0 = no area filtering)."""

MIN_AREA_FILTER_MAX: float = 1000000.0
"""Maximum area filter amount. Large value allows extreme cases while
preventing overflow issues in calculations."""

# Minimum Side Filter constants
DEFAULT_MIN_SIDE_FILTER: dict[int, float] = {
    0: 10.0,  # Unitless: assume mm-equivalent (10mm)
    1: 0.394,  # Inches: 0.394 inches (~10mm)
    2: 0.0328,  # Feet: 0.0328 feet (~10mm)
    4: 10.0,  # Millimeters: 10mm
    5: 1.0,  # Centimeters: 1cm = 10mm
    6: 0.01,  # Meters: 0.01m = 10mm
}
"""Default minimum side filter by unit code.
Polygons with shortest straight side less than this value are filtered out.
Base value is 10mm."""

MIN_SIDE_FILTER_MIN: float = 0.0
"""Minimum side filter amount (0 = no side filtering)."""

MIN_SIDE_FILTER_MAX: float = 100000.0
"""Maximum side filter amount. Large value allows extreme cases while
preventing overflow issues in calculations."""

# Pre-Filter Constants: Skip Curved Entities
DEFAULT_SKIP_CURVED_ENTITIES: bool = False
"""Default for skip curved entities pre-filter.
When True, excludes CIRCLE and ARC entities from edge extraction."""

# Pre-Filter Constants: Min Line Length Filter
DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED: bool = False
"""Default for min line length filter enabled state.
When True, excludes LINE entities below a length threshold."""

DEFAULT_MIN_LINE_LENGTH_FILTER: float = 0.5
"""Default minimum line length threshold in drawing units.
Lines shorter than this are excluded from edge extraction."""

MIN_LINE_LENGTH_FILTER_MIN: float = 0.0
"""Minimum line length filter amount (0 = no line length filtering)."""

MIN_LINE_LENGTH_FILTER_MAX: float = 100.0
"""Maximum line length filter amount. Reasonable limit for CAD drawings."""

# Post-Filter Constants: Curved Lines Filter
DEFAULT_CURVED_FILTER_ENABLED: bool = False
"""Default for curved filter enabled state.
When True, excludes polygons containing curved edges after detection."""

CURVED_FILTER_TOLERANCE: float = 0.01
"""Tolerance for detecting curved edges in polygons.
Small value ensures only true curved edges are detected."""

# =============================================================================
# GUI Settings Defaults and Validation Ranges
# =============================================================================
# These constants support the Advanced Settings modal and SettingsManager.
# See ai_output/064-combined-gui-settings-and-parallel-removal-plan.md for context.

# Performance threshold defaults (early-exit thresholds only, no thread settings)
# Note: POLYGON_COUNT_THRESHOLD, LINE_SEGMENT_THRESHOLD, ENTITY_COUNT_THRESHOLD
# already exist above (lines 162-178). These DEFAULT_ versions are for the
# settings system; the originals remain for backward compatibility.
DEFAULT_POLYGON_COUNT_THRESHOLD: int = 500
DEFAULT_LINE_SEGMENT_THRESHOLD: int = 5000
DEFAULT_ENTITY_COUNT_THRESHOLD: int = 1000

POLYGON_COUNT_THRESHOLD_MIN: int = 100
POLYGON_COUNT_THRESHOLD_MAX: int = 10000
LINE_SEGMENT_THRESHOLD_MIN: int = 1000
LINE_SEGMENT_THRESHOLD_MAX: int = 50000
ENTITY_COUNT_THRESHOLD_MIN: int = 100
ENTITY_COUNT_THRESHOLD_MAX: int = 10000

# Precision setting defaults
# Note: ARC_FLATTENING_SAGITTA already exists above (line 181).
# These provide explicit defaults and validation ranges for the settings system.
DEFAULT_ARC_FLATTENING_SAGITTA: float = 0.1
DEFAULT_COORD_DEDUP_EPSILON: float = 0.01
DEFAULT_ROTATION_TOLERANCE: float = 1.0

ARC_FLATTENING_SAGITTA_MIN: float = 0.01
ARC_FLATTENING_SAGITTA_MAX: float = 1.0
COORD_DEDUP_EPSILON_MIN: float = 0.001
COORD_DEDUP_EPSILON_MAX: float = 1.0
ROTATION_TOLERANCE_MIN: float = 0.1
ROTATION_TOLERANCE_MAX: float = 5.0

# Output setting defaults
DEFAULT_AUTO_OPEN_EXCEL: bool = True
DEFAULT_SHOW_SUCCESS_DIALOG: bool = True
DEFAULT_INCLUDE_TIMESTAMP: bool = True
DEFAULT_FILENAME_PREFIX: str = ""

# Logging setting defaults
DEFAULT_GENERATE_LOG_FILE: bool = False
DEFAULT_FILE_LOG_LEVEL: str = "DEBUG"
DEFAULT_LOG_VIEWER_LEVEL: str = "INFO"
DEFAULT_LOG_VIEWER_AUTO_SCROLL: bool = True
DEFAULT_LOG_VIEWER_MAX_LINES: int = 1000

LOG_VIEWER_MAX_LINES_MIN: int = 100
LOG_VIEWER_MAX_LINES_MAX: int = 10000

# Settings Validation Registry
# Maps setting names to their validation metadata.
# Used by SettingsManager.validate() and Advanced Settings Window.
SETTINGS_VALIDATION_REGISTRY: dict[str, "SettingValidation"] = {
    # Filters
    "unit_override": {
        "min_value": -1,
        "max_value": 6,
        "default": None,
        "unit_aware": False,
    },
    "precision_fix_enabled": {
        "min_value": None,
        "max_value": None,
        "default": True,
        "unit_aware": False,
    },
    "precision_fix_amount": {
        "min_value": PRECISION_FIX_MIN,
        "max_value": PRECISION_FIX_MAX,
        "default": None,
        "unit_aware": True,
    },
    "gap_bridge_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "gap_bridge_amount": {
        "min_value": GAP_BRIDGE_MIN,
        "max_value": GAP_BRIDGE_MAX,
        "default": None,
        "unit_aware": True,
    },
    "min_area_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_area_filter_amount": {
        "min_value": MIN_AREA_FILTER_MIN,
        "max_value": MIN_AREA_FILTER_MAX,
        "default": None,
        "unit_aware": True,
    },
    "min_side_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_side_filter_amount": {
        "min_value": MIN_SIDE_FILTER_MIN,
        "max_value": MIN_SIDE_FILTER_MAX,
        "default": None,
        "unit_aware": True,
    },
    # Pre-Filters
    "skip_curved_entities": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_SKIP_CURVED_ENTITIES,
        "unit_aware": False,
    },
    "min_line_length_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED,
        "unit_aware": False,
    },
    "min_line_length_filter_amount": {
        "min_value": MIN_LINE_LENGTH_FILTER_MIN,
        "max_value": MIN_LINE_LENGTH_FILTER_MAX,
        "default": DEFAULT_MIN_LINE_LENGTH_FILTER,
        "unit_aware": False,
    },
    # Post-Filters
    "curved_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_CURVED_FILTER_ENABLED,
        "unit_aware": False,
    },
    # Performance
    "polygon_count_threshold": {
        "min_value": POLYGON_COUNT_THRESHOLD_MIN,
        "max_value": POLYGON_COUNT_THRESHOLD_MAX,
        "default": DEFAULT_POLYGON_COUNT_THRESHOLD,
        "unit_aware": False,
    },
    "line_segment_threshold": {
        "min_value": LINE_SEGMENT_THRESHOLD_MIN,
        "max_value": LINE_SEGMENT_THRESHOLD_MAX,
        "default": DEFAULT_LINE_SEGMENT_THRESHOLD,
        "unit_aware": False,
    },
    "entity_count_threshold": {
        "min_value": ENTITY_COUNT_THRESHOLD_MIN,
        "max_value": ENTITY_COUNT_THRESHOLD_MAX,
        "default": DEFAULT_ENTITY_COUNT_THRESHOLD,
        "unit_aware": False,
    },
    # Precision
    "arc_flattening_sagitta": {
        "min_value": ARC_FLATTENING_SAGITTA_MIN,
        "max_value": ARC_FLATTENING_SAGITTA_MAX,
        "default": DEFAULT_ARC_FLATTENING_SAGITTA,
        "unit_aware": False,
    },
    "coord_dedup_epsilon": {
        "min_value": COORD_DEDUP_EPSILON_MIN,
        "max_value": COORD_DEDUP_EPSILON_MAX,
        "default": DEFAULT_COORD_DEDUP_EPSILON,
        "unit_aware": False,
    },
    "rotation_tolerance": {
        "min_value": ROTATION_TOLERANCE_MIN,
        "max_value": ROTATION_TOLERANCE_MAX,
        "default": DEFAULT_ROTATION_TOLERANCE,
        "unit_aware": False,
    },
    # Output
    "output_directory": {
        "min_value": None,
        "max_value": None,
        "default": None,
        "unit_aware": False,
    },
    "auto_open_excel": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_AUTO_OPEN_EXCEL,
        "unit_aware": False,
    },
    "show_success_dialog": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_SHOW_SUCCESS_DIALOG,
        "unit_aware": False,
    },
    "filename_prefix": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_FILENAME_PREFIX,
        "unit_aware": False,
    },
    "include_timestamp": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_INCLUDE_TIMESTAMP,
        "unit_aware": False,
    },
    # Logging
    "generate_log_file": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_GENERATE_LOG_FILE,
        "unit_aware": False,
    },
    "file_log_level": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_FILE_LOG_LEVEL,
        "unit_aware": False,
    },
    "log_viewer_level": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_LOG_VIEWER_LEVEL,
        "unit_aware": False,
    },
    "log_viewer_auto_scroll": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_LOG_VIEWER_AUTO_SCROLL,
        "unit_aware": False,
    },
    "log_viewer_max_lines": {
        "min_value": LOG_VIEWER_MAX_LINES_MIN,
        "max_value": LOG_VIEWER_MAX_LINES_MAX,
        "default": DEFAULT_LOG_VIEWER_MAX_LINES,
        "unit_aware": False,
    },
}
