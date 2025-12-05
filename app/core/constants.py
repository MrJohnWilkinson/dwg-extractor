"""
Application-wide constants for the DXF Block Extractor.

This module defines all constants used throughout the application including:
- Supported file extensions for DXF files
- Excel output configuration (column names, worksheet name)
- User-facing messages for UI and error handling

Usage:
    from core.constants import SUPPORTED_EXTENSIONS, EXCEL_COLUMN_BLOCK_NAME
"""

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
# Domain: block, Attribute: suggested_trim, Qualifier: left/right/top/bottom (content zone derived)
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT: str = "block_suggested_trim_left"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT: str = "block_suggested_trim_right"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP: str = "block_suggested_trim_top"
EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM: str = "block_suggested_trim_bottom"
# Domain: block, Attribute: content_zone, Qualifier: detected (boolean flag)
EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED: str = "block_content_zone_detected"

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

# Excel configuration - Fill colors for scale highlighting
# Yellow: Warning color for scale variance with all positive values
EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE: str = "FFFFFF00"
# Orange: Moderate alert for consistent negative scales (mirroring/flipping)
EXCEL_FILL_COLOR_SCALE_NEGATIVE: str = "FFA500FF"
# Red: High priority alert for scale variance with negative values (mixed positive/negative)
EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE: str = "FFFF0000"
# Yellow: Warning color for extraction issues
EXCEL_FILL_COLOR_EXTRACTION_ISSUE: str = "FFFFFF00"

# Log viewer configuration
LOG_POLL_INTERVAL_MS: int = 50

# Content zone detection thresholds
# Maximum polygon count for content zone detection to avoid O(n³) complexity
# Blocks with more polygons than this threshold will skip content zone analysis
POLYGON_COUNT_THRESHOLD: int = 30

# UI messages
MSG_SELECT_FILE: str = "Please select a DXF file"
MSG_PROCESSING: str = "Processing..."
MSG_SUCCESS: str = "Extraction complete"
MSG_ERROR_INVALID_FILE: str = "Invalid or corrupted file"
MSG_ERROR_NO_BLOCKS: str = "No blocks found in file"
MSG_ERROR_FILE_NOT_FOUND: str = "File not found"

# Abort-related messages
MSG_ABORTING: str = "Aborting extraction..."
MSG_ABORTED: str = "Extraction aborted"

# Log file messages
MSG_LOG_FILE_CREATED: str = "Debug log: {}"
