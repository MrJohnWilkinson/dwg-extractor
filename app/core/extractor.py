"""
DWG/DXF extraction logic for the DWG Block Extractor.

This module provides functionality to parse DWG and DXF files using the ezdxf library,
extract comprehensive CAD analysis including block counts, layer metrics, and entity types.

Usage:
    from core.extractor import extract_blocks

    result = extract_blocks('/path/to/drawing.dwg')
    # Returns: ExtractionResult with block_counts, block_entities, layer_insertions, etc.
"""

from pathlib import Path
from typing import Any, TypedDict

import ezdxf
from ezdxf import DXFError

from .constants import SUPPORTED_EXTENSIONS
from .geometry import (
    _calculate_segments,
    _categorize_rotation,
    _get_block_bounding_box,
    _get_intersection_points,
)
from .logger import setup_logger


logger = setup_logger(__name__)


class ExtractionResult(TypedDict):
    """
    Comprehensive extraction result containing all CAD analysis data.

    Attributes:
        block_counts: Dictionary mapping block names to insertion counts
        block_entities: Dictionary mapping block names to entity count within their definition
        block_layer_pairs: Dictionary mapping (block_name, layer_name) tuples to insertion counts
        block_rotation_counts: Dictionary mapping (block_name, layer_name, rotation_category) tuples to insertion counts
                               Rotation categories are strings: '0', '90', '180', '270', 'other'
        block_scale_data: Dictionary mapping (block_name, layer_name) tuples to (x_scale, y_scale) tuples
                          Scale values indicate transformation factors (1.0 = normal, -1.0 = mirrored, 2.0 = 200%)
        layer_block_insertion_counts: Dictionary mapping layer names to block insertion counts on that layer
        layer_entity_counts: Dictionary mapping layer names to total entity counts on that layer
        entity_type_counts: Dictionary mapping entity type names to their total count in the drawing
        block_trimming_data: Dictionary mapping block names to their geometry analysis data.
                             Each block entry contains: native_width (float), native_height (float),
                             vertical_segments (list[float] - left-to-right), horizontal_segments (list[float] - bottom-to-top)

    Examples:
        block_layer_pairs: {('DOOR', 'WALLS'): 5, ('DOOR', 'OPENINGS'): 3, ('WINDOW', 'WALLS'): 8}
        block_rotation_counts: {('DOOR', 'WALLS', '0'): 12, ('DOOR', 'WALLS', '90'): 18, ('DOOR', 'WALLS', '180'): 10}
        block_scale_data: {('DOOR', 'WALLS'): (1.0, 1.0), ('WINDOW', 'WALLS'): (-1.0, 1.0)}
        block_trimming_data: {'SHELF_4FT': {'native_width': 1200.0, 'native_height': 600.0,
                                             'vertical_segments': [50.0, 1100.0, 50.0],
                                             'horizontal_segments': [25.0, 550.0, 25.0]}}
    """

    block_counts: dict[str, int]
    block_entities: dict[str, int]
    block_layer_pairs: dict[tuple[str, str], int]
    block_rotation_counts: dict[tuple[str, str, str], int]
    block_scale_data: dict[tuple[str, str], tuple[float, float]]
    layer_block_insertion_counts: dict[str, int]
    layer_entity_counts: dict[str, int]
    entity_type_counts: dict[str, int]
    block_trimming_data: dict[str, dict[str, Any]]


def extract_blocks(file_path: str) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DWG or DXF file.

    This function loads a CAD file and extracts:
    - Block insertion counts
    - Entity counts within each block definition
    - Block-layer pairs (unique combinations of block name and layer)
    - Block rotation counts for each block-layer pair
    - Layer-based insertion counts
    - Layer-based total entity counts
    - Global entity type counts
    - Block trimming analysis (native dimensions and geometric segments)

    Args:
        file_path: Path to the DWG or DXF file to process

    Returns:
        ExtractionResult TypedDict containing all analysis data.
        All dictionaries will be empty if the file contains no relevant data.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file extension is not supported or file is corrupted

    Examples:
        >>> result = extract_blocks('drawing.dwg')
        >>> result['block_counts']
        {'VALVE_GATE': 142, 'PIPE_SUPPORT': 89}
        >>> result['block_entities']
        {'VALVE_GATE': 8, 'PIPE_SUPPORT': 12}
        >>> result['block_layer_pairs']
        {('VALVE_GATE', 'Piping'): 100, ('VALVE_GATE', 'Equipment'): 42, ('PIPE_SUPPORT', 'Piping'): 89}
        >>> result['layer_block_insertion_counts']
        {'Piping': 200, 'Equipment': 31}
        >>> result['block_trimming_data']
        {'SHELF_4FT': {'native_width': 1200.0, 'native_height': 600.0, 'vertical_segments': [50.0, 1100.0, 50.0], 'horizontal_segments': [25.0, 550.0, 25.0]}}
    """
    logger.info(f"Starting block extraction from {file_path}")

    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.error(
            f"Unsupported file extension: {path.suffix}. Supported: {SUPPORTED_EXTENSIONS}"
        )
        raise ValueError(
            f"Unsupported file extension: {path.suffix}. Must be .dwg or .dxf"
        )

    try:
        # Load DWG/DXF file
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # Initialize result dictionaries
        block_counts: dict[str, int] = {}
        block_entities: dict[str, int] = {}
        block_layer_pairs: dict[tuple[str, str], int] = {}
        block_rotation_counts: dict[tuple[str, str, str], int] = {}
        block_scale_data: dict[tuple[str, str], tuple[float, float]] = {}
        layer_block_insertion_counts: dict[str, int] = {}
        layer_entity_counts: dict[str, int] = {}
        entity_type_counts: dict[str, int] = {}
        block_trimming_data: dict[str, dict[str, Any]] = {}

        # Extract block definition entity counts and geometry analysis
        logger.info("Analyzing block definitions...")
        for block_def in doc.blocks:
            block_name = block_def.name
            # Skip anonymous blocks and modelspace/paperspace
            if block_name.startswith("*"):
                continue

            entity_count = sum(1 for _ in block_def)
            block_entities[block_name] = entity_count

            # Analyze block geometry for trimming assistance
            bbox = _get_block_bounding_box(block_def)
            native_width = round(bbox[2] - bbox[0], 2)
            native_height = round(bbox[3] - bbox[1], 2)

            vertical_points, horizontal_points = _get_intersection_points(block_def)
            vertical_segments = _calculate_segments(vertical_points)
            horizontal_segments = _calculate_segments(horizontal_points)

            block_trimming_data[block_name] = {
                "native_width": native_width,
                "native_height": native_height,
                "vertical_segments": vertical_segments,
                "horizontal_segments": horizontal_segments,
            }

        logger.info(f"Analyzed {len(block_entities)} block definitions")
        logger.info(
            f"Analyzed geometry for {len(block_trimming_data)} block definitions"
        )

        # Iterate through modelspace entities
        logger.info("Analyzing modelspace entities...")
        for entity in msp:
            entity_type = entity.dxftype()
            layer_name = entity.dxf.layer

            # Count entity types
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

            # Count entities per layer
            layer_entity_counts[layer_name] = layer_entity_counts.get(layer_name, 0) + 1

            # Count INSERT entities (block insertions)
            if entity_type == "INSERT":
                block_name = entity.dxf.name
                block_counts[block_name] = block_counts.get(block_name, 0) + 1
                layer_block_insertion_counts[layer_name] = (
                    layer_block_insertion_counts.get(layer_name, 0) + 1
                )

                # Track block-layer pairs
                pair_key = (block_name, layer_name)
                block_layer_pairs[pair_key] = block_layer_pairs.get(pair_key, 0) + 1

                # Track block rotation counts
                rotation = entity.dxf.rotation
                rotation_category = _categorize_rotation(rotation)
                rotation_key = (block_name, layer_name, rotation_category)
                block_rotation_counts[rotation_key] = (
                    block_rotation_counts.get(rotation_key, 0) + 1
                )

                # Extract scale data (X and Y scale factors)
                try:
                    x_scale = entity.dxf.xscale
                    y_scale = entity.dxf.yscale
                except AttributeError:
                    # Default to 1.0 if scale attributes are missing
                    x_scale = 1.0
                    y_scale = 1.0

                # Store scale data for this block-layer pair (only first occurrence)
                if pair_key not in block_scale_data:
                    block_scale_data[pair_key] = (x_scale, y_scale)

        # Log summary
        total_insertions = sum(block_counts.values())
        unique_blocks = len(block_counts)
        total_entities = sum(entity_type_counts.values())
        unique_entity_types = len(entity_type_counts)
        total_layers = len(layer_entity_counts)

        logger.info(
            f"Found {total_insertions} block insertions across {unique_blocks} unique blocks"
        )
        logger.info(f"Found {len(block_layer_pairs)} unique block-layer pairs")
        logger.info(
            f"Tracked rotations for {len(block_rotation_counts)} block-layer-rotation combinations"
        )
        logger.info(
            f"Extracted scale data for {len(block_scale_data)} block-layer pairs"
        )
        logger.info(
            f"Found {total_entities} total entities across {unique_entity_types} entity types"
        )
        logger.info(f"Found {total_layers} layers in drawing")

        # Return comprehensive result
        result: ExtractionResult = {
            "block_counts": block_counts,
            "block_entities": block_entities,
            "block_layer_pairs": block_layer_pairs,
            "block_rotation_counts": block_rotation_counts,
            "block_scale_data": block_scale_data,
            "layer_block_insertion_counts": layer_block_insertion_counts,
            "layer_entity_counts": layer_entity_counts,
            "entity_type_counts": entity_type_counts,
            "block_trimming_data": block_trimming_data,
        }

        return result

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF/DWG file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
