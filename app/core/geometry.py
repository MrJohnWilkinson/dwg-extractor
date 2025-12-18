"""
Geometric calculation utilities for CAD block analysis.

This module provides functions for bounding box calculation, intersection point detection,
segment analysis, rotation categorization, and content zone detection. These utilities
support the extraction and analysis of geometric properties from CAD block definitions.

Content zone detection identifies the primary shape within a block by:
1. Extracting closed polygons from LWPOLYLINE and LINE entities
2. Calculating net areas (own area minus contained polygon areas)
3. Selecting the polygon with the largest net area as the content zone
4. Deriving trim values from the content zone bounding box

Usage:
    from core.geometry import _get_block_bounding_box, _categorize_rotation, _detect_content_zone

    bbox = _get_block_bounding_box(block_def)
    rotation_category = _categorize_rotation(90.5)
    content_zone = _detect_content_zone(block_def, bbox)
"""

import math
import threading
import time
from typing import Any

from ezdxf.layouts import BlockLayout
from ezdxf.path import from_hatch, make_path
from shapely import Point
from shapely import Polygon as ShapelyPolygon
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, snap, unary_union

from .constants import (
    ARC_FLATTENING_SAGITTA,
    DEFAULT_COORD_DEDUP_EPSILON,
    DEFAULT_ROTATION_TOLERANCE,
    ENTITY_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
from .logger import setup_logger
from .types import ContentZoneData, Polygon


logger = setup_logger(__name__)


def _to_shapely_polygon(polygon: Polygon) -> ShapelyPolygon:
    """Convert internal Polygon type to Shapely Polygon."""
    return ShapelyPolygon(polygon)


def _from_shapely_polygon(shapely_poly: ShapelyPolygon) -> Polygon:
    """Convert Shapely Polygon to internal Polygon type."""
    coords = list(shapely_poly.exterior.coords)[:-1]  # Exclude closing point
    return [(float(x), float(y)) for x, y in coords]


def calculate_polygon_area(polygon: Polygon) -> float:
    """
    Calculate the surface area of a polygon.

    Uses Shapely for accurate area calculation. This is the public API
    for area calculation, suitable for use in polygon filtering.

    Args:
        polygon: List of (x, y) vertices from _extract_paint_bucket_regions()

    Returns:
        Area in DXF drawing units squared (always positive).
        Returns 0.0 for degenerate polygons (fewer than 3 vertices).

    Examples:
        >>> calculate_polygon_area([(0, 0), (10, 0), (10, 10), (0, 10)])
        100.0
        >>> calculate_polygon_area([(0, 0), (3, 0), (3, 4)])
        6.0
    """
    if len(polygon) < 3:
        return 0.0
    shapely_poly = ShapelyPolygon(polygon)
    return abs(shapely_poly.area)


def calculate_shortest_straight_side(
    polygon: Polygon,
    angle_tolerance: float = 1.0,
) -> tuple[float, int]:
    """
    Calculate the shortest straight side and total side count of a polygon.

    Merges consecutive collinear edges into single sides before
    finding the minimum. This correctly handles cases where a single
    straight side is represented as multiple LINE segments in the DXF
    (e.g., LINE1 Part1 + LINE1 Part2 being counted as one side).

    Args:
        polygon: List of (x, y) vertices (closed polygon, no repeat of first point)
        angle_tolerance: Maximum angle deviation to consider edges collinear (degrees).
                        Default 1.0 degree handles minor coordinate variations.

    Returns:
        Tuple of (shortest_side_length, side_count) where:
        - shortest_side_length: Length of shortest merged side in DXF units
        - side_count: Total number of straight sides after collinear merging

        For rectangles, side_count will be 4.
        For complex shapes, side_count will be > 4.
        Returns (0.0, 0) for degenerate polygons (fewer than 3 vertices).

    Examples:
        >>> calculate_shortest_straight_side([(0, 0), (100, 0), (100, 50), (0, 50)])
        (50.0, 4)
        >>> # Rectangle with split bottom edge - still finds 50 as shortest, 4 sides
        >>> calculate_shortest_straight_side([(0, 0), (50, 0), (100, 0), (100, 50), (0, 50)])
        (50.0, 4)
    """
    if len(polygon) < 3:
        return (0.0, 0)

    # Close the polygon by appending first vertex
    vertices = polygon + [polygon[0]]

    def edge_angle(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate angle of edge in degrees (0-180 range)."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        return angle % 180

    def edge_length(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def angles_collinear(a1: float, a2: float, tolerance: float) -> bool:
        """Check if two angles are within tolerance (handles wraparound)."""
        diff = abs(a1 - a2)
        return diff <= tolerance or abs(diff - 180) <= tolerance

    # Build list of merged straight sides
    straight_sides: list[float] = []

    i = 0
    while i < len(vertices) - 1:
        # Start a new side
        side_start = vertices[i]
        current_angle = edge_angle(vertices[i], vertices[i + 1])

        # Extend side while consecutive edges are collinear
        j = i + 1
        while j < len(vertices) - 1:
            next_angle = edge_angle(vertices[j], vertices[j + 1])
            if angles_collinear(current_angle, next_angle, angle_tolerance):
                j += 1
            else:
                break

        # Calculate total length of merged side
        side_end = vertices[j]
        side_length = edge_length(side_start, side_end)

        if side_length > 1e-9:  # Ignore degenerate edges
            straight_sides.append(side_length)

        i = j

    if not straight_sides:
        return (0.0, 0)
    return (min(straight_sides), len(straight_sides))


class GeometryAbortedError(Exception):
    """
    Exception raised when a geometry operation is aborted.

    This exception is raised when an abort_event is set during long-running
    geometry operations like cycle detection or net area calculation, allowing
    the calling code to handle graceful cancellation.
    """

    pass


def _get_arc_bounding_box(
    center_x: float,
    center_y: float,
    radius: float,
    start_angle: float,
    end_angle: float,
) -> tuple[float, float, float, float]:
    """
    Calculate the accurate bounding box of an arc based on its angular extent.

    Unlike simplified full-circle bounding boxes, this function calculates
    the actual bounds by considering only:
    1. The arc's start point
    2. The arc's end point
    3. Any cardinal directions (0, 90, 180, 270 degrees) that fall within the arc span

    The algorithm handles wrap-around arcs (e.g., arc from 350 to 10 degrees)
    correctly by treating the arc span as counter-clockwise from start to end angle.

    Args:
        center_x: X-coordinate of the arc center
        center_y: Y-coordinate of the arc center
        radius: Radius of the arc
        start_angle: Start angle in degrees (counter-clockwise from positive X-axis)
        end_angle: End angle in degrees (counter-clockwise from positive X-axis)

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the accurate bounding box.

    Examples:
        >>> _get_arc_bounding_box(0, 0, 100, 0, 90)  # Quarter arc, first quadrant
        (0.0, 0.0, 100.0, 100.0)
        >>> _get_arc_bounding_box(0, 0, 100, 270, 360)  # Quarter arc, fourth quadrant
        (0.0, -100.0, 100.0, 0.0)
    """
    # Normalize start angle to [0, 360) range
    start = start_angle % 360
    end = end_angle % 360

    # Calculate start and end points
    start_rad = math.radians(start)
    end_rad = math.radians(end)

    start_x = center_x + radius * math.cos(start_rad)
    start_y = center_y + radius * math.sin(start_rad)
    end_x = center_x + radius * math.cos(end_rad)
    end_y = center_y + radius * math.sin(end_rad)

    # Initialize bounds with start and end points
    min_x = min(start_x, end_x)
    max_x = max(start_x, end_x)
    min_y = min(start_y, end_y)
    max_y = max(start_y, end_y)

    # Handle wrap-around: if end <= start, the arc crosses 0 degrees
    # Extend span_end by 360 to handle the wrap-around case
    span_end = end if end > start else end + 360

    def angle_in_span(angle: float) -> bool:
        """Check if a cardinal angle falls within the arc span."""
        # Check the angle and angle + 360 (for wrap-around cases)
        return start <= angle <= span_end or start <= angle + 360 <= span_end

    # Check each cardinal direction and extend bounds if in span
    # 0 degrees (right): affects max_x
    if angle_in_span(0) or angle_in_span(360):
        max_x = max(max_x, center_x + radius)

    # 90 degrees (top): affects max_y
    if angle_in_span(90):
        max_y = max(max_y, center_y + radius)

    # 180 degrees (left): affects min_x
    if angle_in_span(180):
        min_x = min(min_x, center_x - radius)

    # 270 degrees (bottom): affects min_y
    if angle_in_span(270):
        min_y = min(min_y, center_y - radius)

    return (min_x, min_y, max_x, max_y)


def _transform_bbox_points(
    bbox: tuple[float, float, float, float],
    insert: Any,
) -> list[tuple[float, float]]:
    """
    Transform a bounding box by an INSERT entity's transformation properties.

    Applies the INSERT entity's scale, rotation, and translation to all four
    corners of the bounding box. The transformation order is: scale -> rotation
    -> translation, matching CAD system conventions.

    Args:
        bbox: Tuple of (min_x, min_y, max_x, max_y) representing the source bounding box.
        insert: ezdxf INSERT entity with dxf.insert (position), dxf.xscale, dxf.yscale,
                and dxf.rotation properties.

    Returns:
        List of 4 transformed (x, y) corner points.

    Examples:
        >>> # Identity transform (scale=1, rotation=0, position=0,0)
        >>> _transform_bbox_points((0, 0, 10, 10), insert)  # insert at origin, no scale/rotation
        [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

        >>> # Translation only (position offset)
        >>> _transform_bbox_points((0, 0, 10, 10), insert)  # insert at (5, 5)
        [(5.0, 5.0), (15.0, 5.0), (15.0, 15.0), (5.0, 15.0)]
    """
    min_x, min_y, max_x, max_y = bbox

    # Extract INSERT transformation properties
    insert_point = insert.dxf.insert
    insert_x = insert_point.x
    insert_y = insert_point.y
    scale_x = insert.dxf.xscale
    scale_y = insert.dxf.yscale
    rotation_deg = insert.dxf.rotation
    rotation_rad = math.radians(rotation_deg)

    # Define all 4 corners of the bbox
    corners = [
        (min_x, min_y),  # bottom-left
        (max_x, min_y),  # bottom-right
        (max_x, max_y),  # top-right
        (min_x, max_y),  # top-left
    ]

    # Transform each corner: scale -> rotation -> translation
    transformed: list[tuple[float, float]] = []
    cos_r = math.cos(rotation_rad)
    sin_r = math.sin(rotation_rad)

    for x, y in corners:
        # Step 1: Apply scale
        x_scaled = x * scale_x
        y_scaled = y * scale_y

        # Step 2: Apply rotation
        x_rotated = x_scaled * cos_r - y_scaled * sin_r
        y_rotated = x_scaled * sin_r + y_scaled * cos_r

        # Step 3: Apply translation
        x_final = x_rotated + insert_x
        y_final = y_rotated + insert_y

        transformed.append((x_final, y_final))

    return transformed


def _get_block_bounding_box(
    block_def: BlockLayout,
    doc: Any | None = None,
    processed_blocks: set[str] | None = None,
) -> tuple[float, float, float, float]:
    """
    Extract the bounding box (extents) of a block definition at 0 degree rotation.

    This function iterates through all entities in the block definition and calculates
    the minimum and maximum X and Y coordinates to determine the block's bounding box.

    When a `doc` parameter is provided, INSERT entities (block references) are processed
    recursively. The nested block's bounding box is calculated and transformed by the
    INSERT's scale, rotation, and position, then included in the overall bounding box.
    Circular references are detected and prevented using the `processed_blocks` set.

    Args:
        block_def: ezdxf block definition object
        doc: Optional ezdxf Drawing document for nested block lookup. When provided,
             INSERT entities are recursively expanded. Default None (INSERTs ignored).
        processed_blocks: Optional set of block names already processed in the current
             recursion chain. Used internally to prevent infinite loops on circular
             block references. Default None (initialized automatically).

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the bounding box extents.
        Returns (0, 0, 0, 0) for empty blocks or blocks with no geometric entities.

    Examples:
        >>> block_def = doc.blocks.get('SHELF_4FT')
        >>> _get_block_bounding_box(block_def)
        (0.0, 0.0, 1200.0, 600.0)

        >>> # With nested INSERT expansion
        >>> _get_block_bounding_box(block_def, doc)
        (0.0, 0.0, 1200.0, 600.0)  # May be larger if nested blocks extend beyond
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
                # Use make_path to correctly interpret bulge values as arc segments
                path = make_path(entity)
                # Flatten to capture arc extents
                for vertex in path.flattening(ARC_FLATTENING_SAGITTA):
                    min_x = min(min_x, vertex.x)
                    max_x = max(max_x, vertex.x)
                    min_y = min(min_y, vertex.y)
                    max_y = max(max_y, vertex.y)
                    has_geometry = True
            except (AttributeError, IndexError, TypeError):
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
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            # Accurate bounding box based on arc's angular extent
            arc_min_x, arc_min_y, arc_max_x, arc_max_y = _get_arc_bounding_box(
                center.x, center.y, radius, start_angle, end_angle
            )
            min_x = min(min_x, arc_min_x)
            max_x = max(max_x, arc_max_x)
            min_y = min(min_y, arc_min_y)
            max_y = max(max_y, arc_max_y)
            has_geometry = True

        elif entity_type == "ELLIPSE":
            try:
                # Use flattening to get accurate ellipse boundary points
                vertices = list(entity.flattening(ARC_FLATTENING_SAGITTA))  # type: ignore[attr-defined]
                for vertex in vertices:
                    min_x = min(min_x, vertex.x)
                    max_x = max(max_x, vertex.x)
                    min_y = min(min_y, vertex.y)
                    max_y = max(max_y, vertex.y)
                has_geometry = True
            except (AttributeError, TypeError, ValueError):
                pass  # Skip malformed ellipses

        elif entity_type == "SPLINE":
            try:
                # Use flattening to get accurate spline boundary points
                vertices = list(entity.flattening(ARC_FLATTENING_SAGITTA))  # type: ignore[attr-defined]
                for vertex in vertices:
                    min_x = min(min_x, vertex.x)
                    max_x = max(max_x, vertex.x)
                    min_y = min(min_y, vertex.y)
                    max_y = max(max_y, vertex.y)
                has_geometry = True
            except (AttributeError, TypeError, ValueError):
                # Fallback to control points for degenerate splines
                try:
                    for point in entity.control_points:  # type: ignore[attr-defined]
                        min_x = min(min_x, point.x)
                        max_x = max(max_x, point.x)
                        min_y = min(min_y, point.y)
                        max_y = max(max_y, point.y)
                    has_geometry = True
                except (AttributeError, TypeError):
                    pass  # Skip completely malformed splines

        elif entity_type == "POINT":
            location = entity.dxf.location
            min_x = min(min_x, location.x)
            max_x = max(max_x, location.x)
            min_y = min(min_y, location.y)
            max_y = max(max_y, location.y)
            has_geometry = True

        elif entity_type == "INSERT" and doc is not None:
            # Handle nested block references (INSERT entities)
            # Initialize processed_blocks set if not provided
            if processed_blocks is None:
                processed_blocks = set()

            # Get the current block name for circular reference tracking
            current_block_name = block_def.name

            # Get the nested block name from the INSERT entity
            nested_block_name = entity.dxf.name

            # Check if nested block exists in document
            if nested_block_name in doc.blocks:
                # Check for circular reference
                if nested_block_name not in processed_blocks:
                    # Get the nested block definition
                    nested_block = doc.blocks[nested_block_name]

                    # Create new processed set including current block
                    new_processed = processed_blocks | {current_block_name}

                    # Recursively get nested block's bounding box
                    nested_bbox = _get_block_bounding_box(
                        nested_block, doc, new_processed
                    )

                    # Only process if nested block has valid geometry
                    if nested_bbox != (0.0, 0.0, 0.0, 0.0):
                        # Transform nested bbox corners by INSERT properties
                        transformed_points = _transform_bbox_points(nested_bbox, entity)

                        # Update bounds from transformed corners
                        for tx, ty in transformed_points:
                            min_x = min(min_x, tx)
                            max_x = max(max_x, tx)
                            min_y = min(min_y, ty)
                            max_y = max(max_y, ty)
                        has_geometry = True
                else:
                    logger.debug(
                        f"Bounding box: skipping circular reference to {nested_block_name}"
                    )

    # Return zeros if no geometry found
    if not has_geometry:
        logger.debug("Bounding box: no geometry found, returning zeros")
        return (0.0, 0.0, 0.0, 0.0)

    logger.debug(f"Bounding box result: ({min_x}, {min_y}, {max_x}, {max_y})")
    return (min_x, min_y, max_x, max_y)


def _get_intersection_points(
    block_def: BlockLayout,
    epsilon: float = DEFAULT_COORD_DEDUP_EPSILON,
) -> tuple[list[float], list[float]]:
    """
    Identify unique vertical and horizontal intersection points in a block definition.

    This function extracts all vertex coordinates from geometric entities in the block
    and identifies unique X-coordinates (vertical intersections) and Y-coordinates
    (horizontal intersections). Duplicate points are filtered using a floating-point
    tolerance (epsilon) to handle precision issues.

    Args:
        block_def: ezdxf block definition object
        epsilon: Tolerance for floating-point comparison when deduplicating
                 coordinates. Default: DEFAULT_COORD_DEDUP_EPSILON (0.01)

    Returns:
        Tuple of (sorted_vertical_points, sorted_horizontal_points) where:
        - sorted_vertical_points: List of unique X-coordinates sorted ascending (left-to-right)
        - sorted_horizontal_points: List of unique Y-coordinates sorted ascending (bottom-to-top)

    Examples:
        >>> block_def = doc.blocks.get('SHELF_4FT')
        >>> _get_intersection_points(block_def)
        ([0.0, 50.0, 1150.0, 1200.0], [0.0, 25.0, 575.0, 600.0])
    """
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

    logger.debug(
        f"Calculate segments: {len(intersection_points)} points -> {len(segments)} segments: {segments}"
    )
    return segments


def _categorize_rotation(
    angle: float,
    tolerance: float = DEFAULT_ROTATION_TOLERANCE,
) -> str:
    """
    Categorize a rotation angle into standard rotation categories.

    This function normalizes rotation angles to the 0-360 range and categorizes them
    as standard orthogonal rotations (0°, 90°, 180°, 270°) or 'other'.
    A configurable tolerance is used for standard angles to handle floating-point
    precision and near-orthogonal manual rotations.

    Args:
        angle: Rotation angle in degrees (can be negative or > 360)
        tolerance: Tolerance in degrees for matching standard angles.
                   Default: DEFAULT_ROTATION_TOLERANCE (1.0)

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

    # Check for standard angles with configurable tolerance
    if abs(normalized - 0) <= tolerance or abs(normalized - 360) <= tolerance:
        result = "0"
    elif abs(normalized - 90) <= tolerance:
        result = "90"
    elif abs(normalized - 180) <= tolerance:
        result = "180"
    elif abs(normalized - 270) <= tolerance:
        result = "270"
    else:
        result = "other"

    logger.debug(
        f"Categorize rotation: {angle}° -> normalized={normalized}° -> category={result}"
    )
    return result


# =============================================================================
# Content Zone Detection Functions
# =============================================================================


def _empty_content_zone_data() -> ContentZoneData:
    """
    Return an empty ContentZoneData with all trim values as None.

    Returns:
        ContentZoneData with content_zone_detected=False and all trim values as None.
    """
    return ContentZoneData(
        suggested_trim_left=None,
        suggested_trim_right=None,
        suggested_trim_top=None,
        suggested_trim_bottom=None,
        content_zone_detected=False,
        content_zone_width=None,
        content_zone_height=None,
        polygon_count=0,
        filtered_polygon_count=0,
    )


def _count_line_segments(block_def: BlockLayout) -> int:
    """
    Count the number of LINE entities in a block definition.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Number of LINE entities in the block.
    """
    count = 0
    for entity in block_def:
        if entity.dxftype() == "LINE":
            count += 1
    return count


def _estimate_arc_segments(radius: float, angle_rad: float, sagitta: float) -> int:
    """
    Calculate segments needed to approximate arc within sagitta tolerance.

    Uses the mathematical relationship between sagitta and arc geometry:
    - sagitta = radius * (1 - cos(theta/2)) where theta is angle per segment
    - Solving for segments: n = angle / (2 * arccos(1 - sagitta/radius))

    This produces segment counts that closely match ezdxf's flattening() output.

    Args:
        radius: Arc radius in drawing units.
        angle_rad: Total arc angle in radians.
        sagitta: Maximum allowed sagitta (distance from arc to chord center).

    Returns:
        Estimated number of segments needed. Always >= 1.

    Examples:
        >>> _estimate_arc_segments(100, 2*math.pi, 0.1)  # Large circle
        ~141 segments
        >>> _estimate_arc_segments(10, 2*math.pi, 0.1)  # Small circle
        ~45 segments
        >>> _estimate_arc_segments(50, math.pi/2, 0.1)  # 90-degree arc
        ~18 segments
    """
    if radius <= 0 or sagitta <= 0 or angle_rad <= 0:
        return 1

    ratio = sagitta / radius
    if ratio >= 1:
        return 1  # Sagitta larger than radius - use minimum

    # Angle per segment that achieves target sagitta
    theta_per_segment = 2 * math.acos(1 - ratio)

    # Number of segments for the arc
    segments = int(math.ceil(angle_rad / theta_per_segment))
    return max(1, segments)


def _estimate_edge_count(block_def: BlockLayout) -> int:
    """
    Fast O(n) edge count estimation without coordinate extraction.

    Counts the number of edges that would be extracted by _extract_all_edges()
    without actually creating LineString objects or extracting coordinates.
    Used for threshold checks before expensive geometry operations.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Estimated number of edges in the block.
    """
    count = 0
    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            count += 1

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                # Count vertices to estimate edge count
                # Each vertex pair = 1 edge, plus closing edge if closed
                points = list(entity.get_points())  # type: ignore[attr-defined]
                vertex_count = len(points)
                if vertex_count >= 2:
                    count += vertex_count - 1
                    if hasattr(entity, "closed") and entity.closed:
                        count += 1
            except (AttributeError, IndexError):
                continue

        elif entity_type == "CIRCLE":
            # Dynamic estimation based on radius and sagitta
            try:
                radius = entity.dxf.radius
                count += _estimate_arc_segments(
                    radius, 2 * math.pi, ARC_FLATTENING_SAGITTA
                )
            except (AttributeError, TypeError, ValueError):
                count += 36  # Fallback to default if properties unavailable

        elif entity_type == "ARC":
            # Dynamic estimation based on radius, angle, and sagitta
            try:
                radius = entity.dxf.radius
                start = math.radians(entity.dxf.start_angle)
                end = math.radians(entity.dxf.end_angle)
                angle = (end - start) % (2 * math.pi)
                if angle == 0:
                    angle = 2 * math.pi  # Full circle case
                count += _estimate_arc_segments(radius, angle, ARC_FLATTENING_SAGITTA)
            except (AttributeError, TypeError, ValueError):
                count += 18  # Fallback to default if properties unavailable

        elif entity_type == "ELLIPSE":
            # Estimate based on ellipse perimeter using Ramanujan approximation
            try:
                # Get semi-major and semi-minor axes
                major_axis = entity.dxf.major_axis
                a = major_axis.magnitude  # Semi-major axis length
                ratio = entity.dxf.ratio  # Ratio of minor to major axis
                b = a * ratio  # Semi-minor axis length

                # Ramanujan approximation for ellipse perimeter
                h = ((a - b) ** 2) / ((a + b) ** 2) if (a + b) > 0 else 0
                perimeter = (
                    math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
                )

                # Estimate segments based on sagitta (use max radius for conservative estimate)
                max_radius = max(a, b)
                if max_radius > 0 and ARC_FLATTENING_SAGITTA > 0:
                    estimated = int(
                        perimeter
                        / (2 * math.sqrt(2 * max_radius * ARC_FLATTENING_SAGITTA))
                    )
                    count += max(8, estimated)
                else:
                    count += 36  # Default fallback
            except (AttributeError, TypeError, ValueError):
                count += 36  # Default estimate if properties unavailable

        elif entity_type == "SPLINE":
            # Estimate based on control point count
            # Each span between control points typically generates ~4 segments
            try:
                cp_count = len(list(entity.control_points))  # type: ignore[attr-defined]
                count += max(cp_count * 4, 16)  # At least 16 segments
            except (AttributeError, TypeError):
                count += 16  # Default estimate if control points unavailable

        elif entity_type == "HATCH":
            # HATCH has complex boundary paths (PolylinePath, EdgePath with various edge types).
            # A fixed estimate of 50 is reasonable for typical hatches.
            # More accurate estimation would require iterating boundary paths,
            # which defeats the purpose of fast estimation.
            count += 50

    return count


def _extract_circle_edges(entity: Any) -> list[LineString]:
    """Extract edges from CIRCLE entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with sagitta-based precision.
    The sagitta controls the maximum distance from arc to chord, producing
    more segments for larger circles and fewer for smaller ones.

    Args:
        entity: ezdxf CIRCLE entity

    Returns:
        List of LineString objects representing the circle as line segments.
        Returns empty list if flattening fails.
    """
    try:
        points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(
                LineString(
                    [(points[i].x, points[i].y), (points[i + 1].x, points[i + 1].y)]
                )
            )
        return edges
    except (AttributeError, TypeError, ValueError):
        return []


def _extract_arc_edges(entity: Any) -> list[LineString]:
    """Extract edges from ARC entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with sagitta-based precision.
    Unlike circles, arcs are open curves (start != end).

    Args:
        entity: ezdxf ARC entity

    Returns:
        List of LineString objects representing the arc as line segments.
        Returns empty list if flattening fails.
    """
    try:
        points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(
                LineString(
                    [(points[i].x, points[i].y), (points[i + 1].x, points[i + 1].y)]
                )
            )
        return edges
    except (AttributeError, TypeError, ValueError):
        return []


def _extract_ellipse_edges(entity: Any) -> list[LineString]:
    """Extract edges from ELLIPSE entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with distance-based precision.
    The distance controls the maximum distance from curve to chord, producing
    more segments for larger ellipses and fewer for smaller ones.

    Args:
        entity: ezdxf ELLIPSE entity

    Returns:
        List of LineString objects representing the ellipse as line segments.
        Returns empty list if flattening fails.
    """
    try:
        # Note: ELLIPSE flattening uses 'distance' parameter, not 'sagitta'
        points = list(entity.flattening(distance=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(
                LineString(
                    [(points[i].x, points[i].y), (points[i + 1].x, points[i + 1].y)]
                )
            )
        return edges
    except (AttributeError, TypeError, ValueError):
        return []


def _extract_spline_edges(entity: Any) -> list[LineString]:
    """Extract edges from SPLINE entity using adaptive flattening.

    Uses ezdxf's built-in flattening method with distance-based precision.
    Falls back to control points as edges for degenerate splines.

    Args:
        entity: ezdxf SPLINE entity

    Returns:
        List of LineString objects representing the spline as line segments.
        Returns empty list if both flattening and control point fallback fail.
    """
    try:
        # Note: SPLINE flattening uses 'distance' parameter, not 'sagitta'
        points = list(entity.flattening(distance=ARC_FLATTENING_SAGITTA))
        edges: list[LineString] = []
        for i in range(len(points) - 1):
            edges.append(
                LineString(
                    [(points[i].x, points[i].y), (points[i + 1].x, points[i + 1].y)]
                )
            )
        return edges
    except (AttributeError, TypeError, ValueError):
        # Fallback to control points as edges for degenerate splines
        try:
            cps = list(entity.control_points)
            fallback_edges: list[LineString] = []
            for i in range(len(cps) - 1):
                fallback_edges.append(
                    LineString([(cps[i].x, cps[i].y), (cps[i + 1].x, cps[i + 1].y)])
                )
            return fallback_edges
        except (AttributeError, TypeError):
            return []


def _snap_linestring_coords(line: LineString, tolerance: float) -> LineString:
    """Snap LineString coordinates to grid based on tolerance.

    Rounds each coordinate to the nearest multiple of tolerance to fix
    floating-point precision artifacts before geometric operations.

    Args:
        line: Shapely LineString to snap
        tolerance: Grid spacing for coordinate rounding

    Returns:
        New LineString with coordinates snapped to grid.
    """
    if tolerance <= 0:
        return line
    coords = [
        (round(x / tolerance) * tolerance, round(y / tolerance) * tolerance)
        for x, y in line.coords
    ]
    return LineString(coords)


def _extract_hatch_boundary_edges(entity: Any) -> list[LineString]:
    """Extract edges from HATCH boundary paths.

    Uses ezdxf's from_hatch() to correctly handle:
    - PolylinePath with bulge values (curved segments)
    - EdgePath with LineEdge, ArcEdge, etc.

    The from_hatch() function automatically converts bulge values to
    arc approximations, ensuring curved polyline segments are captured.

    Args:
        entity: ezdxf HATCH entity

    Returns:
        List of LineString objects representing all boundary path edges.
        Returns empty list if extraction fails.
    """
    edges: list[LineString] = []
    try:
        for path in from_hatch(entity):
            points = list(path.flattening(distance=ARC_FLATTENING_SAGITTA))
            for i in range(len(points) - 1):
                edges.append(
                    LineString(
                        [(points[i].x, points[i].y), (points[i + 1].x, points[i + 1].y)]
                    )
                )
    except (AttributeError, TypeError, ValueError):
        pass
    return edges


def _extract_all_edges(
    block_def: BlockLayout,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[LineString]:
    """
    Extract ALL edges from block as LineStrings for unified polygonize.

    Pre-filter options (reduce edge count before union):
    - skip_curved_entities: Skip CIRCLE and ARC entities entirely
    - min_line_length: Skip LINE entities shorter than threshold

    Extracts edges from:
    - LINE entities (start to end as single edge)
    - LWPOLYLINE/POLYLINE entities (all vertices as edges, closing edge if closed)
    - CIRCLE entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
    - ARC entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
    - ELLIPSE entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
    - SPLINE entities (adaptive flattening to line segments) - skipped if skip_curved_entities=True
    - HATCH boundary paths (PolylinePath and EdgePath variants)

    Args:
        block_def: ezdxf block definition object
        skip_curved_entities: If True, skip CIRCLE, ARC, ELLIPSE, and SPLINE entities. Default False.
        min_line_length: Skip LINE entities shorter than this threshold (drawing units).
                         Default 0.0 (no filtering).

    Returns:
        List of LineString objects representing all edges in the block.
    """
    edges: list[LineString] = []

    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            # PRE-FILTER: Skip short LINE entities
            if min_line_length > 0:
                length = math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)
                if length < min_line_length:
                    continue
            edges.append(LineString([(start.x, start.y), (end.x, end.y)]))

        elif entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                # Use make_path to correctly interpret bulge values as arc segments
                path = make_path(entity)
                # Flatten path to line segments (handles arcs automatically)
                vertices = list(path.flattening(ARC_FLATTENING_SAGITTA))
                for i in range(len(vertices) - 1):
                    edges.append(
                        LineString(
                            [
                                (vertices[i].x, vertices[i].y),
                                (vertices[i + 1].x, vertices[i + 1].y),
                            ]
                        )
                    )
            except (AttributeError, IndexError, TypeError):
                continue

        elif entity_type == "CIRCLE":
            # PRE-FILTER: Skip curved entities
            if skip_curved_entities:
                continue
            edges.extend(_extract_circle_edges(entity))

        elif entity_type == "ARC":
            # PRE-FILTER: Skip curved entities
            if skip_curved_entities:
                continue
            edges.extend(_extract_arc_edges(entity))

        elif entity_type == "ELLIPSE":
            # PRE-FILTER: Skip curved entities if enabled
            if skip_curved_entities:
                continue
            edges.extend(_extract_ellipse_edges(entity))

        elif entity_type == "SPLINE":
            # PRE-FILTER: Skip curved entities if enabled
            if skip_curved_entities:
                continue
            edges.extend(_extract_spline_edges(entity))

        elif entity_type == "HATCH":
            edges.extend(_extract_hatch_boundary_edges(entity))

    logger.debug(f"Extracted {len(edges)} edges from block")
    return edges


def _extract_paint_bucket_regions(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
) -> list[Polygon]:
    """
    Extract all visual regions using paint-bucket algorithm.

    Combines all edges (LWPOLYLINE + LINE) into a unified edge set,
    splits at intersections using unary_union, and finds all closed
    regions using polygonize.

    Two alternative pre-union snapping methods (mutually exclusive):
    - Precision Fix: Snaps individual edge coordinates to grid points to fix
      floating-point artifacts. Uses _snap_linestring_coords() for direct
      coordinate rounding.
    - Gap Bridge: Snaps individual edges to reference geometry to bridge
      intentional design gaps. Uses Shapely's snap() function against a
      reference geometry created from all edges.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading.Event to signal abort request
        precision_tolerance: Precision fix snap tolerance for fixing floating-point
            artifacts. Default 1e-6 (appropriate for most unit systems).
            Set to 0 to disable. Mutually exclusive with gap_bridge_tolerance.
        gap_bridge_tolerance: Gap bridge snap tolerance for bridging intentional
            gaps. Default 0.0 (disabled). Set > 0 to bridge gaps up to this size.
            Mutually exclusive with precision_tolerance.
        skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
            extraction. Default False.
        min_line_length: Skip LINE entities shorter than this threshold (drawing units).
            Default 0.0 (no filtering).

    Returns:
        List of Polygon objects (coordinate tuples) representing all visual regions.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    t_start = time.perf_counter()
    edges = _extract_all_edges(
        block_def,
        skip_curved_entities=skip_curved_entities,
        min_line_length=min_line_length,
    )
    t_edges = time.perf_counter()
    if t_edges - t_start > 0.2:
        logger.debug(f"Edge extraction: {t_edges - t_start:.2f}s ({len(edges)} edges)")

    if not edges:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Region detection aborted")

    # Precision Fix: snap individual edge coordinates to grid BEFORE union
    # Fixes floating-point artifacts at line endpoints
    # Note: Mutually exclusive with gap bridge (GUI enforces this)
    t_snap_start = time.perf_counter()
    if precision_tolerance > 0:
        edges = [_snap_linestring_coords(e, precision_tolerance) for e in edges]
        logger.debug(f"Applied precision fix snap: tolerance={precision_tolerance}")

    # Gap Bridge: snap individual edges to reference geometry BEFORE union
    # Alternative method for closing gaps using Shapely's snap() function
    # Note: Mutually exclusive with precision fix (GUI enforces this)
    if gap_bridge_tolerance > 0:
        all_edges_geom = unary_union(edges)
        edges = [snap(e, all_edges_geom, gap_bridge_tolerance) for e in edges]
        logger.debug(f"Applied gap bridge snap: tolerance={gap_bridge_tolerance}")
    t_snap = time.perf_counter()
    if precision_tolerance > 0 or gap_bridge_tolerance > 0:
        if t_snap - t_snap_start > 0.2:
            logger.debug(f"Edge snapping: {t_snap - t_snap_start:.2f}s")

    # Single authoritative intersection computation via unary_union
    merged = unary_union(edges)
    t_union = time.perf_counter()
    if t_union - t_snap > 0.2:
        logger.debug(f"Unary union: {t_union - t_snap:.2f}s")

    if merged.is_empty:
        return []

    line_segments = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    polygons = list(polygonize(line_segments))
    t_poly = time.perf_counter()
    if t_poly - t_union > 0.2:
        logger.debug(f"Polygonize: {t_poly - t_union:.2f}s ({len(polygons)} polygons)")

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} paint-bucket regions")
    return result


def _polygon_has_curved_edges(
    polygon: Polygon,
    tolerance: float = 0.01,
) -> bool:
    """
    Detect if a polygon contains curved (non-straight) edges.

    A polygon is considered to have curved edges if there is a sequence
    of at least 3 consecutive SMALL angular deviations (indicating a
    smooth curve approximated by line segments). Large angular deviations
    (> 30 degrees) are considered sharp corners, not curves.

    This detects arcs/circles that were flattened during edge extraction
    while correctly ignoring sharp corners in rectangles and L-shapes.

    Args:
        polygon: List of (x, y) coordinate tuples representing polygon vertices.
        tolerance: Maximum deviation from straight line to consider
                   an edge as straight. Default 0.01 drawing units.

    Returns:
        True if polygon contains curved edges, False if all edges
        are straight (within tolerance).
    """
    if len(polygon) < 4:  # Less than 4 vertices - need 4+ for curve detection
        return False

    n = len(polygon)

    # Calculate angular deviations for all consecutive triplets
    # A curve will have many consecutive small angular deviations
    # A corner will have a large angular deviation (>30 degrees)
    consecutive_small_deviations = 0
    required_consecutive = 3  # Need at least 3 consecutive deviations for a curve
    corner_threshold = math.radians(30)  # Angles > 30 degrees are corners

    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        p3 = polygon[(i + 2) % n]

        # Calculate vectors for the two edges meeting at p2
        v1x, v1y = p1[0] - p2[0], p1[1] - p2[1]
        v2x, v2y = p3[0] - p2[0], p3[1] - p2[1]

        len1 = math.sqrt(v1x * v1x + v1y * v1y)
        len2 = math.sqrt(v2x * v2x + v2y * v2y)

        if len1 > 1e-9 and len2 > 1e-9:
            # Calculate angle between vectors using dot product
            dot = v1x * v2x + v1y * v2y
            cos_angle = max(-1.0, min(1.0, dot / (len1 * len2)))
            angle = math.acos(cos_angle)

            # The angle is the angle at the vertex (internal angle)
            # deviation from straight is pi - angle
            deviation_from_straight = abs(math.pi - angle)

            # Check if this is a small deviation (indicating curve) vs large (corner)
            if (
                deviation_from_straight > tolerance
                and deviation_from_straight < corner_threshold
            ):
                # Small deviation - could be part of a curve
                consecutive_small_deviations += 1
                if consecutive_small_deviations >= required_consecutive:
                    return True
            else:
                # Either straight (< tolerance) or a corner (> threshold)
                consecutive_small_deviations = 0
        else:
            # Degenerate edge
            consecutive_small_deviations = 0

    return False


def _extract_closed_lwpolylines(block_def: BlockLayout) -> list[Polygon]:
    """
    Extract closed polygons from LWPOLYLINE entities in a block.

    Only extracts LWPOLYLINE entities that are marked as closed (is_closed=True).
    Each polygon is a list of (x, y) tuples representing vertices.

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of Polygon objects (closed LWPOLYLINE vertices).
    """
    polygons: list[Polygon] = []

    for entity in block_def:
        if entity.dxftype() == "LWPOLYLINE":
            try:
                # Check if polyline is closed
                if entity.closed:  # type: ignore[attr-defined]
                    points: Polygon = []
                    for point in entity.get_points():  # type: ignore[attr-defined]
                        points.append((float(point[0]), float(point[1])))
                    if len(points) >= 3:  # Need at least 3 points for a polygon
                        polygons.append(points)
            except (AttributeError, IndexError):
                continue

    logger.debug(f"Extracted {len(polygons)} closed LWPOLYLINEs")
    return polygons


def _shoelace_area(polygon: Polygon) -> float:
    """
    Calculate the area of a polygon using Shapely.

    Args:
        polygon: List of (x, y) vertices forming a closed polygon.

    Returns:
        Absolute area of the polygon. Returns 0.0 for degenerate polygons
        (fewer than 3 vertices or collinear points).

    Examples:
        >>> _shoelace_area([(0, 0), (10, 0), (10, 10), (0, 10)])
        100.0
        >>> _shoelace_area([(0, 0), (3, 0), (3, 4)])
        6.0
    """
    if len(polygon) < 3:
        return 0.0
    shapely_poly = ShapelyPolygon(polygon)
    return abs(shapely_poly.area)


def _point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool:
    """
    Determine if a point is inside a polygon using Shapely.

    Args:
        point: (x, y) coordinates of the point to test.
        polygon: List of (x, y) vertices forming a closed polygon.

    Returns:
        True if the point is inside the polygon, False otherwise.
        Points exactly on the boundary may return either True or False.
    """
    if len(polygon) < 3:
        return False
    shapely_poly = ShapelyPolygon(polygon)
    return shapely_poly.contains(Point(point))


def _polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool:
    """
    Determine if one polygon completely contains another using Shapely.

    A polygon is considered to contain another if ALL vertices of the inner
    polygon are inside the outer polygon.

    Args:
        outer: The potentially containing polygon.
        inner: The potentially contained polygon.

    Returns:
        True if all vertices of inner are inside outer, False otherwise.
    """
    if len(outer) < 3 or len(inner) < 3:
        return False
    outer_shapely = ShapelyPolygon(outer)
    inner_shapely = ShapelyPolygon(inner)
    return outer_shapely.contains(inner_shapely)


def _get_polygon_bbox(polygon: Polygon) -> tuple[float, float, float, float]:
    """
    Calculate the bounding box of a polygon using Shapely.

    Args:
        polygon: List of (x, y) vertices.

    Returns:
        Tuple of (min_x, min_y, max_x, max_y).
        Returns (0, 0, 0, 0) for empty polygons.
    """
    if not polygon:
        return (0.0, 0.0, 0.0, 0.0)
    # Shapely requires at least 3 points for a valid polygon
    # For degenerate cases (1-2 points), calculate bbox directly
    if len(polygon) < 3:
        min_x = min(p[0] for p in polygon)
        min_y = min(p[1] for p in polygon)
        max_x = max(p[0] for p in polygon)
        max_y = max(p[1] for p in polygon)
        return (min_x, min_y, max_x, max_y)
    shapely_poly = ShapelyPolygon(polygon)
    minx, miny, maxx, maxy = shapely_poly.bounds
    return (minx, miny, maxx, maxy)


def _get_union_bounding_box(
    polygons: list[Polygon],
) -> tuple[float, float, float, float]:
    """
    Calculate the union bounding box encompassing all input polygons using Shapely.

    The union bounding box is the minimum axis-aligned rectangle that contains
    all vertices of all input polygons. This is used when multiple shapes tie
    for maximum net area to derive trim values from the combined area.

    Args:
        polygons: List of Polygon objects to calculate union bbox for.

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the union bounding box.
        Returns (0, 0, 0, 0) for empty input.

    Examples:
        >>> poly1 = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> poly2 = [(20, 20), (30, 20), (30, 30), (20, 30)]
        >>> _get_union_bounding_box([poly1, poly2])
        (0.0, 0.0, 30.0, 30.0)
    """
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)
    shapely_polys = [ShapelyPolygon(p) for p in polygons]
    union = unary_union(shapely_polys)
    minx, miny, maxx, maxy = union.bounds
    return (minx, miny, maxx, maxy)


def _extract_line_cycles(
    block_def: BlockLayout,
    abort_event: threading.Event | None = None,
) -> list[Polygon]:
    """
    Extract closed cycles from LINE segments using Shapely polygonize.

    Collects all LINE entities from the block definition, converts them to
    Shapely LineString objects, and uses polygonize() to find all closed
    polygons formed by the line segments.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading.Event to signal abort request

    Returns:
        List of Polygon objects representing detected cycles.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    # Collect all LINE segments as LineStrings
    lines: list[LineString] = []
    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            lines.append(LineString([(start.x, start.y), (end.x, end.y)]))

    if not lines:
        return []

    # Check abort before expensive operation
    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Cycle detection aborted")

    # Use unary_union to split lines at T-junctions AND crossing points
    merged = unary_union(lines)
    if merged.is_empty:
        return []

    # Handle both single LineString and MultiLineString
    line_segments = list(merged.geoms) if hasattr(merged, "geoms") else [merged]

    # Polygonize now works correctly with split segments
    polygons = list(polygonize(line_segments))

    # Convert to internal Polygon format
    result: list[Polygon] = []
    for poly in polygons:
        if poly.is_valid and not poly.is_empty:
            coords = list(poly.exterior.coords)[:-1]  # Exclude closing point
            result.append([(float(x), float(y)) for x, y in coords])

    logger.debug(f"Found {len(result)} LINE cycles via polygonize")
    return result


def _calculate_net_areas(
    polygons: list[Polygon],
    abort_event: threading.Event | None = None,
) -> list[tuple[Polygon, float]]:
    """
    Calculate net area for each polygon using Shapely geometric difference.

    For each polygon, calculates its area after subtracting any contained
    polygons using Shapely's difference() operation. This provides accurate
    net areas even for complex nested polygon arrangements.

    Complexity: O(n^2) with efficient GEOS-based operations
    - n polygons to process
    - n containment checks per polygon (GEOS optimized)
    - difference() operations are efficient for contained polygons

    Args:
        polygons: List of Polygon objects to analyze.
        abort_event: Optional threading.Event to signal abort request.

    Returns:
        List of (polygon, net_area) tuples sorted by net_area descending.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    if not polygons:
        return []

    if abort_event and abort_event.is_set():
        raise GeometryAbortedError("Net area calculation aborted")

    shapely_polys = [ShapelyPolygon(p) for p in polygons]
    results: list[tuple[Polygon, float]] = []

    for i, (poly, shapely_poly) in enumerate(zip(polygons, shapely_polys)):
        if not shapely_poly.is_valid:
            results.append((poly, 0.0))
            continue

        # Subtract all contained polygons using difference
        net_poly: BaseGeometry = shapely_poly
        for j, other in enumerate(shapely_polys):
            if i != j and shapely_poly.contains(other):
                net_poly = net_poly.difference(other)

        results.append((poly, abs(net_poly.area)))

    results.sort(key=lambda x: x[1], reverse=True)

    logger.debug(
        f"Calculated net areas for {len(polygons)} polygons, "
        f"largest net area: {results[0][1] if results else 0:.2f}"
    )
    return results


def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    precision_tolerance: float = 1e-6,
    gap_bridge_tolerance: float = 0.0,
    min_area_filter: float = 0.0,
    min_side_filter: float = 0.0,
    skip_curved_entities: bool = False,
    min_line_length: float = 0.0,
    curved_filter_enabled: bool = False,
    *,
    polygon_count_threshold: int = POLYGON_COUNT_THRESHOLD,
    line_segment_threshold: int = LINE_SEGMENT_THRESHOLD,
    entity_count_threshold: int = ENTITY_COUNT_THRESHOLD,
) -> ContentZoneData:
    """
    Detect content zone and calculate trim values.

    The content zone is the bounding box encompassing ALL polygons that survive
    both side and area filtering. Trim values are derived from this combined
    bounding box relative to the block bounding box.

    Coordinate snapping options (mutually exclusive - GUI enforces one or the other):
    - Precision Fix: Snaps coordinates to grid to fix floating-point artifacts
      and small coordinate discrepancies. Uses smaller tolerances.
    - Gap Bridge: Snaps edges to reference geometry to bridge intentional gaps.
      Uses larger tolerances suitable for visible coordinate discrepancies.
    Both options solve the same problem: closing small gaps for accurate polygon counts.

    Polygon filtering (when enabled):
    - min_side_filter: Filters polygons by shortest straight side (gross geometry).
      Applied BEFORE net area calculation for efficiency.
    - min_area_filter: Filters polygons by NET area (own area minus contained
      polygons). Applied AFTER net area calculation to correctly handle nested
      polygons like "picture frames".

    Performance safeguards:
    - Skips content zone entirely if > entity_count_threshold entities
    - Skips region detection if > line_segment_threshold edges
    - Skips net area calculation if > polygon_count_threshold polygons

    Args:
        block_def: ezdxf block definition object
        block_bbox: Block bounding box as (min_x, min_y, max_x, max_y)
        abort_event: Optional threading.Event to signal abort request
        precision_tolerance: Stage 1 snap tolerance for fixing floating-point
            artifacts. Default 1e-6. Set to 0 to disable Stage 1 snapping.
        gap_bridge_tolerance: Stage 2 snap tolerance for bridging intentional
            gaps. Default 0.0 (disabled). Set > 0 to bridge gaps.
        min_area_filter: Minimum polygon NET area threshold. Polygons with net
            area (gross minus contained) less than this value are filtered out.
            Default 0.0 (no filtering).
        min_side_filter: Minimum shortest side length threshold. Polygons with
            shortest straight side less than this value are filtered out.
            Default 0.0 (no filtering).
        skip_curved_entities: If True, skip CIRCLE and ARC entities during edge
            extraction. Default False (pre-filter).
        min_line_length: Skip LINE entities shorter than this threshold during edge
            extraction. Default 0.0 (pre-filter).
        curved_filter_enabled: If True, filter out polygons that contain curved edges
            (detected via vertex analysis). Default False (post-filter).
        polygon_count_threshold: Maximum polygons for net area calculation.
            Blocks exceeding this skip content zone detection.
            Default: POLYGON_COUNT_THRESHOLD (500)
        line_segment_threshold: Maximum edges for region detection.
            Blocks exceeding this skip region detection.
            Default: LINE_SEGMENT_THRESHOLD (5000)
        entity_count_threshold: Maximum entities for content zone detection.
            Blocks exceeding this skip content zone entirely.
            Default: ENTITY_COUNT_THRESHOLD (1000)

    Returns:
        ContentZoneData with detected trim values, or empty data if no
        content zone could be determined.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    block_name = block_def.name

    # UNIT 6: Progress feedback - log block processing start
    logger.info(f"[{block_name}] Detecting content zone...")

    # UNIT 1: Fast entity count pre-check (O(n), no coordinate extraction)
    entity_count = sum(1 for _ in block_def)
    if entity_count > entity_count_threshold:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{entity_count} entities exceeds threshold {entity_count_threshold}"
        )
        return _empty_content_zone_data()

    # UNIT 2: Fast edge count estimation (no coordinate extraction)
    estimated_edge_count = _estimate_edge_count(block_def)
    if estimated_edge_count > line_segment_threshold:
        logger.warning(
            f"[{block_name}] Skipping region detection: "
            f"~{estimated_edge_count} estimated edges exceeds threshold {line_segment_threshold}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=0,
            filtered_polygon_count=0,
        )

    # Use paint-bucket algorithm for accurate region detection
    t0 = time.perf_counter()
    all_shapes = _extract_paint_bucket_regions(
        block_def,
        abort_event,
        precision_tolerance,
        gap_bridge_tolerance,
        skip_curved_entities,
        min_line_length,
    )
    t1 = time.perf_counter()
    original_polygon_count = len(all_shapes)
    if t1 - t0 > 0.5:
        logger.info(
            f"[{block_name}] Paint bucket regions: {t1 - t0:.2f}s "
            f"({original_polygon_count} polygons)"
        )
    logger.debug(f"[{block_name}] Found {original_polygon_count} paint-bucket regions")

    # Post-filter: Curved lines filter (before side filter for efficiency)
    if curved_filter_enabled:
        pre_curved_count = len(all_shapes)
        all_shapes = [s for s in all_shapes if not _polygon_has_curved_edges(s)]
        logger.debug(
            f"[{block_name}] Curved filter: {pre_curved_count} -> {len(all_shapes)} polygons"
        )

    # Step 1: Early side filter (uses gross geometry)
    # Applied BEFORE net area calculation for efficiency
    # Only filters 4-sided rectangles; complex polygons pass through
    t2 = time.perf_counter()
    if min_side_filter > 0:
        pre_side_count = len(all_shapes)

        def passes_min_side_filter(polygon: Polygon) -> bool:
            """Check if polygon passes min side filter (only applies to 4-sided rectangles)."""
            shortest_side, side_count = calculate_shortest_straight_side(polygon)
            # Only filter 4-sided rectangles; pass all complex polygons
            if side_count != 4:
                return True
            return shortest_side >= min_side_filter

        all_shapes = [s for s in all_shapes if passes_min_side_filter(s)]
        logger.debug(
            f"[{block_name}] Side filter: {pre_side_count} -> {len(all_shapes)} polygons "
            f"(min_side={min_side_filter})"
        )
    t3 = time.perf_counter()
    if min_side_filter > 0 and t3 - t2 > 0.5:
        logger.info(f"[{block_name}] Side filtering: {t3 - t2:.2f}s")

    if len(all_shapes) == 0:
        logger.debug(f"[{block_name}] No closed shapes found")
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=original_polygon_count,
            filtered_polygon_count=0,
        )

    # Check polygon count BEFORE net area calculation
    if len(all_shapes) > polygon_count_threshold:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{len(all_shapes)} polygons exceeds threshold {polygon_count_threshold}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=original_polygon_count,
            filtered_polygon_count=len(all_shapes),
        )

    # Calculate net areas (O(n^2) but bounded by threshold)
    t4 = time.perf_counter()
    net_areas = _calculate_net_areas(all_shapes, abort_event)
    t5 = time.perf_counter()
    if t5 - t4 > 0.5:
        logger.info(
            f"[{block_name}] Net area calculation: {t5 - t4:.2f}s "
            f"({len(all_shapes)} polygons)"
        )

    # Step 2: Filter by NET area (post-calculation)
    # Applied AFTER net area calculation to correctly handle nested polygons
    t6 = time.perf_counter()
    if min_area_filter > 0:
        pre_area_count = len(net_areas)
        net_areas = [
            (poly, net_area)
            for poly, net_area in net_areas
            if net_area >= min_area_filter
        ]
        logger.debug(
            f"[{block_name}] Net area filter: {pre_area_count} -> {len(net_areas)} polygons "
            f"(min_area={min_area_filter})"
        )
    t7 = time.perf_counter()
    if min_area_filter > 0 and t7 - t6 > 0.5:
        logger.info(f"[{block_name}] Area filtering: {t7 - t6:.2f}s")

    if not net_areas:
        logger.debug(f"[{block_name}] No content zone detected (all polygons filtered)")
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=original_polygon_count,
            filtered_polygon_count=0,
        )

    # Get all surviving polygons (passed both side and area filters)
    survivors = [poly for poly, net_area in net_areas]
    filtered_polygon_count = len(survivors)

    # Determine content zone bounding box from ALL survivors
    if len(survivors) == 1:
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(survivors[0])
    else:
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(survivors)
        logger.debug(
            f"[{block_name}] Content zone: union of {len(survivors)} surviving polygons"
        )
    block_min_x, block_min_y, block_max_x, block_max_y = block_bbox

    # Calculate trim values
    trim_left = round(cz_min_x - block_min_x, 2)
    trim_right = round(block_max_x - cz_max_x, 2)
    trim_top = round(block_max_y - cz_max_y, 2)
    trim_bottom = round(cz_min_y - block_min_y, 2)

    # Calculate content zone dimensions
    cz_width = round(cz_max_x - cz_min_x, 2)
    cz_height = round(cz_max_y - cz_min_y, 2)

    logger.info(
        f"[{block_name}] Content zone detected: {cz_width:.2f} x {cz_height:.2f}"
    )

    return ContentZoneData(
        suggested_trim_left=trim_left,
        suggested_trim_right=trim_right,
        suggested_trim_top=trim_top,
        suggested_trim_bottom=trim_bottom,
        content_zone_detected=True,
        content_zone_width=cz_width,
        content_zone_height=cz_height,
        polygon_count=original_polygon_count,
        filtered_polygon_count=filtered_polygon_count,
    )
