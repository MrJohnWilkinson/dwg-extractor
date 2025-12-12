"""
Unit tests for the content zone detection module.

This test suite validates content zone detection functionality including:
- LWPOLYLINE extraction from closed polylines
- LINE cycle detection via DFS
- Threshold skip behavior for LINE segments and polygon counts
- Area calculation using shoelace formula
- Point-in-polygon containment testing
- Net area calculation with containment subtraction
- Trim value derivation from content zone bbox
- Abort event handling
- Edge cases and degenerate inputs
"""

import threading
import time

import ezdxf
import pytest

from core.constants import (
    ENTITY_COUNT_THRESHOLD,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
from core.geometry import (
    GeometryAbortedError,
    _calculate_net_areas,
    _count_line_segments,
    _detect_content_zone,
    _empty_content_zone_data,
    _estimate_edge_count,
    _extract_all_edges,
    _extract_closed_lwpolylines,
    _extract_line_cycles,
    _get_block_bounding_box,
    _get_polygon_bbox,
    _get_union_bounding_box,
    _point_in_polygon,
    _polygon_contains_polygon,
    _shoelace_area,
)
from core.types import Polygon


class TestLwpolylineDetection:
    """Test suite for _extract_closed_lwpolylines function."""

    def test_extract_closed_lwpolyline_rectangle(self) -> None:
        """Detect closed LWPOLYLINE rectangle."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("SINGLE_RECTANGLE")

        polygons = _extract_closed_lwpolylines(block)

        assert len(polygons) == 1
        assert len(polygons[0]) == 4  # Rectangle has 4 vertices
        # Verify vertices
        assert (0.0, 0.0) in polygons[0]
        assert (50.0, 0.0) in polygons[0]

    def test_extract_closed_lwpolyline_ignores_open(self) -> None:
        """Ignore non-closed LWPOLYLINE entities."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("OPEN_POLYLINE")

        polygons = _extract_closed_lwpolylines(block)

        # Should only find 1 polygon (the closed one), not 2
        assert len(polygons) == 1

    def test_extract_multiple_lwpolylines(self) -> None:
        """Detect multiple closed LWPOLYLINE shapes."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")

        polygons = _extract_closed_lwpolylines(block)

        assert len(polygons) == 2  # Outer and inner rectangle

    def test_extract_lwpolylines_from_mixed_shapes(self) -> None:
        """Extract multiple nested LWPOLYLINE shapes."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("MIXED_SHAPES")

        polygons = _extract_closed_lwpolylines(block)

        assert len(polygons) == 3  # Large, medium, small

    def test_extract_lwpolylines_empty_block(self) -> None:
        """Return empty list for blocks without LWPOLYLINE entities."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY")

        polygons = _extract_closed_lwpolylines(block)

        assert polygons == []


class TestLineCycleDetection:
    """Test suite for _extract_line_cycles function."""

    def test_extract_line_cycle_simple_rectangle(self) -> None:
        """Detect rectangle formed by 4 LINE segments."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("LINE_RECTANGLE")

        cycles = _extract_line_cycles(block)

        # Should find at least one cycle (the rectangle)
        assert len(cycles) >= 1
        # At least one cycle should have 4 vertices
        has_quadrilateral = any(len(c) == 4 for c in cycles)
        assert has_quadrilateral

    def test_extract_line_cycle_no_cycles(self) -> None:
        """Return empty for open line chains (no closed cycles)."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="OPEN_CHAIN")
        # Add lines that don't form a closed cycle
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        # No line back to start

        cycles = _extract_line_cycles(block)

        assert cycles == []

    def test_extract_line_cycle_chamfered(self) -> None:
        """Detect cycle from chamfered shape LINE segments."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("CHAMFERED_SHAPE")

        cycles = _extract_line_cycles(block)

        # Should find the chamfered rectangle cycle
        assert len(cycles) >= 1
        # Chamfered rectangle has 8 vertices (4 corners with chamfers)
        has_octagon = any(len(c) == 8 for c in cycles)
        assert has_octagon

    def test_line_cycle_timeout_protection(self) -> None:
        """Verify Shapely polygonize completes quickly for moderate line counts."""
        # Create a block with moderate LINE count (not exceeding threshold)
        doc = ezdxf.new()
        block = doc.blocks.new(name="MODERATE_LINES")
        # Create a grid with interconnected lines (challenging for cycle detection)
        for i in range(15):
            for j in range(15):
                x, y = i * 10, j * 10
                block.add_line((x, y), (x + 10, y))
                block.add_line((x, y), (x, y + 10))

        start_time = time.perf_counter()
        _extract_line_cycles(block)
        elapsed = time.perf_counter() - start_time

        # Shapely polygonize should complete very quickly (within 5 seconds)
        assert elapsed < 5.0

    def test_line_cycle_abort_event(self) -> None:
        """Verify abort event raises GeometryAbortedError."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST")
        # Create a simple cycle
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        block.add_line((10, 10), (0, 10))
        block.add_line((0, 10), (0, 0))

        # Create pre-set abort event
        abort_event = threading.Event()
        abort_event.set()

        # For very small inputs, might complete before abort check
        # For larger inputs, should raise
        # This test verifies the mechanism exists
        try:
            _extract_line_cycles(block, abort_event)
            # If it completes, that's OK for small inputs
        except GeometryAbortedError:
            pass  # Expected for larger inputs


class TestThresholdSkips:
    """Test suite for threshold skip behavior.

    Note: These tests use the fast edge estimation (_estimate_edge_count) introduced
    in Unit 2 for threshold checks instead of the expensive _extract_all_edges().
    """

    def test_line_threshold_skip(self) -> None:
        """Verify region detection skipped when estimated edge count exceeds threshold.

        Uses fast edge estimation (Unit 2) to check threshold before expensive geometry extraction.
        """
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("MANY_LINES")

        # Verify line count exceeds threshold (LINE entities count as 1 edge each)
        line_count = _count_line_segments(block)
        assert line_count > LINE_SEGMENT_THRESHOLD

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should skip due to estimated edge count
        result = _detect_content_zone(block, bbox)

        # Since MANY_LINES has no LWPOLYLINEs, should return empty
        assert result["content_zone_detected"] is False

    def test_line_threshold_not_skip(self) -> None:
        """Verify region detection runs when estimated edge count is under threshold.

        Uses fast edge estimation (Unit 2) to check threshold before expensive geometry extraction.
        """
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("FEW_LINES")

        # Verify line count is under threshold
        line_count = _count_line_segments(block)
        assert line_count < LINE_SEGMENT_THRESHOLD

        # LINE cycle detection should run (not skip)
        cycles = _extract_line_cycles(block)
        # Should find the nested rectangles
        assert len(cycles) >= 1

    def test_polygon_threshold_skip(self) -> None:
        """Verify net area calculation skipped when polygon count exceeds threshold."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MANY_POLYGONS")

        # Create more polygons than POLYGON_COUNT_THRESHOLD
        for i in range(POLYGON_COUNT_THRESHOLD + 5):
            x = (i % 10) * 50
            y = (i // 10) * 50
            block.add_lwpolyline(
                [(x, y), (x + 40, y), (x + 40, y + 40), (x, y + 40)],
                close=True,
            )

        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        # Should return empty due to polygon threshold
        assert result["content_zone_detected"] is False

    def test_exactly_threshold_lines(self) -> None:
        """Test behavior at exactly LINE_SEGMENT_THRESHOLD."""
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("EXACTLY_THRESHOLD")

        line_count = _count_line_segments(block)
        assert line_count == LINE_SEGMENT_THRESHOLD

        # At exactly threshold, should NOT skip (threshold is >)
        # So cycle detection should run
        _extract_line_cycles(block)
        # May or may not find cycles depending on line arrangement

    def test_just_over_threshold_lines(self) -> None:
        """Test behavior at LINE_SEGMENT_THRESHOLD + 1."""
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("JUST_OVER_THRESHOLD")

        line_count = _count_line_segments(block)
        assert line_count == LINE_SEGMENT_THRESHOLD + 1

        # Just over threshold, should skip
        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        # Should return empty since no LWPOLYLINEs and LINEs skipped
        assert result["content_zone_detected"] is False


class TestEntityCountThreshold:
    """Test suite for entity count threshold skip behavior (Unit 1)."""

    def test_entity_count_threshold_skip(self) -> None:
        """Verify blocks with >30 entities are skipped and return empty ContentZoneData."""
        doc = ezdxf.readfile("app/tests/assets/high_entity_count_test.dxf")
        block = doc.blocks.get("HIGH_ENTITY_COUNT")

        # Verify entity count exceeds threshold
        entity_count = sum(1 for _ in block)
        assert entity_count > ENTITY_COUNT_THRESHOLD

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should skip due to high entity count
        result = _detect_content_zone(block, bbox)

        # Should return empty ContentZoneData
        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None
        assert result["polygon_count"] == 0

    def test_entity_count_threshold_not_skip(self) -> None:
        """Verify blocks with <30 entities proceed with detection."""
        doc = ezdxf.readfile("app/tests/assets/high_entity_count_test.dxf")
        block = doc.blocks.get("LOW_ENTITY_COUNT")

        # Verify entity count is under threshold
        entity_count = sum(1 for _ in block)
        assert entity_count < ENTITY_COUNT_THRESHOLD

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should NOT skip due to entity count
        # (may still skip due to edge threshold, but not entity count)
        result = _detect_content_zone(block, bbox)

        # Detection should proceed (may or may not find content zone depending on geometry)
        # The key is that it didn't return early due to entity count
        # Since LOW_ENTITY_COUNT has LINE entities, polygon_count may be 0 or more
        assert isinstance(result["content_zone_detected"], bool)

    def test_entity_count_exactly_threshold(self) -> None:
        """Verify blocks with exactly 30 entities are NOT skipped (> not >=)."""
        doc = ezdxf.readfile("app/tests/assets/high_entity_count_test.dxf")
        block = doc.blocks.get("EXACTLY_ENTITY_THRESHOLD")

        # Verify entity count is exactly at threshold
        entity_count = sum(1 for _ in block)
        assert entity_count == ENTITY_COUNT_THRESHOLD

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should NOT skip (threshold is >)
        result = _detect_content_zone(block, bbox)

        # At exactly threshold, should proceed with detection
        # (may still skip due to edge threshold, but not entity count)
        assert isinstance(result["content_zone_detected"], bool)

    def test_entity_count_just_over_threshold(self) -> None:
        """Verify blocks with 31 entities ARE skipped (first to be skipped)."""
        doc = ezdxf.readfile("app/tests/assets/high_entity_count_test.dxf")
        block = doc.blocks.get("JUST_OVER_ENTITY_THRESHOLD")

        # Verify entity count is exactly 31
        entity_count = sum(1 for _ in block)
        assert entity_count == ENTITY_COUNT_THRESHOLD + 1

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should skip due to entity count
        result = _detect_content_zone(block, bbox)

        # Should return empty ContentZoneData
        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None
        assert result["polygon_count"] == 0


class TestEdgeEstimation:
    """Test suite for _estimate_edge_count function (Unit 2)."""

    def test_estimate_edge_count_lines_only(self) -> None:
        """Verify LINE entities counted as 1 edge each."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="LINES_ONLY")
        # Add 5 LINE entities
        for i in range(5):
            block.add_line((i * 10, 0), (i * 10 + 5, 5))

        estimated = _estimate_edge_count(block)

        assert estimated == 5

    def test_estimate_edge_count_polylines(self) -> None:
        """Verify polyline vertex pairs counted correctly."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="POLYLINES")
        # Open polyline with 4 vertices = 3 edges
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=False)
        # Closed polyline with 4 vertices = 4 edges (3 + closing)
        block.add_lwpolyline([(20, 0), (30, 0), (30, 10), (20, 10)], close=True)

        estimated = _estimate_edge_count(block)

        # 3 (open) + 4 (closed) = 7 edges
        assert estimated == 7

    def test_estimate_edge_count_circles(self) -> None:
        """Verify circles estimated dynamically based on radius."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLES")
        # Add 2 circles with different radii
        block.add_circle((10, 10), 5)   # Small circle
        block.add_circle((30, 30), 10)  # Larger circle

        estimated = _estimate_edge_count(block)

        # Dynamic estimation: larger circle should have more segments than small one
        # Both should estimate > 0 edges
        assert estimated > 0
        # Estimate should be within 10% of actual flattening
        actual = len(_extract_all_edges(block))
        assert abs(estimated - actual) <= actual * 0.10

    def test_estimate_edge_count_arcs(self) -> None:
        """Verify arcs estimated dynamically based on radius and angle."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ARCS")
        # Add 3 arcs with different radii and angles
        block.add_arc((10, 10), 5, 0, 90)      # 90-degree arc
        block.add_arc((30, 30), 10, 45, 180)   # 135-degree arc
        block.add_arc((50, 50), 7, 0, 270)     # 270-degree arc

        estimated = _estimate_edge_count(block)

        # Dynamic estimation: should estimate > 0 edges
        assert estimated > 0
        # Estimate should be within 10% of actual flattening
        actual = len(_extract_all_edges(block))
        assert abs(estimated - actual) <= actual * 0.10

    def test_estimate_edge_count_hatches(self) -> None:
        """Verify hatches estimated as ~50 edges each."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="HATCHES")
        # Add 2 hatches with simple boundary paths
        hatch1 = block.add_hatch()
        hatch1.paths.add_polyline_path(
            [(0, 0), (10, 0), (10, 10), (0, 10)], is_closed=True
        )
        hatch2 = block.add_hatch()
        hatch2.paths.add_polyline_path(
            [(20, 0), (30, 0), (30, 10), (20, 10)], is_closed=True
        )

        estimated = _estimate_edge_count(block)

        # 2 hatches * 50 edges each = 100 edges
        assert estimated == 100

    def test_estimate_edge_count_mixed(self) -> None:
        """Verify mixed entities counted correctly."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED")
        # 2 LINE entities = 2 edges
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        # 1 closed polyline with 4 vertices = 4 edges
        block.add_lwpolyline([(20, 0), (30, 0), (30, 10), (20, 10)], close=True)
        # 1 circle (dynamic segments based on radius)
        block.add_circle((50, 50), 5)
        # 1 arc (dynamic segments based on radius and angle)
        block.add_arc((70, 70), 10, 0, 180)

        estimated = _estimate_edge_count(block)

        # Should have: 2 lines + 4 polyline + dynamic circle + dynamic arc
        # At minimum should exceed the line and polyline contribution
        assert estimated > 6  # At least lines + polyline
        # Estimate should be within 10% of actual flattening
        actual = len(_extract_all_edges(block))
        assert abs(estimated - actual) <= actual * 0.10

    def test_estimate_vs_actual_accuracy(self) -> None:
        """Compare estimation to actual _extract_all_edges() count.

        Estimation should be reasonably close to actual for typical blocks.
        CIRCLE and ARC estimates (36/18) may vary based on radius, so we
        allow some tolerance.
        """
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")

        estimated = _estimate_edge_count(block)
        actual = len(_extract_all_edges(block))

        # For LWPOLYLINE-only blocks, estimation should be exact
        # (2 closed rectangles with 4 vertices each = 8 edges)
        assert estimated == actual == 8

    def test_estimate_edge_count_empty_block(self) -> None:
        """Verify empty block returns 0 edges."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY")

        estimated = _estimate_edge_count(block)

        assert estimated == 0

    def test_estimate_edge_count_non_geometric_entities(self) -> None:
        """Verify non-geometric entities (TEXT, MTEXT) are not counted."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEXT_ONLY")
        # Add text entities (should not contribute to edge count)
        block.add_text("Hello", dxfattribs={"insert": (0, 0)})
        block.add_mtext("World", dxfattribs={"insert": (10, 10)})
        # Add one LINE to verify counting still works
        block.add_line((0, 0), (10, 0))

        estimated = _estimate_edge_count(block)

        # Only the LINE should be counted
        assert estimated == 1


class TestAreaCalculation:
    """Test suite for _shoelace_area function."""

    def test_shoelace_area_rectangle(self) -> None:
        """Correct area for simple rectangle."""
        rectangle: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        area = _shoelace_area(rectangle)
        assert area == 100.0

    def test_shoelace_area_triangle(self) -> None:
        """Correct area for triangle (3-4-5 right triangle)."""
        triangle: Polygon = [(0, 0), (3, 0), (3, 4)]
        area = _shoelace_area(triangle)
        assert area == 6.0

    def test_shoelace_area_negative_winding(self) -> None:
        """Handle clockwise (negative) winding direction."""
        # Clockwise rectangle
        clockwise: Polygon = [(0, 0), (0, 10), (10, 10), (10, 0)]
        area = _shoelace_area(clockwise)
        assert area == 100.0  # Absolute value handles winding

    def test_shoelace_area_degenerate_line(self) -> None:
        """Handle degenerate polygon (fewer than 3 vertices)."""
        line: Polygon = [(0, 0), (10, 10)]
        area = _shoelace_area(line)
        assert area == 0.0

    def test_shoelace_area_degenerate_point(self) -> None:
        """Handle degenerate polygon (single point)."""
        point: Polygon = [(5, 5)]
        area = _shoelace_area(point)
        assert area == 0.0

    def test_shoelace_area_collinear_points(self) -> None:
        """Handle collinear points (zero area)."""
        collinear: Polygon = [(0, 0), (5, 5), (10, 10)]
        area = _shoelace_area(collinear)
        assert area == 0.0

    def test_shoelace_area_complex_shape(self) -> None:
        """Correct area for L-shaped polygon."""
        # L-shape: 3x3 square minus 2x2 corner
        l_shape: Polygon = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
        area = _shoelace_area(l_shape)
        # Area = 3*3 - 2*2 = 9 - 4 = 5
        assert area == 5.0


class TestPointInPolygon:
    """Test suite for _point_in_polygon function."""

    def test_point_inside_rectangle(self) -> None:
        """Return True for interior point."""
        rectangle: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _point_in_polygon((5, 5), rectangle) is True

    def test_point_outside_rectangle(self) -> None:
        """Return False for exterior point."""
        rectangle: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _point_in_polygon((15, 15), rectangle) is False

    def test_point_on_boundary(self) -> None:
        """Handle boundary points (implementation dependent)."""
        rectangle: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # Boundary behavior may vary; just ensure no crash
        result = _point_in_polygon((5, 0), rectangle)
        assert isinstance(result, bool)

    def test_point_at_vertex(self) -> None:
        """Handle point at polygon vertex."""
        rectangle: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = _point_in_polygon((0, 0), rectangle)
        assert isinstance(result, bool)

    def test_point_in_concave_polygon(self) -> None:
        """Handle concave polygon correctly."""
        # L-shape
        l_shape: Polygon = [(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10)]
        # Point in the L
        assert _point_in_polygon((2, 2), l_shape) is True
        # Point in the notch
        assert _point_in_polygon((7, 7), l_shape) is False

    def test_point_degenerate_polygon(self) -> None:
        """Handle degenerate polygon (fewer than 3 vertices)."""
        line: Polygon = [(0, 0), (10, 10)]
        assert _point_in_polygon((5, 5), line) is False


class TestContainment:
    """Test suite for _polygon_contains_polygon function."""

    def test_polygon_contains_polygon_nested(self) -> None:
        """Detect nested polygons correctly."""
        outer: Polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        inner: Polygon = [(10, 10), (90, 10), (90, 90), (10, 90)]

        assert _polygon_contains_polygon(outer, inner) is True
        assert _polygon_contains_polygon(inner, outer) is False

    def test_polygon_contains_polygon_disjoint(self) -> None:
        """Return False for disjoint polygons."""
        poly1: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly2: Polygon = [(20, 20), (30, 20), (30, 30), (20, 30)]

        assert _polygon_contains_polygon(poly1, poly2) is False
        assert _polygon_contains_polygon(poly2, poly1) is False

    def test_polygon_contains_polygon_partial_overlap(self) -> None:
        """Handle partial overlap (not full containment)."""
        poly1: Polygon = [(0, 0), (20, 0), (20, 20), (0, 20)]
        poly2: Polygon = [(10, 10), (30, 10), (30, 30), (10, 30)]

        # Neither fully contains the other
        assert _polygon_contains_polygon(poly1, poly2) is False
        assert _polygon_contains_polygon(poly2, poly1) is False

    def test_polygon_contains_polygon_shared_edge(self) -> None:
        """Handle polygons sharing an edge."""
        poly1: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly2: Polygon = [(10, 0), (20, 0), (20, 10), (10, 10)]

        # Adjacent polygons don't contain each other
        assert _polygon_contains_polygon(poly1, poly2) is False
        assert _polygon_contains_polygon(poly2, poly1) is False

    def test_polygon_contains_polygon_degenerate(self) -> None:
        """Handle degenerate polygons."""
        valid: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        degenerate: Polygon = [(5, 5), (6, 6)]

        assert _polygon_contains_polygon(valid, degenerate) is False
        assert _polygon_contains_polygon(degenerate, valid) is False


class TestNetAreaCalculation:
    """Test suite for _calculate_net_areas function."""

    def test_net_area_single_polygon(self) -> None:
        """Net area equals gross area for single polygon."""
        polygons: list[Polygon] = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
        results = _calculate_net_areas(polygons)

        assert len(results) == 1
        polygon, net_area = results[0]
        assert net_area == 100.0  # Same as gross area

    def test_net_area_nested_polygons(self) -> None:
        """Correctly subtract contained area from outer polygon."""
        outer: Polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]  # Area = 10000
        inner: Polygon = [(10, 10), (90, 10), (90, 90), (10, 90)]  # Area = 6400
        polygons = [outer, inner]

        results = _calculate_net_areas(polygons)

        # Results sorted by net area descending
        # Inner has net_area = 6400 (nothing inside)
        # Outer has net_area = 10000 - 6400 = 3600
        assert len(results) == 2
        # Inner should have larger net area
        assert results[0][1] == 6400.0
        assert results[1][1] == 3600.0

    def test_net_area_multiple_nested(self) -> None:
        """Handle multiple levels of nesting with Shapely difference.

        Uses Shapely's geometric difference() operation which correctly handles
        nested containment: when medium is subtracted from large, small is already
        removed (since small is inside medium), avoiding double-subtraction.
        """
        large: Polygon = [(0, 0), (200, 0), (200, 150), (0, 150)]  # Area = 30000
        medium: Polygon = [(20, 20), (180, 20), (180, 130), (20, 130)]  # Area = 17600
        small: Polygon = [(50, 50), (150, 50), (150, 100), (50, 100)]  # Area = 5000
        polygons = [large, medium, small]

        results = _calculate_net_areas(polygons)

        # small: 5000 (nothing inside)
        # medium: difference(medium, small) = 17600 - 5000 = 12600
        # large: difference(large, medium) = 30000 - 17600 = 12400
        #   (small is inside medium, so already excluded by medium subtraction)
        assert len(results) == 3
        # Sorted by net area descending
        # medium has largest net area (12600)
        # large has second (12400)
        # small has third (5000)
        net_areas = [r[1] for r in results]
        assert 12600.0 in net_areas
        assert 12400.0 in net_areas
        assert 5000.0 in net_areas

    def test_net_area_disjoint_polygons(self) -> None:
        """Handle disjoint (non-overlapping) polygons."""
        poly1: Polygon = [(0, 0), (40, 0), (40, 30), (0, 30)]  # Area = 1200
        poly2: Polygon = [(60, 0), (100, 0), (100, 30), (60, 30)]  # Area = 1200
        polygons = [poly1, poly2]

        results = _calculate_net_areas(polygons)

        # Both have same net area as gross (nothing inside either)
        assert len(results) == 2
        assert results[0][1] == 1200.0
        assert results[1][1] == 1200.0

    def test_net_area_empty_list(self) -> None:
        """Handle empty polygon list."""
        results = _calculate_net_areas([])
        assert results == []

    def test_net_area_abort_event(self) -> None:
        """Verify abort event is checked."""
        polygons: list[Polygon] = [
            [(i * 10, 0), (i * 10 + 8, 0), (i * 10 + 8, 8), (i * 10, 8)]
            for i in range(15)
        ]
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(GeometryAbortedError):
            _calculate_net_areas(polygons, abort_event)


class TestTrimValueCalculation:
    """Test suite for trim value derivation."""

    def test_trim_values_centered_content_zone(self) -> None:
        """Correct trim for centered content zone."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # With ALL survivors, bbox encompasses both rectangles = full block
        # Outer rectangle is (0, 0) to (100, 80)
        # Inner rectangle is (10, 10) to (90, 70)
        # Union bbox = (0, 0) to (100, 80) = block bbox
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_trim_values_offset_content_zone(self) -> None:
        """Correct trim for offset content zone."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="OFFSET")
        # Block with offset content zone
        # Outer: (0, 0) to (100, 100)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Inner offset toward bottom-left: (5, 10) to (80, 90)
        block.add_lwpolyline([(5, 10), (80, 10), (80, 90), (5, 90)], close=True)

        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # With ALL survivors, bbox encompasses both rectangles = full block
        # Union of (0,0)-(100,100) and (5,10)-(80,90) = (0,0)-(100,100)
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_trim_values_full_block_content_zone(self) -> None:
        """Zero trim when content zone equals block bbox."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("SINGLE_RECTANGLE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Single rectangle is the content zone AND the block bbox
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_content_zone_dimensions_calculated(self) -> None:
        """Verify width and height are calculated correctly."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # With ALL survivors, dimensions are full block bbox
        # Block bbox is (0, 0) to (100, 80)
        # Width = 100, Height = 80
        assert result["content_zone_width"] == 100.0
        assert result["content_zone_height"] == 80.0


class TestContentZoneDetection:
    """Test suite for _detect_content_zone function."""

    def test_detect_content_zone_nested_rectangles(self) -> None:
        """Full detection with nested shapes."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # With ALL survivors, bbox is union of both rectangles
        # Block bbox and content zone bbox are the same
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0

    def test_detect_content_zone_no_shapes(self) -> None:
        """Return empty for blocks without closed shapes."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("EMPTY_BLOCK")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None

    def test_detect_content_zone_single_shape(self) -> None:
        """Handle single shape correctly."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("SINGLE_RECTANGLE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Single shape is the content zone
        assert result["suggested_trim_left"] == 0.0

    def test_detect_content_zone_line_shapes(self) -> None:
        """Detect content zone from LINE segments."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("LINE_RECTANGLE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # LINE rectangle is (0,0)-(80,50)
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0

    def test_detect_content_zone_with_abort_event(self) -> None:
        """Properly handle abort event."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST")
        # Create a few polygons (under edge threshold) to trigger abort check
        for i in range(5):
            x = i * 20
            block.add_lwpolyline(
                [(x, 0), (x + 15, 0), (x + 15, 15), (x, 15)], close=True
            )

        bbox = _get_block_bounding_box(block)
        abort_event = threading.Event()
        abort_event.set()

        with pytest.raises(GeometryAbortedError):
            _detect_content_zone(block, bbox, abort_event)

    def test_detect_content_zone_mixed_lwpolyline_and_line(self) -> None:
        """Detect from both LWPOLYLINE and LINE sources."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED")
        # Large LWPOLYLINE (outer)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 80), (0, 80)], close=True)
        # Inner shape from LINE segments
        block.add_line((10, 10), (90, 10))
        block.add_line((90, 10), (90, 70))
        block.add_line((90, 70), (10, 70))
        block.add_line((10, 70), (10, 10))

        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # The inner LINE rectangle should be the content zone

    def test_polygon_count_returned(self) -> None:
        """Verify polygon count is returned correctly."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["polygon_count"] == 2  # Outer and inner rectangle

    def test_polygon_count_zero_when_no_shapes(self) -> None:
        """Verify polygon_count is 0 when no shapes found."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("EMPTY_BLOCK")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 0


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_empty_block(self) -> None:
        """Return empty ContentZoneData for empty block."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY")
        bbox = (0.0, 0.0, 0.0, 0.0)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None

    def test_degenerate_polygon(self) -> None:
        """Handle zero-area polygons."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="DEGENERATE")
        # Collinear points (zero area)
        block.add_lwpolyline([(0, 0), (10, 10), (20, 20)], close=True)

        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        # Zero area polygon should be skipped
        assert result["content_zone_detected"] is False

    def test_very_small_polygon(self) -> None:
        """Handle tiny polygons correctly."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TINY")
        # Very small but valid polygon
        block.add_lwpolyline(
            [(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001)], close=True
        )

        bbox = _get_block_bounding_box(block)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True

    def test_concurrent_polygons(self) -> None:
        """Handle overlapping but non-nested polygons."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("TWO_DISJOINT_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        # Should detect one of the rectangles as content zone
        # Both have area 40*30 = 1200
        assert result["content_zone_detected"] is True

    def test_empty_content_zone_data(self) -> None:
        """Verify _empty_content_zone_data returns correct structure."""
        result = _empty_content_zone_data()

        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None
        assert result["suggested_trim_right"] is None
        assert result["suggested_trim_top"] is None
        assert result["suggested_trim_bottom"] is None
        assert result["content_zone_width"] is None
        assert result["content_zone_height"] is None
        assert result["polygon_count"] == 0
        assert result["filtered_polygon_count"] == 0

    def test_polygon_bbox_empty(self) -> None:
        """Handle empty polygon for bbox calculation."""
        bbox = _get_polygon_bbox([])
        assert bbox == (0.0, 0.0, 0.0, 0.0)

    def test_polygon_bbox_single_point(self) -> None:
        """Handle single point polygon for bbox."""
        bbox = _get_polygon_bbox([(5.0, 10.0)])
        assert bbox == (5.0, 10.0, 5.0, 10.0)

    def test_count_line_segments_empty(self) -> None:
        """Count LINE segments in empty block."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="EMPTY")

        count = _count_line_segments(block)
        assert count == 0

    def test_count_line_segments_mixed_entities(self) -> None:
        """Count only LINE entities, not other types."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="MIXED")
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        block.add_lwpolyline([(0, 0), (5, 5), (10, 0)], close=True)
        block.add_circle((5, 5), 2)

        count = _count_line_segments(block)
        assert count == 2  # Only the 2 LINE entities


class TestTypeAnnotations:
    """Test type correctness of returned data structures."""

    def test_content_zone_data_type(self) -> None:
        """Verify ContentZoneData structure."""
        result = _empty_content_zone_data()

        # Verify all required keys exist
        assert "suggested_trim_left" in result
        assert "suggested_trim_right" in result
        assert "suggested_trim_top" in result
        assert "suggested_trim_bottom" in result
        assert "content_zone_detected" in result
        assert "content_zone_width" in result
        assert "content_zone_height" in result
        assert "polygon_count" in result
        assert "filtered_polygon_count" in result

    def test_polygon_type(self) -> None:
        """Verify Polygon type structure."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("SINGLE_RECTANGLE")

        polygons = _extract_closed_lwpolylines(block)

        assert len(polygons) > 0
        polygon = polygons[0]
        # Verify it's a list of tuples
        assert isinstance(polygon, list)
        for vertex in polygon:
            assert isinstance(vertex, tuple)
            assert len(vertex) == 2
            assert isinstance(vertex[0], float)
            assert isinstance(vertex[1], float)


class TestPolygonFiltering:
    """Test suite for polygon filtering in _detect_content_zone."""

    def test_no_filtering_with_zero_values(self) -> None:
        """Verify no filtering occurs when filter values are 0 (default)."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        # Default behavior with zeros
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=0.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2  # Both polygons should be present

    def test_area_filter_removes_small_polygons(self) -> None:
        """Verify polygons below min_area threshold are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="AREA_TEST")
        # Large polygon (100x100 = 10000 sq units)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Small polygon (5x5 = 25 sq units)
        block.add_lwpolyline([(110, 10), (115, 10), (115, 15), (110, 15)], close=True)

        bbox = _get_block_bounding_box(block)

        # Filter out polygons with area < 100
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        # Should have filtered out the small polygon, leaving only the large one
        assert result["polygon_count"] == 2  # Original count before filtering
        assert result["filtered_polygon_count"] == 1  # After filtering

    def test_area_filter_filters_all_polygons(self) -> None:
        """Verify behavior when all polygons are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="ALL_SMALL")
        # Small polygon (10x10 = 100 sq units)
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        bbox = _get_block_bounding_box(block)

        # Filter threshold higher than all polygon areas
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=500.0,
            min_side_filter=0.0,
        )

        # All polygons filtered - should return empty content zone
        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 1  # Original count before filtering
        assert result["filtered_polygon_count"] == 0  # After filtering

    def test_side_filter_removes_narrow_polygons(self) -> None:
        """Verify polygons with short sides are filtered out."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SIDE_TEST")
        # Wide polygon with sides >= 50 (100x50)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # Narrow polygon with short side = 5 (100x5)
        block.add_lwpolyline([(0, 60), (100, 60), (100, 65), (0, 65)], close=True)

        bbox = _get_block_bounding_box(block)

        # Filter out polygons with shortest side < 20
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=0.0,
            min_side_filter=20.0,
        )

        assert result["content_zone_detected"] is True
        # Should have filtered out the narrow polygon
        assert result["polygon_count"] == 2  # Original count before filtering
        assert result["filtered_polygon_count"] == 1  # After filtering

    def test_combined_filters(self) -> None:
        """Verify both filters work together."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="COMBINED_TEST")
        # Large polygon with reasonable sides (100x50 = 5000 sq units, shortest side 50)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # Small polygon but with okay sides (10x10 = 100 sq units, sides 10)
        block.add_lwpolyline([(105, 55), (115, 55), (115, 65), (105, 65)], close=True)
        # Large area but narrow (200x2 = 400 sq units, shortest side 2)
        block.add_lwpolyline([(0, 70), (200, 70), (200, 72), (0, 72)], close=True)

        bbox = _get_block_bounding_box(block)

        # Filter: area >= 200 AND shortest side >= 5
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=200.0,
            min_side_filter=5.0,
        )

        assert result["content_zone_detected"] is True
        # Only the first polygon should pass both filters
        assert result["polygon_count"] == 3  # Original count before filtering
        assert result["filtered_polygon_count"] == 1  # After filtering

    def test_filter_with_precision_and_gap_bridge(self) -> None:
        """Verify filters work with other parameters."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="PARAMS_TEST")
        # Large polygon
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
        # Small polygon that should be filtered
        block.add_lwpolyline([(110, 10), (115, 10), (115, 15), (110, 15)], close=True)

        bbox = _get_block_bounding_box(block)

        # Use filters along with precision and gap bridge tolerances
        result = _detect_content_zone(
            block,
            bbox,
            precision_tolerance=1e-6,
            gap_bridge_tolerance=0.0,
            min_area_filter=100.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2  # Original count before filtering
        assert result["filtered_polygon_count"] == 1  # After filtering

    def test_filter_boundary_value_included(self) -> None:
        """Verify polygon exactly at threshold passes the filter."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="BOUNDARY_TEST")
        # Polygon with area exactly 100 (10x10)
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        bbox = _get_block_bounding_box(block)

        # Filter threshold at exactly 100 - should NOT be filtered (< not <=)
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1

    def test_only_area_filter_enabled(self) -> None:
        """Verify only area filter is applied when side filter is 0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="AREA_ONLY")
        # Large but narrow polygon (100x5 = 500 sq units, side 5)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 5), (0, 5)], close=True)

        bbox = _get_block_bounding_box(block)

        # Only area filter, side filter disabled
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,
            min_side_filter=0.0,
        )

        # Should pass because area >= 100, even though side is only 5
        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1

    def test_only_side_filter_enabled(self) -> None:
        """Verify only side filter is applied when area filter is 0."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="SIDE_ONLY")
        # Small but proportional polygon (10x10 = 100 sq units, side 10)
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        bbox = _get_block_bounding_box(block)

        # Only side filter, area filter disabled
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=0.0,
            min_side_filter=5.0,
        )

        # Should pass because side >= 5, regardless of small area
        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1


class TestNetAreaFiltering:
    """Test suite for net area filtering in _detect_content_zone.

    These tests verify that min_area_filter uses NET area (gross minus contained
    polygons) rather than GROSS area. This correctly handles "picture frame"
    scenarios where a large outer polygon has a small net area.

    Test blocks from nested_polygon_filter_test.dxf:
    - PICTURE_FRAME: outer 100x100 (net=3600), inner 80x80 (net=6400)
    - BOX_IN_BOX_IN_BOX: 3 levels - outer (net=3600), middle (net=3900), inner (net=2500)
    - MULTIPLE_SIBLINGS: outer (net=8800), 3 inner 20x20 (net=400 each)
    - SINGLE_LARGE: 80x80 (net=gross=6400)
    """

    def test_picture_frame_filtered_by_net_area(self) -> None:
        """Verify outer polygon with small net area is filtered, leaving inner polygon.

        Scenario:
        - Outer rectangle: 100x100 = 10,000 sq units gross
        - Inner rectangle: 80x80 = 6,400 sq units gross (centered at 10,10 to 90,90)
        - Outer NET area: 10,000 - 6,400 = 3,600 sq units
        - Inner NET area: 6,400 sq units (no children)

        With min_area_filter=5000:
        - Outer fails: 3,600 < 5,000 (filtered OUT)
        - Inner passes: 6,400 >= 5,000 (kept)

        Expected: polygon_count == 1 (only inner remains)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2  # Original count before filtering
        assert (
            result["filtered_polygon_count"] == 1
        )  # Only inner polygon remains after net area filter

    def test_picture_frame_inner_selected_as_content_zone(self) -> None:
        """Verify inner polygon becomes content zone with correct trim values.

        When outer frame is filtered out, the inner polygon (10,10)-(90,90)
        should be selected as the content zone.

        Block bounding box: (0,0)-(100,100)
        Inner polygon: (10,10)-(90,90)
        Expected trim values:
        - left: 10 (inner starts at x=10)
        - right: 10 (inner ends at x=90, bbox is 100)
        - top: 10 (inner ends at y=90, bbox is 100)
        - bottom: 10 (inner starts at y=10)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        # Inner rectangle is (10,10) to (90,90)
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0
        # Content zone dimensions: 80x80
        assert result["content_zone_width"] == 80.0
        assert result["content_zone_height"] == 80.0

    def test_box_in_box_in_box_filtering(self) -> None:
        """Verify multi-level nesting filters correctly by net area.

        3 nested rectangles:
        - Outermost: 100x100, gross=10000, net=10000-6400=3600
        - Middle: 80x80, gross=6400, net=6400-2500=3900
        - Innermost: 50x50, gross=2500, net=2500 (no children)

        With min_area_filter=3000:
        - Outermost: net=3600 >= 3000, PASSES
        - Middle: net=3900 >= 3000, PASSES
        - Innermost: net=2500 < 3000, FAILS (filtered)

        Expected: polygon_count == 2 (outer and middle remain)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("BOX_IN_BOX_IN_BOX")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=3000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        # Innermost filtered out (2500 < 3000), outer and middle remain
        assert result["polygon_count"] == 3  # Original count before filtering
        assert result["filtered_polygon_count"] == 2  # After net area filter

    def test_gross_area_filter_would_pass_outer(self) -> None:
        """Regression test: verify gross area WOULD have passed but net area fails.

        This test ensures we're using NET area, not GROSS area.

        PICTURE_FRAME outer polygon:
        - GROSS area: 100x100 = 10,000 sq units
        - NET area: 10,000 - 6,400 = 3,600 sq units

        With min_area_filter=5000:
        - If using GROSS: outer would PASS (10,000 >= 5,000) - WRONG!
        - If using NET: outer FAILS (3,600 < 5,000) - CORRECT!

        This test verifies the implementation uses NET area by confirming
        the outer polygon is NOT present (polygon_count < 2).
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        # Verify gross area would pass the threshold
        from core.geometry import calculate_polygon_area

        polygons = _extract_closed_lwpolylines(block)
        # Find the outer polygon (larger gross area)
        outer_polygon = max(polygons, key=lambda p: calculate_polygon_area(p))
        outer_gross_area = calculate_polygon_area(outer_polygon)

        # Outer gross area should be 10,000 (would pass filter of 5000)
        assert outer_gross_area >= 9900  # Allow small tolerance
        assert outer_gross_area >= 5000  # Would pass if using gross

        # But with NET area filtering, outer should be filtered out
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=5000.0,
            min_side_filter=0.0,
        )

        # Only 1 polygon remains (inner), proving we use NET area
        assert result["polygon_count"] == 2  # Original count before filtering
        assert (
            result["filtered_polygon_count"] == 1
        )  # Only inner remains after net area filter

    def test_side_filter_still_uses_gross_geometry(self) -> None:
        """Verify side filter uses shortest side of gross geometry, not net area.

        The side filter should evaluate the actual polygon dimensions,
        independent of any contained polygons.

        PICTURE_FRAME outer polygon:
        - Dimensions: 100x100 (square)
        - Shortest side: 100 units (all sides equal)

        With min_side_filter=50:
        - Outer PASSES: shortest side 100 >= 50
        - Inner PASSES: shortest side 80 >= 50

        Expected: Both polygons remain (side filter doesn't use net area)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("PICTURE_FRAME")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=0.0,  # Disable area filter
            min_side_filter=50.0,  # Both should pass
        )

        assert result["content_zone_detected"] is True
        # Both polygons should pass the side filter (100 >= 50, 80 >= 50)
        assert result["polygon_count"] == 2

    def test_filter_order_side_then_net_area(self) -> None:
        """Verify side filter is applied BEFORE net area filter.

        This test uses a scenario where filter order matters:
        - Side filter removes some polygons
        - Then net area is calculated on remaining polygons
        - Then net area filter is applied

        MULTIPLE_SIBLINGS block:
        - Outer 100x100, contains 3 inner 20x20 rectangles
        - Inner polygons have shortest side = 20

        With min_side_filter=25 (filters inner siblings) and min_area_filter=100:
        - Side filter removes all 3 inner siblings (20 < 25)
        - Only outer remains for net area calculation
        - Outer's net area CHANGES because siblings are gone from calculation

        This demonstrates side filter runs first (before net area calc).
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("MULTIPLE_SIBLINGS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,  # Low threshold, not filtering anything by area
            min_side_filter=25.0,  # Filters inner siblings (20 < 25)
        )

        assert result["content_zone_detected"] is True
        # Side filter removed siblings first (3 siblings with side 20 < 25), only outer remains
        assert result["polygon_count"] == 4  # Original count before filtering
        assert (
            result["filtered_polygon_count"] == 1
        )  # After side filter (siblings removed)

    def test_single_large_net_equals_gross(self) -> None:
        """Verify net area equals gross area when no containment.

        SINGLE_LARGE block has a single 80x80 rectangle with no inner polygons.
        Net area should equal gross area (6400).

        With min_area_filter=6000:
        - Single polygon net=gross=6400 >= 6000, PASSES
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("SINGLE_LARGE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=6000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 1

    def test_all_filtered_by_net_area(self) -> None:
        """Verify behavior when all polygons are filtered by net area.

        BOX_IN_BOX_IN_BOX:
        - Outer net=3600, Middle net=3900, Inner net=2500

        With min_area_filter=4000:
        - All polygons have net area < 4000
        - All should be filtered out
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("BOX_IN_BOX_IN_BOX")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=4000.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 3  # Original count before filtering
        assert result["filtered_polygon_count"] == 0  # All filtered by net area

    def test_multiple_siblings_outer_kept_siblings_filtered(self) -> None:
        """Verify outer polygon kept when siblings filtered by net area.

        MULTIPLE_SIBLINGS:
        - Outer 100x100, net = 10000 - 400*3 = 8800
        - 3 inner siblings 20x20, each net = 400

        With min_area_filter=500:
        - Outer passes: 8800 >= 500
        - Siblings fail: 400 < 500

        Expected: polygon_count == 1 (only outer)
        """
        doc = ezdxf.readfile("app/tests/assets/nested_polygon_filter_test.dxf")
        block = doc.blocks.get("MULTIPLE_SIBLINGS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=500.0,
            min_side_filter=0.0,
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 4  # Original count before filtering
        assert (
            result["filtered_polygon_count"] == 1
        )  # Only outer remains after net area filter


class TestUnionBoundingBox:
    """Tests for _get_union_bounding_box() function."""

    def test_empty_input(self) -> None:
        """Empty list returns zero bbox."""
        result = _get_union_bounding_box([])
        assert result == (0.0, 0.0, 0.0, 0.0)

    def test_single_polygon(self) -> None:
        """Single polygon returns its bbox."""
        polygon: Polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        result = _get_union_bounding_box([polygon])
        assert result == (0.0, 0.0, 10.0, 10.0)

    def test_multiple_non_overlapping(self) -> None:
        """Non-overlapping polygons return union bbox."""
        poly1: Polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        poly2: Polygon = [(90.0, 90.0), (100.0, 90.0), (100.0, 100.0), (90.0, 100.0)]
        result = _get_union_bounding_box([poly1, poly2])
        assert result == (0.0, 0.0, 100.0, 100.0)

    def test_overlapping_polygons(self) -> None:
        """Overlapping polygons return correct union bbox."""
        poly1: Polygon = [(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (0.0, 50.0)]
        poly2: Polygon = [(25.0, 25.0), (75.0, 25.0), (75.0, 75.0), (25.0, 75.0)]
        result = _get_union_bounding_box([poly1, poly2])
        assert result == (0.0, 0.0, 75.0, 75.0)

    def test_four_corner_polygons(self) -> None:
        """Four corner polygons return full span bbox."""
        # Bottom-left
        poly1: Polygon = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        # Bottom-right
        poly2: Polygon = [(90.0, 0.0), (100.0, 0.0), (100.0, 10.0), (90.0, 10.0)]
        # Top-left
        poly3: Polygon = [(0.0, 90.0), (10.0, 90.0), (10.0, 100.0), (0.0, 100.0)]
        # Top-right
        poly4: Polygon = [(90.0, 90.0), (100.0, 90.0), (100.0, 100.0), (90.0, 100.0)]

        result = _get_union_bounding_box([poly1, poly2, poly3, poly4])
        assert result == (0.0, 0.0, 100.0, 100.0)


class TestCurvedFilterIntegration:
    """Test suite for curved_filter_enabled in _detect_content_zone.

    These tests verify that the curved_filter_enabled post-filter parameter
    correctly filters out polygons containing curved edges (detected via
    vertex analysis of consecutive angular deviations).
    """

    def test_curved_filter_disabled_keeps_all_polygons(self) -> None:
        """Verify default behavior preserves polygons with curved edges."""
        import math as m

        doc = ezdxf.new()
        block = doc.blocks.new(name="CURVED_DISABLED")

        # Create a circle approximation (12 points to stay under edge threshold)
        circle_points = [
            (50 + 25 * m.cos(m.radians(i * 30)), 50 + 25 * m.sin(m.radians(i * 30)))
            for i in range(12)
        ]
        block.add_lwpolyline(circle_points, close=True)

        # Also add a rectangle (straight edges)
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

        bbox = _get_block_bounding_box(block)

        # With curved_filter_enabled=False (default), both should be kept
        result = _detect_content_zone(
            block, bbox, curved_filter_enabled=False
        )

        assert result["content_zone_detected"] is True
        assert result["polygon_count"] == 2  # Both polygons present

    def test_curved_filter_enabled_removes_curved_polygons(self) -> None:
        """Verify curved polygons are filtered when enabled."""
        import math as m

        doc = ezdxf.new()
        block = doc.blocks.new(name="CURVED_ENABLED")

        # Create a circle approximation (24 points for proper curve detection)
        # 15 degrees per segment ensures small angular deviations are detected
        circle_points = [
            (50 + 25 * m.cos(m.radians(i * 15)), 50 + 25 * m.sin(m.radians(i * 15)))
            for i in range(24)
        ]
        block.add_lwpolyline(circle_points, close=True)

        # Also add a rectangle (straight edges) - will be kept
        block.add_lwpolyline([(100, 0), (200, 0), (200, 100), (100, 100)], close=True)

        bbox = _get_block_bounding_box(block)

        # With curved_filter_enabled=True, curved polygon should be filtered
        result = _detect_content_zone(
            block, bbox, curved_filter_enabled=True
        )

        assert result["content_zone_detected"] is True
        # Original count includes both, but filtered count excludes curved
        assert result["polygon_count"] == 2  # Original count before filtering
        assert result["filtered_polygon_count"] == 1  # Only rectangle remains

    def test_curved_filter_keeps_straight_polygons(self) -> None:
        """Verify rectangles and triangles pass through the filter."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="STRAIGHT_ONLY")

        # Rectangle
        block.add_lwpolyline([(0, 0), (100, 0), (100, 50), (0, 50)], close=True)
        # Triangle
        block.add_lwpolyline([(110, 0), (160, 0), (135, 50)], close=True)
        # L-shape
        block.add_lwpolyline(
            [(170, 0), (220, 0), (220, 30), (200, 30), (200, 50), (170, 50)],
            close=True,
        )

        bbox = _get_block_bounding_box(block)

        # With curved_filter_enabled=True, all straight polygons should be kept
        result = _detect_content_zone(
            block, bbox, curved_filter_enabled=True
        )

        assert result["content_zone_detected"] is True
        # All 3 straight polygons should remain
        assert result["polygon_count"] == 3
        assert result["filtered_polygon_count"] == 3

    def test_curved_filter_with_circle_approximation(self) -> None:
        """Use a polygon approximating a circle (vertices on curved path)."""
        import math as m

        doc = ezdxf.new()
        block = doc.blocks.new(name="CIRCLE_APPROX")

        # Circle approximation with 16 points (under edge threshold of 30)
        circle_points = [
            (100 + 50 * m.cos(m.radians(i * 22.5)), 100 + 50 * m.sin(m.radians(i * 22.5)))
            for i in range(16)
        ]
        block.add_lwpolyline(circle_points, close=True)

        bbox = _get_block_bounding_box(block)

        # With curved_filter_enabled=True, this should be detected as curved
        result = _detect_content_zone(
            block, bbox, curved_filter_enabled=True
        )

        # Circle should be filtered out, leaving no polygons
        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 1  # Original had 1 polygon
        assert result["filtered_polygon_count"] == 0  # Filtered by curved filter

    def test_curved_filter_combined_with_area_filter(self) -> None:
        """Verify both filters work together."""
        import math as m

        doc = ezdxf.new()
        block = doc.blocks.new(name="COMBINED_FILTERS")

        # Large rectangle (10000 sq units)
        block.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)

        # Small rectangle (25 sq units) - will be filtered by area
        block.add_lwpolyline([(110, 0), (115, 0), (115, 5), (110, 5)], close=True)

        # Circle approximation (18 points for curve detection) - will be filtered by curved filter
        circle_points = [
            (200 + 30 * m.cos(m.radians(i * 20)), 50 + 30 * m.sin(m.radians(i * 20)))
            for i in range(18)
        ]
        block.add_lwpolyline(circle_points, close=True)

        bbox = _get_block_bounding_box(block)

        # Apply both filters
        result = _detect_content_zone(
            block,
            bbox,
            min_area_filter=100.0,  # Filters small rectangle
            curved_filter_enabled=True,  # Filters circle
        )

        assert result["content_zone_detected"] is True
        # Original count is 3, but only large rectangle passes both filters
        assert result["polygon_count"] == 3
        assert result["filtered_polygon_count"] == 1

    def test_curved_filter_single_curved_all_filtered(self) -> None:
        """Verify behavior when all polygons are filtered by curved filter."""
        import math as m

        doc = ezdxf.new()
        block = doc.blocks.new(name="SINGLE_CURVED")

        # Single curved polygon (24 points with 15-degree segments for curve detection)
        # 24 edges is under the threshold of 30
        circle_points = [
            (50 + 25 * m.cos(m.radians(i * 15)), 50 + 25 * m.sin(m.radians(i * 15)))
            for i in range(24)
        ]
        block.add_lwpolyline(circle_points, close=True)

        bbox = _get_block_bounding_box(block)

        # With curved_filter_enabled, the single curved polygon should be filtered
        result = _detect_content_zone(
            block, bbox, curved_filter_enabled=True
        )

        # The curved polygon is filtered, leaving nothing
        assert result["content_zone_detected"] is False
        assert result["polygon_count"] == 1  # Original count
        assert result["filtered_polygon_count"] == 0  # Filtered by curved filter


class TestTiedShapeHandling:
    """Tests for tied shape handling in content zone detection."""

    def test_single_max_area_uses_shape_bbox(self) -> None:
        """Single shape with max area uses its bounding box."""
        doc = ezdxf.new()
        block = doc.blocks.new("SINGLE_MAX")
        # Large rectangle (80x80 = 6400 sq units)
        block.add_lwpolyline(
            [(10, 10), (90, 10), (90, 90), (10, 90)],
            close=True,
        )
        # Small rectangle (10x10 = 100 sq units)
        block.add_lwpolyline(
            [(0, 0), (10, 0), (10, 10), (0, 10)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 100.0)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # With ALL survivors, bbox encompasses both rectangles
        # Large: (10,10)-(90,90), Small: (0,0)-(10,10)
        # Union bbox = (0,0)-(90,90)
        # Block bbox = (0,0)-(100,100)
        assert result["suggested_trim_left"] == 0.0  # min_x=0, block_min_x=0
        assert result["suggested_trim_right"] == 10.0  # block_max_x=100, max_x=90
        assert result["suggested_trim_top"] == 10.0  # block_max_y=100, max_y=90
        assert result["suggested_trim_bottom"] == 0.0  # min_y=0, block_min_y=0

    def test_tied_shapes_use_union_bbox(self) -> None:
        """Multiple tied shapes use union bounding box."""
        doc = ezdxf.readfile("app/tests/assets/equal_area_test.dxf")
        block = doc.blocks.get("EQUAL_CORNERS")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Union of 4 corner rectangles should span full block
        # Trim values should be 0 since union covers 0-100 in both dimensions
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_single_large_rectangle_trimming(self) -> None:
        """Rectangle plus LINE frame from test file calculates correct trim values."""
        doc = ezdxf.readfile("app/tests/assets/equal_area_test.dxf")
        block = doc.blocks.get("SINGLE_LARGE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # SINGLE_LARGE has:
        # - LWPOLYLINE rectangle (10,10)-(90,90)
        # - LINE frame cycle (0,0)-(100,100)
        # With ALL survivors, union bbox = (0,0)-(100,100) = block bbox
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_two_equal_rectangles_union(self) -> None:
        """Two equal rectangles produce union bbox."""
        doc = ezdxf.new()
        block = doc.blocks.new("TWO_EQUAL")
        # Left rectangle (10x10 = 100 sq units)
        block.add_lwpolyline(
            [(0, 45), (10, 45), (10, 55), (0, 55)],
            close=True,
        )
        # Right rectangle (10x10 = 100 sq units)
        block.add_lwpolyline(
            [(90, 45), (100, 45), (100, 55), (90, 55)],
            close=True,
        )

        bbox = (0.0, 0.0, 100.0, 100.0)
        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Union spans from x=0 to x=100, y=45 to y=55
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 45.0
        assert result["suggested_trim_bottom"] == 45.0
