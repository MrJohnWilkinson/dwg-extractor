"""
DWG/DXF extraction logic for the DWG Block Extractor.

This module provides functionality to parse DWG and DXF files using the ezdxf library,
iterate through modelspace INSERT entities, and count block insertions by name.

Usage:
    from core.extractor import extract_blocks

    block_counts = extract_blocks('/path/to/drawing.dwg')
    # Returns: {'VALVE_GATE': 10, 'PIPE_SUPPORT': 5, ...}
"""

from pathlib import Path
import ezdxf
from ezdxf import DXFError

from .logger import setup_logger
from .constants import SUPPORTED_EXTENSIONS

logger = setup_logger(__name__)


def extract_blocks(file_path: str) -> dict[str, int]:
    """
    Extract block insertion counts from a DWG or DXF file.

    This function loads a CAD file, iterates through all INSERT entities in the
    modelspace, and counts how many times each block is inserted.

    Args:
        file_path: Path to the DWG or DXF file to process

    Returns:
        Dictionary mapping block names to insertion counts.
        Returns empty dict {} if the file contains no block insertions.

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file extension is not supported or file is corrupted

    Examples:
        >>> counts = extract_blocks('drawing.dwg')
        >>> counts
        {'VALVE_GATE': 142, 'PIPE_SUPPORT': 89, 'EQUIPMENT_TAG': 67}

        >>> total_blocks = sum(counts.values())
        >>> unique_blocks = len(counts)
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

        # Initialize block counts dictionary
        block_counts = {}

        # Iterate through modelspace entities and count INSERT entities
        for entity in msp:
            if entity.dxftype() == 'INSERT':
                block_name = entity.dxf.name
                block_counts[block_name] = block_counts.get(block_name, 0) + 1

        total_count = sum(block_counts.values())
        unique_count = len(block_counts)
        logger.info(f"Found {total_count} block insertions across {unique_count} unique blocks")

        return block_counts

    except (DXFError, IOError, OSError) as e:
        logger.error(f"Invalid or corrupted DXF/DWG file: {file_path} - {str(e)}")
        raise ValueError(f"Invalid or corrupted file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {str(e)}", exc_info=True)
        raise
