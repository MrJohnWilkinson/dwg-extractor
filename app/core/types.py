"""
Shared type definitions for the DXF Block Extractor.

This module provides TypedDict definitions for internal data structures used
throughout the codebase. Using TypedDict instead of generic dict[str, Any]
improves type safety, IDE support, and code documentation.

Frozen dataclass keys provide:
1. Named fields - LLMs and developers understand BlockLayerKey(block_name="DOOR", layer_name="WALLS")
2. Docstrings - Each key class documents its purpose and field meanings
3. Type safety - Field names prevent positional errors when constructing keys
4. Hashability - frozen=True enables use as dict keys

Usage:
    from core.types import BlockTrimmingData, ColorAnalysisRecord, BlockLayerKey, BlockDefinitionRecord

    # Type-safe block trimming data
    trimming: BlockTrimmingData = {
        "native_width": 1200.0,
        "native_height": 600.0,
        "vertical_segments": [50.0, 1100.0, 50.0],
        "horizontal_segments": [25.0, 550.0, 25.0],
    }

    # Frozen dataclass key for dictionary indexing
    key = BlockLayerKey(block_name="DOOR", layer_name="WALLS")
"""

from dataclasses import dataclass
from typing import TypedDict


Polygon = list[tuple[float, float]]
"""List of (x, y) vertices forming a closed polygon.

Vertices should be ordered consecutively (clockwise or counter-clockwise).
The polygon is implicitly closed - the last vertex connects to the first.
Used for content zone detection and area calculations.
"""


@dataclass(frozen=True)
class BlockLayerKey:
    """
    Hashable key identifying a unique block-layer combination for insertion tracking.

    Used as dictionary key in block_layer_pairs and block_xdata_apps fields.

    Attributes:
        block_name: Name of the block definition
        layer_name: Name of the layer where the block is inserted
    """

    block_name: str
    layer_name: str


@dataclass(frozen=True)
class BlockRotationKey:
    """
    Hashable key identifying block insertions by layer and rotation category.

    Used as dictionary key in block_rotation_counts field.

    Attributes:
        block_name: Name of the block definition
        layer_name: Name of the layer where the block is inserted
        rotation_category: One of '0', '90', '180', '270', 'other'
    """

    block_name: str
    layer_name: str
    rotation_category: str


@dataclass(frozen=True)
class AnnotationKey:
    """
    Hashable key identifying unique text annotations by content, type, layer, and RGB color.

    Used as dictionary key in annotation_data field.

    Attributes:
        annotation_contents: Text content of the annotation
        annotation_type: Entity type string ('TEXT' or 'MTEXT')
        layer_name: Name of the layer containing the annotation
        color_r: Red component (0-255)
        color_g: Green component (0-255)
        color_b: Blue component (0-255)
    """

    annotation_contents: str
    annotation_type: str
    layer_name: str
    color_r: int
    color_g: int
    color_b: int


@dataclass(frozen=True)
class ColorEntityKey:
    """
    Hashable key for grouping geometric entities by RGB color, ACI index, layer, and entity type.

    Used internally in extract_color_analysis() for aggregating entity counts.

    Attributes:
        color_r: Red component (0-255)
        color_g: Green component (0-255)
        color_b: Blue component (0-255)
        color_aci: AutoCAD Color Index (0-256) or None for True Color
        layer_name: Name of the layer containing the entity
        entity_type: Entity type string ('Lines', 'Polylines', 'Hatches')
    """

    color_r: int
    color_g: int
    color_b: int
    color_aci: int | None
    layer_name: str
    entity_type: str


class BlockTrimmingData(TypedDict):
    """
    Block geometry analysis data for trimming assistance.

    Contains native dimensions and geometric segment data for a block definition.
    Used in the block_trimming_data field of ExtractionResult.

    Attributes:
        native_width: Block width in drawing units (absolute bounding box width)
        native_height: Block height in drawing units (absolute bounding box height)
        vertical_segments: List of vertical segment lengths from left to right
        horizontal_segments: List of horizontal segment lengths from bottom to top
    """

    native_width: float
    native_height: float
    vertical_segments: list[float]
    horizontal_segments: list[float]


class ColorAnalysisRecord(TypedDict):
    """
    Color analysis record for Lines, Polylines, Hatches, TEXT, and MTEXT entities.

    Contains entity information grouped by RGB color, layer name, and entity type.
    Used in the color_analysis_data field of ExtractionResult.

    Attributes:
        annotation_contents: Text content for TEXT/MTEXT entities, empty string for geometric entities
        layer_name: Layer name of the entity
        color_r: Red component (0-255)
        color_g: Green component (0-255)
        color_b: Blue component (0-255)
        color_aci: AutoCAD Color Index (0-256) or None for True Color (24-bit RGB)
                   0 = ByBlock, 1-7 = named colors, 8-255 = numbered colors, 256 = ByLayer
        entity_type: Entity type string ('Lines', 'Polylines', 'Hatches', 'TEXT', or 'MTEXT')
        entity_count: Count of entities with this unique combination
    """

    annotation_contents: str
    layer_name: str
    color_r: int
    color_g: int
    color_b: int
    color_aci: int | None
    entity_type: str
    entity_count: int


class ExtractionIssue(TypedDict):
    """
    Record for tracking extraction issues such as unresolved anonymous blocks.

    Used in the extraction_issues field of ExtractionResult to report blocks
    that could not be fully processed during extraction.

    Attributes:
        issue_type: Type of issue (e.g., "Unresolved Anonymous Block")
        block_name: The anonymous block name (e.g., "*U1")
        layer_name: Layer where the block was inserted
        insertion_count: Number of times this block was inserted
        details: Additional context (e.g., "No AcDbBlockRepBTag XDATA found")
    """

    issue_type: str
    block_name: str
    layer_name: str
    insertion_count: int
    details: str


class ContentZoneData(TypedDict):
    """
    Results from content zone detection analysis.

    Contains suggested trim values derived from the detected content zone shape
    relative to the block's bounding box. The content zone is the closed polygon
    with the largest net area (own area minus areas of contained polygons).

    Attributes:
        suggested_trim_left: Distance from block left edge to content zone left edge,
                            or None if no content zone detected
        suggested_trim_right: Distance from content zone right edge to block right edge,
                             or None if no content zone detected
        suggested_trim_top: Distance from content zone top edge to block top edge,
                           or None if no content zone detected
        suggested_trim_bottom: Distance from block bottom edge to content zone bottom edge,
                              or None if no content zone detected
        content_zone_detected: True if a valid content zone was found, False otherwise
        content_zone_width: Width of content zone bounding box (cz_max_x - cz_min_x),
                           or None if no content zone detected
        content_zone_height: Height of content zone bounding box (cz_max_y - cz_min_y),
                            or None if no content zone detected
        polygon_count: Total number of closed polygons found BEFORE any filtering
                      (LWPOLYLINE + LINE cycles)
        filtered_polygon_count: Count of polygons AFTER all filtering (side + area
                               filters applied)
    """

    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
    content_zone_width: float | None
    content_zone_height: float | None
    polygon_count: int
    filtered_polygon_count: int


class PolygonMetrics(TypedDict):
    """
    Metrics calculated for a single polygon after precision fix.

    Attributes:
        area_raw: Area in DXF drawing units squared
        shortest_side: Length of shortest straight side in DXF units
        perimeter: Total perimeter length in DXF units
    """

    area_raw: float
    shortest_side: float
    perimeter: float


class BlockDefinitionRecord(TypedDict):
    """
    Complete record for a block definition with insertion and nesting status.

    Used in the all_block_definitions field of ExtractionResult to track
    every block definition in the DXF file regardless of insertion status.

    Attributes:
        block_raw_name: Original name from doc.blocks (e.g., "*U1", "DOOR")
        block_resolved_name: Resolved name (same as raw for non-anonymous blocks)
        block_insertion_status: One of "Inserted", "Nested Only", "Unused",
                               "System", "Unresolved (*U)", "Unresolved (A$C)"
        block_is_nested: True if this block is inserted inside another block definition
        block_nested_parent_names: List of parent block names containing this block
        block_entity_count: Number of entities in the block definition
    """

    block_raw_name: str
    block_resolved_name: str
    block_insertion_status: str
    block_is_nested: bool
    block_nested_parent_names: list[str]
    block_entity_count: int


class BlockAttributeRecord(TypedDict):
    """
    Single attribute tag-value pair from a block insertion.

    Used to store ATTRIB entity data extracted from INSERT entities.
    Attributes are stored as a list of these records per block name.

    Attributes:
        tag: The attribute tag name (e.g., "PROD1", "BAY#", "DEPT")
        value: The attribute value text (e.g., "Garage", "27-004")
    """

    tag: str
    value: str


class AppSettings(TypedDict, total=False):
    """
    Application settings for the DXF Block Extractor.

    All fields are optional (total=False) to allow partial updates.
    Used by SettingsManager for type-safe settings storage and validation.

    Categories:
    - Filters: Polygon filtering and gap bridging options
    - Performance: Early-exit thresholds for content zone detection
    - Precision: Numeric precision for geometry operations
    - Output: File output and Excel behavior settings
    - Logging: Log viewer and file logging configuration
    """

    # Filters (existing GUI options)
    unit_override: int | None
    precision_fix_enabled: bool
    precision_fix_amount: float | None
    gap_bridge_enabled: bool
    gap_bridge_amount: float | None
    min_area_filter_enabled: bool
    min_area_filter_amount: float | None
    min_side_filter_enabled: bool
    min_side_filter_amount: float | None

    # Pre-Filters (applied before polygon detection)
    skip_curved_entities: bool
    min_line_length_filter_enabled: bool
    min_line_length_filter_amount: float | None

    # Post-Filters (applied after polygon detection)
    curved_filter_enabled: bool

    # Performance (early-exit thresholds only - no thread settings)
    polygon_count_threshold: int
    line_segment_threshold: int
    entity_count_threshold: int

    # Precision
    arc_flattening_sagitta: float
    coord_dedup_epsilon: float
    rotation_tolerance: float

    # Output
    output_directory: str | None
    auto_open_excel: bool
    show_success_dialog: bool
    filename_prefix: str
    include_timestamp: bool

    # Logging
    generate_log_file: bool
    file_log_level: str
    log_viewer_level: str
    log_viewer_auto_scroll: bool
    log_viewer_max_lines: int


class SettingValidation(TypedDict):
    """
    Validation metadata for a single application setting.

    Used by SETTINGS_VALIDATION_REGISTRY to define constraints and defaults
    for each setting in AppSettings.

    Attributes:
        min_value: Minimum allowed value for numeric settings, None for non-numeric
        max_value: Maximum allowed value for numeric settings, None for non-numeric
        default: Default value for the setting (type matches the setting type)
        unit_aware: True if default value varies based on drawing unit code
    """

    min_value: float | int | None
    max_value: float | int | None
    default: float | int | bool | str | None
    unit_aware: bool
