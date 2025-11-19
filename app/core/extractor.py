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
from ezdxf.layouts import BlockLayout

from .constants import SUPPORTED_EXTENSIONS
from .logger import setup_logger


logger = setup_logger(__name__)


def _get_block_bounding_box(
    block_def: BlockLayout,
) -> tuple[float, float, float, float]:
    """
    Extract the bounding box (extents) of a block definition at 0° rotation.

    This function iterates through all entities in the block definition and calculates
    the minimum and maximum X and Y coordinates to determine the block's bounding box.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the bounding box extents.
        Returns (0, 0, 0, 0) for empty blocks or blocks with no geometric entities.

    Examples:
        >>> block_def = doc.blocks.get('SHELF_4FT')
        >>> _get_block_bounding_box(block_def)
        (0.0, 0.0, 1200.0, 600.0)
    """
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    has_geometry = False

    for entity in block_def:
        entity_type = entity.dxftype()

        # Extract coordinates based on entity type
        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            min_x = min(min_x, start.x, end.x)
            max_x = max(max_x, start.x, end.x)
            min_y = min(min_y, start.y, end.y)
            max_y = max(max_y, start.y, end.y)
            has_geometry = True

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                for point in entity.get_points():  # type: ignore[attr-defined]
                    x, y = point[0], point[1]
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                    has_geometry = True
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            min_x = min(min_x, center.x - radius)
            max_x = max(max_x, center.x + radius)
            min_y = min(min_y, center.y - radius)
            max_y = max(max_y, center.y + radius)
            has_geometry = True

        elif entity_type == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius
            # Simplified bounding box for arcs (use full circle extents)
            min_x = min(min_x, center.x - radius)
            max_x = max(max_x, center.x + radius)
            min_y = min(min_y, center.y - radius)
            max_y = max(max_y, center.y + radius)
            has_geometry = True

        elif entity_type == "POINT":
            location = entity.dxf.location
            min_x = min(min_x, location.x)
            max_x = max(max_x, location.x)
            min_y = min(min_y, location.y)
            max_y = max(max_y, location.y)
            has_geometry = True

    # Return zeros if no geometry found
    if not has_geometry:
        return (0.0, 0.0, 0.0, 0.0)

    return (min_x, min_y, max_x, max_y)


def _get_intersection_points(block_def: BlockLayout) -> tuple[list[float], list[float]]:
    """
    Identify unique vertical and horizontal intersection points in a block definition.

    This function extracts all vertex coordinates from geometric entities in the block
    and identifies unique X-coordinates (vertical intersections) and Y-coordinates
    (horizontal intersections). Duplicate points are filtered using a floating-point
    tolerance (epsilon = 0.01) to handle precision issues.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Tuple of (sorted_vertical_points, sorted_horizontal_points) where:
        - sorted_vertical_points: List of unique X-coordinates sorted ascending (left-to-right)
        - sorted_horizontal_points: List of unique Y-coordinates sorted ascending (bottom-to-top)

    Examples:
        >>> block_def = doc.blocks.get('SHELF_4FT')
        >>> _get_intersection_points(block_def)
        ([0.0, 50.0, 1150.0, 1200.0], [0.0, 25.0, 575.0, 600.0])
    """
    epsilon = 0.01  # Tolerance for floating-point comparison
    x_coords: set[float] = set()
    y_coords: set[float] = set()

    for entity in block_def:
        entity_type = entity.dxftype()

        # Extract coordinates based on entity type
        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            x_coords.add(start.x)
            x_coords.add(end.x)
            y_coords.add(start.y)
            y_coords.add(end.y)

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                for point in entity.get_points():  # type: ignore[attr-defined]
                    x_coords.add(point[0])
                    y_coords.add(point[1])
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            # Add circle bounding box corners
            x_coords.add(center.x - radius)
            x_coords.add(center.x + radius)
            y_coords.add(center.y - radius)
            y_coords.add(center.y + radius)

        elif entity_type == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius
            # Add arc bounding box corners (simplified)
            x_coords.add(center.x - radius)
            x_coords.add(center.x + radius)
            y_coords.add(center.y - radius)
            y_coords.add(center.y + radius)

        elif entity_type == "POINT":
            location = entity.dxf.location
            x_coords.add(location.x)
            y_coords.add(location.y)

    # Sort and deduplicate with epsilon tolerance
    def deduplicate_with_tolerance(coords: set[float], tol: float) -> list[float]:
        sorted_coords = sorted(coords)
        if not sorted_coords:
            return []

        result = [sorted_coords[0]]
        for coord in sorted_coords[1:]:
            if abs(coord - result[-1]) > tol:
                result.append(coord)
        return result

    vertical_points = deduplicate_with_tolerance(x_coords, epsilon)
    horizontal_points = deduplicate_with_tolerance(y_coords, epsilon)

    return (vertical_points, horizontal_points)


def _calculate_segments(intersection_points: list[float]) -> list[float]:
    """
    Calculate distances between consecutive intersection points.

    This function takes a sorted list of intersection points and calculates
    the segment sizes (distances) between each consecutive pair of points.

    Args:
        intersection_points: Sorted list of coordinate values (X or Y)

    Returns:
        List of segment sizes (distances between consecutive points).
        Returns empty list if fewer than 2 points provided.
        Segments are rounded to 2 decimal places for readability.

    Examples:
        >>> _calculate_segments([0, 50, 1150, 1200])
        [50.0, 1100.0, 50.0]
        >>> _calculate_segments([0])
        []
        >>> _calculate_segments([])
        []
    """
    if len(intersection_points) < 2:
        return []

    segments = []
    for i in range(len(intersection_points) - 1):
        segment_size = intersection_points[i + 1] - intersection_points[i]
        segments.append(round(segment_size, 2))

    return segments


def _categorize_rotation(angle: float) -> str:
    """
    Categorize a rotation angle into standard rotation categories.

    This function normalizes rotation angles to the 0-360 range and categorizes them
    as standard orthogonal rotations (0°, 90°, 180°, 270°) or 'other'.
    A tolerance of ±1° is used for standard angles to handle floating-point precision
    and near-orthogonal manual rotations.

    Args:
        angle: Rotation angle in degrees (can be negative or > 360)

    Returns:
        String representing rotation category: '0', '90', '180', '270', or 'other'

    Examples:
        >>> _categorize_rotation(0.0)
        '0'
        >>> _categorize_rotation(90.5)
        '90'
        >>> _categorize_rotation(45.0)
        'other'
        >>> _categorize_rotation(-90.0)
        '270'
        >>> _categorize_rotation(450.0)
        '90'
    """
    # Normalize angle to 0-360 range
    normalized = angle % 360

    # Check for standard angles with ±1° tolerance
    if abs(normalized - 0) <= 1 or abs(normalized - 360) <= 1:
        return "0"
    elif abs(normalized - 90) <= 1:
        return "90"
    elif abs(normalized - 180) <= 1:
        return "180"
    elif abs(normalized - 270) <= 1:
        return "270"
    else:
        return "other"


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
