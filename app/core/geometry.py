"""
Geometric calculation utilities for CAD block analysis.

This module provides functions for bounding box calculation, intersection point detection,
segment analysis, rotation categorization, and content zone detection. These utilities
support the extraction and analysis of geometric properties from CAD block definitions.

Usage:
    from core.geometry import _get_block_bounding_box, _categorize_rotation, _detect_content_zone

    bbox = _get_block_bounding_box(block_def)
    rotation_category = _categorize_rotation(90.5)
    content_zone = _detect_content_zone(block_def, bbox)
"""

import threading
import time
from collections import defaultdict

from ezdxf.layouts import BlockLayout

from .constants import (
    CYCLE_DETECTION_TIMEOUT_SECONDS,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
from .logger import setup_logger
from .types import ContentZoneData, Polygon


logger = setup_logger(__name__)


def _count_line_segments(block_def: BlockLayout) -> int:
    """
    Count the number of LINE entities in a block definition.

    Efficiently counts LINE entities with early exit optimization - stops counting
    as soon as the count exceeds LINE_SEGMENT_THRESHOLD since we only need to know
    if we're over the threshold.

    Args:
        block_def: ezdxf block definition object

    Returns:
        Number of LINE entities in the block. May return early once threshold is exceeded.

    Examples:
        >>> count = _count_line_segments(block_def)
        >>> if count > LINE_SEGMENT_THRESHOLD:
        ...     # Skip expensive cycle detection
    """
    count = 0
    for entity in block_def:
        if entity.dxftype() == "LINE":
            count += 1
            # Early exit optimization: once we exceed threshold, we don't need exact count
            if count > LINE_SEGMENT_THRESHOLD:
                return count
    return count


class GeometryAbortedError(Exception):
    """Exception raised when geometry operation is aborted by user request."""

    pass


def _check_geometry_abort(abort_event: threading.Event | None) -> None:
    """
    Check if abort has been requested and raise GeometryAbortedError if so.

    Args:
        abort_event: Threading event that signals abort request, or None if abort not supported

    Raises:
        GeometryAbortedError: If abort_event is set
    """
    if abort_event is not None and abort_event.is_set():
        logger.debug("Abort requested during geometry operation")
        raise GeometryAbortedError("Geometry operation aborted")


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

    logger.debug(
        f"Calculate segments: {len(intersection_points)} points -> {len(segments)} segments: {segments}"
    )
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

    logger.debug(
        f"Categorize rotation: {angle}° -> normalized={normalized}° -> category={result}"
    )
    return result


def _calculate_polygon_area(vertices: Polygon) -> float:
    """
    Calculate the area of a polygon using the shoelace formula.

    The shoelace formula calculates the area of a simple polygon given its vertices
    as coordinate pairs. The result is always positive (absolute value).

    Args:
        vertices: List of (x, y) coordinate tuples representing polygon vertices

    Returns:
        The area of the polygon as a positive float.
        Returns 0.0 for polygons with fewer than 3 vertices.

    Examples:
        >>> _calculate_polygon_area([(0, 0), (4, 0), (4, 3), (0, 3)])
        12.0
        >>> _calculate_polygon_area([(0, 0), (3, 0), (3, 4)])
        6.0
        >>> _calculate_polygon_area([(0, 0), (1, 0)])
        0.0
    """
    n = len(vertices)
    if n < 3:
        return 0.0

    # Shoelace formula: 0.5 * |sum(x[i]*y[i+1] - x[i+1]*y[i])|
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]

    return abs(area) / 2.0


def _point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool:
    """
    Check if a point is inside a polygon using the ray casting algorithm.

    Casts a ray from the point horizontally to the right and counts how many
    polygon edges it crosses. An odd count means the point is inside.
    Points on edges are treated as inside for containment purposes.

    Args:
        point: Tuple of (x, y) coordinates for the point to test
        polygon: List of (x, y) coordinate tuples representing polygon vertices

    Returns:
        True if the point is inside or on the edge of the polygon, False otherwise.

    Examples:
        >>> _point_in_polygon((2, 2), [(0, 0), (4, 0), (4, 4), (0, 4)])
        True
        >>> _point_in_polygon((5, 5), [(0, 0), (4, 0), (4, 4), (0, 4)])
        False
        >>> _point_in_polygon((0, 0), [(0, 0), (4, 0), (4, 4), (0, 4)])
        True
    """
    if len(polygon) < 3:
        return False

    x, y = point
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        # Check if point is exactly on a vertex
        if (xi == x and yi == y) or (xj == x and yj == y):
            return True

        # Check if the edge crosses the horizontal ray from the point
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside

        j = i

    return inside


def _polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool:
    """
    Check if all vertices of the inner polygon are inside the outer polygon.

    Args:
        outer: List of (x, y) coordinate tuples for the outer polygon
        inner: List of (x, y) coordinate tuples for the inner polygon

    Returns:
        True if ALL vertices of inner polygon are inside outer polygon, False otherwise.

    Examples:
        >>> outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> inner = [(2, 2), (8, 2), (8, 8), (2, 8)]
        >>> _polygon_contains_polygon(outer, inner)
        True
        >>> inner2 = [(2, 2), (12, 2), (12, 8), (2, 8)]
        >>> _polygon_contains_polygon(outer, inner2)
        False
    """
    if len(outer) < 3 or len(inner) < 3:
        return False

    return all(_point_in_polygon(vertex, outer) for vertex in inner)


def _get_polygon_bounding_box(polygon: Polygon) -> tuple[float, float, float, float]:
    """
    Extract the bounding box of a polygon.

    Args:
        polygon: List of (x, y) coordinate tuples

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) representing the bounding box.
        Returns (0.0, 0.0, 0.0, 0.0) for empty polygons.

    Examples:
        >>> _get_polygon_bounding_box([(1, 2), (5, 2), (5, 6), (1, 6)])
        (1, 2, 5, 6)
        >>> _get_polygon_bounding_box([])
        (0.0, 0.0, 0.0, 0.0)
    """
    if not polygon:
        return (0.0, 0.0, 0.0, 0.0)

    x_coords = [p[0] for p in polygon]
    y_coords = [p[1] for p in polygon]

    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def _get_union_bounding_box(
    polygons: list[Polygon],
) -> tuple[float, float, float, float]:
    """
    Calculate the union bounding box of multiple polygons.

    Returns (min_x, min_y, max_x, max_y) encompassing all polygons.
    Returns (0.0, 0.0, 0.0, 0.0) for empty list.

    Args:
        polygons: List of Polygon objects (vertex lists)

    Returns:
        Tuple of (min_x, min_y, max_x, max_y) encompassing all polygons.

    Examples:
        >>> poly_a = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> poly_b = [(90, 90), (100, 90), (100, 100), (90, 100)]
        >>> _get_union_bounding_box([poly_a, poly_b])
        (0, 0, 100, 100)
    """
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)

    # Get bounding box of first polygon
    union_min_x, union_min_y, union_max_x, union_max_y = _get_polygon_bounding_box(
        polygons[0]
    )

    # Expand to include all other polygons
    for polygon in polygons[1:]:
        bbox = _get_polygon_bounding_box(polygon)
        union_min_x = min(union_min_x, bbox[0])
        union_min_y = min(union_min_y, bbox[1])
        union_max_x = max(union_max_x, bbox[2])
        union_max_y = max(union_max_y, bbox[3])

    logger.debug(
        f"Union bounding box of {len(polygons)} polygons: "
        f"({union_min_x}, {union_min_y}, {union_max_x}, {union_max_y})"
    )
    return (union_min_x, union_min_y, union_max_x, union_max_y)


def _extract_closed_lwpolylines(block_def: BlockLayout) -> list[Polygon]:
    """
    Extract closed LWPOLYLINE/POLYLINE entities from a block definition as polygons.

    Args:
        block_def: ezdxf block definition object

    Returns:
        List of Polygon objects (vertex lists) for each closed polyline.
        Polylines with fewer than 3 vertices are skipped.

    Examples:
        >>> polygons = _extract_closed_lwpolylines(block_def)
        >>> len(polygons)
        2
    """
    polygons: list[Polygon] = []

    for entity in block_def:
        entity_type = entity.dxftype()

        if entity_type in ("LWPOLYLINE", "POLYLINE"):
            try:
                # Check if polyline is closed
                is_closed = getattr(entity, "is_closed", False)
                if not is_closed:
                    # Also check the closed attribute in dxf namespace
                    is_closed = (
                        getattr(entity.dxf, "closed", False)
                        if hasattr(entity, "dxf")
                        else False
                    )
                if not is_closed:
                    continue

                # Extract vertices
                vertices: Polygon = []
                for point in entity.get_points():  # type: ignore[attr-defined]
                    vertices.append((float(point[0]), float(point[1])))

                # Skip polylines with fewer than 3 vertices
                if len(vertices) >= 3:
                    polygons.append(vertices)
                    logger.debug(
                        f"Extracted closed polyline with {len(vertices)} vertices"
                    )

            except (AttributeError, IndexError, TypeError) as e:
                logger.debug(f"Error extracting polyline: {e}")
                continue

    logger.debug(f"Extracted {len(polygons)} closed polylines from block")
    return polygons


def _extract_line_cycles(
    block_def: BlockLayout, abort_event: threading.Event | None = None
) -> list[Polygon]:
    """
    Detect closed cycles from connected LINE entities using graph-based analysis.

    Builds an adjacency graph from LINE endpoints and uses DFS to find cycles.
    Uses epsilon tolerance (0.01) for connecting endpoints.

    Args:
        block_def: ezdxf block definition object
        abort_event: Optional threading event to check for abort requests

    Returns:
        List of Polygon objects (vertex lists) for each detected cycle.
        Cycles with fewer than 3 unique vertices are skipped.

    Examples:
        >>> cycles = _extract_line_cycles(block_def)
        >>> len(cycles)
        1
    """
    start_time = time.perf_counter()
    epsilon = 0.01

    # Collect all line segments
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for entity in block_def:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            segments.append(((start.x, start.y), (end.x, end.y)))

    if not segments:
        return []

    logger.debug(f"Line cycles: found {len(segments)} LINE segments")

    # Build adjacency graph with tolerance-based vertex merging
    # First, collect all unique vertices with tolerance
    all_points: list[tuple[float, float]] = []
    for seg in segments:
        all_points.append(seg[0])
        all_points.append(seg[1])

    # Merge nearby points into canonical representatives
    canonical: dict[tuple[float, float], tuple[float, float]] = {}

    def get_canonical(point: tuple[float, float]) -> tuple[float, float]:
        """Get or create canonical representative for a point."""
        for existing in canonical:
            if (
                abs(existing[0] - point[0]) <= epsilon
                and abs(existing[1] - point[1]) <= epsilon
            ):
                return canonical[existing]
        # New canonical point
        canonical[point] = point
        return point

    # Build adjacency list using canonical points
    adjacency: dict[tuple[float, float], set[tuple[float, float]]] = defaultdict(set)
    for start, end in segments:
        canon_start = get_canonical(start)
        canon_end = get_canonical(end)
        if canon_start != canon_end:  # Skip degenerate lines
            adjacency[canon_start].add(canon_end)
            adjacency[canon_end].add(canon_start)

    logger.debug(
        f"Line cycles: built adjacency graph with {len(adjacency)} unique vertices"
    )

    # Check abort after building adjacency graph (expensive O(n²) operation)
    _check_geometry_abort(abort_event)

    # Find cycles using DFS
    cycle_start_time = time.perf_counter()
    polygons: list[Polygon] = []
    visited_edges: set[tuple[tuple[float, float], tuple[float, float]]] = set()

    def make_edge_key(
        a: tuple[float, float], b: tuple[float, float]
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Create a canonical edge key (smaller point first)."""
        return (a, b) if a < b else (b, a)

    def find_cycle_from(
        start: tuple[float, float], abort_ev: threading.Event | None
    ) -> Polygon | None:
        """Find a simple cycle starting from a given vertex using DFS."""
        stack: list[
            tuple[
                tuple[float, float], list[tuple[float, float]], set[tuple[float, float]]
            ]
        ] = [(start, [start], {start})]

        iterations = 0
        while stack:
            iterations += 1
            # Check abort every 1000 DFS iterations for sub-second responsiveness
            if iterations % 1000 == 0:
                _check_geometry_abort(abort_ev)

            current, path, visited = stack.pop()

            for neighbor in adjacency[current]:
                edge_key = make_edge_key(current, neighbor)
                if edge_key in visited_edges:
                    continue

                # Found a cycle back to start
                if neighbor == start and len(path) >= 3:
                    return path

                # Continue DFS if not visited
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    new_visited = visited | {neighbor}
                    stack.append((neighbor, new_path, new_visited))

        return None

    # Try to find cycles starting from each vertex
    vertices_processed = 0
    timed_out = False
    for vertex in list(adjacency.keys()):
        vertices_processed += 1

        # Check timeout - safety net for edge cases
        elapsed_cycle_time = time.perf_counter() - cycle_start_time
        if elapsed_cycle_time > CYCLE_DETECTION_TIMEOUT_SECONDS:
            logger.warning(
                f"Cycle detection timeout after {elapsed_cycle_time:.1f}s "
                f"(processed {vertices_processed}/{len(adjacency)} vertices, "
                f"found {len(polygons)} cycles)"
            )
            timed_out = True
            break

        # Check abort periodically during cycle detection
        if vertices_processed % 50 == 0:
            _check_geometry_abort(abort_event)

        # Only try vertices with at least 2 connections
        if len(adjacency[vertex]) < 2:
            continue

        cycle = find_cycle_from(vertex, abort_event)
        if cycle and len(cycle) >= 3:
            # Mark all edges in this cycle as visited
            for i in range(len(cycle)):
                j = (i + 1) % len(cycle)
                edge_key = make_edge_key(cycle[i], cycle[j])
                visited_edges.add(edge_key)

            polygons.append(cycle)
            logger.debug(f"Found line cycle with {len(cycle)} vertices")

    cycle_elapsed = time.perf_counter() - cycle_start_time
    total_elapsed = time.perf_counter() - start_time
    timeout_suffix = " (timed out)" if timed_out else ""
    logger.debug(
        f"Line cycles: detected {len(polygons)} cycles in {cycle_elapsed:.3f}s "
        f"(total {total_elapsed:.3f}s){timeout_suffix}"
    )
    return polygons


def _calculate_net_areas(
    polygons: list[Polygon], abort_event: threading.Event | None = None
) -> list[tuple[Polygon, float]]:
    """
    Calculate net areas for all polygons accounting for containment.

    Net area = own area - sum of directly contained polygon areas.
    A polygon A contains polygon B if all vertices of B are inside A.

    Args:
        polygons: List of Polygon objects (vertex lists)
        abort_event: Optional threading event to check for abort requests

    Returns:
        List of (polygon, net_area) tuples.

    Examples:
        >>> outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
        >>> inner = [(2, 2), (8, 2), (8, 8), (2, 8)]
        >>> results = _calculate_net_areas([outer, inner])
        >>> results[0][1]  # outer net area = 100 - 36 = 64
        64.0
    """
    if not polygons:
        return []

    start_time = time.perf_counter()
    n = len(polygons)
    logger.debug(f"Net areas: calculating for {n} polygons")

    # Calculate own area for each polygon
    areas = [_calculate_polygon_area(p) for p in polygons]

    # Build containment relationships
    # contained_by[i] = list of polygon indices that contain polygon i
    contained_by: list[list[int]] = [[] for _ in range(n)]

    containment_checks = 0
    for i in range(n):
        # Log progress every 10 polygons if > 20 total
        if n > 20 and i > 0 and i % 10 == 0:
            logger.debug(f"Net areas: containment check progress {i}/{n}")
            _check_geometry_abort(abort_event)

        for j in range(n):
            if i != j and _polygon_contains_polygon(polygons[j], polygons[i]):
                contained_by[i].append(j)
            containment_checks += 1

    logger.debug(
        f"Net areas: completed {containment_checks} containment checks in "
        f"{time.perf_counter() - start_time:.3f}s"
    )

    # Check abort after containment analysis
    _check_geometry_abort(abort_event)

    # Calculate net areas
    # For each polygon, subtract areas of polygons it directly contains
    # A polygon A directly contains B if A contains B and there's no C where A contains C contains B
    net_areas: list[float] = list(areas)

    direct_containment_start = time.perf_counter()
    for i in range(n):
        # Check abort at start of each polygon to ensure responsive cancellation
        # This loop is O(n³) so frequent checks are critical for responsiveness
        _check_geometry_abort(abort_event)

        # Log progress every 10 polygons for visibility into slow operations
        if n > 20 and i > 0 and i % 10 == 0:
            elapsed = time.perf_counter() - direct_containment_start
            logger.debug(f"Net areas: direct containment progress {i}/{n} ({elapsed:.3f}s)")

        # Find all polygons that this polygon (i) contains
        directly_contained: list[int] = []
        for j in range(n):
            if i != j and _polygon_contains_polygon(polygons[i], polygons[j]):
                # Check if i directly contains j (no intermediate polygon)
                is_direct = True
                for k in range(n):
                    if k != i and k != j:
                        if _polygon_contains_polygon(
                            polygons[i], polygons[k]
                        ) and _polygon_contains_polygon(polygons[k], polygons[j]):
                            is_direct = False
                            break
                if is_direct:
                    directly_contained.append(j)

        # Subtract directly contained polygon areas
        for j in directly_contained:
            net_areas[i] -= areas[j]

    elapsed = time.perf_counter() - start_time
    logger.debug(f"Net areas: calculation completed in {elapsed:.3f}s")

    return [(polygons[i], net_areas[i]) for i in range(n)]


def _detect_content_zone(
    block_def: BlockLayout,
    block_bbox: tuple[float, float, float, float],
    abort_event: threading.Event | None = None,
    block_name: str | None = None,
) -> ContentZoneData:
    """
    Detect the content zone within a block definition and derive trim values.

    The content zone is identified as follows:
    1. If nested shapes exist, select the largest shape that is contained by another shape
       (i.e., the inner content area, not the outer border)
    2. If no nesting exists (all independent or single shape), select the shape with
       the largest net area

    Both LWPOLYLINE and LINE-based closed shapes are considered.

    Args:
        block_def: ezdxf block definition object
        block_bbox: Tuple of (min_x, min_y, max_x, max_y) for the block's bounding box
        abort_event: Optional threading event to check for abort requests
        block_name: Optional block name for logging context

    Returns:
        ContentZoneData with suggested trim values and detection flag.
        All trim values are None if no content zone is detected.

    Examples:
        >>> content_zone = _detect_content_zone(block_def, (0, 0, 100, 50))
        >>> content_zone['content_zone_detected']
        True
        >>> content_zone['suggested_trim_left']
        5.0
    """
    total_start_time = time.perf_counter()
    block_context = f" for block '{block_name}'" if block_name else ""
    logger.debug(f"Content zone detection starting{block_context}")

    # Extract closed shapes from both sources
    polyline_start = time.perf_counter()
    lwpolyline_shapes = _extract_closed_lwpolylines(block_def)
    polyline_elapsed = time.perf_counter() - polyline_start
    logger.debug(
        f"Content zone: extracted {len(lwpolyline_shapes)} polylines in {polyline_elapsed:.3f}s"
    )

    # Check abort after polyline extraction
    _check_geometry_abort(abort_event)

    # Check LINE segment count threshold before expensive cycle detection
    line_segment_count = _count_line_segments(block_def)
    if line_segment_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"Skipping LINE cycle detection{block_context}: {line_segment_count} LINE segments "
            f"exceeds threshold of {LINE_SEGMENT_THRESHOLD} (would cause exponential DFS complexity)"
        )
        line_cycle_shapes: list[Polygon] = []
    else:
        line_cycle_start = time.perf_counter()
        line_cycle_shapes = _extract_line_cycles(block_def, abort_event=abort_event)
        line_cycle_elapsed = time.perf_counter() - line_cycle_start
        logger.debug(
            f"Content zone: extracted {len(line_cycle_shapes)} line cycles in {line_cycle_elapsed:.3f}s"
        )

    # Check abort after line cycle extraction
    _check_geometry_abort(abort_event)

    # Combine all shapes (LWPOLYLINEs first for deterministic ordering)
    all_shapes = lwpolyline_shapes + line_cycle_shapes

    logger.debug(
        f"Content zone detection: {len(lwpolyline_shapes)} polylines, {len(line_cycle_shapes)} line cycles"
    )

    # Check polygon count threshold to avoid O(n³) containment analysis
    polygon_count = len(all_shapes)
    if polygon_count > POLYGON_COUNT_THRESHOLD:
        logger.warning(
            f"Skipping content zone detection{block_context}: {polygon_count} polygons "
            f"exceeds threshold of {POLYGON_COUNT_THRESHOLD}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
        )

    # Return empty result if no shapes found
    if not all_shapes:
        logger.debug("No closed shapes found for content zone detection")
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
        )

    # Calculate net areas for all shapes
    net_area_start = time.perf_counter()
    shape_net_areas = _calculate_net_areas(all_shapes, abort_event=abort_event)
    net_area_elapsed = time.perf_counter() - net_area_start
    logger.debug(
        f"Content zone: calculated net areas for {len(all_shapes)} shapes in {net_area_elapsed:.3f}s"
    )

    # Check abort after net area calculation
    _check_geometry_abort(abort_event)

    # Filter out shapes with non-positive net area
    valid_shapes = [
        (shape, net_area) for shape, net_area in shape_net_areas if net_area > 0
    ]

    if not valid_shapes:
        logger.debug("No shapes with positive net area found")
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
        )

    # Find shapes that are contained by at least one other shape (inner shapes)
    contained_shapes: list[tuple[Polygon, float]] = []
    for i, (shape, net_area) in enumerate(valid_shapes):
        is_contained = False
        for j, (other_shape, _) in enumerate(valid_shapes):
            if i != j and _polygon_contains_polygon(other_shape, shape):
                is_contained = True
                break
        if is_contained:
            contained_shapes.append((shape, net_area))

    # Select content zone:
    # - If there are contained shapes, pick the one(s) with largest net area (the inner content)
    # - If no containment exists, pick the shape(s) with largest net area (single/independent shapes)
    # - When multiple shapes tie for max net area, use union bounding box
    #
    # Use epsilon tolerance for tie detection to handle floating-point precision issues
    epsilon = 0.001

    if contained_shapes:
        max_net_area = max(net_area for _, net_area in contained_shapes)
        # Collect ALL shapes with maximum net area (within epsilon tolerance)
        tied_shapes = [
            shape
            for shape, net_area in contained_shapes
            if abs(net_area - max_net_area) < epsilon
        ]
        logger.debug(
            f"Content zone: {len(tied_shapes)} contained shape(s) with max net area {max_net_area:.2f} "
            f"(from {len(contained_shapes)} total contained shapes)"
        )
    else:
        max_net_area = max(net_area for _, net_area in valid_shapes)
        # Collect ALL shapes with maximum net area (within epsilon tolerance)
        tied_shapes = [
            shape
            for shape, net_area in valid_shapes
            if abs(net_area - max_net_area) < epsilon
        ]
        logger.debug(
            f"Content zone: {len(tied_shapes)} shape(s) with max net area {max_net_area:.2f} "
            f"(no nesting, from {len(valid_shapes)} total shapes)"
        )

    # Calculate union bounding box of all tied shapes
    if len(tied_shapes) == 1:
        cz_bbox = _get_polygon_bounding_box(tied_shapes[0])
        logger.debug(
            f"Content zone selected: single shape with net area {max_net_area:.2f}"
        )
    else:
        cz_bbox = _get_union_bounding_box(tied_shapes)
        logger.debug(
            f"Content zone selected: union of {len(tied_shapes)} shapes with net area {max_net_area:.2f}"
        )
    cz_min_x, cz_min_y, cz_max_x, cz_max_y = cz_bbox
    block_min_x, block_min_y, block_max_x, block_max_y = block_bbox

    # Calculate trim values (distance from block bbox to content zone bbox)
    suggested_trim_left = round(cz_min_x - block_min_x, 2)
    suggested_trim_right = round(block_max_x - cz_max_x, 2)
    suggested_trim_top = round(block_max_y - cz_max_y, 2)
    suggested_trim_bottom = round(cz_min_y - block_min_y, 2)

    logger.debug(
        f"Suggested trims - L: {suggested_trim_left}, R: {suggested_trim_right}, "
        f"T: {suggested_trim_top}, B: {suggested_trim_bottom}"
    )

    total_elapsed = time.perf_counter() - total_start_time
    logger.debug(f"Content zone detection completed{block_context} in {total_elapsed:.3f}s")

    return ContentZoneData(
        suggested_trim_left=suggested_trim_left,
        suggested_trim_right=suggested_trim_right,
        suggested_trim_top=suggested_trim_top,
        suggested_trim_bottom=suggested_trim_bottom,
        content_zone_detected=True,
    )
