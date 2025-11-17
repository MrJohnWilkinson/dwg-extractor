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
from typing import TypedDict
import ezdxf
from ezdxf import DXFError

from .logger import setup_logger
from .constants import SUPPORTED_EXTENSIONS

logger = setup_logger(__name__)


class ExtractionResult(TypedDict):
    """
    Comprehensive extraction result containing all CAD analysis data.

    Attributes:
        block_counts: Dictionary mapping block names to insertion counts
        block_entities: Dictionary mapping block names to entity count within their definition
        block_layer_pairs: Dictionary mapping (block_name, layer_name) tuples to insertion counts
        layer_insertion_counts: Dictionary mapping layer names to block insertion counts on that layer
        layer_entity_counts: Dictionary mapping layer names to total entity counts on that layer
        entity_type_counts: Dictionary mapping entity type names to their total count in the drawing

    Examples:
        block_layer_pairs: {('DOOR', 'WALLS'): 5, ('DOOR', 'OPENINGS'): 3, ('WINDOW', 'WALLS'): 8}
    """
    block_counts: dict[str, int]
    block_entities: dict[str, int]
    block_layer_pairs: dict[tuple[str, str], int]
    layer_insertion_counts: dict[str, int]
    layer_entity_counts: dict[str, int]
    entity_type_counts: dict[str, int]


def extract_blocks(file_path: str) -> ExtractionResult:
    """
    Extract comprehensive CAD analysis from a DWG or DXF file.

    This function loads a CAD file and extracts:
    - Block insertion counts
    - Entity counts within each block definition
    - Block-layer pairs (unique combinations of block name and layer)
    - Layer-based insertion counts
    - Layer-based total entity counts
    - Global entity type counts

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
        >>> result['layer_insertion_counts']
        {'Piping': 200, 'Equipment': 31}
    """
    logger.info(f"Starting block extraction from {file_path}")

    # Validate file exists
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate file extension
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.error(f"Unsupported file extension: {path.suffix}. Supported: {SUPPORTED_EXTENSIONS}")
        raise ValueError(f"Unsupported file extension: {path.suffix}. Must be .dwg or .dxf")

    try:
        # Load DWG/DXF file
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # Initialize result dictionaries
        block_counts: dict[str, int] = {}
        block_entities: dict[str, int] = {}
        block_layer_pairs: dict[tuple[str, str], int] = {}
        layer_insertion_counts: dict[str, int] = {}
        layer_entity_counts: dict[str, int] = {}
        entity_type_counts: dict[str, int] = {}

        # Extract block definition entity counts
        logger.info("Analyzing block definitions...")
        for block_def in doc.blocks:
            block_name = block_def.name
            # Skip anonymous blocks and modelspace/paperspace
            if block_name.startswith('*'):
                continue

            entity_count = sum(1 for _ in block_def)
            block_entities[block_name] = entity_count

        logger.info(f"Analyzed {len(block_entities)} block definitions")

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
            if entity_type == 'INSERT':
                block_name = entity.dxf.name
                block_counts[block_name] = block_counts.get(block_name, 0) + 1
                layer_insertion_counts[layer_name] = layer_insertion_counts.get(layer_name, 0) + 1

                # Track block-layer pairs
                pair_key = (block_name, layer_name)
                block_layer_pairs[pair_key] = block_layer_pairs.get(pair_key, 0) + 1

        # Log summary
        total_insertions = sum(block_counts.values())
        unique_blocks = len(block_counts)
        total_entities = sum(entity_type_counts.values())
        unique_entity_types = len(entity_type_counts)
        total_layers = len(layer_entity_counts)

        logger.info(f"Found {total_insertions} block insertions across {unique_blocks} unique blocks")
        logger.info(f"Found {len(block_layer_pairs)} unique block-layer pairs")
        logger.info(f"Found {total_entities} total entities across {unique_entity_types} entity types")
        logger.info(f"Found {total_layers} layers in drawing")

        # Return comprehensive result
        result: ExtractionResult = {
            'block_counts': block_counts,
            'block_entities': block_entities,
            'block_layer_pairs': block_layer_pairs,
            'layer_insertion_counts': layer_insertion_counts,
            'layer_entity_counts': layer_entity_counts,
            'entity_type_counts': entity_type_counts
        }

        return result

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF/DWG file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
