"""
Unit tests for content zone detection functionality.

Tests cover:
- Polygon area calculation (shoelace formula)
- Point-in-polygon tests (ray casting)
- Polygon containment checks
- Closed LWPOLYLINE extraction
- LINE cycle detection
- Net area calculation with nested shapes
- Full content zone detection pipeline
"""

import os
from pathlib import Path

import ezdxf
import pytest

from core.geometry import (
    _calculate_net_areas,
    _calculate_polygon_area,
    _detect_content_zone,
    _extract_closed_lwpolylines,
    _extract_line_cycles,
    _get_polygon_bounding_box,
    _get_union_bounding_box,
    _point_in_polygon,
    _polygon_contains_polygon,
)
from core.types import Polygon


class TestPolygonArea:
    """Test cases for shoelace formula area calculation."""

    def test_square_area(self) -> None:
        """Test area of a unit square."""
        square: Polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert _calculate_polygon_area(square) == 1.0

    def test_rectangle_area(self) -> None:
        """Test area of a 4x3 rectangle."""
        rect: Polygon = [(0, 0), (4, 0), (4, 3), (0, 3)]
        assert _calculate_polygon_area(rect) == 12.0

    def test_triangle_area(self) -> None:
        """Test area of a right triangle (3-4-5)."""
        triangle: Polygon = [(0, 0), (3, 0), (0, 4)]
        assert _calculate_polygon_area(triangle) == 6.0

    def test_irregular_polygon_area(self) -> None:
        """Test area of an irregular polygon."""
        # L-shaped polygon (10x10 square with 5x5 corner removed)
        l_shape: Polygon = [(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10)]
        # Area = 100 - 25 = 75
        assert _calculate_polygon_area(l_shape) == 75.0

    def test_empty_polygon_area(self) -> None:
        """Test that empty polygon returns 0."""
        empty: Polygon = []
        assert _calculate_polygon_area(empty) == 0.0

    def test_degenerate_line_area(self) -> None:
        """Test that a line (2 vertices) returns 0."""
        line: Polygon = [(0, 0), (5, 5)]
        assert _calculate_polygon_area(line) == 0.0

    def test_clockwise_counterclockwise_same_area(self) -> None:
        """Test that vertex order doesn't affect area (absolute value)."""
        ccw: Polygon = [(0, 0), (4, 0), (4, 3), (0, 3)]
        cw: Polygon = [(0, 0), (0, 3), (4, 3), (4, 0)]
        assert _calculate_polygon_area(ccw) == _calculate_polygon_area(cw)


class TestPointInPolygon:
    """Test cases for point-in-polygon ray casting."""

    def test_point_inside_square(self) -> None:
        """Test point clearly inside a square."""
        square: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _point_in_polygon((5, 5), square) is True

    def test_point_outside_square(self) -> None:
        """Test point clearly outside a square."""
        square: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _point_in_polygon((15, 5), square) is False
        assert _point_in_polygon((-5, 5), square) is False
        assert _point_in_polygon((5, 15), square) is False

    def test_point_on_vertex(self) -> None:
        """Test point exactly on a vertex."""
        square: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _point_in_polygon((0, 0), square) is True
        assert _point_in_polygon((10, 10), square) is True

    def test_point_near_edge(self) -> None:
        """Test points just inside and outside edges."""
        square: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # Just inside
        assert _point_in_polygon((0.001, 5), square) is True
        # Just outside
        assert _point_in_polygon((-0.001, 5), square) is False

    def test_empty_polygon(self) -> None:
        """Test that empty polygon returns False."""
        empty: Polygon = []
        assert _point_in_polygon((5, 5), empty) is False

    def test_degenerate_polygon(self) -> None:
        """Test that 2-vertex polygon returns False."""
        line: Polygon = [(0, 0), (10, 0)]
        assert _point_in_polygon((5, 0), line) is False


class TestPolygonContainment:
    """Test cases for polygon containment checks."""

    def test_contained_polygon(self) -> None:
        """Test inner polygon fully contained in outer."""
        outer: Polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        inner: Polygon = [(20, 20), (80, 20), (80, 80), (20, 80)]
        assert _polygon_contains_polygon(outer, inner) is True

    def test_not_contained_partial_overlap(self) -> None:
        """Test inner polygon partially overlapping outer."""
        outer: Polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        partial: Polygon = [(50, 50), (150, 50), (150, 150), (50, 150)]
        assert _polygon_contains_polygon(outer, partial) is False

    def test_not_contained_disjoint(self) -> None:
        """Test completely separate polygons."""
        poly_a: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly_b: Polygon = [(20, 20), (30, 20), (30, 30), (20, 30)]
        assert _polygon_contains_polygon(poly_a, poly_b) is False
        assert _polygon_contains_polygon(poly_b, poly_a) is False

    def test_same_polygon_not_contains_self(self) -> None:
        """Test that identical polygons - all vertices on boundary count as contained."""
        poly: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # All vertices are on the boundary, which we treat as "inside"
        assert _polygon_contains_polygon(poly, poly) is True

    def test_empty_polygons(self) -> None:
        """Test with empty polygons."""
        poly: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        empty: Polygon = []
        assert _polygon_contains_polygon(poly, empty) is False
        assert _polygon_contains_polygon(empty, poly) is False


class TestPolygonBoundingBox:
    """Test cases for polygon bounding box extraction."""

    def test_simple_rectangle(self) -> None:
        """Test bounding box of a rectangle."""
        rect: Polygon = [(1, 2), (5, 2), (5, 6), (1, 6)]
        bbox = _get_polygon_bounding_box(rect)
        assert bbox == (1, 2, 5, 6)

    def test_irregular_polygon(self) -> None:
        """Test bounding box of irregular polygon."""
        poly: Polygon = [(0, 5), (3, 0), (6, 5), (3, 10)]
        bbox = _get_polygon_bounding_box(poly)
        assert bbox == (0, 0, 6, 10)

    def test_empty_polygon(self) -> None:
        """Test bounding box of empty polygon."""
        empty: Polygon = []
        bbox = _get_polygon_bounding_box(empty)
        assert bbox == (0.0, 0.0, 0.0, 0.0)


class TestClosedLwpolylineExtraction:
    """Test cases for closed LWPOLYLINE extraction from block definitions."""

    @pytest.fixture
    def simple_block_with_closed_polyline(self) -> ezdxf.document.Drawing:
        """Create a document with a block containing a closed polyline."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)
        return doc

    @pytest.fixture
    def block_with_open_polyline(self) -> ezdxf.document.Drawing:
        """Create a document with a block containing an open polyline."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_lwpolyline([(0, 0), (10, 0), (10, 10)], close=False)
        return doc

    def test_extracts_closed_polyline(
        self, simple_block_with_closed_polyline: ezdxf.document.Drawing
    ) -> None:
        """Test that closed polylines are extracted."""
        doc = simple_block_with_closed_polyline
        block_def = doc.blocks.get("TEST_BLOCK")
        polygons = _extract_closed_lwpolylines(block_def)
        assert len(polygons) == 1
        assert len(polygons[0]) == 4

    def test_skips_open_polyline(
        self, block_with_open_polyline: ezdxf.document.Drawing
    ) -> None:
        """Test that open polylines are skipped."""
        doc = block_with_open_polyline
        block_def = doc.blocks.get("TEST_BLOCK")
        polygons = _extract_closed_lwpolylines(block_def)
        assert len(polygons) == 0


class TestLineCycleDetection:
    """Test cases for LINE-based cycle detection."""

    @pytest.fixture
    def block_with_line_rectangle(self) -> ezdxf.document.Drawing:
        """Create a document with a block containing a rectangle made of lines."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_line((0, 0), (10, 0))
        block.add_line((10, 0), (10, 10))
        block.add_line((10, 10), (0, 10))
        block.add_line((0, 10), (0, 0))
        return doc

    @pytest.fixture
    def block_with_disconnected_lines(self) -> ezdxf.document.Drawing:
        """Create a document with a block containing disconnected lines."""
        doc = ezdxf.new()
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_line((0, 0), (10, 0))
        block.add_line((20, 20), (30, 30))
        return doc

    def test_detects_line_rectangle(
        self, block_with_line_rectangle: ezdxf.document.Drawing
    ) -> None:
        """Test detection of rectangle made from lines."""
        doc = block_with_line_rectangle
        block_def = doc.blocks.get("TEST_BLOCK")
        cycles = _extract_line_cycles(block_def)
        assert len(cycles) == 1
        assert len(cycles[0]) == 4

    def test_no_cycles_in_disconnected_lines(
        self, block_with_disconnected_lines: ezdxf.document.Drawing
    ) -> None:
        """Test that disconnected lines don't form cycles."""
        doc = block_with_disconnected_lines
        block_def = doc.blocks.get("TEST_BLOCK")
        cycles = _extract_line_cycles(block_def)
        assert len(cycles) == 0


class TestNetAreaCalculation:
    """Test cases for net area calculation with containment."""

    def test_simple_nested_rectangles(self) -> None:
        """Test net area with outer containing inner rectangle."""
        outer: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]  # area = 100
        inner: Polygon = [(2, 2), (8, 2), (8, 8), (2, 8)]  # area = 36
        results = _calculate_net_areas([outer, inner])

        # Find outer and inner in results
        outer_result = next(
            (p, a) for p, a in results if _calculate_polygon_area(p) == 100
        )
        inner_result = next(
            (p, a) for p, a in results if _calculate_polygon_area(p) == 36
        )

        # Outer net area = 100 - 36 = 64
        assert outer_result[1] == 64.0
        # Inner net area = 36 (nothing contained)
        assert inner_result[1] == 36.0

    def test_disjoint_shapes(self) -> None:
        """Test that disjoint shapes have net area = own area."""
        poly_a: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]  # area = 100
        poly_b: Polygon = [(20, 0), (30, 0), (30, 10), (20, 10)]  # area = 100
        results = _calculate_net_areas([poly_a, poly_b])

        # Both should have net area = own area = 100
        for _, net_area in results:
            assert net_area == 100.0

    def test_empty_list(self) -> None:
        """Test with empty polygon list."""
        results = _calculate_net_areas([])
        assert results == []


class TestContentZoneDetection:
    """Test cases for full content zone detection pipeline."""

    @pytest.fixture
    def test_dxf_path(self) -> str:
        """Return path to the test DXF file."""
        return str(Path(__file__).parent.parent / "assets" / "content_zone_test.dxf")

    def test_nested_rectangles_block(self, test_dxf_path: str) -> None:
        """Test content zone detection for nested rectangles block."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(test_dxf_path)
        block_def = doc.blocks.get("NESTED_RECTANGLES")
        bbox = (0, 0, 100, 50)  # Block bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # Inner rectangle is at (10, 10) to (90, 40)
        # Trim left = 10 - 0 = 10
        # Trim right = 100 - 90 = 10
        # Trim top = 50 - 40 = 10
        # Trim bottom = 10 - 0 = 10
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0

    def test_single_shape_block(self, test_dxf_path: str) -> None:
        """Test content zone detection for block with single shape."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(test_dxf_path)
        block_def = doc.blocks.get("SINGLE_SHAPE")
        bbox = (0, 0, 50, 30)  # Block bounding box = shape bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # Single shape is the content zone, trim values should be 0
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_no_closed_shapes_block(self, test_dxf_path: str) -> None:
        """Test content zone detection for block with no closed shapes."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(test_dxf_path)
        block_def = doc.blocks.get("NO_CLOSED_SHAPES")
        bbox = (0, 0, 50, 30)

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is False
        assert result["suggested_trim_left"] is None
        assert result["suggested_trim_right"] is None
        assert result["suggested_trim_top"] is None
        assert result["suggested_trim_bottom"] is None

    def test_line_rectangle_block(self, test_dxf_path: str) -> None:
        """Test content zone detection for LINE-based rectangle block."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(test_dxf_path)
        block_def = doc.blocks.get("LINE_RECTANGLE")
        bbox = (0, 0, 80, 40)  # Block bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # Inner rectangle is at (10, 10) to (70, 30)
        assert result["suggested_trim_left"] == 10.0
        assert result["suggested_trim_right"] == 10.0
        assert result["suggested_trim_top"] == 10.0
        assert result["suggested_trim_bottom"] == 10.0


class TestContentZoneIntegration:
    """Integration tests for content zone detection in extraction pipeline."""

    @pytest.fixture
    def test_dxf_path(self) -> str:
        """Return path to the test DXF file."""
        return str(Path(__file__).parent.parent / "assets" / "content_zone_test.dxf")

    def test_extraction_includes_content_zone_data(self, test_dxf_path: str) -> None:
        """Test that block extraction includes content zone data."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        from core.extractor import extract_blocks

        result = extract_blocks(test_dxf_path)

        # Check that NESTED_RECTANGLES block has content zone data
        assert "NESTED_RECTANGLES" in result["block_trimming_data"]
        trimming_data = result["block_trimming_data"]["NESTED_RECTANGLES"]

        assert trimming_data["content_zone_detected"] is True
        assert trimming_data["suggested_trim_left"] == 10.0
        assert trimming_data["suggested_trim_right"] == 10.0
        assert trimming_data["suggested_trim_top"] == 10.0
        assert trimming_data["suggested_trim_bottom"] == 10.0

    def test_extraction_no_content_zone_data(self, test_dxf_path: str) -> None:
        """Test that blocks without closed shapes have no content zone."""
        if not os.path.exists(test_dxf_path):
            pytest.skip("Test DXF file not found")

        from core.extractor import extract_blocks

        result = extract_blocks(test_dxf_path)

        # Check that NO_CLOSED_SHAPES block has no content zone
        assert "NO_CLOSED_SHAPES" in result["block_trimming_data"]
        trimming_data = result["block_trimming_data"]["NO_CLOSED_SHAPES"]

        assert trimming_data["content_zone_detected"] is False
        assert trimming_data["suggested_trim_left"] is None
        assert trimming_data["suggested_trim_right"] is None
        assert trimming_data["suggested_trim_top"] is None
        assert trimming_data["suggested_trim_bottom"] is None


class TestUnionBoundingBox:
    """Test cases for union bounding box calculation."""

    def test_single_polygon(self) -> None:
        """Union of single polygon equals its own bounding box."""
        poly: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        bbox = _get_union_bounding_box([poly])
        assert bbox == (0, 0, 10, 10)

    def test_two_disjoint_polygons(self) -> None:
        """Union spans both disjoint polygons."""
        poly_a: Polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly_b: Polygon = [(90, 90), (100, 90), (100, 100), (90, 100)]
        bbox = _get_union_bounding_box([poly_a, poly_b])
        assert bbox == (0, 0, 100, 100)

    def test_four_corner_polygons(self) -> None:
        """Union of 4 corner polygons spans entire area."""
        corners: list[Polygon] = [
            [(0, 0), (10, 0), (10, 10), (0, 10)],  # bottom-left
            [(90, 0), (100, 0), (100, 10), (90, 10)],  # bottom-right
            [(0, 90), (10, 90), (10, 100), (0, 100)],  # top-left
            [(90, 90), (100, 90), (100, 100), (90, 100)],  # top-right
        ]
        bbox = _get_union_bounding_box(corners)
        assert bbox == (0, 0, 100, 100)

    def test_empty_list(self) -> None:
        """Empty list returns zero bounding box."""
        bbox = _get_union_bounding_box([])
        assert bbox == (0.0, 0.0, 0.0, 0.0)

    def test_overlapping_polygons(self) -> None:
        """Union of overlapping polygons spans outer extent."""
        poly_a: Polygon = [(0, 0), (50, 0), (50, 50), (0, 50)]
        poly_b: Polygon = [(30, 30), (80, 30), (80, 80), (30, 80)]
        bbox = _get_union_bounding_box([poly_a, poly_b])
        assert bbox == (0, 0, 80, 80)


class TestTiedNetAreaContentZone:
    """Test cases for content zone detection with tied net areas."""

    @pytest.fixture
    def equal_area_dxf_path(self) -> str:
        """Return path to the equal area test DXF file."""
        return str(Path(__file__).parent.parent / "assets" / "equal_area_test.dxf")

    def test_four_equal_corners_block(self, equal_area_dxf_path: str) -> None:
        """Test content zone spans all 4 equal corner shapes."""
        if not os.path.exists(equal_area_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(equal_area_dxf_path)
        block_def = doc.blocks.get("FOUR_CORNERS")
        bbox = (0, 0, 100, 100)  # Block bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # All 4 corners have equal area (10x10 = 100), union spans 0-100 in both axes
        # Content zone = block bbox, so all trims = 0
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_two_equal_horizontal_block(self, equal_area_dxf_path: str) -> None:
        """Test content zone spans both equal horizontal shapes."""
        if not os.path.exists(equal_area_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(equal_area_dxf_path)
        block_def = doc.blocks.get("TWO_EQUAL_HORIZONTAL")
        bbox = (0, 0, 100, 10)  # Block bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # Two 20x10 rectangles: left at (0,0)-(20,10), right at (80,0)-(100,10)
        # Union spans 0-100 on x-axis, 0-10 on y-axis
        # Content zone = block bbox, so all trims = 0
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0

    def test_single_shape_regression(self, equal_area_dxf_path: str) -> None:
        """Test single shape behavior is preserved (regression test)."""
        if not os.path.exists(equal_area_dxf_path):
            pytest.skip("Test DXF file not found")

        doc = ezdxf.readfile(equal_area_dxf_path)
        block_def = doc.blocks.get("SINGLE_SHAPE")
        bbox = (0, 0, 50, 30)  # Block bounding box = shape bounding box

        result = _detect_content_zone(block_def, bbox)

        assert result["content_zone_detected"] is True
        # Single shape is the content zone, trim values should be 0
        assert result["suggested_trim_left"] == 0.0
        assert result["suggested_trim_right"] == 0.0
        assert result["suggested_trim_top"] == 0.0
        assert result["suggested_trim_bottom"] == 0.0
