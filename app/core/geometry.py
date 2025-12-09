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

import threading

from ezdxf.layouts import BlockLayout
from shapely import Point
from shapely import Polygon as ShapelyPolygon
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, unary_union

from .constants import (
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


class GeometryAbortedError(Exception):
    """
    Exception raised when a geometry operation is aborted.

    This exception is raised when an abort_event is set during long-running
    geometry operations like cycle detection or net area calculation, allowing
    the calling code to handle graceful cancellation.
    """

    pass


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
    line_segments = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]

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
) -> ContentZoneData:
    """
    Detect content zone and calculate trim values.

    The content zone is the closed polygon with the largest net area (own area
    minus areas of contained polygons). Trim values are derived from the
    content zone bounding box relative to the block bounding box.

    Performance safeguards:
    - Skips LINE cycle detection if > LINE_SEGMENT_THRESHOLD segments (5000)
    - Skips net area calculation if > POLYGON_COUNT_THRESHOLD polygons (500)

    Args:
        block_def: ezdxf block definition object
        block_bbox: Block bounding box as (min_x, min_y, max_x, max_y)
        abort_event: Optional threading.Event to signal abort request

    Returns:
        ContentZoneData with detected trim values, or empty data if no
        content zone could be determined.

    Raises:
        GeometryAbortedError: If abort_event is set during processing.
    """
    block_name = block_def.name

    # Extract LWPOLYLINE shapes (always fast)
    lwpolyline_shapes = _extract_closed_lwpolylines(block_def)
    logger.debug(f"[{block_name}] Found {len(lwpolyline_shapes)} closed LWPOLYLINEs")

    # Check LINE segment count BEFORE extraction
    line_count = _count_line_segments(block_def)
    if line_count > LINE_SEGMENT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping LINE cycle detection: "
            f"{line_count} segments exceeds threshold {LINE_SEGMENT_THRESHOLD}"
        )
        line_cycle_shapes: list[Polygon] = []
    else:
        line_cycle_shapes = _extract_line_cycles(block_def, abort_event)
        logger.debug(f"[{block_name}] Found {len(line_cycle_shapes)} LINE cycles")

    # Combine all shapes
    all_shapes = lwpolyline_shapes + line_cycle_shapes
    polygon_count = len(all_shapes)

    if polygon_count == 0:
        logger.debug(f"[{block_name}] No closed shapes found")
        return _empty_content_zone_data()

    # Check polygon count BEFORE net area calculation
    if polygon_count > POLYGON_COUNT_THRESHOLD:
        logger.warning(
            f"[{block_name}] Skipping content zone: "
            f"{polygon_count} polygons exceeds threshold {POLYGON_COUNT_THRESHOLD}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=polygon_count,
        )

    # Calculate net areas (O(n^3) but bounded by threshold)
    net_areas = _calculate_net_areas(all_shapes, abort_event)

    if not net_areas:
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=polygon_count,
        )

    # Find maximum net area value (already sorted descending)
    max_net_area = net_areas[0][1]

    # Skip if content zone has zero or negative area
    if max_net_area <= 0:
        logger.debug(
            f"[{block_name}] Content zone has non-positive area: {max_net_area}"
        )
        return ContentZoneData(
            suggested_trim_left=None,
            suggested_trim_right=None,
            suggested_trim_top=None,
            suggested_trim_bottom=None,
            content_zone_detected=False,
            content_zone_width=None,
            content_zone_height=None,
            polygon_count=polygon_count,
        )

    # Find all shapes tied for maximum net area
    tied_shapes = [shape for shape, net_area in net_areas if net_area == max_net_area]

    # Determine content zone bounding box
    if len(tied_shapes) == 1:
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_polygon_bbox(tied_shapes[0])
    else:
        cz_min_x, cz_min_y, cz_max_x, cz_max_y = _get_union_bounding_box(tied_shapes)
        logger.debug(
            f"[{block_name}] Content zone: union of {len(tied_shapes)} tied shapes"
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

    logger.debug(
        f"[{block_name}] Content zone detected: "
        f"trim_left={trim_left}, trim_right={trim_right}, "
        f"trim_top={trim_top}, trim_bottom={trim_bottom}"
    )

    return ContentZoneData(
        suggested_trim_left=trim_left,
        suggested_trim_right=trim_right,
        suggested_trim_top=trim_top,
        suggested_trim_bottom=trim_bottom,
        content_zone_detected=True,
        content_zone_width=cz_width,
        content_zone_height=cz_height,
        polygon_count=polygon_count,
    )
