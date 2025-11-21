"""
Shared type definitions for the DWG Block Extractor.

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
    Color analysis record for Lines, Polylines, TEXT, and MTEXT entities.

    Contains entity information grouped by RGB color, layer name, and entity type.
    Used in the color_analysis_data field of ExtractionResult.

    Attributes:
        annotation_contents: Text content for TEXT/MTEXT entities, empty string for geometric entities
        layer_name: Layer name of the entity
        color_r: Red component (0-255)
        color_g: Green component (0-255)
        color_b: Blue component (0-255)
        entity_type: Entity type string ('Lines', 'Polylines', 'TEXT', or 'MTEXT')
        entity_count: Count of entities with this unique combination
    """

    annotation_contents: str
    layer_name: str
    color_r: int
    color_g: int
    color_b: int
    entity_type: str
    entity_count: int
