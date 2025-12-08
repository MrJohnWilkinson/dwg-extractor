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
    from core.types import BlockTrimmingData, ColorAnalysisRecord, BlockLayerKey

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
        polygon_count: Total number of closed polygons found (LWPOLYLINE + LINE cycles)
    """

    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool
    content_zone_width: float | None
    content_zone_height: float | None
    polygon_count: int
