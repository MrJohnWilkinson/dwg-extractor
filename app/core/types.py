"""
Shared type definitions for the DXF Block Extractor.

This module provides TypedDict definitions for internal data structures used
throughout the codebase. Using TypedDict instead of generic dict[str, Any]
improves type safety, IDE support, and code documentation.

Usage:
    from core.types import BlockTrimmingData, ColorAnalysisRecord

    # Type-safe block trimming data
    trimming: BlockTrimmingData = {
        "native_width": 1200.0,
        "native_height": 600.0,
        "vertical_segments": [50.0, 1100.0, 50.0],
        "horizontal_segments": [25.0, 550.0, 25.0],
    }
"""

from typing import TypedDict


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


# Type aliases for ExtractionResult dictionary fields
# These provide semantic meaning to commonly used dict patterns

# Block-related type aliases
BlockCountsDict = dict[str, int]
"""Maps block names to their total insertion count across all layers."""

BlockEntitiesDict = dict[str, int]
"""Maps block names to the entity count within their block definition."""

BlockLayerPairsDict = dict[tuple[str, str], int]
"""Maps (block_name, layer_name) tuples to insertion count on that layer."""

BlockRotationCountsDict = dict[tuple[str, str, str], int]
"""Maps (block_name, layer_name, rotation_category) tuples to count.
Rotation categories: '0', '90', '180', '270', 'other'."""

BlockScaleDataDict = dict[str, set[tuple[float, float]]]
"""Maps block names to sets of unique (x_scale, y_scale) tuples."""

BlockXdataAppsDict = dict[tuple[str, str], set[str]]
"""Maps (block_name, layer_name) tuples to sets of XDATA application IDs."""

BlockTrimmingDataDict = dict[str, BlockTrimmingData]
"""Maps block names to their geometry analysis data."""

# Layer-related type aliases
LayerCountsDict = dict[str, int]
"""Generic dict mapping layer names to integer counts."""

LayerColorsDict = dict[str, set[tuple[int, int, int]]]
"""Maps layer names to sets of unique RGB color tuples."""

# Annotation-related type aliases
AnnotationDataDict = dict[tuple[str, str, str, int, int, int], int]
"""Maps (contents, type, layer_name, color_r, color_g, color_b) tuples to count."""

# Entity-related type aliases
EntityTypeCountsDict = dict[str, int]
"""Maps entity type names (e.g., 'LINE', 'INSERT') to their total count."""

# Color analysis type alias
GeometricEntitiesDict = dict[tuple[int, int, int, int | None, str, str], int]
"""Maps (color_r, color_g, color_b, color_aci, layer_name, entity_type) tuples to count."""
