"""
Geometric calculation utilities for CAD block analysis.

This module provides functions for bounding box calculation, intersection point detection,
segment analysis, and rotation categorization. These utilities support the extraction and
analysis of geometric properties from CAD block definitions.

Usage:
    from core.geometry import _get_block_bounding_box, _categorize_rotation

    bbox = _get_block_bounding_box(block_def)
    rotation_category = _categorize_rotation(90.5)
"""

from ezdxf.layouts import BlockLayout

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
        logger.debug(f"Bounding box: processing entity type {entity_type}")

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
        logger.debug("Bounding box: no geometry found, returning zeros")
        return (0.0, 0.0, 0.0, 0.0)

    logger.debug(f"Bounding box result: ({min_x}, {min_y}, {max_x}, {max_y})")
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

    logger.debug(
        f"Intersection points: {len(x_coords)} x-coords, {len(y_coords)} y-coords before deduplication"
    )
    vertical_points = deduplicate_with_tolerance(x_coords, epsilon)
    horizontal_points = deduplicate_with_tolerance(y_coords, epsilon)
    logger.debug(
        f"Intersection points: {len(vertical_points)} vertical, {len(horizontal_points)} horizontal after deduplication"
    )

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
        logger.debug("Calculate segments: fewer than 2 points, returning empty list")
        return []

    segments = []
    for i in range(len(intersection_points) - 1):
        segment_size = intersection_points[i + 1] - intersection_points[i]
        segments.append(round(segment_size, 2))

    logger.debug(f"Calculate segments: {len(intersection_points)} points -> {len(segments)} segments: {segments}")
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
        result = "0"
    elif abs(normalized - 90) <= 1:
        result = "90"
    elif abs(normalized - 180) <= 1:
        result = "180"
    elif abs(normalized - 270) <= 1:
        result = "270"
    else:
        result = "other"

    logger.debug(f"Categorize rotation: {angle}° -> normalized={normalized}° -> category={result}")
    return result
