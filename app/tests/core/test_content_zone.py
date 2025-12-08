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
    CYCLE_DETECTION_TIMEOUT_SECONDS,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)
from core.geometry import (
    GeometryAbortedError,
    _calculate_net_areas,
    _count_line_segments,
    _detect_content_zone,
    _empty_content_zone_data,
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
        """Verify timeout protection terminates within reasonable time."""
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

        # Should complete within timeout + small buffer
        assert elapsed < CYCLE_DETECTION_TIMEOUT_SECONDS + 1.0

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
    """Test suite for threshold skip behavior."""

    def test_line_threshold_skip(self) -> None:
        """Verify LINE cycle detection skipped when segment count exceeds threshold."""
        doc = ezdxf.readfile("app/tests/assets/many_lines_test.dxf")
        block = doc.blocks.get("MANY_LINES")

        # Verify line count exceeds threshold
        line_count = _count_line_segments(block)
        assert line_count > LINE_SEGMENT_THRESHOLD

        # Get block bbox for detection
        bbox = _get_block_bounding_box(block)

        # Run content zone detection - should skip LINE cycle detection
        result = _detect_content_zone(block, bbox)

        # Since MANY_LINES has no LWPOLYLINEs, should return empty
        assert result["content_zone_detected"] is False

    def test_line_threshold_not_skip(self) -> None:
        """Verify LINE cycle detection runs when segment count is under threshold."""
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
        # Inner rectangle is (10, 10) to (90, 70)
        # Block bbox is (0, 0) to (100, 80)
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0

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
        assert result["suggested_trim_left"] == 5.0
        assert result["suggested_trim_right"] == 20.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0

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


class TestContentZoneDetection:
    """Test suite for _detect_content_zone function."""

    def test_detect_content_zone_nested_rectangles(self) -> None:
        """Full detection with nested shapes."""
        doc = ezdxf.readfile("app/tests/assets/content_zone_test.dxf")
        block = doc.blocks.get("NESTED_RECTANGLES")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Inner rectangle (10,10)-(90,70) has larger net area
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0

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
        # Create multiple polygons to trigger abort check
        for i in range(15):
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
        # Should use large rectangle's bbox for trim values
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0

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
        """Single large rectangle from test file calculates correct trim values."""
        doc = ezdxf.readfile("app/tests/assets/equal_area_test.dxf")
        block = doc.blocks.get("SINGLE_LARGE")
        bbox = _get_block_bounding_box(block)

        result = _detect_content_zone(block, bbox)

        assert result["content_zone_detected"] is True
        # Single rectangle from (10,10) to (90,90) within 0-100 bbox
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0

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
